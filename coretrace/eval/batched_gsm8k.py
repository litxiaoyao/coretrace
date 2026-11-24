"""Optional GSM8K batching with unchanged final-line numeric scoring."""
import time
from .batched_inference import greedy_batch
from .gsm8k import score_answer


def evaluate_gsm8k_batches(model, tokenizer, entries, *, method_name, batch_size,
                           eos_token_ids, pad_token_id, body=None, selector=None,
                           component='no_filter'):
    """Yield full 512-token greedy generations for the existing ledger.

    Evidence selection remains per example under its deployment body. Math
    parsing, Decimal normalization, EOS diagnostics and cutoff scoring use the
    same function as the original single-example evaluation path.
    """
    if type(batch_size) is not int or batch_size < 1:
        raise ValueError('Positive integer batch size required')
    for lo in range(0, len(entries), batch_size):
        batch = entries[lo:lo + batch_size]
        started = time.monotonic()
        selected, selections = [], []
        for entry in batch:
            item, selection = selector.select(entry, body=body, component=component) if selector else (entry, dict(chosen=None, address_prefills=0, graph=None))
            selected.append(item)
            selections.append(selection)
        results = greedy_batch(model, tokenizer, selected,
                               eos_token_ids=eos_token_ids, pad_token_id=pad_token_id,
                               body=body, max_new_tokens=512)
        total = (time.monotonic() - started) / len(batch)
        for entry, selection, result in zip(batch, selections, results):
            metrics = score_answer(result['answer'], entry['gold_numeric'],
                                   generated_token_count=result['generated_tokens'],
                                   eos_complete=result['eos_complete'])
            record = dict(result, total_inference_seconds=total, id=entry['id'],
                          source_id=entry['source_id'], query=entry['query'],
                          method=method_name,
                          selection={k: v for k, v in selection.items() if k != 'prompt'})
            for key in ['cluster_id', 'split_cluster_id', 'subject']:
                if key in entry:
                    record[key] = entry[key]
            record.update(metrics)
            yield record
