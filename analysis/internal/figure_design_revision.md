# Numerical figure design revision

## Reference figures inspected visually

- **Tracing the Persona Circuit**, supplied ICML camera-ready PDF: p. 4 framework and p. 6 line plots, layer bars, causal head maps, and paired neuron cards.
- **Emotion-circuit ICML camera-ready paper**: p. 3 two-stage framework and p. 5 compact layer-analysis panels.
- **Bridging the Language Gap**, supplied AAAI paper: p. 5 shared-neuron panels and grouped comparison table with colored gains.
- **Interpret and Improve In-Context Learning via the Lens of Input-Label Mappings**, supplied ACL paper: p. 4 framework and p. 6 three-panel mechanism figure.

These references use compact lettered panels, serif annotations, restrained grids and axes, pale stage-level backgrounds, and clear method hierarchies. Their useful conventions are applied to the present measurements with consistent colors and readable, fixed-width exports.

## Shared design

- Width: 6.75 inches, matching the paper's full text width.
- Typography: Times-like STIXGeneral, supplied by Matplotlib, with DejaVu Serif fallback; 9-point text, 8.5-point ticks, and 10-point panel headings. STIX math aligns with the text family.
- Colors: teal `#087F8C`, coral `#D76B50`, purple `#6F5AA8`, gray `#849199`; the complete intervention is identified by a pale teal `#E5F2EF` row and the explicit label **CoReTrace (Ours)**.
- Exports: vector PDF and 300-dpi PNG. Every text element is checked against the fixed canvas before saving. Fonts are embedded TrueType.

## Figure-specific decisions

| Figure | Revised organization | Purpose |
|---|---|---|
| Composition diagnosis | Aligned horizontal composition stacks and readout points | Keeps the same three model rows while exposing the high failure frequency and recoverable addresses together. |
| Causal interventions | Three factorial line panels plus one horizontal paired-effect forest plot | Makes the access–reading interaction and the direction of address-specific controls easy to compare. |
| Reciprocal content exchange | Three model panels of edited-value and obsolete-answer points | Direct value labels and the highlighted complete intervention separate following edited facts from answer persistence. |
| Head localization | Three complete head maps with selected-cell outlines and one shared horizontal diverging scale | Maintains exact layer/head information and a common quantitative color scale. |
| Head necessity | Nine panels: query type by model; solid selected and dashed random controls | Separates previously overlapping curves and shows the selected operating count explicitly. |
| Component ablations | Three aligned point columns; baseline, tuning, and reader groups; final method last | Distinguishes complete repair from intermediate variants and annotates the total gain. |
| General capabilities | Nine panels: benchmark by model; four absolute-accuracy bars each | Shows all benchmark scores directly, including near-native results, restoration improvements, and full-tuning scores. Native-relative changes appear above each panel. |

## Validation

All 14 numerical CSV tables reproduce exactly the previous values after disregarding row order; the ablation rows are reordered for presentation. Every figure reads recorded experimental summaries. Confidence intervals and sample standard deviations retain their original definitions. The final seven PDFs contain embedded TrueType fonts and produce no Poppler font warnings. Figure canvas bounds pass for every visible text element. Full-size PNGs were reviewed visually, including corrected causal-panel margins and capability-row labels.

Detailed machine-readable checks are in `figure_revision_validation.json`.

## Final appendix layout adjustment

The ablation figure is 6.75 × 3.15 inches and the capability figure is 6.75 × 5.0 inches. Their original font sizes and horizontal dimensions are retained. All seven figures were regenerated together to keep the source manifest consistent. The two shortened figures were visually reviewed and pass text-bound validation.
