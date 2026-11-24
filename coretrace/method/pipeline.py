"""Mechanism-derived input evidence selection under the actual deployment body."""
from contextlib import nullcontext
import torch
from ..data.tokenization import tokenize_prompt
from ..mechanisms.paragraph_attention import NativeParagraphObserver, NativeEagerHeadChunks
from .address_readout import address_scores
from .text_selector import select_text

class EvidenceSelector:

    def __init__(self, model, tokenizer, head_map, readout, *, family, paragraph_boundary):
        self.model = model
        self.tokenizer = tokenizer
        self.head_map = head_map
        self.readout = readout
        self.family = family
        self.paragraph_boundary = paragraph_boundary

    def select(self, entry, *, body=None, component='decoded_text'):
        if component not in ['decoded_text', 'graphfirst_text', 'no_filter']:
            raise ValueError('Unknown fixed component')
        if component == 'no_filter':
            return (entry, dict(chosen=None, address_prefills=0, graph=None))
        if not entry.get('paragraphs'):
            return (entry, dict(chosen=None, address_prefills=0, graph=None))

        def rank(candidates):
            if component == 'graphfirst_text':
                return candidates[0]
            observer = NativeParagraphObserver(self.model, entry, self.head_map)
            x = torch.tensor([entry['prompt_ids']], device=next(self.model.parameters()).device)
            with torch.inference_mode(), NativeEagerHeadChunks(self.model, 4), body.session(entry) if body is not None else nullcontext(), observer:
                result = self.model(input_ids=x, attention_mask=torch.ones_like(x), use_cache=False, logits_to_keep=1)
            del result, x
            row = dict(features=observer.features, paragraphs=[dict(key_count=len(p['keys']), title_mentioned_in_question=p['title_mentioned_in_question']) for p in entry['paragraphs']], prompt_tokens=len(entry['prompt_ids']))
            scores = address_scores(row, self.readout)
            return max(candidates, key=lambda i: float(scores[i]))
        selection = select_text(entry['prompt'], [p['title'] for p in entry['paragraphs']], rank, paragraph_boundary=self.paragraph_boundary)
        if component == 'graphfirst_text':
            selection['address_prefills'] = 0
        if selection['chosen'] is None:
            return (entry, selection)
        geometry = tokenize_prompt(self.tokenizer, selection['prompt'], family=self.family)
        return (dict(entry, **geometry), selection)
