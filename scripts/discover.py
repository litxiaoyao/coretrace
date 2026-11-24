"""Frozen discovery100 localization; --plan default, explicit --run for model work."""
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from coretrace.data.frozen_loader import FrozenDataset

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', required=True)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--plan', action='store_true')
    mode.add_argument('--run', action='store_true')
    p.add_argument('--capture-only', action='store_true')
    p.add_argument('--first-source-control', action='store_true')
    a = p.parse_args()
    cfgpath = Path(a.config).resolve()
    base = cfgpath.parent
    config = json.loads(cfgpath.read_text())

    def path(value):
        item = Path(value).expanduser()
        return item.resolve() if item.is_absolute() else (base / item).resolve()
    data = FrozenDataset(path(config['dataset']))
    counts = config.get('candidate_counts', [20, 40, 80])
    planned = dict(status='PLAN_ONLY', source_split='discovery', sources=100, capture_prefills=200, candidate_counts=counts, calibration_generations=0 if a.capture_only else 100 * (1 + len(counts) * (2 if a.first_source_control else 1)), capture_only=a.capture_only, dataset_version=data.lock['dataset_version'], model_weights_loaded=False, test_data_used=False)
    if not a.run:
        print(json.dumps(planned, indent=2))
        return
    import torch
    from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
    from coretrace.mechanisms.localization import discovery_entries, capture_all_heads, rank_access_gap, calibrate_candidates, select_best_n
    modelpath = path(config['model']['path'])
    native = AutoConfig.from_pretrained(modelpath, local_files_only=True)
    if native.model_type != config['model']['family']:
        raise ValueError('Actual model family mismatch')
    with torch.device('meta'):
        probe = AutoModelForCausalLM.from_config(native, attn_implementation='eager')
    parameters = sum((p.numel() for p in probe.parameters()))
    del probe
    if parameters > 14000000000:
        raise ValueError('Models above14B prohibited')
    model = AutoModelForCausalLM.from_pretrained(modelpath, local_files_only=True, torch_dtype=getattr(torch, config['model'].get('dtype', 'bfloat16')), attn_implementation='eager').to(config['model'].get('device', 'cuda')).eval().requires_grad_(False)
    tokenizer = AutoTokenizer.from_pretrained(modelpath, local_files_only=True)
    entries = discovery_entries(data, tokenizer, family=native.model_type)
    out = path(config['output'])
    out.mkdir(parents=True, exist_ok=False)
    capture = out / 'capture200.jsonl'
    captured = capture_all_heads(model, entries, capture)
    ranked = rank_access_gap(map(json.loads, capture.open()), candidate_counts=counts)
    ranking = out / 'ranking.json'
    ranking.write_text(json.dumps(ranked, indent=2) + '\n')
    selection = None
    if not a.capture_only:
        eos = config.get('eos_token_ids', model.generation_config.eos_token_id or tokenizer.eos_token_id)
        eos = [eos] if isinstance(eos, int) else eos
        records = calibrate_candidates(model, tokenizer, entries, ranked['candidate_maps'], out / 'calibration.jsonl', eos_token_ids=eos, first_source_control=a.first_source_control)
        selection = select_best_n(records, ranked['candidate_maps'], expected_source_ids=ranked['source_ids'])
        selection.update(dataset_version=data.lock['dataset_version'])
        (out / 'SELECTION_FROZEN.json').write_text(json.dumps(selection, indent=2) + '\n')
    manifest = dict(status='COMPLETE_DISCOVERY_CAPTURE_ONLY' if a.capture_only else 'COMPLETE_DISCOVERY_LOCALIZATION_AND_CALIBRATION', dataset_version=data.lock['dataset_version'], model_identity=dict(path=str(modelpath), model_type=native.model_type, native_parameters=parameters), capture=captured, readonly_diagnostic=True, privileged_discovery_annotation=True, test_predictions_used=False, seed=config.get('seed', 42), selection=selection)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(dict(status=manifest['status'], output=str(out)), indent=2))
if __name__ == '__main__':
    from coretrace.stage_lock import run_stage
    run_stage(main, 'manifest.json')
