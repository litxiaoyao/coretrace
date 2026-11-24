"""Auxiliary causal views of the immutable discovery quadruplets.

All entity names, questions, source IDs, facts and original paragraphs come from
the frozen bundle. These views never replace its canonical queries or splits.
"""
from collections import Counter
import hashlib, json, re

def _question_prefix(prompt):
    marker = '\n\nEvidence:\n'
    cut = prompt.find(marker)
    if cut < 0:
        raise ValueError('Original evidence marker required')
    return prompt[:cut + len(marker)]

def discovery_views(dataset):
    """Return250 shared-context queries and100 explicit three-query links."""
    rows = [json.loads(line) for line in (dataset.root / 'mechanism_views/discovery25_quadruplets.jsonl').open()]
    queries = {(q['source_id'], q['query']): q for q in dataset.queries('discovery')}
    corpus = {r['source_id']: r for r in dataset.sources('discovery')}
    aliases = {r['source_id']: r for r in dataset.aliases('discovery')}
    entries = []
    links = []
    for quad in rows:
        text = quad['shared_context_text']
        cells = {q['cell']: q for q in quad['queries']}
        endpoints = {cell: aliases[q['source_id']]['queries']['composed']['golds'] for cell, q in cells.items()}
        ids = {}
        for i in [1, 2]:
            for j in [1, 2]:
                cell = f'C{i}{j}'
                q = cells[cell]
                sid = q['source_id']
                source = corpus[sid]
                for query, view_cell in [('composed', cell), ('direct_target', f'T{i}{j}')] + ([('direct_first', f'F{i}')] if j == 1 else []):
                    original = queries[sid, query]
                    alias = aliases[sid]['queries'][query.removeprefix('direct_')]
                    if original['gold'] != alias['gold']:
                        raise ValueError('Original query/alias mismatch')
                    prompt = _question_prefix(original['prompt']) + text + '\n\nFinal question: ' + original['question']
                    eid = quad['quadruplet_id'] + '__' + view_cell
                    ids[view_cell] = eid
                    other = corpus[cells[f'C{3 - i}{j}']['source_id']]['edges']['second_target']['title']
                    correct = source['edges']['first_target' if query == 'direct_first' else 'second_target']['title']
                    entries.append(dict(id=eid, canonical_query_id=original['id'], source_id=sid, query=query, cell=view_cell, quadruplet_id=quad['quadruplet_id'], prompt=prompt, gold=original['gold'], gold_aliases=alias['golds'], global_split='discovery', root_source_title=source['edges']['first_target']['title'], correct_source_title=correct, bridge_source_title=source['edges']['second_target']['title'], other_bridge_source_title=other, endpoint_aliases=endpoints, origin='Frozen discovery25 shared-context functional probe; canonical dataset unchanged'))
        for i in [1, 2]:
            for j in [1, 2]:
                links.append(dict(quadruplet_id=quad['quadruplet_id'], source_id=cells[f'C{i}{j}']['source_id'], composed=ids[f'C{i}{j}'], first=ids[f'F{i}'], target=ids[f'T{i}{j}']))
    if len(entries) != 250 or len(links) != 100:
        raise ValueError('All25 frozen quadruplets required')
    return (entries, links)

def _object_span(prompt, title, sentence, aliases):
    cut = prompt.rfind('\n\nFinal question: ')
    matches = list(re.finditer('^Title: ([^\\n]+)\\n', prompt[:cut], re.MULTILINE))
    selected = [i for i, m in enumerate(matches) if m.group(1) == title]
    if len(selected) != 1:
        raise ValueError('Unique original bridge paragraph required')
    index = selected[0]
    lo = matches[index].end()
    hi = matches[index + 1].start() if index + 1 < len(matches) else cut
    body = prompt[lo:hi]
    starts = [m.start() for m in re.finditer(re.escape(sentence), body)]
    if len(starts) != 1:
        return (None, 'support_sentence_not_unique')
    for alias in sorted(set(aliases), key=lambda s: (-len(s), s)):
        spans = list(re.finditer('(?<!\\w)' + re.escape(alias) + '(?!\\w)', sentence, re.IGNORECASE))
        if len(spans) == 1:
            m = spans[0]
            start = lo + starts[0] + m.start()
            return ((start, start + len(m.group(0)), m.group(0)), None)
        if len(spans) > 1:
            return (None, 'object_surface_ambiguous')
    return (None, 'no_literal_official_object_alias')

def reciprocal_value_views(dataset):
    """All100 composed queries; reciprocal same-R2 values, explicit no-ops.

    Each original/edited pair retains the exact question, paragraph order and
    global character/word occurrence bags. New values come from the other real
    bridge's same-relation official fact. No model outputs enter construction.
    """
    entries, _ = discovery_views(dataset)
    entries = [e for e in entries if e['query'] == 'composed']
    by = {(e['quadruplet_id'], e['cell']): e for e in entries}
    quads = {q['quadruplet_id']: q for q in map(json.loads, (dataset.root / 'mechanism_views/discovery25_quadruplets.jsonl').open())}
    output = []
    for e in entries:
        cell = e['cell']
        i, j = (int(cell[1]), int(cell[2]))
        other = by[e['quadruplet_id'], f'C{3 - i}{j}']
        quad = quads[e['quadruplet_id']]
        questions = {q['cell']: q for q in quad['queries']}
        prompt = e['prompt']
        spans = []
        reason = None
        for item in [e, other]:
            support = questions[item['cell']]['support_sentences'][1]
            span, error = _object_span(prompt, item['bridge_source_title'], support['text'], item['gold_aliases'])
            if error:
                reason = error
                break
            spans.append(span)
        edited = prompt
        if reason is None:
            a, b = spans
            if not (a[1] <= b[0] or b[1] <= a[0]):
                reason = 'overlapping_object_spans'
            elif a[2].casefold() == b[2].casefold():
                reason = 'same_object_surface'
            else:
                for span, replacement in sorted([(a, b[2]), (b, a[2])], key=lambda x: x[0][0], reverse=True):
                    edited = edited[:span[0]] + replacement + edited[span[1]:]
                if Counter(edited) != Counter(prompt) or Counter(re.findall('\\w+', edited)) != Counter(re.findall('\\w+', prompt)):
                    reason = 'word_boundary_bag_changed'
        applied = reason is None
        if not applied:
            edited = prompt
        output.append(dict(e, original_prompt=prompt, edited_prompt=edited, counterfactual_applied=applied, new_follow_defined=applied, replacement_aliases=other['gold_aliases'] if applied else [], replacement_gold=other['gold'] if applied else None, reason=reason, character_bag_identical=Counter(prompt) == Counter(edited), word_bag_identical=Counter(re.findall('\\w+', prompt)) == Counter(re.findall('\\w+', edited)), source_pair=[e['source_id'], other['source_id']], context_edit='Reciprocal official object surfaces in same-R2 bridge facts; auxiliary input counterfactual, not a canonical corpus relabeling'))
    if len(output) != 100:
        raise ValueError('All100 discovery composed sources required')
    return output
