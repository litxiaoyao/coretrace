"""Per-model complete-only accuracy, source-paired contrasts, and core all3."""
from .ledgers import read_complete

def summarize(directory, *, bootstrap_reps=2000, seed=42):
    import numpy as np
    manifest, rows = read_complete(directory)
    methods = manifest['methods']
    summary = []
    paired = []
    rng = np.random.default_rng(seed)

    def contrast(first, second, query, left, right, metric='correct'):
        ids = sorted(left)
        if set(ids) != set(right):
            raise ValueError('Paired populations differ')
        delta = np.array([int(right[i][metric]) - int(left[i][metric]) for i in ids])
        groups = {}
        for j, i in enumerate(ids):
            groups.setdefault(left[i].get('cluster_id', left[i]['source_id']), []).append(j)
        parts = list(groups.values())
        sums = np.array([delta[g].sum() for g in parts])
        sizes = np.array([len(g) for g in parts])
        # Bound temporary arrays by a modest chunk of replicates, rather than
        # materializing bootstrap_reps x all 14,042 MMLU items at once.
        dist = np.empty(bootstrap_reps, dtype=float)
        stratified = all('subject' in left[i] for i in ids)
        strata = {}
        if stratified:
            for j, i in enumerate(ids):
                if left[i]['subject'] != right[i].get('subject'):
                    raise ValueError('Paired MMLU subject assignments differ')
                strata.setdefault(left[i]['subject'], []).append(j)
        for start in range(0, bootstrap_reps, 64):
            stop = min(start + 64, bootstrap_reps)
            batch = stop - start
            if stratified:
                total = np.zeros(batch, dtype=float)
                for indices in strata.values():
                    sample = rng.choice(indices, size=(batch, len(indices)), replace=True)
                    total += delta[sample].sum(1)
                dist[start:stop] = total / len(ids)
            else:
                draw = rng.integers(0, len(parts), (batch, len(parts)))
                dist[start:stop] = sums[draw].sum(1) / sizes[draw].sum(1)
        return dict(method_before=first, method_after=second, query=query, n=len(ids), metric=metric, before=sum((left[i][metric] for i in ids)), after=sum((right[i][metric] for i in ids)), gains=int((delta > 0).sum()), losses=int((delta < 0).sum()), delta=float(delta.mean()), cluster_count=len(parts), paired_cluster_CI95=np.quantile(dist, [0.025, 0.975]).tolist())
    queries = sorted({r['query'] for r in rows})
    by = {(r['method'], r['query'], r['source_id']): r for r in rows}
    if len(by) != len(rows):
        raise ValueError('Duplicate source-query pair')
    for query in queries:
        tables = {}
        for method in methods:
            rs = [r for r in rows if r['method'] == method and r['query'] == query]
            tables[method] = {r['source_id']: r for r in rs}
            item = dict(method=method, query=query, n=len(rs), correct=sum((r['correct'] for r in rs)), accuracy=sum((r['correct'] for r in rs)) / len(rs))
            for key in ['logprob_correct', 'eos_complete', 'format_failure', 'text_alias_correct']:
                if all((key in r for r in rs)):
                    item[key] = sum((bool(r[key]) for r in rs))
            if all(('text_f1' in r for r in rs)):
                item['mean_text_f1'] = sum((r['text_f1'] for r in rs)) / len(rs)
            if all(('subject' in r for r in rs)):
                subjects = sorted({r['subject'] for r in rs})
                item['subject_macro_accuracy'] = sum((sum((r['correct'] for r in rs if r['subject'] == s)) / sum((r['subject'] == s for r in rs)) for s in subjects)) / len(subjects)
                if all('logprob_correct' in r for r in rs):
                    item['subject_macro_logprob_accuracy'] = sum(
                        sum(r['logprob_correct'] for r in rs if r['subject'] == s)
                        / sum(r['subject'] == s for r in rs)
                        for s in subjects) / len(subjects)
            summary.append(item)
        for j, first in enumerate(methods):
            for second in methods[j + 1:]:
                paired.append(contrast(first, second, query, tables[first], tables[second]))
                if all(('logprob_correct' in row for row in tables[first].values())):
                    paired.append(contrast(first, second, query, tables[first], tables[second], metric='logprob_correct'))
    all3 = []
    conditional_composition = []
    native_conditioned_composition = []
    if set(queries) == {'composed', 'direct_first', 'direct_target'}:
        sourceids = sorted({r['source_id'] for r in rows})
        tables = {}
        for method in methods:
            table = {}
            for sid in sourceids:
                rs = [by[method, q, sid] for q in queries]
                table[sid] = dict(correct=all((r['correct'] for r in rs)), source_id=sid, cluster_id=rs[0].get('cluster_id', sid))
            constituent_correct = [sid for sid in sourceids if by[method, 'direct_first', sid]['correct'] and by[method, 'direct_target', sid]['correct']]
            failures = sum(not by[method, 'composed', sid]['correct'] for sid in constituent_correct)
            conditional_composition.append(dict(method=method, n_sources=len(sourceids), both_constituents_correct=len(constituent_correct), composition_failures=failures, conditional_failure_rate=failures/len(constituent_correct) if constituent_correct else None))
            tables[method] = table
            all3.append(dict(method=method, n=len(table), correct=sum((r['correct'] for r in table.values())), accuracy=sum((r['correct'] for r in table.values())) / len(table)))
        for j, first in enumerate(methods):
            for second in methods[j + 1:]:
                paired.append(contrast(first, second, 'all3', tables[first], tables[second]))
        if 'native' in methods:
            known = [sid for sid in sourceids if by['native','direct_first',sid]['correct'] and by['native','direct_target',sid]['correct']]
            failed = [sid for sid in known if not by['native','composed',sid]['correct']]
            solved = [sid for sid in known if by['native','composed',sid]['correct']]
            for method in methods:
                native_conditioned_composition.append(dict(
                    method=method, population='Native both-constituent-correct sources; fixed across methods',
                    n=len(known), correct=sum(by[method,'composed',sid]['correct'] for sid in known),
                    native_composition_failures=len(failed),
                    repaired_native_failures=sum(by[method,'composed',sid]['correct'] for sid in failed),
                    native_composition_successes=len(solved),
                    lost_native_successes=sum(not by[method,'composed',sid]['correct'] for sid in solved)))
    return dict(status='COMPLETE_MODEL_EVALUATION_SUMMARY', model_identity=manifest['provenance']['model_identity'], seed=manifest['provenance']['seed'], summary=summary, all3=all3, conditional_composition=conditional_composition, native_conditioned_composition=native_conditioned_composition, paired_comparisons=paired, bootstrap_reps=bootstrap_reps, bootstrap_seed=seed, model_aggregation='None; one model per report')
