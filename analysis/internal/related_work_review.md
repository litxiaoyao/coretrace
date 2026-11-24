# Related-work full-reading record and claim boundaries

Internal working document. This file is not manuscript text. Prepared from full reading of the six attached PDFs, including all appendices (17 + 16 + 18 + 24 + 18 + 18 = 111 PDF pages), plus the Sun et al. reading supplied by the reference-narrative agent. PDF page numbers below count from the first PDF page; proceedings page ranges are also recorded. Text extraction and visual page montages are in the temporary `related_review/` directory outside the repository. Bibliographic metadata was checked against primary publication records on 2026-11-24.

## 1. Positioning decision tied to the actual project

The defensible central distinction is **evidence access gates relation-conditioned reading**. The paper should not claim to discover compositional failures despite correct single hops, attention-mediated information routing, bridge-related heads, or the benefit of tuning a small set of heads. All of those have close predecessors below.

The project-specific evidence chain, supplied by the lead analysis and to be checked against the final experiment tables, is:

1. In the native composed run, a linear readout decodes the address of the needed paragraph substantially more accurately than the model answers the composed question. This establishes availability to the probe, not native causal use of that address.
2. Direct-target and composed queries under shared context identify attention differences. Factorized interventions change paragraph attention mass, the conditional within-paragraph distribution, or both, while retaining the receiver's value/output computation. The interaction is the principal mechanistic result; do not flatten it into a generic 'routing' story.
3. Reciprocal object exchanges within contextual paragraphs hold the global answer-token counts fixed. These test local use of the selected paragraph rather than global answer availability.
4. Deployment is distinct from the discovery intervention: an input-derived title graph supplies candidates, a training-fitted linear readout selects a bridge paragraph when required, original paragraphs are selected, and scoped head adaptation with fixed model-specific value/output restoration is evaluated. No support labels, answer labels, or donor activations are used to make test-time selections.
5. Main-paper claims about the complete procedure should be based on the full test split and repeated seeds. Discovery receiver sets, rescue-only populations, and diagnostic donor effects answer different questions and must not be presented as deployment performance.

### Comparison map

| Work | Knowledge / task setting | Main mechanism and intervention | Exact missing test relevant here |
|---|---|---|---|
| Biran et al., 2024 | Parametric two-hop factual retrieval, known-hop controls | Delayed bridge resolution; late-to-early hidden-state back-patching | No contextual paragraph access/conditional-reading separation; successful patch locations selected retrospectively per example |
| Yu et al., 2025 | Parametric factual chains, plus application datasets | Competing relation logits; a new trainable cross-layer attention module | No paragraph-address bottleneck or factorized access/reading causal test |
| Liu et al., 2026 | Parametric MQuAKE, 2–4 hops | Layer-order inversion; probabilistic recall and selective extraction; corruption interventions | No supplied-evidence address/content separation; no evaluated mechanism-derived repair |
| Guo et al., 2025 | Synthetic in-context chains; large-model behavior and small-model mechanism | Three-layer sequential-query circuit; training phase transition | Same internal mechanism not causally established in pretrained LLMs on document QA |
| Zhang et al., 2026 | Contextual multi-document QA | Position-dependent recognition; oracle instructions naming gold documents | Oracle evidence locations; no independent neural factor intervention; prompting also reduces the search space |
| Sun et al., 2026 | Multilingual parametric factual chains | Shared semantic neurons, misaligned attention pathways; targeted head tuning | No paragraph-mass versus conditional-reading decomposition with receiver V/O fixed |
| Kim et al., 2026 | Multilingual parametric factual chains | General/specific bridge-routing heads; head-output amplification | No contextual address/read distinction; rescue subsets do not establish full-distribution deployment gains |

## 2. Bridge Routing Heads — Kim et al. (EMNLP 2026)

**Full title:** *Bridge Routing Heads: Where Multilingual Multi-hop Reasoning Lives in LLMs*.

**Authors:** Seunghan Kim, Minyeong Choe, Hyunil Kim, Haehyun Cho. Proceedings pp. 59179–59195. [Primary record](https://aclanthology.org/2026.emnlp-main.2605/).

### What the paper actually does

- **Task and controls (PDF pp. 3–4, Sections 3.1–3.2):** constructs 82,020 Wikidata two-hop compositions in five languages (English, Korean, Chinese, Japanese, Spanish). The retained examples have both constituent single-hop queries correct in the target language and both proposed shortcut queries wrong across all five languages. Section 3.2 explicitly restricts analysis to facts recalled from model parameters rather than supplied contextual evidence. Main models are Llama 3.1 70B and Qwen 2.5 72B. English entity strings are used in the main analysis; localized-entity variants are checked in Appendix D.
- **Localization (pp. 4–6):** module-level patching distinguishes shared MLP patterns from language-varying attention effects. The Bridge Routing Score combines head-mask gradient scores from first-hop, second-hop, and composed queries. Initial top-head budgets are chosen to retain a small all-language intersection. Individual ablation removes candidates with non-positive necessity evidence. General and language-specific head pools are then studied separately.
- **Mechanistic verification (pp. 5–7 and Appendix F):** head-set mean ablation raises NLL relative to layer-matched random head sets. Specific-head validation uses Patchscopes from the residual state at the candidate head's layer; it is not direct decoding of an individual head's output. The base acceptance rule is at least one successful Patchscopes trial. Stricter rules in Appendix F substantially shrink several pools, sometimes to zero.
- **Intervention (pp. 7–8):** multiply selected head outputs by `1 + alpha`, with alpha in {0.25, 0.5, 1.0}. The strongest reported rescue rate is 51.7%. General-head amplification is evaluated on English-correct/target-language-incorrect examples; language-specific-head amplification uses another failure-conditioned population. These are training-free interventions, and the amplification run does not require an English donor activation.
- **Failure account (p. 9):** output magnitudes differ by under 1% between success and failure, so the authors do not attribute failures to missing activation energy. They propose direction misalignment as a possible explanation and leave detailed success/failure direction and in-context bridge-readout tests for future work.
- **Appendix E (pp. 14–15):** evaluates already-correct samples, balanced correct/incorrect mixtures, and MMLU. At the strongest gain, some initially correct questions become wrong; accuracy on the correct-only sets reaches 89.5% for Llama and 87.3% for Qwen. The balanced mixtures rise to 67.0% and 58.3% from 50%. The paper explicitly distinguishes that synthetic balance from a deployment distribution. General-ability evaluation uses 194 MMLU items; the reported maximum decline is 2.1 percentage points.

### Precise comparison

The paper establishes bridge-related causal head sets and successful output amplification for **parametric multilingual reasoning**. It does not decompose attention into the mass assigned to a supplied evidence paragraph and the relation-conditioned distribution within that paragraph. It also does not test whether a linearly decodable paragraph address can guide oracle-free contextual evidence selection. Our contribution should be stated at this factorization and deployment level.

**Safe sentence:** “Kim et al. identify multilingual bridge-routing head sets and recover parametric failures by amplifying their outputs. Their head-set intervention does not distinguish selecting an evidence paragraph from reading relation-relevant content within it.”

**Do not write:** no known-hop controls; no causal interventions; no random-head control; no retention check; amplification needs an English donor; the headline rescue rate is full-test accuracy. Each would be false or misleading.

## 3. Back Attention — Yu et al. (EMNLP 2025)

**Full title:** *Back Attention: Understanding and Enhancing Multi-Hop Reasoning in Large Language Models*.

**Authors:** Zeping Yu, Yonatan Belinkov, Sophia Ananiadou. Proceedings pp. 11257–11272. [Primary record](https://aclanthology.org/2025.emnlp-main.567/).

### What the paper actually does

- **Scientific setting (pp. 1–3):** studies factual chains such as `e1's r1's r2 is`, contrasting the surface ordering used in earlier work. The principal mechanistic task uses parametric facts from TwoHop/Wikidata.
- **Logit flow (pp. 3–5):** traces output-log-probability contributions and interactions between earlier FFN neurons and attention subkeys. Four stages are identified for single-hop prediction: entity subject enrichment, entity attribute extraction, relation subject enrichment, and relation attribute extraction.
- **Dataset detail (pp. 3 and 5):** main successful-case aggregation uses 889 examples over 26 relation types, with type-weighted aggregation and frequency/duplicate filters. The failure analysis uses 568 human–human–human examples. Among candidate chain outcomes, the reported pattern is 52.3% final entity, 42.4% intermediate entity, and 5.3% the direct first-entity/second-relation alternative.
- **Failure explanation (pp. 5–6):** high-layer first-relation features favor the intermediate entity and interfere with final-entity extraction. The model may already have functional computation supporting the final entity, so this is not simply the absence of second-hop knowledge or a universal delayed-first-hop account.
- **Back attention (pp. 6–8):** adds a new trainable module whose queries are taken from a lower layer and whose keys/values use higher-layer hidden states. Its output is fed back into the lower-layer computation in a second pass. The original LLM parameters remain frozen. On the synthetic arithmetic comparison, a one-layer model with this module reaches 93.8% versus 83.8% for one layer and 92.5% for two layers, at 56.7% of the two-layer model's parameter count.
- **Application evidence (pp. 7–8):** improves five reasoning datasets across five LLMs, including TwoHop, StrategyQA, SVAMP, MultiArith and 1DC. Additional mechanistic figures in the appendices reproduce logit-flow patterns for Llama 3.1 8B and Llama 3.2 3B.
- **Efficiency boundary:** comparisons against chain-of-thought include an analytic computation argument; they are not a full latency benchmark of our kind of selection pipeline.

### Precise comparison

This is a mechanism-to-intervention predecessor and should be acknowledged as such. Its diagnosis concerns **which parametric relation contributes logits at a particular stage**, and its repair adds cross-layer feedback capacity. It does not measure the distinction between access to a relevant contextual paragraph and conditional reading within that paragraph.

**Safe sentence:** “Yu et al. identify interference between relation-conditioned logits and repair it with a trainable cross-layer attention module. Their analysis does not locate an evidence-paragraph address bottleneck or separate paragraph access from the content distribution used after access.”

**Do not write:** toy-only experiments; no real-LLM repair; no reasoning improvement; no mechanistic explanation.

## 4. Hopping Too Late — Biran et al. (EMNLP 2024)

**Full title:** *Hopping Too Late: Exploring the Limitations of Large Language Models on Multi-Hop Queries*.

**Authors:** Eden Biran, Daniela Gottesman, Sohee Yang, Mor Geva, Amir Globerson. Proceedings pp. 14113–14130. [Primary record](https://aclanthology.org/2024.emnlp-main.781/).

### What the paper actually does

- **Task/filtering (pp. 2–4):** 82,020 Wikidata-derived compositions, model-specific shortcut removal, and explicit successful-single-hop/failed-composition subsets. Six models span Llama 2, Llama 3 and Pythia. Main analyses sample by bridge-entity type.
- **Locating mechanism (pp. 4–6):** Patchscopes tests all source/target layers, with three generations per probe. Intermediate entities are often recoverable at the end of the subject expression, while final entities are recovered later at the final prompt position. MLP/attention vocabulary projections and attention knockouts support information transfer between those locations.
- **Explaining failure (pp. 6–7):** incorrect cases resolve the intermediate entity later, while propagation/extraction tends to occur earlier. This creates a timing mismatch.
- **Intervention protocol (pp. 7–9):** back-patching places a later hidden representation into an earlier layer of the same prompt. The reported 32–66% rescue counts an example as rescued if **any tested source–target layer pair** succeeds. Page 8 explicitly states this existence criterion. The final-position patch does not require knowing the intermediate entity, but reporting the best successful pair per example still differs from an inference-time location-selection rule.
- **Deployment boundary (p. 10, Limitations):** the authors explicitly state that the current method is not a practical inference method because only some candidate patches succeed. Their future-work discussion calls for selecting source/target layers in advance.
- **Appendices (pp. 12–18):** expanded model-specific probing, knockout, projection and patching results support the same account; they do not introduce a validated fixed patch-selection rule.

### Precise comparison

Use this paper to establish that known constituent facts do not imply successful latent composition. Its timing diagnosis is about **parametric retrieval**, and the back-patching result is a diagnostic existence bound, not deployed accuracy under a fixed selector. Our deployable readout-driven paragraph selection addresses a different decision and should be evaluated on a complete fixed evaluation distribution.

**Safe sentence:** “Biran et al. trace failures to delayed bridge resolution, but their back-patching rescue rate selects a successful layer pair retrospectively for each example. It does not provide a deployable rule for contextual evidence selection.”

**Do not write:** first discovery of correct-single-hop/incorrect-composition failures; their patching requires ground-truth bridge entities in every variant; fixed interventions preserve 100% of correct cases. The last conflates an existential patch search with one fixed procedure.

## 5. Failure Modes / MFAI — Zhang et al. (ACL 2026)

**Full title:** *Failure Modes in Multi-Hop QA: The Weakest Link Effect and the Recognition Bottleneck*.

**Authors:** Meiru Zhang, Zaiqiao Meng, Nigel Collier. Uploaded version: arXiv:2601.12499v2, 21 April 2026, 24 pages. Published record: ACL 2026, pp. 41823–41846. [Primary record](https://aclanthology.org/2026.acl-long.1937/).

### What the paper actually does

- **Controlled context (pp. 3–4):** 18 documents comprise 2 gold and 16 distractors. Positions are grouped into Beginning, Middle, and Tail buckets of six documents. Spread tests vary distance within a bucket; Cross tests place gold documents across buckets. The Multi-Focus Attention Instruction (MFAI) names explicit document indices. Matched instructions name gold documents; unmatched instructions name distracting or partly relevant document combinations, with full construction detailed in Appendix A.
- **Models/data (p. 4):** MuSiQue 1,246 questions with exact-match evaluation and NeoQA 402 with multiple-choice evaluation. Models include Qwen 2.5 7B/14B, Llama 3.1 8B, Ministral 8B, and Qwen 3 8B in thinking/non-thinking modes.
- **Phenomenon (pp. 5–8):** coarse position buckets dominate within-bucket distance effects. Cross-bucket composition tends toward the weaker location's performance. Gold-location instructions improve low-visibility configurations, supporting a recognition bottleneck; thinking improves robustness with greater output-token cost.
- **Critical scope declaration (p. 4, Diagnostic Scope):** the gold document indices are oracle knowledge. MFAI both steers recognition and reduces the effective search space from 18 to 2 documents, so improvements are an upper bound on the recognition contribution rather than a precise recognition/synthesis isolation.
- **Attention evidence (main Figures 5 and 7):** answer-token attention is aggregated over document spans. The illustrated sample prioritizes rescued cases and then jointly correct cases, excluding degraded cases. This is a descriptive visualization of attention allocation; no Q/K/V/O or factorized attention intervention is performed.
- **Appendix expansion:** gold-only and no-document controls; 2Wiki composition/inference subsets; 3-hop/4-hop MuSiQue; 32B models; randomized NeoQA timelines; instruction-order robustness. These are substantive controls and should not be omitted when characterizing scope.

### Precise comparison

This is the closest **contextual evidence recognition** predecessor. The precise gaps are that evidence locations are supplied by an oracle, and the intervention does not identify causal internal attention factors. Our shared-context mass/conditional interventions separate operations that their prompt jointly changes, while our deployed selector obtains candidates from the input and chooses using training-only readout fitting.

**Safe sentence:** “Zhang et al. reveal a position-dependent recognition bottleneck through instructions that name gold documents. Those instructions supply the missing evidence locations and reduce the search space; they do not isolate the internal attention operations that connect evidence access to relation-conditioned reading.”

**Do not write:** no attention analysis; no contextual QA; no strong controls; no higher-hop evidence; oracle gains are deployable retrieval gains.

## 6. Layer-Order Inversion — Liu et al. (EMNLP 2026)

**Full title:** *Layer-Order Inversion: Rethinking Latent Multi-Hop Reasoning in Large Language Models*.

**Authors:** Xukai Liu, Ye Liu, Jipeng Zhang, Yanghai Zhang, Kai Zhang, Qi Liu. Proceedings pp. 41041–41058. [Primary record](https://aclanthology.org/2026.emnlp-main.1802/).

### What the paper actually does

- **Setting (pp. 3–4):** MQuAKE parametric factual queries with two to four hops, GPT-J 6B and Llama 3 8B. Categories distinguish all-single-hops-correct/composition-correct, all-single-hops-correct/composition-incorrect, and missing-single-hop cases. This explicitly includes the known-hop compositional failure population.
- **Probing controls (pp. 4–5, Appendix A):** Patchscopes with global/local semantic-similarity filtering limits spurious early entity mentions. Raw and filtered results are compared. Bridge entities and answers are probed at different relevant token positions.
- **Core observation (pp. 5–6):** later-hop entities can become decodable earlier than bridge entities, especially with more hops. The group-average statement about two-hop ordering must not be confused with no two-hop inversions: Appendix A/Table 5 includes nonzero instance-level two-hop inversions (37.2% in the specified strict-valid subset), increasing for three and four hops.
- **Explanation (pp. 6–8):** probabilistic recall-and-extract: shallow MLPs broadly recall relevant or deeper-hop information, and later attention selectively extracts it. The model need not implement an exact one-hop-per-stage sequence.
- **Causal evidence (pp. 4 and 6–8):** corrupted representations are inserted into a clean run, rather than repairing a corrupted run, to limit disturbance to the normal trajectory. Subject-token and final-token locations, hidden states, MLP output and attention output are compared. Earlier deep-hop recall can supply a causal answer signal, stronger in weaker models/higher-hop settings. Failed-composition cases show insufficient recall and incomplete extraction.
- **Repair boundary (p. 9):** proposed applications to inference or strengthening the useful signal remain future work. Appendix B reinterprets previous knockout/backpatching/CoT observations conceptually; it does not report a newly evaluated repair.

### Precise comparison

This paper prevents an overly literal universal sequential-hop story. Our mechanism should be described as address availability, access and conditional reading, without claiming a necessary universal order of entity decoding across layers. Their diagnosis concerns parameter-recalled factual signals; it does not disentangle address selection and local reading in supplied contexts, and it stops before a tested repair derived from the diagnosis.

**Safe sentence:** “Liu et al. replace strict layerwise hop ordering with probabilistic recall and selective extraction. Their analysis does not separate contextual evidence access from relation-conditioned reading or evaluate an intervention that repairs the diagnosed failures.”

**Do not write:** no causal evidence; no known-hop failure control; all models solve hops sequentially; any earlier answer decodability proves reasoning without intermediate information.

## 7. Two-Hop Reasoning in Context — Guo et al. (arXiv 2025 version read)

**Full title:** *How Do LLMs Perform Two-Hop Reasoning in Context?*

**Authors:** Tianyu Guo, Hanlin Zhu, Ruiqi Zhang, Jiantao Jiao, Song Mei, Michael I. Jordan, Stuart Russell. Uploaded arXiv:2502.13913v2, 28 May 2025, 18 pages. [Primary record](https://arxiv.org/abs/2502.13913).

### What the paper actually does

- **LLM task (pp. 3–5):** synthetic natural-language chains across six relation templates use fictitious entities to limit factual-memory shortcuts, with irrelevant chains as distractors. More than 50,000 examples are generated. Premise order is randomized at the context level.
- **LLM phenomenon (pp. 4–5 and Appendix A):** a pretrained model places approximately uniform probability on ending entities as the number of chains grows. LoRA fine-tuning on 1,000 contexts with one distractor strongly improves target probability and generalizes to more distractors. Additional models include Qwen 2.5 7B, OLMo 7B and Llama 3.1 8B. The uploaded paper therefore contains real-LLM behavioral experiments, not only a toy model.
- **Mechanistic task (pp. 5–8):** reverse-engineers a small three-layer Transformer trained from scratch on symbolic two-hop chains, then focuses on the attention-only form. Entities are individual tokens, chains are disjoint, and the first premise precedes the second premise within each chain. This is a controlled algorithm-learning setting rather than a natural multi-document evidence task.
- **Mechanism (pp. 6–8):** early training yields diffuse/random-guess behavior with a structured cancellation pattern. A later sequential-query circuit first copies a parent to a child representation, then retrieves the bridge from a shared source, then retrieves the endpoint from the shared bridge. A simplified three-parameter model reproduces the transition; Appendix B supplies derivations and supporting dynamical analyses.
- **Evidence boundary:** the modern pretrained LLM experiments establish behavior before/after fine-tuning. They do not causally establish that the exact three-layer circuit explains those LLMs' errors and repairs.

### Precise comparison

Their strength is an explicit constructive mechanism and training dynamics under controlled symbolic conditions. Our scope is a failure of pretrained contextual QA despite verified component success, with causal changes to existing model attention and a deployment procedure on the fixed evaluation panel. The relevant absent test is the extension of the proposed internal circuit to these pretrained large-model computations, not the existence of any large-model experiment.

**Safe sentence:** “Guo et al. reconstruct a sequential-query circuit in a three-layer synthetic Transformer, but do not causally establish that circuit in the pretrained LLMs used for their behavioral experiments.”

**Bibliographic caution:** search surfaced an ICLR 2026 submission under the revised title *How Do Transformers Perform Two-Hop Reasoning in Context?*. The accessible primary result was an anonymous under-review PDF, and acceptance was not verified. Cite the uploaded arXiv version unless the final paper is independently obtained and read; do not silently change the title, venue, or author list.

## 8. Sun et al. (AAAI 2026): exact overlap and distinction

**Full title:** *Bridging the Language Gap: Uncovering and Aligning Shared Circuits for Multi-Hop Reasoning in Multilingual LLMs*.

**Authors:** Chenghao Sun, Zhen Huang, Yonggang Zhang, Xinmei Tian, Xu Shen, Jieping Ye. AAAI 40(39), pp. 33091–33099. DOI 10.1609/aaai.v40i39.40592. [Publisher record](https://ojs.aaai.org/index.php/AAAI/article/view/40592). [Primary institutional bibliographic record](https://researchportal.hkust.edu.hk/en/publications/bridging-the-language-gap-uncovering-and-aligning-shared-circuits/).

This section uses the reference-narrative agent's full reading of the attached nine-page proceedings paper. The separately cited supplement is absent from that upload, so details claimed only to exist in that supplement were not treated as verified.

- **Mechanism:** shared language-agnostic semantic neurons store parametric factual knowledge; attention pathways fail to reach or align that knowledge across languages. Section 2.2 recursively traces attention attribution from a critical head's source tokens through upstream key representations, which the authors call a QK circuit.
- **Intervention:** Section 2.4 tunes the top 40 heads' WQ, WK, WV and WO. This is already targeted head adaptation guided by a mechanistic diagnosis. Our manuscript must not present that high-level strategy as new.
- **Causal controls:** necessity comparisons against random neurons/heads; semantic-neuron recovery after model ablation; interventions on semantic neuron groups to change answers. Language-neuron switches are also discussed, but implementation detail is deferred to the missing supplement.
- **Capability retention:** Table 3 covers multilingual StrategyQA, MMLU, INCLUDE and Belebele. Mean decline for top-40-head tuning is 0.85 percentage points, compared with much larger declines for the listed full-fine-tuning and DPO baselines. Do not characterize this as an absence of retention evaluation or as literally zero loss.
- **Exact gap:** no decomposition of total paragraph mass and normalized within-paragraph attention; no test preserving receiver V/O while changing those two factors independently; no reciprocal contextual-object changes preserving global answer counts. The task is multilingual parametric factual composition, not the reading of supplied contextual evidence paragraphs.

**Safe sentence:** “Sun et al. align critical attention heads that route multilingual queries toward shared semantic neurons. Their analysis does not separate how much attention reaches an evidence paragraph from which relation-conditioned content is read within it.”

## 9. Manuscript-facing draft and verified citation keys

The companion draft at `/workspace/scratch/768b99381773/related_review/related_work_draft.tex` is approximately 495 words (counting each citation command as one author token), in three paragraphs: latent multi-hop composition; reasoning over contextual evidence; circuit-guided intervention. It uses all six papers plus Sun. The complete seven-entry BibTeX file is `/workspace/scratch/768b99381773/related_review/verified_related.bib`.

| Citation key | Verified source and metadata decision |
|---|---|
| `biran2024hopping` | EMNLP 2024, pp. 14113–14130, DOI 10.18653/v1/2024.emnlp-main.781 |
| `yu2025back` | EMNLP 2025, pp. 11257–11272, DOI 10.18653/v1/2025.emnlp-main.567 |
| `liu2026layerorder` | Update existing arXiv entry to EMNLP 2026, pp. 41041–41058. The official export uses DOI **10.18653/2026.emnlp-main.1802**, without `/v1/`; preserve the verified export rather than inventing a normalized DOI. |
| `guo2025twohop` | arXiv:2502.13913, 2025; title and authors match uploaded v2. No verified venue upgrade. |
| `zhang2026failure` | Uploaded arXiv version now has ACL 2026 publication record, pp. 41823–41846, DOI 10.18653/v1/2026.acl-long.1937. |
| `sun2026bridging` | Existing key can be enriched with volume 40, number 39, DOI 10.1609/aaai.v40i39.40592. |
| `kim2026bridge` | EMNLP 2026, pp. 59179–59195. Official export uses DOI **10.18653/2026.emnlp-main.2605**, without `/v1/`. |

## 10. Cross-paper writing checks

- Do not imply that probing alone proves native use. Use probe accuracy to motivate the availability/use gap, and use the interventions for causal claims.
- Do not describe the factorized diagnostic as a deployed method. It uses paired conditions to test a mechanism. The deployable selector has a separate training/test boundary.
- Reserve “causal” for the intervention-supported statement, and avoid interpreting correlation-only document heatmaps as causal counterparts.
- Define **paragraph access** as total target-paragraph attention and **conditional reading** as the normalized distribution over that paragraph. Neither phrase should float as an undefined synonym for all attention computation.
- Keep value/output computation fixed in the factorized diagnostic description. Do not generalize that to the adaptation stage, where Q/K/V/O are initially tuned and a model-specific V/O scope is restored afterward.
- Do not write that our method is purely QK-only across all models unless the final deployed parameter scopes support that statement.
- Do not claim all single hops are always known in every deployment test merely because discovery conditioned on them. Follow the actual population definition in each result.
- Keep prior work's limits task-specific. Absence of contextual paragraph tests is a real gap; saying a parametric study 'cannot reason' or 'has no causal mechanism' is not supported.
