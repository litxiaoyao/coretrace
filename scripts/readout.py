"""Capture deployment-state paragraph features and fit the fixed training reader.

Default --plan verifies the frozen data only. --run performs model inference.
Test labels are used exclusively in the final diagnostic after train-only fitting.
"""
import argparse, hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coretrace.data.frozen_loader import FrozenDataset

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['dataset', 'model', 'family', 'heads', 'output']:
        p.add_argument('--' + name, required=True)
    p.add_argument('--checkpoint')
    p.add_argument('--scope')
    p.add_argument('--device', default='cuda')
    p.add_argument('--seed', type=int, choices=[42, 43, 44], required=True)
    p.add_argument('--run', action='store_true')
    p.add_argument('--plan', action='store_true')
    a = p.parse_args()
    data = FrozenDataset(a.dataset)
    headfile = json.loads(Path(a.heads).read_text())
    heads = headfile.get('head_map', headfile)
    scope = json.loads(Path(a.scope).read_text()) if a.scope else None
    if scope is not None:
        scope = scope.get('winner', scope)
    if not a.run:
        print(json.dumps(dict(status='PLAN_ONLY', train_sources=2000, test_sources=1000, head_count=sum(map(len, heads.values())), readout_parameters=2 * sum(map(len, heads.values())) + 2, steps=500, lr=0.03, L2=0.01, seed=a.seed, checkpoint=a.checkpoint, scope=scope, model_weights_loaded=False), indent=2))
        return
    import torch
    from contextlib import nullcontext
    from coretrace.models.native import load_native
    from coretrace.models.deployment import DeploymentBody
    from coretrace.data.tokenization import tokenize_prompt
    from coretrace.mechanisms.paragraph_attention import NativeParagraphObserver, NativeEagerHeadChunks
    from coretrace.method.address_readout import fit_address_readout, address_scores
    model, tok = load_native(a.model, family=a.family, device=a.device)
    if scope is not None and (not a.checkpoint):
        raise ValueError('Rollback requires a trained slice checkpoint')
    out = Path(a.output)
    out.mkdir(parents=True, exist_ok=False)
    ledger = out / 'features.jsonl'
    rows = []
    labels = {}
    metadata = json.loads((Path(a.checkpoint) / 'training.json').read_text()) if a.checkpoint else None
    body = DeploymentBody(model, a.checkpoint, scope=scope, expected_dataset_version=data.lock['dataset_version'], expected_model_identity=metadata['model_identity']) if metadata else nullcontext()
    with body as active:
        with ledger.open('x') as stream:
            for split in ['train', 'test']:
                corpus = {e['source_id']: e for e in data.sources(split)}
                for query in data.queries(split, 'composed'):
                    entry = dict(query, **tokenize_prompt(tok, query['prompt'], family=a.family))
                    observer = NativeParagraphObserver(model, entry, heads)
                    ids = torch.tensor([entry['prompt_ids']], device=next(model.parameters()).device)
                    with torch.inference_mode(), NativeEagerHeadChunks(model, 4), active.session(entry) if active else nullcontext(), observer:
                        result = model(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False, logits_to_keep=1)
                    del result, ids
                    row = dict(id=query['id'], source_id=query['source_id'], split=split, features=observer.features, paragraphs=[dict(key_count=len(x['keys']), title_mentioned_in_question=x['title_mentioned_in_question']) for x in entry['paragraphs']], prompt_tokens=len(entry['prompt_ids']))
                    rows.append(row)
                    stream.write(json.dumps(row) + '\n')
                    stream.flush()
                    target = corpus[query['source_id']]['edges']['second_target']['title']
                    targets = [i for i, x in enumerate(entry['paragraphs']) if x['title'] == target]
                    if len(targets) != 1:
                        raise ValueError('Unique official second-source paragraph required')
                    labels[row['id']] = targets[0]
                    (out / 'progress.json').write_text(json.dumps(dict(captured=len(rows), expected=3000, split=split)) + '\n')
    train = [r for r in rows if r['split'] == 'train']
    diagnostics = {}
    for feature_set in ['full', 'attention', 'metadata']:
        artifact = fit_address_readout(train, {r['id']: labels[r['id']] for r in train}, seed=a.seed, feature_set=feature_set)
        artifact.update(dataset_version=data.lock['dataset_version'], scope=scope)
        filename = 'address_readout.json' if feature_set == 'full' else f'{feature_set}_readout.json'
        (out / filename).write_text(json.dumps(artifact, indent=2) + '\n')
        diagnostics[feature_set] = {split: dict(n=sum(r['split'] == split for r in rows), correct=sum(int(address_scores(r, artifact).argmax()) == labels[r['id']] for r in rows if r['split'] == split)) for split in ['train', 'test']}
    report = dict(status='COMPLETE_TRAIN_ONLY_ADDRESS_READOUT', diagnostics=diagnostics, test_labels_used_for_fitting=False, LLM_updates=0, dataset_version=data.lock['dataset_version'])
    if metadata:
        report['native_restore'] = body.restore_report
    (out / 'complete.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
if __name__ == '__main__':
    from coretrace.stage_lock import run_stage
    run_stage(main, 'complete.json')
