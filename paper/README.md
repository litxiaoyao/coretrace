# Paper source and formal figures

**When Correct Hops Fail to Compose: How Evidence Routing Shapes Local Reading**

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

The main text contains fourteen figures and one table. Figures 1–3 explain the evidence-use account and repair workflow. Figures 4–14 connect the recorded data to composition failures, head localization, causal interventions, relation reading, and repair. The appendix contains ten additional figures. Figure and subfigure captions are typeset by LaTeX, so their fonts and numbering follow the manuscript instead of being embedded in a composite plot.

| Figure | File stem | Role |
| --- | --- | --- |
| 1 | `figure1_teaser_revision` | Recorded composition failure, evidence-use functions, and repair overview |
| 2 | `figure2_diagnosis_revision` | Paired-query localization and factorized intervention framework |
| 3 | `figure3_method_revision` | CoReTrace adaptation, restoration, and evidence-selection workflow |
| 4 | `data_main_composition_address` | Correct constituents, composition failures, and address recovery |
| 5 | `data_main_structure_function` | Head-set overlap, paired preferences, and measured head examples |
| 6 | `data_main_localization` | Discovery direct-minus-composed bridge-attention maps and frozen selected heads |
| 7 | `data_main_head_causality` | Ranked and matched-random knockout on composed and direct queries |
| 8 | `data_main_address_routing` | Destination controls and routing repairs within address-recoverable failures |
| 9 | `data_main_relation_tokens_final` | Measured relation-sensitive span weights in the Angela receiver |
| 10 | `data_main_interaction_revision` | Access-dependent effects of transferring the same local reading pattern |
| 11 | `data_main_joint_case_revision` | Recorded four-arm case and joint-only corrections across models |
| 12 | `data_main_content_case_revision` | Original/edited evidence cards and local-value following at a stable address |
| 13 | `data_main_mechanism_closure_final` | Address recovery, bridge access, and relation preference after repair |
| 14 | `data_main_address_signal_final` | Address-guided selection on ambiguous inputs |
| A1 | `data_app_localization` | Complete localization heatmaps and layer profiles |
| A2 | `data_app_head_overlap` | All-model head-set intersections |
| A3 | `data_app_necessity` | Knockout controls across all query types |
| A4 | `data_main_ambiguity` | Bridge selection and answering under candidate-ranking controls |
| A5 | `data_main_case` | Recorded Calvert bridge-disambiguation example |
| A6 | `data_app_ablation` | Projection restoration and capability recovery |
| A7 | `data_app_capabilities` | Complete capability benchmarks |
| A8 | `data_main_mechanism_cases` | Corvinus and Angela evidence-and-answer cases |
| A9 | `data_main_restoration_revision` | Constituent and joint answering after projection restoration |
| A10 | `data_main_repair_chain_revision` | Full address-readout and evidence-selection comparison |

Table 1 (`tables/main_results.tex`) reports the complete-method core benchmark comparison. Figure numbers follow the manuscript; historical file stems remain stable when their placement changes.

### Panel assets and typography

`\figurecontent{stem}` in `main.tex` first loads `figures/<stem>_panels.tex`. These generated layout files assemble independent panel artwork with native `subfigure` environments and captions. A single-panel or legacy asset without a layout file falls back to `figures/<stem>.pdf`. The same entry point is used by the wide figures, column figures, and appendix figures.

LaTeX sets subfigure captions in the manuscript's normal roman font at 9 pt. Panel artwork uses a consistent Times-compatible serif family; legends sit close to the plot and use the same data-to-color conventions throughout the paper. Source panel dimensions are chosen for their final column or page width. Captions are never resized together with artwork; the old height argument to `\widefigshort` is retained only for source compatibility and does not scale panel layouts.

The manuscript keeps the official ICML page dimensions and text sizes. Wide evidence blocks retain native panel sizes and captions, while the prose between them is balanced across columns. Related interaction, case, and repaired-state figures share a compact results page; the aggregate table and final selector figure follow on the last main-text page. Impact, disclosure, and references continue without an artificial page break. Appendix figures and tables use ordinary `htbp` float placement with compact positive separation, allowing explanatory text to fill space around the evidence instead of leaving gaps before fixed-position blocks. The final mechanism appendix continues the preceding sections without a forced blank remainder; its table-to-figure boundary keeps the final measurements and follow-up figures in reading order.

Figure 6 and Figure A1 use the recorded discovery direct-minus-composed bridge-attention scores. Outlines retain the frozen selected heads; Figure 6 additionally marks selected heads that are also in the direct-query top-`k` set. The case cards use recorded evidence, predictions, and measured quantities. Highlighting in a case card indicates the stated relation or answer and must not be interpreted as an unmeasured token-attribution score.

## Regeneration (repository root)

The repository's `analysis/plot_results.py` is the sole manuscript numerical plotting entry point. It reads the recorded summaries, frozen head rankings, and reader validation records; its main and appendix panels share the same collectors. There are no experimental result arrays in the renderer. The existing `analysis/build_tables.py` generates the numerical tables.

Regenerate the complete figure set with the existing entry point, then compile:

```bash
python analysis/plot_results.py
make -C paper
```

The renderer writes vector PDF and 300-dpi PNG artwork, along with the panel layout files consumed by the manuscript. All numerical plot families use the same style helpers; same-family appendix panels are regenerated with the main figures. The CSV summaries and input manifests retain the recorded source values. Existing derived-array generation remains separate from rendering.

To recompute the new derived arrays from the recorded raw inputs, run:

```bash
python analysis/derive_structure_evidence.py
python analysis/derive_causal_evidence.py
```

Both analysis scripts default to the frozen source commit `5586f3816903e64334de80e06b74c6d7b1499b18` and verify archived source identities and numerical summaries. They read captures, predictions, and frozen reader weights; they perform no training, model inference, or plotting. The sole numerical plotting entry point remains `analysis/plot_results.py`.

To regenerate numerical tables as well, run `python analysis/build_tables.py` from the repository root before compiling. Table sources and the plotting entry point remain separate.

The supplied figure PDFs permit direct manuscript compilation without Python. The current figure placements and captions are defined by the LaTeX manuscript. See `analysis/README.md` for the numerical inputs, reconstruction steps, and retained historical tooling.
