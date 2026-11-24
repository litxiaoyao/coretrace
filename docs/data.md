# Data sources and construction

## CoRe-2Wiki v1.0

Source: [official 2WikiMultiHopQA repository](https://github.com/Alab-NII/2wikimultihop). Obtain the original `data_ids.zip` release with `data_ids/train.json`, `data_ids/dev.json`, and `data_ids/id_aliases.json`; use the entity-ID/alias release, not an unrelated processed dataset or a differently segmented revision. The builder checks source annotations and joins while constructing the data.

```
python scripts/build_data.py --archive /path/to/data_ids.zip --output /new/CoRe-2Wiki-v1.0
```

All original questions, complete contexts, two-hop evidence triples, support sentences and official entity aliases are reconstructed from that archive. The distributed selection contains source IDs and their split order, plus document/support locations for the 25 naturally crossed discovery quadruplets. It contains no model predictions or ready-made generated question text.

The fixed split contains 100 discovery, 2,000 training and 1,000 test sources; every source has composed, direct-first and direct-target questions. The original composed question is unchanged; the two constituent questions are diagnostic probes generated from the annotated relations. Only the 2,000 composed training questions are used for LLM training. Discovery provides localization, best-head-count calibration and derived semantic probes. Final core comparisons use all 1,000 test sources and all three queries.

The discovery quadruplets combine complete real paragraphs from their four original sources. Reciprocal fact-exchange views swap the same relation's object surfaces between two original bridge paragraphs, preserving global character and word occurrence bags. They are auxiliary causal interventions, not unedited natural benchmark examples. Unsupported or ambiguous swaps are explicit no-ops and remain in the ledger. `scripts/derive.py` reproduces these views from the reconstructed corpus.

For the historical source-only selection and eligibility rules, see [the builder description](../coretrace/data/builders/README.md). The fixed IDs intentionally preserve the established research panel; rebuilding does not resample it with a new tokenizer. Train/discovery/test source IDs are disjoint; shared entity groups are available for clustered analysis. Pilot overlap is disclosed rather than described as an untouched test set.

## Complete capability benchmarks

| Benchmark | Source and split | Size | Primary metric |
|---|---|---:|---|
| HotpotQA | `hotpotqa/hotpot_qa`, distractor validation | 7,405 | Answer EM, with F1 and completion diagnostics |
| MMLU | `cais/mmlu`, all/test | 14,042 | ABCD same-prefill option-logprob accuracy |
| GSM8K | `openai/gsm8k`, main/test | 1,319 | Numeric accuracy on final `#### NUMBER` line |

The full-split convention follows Appendix B.1 of the provided **Tracing the Persona Circuit** camera-ready paper. That paper explicitly uses full MMLU/GSM8K/CSQA splits. The provided emotion paper uses benchmark-dependent conventions, including 500 CHAIR images; SunC's provided PDF does not specify the per-benchmark retention sample counts. We therefore do not attribute an unverified full/subset setting to SunC.

```
python scripts/build_benchmarks.py --download --output /new/benchmarks
```

Or reconstruct without downloads:

```
python scripts/build_benchmarks.py \
  --hotpot /path/to/distractor/validation-00000-of-00001.parquet \
  --mmlu /path/to/all/test-00000-of-00001.parquet \
  --gsm8k /path/to/main/test-00000-of-00001.parquet \
  --output /new/benchmarks
```

Repository names, source revisions and prompt definitions are in `scripts/build_benchmarks.py` and `data/benchmarks/datasets.json`. Every source row is included in original order. There is no length-based or performance-based exclusion. These three benchmarks are never used to fit the repair or select its configuration. MMLU and GSM8K use zero-shot prompts; GSM8K allows explicit reasoning. Full coverage and prompting are separate protocol choices.

Original dataset and model licenses remain applicable. Data archives and model weights are not copied from the previous research directory into the software package.
