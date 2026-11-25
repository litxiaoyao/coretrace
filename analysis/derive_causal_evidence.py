#!/usr/bin/env python3
"""Derive matched causal evidence from a fixed repository snapshot.

No model, tokenizer, training, or plotting code is invoked. Released linear
reader weights are reapplied to archived paragraph features. Prediction rows
are joined by their original receiver/source identifiers. All inputs are read
with ``git show`` so sparse checkouts need not materialize large archives.

Run from the repository root::

    python analysis/derive_causal_evidence.py

The default revision is the frozen V3 evidence snapshot. An explicit
``--revision`` may be supplied to audit another snapshot.

This writes only analysis/internal/v3_causal_evidence.json and its Markdown
report. analysis/plot_results.py remains the sole numerical plotting entry.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODELS = ("qwen3_4b", "qwen3_8b", "llama3_8b")
FACTOR_ARMS = ("native", "mass_only", "conditional_only", "both")
ACCESS_ARMS = ("native", "oracle_second_paragraph", "oracle_first_paragraph",
               "lengthmatched_other_paragraph")
MAIN_SUBGROUP = "full_decoded_known_constituents_native_failure"
BOOTSTRAP_SEED = 20261125
BOOTSTRAP_REPS = 10000


class Snapshot:
    def __init__(self, revision: str):
        self.commit = self.git("rev-parse", revision).decode().strip()
        self.paths = self.git("ls-tree", "-r", "--name-only", self.commit).decode().splitlines()
        self.provenance: dict[str, dict[str, Any]] = {}

    @staticmethod
    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", *args], cwd=ROOT)

    def read(self, path: str) -> bytes:
        data = self.git("show", f"{self.commit}:{path}")
        self.provenance[path] = {
            "path": path, "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        return data

    def json(self, path: str) -> Any:
        return json.loads(self.read(path))

    def records(self, prefix: str):
        paths = sorted(p for p in self.paths
                       if p == prefix + ".gz" or p.startswith(prefix + ".gz.part"))
        if not paths:
            raise ValueError(f"Missing prediction/feature archive: {prefix}")
        compressed = b"".join(self.read(p) for p in paths)
        with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as handle:
            for line in handle:
                yield json.loads(line)


def native_readout(snapshot: Snapshot, corpus: dict) -> dict:
    """Reapply the released float32 linear readout, without refitting it."""
    output = {}
    for model in MODELS:
        print(f"Native address features: {model}", flush=True)
        readers = {
            name: snapshot.json(f"outputs/{model}/native_readout/{filename}")
            for name, filename in (("full", "address_readout.json"),
                                   ("attention", "attention_readout.json"),
                                   ("metadata", "metadata_readout.json"))
        }
        complete = snapshot.json(f"outputs/{model}/native_readout/complete.json")
        results = []
        for row in snapshot.records(f"outputs/{model}/native_readout/features.jsonl"):
            if row["split"] != "test":
                continue
            source = corpus[row["source_id"]]
            titles = [p[0] for p in source["original_context"]]
            target = titles.index(source["edges"]["second_target"]["title"])
            first = titles.index(source["edges"]["first_target"]["title"])
            other = [i for i in range(len(titles)) if i not in (first, target)]
            columns, masses = [], {}
            for mode in ("all_question_mean", "last_question"):
                observed = []
                for layer in sorted(row["features"], key=int):
                    block = row["features"][layer]
                    index = {head: i for i, head in enumerate(block["heads"])}
                    for head in sorted(index):
                        # Archived values are raw paragraph attention mass, not
                        # logged features. Average these values before logging.
                        values = np.asarray(block[mode][index[head]], dtype=np.float32)
                        observed.append(values)
                        columns.append(np.log(np.maximum(values, 1e-8)))
                observed = np.stack(observed)
                masses[mode] = {
                    "root": float(observed[:, first].mean()),
                    "bridge": float(observed[:, target].mean()),
                    "other_total": float(observed[:, other].sum(axis=1).mean()),
                    "other_paragraph_mean": float(observed[:, other].mean()),
                }
            columns += [
                np.log(np.asarray([p["key_count"] / row["prompt_tokens"]
                                   for p in row["paragraphs"]], dtype=np.float32)),
                np.asarray([p["title_mentioned_in_question"]
                            for p in row["paragraphs"]], dtype=np.float32),
            ]
            x = np.stack(columns, axis=1)
            decoded = {}
            for name, reader in readers.items():
                z = x[:, reader["feature_columns"]]
                scores = ((z - np.asarray(reader["mean"], dtype=np.float32))
                          / np.asarray(reader["std"], dtype=np.float32)) @ np.asarray(
                              reader["weight"], dtype=np.float32)
                chosen = int(scores.argmax())
                order = list(np.argsort(-scores, kind="stable"))
                decoded[name] = {
                    "chosen": chosen, "correct": chosen == target,
                    "target_rank": order.index(target) + 1,
                    "target_score_margin": float(scores[target])
                    - max(float(s) for i, s in enumerate(scores) if i != target),
                    "top_two_score_gap": float(scores[order[0]] - scores[order[1]]),
                }
            results.append({
                "id": row["id"], "source_id": row["source_id"],
                "prompt_tokens": row["prompt_tokens"],
                "gold_bridge_paragraph": target, "gold_bridge_title": titles[target],
                "root_paragraph": first, "paragraph_count": len(titles),
                "paragraph_key_counts": [p["key_count"] for p in row["paragraphs"]],
                "readout": decoded,
                "native_paragraph_mass_selected_head_mean": masses,
            })
        recomputed = {
            name: {"n": len(results),
                   "correct": sum(r["readout"][name]["correct"] for r in results)}
            for name in readers
        }
        expected = {name: complete["diagnostics"][name]["test"] for name in readers}
        if recomputed != expected:
            raise ValueError(f"Released reader reconstruction differs: {model}")
        output[model] = {
            "population": "1000 canonical test composed sources; frozen native-state reader fitted on 2000 training sources only",
            "recomputed_test_readout": recomputed,
            "matches_released_complete_json": True,
            "reader_settings": {
                name: {k: r[k] for k in ("feature_set", "training_sources", "steps", "lr",
                                         "L2", "seed", "LLM_updates", "scope")}
                for name, r in readers.items()
            },
            "records": sorted(results, key=lambda r: r["id"]),
        }
    return output


def endpoint_type(record: dict) -> str:
    i, j = int(record["cell"][1]), int(record["cell"][2])
    mapping = {"own": f"C{i}{j}", "other_entity_same_relation": f"C{3-i}{j}",
               "same_entity_other_relation": f"C{i}{3-j}",
               "other_entity_other_relation": f"C{3-i}{3-j}"}
    matches = [name for name, cell in mapping.items() if record["endpoint_matches"][cell]]
    return ("other_or_no_eos" if not matches else matches[0]
            if len(matches) == 1 else "overlapping_endpoint_aliases")


def factorial(snapshot: Snapshot) -> dict:
    output = {}
    for model in MODELS:
        print(f"Paired factorial receivers: {model}", flush=True)
        by = defaultdict(dict)
        for row in snapshot.records(f"outputs/{model}/causal_factorization/predictions.jsonl"):
            by[row["id"]][row["method"]] = row
        if len(by) != 100 or any(set(v) != set(FACTOR_ARMS) | {"identity"} for v in by.values()):
            raise ValueError("Incomplete factorial population")
        receivers, bits, quads = [], Counter(), defaultdict(Counter)
        endpoints = {arm: Counter() for arm in FACTOR_ARMS}
        transitions = {arm: Counter() for arm in FACTOR_ARMS[1:]}
        for rid, arms in sorted(by.items()):
            if arms["identity"]["generated_token_ids"] != arms["native"]["generated_token_ids"]:
                raise ValueError("Factorial identity does not preserve native generation")
            values = {a: int(arms[a]["correct"]) for a in FACTOR_ARMS}
            pattern = "".join(str(values[a]) for a in FACTOR_ARMS)
            bits[pattern] += 1
            quad = arms["native"]["cluster_id"]
            quads[quad].update(values)
            quads[quad]["receivers"] += 1
            types = {a: endpoint_type(arms[a]) for a in FACTOR_ARMS}
            for arm, category in types.items():
                endpoints[arm][category] += 1
            for arm in transitions:
                transitions[arm][types["native"], types[arm]] += 1
            receivers.append({
                "id": rid, "source_id": arms["native"]["source_id"],
                "quadruplet_id": quad, "cell": arms["native"]["cell"],
                "correct": values, "correctness_pattern": pattern,
                "answer": {a: arms[a]["answer"] for a in FACTOR_ARMS},
                "endpoint_type": types,
                "input_tokens": {a: arms[a]["input_tokens"] for a in FACTOR_ARMS},
                "generated_token_ids": {a: arms[a]["generated_token_ids"] for a in FACTOR_ARMS},
            })
        qrows = [{"quadruplet_id": q, **dict(v),
                  "interaction_count": v["both"] - v["mass_only"] - v["conditional_only"] + v["native"],
                  "interaction_pp": 25 * (v["both"] - v["mass_only"] - v["conditional_only"] + v["native"])}
                 for q, v in sorted(quads.items())]
        if len(qrows) != 25 or any(q["receivers"] != 4 for q in qrows):
            raise ValueError("Factorial quadruplets are not complete")
        failures = [r for r in receivers if not r["correct"]["native"]]
        rescue_cells = []
        for mass in (0, 1):
            for pattern in (0, 1):
                matched = [r for r in failures if r["correct"]["both"]
                           and r["correct"]["mass_only"] == mass
                           and r["correct"]["conditional_only"] == pattern]
                rescue_cells.append({
                    "mass_correct": bool(mass), "pattern_correct": bool(pattern),
                    "n": len(matched), "source_ids": [r["source_id"] for r in matched],
                    "receiver_ids": [r["id"] for r in matched],
                })
        pairs = []
        for before, after in (("native", "mass_only"), ("native", "conditional_only"),
                              ("native", "both"), ("mass_only", "both"),
                              ("conditional_only", "both")):
            c = Counter((r["correct"][before], r["correct"][after]) for r in receivers)
            pairs.append({"from": before, "to": after, "both_wrong": c[0, 0],
                          "rescued": c[0, 1], "harmed": c[1, 0],
                          "both_correct": c[1, 1], "net_correct": c[0, 1] - c[1, 0]})
        summary = {
            "n": 100, "quadruplets": 25, "arm_order": list(FACTOR_ARMS),
            "correct_counts": {a: sum(r["correct"][a] for r in receivers) for a in FACTOR_ARMS},
            "native_failures": len(failures), "joint_only_rescue": bits["0001"],
            "either_single_rescue": sum(bool(r["correct"]["mass_only"] or r["correct"]["conditional_only"]) for r in failures),
            "only_mass_success": sum(bool(r["correct"]["mass_only"] and not r["correct"]["conditional_only"]) for r in failures),
            "only_pattern_success": sum(bool(r["correct"]["conditional_only"] and not r["correct"]["mass_only"]) for r in failures),
            "both_singles_success": sum(bool(r["correct"]["mass_only"] and r["correct"]["conditional_only"]) for r in failures),
            "both_rescues_native_failure": sum(r["correct"]["both"] for r in failures),
            "complete_quadruplets": {a: sum(q[a] == 4 for q in qrows) for a in FACTOR_ARMS},
            "quad_correct_histogram": {a: [sum(q[a] == n for q in qrows) for n in range(5)] for a in FACTOR_ARMS},
            "quad_interaction_sign": dict(Counter("positive" if q["interaction_count"] > 0
                                                else "negative" if q["interaction_count"] < 0
                                                else "zero" for q in qrows)),
        }
        released = snapshot.json(f"outputs/{model}/causal_factorization/summary.json")
        published_counts = {r["method"]: r["correct"] for r in released["summary"] if r["method"] in FACTOR_ARMS}
        if summary["correct_counts"] != published_counts:
            raise ValueError("Factorial reconstruction differs from released summary")
        output[model] = {
            "summary": summary,
            "correctness_patterns": [{"pattern": f"{i:04b}", "n": bits[f"{i:04b}"]} for i in range(16)],
            "native_failure_both_success_2x2": rescue_cells,
            "paired_transitions": pairs,
            "endpoint_counts": {a: dict(c) for a, c in endpoints.items()},
            "endpoint_transitions_from_native": {
                a: [{"from": s, "to": t, "n": n} for (s, t), n in sorted(c.items())]
                for a, c in transitions.items()},
            "quadruplet_records": qrows, "receiver_records": receivers,
            "released_factorial_contrasts": released["factorial_accuracy"],
            "identity_preserves_native_token_ids_all_100": True,
        }
    return output


def source_bootstrap(subset: list[dict], arms=ACCESS_ARMS) -> dict:
    """Fixed-subgroup, paired source bootstrap; no reader refitting/selection."""
    values = np.asarray([[r["correct"][a] for a in arms] for r in subset], dtype=float)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    distribution = np.empty((BOOTSTRAP_REPS, len(arms)), dtype=float)
    for start in range(0, BOOTSTRAP_REPS, 256):
        stop = min(BOOTSTRAP_REPS, start + 256)
        draw = rng.integers(0, len(subset), size=(stop - start, len(subset)))
        distribution[start:stop] = values[draw].mean(axis=1) * 100
    return {
        "unit": "source within fixed observed subgroup", "reps": BOOTSTRAP_REPS,
        "seed": BOOTSTRAP_SEED, "resampling": "same paired source indices for every arm",
        "rate_CI95_percent": {a: np.quantile(distribution[:, i], [.025, .975]).tolist()
                              for i, a in enumerate(arms)},
        "paired_bridge_minus_control_CI95_pp": {
            a: np.quantile(distribution[:, 1] - distribution[:, i], [.025, .975]).tolist()
            for i, a in enumerate(arms) if i in (2, 3)},
        "scope": "Conditional uncertainty for this fixed subgroup; not reader-training uncertainty or uncertainty in subgroup membership.",
    }


def group_summary(name: str, subset: list[dict]) -> dict:
    n = len(subset)
    native_correct = sum(r["correct"]["native"] for r in subset)
    conditions = {}
    for arm in ACCESS_ARMS:
        correct = sum(r["correct"][arm] for r in subset)
        conditions[arm] = {
            "correct": correct, "accuracy_percent": 100 * correct / n if n else None,
            "rescued_from_native": sum(not r["correct"]["native"] and r["correct"][arm] for r in subset),
            "harmed_from_native": sum(r["correct"]["native"] and not r["correct"][arm] for r in subset),
            "net_correct_vs_native": correct - native_correct,
        }
    masses = {mode: {role: float(np.mean([
        r["native_paragraph_mass_selected_head_mean"][mode][role] for r in subset]))
        for role in ("root", "bridge", "other_total", "other_paragraph_mean")}
        for mode in ("all_question_mean", "last_question")} if n else {}
    return {
        "name": name, "n": n, "native_correct": native_correct,
        "source_ids": [r["source_id"] for r in subset],
        "conditions": conditions,
        "native_paragraph_mass_means": masses,
        "native_root_exceeds_bridge_count": sum(
            r["native_paragraph_mass_selected_head_mean"]["all_question_mean"]["root"]
            > r["native_paragraph_mass_selected_head_mean"]["all_question_mean"]["bridge"]
            for r in subset),
    }


def address_access(snapshot: Snapshot, readouts: dict) -> dict:
    output = {}
    for model in MODELS:
        print(f"Same-source canonical access join: {model}", flush=True)
        access, event_checks = defaultdict(dict), Counter()
        for row in snapshot.records(f"outputs/{model}/causal_access/predictions.jsonl"):
            access[row["id"]][row["method"]] = {
                k: row.get(k) for k in ("id", "source_id", "correct", "answer", "generated_token_ids",
                                       "input_tokens", "source_paragraph", "source_title",
                                       "original_context_unchanged", "cluster_id", "split_cluster_id")}
            access[row["id"]][row["method"]]["source_key_count"] = len(row["source_keys"])
            for event in row["budget_events"]:
                event_checks["events"] += 1
                event_checks["invalid_rows"] += event["invalid_rows"]
                event_checks["valid_rows"] += event["valid_rows"]
        core = {(r["query"], r["source_id"]): r for r in snapshot.records(
            f"outputs/{model}/seed42/evaluation/core/predictions.jsonl") if r["method"] == "native"}
        features = {r["id"]: r for r in readouts[model]["records"]}
        if set(features) != set(access) or len(access) != 1000:
            raise ValueError("Reader and causal-access populations differ")
        joined, checks = [], Counter()
        for rid, arms in sorted(access.items()):
            if set(arms) != set(ACCESS_ARMS):
                raise ValueError("Access arms are incomplete")
            f, native = features[rid], arms["native"]
            sid = native["source_id"]
            core_native, bridge = core["composed", sid], arms["oracle_second_paragraph"]
            root = arms["oracle_first_paragraph"]
            known = core["direct_first", sid]["correct"] and core["direct_target", sid]["correct"]
            tests = {
                "same_feature_access_id_source": f["source_id"] == sid,
                "same_feature_access_prompt_token_count": f["prompt_tokens"] == native["input_tokens"],
                "gold_bridge_index_matches": f["gold_bridge_paragraph"] == bridge["source_paragraph"],
                "gold_bridge_title_matches": f["gold_bridge_title"] == bridge["source_title"],
                "bridge_key_count_matches": f["paragraph_key_counts"][bridge["source_paragraph"]] == bridge["source_key_count"],
                "root_index_matches": f["root_paragraph"] == root["source_paragraph"],
                "principal_access_same_input_token_count": core_native["input_tokens"] == native["input_tokens"],
                "principal_access_same_generated_tokens": core_native["generated_token_ids"] == native["generated_token_ids"],
                "principal_access_same_correctness": core_native["correct"] == native["correct"],
                "all_arms_original_context_unchanged": all(a["original_context_unchanged"] for a in arms.values()),
            }
            checks.update({k: int(v) for k, v in tests.items()})
            joined.append({
                "id": rid, "source_id": sid, "cluster_id": native["cluster_id"],
                "readout": f["readout"], "correct": {a: r["correct"] for a, r in arms.items()},
                "answer": {a: r["answer"] for a, r in arms.items()},
                "core_native_correct": core_native["correct"],
                "core_direct_first_correct": core["direct_first", sid]["correct"],
                "core_direct_target_correct": core["direct_target", sid]["correct"],
                "both_core_constituents_correct": bool(known),
                "access_core_native_tokens_equal": tests["principal_access_same_generated_tokens"],
                "native_paragraph_mass_selected_head_mean": f["native_paragraph_mass_selected_head_mean"],
            })
        required = set(checks) - {"principal_access_same_generated_tokens", "principal_access_same_correctness"}
        if any(checks[k] != 1000 for k in required):
            raise ValueError(f"Canonical input alignment failed: {model}: {dict(checks)}")
        groups = [group_summary("all", joined),
                  group_summary("native_failure", [r for r in joined if not r["correct"]["native"]]),
                  group_summary("known_constituents_native_failure", [r for r in joined
                                if r["both_core_constituents_correct"] and not r["correct"]["native"]])]
        for feature in ("full", "attention", "metadata"):
            for decoded in (True, False):
                stem = feature + ("_decoded" if decoded else "_not_decoded")
                subset = [r for r in joined if r["readout"][feature]["correct"] == decoded
                          and not r["correct"]["native"]]
                groups.append(group_summary(stem + "_native_failure", subset))
                subset = [r for r in subset if r["both_core_constituents_correct"]]
                result = group_summary(stem + "_known_constituents_native_failure", subset)
                if result["name"] == MAIN_SUBGROUP:
                    result["source_bootstrap"] = source_bootstrap(subset)
                    for arm in ACCESS_ARMS:
                        result["conditions"][arm]["source_bootstrap_CI95_percent"] = (
                            result["source_bootstrap"]["rate_CI95_percent"][arm])
                groups.append(result)
        principal_ids = {r["source_id"] for r in joined if r["both_core_constituents_correct"]
                         and r["readout"]["full"]["correct"] and not r["core_native_correct"]}
        access_ids = {r["source_id"] for r in joined if r["both_core_constituents_correct"]
                      and r["readout"]["full"]["correct"] and not r["correct"]["native"]}
        baseline = {
            "access_native_correct": sum(r["correct"]["native"] for r in joined),
            "principal_native_correct": sum(r["core_native_correct"] for r in joined),
            "access_correct_principal_wrong": sum(r["correct"]["native"] and not r["core_native_correct"] for r in joined),
            "access_wrong_principal_correct": sum(not r["correct"]["native"] and r["core_native_correct"] for r in joined),
            "different_generated_token_sequences": sum(not r["access_core_native_tokens_equal"] for r in joined),
            "different_correctness_source_ids": [r["source_id"] for r in joined
                                                 if r["correct"]["native"] != r["core_native_correct"]],
            "principal_decoded_known_failure_n": len(principal_ids),
            "access_decoded_known_failure_n": len(access_ids),
            "excluded_because_access_native_now_correct": sorted(principal_ids - access_ids),
            "included_because_access_native_now_wrong": sorted(access_ids - principal_ids),
        }
        released = snapshot.json(f"outputs/{model}/causal_access/summary.json")
        released_correct = {r["method"]: r["correct"] for r in released["summary"]}
        if released_correct != {a: groups[0]["conditions"][a]["correct"] for a in ACCESS_ARMS}:
            raise ValueError("Reconstructed access totals differ from released summary")
        output[model] = {
            "population": "1000 canonical test composed sources; causal_access's own native baseline defines composed failures",
            "n": 1000, "join_checks_counts_out_of_1000": dict(checks),
            "baseline_comparison": baseline, "access_event_totals": dict(event_checks),
            "subgroups": groups, "receiver_records": joined,
            "main_subgroup_definition": "core native direct_first correct AND core native direct_target correct AND causal_access native composed incorrect AND frozen native full-reader bridge prediction correct",
            "prompt_identity_boundary": "Feature rows do not retain prompt text/hash. Canonical query IDs, source IDs, source paragraph identities, paragraph key counts and input-token counts match; scripts/readout.py and scripts/causal.py both consume unchanged frozen composed queries. This is not a new byte-level prompt comparison.",
        }
        main = next(g for g in groups if g["name"] == MAIN_SUBGROUP)
        print(model, "main subgroup", main["n"],
              {a: main["conditions"][a]["correct"] for a in ACCESS_ARMS}, flush=True)
    return output


def content_exchange(snapshot: Snapshot, factor: dict) -> dict:
    output = {}
    for model in MODELS:
        by = defaultdict(dict)
        for row in snapshot.records(f"outputs/{model}/seed42/causal_content/predictions.jsonl"):
            by[row["id"]][row["method"]] = row
        variants = sorted({k.rsplit("_", 1)[0] for arms in by.values() for k in arms})
        summaries, receivers = {}, []
        for variant in variants:
            pairs = [(arms[variant + "_original"], arms[variant + "_edited"]) for arms in by.values()]
            counts = Counter((a["correct"], b["correct"]) for a, b in pairs)
            same = [(a, b) for a, b in pairs if a["selected_paragraph"] == b["selected_paragraph"]]
            original = sum(a["correct"] for a, b in pairs)
            joint = sum(a["correct"] and b["correct"] for a, b in pairs)
            summaries[variant] = {
                "n": len(pairs), "original_correct": original,
                "edited_correct": sum(b["correct"] for a, b in pairs), "joint_correct": joint,
                "edited_following_given_original_correct": joint / original,
                "obsolete_answer_persistence_on_edited": sum(b["old_alias_em"] for a, b in pairs),
                "original_wrong_edited_correct": counts[False, True],
                "original_correct_edited_wrong": counts[True, False], "both_wrong": counts[False, False],
                "same_selected_paragraph_n": len(same),
                "same_selected_paragraph_original_correct": sum(a["correct"] for a, b in same),
                "same_selected_paragraph_edited_correct": sum(b["correct"] for a, b in same),
                "same_selected_paragraph_joint_correct": sum(a["correct"] and b["correct"] for a, b in same),
                "selection_changed_n": len(pairs) - len(same),
                "selection_note": "Null selections are counted as equal for native/body variants; only final has a deployed selected paragraph.",
            }
        factor_by = {r["id"]: r for r in factor[model]["receiver_records"]}
        alignment = Counter()
        for rid, arms in sorted(by.items()):
            f = factor_by[rid]
            for variant, arm in (("native", "native"), ("native_budget", "mass_only")):
                row = arms[variant + "_original"]
                alignment[variant + "_same_source_id"] += row["source_id"] == f["source_id"]
                alignment[variant + "_same_input_token_count"] += row["input_tokens"] == f["input_tokens"][arm]
                alignment[variant + "_same_generated_tokens"] += row["generated_token_ids"] == f["generated_token_ids"][arm]
            receivers.append({
                "id": rid, "source_id": next(iter(arms.values()))["source_id"],
                "quadruplet_id": next(iter(arms.values()))["cluster_id"],
                "conditions": {name: {key: r[key] for key in (
                    "answer", "correct", "old_alias_em", "new_alias_em", "counterfactual_applied",
                    "word_bag_identical", "character_bag_identical", "selected_paragraph",
                    "address_prefills", "input_tokens", "generated_token_ids")}
                    for name, r in arms.items()},
            })
        output[model] = {
            "population": "100 shared-context discovery receiver sources; recorded run42",
            "variants": variants, "summary": summaries, "receiver_records": receivers,
            "factorial_original_alignment_counts_out_of_100": dict(alignment),
            "all_exchanges_applied": all(r["counterfactual_applied"] for v in by.values() for r in v.values()),
            "all_global_word_and_character_bags_preserved": all(
                r["word_bag_identical"] and r["character_bag_identical"]
                for v in by.values() for r in v.values()),
        }
    return output


def necessity_calibration(snapshot: Snapshot) -> dict:
    output = {}
    for model in MODELS:
        necessity = snapshot.json(f"outputs/{model}/causal_necessity/summary.json")
        selection = snapshot.json(f"outputs/{model}/discovery/SELECTION_FROZEN.json")
        output[model] = {
            "knockout_population": "1000 canonical test sources per query; native output-head knockout, not restoration",
            "knockout_rows": [{k: r[k] for k in ("method", "query", "n", "correct", "accuracy")}
                              for r in necessity["summary"]],
            "discovery_calibration_population": "100 original-context discovery composed sources; these scores selected head count",
            "discovery_calibration_candidates": selection["all_candidates"],
            "selected_head_count": selection["winner"]["n"],
            "selected_head_map": selection["head_map"], "per_head_mass_target": selection["budgets"],
            "random_control": necessity["controls"],
        }
    return output


def markdown(report: dict) -> str:
    lines = ["# V3: matched causal evidence audit", "",
             f"Source snapshot: `{report['source_commit']}`.", "",
             "This audit reads archived predictions/features and frozen reader weights. It performs no model inference, refitting, hyperparameter selection, or experiment modification. Exact arrays, receiver/source IDs, and input SHA-256 hashes are in `v3_causal_evidence.json`.", "",
             "## 1. Locate → Route on the same canonical receivers", "",
             "The primary fixed subgroup requires both native constituent answers to be correct, the native composed answer in the **access experiment** to be incorrect, and the frozen full reader to recover the gold bridge paragraph. Bridge, root, and length-matched-other interventions retain this exact subgroup.", "",
             "| Model | Fixed n | Bridge rescue | Root rescue | Other rescue | Mean root mass | Mean bridge mass |", "|---|---:|---:|---:|---:|---:|---:|"]
    for model in MODELS:
        main = next(g for g in report["address_access"][model]["subgroups"] if g["name"] == MAIN_SUBGROUP)
        cells = []
        for arm in ACCESS_ARMS[1:]:
            c = main["conditions"][arm]
            lo, hi = c["source_bootstrap_CI95_percent"]
            cells.append(f"{c['correct']}/{main['n']} = {c['accuracy_percent']:.2f}% [{lo:.2f}, {hi:.2f}]")
        mass = main["native_paragraph_mass_means"]["all_question_mean"]
        lines.append(f"| {model} | {main['n']} | {' | '.join(cells)} | {100*mass['root']:.2f}% | {100*mass['bridge']:.2f}% |")
    lines += ["", "Intervals use 10,000 paired source-bootstrap draws within the fixed observed subgroup, seed 20261125. They condition on the existing reader and subgroup membership. Native mass is averaged over the stored raw per-head paragraph masses, first across selected heads and then across the fixed sources; it is **not** exp(mean log mass).", "",
              "The Qwen3-8B access baseline has 289/1000 correct versus 292/1000 in principal evaluation: 44 generated token sequences and 13 correctness labels differ. Two originally failed, decoded, constituent-correct sources become correct in the access baseline, changing the relevant denominator from 176 to 174. No extra sources enter that subgroup. The source IDs and all comparison counts are retained in JSON.", "",
              "Feature archives do not store full prompt text or hashes. IDs, source IDs, prompt token counts, annotated bridge/root positions, bridge title and key count all match 1000/1000. The source code for both captures consumes unchanged frozen canonical composed queries. This is a provenance/alignment check, not a claim that prompt bytes were independently compared.", "",
              "Interpretation: these are cases with recoverable addresses but failed composition, and routing mass to the relevant paragraph rescues more of them than the controls. The subgroup does **not** establish that decodability or reader confidence predicts greater rescue probability; the unselected decoded/not-decoded groups are retained in JSON for that reason.", "",
              "## 2. Route × Read: exact rescue sets", "",
              "All four arms use the same 100 receivers in 25 shared-context discovery quadruplets. A joint-only rescue has native, mass-only and pattern-only incorrect and Both correct. The 2×2 below is restricted to native-wrong/Both-correct receivers.", "",
              "| Model | Native errors | Both rescues | Joint-only | Mass only already correct | Pattern only already correct | Both single arms correct |", "|---|---:|---:|---:|---:|---:|---:|"]
    for model in MODELS:
        f = report["factorial"][model]; s = f["summary"]
        counts = {(r["mass_correct"], r["pattern_correct"]): r["n"] for r in f["native_failure_both_success_2x2"]}
        lines.append(f"| {model} | {s['native_failures']} | {s['both_rescues_native_failure']} | {counts[False,False]} | {counts[True,False]} | {counts[False,True]} | {counts[True,True]} |")
    lines += ["", "The joint-only fractions among Both rescues are 4/11, 5/13 and 13/29. A compact stacked rescue-count panel makes this individual-level interaction visible while the existing all-receiver four-arm plot preserves aggregate accuracy and paired interaction intervals. Exact losses and all 16 correctness patterns are retained; this rescue-only panel must not be presented as overall net improvement.", "",
              "Pattern transfer rescue/harm at native mass is 0/6, 4/2 and 3/7; at calibrated mass it is 4/2, 8/1 and 15/3. Four-of-four correct quadruplets change from 0→1, 1→4 and 3→6 under native→Both. Cross-endpoint error classifications are sparse and are not recommended as the main mechanism figure.", "",
              "## 3. Read: original/edited transitions", "",
              "All content variants retain 100 original/edited receiver pairs. Final repair follows the edited value in 77/76/80 and is correct on both original and edited versions in 75/72/77. Its selected paragraph is unchanged for all 100 pairs in every model, despite being recomputed. Original-correct counts are 88/84/88, so the conditional edit-following rates are 75/88, 72/84 and 77/88. This describes the complete procedure; it does not isolate a reader-only effect.", "",
              "The original content native and native-budget records are checked against the factorial native and mass-only records by source, receiver, input token count and generated token sequence. JSON contains exact match counts and complete paired transitions. Null selections in non-selector variants are not evidence of a fixed deployed address.", "",
              "## 4. Curves that exist, and curves that do not", "",
              "Knockout summaries contain selected and layer-matched-random head counts 20/40/80, plus native, for direct-first/direct-target/composed queries on 1000 test sources. One random set is used per count; random-set uncertainty cannot be invented.", "",
              "Separate discovery-only access calibration tested counts 0/20/40/80: Qwen3-4B correct counts [35,36,36,33], Qwen3-8B [45,47,47,45], Llama [45,64,66,58]. These selected the head budget on 100 original-context discovery sources. They are not a paired knockout→restoration experiment and must not be labeled restoration or sufficiency curves. There is no released continuous mass-strength sweep or independently held-out sufficiency/recovery curve.", "",
              "Factorial event logs additionally retain per-head/per-question-row receiver/result mass fractions and alpha-delta L2. They do not retain full token-conditional attention vectors. Middle/later-layer pre-intervention mass can already reflect earlier interventions; it is not uniformly the untouched native state.", "",
              "## 5. Recommended figure group", "",
              "1. **Address routing, full width:** retain all-source destination specificity beside rescue rates on the exact decoded, constituent-correct composition-failure subgroup (n=169/174/209). A concise root/bridge native mass annotation can connect the discovery head-function panel to this same-source test subgroup.",
              "2. **Joint rescue, single column:** display all Both rescues as stacked joint-only versus already rescued by one/both single interventions. Retain all three models and label 4/11, 5/13, 13/29. Keep the existing four-arm aggregate figure nearby.",
              "3. Retain the original/edited content figure as the reading evidence; optionally add the already-recorded stable selected-address fact in its caption. Move answer-table examples to the appendix.", "",
              "## Reproduction", "", "```bash", "python analysis/derive_causal_evidence.py --revision " + report["source_commit"], "```", "",
              "This script is an evidence derivation, not a second plotting entry. It reads blobs from the specified Git snapshot and writes only the JSON/Markdown audit. All original results and Figures 1–3 remain unchanged.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", default="5586f3816903e64334de80e06b74c6d7b1499b18")
    args = parser.parse_args()
    snapshot = Snapshot(args.revision)
    # Record code that defines the feature order, unchanged contexts, and joins.
    for path in ("scripts/readout.py", "scripts/causal.py", "scripts/factorized_causal.py",
                 "coretrace/method/paragraph_features.py", "coretrace/method/address_readout.py"):
        snapshot.read(path)
    corpus = {r["source_id"]: r for r in snapshot.records("data/CoRe-2Wiki-v1.0/corpus.jsonl")}
    readouts = native_readout(snapshot, corpus)
    factors = factorial(snapshot)
    access = address_access(snapshot, readouts)
    content = content_exchange(snapshot, factors)
    inventory = necessity_calibration(snapshot)
    report = {
        "schema_version": 1, "source_commit": snapshot.commit, "status": "COMPLETE",
        "scope": "Derived evidence only; no model inference, refitting, test parameter selection, or experiment modification.",
        "provenance": sorted(snapshot.provenance.values(), key=lambda r: r["path"]),
        "native_readout": readouts, "factorial": factors, "address_access": access,
        "content_exchange": content, "necessity_calibration": inventory,
        "main_address_subgroup": MAIN_SUBGROUP,
        "rescue_cell_order": [[False, False], [False, True], [True, False], [True, True]],
    }
    destination = ROOT / "analysis/internal/v3_causal_evidence.json"
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    destination.with_suffix(".md").write_text(markdown(report), encoding="utf-8")
    print(f"Wrote {destination.relative_to(ROOT)} and .md; {len(snapshot.provenance)} hashed inputs.")


if __name__ == "__main__":
    main()
