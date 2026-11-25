# V3 structure and functional attention evidence

Frozen source commit: `5586f3816903e64334de80e06b74c6d7b1499b18`.

This derivation reads existing records only. It reconstructs 200 captures per model (100 paired canonical discovery sources) and checks every released head-ranking mean and gap to absolute error below 1e-12.

## Figure-ready findings

All values below are percentages of total attention, averaged first across the selected heads and then across the 100 sources. The main metric averages all question-token rows. The JSON also retains final-question-token measurements separately.

| Model | q12 root | q12 bridge | q2 root | q2 bridge | q2 bridge / q12 root preference switch |
|---|---:|---:|---:|---:|---:|
| qwen3_4b | 29.413 | 10.721 | 7.825 | 33.519 | 98/100 |
| qwen3_8b | 30.402 | 12.139 | 9.329 | 34.132 | 94/100 |
| llama3_8b | 24.351 | 10.909 | 6.851 | 30.045 | 89/100 |

Every model has increased selected-set mean root mass under q12 on all 100 paired sources. All 20/20/40 selected heads also show this direction after averaging sources. The JSON includes paired source distributions and per-head root/bridge/distractor arrays, not only aggregate means.

The random comparison is the exact recorded layer-matched head set used for the selected-count necessity experiment. Its head IDs, layer maps, seeds, and selected-set overlaps are preserved. Existing head-intersection counts are independently reconstructed from the frozen ranking and selection.

## Representative heads and actual contexts

### qwen3_4b: layer 23, head 10 (zero-based)

- Source `6a0c11720bdb11eba7f7acde48001122`: **Linda Salzman Sagan → Carl Sagan**.
  q12: Where does Linda Salzman Sagan's husband work at?
  q2: According to the evidence, for Carl Sagan, what is the value of the relation "employer"?
  This head's q12 root/bridge mass is 56.530%/15.776%; q2 root/bridge mass is 6.114%/54.010%.
  Same-canonical-context recorded outputs: Native `Carl Sagan` → selected-set mass calibration `Cornell University`.
- Source `510b4f140bd911eba7f7acde48001122`: **At the Heart of Gold: Inside the USA Gymnastics Scandal → Erin Lee Carr**.
  q12: Who is the father of the director of film At The Heart Of Gold: Inside The Usa Gymnastics Scandal?
  q2: Who is the father of Erin Lee Carr?
  This head's q12 root/bridge mass is 58.198%/9.892%; q2 root/bridge mass is 13.644%/37.244%.
  Same-canonical-context recorded outputs: Native `David Ulich` → selected-set mass calibration `David Carr`.

### qwen3_8b: layer 23, head 10 (zero-based)

- Source `8b6f0e800bdd11eba7f7acde48001122`: **Sabine Thalbach → Benno Besson**.
  q12: Where was the place of death of Sabine Thalbach's husband?
  q2: Where did Benno Besson die?
  This head's q12 root/bridge mass is 36.411%/5.301%; q2 root/bridge mass is 15.486%/51.020%.
  Same-canonical-context recorded outputs: Native `Beaulieu-sur-Loire` → selected-set mass calibration `Berlin, Germany`.
- Source `6a0c11720bdb11eba7f7acde48001122`: **Linda Salzman Sagan → Carl Sagan**.
  q12: Where does Linda Salzman Sagan's husband work at?
  q2: According to the evidence, for Carl Sagan, what is the value of the relation "employer"?
  This head's q12 root/bridge mass is 61.613%/16.913%; q2 root/bridge mass is 12.090%/39.360%.
  Same-canonical-context recorded outputs: Native `Carl Sagan` → selected-set mass calibration `Cornell University`.

### llama3_8b: layer 13, head 18 (zero-based)

- Source `d3c5124a0bda11eba7f7acde48001122`: **Blame Canada → Mary Kay Bergman**.
  q12: Where was the performer of song Blame Canada born?
  q2: Where was Mary Kay Bergman born?
  This head's q12 root/bridge mass is 43.118%/1.254%; q2 root/bridge mass is 4.303%/64.389%.
  Same-canonical-context recorded outputs: Native `Colorado` → selected-set mass calibration `Los Angeles.`.
- Source `3ab846860bde11eba7f7acde48001122`: **Camille → William Axt**.
  q12: Where did the composer of film Camille (1926 Feature Film) die?
  q2: Where did William Axt die?
  This head's q12 root/bridge mass is 51.070%/12.613%; q2 root/bridge mass is 2.062%/69.328%.
  Same-canonical-context recorded outputs: Native `There is no information about the death of the composer of the film Camille (1926 Feature Film).` → selected-set mass calibration `Ukiah, California.`.

## Figure schema and claim wording

- Structure panel: `models[model].exact_intersections` and `headsets` contain selected/direct-top-K/composed-top-K masks and actual head IDs.
- Population functional panel: `aggregate_profiles[selected|random_layer_matched].metrics.all_question_mean` contains means, all 100 paired source arrays, and descriptive quantiles. `selected_and_random_source_profiles` supplies head × source arrays.
- Concrete functional panels: `representative_candidates` contains exact questions, all ten paragraph titles and original sentences, support facts, capture/prompt hashes, and the measured 2-query × 10-paragraph arrays for each displayed head. `recommended_example_ids` prioritizes native-error/calibration-rescue cases with a clear primary-head preference switch, excluding native answers that already contain an accepted alias as a complete normalized word sequence; this is an explicit illustrative selection rule. Calibration intervenes on the entire selected set, while the displayed head is one representative member.
- Positive supported wording: **The same localized heads preferentially access the explicitly named entity: the bridge under q2, but the root under q12. Their attention shift is visible across sources and in concrete paragraph-level examples.**
- Use `question-token mean paragraph attention` on the main panels. The independent `last_question` field is a different recorded measurement and must not silently replace that denominator.
- The head sets are defined by measured access rankings, not separate Locate/Route/Read head classes. Their overlap and observed targeting profiles support an evidence-access function; the separate factorial experiment supplies the routing–reading interaction.
- Canonical capture/calibration examples retain the same original ten-paragraph input. Shared-context factorial examples use another documented input construction and should be labeled separately. No token-wise attention, neuron attribution, decoding trajectory, or temporal stage is inferred from these arrays.

## Reproduction

```bash
python analysis/derive_structure_evidence.py
```

The default commit is frozen explicitly in the script. `input_files` records every consumed Git blob's SHA-256; `capture_record_index` records raw JSONL-line hashes. The exported JSON contains the measured inputs needed for plotting without reading the large archives again. The only generated files are the new structure-evidence JSON and this review; original result CSVs and figures are unchanged.
