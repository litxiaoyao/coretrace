"""Separate paragraph-access mass from relation-conditioned attention within it.

Uses all25 frozen discovery quadruplets as diagnostic views, not the canonical
QA test set. A direct-target question donates only normalized source attention;
receiver values, output projections, questions and original contexts stay intact.
"""
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from coretrace.data.frozen_loader import FrozenDataset
from coretrace.data.derived_views import discovery_views
from coretrace.eval.ledgers import EvaluationLedger
from coretrace.eval.summarize import summarize
from causal import validate_budget
ARMS = ['native', 'identity', 'mass_only', 'conditional_only', 'both']

def run_loaded(model, tokenizer, views, links, budget, output, provenance, *, family, eos_token_ids):
    import torch
    from coretrace.data.tokenization import tokenize_prompt
    from coretrace.mechanisms.factorized_attention import NativeSourceConditionalDonor, NativeFactoredParagraphIntervention, verify_source_alignment
    from coretrace.mechanisms.paragraph_attention import NativeEagerHeadChunks
    from coretrace.eval.inference import greedy_answer
    from coretrace.eval.answer_metrics import score_answer
    model.eval().requires_grad_(False)
    maps, taus = validate_budget(budget, provenance['dataset_version'])
    by = {e['id']: e for e in views}
    receivers = [by[link['composed']] for link in links]
    ledger = EvaluationLedger(output, provenance=provenance, entry_ids=[e['id'] for e in receivers], methods=ARMS)

    def prepare(entry):
        out = dict(entry, **tokenize_prompt(tokenizer, entry['prompt'], family=family))
        matches = [p for p in out['paragraphs'] if p['title'] == entry['bridge_source_title']]
        if len(matches) != 1:
            raise ValueError('Unique original diagnostic bridge paragraph required')
        return dict(out, second_source_keys=matches[0]['keys'])
    pad = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
    for link in links:
        receiver = prepare(by[link['composed']])
        donor_entry = prepare(by[link['target']])
        capture = NativeSourceConditionalDonor(model, donor_entry, maps)
        ids = torch.tensor([donor_entry['prompt_ids']], device=next(model.parameters()).device)
        with torch.inference_mode(), NativeEagerHeadChunks(model, 4), capture:
            result = model(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False, logits_to_keep=1)
        del result, ids
        donor = capture.donor_bank()
        verify_source_alignment(receiver, donor)
        for arm in ARMS:
            if arm + ':' + receiver['id'] in ledger.rows:
                continue
            session = None if arm == 'native' else NativeFactoredParagraphIntervention(model, receiver, maps, taus, donor, mode=arm, rows=receiver['question_positions'])
            prediction = greedy_answer(model, tokenizer, receiver, eos_token_ids=eos_token_ids, pad_token_id=pad, session=session)
            if arm == 'identity' and prediction['generated_token_ids'] != ledger.rows['native:' + receiver['id']]['generated_token_ids']:
                raise ValueError('Identity intervention changed native IDs')
            metrics = score_answer(prediction['answer'], receiver['gold_aliases'])
            endpoint = {cell: bool(prediction['eos_complete'] and score_answer(prediction['answer'], aliases)['em']) for cell, aliases in receiver['endpoint_aliases'].items()}
            ledger.append(dict(prediction, id=receiver['id'], source_id=receiver['source_id'], cluster_id=receiver['quadruplet_id'], query='composed', method=arm, correct=bool(prediction['eos_complete'] and metrics['em']), text_f1=metrics['f1'], cell=receiver['cell'], endpoint_matches=endpoint, source_alignment_verified=True, donor_query_id=donor_entry['id'], donor_kind='Native direct-target last-question-row source attention conditional only', donor_invalid_heads=sum((not rec['valid'] for layer in donor['records'].values() for rec in layer.values())), events=[] if session is None else session.events, privileged_diagnostic=True))
    ledger.finish(restore_reports=dict(readonly_intervention=True))
    report = summarize(output, seed=provenance['seed'])
    report.update(status='COMPLETE_FACTORIZED_CAUSAL_DIAGNOSIS', donor='Only normalized alpha, no answer residual or V/O transfer', calibration_overlap='Discovery diagnostic sources also used for head/tau selection; not an independent generalization estimate.', endpoint_counts={arm: {cell: sum((r['endpoint_matches'][cell] for r in ledger.rows.values() if r['method'] == arm)) for cell in ['C11', 'C12', 'C21', 'C22']} for arm in ARMS}, endpoint_alias_overlap_allowed=True)
    categories = {'own': lambda i,j: f'C{i}{j}', 'other_entity_same_relation': lambda i,j: f'C{3-i}{j}', 'same_entity_other_relation': lambda i,j: f'C{i}{3-j}', 'other_entity_other_relation': lambda i,j: f'C{3-i}{3-j}'}
    report['relative_endpoint_counts'] = {arm: {name: sum(r['endpoint_matches'][cell(int(r['cell'][1]),int(r['cell'][2]))] for r in ledger.rows.values() if r['method'] == arm) for name,cell in categories.items()} for arm in ARMS}
    from coretrace.eval.factorial import summarize_factorial
    report['factorial_accuracy'] = summarize_factorial(list(ledger.rows.values()), seed=provenance['seed'])
    (Path(output) / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    return report

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', required=True)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--plan', action='store_true')
    mode.add_argument('--run', action='store_true')
    args = p.parse_args()
    cp = Path(args.config).resolve()
    config = json.loads(cp.read_text())

    def path(value):
        item = Path(value).expanduser()
        return item.resolve() if item.is_absolute() else (cp.parent / item).resolve()
    data = FrozenDataset(path(config['dataset']))
    views, links = discovery_views(data)
    budgetpath = path(config['budget'])
    budget = json.loads(budgetpath.read_text())
    validate_budget(budget, data.lock['dataset_version'])
    plan = dict(status='PLAN_ONLY', quad_clusters=25, sources=len(links), arms=ARMS, expected_generations=len(links) * len(ARMS), readonly_donor_prefills=len(links), dataset_version=data.lock['dataset_version'], canonical_dataset_changed=False, model_weights_loaded=False, privileged_diagnostic=True, discovery_calibration_overlap=True)
    if not args.run:
        print(json.dumps(plan, indent=2))
        return
    from coretrace.models.native import load_native
    model, tok = load_native(path(config['model']['path']), family=config['model']['family'], device=config['model'].get('device', 'cuda'), dtype=config['model'].get('dtype', 'bfloat16'))
    eos = config.get('eos_token_ids', model.generation_config.eos_token_id or tok.eos_token_id)
    eos = [eos] if isinstance(eos, int) else eos
    provenance = dict(model_identity=dict(**config['model']), seed=config['seed'], dataset_version=data.lock['dataset_version'])
    print(json.dumps(run_loaded(model, tok, views, links, budget, path(config['output']), provenance, family=config['model']['family'], eos_token_ids=eos), indent=2))
if __name__ == '__main__':
    from coretrace.stage_lock import run_stage
    run_stage(main, 'manifest.json')
