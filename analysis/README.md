# Evidence analysis and manuscript reconstruction

This directory supports **When Correct Hops Fail to Compose: Locating, Routing, and Reading Evidence**. The **Locate–Route–Read** account connects recoverable bridge addresses, attention allocation to the relevant paragraph, and relation-conditioned local reading. Paired head structure/function, recoverable addresses linked to same-source routing corrections, and receiver-level joint interventions support the mechanism and its application through CoReTrace. Figure and table generators read completed summaries and explicitly listed derived measurements.

## Regenerate figures and tables

Use Python 3.10 or newer. NumPy and Matplotlib support numerical plotting; table construction uses the standard library. `analysis/plot_results.py` is the sole manuscript numerical plotting entry point.

Revision 3 connects the mechanism with a combined diagnostic and four new mechanism tasks:

```bash
python -m pip install numpy matplotlib
python analysis/plot_results.py --only composition_address mechanism_structure mechanism_causality address_routing joint_rescue
```

| Task | Output stem | Numerical inputs |
| --- | --- | --- |
| `composition_address` | `data_main_composition_address` | Existing composition and failure-readout CSVs with matched subgroup counts |
| `mechanism_structure` | `data_main_structure_function` | `internal/v3_structure_evidence.json`: frozen head sets, all 100 paired source profiles, measured head-level paragraph arrays and same-context calibration answers |
| `mechanism_causality` | `data_main_head_causality` | Existing `figure_data/data_app_necessity.csv`: all three models and measured knockout doses |
| `address_routing` | `data_main_address_routing` | `internal/v3_causal_evidence.json` plus original destination-control summaries: fixed same-source readout/routing joins |
| `joint_rescue` | `data_main_joint_rescue` | `internal/v3_causal_evidence.json`: all four outcomes per shared-context receiver |

New tasks write new supporting CSVs and an input manifest, without rewriting the existing result CSVs. The supplied artwork and full TeX environments for Figures 1–3 remain unchanged. The previous Corvinus/Angela figure is retained in the appendix and remains reproducible through `--only mechanism_cases`; the Calvert example also remains in the appendix.

The released derived JSONs make figure reproduction lightweight. To derive them again from the recorded Git inputs:

```bash
python analysis/derive_structure_evidence.py
python analysis/derive_causal_evidence.py
```

Both extraction scripts default to source commit `5586f3816903e64334de80e06b74c6d7b1499b18`. The structure derivation verifies the 600 capture records against every released ranking statistic and preserves the exact random-head control used for knockout. The causal derivation reapplies the frozen native readers, matches source/query identities, and verifies the released aggregate results. It retains the full four-arm outcomes and the native baselines for each pipeline. They do not run models or draw figures; `plot_results.py` remains the sole numerical plotting entry point. Source file hashes, fixed populations, and statistical definitions are documented in `internal/v3_structure_evidence.md` and `internal/v3_causal_evidence.md`.

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
| Main 2 | `figure2_diagnosis` | Supplied mechanistic-analysis framework, preserved exactly |
| Main 3 | `figure3_method` | Supplied CoReTrace workflow, preserved exactly |
| Main 4 | `data_main_composition_address` | Correct constituent answers, composition failures, and bridge-address recovery within those failures |
| Main 5 | `data_main_structure_function` | Head-set structure, paired root/bridge preferences, and measured head-level functional examples |
| Main 6 | `data_main_head_causality` | Selected and matched-random knockout for composed/direct-target queries across all models |
| Main 7 | `data_main_address_routing` | Destination controls, native allocation in address-decodable failures, and routing corrections on the same sources |
| Main 8 | `data_main_causal_pair` | Crossed mass/pattern intervention and access-dependent pattern effects |
| Main 9 | `data_main_joint_rescue` | Joint-only corrections within the paired four-arm outcomes |
| Main 10 | `data_fig5_content` | Local-value following at a stable selected evidence address |
| Appendix | `data_app_localization` | Complete head maps and measured layer profiles |
| Appendix | `data_app_head_overlap` | All-model within-model head-set intersections |
| Appendix | `data_app_necessity` | All-query selected and matched-random knockout |
| Appendix | `data_main_ambiguity` | Candidate-ranking comparison |
| Appendix | `data_main_case` | Calvert candidate-selection example |
| Appendix | `data_app_ablation` | Projection-restoration component comparison |
| Appendix | `data_app_capabilities` | Full capability comparisons |
| Appendix | `data_main_mechanism_cases` | Corvinus and Angela evidence-and-answer cases |

The main text targets eight pages and contains ten figures—three supplied conceptual figures and seven empirical figures—and one table. The appendix contains eight figures with independent `A` numbering. New mechanism figures use fonts of at least 6 pt at their intended size. Vector PDFs and 300-dpi PNG previews are saved together. Current numbering and captions are defined by the LaTeX manuscript.

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

`analysis/package_delivery.py` is retained from an earlier delivery. Its configured figure inventory and reconstruction scope still name the earlier overview and figure arrangement. Inspect that inventory before using it for a new delivery; it is not the current ten-figure main-text specification. Its read-only planning command remains:

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
