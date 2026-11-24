# Main-manuscript editorial and citation review

Internal review of `paper/main.tex`, `paper/related_work.tex`, and `paper/sections/{introduction,method,experiments,conclusion}.tex`, plus the generated main/diagnostic tables. This review does not edit the manuscript. The appendix was still being written, so pending appendix labels and details are not treated as missing final content. Bibliographic accuracy is documented separately in `reference_verification.md`.

## Overall assessment

The manuscript now has a coherent scientific progression: **a concrete same-context error → a conditioned composition gap → recoverable bridge address → an access/reading interaction → content following → evidence selection and scoped adaptation**. The strongest novelty is correctly concentrated in the factorized intervention and its connection to contextual evidence use. The text does not claim to invent correct-single-hop failures, generic attention routing, or targeted-head fine-tuning. Related Work accurately locates those predecessors.

One numerical statement should be corrected immediately. Two operational details should be stated explicitly in the main Method because they determine what information is available to the readout and what the factorial manipulation actually changes. The remaining improvements are mostly citation placement, terminology, and removal of repeated defensive prose. These edits should preserve the substantive limits on development overlap, deterministic recorded runs, diagnostic population and capability losses.

## Highest-priority corrections

| Priority | Location / current phrase | Finding | Direct action |
|---|---|---|---|
| Required | Experiments, “Repaired Answers…”, “improves edited-value following by 10--13 points” | Table values are 77−64=13, 76−66=10, and 80−72=8. | Change to **“by 13, 10, and 8 percentage points”** or “by 8--13 points.” |
| Required for clarity | Method, readout feature paragraph | It never explicitly says that the readout features come from a **composed-query** prefill. After the preceding direct/composed localization, readers could mistakenly infer direct-query features or a donor input. | Add “A composed-query prefill…” as proposed below. |
| Required for clarity | Method, “mean question position” | The feature is the **mean attention mass over question tokens**, not attention at an averaged token position. | Replace with “the question-token mean and the final-question-token attention mass.” |
| Required for intervention reproducibility | Method, donor description | Code captures the direct second-hop **last-question-token row**, then applies that conditional pattern to **all receiver question-token rows**. Exact context-token alignment does not specify those query-token choices. | State both choices in the main text; retain equations and exceptional rows in the appendix. |
| Citation placement | Introduction, first list of the three models | Model citations first appear only in Experimental Setup. Abstract citations may conventionally be omitted, but the first main-text model list should be cited. | Add Qwen and Llama report citations to that Introduction sentence. |
| Citation placement | Experimental Setup, first definition of official alias EM | The 2Wiki dataset has been cited, but the named official evaluator should have an explicit source at metric definition. | Cite `alab2020twikievaluation` here or place the official evaluator URL in the detailed protocol while citing Ho in the main sentence. |

### Replacement: native readout description

Replace the first two sentences of the readout paragraph with:

```latex
To test whether the address is recoverable from the composed query, we extract
paragraph features from a composed-query prefill. For each selected head, the
features contain the log of its question-token mean attention mass and its
final-question-token attention mass to that paragraph. The full readout adds
log paragraph-length fraction and a question/title-mention indicator.
```

The existing training-standardization, cross-entropy, regularization and state-matching sentences can then follow. This makes the probe's information boundary clear without another generic disclaimer.

### Replacement: donor definition and intervention positions

Replace the current donor sentence with:

```latex
For each selected head, $\rho^{\mathrm{dir}}$ is the bridge-normalized attention
at the final token of the direct second-hop question. We apply the chosen
factorization to every question-token attention row of the composed prefill;
donor and receiver contexts have exactly aligned tokens.
```

Evidence checked: `scripts/factorized_causal.py` constructs `NativeSourceConditionalDonor`, records “last-question-row source attention conditional only,” and passes `rows=receiver['question_positions']`. `coretrace/mechanisms/factorized_attention.py` captures the final question row and applies the stored conditional to the selected receiver rows. The unchanged V/O statement is important and should remain.

### Replacement: content result paragraph

```latex
Compared with scoped adaptation alone, the full repair improves edited-value
following by 13, 10, and 8 percentage points and reduces obsolete-answer
persistence. Selection is recomputed after the exchange, so this comparison
tests the complete procedure's response to changed evidence. Obsolete answers
still persist in 4--9\% of the final-repair cases.
```

This corrects the range, gives a concrete remaining failure, and replaces the broad statement that the experiment does not establish “universal factual consistency.” The discovery scope should remain explicit in the subsection/figure and methodological limitation.

## Narrative and claim calibration

### What already works

1. **Introduction begins with a scientific problem.** The Walter → James → Arsuf case is concrete and immediately intelligible. The next paragraph distinguishes supplied evidence from parametric recall. This follows the requested discovery-led narrative.
2. **The availability/use distinction is measured rather than asserted.** Native-state readout performance is reported specifically on native composition failures, with metadata controls. The text correctly separates decodability from endogenous use.
3. **The factorial result carries the explanation.** The Llama example presents all four cells and the change in the pattern-transfer effect; it does not hide the negative pattern-only result. Qwen3-8B's interval touching zero is explicitly acknowledged.
4. **The application has an interpretable contribution beyond tuning.** The 103-question ambiguity analysis isolates the readout under the same scoped model and fixed evidence budget. The checks confirm identical generated token IDs outside that subset, supporting the statement that all differences occur within it.
5. **Full evaluations preserve important adverse results.** First-hop losses and incomplete capability recovery remain in the main text. FullFT is correctly described as a fixed-recipe comparison.

### Claims to sharpen

**Abstract: “We trace this failure to a gap…”** can sound like an exhaustive explanation of all failures. The actual finding identifies a mechanism contributing to the tested phenomenon. Prefer:

```latex
We identify a gap between recoverable evidence location and effective evidence use:
```

**Abstract: “reciprocal fact exchanges test whether…”** describes an experiment without stating its positive result. This is a missed opportunity in the abstract. A concise replacement for the current factorization/content sentence is:

```latex
On a shared-context diagnostic, transferring a direct second-hop reading pattern
becomes more useful under calibrated paragraph access, with interaction estimates
of 5--16 percentage points. After reciprocal fact exchanges that preserve global
answer counts, repaired predictions follow the changed local values in
76--80\% of cases, compared with 26--35\% natively.
```

This reports point estimates rather than claiming that every interaction excludes zero. The main text already supplies population size, discovery overlap and intervals. If abstract length is tight, retain the interaction result and omit the content percentages rather than replacing the result with “we test.”

**Content subsection: “An improvement on this diagnostic must therefore depend on where the relevant value occurs.”** is stronger than the word-count control alone establishes. Fixed global counts rule out an explanation based solely on counts; they do not prove a unique algorithm or rule out every positional/structural heuristic. Prefer:

```latex
Reciprocal object exchanges preserve every answer surface and its frequency,
ruling out an explanation based solely on global answer occurrence.
We therefore compare whether answers track the changed value in the relevant
paragraph and whether they remain correct on both versions of the context.
```

The joint original/edited result is particularly useful because correct answers on the edited condition alone do not establish context sensitivity.

**Necessity paragraph:** severe target-hop loss shows that the selected heads are not exclusive to composition. The manuscript states this appropriately. To avoid attributing a narrowly defined operation from head knockout alone, the tightest wording is:

```latex
The selected heads contribute strongly to both constituent and composed answers.
Paragraph-address interventions below test whether their access allocation is
causally relevant to composition.
```

The existing interpretation is plausible; this is a precision improvement, not a rejection of the result.

**Mechanism-to-application link:** do not strengthen the current account to say that scoped adaptation specifically implements the transplanted $\rho$ or that Q/K updates alone explain the deployment gain. The adaptation updates Q/K/V/O and applies model-specific restoration. The factorial diagnostic and deployed repair are related functional tests, not identical interventions. Current Method mostly respects this distinction.

## Citation audit and first-use recommendations

| Item | Current status | Recommended placement / text |
|---|---|---|
| Composition gap | Correctly cited in Introduction and Related Work | In Method, describe CFR as the conditional compositionality gap rather than implying a newly invented metric. A second citation at the equation is optional but useful. |
| Qwen3 and Llama | Correct citations in Setup, late relative to first main-text mention | At Introduction's three-model list: `Qwen3-4B and Qwen3-8B \citep{yang2025qwen3}, and Llama-3.1-8B-Instruct \citep{grattafiori2024llama3}`. Define the shortened Llama name once if it remains in tables. Abstract can remain uncited. |
| 2WikiMultiHopQA | Correct first citation | Keep the distinction between original source data and the project's paired query protocol. |
| Official answer normalization / aliases | Dataset source cited earlier, metric source not explicit | `official normalized alias exact match \citep{alab2020twikievaluation}`; then define the additional end-of-generation condition. |
| Transformer attention | Correct citation at the first factorization formula | `vaswani2017attention` is sufficient; no need to cite every use of Q/K/V/O. |
| Activation interventions | No explicit foundational citation in Method | Add once: `We use controlled activation interventions \citep{meng2022locating,zhang2024patching} to separate the two operations.` This cites the methodology lineage, not our novel factorization. |
| AdamW for model adaptation | Optimizer is omitted in the main Setup | Short insertion: `Both adaptation recipes use AdamW \citep{loshchilov2019adamw}, one epoch, ...`. Retain weight-decay value in the appendix. |
| Adam for readout | Not named in the main text | Fine to cite only at its first appendix mention: `Adam \citep{kingma2015adam}`. Do not add optimizer detail to the main readout paragraph merely to use a citation. |
| HotpotQA, MMLU, GSM8K | Correctly cited at first main-text introduction | Current primary references are appropriate. Maintain explicit zero-shot/metric details; a benchmark citation does not make custom evaluation choices standard. |
| Sun ACL / Sun AAAI / BRH | Correct references and substantive comparison | Keep. These directly constrain our novelty claim. |
| Persona / emotional circuits | Not forced into Related Work | Correct decision. Their value here is narrative/methodological inspiration, not multi-hop task precedence. |

### Metric wording should be operationally exact

“The answer complete within 32 generated tokens” should specify what counts as completion. If EOS is the gate, state it directly:

```latex
We score a response as correct when it matches an official answer alias after
normalization and emits the model's end-of-turn token within 32 generated tokens.
```

Use “EOS token” instead if the actual permitted terminators are exactly the model EOS IDs. The appendix should list the implementation's accepted terminators. Simply generating a correct visible string in fewer than 32 tokens is not sufficient under this protocol, and the prose should not imply it is.

The proposed formal term **completed-answer EM** works once defined this way. Use it consistently for the gated metric; reserve **text EM/F1** for scores without that gate.

## Related Work: precision and compression

The current criticism of every cited paper is supported by the full readings. No task-irrelevant reference is needed. Three small edits improve exactness and flow.

### Biran: describe the actual existence criterion

Current “their back-patching rescue rate selects a successful layer pair retrospectively” is broadly accurate, but a rate itself does not select a pair. Prefer:

```latex
\citet{biran2024hopping} identify delayed bridge resolution; their rescue rate
counts whether any tested back-patching layer pair succeeds for each example,
without an inference-time rule for choosing that pair.
```

This preserves the direct limitation and avoids misdescribing their diagnostic as an implemented oracle selector.

### Sun ACL: specify query-to-demonstration matching

“Demonstration-to-label matching” is slightly ambiguous about what is matched to what. Prefer:

```latex
\citet{sun2025mappings} localize heads that match new queries to demonstration
labels and improve in-context classification by fine-tuning those heads.
```

### Remove repeated deployment detail from the end of Related Work

The final sentences about input-derived graphs, training-fitted readouts, annotation-free inference and V/O restoration are all explained again in Method. The scientific contrast can end more directly:

```latex
These interventions do not separate evidence-paragraph access from conditional
reading within that paragraph. We test this separation in contextual composition:
an address can remain decodable despite answer failure, and access calibration
changes the effect of transferring a relation-conditioned reading pattern.
\method\ uses the recoverable address signal for evidence selection and combines
it with scoped head adaptation.
```

The distinction remains strong; implementation detail no longer dilutes the comparison paragraph.

## Terminology cleanup

| Current variants | Recommended convention | Reason |
|---|---|---|
| direct-hop / direct-target / target-hop / direct second-hop | Define `first-hop question $q_1$` and `direct second-hop question $q_2$`; use `second-hop` for the latter thereafter | Avoids exposing internal `direct_target` terminology as if it names another experimental condition. |
| mean question position | question-token mean attention mass | An aggregate is not a position. |
| body / native body / scoped body | model / native model / scoped model | “Body” is an implementation label and adds no scientific distinction. |
| fixed projection restoration / scoped adaptation / native V/O restoration | Define scoped adaptation as selected-head tuning plus specified native V/O restoration; use that name consistently | Prevents readers from inferring three unrelated interventions. |
| independently mentioned root | unique root title explicitly mentioned in the question | More readable; specify exclusion of nested title matches in the appendix. |
| prefill | first mention: forward pass over the input, or `input prefill` with a short definition | Explain once outside the abstract. In the abstract, “extra input pass” is clearer. |
| same-prefill option probabilities | option probabilities from the same prompt | Describes the scientific control without implementation jargon. |
| parameterized knowledge | facts stored in model parameters / parametric knowledge | Standard and more direct. |
| CFR | conditional composition-failure rate / compositionality gap | CFR appears only at its definition; the acronym can be omitted without losing content. |

Suggested Q/K/V/O first expansion:

```latex
answer-only cross-entropy updates the full-rank query, key, value, and output
(Q/K/V/O) projection slices associated with the selected heads
```

## Defensive prose that can be removed or shortened

The manuscript's scientific limits are important. Repeating them after most positive findings makes the paper sound less confident and consumes space. Keep each consequential boundary in one clear place and use concrete adverse results elsewhere.

| Location | Current wording | Proposed replacement |
|---|---|---|
| Introduction opening | “This is an observed model response, not a missing-fact example…” | `All three questions are evaluated against the same ten evidence paragraphs (\cref{fig:teaser}).` The figure caption already identifies the real example. |
| Introduction contributions | “We report both gains and remaining losses, rather than treating task improvement as proof of universal capability preservation.” | Delete. Main constituent and retention subsections already report the losses quantitatively. |
| Figure 1 caption | “it does not assign them to exclusive consecutive layers” | `a functional distinction between recoverable location, access allocation, and relation-conditioned reading`. Retain the anatomical-identifiability limit once near the causal result. |
| Figure 2 caption | “Symbols depict operations, not measured head layouts.” | `Operations are shown schematically.` |
| Setup, capability paragraph | “rather than reproduce few-shot leaderboard scores” | `The same zero-shot protocols are applied to all compared model states.` This states the evaluation purpose positively. |
| Phenomenon paragraph | “not a comparison between unrelated easy and hard questions” | `The discrepancy is measured within each source under identical evidence.` |
| Ambiguity result | “not a changed model or a different evidence budget” | `The scoped model and two-paragraph evidence budget are held fixed.` |
| Retention opening | “reports full evaluation splits, including losses” | Start directly with the Llama GSM8K numbers; the table caption already says complete splits. |
| Retention ending | “without supporting a claim of lossless preservation” | `Scoped adaptation recovers much of the lost capability, while residual losses remain on several tasks.` Or omit after the explicit losses. |
| Cost ending | “prevent a universal latency claim” | `Observed latency also depends on the extra input pass and implementation overhead; detailed timing and token counts appear in ...` |

### Limitations that should remain explicit

- Formal train/discovery/test source IDs are disjoint, but the fixed evaluation panel can overlap preceding development. This materially limits claims of untouched generalization.
- The 25 diagnostic quadruplets overlap head/tau calibration; the factorial result is a discovery diagnostic.
- The Qwen3-8B interaction interval touches zero. Do not compress this into “all models show significant interaction.”
- Selected-head training is deterministic under the recorded recipe; run SDs do not estimate independent training randomness.
- Diagnostic mass/conditional interventions use annotated addresses and donors; the deployed selector does not.
- The scopes are fixed from development and not chosen by the present reported test comparison. The existing sentence should not be strengthened into a claim that development never touched overlapping sources.
- First-hop/all-three tradeoffs and residual capability losses are real main results.
- FullFT is a fixed-recipe comparator, and its GSM8K formatting failure limits interpretation of the zero score.

These should be concise factual statements, not removed in pursuit of a more positive tone.

## Optional compact Setup wording

If page pressure requires compression, the following preserves the most consequential information while moving implementation and replicate detail to the appendix:

```latex
\textbf{Models and data.} We evaluate Qwen3-4B, Qwen3-8B
\citep{yang2025qwen3}, and Llama-3.1-8B-Instruct
\citep{grattafiori2024llama3} with native chat templates, BF16 inference, and
greedy decoding; Qwen thinking is disabled. \dataset\ contains 100 discovery,
2,000 training, and 1,000 test sources from 2WikiMultiHopQA
\citep{ho2020constructing}, each with three queries over ten unchanged paragraphs.
Only composed queries train model weights. Formal splits have disjoint source IDs;
the fixed test panel can overlap preceding development.

\textbf{Evaluation.} Core accuracy is official-alias EM
\citep{alab2020twikievaluation} with an end-of-generation requirement within
32 tokens. We compare the native model, evidence selection, selected-head and
scoped adaptation, readout controls, and full fine-tuning. Both adaptation recipes
use AdamW \citep{loshchilov2019adamw} for one epoch at $2\!\times\!10^{-5}$
with eight-example accumulation; full fine-tuning uses a fixed recipe.
Recorded-run SDs are descriptive because selected-head optimization is deterministic.
Paired uncertainty resamples sources or diagnostic quadruplets.

\textbf{Capabilities.} We evaluate complete HotpotQA distractor validation
(7,405) \citep{yang2018hotpotqa}, MMLU test (14,042)
\citep{hendrycks2021mmlu}, and GSM8K test (1,319) \citep{cobbe2021gsm8k}
splits with zero-shot prompts. MMLU ranks option letters by their probabilities
from the same prompt; GSM8K checks a final numerical answer after at most
512 generated tokens. Construction, prompts, completion rules, optimization,
and recorded-run conventions appear in the appendix.
```

Use the original subsection cross-references instead of the final generic appendix sentence once the appendix is assembled. Do not copy “end-of-generation requirement” without the actual terminator definition somewhere in the protocol.

## Final consistency observations and checks

- Current model/head/readout sizes are internally consistent: selected heads 20/20/40 and full-reader weights 42/42/82. Do not reintroduce the earlier unverified 80-head Llama assumption.
- The native conditioned counts and failure percentages match the main results: 234/457, 236/462 and 243/501 failures.
- The all-test native address accuracies and failure-subset address accuracies match the readout table.
- The factorial cells imply the stated +8/+5/+16 point interactions; Qwen3-8B's interval has lower endpoint zero.
- The ambiguity population is 822 unique + 103 multiple + 75 inapplicable = 1,000. The saved subgroup check confirms generated-token identity for graph-first and final outside the 103 cases in every recorded run.
- Qwen3-8B GSM8K +0.83 and Llama HotpotQA −2.56 point changes are correct from unrounded values. Subtracting the displayed two-decimal table entries yields +0.84 and −2.57 respectively; this is harmless rounding, not a scientific discrepancy. One decimal in narrative would avoid apparent inconsistency if desired.
- The Main Results and Retention tables are both explicitly cited and interpreted. The five planned main figures are also referenced and their narrative roles are clear.
- Main tables display many `±0.0` SDs arising from repeated deterministic execution. An optional space/readability improvement is to report means in the main table, paired gain intervals in text, and full recorded-run dispersion in the appendix. The current descriptive SD presentation is transparent but should never be read as replicated training evidence.
- With five full-width figures and two full-width tables, final PDF placement should be checked carefully so the mechanism figure and first quantitative result do not drift behind later applications. This is a layout follow-up, not an instruction to remove the mechanistic evidence.
- The main file uses `icml2027`; confirm this remains the intentionally selected current official template. No template edit is proposed by this editorial review.

## Ready-to-merge minimum set

If only a few edits are made before the next compile, prioritize: **(1)** 8--13 point content gain; **(2)** composed-query readout features and correct mean-mass wording; **(3)** donor final-row / receiver all-question-row scope; **(4)** first-main-text model and metric citations; **(5)** one explicit completion-token definition; **(6)** remove the repeated “universal preservation/consistency” sentences while retaining the concrete limitations listed above.
