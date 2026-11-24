# Positive-result coverage after the presentation revision

Internal review for the 2026-11-24 revision. This file is excluded from the manuscript.
All scientific values below are taken from existing recorded experiments; this revision
adds analysis and presentation, without new model training.

## Coverage by experiment family

| Experiment family | Positive evidence carried into the paper | Manuscript location |
| --- | --- | --- |
| Paired composition phenomenon | 51.2/51.1/48.5% composition failures after two correct constituents | Introduction; Fig.3; Eq.1 |
| Native address information | 72.2/74.6/86.0% correct bridge addresses within native failures; native overall 80.3/83.9/91.9% | Fig.3; Table readout diagnostics |
| Adapted address information | Overall full readout 90.3/92.6/95.0%; failure subset 82.9/86.0/92.2%; attention-only overall 89.6/91.2/94.3% | Main diagnosis; appendix readout section and complete table |
| Localized heads | Selected knockout effects exceed layer-matched random effects; all doses, all three query types, all layer/head scores and chosen counts | Main diagnosis; appendix localization/necessity figures and head-count table |
| Address specificity | Bridge calibration +4.9/+5.5/+16.0 pp; root/other controls measured side by side | Fig.4d; paired-effect table |
| Access × reading | Interaction +8/+5/+16 pp; pattern effects change -6/+2/-4 to +2/+7/+12; mass effects change +7/+4/+13 to +15/+9/+29 | Fig.4a–c; main causal section; complete factorial contrast table |
| Local content binding | Following 26/35/32→77/76/80%; joint 21/29/29→75/72/77%; mass-only and scoped intermediate results; obsolete-answer persistence | Fig.5; complete content table and appendix discussion |
| Composed repair | Native 26.9/29.2/36.4→66.8/67.2/69.7%; parameter fraction 0.49–0.94%; +9.67/+12.03/+34.50 pp over fixed FullFT recipe | Main Table1; complete core and parameter tables |
| Evidence selection | Native filtering gains +20.3/+18.9/+17.0 pp; final/scoped +6.4/+6.3/+3.4 pp; graph-first, metadata-only, attention-only ablations | Main application; appendix component figure and complete table |
| Ambiguity resolution | Full bridge accuracy 92.2/93.2/95.1% vs 35.9%; composed 70.2/70.9/76.7% vs graph-first 36.9/36.9/38.2%; +10.4/+5.8/+3.6 pp over scoped body on same103 | Main application; complete ambiguity table |
| Constituent and joint behavior | Second-hop gains +14.7/+15.7/+11.6 pp; all-three 22.3/22.6/25.8→41.3/45.4/42.3%; scoped restoration first-hop +5.0/+2.4/+27.3 over head tuning | Main application; complete triplet table; appendix component discussion |
| Conditional composition rate | Method-conditioned CFR 51.2/51.1/48.5→11.6/10.8/8.6%; every method's numerator and denominator included | New `tab:conditional_composition` |
| Fixed native error recovery | 80.8/80.9/77.8% failures repaired; 94.6/92.9/95.1% native successes retained; fixed-set accuracy 87.5/86.8/86.7% | Main application summary; new `tab:fixed_population` and appendix discussion |
| Core text and completion | Text F1 39.48/41.87/49.83→73.41/74.35/76.85%; completed/textEM same; 100% final completion; all9methods | Expanded `tab:scoring`; appendix scoring prose |
| Answer-form sensitivity | Even crediting all14/9/6 alias-containing failures leaves CFR48.1/49.1/47.3% | Appendix scoring |
| General capabilities | Qwen Hotpot +3.52/+3.90pp; Qwen8 GSM +0.83pp; Llama restoration GSM +31.92pp, Hotpot +7.19pp, MMLU +0.67pp over head tuning | Main Table2; full capability table and appendix figure |
| Secondary QA quality | Qwen Hotpot F1 +4.97/+4.69pp; Llama head-tuning→final F1 +7.44pp; near100% completion | New `tab:secondary_qa`; appendix answer-quality subsection |
| GSM output format | Llama valid-format58.61→96.36% under restoration; Qwen8native95.98→96.82%; completion98.79→99.39% | New `tab:secondary_qa`; appendix mathematical-format paragraph |
| MMLU generated output | Generated-lettermicro7.92/67.06/54.54→33.91/69.78/65.11%; macro and format improvements; headtuning Qwen4bestgen42.24% reported | New `tab:mmlu_generation`; appendix multiple-choice paragraph |
| Parameter and workload efficiency | Full-rank slices23.59/39.85/75.50M; reader42/42/82 weights; generationinput56.3–57.6% reduction;103/1000extra composedprefills; all observed training/inference timing records | Main cost paragraph; appendix parameter/training/inference tables |
| Qualitative chains | Walter→James→Arsuf and JohnCorvinus→MatthiasCorvinus→JohnHunyadi; allthree models corrected second case | Fig.1; appendix workedexamples |

## Source families for newly expanded coverage

- `outputs/{model}/seed{42,43,44}/evaluation/core/summary.json`:
  `summary`, `all3`, `conditional_composition`, `native_conditioned_composition`.
- `outputs/{model}/seed{42,43,44}/evaluation/{hotpot,mmlu,gsm8k}/summary.json`:
  primary accuracy, text F1, EOS completion, format failure, generated MMLU letters,
  and subject-macro scoring.
- Full-parameter counterparts are under `evaluation_fullft/` and use method
  identifier `FullFT`.
- Fixed-population means were checked against
  `analysis/internal/fixed_population_and_graph_analysis.json`.
- Tables are generated from their source records by `analysis/build_tables.py`;
  no numeric values were typed into the generated table files by the prose editor.

## Editorial decisions

- Removed all rhetorical scope/defensive passages and contrastive disclaimers
  from the manuscript. Remaining `scoped adaptation` is the operational method
  term, with its restoration positions defined in the method and appendix.
- Repository package/weight availability never appeared in the manuscript and
  remains excluded.
- Dataset provenance, source reuse, training order, nominal seeds, batches,
  denominator definitions, and the literal FullFT format-failure outcomes remain
  concise factual protocol entries.
- All variants and numerical declines remain visible in the complete tables;
  the narrative now explains the positive experimental findings directly.
- The four new appendix tables include independent labels, captions, and
  explanatory prose; no empty appendix sections were introduced.
