# Mechanistic narrative references: full reading and project-specific recommendations

Internal working document. All four supplied files were read page by page, including every available appendix, table, caption, and reference section. Eleven pages containing overview/framework/application figures were additionally rendered and visually reviewed. These notes do not establish publication metadata beyond what the supplied PDFs state.

## 1. Exact references and coverage

1. **Guanzheng Qin, Chenghao Sun, Zhining Xie, Xinmei Tian. 2026. _Tracing the Persona Circuit: How Large Language Models Encode and Express Character Traits_.** The supplied PDF prints ICML 2026, Proceedings of the 43rd International Conference on Machine Learning, PMLR 306. File: `icml2026_camera_ready (1).pdf`, 22 pages. Main text pp.1–9, references pp.9–11, appendices A–I pp.12–22. Full supplied file read.
2. **Chengsheng Zhang, Chenghao Sun, Zhining Xie, Xinmei Tian. 2026. _Interpreting and Enhancing Emotional Circuits in Large Vision-Language Models via Cross-Modal Information Flow_.** The supplied PDF prints ICML 2026, PMLR 306. File: `icml2026__Camera_Ready_ (1).pdf`, 20 pages. Main text pp.1–9, references pp.9–12, appendices A–G pp.13–20. Full supplied file read. Running headers retain template wording; do not reproduce this defect.
3. **Chenghao Sun, Zhen Huang, Yonggang Zhang, Xinmei Tian, Xu Shen, Jieping Ye. 2026. _Bridging the Language Gap: Uncovering and Aligning Shared Circuits for Multi-Hop Reasoning in Multilingual LLMs_.** AAAI 2026, volume 40, pp.33091–33099. File: `21890-AAAI26.SunC-NLP(10).pdf`, 9 pages. Main text pp.1–7 (=33091–33097), references pp.8–9. Full supplied file read. **The appendices repeatedly cited by this paper are not included in the uploaded file**, so claims depending only on those appendices cannot be independently checked from this attachment.
4. **Chenghao Sun, Zhen Huang, Yonggang Zhang, Le Lu, Houqiang Li, Xinmei Tian, Xu Shen, Jieping Ye. 2025. _Interpret and Improve In-Context Learning via the Lens of Input-Label Mappings_.** ACL 2025, Volume 1: Long Papers, pp.3873–3895. File: `2025.acl-long.196_Interpret and Improve In-Context Learning via the Lens of Input-Label.pdf`, 23 pages. Main text pp.1–10, references pp.10–12, appendices A–J pp.13–23. Full supplied file read. Public canonical identifier is the filename's ACL Anthology `2025.acl-long.196`; DOI should be verified by the parent before publication.

## 2. What these papers actually do

### Persona circuit

**Scientific question:** How can an abstract trait be encoded and expressed, and why does persona consistency decay during a conversation? The paper first identifies an obstacle particular to its scientific object: a one-token logit metric cannot represent a response-level stylistic tendency. It does not begin with an essay about the standards of mechanistic research.

**Discovery and measurement:** Positive/negative trait prompts share queries and a generation-boundary prefix “As”. The mean hidden-state contrast defines a Latent Persona Vector (Eq.2, p.3). Similarity at an anchor layer defines a differentiable persona proxy and normalized Personality Restoration Score (PRS, Eqs.3–6, pp.3–5). Layerwise steering determines where this metric is behaviorally effective, rather than simply assigning a stage name to every layer.

**Localization:** Head output patching is measured against the anchor-layer persona signal; QK-sensitive attribution traces upstream neurons (Eq.7, p.5). The downstream part instead measures output-distribution KL (Eq.8), which makes the distinction between constructing intent and expressing intent operational.

**Explanation:** Preparation–Establishment–Expression is supported by layerwise interventions, MLP-versus-attention patching, attention entropy, vocabulary projections, and token rank (Figs.3–9, pp.6–7). Persona-related information first appears as fragments, becomes a usable coherent direction in the middle layers, and is translated to lexical output later. The actionable failure is **competition between an emergent persona signal and an assistant-like default direction** (Sec.4.3, p.8). Appendix G makes “assistant-like” an operationally defined direction and compares it against helpful-person/pirate controls; this is stronger than merely observing low persona similarity.

**Causal checks:** Identified versus random head knockout and recovery (Fig.10, p.8); matched assistant-direction suppression controls (Table7, p.17). Appendix D is especially instructive: standard option-token patching knocks out the option behavior but barely affects open-ended persona behavior, whereas PRS-selected heads affect both (Table4, p.15). This directly validates that the bespoke metric measures the intended behavior.

**Application:** PSE injects a canonical mean persona signal into selected heads without parameter updates. Character-LLM and RoleBench assess the target use case; MMLU/GSM8K/CSQA, MT-Bench and long conversations test effects beyond the diagnostic prompt (Tables1–2, Fig.12, pp.8–9; Appendices F,I). Detailed dataset construction, alternative trait contrasts, scales and latency are in appendices.

**Narrative lesson:** The strongest hook is a concrete explanatory reversal: the desired intent is present but does not dominate a competing mode. The method is introduced because that hidden distinction cannot be read from next-token accuracy.

### Emotional circuits

**Scientific question:** How do visual affective cues become an emotional narrative, and why can the output contradict the image? Two obstacles motivate new tools: controlled emotional visual counterfactuals and a continuous latent metric for diffuse expression (pp.1–3).

**Discovery and measurement:** Emotional/neutral image pairs share textual neutral events. Successful emotional pairs yield a global contrast direction (Eqs.4–5). Layerwise steering identifies a pivot layer. A Latent Restoration Metric quantifies restoration of emotion-aligned attention output; head patching then traces upstream MLP neurons through QK (Eqs.6–9, p.4).

**Explanation:** Adapt–Aggregate–Execute is not merely a three-box metaphor. The paper follows distinct V→Q, Q→L, V→L paths, visual entropy, vocabulary projections and position-specific patching (Fig.5, p.6). Its more interesting finding is **sentiment-specific aggregation followed by broadly shared emotional execution** (Fig.6, p.7). Head intersections and upstream/downstream neuron semantics establish that functional division.

**Causal checks:** Saliency motivates the hypothesis; token-group activation patching tests it (Sec.4.2.2). Important-head recovery/knockout versus random controls follow (Fig.7). Neutral-image checks and generation side effects are separated into Appendix F.

**Application:** VEENA couples two operations: VEE changes selected attention routing at specified prefill/decoding stages; ENA amplifies selected MLP activations (Fig.3, Eqs.10–12, pp.4–5). Full MER-UniBench performance, each component, competing methods, selected-component scale, and capability retention are shown separately (Fig.10, Tables1–3, p.8). The joint intervention improves average score 58.1→64.8 on the primary model. General-task results include negative changes; claims of exact orthogonality are stronger than the reported retention tests establish and should not be imitated.

**Narrative lesson:** A useful mechanistic story partitions **operations**, then makes the intervention mirror that partition. “Routing + semantic activation” is justified because two measured operations exist, not because two modules make the system diagram more elaborate.

### Shared multilingual circuits

**Scientific question:** An identical factual multi-hop query succeeds in English but fails in another language: are facts missing or inaccessible? The introduction opens with Anna Faris→USA→Washington versus a wrong Canada→Toronto chain (p.1).

**Localization:** Recursively trace attribution from output logits into neurons and heads, including QK-dependent source-token pathways (Sec.2.2, p.3). Vocabulary projection and maximal-activation examples support LLM-assisted semantic grouping (Fig.1, p.2; Sec.2.3, p.4).

**Explanation:** Shared language-agnostic knowledge neurons and broadly shared attention heads coexist; the same head selects the wrong semantic group in a low-resource language (Figs.2–5). Knowledge representation is available, but the pathway to the relevant knowledge is misaligned. Neuron intervention can redirect the answer.

**Causal checks:** Targeted neuron/head ablation, random controls, and circuit-neuron recovery (Fig.6, p.6). The paper reports recovery above 60% with 500 neurons after broader ablation. Language-versus-knowledge dissociation is described in main text, but its full appendix demonstration is unavailable in the supplied PDF.

**Application:** Fine-tune Q/K/V/O of top-40 heads. A primary task table, cross-lingual transfer matrix, and capability-retention table form a strong progression (Tables1–3, pp.5–7). Row groupings and direct baseline-relative changes make the main advantage visible immediately. Setup is compact: source/translated data, discovery100, train2000, test1000, model and compute; construction details are delegated.

**Novelty implication for CoReTrace:** The claim “knowledge exists but attention routing fails” is already central here. Reusing that claim would make CoReTrace look like a contextual adaptation. A sharp difference is to separate **paragraph access mass** from **relation-conditioned reading within that paragraph**, and causally test their interaction under supplied context. This paper does not perform that factorized contextual-access experiment or reciprocal contextual-value swaps preserving answer occurrence.

### Input-label mappings

**Scientific question:** What are input-label mappings inside a model, where do they operate, and how are they used? Semantically unrelated labels isolate mapping behavior from pretrained label meaning (pp.1–3).

**Discovery:** Hidden states do not transparently show task semantics, but their middle-layer principal components do; PC-direction control shifts label logits (Fig.4, p.6). The move from the apparent absence of semantic evidence to its structured presence gives the paper a discovery rather than a catalogue of components.

**Localization:** Principal Component Lens finds a task-related direction; PC Patching perturbs that direction to create representation-level counterfactuals, then measures head-specific effects (Fig.3, Algorithms1–2, pp.4–5). This method is motivated by the difficulty of constructing text that turns off ICL while otherwise preserving the task.

**Explanation and intervention checks:** Important heads attend demonstration labels matching the new query. Swapping their attention across different labels degrades accuracy sharply, while random swaps do not (Fig.5, p.7). Earlier input→label interactions establish the mappings; late layers refine/decode the matched output (Sec.6.1 and Appendix B). The attention swap directly tests the proposed function beyond head necessity.

**Application:** Pinpoint SFT updates selected heads and compares with Full SFT and random-head SFT. The main table places task gains, tuned parameter count, and MMLU retention in one view (Table1, p.8). Additional models, datasets, structured list transformations, representation filtering, and task-specific details broaden the result without obscuring the main mapping story.

**Novelty implication for CoReTrace:** This work localizes and swaps class-label matching in demonstration-based ICL. It does not explain the failure to compose two individually answerable supplied facts or separate contextual paragraph access from within-paragraph relation reading.

## 3. The shared narrative design worth transferring

1. **Start from a contradiction the reader can understand immediately.** Correct isolated facts versus wrong composed answer is stronger than a generic claim that LLMs are opaque.
2. **Name the hidden distinction that resolves it.** Recoverable address, amount of access, and local content use are different measurable operations. Avoid merely renaming shallow/middle/deep layers.
3. **Motivate any custom dataset or metric by the confound it removes.** Three queries on the same context distinguish constituent answerability from composition; paired attention contrasts reduce context differences; factorization separates total paragraph allocation from normalized local reading; reciprocal edits distinguish factual content use from answer-string salience.
4. **Use observations to pose a specific mechanism, then interventions to test it.** A head heatmap is a localization result, not the explanatory conclusion. The mass×conditional factorial contrast is the mechanistic center.
5. **Make repair instantiate the diagnosed operation.** The train-only attention readout and input title graph expose relevant original paragraphs; a scoped trained body uses them. State exactly which diagnostic information disappears at deployment.
6. **Close the loop with outcomes on the target behavior and collateral capability.** Report final composition, all-three correctness, fixed native-conditioned subsets, same-body selector comparisons, and actual retention changes. Retention does not prove anatomical orthogonality.
7. **Treat appendices as complete support, not storage bins.** Every appendix section has a clear question, a method or control, a figure/table, and a short finding. No empty sections or internal experimental labels.

## 4. Proposed project story (conditioned on root-verified evidence)

### Central claim

**Individually answerable hops can fail to compose because usable evidence access is incomplete: the bridge address remains recoverable, but total access and relation-conditioned reading interact. This functional diagnosis yields a label-free evidence-selection and scoped-head repair.**

“Access-gated content reading” is an effective compact name. Its empirical meaning must be stated: the estimated effect of transplanting within-paragraph attention changes when paragraph mass is also repaired. This is an operational interaction, not proof of an exclusive anatomically sequential circuit.

### Suggested title directions

- **When Correct Hops Fail to Compose: Tracing Evidence Access and Relation-Conditioned Reading**
- **CoReTrace: Tracing and Repairing Evidence Access in Contextual Multi-Hop Reasoning**
- **Recovering Composition through Evidence Access and Relation-Conditioned Reading**

The first presents the scientific question and mechanism most clearly. The name CoReTrace can be introduced as the framework in the abstract/method.

### Intro sequence

Paragraph 1: Show the same-context two-hop paradox. Explicitly supplying all facts does not ensure their composition, even when both direct questions are answered correctly. End with the scientific question: what prevents the composed query from using evidence the model can use separately?

Paragraph 2: Locate the missing scientific distinction in prior work. Timing/ordering accounts and shared knowledge-routing accounts do not disentangle reaching an evidence paragraph from selecting the relation-conditioned content inside it. Avoid a long methodological manifesto.

Paragraph 3: State the core discovery before listing machinery: bridge-address information is recoverable, yet the contribution of within-paragraph reading depends on access allocation. On the controlled diagnostic panel, conditional-pattern transfer alone yields 28/50/47% from native34/48/51%; combining it with repaired mass yields43/59/76%. State the sample scope in the experimental section, not as a universal mechanism.

Paragraph 4: Explain how this conclusion is established: matched queries, readout, oracle-address controls, mass×conditional factorization, reciprocal content edits. The donor supplies normalized attention only; neither answer residual nor value/output vectors are transferred. This detail makes the causal intervention intelligible.

Paragraph 5: Derive the application. A train-only attention readout selects evidence through the input title graph; only original text enters the final prompt, and scoped head tuning supplies the body. No support/answer labels enter selection at inference. Summarize verified final composed gains and report retention accurately.

Paragraph 6: Three contributions: an operational diagnosis of contextual composition failure; controlled causal evidence for access–reading interaction plus content following; a practical label-free repair with component comparisons and full capability evaluation.

### Main experiment sequence

1. **The composition gap persists after constituent success.** Main phenomenon figure/table uses the same fixed test panel and clearly distinguishes unconditional composition accuracy, conditioned gap, all-three correctness.
2. **The bridge address is recoverable but underused.** Pair the localization evidence with readout/control evidence. Attention-only matches the full reader's final composed accuracy across all three models, so this positive result supports the explanation and should appear at least once in main text. Equal accuracy does not establish identical generated outputs or per-source behavior.
3. **Access allocation changes the effect of local reading.** The central factorization figure uses native/mass-only/conditional-only/both, with paired cluster intervals for the interaction: +8 pp [1,14], +5 pp [0,10], +16 pp [8,25] as supplied by root. Qwen8 lower bound is zero; avoid saying all three interactions are strictly significant. Diagnostic panels overlap head/tau selection; describe that once clearly.
4. **Repaired predictions follow relational content.** Reciprocal swaps preserve global answer occurrences and require new-value following, distinguishing content use from bag-of-answer cues. Keep no-ops explicitly in protocol and denominators.
5. **The mechanism supports a usable repair.** Main task table gives native/head-tuned/final/FullFT and a compact same-body selector comparison. Final composed root-verified scores: 66.8/67.2/69.7 from26.9/29.2/36.4. Same-body graph-first:63.37/63.7/65.73. Show gains with source-paired uncertainty, and dispersion across recorded runs separately. The audit subsequently found repeated selected-head training traces across seed labels; such dispersion does not establish stochastic-training robustness.
6. **The scope of intervention matters for retention.** Report actual side effects. Llama GSM8K48.45→80.36 with rollback still sits below native86.05. “Preserves general capabilities without loss” is not supported; scoped repair recovers much of the lost capability while improving composition.

### Main/appendix allocation

Keep the causal factorial test and reciprocal content intervention in main text; they carry the novelty. A head heatmap alone can be compressed or moved if needed. Keep at least a concise retention table and component comparison in main. Put detailed splits, all seed rows, native-conditioned breakdowns, reader coefficients/features, random-control overlap, prompt/decoding details, EOS and numeric evaluation conventions, model-specific rollback scopes, head/tau selection, inference batching/cost tables and extra worked examples in appendices. FullFT settings must remain reproducible and default-recipe scope explicit.

## 5. Figure and table design

### Figure 1: discovery teaser

A conceptual three-part figure with one running factual example:

- **Individually answerable**: the same context supports each direct hop, but the composed query misses the correct endpoint.
- **Mechanistic bottleneck**: the relevant bridge paragraph has an address indicator, a narrow access channel, and several relation-specific values; enlarging access and reading the relevant relation jointly resolves the information-use bottleneck.
- **Mechanism-guided repair**: select original evidence through the learned readout and input graph, then answer with the scoped body. A small verified score callout can summarize the application, while exact empirical charts remain Python-rendered elsewhere.

Color semantic roles consistently: navy/question, teal/relevant evidence and successful reading, orange/intervention, muted grey/distractors. The figure should not imply that the diagnostic annotated-address intervention is the deployed method. The caption should explicitly distinguish conceptual mechanism from measured results.

### Figure 2: actual method framework

Use clearly separated **Diagnosis** and **Deployment** routes.

Diagnosis: same-context direct and composed queries → paragraph attention contrast → selected heads and address recoverability → controlled mass/conditional/content interventions. Annotated support addresses enter only this route.

Deployment: question + original context → title graph candidates + attention features → train-only linear readout → root/bridge original paragraphs → scoped head-tuned model → generated answer.

The learned components should be marked at training time, and the frozen selector/model state at inference made clear. No answer label, gold support marker, donor residual, or oracle arrow should enter the deployment route. If training and rollback are shown, name the exact frozen/updated projections from code, not a generic “adapter.”

### Numerical figure policy

- Plot the factorization as paired two-line interaction plots (x=mass unchanged/repaired; line=receiver/donor conditional pattern), one panel per model. This makes the interaction visible more directly than four isolated bars. Provide native and identity equivalence in caption or appendix.
- Couple reciprocal swap original accuracy, new-value following and stale-answer persistence into a compact panel; do not collapse the three into a misleading single score.
- Plot accuracy change versus capability change only when uncertainty and actual metric meanings stay readable. Avoid a single average combining Hotpot F1, MMLU probability accuracy and GSM numeric accuracy.
- Use two-level tables: row group for Native, training-only baselines, deployed repair; columns pair task accuracy and change. Round consistently (one decimal for accuracy, two only where meaningful). Show mean±SD and paired CIs as different quantities.

## 6. Direct related-work language supported by these four sources

Potential source-grounded phrasing (to integrate with other reviewed related papers):

> Sun et al. (2026) attribute multilingual factual inconsistency to misaligned attention pathways over shared semantic knowledge. Their analysis does not separate the amount of attention allocated to an evidence paragraph from the relation-conditioned distribution inside it. We isolate these two operations in contextual composition and test their interaction while holding the context and value representations fixed.

> Sun et al. (2025) identify input-label mappings and the heads that apply them in demonstration-based classification. Their label-swapping experiments concern matching demonstrations to class labels; they do not test why a model fails to compose two supplied facts that it can answer individually. Our interventions operate on bridge evidence and the contextual relation values needed for composition.

The persona and visual-emotion papers are most useful as narrative/methodological references, not as central multi-hop baselines. If cited in Related Work, one short general sentence can situate operation-directed intervention; forcing them into a task-comparison paragraph would distract from the scientific gap.

## 7. Practices to learn without reproducing reference defects

The PDFs contain instructive design choices but are not style authorities in every detail. Avoid their occasional unsupported universal/orthogonality language, percentage-versus-percentage-point ambiguity, unexplained abbreviations, overly dense example figures, caption/panel inconsistencies, and template running headers. Do not imitate “safe alignment,” “root cause,” “necessary and sufficient” or “no latency” unless the actual project experiments justify those exact claims. A confident paper can state a precise positive result and its measured setting directly without apologetic framing.
