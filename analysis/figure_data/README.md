# Numerical figure data

Run `python analysis/plot_results.py` from the repository root. The script requires Python 3.10 or newer, NumPy, and Matplotlib; it does not require model weights, PyTorch, a GPU, network access, or decompressed prediction archives. It writes the formal numerical figures as vector PDF and 300-dpi PNG under `paper/figures/` and regenerates the CSV files in this directory from the completed result summaries.

`input_manifest.csv` lists every file read by a complete execution, with its repository-relative path, byte count, and SHA-256 digest. Copy these files while preserving their paths, together with `analysis/plot_results.py`, to create a small standalone reproduction tree. A restricted run such as `python analysis/plot_results.py --only diagnosis` writes a separate restricted manifest and preserves the complete manifest.

## Figure mapping

| Figure stem | Contents | CSV source tables |
| --- | --- | --- |
| `data_fig3_diagnosis` | Composition conditional on two correct constituent answers; native address readout on the resulting composition-failure subgroup | `_composition`, `_address_readout`; `_address_readout_overall` supplies the full test-population reference |
| `data_fig4_causal` | Paragraph-mass × within-paragraph conditional-attention factorization; paired full-test paragraph-calibration controls | `_factorial`, `_factorial_contrasts`, `_access_controls` |
| `data_fig5_content` | Edited-value following and obsolete-answer persistence after reciprocal content swaps | `_seed_values`, `_aggregated` |
| `data_app_localization` | Complete per-head direct-query minus composed-query paragraph-mass map, with the frozen selected set outlined; measured layer mean/max profiles | Matching CSV stem and `_layer_profiles` |
| `data_app_necessity` | Selected and layer-matched random head knockouts for composed and constituent questions | Matching CSV stem |
| `data_app_ablation` | Controlled projection restoration for first-hop, all-three, and GSM8K accuracy | `_seed_values`, `_aggregated` |
| `data_app_capabilities` | Native, full fine-tuning, and CoReTrace on HotpotQA, MMLU, and GSM8K | `_seed_values`, `_aggregated` |

Every exported observation contains its source path. Percentages and percentage-point changes are computed from the recorded counts or recorded paired contrasts, rather than copied into the plotting code. Model names and experimental method labels used in the figures are presentation labels; the CSV `model`, `method`, and `variant` fields preserve the source identifiers.

## Population and uncertainty conventions

- Figure 4a conditions on native correctness of both constituent questions, with model-specific denominators. Figure 4b further conditions on native failure of the composed question, and therefore has a smaller denominator. Its data come from the independent saved-weight recomputation in `analysis/internal/readout_validation.json`; `analysis/audit_experiments.py` documents the feature, frozen-reader, and generation-record inputs used to reconstruct that subgroup. The full-population native-reader data are exported separately and are not silently mixed with the subgroup.
- Figure 5a–c shows 100 receiver questions grouped into 25 shared-context quadruplets. Interaction intervals are the recorded paired cluster-bootstrap intervals in the factorial summary. This population overlaps discovery and is a mechanistic test, not an independent generalization sample. Figure 5d–f use the separate full-test access experiment and its same-run native reference. In particular, that pipeline records Qwen3-8B native correctness as 289/1000, whereas the principal evaluation pipeline records 292/1000.
- Error bars for trained methods are sample standard deviations across three recorded runs. The selected-head training traces repeat across the seed labels, so this dispersion must not be interpreted as independent stochastic-training robustness. Native references are read once; repeated native content-control entries are checked for equality. A zero-height bar is an observed lack of run dispersion, not an omitted uncertainty estimate.
- Content-following rates use all 100 original sources in their denominator. Every exchange changes the context and passes the word/character preservation checks. The CSV also exports the actual-swap count.
- Capability metrics are HotpotQA answer exact match, MMLU option-probability accuracy (`logprob_correct / n`), and GSM8K numeric-answer accuracy. The MMLU free-generation correctness field is not used.
- Head heatmaps use zero-based layer and query-head indices. Selected-set outlines come directly from the frozen head map. Knockout controls export the observed selected/random head overlap; the controls are layer matched and are not assumed disjoint.

All figures use a white background, embedded DejaVu Sans fonts of at least 8 pt, and a shared blue/orange/gray palette with red–blue diverging heatmaps. All figure widths are 6.75 inches. Numerical figure captions and scientific interpretation belong in the LaTeX manuscript, not in the image files.
