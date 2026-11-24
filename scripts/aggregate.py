"""Write per-model formal tables from complete immutable prediction ledgers."""
import argparse, csv, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from coretrace.eval.aggregate import aggregate
from coretrace.eval.table_sources import export_sources

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    source = Path(args.manifest).resolve()
    result = aggregate(json.loads(source.read_text()), source.parent)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'tables.json').write_text(json.dumps(result, indent=2) + '\n')
    export_sources(result,out)
    fields = ['model', 'benchmark', 'method', 'query', 'metric', 'n', 'mean_accuracy', 'sample_std_accuracy', 'deterministic_reference', 'independent_seed_runs']
    with (out / 'tables.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(result['rows'])
    print(json.dumps(dict(status=result['status'], rows=len(result['rows']), output=str(out)), indent=2))
if __name__ == '__main__':
    main()
