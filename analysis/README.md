# Evidence analysis and manuscript reconstruction

**When Correct Hops Fail to Compose: How Evidence Routing Shapes Local Reading**

This directory contains the experiment analysis, recorded measurements, and figure/table reconstruction for CoReTrace. The LaTeX manuscript and publication assets are under `paper/`; the scientific implementation, datasets, and original experiment results remain in `coretrace/`, `scripts/`, `data/`, and `outputs/`.

## Regenerate figures and tables

Use Python 3.10 or newer with NumPy, Matplotlib and PyMuPDF, plus pdfLaTeX for the LaTeX figure overviews. From a complete Git checkout, run:

```bash
python -m pip install numpy matplotlib pymupdf
python analysis/plot_results.py
python analysis/build_tables.py
```

`plot_results.py` remains the single manuscript numerical plotting entry point. It loads the verified original collectors from commit `4990754cb73512599adfea9519862868b4260dbf`; a checkout must contain that commit (a source ZIP or shallow clone alone is insufficient). The default command, equivalently `python analysis/plot_results.py --only publication`, redraws the current 14 main-text and 10 appendix figures from the released measurements. It does not recompute experiments or rewrite those input CSVs.

Every multi-panel figure has independent vector PDF and 300-dpi PNG panels plus a `paper/figures/<stem>_panels.tex` file. The manuscript inputs that file, so LaTeX owns the subfigure counters, labels and 9-pt captions. Numerical `<stem>.pdf/.png` files are also refreshed as standalone previews, with their captions typeset by the same LaTeX settings. The three original conceptual PNGs are preserved byte-for-byte; independent panels use exact clipped views with the old title bands replaced by LaTeX captions.

Numerical artwork uses the TrueType **Liberation Serif** family (Times-compatible metrics) and STIX mathematics. The same plotting helpers control main and appendix axes, compact legends, error bars, heatmaps and case cards. Figure 6 and Figure A1 use the recorded direct-minus-composed bridge-attention scores on one symmetric color scale, with the frozen selected-head sets outlined and direct-set overlap marked. Case highlights identify evidence roles and recorded answers, not unmeasured token-attribution scores.

Legacy `--only` tasks remain available when their underlying numerical exports need reconstruction. The publication renderer always runs last, even if `publication` is listed first, so a historical renderer cannot overwrite the current assets. `figure_data/input_manifest_publication.csv` records the exact file hashes used in the current render. No new model execution is required.

On a minimal TeX installation with missing generated format/font-map caches, first run `bash analysis/compile_paper.sh` using the committed figures. The existing build script prepares local caches under `analysis/tex_runtime/`; the plotter reuses them for the standalone previews. A normal complete TeX installation needs no such initialization.

### Current main-text figure inventory

| Figure | File stem under paper/figures | Role |
| --- | --- | --- |
| 1 | `figure1_teaser_revision` | Author-selected teaser |
| 2 | `figure2_diagnosis_revision` | Mechanistic-analysis framework |
| 3 | `figure3_method_revision` | CoReTrace workflow |
| 4 | `data_main_composition_address` | Composition failures and recoverable addresses |
| 5 | `data_main_structure_function` | Paired head structure and function |
| 6 | `data_main_localization` | Selected heads across layers |
| 7 | `data_main_head_causality` | Selected versus matched-random knockout |
| 8 | `data_main_address_routing` | Destination controls and matched routing corrections |
| 9 | `data_main_relation_tokens_final` | Relation-conditioned token weights |
| 10 | `data_main_interaction_revision` | Factorized mass/pattern intervention |
| 11 | `data_main_joint_case_revision` | Joint-only correction |
| 12 | `data_main_content_case_revision` | Reciprocal fact exchange |
| 13 | `data_main_mechanism_closure_final` | Locate, Route and Read after repair |
| 14 | `data_main_address_signal_final` | Address-guided evidence selection |

The manuscript TeX defines current figure placement and captions, including the appendix. The principal table is `paper/tables/main_results.tex`. See [figure_data/README.md](figure_data/README.md) for measured quantities and populations.

## Reconstruct the analysis

The derived head structure and causal evidence are retained in `internal/v3_structure_evidence.json` and `internal/v3_causal_evidence.json`. Recompute from the archived sources with:

```bash
python analysis/derive_structure_evidence.py
python analysis/derive_causal_evidence.py
```

Both default to source commit `5586f3816903e64334de80e06b74c6d7b1499b18` and validate frozen identities, predictions, and recorded measurements. These commands require the corresponding Git history. The derivations perform no model training or inference; their source identities and measurements are retained in the two JSON files.

To recompute the routing and paired-relation summaries from the recorded experiment artifacts:

```bash
python analysis/derive_story_adapted_routing.py --seed 42
python analysis/derive_story_relation_reading.py \
  analysis/figure_data/data_revision_relation_reading_qwen3_4b.json.gz \
  analysis/figure_data/data_revision_relation_reading_qwen3_8b.json.gz \
  analysis/figure_data/data_revision_relation_reading_llama3_8b.json.gz
```

The full raw relation-reading captures, pilot, frozen scopes, per-receiver measurements, summaries, and source manifests are retained. `capture_paired_relation_reading.py` and `capture_story_attention.py` are the original read-only capture tools; only use them with the recorded model/checkpoint and frozen inputs when new capture is actually required. See [REPRODUCIBILITY.md](REPRODUCIBILITY.md) for experimental protocols and data provenance.

`audit_experiments.py`, `audit_answer_forms.py` and `audit_clustered_contrasts.py` preserve experiment verification and the derivation of audit-based table/figure inputs. The `internal/` directory retains these scientific records, source snapshots and measured evidence. Historical manuscript editing notes and superseded installation/packaging tools are not part of this workflow.

## Evidence and scope

See [REPRODUCIBILITY.md](REPRODUCIBILITY.md) for the retained machine-readable audit evidence.

Principal composition uses 1,000 test sources. Address-readout failure subsets condition on the native model's constituent and composition outcomes. The factorial diagnostic uses 100 receivers in 25 discovery quadruplets; its bootstrap preserves these clusters. Reciprocal exchanges use 100 diagnostic sources and preserve full-input word and character multisets before the selector is recomputed.

Run labels 42/43/44 identify recorded executions. Selected-head training uses fixed source order and zero-initialized deltas, and its source/loss/gradient sequences agree within each model across runs. Reported sample SD describes those executions; source-bootstrap intervals describe source sampling. The access experiment uses its own native baseline, including Qwen3-8B's 28.9% reference versus 29.2% in the principal evaluation.

Core/HotpotQA scores require alias exact match and completion within the 32-token budget. MMLU uses same-prefill option probabilities. GSM8K uses a parsed final numerical answer within a 512-token budget. `analysis/figure_data/README.md` defines the exported quantities and their denominators.

## Build and inspect the manuscript

```bash
bash analysis/compile_paper.sh
```

This writes `analysis/build_final/main.pdf` and retains the exact source snapshot and logs. When PyMuPDF is installed, the build deduplicates repeated embedded PDF resources without rasterizing pages or changing their content. It uses the original ICML template and keeps generated TeX caches inside `analysis/tex_runtime/` where needed. Inspect the compiled PDF page by page before copying the verified files into the formal source directory:

```bash
cp analysis/build_final/main.pdf paper/main.pdf
cp analysis/build_final/main.bbl paper/main.bbl
```

See `paper/README.md` for TeX/Overleaf alternatives. For an isolated build, use `bash analysis/compile_paper.sh paper analysis/build_review`. Nonstandard TeX trees can be selected via `CORETRACE_TEX_DIST`; `CORETRACE_LOCAL_TEX=1` enables local cache recovery.
