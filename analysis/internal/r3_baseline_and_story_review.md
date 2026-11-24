# Revision 3: comparison evidence and three-stage visual story

Internal scientific/editorial record, 2026-11-24. This file is excluded from the manuscript.

## 1. Repository comparison audit

The 90 `outputs/**/summary.json` files were inspected across commits `6894d18`,
`f171808`, `a00e622`, `f498448`, and `95562c4`. The same 90 paths occur at every
revision and every summary has the same Git object identifier in all five
revisions. No earlier external-baseline result was removed. The exhaustive
history inventory is `r3_history_method_audit.json`.

Application evaluation identifiers are Native, FullFT, and the internal
configurations `native_text`, `head_tuning`, `scoped_body`, `graphfirst`, `final`,
`final_attention`, and `final_metadata`. The remaining conditions are controlled
mechanism interventions: bridge/root/length-matched access calibration,
identity/mass/conditional/both attention edits, selected versus matched random
head knockout, and reciprocal content changes. Searches of code, configuration,
result paths, and historical summaries found no evaluation of Back Attention,
Bridge Routing Heads, Sun et al.'s multilingual head-tuning procedure, ROME,
MEMIT, LoRA, or DPO under the present contextual protocol.

**Consequence:** the paper can report improvement over Native and the recorded
full fine-tuning recipe. It cannot claim SOTA against unmeasured published
methods. An internal selected-head checkpoint cannot be renamed as a published
baseline: its head selection, data, and deployment differ. The revision retains
this distinction through direct factual wording rather than a defensive
manuscript disclaimer.

## 2. Closest published interventions and protocol compatibility

The attached PDFs were checked alongside their official publication records:

| Work | Actual intervention and evaluation | Implication for comparison here |
| --- | --- | --- |
| Yu et al., Back Attention, EMNLP 2025 | Adds trainable cross-layer attention. Its mechanism study uses parametric TwoHop prompts; application evaluation covers 1-Digit-Composite, SVAMP, MultiArith, TwoHop, and StrategyQA. | A meaningful external baseline would require its own implementation/training and evaluation on the same complete-context source panel. Published accuracy is not an interchangeable number for this paper's protocol. |
| Kim et al., Bridge Routing Heads, EMNLP 2026 | Identifies language-general/specific heads on a Wikidata-derived multilingual two-hop population, then scales selected outputs on failures. Evaluates Llama 3.1 70B and Qwen2.5 72B. | The reported rescue denominator and models differ from this paper's contextual failure subsets and 4B/8B models. Its percentage cannot be placed alongside our composed EM. |
| Sun et al., Bridging the Language Gap, AAAI 2026 | Uses attribution-defined critical heads, trains their Q/K/V/O on cross-language inconsistent pairs, compares with FullFT and DPO on XHOPREASON, and studies general capabilities. | Our head adaptation is a component with a different localization objective and dataset, not a reproduction of their complete method. Their scientifically relevant gap is the unmeasured paragraph-mass/conditional-reading interaction. |

Official sources:

- https://aclanthology.org/2025.emnlp-main.567/
- https://github.com/zepingyu0512/back-attention
- https://aclanthology.org/2026.emnlp-main.2605/
- https://github.com/ICT-Convergence-Security-Lab-Chosun/bridge-routing-heads/blob/main/README.md
- https://ojs.aaai.org/index.php/AAAI/article/download/40592/44553

The principal claim remains the measured composition gain of 33.3–39.9 points,
with 9.7/12.0/34.5 points over the recorded full fine-tuning recipe. Mechanistic
comparisons establish what changes the computation and the answer, and are
presented as interventions/ablations rather than separate competing methods.

## 3. Why the original three conceptual figures were appropriate

The original `paper/figures/figure1.png`, `figure2.png`, and `figure3.png` were
visually inspected, with `captions.json` and `figure_sources.json` checked.
Their roles are distinct:

1. **Figure 1 — phenomenon and functional hypothesis.** A real Walter–James–Arsuf
   chain shows correct constituents and failed composition under identical
   evidence, then distinguishes address recovery, evidence access, and local
   content use.
2. **Figure 2 — causal diagnosis.** Paired queries localize heads; discovery
   calibration selects their count; selected/random knockout checks necessity;
   the 2×2 attention intervention separates mass and conditional pattern;
   reciprocal fact exchange checks local evidence dependence.
3. **Figure 3 — mechanism-derived repair.** Selected Q/K/V/O adaptation and fixed
   native-projection restoration define the model; an input title graph and
   trained attention readout select evidence at inference.

The preceding two-conceptual-figure revision removed the independent causal
framework role. That compression made the connection between phenomenon,
mechanism identification, and deployment harder to follow. The original
three-role plan is scientifically justified. Revision 3 restores it, with a
portrait single-column teaser and separate diagnosis/deployment frameworks.

New file/label mapping:

| Role | New formal image | LaTeX label |
| --- | --- | --- |
| Phenomenon + result | `figure1_teaser` | `fig:teaser` |
| Diagnosis framework | `figure2_diagnosis` | `fig:causal_framework` |
| Deployment framework | `figure3_method` | `fig:framework` |

The text uses `rho` for the within-paragraph distribution and describes native
value/output **computations retained in the receiver**; it does not imply that
all downstream activations are fixed. Fixed projection restoration is the
formal public term replacing the implementation-oriented `scoped` label.

## 4. Main / appendix comparison design

- Main contextual table: Native, FullFT, and complete CoReTrace; composed and
  all-three accuracy. Gray Native row, pale-yellow CoReTrace row, genuine maxima.
- Main capability table: paired Native / CoReTrace rows for each model, with
  percentage-point changes computed before rounding. FullFT remains in the
  complete capability table and plot.
- One component-intervention table: four explicit enabled operations and composed
  accuracy for the three models. It preserves all composed component scores once;
  constituent and joint effects remain in the focused text and restoration plot.
- A dedicated restoration plot replaces the nine-method ranking plot. Its
  comparison holds the trained slices and full contexts fixed. On MMLU/GSM8K,
  the selector is inapplicable; head versus final therefore isolates restoration.
- Conditional composition and fixed-native recovery are two panels of one
  Native–CoReTrace table. Denominators and per-run averaging remain explicit.
- Supplemental benchmark, format, scoring, per-run, and cost tables use the
  principal methods. Mechanistic readout and content controls retain functional
  condition names, and their relevant outcomes remain explained in prose.

## 5. Coverage of all 21 previously identified positive result families

| # | Positive family | Revision 3 evidence and location |
| --- | --- | --- |
| 1 | Paired composition failure | 51.2/51.1/48.5%; Introduction, `fig:diagnosis`, `eq:cfr`. |
| 2 | Native address recoverability | Failure subset 72.2/74.6/86.0% and overall 80.3/83.9/91.9%; main diagnosis and `tab:readouts`. |
| 3 | Adapted address information | Overall 90.3/92.6/95.0%, failures 82.9/86.0/92.2%, attention-only 89.6/91.2/94.3%; main + complete readout section/table. |
| 4 | Localized causal heads | Every dose/query necessity curve, complete head maps, layer means/maxima, selected counts; `fig:localization`, `fig:necessity`, `tab:head_selection`. |
| 5 | Address specificity | +4.9/+5.5/+16.0 pp versus root/other controls; main causal text, `fig:causal` d–f and paired-effect table. |
| 6 | Access × reading | +8/+5/+16 pp interactions and both factorial directions; `fig:causal` a–c and `tab:factorial`. |
| 7 | Local content binding | Following 26/35/32→77/76/80, joint 21/29/29→75/72/77; main figure and `tab:content` retain access-only/adaptation controls and persistence. |
| 8 | Complete composed repair | +39.9/+38.0/+33.3 pp; 0.49–0.94% parameters; gains over FullFT; main results and complete core/parameter tables. |
| 9 | Evidence selection | Native filtering +20.3/+18.9/+17.0 pp; adding final selection +6.4/+6.3/+3.4 pp; `app:components` and sole component table. |
| 10 | Ambiguity resolution | Full 92.2/93.2/95.1% bridge accuracy vs35.9; exact outside-subset agreement; +10.4/+5.8/+3.6 pp over restored adaptation; main + ambiguity section. |
| 11 | Constituents and joint behavior | Second-hop gain +14.7/+15.7/+11.6; all-three improvements; restoration first-hop +5.0/+2.4/+27.3; complete core, component prose, restoration figure. |
| 12 | Conditional failure | 51.2/51.1/48.5→11.6/10.8/8.6; each model state's mean numerator/denominator in `tab:conditional_composition` panel a. |
| 13 | Fixed native recovery | Failure repair80.8/80.9/77.8; retention94.6/92.9/95.1; fixed-set87.5/86.8/86.7; panel b and main prose. |
| 14 | Core text / completion | F1 39.48/41.87/49.83→73.41/74.35/76.85;100% final completion; `tab:scoring` and scoring prose. |
| 15 | Answer-form robustness | Permissive alias credit leaves48.1/49.1/47.3% CFR; scoring subsection. |
| 16 | General capabilities | Qwen Hotpot +3.52/+3.90, Qwen8GSM+.83, Llama restorationGSM+31.92/MMLU+.67; main capability table and restoration component paragraph/figure. |
| 17 | Secondary QA quality | Qwen HotpotF1 to65.13/67.98; Llama head→full56.87→64.31, HotpotEM+7.19; component and answer-quality paragraphs, complete table. |
| 18 | GSM formatting | Llama58.61→96.36 validformat, Qwen8native95.98→96.82 and completion98.79→99.39; component and formatting paragraphs. |
| 19 | MMLU generated answers | Micro7.92/67.06/54.54→33.91/69.78/65.11; format and macro gains; `tab:mmlu_generation`; Qwen4head42.24 retained in component prose. |
| 20 | Parameter/workload efficiency |23.59/39.85/75.50M slices;42/42/82reader weights;56.3–57.6%generation-input reduction;103composed readouts; parameter/training/inference tables. |
| 21 | Qualitative chains | Walter→James→Arsuf teaser and JohnCorvinus→MatthiasCorvinus→JohnHunyadi worked example; both preserved. |

The full procedure's first-hop regressions, Llama capability losses, the slightly
higher all-three scores of restoration-only configurations, and attention-only
reader ties remain visible in their appropriate table or text. No value was
changed to manufacture universal dominance.

## 6. Caption and reference consistency

Caption updates were coordinated with the plotting author:

- Diagnosis: two grouped-bar panels, composition outcomes and failure-subset
  readout accuracy.
- Causal: six panels, a–c grouped factorial bars and d–f address-specific
  accuracy-change bars with paired confidence intervals.
- Content: three model panels with Native/CoReTrace following and persistence;
  intermediate controls remain in the complete content table.
- Localization: a–c head maps and d–f measured layer mean/max profiles.
- Necessity: 3×3 query/model panels with selected and matched random knockout.
- Restoration: three metric panels, each grouping the three models, with and
  without fixed restoration; all use paired checkpoints and identical input.
- Capabilities: three task panels grouping Native/FullFT/CoReTrace by model.

A static scan of the eight manuscript TeX sources found zero missing cross-
reference labels, zero missing bibliography keys, and balanced figure/table
float environments. Final PDF-level layout review remains with the root agent.

## 7. Final image-level scientific review

All three generated conceptual figures and all seven numeric PNGs were visually
inspected after the new artwork was installed. The teaser uses the recorded
Walter–James–Arsuf chain; diagnosis uses the correct mass × conditional-pattern
2×2; the deployment diagram trains Q/K/V/O, restores native V/O at fixed prefill
positions, retains adapted decoding, and routes unique/ambiguous/inapplicable
candidates correctly. The diagrams contain no fabricated numerical results.

The final causal plot changed from lines to grouped bars; its caption was
corrected accordingly. The restoration plot's second-panel title was requested
to use “All-three accuracy” because “joint accuracy” elsewhere refers to
original/edited context correctness. Figure 2's caption now explicitly names
direct second-hop queries. The one ablation table was further compressed to
eight configurations × three model composed-accuracy columns. The adjacent
text preserves first-hop and all-three recovery, the small restoration-only
all-three advantages for Qwen3-4B/Llama, and the generated-answer contrast.

The 23-page compiled review PDF contained no unresolved `??`, replacement
characters, `scoped`, `graph-first`, `rather than`, SOTA, AUDIT, TODO, or provenance
strings. Source cross-reference and bibliography checks found zero missing
labels/keys. No manuscript claim asserts that CoReTrace dominates every internal
configuration or establishes an unmeasured global SOTA.
