"""Greedy QA and exact one-token MCQ evaluation, without answer-label access."""
import time
from contextlib import nullcontext
import torch
from ..mechanisms.paragraph_attention import NativeEagerHeadChunks

def greedy_answer(model, tokenizer, entry, *, eos_token_ids, pad_token_id, max_new_tokens=32, session=None, chunk_heads=4):
    if model.training:
        raise ValueError('Inference requires an eval model')
    ids = torch.tensor([entry['prompt_ids']], device=next(model.parameters()).device)
    tick = time.monotonic()
    with torch.inference_mode(), NativeEagerHeadChunks(model, chunk_heads), session if session is not None else nullcontext():
        generated = model.generate(input_ids=ids, attention_mask=torch.ones_like(ids), do_sample=False, num_beams=1, max_new_tokens=max_new_tokens, use_cache=True, logits_to_keep=1, eos_token_id=list(eos_token_ids), pad_token_id=pad_token_id, temperature=None, top_p=None)
    if generated[0, :ids.shape[1]].tolist() != entry['prompt_ids']:
        raise ValueError('Generation changed the supplied input')
    tokens = generated[0, ids.shape[1]:].tolist()
    eos_complete = bool(tokens and tokens[-1] in eos_token_ids)
    answer = tokenizer.decode(tokens[:-1] if eos_complete else tokens, skip_special_tokens=False, clean_up_tokenization_spaces=False).strip()
    return dict(answer=answer, generated_token_ids=tokens, eos_complete=eos_complete, input_tokens=ids.shape[1], generated_tokens=len(tokens), seconds=time.monotonic() - tick)

def option_logprobs(model, entry, *, session=None, chunk_heads=4):
    if model.training:
        raise ValueError('Inference requires an eval model')
    labels = entry['label_token_ids']
    if set(labels) != set('ABCD') or any((len(v) != 1 for v in labels.values())) or len({v[0] for v in labels.values()}) != 4:
        raise ValueError('ABCD must each be one distinct tokenizer token')
    ids = torch.tensor([entry['prompt_ids']], device=next(model.parameters()).device)
    tick = time.monotonic()
    with torch.inference_mode(), NativeEagerHeadChunks(model, chunk_heads), session if session is not None else nullcontext():
        result = model(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False, logits_to_keep=1)
        logits = result.logits[0, -1].float()
        normal = torch.logsumexp(logits, dim=-1)
        scores = {c: float(logits[labels[c][0]] - normal) for c in 'ABCD'}
    return dict(label_logprobs=scores, predicted_label=max('ABCD', key=lambda c: scores[c]), raw_prefill_argmax_token_id=int(logits.argmax()), native_prefills=1, generated_tokens=0, seconds=time.monotonic() - tick)
