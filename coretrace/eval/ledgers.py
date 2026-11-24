"""Resumable prediction files with explicit configuration and complete ID coverage."""
import json
import os
from pathlib import Path

class EvaluationLedger:
    def __init__(self,directory,*,provenance,entry_ids,methods):
        self.root=Path(directory); self.root.mkdir(parents=True,exist_ok=True)
        self.manifest_path=self.root/'manifest.json'; self.path=self.root/'predictions.jsonl'
        entry_ids=list(entry_ids); methods=list(methods)
        if not entry_ids or not methods or len(set(entry_ids))!=len(entry_ids) or len(set(methods))!=len(methods):
            raise ValueError('Expected IDs and methods must be nonempty and unique')
        self.expected={method+':'+entry for method in methods for entry in entry_ids}
        self.manifest=dict(status='RUNNING',provenance=provenance,
                           expected_entry_ids=entry_ids,methods=methods,expected_rows=len(self.expected))
        self.rows={}
        if self.manifest_path.exists():
            prior=json.loads(self.manifest_path.read_text())
            if prior['provenance']!=self.manifest['provenance'] or prior['expected_entry_ids']!=entry_ids or prior['methods']!=methods:
                raise ValueError('Resume configuration or expected population mismatch')
            if prior['status']=='COMPLETE':
                raise ValueError('Evaluation already complete; reuse its output')
        else:
            self._write_manifest()
        if self.path.exists():
            with self.path.open() as stream:
                for line in stream:
                    row=json.loads(line); self._validate(row); self.rows[row['job_id']]=row

    def _write_manifest(self):
        temporary=self.manifest_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.manifest,indent=2)+'\n')
        os.replace(temporary,self.manifest_path)

    def _validate(self,row):
        job=row['method']+':'+row['id']
        if row.get('job_id')!=job or job not in self.expected or job in self.rows:
            raise ValueError('Unexpected or duplicate prediction row')
        if not isinstance(row.get('correct'),bool):
            raise ValueError('Every requested item must have a boolean primary score')

    def append(self,row):
        row=dict(row,job_id=row['method']+':'+row['id']); self._validate(row)
        with self.path.open('a') as stream:
            stream.write(json.dumps(row,ensure_ascii=False)+'\n'); stream.flush()
        self.rows[row['job_id']]=row

    def finish(self,*,restore_reports=None):
        if set(self.rows)!=self.expected:
            raise ValueError('Incomplete evaluation; cannot compute final statistics')
        self.manifest.update(status='COMPLETE',actual_rows=len(self.rows),predictions_file='predictions.jsonl')
        if restore_reports:
            self.manifest['restore_reports']=restore_reports
        self._write_manifest()
        return self.manifest

def read_complete(directory):
    root=Path(directory); manifest=json.loads((root/'manifest.json').read_text())
    if manifest['status']!='COMPLETE':
        raise ValueError('Final statistics require a COMPLETE evaluation')
    path=root/manifest['predictions_file']
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Prediction path escapes output directory')
    with path.open() as stream:
        rows=[json.loads(line) for line in stream]
    keys=[r['method']+':'+r['id'] for r in rows]
    expected={m+':'+i for m in manifest['methods'] for i in manifest['expected_entry_ids']}
    if len(keys)!=len(set(keys)) or set(keys)!=expected or len(rows)!=manifest['actual_rows']:
        raise ValueError('Complete evaluation does not cover the full population')
    if any(r.get('job_id')!=k or not isinstance(r.get('correct'),bool) for r,k in zip(rows,keys)):
        raise ValueError('Invalid prediction identity or primary score')
    return manifest,rows
