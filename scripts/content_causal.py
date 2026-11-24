"""Matched original/reciprocal content-use assessment on frozen discovery facts.

Support addresses are diagnostic only for the explicitly named oracle-budget
arm. Final evidence selection uses the actual edited input and frozen readout.
"""
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from coretrace.data.frozen_loader import FrozenDataset
from coretrace.data.derived_views import reciprocal_value_views
from coretrace.eval.ledgers import EvaluationLedger, read_complete

def summarize_content(directory, *, seed=42):
    import numpy as np
    manifest, rows = read_complete(directory)
    rng = np.random.default_rng(seed)
    by = {(r['variant'], r['view'], r['source_id']): r for r in rows}
    variants = list(dict.fromkeys((r['variant'] for r in rows)))
    ids = sorted({r['source_id'] for r in rows})
    summary = []
    contrasts = []
    for variant in variants:
        before = [by[variant, 'original', sid] for sid in ids]
        after = [by[variant, 'edited', sid] for sid in ids]
        for pool in ['all_sources', 'actual_swaps']:
            keep = [i for i, r in enumerate(after) if pool == 'all_sources' or r['counterfactual_applied']]
            summary.append(dict(variant=variant, pool=pool, n=len(keep), original_old_correct=sum((before[i]['old_alias_em'] for i in keep)), edited_new_follow=sum((after[i]['new_alias_em'] for i in keep)), edited_old_persistence=sum((after[i]['old_alias_em'] for i in keep)), original_correct_then_new=sum((before[i]['old_alias_em'] and after[i]['new_alias_em'] for i in keep)), address_prefills=sum((after[i]['address_prefills'] for i in keep))))
    for j, left in enumerate(variants):
        for right in variants[j + 1:]:
            groups = {}
            gains = losses = 0
            for sid in ids:
                a = by[left, 'edited', sid]
                b = by[right, 'edited', sid]
                d = int(b['new_alias_em']) - int(a['new_alias_em'])
                groups.setdefault(a['cluster_id'], []).append(d)
                gains += d > 0
                losses += d < 0
            parts = list(groups.values())
            totals = np.array([sum(x) for x in parts])
            sizes = np.array([len(x) for x in parts])
            draw = rng.integers(0, len(parts), (2000, len(parts)))
            dist = totals[draw].sum(1) / sizes[draw].sum(1)
            contrasts.append(dict(before=left, after=right, n=len(ids), metric='edited_new_follow', gains=int(gains), losses=int(losses), delta=float(totals.sum() / sizes.sum()), quad_clusters=len(parts), quad_cluster_CI95=np.quantile(dist, [0.025, 0.975]).tolist()))
    return dict(status='COMPLETE_MATCHED_CONTENT_CAUSAL_ASSESSMENT', summary=summary, paired_method_contrasts=contrasts, noops_receive_new_target_credit=False, interpretation='Auxiliary input counterfactual, separate from canonical QA benchmark scores; all original sources and flags retained.')

def assess(model, tokenizer, entries, *, family, variants, head_map, readout, checkpoint, scope, budget, output, provenance, freeze):
    from contextlib import nullcontext
    from coretrace.models.deployment import DeploymentBody
    from coretrace.data.tokenization import tokenize_prompt
    from coretrace.method.pipeline import EvidenceSelector
    from coretrace.mechanisms.paragraph_attention import NativeParagraphBudget
    from coretrace.eval.inference import greedy_answer
    from coretrace.eval.answer_metrics import score_answer
    ids = [r['id'] for r in entries]
    methods = [v + '_' + view for v in variants for view in ['original', 'edited']]
    ledger = EvaluationLedger(output, provenance=provenance, entry_ids=ids, methods=methods)
    eos = [151645, 151643] if family == 'qwen3' else [128001, 128008, 128009]
    restore = {}
    for variant in variants:
        metadata = json.loads((Path(checkpoint) / 'training.json').read_text()) if variant in ['body', 'final'] else None
        context = DeploymentBody(model, checkpoint, scope=scope, expected_dataset_version=freeze, expected_model_identity=metadata['model_identity']) if metadata else nullcontext()
        with context as body:
            selector = EvidenceSelector(model, tokenizer, head_map, readout, family=family, paragraph_boundary='leading_newline' if family == 'qwen3' else 'line_start') if variant == 'final' else None
            for item in entries:
                for view in ['original', 'edited']:
                    method = variant + '_' + view
                    job = method + ':' + item['id']
                    if job in ledger.rows:
                        continue
                    prompt = item[view + '_prompt']
                    entry = dict(item, **tokenize_prompt(tokenizer, prompt, family=family))
                    selection = dict(chosen=None, address_prefills=0)
                    if selector:
                        entry, selection = selector.select(entry, body=body)
                    session = body.session(entry) if body is not None else None
                    if variant == 'native_budget':
                        titles = [p['title'] for p in entry['paragraphs']]
                        target = [i for i, t in enumerate(titles) if t == item['bridge_source_title']]
                        if len(target) != 1:
                            raise ValueError('Unique diagnostic bridge title required')
                        entry = dict(entry, second_source_keys=entry['paragraphs'][target[0]]['keys'])
                        session = NativeParagraphBudget(model, entry, budget['head_map'], budget['budgets'])
                    prediction = greedy_answer(model, tokenizer, entry, eos_token_ids=eos, pad_token_id=tokenizer.eos_token_id, session=session)
                    old = score_answer(prediction['answer'], item['gold_aliases'])
                    new = score_answer(prediction['answer'], item['replacement_aliases']) if item['counterfactual_applied'] else None
                    old_correct = bool(prediction['eos_complete'] and old['em'])
                    new_correct = bool(item['counterfactual_applied'] and prediction['eos_complete'] and new['em'])
                    row = dict(id=item['id'], source_id=item['source_id'], cluster_id=item['quadruplet_id'], query='composed', method=method, variant=variant, view=view, correct=old_correct if view == 'original' else new_correct, old_alias_em=old_correct, new_alias_em=new_correct, counterfactual_applied=item['counterfactual_applied'], reason=item['reason'], word_bag_identical=item['word_bag_identical'], character_bag_identical=item['character_bag_identical'], address_prefills=selection['address_prefills'], selected_paragraph=selection['chosen'], **prediction)
                    if view == 'edited' and (not item['counterfactual_applied']):
                        prior = ledger.rows[variant + '_original:' + item['id']]
                        if row['generated_token_ids'] != prior['generated_token_ids']:
                            raise ValueError('Unchanged input must preserve exact prediction IDs')
                    ledger.append(row)
        if metadata:
            restore[variant] = context.restore_report
    restore['native'] = dict(readonly_intervention=True)
    ledger.finish(restore_reports=restore)
    report = summarize_content(output, seed=provenance['seed'])
    (Path(output) / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    return report

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', required=True)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--plan', action='store_true')
    mode.add_argument('--run', action='store_true')
    a = p.parse_args()
    configpath = Path(a.config).resolve()
    config = json.loads(configpath.read_text())

    def path(value):
        p = Path(value).expanduser()
        return p.resolve() if p.is_absolute() else (configpath.parent / p).resolve()
    data = FrozenDataset(path(config['dataset']))
    entries = reciprocal_value_views(data)
    variants = config.get('variants', ['native', 'body', 'final'])
    if len(set(variants)) != len(variants) or not set(variants) <= set(['native', 'native_budget', 'body', 'final']):
        raise ValueError('Unique declared content-assay variants required')
    plan = dict(status='PLAN_ONLY', sources=len(entries), quad_clusters=25, variants=variants, views=['original', 'edited'], expected_generations=2 * len(variants) * len(entries), actual_swaps=sum((e['counterfactual_applied'] for e in entries)), dataset_version=data.lock['dataset_version'], canonical_dataset_changed=False, model_weights_loaded=False)
    if not a.run:
        print(json.dumps(plan, indent=2))
        return
    from coretrace.models.native import load_native
    model, tok = load_native(path(config['model']['path']), family=config['model']['family'], device=config['model'].get('device', 'cuda'), dtype=config['model'].get('dtype', 'bfloat16'))
    heads = json.loads(path(config['heads']).read_text())
    heads = heads.get('head_map', heads)
    readout = json.loads(path(config['readout']).read_text()) if 'final' in variants else None
    checkpoint = path(config['checkpoint']) if set(variants) & set(['body', 'final']) else None
    scope = json.loads(path(config['scope']).read_text()) if config.get('scope') else None
    if scope is not None:
        scope = scope.get('winner', scope)
    budget = json.loads(path(config['budget']).read_text()) if 'native_budget' in variants else None
    if budget is not None:
        from causal import validate_budget
        validate_budget(budget, data.lock['dataset_version'])
    provenance = dict(model_identity=config['model'], seed=config['seed'], dataset_version=data.lock['dataset_version'], variants=variants, oracle_addressing='native_budget only; final selector input-only')
    report = assess(model, tok, entries, family=config['model']['family'], variants=variants, head_map=heads, readout=readout, checkpoint=checkpoint, scope=scope, budget=budget, output=path(config['output']), provenance=provenance, freeze=data.lock['dataset_version'])
    print(json.dumps(report, indent=2))
if __name__ == '__main__':
    from coretrace.stage_lock import run_stage
    run_stage(main, 'manifest.json')
