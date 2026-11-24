# Numerical figure redesign, revision 3

This internal design record supersedes the numerical-figure style descriptions in the earlier revision notes. It is not manuscript text.

## Reference inspection

The eight screenshots attached in this revision were opened and visually inspected. `image(20261124-132030).png` contains the rejected CoReTrace plots. The reference data figures are in `image(20261124-132320).png`, `image(20261124-132331).png`, `image(20261124-132441).png`, and `image(20261124-132503).png`. The remaining three screenshots show a conceptual visualization and the two reference table styles.

The numerical reference figures use sans-serif plot labels, conventional saturated blue/orange/red curves and bars, black axes, light dashed grids, distinct observed-point markers, and red–blue heatmaps. The earlier assertion that their plot annotations were serif was incorrect; Times-like text belongs to the surrounding LaTeX captions.

## Implemented style

- DejaVu Sans, 8.5–10 pt labels at the fixed 6.75-inch export width.
- Blue `#1F77B4`, orange `#FF7F0E`, neutral gray `#7F7F7F`; red–blue diverging `RdBu_r` heatmaps.
- White background, black axes and fine bar outlines, light gray dashed grids.
- Conventional grouped bars, observed-point line plots, and head-by-layer heatmaps; the previous horizontal dot/forest plots and colored row backgrounds are removed.
- Vector PDFs with embedded TrueType text and matching 300-dpi PNGs.

## Figure mapping and caption semantics

| File stem | Revised contents | Caption requirements |
|---|---|---|
| `data_fig3_diagnosis` | (a) composition success/failure grouped bars conditional on both constituents being correct; (b) metadata/attention/full address-readout grouped bars on the failed-composition subset | Preserve denominators 457/462/501 and failure-subset denominators 234/236/243. |
| `data_fig4_causal` | (a–c) two mass settings × two reading patterns for each model; (d–f) bridge/first-hop/other paragraph calibration | Top bars report accuracies and interaction point estimates; cluster interaction intervals remain in the corresponding table. Bottom error bars are recorded paired-bootstrap 95% intervals. |
| `data_fig5_content` | Native and CoReTrace grouped bars for edited-value following and obsolete-answer persistence | Means and sample SD over recorded runs; the other controls remain in the complete data export. |
| `data_app_localization` | (a–c) red–blue head/layer attention-gap maps with black outlines around selected heads; (d–f) exact layer-wise mean and maximum over all heads | Lower curves are direct summaries of the ranked head values, without smoothing or a fitted curve; the layer-profile CSV records every plotted value. |
| `data_app_necessity` | Nine panels, rows for composed/first-hop/second-hop questions, columns for models; ranked versus layer-matched random head knockout | Only actual sizes 0/20/40/80 are plotted. Gray vertical lines indicate preselected intervention size. Composition row uses 0–45%; direct-query rows use 0–100%. Labels show accuracy at the selected size. |
| `data_app_ablation` | Controlled effect of fixed projection restoration: first-hop accuracy, all-three joint accuracy, and GSM8K across the three models | Blue is without restoration; orange is with restoration. Bar-top labels are gains in percentage points; bars are mean with sample SD. Core comparison uses `head_tuning` versus `scoped_body`, sharing checkpoint and original context. GSM8K uses `head_tuning` versus `final`; the evidence selector is inapplicable to its unsegmented prompts. |
| `data_app_capabilities` | HotpotQA, MMLU, and GSM8K, each grouped by model with Native/Full fine-tuning/CoReTrace | Only external baseline and complete method appear. Error bars are recorded-run sample SD. The actual zero GSM8K results for full fine-tuning are explicitly labeled. |

The old nine-method composed-accuracy leaderboard has been replaced by a controlled mechanism intervention. The capability figure has removed the internal head-adaptation condition. Neither change modifies retained results.

## Numerical verification

`python analysis/plot_results.py` completed successfully, reading 92 distinct source files and updating `analysis/figure_data/input_manifest.csv`.

Ten existing CSV files for diagnosis, factorization, access controls, content controls, localization, and necessity remain byte-identical to the previous Git revision. Every retained FullFT/CoReTrace capability aggregate exactly matches the previous revision. The new restoration figure is computed directly from the recorded summaries; the added layer profiles are computed directly from every head in each layer. No source outputs, datasets, configurations, or research code were modified.

All seven figure PDFs were inspected with `pdffonts`: DejaVu Sans is embedded, with no Type 3 fonts. The plotting script checks visible text against the full canvas before export. The exported PNGs were opened for visual inspection, and text/legend collisions identified during the first renders were corrected.
