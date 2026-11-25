# Paper source and formal figures

**When Correct Hops Fail to Compose: Locating, Routing, and Reading Evidence**

`main.tex` compiles the complete manuscript and appendix. The main text follows **Introduction – Related Work – Method – Experiments – Conclusion**. Its **Locate–Route–Read** account connects recoverable bridge addresses, attention allocation to the relevant paragraph, and relation-conditioned local reading. Causal localization, access controls, crossed attention interventions, and recorded cases support this account and its application through CoReTrace.

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

For Overleaf, upload the current contents of `paper/` or a source archive built from them, choose `main.tex` as the main document, and use pdfLaTeX. Place `main.tex`, the bibliography, styles, and this Makefile at the archive root, with `sections/`, `tables/`, and `figures/` beside them. Include a generated `main.bbl` when available; `references.bib` remains the bibliography source.

`make clean` removes auxiliary compilation files while retaining the PDF. `make distclean` also removes the compiled PDF. Neither command changes manuscript sources or figures.

## Formal figure set

The main text targets eight pages and contains eleven figures—three supplied conceptual figures and eight empirical figures—and one table. Figures 1–3 retain the supplied artwork, figure environments, and captions exactly. Figure 9 presents the crossed 2-by-2 attention intervention at full width; Figure 11 presents two recorded mechanism cases at full width. The remaining empirical figures use single-column layouts.

| Figure | File stem | Role |
| --- | --- | --- |
| 1 | `figure1_teaser` | Portrait teaser |
| 2 | `figure2_diagnosis` | Mechanistic analysis |
| 3 | `figure3_method` | Deployment workflow |
| 4 | `data_main_composition` | Composition success and failure within the native constituent-correct population |
| 5 | `data_main_localization` | Qwen and Llama head heatmaps with a shared vertical colorbar |
| 6 | `data_main_head_pair` | Layer-wise gap and matched knockout curves |
| 7 | `data_fig3_diagnosis` | Address readout on composition failures |
| 8 | `data_app_access_controls` | Bridge, root, and other-paragraph access calibration; restored to the main text |
| 9 | `data_main_causal_pair` | Four intervention arms and access-dependent pattern effects |
| 10 | `data_fig5_content` | Edited-value and joint correctness |
| 11 | `data_main_mechanism_cases` | Corvinus composition and Angela routing/reading cases |

Table 1 (`tables/main_results.tex`) reports the core benchmark comparison. The appendix contains seven figures: complete head maps, within-model head-overlap plots, knockout controls, candidate-ranking comparisons (`data_main_ambiguity`), the earlier Calvert worked example (`data_main_case`), projection-restoration analysis (`data_app_ablation`), and capability comparisons (`data_app_capabilities`). File stems remain stable when their placement changes, including `data_app_access_controls` in the main text. Full component and capability tables retain the recorded results, including the tied composed EM of full and attention-only candidate ranking.

## Regeneration (repository root)

The repository's `analysis/plot_results.py` is the sole manuscript numerical plotting entry point. It reads the recorded summaries, frozen head rankings, and reader validation records; its main and appendix panels share the same collectors. There are no experimental result arrays in the renderer. The existing `analysis/build_tables.py` generates the numerical tables.

For revision 2, regenerate the composition-gap, causal, and mechanism-case figures:

```bash
python analysis/plot_results.py --only composition causal mechanism_cases
make -C paper
```

This writes `data_main_composition`, `data_main_causal_pair`, `data_app_access_controls`, and `data_main_mechanism_cases`, along with PNG previews, supporting CSVs, and a partial input manifest. The mechanism-case task reads `analysis/internal/mechanism_case_records_20261125_v2.json`, which records the Corvinus and Angela contexts and predictions from completed experiments. It leaves Figures 1–3 unchanged and runs no model inference.

To regenerate the complete numerical figure and table set when needed:

```bash
python analysis/plot_results.py
python analysis/build_tables.py
make -C paper
```

The supplied figure PDFs permit direct manuscript compilation without Python. The current figure placements and captions are defined by the LaTeX manuscript. See `analysis/README.md` for the numerical inputs, reconstruction steps, and retained historical tooling.
