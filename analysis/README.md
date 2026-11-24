# Evidence analysis and manuscript reconstruction

This directory supports **When Correct Hops Fail to Compose: Diagnosing Evidence Access and Local Reading**. The main scientific sequence is composition failure under shared evidence, recoverable bridge addresses, controlled access-by-reading interaction, and diagnosis-guided repair with local-fact validation. Figure and table generators read completed summaries and explicitly listed derived measurements. The overview drawing presents a verified worked example and a schematic identity for a head's bridge contribution.

## Regenerate figures and tables

Use Python 3.10 or newer. NumPy and Matplotlib support the plots and overview; table construction uses the standard library.

```bash
python -m pip install numpy matplotlib
python analysis/plot_results.py
python analysis/build_tables.py
python analysis/draw_story_overview.py
```

These commands regenerate seven numerical figures and one vector overview under `paper/figures/`, all numerical LaTeX tables under `paper/tables/`, and the supporting CSVs and input inventories under `analysis/figure_data/`. The two compact main-text tables are `main_components.tex` and `main_ambiguity.tex`; the appendix retains their full results and dispersion.

A partial plotting command such as `python analysis/plot_results.py --only diagnosis causal content` writes a separate partial manifest. A complete run refreshes `input_manifest.csv`; the table builder refreshes `table_inputs.json`. Use complete runs before final packaging.

### Formal figure inventory

| Placement | File stem | Role |
| --- | --- | --- |
| Main | `story_overview` | Worked failure and schematic factorization of the bridge contribution |
| Main | `data_fig3_diagnosis` | Constituent-conditioned composition and address recovery |
| Main | `data_fig4_causal` | Crossed access/reading intervention and address specificity |
| Main | `data_fig5_content` | Edited-value following and joint original/edited correctness |
| Appendix | `figure2_diagnosis` | Diagnostic procedure schematic |
| Appendix | `data_app_localization` | Complete head maps and measured layer profiles |
| Appendix | `data_app_necessity` | Selected and layer-matched random knockout controls |
| Appendix | `figure3_method` | CoReTrace training and inference schematic |
| Appendix | `data_app_ablation` | Projection-restoration component comparison |
| Appendix | `data_app_capabilities` | Full HotpotQA, MMLU, and GSM8K comparisons |

The main paper contains four figures and the appendix six. The seven numerical PDFs and `story_overview.pdf` contain vector graphics with embedded fonts; previews are 300 dpi and 400 dpi, respectively. The two appendix conceptual illustrations are existing raster assets. `analysis/image_prompts.json` preserves their historical generation/editing records; reproducing a prompt need not reproduce the same pixels. `analysis/wrap_conceptual_figures.py` embeds the two existing PNGs in PDF containers without changing their pixels (optional dependencies: PyMuPDF and Pillow).

`paper/figures/captions.json` describes the current roles. Legacy metadata for earlier artwork is explicitly archived under `analysis/internal/` and does not identify the current overview's source. Final manuscript captions remain authoritative.

## Evidence and scope

The fresh audit at source revision `cf00035eb9b71bebf3ae88f76caf30ee9b58065c` checked 90 experiment manifests, 991,680 prediction records, 12 released paragraph readers, and 144 aggregate result entries. The coverage and implementation boundary are specified in `analysis/REPRODUCIBILITY.md`; detailed evidence is in `analysis/internal/current_evidence_audit.md` and `analysis/internal/current_audit/`.

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

## Lightweight reconstruction and packaging

The delivered `coretrace_plotting_code.zip` preserves the scripts and every small JSON/CSV input at the paths expected by those scripts. After extraction:

```bash
python -m pip install -r analysis/requirements.txt
python analysis/plot_results.py
python analysis/build_tables.py
python analysis/draw_story_overview.py
```

The reconstruction uses supplied experiment summaries and derived measurements. It requires no model weights, GPU, PyTorch, decompressed prediction archives, or network after dependency installation. The full repository's audit scripts additionally use prediction and feature archives. `SOURCE.json` distinguishes the earlier scientific baseline, the freshly audited revision, and the packaging HEAD, and records input hashes and dependency versions.

From the full working tree, after final PDF QA:

```bash
python analysis/package_delivery.py --dry-run
python analysis/package_delivery.py --verify-reproduction
```

The default output is `analysis/delivery/`. Other repository paths are refused; an external delivery directory may also be selected with `--output-dir`. The dry run only checks the plan. A real run requires a compiled PDF newer than its manuscript inputs and verifies local TeX dependencies.

| File | Contents |
| --- | --- |
| `coretrace_paper.pdf` | Complete compiled manuscript and appendix |
| `coretrace_overleaf.zip` | Formal LaTeX source, official styles, tables, and ten figure PDFs |
| `coretrace_figures.zip` | Ten formal figures in PDF/PNG and current role metadata |
| `coretrace_plotting_code.zip` | Three reconstruction scripts, supplied small inputs, documentation, and provenance |
| `delivery_manifest.json` | Artifact hashes, source revisions, and reconstruction outcome |
| `SHA256SUMS.txt` | Delivery checksums |

`--verify-reproduction` extracts the reconstruction archive into a fresh temporary tree with a cleared `PYTHONPATH`, regenerates seven numerical figures, all tables, and the overview, and compares table/CSV contents and deterministic overview assets against the working tree. It also verifies that source files stay unchanged during packaging. The two appendix conceptual illustrations remain supplied assets. GitHub synchronization is a separate operation.
