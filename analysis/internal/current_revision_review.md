# Independent review of the rewritten main text

**Resolution:** All three corrections below were incorporated before the final PDF build. This file preserves the independent review findings; final layout acceptance is recorded in `current_pdf_qa.json`.

Reviewed 2026-11-24 against the raw-record audit of commit `cf00035eb9b71bebf3ae88f76caf30ee9b58065c`. Scope: `main.tex`, introduction, method, experiments, conclusion, related work, captions, and the three main summary tables. This review makes no manuscript edits.

## Overall assessment

The revised title, abstract, introduction, diagnostic framework, experiments, and conclusion now follow one coherent evidence chain. The title **When Correct Hops Fail to Compose: Diagnosing Evidence Access and Local Reading** accurately describes the contribution. The discovery is recoverable bridge-address information during failed composition; the diagnosis is the access-by-local-pattern interaction; the practical validation combines component comparisons, ambiguity resolution, and sensitivity to local fact changes.

The rewrite correctly makes the factorial result the diagnostic hinge and keeps the reciprocal exchange assay at the level of complete-procedure behavior. It describes the selected heads as shared evidence-use components, avoiding an exclusive-circuit interpretation. Native/adapted readout states, training-label use, annotated diagnostic addresses, recorded-run uncertainty, and the separate 100-receiver/1,000-source populations are clear.

Every numerical value in the reviewed main text matches the independently reaggregated source records, including percentages, interaction intervals, parameter counts, ambiguity gains, and fixed-native-population repair/retention. The title is justified by the actual experiments and does not introduce an unsupported mechanism name.

## Corrections to make before final compilation

### 1. Clarify the component table's final transition

The caption of `tab:main_components` says that rows cumulatively enable each operation. The final row replaces input-order candidate ranking with the full readout; it does not add readout ranking while retaining input-order ranking. Suggested caption wording:

> Composed EM (%). Rows add restoration and evidence selection; the final row replaces input-order ranking with the full attention-based reader. Complete component results and dispersion appear in the appendix.

The sequential configuration values themselves are correct. Restoration and input-order selection have model-dependent effects, so the current neutral prose describing the values is preferable to claiming a monotonic gain at each step.

### 2. Complete the concise capability profile

The main paragraph reports Qwen3-8B's +0.83-point GSM8K change but omits Qwen3-4B's -2.35-point change. It already points to full appendix outcomes, so no broad retention claim is false. For a balanced single-pass profile, add that omitted value once, for example:

> Qwen GSM8K changes by -2.35/+0.83 points, and Qwen MMLU by -0.17/-0.22 points.

This keeps all benchmark changes in one compact paragraph, without expanding the negative-result discussion.

### 3. Align the Related Work intervention wording

The Method section correctly says that the receiving forward pass supplies value vectors, uses original output-projection weights, and allows downstream states to evolve. Related Work still says “retaining receiver value and output computations.” This is understandable but less precise. Replace that clause with:

> using receiver-computed values and the original output-projection weights

The actual intervention transfers only normalized attention distributions. Earlier interventions can alter values at later layers; keeping the wording uniform avoids implying identical value tensors across arms.

## Points that are already handled correctly

- **Abstract:** positive interaction estimates are reported with their 25-quadruplet scope; the prose does not claim significance for every model. Qwen3-8B's interval touches zero and is displayed in the main figure caption and text.
- **Readout:** the full-reader 72.2–86.0% range is complemented by attention-only 64.5–84.4%; metadata contribution is transparent. “Recoverable” and “decodable” are appropriate for the trained attention-feature probe.
- **Head localization:** knockout is described as contribution to answering and shared evidence use. Strong constituent effects are included, which correctly limits any composition-exclusive interpretation.
- **Causal design:** direct-query normalized patterns, discovery-fitted mass targets, question-row replacement, and receiver-side value/output computation are distinguished. A separate 1,000-source address control supports specificity.
- **Repair:** the native-model evidence-selection baseline is visible in the main table, and the component table exposes selected-head adaptation, restoration, and candidate ranking. The text credits both context selection and adapted computation.
- **Ambiguity:** the 103-case population is fixed by the input graph; the remaining 897 predictions are exactly identical between the compared policies. Full-reader bridge counts are unchanged across recorded runs, so the displayed run means are accurate.
- **Content assay:** word/character invariance is explicitly before selection, and the selector reruns on the edited input. Joint original/edited correctness is visible in both caption and text. The conclusion presents this as complete-system evidence sensitivity, without identifying mediation through the factorial interaction.
- **Efficiency:** the reduction is correctly limited to answer-generation input tokens, with the extra readout pass disclosed separately.
- **Statistical scope:** the paper says “three recorded runs,” identifies deterministic selected-head optimization, and directs sampling uncertainty to source/quadruplet bootstrap intervals.
- **Related Work tone:** contributions are described positively and the distinctions serve the diagnostic story; the draft no longer relies on a list of dismissive limitations of prior papers.

## Appendix and delivery follow-through

The planned appendix scope/reproducibility section should retain development-source reuse, the 43 test sources connected to training entity groups, the single random knockout set per dose, full constituent/capability outcomes, and exact prompt/score definitions. State these once in their natural protocol locations.

The missing `coretrace/models/` implementation remains a release limitation, not a numerical contradiction. Head counts/maps and parameter metadata are verified; exact GQA slice masks and native-projection restoration internals cannot be independently inspected in the current checkout. Keep the release limitation visible in the delivery and reproducibility notes without claiming new training or end-to-end rerun validation.

No additional experiments or user clarification are needed to complete this evidence-grounded revision. Final acceptance of the typesetting still requires inspection of the compiled PDF after all appendix additions and float changes.
