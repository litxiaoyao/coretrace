"""Input-only title links; no relation labels, answers or support annotations."""
import re, unicodedata

def normalized_words(text):
    return ' '.join(re.findall('\\w+', unicodedata.normalize('NFKC', text).casefold()))

def contains_title(text, title):
    needle = normalized_words(title)
    return bool(needle and ' ' + needle + ' ' in ' ' + normalized_words(text) + ' ')

def root_and_neighbors(prompt, titles):
    end = prompt.rfind('\n\nFinal question: ')
    if end < 0:
        return dict(root=None, neighbors=[], reason='unrecognized_question_marker')
    question = prompt[end + len('\n\nFinal question: '):]
    matches = list(re.finditer('(?:^|\\n)Title: ([^\\n]+)\\n', prompt[:end]))
    if [m.group(1) for m in matches] != titles:
        raise ValueError('Exact original title order')
    roots = [i for i, t in enumerate(titles) if contains_title(question, t)]
    if not roots:
        return dict(root=None, neighbors=[], reason='no_explicit_root_title')
    longest = max((len(normalized_words(titles[i])) for i in roots))
    roots = [i for i in roots if len(normalized_words(titles[i])) == longest]
    if len(roots) != 1:
        return dict(root=None, neighbors=[], reason='ambiguous_longest_root_title')
    root = roots[0]
    body = prompt[matches[root].end():matches[root + 1].start() if root + 1 < len(matches) else end]
    neighbors = [i for i, t in enumerate(titles) if i != root and contains_title(body, t)]
    return dict(root=root, neighbors=neighbors, reason='explicit_root_title_links' if neighbors else 'no_explicit_neighbor_title')
