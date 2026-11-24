# Manuscript and formal figures

**When Correct Hops Fail to Compose: Diagnosing Evidence Access and Local Reading**

`main.tex` contains the complete anonymous ICML submission and appendix. The argument connects a contextual composition failure, a recoverable bridge-paragraph address, a controlled interaction between paragraph access and local reading, and a repair evaluated on the existing experiment records. The main text presents the central evidence, component comparison, ambiguous-candidate analysis, and local-fact validation. The appendix carries the complete protocol, controls, per-run results, capability evaluations, implementation details, and reproducibility scope.

## Compile and inspect

From the repository root:

```bash
bash analysis/compile_paper.sh
```

The compiled PDF and logs appear in `analysis/build_final/`. The script builds a fresh source snapshot and uses standard pdfLaTeX/BibTeX with the original template. In the supplied execution image, it generates the missing format and font maps under `analysis/tex_runtime/`. It leaves the system installation and manuscript inputs unchanged.

Inspect the **compiled PDF** page by page, including the appendix, and resolve layout or reference issues before promoting the result. After this check:

```bash
cp analysis/build_final/main.pdf paper/main.pdf
cp analysis/build_final/main.bbl paper/main.bbl
```

With a complete local TeX installation, `make -C paper` is also supported. `make -C paper pdf-pdflatex` performs the explicit pdfLaTeX–BibTeX–pdfLaTeX–pdfLaTeX sequence. For Overleaf, upload `coretrace_overleaf.zip`, select `main.tex`, and use pdfLaTeX. The archive contains the manuscript, bibliography, styles, sections, tables, and the ten formal figure PDFs.

The source uses the official anonymous **ICML 2027** template. Its style and bibliography files were checked byte-for-byte against the [official archive](https://media.icml.cc/Conferences/ICML2027/styles/icml2027.zip). The [author instructions](https://icml.cc/Conferences/2027/AuthorInstructions) define the submission format. The manuscript includes an impact statement and the required AI Disclosure Statement.

## Formal figure roles

The main paper has four figures; the appendix has six. Stable filenames preserve links to the recorded numerical data even where the manuscript figure numbers changed.

| Placement | File stem | Purpose |
| --- | --- | --- |
| Main | `story_overview` | Worked example and schematic attention factorization |
| Main | `data_fig3_diagnosis` | Composition failures and bridge-address readout on those failures |
| Main | `data_fig4_causal` | Access-by-reading interaction and paragraph-address controls |
| Main | `data_fig5_content` | Edited-value following and joint original/edited correctness |
| Appendix | `figure2_diagnosis` | Complete diagnostic procedure, shown schematically |
| Appendix | `data_app_localization` | Head maps, frozen selections, and layer profiles |
| Appendix | `data_app_necessity` | Selected-head and layer-matched random knockout controls |
| Appendix | `figure3_method` | Offline preparation and inference procedure |
| Appendix | `data_app_ablation` | Controlled effects of fixed projection restoration |
| Appendix | `data_app_capabilities` | Complete benchmark comparisons |

All figures have PDF and PNG versions. Seven numerical figures are vector PDFs with 300-dpi previews. `story_overview` is a separately generated vector diagram with a 400-dpi preview. The two appendix conceptual illustrations are supplied raster assets embedded in PDF containers. Their schematic marks illustrate the procedure; numerical evidence appears in the measured plots and tables. `figures/captions.json` and `figures/figure_sources.json` record current roles and provenance.

## Regenerate presentation assets

From the full repository root or the lightweight reproduction archive:

```bash
python analysis/plot_results.py
python analysis/build_tables.py
python analysis/draw_story_overview.py
```

Python 3.10 or newer, NumPy, and Matplotlib are sufficient. These commands regenerate the seven numerical figures, every numerical LaTeX table, and the vector overview. The table builder includes `main_components.tex` and `main_ambiguity.tex`, the compact main-text views of existing component and selector results. The supplied small JSON/CSV inputs preserve their original project-relative paths.

The two appendix conceptual illustrations remain supplied assets. Their historical generation prompts are recorded in `analysis/image_prompts.json`. If only their PDF containers need rebuilding from the supplied PNGs, use `python analysis/wrap_conceptual_figures.py` with PyMuPDF and Pillow installed.

## Reproducibility and delivery

`analysis/REPRODUCIBILITY.md` specifies the verified prediction, readout, and table coverage; recorded-run conventions; and the runtime modules required for a complete GPU rerun. The numerical reconstruction package uses the existing measurements and requires no model execution.

After the final PDF has passed visual QA and been copied to `paper/main.pdf`:

```bash
python analysis/package_delivery.py --dry-run
python analysis/package_delivery.py --verify-reproduction
```

Delivery files are written under `analysis/delivery/`. They comprise the PDF, Overleaf source, formal figure archive, lightweight reconstruction archive, verification manifest, and checksums. The Overleaf archive excludes earlier exploratory figures, uploaded reference papers, internal review notes, prediction archives, and checkpoints.
