"""Source-aligned contrasts averaged across the three recorded repair runs.

Uses the actual test split entity-cluster IDs. The released test panel happens
to contain 1,000 singleton entity clusters; this is verified, not assumed.
Only analysis/internal/ is written. No model or GPU is used.
"""
from collections import defaultdict
import json
import numpy as np
from audit_experiments import records, MODELS, OUT, write_json
from coretrace.data.builders.core2wiki import clusters


def paired_interval(delta, group_ids, *, reps=2000, seed=42):
    groups = defaultdict(list)
    for index, group in enumerate(group_ids):
        groups[group].append(index)
    parts = list(groups.values())
    totals = np.array([delta[index].sum() for index in parts])
    sizes = np.array([len(index) for index in parts])
    rng = np.random.default_rng(seed)
    distribution = []
    for start in range(0, reps, 64):
        draw = rng.integers(0, len(parts), (min(64, reps-start), len(parts)))
        distribution.extend((totals[draw].sum(1) / sizes[draw].sum(1)).tolist())
    return dict(n=len(delta), clusters=len(parts), estimate=float(delta.mean()),
                paired_cluster_CI95=np.quantile(distribution,[.025,.975]).tolist(),
                bootstrap_reps=reps, bootstrap_seed=seed)


def main():
    sources = [r for r in records("data/CoRe-2Wiki-v1.0/corpus.jsonl") if r["global_split"] == "test"]
    rebuilt, sizes = clusters(sources)
    assert all(rebuilt[r["source_id"]] == r["split_cluster_id"] for r in sources)
    ids = sorted(r["source_id"] for r in sources)
    groups = [rebuilt[sid] for sid in ids]
    report = dict(population="All 1,000 canonical test composed questions",
                  entity_cluster_definition="Transitive shared normalized root/bridge title; exactly the released clusters() rule",
                  test_clusters=len(sizes), cluster_sizes=sorted(sizes.values()),
                  cluster_ids_recomputed_and_equal=True,
                  singleton_note="All test entity clusters have size one, so entity-cluster and source-paired bootstrap are identical for this panel.",
                  recorded_run_policy="Average each source's correctness across configured repair runs 42/43/44 before resampling sources; native reference measured once. These runs are not independent random-initialization trials.",
                  models={})
    for model in MODELS:
        runs = {}
        for seed in [42,43,44]:
            runs[seed] = {(r["method"],r["source_id"]): int(r["correct"]) for r in records(f"outputs/{model}/seed{seed}/evaluation/core/predictions.jsonl") if r["query"] == "composed"}
        native = np.array([runs[42]["native",sid] for sid in ids],dtype=float)
        final = np.array([np.mean([runs[s]["final",sid] for s in [42,43,44]]) for sid in ids])
        first = np.array([np.mean([runs[s]["graphfirst",sid] for s in [42,43,44]]) for sid in ids])
        result = {}
        for name, before, after in [("repair_minus_native",native,final),("repair_minus_graphfirst",first,final)]:
            result[name] = dict(paired_interval(after-before,groups),before_accuracy=float(before.mean()),after_accuracy=float(after.mean()),
                                source=f"outputs/{model}/seed{{42,43,44}}/evaluation/core/predictions.jsonl.gz")
        causal = {(r["method"],r["source_id"]):int(r["correct"]) for r in records(f"outputs/{model}/causal_access/predictions.jsonl")}
        before = np.array([causal["native",sid] for sid in ids],dtype=float)
        after = np.array([causal["oracle_second_paragraph",sid] for sid in ids],dtype=float)
        result["bridge_mass_minus_native"] = dict(paired_interval(after-before,groups),before_accuracy=float(before.mean()),after_accuracy=float(after.mean()),
                                                  source=f"outputs/{model}/causal_access/predictions.jsonl.gz.part*")
        report["models"][model] = result
    write_json("clustered_contrasts.json",report)
    print(json.dumps({m:{k:v for k,v in r.items()} for m,r in report["models"].items()},indent=2))


if __name__ == "__main__":
    main()
