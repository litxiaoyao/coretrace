# V3 scientific consistency review

Reviewed the current abstract, introduction, method, experiments, conclusion,
and appendix on 2026-11-25 against `v3_structure_evidence.json`,
`v3_causal_evidence.json`, the original figure-data CSVs, and the derivation
code. The current text passes the checks below.

## Structure and functional profiles

- Selected/direct overlap is 14/14/31 and selected/composed overlap is 0/1/10,
  for sets of 20/20/40 heads. These agree with the original intersection CSV.
- The reported discovery root/bridge ranges and 98/94/89 preference-switch
  counts agree with the 100 paired canonical sources. Measurements average
  question-token paragraph mass within each head, then the fixed head set
  within a source, then sources. Paragraph masses use the complete attention
  row as denominator.
- Random profiles reuse the exact layer-matched knockout sets. The individual
  profiles use real zero-based head IDs and original paragraph positions.
- The main caption and appendix correctly distinguish an individual displayed
  head from mass calibration applied to the entire selected set.
- Selected-head knockout yields composed EM 7.4/5.5/6.4 and direct-target EM
  1.1/1.0/6.5, matching the recorded necessity results.

## Matched location and routing

- The fixed group requires correct native constituents, an incorrect composed
  answer under the access experiment's own baseline, and a correct frozen full
  address-reader prediction. Its sizes are 169/174/209.
- Bridge/root/other corrections are 31/27/97, 12/10/12, and 7/2/7. The bridge
  rates round to 18.3/15.5/46.4 percent.
- Native root/bridge masses within those exact groups are 30.30/8.24,
  32.46/8.80, and 26.35/7.65 percent. Root exceeds bridge on 167/169,
  174/174, and 204/209 sources. The code averages raw masses before any
  logarithmic feature transformation.
- The appendix correctly explains the Qwen3-8B difference between 176
  principal-evaluation readout-correct failures and 174 matched routing
  failures. Discovery profiles, canonical test routing, and shared-context
  discovery quadruplets remain separately labeled.

## Routing and local reading

- Four-arm accuracies, interaction estimates, and intervals match the original
  results; the Qwen3-8B interaction interval retains its zero endpoint.
- Both corrects 11/13/29 native errors; 4/5/13 are joint-only corrections.
  Their shares round to the reported 36–45 percent range. Appendix correctness
  cells sum to the stated native-error/Both-correct populations.
- Receiver-computed values, original output-projection weights, fixed donor
  patterns, and subsequent forward propagation are described consistently.
  The revised routing conclusion uses “mass recalibration alone” rather than
  implying every downstream attention distribution is frozen to its native
  value.
- Locate–Route–Read remains a functional account. The manuscript does not
  assign separate head classes or early/middle/late layer stages to the three
  operations. Corvinus and Angela remain recorded appendix examples, with
  diagnostic Both and complete CoReTrace fact-exchange outputs distinguished.

No remaining factual correction was identified in this text review. No TeX,
plotting code, or original result data were changed by the review.
