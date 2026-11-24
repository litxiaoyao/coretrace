"""Default true FullFT baseline: plan by default; --run is explicit."""
import argparse, json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coretrace.data.frozen_loader import FrozenDataset
from coretrace.train.selected_heads import DEFAULT_RECIPE, prepare_entries

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset', required=True)
    p.add_argument('--model', required=True)
    p.add_argument('--family', required=True, choices=['qwen3', 'llama'])
    p.add_argument('--seed', type=int, choices=[42, 43, 44], required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--device', default='cuda')
    p.add_argument('--cpu-memory-budget-gib', type=float)
    p.add_argument('--disk-reserve-gib', type=float, default=2)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--plan', action='store_true')
    mode.add_argument('--run', action='store_true')
    a = p.parse_args()
    data = FrozenDataset(a.dataset)
    queries = data.queries('train', 'composed')
    plan = dict(status='PLAN_ONLY', sources=len(queries), updates=math.ceil(len(queries) / 8), seed=a.seed, recipe=DEFAULT_RECIPE, dataset_version=data.lock['dataset_version'], model=a.model, family=a.family, source_order='Original seed:sourceID SHA order', full_parameter=True, CPU_optimizer_states_saved=False, final_checkpoint='One BF16 HuggingFace checkpoint only', model_weights_loaded=False)
    if not a.run:
        print(json.dumps(plan, indent=2))
        return
    import torch
    from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
    from coretrace.train.fullft import train_fullft, resource_plan
    config = AutoConfig.from_pretrained(a.model, local_files_only=True)
    if config.model_type != a.family:
        raise ValueError('Model family mismatch')
    with torch.device('meta'):
        probe = AutoModelForCausalLM.from_config(config, attn_implementation='eager')
    if sum((p.numel() for p in probe.parameters())) > 14000000000:
        raise ValueError('Model exceeds14B')
    del probe
    model = AutoModelForCausalLM.from_pretrained(a.model, local_files_only=True, torch_dtype=torch.bfloat16, attn_implementation='eager').to(a.device)
    tok = AutoTokenizer.from_pretrained(a.model, local_files_only=True)
    entries = prepare_entries(queries, tok, family=a.family)
    identity = dict(model=a.model, model_type=config.model_type, native_parameters=sum((p.numel() for p in model.parameters())), native_dtype='torch.bfloat16')
    result = train_fullft(model, tok, entries, a.output, seed=a.seed, dataset_version=data.lock['dataset_version'], model_identity=identity, cpu_memory_budget_bytes=None if a.cpu_memory_budget_gib is None else int(a.cpu_memory_budget_gib * (1 << 30)), disk_reserve_bytes=int(a.disk_reserve_gib * (1 << 30)))
    print(json.dumps({k: result[k] for k in ['status', 'actual_sources', 'actual_steps']}, indent=2))
def serialized_main():
    if '--run' not in sys.argv:
        return main()
    # Large runs retain the legacy mutex, including an already-running 8B job.
    # A 4B run can overlap one 8B run when aggregate host memory fits half-server.
    import fcntl
    import torch
    from transformers import AutoConfig, AutoModelForCausalLM
    import importlib
    from coretrace.train import memory_admission
    importlib.reload(memory_admission)
    admit, wait_status = memory_admission.admit, memory_admission.wait_status
    model_path = sys.argv[sys.argv.index('--model') + 1]
    config = AutoConfig.from_pretrained(model_path, local_files_only=True)
    with torch.device('meta'):
        probe = AutoModelForCausalLM.from_config(config, attn_implementation='eager')
    counts = [parameter.numel() for parameter in probe.parameters()]
    count = sum(counts)
    if count > 14_000_000_000:
        raise ValueError('Model exceeds14B')
    extra = 16 * count + 12 * max(counts) + (3 << 30)
    del probe
    runtime = Path(__file__).resolve().parents[1] / 'outputs/runtime'
    lockpath = runtime / ('fullft_small_training.lock' if count <= 5_000_000_000 else 'fullft_training.lock')
    lockpath.parent.mkdir(parents=True, exist_ok=True)
    with lockpath.open('a') as stream:
        print('Waiting for the size-class FullFT slot: ' + lockpath.name, flush=True)
        wait_status(runtime, 'WAITING_SIZE_CLASS_SLOT', lock=str(lockpath))
        fcntl.flock(stream, fcntl.LOCK_EX)
        output = Path(sys.argv[sys.argv.index('--output') + 1])
        reserve = float(sys.argv[sys.argv.index('--disk-reserve-gib') + 1]) if '--disk-reserve-gib' in sys.argv else 2
        memory_admission.wait_for_checkpoint_space(runtime, output, count, int(reserve * (1 << 30)))
        with admit(runtime, extra):
            # Resident executors cache modules. Pick up an already-validated
            # transport implementation only at the boundary of a new training
            # job, never while an optimizer is running.
            import importlib
            import coretrace.models.cpu_adamw as cpu_adamw
            importlib.reload(cpu_adamw)
            import coretrace.train.fullft as fullft
            importlib.reload(fullft)
            return main()

if __name__ == '__main__':
    from coretrace.stage_lock import run_stage
    run_stage(serialized_main, 'training.json')
