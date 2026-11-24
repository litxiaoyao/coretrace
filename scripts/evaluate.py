"""One-model formal evaluation; JSON configuration paths resolve beside that file.

Default --plan verifies inputs/artifacts and prints expected counts without model
loading. --run loads the native model and evaluates every requested item.
"""
import argparse, json, sys, time
from pathlib import Path
from contextlib import nullcontext
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from coretrace.data.frozen_loader import FrozenDataset
from coretrace.eval.ledgers import EvaluationLedger
from coretrace.eval.summarize import summarize

def resolve(base, path):
    p = Path(path).expanduser()
    return p.resolve() if p.is_absolute() else (base / p).resolve()

def read_json_or_inline(base, value):
    if isinstance(value, str):
        return json.loads(resolve(base, value).read_text())
    return value

def load_population(config, base):
    dataset = config['dataset']
    kind = dataset['kind']
    path = resolve(base, dataset['path'])
    if kind == 'core':
        frozen = FrozenDataset(path)
        split = dataset.get('split', 'test')
        rows = frozen.queries(split)
        aliases = {a['source_id']: a for a in frozen.aliases(split)}
        for e in rows:
            e['gold_aliases'] = aliases[e['source_id']]['queries'][e['canonical_query']]['golds']
        identity = dict(kind=kind, split=split, dataset_version=frozen.lock['dataset_version'], sources=len(frozen.split(split)['source_ids']), queries=len(rows), path=str(path))
    elif kind in ['hotpot', 'mmlu', 'gsm8k']:
        expected = {'hotpot': 7405, 'mmlu': 14042, 'gsm8k': 1319}[kind]
        rows = list(map(json.loads, path.open()))
        if len(rows) != expected:
            raise ValueError('External benchmark full fixed denominator required')
        for e in rows:
            e['id'] = e.get('id', e.get('row_id', e.get('source_id')))
            if not e['id']:
                raise ValueError('External stable row ID required')
            e['source_id'] = e.get('source_id', e['id'])
            e['query'] = kind
            if kind == 'hotpot':
                e['gold_aliases'] = e.get('gold_aliases', e.get('golds', [e['gold']]))
        identity = dict(kind=kind, rows=len(rows), path=str(path))
    else:
        raise ValueError('Dataset kind must be core, hotpot, mmlu, or gsm8k')
    if len({e['id'] for e in rows}) != len(rows):
        raise ValueError('Duplicate evaluation IDs')
    return (rows, identity)

def plan(config, base):
    rows, dataset = load_population(config, base)
    methods = config['methods']
    if not methods or len({m['name'] for m in methods}) != len(methods):
        raise ValueError('Unique nonempty method names required')
    refs = {}
    freeze = config.get('dataset_version', dataset.get('dataset_version'))
    for method in methods:
        if method.get('selector', 'no_filter') not in ['no_filter', 'decoded_text', 'graphfirst_text']:
            raise ValueError('Unknown fixed selector')
        if method.get('artifact'):
            artifact = resolve(base, method['artifact'])
            manifest = json.loads((artifact / 'training.json').read_text())
            if manifest['status'] != 'COMPLETE_SELECTED_HEAD_TRAINING':
                raise ValueError('Completed selected-head artifact required')
            if freeze is None:
                freeze = manifest['dataset_version']
            if manifest['dataset_version'] != freeze:
                raise ValueError('Method artifact freeze mismatch')
            refs[str(artifact)] = 'selected-head checkpoint'
        for field in ['scope', 'readout']:
            if isinstance(method.get(field), str):
                p = resolve(base, method[field])
                refs[str(p)] = field
        if method.get('selector', 'no_filter') == 'decoded_text' and (not method.get('readout')):
            raise ValueError('Decoded text requires a frozen readout artifact')
    return (rows, dict(status='PLAN_ONLY', dataset_identity=dataset, dataset_version=freeze, methods=[m['name'] for m in methods], expected_rows=len(rows) * len(methods), model_weights_loaded=False))

def evaluate_loaded(model, tokenizer, rows, config, base, output, provenance):
    """Caller-owned model interface; also exercised using tiny native models."""
    import torch
    from coretrace.data.tokenization import tokenize_prompt
    from coretrace.models.deployment import DeploymentBody
    from coretrace.method.pipeline import EvidenceSelector
    from coretrace.eval.inference import greedy_answer
    from coretrace.eval.answer_metrics import score_answer
    from coretrace.eval.gsm8k import score_answer as score_math
    family = config['model']['family']
    kind = config['dataset']['kind']
    model.eval().requires_grad_(False)
    eos = config.get('eos_token_ids', model.generation_config.eos_token_id or tokenizer.eos_token_id)
    eos = [eos] if isinstance(eos, int) else list(eos)
    if not eos or any((type(i) is not int for i in eos)):
        raise ValueError('Native EOS IDs required')
    pad = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
    entries = []
    for row in rows:
        entry = dict(row, **tokenize_prompt(tokenizer, row['prompt'], family=family))
        if kind == 'mmlu':
            entry['label_token_ids'] = {c: tokenizer.encode(c, add_special_tokens=False) for c in 'ABCD'}
            if any((len(v) != 1 for v in entry['label_token_ids'].values())) or len({v[0] for v in entry['label_token_ids'].values()}) != 4:
                raise ValueError('Native ABCD single-token contract')
        entries.append(entry)
    ledger = EvaluationLedger(output, provenance=provenance, entry_ids=[e['id'] for e in entries], methods=[m['name'] for m in config['methods']])
    restores = {}
    for method in config['methods']:
        artifact = resolve(base, method['artifact']) if method.get('artifact') else None
        metadata = json.loads((artifact / 'training.json').read_text()) if artifact else None
        scope = read_json_or_inline(base, method.get('scope'))
        scope = scope.get('winner', scope) if scope else None
        context = DeploymentBody(model, artifact, scope=scope, expected_dataset_version=provenance['dataset_version'], expected_model_identity=metadata['model_identity']) if artifact else nullcontext()
        readout = read_json_or_inline(base, method.get('readout'))
        component = method.get('selector', 'no_filter')
        head_map = method.get('head_map', metadata['head_map'] if metadata else None)
        selector = EvidenceSelector(model, tokenizer, head_map, readout, family=family, paragraph_boundary=method.get('paragraph_boundary', 'line_start')) if component != 'no_filter' else None
        with context as body:
            batch_size = config.get('batch_size', 1)
            if type(batch_size) is not int or batch_size < 1:
                raise ValueError('Positive integer batch_size required')
            if kind == 'mmlu' and batch_size > 1:
                from coretrace.eval.batched_mmlu import evaluate_mmlu_batches
                pending = [e for e in entries if method['name'] + ':' + e['id'] not in ledger.rows]
                for record in evaluate_mmlu_batches(
                        model, tokenizer, pending, method_name=method['name'],
                        batch_size=batch_size, eos_token_ids=eos, pad_token_id=pad,
                        body=body, selector=selector, component=component):
                    ledger.append(record)
                single_entries = []
            elif kind in ('core', 'hotpot') and batch_size > 1:
                from coretrace.eval.batched_qa import evaluate_qa_batches
                pending = [e for e in entries if method['name'] + ':' + e['id'] not in ledger.rows]
                for record in evaluate_qa_batches(
                        model, tokenizer, pending, method_name=method['name'],
                        batch_size=batch_size, eos_token_ids=eos, pad_token_id=pad,
                        body=body, selector=selector, component=component):
                    ledger.append(record)
                single_entries = []
            elif kind == 'gsm8k' and batch_size > 1:
                from coretrace.eval.batched_gsm8k import evaluate_gsm8k_batches
                pending = [e for e in entries if method['name'] + ':' + e['id'] not in ledger.rows]
                for record in evaluate_gsm8k_batches(
                        model, tokenizer, pending, method_name=method['name'],
                        batch_size=batch_size, eos_token_ids=eos, pad_token_id=pad,
                        body=body, selector=selector, component=component):
                    ledger.append(record)
                single_entries = []
            else:
                single_entries = entries
            for entry in single_entries:
                if method['name'] + ':' + entry['id'] in ledger.rows:
                    continue
                inference_started = time.monotonic()
                selected, selection = selector.select(entry, body=body, component=component) if selector else (entry, dict(chosen=None, address_prefills=0, graph=None))
                captured = {}
                handle = None
                if kind == 'mmlu':

                    def hook(module, args, kwargs, result):
                        if captured:
                            return
                        logits = result.logits[0, -1].float()
                        z = torch.logsumexp(logits, dim=-1)
                        captured.update(label_logprobs={c: float(logits[entry['label_token_ids'][c][0]] - z) for c in 'ABCD'}, raw_prefill_argmax_token_id=int(logits.argmax()))
                    handle = model.register_forward_hook(hook, with_kwargs=True)
                try:
                    result = greedy_answer(model, tokenizer, selected, eos_token_ids=eos, pad_token_id=pad, max_new_tokens=512 if kind == 'gsm8k' else 32, session=body.session(selected) if body else None)
                finally:
                    if handle is not None:
                        handle.remove()
                record = dict(result, total_inference_seconds=time.monotonic()-inference_started, id=entry['id'], source_id=entry['source_id'], query=entry['query'], method=method['name'], selection={k: v for k, v in selection.items() if k != 'prompt'})
                for key in ['cluster_id', 'split_cluster_id', 'subject']:
                    if key in entry:
                        record[key] = entry[key]
                if kind == 'mmlu':
                    if result['generated_token_ids'][0] != captured['raw_prefill_argmax_token_id']:
                        raise ValueError('Native output differs from same-prefill raw argmax')
                    text = tokenizer.decode(result['generated_token_ids'], skip_special_tokens=True).strip()
                    native = text if result['eos_complete'] and text in 'ABCD' and (len(text) == 1) else None
                    label = max('ABCD', key=lambda c: captured['label_logprobs'][c])
                    record.update(captured, correct=bool(native == entry['gold']), native_prediction=native, logprob_prediction=label, logprob_correct=bool(label == entry['gold']), format_failure=native is None)
                elif kind == 'gsm8k':
                    metrics = score_math(result['answer'], entry['gold_numeric'], generated_token_count=result['generated_tokens'], eos_complete=result['eos_complete'])
                    record.update(metrics)
                else:
                    metrics = score_answer(result['answer'], entry['gold_aliases'])
                    record.update(correct=bool(result['eos_complete'] and metrics['em']), text_alias_correct=bool(metrics['em']), text_f1=metrics['f1'])
                ledger.append(record)
        if body:
            restores[method['name']] = body.restore_report
    ledger.finish(restore_reports=restores)
    summary = summarize(output, seed=config['seed'])
    (Path(output) / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', required=True)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--plan', action='store_true')
    mode.add_argument('--run', action='store_true')
    a = p.parse_args()
    cfgpath = Path(a.config).resolve()
    base = cfgpath.parent
    config = json.loads(cfgpath.read_text())
    if 'batch_size' not in config:
        defaults = json.loads((ROOT / 'configs/experiments.json').read_text())
        config['batch_size'] = defaults.get('mmlu_batch_size', 1) if config['dataset']['kind'] == 'mmlu' else 1
    rows, planned = plan(config, base)
    if not a.run:
        print(json.dumps(planned, indent=2))
        return
    import torch
    from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
    model_path = resolve(base, config['model']['path'])
    nativeconfig = AutoConfig.from_pretrained(model_path, local_files_only=True)
    if nativeconfig.model_type != config['model']['family']:
        raise ValueError('Native model family mismatch')
    with torch.device('meta'):
        probe = AutoModelForCausalLM.from_config(nativeconfig, attn_implementation='eager')
    count = sum((p.numel() for p in probe.parameters()))
    del probe
    if count > 14000000000:
        raise ValueError('Models above14B are prohibited')
    dtype = getattr(torch, config['model'].get('dtype', 'bfloat16'))
    model = AutoModelForCausalLM.from_pretrained(model_path, local_files_only=True, torch_dtype=dtype, attn_implementation='eager').to(config['model'].get('device', 'cuda'))
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    identity = dict(model_path=str(model_path), model_type=nativeconfig.model_type, native_parameters=count, native_dtype=str(dtype))
    provenance = dict(model_identity=identity, dataset_identity=planned['dataset_identity'], dataset_version=planned['dataset_version'], seed=config['seed'], config=config, metrics=dict(core='EOS-gated official alias EM; text F1 secondary', hotpot='EOS-gated official alias EM', mmlu='Strict complete-letter EOS; same-prefill ABCD logprob accuracy', gsm8k='Final-line Decimal numeric correctness, no EOS gate'), generation=dict(do_sample=False, num_beams=1, max_new_tokens=512 if config['dataset']['kind'] == 'gsm8k' else 32))
    torch.manual_seed(config['seed'])
    result = evaluate_loaded(model, tokenizer, rows, config, base, resolve(base, config['output']), provenance)
    print(json.dumps(result, indent=2))
if __name__ == '__main__':
    from coretrace.stage_lock import run_stage
    run_stage(main, 'manifest.json')
