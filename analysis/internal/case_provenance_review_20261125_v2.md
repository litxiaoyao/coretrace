# V2 mechanism and case provenance review

Date: 2026-11-25. Reviewed the current `paper/main.tex` and the introduction,
method, experiments, and conclusion sections against the released code and
recorded outputs. No model experiments were run.

## Mechanism statements

The manuscript presents Locate–Route–Read as three coupled functional operations.
Address recovery, destination-specific mass calibration, and the crossed
mass/pattern experiment provide the corresponding measurements. The reported
interaction estimates and intervals are preserved, including the Qwen3-8B
interval whose lower endpoint is zero. Donor transfers are correctly described
as normalized attention patterns, with receiver-computed values and original
output-projection weights. The text does not assign the operations to separate
early, middle, or late layer stages.

## Verified cases

The machine-readable source is
`analysis/internal/mechanism_case_records_20261125_v2.json`, constructed from
commit `766aaa073672d09aeb9e93a1cf6b60a3110d921e`. It includes source IDs, exact
context sentences, query and prediction records, input-file SHA-256 hashes, and
reconstructed prompt hashes.

- **John Corvinus:** In recorded run 42, Qwen3-4B, Qwen3-8B, and Llama-3.1-8B
  correctly answer both constituent queries, answer the composed query with
  “Matthias Corvinus” natively, and answer “John Hunyadi” with complete CoReTrace.
  All three select original paragraph 1, titled “Matthias Corvinus.” This is a
  composition-repair example; the JSON also retains the recorded component
  outputs.
- **Angela:** The Llama shared-context diagnostic answers Native/Mass/Pattern/
  Both with “Arthur Miller”/“Arthur Miller.”/“Arthur Miller”/“Inge Morath”. The
  manuscript's prose correctly omits only terminal punctuation. Complete
  CoReTrace separately answers “Inge Morath” on the original context and
  “Gisela Elsner” after reciprocal exchange, selecting paragraph 5 (“Rebecca
  Miller”) in both versions.
- **Context identity:** Released `discovery_views` and `reciprocal_value_views`
  reconstruct the same original Angela prompt. The factorial and content native
  records also agree in prompt-token count and generated token IDs. The two
  exchanged mother-name spans preserve the full-context word and character
  multisets. The native-model Both intervention and complete CoReTrace exchange
  experiment are separately identified in both the JSON and manuscript.

## Compact precision edits suggested to the manuscript owner

1. Describe adaptation as Q/O slices of the selected query heads plus their
   associated K/V groups; `coretrace/models/head_slices.py` uses the union of
   shared K/V groups.
2. Describe the title-graph root as the unique maximal title match;
   `coretrace/method/title_graph.py` removes nested matches before checking
   uniqueness. The appendix already specifies this behavior.

All checked case statements and aggregate values match their recorded sources.
No paper files or original result data were changed by this review.
