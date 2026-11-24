# Scientific review of the reconstructed main manuscript

Internal review only. This file must not be included in the manuscript or the
Overleaf input tree. Reviewed `paper/main.tex`, `paper/related_work.tex`, and
`paper/sections/{introduction,method,experiments,conclusion}.tex`, together with
the generated main tables and current Figures 1, 2 and 5. Line references below
refer to the first draft reviewed on 2026-11-24 and may move after editing.
No paper file was modified by this reviewer.

## Overall assessment

The main numerical story is supported by the released results. The draft
correctly separates the canonical test panel from the discovery quadruplets,
uses the appropriate Qwen3-8B native baseline for each experiment, distinguishes
diagnostic annotations from deployment inputs, and describes the nominal seeds
as recorded runs. The ambiguity analysis is particularly strong: it isolates
the exact population on which the reader changes an otherwise identical model
and selection rule.

One definite numerical error needs correction: the content-following gain over
scoped adaptation is **8--13 pp**, not 10--13 pp. Several causal or operational
phrases should be made more precise, as detailed below. The largest scientific
issue is the breadth of the word "gates" in the title, not a failure of the
reported interaction calculation.

## 1. Required or strongly recommended corrections

### R1. Content-following improvement: wrong lower endpoint

**Location:** `sections/experiments.tex`, content-results final paragraph,
original line 57.

The archived `causal_content/summary.json` files give scoped-body following
64/66/72 and final following 77/76/80. The differences are 13/10/8 pp. All three
recorded runs agree exactly on these values.

**Replace with:**

> Compared with scoped adaptation alone, the full repair improves edited-value
> following by 8--13 points and reduces obsolete-answer persistence.

For exact model-resolved prose, use "by 13, 10, and 8 points, respectively."

### R2. "Access gates reasoning" is broader than the intervention establishes

**Locations:** title and running title; Introduction's "access-gated reading";
abstract's "We trace this failure to a gap".

The experiment crosses two mass settings (native and a discovery-fixed target)
with two conditional distributions (native and the corresponding direct-query
donor). This supports a functional interaction. It does not establish a
threshold, a necessary-and-sufficient gate, a monotonic relation with mass, or
the cause of every canonical-test failure. The Qwen3-8B interaction interval
touches zero; the donor and head/mass calibration share discovery sources. The
test-failure readout cohort and the factorial cohort are also different.

"Gating" could be defined explicitly as the measured interaction, but that
definition does not justify a title-level claim about contextual multi-hop
reasoning in general. The direct, positive scientific statement is that access
changes the usefulness of the direct-query conditional pattern.

**Recommended title:**

> When Correct Hops Fail to Compose: Evidence Access Shapes
> Relation-Conditioned Reading

**Alternative preserving the domain in the title:**

> When Correct Hops Fail to Compose: Evidence Access and Conditional Reading
> in Contextual Reasoning

**Abstract replacement for the causal attribution sentence:**

> We identify a dissociation between recoverable evidence location and
> successful answering: a training-fitted linear readout still identifies the
> bridge paragraph in 72.2--86.0\% of these failed compositions.

**Replacement for the end of Introduction's factorial paragraph:**

> Together, these experiments identify an access--reading interaction: the
> usefulness of a direct-hop attention pattern depends on the mass allocated
> to its paragraph.

The rest of the abstract's account of factorization is accurate. The word
"while" connecting factorization and reciprocal exchanges should continue to
describe separate tests, not suggest that the exchange identifies the semantic
content of the transferred attention pattern.

### R3. State the actual donor and receiver positions

**Location:** `sections/method.tex`, factorization paragraph, original line 34.

The donor is **one last-question-token row per selected head**. The same donor
conditional is applied to **every question-prefill row** of the receiver. The
current query-level description omits this material implementation choice.
It could be mistaken for a token-aligned donor transfer or last-row-only
intervention. Context positions, not question positions, are aligned exactly.

**Replace the donor sentence with:**

> For each selected head, $\rho^{\mathrm{dir}}$ is the normalized bridge-paragraph
> attention at the last question token of the corresponding direct-target
> query. We reuse this distribution at every receiver question-prefill row;
> donor and receiver have exactly aligned context tokens.

The current statements about receiving value/output computations, row-total
preservation, and the absence of direct cache edits are correct. Earlier
interventions can still alter later-layer activations and caches through
ordinary computation; "unchanged native values at every later layer" would
not be correct.

### R4. No donor value transfer is not proof of no answer information transfer

**Location:** `sections/experiments.tex`, original line 43.

"The effect cannot be attributed to inserting their answer representations"
is too broad. No donor hidden state or value vector is copied, but attention
can itself encode information about where an answer is. The donor query names
the bridge and relation explicitly. There is no wrong-relation donor,
wrong-entity donor, or matched random conditional control in the released
factorial experiment. Thus the experiment does not identify a standalone
semantic representation of the second relation.

**Replace with:**

> The identity intervention preserves generated token IDs for every receiver.
> Donors supply only normalized attention weights, so the intervention
> reweights receiver values without copying donor hidden states or value
> vectors. The results establish an interaction between access allocation and
> a direct-query conditional pattern; they do not identify a unique anatomical
> sequence.

Optional appendix clarification:

> We use "relation-conditioned" operationally for a pattern elicited by the
> direct query specifying that relation; we do not claim that the transferred
> weights alone constitute its semantic representation.

### R5. Graph-first and full repair match paragraph count, not token budget

**Location:** `sections/experiments.tex`, ambiguity paragraph, original line 72.

Both methods retain the root and one candidate paragraph, and use the same
scoped body. Different candidates have different lengths. Moreover, only the
decoded selector performs the extra prefill. Therefore "not ... a different
evidence budget" is too broad if budget means input tokens or compute.

**Replace the relevant sentence with:**

> The gains of 3.4/3.5/4.0 points arise under the same scoped model and the same
> two-paragraph selection rule, isolating the choice among candidate bridges.

The claim that predictions agree on all other 897 sources is stronger than
mere accuracy equality and is verified: generated token IDs agree exactly in
every recorded run.

### R6. Restoration is a position-dependent computation rule

**Location:** final sentence of `related_work.tex`.

"Constrains the parameter scope retained after adaptation" could describe
permanently discarding parameter updates. The actual documented design restores
native V/O contributions at designated prefill positions; the adapted weights
remain in use for decoding. The Method section already explains this correctly.

**Replace with:**

> Model-specific restoration limits where adapted value/output projections
> affect prefill computation, while decoding retains the adapted weights.

### R7. Keep the content-exchange inference at the level actually controlled

**Location:** `sections/experiments.tex`, original line 48; related-work content
paragraph; conclusion's connection from exchange to mechanism.

The swaps preserve full-input word and character bags and exchange two
same-relation answer surfaces. This is a useful control on global occurrence
counts. It does not exclude every lexical strategy, and it does not show that
the factorial donor's conditional pattern carries value semantics. In the
deployed procedure, selection is recomputed and the two-paragraph input itself
need not preserve the original global bag. The existing paragraph later in
this subsection correctly describes the whole-procedure evaluation.

**Recommended replacement for the first two sentences:**

> Reciprocal object exchanges preserve the complete context's word and
> character counts while changing which value is attached to each bridge
> relation. Paired answer changes therefore cannot be explained by a change
> in global answer frequency.

The joint original-and-edited correctness numbers are more decisive than
edited following alone and should remain next to this statement. A useful
appendix sentence is:

> For methods that select evidence, bag preservation applies before selection;
> the selected contexts may differ because the deployed selector is rerun.

## 2. Additional precision improvements

### P1. State what knockout establishes without attributing every head function

**Location:** `sections/experiments.tex`, original line 27.

Knocking out head outputs can remove functions other than paragraph access.
The separate mass experiment supplies the access-specific intervention. The
current first sentence is fine, but "They therefore support evidence access
shared across query types" overinterprets necessity by itself.

**Suggested replacement:**

> Their causal contribution extends across query types; the selected set is
> not a composition-exclusive circuit.

### P2. Describe scope selection relative to recorded runs

**Location:** `sections/method.tex`, original line 56.

The documentation says scopes were fixed from preceding development and were
not re-optimized in the recorded formal runs. That development could reuse the
fixed panel; no complete development sweep is released. "Not selected by the
present test scores" can be read more strongly than the archive establishes.

**Suggested replacement:**

> The model-specific scopes were fixed during preceding development and were
> not re-optimized in the recorded runs; that development could reuse examples
> from the present panel.

This can be shorter in the main text if the exact limitation appears once in
the appendix and the setup already states fixed-panel reuse.

### P3. Define the primary failure construct operationally

The reported failure rates use completed-answer exact match, not semantic
judgment. Some failed responses contain the correct answer in a longer
sentence. This does not overturn the phenomenon, but a statement treating
every EM failure as an internally incorrect fact composition would overreach.

I independently checked all native constituent-correct failures. The counts
containing any complete normalized official alias are only 14/234, 9/236 and
6/243. Even if every such response is credited, the remaining failure rates on
the fixed constituent-correct populations are **48.1/49.1/47.3%**. This is an
intentionally generous sensitivity check, not a proposed alternative metric:
mentioning an alias is not sufficient evidence that an answer asserts it.

Files: `analysis/audit_answer_forms.py` and
`analysis/internal/answer_form_diagnostics.json`.

**Suggested appendix text:**

> Exact match can reject a response that embeds the correct entity in extra
> wording. Among the 234/236/243 native failures with both constituent answers
> correct, 14/9/6 contain a complete normalized gold alias. Even granting all
> such responses credit leaves failure rates of 48.1/49.1/47.3\% on the original
> constituent-correct populations. This permissive diagnostic is not used for
> model selection or the primary scores.

The Walter/James/Arsuf example is a genuine wrong-entity answer, not this
formatting issue. I independently checked source
`df212d0e0bda11eba7f7acde48001122`: native Llama returns `Avesnes.`, its two
constituents return the correct entities, and final composition returns `Arsuf`.

### P4. Exact feature denominator

The metadata length feature is `log(paragraph_key_count / full_prompt_tokens)`,
not the fraction of context-only tokens or a normalized paragraph prior.
"Log paragraph-length fraction" is acceptable in the main text; define the
full-prompt denominator precisely in the appendix.

### P5. Supplementary diagnostics must actually be supplied

The setup promises text EM/F1 and completion rates. Ensure the appendix includes
their numerical values or a clearly linked supplementary table; merely defining
them would not fulfill the promise. The primary EOS-completed EM itself is
described correctly.

## 3. Number-by-number verification of the main narrative

All values below match independently validated predictions or summaries unless
an error is identified above. Model order is Qwen3-4B / Qwen3-8B / Llama-3.1-8B.

| Claim | Reviewed value | Status/source |
|---|---|---|
| Canonical source splits | 100 / 2,000 / 1,000 | Correct; corpus, split files and loader verification |
| Native constituent-correct population | 457 / 462 / 501 | Correct; native core prediction joins |
| Native composition failures in that population | 234 / 236 / 243 | Correct; rates 51.2 / 51.1 / 48.5% |
| Native full address readout, all test | 80.3 / 83.9 / 91.9% | Correct; independently replayed weights/features |
| Native full address readout, failure subset | 169/234 / 176/236 / 209/243 | Correct; 72.2 / 74.6 / 86.0% |
| Failure-subset metadata readout | 39.7 / 42.4 / 42.8% | Correct |
| Selected heads | 20 / 20 / 40 | Correct; discovery selection records |
| Qwen4 knockout, composed | 26.9 to 7.4%; random 24.4% | Correct; necessity predictions |
| Qwen4 knockout, target hop | 52.9 to 1.1% | Correct |
| Full-test bridge mass effect | +4.9 / +5.5 / +16.0 pp | Correct; causal own native baselines |
| Full-test root mass effect | -4.6 / -5.2 / -7.3 pp | Correct |
| Full-test other-paragraph mass effect | -7.4 / -4.5 / -20.6 pp | Correct |
| Factorial native/mass/pattern/both | 34/41/28/43; 48/52/50/59; 51/64/47/76% | Correct; 100 receivers, 25 quadruplets |
| Factorial interactions | +8 [1,14]; +5 [0,10]; +16 [8,25] pp | Correct; Qwen8 boundary-zero interpretation correct |
| Edited-value following, native to final | 26/35/32 to 77/76/80% | Correct |
| Joint original/edited correctness | 21/29/29 to 75/72/77% | Correct |
| Scoped-to-final edited-value gain | 13 / 10 / 8 pp | Draft range needed correction |
| Native to final composed EM | 26.9/29.2/36.4 to 66.8/67.2/69.7% | Correct; recorded-run means |
| Scoped-only composed EM | 60.4 / 60.9 / 66.3% | Correct |
| Input-graph categories | 822 unique / 103 ambiguous / 75 inapplicable | Correct; independently derived |
| Ambiguous bridge choice, graph-first | 35.9% each | Correct; 37/103 |
| Ambiguous bridge choice, full reader | 92.2 / 93.2 / 95.1% | Correct; 95/96/98 out of 103 |
| Ambiguous answer EM, graph-first to full | 36.9/36.9/38.2 to 70.2/70.9/76.7% | Correct; recorded-run means |
| Outside-ambiguity invariance | 897 sources | Exact generated-token equality verified |
| Metadata-only complete-panel composed EM | 64.0 / 64.6 / 66.7% | Correct |
| Attention-only equals full composed EM | Every recorded run | Correct; does not claim identical predictions |
| Final first hop vs native | 69.8/73.4/66.0 vs 87.2/86.0/85.2% | Correct |
| Llama GSM8K native/head/final | 86.05 / 48.45 / 80.36% | Correct |
| Qwen4/Qwen8 GSM8K final-native | -2.35 / +0.83 pp | Correct |
| Llama Hotpot/MMLU final-native | -2.56 / -1.44 pp | Correct |
| Trainable counts | 23.6M / 39.8M / 75.5M | Correct rounded counts |
| Trainable fraction | 0.59 / 0.49 / 0.94% | Correct; abstract min-max 0.49--0.94% correct |
| Full reader weight counts | 42 / 42 / 82 | Correct; no intercept |
| Extra readout prefill frequency | 10.3% of composed test queries | Correct; does not generalize to all tasks |
| Complete benchmark split sizes | 7,405 / 14,042 / 1,319 | Correct |

The main-result and capability tables agree with the validated source tables,
including displayed rounding and bold winners among the methods shown. Native
is measured once. Recorded-run dispersion is described correctly. The training
protocol, zero-shot benchmark settings, and separate GSM8K numerical metric are
consistent with available code and saved manifests.

## 4. Figure-specific checks

### Figure 1

The real example and repaired answer are correct. The middle panel is a
conceptual population-level account, not a direct measurement of the Walter
example's internal attention. The caption already identifies the illustration
as conceptual. "Limited access" could be read as claiming that mass calibration
always increases native mass; the method correctly notes that some rows decrease.
"Native access" would avoid that inference if an image revision is already
planned. No numerical chart is embedded in the generated figure.

### Figure 2

The main pipeline matches the visible implementation: train-only offline
fitting, unique candidate without readout, ambiguous candidate with readout,
inapplicable graph with unchanged context, same scoped answer model. Q/K boxes
are white while V/O boxes are colored; under the heading "Adapt selected heads"
this could be mistaken for training only V/O. All Q/K/V/O slices are adapted;
the V/O distinction belongs to restoration. If revision is easy, color all four
training boxes uniformly and identify V/O only on the restoration label.
Otherwise a brief caption clarification is sufficient.

### Figure 5

The inspected PNG and `analysis/plot_results.py` currently use grouped bars,
with correct values. The caption does not claim bars and remains valid if the
planned revision uses points/ranges. Avoid adding a "bar height" description.
All adapted-method sample SDs are exactly zero in this content diagnostic; error
caps in the current image therefore do not show nonzero uncertainty. The
caption's mean/sample-SD description is numerically true but a simpler note
that the three recorded runs agree would be clearer. The original horizontal
method labels crowd each other; the planned point layout can resolve this.

## 5. Honest disclosure of unavailable implementation

There is currently no false code-availability promise in the manuscript. Keep
internal filenames, audit logs and missing-module inventories out of its prose.
The author-facing delivery must nevertheless say that the repository snapshot
does not contain `coretrace/models/` or the trained slice files, and that this
prevents independent end-to-end re-execution from the delivered snapshot.

**Suggested Chinese delivery wording:**

> 论文中的数字已逐项对照仓库保存的预测、配置和汇总，并重新生成了表图。
> 原仓库缺少 `coretrace/models/` 源码包以及训练后的切片权重，因此本次完成的
> 是对已有实验记录的独立核验与分析重建，没有从该快照重新执行模型训练或推理。
> 随附代码可以重建本文的表格、数据图和审查结果；若要端到端重跑原实验，需要
> 恢复原始模型实现，并补回权重或重新训练。

Do not say "fully reproducible end-to-end," "all experiments rerun," or imply
that restoration/GQA details were verified against missing source. The current
method can be described from its visible callers, fixed configurations and
records. If the final paper later includes a code-availability statement, it
must accurately describe the released scope until the implementation is restored.

## 6. Review coverage and outstanding scope

The title, abstract, every main-section paragraph, main numeric table entries,
main mechanism equations, and image captions were checked against code and
the completed independent experiment review. External related-work claims
about the cited papers were not independently re-read in this second review;
the reference-review agent owns their primary-source check. This review did
check all statements in Related Work about our own controls and deployment.

The appendix is pending a separate review after it is complete. In that review,
verify exact scope positions/layers, the 43 test-to-train shared entity groups,
source/quadruplet resampling units, the 28.9-versus-29.2 Qwen8 native baselines,
the limited single random-head-set control, and the promised text/format
diagnostics. The main draft already signals these limitations appropriately.
