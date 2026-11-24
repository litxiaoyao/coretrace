"""Fixed privileged paragraph-access causal assessment; no deployed support oracle.

Native contexts stay unchanged. Heads and per-head tau come exclusively from a
frozen discovery selection. Four fixed arms retain every composed test source.
"""
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from coretrace.data.frozen_loader import FrozenDataset
from coretrace.eval.ledgers import EvaluationLedger
from coretrace.eval.summarize import summarize
ARMS = ('native', 'oracle_second_paragraph', 'oracle_first_paragraph', 'lengthmatched_other_paragraph')

def attach_addresses(entry, source):
    titles = [p['title'] for p in entry['paragraphs']]
    result = dict(entry)
    for role in ['first', 'second']:
        title = source['edges'][role + '_target']['title']
        matches = [i for i, t in enumerate(titles) if t == title]
        if len(matches) != 1:
            raise ValueError(f"{entry['source_id']}: {role} source title {title!r} requires one exact original paragraph")
        result[role + '_paragraph'] = matches[0]
    return result

def other_paragraph(entry):
    """Input-only nearest token length to bridge, excluding both source addresses."""
    paragraphs = entry['paragraphs']
    target = len(paragraphs[entry['second_paragraph']]['keys'])
    excluded = {entry['first_paragraph'], entry['second_paragraph']}
    candidates = [i for i in range(len(paragraphs)) if i not in excluded]
    return min(candidates, key=lambda i: (abs(len(paragraphs[i]['keys']) - target), paragraphs[i]['title'], i)) if candidates else None

def validate_budget(budget, freeze):
    if budget.get('status') != 'DISCOVERY_ONLY_HEAD_SELECTION_FROZEN' or budget.get('test_predictions_used') is not False:
        raise ValueError('A frozen discovery-only head/tau selection is required')
    if budget.get('dataset_version') != freeze:
        raise ValueError('Discovery budget/dataset freeze mismatch')
    maps = budget['head_map']
    taus = budget['budgets']
    if not maps:
        raise ValueError('Nonempty fixed head map required')
    for layer, heads in maps.items():
        if not heads or len(set(heads)) != len(heads):
            raise ValueError('Unique selected query heads required')
        for head in heads:
            tau = taus[str(layer)][str(head)]
            if not 0 <= tau <= 1:
                raise ValueError('Fixed finite per-head tau in [0,1] required')
    return (maps, taus)

def run_loaded(model, tokenizer, entries, sources, budget, output, provenance, *, family, eos_token_ids):
    import torch
    from coretrace.data.tokenization import tokenize_prompt
    from coretrace.mechanisms.paragraph_attention import NativeParagraphBudget
    from coretrace.eval.inference import greedy_answer
    from coretrace.eval.answer_metrics import score_answer
    maps, taus = validate_budget(budget, provenance['dataset_version'])
    model.eval().requires_grad_(False)
    prepared = [attach_addresses(dict(e, **tokenize_prompt(tokenizer, e['prompt'], family=family)), sources[e['source_id']]) for e in entries]
    ledger = EvaluationLedger(output, provenance=provenance, entry_ids=[e['id'] for e in prepared], methods=list(ARMS))
    pad = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
    for entry in prepared:
        addresses = {'native': None, 'oracle_second_paragraph': entry['second_paragraph'], 'oracle_first_paragraph': entry['first_paragraph'], 'lengthmatched_other_paragraph': other_paragraph(entry)}
        for method in ARMS:
            job = method + ':' + entry['id']
            if job in ledger.rows:
                continue
            address = addresses[method]
            noop = method == 'lengthmatched_other_paragraph' and address is None
            session = None if address is None else NativeParagraphBudget(model, dict(entry, second_source_keys=entry['paragraphs'][address]['keys']), maps, taus)
            result = greedy_answer(model, tokenizer, entry, eos_token_ids=eos_token_ids, pad_token_id=pad, session=session)
            if noop and result['generated_token_ids'] != ledger.rows['native:' + entry['id']]['generated_token_ids']:
                raise ValueError('No-other no-op must preserve full native IDs')
            metric = score_answer(result['answer'], entry['gold_aliases'])
            record = dict(result, id=entry['id'], source_id=entry['source_id'], query='composed', method=method, correct=bool(result['eos_complete'] and metric['em']), text_alias_correct=bool(metric['em']), text_f1=metric['f1'], original_context_unchanged=True, privileged_diagnostic_address=True, source_paragraph=address, source_title=None if address is None else entry['paragraphs'][address]['title'], source_keys=[] if address is None else entry['paragraphs'][address]['keys'], no_valid_other_noop=noop, budget_events=[] if session is None else session.events)
            for key in ['cluster_id', 'split_cluster_id']:
                if key in entry:
                    record[key] = entry[key]
            ledger.append(record)
    ledger.finish(restore_reports=dict(readonly_intervention=True))
    summary = summarize(output, seed=provenance['seed'])
    summary.update(arms=list(ARMS), interpretation='Privileged diagnostic source addressing, not deployed repair; all arms use the same discovery-frozen per-head tau.', no_other_control_noops=sum((r['no_valid_other_noop'] for r in ledger.rows.values())))
    (Path(output) / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', required=True)
    p.add_argument('--budget', help='Override discovery SELECTION_FROZEN path, relative to config')
    p.add_argument('--split', choices=['discovery', 'train', 'test'], default='test')
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--plan', action='store_true')
    mode.add_argument('--run', action='store_true')
    a = p.parse_args()
    cp = Path(a.config).resolve()
    base = cp.parent
    config = json.loads(cp.read_text())

    def path(value):
        item = Path(value).expanduser()
        return item.resolve() if item.is_absolute() else (base / item).resolve()
    data = FrozenDataset(path(config['dataset']))
    budgetpath = path(a.budget or config['budget'])
    budget = json.loads(budgetpath.read_text())
    maps, taus = validate_budget(budget, data.lock['dataset_version'])
    entries = data.queries(a.split, 'composed')
    aliases = {x['source_id']: x for x in data.aliases(a.split)}
    for e in entries:
        e['gold_aliases'] = aliases[e['source_id']]['queries']['composed']['golds']
    planned = dict(status='PLAN_ONLY', split=a.split, composed_sources=len(entries), expected_generations=4 * len(entries), arms=list(ARMS), dataset_version=data.lock['dataset_version'], selected_heads=sum(map(len, maps.values())), model_weights_loaded=False, budget_fit_on_test=False, other_rule='Exclude first/second paragraph, minimize absolute key_count difference to second; title then original index tie. No valid other: explicit no-op, keep denominator.')
    if not a.run:
        print(json.dumps(planned, indent=2))
        return
    import torch
    from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
    nativepath = path(config['model']['path'])
    native = AutoConfig.from_pretrained(nativepath, local_files_only=True)
    if native.model_type != config['model']['family']:
        raise ValueError('Native model family mismatch')
    with torch.device('meta'):
        probe = AutoModelForCausalLM.from_config(native, attn_implementation='eager')
    count = sum((p.numel() for p in probe.parameters()))
    del probe
    if count > 14000000000:
        raise ValueError('Models above14B prohibited')
    model = AutoModelForCausalLM.from_pretrained(nativepath, local_files_only=True, torch_dtype=getattr(torch, config['model'].get('dtype', 'bfloat16')), attn_implementation='eager').to(config['model'].get('device', 'cuda')).eval().requires_grad_(False)
    tok = AutoTokenizer.from_pretrained(nativepath, local_files_only=True)
    eos = config.get('eos_token_ids', model.generation_config.eos_token_id or tok.eos_token_id)
    eos = [eos] if isinstance(eos, int) else eos
    provenance = dict(seed=config.get('seed', 42), dataset_version=data.lock['dataset_version'], source_split=a.split, head_map=maps, per_head_tau=taus, model_identity=dict(path=str(nativepath), model_type=native.model_type, native_parameters=count), metric='EOS-gated official aliases EM; text F1 secondary; complete denominator', generation=dict(do_sample=False, num_beams=1, max_new_tokens=32), privileged_diagnostic_addresses=True, test_tau_fit=False)
    sources = {e['source_id']: e for e in data.sources(a.split)}
    result = run_loaded(model, tok, entries, sources, budget, path(config['output']), provenance, family=native.model_type, eos_token_ids=eos)
    print(json.dumps(result, indent=2))
if __name__ == '__main__':
    from coretrace.stage_lock import run_stage
    run_stage(main, 'manifest.json')
