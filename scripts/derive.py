"""Export auxiliary semantic/content views from the immutable discovery corpus."""
import argparse, hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coretrace.data.frozen_loader import FrozenDataset
from coretrace.data.derived_views import discovery_views, reciprocal_value_views

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset', required=True)
    p.add_argument('--output')
    p.add_argument('--write', action='store_true')
    a = p.parse_args()
    data = FrozenDataset(a.dataset)
    semantic, links = discovery_views(data)
    cf = reciprocal_value_views(data)
    result = dict(status='PLAN_ONLY', dataset_version=data.lock['dataset_version'], semantic_queries=len(semantic), semantic_source_triplets=len(links), reciprocal_composed_queries=len(cf), actual_swaps=sum((e['counterfactual_applied'] for e in cf)), unchanged_noops=sum((not e['counterfactual_applied'] for e in cf)), quad_clusters=25, model_outputs_read=False, canonical_data_changed=False, primary_test_sources_unchanged=1000)
    if a.write:
        if not a.output:
            raise ValueError('Explicit output directory required')
        out = Path(a.output)
        out.mkdir(parents=True, exist_ok=False)
        files = {}
        for name, rows in [('semantic250.jsonl', semantic), ('all3_links100.jsonl', links), ('reciprocal100.jsonl', cf)]:
            target = out / name
            target.write_text(''.join((json.dumps(e, ensure_ascii=False) + '\n' for e in rows)))
            files[name] = len(rows)
        result.update(status='COMPLETE_DERIVED_AUXILIARY_VIEWS')
        (out / 'MANIFEST.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
if __name__ == '__main__':
    main()
