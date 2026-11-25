#!/usr/bin/env python3
"""One supplemental experiment: read-only paired token-conditional attention.

Use frozen discovery25, frozen head maps, native vs existing adapted/restored
checkpoint on identical full contexts. No training, donor transplantation, or
new test set. Defaults to plan only. Outputs only analysis/figure_data/.
"""
from __future__ import annotations
import argparse
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
CASE_ID = 'natural_crossed_3e05970d5c8422f2710d__C12'
MODELS = {'qwen3_4b': 'qwen3', 'qwen3_8b': 'qwen3', 'llama3_8b': 'llama'}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model-id', choices=list(MODELS), required=True)
    for k in ('dataset', 'model', 'budget', 'checkpoint', 'scope'):
        p.add_argument('--' + k, required=True)
    p.add_argument('--device', default='cuda')
    p.add_argument('--case-only', action='store_true', help='Angela pilot; Llama only')
    p.add_argument('--run', action='store_true')
    p.add_argument('--output', help='Must be a new JSON file under analysis/figure_data/')
    a = p.parse_args()
    if a.case_only and a.model_id != 'llama3_8b':
        p.error('--case-only is reserved for the recorded Llama example')
    out = Path(a.output or ROOT / 'analysis/figure_data' / (f'data_revision_relation_reading_{a.model_id}' + ('_pilot' if a.case_only else '') + '.json')).resolve()
    if not out.is_relative_to(ROOT / 'analysis/figure_data'):
        p.error('Output must be under analysis/figure_data/')
    states = ['native_composed', 'native_direct_same_relation', 'native_direct_other_relation', 'adapted_composed']
    if not a.run:
        print(json.dumps(dict(status='PLAN_ONLY', model=a.model_id, frozen_receivers=1 if a.case_only else 100, states=states, max_prefills=4 if a.case_only else 400, output=str(out), no_training=True), indent=2))
        return
    if out.exists():
        raise FileExistsError(f'Reuse/verify existing captures; do not overwrite: {out}')
    import numpy as np
    import torch
    torch.set_num_threads(4)
    torch.set_num_interop_threads(2)
    from coretrace.data.frozen_loader import FrozenDataset
    from coretrace.data.derived_views import discovery_views, _object_span
    from coretrace.data.tokenization import tokenize_prompt
    from coretrace.models.native import load_native
    from coretrace.models.deployment import DeploymentBody
    from coretrace.mechanisms.paragraph_attention import NativeEagerHeadChunks
    from coretrace.mechanisms.factorized_attention import NativeSourceConditionalDonor, verify_source_alignment
    from causal import validate_budget

    family = MODELS[a.model_id]
    data = FrozenDataset(a.dataset)
    entries, links = discovery_views(data)
    by = {e['id']: e for e in entries}
    quads = {q['quadruplet_id']: q for q in map(json.loads, (data.root / 'mechanism_views/discovery25_quadruplets.jsonl').open())}
    if a.case_only:
        links = [l for l in links if l['composed'] == CASE_ID]
    budget = json.loads(Path(a.budget).read_text())
    maps, _ = validate_budget(budget, data.lock['dataset_version'])
    expected_heads = {'qwen3_4b': 20, 'qwen3_8b': 20, 'llama3_8b': 40}[a.model_id]
    if sum(map(len, maps.values())) != expected_heads:
        raise ValueError('Unexpected selected head count')
    training_path = Path(a.checkpoint) / 'training.json'
    training = json.loads(training_path.read_text())
    scope = json.loads(Path(a.scope).read_text())
    scope = scope.get('winner', scope)
    if Path(training['model_identity']['model']).resolve() != Path(a.model).resolve():
        raise ValueError('Checkpoint was trained from a different base model')
    if {str(k): sorted(v) for k,v in training['head_map'].items()} != {str(k): sorted(v) for k,v in maps.items()}:
        raise ValueError('Checkpoint head map differs from frozen discovery selection')
    config = json.loads((ROOT/'configs/experiments.json').read_text())
    # The actual evaluation manifest is the authority for the frozen deployment scope.
    evaluation = json.loads((ROOT/f'outputs/configs/{a.model_id}_42_core.json').read_text())
    if scope != next(x['scope'] for x in evaluation['methods'] if x['name']=='final'):
        raise ValueError('Scope differs from the original final-method manifest')
    source_paths = [Path(a.budget), training_path, Path(a.checkpoint)/'slices_final.safetensors',
                    Path(a.scope), data.root/'mechanism_views/discovery25_quadruplets.jsonl',
                    data.root/'dataset.json', data.root/'corpus.jsonl',data.root/'queries.jsonl',
                    data.root/'aliases.jsonl', ROOT/f'outputs/configs/{a.model_id}_42_core.json']
    source_paths += [p for name in ['config.json','tokenizer_config.json','tokenizer.json','model.safetensors.index.json']
                     if (p := Path(a.model)/name).exists()]
    provenance = {str(p.resolve()): sha(p) for p in source_paths}
    provenance_key = hashlib.sha256(json.dumps(provenance,sort_keys=True).encode()).hexdigest()
    cache = ROOT/'analysis/build_story_revision'/f'token_cache_{a.model_id}'/provenance_key
    cache.mkdir(parents=True,exist_ok=True)
    model, tok = load_native(a.model, family=family, device=a.device)
    model.eval().requires_grad_(False)
    if sum(p.numel() for p in model.parameters()) != training['model_identity']['native_parameters']:
        raise ValueError('Base-model parameter count differs from training identity')
    print(json.dumps(dict(event='MODEL_READY',model=a.model_id,scope=scope,provenance=provenance_key)),flush=True)

    def prepare(e):
        item = dict(e, **tokenize_prompt(tok, e['prompt'], family=family))
        ps = [v for v in item['paragraphs'] if v['title'] == e['bridge_source_title']]
        if len(ps) != 1:
            raise ValueError('Unique bridge required')
        item['second_source_keys'] = ps[0]['keys']
        return item

    def capture(entry, active=None):
        state = 'adapted' if active else 'native'
        key = hashlib.sha256(json.dumps([state,entry['id'],entry['prompt_ids']],separators=(',',':')).encode()).hexdigest()
        target = cache/(key+'.json')
        if target.exists():
            bank = json.loads(target.read_text())
            verify_source_alignment(entry,bank)
            return bank
        observer = NativeSourceConditionalDonor(model, entry, maps)
        ids = torch.tensor([entry['prompt_ids']], device=next(model.parameters()).device)
        with torch.inference_mode(), NativeEagerHeadChunks(model, 4), active.session(entry) if active else nullcontext(), observer:
            result = model(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False, logits_to_keep=1)
        del result, ids
        bank = observer.donor_bank()
        temporary=target.with_suffix('.tmp')
        temporary.write_text(json.dumps(bank,separators=(',',':')))
        temporary.replace(target)
        print(json.dumps(dict(event='PREFILL_CAPTURED',state=state,query_id=entry['id'],prompt_tokens=len(entry['prompt_ids']),time=time.time())),flush=True)
        return bank

    # Every eligible receiver is selected by geometry/annotation, never correctness.
    # Keep all exclusion reasons; raw weights cannot be recovered from old mass logs.
    valid = []
    excluded = []
    for link in links:
        cid = link['composed']
        rec = by[cid]
        i, j = int(rec['cell'][1]), int(rec['cell'][2])
        other_cell = f'C{i}{3-j}'
        other_rec = by[rec['quadruplet_id']+'__'+other_cell]
        same = by[link['target']]
        other = by[rec['quadruplet_id']+f'__T{i}{3-j}']
        if rec['bridge_source_title'] != other_rec['bridge_source_title']:
            excluded.append(dict(id=cid, reason='different_bridge')); continue
        try:
            r, t, o = [prepare(e) for e in (rec, same, other)]
        except ValueError as error:
            excluded.append(dict(id=cid,reason='token_geometry:'+str(error)));continue
        keys = r['second_source_keys']
        prefix = r['prompt_ids'][:max(keys)+1]
        if any(e['second_source_keys'] != keys or e['prompt_ids'][:max(keys)+1] != prefix for e in (t,o)):
            excluded.append(dict(id=cid, reason='bridge_alignment')); continue
        qs = {q['cell']: q for q in quads[rec['quadruplet_id']]['queries']}
        kwargs = dict(tokenize=False, add_generation_prompt=True)
        if family == 'qwen3': kwargs['enable_thinking'] = False
        prompt = r['prompt']; chat = tok.apply_chat_template([dict(role='user',content=prompt)], **kwargs)
        enc = tok(chat, add_special_tokens=False, return_offsets_mapping=True)
        if list(enc['input_ids']) != r['prompt_ids']:
            raise ValueError('Native tokenization differs from offset encoding')
        content = prompt if prompt in chat else prompt.strip()
        shift = chat.index(content) - (0 if content == prompt else len(prompt)-len(prompt.lstrip()))
        spans = {}; reason = None; groups = {}
        for kind, item, cell in [('target',rec,rec['cell']), ('other_relation',other_rec,other_cell)]:
            span, error = _object_span(prompt, item['bridge_source_title'], qs[cell]['support_sentences'][1]['text'], item['gold_aliases'])
            if error: reason = kind+':'+error; break
            lo,hi,name = span
            positions = [ix for ix,k in enumerate(keys) if enc['offset_mapping'][k][1]>shift+lo and enc['offset_mapping'][k][0]<shift+hi]
            if not positions: reason=kind+':empty_token_span';break
            groups[kind] = positions; spans[kind]=dict(text=name, prompt_span=[lo,hi], token_indices=positions)
        if reason or set(groups.get('target',[])) & set(groups.get('other_relation',[])):
            excluded.append(dict(id=cid, reason=reason or 'overlapping_token_spans'));continue
        valid.append(dict(id=cid, receiver=r, same=t, other=o, spans=spans, groups=groups, banks={}))
    if len(valid)+len(excluded)!=len(links) or not valid:
        raise ValueError('No eligible frozen receiver or bad accounting')
    print(json.dumps(dict(event='GEOMETRY_VALIDATED',eligible=len(valid),excluded=excluded)),flush=True)
    for item in valid:
        banks=item['banks']
        banks['native_composed']=capture(item['receiver'])
        banks['native_direct_same_relation']=capture(item['same'])
        verify_source_alignment(item['receiver'],banks['native_direct_same_relation'])
        banks['native_direct_other_relation']=capture(item['other'])
    with DeploymentBody(model, a.checkpoint, scope=scope, expected_dataset_version=data.lock['dataset_version'], expected_model_identity=training['model_identity']) as active:
        for item in valid:
            item['banks']['adapted_composed']=capture(item['receiver'],active)
    records=[]
    for item in valid:
        banks=item['banks']; receiver=item['receiver']; keys=receiver['second_source_keys']; groups=item['groups']
        heads=[(str(l),str(h)) for l,hs in maps.items() for h in hs if all(b['records'][str(l)][str(h)]['valid'] for b in banks.values())]
        if not heads:
            excluded.append(dict(id=item['id'],reason='no_common_valid_heads'));continue
        rows=[]
        for state in states:
            bank=banks[state]; recs=[bank['records'][l][h] for l,h in heads]
            vector=np.asarray([r['conditional'] for r in recs],dtype=float)
            mass=np.asarray([r['native_source_mass']/r['native_row_total'] for r in recs],dtype=float)
            if vector.shape!=(len(heads),len(keys)) or not np.isfinite(vector).all() or np.any(vector<0) or not np.allclose(vector.sum(axis=1),1,atol=1e-5) or not np.isfinite(mass).all() or np.any((mass<0)|(mass>1.00001)):
                raise ValueError(f'Invalid measured attention: {item["id"]}, {state}')
            rho={k:vector[:,v].sum(axis=1) for k,v in groups.items()}
            rows.append(dict(state=state, query_id=bank['donor_id'], bridge_mass=float(mass.mean()), conditional_target=float(rho['target'].mean()), conditional_other=float(rho['other_relation'].mean()), conditional_target_per_token=float((rho['target']/len(groups['target'])).mean()), conditional_other_per_token=float((rho['other_relation']/len(groups['other_relation'])).mean()), absolute_target_mass=float((mass*rho['target']).mean()), absolute_other_mass=float((mass*rho['other_relation']).mean()), conditional_mean=vector.mean(axis=0).tolist()))
        records.append(dict(id=item['id'], source_id=receiver['source_id'], quadruplet_id=receiver['quadruplet_id'], question=receiver['question'], bridge=receiver['bridge_source_title'], spans=item['spans'], valid_heads=heads, bridge_token_ids=[receiver['prompt_ids'][k] for k in keys], tokens=tok.convert_ids_to_tokens([receiver['prompt_ids'][k] for k in keys]), states=rows, raw_records=banks))
    if len(records)+len(excluded)!=len(links) or not records:
        raise ValueError('Incomplete receiver accounting')
    payload=dict(status='MEASURED_PAIRED_RELATION_CAPTURE', model_id=a.model_id, model_path=str(a.model), checkpoint=str(a.checkpoint), dataset_version=data.lock['dataset_version'], frozen_head_count=expected_heads, question_row='last_question', expected_receivers=len(links), analyzed_receivers=len(records), excluded_receivers=excluded, states=states, budget_sha256=sha(a.budget), training_json_sha256=sha(training_path), scope_sha256=sha(a.scope), view_sha256=sha(data.root/'mechanism_views/discovery25_quadruplets.jsonl'), records=records)
    payload.update(source_files_sha256=provenance,source_identity=provenance_key,scope=scope,
                   native_model_identity=training['model_identity'],read_only_prefill=True,
                   no_evidence_selection=True,cache_reuse='Exact input token IDs, query ID, state and source hashes; pilot and full run share the same cache')
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf8') as f: json.dump(payload,f,ensure_ascii=False,separators=(',',':')); f.write('\n')
    print(f'Wrote {out}; {len(records)}/{len(links)} matched receivers')
    if a.model_id == 'llama3_8b':
        export_case_panel(payload, out)


def export_case_panel(payload, source):
    """Export the fixed case from a measured pilot or full bank without inference."""
    if payload['status'] != 'MEASURED_PAIRED_RELATION_CAPTURE' or payload['model_id'] != 'llama3_8b':
        raise ValueError('Expected a measured Llama capture')
    case = next((record for record in payload['records'] if record['id'] == CASE_ID), None)
    if case is None:
        raise ValueError(f'Missing fixed Angela case in {source}')
    target = case['spans']['target']['text']
    other = case['spans']['other_relation']['text']
    states = [
        dict(
            state=row['state'],
            donor_id=row['query_id'],
            bridge_mass=row['bridge_mass'],
            conditional_mean=row['conditional_mean'],
            span_weights={target: row['conditional_target'], other: row['conditional_other']},
            other_weight=1 - row['conditional_target'] - row['conditional_other'],
        )
        for row in case['states']
    ]
    panel = dict(
        status='MEASURED_READONLY_CAPTURE',
        case_id=CASE_ID,
        head_count=len(case['valid_heads']),
        source=str(source.resolve().relative_to(ROOT)),
        source_sha256=sha(source),
        source_identity=payload['source_identity'],
        states=states,
        span_labels=dict(target=target, other_relation=other),
        bridge_token_ids=case['bridge_token_ids'],
        tokens=case['tokens'],
        span_indices={span['text']: span['token_indices'] for span in case['spans'].values()},
        raw_records=case['raw_records'],
    )
    out = ROOT / 'analysis/figure_data/data_revision_token_capture.json'
    if out.exists():
        existing = json.loads(out.read_text())
        for key in panel.keys() - {'source', 'source_sha256'}:
            if existing.get(key) != panel[key]:
                raise ValueError(f'Existing panel differs from {source} in {key}')
        return
    with out.open('x', encoding='utf8') as stream:
        json.dump(panel, stream, ensure_ascii=False, separators=(',', ':'))
        stream.write('\n')


if __name__ == '__main__':
    main()
