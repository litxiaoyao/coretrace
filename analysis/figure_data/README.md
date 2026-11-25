# Figure data and population definitions

The numerical input and export files here support the main and appendix figures and tables. Run `python analysis/plot_results.py` from a complete Git checkout containing the base plotting commit listed in [../README.md](../README.md). Model execution is unnecessary for plotting from the stored summaries.

`input_manifest.csv` records paths, sizes and SHA-256 hashes for a complete plotting run; named partial-run manifests preserve the corresponding input inventories. `table_inputs.json` records the inputs read by the table generator. The raw relation-reading banks (`data_revision_relation_reading_*.json.gz`), the verified pilot, per-receiver CSVs, frozen scopes and source manifests retain the recorded experiment evidence. File stems may reflect earlier figure numbering; the current manuscript TeX and [main figure inventory](../README.md) define actual placement.

## Measured data families

| Data family | Contents |
| --- | --- |
| `data_fig3_diagnosis_*`, `data_main_composition*` | Composition and bridge-address accuracy on the fixed native populations |
| `data_app_head_*`, `data_app_localization*`, `data_main_structure_function_*` | Head rankings, selected sets, intersections, paired attention profiles |
| `data_app_necessity.csv`, `data_main_head_causality.csv` | Ranked and layer-matched random knockout |
| `data_fig4_causal_*`, `data_main_address_routing_*`, `data_main_joint_rescue*` | Access controls, matched routing corrections, factorial contrasts and joint corrections |
| `data_revision_case_records.json`, `data_revision_joint_counts.csv`, `data_revision_content.csv`, `data_fig5_content_*` | Recorded cases, joint-only corrections and reciprocal content outcomes |
| `data_revision_adapted_routing*`, `data_revision_relation_reading_*`, `data_revision_token_capture.json` | Paired model-state measurements, original captures, per-receiver outcomes and relation-reading contrasts |
| `data_revision_mechanism_repair.csv`, `data_revision_repair_components.csv`, `data_app_ablation_*`, `data_app_capabilities_*` | Repair mechanism, component and capability results |

## Denominators, interventions, and uncertainty

- Diagnosis panel (a) conditions on both constituent answers being correct under the native model. Panel (b) additionally requires native composition failure. Its data are reconstructed from archived features and fitted reader weights in `analysis/internal/readout_validation.json`. The overall population is exported separately.
- The factorial diagnostic contains 100 receivers in 25 shared-context discovery quadruplets. Intervals resample whole quadruplets. The paragraph-address control uses the separate 1,000-source test evaluation and its own native reference; Qwen3-8B's access baseline is 289/1000, while its principal evaluation records 292/1000.
- The factorial intervention changes attention mass and/or the normalized pattern within the bridge paragraph. Value vectors are computed by the receiving model and its output-projection weights are unchanged. Earlier interventions can influence downstream activations through the forward pass.
- Trained-method error bars show sample SD across three recorded executions. Selected-head source/loss/gradient traces agree across their nominal seed labels. The SD therefore describes this recorded execution protocol. Native references are used once, and repeated native content records are checked for agreement.
- Content metrics use all 100 diagnostic sources. Edited-value following measures the edited answer; joint correctness requires both original and edited answers to be correct. Full-input word and character multisets are preserved before the selector is rerun. The exports retain actual-swap counts and all outcome fields.
- Capability metrics are completed-answer alias EM for HotpotQA, same-prefill option-probability accuracy for MMLU, and parsed numerical-answer accuracy for GSM8K. The MMLU free-generation field is a separate diagnostic.
- Head maps use zero-based layer/query-head indices. Frozen selections supply the outlines. Random knockout controls match per-layer counts; their measured overlap with selected heads is exported.

All numerical observations retain their source paths. Percentages and contrasts are calculated from recorded counts or paired estimates. Numerical plots use embedded DejaVu Sans, white backgrounds, and a common blue/orange/gray palette; head maps use a shared diverging scale. The plots are unsmoothed. Final captions and interpretation are maintained in the manuscript.
