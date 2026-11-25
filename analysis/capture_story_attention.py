#!/usr/bin/env python3
"""Read-only, optional token-level capture for the recorded Angela case.

Uses the frozen discovery budget and shared context; no training or intervention.
All output goes under analysis/. Requires the original model-loading modules,
local model weights, and (optionally) the saved slice checkpoint.
"""
from __future__ import annotations
import argparse
from contextlib import nullcontext
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
CASE_ID = 'natural_crossed_3e05970d5c8422f2710d__C12'
BRIDGE = 'Rebecca Miller'
NAMES = ('American', 'Inge Morath')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('dataset', 'model', 'budget'):
        p.add_argument('--' + key, required=True)
    p.add_argument('--family', choices=['llama'], default='llama')
    p.add_argument('--device', default='cuda')
    p.add_argument('--checkpoint', help='Original trained slice checkpoint directory')
    p.add_argument('--scope', help='Original fixed restoration scope JSON; required with checkpoint')
    p.add_argument('--output', default=str(ROOT / 'analysis/figure_data/data_revision_token_capture.json'))
    p.add_argument('--run', action='store_true')
    args = p.parse_args()
    out = Path(args.output).resolve()
    if not out.is_relative_to(ROOT / 'analysis'):
        p.error('Output must be inside analysis/')
    if bool(args.checkpoint) != bool(args.scope):
        p.error('Provide both checkpoint and scope, or neither')
    if not args.run:
        print(json.dumps(dict(status='PLAN_ONLY', case=CASE_ID, captures=['native_composed','native_direct_same_relation','native_direct_other_relation'] + (['adapted_composed'] if args.checkpoint else []), output=str(out), weights_loaded=False), indent=2)); return
    if out.exists():
        raise FileExistsError(f'Reuse existing measured panel: {out}')
    import numpy as np
    import torch
    from coretrace.data.frozen_loader import FrozenDataset
    from coretrace.data.derived_views import discovery_views
    from coretrace.data.tokenization import tokenize_prompt
    from coretrace.models.native import load_native
    from coretrace.mechanisms.paragraph_attention import NativeEagerHeadChunks
    from coretrace.mechanisms.factorized_attention import NativeSourceConditionalDonor, verify_source_alignment
    from causal import validate_budget
    data = FrozenDataset(args.dataset)
    entries, links = discovery_views(data)
    by = {e['id']: e for e in entries}
    link = next(x for x in links if x['composed'] == CASE_ID)
    budget = json.loads(Path(args.budget).read_text())
    maps, _ = validate_budget(budget, data.lock['dataset_version'])
    model, tok = load_native(args.model, family=args.family, device=args.device)
    model.eval().requires_grad_(False)

    def prepare(e):
        entry = dict(e, **tokenize_prompt(tok, e['prompt'], family=args.family))
        matches = [v for v in entry['paragraphs'] if v['title'] == BRIDGE]
        if len(matches) != 1:
            raise ValueError('Expected a unique Rebecca Miller bridge')
        entry['second_source_keys'] = matches[0]['keys']
        return entry, matches[0]

    receiver, paragraph = prepare(by[CASE_ID])
    same, _ = prepare(by[link['target']])
    # C12 and T11 share the first-hop entity and paragraph, but request
    # different second-hop relations. This is an observational comparison,
    # not a donor-transfer intervention (the source IDs differ).
    other, _ = prepare(by[CASE_ID.rsplit('__',1)[0] + '__T11'])
    keys = receiver['second_source_keys']
    prefix = receiver['prompt_ids'][:max(keys)+1]
    for e in (same,other):
        if e['second_source_keys'] != keys or e['prompt_ids'][:max(keys)+1] != prefix:
            raise ValueError('Bridge keys and context prefix must align exactly')
    chat = tok.apply_chat_template([dict(role='user',content=receiver['prompt'])], tokenize=False, add_generation_prompt=True)
    enc = tok(chat, add_special_tokens=False, return_offsets_mapping=True)
    if list(enc['input_ids']) != receiver['prompt_ids']:
        raise ValueError('Offset mapping differs from captured native prompt')
    prompt = receiver['prompt']; content = prompt if prompt in chat else prompt.strip()
    shift = chat.index(content) - (0 if content == prompt else len(prompt)-len(prompt.lstrip()))
    lo, hi = paragraph['prompt_char_span']; body = prompt[lo:hi]
    groups = {}
    for name in NAMES:
        if body.count(name) != 1:
            raise ValueError(f'Unique literal {name!r} required in bridge')
        start = shift + lo + body.index(name); end = start+len(name)
        groups[name] = [j for j,k in enumerate(keys) if enc['offset_mapping'][k][1] > start and enc['offset_mapping'][k][0] < end]
        if not groups[name]:
            raise ValueError(f'Empty token span: {name}')
    if set(groups[NAMES[0]]) & set(groups[NAMES[1]]):
        raise ValueError('Overlapping token spans')

    def observe(entry, active=None):
        cap = NativeSourceConditionalDonor(model, entry, maps)
        ids = torch.tensor([entry['prompt_ids']], device=next(model.parameters()).device)
        with torch.inference_mode(), NativeEagerHeadChunks(model, 4), active.session(entry) if active else nullcontext(), cap:
            result = model(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False, logits_to_keep=1)
        del result, ids
        return cap.donor_bank()

    banks = {'native_composed':observe(receiver), 'native_direct_same_relation':observe(same), 'native_direct_other_relation':observe(other)}
    verify_source_alignment(receiver, banks['native_direct_same_relation'])
    if args.checkpoint:
        from coretrace.models.deployment import DeploymentBody
        cp = Path(args.checkpoint)
        training = json.loads((cp/'training.json').read_text())
        scope = json.loads(Path(args.scope).read_text()); scope = scope.get('winner', scope)
        with DeploymentBody(model, args.checkpoint, scope=scope, expected_dataset_version=data.lock['dataset_version'], expected_model_identity=training['model_identity']) as active:
            banks['adapted_composed'] = observe(receiver, active)
    # The same valid heads enter each displayed state; record excluded heads.
    shared = [(str(l),str(h)) for l, hs in maps.items() for h in hs if all(b['records'][str(l)][str(h)]['valid'] for b in banks.values())]
    if not shared:
        raise ValueError('No head with a valid conditional in all captures')
    rows = []
    for state,bank in banks.items():
        records = [bank['records'][l][h] for l,h in shared]
        vectors = np.asarray([x['conditional'] for x in records], dtype=float)
        if vectors.shape != (len(shared),len(keys)) or not np.allclose(vectors.sum(axis=1),1,atol=1e-5):
            raise ValueError('Invalid conditional capture')
        mean = vectors.mean(axis=0)
        mass = np.mean([x['native_source_mass']/x['native_row_total'] for x in records])
        weights = {n:float(mean[ix].sum()) for n,ix in groups.items()}
        rows.append(dict(state=state, donor_id=bank['donor_id'], bridge_mass=float(mass), conditional_mean=mean.tolist(), span_weights=weights, other_weight=float(1-sum(weights.values()))))
    payload = dict(status='MEASURED_READONLY_CAPTURE', dataset_version=data.lock['dataset_version'], case_id=CASE_ID, source_id=receiver['source_id'], bridge=BRIDGE, question=receiver['question'], family=args.family, model_path=str(args.model), checkpoint=str(args.checkpoint) if args.checkpoint else None, head_count=len(shared), frozen_head_count=sum(map(len,maps.values())), valid_heads=shared, last_question_row=True, bridge_token_ids=[receiver['prompt_ids'][k] for k in keys], tokens=tok.convert_ids_to_tokens([receiver['prompt_ids'][k] for k in keys]), span_indices=groups, states=rows, raw_records=banks)
    out.parent.mkdir(parents=True,exist_ok=True)
    payload['span_labels'] = dict(other_relation=NAMES[0], target=NAMES[1])
    with out.open('x', encoding='utf-8') as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(f'Wrote {out}')

if __name__ == '__main__':
    main()
