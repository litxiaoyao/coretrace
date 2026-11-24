"""Discovery-only all-head access-gap localization and causal best-n calibration.

Paragraph addresses are privileged diagnostic annotations, never a deployed
inference policy. Original prompts and source title order are retained exactly.
"""
import json
from pathlib import Path
from contextlib import nullcontext
from ..data.tokenization import tokenize_prompt
from .paragraph_attention import NativeParagraphObserver, NativeParagraphBudget, NativeEagerHeadChunks
from ..eval.inference import greedy_answer
from ..eval.answer_metrics import score_answer

def discovery_entries(dataset, tokenizer, *, family):
    corpus = {row['source_id']: row for row in dataset.sources('discovery')}
    aliases = {row['source_id']: row for row in dataset.aliases('discovery')}
    queries = dataset.queries('discovery')
    result = []
    for query in queries:
        if query['query'] not in ['composed', 'direct_target']:
            continue
        entry = dict(query, **tokenize_prompt(tokenizer, query['prompt'], family=family))
        titles = [p['title'] for p in entry['paragraphs']]
        for role in ['first', 'second']:
            title = corpus[query['source_id']]['edges'][role + '_target']['title']
            matches = [i for i, value in enumerate(titles) if value == title]
            if len(matches) != 1:
                raise ValueError(f"{query['source_id']}: exact {role} target title {title!r} has {len(matches)} paragraph matches")
            entry[role + '_paragraph'] = matches[0]
        entry['gold_aliases'] = aliases[entry['source_id']]['queries'][entry['canonical_query']]['golds']
        result.append(entry)
    if len(corpus) != 100 or len(result) != 200 or len({e['source_id'] for e in result}) != 100:
        raise ValueError('Frozen discovery100 must provide all100 composed/direct_target pairs')
    return result

def capture_all_heads(model, entries, output):
    import torch
    heads = {layer: list(range(model.config.num_attention_heads)) for layer in range(model.config.num_hidden_layers)}
    path = Path(output)
    seen = set()
    with path.open('x') as stream:
        for entry in entries:
            if entry['id'] in seen:
                raise ValueError('Duplicate capture query ID')
            seen.add(entry['id'])
            observer = NativeParagraphObserver(model, entry, heads)
            ids = torch.tensor([entry['prompt_ids']], device=next(model.parameters()).device)
            with torch.inference_mode(), NativeEagerHeadChunks(model, 4), observer:
                result = model(input_ids=ids, attention_mask=torch.ones_like(ids), use_cache=False, logits_to_keep=1)
            del ids, result
            row = dict(id=entry['id'], source_id=entry['source_id'], query=entry['query'], features=observer.features, second_paragraph=entry['second_paragraph'], first_paragraph=entry['first_paragraph'], paragraph_titles=[p['title'] for p in entry['paragraphs']])
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')
            stream.flush()
    return dict(rows=len(seen), head_map=heads)

def rank_access_gap(rows, *, candidate_counts=(20, 40, 80)):
    """Same-source mean direct-target minus composed mass; tau uses target last row."""
    rows = list(rows)
    by = {}
    for row in rows:
        if row['query'] not in ['composed', 'direct_target']:
            raise ValueError('Unexpected capture query')
        key = (row['source_id'], row['query'])
        if key in by:
            raise ValueError('Duplicate captured source/query')
        by[key] = row
    source_ids = sorted({row['source_id'] for row in rows})
    if len(rows) != 2 * len(source_ids) or not source_ids:
        raise ValueError('Every source requires both query modes')
    reference = rows[0]['features']
    ranking = []
    for layer in sorted(reference, key=int):
        heads = reference[layer]['heads']
        for index, head in enumerate(heads):
            composed = []
            direct = []
            last = []
            for sid in source_ids:
                for query, values in [('composed', composed), ('direct_target', direct)]:
                    row = by[sid, query]
                    if set(row['features']) != set(reference) or row['features'][layer]['heads'] != heads:
                        raise ValueError('All-head feature geometry changed across entries')
                    paragraph = row['second_paragraph']
                    feature = row['features'][layer]
                    values.append(float(feature['all_question_mean'][index][paragraph]))
                    if query == 'direct_target':
                        last.append(float(feature['last_question'][index][paragraph]))
            c = sum(composed) / len(composed)
            d = sum(direct) / len(direct)
            tau = sum(last) / len(last)
            if not all((0 <= v <= 1.00001 for v in composed + direct + last)):
                raise ValueError('Attention mass out of bounds')
            ranking.append(dict(layer=int(layer), head=head, score=d - c, composed_all_question_mean=c, direct_target_all_question_mean=d, tau_direct_target_last_question=tau, n_sources=len(source_ids)))
    ranking.sort(key=lambda r: (-r['score'], r['layer'], r['head']))
    candidates = {}
    for n in candidate_counts:
        if type(n) is not int or not 0 < n <= len(ranking):
            raise ValueError('Candidate count outside actual model head count')
        head_map = {}
        budgets = {}
        for row in ranking[:n]:
            layer = str(row['layer'])
            head = row['head']
            head_map.setdefault(layer, []).append(head)
            budgets.setdefault(layer, {})[str(head)] = row['tau_direct_target_last_question']
        candidates[str(n)] = dict(n=n, head_map=head_map, budgets=budgets)
    return dict(ranking=ranking, all_head_map={layer: reference[layer]['heads'] for layer in sorted(reference, key=int)}, candidate_maps=candidates, source_ids=source_ids, ranking_scope='Discovery composed/direct_target paired sources only', tau_definition='Mean direct_target lastquestion paragraph mass, separately for each head')

def select_best_n(records, candidates, *, expected_source_ids):
    """Choose only own-paragraph arms by composed accuracy; ties prefer fewer heads."""
    records = list(records)
    expected = set(expected_source_ids)
    summary = []
    for method, n in [('native', 0)] + [('own_top' + str(n), int(n)) for n in candidates]:
        group = [r for r in records if r['method'] == method]
        if len(group) != len(expected) or {r['source_id'] for r in group} != expected:
            raise ValueError('Calibration must retain every discovery source for every candidate')
        summary.append(dict(method=method, n=n, sources=len(group), correct=sum((r['correct'] for r in group))))
    winner = max([r for r in summary if r['n']], key=lambda r: (r['correct'], -r['n']))
    return dict(status='DISCOVERY_ONLY_HEAD_SELECTION_FROZEN', winner=winner, head_map=candidates[str(winner['n'])]['head_map'], budgets=candidates[str(winner['n'])]['budgets'], all_candidates=summary, selection_rule='Max discovery100 composed EOS-gated official-alias EM; smaller n on ties.', selection_population='Frozen discovery100 only', test_predictions_used=False, privileged_addresses=True, deployment_method=False)

def calibrate_candidates(model, tokenizer, entries, candidates, output, *, eos_token_ids, first_source_control=False):
    composed = [e for e in entries if e['query'] == 'composed']
    records = []
    pad = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
    with Path(output).open('x') as stream:
        for entry in composed:
            arms = [('native', None, 'second')] + [('own_top' + n, c, 'second') for n, c in candidates.items()]
            if first_source_control:
                arms.extend([('source1_top' + n, c, 'first') for n, c in candidates.items()])
            for method, candidate, source in arms:
                address = entry[source + '_paragraph']
                keys = entry['paragraphs'][address]['keys']
                session = None if candidate is None else NativeParagraphBudget(model, dict(entry, second_source_keys=keys), candidate['head_map'], candidate['budgets'])
                result = greedy_answer(model, tokenizer, entry, eos_token_ids=eos_token_ids, pad_token_id=pad, session=session)
                score = score_answer(result['answer'], entry['gold_aliases'])
                row = dict(result, id=entry['id'], source_id=entry['source_id'], method=method, correct=bool(result['eos_complete'] and score['em']), text_alias_correct=bool(score['em']), text_f1=score['f1'], privileged_source=source if candidate else None, source_paragraph=address if candidate else None, budget_events=[] if session is None else session.events)
                records.append(row)
                stream.write(json.dumps(row, ensure_ascii=False) + '\n')
                stream.flush()
    return records
