# Final scientific consistency review of the revised manuscript

Reviewed the compiled manuscript and revised figures on 2026-11-24 while final
pagination was being adjusted. Scientific source values were stable during review.

## Checks completed

- Read all main-text claims and the expanded appendix results in the compiled PDF.
- Viewed both regenerated conceptual figures and checked example chains,
  preparation/inference separation, Q/K/V/O training, projection restoration,
  graph branches, and readout flow against the manuscript method.
- Independently compared every native-conditioned summary row for three models,
  three recorded runs, and all stored component methods with the fixed-population
  analysis used by the new recovery table. Repaired failures, lost successes, and
  fixed-population correct counts all match the original summaries.
- Independently recomputed all 120 scalar means underlying the two new secondary
  capability tables from original HotpotQA, MMLU, and GSM8K summary files. Every
  value matches the table-data JSON to numerical precision.
- Checked the generated-letter MMLU evaluator: a valid generated response is one
  stripped A/B/C/D character with EOS completion. The manuscript states this in
  the MMLU secondary-table caption. Primary MMLU remains same-prefill option-token
  probability accuracy; no claim conflates the two metrics.
- Confirmed composed completed-answer EM equals unconstrained text EM for every
  archived method/run, validating the appendix scoring statement after expansion
  of its table to all nine variants.
- Checked gains, numerator/denominator definitions, run averages, causal-arm values,
  interaction intervals, native baseline differences, and appendix cross-references.

## Corrections made during review

1. Conditional failure-table caption now explicitly says that the ratio is
   computed within each run before averaging. Displayed counts are run means;
   the rates show mean and sample SD. This explains cases where dividing the
   two displayed mean counts differs from the mean rate.
2. Main text uses “second-hop accuracy”; table generation was asked to replace
   “Target hop” with “Second hop” for consistent q2 terminology.

No remaining scientific or numeric correction was identified. Final pagination,
figure sharpness, and typography are handled by the parent agent's visual review.
