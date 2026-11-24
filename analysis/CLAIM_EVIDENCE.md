# Claim–evidence map

This review map accompanies the manuscript; it is not manuscript text. Numbers
are in model order **Qwen3-4B / Qwen3-8B / Llama-3.1-8B**. Percentages refer to
completed-answer exact match unless explicitly identified as address accuracy.

## File conventions

`{m}` expands to `qwen3_4b`, `qwen3_8b`, or `llama3_8b`; `{s}` expands to
`42`, `43`, or `44`. The following keys name the actual result files used below.

| Key | Repository result files |
|---|---|
| **CORE** | `outputs/{m}/seed{s}/evaluation/core/summary.json` and `predictions.jsonl.gz`; the Native reference is in `seed42`. |
| **READER** | `outputs/{m}/native_readout/{address_readout.json,attention_readout.json,metadata_readout.json,complete.json}` and corresponding `outputs/{m}/seed{s}/readout/` files. Feature archives are `features.jsonl.gz.part0000` through `part0002` for Qwen, through `part0005` for Llama. |
| **ACCESS** | `outputs/{m}/causal_access/summary.json`; raw `predictions.jsonl.gz.part0000` through `part0005` for Qwen, through `part0010` for Llama. |
| **FACTORIAL** | `outputs/{m}/causal_factorization/summary.json`; Qwen raw file `predictions.jsonl.gz`, Llama raw files `predictions.jsonl.gz.part0000` and `part0001`. |
| **NECESSITY** | `outputs/{m}/causal_necessity/{summary.json,predictions.jsonl.gz}`. |
| **CONTENT** | `outputs/{m}/seed{s}/causal_content/{summary.json,predictions.jsonl.gz}`. |
| **CAPABILITY** | `outputs/{m}/seed{s}/evaluation/{hotpot,mmlu,gsm8k}/summary.json` and the adjacent prediction archives; FullFT uses `evaluation_fullft` instead of `evaluation`. |
| **TRAIN** | `outputs/{m}/seed{s}/head_tuning/{training.json,microbatch_trace.jsonl.gz}`; FullFT records are in `outputs/{m}/seed{s}/fullft/`. Counts/timings are also in `outputs/tables/{training_costs.csv,inference_costs.csv}`. |

Split archive parts are concatenated in filename order **before** gzip
decompression. `analysis/audit_experiments.py` reads these archives directly.
Figure/table labels below are the LaTeX labels, which remain stable if float
positions or appendix numbering change.

## Main claims and supporting evidence

| Claim and key result | Population and metric | Evidence and implementation | Manuscript placement and interpretation boundary |
|---|---|---|---|
| **Correct constituents can coexist with failed composition.** Native failures are 234/457, 236/462, 243/501: **51.2/51.1/48.5%**. | Fixed native sets with both constituent answers correct, within 1,000 test sources. | **CORE**, `conditional_composition` and native query joins. Definition: `coretrace/eval/summarize.py`; scoring: `coretrace/eval/answer_metrics.py`. | Introduction; Fig. 3, `fig:diagnosis`. An operational EM discrepancy under identical supplied context; not a semantic judgment of every failed response. |
| **Addresses remain recoverable inside those failures.** Full native reader: **169/234, 176/236, 209/243** correct, or **72.2/74.6/86.0%**; metadata: 39.7/42.4/42.8%. | The same native failure sets; paragraph-index accuracy, reader fitted on 2,000 training sources. | **READER** + **CORE**; independent weight/feature replay in `analysis/internal/readout_validation.json`. Code: `coretrace/method/{paragraph_features,address_readout}.py`. | Fig. 3; `tab:readouts`. Decodability establishes available information, not endogenous use or a complete native reasoning circuit. |
| **Localized heads contribute causally.** Chosen-dose knockout gives **7.4/5.5/6.4%** composed accuracy versus **24.4/27.3/29.4%** for matched random heads. | All 1,000 sources, all three query types; doses 20/40/80. | **NECESSITY**; `scripts/necessity.py`; ranking/counts in `outputs/{m}/discovery/{ranking.json,SELECTION_FROZEN.json}`. | Main diagnosis; `fig:localization`, `fig:necessity`, `tab:head_selection`. Knockout also damages constituents. One random set per dose; no composition-exclusive-head claim. |
| **Access is address-specific.** Bridge-mass calibration improves composition by **4.9/5.5/16.0 pp**; root and nearest-length other-paragraph controls reduce accuracy. | All 1,000 composed test questions; paired within each causal run. | **ACCESS**; `scripts/causal.py`; `coretrace/mechanisms/paragraph_attention.py`. Targets/head sets come from `SELECTION_FROZEN.json`. | Fig. 4d, `fig:causal`; `tab:paired_effects`. Annotated addresses are diagnostic only. Qwen8 causal Native is **28.9%**, versus **29.2%** in the main evaluation. |
| **Access changes the utility of the direct-query conditional pattern.** Native/mass/pattern/both: **34/41/28/43**, **48/52/50/59**, **51/64/47/76%**. Interactions: **+8 [1,14], +5 [0,10], +16 [8,25] pp**. | 100 receivers in 25 shared-context discovery quadruplets; paired quadruplet bootstrap. | **FACTORIAL**; `coretrace/mechanisms/factorized_attention.py`, `scripts/factorized_causal.py`, `coretrace/eval/factorial.py`. | Fig. 4a–c; `tab:factorial`. Last-question donor attention is reused across receiver question rows; no donor hidden states/values are copied. Functional interaction at measured settings, not an absolute gate or independent held-out replication. |
| **Repaired answers respond to local fact exchanges.** Edited-value following rises from **26/35/32%** to **77/76/80%**; joint original/edited correctness from **21/29/29%** to **75/72/77%**. | 100 reciprocal exchanges from the same 25 quadruplets; all examples retained. | **CONTENT**; `coretrace/data/derived_views.py`, `scripts/content_causal.py`; invariant checks in `analysis/internal/data_and_derived_views_validation.json`. | Fig. 5, `fig:content`; `tab:content`. Full-input word/character bags are unchanged; selection is recomputed. Tests the deployed procedure, not the semantic contents of a donor pattern. |
| **The complete repair improves composition.** **26.9/29.2/36.4 → 66.8/67.2/69.7%**, using **0.587/0.486/0.940%** trainable model parameters. | All 1,000 composed test sources; adapted scores average three recorded runs. | **CORE**, **TRAIN**; `outputs/tables/tables.csv`; `coretrace/train/selected_heads.py`, `coretrace/method/pipeline.py`, `configs/experiments.json`. Run-averaged intervals: `analysis/internal/clustered_contrasts.json`. | `tab:main`, `tab:parameters`; `fig:ablations`. Mechanism-derived application with constituent losses; not a best-achievable multi-hop-QA comparison. |
| **Reader gains occur exactly where input candidates are ambiguous.** On 103 cases, full-reader bridge choices are **95/96/98**, versus **37** for graph-first; answer EM is **70.2/70.9/76.7%**, versus **36.9/36.9/38.2%**. All other **897** generated sequences agree exactly. | Input-defined subset, without correctness filtering. Every method uses the same scoped body and root-plus-one-candidate rule. | **CORE** + corpus; `analysis/internal/{ambiguous_evidence.json,ambiguous_evidence.csv,test_graph.json}`. Code: `coretrace/method/{title_graph,title_links,text_selector,pipeline}.py`. | Main application; `tab:ambiguity`. Isolates candidate choice, not identical token/compute budgets. Only **103/1,000** composed inputs require an extra readout prefill. |
| **Attention features suffice for the reported composed-score gain.** Attention-only and full readers have equal composed EM in every run; metadata-only yields **64.0/64.6/66.7%**. | Complete test panel and 103-case ambiguous subset. | **CORE**, **READER**; `analysis/internal/ambiguous_evidence.json`; feature ablations in `coretrace/method/address_readout.py`. | Main application; `tab:core_complete`, `tab:ambiguity`, `fig:ablations`. Equal aggregate accuracy does not mean identical choices or predictions. |
| **Recovery coexists with regressions.** Run 42 repairs **189/234, 191/236, 189/243** native failures, while losing **12/223, 16/226, 14/258** native successes. | Native constituent-correct populations held fixed; final composed outcomes only. | **CORE**, `native_conditioned_composition`; `analysis/internal/fixed_population_and_graph_analysis.json`. Definition: `coretrace/eval/summarize.py`. | Appendix application, `tab:core_complete`. A fixed-population analysis; do not recompute the conditioning set after repair. |
| **Restoration improves retention but is not lossless.** Llama GSM8K: **86.05% Native, 48.45% head tuning, 80.36% final**. Other native capability losses remain. | Complete HotpotQA validation 7,405; MMLU test 14,042; GSM8K test 1,319. | **CAPABILITY**; `coretrace/eval/{gsm8k,batched_mmlu}.py`, `scripts/evaluate.py`; scope in `configs/experiments.json`. | `tab:retention`, `tab:capability_full`, `fig:capability_detail`. MMLU uses option probabilities; GSM8K final-line numeric equality. FullFT's zero GSM8K accompanies 1,319/1,319 formatting failures per run, not proof of erased mathematical knowledge. |
| **Answer wording does not account for most of the gap.** Crediting every failed response containing a complete normalized alias still leaves **48.1/49.1/47.3%** failure. | Original native constituent-correct sets; 14/9/6 alias-containing failures generously credited. | `analysis/internal/answer_form_diagnostics.json`; reproducible with `analysis/audit_answer_forms.py` from **CORE** and `data/CoRe-2Wiki-v1.0/aliases.jsonl.gz`. | Appendix scoring; `tab:scoring`. Sensitivity analysis only; alias mention is not a validated semantic-correctness metric. |

## Additional results presented in the revised appendix

The revision includes the complete method-conditioned composition failure table
(`tab:conditional_composition`), fixed-native recovery and retention
(`tab:fixed_population`), all nine composed text-scoring variants (`tab:scoring`),
HotpotQA/GSM8K secondary metrics (`tab:secondary_qa`), and MMLU generated-letter,
formatting, completion, and subject-macro results (`tab:mmlu_generation`).
Their exact sources and full positive-result coverage are recorded in
`analysis/internal/positive_results_revision.md`. These tables preserve every
compared variant, including cases where a component has the best score.

## Scope and reproducibility boundaries

- **Data:** `data/CoRe-2Wiki-v1.0/{dataset.json,splits/train.json,splits/discovery.json,splits/test.json}` define 100/2,000/1,000 sources, with ten original paragraphs each. Construction is in `coretrace/data/builders/{core2wiki.py,selection.json}`. Formal source IDs are disjoint, but preceding development could reuse the panel; 43 test sources share normalized root/bridge groups with training. Every within-test entity group is a singleton. See `analysis/internal/dataset_audit.json`.
- **Runs:** selected-head training has zero-initialized deltas, fixed source order and no dropout. Its loss/gradient trajectories are identical across labels 42/43/44; dispersion is not independent initialization uncertainty. Evaluation batches vary. FullFT uses seed-dependent source order. Details: `analysis/internal/training_seed_validation.json` and each evaluation `manifest.json`.
- **Deployment:** diagnostic support addresses and direct-query donors are privileged. Runtime selection uses input titles/text and training-fitted reader weights. Model-specific restoration scopes were fixed during preceding development, not re-optimized in the recorded suite.
- **Missing original implementation:** the released snapshot omits `coretrace/models/` (including head-slice, deployment, native-loading and CPU-optimizer implementations) and trained slice/checkpoint artifacts. Saved predictions, features, tables and plots can be independently checked; end-to-end training/inference cannot be rerun from this snapshot alone. No replacement implementation was invented. See `analysis/internal/{missing_modules.json,experiment_audit.md}`.
