# Current evidence audit for the manuscript revision

Audit date: 2026-11-24. Source snapshot: `cf00035eb9b71bebf3ae88f76caf30ee9b58065c`.

This audit reads the released experiment code, configurations, training metadata, complete compressed prediction records, and readout feature archives. It changes no experiment inputs, predictions, summaries, or runtime code. The audit was executed against the complete clone while the paper revision uses the sparse working checkout at the same commit. The machine-readable checks are retained under `analysis/internal/` and `analysis/internal/current_audit/`.

## Decision

The most distinctive supported claim is **access-conditioned evidence use in contextual composition**: many failures retain a recoverable bridge-paragraph address; crossing paragraph attention mass with a direct-query within-paragraph pattern changes the pattern's behavioral utility; an input-derived evidence selector and selected-head adaptation turn the diagnostic into a useful repair. The factorial experiment is the scientific hinge. Sparse tuning by itself is a less distinctive contribution, and the selector contributes a substantial part of the application gain.

The resulting story can be stated positively in four steps:

1. Under identical evidence, correct constituent answers coexist with failed composition.
2. Selected-head attention features expose a recoverable bridge address in many failures.
3. Controlled redistribution establishes address specificity and a mass-by-reading interaction on shared-context discovery cases.
4. Evidence selection and targeted adaptation improve held-out source performance; reciprocal fact exchanges demonstrate that the complete procedure follows changed local evidence.

The content experiment tests the fourth step directly. It does not identify mediation of the repair by the same native-model factorial pathway. Paragraph readout, causal intervention, and complete-procedure evaluation should retain distinct roles throughout the paper.

## Reaggregation coverage

| Check | Coverage | Result |
| --- | ---: | --- |
| Prediction manifests and recorded summaries | 90 experiment directories; 991,680 prediction rows | No duplicate/missing IDs, population discrepancies, or summary count mismatches |
| Released linear paragraph readers reapplied to archived features | 12 readers/states; full, attention, and metadata variants | All recorded train/test counts reproduced |
| Aggregate result-table cells | 144 model/benchmark/method/query entries | Counts, means, and sample SDs reproduced |
| Factorial contrasts and cluster-bootstrap intervals | Three models; 100 receivers each | All estimates and intervals reproduced |
| Identity interventions | 300 model/source pairs | Generated token IDs equal native in every pair |
| Reciprocal content summaries | Nine model/run directories; 800 prediction rows each | All before/after, following, persistence, joint, and prefill counts reproduced |
| Selected-head training traces | Nine traces; 2,000 examples each | Within each model, source, loss, and gradient-norm sequences are identical across run IDs |

Recorded outputs: `current_audit/result.json`, `current_audit/additional_checks.json`, `prediction_validation.json`, `prediction_metrics.json`, `readout_validation.json`, `table_validation.json`, `dataset_audit.json`, `test_graph.json`, and `fixed_population_and_graph_analysis.json` under `analysis/internal/`. Byte-identical duplicate snapshots have been consolidated without changing the records.

## Core claims and exact numerical support

All model triples below use Qwen3-4B, Qwen3-8B, Llama-3.1-8B-Instruct order.

### 1. Contextual composition gap

On the 1,000 fixed test sources, native both-constituent-correct populations contain 457/462/501 sources. Compositions fail in 234/236/243 cases: 51.20/51.08/48.50%. Native composed accuracy over all sources is 26.9/29.2/36.4%; native all-three accuracy is 22.3/22.6/25.8%.

Source: `outputs/{model}/seed42/evaluation/core/predictions.jsonl.gz`, matched by `source_id` and the three query types; `coretrace/eval/summarize.py`; fresh fixed-population audit. A method's own constituent-correct subset changes after adaptation, so fixed-native-population recovery is the strongest matched repair result.

### 2. Bridge address recoverability

| Native failure readout | Qwen3-4B | Qwen3-8B | Llama-3.1-8B |
| --- | ---: | ---: | ---: |
| Full features | 169/234 = 72.2% | 176/236 = 74.6% | 209/243 = 86.0% |
| Attention features | 151/234 = 64.5% | 166/236 = 70.3% | 205/243 = 84.4% |
| Metadata features | 93/234 = 39.7% | 100/236 = 42.4% | 104/243 = 42.8% |

Overall full-readout accuracy is native 80.3/83.9/91.9% and adapted 90.3/92.6/95.0%. These are trained probes on log-transformed attention-mass features, with the full variant adding paragraph length and title mention. They establish decodability from those features, not a claim that the unassisted model correctly identifies a bridge internally in a unique representational code. The attention-only comparison gives direct support for information in attention beyond metadata.

Source: `coretrace/method/address_readout.py`, `paragraph_features.py`, `outputs/{model}/native_readout/` and `seed{42,43,44}/readout/`; each reader is fitted in its own model state on 2,000 training sources. All released feature rows and reader weights were reapplied during this audit.

### 3. Address-specific access intervention

Applying discovery-fitted per-head mass targets to the bridge raises composed accuracy by +4.9/+5.5/+16.0 percentage points. Applying the same targets to the root yields -4.6/-5.2/-7.3 points, and a length-matched other paragraph yields -7.4/-4.5/-20.6 points. Every arm contains 1,000 sources and the wrong-address control has zero no-op cases. Qwen3-8B's causal-access native reference is 28.9%, whereas the main batch-4 reference is 29.2%; pair every intervention with its own recorded native reference.

Source: `scripts/causal.py`, `coretrace/mechanisms/paragraph_attention.py`, `outputs/{model}/causal_access/`. The intervention changes attention mass at question-prefill positions, with frozen discovery targets and annotated paragraph locations. These annotated addresses are diagnostic inputs; the deployed selector obtains candidates from the user input.

### 4. Access-by-reading interaction

| Model | Native | Mass | Pattern | Both | Interaction, pp [95% interval] |
| --- | ---: | ---: | ---: | ---: | --- |
| Qwen3-4B | 34 | 41 | 28 | 43 | +8 [1, 14] |
| Qwen3-8B | 48 | 52 | 50 | 59 | +5 [0, 10] |
| Llama-3.1-8B | 51 | 64 | 47 | 76 | +16 [8, 25] |

These are counts/percentages on 100 receivers organized into 25 discovery quadruplets. Interaction is `both - mass - pattern + native`. Bootstrap resamples complete quadruplets, preserving all four arms. Qwen3-8B's interval touches zero; describe consistently positive estimates, with the displayed uncertainty, rather than universal significant interactions.

At native mass, pattern effects are -6/+2/-4 points; at calibrated mass they are +2/+7/+12. Equivalently, the mass effect grows from +7/+4/+13 to +15/+9/+29 when using the direct-query pattern. This is the most compact demonstration of the central finding.

The donor supplies the last-question-token normalized bridge attention distribution; it is copied to every receiver question-token row in the selected heads. Receiver values and output projections are computed in the receiving forward pass. Earlier intervention effects can alter downstream activations naturally. This is more precise than claiming all receiver tensors remain frozen. The outside-bridge distribution is rescaled to keep the attention-row total; the intervention consequently reallocates evidence access across the row.

Source: `scripts/factorized_causal.py`, `coretrace/mechanisms/factorized_attention.py`, `coretrace/eval/factorial.py`, `outputs/{model}/causal_factorization/`. Head selection and tau fitting use discovery sources that also contribute these diagnostic quadruplets. The canonical held-out test result is the separate 1,000-source access experiment, not the 100-receiver factorial experiment.

### 5. Localization

Head-count selection chooses 20/20/40 heads from 20/40/80 candidates. At these selected doses, composed accuracy after knockout is 7.4/5.5/6.4%, compared with 24.4/27.3/29.4% for one layer-matched random set. The heads also strongly affect constituent answering; for Qwen3-4B the direct second-hop score falls from 52.9 to 1.1%.

Source: `coretrace/mechanisms/localization.py`, `scripts/necessity.py`, `outputs/{model}/discovery/SELECTION_FROZEN.json`, `causal_necessity/`. The evidence locates a causally important head set for contextual answering. An exclusive/minimal composition circuit and superiority over random-head *training* are outside the tested design. The sampled random knockout sets preserve per-layer head counts and can overlap the ranked sets; exactly one random set is used per dose/model.

### 6. Repair and its components

| Configuration, composed EM (%) | Qwen3-4B | Qwen3-8B | Llama-3.1-8B |
| --- | ---: | ---: | ---: |
| Native | 26.9 | 29.2 | 36.4 |
| Native + evidence selector | 47.2 | 48.1 | 53.4 |
| Head adaptation | 60.1 | 61.8 | 63.6 |
| Adaptation + fixed restoration | 60.4 | 60.9 | 66.3 |
| Adaptation + restoration + input-order selection | 63.4 | 63.7 | 65.7 |
| Full CoReTrace | 66.8 | 67.2 | 69.7 |
| Full-parameter training, fixed recipe | 57.1 | 55.2 | 35.2 |

Full CoReTrace adds 39.9/38.0/33.3 points over native. All-three accuracy becomes 41.3/45.4/42.3%. On the fixed native failure subsets it repairs 189/191/189 cases, or 80.8/80.9/77.8%, while retaining 94.6/92.9/95.1% of native successes. First-hop performance changes from 87.2/86.0/85.2 to 69.8/73.4/66.0%; those complete outcomes should remain readily available in the appendix and prevent a claim that every constituent skill improves.

The component table belongs close to the application claim: it connects the intervention insight to evidence selection and adapted computation, and shows the substantial contribution of text selection. The FullFT comparison is a fixed same-data/learning-rate recipe. Optimizer implementation, source order, train/eval mode, parameter dtype, and parameterization differ; the evidence supports this evaluated comparison, not all possible full-fine-tuning recipes.

Source: all nine core evaluation prediction archives and corresponding summaries; `outputs/tables/tables.json`; fresh 144-cell validation.

### 7. Ambiguity provides the clearest internal-information-to-application link

On the 1,000 composed test inputs, the graph produces 822 unique-candidate cases, 103 ambiguous cases, and 75 inapplicable/no-candidate cases. The unique candidate matches the annotated bridge in 817/822 cases; 918 inputs include the annotated bridge somewhere in the candidate set. Ambiguous cases comprise 86 pairs, 16 triples, and one four-candidate case.

On the 103 ambiguous cases, input-order choice is correct in 37 cases (35.9%). Full-reader choice is correct in 95/96/98 cases (92.2/93.2/95.1%). Composed EM rises from 36.9/36.9/38.2% with input-order selection to 70.2/70.9/76.7%. Generated token sequences are identical outside the ambiguous subset for input-order and full-reader variants, in every run. The full-panel increments are 3.4/3.5/4.0 points. Attention-only readers reach the same aggregate composed EM as full readers, although some paragraph choices and individual predictions differ.

Source: `coretrace/method/title_graph.py`, `title_links.py`, `text_selector.py`, `pipeline.py`, fresh `test_graph.json` and `fixed_population_and_graph_analysis.json`. The readout runs under the actual adapted/restored body before selected-context answer generation. Unique candidates skip that pass.

### 8. Reciprocal exchanges validate local input dependence

The 100 exchanges preserve exact complete-prompt word and character multisets, question, titles, and paragraph order. Every exchange is valid and changes the input. Native edited-value following is 26/35/32%, and full CoReTrace reaches 77/76/80%. Joint before-and-after correctness is native 21/29/29% and full 75/72/77%. Full obsolete-answer persistence is 9/7/4%; adapted/restored full-context persistence is 17/23/16%. Each result is identical across the recorded runs.

Source: `coretrace/data/derived_views.py`, `scripts/content_causal.py`, nine `causal_content` archives. The complete selector is recomputed on the edited input, so retained-context word bags can change. Phrase the finding as a complete-procedure response to local relation-value attachment under preserved full-input lexical content. Avoid using it as proof of an isolated internal binding mechanism or of mediation through the factorial effect.

## Protocol, scope, and uncertainty

The dataset has disjoint source IDs across 100 discovery, 2,000 training, and 1,000 test sources, each with three queries and ten original paragraphs. Discovery contains 77 official train and 23 official dev sources; all formal training sources are official train and all formal test sources are official dev. Forty-three test sources share transitive root/bridge entity groups with training. Earlier development could reuse discovery/test sources, and model-specific restoration scopes come from that development. Source disjointness is accurate; untouched-test or fully entity-disjoint claims would be inaccurate.

Selected-head training uses 2,000 composed queries, answer-plus-EOS cross-entropy, one fixed-order pass, microbatch size one, accumulation eight, 250 steps, zero FP32 slice deltas, and model eval mode. AdamW uses learning rate 2e-5, betas (0.9,0.999), epsilon 1e-8, zero weight decay, and gradient clipping 1. The exact trainable counts recorded in all runs are 23,592,960; 39,845,888; and 75,497,472, or 0.5865%, 0.4865%, and 0.9402% of their model counts. Reader weights are 42/42/82. Paragraph-label supervision fits the reader separately from answer supervision of the model.

Run IDs 42/43/44 represent recorded executions, with identical selected-head optimization traces. The small nonzero evaluation SDs partly reflect BF16/batch-size changes; they are not independent initialization estimates. Source bootstrap intervals quantify variation in the fixed sample. FullFT uses seed-dependent source order and train mode.

Core and Hotpot accuracy require alias EM and EOS within 32 tokens. For the reported composed scores, this gate agrees with ungated text EM. MMLU uses same-prefill A/B/C/D option probabilities over all 14,042 test items. GSM8K uses final-line numeric equality over all 1,319 test items with 512 tokens; format validity is explicit. The full 7,405-example Hotpot distractor validation split is used.

General capability results support a mixed retention profile. Qwen Hotpot EM improves 3.52/3.90 points, Qwen MMLU changes -0.17/-0.22, Qwen3-8B GSM8K gains 0.83, and Qwen3-4B GSM8K changes -2.35. Llama changes -2.56/-1.44/-5.69 on Hotpot/MMLU/GSM8K. Restoration recovers Llama GSM8K from 48.45 to 80.36 relative to head adaptation alone. It is reasonable to highlight that within-checkpoint recovery while presenting complete benchmark outcomes in a compact table. FullFT GSM8K scores zero because all nine runs fail the specified final-answer format; avoid a blanket claim that the model has lost all arithmetic ability.

The 56.3–57.6% token reduction refers to **answer-generation input tokens** on composed questions. It excludes separate full-context readout prefills. Those prefills occur on 10.3% of composed questions and 190 of all 3,000 triplet queries. Recorded runtimes use different batch sizes and shared scheduling; token saving is the sound efficiency result, and runtime should remain descriptive.

## Reproducibility release gap

The tracked repository omits `coretrace/models/`, including `native`, `deployment`, `head_slices`, and `cpu_adamw`, although 12 import sites require them. This was independently confirmed by the repository tree and imports, and agrees with the earlier `missing_modules.json`. It prevents a complete GPU rerun from the current checkout and direct inspection of the exact head-slice/restoration implementation. The configuration, training metadata, results, selection, intervention, scoring, and analysis code remain available and were audited.

The authorized edit scope is `paper/` and `analysis/`. Restoring these runtime modules would exceed it. Therefore preserve the existing experimental facts, make the manuscript's implementation description precise, deliver a reproducible numerical-analysis package, and identify the release gap once in the delivery notes. Do not manufacture substitute runtime modules, claim a new full-model rerun, or label the current checkout end-to-end executable.

## Suggested manuscript edits from this audit

- Use the same diagnosis in title, abstract, introduction, factorial section, and conclusion: evidence access conditions the usefulness of local reading.
- Present the factorial table/figure with its 25-quadruplet scope and intervals, and pair it with the 1,000-source address-specificity control.
- Place a compact component comparison and the ambiguous-candidate test in the main text. They supply the shortest evidence chain from recovered information to useful repair.
- Describe reciprocal exchanges as validation of the complete procedure's local evidence dependence. Keep original/edited joint correctness visible.
- Retain complete constituent/capability outcomes, random-dose controls, exact transformation equations, development overlap, and deterministic-run details in the appendix. State scope once per experiment rather than repeatedly apologizing for it.
- Preserve the distinction between a training-fitted attention-feature readout, causally consequential heads, factorized attention interventions, and a complete circuit-level explanation.

No discrepancy in the reported main empirical numbers requires user clarification. The current repository release gap is material to reproducibility and should be disclosed at delivery.
