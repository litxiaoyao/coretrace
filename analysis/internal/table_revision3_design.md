# Table redesign from the supplied accepted-paper references

This is an internal working note. It is not manuscript content.

## Visual decisions

The two supplied table screenshots use Times text, black booktabs rules,
light-gray reference rows, pale-yellow selected/Ours rows, grouped column
headings, and true column maxima in bold. The manuscript uses the same
structure. Positive differences are blue and negative differences are red;
green is excluded at the user's request. The main document defines the
shared colors (`tableours=FFF0BE`, `tablebase=EEEEEE`, `gain=1F77B4`,
`loss=D62728`). Standard deviations remain at 80% black for legibility.

## Comparison structure

- Main contextual reasoning: Native, full fine-tuning, and CoReTrace;
  three model groups, each with composed and all-three accuracy.
- Main capability evaluation: a Native model row and a +CoReTrace row
  for each model, followed by the change from Native. Both improvements
  and regressions are displayed. Differences use unrounded source values.
- Complete core/capability/format/scoring/cost tables use the same genuine
  comparison methods. Internal components are not relabeled as published
  baselines.
- One component-ablation table represents all eight experimental settings
  through head adaptation, V/O restoration, evidence selection, and the
  candidate-ranking signal. Each configuration appears once, followed by
  composed EM for the three models, with recorded-run standard deviations.
  True maxima, including ties, are bold. The eight-row structure isolates
  each component's effect on the main dependent variable. First-hop,
  all-three, and capability-restoration effects are retained in the
  controlled-effect figure and adjoining discussion, including outcomes
  where a component exceeds the complete intervention. Complete baseline,
  full fine-tuning, and CoReTrace query metrics remain in the core results
  table.
- Candidate ambiguity, address readouts, and content exchange remain
  functional mechanism diagnostics with descriptive experimental conditions.
- Conditional composition and fixed-native-population recovery share one
  two-panel table. The first panel changes the constituent-correct population
  with the model state; the second holds the native population fixed.
- The full secondary-metric analysis JSON continues to retain head-adaptation
  outcomes, allowing the accompanying ablation discussion to report its
  positive results without placing the component in benchmark leaderboards.

There are no archived same-protocol results for a published external
intervention. The table redesign makes no state-of-the-art claim and adds
no external score.

## Validation

`analysis/build_tables.py` generates 18 table files from 94 source files.
The standalone table document compiled successfully, and the main tables,
component table, and merged recovery table were visually inspected.
At 9-point text and 4-point column separation, the single-column capability
table is 234.22 TeX points wide; its outer padding is removed to fit an ICML
column without scaling.

`table_revision3_numeric_check.json` records 153 independent source checks:
108 core mean/dispersion aggregates, 27 primary capability aggregates, and
18 fixed-population counts. All checks agree with the archived summaries.

The removed `fixed_population.tex` is replaced by panel (b) of
`conditional_composition.tex`; `component_ablation.tex` is newly generated.
The corresponding manuscript references and captions are maintained by the
prose revision.
