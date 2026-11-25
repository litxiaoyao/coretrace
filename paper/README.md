# Paper source and formal figures

**When Correct Hops Fail to Compose: How Evidence Access Shapes Local Reading**

`main.tex` compiles the complete manuscript and appendix. The main text follows **Introduction – Related Work – Method – Experiments – Conclusion**. It asks why correct constituent answers fail to compose, causally localizes evidence-access heads, recovers the bridge addresses they carry, tests the interaction of paragraph access and local reading, and applies those findings through CoReTrace.

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

The eight-page main text uses eight figures and one table. Figures 1–3 retain the supplied artwork, figure environments, and captions exactly. Figure 7 is a full-width display of the crossed 2-by-2 attention intervention and its interaction effects; the remaining main-text numerical figures use single-column layouts.

| Figure | File stem | Role |
| --- | --- | --- |
| 1 | `figure1_teaser` | Portrait teaser |
| 2 | `figure2_diagnosis` | Mechanistic analysis |
| 3 | `figure3_method` | Deployment workflow |
| 4 | `data_main_localization` | Qwen and Llama head heatmaps with a shared vertical colorbar |
| 5 | `data_main_head_pair` | Layer-wise gap and matched knockout curves |
| 6 | `data_fig3_diagnosis` | Address readout on composition failures |
| 7 | `data_main_causal_pair` | Four intervention arms and access-dependent pattern effects |
| 8 | `data_fig5_content` | Edited-value and joint correctness |

Table 1 (`tables/main_results.tex`) reports the core benchmark comparison. The appendix contains complete head maps, within-model head-overlap plots, knockout controls, and the address-specific calibration controls (`data_app_access_controls`). Candidate-ranking comparisons (`data_main_ambiguity`), the saved worked example (`data_main_case`), projection-restoration analysis (`data_app_ablation`), and capability comparisons (`data_app_capabilities`) also appear in the appendix. Their file stems are stable even when their placement changes. Full component and capability tables retain the recorded results, including the tied composed EM of full and attention-only candidate ranking.

## Regeneration (repository root)

The repository's `analysis/plot_results.py` is the sole manuscript numerical plotting entry point. It reads the recorded summaries, frozen head rankings, and reader validation records; its main and appendix panels share the same collectors. There are no experimental result arrays in the renderer. The existing `analysis/build_tables.py` generates the numerical tables.

For this revision, the numerical redraw is limited to the causal panels:

```bash
python analysis/plot_results.py --only causal
make -C paper
```

This writes the full-width main interaction figure (`data_main_causal_pair`) and the appendix address-control figure (`data_app_access_controls`), along with their PNG previews and causal input manifest. It leaves Figures 1–3 unchanged.

To regenerate the complete numerical figure and table set when needed:

```bash
python analysis/plot_results.py
python analysis/build_tables.py
make -C paper
```

The supplied figure PDFs permit direct manuscript compilation without Python. The current figure placements and captions are defined by the LaTeX manuscript. See `analysis/README.md` for the numerical inputs, reconstruction steps, and retained historical tooling.
