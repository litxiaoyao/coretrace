# Evidence analysis and manuscript reconstruction

This directory supports **When Correct Hops Fail to Compose: Locating, Routing, and Reading Evidence**. The **Locate–Route–Read** account connects recoverable bridge addresses, attention allocation to the relevant paragraph, and relation-conditioned local reading. Composition-gap measurements, causal head localization, destination controls, crossed attention interventions, and recorded cases support the mechanism and its application through CoReTrace. Figure and table generators read completed summaries and explicitly listed derived measurements.

## Regenerate figures and tables

Use Python 3.10 or newer. NumPy and Matplotlib support numerical plotting; table construction uses the standard library. `analysis/plot_results.py` is the sole manuscript numerical plotting entry point.

Revision 2 adds the composition-gap and mechanism-case tasks and restores the address-control figure to the main text. Regenerate this figure group with:

```bash
python -m pip install numpy matplotlib
python analysis/plot_results.py --only composition causal mechanism_cases
```

The `composition` task writes `data_main_composition.pdf/.png`. The `causal` task writes the full-width interaction display, `data_main_causal_pair.pdf/.png`, and the main-text destination control, `data_app_access_controls.pdf/.png`. The `mechanism_cases` task writes `data_main_mechanism_cases.pdf/.png`. Supporting CSVs and `input_manifest_composition_causal_mechanism_cases.csv` are written under `analysis/figure_data/`. Figures 1–3, their source artwork, and their existing captions remain unchanged.

The new case figure reads `analysis/internal/mechanism_case_records_20261125_v2.json`. It pairs the canonical Corvinus test example across three models with a shared-context Angela diagnostic: joint mass/pattern intervention identifies the requested relation value, and the complete procedure follows its reciprocal change. The JSON retains the contexts, recorded predictions, distinct populations, and source inputs. Rendering these cases requires no new model inference. The earlier Calvert candidate-selection case remains in the appendix.

For a complete numerical reconstruction when needed:

```bash
python analysis/plot_results.py
python analysis/build_tables.py
```

These commands regenerate numerical figure PDFs/PNGs under `paper/figures/`, numerical LaTeX tables under `paper/tables/`, and their supporting CSVs and input inventories. A complete plotting run refreshes `input_manifest.csv`; a partial run writes a separate manifest. The table builder refreshes `table_inputs.json`. The current main-text table is `main_results.tex`; complete component, constituent, and capability results remain in the appendix.

### Formal figure inventory

| Placement | File stem | Role |
| --- | --- | --- |
| Main 1 | `figure1_teaser` | Supplied teaser, preserved exactly |
| Main 2 | `figure2_diagnosis` | Supplied mechanistic-analysis schematic, preserved exactly |
| Main 3 | `figure3_method` | Supplied CoReTrace workflow, preserved exactly |
| Main 4 | `data_main_composition` | Composition outcomes within each native constituent-correct population |
| Main 5 | `data_main_localization` | Head heatmaps with a shared scale |
| Main 6 | `data_main_head_pair` | Layer profiles and matched knockout curves |
| Main 7 | `data_fig3_diagnosis` | Address recovery during composition failures |
| Main 8 | `data_app_access_controls` | Bridge, root, and other-paragraph access calibration |
| Main 9 | `data_main_causal_pair` | Full-width crossed intervention and interaction effects |
| Main 10 | `data_fig5_content` | Edited-value following and joint original/edited correctness |
| Main 11 | `data_main_mechanism_cases` | Recorded Corvinus and Angela mechanism cases |
| Appendix | `data_app_localization` | Complete head maps and measured layer profiles |
| Appendix | `data_app_head_overlap` | Within-model intersections of head sets |
| Appendix | `data_app_necessity` | Selected and layer-matched random knockout controls |
| Appendix | `data_main_ambiguity` | Matched candidate-ranking comparison |
| Appendix | `data_main_case` | Earlier Calvert candidate-selection example |
| Appendix | `data_app_ablation` | Projection-restoration component comparison |
| Appendix | `data_app_capabilities` | Full HotpotQA, MMLU, and GSM8K comparisons |

The main text targets eight pages and contains eleven figures—three supplied conceptual figures and eight empirical figures—and one table. The appendix contains seven figures with independent `A` numbering. Generated plots and case panels are saved as vector PDFs with 300-dpi PNG previews. File stems retain their established names when placement changes; the table above follows the actual LaTeX references.

`analysis/draw_story_overview.py`, `analysis/wrap_conceptual_figures.py`, and `analysis/image_prompts.json` retain material from earlier figure revisions. They are not steps in the current figure regeneration. Likewise, `paper/figures/captions.json` and `figure_sources.json` retain an earlier inventory; current placements and final captions are authoritative in the LaTeX manuscript. Historical revision documents remain unchanged.

## Evidence and scope

The recorded audit at source revision `cf00035eb9b71bebf3ae88f76caf30ee9b58065c` checked 90 experiment manifests, 991,680 prediction records, 12 released paragraph readers, and 144 aggregate result entries. The coverage and implementation boundary are specified in `analysis/REPRODUCIBILITY.md`; detailed evidence is in `analysis/internal/current_evidence_audit.md` and `analysis/internal/current_audit/`.

Principal composition uses 1,000 test sources. Address-readout failure subsets condition on the native model's constituent and composition outcomes. The factorial diagnostic uses 100 receivers in 25 discovery quadruplets; its bootstrap preserves these clusters. Reciprocal exchanges use 100 diagnostic sources and preserve full-input word and character multisets before the selector is recomputed.

Run labels 42/43/44 identify recorded executions. Selected-head training uses fixed source order and zero-initialized deltas, and its source/loss/gradient sequences agree within each model across runs. Reported sample SD describes those executions; source-bootstrap intervals describe source sampling. The access experiment uses its own native baseline, including Qwen3-8B's 28.9% reference versus 29.2% in the principal evaluation.

Core/HotpotQA scores require alias exact match and completion within the 32-token budget. MMLU uses same-prefill option probabilities. GSM8K uses a parsed final numerical answer within a 512-token budget. `analysis/figure_data/README.md` defines the exported quantities and their denominators.

## Build and inspect the manuscript

```bash
bash analysis/compile_paper.sh
```

This writes `analysis/build_final/main.pdf` and retains the exact source snapshot and logs. It uses the original ICML template and keeps generated TeX caches inside `analysis/tex_runtime/` where needed. Inspect the compiled PDF page by page before copying the verified files into the formal source directory:

```bash
cp analysis/build_final/main.pdf paper/main.pdf
cp analysis/build_final/main.bbl paper/main.bbl
```

See `paper/README.md` and `analysis/tex_build_notes.md` for normal TeX/Overleaf alternatives and environment details.

## Lightweight reconstruction and retained packaging tooling

Numerical reconstruction uses supplied experiment summaries and derived measurements at their repository paths. It requires no model weights, GPU, PyTorch, decompressed prediction archives, or network after dependency installation. The full repository's audit scripts additionally use prediction and feature archives. The plotting and table commands above reconstruct the current numerical material without regenerating Figures 1–3.

`analysis/package_delivery.py` is retained from an earlier delivery. Its configured figure inventory and reconstruction scope still name the earlier overview and figure arrangement. Inspect that inventory before using it for a new delivery; it is not the current eleven-figure main-text specification. Its read-only planning command remains:

```bash
python analysis/package_delivery.py --dry-run
```

For its configured inventory, the helper supports `--verify-reproduction`, which reconstructs figures and tables from an isolated small-input archive and checks source immutability. Its default output is `analysis/delivery/`; an external destination can be selected with `--output-dir`. A real run requires a compiled PDF newer than its manuscript inputs and checks local TeX dependencies. The retained artifact names are:

| File | Contents |
| --- | --- |
| `coretrace_paper.pdf` | Complete compiled manuscript and appendix |
| `coretrace_overleaf.zip` | LaTeX source, styles, tables, and the helper's configured figure inventory |
| `coretrace_figures.zip` | Configured figure assets and metadata |
| `coretrace_plotting_code.zip` | Reconstruction scripts, small inputs, documentation, and provenance |
| `delivery_manifest.json` | Artifact hashes, source revisions, and reconstruction outcome |
| `SHA256SUMS.txt` | Delivery checksums |

A new delivery must match the current manuscript's figure references and captions. GitHub synchronization is a separate operation from this packaging helper.
