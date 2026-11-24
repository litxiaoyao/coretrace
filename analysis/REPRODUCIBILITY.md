# Reproducibility scope and verified evidence

Audit date: 2026-11-24. Audited repository revision: `cf00035eb9b71bebf3ae88f76caf30ee9b58065c`.

The current revision is supported by fresh reaggregation of recorded predictions and reapplication of released paragraph readers. Figure/table reconstruction uses these existing experiment artifacts. It does not execute new model training or inference.

## Verified coverage

| Verification | Coverage | Recorded outcome | Evidence file |
| --- | --- | --- | --- |
| Prediction manifests, IDs, populations, and summary counts | 90 experiment directories; 991,680 prediction records | Zero recorded errors | `analysis/internal/current_audit/result.json`, `prediction_validation.json` |
| Released reader weights reapplied to archived paragraph features | 12 native/adapted readers, with full/attention/metadata variants | Stored train/test counts reproduced | `analysis/internal/current_audit/readout_validation.json` |
| Aggregate result entries | 144 model/benchmark/method/query entries | Counts, means, and sample SDs reproduced | `analysis/internal/current_audit/table_validation.json`, `additional_checks.json` |
| Factorial contrasts and clustered intervals | Three models; 100 receivers each | Recorded estimates reproduced | `analysis/internal/current_audit/additional_checks.json`, `current_evidence_audit.md` |
| Identity interventions | 300 model/source pairs | All generated token sequences match native | `analysis/internal/current_audit/additional_checks.json` |
| Reciprocal content experiments | Nine model/run directories; 800 rows per directory | Outcome counts and valid exchanges reproduced | `analysis/internal/current_audit/additional_checks.json` |
| Head metadata | Nine recorded model/run configurations | Ranked selections, trained selections, and parameter counts agree | `analysis/internal/current_audit/head_metadata_checks.json` |

The detailed report is `analysis/internal/current_evidence_audit.md`. Evidence paths in the table refer to the full repository; the lightweight package contains only the small inputs needed for figure/table reconstruction.

## Recorded runs and populations

Selected-head runs 42/43/44 use fixed source order, zero-initialized deltas, and model evaluation mode during adaptation. Within each model, all three 2,000-example source, loss, and gradient-norm sequences agree. Reported sample SD describes the recorded executions, including their evaluation settings; it is not an estimate across independent stochastic initializations. Source-bootstrap intervals and quadruplet-bootstrap intervals retain their stated sampling units.

The formal split uses 100 discovery, 2,000 training, and 1,000 test source IDs. The factorial analysis uses 25 discovery quadruplets, yielding 100 receivers. The 1,000-source address-specificity evaluation is a separate test population. Development provenance, entity overlap, batch sizes, and the model-specific restoration choices are reported in the appendix.

## Implementation boundary

Four imported runtime modules are absent from the audited checkout:

- `coretrace/models/native`
- `coretrace/models/deployment`
- `coretrace/models/head_slices`
- `coretrace/models/cpu_adamw`

Their import sites are enumerated in `analysis/internal/missing_modules.json`. A complete GPU rerun requires these modules, model weights, and the relevant execution environment. The available data construction, attention intervention, evidence selection, scoring, and analysis code supports inspection of those procedures. The recorded training and evaluation metadata supports verification of parameter counts and declared restoration masks.

| Model | Declared native restoration | Prefill scope |
| --- | --- | --- |
| Qwen3-4B | V and O; layers 16–19 | Prefix before the question |
| Qwen3-8B | V and O; layers 12–19 | Question tokens |
| Llama-3.1-8B | V; selected layers | Prefix before the question |

These settings were checked in `outputs/{model}/seed42/evaluation/core/manifest.json`, under `provenance.config.methods` for `final`, and agree with the manuscript's scope table. The missing model runtime prevents direct inspection of the complete restoration/head-slice implementation. No substitute runtime was added during this paper-only revision.

## Reconstructing the displayed evidence

From the full repository or extracted lightweight archive:

```bash
python analysis/plot_results.py
python analysis/build_tables.py
python analysis/draw_story_overview.py
```

The archive supplies all listed JSON/CSV inputs and regenerates seven numerical figures, every numerical table including the two compact main-text summaries, and the vector story overview. Two appendix conceptual schematics are supplied assets. `--verify-reproduction` in the delivery script performs reconstruction in a fresh extracted tree and records its actual outcome in `delivery_manifest.json`; this document does not assume that a future packaging run has already passed.

The metadata file `analysis/internal/source_snapshot.json` preserves the original scientific baseline `a00e62230ab83d4e050e3da29a9e9cfd5e239dd6` and separately records the fresh audit revision above. At packaging time, `SOURCE.json` adds the exact Git HEAD, working-tree status, dependencies, and input hashes. These commit roles distinguish historical evidence provenance from the current manuscript revision.

## Compiling the submission

Run `bash analysis/compile_paper.sh`, inspect `analysis/build_final/main.pdf` page by page, and resolve layout/reference issues. Only after visual QA should the compiled PDF and bibliography output be copied to `paper/main.pdf` and `paper/main.bbl`. Final packaging checks source freshness and reads the verified PDF. See `paper/README.md` for the complete build and delivery commands.
