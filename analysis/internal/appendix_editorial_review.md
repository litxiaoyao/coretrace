# Appendix editorial, citation and figure review

Internal review of `paper/sections/appendix.tex`, its included tables, and the actual PNG/PDF plotting outputs. The experimental-protocol subfile is being supplied separately by the reference agent. No manuscript files were edited by this review.

## Verdict

The appendix now supplies the scientific details needed to interpret the main results: the fixed source population, development overlap, construction of shared contexts, exactly what mass/pattern interventions change, the limits of the random-head controls, evidence-selection applicability, constituent regressions, and the generation-format explanation for FullFT's GSM8K zero. No additional high-impact scientific inconsistency was found after the corrections below were incorporated during this review.

Two real figure inconsistencies were detected and communicated immediately. Both are **resolved in the latest inspected files**. The final compile should use those regenerated assets.

## High-impact findings and current status

| Finding | Original inconsistency | Latest verification |
|---|---|---|
| Ablation caption described unplotted outcomes | `data_app_ablation` contains only composed-question accuracy, but the original caption claimed both constituents and separately shown all-three accuracy; the lead-in also implied the figure plotted all table outcomes. | **Resolved.** The latest caption says “Component ablations on composed questions,” and directs constituent/joint outcomes to the complete table. The lead-in now correctly identifies composed accuracy. |
| Evidence-filtering values used an inconsistent aggregation in an earlier rendered asset | Initial image labels were 47.1/48.1/53.5, whereas the main table reported three-run means 47.2/48.1/53.4. The original labels corresponded to run 42. | **Resolved.** The latest image and exported aggregated CSV use 47.2333/48.1/53.4333, displayed as 47.2/48.1/53.4. The current plotting helper uses a single reference only for Native and all recorded runs for evidence filtering. |
| Earlier `vig2020investigating` citation lacked a BibTeX entry | Initial appendix text cited Vig and Meng; the 26-entry bibliography contained Meng but not Vig. | **Resolved by citation replacement.** Current text cites `meng2022locating,zhang2024patching`, both valid. All current manuscript citation keys resolve. Optional verified Vig metadata is given below, but adding it is unnecessary. |

## Actual-image checks

All four requested figures were visually inspected, not inferred solely from their filenames or plotting functions.

### `data_app_ablation`

- Three model panels, each plotting **composed accuracy only** across Native, evidence filtering, head tuning, scoped adaptation, graph-first, metadata-only, attention-only, CoReTrace and FullFT.
- Points are recorded-run means; horizontal error bars are sample SD. Native is a single reference. Large FullFT SDs are visible; many other SDs are small.
- Latest labels agree with the corresponding main-results cells, including the corrected evidence-filtering means.
- Full and attention-only readouts coincide in composed EM as stated. There are no constituent or all-three panels, and the revised caption now correctly says so.

### `data_app_capabilities`

- The three panels are HotpotQA answer EM, MMLU option accuracy and GSM8K numeric accuracy.
- The y-axis is **change from each model's native reference in percentage points**, not raw accuracy. The caption correctly identifies this.
- Method colors/legend distinguish head tuning, full fine-tuning and CoReTrace. The plot does not contain a separate scoped-only row; restoration conclusions are supported by the text explaining that the selector is inapplicable on MMLU/GSM8K.
- Error bars describe recorded-run SD. Native is a fixed baseline, so subtracting it does not change those SDs.
- CoReTrace labels agree with the underlying table: Hotpot approximately +3.5/+3.9/−2.6, MMLU −0.2/−0.2/−1.4, GSM8K −2.4/+0.8/−5.7 points.
- FullFT GSM8K bars correspond to zero scored accuracy, hence declines of approximately 89.5/90.0/86.1 points from Native. The caption and surrounding text correctly preserve the formatting/extraction qualification.

### `data_app_necessity`

- Three model panels, with composed/first-hop/second-hop curves; solid lines are selected sets, dashed lines are layer-matched random sets.
- Measured counts are 0/20/40/80, with zero serving as the native reference for this pipeline. The caption states that these are measured points rather than a fitted dose-response curve.
- The selected-count results match the narrative: composed accuracy 7.4/5.5/6.4% at 20/20/40 heads, versus 24.4/27.3/29.4% for the corresponding random controls.
- The one-random-set-per-count limitation, possible overlap with the selected set, and explicit overlap counts are stated. This avoids representing the dashed curves as random-set uncertainty.

### `data_app_localization`

- Full layer/head maps are present: Qwen models show 36 layers and 32 query-head positions; Llama shows 32 layers and 32 positions.
- Outlined cells and panel titles mark 20/20/40 selected heads. Axes use zero-based indices.
- The colorbar denotes the **direct minus composed paragraph-mass difference**, matching the caption and ranking equation.
- The figure does not display measured Q/K/V/O pathways or an exclusive layer-stage assignment. The caption correctly treats it as localization of a query-conditioned attention difference.

## Scientific consistency checks

1. **Canonical versus shared-context populations are separated correctly.** The 300 canonical discovery queries differ from the 250 shared-context prompts. Four composed, four direct second-hop and two distinct first-hop prompts per quadruplet give 250 prompts; 100 three-query links reuse some first-hop prompts. The appendix explains this rather than incorrectly presenting 250 as 100 independent triplets.
2. **Context changes are explicit.** The shared-context construction unions complete original supporting paragraphs and pads to ten, so its native scores need not match canonical discovery scores. The head-count selection table and factorial experiment are properly distinguished.
3. **The content control's domain is precise.** Complete-context character/word multisets are preserved before selection; rerunning a selector can change the retained context. This qualification is essential and correctly included.
4. **The donor-row description now matches code.** The donor uses final-question-token bridge attention, while its normalized pattern is applied to each receiver question-token row. Receiver V/O is preserved locally; downstream activations may change. The appendix correctly avoids treating local V/O preservation as a freeze of all later computation.
5. **The factorial interaction is not presented as an absolute gate.** The appendix states measured operating points and the Qwen3-8B interval touching zero. The causal claim remains a functional interaction.
6. **Graph arithmetic is consistent.** 75 inapplicable + 822 unique + 103 ambiguous = 1,000. Ambiguous counts 86×2, 16×3 and 1×4 sum to 103 cases. The 817 correct unique candidates plus 37 correct first choices in the ambiguous set give 854 correct first candidates. The annotated bridge appears somewhere among candidates in 918 cases.
7. **Bridge-selection counts are stable across runs.** The saved per-run analysis gives full-reader 95/96/98, attention-only 94/97/97, metadata-only 57/57/59, and graph-first 37 for all three recorded runs. The address percentages therefore remain consistent even though the table displays SD only for composed accuracy.
8. **Efficiency denominators are not conflated.** The appendix distinguishes 190 extra prefills over all 3,000 triplet queries from 103 over the 1,000 composed queries. Prompt-token reductions exclude the extra full-context readout passes, and no universal speedup is claimed.

## References and metadata

The current `paper/references.bib` has **26 unique keys**. Citation scanning across the currently available manuscript `.tex` files finds no unresolved key. The existing merged entries remain consistent with the primary-source verification in `reference_verification.md`; the two needed activation-intervention keys are:

- `meng2022locating`: Kevin Meng, David Bau, Alex Andonian, Yonatan Belinkov. *Locating and Editing Factual Associations in GPT*. NeurIPS 2022, volume 35. [Official proceedings](https://proceedings.neurips.cc/paper_files/paper/2022/hash/6f1d43d5a82a37e89b0665b33bf3a182-Abstract-Conference.html).
- `zhang2024patching`: Fred Zhang, Neel Nanda. *Towards Best Practices of Activation Patching in Language Models: Metrics and Methods*. ICLR 2024. [Official proceedings](https://proceedings.iclr.cc/paper_files/paper/2024/hash/06a52a54c8ee03cd86771136bc91eb1f-Abstract-Conference.html).

If Vig is intentionally preferred as the earlier causal-mediation reference, the following optional entry has a verified primary title, author order, venue and volume. It is **not currently needed** and has not been inserted into the manuscript bibliography:

```bibtex
@inproceedings{vig2020investigating,
  title = {Investigating Gender Bias in Language Models Using Causal Mediation Analysis},
  author = {Vig, Jesse and Gehrmann, Sebastian and Belinkov, Yonatan and Qian, Sharon and Nevo, Daniel and Singer, Yaron and Shieber, Stuart},
  booktitle = {Advances in Neural Information Processing Systems},
  volume = {33},
  year = {2020},
  url = {https://proceedings.neurips.cc/paper/2020/hash/92650b2e92217715fe312e6fa7b90d82-Abstract.html}
}
```

[Vig primary proceedings record](https://proceedings.neurips.cc/paper/2020/hash/92650b2e92217715fe312e6fa7b90d82-Abstract.html). This is a method-lineage reference, not a task comparison; neither its title nor its experiments should be described as contextual multi-hop reasoning.

## Final-compile follow-up

Only layout/integration checks remain from this review: confirm the separately supplied protocol subfile resolves its labels; ensure all four inspected images are the latest regenerated versions; and verify appendix table widths and float order in the compiled PDF. No unresolved high-impact scientific or figure-caption problem remains in the inspected appendix file.
