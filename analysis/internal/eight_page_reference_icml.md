# Eight-page allocation: the two supplied ICML references

Comparison baseline: commit `175f9e299c3722c870b8bde120f45e31288be059`, whose main body occupies seven pages. The completed eight-page allocation is recorded in `eight_page_section_allocation.json`.

## Measurement and recommendation

**Concentrate the additional space on the diagnostic design and the interpretation of existing controls.** The current Related Work and conclusion already have approximately the same prose allocation as the references. A useful first expansion budget is **660–870 words**: 80–120 in the introduction, 230–300 in the framework, and 350–450 in experiments. Render after that pass and adjust to the requested eight main-paper pages.

This report measures the supplied persona PDF (`upload/icml2026_camera_ready (1)(6).pdf`), the emotion/LVLM PDF (`upload/icml2026__Camera_Ready_ (1)(5).pdf`), and the pre-expansion manuscript PDF `analysis/build_final/main.pdf`. Counts were extracted from the rendered PDFs with PyMuPDF in column reading order. Body-prose lines were identified by the ICML body font/size; captions were counted separately. Headers, affiliations, references, acknowledgements, impact statements, appendices, chart labels, table cells, and most display mathematics were excluded. Line-break hyphenation was joined. **Counts are approximate editorial measurements**, rounded below; inline equations, PDF span splitting, and mixed-format lines introduce small differences from a source-level word counter. They are suitable for allocation comparisons, not an official word-limit calculation. L/R denote left/right columns.

Both supplied references place substantive main-paper material on **page 9**. The persona paper has its two result tables and a conclusion continuation there. The emotion paper places Related Work and the conclusion there. Their section proportions and explanatory depth provide the useful benchmark for our eight-page target.

## Main-section comparison

| Allocation | Persona circuits | Emotion/LVLM circuits | Current CoReTrace |
|---|---:|---:|---:|
| Abstract, counted separately | ~160 | ~170 | ~200 |
| Introduction | ~730, 19% | ~740, 18% | ~560, 19% |
| Related Work | ~270, 7% | ~320, 8% | ~320, 11% |
| Preliminaries + method/framework | ~1,050, 27% | ~1,330, 32% | ~710, 24% |
| Experiments and scientific interpretation | ~1,690, 44% | ~1,670, 40% | ~1,220, 42% |
| Conclusion | ~120, 3% | ~90, 2% | ~120, 4% |
| **Main prose excluding abstract** | **~3,860** | **~4,140** | **~2,930** |
| Captions, additional to prose above | ~250 | ~390 | ~400 |
| Main figures / tables | 12 / 2 | 10 / 3 | 4 / 3 |

Percentages use the unrounded main-prose counts. CoReTrace already carries substantial detail in its captions and integrated multipanel figures. Additional body text should explain why the controls answer the scientific question and what the observed contrasts establish. The reference papers' larger number of individual figures is unnecessary to reproduce.

| Section | Persona: approximate visible span | Emotion: approximate visible span | CoReTrace: approximate visible span |
|---|---|---|---|
| Introduction | p. 1 L lower part through p. 2 | p. 1 R through p. 2 R | p. 1 R through p. 2 R |
| Related Work | p. 3 L | p. 9 L | p. 2 R through p. 3 L |
| Framework/method | p. 3 L through p. 5 L | Preliminaries p. 2 R–3 R; methodology p. 3 R–5 L | p. 3 L through p. 4 R |
| Experiments | p. 5 R through p. 8 R; two result tables on p. 9 | p. 5 L through p. 8 | p. 4 R through p. 7 L |
| Conclusion | p. 8 R through p. 9 L | p. 9 L through p. 9 R | p. 7 L through p. 7 R |

These spans include intervening floats. They should not be interpreted as pure prose-area measurements.

## Subsection allocation

### Persona circuits

| Section/subsection | Approx. prose words | Visible span |
|---|---:|---|
| 3. Method opening | 50 | p. 3 L |
| 3.1 Preliminaries | 320 | p. 3 L–R |
| 3.2.1 Metric | 230 | p. 3 R–4 R |
| 3.2.2 Layer selection via activation steering | 100 | p. 4 R |
| 3.2.3 Head-level localization | 120 | p. 4 R–5 L |
| 3.2.4 Neuron-level localization | 170 | p. 5 L |
| 3.2.5 Downstream circuit localization | 70 | p. 5 L |
| 4. Experiments opening | 70 | p. 5 R |
| 4.1 Experimental setup | 300 | p. 5 R–6 L |
| 4.2 Dynamics opening | 150 | p. 6 L |
| 4.2.1 Preparation | 200 | p. 6 L–7 L |
| 4.2.2 Establishment | 220 | p. 7 L–R |
| 4.2.3 Expression | 200 | p. 7 R |
| 4.2.4 Causal verification | 120 | p. 7 R–8 L |
| 4.3 Misalignment and enhancement | 440 | p. 8 L–R; result tables p. 9 |

The useful writing pattern is the space devoted to a **measurable intermediate target**, then multiple observations about its organization, then an explicit failure diagnosis, then the intervention. The ~440-word enhancement subsection explains the failure-specific rationale alongside quantitative gains. Our central diagnostic interaction deserves comparable interpretive attention, while our evidence supports an attention-level functional account.

### Emotion/LVLM circuits

| Section/subsection | Approx. prose words | Visible span |
|---|---:|---|
| 2. Preliminaries | 390 | p. 2 R–3 R |
| 3.1 Emotional direction extraction | 180 | p. 3 R–4 L |
| 3.2 Emotional circuit discovery | 430 | p. 4 L–R |
| 3.3 VEENA intervention | 330 | p. 4 R–5 L |
| 4.1 Experimental setup | 320 | p. 5 L–R |
| 4.2 Circuit-analysis opening | 30 | p. 5 R–6 L |
| 4.2.1 Layer-wise semantics | 210 | p. 6 L |
| 4.2.2 Cross-modal routing dynamics | 380 | p. 6 L–7 L |
| 4.2.3 Circuit composition | 370 | p. 7 L–R |
| 4.3 Mitigating emotional hallucinations | 360 | p. 7 R–8 |

Its strongest allocation lesson is the ~750 words across routing and circuit composition: observations are connected through explicit questions about function. The discovery method itself receives ~430 words, enough to explain the intervention target, its operationalization, and how measurements are interpreted. CoReTrace's factorization subsection (~220 words) and diagnosis results (~270 words) currently carry several distinct design decisions in compressed form.

### Current CoReTrace

| Subsection | Approx. prose words |
|---|---:|
| 3.1 Paired contextual reasoning | 120 |
| 3.2 Head localization and address readout | 150 |
| 3.3 Crossing access and local reading | 220 |
| 3.4 Evidence selection and selected-head adaptation | 220 |
| 4.1 Experimental setup | 180 |
| 4.2 Recoverable addresses during composition failures | 190 |
| 4.3 Access–reading diagnosis | 270 |
| 4.4 Repair, components, and ambiguous candidates | 270 |
| 4.5 Local-fact exchange validation | 140 |
| 4.6 Capability, cost, and scope | 180 |

## Concrete expansion priorities using existing evidence

1. **Explain why the controlled diagnostic uses shared contexts — add 100–130 words to §3.3.** Promote the relevant existing appendix explanation: a quadruplet crosses two bridges and two relations; all four composed receivers see one ten-paragraph context; direct queries provide aligned donor-token positions. State how this construction makes the four attention interventions comparable. Distinguish its 100 receivers/25 discovery quadruplets from the separate 1,000-source address-control panel. This strengthens the design rationale without changing the population or introducing new results.

2. **Make the crossed contrast interpretable — add 130–160 words to §4.3.** Explain the difference-in-differences in ordinary language: how much mass calibration changes the benefit of transferring the local pattern. For Llama, Native/Mass/Pattern scores imply an additive expectation of 60%; Both reaches 76%, yielding the reported +16-point interaction. This is arithmetic from the existing four cells. Tie that result to the exact attention contribution equation, then state the empirical level: the selected-head interventions reveal functional dependence between access and local weighting. Preserve the reported intervals, including Qwen3-8B's zero boundary. The explanation should focus on the interaction, with the matched paragraph controls supplying address specificity.

3. **Separate the two roles of the reader — add 90–110 words across §§3.2–3.4.** The diagnostic reader ranks paragraphs to measure information in native attention features, while deployment uses a separately fitted adapted-state reader to resolve multiple graph-derived candidates. Explain why a recovered address supplies an actionable selection signal and where that decision enters the inference procedure. Keep the no-ambiguity path and the complete-context fallback clear. Existing implementation and ablation results support every element.

4. **Develop the evidence-to-repair link — add 100–130 words to §4.4.** Explain the role of each existing comparison: native evidence selection measures the benefit of the supplied subset; adaptation changes selected-head computation; fixed restoration contributes to the capability profile; input-order versus reader ranking isolates the ambiguous bridge decision under the same adapted model. Use the 103-case control and exact agreement on the other 897 cases to show where the readout's practical gain occurs. Avoid listing the same full-table scores again.

5. **Explain paired fact-exchange success — add 80–110 words to §4.5.** Both answer strings remain present in the complete input after reciprocal exchange, while their relation attachments change. Joint correctness credits a case only when both its original and edited answers are correct. Explain why this is the relevant complement to edited-value following. State once that the selector reruns after the edit: the result validates the complete procedure's response to the local binding. Use the existing 75/72/77% joint success and its native comparison already displayed in the main figure; retain full outcome categories in the appendix.

6. **Strengthen problem motivation and population orientation — add 80–120 words to the introduction and 80–110 across §§3.1/4.1/4.2.** The central bridge is the question raised by successful address decoding: under what access conditions does that information contribute to the answer? Explain the difference between a direct second-hop question that names the bridge and a composed question that reaches it through the first fact. Orient readers to the fixed native constituent-correct population versus all-source repair evaluation, and to complete original evidence versus shared-context diagnostics. These distinctions are currently present but densely packed.

This range overlaps naturally across adjacent paragraphs; the total target remains **660–870 additional words**. Prioritize §§3.3, 4.3, and 4.5 if final page space is tighter. Keep the abstract, Related Work, conclusion, and caption lengths approximately stable. Preserve the current main figures/tables and the appendix's role for full controls, exact transforms, run-level outcomes, and reproducibility. No new experiment is required for these additions.
