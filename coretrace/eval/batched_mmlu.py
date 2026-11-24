"""Optional MMLU batching with the same native greedy and prefill metrics.

Only the batch geometry changes: native prompts are left-padded and each result
is trimmed at its first actual EOS, including that EOS. No rows are dropped and
ABCD scores come from the same prefill that generates the first output token.
"""
import time


def greedy_mmlu_batch(model, tokenizer, entries, *, eos_token_ids,
                      pad_token_id, body=None, max_new_tokens=32, chunk_heads=4):
    """Retain the MMLU API and capture ABCD on the actual generation prefill."""
    from .batched_inference import greedy_batch
    return greedy_batch(model, tokenizer, entries, eos_token_ids=eos_token_ids,
                        pad_token_id=pad_token_id, body=body,
                        max_new_tokens=max_new_tokens, chunk_heads=chunk_heads,
                        capture_labels=True)


def evaluate_mmlu_batches(model, tokenizer, entries, *, method_name, batch_size,
                          eos_token_ids, pad_token_id, body=None, selector=None,
                          component='no_filter'):
    """Yield EvaluationLedger-compatible rows; callers own resume and completion."""
    if type(batch_size) is not int or batch_size < 1:
        raise ValueError('Positive integer batch size required')
    for lo in range(0, len(entries), batch_size):
        batch = entries[lo:lo+batch_size]
        started = time.monotonic()
        selected, selections = [], []
        for entry in batch:
            item, selection = selector.select(entry, body=body, component=component) if selector else (entry, dict(chosen=None, address_prefills=0, graph=None))
            selected.append(item)
            selections.append(selection)
        results = greedy_mmlu_batch(model, tokenizer, selected, eos_token_ids=eos_token_ids,
                                     pad_token_id=pad_token_id, body=body)
        total = (time.monotonic()-started)/len(batch)
        for entry, selection, result in zip(batch, selections, results):
            text = tokenizer.decode(result['generated_token_ids'], skip_special_tokens=True).strip()
            native = text if result['eos_complete'] and text in 'ABCD' and len(text) == 1 else None
            label = max('ABCD', key=lambda c: result['label_logprobs'][c])
            record = dict(result, total_inference_seconds=total, id=entry['id'],
                          source_id=entry['source_id'], query=entry['query'], method=method_name,
                          selection={k: v for k, v in selection.items() if k != 'prompt'},
                          correct=bool(native == entry['gold']), native_prediction=native,
                          logprob_prediction=label, logprob_correct=bool(label == entry['gold']),
                          format_failure=native is None)
            for key in ['cluster_id', 'split_cluster_id', 'subject']:
                if key in entry:
                    record[key] = entry[key]
            yield record
