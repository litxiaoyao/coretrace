# Scientific review of the appendix

Internal author-facing record only. Reviewed `paper/sections/appendix.tex`,
`paper/sections/appendix_protocol.tex`, every generated appendix table, the four
appendix figure PNGs, the corresponding plotting/table code, and the original
scientific implementation and result files. No paper file was edited by this
reviewer. Review date: 2026-11-24.

## Overall result

The appendix's numerical results match the archived evidence. Dataset counts,
relation counts, head-count selection, random-set overlap, factorial contrasts,
reader diagnostics, ambiguity results, complete triplet outcomes, capability
scores, and reported workload counts are correct. The principal scientific
corrections found during this review have already been communicated and most
are now present in the paper.

Two substantive initial errors were identified: the eleven discovery exceptions
were not all subject/title mismatches, and the ablation figure caption described
outcomes absent from that figure. Both have been corrected in the current
appendix. The batch paragraph now also distinguishes FullFT from selected-head
evaluation.

## 1. Corrections identified and their current status

### A1. Eleven discovery exceptions comprise two kinds — corrected

The original appendix said that all eleven had subject/title mismatches. I
independently re-ran the literal checks on every edge of all 3,100 sources.
There are ten discovery first-edge subject/title surface mismatches, plus one
discovery second-edge object-surface mismatch:

- Source `fc6058660bdc11eba7f7acde48001122` has subject and paragraph title
  `Nusrat Fateh Ali Khan`, which match.
- Its annotated object is `Pakistan`; the official supporting sentence says
  "Pakistani vocalist and musician". The strict whole-object helper does not
  treat `Pakistan` as a word inside `Pakistani`.
- The original generic `chain_validation` flag incorrectly labels the cause
  as a subject/title mismatch. Its support-index resolution itself uses the
  correct original official sentence.

The current appendix correctly states ten subject/title mismatches and one
demonym case. The audit implementation and earlier internal report were updated
to distinguish the causes. Evidence is saved in
`analysis/internal/discovery_annotation_exceptions.json` and reproduced by
`dataset_and_graph()` in `analysis/audit_experiments.py`.

Small accompanying improvement: the opening eligibility paragraph should say
"The standard chain filter requires ..." rather than implying that every
discovery source passes the strict literal filter. The later explicit exception
paragraph already makes the intended scope understandable.

### A2. Ablation figure shows composition only — corrected

The original caption claimed composition, both constituents, and all-three
accuracy. `make_ablation()` and the actual figure contain only composed accuracy
for the three models. The complete constituent and joint results are in the
table. The current caption and introductory sentence now say composition only,
which matches the figure.

The parent also identified that evidence-filtering values should average all
three recorded evaluations, despite sharing a native model and reader. Ensure
the final plotting helper uses all three runs for `native_text`, and only a
single run for `native`. This correction is present in the current helper.
Expected composed values are:

| Model | Evidence-filtering mean | Sample SD |
|---|---:|---:|
| Qwen3-4B | 47.2333% | 0.11547 pp |
| Qwen3-8B | 48.1000% | 0 pp |
| Llama-3.1-8B | 53.4333% | 0.05774 pp |

### A3. Batch settings require method-family scope — corrected

I checked the manifest configurations and actual GSM8K prediction records.
The following table applies to the native/selected-head evaluation series:

| Model | Core/Hotpot runs 42,43,44 | MMLU runs 42,43,44 | GSM8K runs 42,43,44 |
|---|---|---|---|
| Qwen3-4B | 1,4,4 | 4,4,4 | 1,1,4 |
| Qwen3-8B | 4,4,4 | 4,4,4 | 4,4,4 |
| Llama-3.1-8B | 1,4,4 | 4,4,4 | 1,1,1 |

All FullFT evaluations use batch size 4. For 1,319-example GSM8K, each
batch-4 method has 1,316 rows from full batches and three rows from the final
batch of size 3. Single-example API records have no `batch_size` field. There
is no indication that runtime behavior overrides the recorded configuration.

The current protocol now explicitly scopes these settings and adds the
FullFT distinction. Qwen3-8B's 29.2% versus 28.9% native references are correctly
kept separate.

### A4. Knockout does not by itself identify the removed function — corrected

The original appendix inferred "evidence access shared across query types"
from knockout alone. The current sentence instead says the heads contribute
causally across query types. This is the appropriate conclusion. Paragraph-mass
interventions separately provide evidence about access allocation.

### A5. Donor-answer-representation sentence — corrected

During this review, the current main experiments text still contained:

> Donors supply only normalized attention patterns, so the effect cannot be
> attributed to inserting their answer representations.

This was reported again to the parent. Attention weights may themselves encode
answer-location information, even when no hidden states or values are copied.
The precise replacement, now present in the main text, is:

> Donors supply only normalized attention weights, reweighting receiver values
> without copying donor hidden states or value vectors.

The appendix's own receiver-V/O and downstream-causal-effect explanation is
correct and already avoids this overstatement.

## 2. Exact data and graph checks

All of the following agree with the released corpus and independent rebuilding:

- Discovery: 100 sources, 300 queries, 50 distinct roots, 50 bridges, 50 groups;
  official origin 77 train and 23 development.
- Training: 2,000 sources, 6,000 queries, 1,949 distinct roots, 1,558 bridges,
  1,543 groups; all originate in official training.
- Test: 1,000 sources, 3,000 queries, 1,000 distinct roots, bridges and groups;
  all originate in official development.
- Forty-three test sources share a global root/bridge group with training.
  Split-level and global-group counts happen to agree within each split here.
- Every canonical source has ten paragraphs. Source identifiers are disjoint
  across splits. Standard eligibility, official alias joins and the seven
  direct-question templates match the available builder.
- Training first-edge director count is 1,154, test is 280; father counts are
  199 and 333, respectively.
- The historical selection description (1,001-source test pool; 32 initial
  quadruplets; 868 retained and 1,132 added training sources; 4,096-token rule
  for added candidates) matches the original builder README. The released
  builder restores the fixed selection rather than redoing that historical
  pool construction, which the appendix states accurately.
- All 25 quadruplets have ten shared paragraphs and four distinct endpoint
  entity IDs. Their endpoint alias sets are disjoint in the actual released
  data, though the original code does not assume disjointness universally.
  The 250-prompt total is 25 times (four composed, four target-hop, two first-hop
  prompts); there are 100 composed receivers and 100 three-query links.
- The input graph has 75 inapplicable/no-candidate cases, 822 unique-candidate
  cases and 103 ambiguous cases. The latter have candidate counts 2/3/4 on
  86/16/1 cases. The correct bridge appears among candidates in 918 cases,
  and unique-candidate choice is correct on 817/822.
- Full/attention/metadata bridge-choice counts on the ambiguous set are
  95/94/57, 96/97/57 and 98/97/59. Graph-first is 37 for every model. The full
  and attention methods have identical composed-EM totals, not necessarily
  identical choices or answers. The full repair and graph-first generated IDs
  agree exactly on all other 897 cases in every run.

One small graph wording refinement would improve reproducibility. The code
deduplicates title indices, so applicability means exactly one **distinct
maximally matched title**, not exactly one textual occurrence. Repeating the
same title in a question does not make the graph inapplicable.

## 3. Reciprocal-swap invariants and their meaning

All 100 swaps change the input, preserve raw character and word bags, and have
disjoint old/new normalized answer aliases. Paragraph order, titles and question
remain unchanged. The code identifies one literal official object alias in
each uniquely located support sentence. The complete input, not necessarily
the selector's output, has the stated bag invariant.

I additionally counted answer aliases in two ways. Literal whole-word alias
counts after Unicode/case/whitespace normalization are unchanged on all 100
inputs. If the *answer scorer's punctuation-deleting normalization* is applied
to whole contexts before counting, four inputs have different apparent phrase
counts: `British/American` loses a word boundary, and `Raj Kapoor's` becomes
`raj kapoors`. This is a distinction between normalization conventions, not a
failure of the input intervention. The initially raised frequency concern
was narrowed after this additional check. There is no need to discuss it in
the manuscript. The current wording "word and character counts unchanged"
states the construction invariant precisely and avoids ambiguity.

Checks are saved in `data_and_derived_views_validation.json`. The current
bag-of-words interpretation is appropriate: high paired original/edited joint
accuracy requires sensitivity to organization beyond an unordered bag. It
does not identify semantic content in the factorized attention donor.

## 4. Localization, interventions and numerical tables

The discovery calibration table is correct:

| Model | Native | Top 20 | Top 40 | Top 80 | Selected |
|---|---:|---:|---:|---:|---:|
| Qwen3-4B | 35 | 36 | 36 | 33 | 20 |
| Qwen3-8B | 45 | 47 | 47 | 45 | 20 |
| Llama-3.1-8B | 45 | 64 | 66 | 58 | 40 |

The random-control seeds are exactly `42 + count`, giving 62/82/122. The random
overlaps are 3/7/13, 0/4/15 and 3/8/21. Sets match the selected per-layer head
counts and allow overlap. The chosen-dose composed scores 7.4/5.5/6.4% and
24.4/27.3/29.4% match the necessity summaries.

The attention equations match the implementation. The donor is captured at
the final direct-query stem token and copied across all receiver question rows.
Context token-prefix and bridge-key alignment are checked. The code retains
receiver values, transfers only attention weights, evaluates the transformation
in FP32 and casts to the native dtype. The factorized implementation rejects
nonfinite, negative and degenerate conditional cases; the actual access and
factorial archives report zero invalid rows. Identity is exact for all
3 models times 100 receivers. Later activations can change through the normal
forward computation, as correctly stated.

For complete precision, "length-matched other paragraph" is the **nearest
token-length** paragraph excluding root and bridge, not necessarily an exact
length match. Ties are broken by title and then original index. A concise
appendix sentence can state this rule without adding an experiment.

The following generated tables were checked against their input data and
independent audit outputs and contain no numerical discrepancy:

- `readout_diagnostics.tex`, including scoped-state accuracies on native
  failure cohorts;
- `factorial_contrasts.tex`, all five contrasts and quadruplet intervals;
- `content_outcomes.tex`, all original, edited, persistence and joint values;
- `ambiguous_selection.tex`;
- `complete_core.tex` and `per_run_core.tex`;
- `capability_full.tex` and `scoring_diagnostics.tex`;
- `parameters.tex`, `paired_effects.tex`, `inference_costs.tex`, and
  `training_costs.tex`.

The Figure 4 bridge-control intervals agree with the fresh run-aligned
bootstrap table where they overlap. Repair comparisons correctly average each
source over the three runs before resampling; the actual test groups are
singletons. The 25-quadruplet factorial resampling unit is correct.

All-three accuracy, failure-set rescue counts 189/234, 191/236, 189/243, and
regression counts 12/223, 16/226, 14/258 refer to the specified populations and
run 42. FullFT's nine complete GSM8K runs indeed have 1,319 format failures and
zero scores each. Its source order is genuinely seed-dependent SHA order,
unlike selected-head adaptation's fixed ordering. The protocol distinguishes
these recipes correctly.

## 5. Reader, scoring and execution details

The reader protocol is accurate: per-head log mean and last-question masses,
floor `1e-8`, full-prompt length denominator, population standardization with
floor `1e-4`, zero-initialized bias-free weights, 500 full-batch Adam steps,
learning rate .03 and L2 penalty .01. The intercept-cancellation explanation
is correct.

One implementation detail is worth adding if complete reader reproducibility
is desired: the metadata title indicator is a normalized substring test for
Qwen and a whole normalized word-sequence test for Llama. The graph itself uses
whole-word sequences for all models. The present generic wording is not false,
but these should not be described as a single identical matching procedure.

**Suggested addition:**

> The title indicator uses normalized substring inclusion for Qwen and whole
> normalized word-sequence matching for Llama, following the recorded native
> tokenization geometry; the input title graph uses whole-word matching in all
> models.

QA EOS-gated exact match, token F1, MMLU micro-averaged same-prefill label-token
probabilities, and GSM8K final-line numerical equality all match the code.
GSM8K correctly does not require EOS for a valid final number. The supplementary
scoring table now supplies the promised numerical diagnostics. The alias
containment sensitivity percentages 48.1/49.1/47.3 are correct and retain the
original constituent-correct denominators.

The total 190 reader prefills decompose as 103 composed, 85 direct first-hop,
and 2 direct second-hop queries for each model. The 42.5/42.4/43.7% answer-input
token ratios are composed-only run-42 ratios. The efficiency text correctly
distinguishes these from the full 3,000-query workload and excludes additional
reader prefills from the answer-generation input totals. It makes no unsupported
overall speedup or total-compute claim.

## 6. Worked examples and figures

Walter/James/Arsuf is verified directly from the corpus, questions, and native
and final Llama predictions. The appendix correctly avoids claiming that all
constituents remain correct after repair; the final first-hop answer in this
example is actually wrong.

John Corvinus/Matthias Corvinus/John Hunyadi is verified across all three models
and all three final runs. There are two input candidates, and the full selector
does perform its extra attention prefill. Graph-first also answers this example
correctly and chooses the same bridge. Therefore it illustrates a composed
repair with an ambiguous input graph, but is not an example of an incremental
readout advantage over graph-first. The current wording merely says it
exercises disambiguation, which is accurate.

All four appendix figures were visually inspected:

- Localization maps show the full layer/head arrays and the 20/20/40 selected
  cells with zero-based indices; the caption matches.
- Necessity plots show composed, first-hop and target-hop curves, selected and
  random sets, and the native value at dose zero; the caption matches.
- Ablation is a three-model composed-accuracy point plot; the corrected caption
  matches. Small selected-head SDs can be visually hidden by the markers.
- Capability plots show model-specific differences from Native on each full
  benchmark split, with recorded-run SD. The baseline and formatting-failure
  interpretation are correct.

Minor caption consistency improvement: native and mass-calibration rows in
the content table are deterministic references shown without a printed SD;
adapted rows are displayed as mean plus/minus SD. All three underlying content
runs coincide, so the numerical interpretation is already correct.

## 7. Remaining verification boundary

All supplied prose assertions can be checked against the visible scientific
code, original result files, or explicit historical selection documentation.
The missing `coretrace/models/` package still prevents inspection of the actual
GQA slice implementation and restoration hooks. Scope tables accurately report
the saved configuration; this review does not claim to have re-executed those
missing internals. The delivery disclosure in the main scientific-review file
remains necessary. No manuscript audit log or invented replacement code is
needed to report the recorded experiment honestly.
