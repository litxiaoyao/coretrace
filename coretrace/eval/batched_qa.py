"""Optional core/Hotpot batching; original selectors and official QA scoring."""
import time
from .batched_inference import greedy_batch
from .answer_metrics import score_answer


def evaluate_qa_batches(model, tokenizer, entries, *, method_name, batch_size,
                        eos_token_ids, pad_token_id, body=None, selector=None,
                        component='no_filter'):
    """Yield complete, untruncated QA rows for the existing EvaluationLedger.

    Evidence selection remains one native example at a time, under the actual
    deployment body. Only the final greedy generation is combined into batches.
    """
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
        results = greedy_batch(model, tokenizer, selected,
                               eos_token_ids=eos_token_ids, pad_token_id=pad_token_id,
                               body=body, max_new_tokens=32)
        total = (time.monotonic()-started)/len(batch)
        for entry, selection, result in zip(batch, selections, results):
            metrics = score_answer(result['answer'], entry['gold_aliases'])
            record = dict(result, total_inference_seconds=total, id=entry['id'],
                          source_id=entry['source_id'], query=entry['query'],
                          method=method_name,
                          selection={k: v for k, v in selection.items() if k != 'prompt'},
                          correct=bool(result['eos_complete'] and metrics['em']),
                          text_alias_correct=bool(metrics['em']), text_f1=metrics['f1'])
            for key in ['cluster_id', 'split_cluster_id', 'subject']:
                if key in entry:
                    record[key] = entry[key]
            yield record
