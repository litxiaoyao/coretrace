"""Aggregate complete fixed-population results per model over prescribed seeds."""
import json
import statistics
from pathlib import Path
from .ledgers import read_complete
SEEDS=[42,43,44]
COUNTS={'core':1000,'hotpot':7405,'mmlu':14042,'gsm8k':1319}

def aggregate(spec,base):
    if spec.get('seeds')!=SEEDS:raise ValueError('Formal replication seeds must be exactly42,43,44')
    dataset=spec['dataset_version'];results=[];sources=[];keys=set();shared_populations={}
    for group in spec['groups']:
        model,benchmark,method=group['model'],group['benchmark'],group['method'];key=(model,benchmark,method)
        if key in keys:raise ValueError('Duplicate table group')
        keys.add(key)
        if benchmark not in COUNTS:raise ValueError('Unknown fixed benchmark')
        deterministic=group.get('deterministic_reference',False);directories=group['directories']
        if len(directories)!=(1 if deterministic else 3):raise ValueError('One explicit deterministic reference or three trained-seed evaluations required')
        observations={};populations=set();datasets=set()
        for directory in directories:
            p=Path(directory).expanduser();p=p if p.is_absolute()else Path(base)/p
            manifest,allrows=read_complete(p);provenance=manifest['provenance'];seed=provenance['seed']
            if seed not in SEEDS or seed in observations:raise ValueError('Unexpected/duplicate seed; best-seed selection prohibited')
            if benchmark=='core' and provenance.get('dataset_version')!=dataset:raise ValueError('Dataset version mismatch')
            rows=[r for r in allrows if r['method']==method]
            if not rows:raise ValueError('Requested method missing')
            if deterministic:
                config=provenance.get('config',{})
                definition=next((m for m in config.get('methods',[])if m['name']==method),None)
                if definition is None or definition.get('artifact')or definition.get('scope')or definition.get('readout'):raise ValueError('Shared deterministic reference must be explicitly untrained/unmodified')
            ids=[(r['source_id'],r['query'],r['id']) for r in rows]
            populations.add(tuple(sorted(ids)));datasets.add(json.dumps(provenance.get('dataset_identity'), sort_keys=True))
            values={}
            queries=sorted({r['query']for r in rows})
            if benchmark=='core'and set(queries)!={'composed','direct_first','direct_target'}:raise ValueError('All three core queries required')
            for query in queries:
                panel=[r for r in rows if r['query']==query]
                if len(panel)!=COUNTS[benchmark]or len({r['source_id']for r in panel})!=len(panel):raise ValueError('Fixed complete benchmark denominator required')
                metric='logprob_correct'if benchmark=='mmlu'else'correct'
                if any(type(r.get(metric))is not bool for r in panel):raise ValueError('Primary benchmark score unavailable')
                values[(query,metric)]=dict(n=len(panel),correct=sum(r[metric]for r in panel))
            if benchmark=='core':
                sourceids={r['source_id']for r in rows};table={(r['source_id'],r['query']):r for r in rows}
                if len(table)!=len(rows):raise ValueError('Duplicate source query')
                values[('all3','correct')]=dict(n=len(sourceids),correct=sum(all(table[sid,q]['correct']for q in queries)for sid in sourceids))
            observations[seed]=values;sources.append(dict(model=model,benchmark=benchmark,method=method,seed=seed,directory=str(p)))
        if len(populations)!=1 or len(datasets)!=1:raise ValueError('Population or dataset identity changed across seeds')
        population=(next(iter(populations)),next(iter(datasets)));comparison=(model,benchmark)
        if comparison in shared_populations and shared_populations[comparison]!=population:raise ValueError('Compared methods use different populations or dataset identities')
        shared_populations[comparison]=population
        if not deterministic and set(observations)!=set(SEEDS):raise ValueError('All prescribed seeds required')
        first=next(iter(observations.values()))
        for query,metric in first:
            ns={v[(query,metric)]['n']for v in observations.values()}
            if len(ns)!=1:raise ValueError('Denominator changed')
            accuracy={str(seed):v[(query,metric)]['correct']/v[(query,metric)]['n']for seed,v in sorted(observations.items())};scores=list(accuracy.values())
            results.append(dict(model=model,benchmark=benchmark,method=method,query=query,metric=metric,n=next(iter(ns)),per_seed_correct={str(seed):v[(query,metric)]['correct']for seed,v in sorted(observations.items())},per_seed_accuracy=accuracy,mean_accuracy=statistics.mean(scores),sample_std_accuracy=None if deterministic else statistics.stdev(scores),deterministic_reference=deterministic,independent_seed_runs=len(scores),identical_scores=len(set(scores))==1))
    return dict(status='COMPLETE_FORMAL_PER_MODEL_AGGREGATION',seeds=SEEDS,dataset_version=dataset,rows=results,sources=sources,model_averaging=False,deterministic_reference_policy='One measured reference; no invented three-run standard deviation. Trained runs use all42/43/44, never best seed.',MMLU_primary='ABCD same-prefill option-logprob accuracy')
