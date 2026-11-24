"""Original-recipe formal selected-head training, explicit --run opt-in.

Without --run this emits a CPU data/config plan and never loads model weights.
"""
import argparse
import json
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coretrace.data.frozen_loader import FrozenDataset
from coretrace.train.selected_heads import DEFAULT_RECIPE, prepare_entries, train_selected_heads

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset', required=True)
    p.add_argument('--model', required=True)
    p.add_argument('--family', required=True, choices=['qwen3', 'llama'])
    p.add_argument('--heads', required=True, help='Frozen JSON head_map or JSON with head_map field')
    p.add_argument('--seed', type=int, choices=[42, 43, 44], required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--device', default='cuda')
    p.add_argument('--dtype', choices=['bfloat16', 'float32'], default='bfloat16')
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--plan', action='store_true', help='Verify frozen data and print plan; default')
    mode.add_argument('--run', action='store_true', help='Actually load native weights and train')
    a = p.parse_args()
    data = FrozenDataset(a.dataset)
    queries = data.queries('train', 'composed')
    heads = json.loads(Path(a.heads).read_text())
    heads = heads.get('head_map', heads)
    if not heads or not all((str(k).isdigit() and isinstance(v, list) and v for k, v in heads.items())):
        raise ValueError('Explicit nonempty selected head map required')
    expected = math.ceil(len(queries) / DEFAULT_RECIPE['gradient_accumulation'])
    plan = dict(status='PLAN_ONLY' if not a.run else 'RUN_REQUESTED', sources=len(queries), updates=expected, epochs=1, seed=a.seed, recipe=DEFAULT_RECIPE, dataset_version=data.lock['dataset_version'], head_map=heads, model=a.model, family=a.family, output=a.output, model_weights_loaded=False, optimizer_states_saved=False, full_checkpoint_saved=False)
    if not a.run:
        print(json.dumps(plan, indent=2))
        return
    import torch
    from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
    config = AutoConfig.from_pretrained(a.model, local_files_only=True)
    if config.model_type != a.family:
        raise ValueError('Native model family mismatch')
    with torch.device('meta'):
        probe = AutoModelForCausalLM.from_config(config, attn_implementation='eager')
    if sum((p.numel() for p in probe.parameters())) > 14000000000:
        raise ValueError('Model exceeds14B; refusing to load its weights')
    del probe
    tok = AutoTokenizer.from_pretrained(a.model, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(a.model, local_files_only=True, torch_dtype=getattr(torch, a.dtype), attn_implementation='eager').to(a.device)
    if sum((p.numel() for p in model.parameters())) > 14000000000:
        raise ValueError('Model exceeds14B')
    identity = dict(model=a.model, model_type=config.model_type, native_parameters=sum((p.numel() for p in model.parameters())), native_dtype=str(next(model.parameters()).dtype), tokenizer_class=type(tok).__name__)
    entries = prepare_entries(queries, tok, family=a.family)
    result = train_selected_heads(model, entries, heads, a.output, seed=a.seed, dataset_version=data.lock['dataset_version'], model_identity=identity)
    print(json.dumps({k: result[k] for k in ['status', 'actual_sources', 'actual_steps']}, indent=2))
if __name__ == '__main__':
    from coretrace.stage_lock import run_stage
    run_stage(main, 'training.json')
