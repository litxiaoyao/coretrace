# Evidence-supported expansion for an eight-page main text

The current main text is numerically sound but compresses the experimental reasoning into short transitions. The strongest use of additional space is to explain what each comparison resolves and how the diagnostic signal becomes operational. The five insertions below add approximately 455 words without adding an experiment or changing a reported result. They are ordered by manuscript location; all numbers and design details were covered by the completed raw-record audit.

## 1. Explain why the paired protocol is informative

**Location:** `sections/method.tex`, Section 3.1, after the first paragraph ending “All three queries share the original evidence,” before the correctness notation.

```latex
The paired queries distinguish access to each fact from their use in a composed answer. The first probe asks for the bridge specified by the root fact; the second makes that bridge explicit and asks for the requested relation value. Their shared context preserves the supporting sentences, distractors, and paragraph positions. Conditioning on successful constituent answers therefore identifies examples on which the individual facts are behaviorally accessible. This population motivates the diagnosis: we examine how the composed query changes evidence use when both ingredients already support correct direct answers.
```

**Purpose:** Establish the rationale for the paired construction before introducing the conditional metric. This develops the problem setup without re-stating the headline failure percentages.

## 2. Give the four arms an interpretable causal role

**Location:** `sections/method.tex`, Section 3.3, after the paragraph containing the exact-transformation appendix pointer, before “Twenty-five discovery quadruplets…”.

```latex
Each arm answers a distinct question about the paragraph contribution in \cref{eq:contribution}. Mass calibration preserves the receiver's relative allocation within the bridge and tests the effect of giving that evidence a different share of the row. Pattern transfer preserves the bridge mass and changes the mixture of local value vectors. Their combination tests the transferred pattern at the calibrated access level. Because the same receiver questions enter every arm, the interaction compares the pattern's usefulness at two access settings on an identical population. This makes the dependence between the two factors directly measurable.
```

**Purpose:** Help readers interpret the factorial design, especially the meaning of positive interaction. “Preserves” here refers to the attention-row transformation at the receiving head, consistent with the immediately preceding paragraph that allows downstream states to evolve.

## 3. Explain why the localization controls are matched

**Location:** `sections/experiments.tex`, Section 4.2, after the paragraph ending with the localization/necessity figure references.

```latex
The controls preserve different aspects of the comparison. Layer-matched random knockout keeps the selected set's distribution across depth, allowing the ranked heads' behavioral effect to be compared with other heads at the same layers. The paragraph-address experiment then keeps the selected heads and their calibrated targets fixed while changing the evidence location that receives those targets. Together, these comparisons connect the query-dependent attention signal to specific interventions on the model's evidence use. They motivate the next test: whether the local reading pattern becomes more useful when access reaches the relevant paragraph.
```

**Purpose:** Introduce the diagnostic transition through control logic, rather than adding more negative-result statistics. The target masses are held fixed; the realized mass changes can differ across paragraphs.

## 4. Explain the reader's operational validation

**Location:** `sections/experiments.tex`, Section 4.4, after the paragraph reporting the 103 ambiguous cases, before its table.

```latex
This subset is defined by the input graph before evaluating model answers. Both ranking policies retain the root and one candidate paragraph and use the same adapted checkpoint, so their comparison tests how the chosen evidence affects generation. Reporting bridge accuracy alongside answer EM links the intermediate selection decision to its downstream consequence. The unique-candidate branch supplies a complementary check on the graph: its candidate matches the annotated bridge in 817 of 822 cases. The attention readout is therefore applied at the branch where the input structure leaves an actual choice to resolve.
```

**Purpose:** Clarify why this is a meaningful operational test of the readout. The 817/822 count already appears in the audited appendix and raw input-graph analysis; this promotes an existing result that explains why the reader is needed on a subset.

## 5. Explain what joint original/edited correctness adds

**Location:** `sections/experiments.tex`, Section 4.5, after the first paragraph describing the reciprocal exchange design, before the outcome paragraph.

```latex
We evaluate both edited-value following and joint correctness on the original and exchanged contexts. Following asks whether generation adopts the newly attached value. Joint correctness additionally requires a correct answer before the exchange, making the pair a test of successful evidence use in both versions of the same question. The two measures connect answer accuracy with appropriate answer revision under a localized input change. Evaluating the complete selection-and-answering procedure also allows its evidence choice to respond to the exchanged facts, matching the procedure used for ordinary inference.
```

**Purpose:** Explain the role of the now-visible joint-correctness plot, reinforcing the content-validation link without attributing the behavior to an isolated internal mechanism.

## Integration notes

- These are insertions, not replacements for scope statements or control results. Avoid adding another concluding summary after each insertion.
- The five paragraphs have a similar explanatory role to the supplied papers' fuller method/experiment transitions: a question, a controlled comparison, and the meaning of the measurement.
- All paragraphs use positive factual language. None claims a complete circuit, exclusive mechanism, independent mechanism generalization, or unchanged downstream value tensors.
- If the compiled body needs a smaller increase, omit insertion 3 first: the four-arm and operational explanations have the greatest payoff. If more explanation is needed, expand the shared-context construction in Section 3.3 rather than repeating repair scores.
- Exact page count must be decided from the newly compiled PDF. Preserve the conference font sizes and margins and let the explanatory content fill the added page naturally.
