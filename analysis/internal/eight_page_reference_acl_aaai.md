# Section balance for the eight-page main-text revision

Comparison baseline: commit `175f9e299c3722c870b8bde120f45e31288be059`, whose main body occupies seven pages. The completed eight-page allocation is recorded in `eight_page_section_allocation.json`.

## Recommendation

Expand the current main text through the **motivating diagnostic question, the intervention design, and the interpretation of the existing controls**. Related Work already has the amount of space and the problem-oriented structure used by the supplied ACL and AAAI papers. I do **not** recommend adding 90–140 words to Related Work simply to reach eight pages. The current conclusion is also sufficiently developed. A useful initial expansion budget is approximately 450–600 substantive words across the introduction, framework, and experiments, followed by compilation and page-level adjustment.

## Sources and counting convention

The comparison uses the supplied PDFs, with PDF page numbers rather than proceedings page numbers:

- `2025.acl-long.196_Interpret and Improve In-Context Learning via the Lens of Input-Label.pdf`: 23 pages; main argument through p. 9, acknowledgements/limitations and references on pp. 10–12, appendix on pp. 13–23.
- `21890-AAAI26.SunC-NLP(5).pdf`: nine pages; main argument through p. 7 and references on pp. 8–9. Appendices mentioned by this paper are absent from the supplied file.
- `analysis/build_final/main.pdf`: the completed seven-page main-text baseline, followed by references on pp. 8–9 and the appendix on pp. 10–24. SHA-256 of the measured PDF: `a4c76e1a710c50d40fc3410c5f1e105614c4e4249295866d33c151f742daeb2a`. Later expansion edits will change these numbers.

Counts are approximate **rendered prose words**, including inline citation names and section/subsection headings. PyMuPDF text blocks were assigned to their section in PDF reading order. Body-sized Times-family text was retained; figure/table captions, graphical labels, small table cells, running headers, and footers were excluded. Equations and extraction around small capitals can introduce small differences. Counts are rounded below and should guide allocation, not serve as an exact publication word limit. The raw section counts and heading coordinates are in `eight_page_section_counts.json`.

## Approximate section amounts and page spans

| Section | ACL input–label paper | AAAI multilingual reasoning paper | Current CoReTrace baseline |
| --- | --- | --- | --- |
| Introduction | **800 words**, pp. 1–3 | **775 words**, pp. 1–2 | **540 words**, pp. 1–2 |
| Related Work | **260 words**, p. 3 | **300 words**, p. 7 | **310 words**, pp. 2–3 |
| Preliminaries | **190 words**, p. 3 | Included in Methodology | Included in framework |
| Method / diagnostic framework | **765 words**, pp. 3–5 | **840 words**, pp. 2–4 | **675 words**, pp. 3–4 |
| Experiments / experimental analysis | **1,405 words**, pp. 5–8 | **960 words**, pp. 4–7 | **1,060 words**, pp. 4–7 |
| Additional mechanistic discussion | **590 words**, p. 9 | Integrated into analysis | Integrated into experiments |
| Conclusion | **90 words**, p. 9 | **95 words**, p. 7 | **115 words**, p. 7 |
| Total of these sections | **4,100 words** | **2,970 words** | **2,700 words** |

Page spans overlap because sections begin within columns and figures float. For example, the current Related Work spans two pages partly because a large diagnostic figure occupies the upper part of p. 3. Its actual prose remains compact. The ACL reference has a longer main argument and a different template; copying its absolute page allocation would overfill an eight-page ICML manuscript.

For a comparable five-part balance, combine ACL Preliminary with Method and its Discussion with Experiments:

| Share of measured section prose | ACL | AAAI | Current baseline |
| --- | --- | --- | --- |
| Introduction | 19.5% | 26.1% | 20.0% |
| Related Work | 6.4% | 10.1% | 11.5% |
| Framework / method | 23.3% | 28.3% | 25.0% |
| Experiments / mechanistic discussion | 48.7% | 32.4% | 39.3% |
| Conclusion | 2.1% | 3.2% | 4.3% |

The current paper's largest relative gap is in **absolute explanatory detail**, especially the introduction and method. Related Work already occupies the largest relative share of the three papers. Experimental analysis falls between the two references in proportional allocation.

## What to transfer from the reference organization

### Introduction: develop the question that the diagnosis answers

Both references devote roughly 780–800 prose words to establishing the phenomenon, identifying the unresolved mechanistic question, and previewing how distinct experiments answer successive questions. The ACL introduction develops its what/where/how progression. The AAAI introduction repeatedly connects the language-dependent failure, the inferred routing problem, and the targeted repair.

The current 540-word introduction has the right sequence but can make one transition more explicit: successful direct-hop answers establish behavioral access to supplied facts, while the recoverable bridge address creates a second question about how the composed query uses that evidence. A substantive expansion can explain why a paragraph-address readout, a knockout, and a crossed attention intervention answer different parts of this question. This gives the central factorial experiment a clear purpose before its algebra appears.

### Framework: allow the reviewer to understand the controlled comparison

AAAI spends approximately 840 words on method; ACL uses approximately 955 including preliminaries. The current framework is approximately 675 words. Additional space is most useful for explaining the two attention factors and the matched conditions: the mass assigned to a paragraph, the normalized distribution within it, what the direct-query donor contributes, and how the receiver computes the resulting output. A compact worked example can make the interaction estimand intelligible. A second short paragraph can connect the input-derived candidate set, ambiguity-triggered readout, and original-paragraph answer generation.

### Experiments: explain why the main comparisons establish the story

The ACL paper separates descriptive observations, functional interventions, and practical improvement, then returns to interpretation in its discussion. AAAI organizes its experimental section around shared structure, a failure diagnosis, causal controls, and alignment. Both give experiments clear evidential jobs.

The current figures and compact component/ambiguity tables already provide the right evidence. Further prose should interpret them: explain a four-arm interaction numerically, connect bridge-versus-root/other controls to the destination of access, and show why the 103 ambiguous inputs isolate the practical role of the readout. The content exchange then validates the complete repaired procedure's dependence on the changed local value. This adds scientific explanation using existing measurements.

## Suggested allocation for the additional page

| Location | Approximate added words | Content that earns the space |
| --- | --- | --- |
| Introduction | 120–170 | The unresolved step between recoverable bridge location and effective evidence use; why the diagnostic comparisons answer it |
| Framework / method | 140–190 | Matched attention factors and receiver computations; a concrete operational account of ambiguous candidate selection |
| Experimental interpretation | 180–240 | One worked factorial contrast and a precise explanation of the component/ambiguity evidence; transition to local-fact validation |
| Related Work | **0 recommended** | Current coverage and positioning are proportionate |
| Conclusion | **0 recommended** | Already longer than both reference conclusions |

These are editorial budgets, not mandatory quotas. Final placement should be decided from the compiled PDF with the original font sizes, margins, and figure readability preserved.

## Related Work decision

ACL uses two focused paragraphs: ICL mechanisms and interpretability methods. AAAI uses two focused paragraphs: cross-lingual knowledge/repair and mechanistic methods. Each category ends by connecting existing work to the paper's specific diagnostic contribution. The current three-paragraph structure already does this for factual composition, supplied evidence, and targeted repair, and it contains the relevant verified 2026 work.

At roughly 310 rendered words, or roughly 270 prose words when citation strings are omitted, the current section is already comparable to these references. An extra 90–140 words would mostly restate the framework's distinction between recoverability, controlled intervention, and deployment. Those explanations are more useful adjacent to the methods and evidence they clarify. Keep Related Work concise and let the additional main-text space deepen the diagnostic argument.
