# Related-work and submission-format verification

Verified on 2026-11-24 (Asia/Shanghai). Scope: the supplied manuscript, its bibliography, and primary publication/venue sources. This is an editorial audit, not an experimental reanalysis.

## Recommendation

The existing bibliography already contains the three most directly useful 2026 studies found in the targeted search: **Layer-Order Inversion** (EMNLP 2026), **Failure Modes in Multi-Hop QA** (ACL 2026), and **Bridge Routing Heads** (EMNLP 2026). All three are real published papers, and their existing author lists, titles, proceedings, page ranges, URLs, and DOIs match the primary publication pages. Preserve them. The paper does not need a larger catalogue of 2026 citations.

The current Related Work is broad enough but its organization is too adversarial: almost every cited paper is followed by a deficit. That obscures the positive progression leading to the manuscript's actual contribution. Reorganize around (1) composition of stored facts, (2) access to supplied evidence, and (3) converting internal signals into targeted intervention. Each paragraph should establish a result already known and end with the precise extension measured here.

The useful scientific distinction is **decodable address -> effective access -> useful local reading**. The novelty should reside in the crossed intervention and the measured interaction, supported by the readout and local-value exchange. Neither a successful probe nor output improvements alone localize a complete reasoning circuit.

## Reference selection

- Keep `press2023compositionality`, `biran2024hopping`, `yu2025back`, `liu2026layerorder`: they define the composition problem and the alternative explanations in parameterized knowledge.
- Keep `guo2025twohop` and `zhang2026failure`: these are the closest contextual-composition and evidence-recognition comparisons.
- Bring `liu2024lost`, `wu2025retrieval`, and optionally `yuksekgonul2024attention` into the narrative; all already exist in the bibliography. They ground the access problem and the distinction between attention-derived prediction and causal component evidence.
- Keep `kim2026bridge` for a recent example of intervention on multi-hop routing.
- `sun2026bridging` is the only supplied reference with a particularly direct scientific relationship: multilingual multi-hop failure and selected-head tuning. Retaining it is justified if the head-adaptation lineage matters. Its inclusion should be based on this connection, independently of its role as a style example.
- Remove `qin2026persona`, `zhang2026emotional`, and `sun2025mappings` from the Related Work paragraph. Their subject matter widens the discussion without advancing the contextual-composition argument. Their entries may remain in the source bibliography, but uncited entries will not appear in the compiled paper.
- Do not add a literature claim to the abstract merely to increase coverage. A self-contained abstract should reserve space for the question, diagnosis, evidence, and repair outcome.

## Suggested Related Work (existing citation keys only)

```latex
\section{Related Work}
\label{sec:related}

\paragraph{Composing factual knowledge.}
The compositionality gap measures failures to combine correctly answered subproblems \citep{press2023compositionality}. Mechanistic accounts of latent multi-hop reasoning trace bridge-entity resolution and downstream answer extraction: back-patching exposes the importance of layer timing \citep{biran2024hopping}, while back attention addresses conflicting relation-specific signals \citep{yu2025back}. Recent work identifies layer-order inversion and models reasoning through probabilistic recall followed by selective extraction \citep{liu2026layerorder}. We study the corresponding gap when all queries share explicit evidence, making the bridge paragraph and its local relation value independently accessible to intervention.

\paragraph{Accessing and using supplied evidence.}
Long-context studies establish position-sensitive evidence use \citep{liu2024lost}, and retrieval-head ablations identify attention components that support contextual retrieval \citep{wu2025retrieval}. In synthetic two-hop tasks, \citet{guo2025twohop} describe the emergence of a sequential-query mechanism. On natural multi-document questions, \citet{zhang2026failure} connect evidence visibility to composition through position-controlled attention instructions. Our paired queries reveal a further distinction: an attention-derived bridge address can remain decodable during a failed answer. We test how paragraph access mass and the conditional attention pattern within that paragraph jointly affect composition, using crossed interventions with receiver-computed values and the original output-projection weights.

\paragraph{From internal signals to targeted repair.}
Attention probes can predict factual errors and constraint satisfaction \citep{yuksekgonul2024attention}. Mechanism-guided interventions also improve multilingual multi-hop reasoning through selected-head tuning \citep{sun2026bridging} and amplification of bridge-routing heads \citep{kim2026bridge}. \method\ links an internal paragraph-address readout to input-derived evidence selection and selected-head adaptation. Its ambiguity control measures where the readout changes the selected evidence and the answer; reciprocal value exchanges test whether the resulting predictions track the local facts. This connects diagnosis, controlled intervention, and an inference-time use of the recovered signal.
```

Historical draft status: the paragraphs above record the proposal before manuscript integration; the current LaTeX and compiled paper contain the final adopted wording. If the main paper becomes tight, omit SAT Probe and shorten the third paragraph to the two directly related multi-hop interventions. Avoid all assertions that earlier work lacks a capability unless that absence is essential to defining the current experimental comparison.

## Bibliographic findings

1. **Guo entry:** retain the arXiv citation (2025) and original title *How Do LLMs Perform Two-Hop Reasoning in Context?*. A secondary index calls a retitled version *How Do Transformers Perform Two-Hop Reasoning in Context?* an ICLR 2026 presentation, but the accessible primary OpenReview PDF states “under review,” and the authors' own publication pages list a 2025 preprint. The primary arXiv page supplies no accepted-venue metadata. Do not upgrade its venue on this evidence. The current entry's `primaryClass = {cs.LG}` should be corrected to `primaryClass = {cs.CL}`.
2. **2026 EMNLP DOIs:** the existing DOI forms `10.18653/2026.emnlp-main.1802` and `10.18653/2026.emnlp-main.2605` match the official pages. Their lack of `/v1/` is not an error.
3. **ICML 2026 style references:** the two supplied persona/emotion papers have real PMLR records with volume 306 and the long page ranges already present in the bibliography. Their metadata is valid, but their relevance to this particular Related Work is weak.
4. **AAAI 2026 supplied paper:** the publisher page was blocked by an access challenge during this audit. Its supplied proceedings PDF verifies the title, authors, and publication identity. The DOI/page details should be kept if already verified in the repository audit; do not claim the blocked page was successfully read in this session.
5. **Core existing entries:** the official pages confirm titles and author identities for Biran, Press, Yu, Geva, Liu (Lost in the Middle), Ho (2Wiki), Sun (input-label), Wu (retrieval heads), Yuksekgonul (SAT Probe), Zhang/Nanda (patching), Meng (ROME), HotpotQA, the Qwen3 report, the Llama 3 report, GSM8K, Adam, AdamW, and MMLU. No fabricated citation was found among the checked entries. This verification does not justify keeping every entry in the final narrative.

Corrected Guo entry:

```bibtex
@misc{guo2025twohop,
  title = {How Do {LLMs} Perform Two-Hop Reasoning in Context?},
  author = {Guo, Tianyu and Zhu, Hanlin and Zhang, Ruiqi and Jiao, Jiantao and Mei, Song and Jordan, Michael I. and Russell, Stuart},
  year = {2025},
  eprint = {2502.13913},
  archivePrefix = {arXiv},
  primaryClass = {cs.CL},
  doi = {10.48550/arXiv.2502.13913},
  url = {https://arxiv.org/abs/2502.13913}
}
```

## Primary source audit trail

| Source | Verified point | Exact source URL | Retrieved reference |
|---|---|---|---|
| Liu et al., EMNLP 2026 | Layer-order inversion; recall/extract framing; published metadata | https://aclanthology.org/2026.emnlp-main.1802/ | `turn238479448view0` |
| Zhang et al., ACL 2026 | Multi-Focus Attention Instruction; weakest-link/recognition account; natural multi-document QA | https://aclanthology.org/2026.acl-long.1937/ and https://aclanthology.org/2026.acl-long.1937.pdf | `turn699791339search1`, `turn992637333view2` |
| Kim et al., EMNLP 2026 | Bridge-routing heads; ablation and amplification; published metadata | https://aclanthology.org/2026.emnlp-main.2605/ and https://aclanthology.org/2026.emnlp-main.2605.pdf | `turn238479448view1`, `turn992637333view1` |
| Yu et al., EMNLP 2025 | Logit-flow account; relation extraction conflicts; back attention | https://aclanthology.org/2025.emnlp-main.567/ | `turn992637333view3` |
| Biran et al., EMNLP 2024 | Sequential bridge resolution; back-patching analysis | https://aclanthology.org/2024.emnlp-main.781/ | `turn193132659search0` |
| Press et al., Findings EMNLP 2023 | Conditional compositionality gap | https://aclanthology.org/2023.findings-emnlp.378/ | `turn193132659search1` |
| Guo et al., arXiv 2025 | Synthetic two-hop setting; 3-layer Transformer; sequential-query mechanism | https://arxiv.org/abs/2502.13913 | `turn939018473view3` |
| Guo et al., OpenReview manuscript | Retitled version remains marked under review in accessible PDF | https://openreview.net/pdf?id=DPdev1Gg1o | `turn400028095search3` |
| Wu et al., ICLR 2025 | Retrieval heads; causal pruning tests | https://proceedings.iclr.cc/paper_files/paper/2025/hash/9b77f07301b1ef1fe810aae96c12cb7b-Abstract-Conference.html | `turn238479448view2` |
| Yuksekgonul et al., ICLR 2024 | Attention-derived SAT Probe predicts errors and constraint satisfaction | https://proceedings.iclr.cc/paper_files/paper/2024/hash/880ee6e23b6ee548ebcccafe0ef0f513-Abstract-Conference.html | `turn238479448view3` |
| Zhang and Nanda, ICLR 2024 | Patching metrics and corruption choices affect localization conclusions | https://proceedings.iclr.cc/paper_files/paper/2024/hash/06a52a54c8ee03cd86771136bc91eb1f-Abstract-Conference.html | `turn587756483view0` |
| Liu et al., TACL 2024 | Position-sensitive long-context use | https://aclanthology.org/2024.tacl-1.9/ | `turn228733578view1` |
| Qin et al., ICML 2026 | Published persona paper metadata | https://proceedings.mlr.press/v306/qin26h.html | `turn939018473view0` |
| Zhang et al., ICML 2026 | Published emotional-circuit paper metadata | https://proceedings.mlr.press/v306/zhang26fi.html | `turn939018473view1` |

Other verified bibliographic URLs are the existing exact URLs in `source_upload/references.bib`. Their retrieval records are `turn228733578view0` through `turn228733578view6`, `turn587756483view1` through `turn587756483view3`, `turn587756483search5`, and `turn587756483search6`.

## ICML target and formatting

The uploaded manuscript uses `icml2027.sty`. Official ICML 2027 author instructions and the 2027 style package are already available as of the audit date. The submission main body is limited to **8 pages**, including the conclusion. References, appendices, impact statement, and AI Disclosure Statement are excluded from that limit. Use anonymous submission mode. Key material needed to assess the result belongs in the main paper because consulting appendices is optional for reviewers.

Author instructions: https://icml.cc/Conferences/2027/AuthorInstructions (`turn649978355view1`).

Call for papers: https://icml.cc/Conferences/2027/CallForPapers (`turn649978355view2`).

Official style ZIP: https://media.icml.cc/Conferences/ICML2027/styles/icml2027.zip (linked by the official instructions; binary retrieval unsupported by search tool).

Official example: https://media.icml.cc/Conferences/ICML2027/styles/example_paper.pdf (`turn193132659view1`). It specifies 10-point Times, standard two-column geometry, figure captions below/table captions above, and no compression of template vertical spaces. Its accepted-copy footer still has stale 2026 conference details; anonymous submission mode avoids this issue. The author instructions allow 50 MB for submission while the example contains a stale 10 MB line; keeping the final file below 10 MB satisfies both.

### AI disclosure

The new official 2027 policy requires an **AI Disclosure Statement for every submission**, before or after references, outside the page limit. It includes substantive manuscript drafting, literature synthesis, interpretation, and figure construction among uses to disclose. Routine spelling/formatting edits are exempt from substantive-use reporting, but this requested revision is broader.

Policy: https://icml.cc/Conferences/2027/UseOfGenerativeAIByAuthors (`turn649978355view3`).

Suggested wording reflecting the work actually performed in this revision:

> Generative AI tools assisted with organizing the scientific narrative, reviewing related literature, cross-checking manuscript claims against the existing experimental artifacts, and revising text and presentation. Numerical claims were checked against recorded results, bibliographic details were checked against primary sources, and the final LaTeX document was compiled and visually inspected.

Do not state that authors have independently reviewed or approved the result until that has actually happened. This statement covers the observed editorial work; the authors should extend it if earlier research-stage AI use also needs disclosure.

## Official template binary comparison

The official ZIP was downloaded successfully from the URL above and compared byte-for-byte by SHA-256 against every matching file in the repository paper directory. Results are recorded in `icml2027_template_verification.json`. The supplied manuscript's `icml2027.sty`, `icml2027.bst`, `algorithm.sty`, `algorithmic.sty`, and `fancyhdr.sty` all match the official package exactly. No template replacement or custom geometry is required.
