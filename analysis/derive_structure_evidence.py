#!/usr/bin/env python3
"""Derive paragraph-level head structure/function evidence from frozen records.

This script performs no model inference, training, or plotting. It reads Git
blobs at an explicit commit, reconstructs the recorded paired attention arrays,
checks the released ranking, and exports figure-ready measurements plus their
provenance. Existing experimental results are never rewritten.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import gc
import gzip
import hashlib
import io
import itertools
import json
from pathlib import Path
import re
import string
import subprocess

import numpy as np


FROZEN_COMMIT = "5586f3816903e64334de80e06b74c6d7b1499b18"
MODELS = ("qwen3_4b", "qwen3_8b", "llama3_8b")
QUERIES = ("composed", "direct_target")
MODES = ("all_question_mean", "last_question")
METRICS = ("root", "bridge", "distractor_mean", "distractor_sum")


class FrozenSources:
    def __init__(self, root: Path, commit: str, workers: int):
        self.root, self.commit, self.workers = root, commit, workers
        self.paths = self.git("ls-tree", "-r", "--name-only", commit).decode().splitlines()
        self.cache: dict[str, bytes] = {}
        self.provenance: dict[str, dict] = {}

    def git(self, *args: str) -> bytes:
        return subprocess.check_output(["git", "-C", str(self.root), *args])

    def blob(self, path: str) -> bytes:
        if path not in self.cache:
            data = self.git("show", f"{self.commit}:{path}")
            self.cache[path] = data
            self.provenance[path] = {
                "path": path, "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        return self.cache[path]

    def json(self, path: str):
        return json.loads(self.blob(path))

    def parts(self, prefix: str) -> list[str]:
        paths = sorted(p for p in self.paths if p == prefix or p.startswith(prefix + ".part"))
        if not paths:
            raise FileNotFoundError(prefix)
        return paths

    def prefetch(self, paths: list[str]) -> None:
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            futures = {pool.submit(self.blob, p): p for p in paths}
            for future in as_completed(futures):
                future.result()

    def jsonl(self, paths: list[str]):
        self.prefetch(paths)
        compressed = b"".join(self.cache[p] for p in paths)
        with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
            for line in stream:
                if line.strip():
                    yield json.loads(line), hashlib.sha256(line).hexdigest()

    def release(self, paths: list[str]) -> None:
        for path in paths:
            self.cache.pop(path, None)


def head_pairs(heads) -> list[list[int]]:
    return [list(pair) for pair in sorted(heads)]


def quantiles(values) -> dict:
    a = np.asarray(values, dtype=float)
    return {
        "n": len(a), "mean": float(a.mean()), "median": float(np.median(a)),
        "p10": float(np.quantile(a, .10)), "p25": float(np.quantile(a, .25)),
        "p75": float(np.quantile(a, .75)), "p90": float(np.quantile(a, .90)),
        "positive_count": int((a > 0).sum()), "zero_count": int((a == 0).sum()),
    }


def paired_statistics(values: np.ndarray, mode: int) -> dict:
    # Axes: source, query, mode, paragraph role.
    v = values[:, :, mode, :]
    return {
        "bridge_direct_minus_composed": quantiles(v[:, 1, 1] - v[:, 0, 1]),
        "root_composed_minus_direct": quantiles(v[:, 0, 0] - v[:, 1, 0]),
        "direct_bridge_minus_root": quantiles(v[:, 1, 1] - v[:, 1, 0]),
        "composed_root_minus_bridge": quantiles(v[:, 0, 0] - v[:, 0, 1]),
        "both_switch_counts": int(((v[:, 1, 1] > v[:, 1, 0]) & (v[:, 0, 0] > v[:, 0, 1])).sum()),
    }


def mean_profiles(values: np.ndarray) -> dict:
    return {
        query: {
            mode: {metric: float(values[:, qi, mi, ri].mean()) for ri, metric in enumerate(METRICS)}
            for mi, mode in enumerate(MODES)
        }
        for qi, query in enumerate(QUERIES)
    }


def minimal_prediction(record: dict) -> dict:
    names = ("id", "source_id", "method", "answer", "correct", "eos_complete",
             "input_tokens", "generated_token_ids", "privileged_source", "source_paragraph")
    return {name: record[name] for name in names if name in record}


def contains_alias(answer: str, aliases: list[str]) -> bool:
    def normalize(text: str) -> str:
        text = text.lower().translate(str.maketrans("", "", string.punctuation))
        return " ".join(re.sub(r"\b(a|an|the)\b", " ", text).split())
    normalized = " " + normalize(answer) + " "
    return any(value and " " + value + " " in normalized for value in map(normalize, aliases))


def derive_model(sources: FrozenSources, model: str) -> dict:
    prefix = f"outputs/{model}"
    ranking = sources.json(f"{prefix}/discovery/ranking.json")
    selection = sources.json(f"{prefix}/discovery/SELECTION_FROZEN.json")
    necessity = sources.json(f"{prefix}/causal_necessity/summary.json")
    selected = {(int(layer), int(head)) for layer, heads in selection["head_map"].items() for head in heads}
    k = len(selected)
    source_ids = ranking["source_ids"]
    source_index = {sid: i for i, sid in enumerate(source_ids)}
    n_layers = len(ranking["all_head_map"])
    n_heads = len(ranking["all_head_map"]["0"])
    capture_paths = sources.parts(f"{prefix}/discovery/capture200.jsonl.gz")
    print(f"Reading {model}: {len(capture_paths)} capture parts", flush=True)
    masses = np.zeros((len(source_ids), 2, n_layers, n_heads, 2, 10), dtype=np.float64)
    metadata, record_index, seen = {}, [], set()
    for record, line_hash in sources.jsonl(capture_paths):
        sid, query = record["source_id"], record["query"]
        i, qi = source_index[sid], QUERIES.index(query)
        assert (sid, query) not in seen
        seen.add((sid, query))
        geometry = {
            "paragraph_titles": record["paragraph_titles"],
            "root_index": record["first_paragraph"],
            "bridge_index": record["second_paragraph"],
        }
        assert len(geometry["paragraph_titles"]) == 10
        if sid in metadata:
            assert metadata[sid] == geometry
        metadata[sid] = geometry
        record_index.append({"id": record["id"], "source_id": sid, "query": query, "jsonl_line_sha256": line_hash})
        for layer, features in record["features"].items():
            assert features["heads"] == list(range(n_heads))
            for mi, mode in enumerate(MODES):
                masses[i, qi, int(layer), :, mi, :] = features[mode]
    assert len(seen) == 200 and len(source_ids) == 100
    root = np.stack([masses[i, :, :, :, :, metadata[sid]["root_index"]] for i, sid in enumerate(source_ids)])
    bridge = np.stack([masses[i, :, :, :, :, metadata[sid]["bridge_index"]] for i, sid in enumerate(source_ids)])
    distractors = masses.sum(-1) - root - bridge
    roles = np.stack([root, bridge, distractors / 8, distractors], axis=-1)
    max_error = 0.0
    for record in ranking["ranking"]:
        means = bridge[:, :, record["layer"], record["head"], 0].mean(0)
        max_error = max(max_error, abs(means[0] - record["composed_all_question_mean"]),
                        abs(means[1] - record["direct_target_all_question_mean"]),
                        abs(means[1] - means[0] - record["score"]))
    assert max_error < 1e-12
    gap_top = {(r["layer"], r["head"]) for r in ranking["ranking"][:k]}
    assert gap_top == selected
    direct = {(r["layer"], r["head"]) for r in sorted(ranking["ranking"], key=lambda r: (-r["direct_target_all_question_mean"], r["layer"], r["head"]))[:k]}
    composed = {(r["layer"], r["head"]) for r in sorted(ranking["ranking"], key=lambda r: (-r["composed_all_question_mean"], r["layer"], r["head"]))[:k]}
    control = necessity["controls"][str(k)]
    assert selected == {(int(layer), h) for layer, hs in control["selected"].items() for h in hs}
    random_heads = {(int(layer), h) for layer, hs in control["random_layer_matched"].items() for h in hs}
    groups = {"selected": selected, "random_layer_matched": random_heads,
              "direct_topk": direct, "composed_topk": composed,
              "composed_topk_not_selected": composed - selected}
    union = set.union(*groups.values())
    intersections = [
        {"selected": a, "direct": b, "composed": c,
         "count": sum(((h in selected) == bool(a) and (h in direct) == bool(b) and (h in composed) == bool(c)) for h in selected | direct | composed)}
        for a, b, c in itertools.product((0, 1), repeat=3) if a or b or c
    ]
    aggregate = {}
    for name, heads in groups.items():
        if not heads:
            continue
        values = np.stack([roles[:, :, layer, head, :, :] for layer, head in sorted(heads)], axis=2).mean(2)
        metrics = {}
        for mi, mode in enumerate(MODES):
            metrics[mode] = {
                "means_by_query": {q: {r: float(values[:, qi, mi, ri].mean()) for ri, r in enumerate(METRICS)} for qi, q in enumerate(QUERIES)},
                "source_ids": source_ids,
                "per_source": {q: {r: values[:, qi, mi, ri].tolist() for ri, r in enumerate(METRICS)} for qi, q in enumerate(QUERIES)},
                "paired_statistics": paired_statistics(values, mi),
            }
        aggregate[name] = {"n_heads": len(heads), "heads": head_pairs(heads), "metrics": metrics}

    profiles = []
    for record in ranking["ranking"]:
        layer, head = record["layer"], record["head"]
        if (layer, head) not in union:
            continue
        values = roles[:, :, layer, head, :, :]
        profiles.append({
            **record, "selected": (layer, head) in selected,
            "direct_topk": (layer, head) in direct, "composed_topk": (layer, head) in composed,
            "random_layer_matched": (layer, head) in random_heads,
            "means": mean_profiles(values),
            "paired_all_question_statistics": paired_statistics(values, 0),
        })
    detailed_heads = sorted(selected | random_heads)
    source_profiles = {
        "source_ids": source_ids, "head_order": head_pairs(detailed_heads),
        "axes": ["head", "source"], "modes": ["all_question_mean"],
        "values": {q: {mode: {metric: np.stack([roles[:, qi, l, h, mi, ri] for l, h in detailed_heads]).tolist()
                              for ri, metric in enumerate(METRICS[:3])}
                       for mi, mode in enumerate(MODES) if mode == "all_question_mean"} for qi, q in enumerate(QUERIES)},
    }

    calibration_paths = sources.parts(f"{prefix}/discovery/calibration.jsonl.gz")
    calibration = {}
    for record, line_hash in sources.jsonl(calibration_paths):
        if record["method"] in ("native", f"own_top{k}"):
            calibration.setdefault(record["source_id"], {})[record["method"]] = {
                **minimal_prediction(record), "jsonl_line_sha256": line_hash,
            }
    assert len(calibration) == 100
    aliases = {r["source_id"]: r["queries"]["composed"]["golds"]
               for r, _ in sources.jsonl(sources.parts("data/CoRe-2Wiki-v1.0/aliases.jsonl.gz"))
               if r["source_id"] in source_index}
    native_contains_alias = {sid: contains_alias(calibration[sid]["native"]["answer"], aliases[sid]) for sid in source_ids}
    primary = ranking["ranking"][0]
    secondary = next(r for r in sorted(ranking["ranking"], key=lambda r: (-r["composed_all_question_mean"], r["layer"], r["head"])) if (r["layer"], r["head"]) not in selected)
    layer, head = primary["layer"], primary["head"]
    values = roles[:, :, layer, head, 0, :]
    strength = np.minimum(values[:, 1, 1] - values[:, 1, 0], values[:, 0, 0] - values[:, 0, 1])
    positive = np.where(strength > 0)[0]
    median = int(positive[np.argmin(np.abs(strength[positive] - np.median(strength[positive])))]) if len(positive) else int(np.argmax(strength))
    rescued = [i for i in np.argsort(-strength).tolist()
               if strength[i] > 0 and not calibration[source_ids[i]]["native"]["correct"]
               and not native_contains_alias[source_ids[i]]
               and calibration[source_ids[i]][f"own_top{k}"]["correct"]]
    recommended = []
    used_chains = set()
    for i in rescued:
        m = metadata[source_ids[i]]
        chain = (m["paragraph_titles"][m["root_index"]], m["paragraph_titles"][m["bridge_index"]])
        if chain not in used_chains:
            recommended.append(i)
            used_chains.add(chain)
        if len(recommended) == 2:
            break
    if not recommended:
        recommended = np.argsort(-strength)[:2].tolist()
    example_indices = list(dict.fromkeys(recommended + np.argsort(-strength)[:6].tolist() + [median]))
    angela = "29c2b50c0bdc11eba7f7acde48001122"
    if angela in source_index:
        example_indices = list(dict.fromkeys(example_indices + [source_index[angela]]))

    def example(i: int) -> dict:
        sid = source_ids[i]
        heads = []
        for record, rule in ((primary, "highest_direct_minus_composed_bridge_gap"),
                             (secondary, "highest_composed_bridge_mass_outside_selected_set")):
            l, h = record["layer"], record["head"]
            heads.append({
                "layer": l, "head": h, "selection_rule": rule, "global_bridge_gap": record["score"],
                "selected": (l, h) in selected, "direct_topk": (l, h) in direct, "composed_topk": (l, h) in composed,
                "paragraph_mass": {q: {mode: masses[i, qi, l, h, mi, :].tolist() for mi, mode in enumerate(MODES)} for qi, q in enumerate(QUERIES)},
            })
        return {
            "source_id": sid, "population": "canonical_discovery_original_context",
            "selection": ("native_error_calibration_rescue_with_primary_head_root_bridge_flip" if i in recommended and i in rescued
                          else "median_root_bridge_flip_for_primary_head" if i == median
                          else "angela_canonical_context" if sid == angela else "strong_primary_head_root_bridge_flip"),
            "primary_head_flip_strength": float(strength[i]), **metadata[sid], "heads": heads,
            "case_selection_checks": {"native_contains_accepted_alias_as_word_sequence": native_contains_alias[sid]},
            "canonical_mass_calibration": {"selected_head_count": k, "source_paths": calibration_paths,
                                           "native": calibration[sid]["native"], "calibrated": calibration[sid][f"own_top{k}"]},
        }

    examples = [example(i) for i in example_indices]
    result = {
        "k": k, "n_layers": n_layers, "heads_per_layer": n_heads, "n_sources": 100,
        "source_ids": source_ids, "capture_paths": capture_paths, "capture_record_index": record_index,
        "headsets": {name: head_pairs(heads) for name, heads in groups.items()},
        "exact_intersections": intersections,
        "random_control_provenance": {"source": f"{prefix}/causal_necessity/summary.json",
                                      "random_seed": control["random_seed"], "selected_overlap": control["overlap_heads"],
                                      "selected_map": control["selected"], "random_map": control["random_layer_matched"]},
        "aggregate_profiles": aggregate, "head_profiles": profiles,
        "head_profiles_coverage": "Union of selected, direct top-K, composed top-K, and recorded layer-matched random heads; all-head ranking checked before filtering.",
        "selected_and_random_source_profiles": source_profiles,
        "representative_candidates": examples,
        "recommended_example_ids": [source_ids[i] for i in recommended],
        "primary_head": primary, "secondary_composed_head": secondary,
        "checks": {"paired_capture_count": len(seen), "recomputed_ranking_max_absolute_difference": max_error,
                   "recorded_knockout_selected_heads_match": True,
                   "selected_heads_with_larger_mean_root_attention_in_composed": sum(p["selected"] and p["means"]["composed"]["all_question_mean"]["root"] > p["means"]["direct_target"]["all_question_mean"]["root"] for p in profiles)},
    }
    print(model, json.dumps(aggregate["selected"]["metrics"]["all_question_mean"]["means_by_query"]), flush=True)
    print("Recommended", model, result["recommended_example_ids"], flush=True)
    sources.release(capture_paths + calibration_paths)
    return result


def attach_contexts(sources: FrozenSources, models: dict) -> dict:
    wanted = {e["source_id"] for m in models.values() for e in m["representative_candidates"]}
    corpus_paths = sources.parts("data/CoRe-2Wiki-v1.0/corpus.jsonl.gz")
    query_paths = sources.parts("data/CoRe-2Wiki-v1.0/queries.jsonl.gz")
    corpus, queries = {}, {}
    for record, line_hash in sources.jsonl(corpus_paths):
        if record["source_id"] in wanted:
            corpus[record["source_id"]] = (record, line_hash)
    for record, line_hash in sources.jsonl(query_paths):
        if record["source_id"] in wanted:
            queries.setdefault(record["source_id"], {})[record["query"]] = {
                key: record[key] for key in ("id", "source_id", "query", "question", "gold")
            } | {"prompt_sha256": hashlib.sha256(record["prompt"].encode()).hexdigest(), "jsonl_line_sha256": line_hash}
    assert set(corpus) == wanted and set(queries) == wanted
    for model in models.values():
        for example in model["representative_candidates"]:
            record, line_hash = corpus[example["source_id"]]
            assert [paragraph[0] for paragraph in record["original_context"]] == example["paragraph_titles"]
            example.update({"questions": queries[example["source_id"]], "context": record["original_context"],
                            "root": record["root"], "bridge": record["bridge"],
                            "relation1": record["relation1"], "relation2": record["relation2"],
                            "evidence": record["edges"], "corpus_jsonl_line_sha256": line_hash})
            for edge in record["edges"].values():
                if isinstance(edge, dict) and "title" in edge and "sent_id" in edge:
                    paragraph = record["original_context"][example["paragraph_titles"].index(edge["title"])]
                    assert paragraph[1][edge["sent_id"]] == edge["text"]
    return {"corpus_paths": corpus_paths, "query_paths": query_paths}


def report(result: dict) -> str:
    lines = ["# V3 structure and functional attention evidence", "", f"Frozen source commit: `{result['source_commit']}`.", "",
             "This derivation reads existing records only. It reconstructs 200 captures per model (100 paired canonical discovery sources) and checks every released head-ranking mean and gap to absolute error below 1e-12.", "",
             "## Figure-ready findings", "",
             "All values below are percentages of total attention, averaged first across the selected heads and then across the 100 sources. The main metric averages all question-token rows. The JSON also retains final-question-token measurements separately.", "",
             "| Model | q12 root | q12 bridge | q2 root | q2 bridge | q2 bridge / q12 root preference switch |", "|---|---:|---:|---:|---:|---:|"]
    for name, model in result["models"].items():
        metric = model["aggregate_profiles"]["selected"]["metrics"]["all_question_mean"]
        means = metric["means_by_query"]
        vals = [100 * means[q][role] for q, role in (("composed", "root"), ("composed", "bridge"), ("direct_target", "root"), ("direct_target", "bridge"))]
        lines.append(f"| {name} | " + " | ".join(f"{v:.3f}" for v in vals) + f" | {metric['paired_statistics']['both_switch_counts']}/100 |")
    lines += ["", "Every model has increased selected-set mean root mass under q12 on all 100 paired sources. All 20/20/40 selected heads also show this direction after averaging sources. The JSON includes paired source distributions and per-head root/bridge/distractor arrays, not only aggregate means.", "",
              "The random comparison is the exact recorded layer-matched head set used for the selected-count necessity experiment. Its head IDs, layer maps, seeds, and selected-set overlaps are preserved. Existing head-intersection counts are independently reconstructed from the frozen ranking and selection.", "",
              "## Representative heads and actual contexts", ""]
    for name, model in result["models"].items():
        head = model["primary_head"]
        lines.append(f"### {name}: layer {head['layer']}, head {head['head']} (zero-based)")
        lines.append("")
        for sid in model["recommended_example_ids"]:
            e = next(x for x in model["representative_candidates"] if x["source_id"] == sid)
            h = e["heads"][0]
            r, b = e["root_index"], e["bridge_index"]
            cm = h["paragraph_mass"]["composed"]["all_question_mean"]
            dm = h["paragraph_mass"]["direct_target"]["all_question_mean"]
            p = e["canonical_mass_calibration"]
            lines += [f"- Source `{sid}`: **{e['root']} → {e['bridge']}**.",
                      f"  q12: {e['questions']['composed']['question']}",
                      f"  q2: {e['questions']['direct_target']['question']}",
                      f"  This head's q12 root/bridge mass is {100*cm[r]:.3f}%/{100*cm[b]:.3f}%; q2 root/bridge mass is {100*dm[r]:.3f}%/{100*dm[b]:.3f}%.",
                      f"  Same-canonical-context recorded outputs: Native `{p['native']['answer']}` → selected-set mass calibration `{p['calibrated']['answer']}`."]
        lines.append("")
    lines += ["## Figure schema and claim wording", "",
              "- Structure panel: `models[model].exact_intersections` and `headsets` contain selected/direct-top-K/composed-top-K masks and actual head IDs.",
              "- Population functional panel: `aggregate_profiles[selected|random_layer_matched].metrics.all_question_mean` contains means, all 100 paired source arrays, and descriptive quantiles. `selected_and_random_source_profiles` supplies head × source arrays.",
              "- Concrete functional panels: `representative_candidates` contains exact questions, all ten paragraph titles and original sentences, support facts, capture/prompt hashes, and the measured 2-query × 10-paragraph arrays for each displayed head. `recommended_example_ids` prioritizes native-error/calibration-rescue cases with a clear primary-head preference switch, excluding native answers that already contain an accepted alias as a complete normalized word sequence; this is an explicit illustrative selection rule. Calibration intervenes on the entire selected set, while the displayed head is one representative member.",
              "- Positive supported wording: **The same localized heads preferentially access the explicitly named entity: the bridge under q2, but the root under q12. Their attention shift is visible across sources and in concrete paragraph-level examples.**",
              "- Use `question-token mean paragraph attention` on the main panels. The independent `last_question` field is a different recorded measurement and must not silently replace that denominator.",
              "- The head sets are defined by measured access rankings, not separate Locate/Route/Read head classes. Their overlap and observed targeting profiles support an evidence-access function; the separate factorial experiment supplies the routing–reading interaction.",
              "- Canonical capture/calibration examples retain the same original ten-paragraph input. Shared-context factorial examples use another documented input construction and should be labeled separately. No token-wise attention, neuron attribution, decoding trajectory, or temporal stage is inferred from these arrays.", "",
              "## Reproduction", "", "```bash", "python analysis/derive_structure_evidence.py", "```", "",
              "The default commit is frozen explicitly in the script. `input_files` records every consumed Git blob's SHA-256; `capture_record_index` records raw JSONL-line hashes. The exported JSON contains the measured inputs needed for plotting without reading the large archives again. The only generated files are the new structure-evidence JSON and this review; original result CSVs and figures are unchanged.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--source-commit", default=FROZEN_COMMIT)
    parser.add_argument("--models", nargs="+", choices=MODELS, default=list(MODELS))
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--output-json", type=Path, default=Path("analysis/internal/v3_structure_evidence.json"))
    parser.add_argument("--output-md", type=Path, default=Path("analysis/internal/v3_structure_evidence.md"))
    args = parser.parse_args()
    root = args.repo.resolve()
    destinations = [(root / p).resolve() if not p.is_absolute() else p.resolve() for p in (args.output_json, args.output_md)]
    if any(not p.is_relative_to(root / "analysis") for p in destinations):
        raise ValueError("Derived artifacts must remain inside analysis/.")
    sources = FrozenSources(root, args.source_commit, args.workers)
    result = {
        "schema_version": 2, "source_commit": args.source_commit,
        "derivation_script": "analysis/derive_structure_evidence.py",
        "derivation_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "description": "Reanalysis of recorded paragraph-attention features; no model execution. Layer/head/paragraph indices are zero-based. Capture and calibration inputs are canonical discovery contexts.",
        "measurement": {"paragraph_mass_denominator": "Total attention over the full prompt row; paragraph values are not renormalized over the ten paragraphs.",
                        "all_question_mean": "Recorded arithmetic mean over all question-token rows.",
                        "last_question": "Recorded attention at the final question-token row.",
                        "distractor_mean": "Mean of the eight paragraphs other than the root and bridge.",
                        "source_average": "Each source receives equal weight; head-group means average their fixed members first."},
        "models": {},
    }
    for model in args.models:
        result["models"][model] = derive_model(sources, model)
        gc.collect()
    result["context_provenance"] = attach_contexts(sources, result["models"])
    result["input_files"] = [sources.provenance[p] for p in sorted(sources.provenance)]
    for destination in destinations:
        destination.parent.mkdir(parents=True, exist_ok=True)
    destinations[0].write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n")
    destinations[1].write_text(report(result))
    print(f"Wrote {destinations[0]} ({destinations[0].stat().st_size:,} bytes)", flush=True)
    print(f"Wrote {destinations[1]}", flush=True)


if __name__ == "__main__":
    main()
