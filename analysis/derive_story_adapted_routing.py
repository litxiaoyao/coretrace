#!/usr/bin/env python3
"""Derive adapted-versus-native paragraph access on matched test sources.

Reads existing archives in the working tree (including uncommitted local
results). No model inference and no training. Output only under analysis/.
"""
from __future__ import annotations
import argparse, csv, gzip, io, json, hashlib
from pathlib import Path
from collections import defaultdict
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
MODELS=('qwen3_4b','qwen3_8b','llama3_8b')
EXPECTED={'qwen3_4b':234,'qwen3_8b':236,'llama3_8b':243}


def records(stem, manifest):
    p=ROOT/stem
    # Prefer an intact JSONL archive. Otherwise concatenate split gzip bytes.
    if p.exists(): paths=[p]; compressed=False
    elif p.with_name(p.name+'.gz').exists(): paths=[p.with_name(p.name+'.gz')]; compressed=True
    else:
        paths=sorted(p.parent.glob(p.name+'.gz.part*')); compressed=True
        expected=[p.name+f'.gz.part{i:04d}' for i in range(len(paths))]
        if [x.name for x in paths]!=expected: raise ValueError(f'Noncontiguous gzip parts: {p}')
    if not paths: raise FileNotFoundError(str(p))
    chunks=[]
    for f in paths:
        b=f.read_bytes();chunks.append(b);manifest[str(f.relative_to(ROOT))]=hashlib.sha256(b).hexdigest()
    data=b''.join(chunks)
    with (gzip.GzipFile(fileobj=io.BytesIO(data)) if compressed else io.BytesIO(data)) as h:
        for l in h:
            if l.strip(): yield json.loads(l)


def source_features(prefix, corpus, manifest, expected_heads):
    result={}
    for row in records(prefix,manifest):
        if row['split']!='test': continue
        sid=row['source_id']; src=corpus[sid]
        if sid in result: raise ValueError(f'Duplicate feature row {sid}')
        titles=[p[0] for p in src['original_context']]
        root=titles.index(src['edges']['first_target']['title']); bridge=titles.index(src['edges']['second_target']['title'])
        order=[]; observed=[]
        for l,block in sorted(row['features'].items(),key=lambda kv:int(kv[0])):
            shape=(len(block['heads']),len(titles))
            for field in ('all_question_mean','last_question'):
                values=np.asarray(block[field],dtype=float)
                # Attention probabilities were formed in native BF16; their
                # disjoint paragraph sums can exceed one by rounding error.
                # Permit 0.5% numerical slack without renormalizing the data.
                if values.shape!=shape or not np.isfinite(values).all() or np.any(values<0) or np.any(values>1.005) or np.any(values.sum(axis=1)>1.005):
                    raise ValueError(f'Invalid raw paragraph mass: {sid}, layer={l}, {field}')
            for i,h in enumerate(block['heads']):
                order.append((int(l),int(h)));observed.append(block['all_question_mean'][i])
        if sorted(order)!=expected_heads or len(order)!=len(set(order)):
            raise ValueError(f'Feature heads differ from frozen selection: {sid}')
        a=np.asarray(observed,dtype=float)
        if a.shape!=(len(order),len(titles)) or not np.isfinite(a).all() or np.any(a<0): raise ValueError(f'Bad features: {sid}')
        # Keep mean unnormalized raw paragraph mass, as in V3.
        result[sid]={'query_id':row['id'],'head_set':sorted(order),'prompt_tokens':row['prompt_tokens'],'keys':[p['key_count'] for p in row['paragraphs']], 'title_mentioned':[p['title_mentioned_in_question'] for p in row['paragraphs']], 'titles':titles, 'root_index':root,'bridge_index':bridge, 'root':100*float(a[:,root].mean()),'bridge':100*float(a[:,bridge].mean())}
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--seed',type=int,default=42,choices=[42,43,44]);p.add_argument('--bootstrap',type=int,default=10000);a=p.parse_args()
    if a.bootstrap<1: p.error('--bootstrap must be positive')
    manifest={};corpus={r['source_id']:r for r in records('data/CoRe-2Wiki-v1.0/corpus.jsonl',manifest)}
    test_ids={sid for sid,r in corpus.items() if r['global_split']=='test'}
    if len(test_ids)!=1000: raise ValueError('Frozen corpus must contain 1,000 test sources')
    rows=[]; paired=[]
    rng=np.random.default_rng(20261125)
    for m in MODELS:
        frozen=ROOT/f'outputs/{m}/discovery/SELECTION_FROZEN.json'
        manifest[str(frozen.relative_to(ROOT))]=hashlib.sha256(frozen.read_bytes()).hexdigest()
        head_map=json.loads(frozen.read_text())['head_map']
        expected_heads=sorted((int(l),int(h)) for l,heads in head_map.items() for h in heads)
        pred=defaultdict(dict)
        for r in records(f'outputs/{m}/seed42/evaluation/core/predictions.jsonl',manifest):
            if r['method']=='native':
                if r['query'] in pred[r['source_id']]: raise ValueError('Duplicate native predictions')
                pred[r['source_id']][r['query']]=bool(r['correct'])
        if set(pred)!=test_ids or any(set(q)!={'direct_first','direct_target','composed'} for q in pred.values()):
            raise ValueError(f'Incomplete native three-query panel: {m}')
        failures={sid for sid,q in pred.items() if q['direct_first'] and q['direct_target'] and not q['composed']}
        if len(failures)!=EXPECTED[m]: raise ValueError(f'Fixed native failure count differs: {m}, {len(failures)}')
        native=source_features(f'outputs/{m}/native_readout/features.jsonl',corpus,manifest,expected_heads)
        adapted=source_features(f'outputs/{m}/seed{a.seed}/readout/features.jsonl',corpus,manifest,expected_heads)
        if set(native)!=test_ids or set(adapted)!=test_ids or not failures<=set(native): raise ValueError('Expected matched 1,000 test sources')
        for sid in native:
            if any(native[sid][k]!=adapted[sid][k] for k in ('query_id','head_set','prompt_tokens','keys','title_mentioned','titles','root_index','bridge_index')): raise ValueError(f'Native/adapted source geometry differs: {sid}')
        for sid in sorted(native):
            paired.append(dict(model=m,seed=a.seed,source_id=sid,query_id=native[sid]['query_id'],fixed_native_failure=sid in failures,root_index=native[sid]['root_index'],bridge_index=native[sid]['bridge_index'],native_root_pct=native[sid]['root'],native_bridge_pct=native[sid]['bridge'],adapted_root_pct=adapted[sid]['root'],adapted_bridge_pct=adapted[sid]['bridge']))
        for group,ids in [('all_test',set(native)),('fixed_native_failures',failures)]:
            ids=sorted(ids)
            for target in ('root','bridge'):
                x=np.asarray([native[s][target] for s in ids]);y=np.asarray([adapted[s][target] for s in ids]);d=y-x
                boot=np.empty(a.bootstrap)
                for i in range(0,a.bootstrap,512):
                    idx=rng.integers(0,len(ids),size=(min(512,a.bootstrap-i),len(ids)));boot[i:i+len(idx)]=d[idx].mean(axis=1)
                lo,hi=np.quantile(boot,[.025,.975])
                rows.append(dict(model=m,seed=a.seed,population=group,n=len(ids),target=target,native_mass_percent=float(x.mean()),adapted_mass_percent=float(y.mean()),delta_pp=float(d.mean()),ci95_low_pp=float(lo),ci95_high_pp=float(hi),source='native_readout and adapted-state readout feature archives'))
    out=ROOT/'analysis/figure_data/data_revision_adapted_routing.csv';out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator="\n");writer.writeheader();writer.writerows(rows)
    per=out.with_name('data_revision_adapted_routing_receivers.csv')
    with per.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=paired[0].keys(),lineterminator="\n");writer.writeheader();writer.writerows(paired)
    out.with_suffix('.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Wrote {out}')
if __name__=='__main__': main()
