"""Native chat geometry without model loading or import-time environment changes.

The caller supplies the tokenizer and family ('qwen3' or 'llama'). Prompt text is
returned unchanged. Token IDs reflect each native chat template, including Llama
whitespace trimming. Question positions always mean overlapping stem tokens.
"""
import hashlib
import json
import re
import unicodedata

def _normalized_words(text):
    return ' '.join(re.findall('\\w+', unicodedata.normalize('NFKC', text).casefold()))

def question_span(prompt):
    """Return (start, end, marker) in the original prompt's character coordinates."""
    markers = ('\n\nFinal question: ', '\n\nQuestion: ', '\n\nQuestion:\n')
    marker = max(markers, key=prompt.rfind)
    cut = prompt.rfind(marker)
    if cut < 0:
        raise ValueError('Explicit Final question / Question marker required')
    start = cut + len(marker)
    if marker == '\n\nQuestion:\n':
        end = prompt.rfind('\n\nA. ', start)
        if end < 0:
            raise ValueError('MMLU stem must end before a blank line and choices')
    else:
        answer = prompt.find('\nAnswer:', start)
        end = answer if answer >= 0 else len(prompt)
    if end <= start:
        raise ValueError('Empty question stem')
    return (start, end, marker)

def tokenize_prompt(tokenizer, prompt, *, family, question_char_span=None):
    """Build native chat IDs, exact stem offsets, and original titled paragraphs.

    An explicit question_char_span can disambiguate unusual content containing
    marker-like text; it must refer to this exact unchanged prompt.
    """
    if family not in ('qwen3', 'llama'):
        raise ValueError('Supported families: qwen3, llama')
    kwargs = dict(tokenize=False, add_generation_prompt=True)
    if family == 'qwen3':
        kwargs['enable_thinking'] = False
    chat = tokenizer.apply_chat_template([dict(role='user', content=prompt)], **kwargs)
    enc = tokenizer(chat, add_special_tokens=False, return_offsets_mapping=True)
    content = prompt if prompt in chat else prompt.strip()
    if not content or content not in chat:
        raise ValueError('Native template did not preserve the prompt content')
    removed_left = 0 if content == prompt else len(prompt) - len(prompt.lstrip())
    shift = chat.index(content) - removed_left
    start, end, marker = question_span(prompt)
    if question_char_span is not None:
        start, end = question_char_span
    if not 0 <= start < end <= len(prompt):
        raise ValueError('Question character span outside original prompt')
    offsets = enc['offset_mapping']
    positions = [i for i, (a, b) in enumerate(offsets) if b > a and b > shift + start and (a < shift + end)]
    if not positions:
        raise ValueError('Question has no overlapping native tokens')
    cut = prompt.rfind(marker)
    pattern = '(?:^|\\n)Title: ([^\\n]+)\\n' if family == 'qwen3' else '^Title: ([^\\n]+)\\n'
    matches = list(re.finditer(pattern, prompt[:cut], re.MULTILINE))
    paragraphs = []
    assigned = set()
    question = prompt[start:end]
    for i, match in enumerate(matches):
        lo = match.start()
        hi = matches[i + 1].start() if i + 1 < len(matches) else cut
        if family == 'llama':
            hi = len(prompt[:hi].rstrip('\n'))
        keys = [j for j, (a, b) in enumerate(offsets) if b > a and b > shift + lo and (a < shift + hi) and (j not in assigned)]
        if not keys or max(keys) >= min(positions):
            raise ValueError('Paragraph keys must precede question tokens')
        assigned.update(keys)
        title = match.group(1)
        needle = _normalized_words(title)
        if family == 'qwen3':
            normalize = lambda s: ' '.join(unicodedata.normalize('NFKC', s).casefold().split())
            mentioned = bool(normalize(title) in normalize(question))
        else:
            mentioned = bool(needle and ' ' + needle + ' ' in ' ' + _normalized_words(question) + ' ')
        paragraphs.append(dict(title=title, keys=keys, prompt_char_span=[lo, hi], title_mentioned_in_question=mentioned))
    ids = enc['input_ids']
    return dict(prompt=prompt, prompt_ids=ids, question=question, question_positions=positions, paragraphs=paragraphs, question_char_span=[start, end], question_marker=marker)
