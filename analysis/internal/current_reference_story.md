# Reference-informed scientific story review

## Scope and reading record

This review reads the complete supplied manuscript (`source_upload/main.tex`, all section files, table inputs, and bibliography context) and all supplied pages of the four reference PDFs. It also visually inspects the manuscript's three conceptual figures. The four reference files contain: ACL input–label mappings, 23 pages; AAAI multilingual circuits, 9 pages; ICML persona circuits, 22 pages; ICML emotional circuits, 20 pages. The AAAI file cites appendices that are **absent from the supplied 9-page PDF**; no claim is made to have read those missing materials.

This is a narrative and evidence-logic review. Numerical statements below reproduce the uploaded manuscript for cross-checking by the separate repository audit; this report does not independently authenticate the run artifacts.

## 1. Recommended central story

**Contextual composition fails at the coupling between evidence access and local use: bridge-paragraph identity remains decodable in many failures, while a crossed intervention shows that paragraph access changes the usefulness of the within-paragraph attention pattern. This diagnosis motivates a targeted repair whose internal address signal has a measurable role in resolving ambiguous evidence.**

The most distinctive finding is the **access–pattern interaction**. Sparse head adaptation is an application of this finding and of the localization work. It is already an established intervention family in the supplied AAAI and ACL papers, so it should not carry the novelty claim by itself.

The paper should keep the existing concrete opening: two correct constituent answers, identical ten-paragraph evidence, wrong composed answer. The next question should be precise: *When the bridge remains identifiable, what prevents the model from using its local relation value?* The answer is then operationally tested through the two attention factors. This creates the currently underdeveloped diagnosis step without inventing a deeper circuit.

Recommended title direction: **When Correct Hops Fail to Compose: Diagnosing Evidence Access and Local Reading**. The current title's first half is memorable and accurate; “Evidence Access Shapes Local Reading” is comparatively broad. Another concise option is **When Correct Hops Fail to Compose: An Evidence-Access Diagnosis**, provided the abstract immediately states the access–reading interaction. Avoid “a complete reasoning circuit,” “the mechanism of composition,” “stored knowledge remains intact,” or an unmeasured universal bottleneck.

### Evidence chain to present

| Step | Question for the reader | Existing evidence | Supported interpretation |
|---|---|---|---|
| Problem | Do failures remain when each hop works? | Native constituent-correct sets contain 234/236/243 composition errors among 457/462/501 sources. | Composition creates an additional difficulty under the same evidence. |
| Finding | Is the bridge paragraph still identifiable? | Training-fitted readout recovers 72.2/74.6/86.0% of these failed cases, above metadata controls. | Selected-head attention contains a usable paragraph-address signal. |
| Localization | Does the selected access pathway affect behavior? | Selected-head knockout is stronger than layer-matched random knockout; bridge-mass calibration improves answers while root/other-paragraph calibration has opposing effects. | These components and the destination of access are causally consequential in the evaluated settings. |
| Diagnosis | How does access affect local use? | Four intervention arms separate paragraph mass and normalized within-paragraph pattern; interactions are +8/+5/+16 pp. | The usefulness of the direct-query pattern depends on paragraph access. |
| Repair | Can the measured signal improve an input-based procedure? | Adaptation, restoration, and selection ablations; attention ranking resolves 103 ambiguous graphs; predictions remain identical in the other 897 cases. | The address readout has a localized operational contribution to repair. |
| Validation | Does the repaired procedure follow changed local facts? | Reciprocal value exchange, edited-value following, and joint before/after correctness. | The full procedure responds to local relational assignment under fixed complete-context word counts. |

The content exchange should follow the repair results in the exposition. It evaluates the complete procedure after evidence selection is recomputed; it does not directly identify the mediator of the earlier native factorial effect.

## 2. What each reference teaches

### ACL 2025: input–label mappings

Relevant locations: pp. 1–3 (questions and contribution structure), pp. 6–9 (observations, perturbations, head behavior, repair), pp. 13–23 (full interpretation, training, generalization, controls).

The narrative has a clear sequence of reader questions: what is represented, where does it matter, how is it used, and what improvement follows. Each descriptive observation is followed by a manipulation: semantic principal components are perturbed; selected heads are ablated; attention scores between class labels are exchanged. The last control is especially instructive because it targets the proposed *function* of the component, beyond demonstrating that the component matters.

For CoReTrace, the useful analogue is not a new three-stage terminology. It is the distinction between **component relevance** and **functional diagnosis**: knockout says a head matters, while the access/pattern crossing says what aspect of its operation changes the answer. The paper should explicitly give the second role to the factorial experiment.

The main quantitative result combines target-task improvement, parameter count, and a compact general-capability column. Detailed per-model and per-dataset replication sits in the appendix. This supports keeping CoReTrace's main repair comparison concise and moving complete capability breakdowns out of the central story.

The reference also has dense prose, inconsistent figure-panel references, and some stronger interpretation than its measurements establish. Those features should not be imitated. The requested revision can adopt the question-driven evidence sequence with more calibrated claims.

### AAAI 2026: multilingual shared circuits

Relevant locations: pp. 1–2 (paradox and diagnosis), pp. 3–4 (functional circuit interpretation and repair), pp. 5–7 (shared structure, necessity/recovery, transfer, capability summary).

The paper repeatedly connects one paradox to one diagnosis: the same factual query succeeds in one language and fails in another; circuit analysis identifies a shared substrate and a routing difference; targeted adjustment follows that diagnosis. Its worked example recurs across the introduction, circuit picture, intervention, and method. CoReTrace can similarly reuse the Walter–James–Arsuf example to explain the task and the two attention factors.

The key distinction is that the AAAI paper investigates parameterized multilingual knowledge and neurons. CoReTrace has a different object: supplied paragraphs, recoverable bridge addresses, and factorized attention intervention. The revision should make that object concrete rather than borrow claims about semantic-neuron storage.

The knockout and recovery figures give distinct evidential roles to necessity and sufficiency. CoReTrace currently has necessity-style ablation and controlled access interventions, but the supplied manuscript does not establish a complete, sufficient composition circuit. “Selected heads contribute causally” is an appropriate description. “The reasoning circuit is located” would add unsupported precision.

Of the four supplied papers, this AAAI work is the most defensible citation in the revised Related Work because it is directly related to multi-hop reasoning and head-based repair. The others mainly inform presentation.

### ICML 2026: persona circuits

Relevant locations: pp. 1–3 (metric gap and storyline), pp. 6–8 (three-stage evidence and diagnosis), pp. 14–18 (metric validation and matched competing-direction controls), pp. 20–22 (replication and latency).

This reference makes its diagnostic pivot especially explicit. The broad circuit description leads to a specific failure hypothesis: persona signals compete with an operationally defined assistant-like direction. The appendix then contains matched directions, similarity measurements, and suppressive interventions. The strongest transferable lesson is **state the explanation as a testable operational hypothesis, then give the contrast that distinguishes it**.

For CoReTrace, the hypothesis is: increasing access should change the marginal value of the direct-hop local pattern. The four-arm table and interaction contrast are exactly the discriminating experiment. This can serve as the manuscript's explicit diagnostic hinge without adding any new experiments or abstract terminology.

The persona paper uses appendix material to validate the measurement instrument, test alternative operationalizations, and document transfer. CoReTrace's readout feature controls, exact attention transformations, fixed-population analyses, batch differences, and detailed prompt/scoring protocol serve the same supporting roles.

This reference also occasionally equates preserved benchmark scores with functional orthogonality. CoReTrace should report measured capability retention directly; aggregate task scores do not identify disjoint computation.

### ICML 2026: emotional circuits

Relevant locations: pp. 1–4 (functional decomposition and two-component intervention), pp. 6–8 (saliency hypothesis, causal patching, component validation, main results), pp. 13–20 (metrics, counterfactual checks, full results, side effects).

The clearest presentation choice is its separation of observational saliency from phase-level activation-patching verification. CoReTrace can use the same evidential discipline: attention differences nominate heads; readout shows decodability; knockout/access interventions test causal relevance; factorial manipulation tests interaction.

Its counterfactual appendix explicitly records what was preserved in the paired inputs and what was changed. CoReTrace's reciprocal text exchanges have stronger exact invariants: complete-context character and word multisets, question, titles, and order. These should be stated precisely, followed by the evaluation object: the complete repaired procedure with recomputed selection.

Its Related Work groups papers by the paper's scientific problem and analytical tool. This is useful. Generic comparisons to emotion/persona applications would distract from CoReTrace's own scientific question. It is also unnecessary to copy the reference's broad rhetoric about universal mechanisms or causal fidelity from aggregate performance.

## 3. Global diagnosis of the uploaded manuscript

### Coherence already present

The title, abstract, introduction, attention factorization, and conclusion already share the vocabulary of evidence access and local reading. The task protocol, paired interventions, address readout, and full repair are substantial and complementary. The manuscript has enough evidence for a coherent paper; a new layer of speculative mechanism is unnecessary.

### Main narrative weaknesses

1. **The diagnosis is stated after the machinery.** The method introduces ranking, readout, factorization, exchanges, and repair before the reader has seen why each is needed. Make the motivation for the factorial contrast explicit before its formalism, and structure results by the causal questions above.
2. **The core interaction competes with many headline numbers.** The abstract currently includes failure rates, three readout rates, interaction range, swap rates, six accuracies, parameter fraction, and inference frequency. Keep the failure setting, interaction finding, and one compact repair gain. Readout range can remain; per-model raw scores and the 10.3% overhead belong in the results.
3. **Repair components appear as an accumulation.** Explain two scientific targets (identify the bridge and use its content) and one stability operation (fixed projection restoration). The restoration rule is an empirically specified component; no need to claim it uniquely implements the factorial diagnosis.
4. **The bridge from diagnosis to repair is not visually supported in the main text.** Main accuracy is visible, but the component ablation and ambiguous-candidate result are hidden in the appendix. A compact summary of those two analyses would make the application much more persuasive.
5. **Content exchanges are introduced before the repair's performance.** Move them after repair and ambiguity results so their role is validation of input dependence.
6. **Related Work reads as a sequence of objections.** Phrases about retrospective layer-pair selection, absent repair, and remaining observational analyses make earlier work seem like a list of deficiencies. Replace with factual accounts of what each line established, followed by the precise variable that CoReTrace tests.
7. **Too many conceptual figures repeat the same pipeline.** The tall teaser, complete diagnostic schematic, and complete method schematic collectively consume more space than their new information warrants.
8. **Conclusion makes an inferential jump.** “Reciprocal fact exchanges connect this interaction to predictions…” blends two experiments. Say instead that crossed interventions establish access–pattern dependence and reciprocal exchanges validate the repaired procedure's response to local facts.

## 4. Evidence boundaries and positive formulations

| Evidence | Precise statement to use | Scope to preserve |
|---|---|---|
| Constituent success | “The same evidence supports correct answers to both constituent probes.” | Behavioral availability under different questions; not simultaneous composition of those representations. |
| Linear readout | “Selected-head attention supports accurate bridge-paragraph readout even on many failed compositions.” | Decodability from training-fitted features; does not establish that the native output computation already selects that bridge. |
| Knockout | “The localized heads contribute causally to constituent and composed answers.” | Effects occur across query types, so composition-specific specialization is unestablished. |
| Address controls | “The effect depends on directing access to the bridge paragraph.” | The intervention uses annotated addresses and is a diagnostic, whereas deployment uses input-derived candidates. |
| Factorial contrast | “Calibrated access increases the marginal benefit of the direct-query attention pattern.” | A functional interaction in the selected-head intervention family, evaluated on 100 receivers in 25 discovery quadruplets. |
| Donor transfer | “The receiver computes its own values and output projections.” | This does not freeze all downstream activations or prove a unique token-level semantic mechanism. |
| Reciprocal exchange | “The repaired procedure follows the newly assigned local value under fixed complete-context word counts.” | Evidence selection is recomputed; the retained generation context can consequently differ. |
| Ambiguity result | “The attention readout improves composed accuracy on the 103 ambiguous cases, with identical outputs on the other 897.” | A strong localized effect of the selection decision; full-panel gains are 3.4–4.0 pp. |
| Sparse adaptation | “Selected-head updates use 0.49–0.94% of model parameters.” | Parameter efficiency; no claim that these are uniquely optimal trainable heads without a matched head-training study. |
| Capability scores | “Restoration recovers substantial capability after adaptation; final benchmark changes are reported by model.” | Report measured changes, not perfect preservation or proven circuit orthogonality. |
| Recorded runs | “Three recorded evaluations; paired bootstrap intervals quantify sampling variation.” | Fixed source order and zero initialization make selected-head training deterministic; SD is not independent training-seed uncertainty. |

These qualifications can be communicated affirmatively in a compact protocol paragraph or appendix. They need not dominate the main narrative.

## 5. Figure and table roles for an eight-page main text

### Recommendation on the standalone causal schematic

**Move `figure2_diagnosis.pdf` to the appendix.** Its ranking panel repeats the method description; its four-arm panel is already expressible in the numerical factorial figure; its exchange panel repeats the content-validation description. Keep the numerical `data_fig4_causal.pdf` in the main text as the central figure and define the four interventions adjacent to it. If a small scientific schematic is desired, reuse the access-factorization idea in a compact teaser or an inset above the numerical factorial panel.

### Suggested main assets

| Asset | Main scientific role | Recommended treatment |
|---|---|---|
| Compact failed-chain teaser | Establish the paradox and task immediately | Retain the Walter–James–Arsuf example; reduce the current three stacked panels. Its present full-height design is too expensive for a column figure. |
| Failure/readout quantitative figure | Pair the behavioral gap with surviving address signal | Keep. Clearly label different denominators and the native model used for features. |
| Factorial plus address-control figure | Central diagnosis and destination specificity | Highest visual priority. Show four arm accuracies and interaction intervals; all models should remain directly comparable. |
| Main composed/all-three result table | Establish the repair gain and joint task performance | Keep. Exact constituent breakdown remains in appendix. |
| Compact component/ambiguity summary | Connect method parts and internal signal to gain | Promote selected rows of the component table and ambiguity result. This is more central than a large capability table. |
| Content-swap result | Validate local input dependence | A compact table with following and joint correctness is sufficient; obsolete-answer persistence can remain in the complete appendix table. |

`figure3_method.pdf` can remain if it fits after reducing the teaser, but its implementation flow is adequately conveyed by three short method paragraphs and an appendix figure. It is the next candidate to move after the causal schematic. Avoid sacrificing the component/ambiguity evidence to retain three large schematics.

Complete layer/head heatmaps, all knockout doses, reader feature controls, full four-arm contrasts, complete exchange outcomes, parameter counts, prompt/scoring details, all capability splits, cost tables, and per-run results belong in the appendix. The appendix should be ordered for verification rather than following the chronology of experiment execution.

Suggested appendix order: data and splits; exact protocol; localization and interventions; complete repair/component results; capability and output-format results; efficiency and reproducibility. Insert explicit pointers from each main claim to its complete evidence.

## 6. Related Work strategy

Three concise paragraphs can support the story:

1. **Composition from parametric knowledge.** Establish the compositionality gap and the progression toward mechanistic accounts of bridge timing and relation extraction. Conclude with the distinct question addressed here: composing facts available in supplied evidence.
2. **Evidence use in context.** Position paragraph selection, attention-based retrieval, and contextual multi-hop mechanisms. Explain that the present experiment separates total paragraph attention from its normalized internal pattern, making their interaction measurable.
3. **Causal diagnosis and targeted repair.** Establish intervention-based analysis and component adaptation as tools. State that CoReTrace couples a functional diagnosis with an input-only repair and isolates the readout's effect on ambiguous candidates.

Remove persona and emotional-circuit citations unless a specific borrowed method requires attribution. Their tasks and attribution metrics are peripheral. The ACL input–label paper is relevant to head adaptation in a broad sense, but the AAAI multi-hop paper is closer and enough if space is limited. Do not cite all four solely because they supplied storytelling examples.

The current manuscript already contains several 2026 entries, but the presence of a year is not verification of publication status. The separate literature audit should verify venues, titles, and substantive claims. Recent papers should sharpen the distinction between evidence-location decodability and evidence-use intervention, rather than add a fourth generic related-work category.

## 7. Specific revision priorities

1. Put the operational diagnostic hypothesis into the introduction and at the opening of the factorial subsection.
2. Use the same term for each measured object throughout: **bridge paragraph**, **paragraph access mass**, **within-paragraph attention pattern**, **bridge-address readout**, **selected-head adaptation**, **fixed projection restoration**.
3. Reserve “local reading” for the high-level interpretation and define it through the within-paragraph pattern plus the receiver's values/output projection.
4. Make the Llama four-arm result a worked quantitative example, then state the other-model interactions and confidence intervals once.
5. Explain that head selection and the 25-quadruplet factorial analysis use discovery data. The 1,000-source repair result is a separate fixed test panel.
6. State the input-only inference rule clearly: a unique candidate needs no readout; ambiguous candidates trigger one full-context prefill; inapplicable graphs retain context.
7. Promote the 103-case ambiguity contrast. This is a precise link from an interpretability signal to a practical decision.
8. Frame full fine-tuning as the fixed-recipe comparison actually run. A broad superiority claim over optimized fine-tuning or PEFT would exceed that experiment.
9. Keep general capability information truthful and compact. Main-text emphasis can be on recovery from adaptation and measured final capability, with the complete adverse and positive results available in the appendix.
10. Remove forced page breaks that isolate the conclusion; then inspect the compiled PDF page by page. The supplied emotional reference itself has a stale template running header and crowded figures; the final manuscript should use it for scientific organization, not as a typography target.

## Overall assessment

The manuscript's best contribution is a controlled explanation of why a recoverable paragraph address can coexist with a failed composed answer. Its four-arm intervention is more distinctive than the sparse repair alone, and the ambiguity-conditioned readout result supplies the cleanest link to application. A focused revision should make these two experiments immediately visible, place reciprocal content exchange in its proper validation role, and retain complete reproducibility details in the appendix. This yields a clear, forceful story while preserving the exact scope of the existing evidence.
