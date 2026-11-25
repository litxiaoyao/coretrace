# Mechanism-centered story revision plan — 2026-11-25

## Scope and evidence reviewed

This is an editorial working note for the authorized manuscript revision. It does not change the scientific results or prescribe new experiments. Figures 1–3, including their existing figure environments and captions, remain unchanged. The parent editor integrates the introduction/abstract candidates. Following a separate delegation, this agent also edited only `paper/related_work.tex`; its three-paragraph structure and all eleven existing citation keys were preserved.

The candidates below were prepared from the current repository manuscript, rather than from the earlier PDF review alone. Read: `paper/main.tex`, `paper/sections/{introduction,method,experiments,conclusion}.tex`, `paper/related_work.tex`, `analysis/{STORY_DESIGN,CLAIM_EVIDENCE}.md`, and `docs/experiments.md`. Independently checked the recorded contents of all three `outputs/{model}/causal_factorization/summary.json` files, Llama's `causal_access/summary.json` and `seed42/causal_content/summary.json`, and `outputs/tables/tables.csv`. The older analysis documents provide evidence and history; the current user instructions govern emphasis.

## 1. Central proposition and narrative hierarchy

**Central proposition:** Evidence access shapes the usefulness of local reading during contextual composition. Paired queries locate heads involved in this process; crossed attention interventions reveal the interaction; adapting these heads and selecting relevant evidence turn the mechanism into a practical improvement.

The paper should proceed through **question → localization → discovery → causal explanation → application**:

1. The same evidence supports both constituent answers but often fails to support their composition.
2. Direct versus composed queries expose a concentrated set of evidence-access heads. Their knockout establishes a causal contribution to answering.
3. Attention from these heads still contains recoverable information about the bridge paragraph when composition fails.
4. Separately manipulating paragraph mass and normalized local attention reveals that the benefit of a reading pattern depends on the access allocated to that paragraph.
5. CoReTrace uses the identified heads and recoverable evidence information to improve composition; reciprocal fact exchanges show the resulting system follows the relevant local values.

The principal finding is the access–reading interaction, supported by localization and causal intervention. Readout disambiguation is an application component, not a second scientific center. Projection restoration is part of the adaptation recipe and its supporting analysis, not the opening problem. Keep the complete recorded constituent and capability outcomes available in their tables and appendix, without letting regressions organize the main narrative.

### Compact statement for opening/closing transitions

> Our analysis identifies an interaction between where attention is allocated and how the selected evidence is read. CoReTrace turns this mechanism into a targeted intervention on the responsible heads and the evidence supplied to them.

The word “responsible” here denotes the experimentally implicated heads; it should not be expanded to “the complete composition circuit” or “composition-exclusive heads.”

## 2. Title

Recommended:

> **When Correct Hops Fail to Compose: How Evidence Access Shapes Local Reading**

Running title:

> **Evidence Access Shapes Local Reading**

This preserves the concrete puzzle while replacing a procedural subtitle (“Diagnosing”) with the scientific message. It fits the mechanism-first framing and does not require changes to Figures 1–3.

## 3. Abstract candidate

The following candidate contains approximately 180 words; model-specific before/after triplets, restoration details, and the ambiguous-candidate analysis remain in the body/appendix.

> Language models can answer each step of a factual chain from the same context yet fail when the steps are composed. We trace this failure through CoRe-2Wiki, which pairs composed and constituent queries under identical evidence. Across three models, composition fails on roughly half of constituent-correct sources. We identify attention heads whose bridge access changes with query formulation and whose removal disrupts answering. Their attention features retain recoverable bridge addresses even in failed compositions. To explain this discrepancy, we separate paragraph attention into access mass and the conditional reading pattern within the paragraph. Crossed interventions reveal that calibrating access increases the utility of direct-query reading patterns, with interaction estimates of 5–16 percentage points. Guided by these findings, CoReTrace combines adaptation of the identified heads with attention-guided evidence selection. Across Qwen3-4B, Qwen3-8B, and Llama-3.1-8B, it improves composed accuracy by 33.3–39.9 points with fewer than 1% trainable model parameters. Reciprocal fact exchanges further show that repaired predictions follow changed local values in 76–80% of cases. These results explain how evidence access shapes local reading and provide a mechanistic basis for targeted improvement.

Implementation into LaTeX should use the existing `\dataset` and `\method` macros and `--` for numerical ranges. If the editor prefers fewer numbers, the interaction range is more central than the reciprocal-exchange range; retain the overall application gain and parameter budget.

## 4. Introduction: six paragraphs with one job each

The candidates below use existing citation keys and figure labels. Preserve the existing Figure 2 environment verbatim at its chosen location; its physical placement need not determine the paragraph argument.

### Paragraph 1 — Concrete puzzle under identical evidence

> Large language models (LLMs) can retrieve facts from supplied evidence yet struggle to connect them across documents. Consider a context stating that Walter II of Avesnes was the son of James of Avesnes, and that James died at Arsuf. Llama-3.1-8B correctly answers questions about Walter’s father and James’s place of death, but predicts “Avesnes” when asked where Walter’s father died (\cref{fig:teaser}). Both facts are present, and both constituent questions are answerable under the same context. Why, then, do individually accessible facts fail to support their composition?

This keeps the existing worked example and factual content. It lets the question arise from the observation instead of adding a general claim that models “cannot reason.”

### Paragraph 2 — Scientific gap: access and reading in supplied evidence

> The compositionality gap has motivated studies of how LLMs connect facts stored in their parameters \citep{press2023compositionality,biran2024hopping,yu2025back,liu2026layerorder}. Work on contextual retrieval has also identified attention heads that carry relevant information across long inputs \citep{wu2025retrieval,zhang2026failure}. When both facts are supplied explicitly, composition places a more specific demand on this information flow: the model must access the paragraph about the intermediate entity and read the value requested by the second relation. These operations occur together in attention, making it difficult to determine how a change in evidence access affects local reading. Understanding their interaction is central to explaining why the same context supports separate hops but fails to support the composed question.

This identifies the question without listing deficiencies of individual papers. “The paragraph about the intermediate entity” introduces the bridge concept in ordinary language before relying on the term.

### Paragraph 3 — Paired queries locate the mechanism and expose the discrepancy

> We investigate this question with \dataset, a paired contextual reasoning protocol derived from 2WikiMultiHopQA \citep{ho2020constructing}. Each composed question is paired with its two constituent questions under the original context. The direct second-hop question explicitly names the bridge entity, providing a reference for tracing how composition changes access to the relevant paragraph (\cref{fig:causal_framework}). The resulting attention contrast identifies a small set of heads whose removal strongly reduces answering accuracy. Yet their attention features still retain substantial information about the required evidence: a linear readout fitted on training examples recovers the bridge paragraph in 72.2--86.0\% of composition failures with correct constituent answers. This combination of causal contribution and recoverable evidence information directs our analysis toward how the heads use the paragraph they access.

The removal result and recoverability result play different roles, stated once. No claim that the unmodified model itself executes the external readout is needed.

### Paragraph 4 — Central finding: access changes the usefulness of local reading

> Our central finding is that evidence access shapes the usefulness of local reading. We factor an attention row into the total mass allocated to the bridge paragraph and the conditional distribution over tokens within that paragraph. Crossed interventions independently calibrate the former and transfer the latter from a direct second-hop query, using values computed by the receiving model. Calibrated access makes the direct-query reading pattern more useful, yielding interaction estimates of 5--16 percentage points across the three models. For Llama, combining the two interventions reaches 76\% accuracy, compared with the 60\% expected by adding their separate effects. This interaction explains how a recoverable bridge address can coexist with ineffective evidence use: the contribution of a local reading pattern depends on the access allocated to its paragraph.

The 76-versus-60 comparison is a memorable positive mechanism result. It uses the exact recorded Llama arms: Native 51, Mass 64, Pattern 47, Both 76; additive expectation is 64 + 47 − 51 = 60. The experiments section should retain all four arms and confidence intervals; this paragraph need not center the negative pattern-only contrast.

### Paragraph 5 — Mechanism to application, with local-fact behavior

> Guided by this mechanism, we introduce \method, which couples adaptation of the identified heads with attention-guided evidence selection (\cref{fig:framework}). The method trains a small set of head projections to improve their use of evidence and uses recoverable paragraph information to select a compact context for composition. Across Qwen3-4B, Qwen3-8B, and Llama-3.1-8B, \method\ improves composed accuracy by 33.3--39.9 percentage points while updating fewer than 1\% of model parameters. Its predictions also follow local factual changes: after reciprocal exchanges of relation values between paragraphs, the repaired system answers with the changed value in 76--80\% of cases. These results connect the mechanistic account to improved composition and evidence-sensitive predictions.

If “to improve their use of evidence” feels too close to an unmeasured post-training attribution claim, use “for composed question answering.” Do not say head adaptation is proven to restore precisely the measured mass/pattern interaction; such before/after mechanism measurement is not in the checked records.

### Paragraph 6 — Three contributions organized around scientific content

> Our contributions are threefold:
>
> - **Tracing evidence access.** We introduce a paired-query protocol that localizes causally important evidence-access heads and reveals recoverable bridge information during composition failures.
> - **Explaining local reading.** We separate paragraph access from within-paragraph attention and identify their interaction through crossed interventions, providing a functional explanation of how evidence access shapes reading.
> - **Improving composition.** We develop \method, translating these findings into substantial accuracy gains through selected-head adaptation and evidence selection, with reciprocal fact exchanges demonstrating sensitivity to local values.

This order leads with the explanation and its causal support. It avoids an administrative “Methodology/Mechanism/Application” division and does not repeat every headline number a third time.

## 5. Related Work: affirmative, specific replacement candidate

The existing section devotes substantial space to per-paper limitations (“retrospectively selects,” “without evaluating,” “without causal verification,” “remains observational”). Replace those audit details with what each line of work establishes and the concrete operation this manuscript studies. The following candidate preserves relevant citations while removing unsupported priority claims.

```latex
\section{Related Work}
\label{sec:related}

\paragraph{Latent multi-hop composition.}
The compositionality gap captures failed composition after successful constituent reasoning \citep{press2023compositionality}. Mechanistic studies connect latent multi-hop reasoning to the timing and use of intermediate information. \citet{biran2024hopping} diagnose delayed bridge resolution; \citet{yu2025back} address competing relation logits through trainable cross-layer attention; and \citet{liu2026layerorder} describe probabilistic recall and selective extraction. These accounts of parameterized knowledge motivate examining how available information becomes usable across a reasoning chain. We study this question with explicitly supplied facts, separating access to the bridge paragraph from the conditional reading of its contents.

\paragraph{Contextual evidence use.}
\citet{guo2025twohop} reconstruct a sequential-query circuit in a three-layer synthetic Transformer, connecting contextual two-hop reasoning to intermediate computations. \citet{zhang2026failure} examine position-dependent recognition of relevant documents. These studies motivate tracing how models identify and process evidence within a context. Our paired-query protocol compares composed and constituent questions under identical evidence, locating heads whose bridge access changes with query formulation. Supporting facts, distractors, and paragraph positions remain unchanged across queries. Crossed interventions then independently manipulate paragraph attention mass and its normalized token distribution, using receiver-computed values and original output-projection weights. This design reveals how access changes the usefulness of local reading.

\paragraph{Circuit-guided repair.}
Mechanistic findings also guide targeted model improvement. \citet{sun2026bridging} align multilingual pathways over shared semantic neurons by tuning critical heads, while \citet{kim2026bridge} amplify bridge-routing heads in multilingual reasoning. \citet{sun2025mappings} tune heads that apply input--label mappings during in-context learning. Related interventions strengthen persona signals \citep{qin2026persona} and visual emotional information flow \citep{zhang2026emotional}. \method\ extends this explanation-to-intervention approach to contextual composition: the access--reading interaction identifies complementary targets for selected-head adaptation and evidence selection. Reciprocal fact exchanges further connect the resulting improvement to predictions that follow local relation values.
```

For tighter space, omit the final persona/emotion sentence from Related Work rather than discussing their tasks at length. They are valuable stylistic references, but contextual composition, retrieval heads, and multilingual bridge routing are the nearest scientific neighbors. The suggested descriptions use the repository's established reference mapping; this note did not introduce new external related-work claims or conduct a new novelty search.

## 6. Suggested main-section emphasis and transitions

Keep the existing method definitions and accurate intervention details. Improve the research-question structure through short positive headings:

| Current role | Suggested heading / lead sentence |
|---|---|
| Failure, localization, readout | **Tracing Evidence Access in Failed Compositions** |
| Causal interventions | **Evidence Access Shapes Local Reading** |
| Overall application | **Improving Composition with CoReTrace** |
| Reciprocal exchange | **Following Local Fact Changes** |
| Final practical evaluation | **General Capabilities and Efficiency** |

Prefer “The destination of access matters” and “Access changes the benefit of local reading” as result leads. Keep statistical and implementation details adjacent to the relevant result, without beginning every paragraph with verification language.

Candidate transition from localization to intervention:

> The selected heads contribute to answering and retain information about the relevant paragraph even when composition fails. We therefore ask how their allocation of attention determines the contribution of that paragraph to the answer.

Candidate transition from causal analysis to application:

> The interventions identify two complementary targets: access to the bridge evidence and its use by the localized heads. CoReTrace acts on both by selecting relevant paragraphs and adapting the identified projections for composed question answering.

Candidate local-fact paragraph lead:

> A successful repair should use the relation value in the selected evidence. We examine this behavior by reciprocally exchanging object spans between paragraphs that express the same relation, preserving the question and the full context's word and character counts.

This states the scientific reason for the exchange before procedural details. It must describe results of the complete procedure, with selection rerun, rather than a pure within-head semantic intervention.

Candidate conclusion:

> Correct constituent answers do not ensure successful composition, even when attention retains information about the relevant bridge paragraph. By localizing evidence-access heads and separately intervening on paragraph mass and local attention patterns, we show that access shapes the usefulness of local reading. CoReTrace translates this mechanism into selected-head adaptation and evidence selection, improving composed accuracy by 33.3--39.9 percentage points with fewer than 1\% trainable model parameters. Reciprocal fact exchanges show that the resulting predictions follow local evidence. Together, these findings connect a mechanistic explanation of contextual composition with a targeted way to improve it.

## 7. Accuracy checks for the editor, without turning them into the story

These checks constrain wording, not main-text emphasis:

- The factorized experiment has 100 receivers in 25 shared-context discovery quadruplets. The recorded interactions are +8 [1,14], +5 [0,10], and +16 [8,25] points. “Positive interaction estimates across the three models” is supported; “statistically significant in all models” is not.
- Direct-query donors contribute normalized attention, not copied answer vectors or value/output projections. No wrong-relation-donor experiment or trained-versus-native factorial comparison was found in the checked records; do not imply either exists.
- Receiver values are recomputed in the receiving forward pass and original output-projection weights are used in the diagnostic. “Using receiver-computed values” is precise; “holding all hidden states fixed” is not.
- Calibration can raise or lower a given row's mass. Use “calibrate,” “allocate,” or “reallocate,” rather than always “increase attention.”
- Knockout supports a causal contribution of the selected heads. These heads also support constituent answering; avoid composition-exclusive terminology.
- Keep complete recorded capability and constituent outcomes. A compact neutral treatment is compatible with a positive main story; lossless preservation claims are not supported.
- The main improvement is for the evaluated protocol. Existing measurements do not establish a SOTA comparison against unimplemented published methods.
- The new prose should use “full procedure/system” for reciprocal exchange results when the distinction matters. The address selector is rerun on edited inputs.

No new experimental data, application components, or Figure 1–3 modifications are proposed in this note.
