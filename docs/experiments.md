# Formal experiment protocol

## Shared settings

`configs/experiments.json` is the single source for model families, seeds, discovery head counts and fixed rollback scopes. `configs/models.local.json` supplies machine-specific model paths only. The source data, split IDs, prompts and aliases are shared across models and seeds. No model results are included in the migration.

CoRe-2Wiki has 100 discovery, 2,000 train and 1,000 test sources. Each source has three queries. Only composed training queries update model weights; constituent labels remain diagnostic. Each method is evaluated on the same complete test sources. Use per-source and shared-entity-cluster paired intervals; discovery-quad probes use quadruplet clusters.

The main family is Qwen3-4B/8B; Llama-3.1-8B-Instruct supplies second-family validation. Each has its own discovery localization, causal best-n selection and state-aligned train-only reader. Scores are not averaged across model families or scales.

The discovery procedure ranks all heads by the paired direct-target/composed bridge-paragraph attention gap. It evaluates top-20/40/80 sets using a fixed discovery-derived per-head paragraph-mass target, chooses the highest discovery accuracy, and prefers fewer heads on a tie. Test scores never choose the head count. Per-model rollback scopes are fixed from development and written explicitly in the configuration; formal runs do not re-optimize them using test or capability scores.

Training uses the original default answer-only recipes, not comparator hyperparameter search. Selected-head full-rank QKVO training: one epoch, learning rate 2e-5, accumulation 8, AdamW, gradient norm clipping 1. The selected-head baseline and final repair share that checkpoint. True FullFT updates all model parameters with its original 2e-5/one-epoch/accumulation-8 recipe and CPU FP32 Adam state. Its name always means full-model training. LLM training uses 250 optimizer steps on 2,000 sources. FullFT preserves its original seed-based source ordering; selected-head training preserves fixed split order.

The paragraph-address reader uses the actual deployed body state, zero-initialized linear weights, 500 Adam steps, learning rate .03, L2 .01, and training sources only. Full, attention-only and metadata-only readers share the same captured features. For H heads, the full reader has 2H+2 weights; the metadata-only control uses paragraph length and title mention. There is no test-label fitting.

## Tables

| Result | Generated from | Contents |
|---|---|---|
| Main task / application | `seed*/evaluation/core`, `seed*/evaluation_fullft/core` | Per-model composed, direct-first, direct-target and all-three correctness; original model, selected-head CE tuning, final method, true FullFT |
| Component ablations | Same core prediction files | Native+text, full head tuning, scoped body, graph-first selector, decoded selector; full/attention-only/metadata-only readers |
| General capability preservation | `evaluation/{hotpot,mmlu,gsm8k}` and FullFT counterparts | All 7,405/14,042/1,319 official evaluation rows; absolute scores and native-relative changes; no requirement of improvement |
| Resource / efficiency | Training records and prediction timing | Trainable parameters, sources/steps, measured training wall time, inference wall time including address selection, input/output tokens and extra readout prefills |

`scripts/aggregate.py` writes per-seed results and per-model means/sample standard deviations to CSV/JSON. Native greedy reference predictions are reported once, not as three independent stochastic replications. Deterministic trained pipelines can have identical seed outputs; report that result, not fabricated variation or a best seed. Pairwise source/cluster intervals are in each evaluation's `summary.json`; cross-seed standard deviation is a different quantity.

MMLU uses batch size4 with left padding, preserving native prompts, greedy
generation and same-prefill ABCD scoring. Each output is trimmed at its actual
first EOS. Rollback positions are shifted separately for each padded example.
The effective batch size is recorded in the evaluation configuration and
prediction rows. Core and Hotpot also support batch size4, with the original
per-example evidence selection followed by batched generation. Completed
seed42 core/Hotpot runs on Llama8B and Qwen4B used batch size1 and are retained;
subsequent new core/Hotpot jobs use batch size4. New GSM8K jobs also use
batch size4, preserving the full512-token generation allowance and all numeric
scoring and completion diagnostics. Started evaluation jobs resume with their
original saved configuration; completed batch-one evaluations are retained.
Cost tables record the observed generation batch sizes separately.

## Figures

| Figure role | Code and generated inputs | Output stem |
|---|---|---|
| Natural phenomenon: individually correct hops fail to compose | `evaluate.py`, `summarize.py`; native three-query predictions on test1,000 | `phenomenon` |
| Where bridge-address access differs | `discover.py`; all-head paired attention capture and ranking on discovery100 | `*_head_localization` |
| Is bridge-address information recoverable? | `readout.py`; train-only full/attention/metadata reader, fixed test diagnostic | `*_address_readout` |
| Causal evidence access | `causal.py`; native / annotated bridge / annotated first-source / length-matched other paragraph | `*_causal_access` |
| Access mass versus relation-conditioned paragraph reading | `factorized_causal.py`; native, identity, mass-only, conditional-only, both | `*_causal_factorization` |
| Local content use rather than answer occurrence | `content_causal.py`; original versus reciprocal values under native/budget/body/final | `*_content_reading` |
| Mechanism-derived repair and component value | Same-body graph-first versus decoded selection; native-body and scoped-body removal | `*_application_ablations`, `comparison_core` |
| General capability preservation | Complete benchmark predictions and per-model seed aggregation | `comparison_hotpot`, `comparison_mmlu`, `comparison_gsm8k` |

`scripts/figures.py` writes PDF/PNG figures and real worked examples selected by an explicit predicate. `scripts/aggregate.py` writes inference/training cost CSVs and their source mappings. Figure numbers can be assigned during writing; the output names describe their scientific content.

## Causal interpretation

The functional account is **recoverable bridge address → allocation of evidence access → relation-conditioned local value reading**. It is not assumed to be an exclusive anatomically sequential three-stage circuit. Discovery and causal controls establish operations; deployment removes the diagnostic oracle.

Paragraph-budget arms use official support addresses solely for diagnosis. All fixed test sources remain in the denominator; no valid other-paragraph control is an explicit no-op. The factorized experiment uses the original shared-context discovery quadruplets; donor and receiver native context-token prefixes must align. The donor contributes only normalized attention within a paragraph, not an answer residual, value vector or output projection. Identity must preserve generated IDs. Discovery head/tau selection and this diagnostic view overlap, so these probes are not presented as independent test generalization.

The factorized report additionally estimates the paired accuracy interaction
`both - mass_only - conditional_only + native`, and the conditional effect
under each mass setting. Bootstrap intervals resample all25 quadruplet clusters
(100 receiver queries), retaining the four paired intervention outcomes per
receiver. This measures interaction on accuracy, without assigning separate
anatomical stages. The factorization plot shows both conditional settings
against the mass intervention; its point values and source summary are saved
beside the PDF in `*_causal_factorization_data.csv`.

Reciprocal content interventions exchange the same relation's object surfaces between original bridge paragraphs. They preserve global character/word occurrence counts, retain ambiguous no-ops explicitly, and recompute the final method's selector on the edited input. The primary report distinguishes original accuracy, edited-value following, obsolete-answer persistence and jointly correct original→edited pairs. No-op rows do not receive new-target credit.

The deployed method uses the input title graph, a fixed train-only address reader, and original selected paragraphs as plain text. Support annotations and answer labels are unavailable to its selector. Controls use their own deployment-state readers; comparing against graph-first uses the same trained/scoped body. Hyperparameters for standard comparisons are not tuned to enlarge or shrink the margin.

## Capability metrics

All three benchmarks use complete official evaluation splits, with no post-hoc exclusions or truncation. Prompts are generated by `build_benchmarks.py` and shared across methods within each model. Native chat templates and model-specific EOS IDs are used.

- HotpotQA: original complete distractor contexts, answer-only greedy generation, 32 new tokens; report EOS-gated EM, text EM/F1 and completion diagnostics.
- MMLU: zero-shot original stem and four choices. Primary score is the argmax probability of native single-token A/B/C/D labels at the same initial prefill. Micro and subject-macro scores are reported. Complete generated-letter/EOS correctness and formatting failure are secondary.
- GSM8K: zero-shot explicit reasoning prompt, 512 new tokens, required final `#### NUMBER` line. Decimal numeric equality is primary; a valid numeric answer is not rejected merely because generation did not emit EOS. Report format, completion and cutoff diagnostics.

The capability suite measures preservation. These are explicitly defined prompts; full-split coverage does not imply standard five-shot MMLU or eight-shot GSM8K evaluation.

## Execution and storage

Use `python scripts/run.py` to inspect the plan. Only `--run` starts model work. The queue is sequential, stops on a failed command and skips completed stages. Each run retains its effective configuration, prediction JSONL and summary under a model/seed directory, preventing pilot/formal or cross-model result mixing.

`scripts/experiment_queue.py --plan PLAN.json --worker WORKER` runs a saved list of
commands with explicit job dependencies. Each worker has a process lock and
per-job pending/running/complete/failed records. A failed dependency stops its
dependents; `--retry-failed` resumes after the underlying issue is resolved.
The server's active plan is `outputs/runtime/formal_queue.json`. Independent
discovery, training, causal tests and evaluations run concurrently.
After Qwen4's complete evaluation finished, its resident and the
memory-only 4B service were replaced by a Qwen8 evaluation resident on GPU2.
The `gpu2eval` queue evaluates Qwen8 seed42, then runs Qwen4 FullFT without
waiting for all Llama seeds. GPU0 completes Qwen8 causal experiments, evaluates
seeds43/44, then runs Qwen8 FullFT. GPU2's big resident continues Llama FullFT.
The existing job ID `gpu0_qwen3_8b_evaluate` is retained for seed42; its worker
is `gpu2eval` and resident is `outputs/runtime/gpu2evalslot`. The additional
job `gpu0_qwen3_8b_evaluate_43_44` covers the other two seeds. The public
`run.py --stage evaluate --eval-seeds ...` option only partitions dispatch;
the fixed seed configuration and native-reference convention are retained.
These are scheduling changes only;
dataset, training recipes, seeds and evaluation protocols are unchanged.
After all Qwen4 experiments and Qwen8 non-FullFT evaluations completed, the
user requested release of idle GPU0. Its waiting Qwen8 resident was stopped;
the remaining Qwen8 FullFT job keeps its existing ID but now uses `gpu2eval`
and `gpu2evalslot`, depending on completed Qwen4 FullFT. No GPU0 restart is
required for remaining experiments. The resident's host-memory ceiling is
216GiB for8B training; aggregate admission still enforces half-server memory.
FullFT uses size-class host-memory admission: 8B runs retain the original
large-model mutex, while a4B run can overlap an8B run when their aggregate
projected project memory fits below half-server memory with4GiB reserve.
At each new training boundary, unused pinned-host/malloc caches are released.
If conservative admission is blocked by this service's clean file cache,
the service reclaims that cache with swapping disabled before rechecking;
live tensors and GPU allocator reservations are retained. Historical peaks
are not assigned to other jobs which are only waiting for a size-class slot.
Reservations include optimizer states, gradient buffers and tensor temporaries;
already-admitted but not-yet-allocated memory remains reserved. The legacy live
8B process is accounted at its measured cgroup high-water mark. CPU updates
and gradient calculation recipes are unchanged. Their subsequent evaluations
can overlap. Aggregation waits for all workers.

Gradient transport uses synchronous reusable pinned FP32 staging instead of
repeated pageable copies. If a resident's already-retained allocator cache
can hold the full FP32 gradient sum with8GiB left for activations/workspace,
the sum is accumulated on GPU and copied to CPU once per optimizer update.
Otherwise accumulation remains on CPU. Both retain the same per-source
FP32 summation order, eight-source accumulation, CPU FP32 masters/moments,
global clipping and original AdamW recipe. Microbatch traces explicitly
record `gradient_accumulation_device` and `all_gradients_FP32`; a GPU sum
correctly reports `all_gradients_CPU_FP32=false`. CPU/GPU BF16/FP32 multi-step
checks verified bitwise-identical gradients, optimizer states and weights.
Runtime transport validation is recorded separately from scientific results.

Controllers write a heartbeat every10 seconds while a command is active and
automatically dispatch the next task when it completes. Submission reconnects
to an identical pending resident request after a controller restart, preserving
the live training state and avoiding duplicate training requests. Server-local
`outputs/runtime/queue_guard.py` checks every30 seconds and restores an
unexpectedly stopped dispatcher while its resident is alive. It records
dependency waits, unavailable residents, experiment failures and result files
without progress for30 minutes in `outputs/runtime/queue_health.json`.
The health report distinguishes size-class/memory admission waits and actual
kernel lock waits from active computation and records aggregate project host
memory. Scientific failures are not retried blindly, and the guard never
restarts CUDA workers or an in-flight optimizer. Controller entry points use
`scripts/experiment_queue.py` throughout.

Checkpoint-space preflight waits automatically if shared storage is temporarily
insufficient. The trained model is also retained while waiting for save space
at the end of a new training job. The server guard can recover an older
disk-preflight failure only when the training output never existed and enough
checkpoint space has returned; it does not rerun partially trained experiments.

FullFT saves one final BF16 checkpoint, evaluates all four datasets, then deletes those weights by default; its training metadata and all predictions remain. No optimizer snapshots or intermediate checkpoints are retained. Reader and selected-head artifacts are small and retained for ablations. `--keep-fullft` is an explicit disk-space tradeoff. Complete summaries require all expected IDs; partial prediction files are not reported as final results.

The open-source queue uses standalone model loading. Machine-specific resident-service scheduling belongs to the execution environment and is not an import dependency. On this server, coordinate use of the already resident GPU2 models when formal execution is requested; migration itself runs no formal model experiments.

## Confirmed formal coverage against the reference papers

The four reference papers guide experiment design; Repair Attractors is excluded.
SunC motivates the main-task/transfer/retention tables and selected-component
necessity curves. The ICL mapping paper motivates controlled interchange and
operation-specific component ablations. The persona and cross-modal emotion
papers motivate tracing functional operations and testing the resulting repair.
Their application domains are not treated as related-work topics for this study.

The formal queue additionally includes `scripts/necessity.py`: native versus
selected-head and layer-matched random-head question-prefill knockout at
20/40/80 heads, retaining all1,000 test sources and their three queries.
Its outputs are `causal_necessity/{predictions.jsonl,summary.json}` and
`*_causal_necessity.pdf`. Random overlap with selected heads is reported.
These curves measure necessity under the specified intervention and compare
composed/constituent effects.

All eight method/component arms are evaluated on the core task. The three
complete capability benchmarks evaluate native, head tuning, final repair and
FullFT; task-specific component ablations stay in the core table. Native
predictions are measured once at seed42 and reused as the deterministic
reference. Training-dependent methods run all42/43/44 seeds. This avoids
repeatedly measuring an unchanged native model.

For an existing resident model, `scripts/resident_worker.py` provides an optional
repository-local executor and `run.py --resident STATE` submits the same public
CLI stages to it. It keeps the model's allocation across stages and restores
the base after FullFT evaluation. The standard standalone CLI remains available.

## Manuscript and artifact requirements

Write the complete manuscript after formal experiments finish, using SunC and
the two camera-ready papers as presentation references. Keep the revised
Related Work concise and directly relevant to contextual composition.

Data-result figures are generated from the single `scripts/figures.py` entry
point. By the updated manuscript instruction, Figures1–3 use the separate
manuscript-only `paper/draw_figures.py`; that code and its editable artwork
are not required in the research code release. The requested
format is editable PPTX slides, converted to PDF,
and included in the LaTeX source as PDF. They are not to be replaced with
non-editable screenshots embedded in slides. Numerical panels use completed
formal outputs. Figure assignments and captions are finalized from the actual
results; no provisional numbers are written into the paper.

Every table must have an explicit source file. `scripts/aggregate.py` writes
`tables/dataset_statistics.csv` and `tables/data_sources.json` for the fixed
dataset and the three complete capability benchmark splits. It also writes
`tables/sources.json` linking each accuracy cell to its model, seed, prediction
file, method/query filter and scoring formula. `tables/cost_sources.json`
records the corresponding training-log and prediction sources for
`training_costs.csv` and `inference_costs.csv`. These are ordinary readable
source mappings, not cryptographic audit manifests. Any additional paper table
must extend this source mapping when its data are produced.

Observed wall times reflect the shared GPU schedule. Parameter counts, question
counts and extra forward-prefill counts provide schedule-independent resource
comparisons. Cost table sources retain the measured wall times separately.
