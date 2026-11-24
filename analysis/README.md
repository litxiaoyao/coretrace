# Reconstructing the paper's figures and tables

This directory contains the evidence analysis and presentation code for **When Correct Hops Fail to Compose: Evidence Access Shapes Local Reading**. The numerical figures and LaTeX tables are generated from completed experiment summaries and explicitly listed derived measurements. The plotting code contains no handwritten experimental result values.

## Scientific organization

The main paper follows a specific question: why can a model answer both constituent questions correctly yet fail their composition? It connects four findings:

1. Composition can fail even when the two constituent answers are correct and a fitted reader can recover the bridge paragraph's address.
2. Factorizing attention separates paragraph access mass from the conditional distribution within that paragraph. Their interaction shows that the effect of local reading depends on access.
3. Reciprocal content exchanges preserve global word and character counts while testing whether answers follow the relevant local value.
4. CoReTrace combines selected-head adaptation, fixed native-projection restoration, and input-derived evidence selection. Ambiguous title-link candidates provide a direct test of the address reader's application value.

The main text contains the scientific argument, its controlled interventions, and the principal application results. The appendix provides complete head maps, necessity controls, reader and selector comparisons, constituent outcomes, capability changes, scoring diagnostics, training details, and recorded-run statistics. Discovery diagnostics and full test-panel results retain separate denominators.

## Run the numerical reconstruction

Use Python 3.10 or newer from the repository root. Figure generation requires NumPy and Matplotlib; table generation uses the Python standard library.

```bash
python -m pip install numpy matplotlib
python analysis/plot_results.py
python analysis/build_tables.py
```

The commands regenerate:

- Seven numerical figures as vector PDF and 300-dpi PNG in `paper/figures/`.
- Their observations, aggregates, and source paths as CSV files in `analysis/figure_data/`.
- The manuscript's numerical LaTeX tables in `paper/tables/`.
- The input inventories `analysis/figure_data/input_manifest.csv` and `analysis/figure_data/table_inputs.json`.

The plotting script also accepts a subset, for example:

```bash
python analysis/plot_results.py --only diagnosis causal content
```

A partial run writes a separate partial manifest; a complete run refreshes the complete manifest. Always execute both complete commands before packaging a revised set of results.

### Formal figure inventory

| Manuscript role | File stem | Contents |
| --- | --- | --- |
| Figure 1 | `figure1_teaser` | The composition failure, access/reading interaction, and evidence-based repair |
| Figure 2 | `figure2_method` | Offline preparation and inference from the input |
| Figure 3 | `data_fig3_diagnosis` | Constituent-conditioned composition failure and address recovery on those failures |
| Figure 4 | `data_fig4_causal` | Mass × conditional-attention interaction and paragraph-calibration controls |
| Figure 5 | `data_fig5_content` | Edited-value following and obsolete-answer persistence |
| Appendix | `data_app_localization` | Complete head maps and frozen selections |
| Appendix | `data_app_necessity` | Selected and layer-matched random knockout controls |
| Appendix | `data_app_ablation` | Complete component comparisons |
| Appendix | `data_app_capabilities` | Changes on HotpotQA, MMLU, and GSM8K |

Figures 1 and 2 were created with ChatGPT's built-in image generation and then inspected against the method. Their generation and editing prompts are in `analysis/image_prompts.json`. Their PDFs embed the supplied PNGs at 6.75-inch width without resampling. These two conceptual illustrations are supplied assets; the Python numerical-plotting script regenerates the other seven figures. Reissuing an image-generation prompt need not produce pixel-identical illustrations. To rebuild just their font-free PDF containers from the supplied PNGs, install PyMuPDF and Pillow, then run `python analysis/wrap_conceptual_figures.py`. This operation preserves the original RGB pixels and does not regenerate the images.

## Lightweight reproduction archive

The delivered `coretrace_plotting_code.zip` preserves the project-relative layout of the scripts and every small JSON/CSV input they read. It includes `analysis/requirements.txt`, the input inventories, an input-hash record, and the scientific source commit. After extracting it into an empty directory:

```bash
python -m pip install -r analysis/requirements.txt
python analysis/plot_results.py
python analysis/build_tables.py
```

These commands require no model weights, PyTorch, GPU, network access after dependency installation, or decompressed prediction archives. Required derived JSON measurements retain their original paths under `analysis/internal/`; that directory name does not imply that the package recomputes them from raw model outputs. The package supplies those measurements as inputs. `analysis/figure_data/README.md` defines the figure populations and uncertainty conventions.

### Scope of reproducibility

The lightweight archive reproduces the **numerical figures and tables** from the supplied summaries and derived measurements. It does not rerun model training, model inference, or the raw-prediction verification analyses.

The current repository release omits `coretrace/models/` and the trained model/slice weights. Those omissions prevent a complete model-level rerun from the release alone. Regenerating the derived measurements from archived predictions additionally requires the full repository data and prediction/feature archives, rather than just the small-input reproduction archive. No replacement model implementation or checkpoint is supplied by the presentation pipeline.

Optional `analysis/audit_*.py` scripts can be included with `--include-audit-code` when packaging. They are supplied for inspection and use with the full repository; they are not part of the standalone figure/table execution path and may require additional dependencies and archived data.

## Statistical and evaluation conventions

- The principal composed comparison uses all 1,000 test sources. The native known-hop failure subset is defined before evaluating repairs. The shared-context factorial experiment instead uses 100 receivers in 25 discovery quadruplets.
- Error bars described as run dispersion use sample standard deviation across recorded runs. Selected-head training has fixed ordering, zero-initialized deltas, and identical recorded training traces across nominal seeds. Such dispersion is not evidence of independent initialization robustness.
- Paired intervals use source-aligned outcomes; repair comparisons first average a source's outcomes across the recorded runs. The factorial intervals preserve quadruplet clusters.
- The access experiment uses its own native reference. Qwen3-8B records 28.9% native accuracy there and 29.2% in the principal evaluation, under different batch settings.
- Core/HotpotQA primary scoring requires EOS completion and normalized answer-alias exact match within 32 generated tokens. MMLU uses same-prefill option-probability accuracy. GSM8K uses numerical equality from the required final answer line within a 512-token budget, without an EOS requirement.
- Reciprocal exchanges preserve complete-context word and character multisets. These preservation checks apply to the complete context before the evidence selector is rerun.

## Build and package the delivery

Compile the paper using the commands in `paper/README.md`, then run:

```bash
python analysis/package_delivery.py --dry-run
python analysis/package_delivery.py --output-dir ../coretrace_delivery --verify-reproduction
```

The output directory must be outside the repository. The script uses an explicit file allowlist, checks the manuscript's local inputs and figure references, and checks that the compiled PDF is newer than its manuscript inputs. It creates:

| File | Contents |
| --- | --- |
| `coretrace_paper.pdf` | The compiled paper and appendix |
| `coretrace_overleaf.zip` | Complete LaTeX source, official style files, tables, and the nine formal figure PDFs |
| `coretrace_figures.zip` | The nine formal figures, each as PDF and PNG |
| `coretrace_plotting_code.zip` | Plot/table scripts, prompts, small source inputs, requirements, and source metadata |
| `delivery_manifest.json` | Artifact hashes, source metadata, and reconstruction-check outcome |
| `SHA256SUMS.txt` | SHA-256 checksums for the delivered artifacts and manifest |

`--verify-reproduction` extracts the code archive into a fresh temporary directory, runs both reconstruction commands there, and compares the resulting tables and numerical CSVs with the current project. It does not use or change the original outputs. A dry run does not write packages and can report a missing compiled PDF while the manuscript is still being prepared. A real packaging run requires a current `paper/main.pdf`.

The Overleaf archive excludes internal analysis notes, older figures, uploaded reference papers, prediction archives, and checkpoints. The scientific baseline commit and the official template source are recorded in the package metadata. Publication and GitHub synchronization are separate actions; this script performs neither.
