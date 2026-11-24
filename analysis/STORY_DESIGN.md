# Paper narrative and evidence allocation

## Central question

Why can a language model answer both constituent questions from the same context, yet fail when those questions are composed?

## Central finding

Evidence access shapes relation-conditioned reading. A bridge paragraph's address remains decodable in many failed compositions. Reallocating paragraph attention and substituting its normalized within-paragraph attention have interacting effects: a useful local reading pattern is not reliably useful at the native paragraph mass. This is a functional account, not a claim of three exclusive sequential neural stages.

## Evidence-led story

1. **Concrete phenomenon.** Preserve the complete ten-paragraph context and ask the two constituent questions and their original composition. Approximately half of sources whose native constituent answers are both correct still fail in composition. Figure 1 introduces a real example; Figure 4 quantifies the phenomenon.
2. **Localization and information availability.** Rank heads by the paired direct-target minus composed bridge-paragraph attention gap on 100 discovery sources. Test knockout shows these are evidence-access heads shared by constituent and composed questions. Train-only address readouts recover the bridge on 72.2%, 74.6%, and 86.0% of the respective native composition-failure subsets. This establishes information availability, not endogenous use.
3. **Mechanistic explanation.** Separate paragraph mass from the conditional attention distribution inside the bridge paragraph. The 2-by-2 intervention retains receiver values/output projections. Interaction estimates are +8, +5, and +16 percentage points, with the Qwen3-8B interval touching zero. Use within-experiment baselines. Figure 5 makes the interaction central. These are discovery diagnostics, not held-out causal generalization estimates.
4. **Content dependence.** Reciprocal same-relation object exchanges preserve whole-context word and character counts. Repaired predictions follow the relocated local values substantially more often. Figure 6 connects evidence selection to content-sensitive behavior under unchanged global word counts.
5. **Mechanism-derived intervention.** CoReTrace combines selected-head adaptation, fixed prefill projection restoration, and an input-only title graph with a training-fitted paragraph readout. Figure 3 explains the procedure; Figure 2 independently explains the diagnostic design. The readout matters exactly where title links are ambiguous: 103 of 1,000 test sources. Its same-body advantage over graph-first selection is concentrated in that subset. Original paragraphs are passed to the model; no donor or support annotations enter inference.
6. **Practical effect and limits.** Composed EM rises from 26.9/29.2/36.4 to 66.8/67.2/69.7. Report constituent and capability tradeoffs, including Llama and Qwen4 declines. Full fine-tuning under the fixed answer-only recipe is a comparator, not the novelty claim or a universal baseline upper bound.

## Main text allocation

- Introduction: question, surprising address/use gap, access–reading interaction, repair, three contributions.
- Related Work: precise task and intervention gaps in latent-composition, contextual-recognition, and circuit-guided work. No claim that prior work lacked any causal interventions or head tuning.
- Method: paired contextual triplets; localized paragraph features; factorized and reciprocal probes; deployable CoReTrace.
- Experiments: concise setup; failure/address availability; causal factorization; reciprocal content use; repair, ambiguous selection, capability tradeoffs.
- Conclusion: functional mechanism and its actionable consequence, with scope stated plainly.

Main figures: generated portrait teaser (1), generated causal diagnostic overview (2), generated deployment overview (3), failure/address diagnosis (4), access/reading interventions (5), reciprocal content use (6). The three conceptual figures retain the original distinct roles: phenomenon, causal diagnosis, and application. Main tables: main composition results and full-split capability retention. Every main figure must be explained where it appears.

## Appendix allocation

Data reconstruction and selection history; exact prompts and scoring; model/head/restore settings; training and reader details; complete per-query and per-run results; head localization heatmaps; knockout curves and overlaps; reader feature controls; full factorial contrasts; reciprocal-pair diagnostics; input-graph subgroups; parameter/token/prefill costs; exact worked examples. Appendix figures/tables have A-prefixed independent numbering.

## Interpretation constraints

- A fixed attention-mass target can raise or lower an individual row: call it calibration/reallocation.
- Heads are not composition-exclusive; single-hop knockout damage is substantial.
- A linear probe establishes recoverability, not use by the unmodified model.
- Conditional-pattern donor transfer is privileged diagnosis, not a deployable method.
- Discovery/factorization/content panels overlap by design; no held-out causal-generalization claim.
- Source IDs are disjoint across formal splits; the fixed test panel may overlap preceding development, and entities can connect training/test sources.
- Selected-head runs with seed labels 42/43/44 have identical optimization traces. Descriptive run SD is not independent training-seed uncertainty. Batch-size variation explains small recorded evaluation differences.
- No claim of lossless general-capability or constituent preservation.
- The original archive omits model support modules; this is an internal reproducibility issue reported separately from the scientific manuscript.

## New positive results recovered in this analysis

Native failure-subset address decoding; ambiguous-candidate bridge-selection and answer improvements; the fact that all readout-versus-graph-first answer differences lie in the ambiguous subset; identical composed accuracy for full and attention-only deployed readers; fixed-native-population rescue/loss counts. These complement, rather than replace, the complete result distribution.
