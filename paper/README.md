# Paper source and formal figures

**When Correct Hops Fail to Compose: Locating, Routing, and Reading Evidence**

`main.tex` compiles the complete manuscript and appendix. The main text follows **Introduction – Related Work – Method – Experiments – Conclusion**. Its **Locate–Route–Read** account connects recoverable bridge addresses, attention allocation to the relevant paragraph, and relation-conditioned local reading. Component structure and function, matched address-to-routing interventions, and receiver-level joint corrections connect the three operations. CoReTrace applies this mechanism to improve composition and follow local fact changes.

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

The main text targets eight pages and contains ten figures—three supplied conceptual figures and seven empirical figures—and one table. Figures 1–3 retain their artwork, full TeX environments, and captions exactly. Figures 4–8 use full-width layouts to expose component-level and matched causal evidence. The answer-based Corvinus/Angela case study is retained in the appendix.

| Figure | File stem | Role |
| --- | --- | --- |
| 1 | `figure1_teaser` | Supplied teaser, preserved exactly |
| 2 | `figure2_diagnosis` | Supplied mechanistic-analysis framework, preserved exactly |
| 3 | `figure3_method` | Supplied CoReTrace workflow, preserved exactly |
| 4 | `data_main_composition_address` | Correct constituent answers, composition failures, and bridge-address recovery within those failures |
| 5 | `data_main_structure_function` | Head-set structure, paired root/bridge preferences, and measured head-level functional examples |
| 6 | `data_main_head_causality` | Selected and matched-random knockout for composed/direct-target queries across all models |
| 7 | `data_main_address_routing` | Destination controls, native allocation in address-decodable failures, and routing corrections on the same sources |
| 8 | `data_main_causal_pair` | Crossed mass/pattern intervention and access-dependent pattern effects |
| 9 | `data_main_joint_rescue` | Joint-only corrections within the paired four-arm outcomes |
| 10 | `data_fig5_content` | Local-value following at a stable selected evidence address |

Table 1 (`tables/main_results.tex`) reports the complete-method core benchmark comparison. The appendix contains eight figures: complete head maps, all-model head intersections, all-query knockout controls, candidate-ranking comparisons, the Calvert example, projection-restoration analysis, capability comparisons, and the Corvinus/Angela evidence-and-answer cases. Figure numbers follow the manuscript; older file stems are retained when their placement changes.

## Regeneration (repository root)

The repository's `analysis/plot_results.py` is the sole manuscript numerical plotting entry point. It reads the recorded summaries, frozen head rankings, and reader validation records; its main and appendix panels share the same collectors. There are no experimental result arrays in the renderer. The existing `analysis/build_tables.py` generates the numerical tables.

For revision 3, regenerate the combined diagnostic and four new mechanism figures from the released derived arrays:

```bash
python analysis/plot_results.py --only composition_address mechanism_structure mechanism_causality address_routing joint_rescue
make -C paper
```

This produces `data_main_composition_address`, `data_main_structure_function`, `data_main_head_causality`, `data_main_address_routing`, and `data_main_joint_rescue` as vector PDF and 300-dpi PNG, with new CSVs and an input manifest. Existing result CSVs and Figures 1–3 remain unchanged. The earlier case figure remains reproducible with the `mechanism_cases` task.

To recompute the new derived arrays from the recorded raw inputs, run:

```bash
python analysis/derive_structure_evidence.py
python analysis/derive_causal_evidence.py
```

Both analysis scripts default to the frozen source commit `5586f3816903e64334de80e06b74c6d7b1499b18` and verify archived source identities and numerical summaries. They read captures, predictions, and frozen reader weights; they perform no training, model inference, or plotting. The sole numerical plotting entry point remains `analysis/plot_results.py`.

To regenerate the complete numerical figure and table set when needed:

```bash
python analysis/plot_results.py
python analysis/build_tables.py
make -C paper
```

The supplied figure PDFs permit direct manuscript compilation without Python. The current figure placements and captions are defined by the LaTeX manuscript. See `analysis/README.md` for the numerical inputs, reconstruction steps, and retained historical tooling.
