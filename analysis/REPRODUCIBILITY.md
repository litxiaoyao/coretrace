# Reproducibility

## Recorded inputs and scope

Use the frozen splits in `data/CoRe-2Wiki-v1.0/`, configurations in `configs/`, and recorded results in `outputs/`. The full experiment workflow is described in [../docs/experiments.md](../docs/experiments.md); dataset construction is described in [../docs/data.md](../docs/data.md). A fresh GPU run requires the original model weights, checkpoints and execution environment.

The formal discovery/train/test splits contain 100/2,000/1,000 distinct, source-disjoint IDs. The panels preserve earlier research selections; source disjointness does not imply entity disjointness or independence from all prior development. Discovery fixes head budgets and mass targets; composed training questions fit model updates and address readers. Restoration scopes are fixed for the reported suite. Selected-head runs 42/43/44 use fixed source order and zero-initialized deltas in evaluation mode; their recorded source, loss and gradient-norm sequences agree within each model. Sample SD describes recorded executions, not independent initialization uncertainty.

| Model | Selected query heads | Native restoration | Prefill scope |
| --- | ---: | --- | --- |
| Qwen3-4B | 20 | V and O, layers 16–19 | Prefix before question |
| Qwen3-8B | 20 | V and O, layers 12–19 | Question tokens |
| Llama-3.1-8B | 40 | V, selected layers | Prefix before question |

Frozen selections: `outputs/{model}/discovery/SELECTION_FROZEN.json`. Restoration scopes: `figure_data/v5_frozen_scope_*.json` and `outputs/{model}/seed42/evaluation/core/manifest.json` (final method). The implementation is in `coretrace/models/`.

## Reconstruct figures, tables and derived evidence

From the repository root with Python 3.10+, NumPy and Matplotlib:

```bash
python analysis/plot_results.py
python analysis/build_tables.py
python analysis/derive_structure_evidence.py
python analysis/derive_causal_evidence.py
python analysis/derive_story_adapted_routing.py --seed 42
python analysis/derive_story_relation_reading.py \
  analysis/figure_data/data_revision_relation_reading_qwen3_4b.json.gz \
  analysis/figure_data/data_revision_relation_reading_qwen3_8b.json.gz \
  analysis/figure_data/data_revision_relation_reading_llama3_8b.json.gz
```

The plotting entry requires Git commit `4990754cb73512599adfea9519862868b4260dbf`; the structure/causal derivations default to `5586f3816903e64334de80e06b74c6d7b1499b18`. Use a full checkout containing these objects. Reconstruction from recorded summaries does not require model execution. See [README.md](README.md) for figure inventory and [figure_data/README.md](figure_data/README.md) for metric definitions.

Structure evidence uses 100 paired canonical discovery sources per model; the main profile averages question-token rows, with final-question-row values separately retained. The random comparison is the recorded layer-matched set. Causal evidence uses the fixed native constituent-correct, access-baseline composition-wrong, full-reader-correct subgroup (169/174/209). Qwen3-8B's access evaluation differs from principal evaluation: two previously eligible failures are correct under the access baseline, reducing 176 to 174. The 10,000 paired source-bootstrap draws use seed 20261125; mass is the mean of raw per-head paragraph masses, not the exponent of a mean log mass. The factorial experiment uses 100 receivers in 25 discovery quadruplets; bootstrap resamples whole quadruplets. Joint-only correction requires Native, Mass and Pattern incorrect and Both correct. The reciprocal exchange uses 100 original/edited pairs. Full outcomes, including losses, source identities, alignment checks and hashes are retained in `internal/v3_causal_evidence.json` and `internal/v3_structure_evidence.json`.

## Matched routing and relation-reading analysis

Routing compares native and adapted/restored seed-42 features on the same 1,000 test sources per model; fixed failures require both native constituent answers correct and native composition incorrect (234/236/243). The derivation validates source/query IDs, frozen heads, paragraph ordering and token geometry. Results and source hashes: `figure_data/data_revision_adapted_routing.csv`, `data_revision_adapted_routing_receivers.csv`, and `data_revision_adapted_routing.manifest.json` in that directory.

Relation reading uses the frozen 25 discovery quadruplets, identical shared contexts, original tokenizer/chat template and four states: native composed, native direct same relation, native direct other relation, and adapted/restored composed. The last question token row supplies each head's bridge mass and conditional token weights. Compare target-minus-other relation spans, including per-token length normalization; absolute weights are computed per head as mass times conditional weight before averaging. The two paired contrasts are adapted versus native composed and same versus other direct relation. The statistics retain both signs and use 10,000 whole-quadruplet bootstrap draws (seed 20261125).

Each model retains 98/100 receivers; `natural_crossed_901c815fb5a1839eb3e1__C21` and `natural_crossed_901c815fb5a1839eb3e1__C22` are excluded because relation spans overlap after tokenization. The 25 clusters remain represented. These are discovery measurements, not independent held-out evaluation or causal mediation. The original Llama pilot is retained and supplies the verified Angela token panel.

The raw banks `figure_data/data_revision_relation_reading_*.json.gz` contain per-head weights, token IDs, spans, exclusions and source hashes (corpus/views, head selection, checkpoint, scope, tokenizer/model files). The summary, per-receiver CSV and `data_revision_relation_reading_manifest.json` retain aggregation and input checksums. `data_revision_token_capture.json` contains the measured case panel.

If a fresh capture is required, resolve the original model and checkpoint paths from the frozen manifests, then plan with:

```bash
python analysis/capture_paired_relation_reading.py \
  --model-id llama3_8b --dataset data/CoRe-2Wiki-v1.0 \
  --model "$MODEL" --budget outputs/llama3_8b/discovery/SELECTION_FROZEN.json \
  --checkpoint "$CHECKPOINT" \
  --scope analysis/figure_data/v5_frozen_scope_llama3_8b.json
```

Replace model-specific inputs consistently for other models. The default is plan-only; `--run` performs read-only forwards, and `--case-only` selects the Llama pilot. Reuse verified captures rather than rerunning them unnecessarily.

## Verification and provenance

The audit snapshot is `cf00035eb9b71bebf3ae88f76caf30ee9b58065c`; scientific baseline is `a00e62230ab83d4e050e3da29a9e9cfd5e239dd6`. See `internal/source_snapshot.json`. The retained audit covers 90 experiment manifests, 991,680 prediction records, 12 readers and 144 aggregate entries. Machine-readable results are in `internal/prediction_validation.json`, `readout_validation.json`, `table_validation.json`, and `internal/current_audit/`; scripts are `audit_experiments.py`, `audit_answer_forms.py`, and `audit_clustered_contrasts.py`. The historical missing-runtime-module finding is retained in `internal/missing_modules.json`; those sources have since been restored in `coretrace/models/`. Cases and exact input/response provenance are in `internal/mechanism_case_records_20261125_v2.json` and `figure_data/data_revision_case_records.json`.

## Compile

```bash
bash analysis/compile_paper.sh
```

Inspect `analysis/build_final/main.pdf` before copying it and `main.bbl` to `paper/`. For Overleaf, use the existing `paper/` source tree. See [../paper/README.md](../paper/README.md).
