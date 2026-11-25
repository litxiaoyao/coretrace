# V3: matched causal evidence audit

Source snapshot: `5586f3816903e64334de80e06b74c6d7b1499b18`.

This audit reads archived predictions/features and frozen reader weights. It performs no model inference, refitting, hyperparameter selection, or experiment modification. Exact arrays, receiver/source IDs, and input SHA-256 hashes are in `v3_causal_evidence.json`.

## 1. Locate → Route on the same canonical receivers

The primary fixed subgroup requires both native constituent answers to be correct, the native composed answer in the **access experiment** to be incorrect, and the frozen full reader to recover the gold bridge paragraph. Bridge, root, and length-matched-other interventions retain this exact subgroup.

| Model | Fixed n | Bridge rescue | Root rescue | Other rescue | Mean root mass | Mean bridge mass |
|---|---:|---:|---:|---:|---:|---:|
| qwen3_4b | 169 | 31/169 = 18.34% [12.43, 24.26] | 12/169 = 7.10% [3.55, 11.24] | 7/169 = 4.14% [1.18, 7.69] | 30.30% | 8.24% |
| qwen3_8b | 174 | 27/174 = 15.52% [10.34, 21.26] | 10/174 = 5.75% [2.87, 9.20] | 2/174 = 1.15% [0.00, 2.87] | 32.46% | 8.80% |
| llama3_8b | 209 | 97/209 = 46.41% [39.71, 53.11] | 12/209 = 5.74% [2.87, 9.09] | 7/209 = 3.35% [0.96, 5.74] | 26.35% | 7.65% |

Intervals use 10,000 paired source-bootstrap draws within the fixed observed subgroup, seed 20261125. They condition on the existing reader and subgroup membership. Native mass is averaged over the stored raw per-head paragraph masses, first across selected heads and then across the fixed sources; it is **not** exp(mean log mass).

The Qwen3-8B access baseline has 289/1000 correct versus 292/1000 in principal evaluation: 44 generated token sequences and 13 correctness labels differ. Two originally failed, decoded, constituent-correct sources become correct in the access baseline, changing the relevant denominator from 176 to 174. No extra sources enter that subgroup. The source IDs and all comparison counts are retained in JSON.

Feature archives do not store full prompt text or hashes. IDs, source IDs, prompt token counts, annotated bridge/root positions, bridge title and key count all match 1000/1000. The source code for both captures consumes unchanged frozen canonical composed queries. This is a provenance/alignment check, not a claim that prompt bytes were independently compared.

Interpretation: these are cases with recoverable addresses but failed composition, and routing mass to the relevant paragraph rescues more of them than the controls. The subgroup does **not** establish that decodability or reader confidence predicts greater rescue probability; the unselected decoded/not-decoded groups are retained in JSON for that reason.

## 2. Route × Read: exact rescue sets

All four arms use the same 100 receivers in 25 shared-context discovery quadruplets. A joint-only rescue has native, mass-only and pattern-only incorrect and Both correct. The 2×2 below is restricted to native-wrong/Both-correct receivers.

| Model | Native errors | Both rescues | Joint-only | Mass only already correct | Pattern only already correct | Both single arms correct |
|---|---:|---:|---:|---:|---:|---:|
| qwen3_4b | 66 | 11 | 4 | 7 | 0 | 0 |
| qwen3_8b | 52 | 13 | 5 | 4 | 3 | 1 |
| llama3_8b | 49 | 29 | 13 | 14 | 2 | 0 |

The joint-only fractions among Both rescues are 4/11, 5/13 and 13/29. A compact stacked rescue-count panel makes this individual-level interaction visible while the existing all-receiver four-arm plot preserves aggregate accuracy and paired interaction intervals. Exact losses and all 16 correctness patterns are retained; this rescue-only panel must not be presented as overall net improvement.

Pattern transfer rescue/harm at native mass is 0/6, 4/2 and 3/7; at calibrated mass it is 4/2, 8/1 and 15/3. Four-of-four correct quadruplets change from 0→1, 1→4 and 3→6 under native→Both. Cross-endpoint error classifications are sparse and are not recommended as the main mechanism figure.

## 3. Read: original/edited transitions

All content variants retain 100 original/edited receiver pairs. Final repair follows the edited value in 77/76/80 and is correct on both original and edited versions in 75/72/77. Its selected paragraph is unchanged for all 100 pairs in every model, despite being recomputed. Original-correct counts are 88/84/88, so the conditional edit-following rates are 75/88, 72/84 and 77/88. This describes the complete procedure; it does not isolate a reader-only effect.

The original content native and native-budget records are checked against the factorial native and mass-only records by source, receiver, input token count and generated token sequence. JSON contains exact match counts and complete paired transitions. Null selections in non-selector variants are not evidence of a fixed deployed address.

## 4. Curves that exist, and curves that do not

Knockout summaries contain selected and layer-matched-random head counts 20/40/80, plus native, for direct-first/direct-target/composed queries on 1000 test sources. One random set is used per count; random-set uncertainty cannot be invented.

Separate discovery-only access calibration tested counts 0/20/40/80: Qwen3-4B correct counts [35,36,36,33], Qwen3-8B [45,47,47,45], Llama [45,64,66,58]. These selected the head budget on 100 original-context discovery sources. They are not a paired knockout→restoration experiment and must not be labeled restoration or sufficiency curves. There is no released continuous mass-strength sweep or independently held-out sufficiency/recovery curve.

Factorial event logs additionally retain per-head/per-question-row receiver/result mass fractions and alpha-delta L2. They do not retain full token-conditional attention vectors. Middle/later-layer pre-intervention mass can already reflect earlier interventions; it is not uniformly the untouched native state.

## 5. Recommended figure group

1. **Address routing, full width:** retain all-source destination specificity beside rescue rates on the exact decoded, constituent-correct composition-failure subgroup (n=169/174/209). A concise root/bridge native mass annotation can connect the discovery head-function panel to this same-source test subgroup.
2. **Joint rescue, single column:** display all Both rescues as stacked joint-only versus already rescued by one/both single interventions. Retain all three models and label 4/11, 5/13, 13/29. Keep the existing four-arm aggregate figure nearby.
3. Retain the original/edited content figure as the reading evidence; optionally add the already-recorded stable selected-address fact in its caption. Move answer-table examples to the appendix.

## Reproduction

```bash
python analysis/derive_causal_evidence.py --revision 5586f3816903e64334de80e06b74c6d7b1499b18
```

This script is an evidence derivation, not a second plotting entry. It reads blobs from the specified Git snapshot and writes only the JSON/Markdown audit. All original results and Figures 1–3 remain unchanged.
