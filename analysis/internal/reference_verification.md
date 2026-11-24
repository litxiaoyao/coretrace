# Verified bibliography and citation placement

Internal reference check, 2026-11-24. `bibliography_verified.bib` merges the existing nine-entry bibliography, the seven fully reviewed related papers (two keys overlap), and twelve additional model/method/data references: **26 distinct keys**. The original `paper/references.bib` has not been overwritten. The short Related Work has no unresolved citation keys. Publication metadata was checked against the primary records below; this metadata verification does not imply full reading of every newly added methods report.

## Required models, data and methods

| Key | Source verified | Where / how to cite |
|---|---|---|
| `yang2025qwen3` | [Qwen3 Technical Report, arXiv:2505.09388](https://arxiv.org/abs/2505.09388); [official repository citation](https://github.com/QwenLM/Qwen3/blob/main/README.md#citation) | First introduction of Qwen3-4B and Qwen3-8B. Both models share this report. Report title, year, author order and arXiv ID verified. |
| `grattafiori2024llama3` | [The Llama 3 Herd of Models, arXiv:2407.21783](https://arxiv.org/abs/2407.21783); [Meta publication record](https://ai.meta.com/research/publications/the-llama-3-herd-of-models/) | First introduction of Llama-3.1-8B-Instruct. The existing configuration names that model, not the original Llama-3-8B checkpoint. The current report author list begins Aaron Grattafiori. |
| `ho2020constructing` | [COLING 2020, pp.6609–6625](https://aclanthology.org/2020.coling-main.580/) | First introduction of 2WikiMultiHopQA and source data. Retained existing key. The project-specific derived query panel still requires its own construction description. |
| `alab2020twikievaluation` | [Official v1.1 evaluator](https://github.com/Alab-NII/2wikimultihop/blob/main/2wikimultihop_evaluate_v1.1.py); [official update notes](https://github.com/Alab-NII/2wikimultihop/blob/main/README.md) | Optional software citation or footnote for alias-aware answer EM/F1. The README dates the v1.1 update to December 2020 and explains `answer_id`, `evidences_id` and `id_aliases.json`. This is separate from the dataset paper. |
| `yang2018hotpotqa` | [EMNLP 2018, pp.2369–2380](https://aclanthology.org/D18-1259/) | First introduction of the HotpotQA retention evaluation. Title, seven authors, venue, pages and DOI verified. |
| `hendrycks2021mmlu` | [ICLR 2021 paper](https://openreview.net/pdf?id=d7KBjmI3GmQ); [arXiv record](https://arxiv.org/abs/2009.03300) | First introduction of MMLU. Cite the 2021 conference version, not 2020 merely because that is the preprint date. |
| `cobbe2021gsm8k` | [Training Verifiers to Solve Math Word Problems, arXiv:2110.14168](https://arxiv.org/abs/2110.14168) | First introduction of GSM8K. Its custom numeric/formatting evaluation should be described separately. Full twelve-author list verified. |
| `kingma2015adam` | [Adam primary record](https://arxiv.org/abs/1412.6980) | Address-readout optimizer: `address_readout.py` calls `torch.optim.Adam`. The primary record explicitly states ICLR 2015; use the conference year rather than preprint year 2014. |
| `loshchilov2019adamw` | [ICLR 2019 paper](https://openreview.net/pdf?id=Bkg6RiCqY7); [arXiv record](https://arxiv.org/abs/1711.05101) | Selected-head / full-parameter training optimizer. The code uses AdamW, with the selected-head recipe setting weight decay to zero. Do not imply a nonzero weight-decay regularizer was used. |
| `vaswani2017attention` | [NeurIPS 2017 official proceedings](https://proceedings.neurips.cc/paper_files/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html) | Cite when first defining attention weights and Q/K/V/O notation, rather than at every equation. |
| `meng2022locating` | [NeurIPS 2022 official proceedings](https://proceedings.neurips.cc/paper_files/paper/2022/hash/6f1d43d5a82a37e89b0665b33bf3a182-Abstract-Conference.html) | Existing factual causal-tracing reference. Suitable for the general activation-intervention lineage; our attention-distribution factorization is project-specific. |
| `zhang2024patching` | [ICLR 2024 official proceedings](https://proceedings.iclr.cc/paper_files/paper/2024/hash/06a52a54c8ee03cd86771136bc91eb1f-Abstract-Conference.html) | Cite the activation-patching methodological context and sensitivity to intervention/metric choices. Authors are **Fred Zhang and Neel Nanda**. This is not a source for our particular mass/conditional factorization. |

## Fully reviewed related work and writing references

| Key | Primary record | Decision |
|---|---|---|
| `biran2024hopping` | [EMNLP 2024](https://aclanthology.org/2024.emnlp-main.781/) | Included in short Related Work; full reading recorded separately. |
| `yu2025back` | [EMNLP 2025](https://aclanthology.org/2025.emnlp-main.567/) | Included in short Related Work. |
| `liu2026layerorder` | [EMNLP 2026](https://aclanthology.org/2026.emnlp-main.1802/) | Replaces existing arXiv bibliographic entry under the same key. Official export gives DOI `10.18653/2026.emnlp-main.1802` without `/v1/`. |
| `guo2025twohop` | [Uploaded-version arXiv record](https://arxiv.org/abs/2502.13913) | Preserve the title *How Do LLMs Perform Two-Hop Reasoning in Context?* and 2025 arXiv citation. A renamed ICLR submission surfaced, but its acceptance/version was not verified. |
| `zhang2026failure` | [ACL 2026](https://aclanthology.org/2026.acl-long.1937/) | Published counterpart of the uploaded arXiv file. Metadata verified; analysis is based on the uploaded version. |
| `kim2026bridge` | [EMNLP 2026](https://aclanthology.org/2026.emnlp-main.2605/) | Official export gives DOI `10.18653/2026.emnlp-main.2605` without `/v1/`. |
| `sun2026bridging` | [AAAI publisher record](https://ojs.aaai.org/index.php/AAAI/article/view/40592); [author-institution record](https://researchportal.hkust.edu.hk/en/publications/bridging-the-language-gap-uncovering-and-aligning-shared-circuits/) | Enrich existing entry with volume 40, issue 39 and DOI. Institutional record confirms title, author order, pp.33091–33099 and DOI when publisher browser verification blocks text access. |
| `sun2025mappings` | [ACL 2025](https://aclanthology.org/2025.acl-long.196/) | Included in short Related Work because its head localization, attention swapping and targeted tuning directly contextualize the intervention strategy. Its task remains demonstration-to-label matching, not contextual factual composition. |
| `qin2026persona` | [ICML 2026 / PMLR 306](https://proceedings.mlr.press/v306/qin26h.html) | Optional citation only. Title, four authors and pp.101666–101687 verified. Useful if discussing diagnostic metrics for distributed behavior or circuit-guided intervention; not a multi-hop baseline. No persona citation is forced into the short Related Work. |

The visual-emotion paper is a writing reference, but not a close scientific predecessor for this task. It is intentionally not added as a generic filler citation.

## Remaining existing entries checked

| Key | Primary source | Verification |
|---|---|---|
| `press2023compositionality` | [Findings of EMNLP 2023](https://aclanthology.org/2023.findings-emnlp.378/) | Title, author identities, year, pp.5687–5711 and DOI verified; useful at the first mention of the compositionality gap. |
| `liu2024lost` | [TACL 2024](https://aclanthology.org/2024.tacl-1.9/) | Title, authors, volume 12, pp.157–173, DOI verified. |
| `geva2023dissecting` | [EMNLP 2023](https://aclanthology.org/2023.emnlp-main.751/) | Title, four authors, pp.12216–12235, DOI verified. |
| `wu2025retrieval` | [ICLR 2025 official proceedings](https://proceedings.iclr.cc/paper_files/paper/2025/hash/9b77f07301b1ef1fe810aae96c12cb7b-Abstract-Conference.html) | Title, five authors, year and venue verified. |
| `yuksekgonul2024attention` | [ICLR 2024 official proceedings](https://proceedings.iclr.cc/paper_files/paper/2024/hash/880ee6e23b6ee548ebcccafe0ef0f513-Abstract-Conference.html) | Title, eight authors, year and venue verified. Merged entry upgrades its URL from arXiv to official proceedings without changing its key. |

## Important application and metadata boundaries

1. **Official normalization versus project protocol.** The official v1.1 evaluator lowercases, removes punctuation and articles, normalizes whitespace and takes the maximum answer score over the accepted aliases. `coretrace/eval/answer_metrics.py` implements these functions. The project's EOS requirement is imposed elsewhere and is **additional to** the official answer scoring. Say “official-alias exact match with an end-of-generation requirement,” define the requirement, and distinguish ungated text F1 where reported. Do not label the complete EOS-gated protocol as the unmodified official metric.
2. **Benchmark citation does not make every evaluation choice standard.** The MMLU same-prefill A/B/C/D probability comparison and GSM8K final-line numeric parsing should be specified as the actual evaluation procedures. HotpotQA's subset/prompt and answer handling likewise need their own description.
3. **Model report version and author order.** Llama report v1 begins Abhimanyu Dubey; current v3 begins Aaron Grattafiori. The merged bibliography uses the current primary record and key `grattafiori2024llama3`. A manuscript retaining “Dubey et al.” must deliberately cite v1 instead; do not combine one version's author order with a different asserted version. Very long Qwen/Llama author lists use standard BibTeX `and others` abbreviation after the first five verified authors.
4. **Causal claims have project-specific support.** General activation-patching citations establish methodological ancestry. They do not validate the project's factorization or independence assumptions; the actual equations, unchanged receiver V/O, paired design and content controls must do that work.
5. **No new novelty from targeted-head tuning alone.** Sun (2026), Sun (2025) and Kim (2026) already contain causal circuit analysis and targeted intervention. The access/conditional-reading separation is the precise project distinction.
6. **Short draft wording.** `related_work_short.tex` contains 326 whitespace-separated tokens when each citation command is counted once; rendered author-year citations put it near 350 words. It includes nine citations (Press, six related works, Sun AAAI and Sun ACL). “Previously unseen,” “untouched test set,” and independent-random-seed claims are absent. The longer scratch draft's previous “previously unseen questions” wording has also been corrected to “ordinary inference inputs.”

## Suggested first-use citation strings

```latex
Qwen3-4B and Qwen3-8B \citep{yang2025qwen3}, and
Llama-3.1-8B-Instruct \citep{grattafiori2024llama3}

2WikiMultiHopQA \citep{ho2020constructing}
HotpotQA \citep{yang2018hotpotqa}
MMLU \citep{hendrycks2021mmlu}
GSM8K \citep{cobbe2021gsm8k}

Adam \citep{kingma2015adam}
AdamW \citep{loshchilov2019adamw}
Transformer attention \citep{vaswani2017attention}
activation interventions \citep{meng2022locating,zhang2024patching}
```
