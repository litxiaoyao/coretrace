# V3 figure story: component function and connected interventions

Reviewed source: `5586f3816903e64334de80e06b74c6d7b1499b18`.

Scope: read-only design review of the current eight-page main text and the two user-supplied reference images. This document does not authorize new model inference, change the manuscript, or change the plotting implementation. Figures 1–3 stay byte-for-byte intact. The current Corvinus/Angela answer-based Figure 11 and its case-study subsection move to the appendix.

### Implemented coordination update

After the design review, the root agent authorized four new tasks in the existing `analysis/plot_results.py`. The implemented layout keeps the composition-gap and native-address figures separate while checking the eight-page fit: F4 composition, F5 structure/function, F6 head causality, F7 native address readout, F8 address/routing, F9 the original factorial display, F10 joint rescue, and F11 reciprocal content, in addition to protected Figures 1–3. The combination suggestions below remain layout options rather than instructions to merge those figures.

The new files are `data_main_structure_function` (6.75 × 3.00 in), `data_main_head_causality` (6.75 × 2.85 in), `data_main_address_routing` (6.75 × 2.40 in), and `data_main_joint_rescue` (3.25 × 1.90 in), each as vector PDF and 300-dpi PNG. All new PDF text is at least 6 pt. Reconstruction uses:

```bash
python analysis/plot_results.py --only mechanism_structure mechanism_causality address_routing joint_rescue
```

The completed source audit adds a stronger Locate–Route connection than the initial stratification proposal: among the 169/174/209 access-native failures with correct constituents and a correctly decoded bridge, native selected-head question-row mean mass favors the root (30.30/32.46/26.35%) over the bridge (8.24/8.80/7.65%). Bridge-mass calibration repairs 31/27/97 of these same failures. The implemented address/routing figure therefore has three panels: full-test destination effects, conditional native root/bridge allocation, and conditional destination-specific repair. It does not compare decoded versus undecoded groups. Qwen3-8B's conditional denominator is 174 rather than the original readout figure's 176 because two sources are already correct under the access experiment's native run. Source-joined JSON records preserve this distinction.

New CSV exports and input manifests record every new numerical panel. The pre-existing CSVs and protected Figure 1–3 assets were verified unchanged. No new model inference was run.

## 1. What the reference figures accomplish

The reference structure figure links a population-level component organization to identifiable individual components: set overlap establishes the shared population, while neuron IDs, activation contexts, and projections explain what two members do. The reference causal figure then intervenes on the identified components, compares matched/random components, and measures both destruction and recovery. The essential storytelling unit is **the same components, their observed behavior, and the consequences of changing them**.

For CoReTrace, the available internal unit is an attention head. The appropriate functional portrait is therefore a real head ID and its paragraph-allocation behavior under the paired direct and composed queries. The available records do not contain vocabulary projections or token-level attention traces. A neuron-style semantic card would add unsupported specificity. Actual paragraph-level head portraits are both sufficient for the access question and more faithful to the experiment.

## 2. Missing connections in the current main text

1. **A selected band is not yet a functional description.** Current Figure 5 shows averaged direct-minus-composed scores; Figure 6a repeats their layer distribution. Neither exposes a concrete head ID, the evidence it attends to, or the same head's response to a changed query. The reader sees where scores occur, but cannot inspect the computation that the score summarizes.
2. **The component population loses its identity after localization.** Figure 6b currently presents one model's composed-answer knockout curve. Figures 7–9 then discuss location, mass, and pattern without a visible reminder that the interventions operate on the same frozen head set. Functional continuity should be visible through head IDs/set definitions and consistent labels, not only stated in prose.
3. **Locate and Route are adjacent aggregate statements.** Figure 7 shows an address can be read out on composition failures; Figure 8 shows annotated-bridge mass calibration improves aggregate accuracy. A same-source join can show which address-recoverable failures respond to the mass intervention. This is the useful next analysis. The readout is a diagnostic in that join; the calibration experiment still uses its recorded annotated destination.
4. **Read is summarized by a net contrast.** Figure 9 correctly establishes the mass-by-pattern interaction, but net accuracy obscures whether the same receivers are repaired by pattern transfer at one mass and not the other. Paired changes can show the interaction operating across examples without replacing the aggregate result with selected answers.
5. **The current cases illustrate output behavior rather than component function.** Figure 11 repeats the phenomenon, the four intervention arms, and a value swap. It is useful appendix material, but it cannot fill the missing head-level analysis. Moving it creates space for the raw attention records and paired intervention responses.
6. **Application and mechanism use different procedures.** Reciprocal exchanges test the complete CoReTrace procedure; mass/pattern interventions test native-model computation. Keep the application plot and main result table after the mechanism, with the population/procedure named. Do not draw one continuous sample trajectory across unrelated evaluations.

## 3. Evidence that is actually available

| Analysis | Available record | Safe visual role |
| --- | --- | --- |
| All-head localization and set membership | `outputs/{model}/discovery/ranking.json`, `SELECTION_FROZEN.json`; exported `data_app_head_membership.csv` and `data_app_head_intersections.csv` | Layer/head structure; overlap among the selected set and top direct/composed bridge-attending heads |
| Individual paired head behavior | `outputs/{model}/discovery/capture200.jsonl.gz.part*`: 100 sources × q2/q12, layer × head × ten paragraphs, `all_question_mean` and `last_question`, paragraph titles/root/bridge indices | Real head ID, paired query wording, root/bridge/distractor mass and redistribution; repeated source portraits |
| Native address information | Native readout training/test records; existing native-failure counts | Full/attention/metadata location readouts; same-source address/answer cross-tab |
| Head necessity | `causal_necessity` records; `data_app_necessity.csv` | Frozen selected heads versus layer-matched random knockout at recorded 20/40/80 doses; direct second-hop and composed outcomes |
| Destination specificity | `causal_access` records; `data_fig4_causal_access_controls.csv` | Bridge/root/other calibration; source-matched relation to native address recoverability |
| Pattern-dependent repair | `causal_factorization` four-arm predictions and 25 quadruplet membership | Four-arm outcome rates, interaction intervals, paired repair counts under native/calibrated mass |
| Application | Existing main-result summaries and reciprocal-exchange predictions | Whole-method accuracy and following of edited values |

The raw capture contains q2/q12, not q1 attention and not token attention. The discovery access-calibration curves at 20/40/80 heads are not knockout-then-restoration experiments. They must not be labeled circuit restoration or sufficiency. No extra inference is needed for the proposed derived views.

## 4. Recommended cumulative mechanism

The empirical chain should answer six concrete questions in order:

1. **Which components change when the bridge becomes implicit?** A localized head set, with direct/composed population structure.
2. **What do those components do on an actual query?** The same head reallocates mass among the named root, bridge, and distractors; paired query wording determines the observed change.
3. **Does a wrong composed answer still retain the bridge address?** Population counts and attention-only readout connect constituent success, composition failure, and recoverable location.
4. **Does changing this access computation change the answer?** Selected-head knockout establishes involvement; destination controls establish where additional access is useful; same-source address/repair analysis connects the first two operations.
5. **How does access enable the requested relation to be read?** The four-arm experiment and paired pattern repairs show that the same transferred pattern is useful under calibrated access.
6. **Does this account guide a useful procedure?** The main result table and reciprocal exchanges establish complete repair and sensitivity to changed local evidence.

Locate, Route, and Read remain functional operations carried by the selected computation. The design does not assign three nonoverlapping head sets or claim three separately established layer/time stages.

## 5. Eight-page architecture: six empirical figures with distinct jobs

The recommended main text has the three preserved conceptual figures, **six substantive empirical figures**, and the existing main table. The number is a consequence of the six questions above; several old figures are combined, and the new space is spent on additional recorded analyses rather than extra figure captions. A compact alternative can merge proposed Figures 6–7 if the final typeset manuscript needs space.

### Figure 4 — Structure and function of evidence-access heads

**Role:** directly answer the user's Figure-4-style request. Full-width; roughly 3.0–3.5 inches including panels, plus a concise caption. Replace current Figure 5 and Figure 6a; bring only the useful membership evidence out of the appendix.

Recommended panels:

- **(a) Population structure:** compact all-head maps for the three models, with frozen selected heads marked and one shared gap scale. Existing complete-map data are already available. If maps dominate the width, show two representative models and retain the third in the appendix, as the current paper does.
- **(b) Query-dependent membership:** a compact overlap display for the selected set, top-k direct bridge-attending heads, and top-k composed bridge-attending heads. Prefer a simple membership/count matrix or two overlap fractions over a large decorative UpSet. The selected/direct overlaps are 14/20, 14/20, and 31/40; selected/composed overlaps are 0/20, 1/20, and 10/40. These are descriptive properties of the frozen selection, not independent validation of the selection score.
- **(c–d) Two actual head portraits:** print model, layer, and head ID; the paired direct/composed query; root/bridge paragraph titles; and measured paragraph mass. Each head should appear on more than one source, or have an adjacent across-source distribution, so its claimed role is not inferred from one attractive example. Show the ten paragraphs in fixed input order or summarize root/bridge/distractors with exact totals. For a compact title list, root and bridge are fully named, with other paragraphs indexed consistently.

The cards should expose numerical attention cells, not just an answer and highlighted evidence. Keep the source sample rule explicit: e.g. choose a top frozen head and select the nearest-to-median example among sources with a positive gap, then verify the displayed values against the complete capture. A second portrait can show a distinct observed allocation profile if supported; do not invent a root head and a bridge head just to complete a diagram. Use the audited records to determine the role labels.

Suggested caption headline: **“Identified heads change how the same evidence is addressed.”**

### Figure 5 — From correct hops to recoverable bridge addresses

**Role:** combine current Figure 4 (composition gap) and Figure 7 (address recovery), so the Locate result is conditional on the actual motivating population. Single-column, two compact panels.

- **(a) Population accounting:** for each model, partition the native constituent-correct set into composed correct, composed wrong/address recoverable, and composed wrong/address not recovered. Use counts as well as percentages. Current totals support Qwen3-4B 223/169/65 of 457, Qwen3-8B 226/176/60 of 462, and Llama 258/209/34 of 501. Name the full native readout in this panel.
- **(b) What carries the address:** retain attention-only versus metadata-only/full readout on the same failure subset, or show a compact point comparison if the full bar chart is redundant. Label the different denominator explicitly: 234/236/243 failures.

This is stronger than placing a composition-gap bar and a reader-accuracy bar several paragraphs apart: it makes the fraction of failures with retained location information visible in one view. It does not imply the native model explicitly executes the fitted reader.

Suggested caption headline: **“Composition can fail while the relevant address remains recoverable.”**

### Figure 6 — The localized heads contribute to answering

**Role:** strengthen the existing necessity evidence using the recorded selected/random comparisons, and align it with the functional portrait. Single-column, approximately two compact panels.

- **(a) Dose response:** selected versus layer-matched random knockout on composed queries, using only the measured 0/20/40/80 doses. A main model can supply the dose shape, but the second panel must make all-model replication visible.
- **(b) Query-aligned outcomes at frozen k:** show native, selected knockout, and layer-matched random for direct second-hop and composed queries across all three models. A small matrix or paired-dot display is more efficient than many bars. This tests the same endpoint under explicit/implicit bridge formulations. The first-hop results can remain in the appendix.

Reuse the same head-set name, counts, and model colors as Figure 4. This establishes causal involvement of the identified set in using the supplied endpoint evidence. Do not relabel it as a pure composition module, and do not substitute fixed projection restoration for a missing knockout-recovery experiment.

Suggested caption headline: **“Disrupting the identified heads removes access to the answer computation.”** A less interpretive fallback is **“Selected-head knockout changes direct and composed answers.”**

### Figure 7 — Connect recoverable addresses to targeted routing

**Role:** join Locate and Route at the source level, not just through adjacent headings. Single-column, two panels; extend current Figure 8.

- **(a) Where access is allocated:** preserve the bridge/root/other target comparison across models, including paired intervals. This is the experiment that identifies a useful destination.
- **(b) Same-source repair:** among native composition failures with both constituents correct, cross native address-readout correctness with bridge-mass intervention outcomes. Display numerator/denominator and repair rates for address-recovered and address-not-recovered failures. Use exact source-ID joins and the access experiment's own native baseline. An optional compact transition strip can show the repaired portion of the address-recoverable population.

The second panel's actual conclusion must follow the audited cross-tab. It is an observational stratification of a randomized-free intervention outcome, not an intervention on the reader or a mediation estimate. Its main purpose is to reveal the overlap of the populations supporting Locate and Route. If repair is not enriched among address-recovered failures, state the observed relationship and retain the source accounting; do not force a causal staircase or make the wrong-address group the narrative focus.

Suggested caption headline: **“Targeting the bridge turns recoverable location into useful access.”** Use only if the joined data supports that wording; otherwise **“Address recovery and access repair on the same failed compositions.”**

### Figure 8 — Access determines which receivers benefit from the same pattern

**Role:** the central Route × Read result. Full-width, around 3.0–3.5 inches; upgrade current Figure 9 with per-receiver evidence rather than another selected answer.

- **(a) Four-arm rates:** retain all three models' Native/Mass/Pattern/Both accuracies, preferably in one aligned model × arm matrix to reduce repeated whitespace.
- **(b) Interaction estimates:** retain the three quadruplet-bootstrap interaction estimates and intervals; a compact forest plot is sufficient.
- **(c) Paired pattern repairs:** for each model compare Native→Pattern with Mass→Both on the same 100 receivers. Report the count that becomes correct under the pattern change at native and calibrated access. The audited counts are **0→4, 4→8, and 3→15**. Denominators are 100 receivers for the transition count; if converting to a repair percentage, use the failed receivers in the relevant starting arm and display that denominator.
- **(d) Joint-only rescue:** show **4/5/13** receivers that are wrong under Native, Mass, and Pattern and correct under Both, or put those three counts in a narrow annotation beneath (c). Native failures are 66/52/49. This establishes example-level complementarity and replaces the Angela answer card's role in the main text.

To preserve exact accounting, pattern-change regressions are 6/2/7 at native access and 2/1/3 after calibration; together with repairs they yield the existing net pattern effects −6/+2/−4 and +2/+7/+12. A thin secondary gray component or supporting exported table can carry these counts; the main visual statement should be how calibrated access enables additional repaired receivers. Do not count only repairs and imply they equal the net effect.

Wrong-endpoint categories are sparse in the current audit and should not become a principal semantic panel. The records support a relation-conditioned pattern intervention and receiver-level answer effects, not a token-level map of semantic extraction. Keep native/calibrated access and receiver/direct-query pattern labels identical to the method.

Suggested caption headline: **“The same local pattern repairs more receivers when access is calibrated.”**

### Figure 9 and Table 1 — Mechanism-guided application

**Role:** retain the current reciprocal-value figure as a compact two-panel Figure 9 and retain the main method-comparison table. The table supplies complete method effectiveness, while the figure tests whether predictions respond to the supplied local values. These answer different questions and should not be expanded into a separate reader innovation.

Move the current two-answer case figure and §4.7 to the appendix next to worked evidence chains. Keep the older Calvert reader-selection example there. Main-text prose can refer to the appendix examples once, after the quantitative mechanism.

## 6. Space and editing decisions

| Current main material | V3 disposition | Reason |
| --- | --- | --- |
| Figure 4 composition gap | Merge into new Figure 5 | Population conditioning belongs beside retained address information |
| Figure 5 all-head maps + Figure 6a layer means | New Figure 4; layer mean curve moves to appendix | Removes a second rendering of the same average localization score and creates space for actual head behavior |
| Figure 6b one-model knockout | Expand into new Figure 6 with recorded all-model/query outcomes | Demonstrates the identified components' role, beyond one aggregate curve |
| Figure 7 address readout | New Figure 5 and same-source join in Figure 7 | Connects the motivating population and intervention population |
| Figure 8 destination control | New Figure 7a | Keeps the most useful routing control and adds source-level connection |
| Figure 9 factorial rates/interaction | New Figure 8 with paired receiver responses | Makes Route–Read complementarity visible within receivers |
| Figure 10 reciprocal edits | New Figure 9 | Keeps factual sensitivity as the application endpoint |
| Figure 11 + case subsection | Appendix | Makes room for component-function and intervention evidence |

A practical eight-page budget is to preserve the existing introduction/method backbone, use the page released by Figure 11 and its subsection for the new component portraits plus receiver analyses, and recover additional space by merging the gap/readout figures and moving the repeated layer-average curve. Do not create a dedicated new main-text case-study page or a clear-page command for the replacement analysis. Keep the two wide empirical anchors (component function and pattern interaction) adjacent to their corresponding explanation. The other four empirical figures are compact single-column units; captions explain the variable, unit, and comparison once.

## 7. What the main text should now be able to say

The intended evidence-backed sentence sequence is:

> Paired questions identify a compact set of heads whose allocation to the bridge changes when the bridge is implicit. Individual-head records show this change on the same supplied paragraphs. Although composition fails, the selected heads often retain enough information to recover the bridge address. Intervening on these heads changes the answer, and adding access is useful specifically at the bridge. On the same receivers, calibrated access makes a direct-query reading pattern repair additional answers; the combined intervention also succeeds where neither change alone succeeds. This coupling motivates a targeted repair whose predictions follow changes to local facts.

This progression adds empirical links between operations. It does not rely on renaming existing aggregate plots, increasing figure count, assigning an unsupported third set of heads, or interpreting an answer-only example as an internal mechanism.
