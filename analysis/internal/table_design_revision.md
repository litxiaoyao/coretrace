# Table design revision

## Reference pages visually inspected

The revision was based on rendered page images, including all table typography,
row grouping, color, numeric emphasis, and caption placement on these pages:

- *Bridging the Language Gap* (AAAI 2026), pages 5–6: an italic named method
  section separates mechanistically informed head tuning from baseline/full
  fine-tuning; bold column maxima; compact colored improvement values.
- *Tracing the Persona Circuit* (ICML 2026), page 9: light-gray baseline row,
  highlighted chosen setting, grouped metric headers, thin horizontal rules.
- Emotion intervention paper (ICML 2026), page 8: highlighted final method,
  method-group headings, separate accuracy and capability tables, colored deltas.
- *Interpret and Improve In-Context Learning via the Lens of Input-Label
  Mappings* (ACL 2025), page 8: grouped task/model headers, parameter and
  capability comparisons, clear bold best results and compact ablation tables.

## Applied conventions

All generated tables now use consistent Times-compatible manuscript type,
booktabs rules, bold headers, compact 1.08 row spacing, aligned numeric columns,
and two levels of value emphasis. Means remain black; recorded-run SDs are a
lighter gray at the same type size. Native rows use a light-gray background.
The complete method is explicitly named `CoReTrace (Ours)` and highlighted in
restrained pale teal. Actual column maxima are bold, including cases in which
an ablation or Native exceeds the complete method. The readout table instead
bolds the best feature variant within each model state and evaluation population.

The main performance table groups standard comparisons first, then
mechanistically informed adaptation. The complete method appears last, followed
by a compact signed percentage-point gain over Native. The capability table
uses the same order and includes the complete method's signed gain over head
tuning. Its nine gains are computed from unrounded underlying means, including
the 31.92-point Llama GSM8K restoration result. These rows use teal for positive
values and coral for negative values; no outcome is suppressed by the styling.

## Added result coverage

- `fixed_population.tex`: all eight archived intervention variants on each
  fixed native-constituent-correct population, showing failed compositions
  repaired, native composed successes retained, and total composed accuracy.
- `conditional_composition.tex`: all nine core variants, with each method's
  constituent-correct population size, composition-failure count, and conditional
  failure rate. Both denominators and failures are averaged across the same
  recorded runs as the rate; the native row is a single reference.
- `secondary_qa_metrics.tex`: HotpotQA text EM, text F1, and completion;
  GSM8K format validity and completion, for Native/full fine-tuning/head tuning/
  the complete method across all three models.
- `mmlu_generation_metrics.tex`: generated-letter micro and macro accuracy,
  format validity, completion, and option-score macro accuracy for the same
  four model states and all three models.
- `scoring_diagnostics.tex`: expanded from three to all nine core method
  variants, retaining completed EM, text EM, text F1, and EOS completion.

Every generated value is read from experiment summaries or the previously
verified fixed-population report. The source manifest now records 94 input
files. Secondary capability aggregates are also exported in
`analysis/figure_data/secondary_capabilities.json`.

## Validation

All 18 generated tables were compiled independently using the manuscript's
Times family and a 6.7-inch text block, with no overfull boxes or LaTeX errors.
Rendered main tables, full core results, readout results, content outcomes,
efficiency results, fixed-population results, conditional composition, and both secondary capability
tables were inspected visually for clipping, line rules, numeric legibility,
color hierarchy, and consistent spacing. Main manuscript float placement and
page balance are handled by the final integrated PDF review.
