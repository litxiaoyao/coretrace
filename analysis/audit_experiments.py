"""Read-only audit of archived experiments; writes only analysis/internal/.

Run from any directory with Python 3 and NumPy. No model is loaded. Compressed
archives are streamed in memory, including the distributed .partNNNN files.
This is an internal evidence check, not a manuscript component.
"""
from __future__ import annotations
from collections import Counter, defaultdict
import ast
import csv
import gzip
import io
import json
from pathlib import Path
import re
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis/internal"
MODELS = ["qwen3_4b", "qwen3_8b", "llama3_8b"]
sys.path.insert(0, str(ROOT))


def load(path):
    return json.loads((ROOT / path).read_text())


def records(path):
    path = ROOT / path
    if path.exists():
        with path.open() as stream:
            for line in stream:
                if line.strip():
                    yield json.loads(line)
        return
    zipped = Path(str(path) + ".gz")
    parts = [zipped] if zipped.exists() else sorted(zipped.parent.glob(zipped.name + ".part*"))
    if not parts:
        raise FileNotFoundError(path)
    payload = b"".join(p.read_bytes() for p in parts)
    with gzip.GzipFile(fileobj=io.BytesIO(payload)) as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def write_json(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def audit_predictions():
    findings = []
    all_stats = []
    for manifest_path in sorted((ROOT / "outputs").rglob("manifest.json")):
        manifest = json.loads(manifest_path.read_text())
        directory = manifest_path.parent.relative_to(ROOT)
        path = directory / "predictions.jsonl"
        if not list((ROOT / directory).glob("predictions.jsonl*")):
            continue
        expected = set(manifest.get("expected_entry_ids", []))
        methods = set(manifest.get("methods", []))
        seen = set()
        ids_by_method = defaultdict(set)
        groups = defaultdict(Counter)
        discrepancy = []
        events = Counter()
        for row in records(path):
            key = (row["method"], row["id"])
            if key in seen:
                discrepancy.append("duplicate:" + ":".join(key))
            seen.add(key)
            ids_by_method[row["method"]].add(row["id"])
            g = groups[(row["method"], row.get("query", "composed"))]
            g["n"] += 1
            for metric in ["correct", "text_alias_correct", "eos_complete", "format_failure", "logprob_correct", "official_compatible_numeric_correct", "cutoff"]:
                if metric in row:
                    g[metric] += int(bool(row[metric]))
            g["generated_tokens"] += row.get("generated_tokens", 0)
            g["input_tokens"] += row.get("input_tokens", 0)
            g["extra_prefills"] += row.get("selection", {}).get("address_prefills", row.get("address_prefills", 0))
            g["selection_applied"] += int(row.get("selection", {}).get("chosen") is not None)
            g["batch_" + str(row.get("batch_size", 1))] += 1
            for e in row.get("budget_events", row.get("events", [])):
                events["events"] += 1
                for k in ["valid_rows", "invalid_rows", "invalid_source_rows", "invalid_outside_rows", "invalid_donor_rows"]:
                    events[k] += e.get(k, 0)
        if len(seen) != manifest.get("actual_rows", len(seen)):
            discrepancy.append("manifest_actual_count")
        if methods and set(ids_by_method) != methods:
            discrepancy.append("method_set")
        if expected and any(ids != expected for ids in ids_by_method.values()):
            discrepancy.append("entry_id_set")
        summary_path = manifest_path.parent / "summary.json"
        if summary_path.exists():
            summary = json.loads(summary_path.read_text())
            for row in summary.get("summary", []):
                if "method" not in row:
                    continue
                g = groups[(row["method"], row.get("query", "composed"))]
                for k in ["n", "correct", "text_alias_correct", "eos_complete", "format_failure", "logprob_correct"]:
                    if k in row and row[k] != g[k]:
                        discrepancy.append(f"summary:{row['method']}:{row.get('query')}:{k}")
        for (method, query), g in groups.items():
            all_stats.append(dict(directory=str(directory), method=method, query=query, **dict(g)))
        findings.append(dict(directory=str(directory), rows=len(seen), methods=len(ids_by_method), errors=discrepancy, events=dict(events)))
        print(json.dumps(dict(directory=str(directory), rows=len(seen), errors=discrepancy)), flush=True)
    write_json("prediction_validation.json", findings)
    write_json("prediction_metrics.json", all_stats)
    return findings, all_stats


def dataset_and_graph():
    from coretrace.method.title_graph import single_root_graph
    from coretrace.data.builders.core2wiki import norm, title_key
    sources = list(records("data/CoRe-2Wiki-v1.0/corpus.jsonl"))
    queries = list(records("data/CoRe-2Wiki-v1.0/queries.jsonl"))
    by_source = {r["source_id"]: r for r in sources}
    summary = {}
    graph_rows = []
    for split in ["discovery", "train", "test"]:
        ss = [r for r in sources if r["global_split"] == split]
        groups = Counter(r["cluster_id"] for r in ss)
        roots = set(r["root"] for r in ss)
        bridges = set(r["bridge"] for r in ss)
        summary[split] = dict(n=len(ss), clusters=len(groups), largest_cluster=max(groups.values()), unique_roots=len(roots), unique_bridges=len(bridges), parent_splits=dict(Counter(r["official_parent_split"] for r in ss)), relation1=dict(Counter(r["relation1"] for r in ss)), relation2=dict(Counter(r["relation2"] for r in ss)), paragraphs=dict(Counter(len(r["original_context"]) for r in ss)), annotation_exceptions=sum(bool(r["chain_validation"]["flags"]) for r in ss))
    groups = defaultdict(set)
    for r in sources:
        groups[r["cluster_id"]].add(r["global_split"])
    summary["test_train_overlap"] = dict(shared_global_clusters=sum({"test", "train"} <= s for s in groups.values()), test_sources_in_train_connected_clusters=sum(r["global_split"] == "test" and "train" in groups[r["cluster_id"]] for r in sources))
    exceptions = []
    for source in sources:
        for role, edge in source["edges"].items():
            title_matches = title_key(edge["subject"]) == title_key(edge["title"])
            object_matches = bool(re.search(r"(?<!\w)" + re.escape(norm(edge["object"])) + r"(?!\w)", norm(edge["text"])))
            if not title_matches or not object_matches:
                exceptions.append(dict(source_id=source["source_id"], split=source["global_split"], edge=role,
                                       subject_title_matches=title_matches, literal_object_matches=object_matches,
                                       subject=edge["subject"], title=edge["title"], object=edge["object"],
                                       support_sentence=edge["text"]))
    write_json("discovery_annotation_exceptions.json", dict(
        subject_title_mismatches=sum(not row["subject_title_matches"] for row in exceptions),
        literal_object_mismatches=sum(not row["literal_object_matches"] for row in exceptions),
        note="Ten discovery subjects differ from support titles; one has Pakistan as object but Pakistani in the sentence. The original generic flag does not distinguish these causes.",
        rows=exceptions))
    for q in queries:
        if q["global_split"] != "test" or q["query"] != "composed":
            continue
        source = by_source[q["source_id"]]
        titles = [p[0] for p in source["original_context"]]
        graph = single_root_graph(q["prompt"], titles)
        target = titles.index(source["edges"]["second_target"]["title"])
        graph_rows.append(dict(id=q["id"], source_id=q["source_id"], root=graph["root"], neighbors=graph["neighbors"], n_candidates=len(graph["neighbors"]), target=target, target_available=target in graph["neighbors"], graphfirst_correct=bool(graph["neighbors"] and graph["neighbors"][0] == target), reason=graph["reason"]))
    summary["test_graph"] = dict(n=1000, candidate_count=dict(Counter(r["n_candidates"] for r in graph_rows)), target_in_candidates=sum(r["target_available"] for r in graph_rows), first_candidate_correct=sum(r["graphfirst_correct"] for r in graph_rows))
    write_json("dataset_audit.json", summary)
    write_json("test_graph.json", graph_rows)
    return graph_rows


def key_evidence(graph_rows):
    report = {}
    graph_by_id = {r["id"]: r for r in graph_rows}
    for model in MODELS:
        root = Path("outputs") / model
        core_by_seed = {}
        for seed in [42, 43, 44]:
            rows = list(records(root / f"seed{seed}/evaluation/core/predictions.jsonl"))
            core_by_seed[seed] = {(r["method"], r["query"], r["source_id"]): r for r in rows}
        reference = core_by_seed[42]
        source_ids = sorted({sid for method, query, sid in reference if method == "native"})
        known = [sid for sid in source_ids if reference["native", "direct_first", sid]["correct"] and reference["native", "direct_target", sid]["correct"]]
        failed = [sid for sid in known if not reference["native", "composed", sid]["correct"]]
        solved = set(known) - set(failed)
        per_seed = {}
        for seed, rows in core_by_seed.items():
            methods = sorted(set(m for m, q, s in rows))
            per_seed[seed] = {}
            for method in methods:
                rs = [rows[method, "composed", sid] for sid in source_ids]
                buckets = {}
                for name, predicate in [("no_candidates", lambda n: n == 0), ("unique_candidate", lambda n: n == 1), ("ambiguous_candidates", lambda n: n > 1)]:
                    kept = [r for r in rs if predicate(graph_by_id[r["id"]]["n_candidates"])]
                    buckets[name] = dict(n=len(kept), correct=sum(r["correct"] for r in kept), selected_correct=sum(r["selection"].get("chosen") == graph_by_id[r["id"]]["target"] for r in kept if r["selection"].get("chosen") is not None))
                per_seed[seed][method] = dict(composed_correct=sum(r["correct"] for r in rs), native_known_correct=sum(rows[method, "composed", sid]["correct"] for sid in known), rescued=sum(rows[method, "composed", sid]["correct"] for sid in failed), lost=sum(not rows[method, "composed", sid]["correct"] for sid in solved), graph_buckets=buckets)
            for subset, predicate in [("other_897", lambda n: n <= 1), ("ambiguous_103", lambda n: n > 1)]:
                pairs = [(rows["graphfirst", "composed", sid], rows["final", "composed", sid]) for sid in source_ids if predicate(graph_by_id[rows["final", "composed", sid]["id"]]["n_candidates"])]
                per_seed[seed]["comparison_" + subset] = dict(n=len(pairs), correctness_changed=sum(a["correct"] != b["correct"] for a,b in pairs), generated_ids_changed=sum(a["generated_token_ids"] != b["generated_token_ids"] for a,b in pairs), final_gains=sum(not a["correct"] and b["correct"] for a,b in pairs), final_losses=sum(a["correct"] and not b["correct"] for a,b in pairs))
        single = {r["source_id"]: r for r in records(root / "causal_access/predictions.jsonl") if r["method"] == "native"}
        batch_diffs = [dict(source_id=sid, batch1_correct=single[sid]["correct"], main_correct=reference["native", "composed", sid]["correct"], batch1_answer=single[sid]["answer"], main_answer=reference["native", "composed", sid]["answer"]) for sid in source_ids if single[sid]["generated_token_ids"] != reference["native", "composed", sid]["generated_token_ids"]]
        report[model] = dict(native_known=len(known), native_failures=len(failed), native_known_solved=len(solved), per_seed=per_seed, native_batch_difference=batch_diffs)
    write_json("fixed_population_and_graph_analysis.json", report)
    return report


def missing_internal_imports():
    findings = []
    for p in list((ROOT / "coretrace").rglob("*.py")) + list((ROOT / "scripts").rglob("*.py")):
        tree = ast.parse(p.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            module = node.module or ""
            if node.level:
                base = p.parent
                for _ in range(node.level - 1):
                    base = base.parent
                target = base.joinpath(*module.split("."))
            elif module.startswith("coretrace"):
                target = ROOT.joinpath(*module.split("."))
            else:
                continue
            if not target.is_dir() and not target.with_suffix(".py").exists():
                findings.append(dict(importer=str(p.relative_to(ROOT)), line=node.lineno, module=("." * node.level) + module, absent_path=str(target.relative_to(ROOT))))
    write_json("missing_modules.json", findings)
    return findings


def audit_readouts():
    """Reapply released reader weights to every archived train/test feature row."""
    import numpy as np
    sources = {r["source_id"]: r for r in records("data/CoRe-2Wiki-v1.0/corpus.jsonl")}
    report = []
    for model in MODELS:
        directories = [Path("outputs") / model / "native_readout"] + [Path("outputs") / model / f"seed{seed}/readout" for seed in [42, 43, 44]]
        reference = {(r["query"], r["source_id"]): r for r in records(Path("outputs") / model / "seed42/evaluation/core/predictions.jsonl") if r["method"] == "native"}
        for directory in directories:
            readers = {name: load(directory / filename) for name, filename in [("full", "address_readout.json"), ("attention", "attention_readout.json"), ("metadata", "metadata_readout.json")]}
            counts = {name: {split: Counter() for split in ["train", "test"]} for name in readers}
            failure_counts = {name: Counter() for name in readers}
            for row in records(directory / "features.jsonl"):
                cols = []
                for mode in ["all_question_mean", "last_question"]:
                    for layer in sorted(row["features"], key=int):
                        block = row["features"][layer]
                        index = {head: i for i, head in enumerate(block["heads"])}
                        for head in sorted(index):
                            cols.append(np.log(np.maximum(np.array(block[mode][index[head]], dtype=np.float32), 1e-8)))
                cols += [np.log(np.array([p["key_count"] / row["prompt_tokens"] for p in row["paragraphs"]], dtype=np.float32)), np.array([p["title_mentioned_in_question"] for p in row["paragraphs"]], dtype=np.float32)]
                x = np.stack(cols, axis=1)
                source = sources[row["source_id"]]
                target = [p[0] for p in source["original_context"]].index(source["edges"]["second_target"]["title"])
                for name, reader in readers.items():
                    z = x[:, reader["feature_columns"]]
                    scores = ((z - np.array(reader["mean"], dtype=np.float32)) / np.array(reader["std"], dtype=np.float32)) @ np.array(reader["weight"], dtype=np.float32)
                    counts[name][row["split"]]["n"] += 1
                    counts[name][row["split"]]["correct"] += int(scores.argmax() == target)
                    sid = row["source_id"]
                    if row["split"] == "test" and reference["direct_first", sid]["correct"] and reference["direct_target", sid]["correct"] and not reference["composed", sid]["correct"]:
                        failure_counts[name]["n"] += 1
                        failure_counts[name]["correct"] += int(scores.argmax() == target)
            expected = load(directory / "complete.json")["diagnostics"]
            result = {name: {split: dict(c) for split, c in value.items()} for name, value in counts.items()}
            report.append(dict(directory=str(directory), recomputed=result, expected=expected, equal=result == expected, native_composition_failure_readout={name: dict(c) for name,c in failure_counts.items()}))
    write_json("readout_validation.json", report)
    return report


def export_focus_tables():
    """Compact, source-linked data for the additional ambiguity result."""
    import numpy as np
    evidence = load("analysis/internal/fixed_population_and_graph_analysis.json")
    rows = []
    for model, result in evidence.items():
        for method in ["native", "native_text", "head_tuning", "scoped_body", "graphfirst", "final_metadata", "final_attention", "final"]:
            seeds = [42] if method == "native" else [42,43,44]
            values = [result["per_seed"][str(seed)][method]["graph_buckets"]["ambiguous_candidates"] for seed in seeds]
            scores = [r["correct"] / r["n"] for r in values]
            rows.append(dict(model=model, method=method, n=103, seed_count=len(seeds), answer_accuracy_mean=float(np.mean(scores)), answer_accuracy_sample_std=float(np.std(scores, ddof=1)) if len(seeds)>1 else None, bridge_selection_correct=values[0]["selected_correct"] if method not in ["head_tuning", "scoped_body", "native"] else None, bridge_selection_accuracy=values[0]["selected_correct"] / 103 if method not in ["head_tuning", "scoped_body", "native"] else None, source=f"outputs/{model}/seed{{42,43,44}}/evaluation/core/predictions.jsonl.gz; data/CoRe-2Wiki-v1.0/corpus.jsonl.gz.part*; queries.jsonl.gz.part*"))
    with (OUT / "ambiguous_evidence.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    write_json("ambiguous_evidence.json", dict(population="All test composed queries whose input title graph has more than one outgoing candidate from its unique explicitly named root; no correctness filtering", n=103, all_test_n=1000, answer_metric="EOS-gated official-alias exact match", bridge_metric="Selected paragraph equals the official second-hop subject paragraph; diagnostic labels used only after selection", seed_policy="Native reference measured once; other scores are mean and sample SD of recorded runs 42/43/44. This deterministic recipe does not provide independent random-initialization uncertainty.", rows=rows, outside_subgroup={model:{seed:result["per_seed"][seed]["comparison_other_897"] for seed in result["per_seed"]} for model,result in evidence.items()}))
    return rows


def audit_final_table():
    """Match every table cell, including all-three joins, to archived predictions."""
    metrics = load("analysis/internal/prediction_metrics.json")
    counts = {(r["directory"], r["method"], r["query"], "logprob_correct" if r["query"] == "mmlu" else "correct"): r["logprob_correct" if r["query"] == "mmlu" else "correct"] for r in metrics}
    for model in MODELS:
        for seed in [42,43,44]:
            for pipeline in ["evaluation", "evaluation_fullft"]:
                directory = f"outputs/{model}/seed{seed}/{pipeline}/core"
                groups = defaultdict(list)
                for row in records(directory + "/predictions.jsonl"):
                    groups[row["method"], row["source_id"]].append(bool(row["correct"]))
                methods = {m for m,s in groups}
                for method in methods:
                    rs = [values for (m,s),values in groups.items() if m == method]
                    assert len(rs) == 1000 and all(len(v) == 3 for v in rs)
                    counts[directory, method, "all3", "correct"] = sum(all(v) for v in rs)
    checked = []
    table = load("outputs/tables/tables.json")
    for row in table["rows"]:
        errors = []
        for seed, value in row["per_seed_correct"].items():
            pipeline = "evaluation_fullft" if row["method"] == "FullFT" else "evaluation"
            directory = f"outputs/{row['model']}/seed{seed}/{pipeline}/{row['benchmark']}"
            if counts[directory, row["method"], row["query"], row["metric"]] != value:
                errors.append("count")
        values = [v/row["n"] for v in row["per_seed_correct"].values()]
        if abs(statistics.mean(values)-row["mean_accuracy"])>1e-12:
            errors.append("mean")
        if len(values)>1 and abs(statistics.stdev(values)-row["sample_std_accuracy"])>1e-12:
            errors.append("sd")
        checked.append(dict(model=row["model"],benchmark=row["benchmark"],method=row["method"],query=row["query"],errors=errors))
    write_json("table_validation.json",checked)
    return checked


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    missing = missing_internal_imports()
    graphs = dataset_and_graph()
    evidence = key_evidence(graphs)
    export_focus_tables()
    validation, metrics = audit_predictions()
    readers = audit_readouts()
    audit_final_table()
    result = dict(manifests_checked=len(validation), prediction_rows=sum(r["rows"] for r in validation), errors=sum(bool(r["errors"]) for r in validation), missing_import_sites=len(missing), summaries_parsed=len(list((ROOT / "outputs").rglob("summary.json"))))
    write_json("audit_result.json", result)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
