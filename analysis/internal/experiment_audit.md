# Internal experiment review for manuscript reconstruction

This file is an internal working record. It is not manuscript text and must not
be included in the compiled paper. The review concerns repository commit
`a00e62230ab83d4e050e3da29a9e9cfd5e239dd6` and changes only files under
`analysis/`. The original scientific files were read without modification.

## 1. Completed verification and exact scope

- Inventoried all 759 tracked files in `repository_inventory.csv`, including
  every compressed result filename and archive part.
- Read the complete available scientific implementation: dataset construction,
  frozen loader, tokenization, localization, paragraph-mass intervention,
  conditional-attention interchange, reader fitting, input title graph,
  text selection, selected-head and full-parameter training, single/batched
  evaluation, scoring, aggregation, paired intervals, and all experiment CLIs.
- Read the execution and resource-management scripts. These control scheduling,
  memory, loading, restoration and resumption, rather than supplying additional
  scientific hypotheses.
- Read the data and experiment documentation, fixed experiment configuration,
  model-specific scope configurations, evaluation manifests, training records,
  every final experiment summary, and the existing plotting implementation.
- Streamed all 90 prediction archives: **991,680 prediction records**. Every
  method population, expected ID set, row count and reported summary count
  agreed; no duplicate or missing prediction was found. See
  `prediction_validation.json` and `prediction_metrics.json`.
- Independently reapplied all 12 saved reader sets (native plus three deployed
  states for each model), each with full/attention/metadata features, to their
  3,000 archived train/test feature rows. All 36 train/test diagnostic pairs
  matched the released summaries exactly. See `readout_validation.json`.
- Independently checked the 144 final table rows, including all-three-query
  joins and their reported per-run means/sample standard deviations. See
  `table_validation.json`.
- Compared all 2,000 selected-head training loss records and 250 gradient-norm
  records between runs 42/43/44. Source order, loss and gradient norms were
  identical within every model. See `training_seed_validation.json`.
- Reconstructed the released data into a temporary directory outside the
  repository and ran `FrozenDataset.verify()`. Recreated all 250 shared-context
  query views and 100 reciprocal swaps. All 100 swaps actually change content,
  preserve the complete character and word bags, and have disjoint old/new
  normalized answer aliases. See `data_and_derived_views_validation.json`.
- Recomputed the principal paired confidence intervals after first averaging
  each source's outcomes over the three recorded repair runs. The actual test
  entity clusters are all singletons, so source and entity-cluster resampling
  coincide. See `clustered_contrasts.json` and
  `analysis/audit_clustered_contrasts.py`.

### Material unresolved implementation gap

The repository omits the entire `coretrace/models/` package. Twelve static
import sites refer to absent implementation modules, including
`head_slices`, `deployment`, `native`, and `cpu_adamw`; runtime refresh also
names `scoped_rollback`. `git log --all -- coretrace/models` finds no recoverable
history. The unanchored `models/` rule in the root `.gitignore` would ignore
this package, which plausibly explains the omission, but this causal explanation
cannot be established from the archive alone.

Consequently, the released predictions and visible numerical procedures can be
checked, but the exact Q/K/V/O slice implementation, grouped-query-head slice
sharing, deployment rollback hooks and full-parameter optimizer internals
cannot be fully inspected or re-executed. The recorded scopes below are clear;
the low-level implementation is not present. No substitute implementation was
invented. Missing code is a reproducibility issue to tell the author directly;
it is not a reason to discard internally consistent recorded results.

## 2. Result-file and experiment map

`M` denotes one of `qwen3_4b`, `qwen3_8b`, `llama3_8b`; `S` is 42, 43 or 44.
Distributed prediction/features files are `.jsonl.gz` or lossless
`.jsonl.gz.part0000`, `.part0001`, etc. The names below give the logical JSONL
path consumed by the original analysis scripts.

| Experiment | Producer and important implementation | Recorded outputs | Appropriate inference |
|---|---|---|---|
| Canonical data | `coretrace/data/builders/core2wiki.py`, `selection.json` | `data/CoRe-2Wiki-v1.0/{corpus,queries,aliases}.jsonl`, `splits/*.json`, `dataset.json` | Original composed questions and full contexts with two explicit constituent probes |
| Shared-context mechanism views | `coretrace/data/derived_views.py`, `scripts/derive.py` | `mechanism_views/discovery25_quadruplets.jsonl`; derived semantic/reciprocal inputs are reproducible | 25 real crossed quadruplets, 100 composed receivers, 250 total query views |
| Head localization | `scripts/discover.py`, `mechanisms/localization.py` | `outputs/M/discovery/{capture200.jsonl,ranking.json,calibration.jsonl,SELECTION_FROZEN.json,manifest.json}` | Paired direct-target minus composed attention to the bridge paragraph; discovery-only head count and target mass |
| Address recovery | `scripts/readout.py`, `method/{paragraph_features,address_readout}.py` | `outputs/M/native_readout/{features.jsonl,address_readout.json,attention_readout.json,metadata_readout.json,complete.json}` and `seedS/readout/*` | Linear readout of a paragraph address; train annotations only fit the reader |
| Address-specific mass intervention | `scripts/causal.py`, `mechanisms/paragraph_attention.py` | `outputs/M/causal_access/{predictions.jsonl,summary.json,manifest.json}` | Whether changing access to the actual bridge improves answering versus first-source/distractor controls |
| Necessity | `scripts/necessity.py` | `outputs/M/causal_necessity/{predictions.jsonl,summary.json,manifest.json}` | Localized head-output contribution at question-prefill positions, with layer-matched random sets |
| Mass × conditional-attention experiment | `scripts/factorized_causal.py`, `mechanisms/factorized_attention.py`, `eval/factorial.py` | `outputs/M/causal_factorization/{predictions.jsonl,summary.json,manifest.json}` | Functional interaction of access mass and within-paragraph conditional reading |
| Reciprocal content exchange | `scripts/content_causal.py`, `data/derived_views.py` | `outputs/M/seedS/causal_content/{predictions.jsonl,summary.json,manifest.json}` | Local evidence binding under fixed global word/character occurrence counts |
| Selected-head training | `scripts/train.py`, `train/selected_heads.py` | `outputs/M/seedS/head_tuning/{training.json,microbatch_trace.jsonl}` | One epoch answer-only selected-slice learning; saved weights are excluded |
| Application/ablations | `scripts/evaluate.py`, `method/pipeline.py`, `method/text_selector.py`, `method/title_graph.py` | `outputs/M/seedS/evaluation/core/{predictions.jsonl,summary.json,manifest.json}` | Complete-panel task improvement, component value and constituent trade-offs |
| Capability retention | Same evaluation with benchmark-specific scoring | `outputs/M/seedS/evaluation/{hotpot,mmlu,gsm8k}/*` | Full-split capability outcomes under the specified zero-shot prompts |
| Full-parameter comparator | `scripts/fullft_train.py`, `train/fullft.py` | `outputs/M/seedS/fullft/{training.json,microbatch_trace.jsonl,optimizer_trace.jsonl}`; `evaluation_fullft/{core,hotpot,mmlu,gsm8k}/*` | Outcome of the recorded answer-only full-parameter recipe, not best achievable FullFT |
| Aggregation/resources | `scripts/aggregate.py`, `eval/{aggregate,table_sources}.py` | `outputs/tables/{tables.csv,tables.json,sources.json,dataset_statistics.csv,inference_costs.csv,training_costs.csv,cost_sources.json,data_sources.json}` | Cell-level mapping and resource bookkeeping |

The old `outputs/figures/` uses these roles as filenames:
`phenomenon`, `M_head_localization`, `M_address_readout`, `M_causal_access`,
`M_causal_necessity`, `M_causal_factorization`, `M_content_reading`,
`M_application_ablations`, and `comparison_{core,hotpot,mmlu,gsm8k}`.
`M_causal_factorization_data.csv` and `worked_examples.json` provide additional
numeric/example material. The old numerical panels are generic bar/line plots;
they do not determine the new paper's narrative or figure allocation.

## 3. Dataset and evaluation denominators

The source split is discovery 100, train 2,000, test 1,000. Every source has
exactly 10 complete titled paragraphs and three queries. Only composed training
queries update LLM weights. All canonical test sources are official development
examples; all training sources are official training examples. Discovery mixes
77 official training and 23 development examples. The 100 discovery sources
form 25 crossed quadruplets; they are not 100 independent trials for the shared
context mechanism experiments.

The fixed source IDs preserve the earlier research panel. Selection was based
on annotations and input-length rules, not model predictions, but prior
development/formal source reuse was allowed. Thus **do not call the test panel
untouched**. The train/discovery/test source IDs are disjoint. Under the
released transitive root/bridge grouping, the 1,000 test sources occupy 1,000
groups, and 43 test sources share a global group with training sources.
See `dataset_audit.json` for relation distributions and exact counts. Eleven
discovery examples require explicit support-index resolution: ten have
subject-title surface mismatches, and one has the object `Pakistan` expressed
as `Pakistani` in the sentence. The original generic flag calls all eleven
subject-title exceptions, but independent literal checks distinguish the last
case. See `discovery_annotation_exceptions.json`. Train/test have zero exceptions.

For the run-averaged complete-panel repair-versus-native contrast, paired
percentile bootstrap (2,000 replicates, seed 42) gives Qwen4 +39.90 pp
[36.73, 43.03], Qwen8 +38.00 [34.70, 41.40], and Llama +33.30 [30.23, 36.50].
The corresponding repair-versus-graph-first intervals are +3.43 [2.40, 4.63],
+3.50 [2.40, 4.80], and +3.97 [2.87, 5.30]. These intervals describe sampling
variation across the fixed-panel sources, not training-initialization variance.

The three complete external splits are HotpotQA distractor validation 7,405,
MMLU test 14,042 and GSM8K test 1,319. Primary metrics differ deliberately:

- Core/Hotpot: official normalized answer-alias exact match, gated on emitting
  an EOS within 32 generated tokens; text EM/F1 and completion are secondary.
- MMLU: highest probability among native single-token A/B/C/D labels at the
  same initial prefill. Zero-shot, micro-averaged; subject-macro and strict
  generated-letter scores are retained.
- GSM8K: Decimal numerical equality from the required final `#### NUMBER`
  line, up to 512 generated tokens. A valid final numerical answer does not
  require EOS. Format and cutoff are separately recorded.

These are explicit zero-shot prompt definitions, not reproductions of standard
five-shot MMLU or eight-shot GSM8K leaderboard settings.

## 4. Strongest phenomenon and mechanism evidence

All percentages below are percentages, not fractions. Models are ordered
Qwen3-4B, Qwen3-8B, Llama-3.1-8B-Instruct.

### 4.1 Composition failures when both constituent answers are correct

| Model | Native composed | Both constituents correct | Composition failures in that fixed set | Failure rate |
|---|---:|---:|---:|---:|
| Qwen3-4B | 26.9 | 457 | 234 | 51.20 |
| Qwen3-8B | 29.2 | 462 | 236 | 51.08 |
| Llama-3.1-8B | 36.4 | 501 | 243 | 48.50 |

Source: `seed42/evaluation/core/summary.json` and independently joined native
prediction rows. This establishes the failure phenomenon without filtering the
main test denominator. Method-conditioned failure rates change their
denominators and should not be used alone to claim repair. The fixed native
failure sets are the proper repair subset.

### 4.2 Addresses remain recoverable in the failures themselves

| Model | Native full reader, all test | Native attention-only | Metadata-only | Full reader on native known-hop composition failures |
|---|---:|---:|---:|---:|
| Qwen3-4B | 80.3 | 75.0 | 43.5 | 169/234 = 72.22 |
| Qwen3-8B | 83.9 | 79.3 | 43.5 | 176/236 = 74.58 |
| Llama-3.1-8B | 91.9 | 90.9 | 44.1 | 209/243 = 86.01 |

The last column is a newly extracted, useful positive result. It directly links
the address signal to actual composition failures. The corresponding
attention-only failure-subset counts are 151/234, 166/236, 205/243; metadata
counts are 93/234, 100/236, 104/243. This is supervised linear decodability, not
proof that the unmodified model's own output computation uses this address.
Files: `readout_validation.json` and native reader/feature archives.

The deployed-state full reader rises to 90.3/92.6/95.0 on the same 1,000 test
sources; attention-only is 89.6/91.2/94.3. Readers have 42/42/82 coefficients
(two features for each selected head plus two metadata features), trained on
2,000 composed training sources. No bias is needed because an intercept common
to every paragraph cancels in paragraph-wise softmax.

### 4.3 Localized heads matter, but are not composition-exclusive

Discovery selects 20/20/40 heads from candidates 20/40/80. The ranking is the
mean same-source direct-target minus composed bridge-paragraph attention,
averaged over question tokens. The target mass for each head is separately
calibrated from the last direct-target question-token row. Candidate count is
chosen by discovery composed EM; ties prefer fewer heads.

Knocking out selected head outputs at question-prefill positions reduces
composed EM from 26.9/28.9/36.4 to 7.4/5.5/6.4 at each model's selected count;
the corresponding layer-matched random result is 24.4/27.3/29.4. All three
query types are impaired by selected knockouts, especially direct-target.
Therefore describe shared evidence-access contributions rather than a circuit
exclusive to multi-hop composition. One random set is used at each count, with
overlap explicitly allowed; do not invent random-head confidence bands.

### 4.4 Address specificity on all 1,000 test composed questions

| Intervention | Qwen3-4B | Qwen3-8B | Llama-3.1-8B |
|---|---:|---:|---:|
| Native in this experiment | 26.9 | 28.9 | 36.4 |
| Bridge-paragraph mass | 31.8 | 34.4 | 52.4 |
| First-source paragraph mass | 22.3 | 23.7 | 29.1 |
| Length-matched other paragraph | 19.5 | 24.4 | 15.8 |

All arms use identical discovery-frozen head-wise targets. The bridge address
is an annotated diagnostic intervention and is not the deployed selector.
The method sets mass to a calibrated value; it may decrease an individual row's
mass if the native value is already higher. Use **mass calibration/reallocation**,
not an unconditional statement that all interventions amplify attention.

### 4.5 Functional access × local-reading interaction

| Arm | Qwen3-4B | Qwen3-8B | Llama-3.1-8B |
|---|---:|---:|---:|
| Native/identity | 34 | 48 | 51 |
| Mass only | 41 | 52 | 64 |
| Conditional only | 28 | 50 | 47 |
| Both | 43 | 59 | 76 |
| Accuracy interaction, pp | +8 [1, 14] | +5 [0, 10] | +16 [8, 25] |

Intervals are 95% paired bootstraps over 25 quadruplet clusters (2,000 draws).
All 100 receiver queries remain in each arm. Donor and receiver context-token
prefixes are exactly aligned; donor information is the normalized attention
distribution inside the correct paragraph, captured at the last token of the
direct-target question. This conditional is applied to all receiver question
rows. No donor residual, value vector or output projection is transplanted.
Identity preserves exact generated token IDs.

The data support the conclusion that the effect of local reading depends on
how much access the paragraph receives. They do not support uniformly positive
conditional-only effects, significance in all three models, or an anatomically
exclusive sequential three-stage circuit. The same discovery sources selected
the heads and target masses; these are controlled diagnostics, not independent
test generalization. No cache tensor is directly edited, although ordinary
downstream causal effects can change later activations and cache contents.

### 4.6 Content exchange grounds the repair in local evidence

All 100 reciprocal swaps succeeded, with global character and word occurrence
bags preserved. Every query keeps its original question and paragraph order;
the edited target is the other bridge's object under the same relation.
The final selector is recomputed on the edited input.

| Variant | Edited-value following: Q4/Q8/Llama | Joint original-correct then edited-correct: Q4/Q8/Llama |
|---|---|---|
| Native | 26 / 35 / 32 | 21 / 29 / 29 |
| Native + annotated mass | 35 / 37 / 52 | 29 / 31 / 49 |
| Scoped learned body | 64 / 66 / 72 | 57 / 60 / 69 |
| Final repair | 77 / 76 / 80 | 75 / 72 / 77 |

Three recorded runs produce identical content results. Final obsolete-answer
persistence is 9/7/4, compared with body-only 17/23/16. Native-to-final following
improvements are +51/+41/+48 pp, with cluster intervals [41,62]/[28,54]/[36,60]
in run 42. This rules out improvement explained solely by global answer-surface
presence. It does not by itself exclude all lexical extraction strategies.

## 5. Newly surfaced deployable ambiguity result

The input-only title graph has no candidate for 75 of 1,000 test composed
questions, one candidate for 822, and multiple candidates for 103 (86 have two,
16 have three, one has four). The correct bridge is among the candidates for
918/1,000. The selector leaves all 75 no-candidate examples intact and retains
the root plus chosen complete original paragraph for the other 925.

On the pre-defined-by-input 103 ambiguous questions, the learned address reader
selects the correct bridge 95/96/98 times, versus 37 for the graph-first policy.
Metadata-only selects 57/57/59; attention-only selects 94/97/97. These values
are the same across recorded runs. The reader uses an extra full-context
prefill on exactly these 103 examples: **10.3% of composed test queries**.

| Answer accuracy on 103 ambiguous questions | Qwen3-4B | Qwen3-8B | Llama-3.1-8B |
|---|---:|---:|---:|
| Native | 26.21 | 33.98 | 45.63 |
| Native + decoded evidence | 53.40 | 54.37 | 63.11 |
| Selected-head tuning | 60.52 | 66.99 | 67.96 |
| Scoped learned body | 59.87 | 65.05 | 73.14 |
| Graph-first, same body | 36.89 | 36.89 | 38.19 |
| Metadata reader, same body | 43.37 | 45.63 | 47.57 |
| Full reader, same body | 70.23 | 70.87 | 76.70 |

The final-minus-graph-first overall gains, +3.43/+3.50/+3.97 pp, arise entirely
on this subset. Other 897 queries have identical correctness between the two
policies in every run. The machine-readable file additionally checks exact
generated-ID agreement, so prose should use that result if discussing stronger
equivalence. A graph-first policy is weaker than body-only on ambiguous cases;
therefore report body-only alongside graph-first to make actual incremental
value transparent. This is the clearest diagnostic-to-application bridge in
the archive and deserves a main-text panel or compact table.

Files: `ambiguous_evidence.csv`, `ambiguous_evidence.json`,
`fixed_population_and_graph_analysis.json`, `test_graph.json`. Mean/SD are
over the three recorded evaluation runs; native is one deterministic reference.

## 6. Application, ablations, and retention

| Composed EM, mean over recorded runs | Qwen3-4B | Qwen3-8B | Llama-3.1-8B |
|---|---:|---:|---:|
| Native | 26.90 | 29.20 | 36.40 |
| Native + decoded evidence | 47.23 | 48.10 | 53.43 |
| Selected-head tuning | 60.13 | 61.80 | 63.60 |
| Scoped learned body | 60.43 | 60.90 | 66.30 |
| Graph-first, same body | 63.37 | 63.70 | 65.73 |
| Final repair | 66.80 | 67.20 | 69.70 |
| Attention-only reader | 66.80 | 67.20 | 69.70 |
| Metadata-only reader | 64.03 | 64.60 | 66.70 |
| Full-parameter answer-only recipe | 57.13 | 55.17 | 35.20 |

Final repair improves over native by 39.90/38.00/33.30 pp. On fixed native
known-hop failures, it rescues 189/234, 191/236, 189/243 = 80.77/80.93/77.78%.
It also loses some previously correct composed answers: 12/223, 16/226, and
14/258 (Llama run 42; runs 43/44 lose 12). This is repair, not perfect recovery.

The learned body updates 23,592,960 / 39,845,888 / 75,497,472 parameters, about
0.587 / 0.486 / 0.940% of the models. Training uses 2,000 composed examples,
250 optimizer steps, one epoch, answer-plus-EOS CE, learning rate 2e-5,
accumulation 8, zero weight decay, AdamW, and norm clipping 1. These are
full-rank selected Q/K/V/O slices, not low-rank adapters. The final method
and its components share the same selected-head checkpoint.

Recorded restoration scopes (zero-based layer indices) are:

| Model | Restored projections | Token role | Layers |
|---|---|---|---|
| Qwen3-4B | V and O | Prefix before question | 16--19 |
| Qwen3-8B | V and O | Question prefill | 12--19 |
| Llama-3.1-8B | V | Prefix before question | All selected layers |

These scopes came from preceding development and were fixed before the formal
suite; they were not re-optimized on formal results. Avoid portraying them as
newly derived by a released sweep, because that sweep is absent. Reproduce the
scope table in the appendix, without guessing the absent hook internals.

General capability is **better retained than indiscriminate tuning**, not
universally unchanged. Native → final means:

| Benchmark | Qwen3-4B | Qwen3-8B | Llama-3.1-8B |
|---|---|---|---|
| HotpotQA | 46.93 → 50.45 | 49.91 → 53.81 | 53.13 → 50.56 |
| MMLU | 66.31 → 66.14 | 70.42 → 70.20 | 66.56 → 65.12 |
| GSM8K | 89.46 → 87.11 | 89.99 → 90.83 | 86.05 → 80.36 |

Llama's selected-head tuning GSM8K score is 48.45, so final 80.36 recovers
31.92 pp while still trailing native by 5.69 pp. Its Hotpot recovery over
selected-head tuning is 7.19 pp. These are useful collateral-damage mitigation
results, but final differs from head-tuning by both scope and selector on
contextual QA. MMLU/GSM8K have no titled evidence paragraphs, so their selector
does not apply; their change isolates the deployed body.

Final direct-first EM still decreases from native 87.2/86.0/85.2 to
69.8/73.4/65.97. Final all-three correctness is 41.33/45.40/42.30, versus native
22.3/22.6/25.8, but slightly below scoped-body 41.8/42.4/42.5 in Q4/Llama.
Do not claim preservation of all constituent abilities or superiority on every
component metric.

Inference-input token totals fall to 42.5/42.4/43.7% of native for final
answer generation (run 42 composed queries). These totals omit the extra
address-prefill tokens, so do not call them total computational savings.
Wall-time measurements are affected by shared GPU scheduling and mixed batch
sizes and should not be used for an unqualified speedup claim.

## 7. Required consistency decisions and limitations

1. **Native baseline mismatch:** Qwen3-8B main evaluation used batch size 4;
   causal access/necessity used batch size 1. Both use BF16/eager greedy
   decoding. Native composed scores are 29.2 and 28.9 respectively. There are
   44/1,000 different generated sequences and a net three correct-answer
   difference. Qwen4/Llama run-42 main and causal baselines match exactly.
   Always use each experiment's own paired baseline; explain retained batch
   settings in appendix rather than silently replacing one number.
2. **Seed interpretation:** selected-head training has zero-initialized
   deltas, a fixed source order and evaluation mode without dropout. All
   training losses/gradient norms and final delta norms match across nominal
   seeds. Readers are likewise deterministic. The minor Q4/Llama run-score
   variation coincides with seed42 batch1 versus later batch4. Report recorded
   run dispersion accurately; do not call it evidence about initialization
   stability or independent optimization variation. Native-text uses the same
   native reader in all runs, so it has no training-seed variation at all.
3. **FullFT GSM8K:** all nine full-parameter runs have 0/1,319 scored correct
   and 1,319/1,319 format failures. Most outputs are very short; the required
   `####` format is absent. Even the secondary official-compatible extractor
   reports zero. The result demonstrates failure of the specified protocol,
   not that mathematical knowledge has been eliminated. FullFT is a fixed
   default recipe without hyperparameter search; it is not a competitive
   upper-bound baseline. Do not build the main story on defeating it.
4. **Missing code:** absent `coretrace/models` prevents full end-to-end
   reproducibility; see Section 1 and `missing_modules.json`.
5. **Causal scope:** source addresses and direct-target donors are privileged
   diagnostics. Runtime uses input text/title links and train-only readout
   weights. Never show donor attention or annotated support entering the
   deployed method's inference block.
6. **Generalization scope:** three small/medium instruction models, two
   families, one natural contextual two-hop panel, and controlled discovery
   views. No evidence for an exclusive universal circuit, arbitrary hop count,
   all languages, untitled evidence, or model scales beyond those measured.
7. **Comparator scope:** no released CoT, retrieval-model or tuned LoRA
   comparison. Position the repair as an application of the mechanism, not
   a claim of state-of-the-art multi-hop QA performance.

## 8. Recommended evidence-led story and allocation

The scientific question is why accessible constituent facts fail to compose
even when the bridge's paragraph address can still be read out. The clearest
finding is that address recovery, evidence-access mass and local conditional
reading are separable in analysis, while useful local reading depends on
adequate access. A deployed intervention then converts the reader into an
input-only evidence choice and constrains learned changes to reduce damage.

Suggested main-text evidence: native known-hop failure; native address
decodability (including failed cases); bridge-specific causal access; the
factorial interaction; the 103-question ambiguity result; final application
EM and compact content-exchange grounding. Put full head maps, count selection,
all necessity doses/queries, full reader diagnostics, full ablation tables,
all capability metrics, run details and full cost records in the appendix.

There is no need to make FullFT the central antagonist. The much stronger
within-body controls are graph-first versus decoded evidence and metadata
versus attention-based readers. The 103 ambiguous cases pinpoint exactly
where a mechanistic readout changes an otherwise identical deployed system.

A real concise teaser example is source
`d56342fa0baf11ebab90acde48001122`: “Who is John Corvinus's paternal
grandfather?” The evidence chain is John Corvinus → Matthias Corvinus → John
Hunyadi. All three native models answer both constituent questions correctly,
yet answer the composed question “Matthias Corvinus”; all three final models
repair it. See `candidate_worked_examples.json` for exact support sentences.

## 9. Finished versus remaining

Finished: all available research code and configuration review; all primary
prediction/summary/table consistency checks; reader replay; explicit seed
behavior verification; source and graph statistics; novel ambiguity and
failure-subset readout analyses; result-to-file mapping; scientific-claim
boundaries and manuscript allocation advice.

Remaining for the author: recover the originally used `coretrace/models/`
package and trained-slice artifacts if end-to-end re-execution is desired.
New model experiments were not run. Manuscript/figure rendering, reference
verification and final GitHub synchronization are performed by the parent
agent. These internal records should remain outside the manuscript and its
Overleaf input tree.
