# Dataset construction

Rebuild CoRe-2Wiki from the original **2WikiMultiHopQA `data_ids.zip`** release:

```bash
python scripts/build_data.py --archive /path/to/data_ids.zip --output /path/to/new/CoRe-2Wiki-v1.0
```

The archive must contain `data_ids/train.json`, `data_ids/dev.json` and
`data_ids/id_aliases.json`. The builder streams it on CPU; no model, tokenizer,
GPU, previous experiment directory or prebuilt CoRe-2Wiki dataset is required.
An existing output directory is never overwritten.

`selection.json` is the fixed source selection for version 1.0. It contains
source IDs in split order, the original 868 training-source IDs, and the 25
quadruplets' source IDs, document-title order and official support-sentence
indices. It contains no question text, answer labels, aliases or paragraph
text. All those fields are reconstructed from the official archive. The
result preserves the original official composed questions and complete
contexts; the two single-hop questions are explicit diagnostic probes.
Aliases are joined through official entity IDs and `id_aliases.json`.

## How the fixed sample was selected

Selection used source annotations and input lengths, never model predictions:

- **Test (1,000 sources):** the existing two source-only evaluation pools had
  1,001 unique sources. Sort by the hexadecimal SHA-256 of
  `CoRe-2Wiki-v1-test:` followed by the source ID and keep the first 1,000.
- **Discovery (100 sources):** start with 32 naturally crossed calibration
  quadruplets. Remove whole quadruplets intersecting the fixed test sources.
  Sort remaining quadruplets by SHA-256 of `CoRe-2Wiki-v1-discovery:` followed
  by their ID and keep 25 complete quadruplets.
- **Train (2,000 sources):** retain the original 868 source-only training
  examples in their established order. From official training data, require a
  unique two-edge evidence chain, three distinct chain entities, exact official
  support sentences and matching subject paragraph titles; exclude all already
  selected source IDs. Sort by SHA-256 of `CoRe-2Wiki-v1-train:` followed by the
  source ID. Keep the first 1,132 candidates whose three prompts fit 4,096 tokens
  under the shared original Qwen3 tokenizer/template.

The released selection fixes the outcome of that historical length filter;
reconstruction deliberately does not resample with a different tokenizer or
repeat earlier exploratory pool selection. The `chain`, `edge`, `norm` and
`title_key` functions retain the actual source eligibility rules. Fixed
annotation/title-alias exceptions in discovery are reconstructed from their
original official support indices and marked explicitly in `chain_validation`.
The 25 shared-context views use complete original support paragraphs and
original distractor paragraphs from the same four source records.

Train, discovery and test are source-ID disjoint. Pilot/formal source reuse was
allowed; the test is a fixed comparison panel, not an untouched test set.
Shared root/bridge entities can connect sources across splits. The supplied
cluster IDs encode the transitive shared-entity groups for analysis; their
stable hash representation is an identifier, not a file-integrity requirement.
