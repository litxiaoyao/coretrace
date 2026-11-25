# Access-by-reading figure revision plan

Status: approved by the main editor; implementing the double-column layout in
the existing numerical entry point, `analysis/plot_results.py`.

## Purpose

Make the measured access-by-reading interaction the main scientific result of the
quantitative mechanism figure. A reader should immediately see the four crossed
conditions and how the same direct-query pattern has different utility at native
and calibrated paragraph mass.

The current `data_main_causal_pair` devotes half its area to bridge/root/other
address controls. Those results remain useful but should support the central
mechanism in the appendix rather than lead the main figure.

## Frozen scope

- Preserve all Figure 1--3 artwork, aliases, PowerPoint sources, captions, and
  manuscript references. Do not run `paper/draw_figures.py`.
- Extend only the existing numerical renderer `analysis/plot_results.py`; do not
  add another plotting entry point or modify experimental code.
- Keep `make_causal()`'s recorded-summary collectors and numerical CSV exports.
- Do not change observations, conditions, bootstrap intervals, populations,
  model order, or inference claims.
- Keep all three models. Qwen3-8B's interaction interval `[0, 10]` includes zero
  at its boundary and must remain visible.

## Proposed main figure

Approved layout: a double-column figure (6.75 by 2.45 inches) with
three aligned model panels, ordered Qwen3-4B, Qwen3-8B, Llama-3.1-8B.

Each model panel contains:

1. A compact, explicitly labeled 2-by-2 table of composed accuracy. Rows are
   paragraph access (native, calibrated); columns are within-paragraph reading
   (receiver, direct-query). Cell areas are equal; shading is an organizational
   cue, not a synthetic attention map.
2. The effect of substituting the direct-query reading pattern, shown at native
   and calibrated access with the original paired quadruplet-bootstrap 95%
   intervals. Use a zero reference and the same effect axis for all models.
3. The interaction estimate and its original 95% interval, written plainly as
   the difference between the two pattern effects. Do not add significance
   stars or describe every model as statistically separated from zero.

Alternative if the manuscript must retain a single-column float: the same
information in a stacked layout of approximately 3.25 by 2.8 inches, with the
2-by-2 cells in a common header row and the conditional-effect plot below. The
double-column version is preferable for label legibility and the prominence of
the core finding.

### Recorded values, unchanged

| Model | Native | Pattern only | Mass only | Both | Pattern effect at native access | Pattern effect at calibrated access | Interaction |
|---|---:|---:|---:|---:|---|---|---|
| Qwen3-4B | 34% | 28% | 41% | 43% | -6 [-10, -2] pp | +2 [-3, 7] pp | +8 [1, 14] pp |
| Qwen3-8B | 48% | 50% | 52% | 59% | +2 [-3, 7] pp | +7 [3, 11] pp | +5 [0, 10] pp |
| Llama-3.1-8B | 51% | 47% | 64% | 76% | -4 [-9, 1] pp | +12 [3, 21] pp | +16 [8, 25] pp |

All four conditions use the same 100 receivers in 25 discovery quadruplets.
The uncertainty intervals belong to paired contrasts, not to independently
estimated per-cell accuracies. No cell-level error bars will be invented.

## Address controls

Retain the separate 1,000-source bridge/root/length-matched-other comparison in
`data_app_access_controls.pdf` and `.png`, generated from the existing `access`
records. Preserve its own pipeline-native reference and source-bootstrap
intervals. Do not combine its denominator or uncertainty with the 100-receiver
crossed diagnostic.

The main editor will adjust manuscript captions and references after choosing
the placement. Existing references to `fig:causal` panel (a) as an address
control must then refer to the new appendix figure.

## Planned file changes

- `analysis/plot_results.py`: revise `render_causal`, add an address-control
  rendering helper within this same script, retain collectors and exports.
- `paper/figures/data_main_causal_pair.pdf` and `.png`: replace only this core
  numerical figure.
- `paper/figures/data_app_access_controls.pdf` and `.png`: preserve the relocated
  control panel as an explicit appendix asset.
- `analysis/figure_data/input_manifest_causal.csv`: normal partial-run inventory.
- This internal plan and a compact verification note if needed.

Do not change README files or TeX concurrently with the main editor. Send the
verified aspect ratio, panel meanings, and caption suggestion for integration.

## Inputs and verification

Use the existing `outputs/<model>/causal_factorization/summary.json` and
`outputs/<model>/causal_access/summary.json` inputs for the three models. The
existing exported `data_fig4_causal_factorial.csv`,
`data_fig4_causal_factorial_contrasts.csv`, and
`data_fig4_causal_access_controls.csv` establish the pre-edit numerical baseline.

Verification consists of unchanged CSV observations, arithmetic agreement of
the four cells and paired point estimates, unchanged bootstrap endpoints,
vector-PDF and PNG visual inspection, and byte-preservation of Figure 1--3
assets. This is a figure rendering change and does not require model execution.
