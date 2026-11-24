"""Sensitivity check for answer wording among constituent-correct failures.

This is an intentionally permissive diagnostic, not a replacement scoring
metric. A gold alias appearing inside a response does not guarantee that the
response asserts the correct answer. The official completed-answer EM remains
the primary metric. No model inference is performed.
"""
import json

from audit_experiments import MODELS, records, write_json
from coretrace.eval.answer_metrics import normalize_answer


def main():
    aliases = {
        r["source_id"]: r["queries"]["composed"]
        for r in records("data/CoRe-2Wiki-v1.0/aliases.jsonl")
        if r["global_split"] == "test"
    }
    questions = {
        r["source_id"]: r["question"]
        for r in records("data/CoRe-2Wiki-v1.0/queries.jsonl")
        if r["global_split"] == "test" and r["query"] == "composed"
    }
    report = {}
    for model in MODELS:
        path = f"outputs/{model}/seed42/evaluation/core/predictions.jsonl"
        rows = {
            (r["source_id"], r["query"]): r
            for r in records(path) if r["method"] == "native"
        }
        known = {
            sid for sid, query in rows
            if query == "composed" and rows[sid, "direct_first"]["correct"]
            and rows[sid, "direct_target"]["correct"]
        }
        failures = [rows[sid, "composed"] for sid in sorted(known)
                    if not rows[sid, "composed"]["correct"]]
        contains, canonical = [], []
        for row in failures:
            alias = aliases[row["source_id"]]
            prediction = " " + normalize_answer(row["answer"]) + " "
            hits = [gold for gold in alias["golds"]
                    if normalize_answer(gold)
                    and " " + normalize_answer(gold) + " " in prediction]
            if hits:
                contains.append(dict(
                    source_id=row["source_id"], question=questions[row["source_id"]],
                    answer=row["answer"], gold=alias["gold"], matched_aliases=hits,
                    eos_complete=row["eos_complete"], text_f1=row["text_f1"]))
            if " " + normalize_answer(alias["gold"]) + " " in prediction:
                canonical.append(row["source_id"])
        report[model] = dict(
            native_constituent_correct_n=len(known), n=len(failures),
            contains_any_alias=len(contains), contains_canonical_gold=len(canonical),
            eos_failed=sum(not r["eos_complete"] for r in failures),
            f1_one=sum(r["text_f1"] == 1 for r in failures),
            remaining_failure_rate_if_all_alias_containing_responses_credited=
                (len(failures) - len(contains)) / len(known),
            source=path, examples=contains)
    write_json("answer_form_diagnostics.json", report)
    print(json.dumps({model: {key: value for key, value in row.items()
                             if key != "examples"}
                      for model, row in report.items()}, indent=2))


if __name__ == "__main__":
    main()
