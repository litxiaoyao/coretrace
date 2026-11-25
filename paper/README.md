# Paper source and formal figures

**When Correct Hops Fail to Compose: Diagnosing Evidence Access and Local Reading**

`main.tex` compiles the complete manuscript and appendix. The main text follows **Introduction – Related Work – Method – Experiments – Conclusion**. It asks why correct constituent answers fail to compose, distinguishes recoverable evidence location from effective evidence use, tests the interaction of paragraph access and local reading, and applies those findings through CoReTrace.

The appendix contains the complete experimental protocols, head maps, necessity controls, reader and selector diagnostics, component interventions, constituent results, capability evaluations, and uncertainty details. Appendix figures and tables have their own `A` numbering. Numerical results and captions share the source summaries described in the accompanying analysis documentation.

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

The eight-page main text uses 11 figures and two tables. Figures 1--3 retain the supplied artwork byte-for-byte; Figures 2 and 3 appear on separate pages. All quantitative figures and the worked example use single-column layouts. Related measurements share compact two-panel figures.

| Figure | File stem | Role |
| --- | --- | --- |
| 1 | `figure1_teaser` | Portrait teaser |
| 2 | `figure2_diagnosis` | Mechanistic analysis |
| 3 | `figure3_method` | Deployment workflow |
| 4 | `data_main_localization` | Qwen and Llama head heatmaps with a shared vertical colorbar |
| 5 | `data_main_head_pair` | Layer-wise gap and matched knockout curves |
| 6 | `data_fig3_diagnosis` | Address readout on composition failures |
| 7 | `data_main_causal_pair` | Access calibration and conditional pattern effects |
| 8 | `data_main_ambiguity` | Matched candidate-ranking control |
| 9 | `data_main_case` | Saved candidate-selection example |
| 10 | `data_fig5_content` | Edited-value and joint correctness |
| 11 | `data_main_restoration` | Matched projection-restoration control |

The appendix retains the full head heatmaps, knockout controls, and new three-model within-model UpSet plots (Figure A2). Table 1 reports the core benchmark comparison. Table 2 reports general capabilities. Table A14 retains every original component intervention and separates baseline configurations from the mechanistically-informed head-tuning family. Full and attention-only candidate-ranking configurations retain their actual tied composed EM.

## Regeneration (repository root)

The repository's `analysis/plot_results.py` is the sole manuscript numerical plotting entry point. It reads the recorded summaries, frozen head rankings, and reader validation records; its main and appendix panels share the same collectors. There are no experimental result arrays in the renderer. The existing `analysis/build_tables.py` generates tables, including the revised `main_results()`, `retention()`, and `component_ablation()` functions. No `redesign_main_figures.py` is needed.

```bash
python analysis/plot_results.py
python analysis/build_tables.py
cd paper && make
```

The supplied vector PDFs permit direct manuscript compilation without Python. See `analysis/REVISION_SINGLE_COLUMN.md` for source and validation scope for the cumulative revision.
