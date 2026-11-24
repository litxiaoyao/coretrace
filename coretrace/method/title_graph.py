"""Input-only applicability: one independently mentioned root, excluding nested title matches.
Do not discard a second explicit query entity using longest-title tie breaking.
"""
from .title_links import root_and_neighbors, normalized_words

def maximal_root_mentions(prompt, titles):
    marker = '\n\nFinal question: '
    end = prompt.rfind(marker)
    if end < 0:
        return []
    words = normalized_words(prompt[end + len(marker):]).split()
    hits = []
    for i, title in enumerate(titles):
        needle = normalized_words(title).split()
        if not needle:
            continue
        for j in range(len(words) - len(needle) + 1):
            if words[j:j + len(needle)] == needle:
                hits.append((j, j + len(needle), i))
    return sorted({i for a, b, i in hits if not any((c <= a and b <= d and (c < a or b < d) for c, d, _ in hits))})

def single_root_graph(prompt, titles):
    roots = maximal_root_mentions(prompt, titles)
    if len(roots) != 1:
        return dict(root=None, neighbors=[], reason='no_unique_independent_root_title', maximal_roots=roots)
    graph = root_and_neighbors(prompt, titles)
    if graph['root'] != roots[0]:
        raise ValueError('Unique maximal root agrees with original unique longest root')
    return dict(graph, maximal_roots=roots)
