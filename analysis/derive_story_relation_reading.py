#!/usr/bin/env python3
"""Summarize measured paired-relation captures; no model/GPU or plotting.

Reads complete capture JSON files produced by capture_paired_relation_reading.py.
Resamples entire discovery quadruplets; no claim about independent test data.
"""
from __future__ import annotations
import argparse, csv, gzip, hashlib, json
from pathlib import Path
from collections import defaultdict
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
STATES = ('native_composed', 'native_direct_same_relation', 'native_direct_other_relation', 'adapted_composed')
METRICS = ('bridge_mass','conditional_target','conditional_other','conditional_target_per_token','conditional_other_per_token','absolute_target_mass','absolute_other_mass')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('captures',nargs='+',type=Path,help='Complete .json or losslessly compressed .json.gz captures')
    p.add_argument('--bootstrap',type=int,default=10000)
    a=p.parse_args()
    if a.bootstrap<1000: p.error('At least 1000 cluster bootstrap replicates required')
    rng=np.random.default_rng(20261125); summaries=[]; receivers=[]; provenance={}; decoded_hashes={}; seen=set()
    for path in a.captures:
        path=path.resolve()
        raw=path.read_bytes()
        decoded=gzip.decompress(raw) if path.suffix=='.gz' else raw
        d=json.loads(decoded)
        if d.get('status')!='MEASURED_PAIRED_RELATION_CAPTURE' or d.get('expected_receivers')!=100:
            raise ValueError(f'Expected a full frozen 100-receiver capture, not a pilot: {path}')
        model=d['model_id']
        if model in seen: raise ValueError(f'Duplicate model capture: {model}')
        seen.add(model)
        if len(d['records'])!=d['analyzed_receivers'] or len(d['records'])+len(d['excluded_receivers'])!=100:
            raise ValueError('Receiver accounting mismatch')
        name=str(path.relative_to(ROOT))
        provenance[name]=hashlib.sha256(raw).hexdigest()
        decoded_hashes[name]=hashlib.sha256(decoded).hexdigest()
        by_cluster=defaultdict(list); ids=set()
        for rec in d['records']:
            if rec['id'] in ids: raise ValueError('Duplicate receiver')
            ids.add(rec['id']); row={x['state']:x for x in rec['states']}
            if set(row)!=set(STATES): raise ValueError('Missing matched state')
            values={}
            for state in STATES:
                r=row[state]
                v={k:float(r[k]) for k in METRICS}
                if not all(np.isfinite(x) and -1e-8<=x<=1.00001 for x in v.values()): raise ValueError('Invalid measured mass')
                v['conditional_margin']=v['conditional_target']-v['conditional_other']
                v['per_token_margin']=v['conditional_target_per_token']-v['conditional_other_per_token']
                v['absolute_margin']=v['absolute_target_mass']-v['absolute_other_mass']
                values[state]=v
                receivers.append(dict(model=model,receiver_id=rec['id'],source_id=rec['source_id'],quadruplet_id=rec['quadruplet_id'],state=state,n_heads=len(rec['valid_heads']),target_span=rec['spans']['target']['text'],other_span=rec['spans']['other_relation']['text'],**{k:100*x for k,x in v.items()}))
            by_cluster[rec['quadruplet_id']].append(values)
        clusters=sorted(by_cluster)
        if not clusters: raise ValueError('No matched receiver')
        contrasts=[('adapted_vs_native','adapted_composed','native_composed'),('same_vs_other_direct','native_direct_same_relation','native_direct_other_relation')]
        for metric in ('bridge_mass',*METRICS[1:],'conditional_margin','per_token_margin','absolute_margin'):
            for label,plus,minus in contrasts:
                arrays=[np.array([100*(x[plus][metric]-x[minus][metric]) for x in by_cluster[c]]) for c in clusters]
                total=np.array([x.sum() for x in arrays]);counts=np.array([len(x) for x in arrays]);boot=[]
                for i in range(0,a.bootstrap,512):
                    ix=rng.integers(0,len(clusters),size=(min(512,a.bootstrap-i),len(clusters)))
                    boot.extend((total[ix].sum(axis=1)/counts[ix].sum(axis=1)).tolist())
                lo,hi=np.quantile(boot,[.025,.975]); native_means={s:100*np.mean([x[s][metric] for c in clusters for x in by_cluster[c]]) for s in STATES}
                summaries.append(dict(model=model,metric=metric,contrast=label,plus=plus,minus=minus,n_receivers=int(counts.sum()),n_clusters=len(clusters),estimate_pp=float(total.sum()/counts.sum()),ci95_low_pp=float(lo),ci95_high_pp=float(hi),**native_means))
    out=ROOT/'analysis/figure_data';out.mkdir(parents=True,exist_ok=True)
    for name,rows in [('data_revision_relation_reading_summary.csv',summaries),('data_revision_relation_reading_receivers.csv',receivers)]:
        f=out/name
        with f.open('w',newline='',encoding='utf8') as s:
            w=csv.DictWriter(s,fieldnames=rows[0].keys(),lineterminator="\n");w.writeheader();w.writerows(rows)
        print('Wrote',f)
    (out/'data_revision_relation_reading_manifest.json').write_text(json.dumps(dict(inputs=provenance,decoded_json_sha256=decoded_hashes,bootstrap_reps=a.bootstrap,bootstrap_seed=20261125,unit='percentage points; receiver means with quadruplet bootstrap',population='fixed discovery, not independent held-out'),indent=2)+'\n')
if __name__=='__main__': main()
