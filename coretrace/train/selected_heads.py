"""Original selected full-rank QKVO answer-CE recipe, architecture resolved.

One pass in the supplied frozen source order; model.eval(), zero FP32 slice deltas,
AdamW default recipe. No base/optimizer checkpoint and no import-time model load.
"""
import gc
import hashlib
import importlib
import json
import math
import time
from pathlib import Path
DEFAULT_RECIPE = dict(lr=2e-05, betas=[0.9, 0.999], eps=1e-08, weight_decay=0.0, grad_clip_max_norm=1.0, gradient_accumulation=8, epochs=1)

def answer_ce_checkpointed(model, entry):
    """Exact answer-only mean TF cross-entropy with native decoder checkpointing."""
    import torch
    from torch.utils.checkpoint import checkpoint
    backend = importlib.import_module(type(model).__module__)
    make_mask = getattr(backend, 'create_causal_mask', None)
    if make_mask is None:
        from transformers.masking_utils import create_causal_mask
        make_mask = create_causal_mask
    prompt = entry['prompt_ids']
    target = entry['target_ids']
    if not prompt or not target:
        raise ValueError('Nonempty prompt and answer+EOS target required')
    ids = torch.tensor([prompt + target[:-1]], device=next(model.parameters()).device)
    length = ids.shape[1]
    hidden = model.model.embed_tokens(ids)
    positions = torch.arange(length, device=ids.device)
    position_ids = positions[None, :]
    mask = make_mask(config=model.config, input_embeds=hidden, attention_mask=torch.ones_like(ids), cache_position=positions, past_key_values=None, position_ids=position_ids)
    rope = model.model.rotary_emb(hidden, position_ids)
    for layer in model.model.layers:

        def block(h, decoder=layer):
            result = decoder(h, attention_mask=mask, position_ids=position_ids, past_key_values=None, use_cache=False, cache_position=positions, position_embeddings=rope)
            return result[0] if isinstance(result, (tuple, list)) else result
        hidden = checkpoint(block, hidden, use_reentrant=False, preserve_rng_state=True)
    hidden = model.model.norm(hidden)
    logits = model.lm_head(hidden[:, len(prompt) - 1:len(prompt) + len(target) - 1]).float()
    return torch.nn.functional.cross_entropy(logits[0], torch.tensor(target, device=ids.device))

def prepare_entries(queries, tokenizer, *, family):
    """Retokenize unchanged composed prompts and append native EOS to gold answer."""
    from ..data.tokenization import tokenize_prompt
    result = []
    for query in queries:
        if query['query'] != 'composed':
            raise ValueError('Training uses composed queries only')
        entry = dict(query, **tokenize_prompt(tokenizer, query['prompt'], family=family))
        entry['target_ids'] = tokenizer.encode(query['gold'], add_special_tokens=False) + [tokenizer.eos_token_id]
        if entry['target_ids'][-1] is None:
            raise ValueError('Native tokenizer EOS is required')
        result.append(entry)
    if len({entry['source_id'] for entry in result}) != len(result):
        raise ValueError('Duplicate composed training sources')
    return result

def train_selected_heads(model, entries, head_map, output, *, seed, dataset_version, model_identity, boundary=None, progress=None):
    """Train one original-recipe epoch; save only slices and auditable metadata.

    Callbacks support caller-owned resource scheduling, without importing a service.
    A partial last accumulation group divides by its actual size, as in the pilot.
    """
    import torch
    from safetensors.torch import save_file
    from ..models.head_slices import HeadSliceQKVO
    if not entries or len({e['source_id'] for e in entries}) != len(entries):
        raise ValueError('Nonempty unique-source entries required')
    if sum((p.numel() for p in model.parameters())) > 14000000000:
        raise ValueError('Models above 14B are outside the experiment protocol')
    if not isinstance(model_identity, dict) or not model_identity:
        raise ValueError('Explicit model identity dictionary required')
    if getattr(model, '_headslice_qkvo_merged_owner', None) is not None:
        raise ValueError('Native unmerged base required')
    out = Path(output)
    out.mkdir(parents=True, exist_ok=False)
    recipe = dict(DEFAULT_RECIPE, seed=int(seed))
    torch.manual_seed(int(seed))
    model.eval().requires_grad_(False)
    adapter = None
    optimizer = None
    params = []
    steps = 0
    micro = 0
    started = time.monotonic()
    devices = {}
    try:
        adapter = HeadSliceQKVO(model, head_map)
        adapter.install()
        params = list(adapter.parameters())
        if not all((p.dtype == torch.float32 for p in params)):
            raise ValueError('FP32 independent deltas required')
        optimizer = torch.optim.AdamW(params, lr=recipe['lr'], betas=tuple(recipe['betas']), eps=recipe['eps'], weight_decay=recipe['weight_decay'], foreach=False)
        optimizer.zero_grad(set_to_none=True)
        with (out / 'microbatch_trace.jsonl').open('x') as trace:
            for start in range(0, len(entries), recipe['gradient_accumulation']):
                group = entries[start:start + recipe['gradient_accumulation']]
                for index, entry in enumerate(group):
                    if boundary:
                        boundary()
                    loss = answer_ce_checkpointed(model, entry)
                    value = float(loss.detach())
                    if not torch.isfinite(loss):
                        raise ValueError('Nonfinite answer loss')
                    (loss / len(group)).backward()
                    del loss
                    micro += 1
                    row = dict(index=micro - 1, source_id=entry['source_id'], answer_loss=value, student_forward_calls=1, student_backward_calls=1)
                    if index == len(group) - 1:
                        if not all((p.grad is not None and torch.isfinite(p.grad).all() for p in params)):
                            raise ValueError('Missing/nonfinite selected-slice gradient')
                        norm = torch.nn.utils.clip_grad_norm_(params, recipe['grad_clip_max_norm'], error_if_nonfinite=True)
                        optimizer.step()
                        optimizer.zero_grad(set_to_none=True)
                        steps += 1
                        row.update(optimizer_step=steps, gradient_norm=float(norm))
                    trace.write(json.dumps(row) + '\n')
                    trace.flush()
                    if progress:
                        progress(row)
        if micro != len(entries) or steps != math.ceil(len(entries) / recipe['gradient_accumulation']):
            raise ValueError('Actual update/source count differs from recipe')
        for state in optimizer.state.values():
            for name, tensor in state.items():
                if torch.is_tensor(tensor):
                    key = name + ':' + str(tensor.device)
                    devices[key] = devices.get(key, 0) + tensor.numel()
        delta = sum((float(p.detach().double().square().sum()) for p in params)) ** 0.5
        if not delta > 0:
            raise ValueError('Training did not change slices')
        weights = out / 'slices_final.safetensors'
        save_file({k: v.detach().cpu().contiguous().clone() for k, v in adapter.state_dict().items()}, str(weights))
        sources = [e['source_id'] for e in entries]
        metadata = dict(status='COMPLETE_SELECTED_HEAD_TRAINING', head_map=adapter.head_map, actual_steps=steps, actual_sources=micro, dataset_version=dataset_version, model_identity=model_identity, training_source_ids=sources, training_query_ids=[e.get('id') for e in entries], hyperparameters=recipe, parameter_count=sum((p.numel() for p in params)), adapter_delta_L2=delta, all_token_QKVO=True, low_rank=False, source_order='Provided frozen split order; no shuffle', model_mode='eval', optimizer='Actual torch.optim.AdamW; FP32 delta parameters colocated with native base', optimizer_state_tensor_elements_by_field_and_device=devices, optimizer_states_saved=False, full_checkpoint_saved=False, seconds=time.monotonic() - started)
    finally:
        if adapter is not None:
            adapter.remove()
        del optimizer, params, adapter
        gc.collect()
        restore = dict(slices_removed=True)
    metadata['native_restore'] = restore
    (out / 'training.json').write_text(json.dumps(metadata, indent=2) + '\n')
    return metadata
