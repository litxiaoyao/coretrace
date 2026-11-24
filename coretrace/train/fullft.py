"""Original default true FullFT baseline, full-parameter CPU-state AdamW.

No adapters, hyperparameter tuning, frozen prefix, optimizer checkpoint, or base
restore. The actual trained model remains in caller memory after completion.
"""
import gc
import hashlib
import json
import math
import os
import shutil
import time
from pathlib import Path
from .selected_heads import DEFAULT_RECIPE

def answer_ce(model, entry):
    import torch
    prompt = entry['prompt_ids']
    target = entry['target_ids']
    ids = torch.tensor([prompt + target[:-1]], device=next(model.parameters()).device)
    logits = model(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False, logits_to_keep=len(target)).logits
    if logits.shape[1] != len(target):
        raise ValueError('Answer/EOS suffix alignment')
    return torch.nn.functional.cross_entropy(logits[0].float(), torch.tensor(target, device=ids.device), reduction='mean')

def _memory():
    values = {}
    with open('/proc/meminfo') as stream:
        for line in stream:
            key, value = line.split(':', 1)
            values[key] = int(value.split()[0]) * 1024
    with open('/proc/self/statm') as stream:
        rss = int(stream.read().split()[1]) * os.sysconf('SC_PAGE_SIZE')
    return (values['MemTotal'], values['MemAvailable'], rss)

def resource_plan(model, output, *, cpu_memory_budget_bytes=None, disk_reserve_bytes=2 << 30):
    """Conservative state/temporary estimate and actual disk preflight; no allocation."""
    params = list(model.parameters())
    count = sum((p.numel() for p in params))
    if count > 14000000000:
        raise ValueError('Models above14B not allowed')
    total, available, rss = _memory()
    limit = min(total // 2, cpu_memory_budget_bytes or total // 2)
    extra = 16 * count + 12 * max((p.numel() for p in params)) + (3 << 30)
    if rss + extra > limit:
        raise MemoryError('Estimated FullFT CPU peak exceeds half-server/caller budget')
    if extra > available - max(2 << 30, total // 20):
        raise MemoryError('Insufficient available CPU memory plus server reserve')
    out = Path(output).expanduser().resolve()
    ancestor = out
    while not ancestor.exists():
        ancestor = ancestor.parent
    free = shutil.disk_usage(ancestor).free
    required = 2 * count + (64 << 20) + disk_reserve_bytes
    if free < required:
        raise OSError('Insufficient disk for single final BF16 checkpoint plus reserve')
    return dict(native_parameters=count, existing_process_rss_bytes=rss, estimated_extra_CPU_bytes=extra, CPU_memory_limit_bytes=limit, server_memory_bytes=total, available_memory_bytes=available, disk_free_bytes=free, final_BF16_weight_bytes=2 * count, disk_required_with_reserve_bytes=required)

def train_fullft(model, tokenizer, entries, output, *, seed, dataset_version, model_identity, cpu_memory_budget_bytes=None, disk_reserve_bytes=2 << 30, before_each=None, after_microbatch=None, after_step=None):
    import torch
    from ..models.cpu_adamw import CPUOffloadedFullAdamW
    if not entries or len({e['source_id'] for e in entries}) != len(entries):
        raise ValueError('Nonempty unique composed sources required')
    if any((p.dtype != torch.bfloat16 for p in model.parameters())):
        raise ValueError('Original FullFT baseline uses native BF16 parameters')
    if getattr(model, '_headslice_qkvo_merged_owner', None) is not None:
        raise ValueError('True FullFT requires an unmodified native base')
    plan = resource_plan(model, output, cpu_memory_budget_bytes=cpu_memory_budget_bytes, disk_reserve_bytes=disk_reserve_bytes)
    out = Path(output)
    out.mkdir(exist_ok=False, parents=True)
    h = dict(DEFAULT_RECIPE, seed=int(seed))
    accum = h['gradient_accumulation']
    order = sorted(entries, key=lambda e: (hashlib.sha256((str(seed) + ':' + e['source_id']).encode()).hexdigest(), e['source_id']))
    torch.manual_seed(seed)
    model.requires_grad_(True)
    model.train()
    model.config.use_cache = False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    optimizer = None
    micro = 0
    updates = 0
    started = time.monotonic()
    group_losses = []
    names = set(dict(model.named_parameters()))
    trace = out / 'microbatch_trace.jsonl'
    steps = out / 'optimizer_trace.jsonl'

    def guard():
        total, available, rss = _memory()
        if rss > plan['CPU_memory_limit_bytes'] or available < max(2 << 30, total // 20):
            raise MemoryError('FullFT process/system memory pressure limit reached')
    try:
        if before_each:
            before_each(dict(order[0], phase='INITIALIZE_FULL_PARAMETER_CPU_ADAM'), -1)
        optimizer = CPUOffloadedFullAdamW(model, lr=h['lr'], betas=tuple(h['betas']), eps=h['eps'], weight_decay=h['weight_decay'], max_grad_norm=h['grad_clip_max_norm'], gpu_accumulation='auto')
        with trace.open('x') as tf, steps.open('x') as sf:
            for index, entry in enumerate(order):
                guard()
                if before_each:
                    before_each(dict(entry, phase='TRUE_FULL_PARAMETER_FORWARD_BACKWARD'), index)
                tick = time.monotonic()
                loss = answer_ce(model, entry)
                value = float(loss.detach())
                forward = time.monotonic() - tick
                tick = time.monotonic()
                optimizer.backward(loss)
                backward = time.monotonic() - tick
                del loss
                micro += 1
                group_losses.append(value)
                if set(optimizer.grads) != names:
                    raise ValueError('Every parameter must receive a FullFT gradient')
                record = dict(index=index, source_id=entry['source_id'], loss=value, forward_seconds=forward, backward_seconds=backward, accumulated_microbatches=optimizer.microbatches, gradient_parameter_tensors=len(optimizer.grads), all_gradients_CPU_FP32=all((g.device.type == 'cpu' and g.dtype == torch.float32 for g in optimizer.grads.values())), model_parameter_grads_released=all((p.grad is None for p in model.parameters())))
                record['gradient_accumulation_device'] = 'cuda' if optimizer.gpu_accumulation else 'cpu'
                record['all_gradients_FP32'] = all(g.dtype == torch.float32 for g in optimizer.grads.values())
                tf.write(json.dumps(record) + '\n')
                tf.flush()
                if after_microbatch:
                    after_microbatch(record)
                if optimizer.microbatches == accum or index == len(order) - 1:
                    tick = time.monotonic()
                    report = optimizer.step()
                    updates += 1
                    step = dict(optimizer_step=updates, completed_sources=micro, mean_group_source_CE=sum(group_losses) / len(group_losses), actual_group_sources=len(group_losses), CPU_Adam_seconds=time.monotonic() - tick, **report)
                    group_losses = []
                    if report['updated_parameter_tensors'] != len(names):
                        raise ValueError('FullFT update omitted parameters')
                    sf.write(json.dumps(step) + '\n')
                    sf.flush()
                    if after_step:
                        after_step(step)
        if micro != len(order) or updates != math.ceil(len(order) / accum):
            raise ValueError('Incomplete one-epoch FullFT')
        optimizer.close()
        optimizer = None
        gc.collect()
        model.gradient_checkpointing_disable()
        model.eval()
        model.config.use_cache = True
        model.requires_grad_(False)
        from .memory_admission import wait_for_checkpoint_space
        wait_for_checkpoint_space(Path(__file__).resolve().parents[2] / 'outputs/runtime',
                                  out, sum(p.numel() for p in model.parameters()), disk_reserve_bytes)
        if before_each:
            before_each(dict(order[-1], phase='SAVE_UNIQUE_FINAL_BF16_MODEL'), len(order))
        final = out / 'final_model'
        model.save_pretrained(final, safe_serialization=True, max_shard_size='2GB')
        tokenizer.save_pretrained(final)
        files = {p.name: dict(bytes=p.stat().st_size) for p in sorted(final.iterdir()) if p.is_file()}
        result = dict(status='COMPLETE_TRUE_FULL_PARAMETER_TRAINING', actual_sources=micro, actual_steps=updates, all_parameter_elements=sum((p.numel() for p in model.parameters())), all_unique_parameter_tensors=len(names), all_parameters_trainable_during_science=True, frozen_prefix=False, adapter=False, dataset_version=dataset_version, model_identity=model_identity, hyperparameters=h, source_order='Original default seed:sourceID SHA order', training_source_ids=[e['source_id'] for e in order], training_query_ids=[e.get('id') for e in order], final_model_directory='final_model', final_model_files=files, CPU_optimizer_states_saved=False, CPU_optimizer_objects_released=True, original_resource_plan=plan, model_resident_state='Actual trained BF16 full model; no native-base restoration', seconds=time.monotonic() - started)
        (out / 'training.json').write_text(json.dumps(result, indent=2) + '\n')
        return result
    except BaseException as exc:
        (out / 'failed_training.json').write_text(json.dumps(dict(status='FAILED_INCOMPLETE_TRUE_FULL_PARAMETER_TRAINING', error=repr(exc), actual_sources=micro, actual_steps=updates), indent=2) + '\n')
        raise
    finally:
        if optimizer is not None:
            optimizer.close()
        for parameter in model.parameters():
            parameter.grad = None
        model.gradient_checkpointing_disable()
        model.eval()
        model.config.use_cache = True
        gc.collect()
