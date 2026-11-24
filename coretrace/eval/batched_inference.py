"""Shared optional left-padded native greedy generation, with no input truncation.

Per-example outputs end at the first actual EOS, including the EOS itself;
post-completion batch padding is never counted as a generated answer token.
"""
import time
from contextlib import nullcontext
import torch
from ..mechanisms.paragraph_attention import NativeEagerHeadChunks


def greedy_batch(model, tokenizer, entries, *, eos_token_ids,
                 pad_token_id, body=None, max_new_tokens=32, chunk_heads=4,
                 capture_labels=False):
    """Native greedy generation shared by optional QA and MMLU batching."""
    if model.training or not entries:
        raise ValueError('Nonempty batch and eval model required')
    if type(pad_token_id) is not int or not eos_token_ids:
        raise ValueError('Native pad and EOS IDs required')
    for entry in entries:
        if capture_labels:
            labels = entry['label_token_ids']
            if set(labels) != set('ABCD') or any(len(v) != 1 for v in labels.values()) or len({v[0] for v in labels.values()}) != 4:
                raise ValueError('ABCD must each be one distinct native token')
        if not entry['prompt_ids']:
            raise ValueError('Empty native prompt')
    lengths = [len(e['prompt_ids']) for e in entries]
    width = max(lengths)
    device = next(model.parameters()).device
    ids = torch.full((len(entries), width), pad_token_id, device=device, dtype=torch.long)
    mask = torch.zeros_like(ids)
    for i, entry in enumerate(entries):
        ids[i, width-lengths[i]:] = torch.tensor(entry['prompt_ids'], device=device)
        mask[i, width-lengths[i]:] = 1
    captured = {}

    def hook(module, args, kwargs, result):
        if captured:
            return
        logits = result.logits[:, -1].float()
        normal = torch.logsumexp(logits, dim=-1, keepdim=True)
        label_ids = torch.tensor([[e['label_token_ids'][c][0] for c in 'ABCD'] for e in entries], device=logits.device)
        captured['scores'] = (logits.gather(1, label_ids)-normal).tolist()
        captured['argmax'] = logits.argmax(-1).tolist()

    handle = model.register_forward_hook(hook, with_kwargs=True) if capture_labels else None
    tick = time.monotonic()
    try:
        with torch.inference_mode(), NativeEagerHeadChunks(model, chunk_heads), body.batch_session(entries, padded_length=width) if body else nullcontext():
            generated = model.generate(
                input_ids=ids, attention_mask=mask, do_sample=False, num_beams=1,
                max_new_tokens=max_new_tokens, use_cache=True, logits_to_keep=1,
                eos_token_id=list(eos_token_ids), pad_token_id=pad_token_id,
                temperature=None, top_p=None)
    finally:
        if handle is not None:
            handle.remove()
    if not torch.equal(generated[:, :width], ids):
        raise ValueError('Generation changed the padded input')
    sequences = generated[:, width:].tolist()
    elapsed = time.monotonic()-tick
    if capture_labels and len(captured.get('scores', [])) != len(entries):
        raise ValueError('Missing same-prefill label scores')
    eos = set(eos_token_ids)
    results = []
    for i, tokens in enumerate(sequences):
        first_eos = next((j for j, tok in enumerate(tokens) if tok in eos), None)
        if first_eos is not None:
            tokens = tokens[:first_eos+1]
        complete = first_eos is not None
        if not tokens or (capture_labels and tokens[0] != captured['argmax'][i]):
            raise ValueError('Native first output differs from same-prefill argmax')
        answer = tokenizer.decode(tokens[:-1] if complete else tokens,
                                  skip_special_tokens=False,
                                  clean_up_tokenization_spaces=False).strip()
        record = dict(
            answer=answer, generated_token_ids=tokens, eos_complete=complete,
            input_tokens=lengths[i], generated_tokens=len(tokens),
            seconds=elapsed/len(entries), batch_size=len(entries),
            batch_wall_seconds=elapsed, padded_input_tokens=width,
            batch_processed_decode_steps=len(sequences[i]))
        if capture_labels:
            record.update(label_logprobs=dict(zip('ABCD', captured['scores'][i])),
                          raw_prefill_argmax_token_id=captured['argmax'][i])
        results.append(record)
    return results

