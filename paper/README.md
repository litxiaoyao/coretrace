# Paper source and formal figures

**When Correct Hops Fail to Compose: Evidence Access Shapes Local Reading**

`main.tex` compiles the complete manuscript and appendix. The main text follows **Introduction – Related Work – Method – Experiments – Conclusion**. It asks why correct constituent answers fail to compose, distinguishes recoverable evidence location from effective evidence use, tests the interaction of paragraph access and local reading, and applies those findings through CoReTrace.

The appendix contains the complete experimental protocols, head maps, necessity controls, reader and selector diagnostics, component comparisons, constituent results, capability evaluations, and uncertainty details. Appendix figures and tables have their own `A` numbering. Numerical results and captions share the source summaries described in the accompanying analysis documentation.

The supplied manuscript uses the official anonymous submission mode. Author, affiliation, and correspondence fields can be filled when preparing a named preprint or an accepted version.

## Compile

The source uses the official **ICML 2027** style and bibliography style, together with the template's auxiliary `algorithm.sty`, `algorithmic.sty`, and `fancyhdr.sty` files.

- Author instructions: <https://icml.cc/Conferences/2027/AuthorInstructions>
- Official style archive: <https://media.icml.cc/Conferences/ICML2027/styles/icml2027.zip>

With a normal TeX installation containing `latexmk`, pdfLaTeX, BibTeX, and the packages declared in `main.tex`, run from this directory:

```bash
make
```

Equivalently:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error main.tex
```

If `latexmk` is unavailable, `make pdf-pdflatex` performs the standard sequence:

```bash
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex
```

For Overleaf, upload `coretrace_overleaf.zip`, choose `main.tex` as the main document, and use pdfLaTeX. The archive places `main.tex`, the bibliography, styles, and this Makefile at its root, with `sections/`, `tables/`, and `figures/` beside them. A generated `main.bbl` is included when available; `references.bib` remains the bibliography source.

`make clean` removes auxiliary compilation files while retaining the PDF. `make distclean` also removes the compiled PDF. Neither command changes manuscript sources or figures.

## Formal figure set

The manuscript uses exactly these nine figure stems, all under `figures/`:

| Role | File stem |
| --- | --- |
| Figure 1: scientific teaser | `figure1_teaser` |
| Figure 2: method overview | `figure2_method` |
| Figure 3: failure and address diagnosis | `data_fig3_diagnosis` |
| Figure 4: access/reading interaction | `data_fig4_causal` |
| Figure 5: local-content response | `data_fig5_content` |
| Appendix: head localization | `data_app_localization` |
| Appendix: necessity controls | `data_app_necessity` |
| Appendix: component comparisons | `data_app_ablation` |
| Appendix: capability changes | `data_app_capabilities` |

All formal figures are supplied as PDF and PNG. Figures 1 and 2 are image-generated conceptual illustrations; their PDFs embed the final PNGs at the original aspect ratio. The seven numerical figures are vector PDFs with embedded fonts and matching 300-dpi PNG previews. The LaTeX manuscript uses the PDFs. Earlier exploratory images are not included in the Overleaf or formal-figure delivery archives.

## Regenerate numerical figures and tables

From the complete repository root, or from the separate lightweight reproduction archive, run:

```bash
python analysis/plot_results.py
python analysis/build_tables.py
```

Python 3.10 or newer, NumPy, and Matplotlib are sufficient. `analysis/image_prompts.json` records the conceptual figure prompts and edits; those illustrations are supplied assets rather than outputs of the numerical plotting script. The reconstruction scripts, requirements, CSV figure data, and all small JSON/CSV inputs are provided in `coretrace_plotting_code.zip`. That archive preserves project-relative paths and includes its source commit and file hashes.

This is reproducibility of **figures and tables from completed measurements**. The current repository release omits the model integration package `coretrace/models/` and trained weights, which precludes a complete model-training/inference rerun from the release alone. Raw-prediction verification also requires the full archived data beyond the lightweight reconstruction package. The manuscript does not claim end-to-end reproducibility from the Overleaf source.

## Packaging

From the full repository root, after compiling `paper/main.pdf`:

```bash
python analysis/package_delivery.py --output-dir ../coretrace_delivery --verify-reproduction
```

The script creates the compiled PDF, Overleaf source archive, formal-figure archive, lightweight plotting/table archive, and checksums. It includes only formal manuscript assets; uploaded reference papers, internal analysis notes, model checkpoints, and older figures remain outside the Overleaf package.
