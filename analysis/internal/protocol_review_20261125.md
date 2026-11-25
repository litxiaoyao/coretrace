# Protocol review for the manuscript revision

Date: 2026-11-25. Reviewed repository snapshot: `7e498a6a29ff9623183e7bddc7e5c3019035caef`.

Scope: read-only examination of the released data selection, formal execution code, configuration, and recorded audits. This review changes no data, experiment configuration, prediction, or result. It runs no model and does not prescribe new experiments. Earlier review comments and internal notes are evidence of prior discussion, not instructions for the current revision.

## Finding

The released formal workflow supports a positive, precise account: fixed source-level splits; discovery-only head and mass-target selection; composed-training-only model adaptation; training-only paragraph-reader fitting; and fixed model-specific restoration configurations applied throughout the reported suite. No inspected formal code or record shows test predictions being used to select heads, fit the reader, or re-optimize restoration settings.

The earlier concern about preceding development is a provenance qualification, not an observed experimental failure. The repository explicitly preserves an established research panel and permits source reuse from earlier work. It does not supply a complete item-level history of every preceding-development evaluation. Therefore neither a claim of test-driven rule selection nor a claim that the final panel had never previously been examined is established by this review.

## Independently checked selection facts

The fixed IDs in `coretrace/data/builders/selection.json` were compared directly with the three released `data/CoRe-2Wiki-v1.0/splits/*.json` files using the Git objects at the reviewed snapshot.

| Check | Result |
| --- | --- |
| Discovery/train/test source counts | 100 / 2,000 / 1,000 |
| Unique source counts | 100 / 2,000 / 1,000 |
| Discovery–train, discovery–test, train–test intersections | 0 / 0 / 0 |
| Selection IDs and released split order | Exact match in all three splits |
| Shared-context quadruplets | 25, containing 100 distinct source IDs |
| Quadruplet source set | Exactly the discovery source set |
| Original training panel | All 868 original IDs are within the 2,000-source training split |

The recorded `analysis/internal/dataset_audit.json` further reports that all formal training sources originate in official train and all test sources originate in official dev; discovery contains 77 official-train and 23 official-dev sources. The test panel has 1,000 distinct roots, bridges, and within-test entity groups. Forty-three test sources belong to global root/bridge groups also represented in training. These are entity-group connections, not duplicate source IDs. The latter statistics were read from the existing audit, rather than newly recomputed from the full official archive.

## Evidence map

| Supported statement | Primary code or record |
| --- | --- |
| Data construction reconstructs original questions, contexts, supports, and aliases from the official archive | `coretrace/data/builders/core2wiki.py`, lines 184–258; `scripts/build_data.py` |
| The builder uses fixed source IDs and enforces 3,100 distinct selected sources | `coretrace/data/builders/core2wiki.py`, lines 188–202 |
| The loader rejects overlapping source IDs and inconsistent query/split assignments | `coretrace/data/frozen_loader.py`, lines 34–76 |
| Head ranking and mass calibration use discovery only | `coretrace/mechanisms/localization.py`, lines 14–33 and 56–120; `scripts/discover.py`, lines 45–61 |
| Best head count is selected by discovery accuracy, with smaller count on ties | `coretrace/mechanisms/localization.py`, lines 109–120; `outputs/{model}/discovery/SELECTION_FROZEN.json` |
| Model adaptation uses only composed training questions | `scripts/train.py`, line 29 and lines 54–55 |
| Test features/labels enter reader diagnostics, but not reader fitting | `scripts/readout.py`, lines 50–77; the fitting call receives only rows selected as `split == 'train'` |
| Restoration scopes are explicit fixed configurations | `configs/experiments.json`, lines 10–13; matching `outputs/configs/{model}_scope.json` |
| Formal runs do not re-optimize scopes using test or capability results | `docs/experiments.md`, line 11, consistent with the fixed-configuration formal workflow |
| The source panel preserves previous research selections | `coretrace/data/builders/README.md`, lines 23–55; `data/CoRe-2Wiki-v1.0/dataset.json` |
| Earlier source reuse is permitted; an untouched-test claim is not made | Root `README.md`, final protocol bullet; `docs/data.md`, line 17; builder metadata policy at `core2wiki.py`, line 257 |

`analysis/internal/current_audit/result.json` records 90 experiment manifests and 991,680 prediction rows, with zero prediction-validation errors and zero readout-validation errors. `additional_checks.json` records 144 matching aggregate cells. These existing numerical checks support the reported results; they do not reconstruct the complete historical development process.

## Recommended manuscript wording

### Main experimental setup

> CoRe-2Wiki contains 100 discovery, 2,000 training, and 1,000 test sources with disjoint source IDs. Discovery fixes the selected heads and attention targets; the composed training questions fit the head updates and paragraph-address readers. Model-specific projection-restoration settings are fixed before the reported evaluation suite and shared across the corresponding component comparisons.

This states the actual workflow directly. It does not need a speculative sentence about what earlier work might have done.

### Appendix provenance

> The released source selection preserves the established research panels. Test sources are fixed from the 1,001-source evaluation pool, discovery uses 25 complete crossed quadruplets after removing test-source overlaps, and training combines the original 868 sources with 1,132 eligible official-training sources. The projection-restoration scopes were established during preceding development and remain fixed throughout the reported suite.

This is a factual replacement for repeated or vague “may reuse preceding development” wording. The existing appendix details of fixed ordering, eligibility, and source origins can remain. The formal source-disjointness claim should not be expanded into entity disjointness or independence from all preceding development.

### Diagnostic population

> The shared-context diagnostic comprises 100 receivers in 25 discovery quadruplets, with uncertainty estimated by resampling complete quadruplets. The separate address-specificity evaluation uses the 1,000-source test panel.

This gives the actual populations once, without defensive repetition or implying that the diagnostic quadruplets form an independent test split.

## Editorial decision

Remove repeated historical uncertainty from the main narrative. Preserve the concrete selection history and fixed-configuration origin in the appendix, phrased affirmatively as protocol facts. Do not introduce “untouched,” “never examined,” “fully entity-disjoint,” or “independent validation set” for the existing panels. Conversely, do not label the formal experiments contaminated or incorrectly conducted: the inspected formal workflow supplies no evidence for that accusation.

No change to the experimental data or new GPU run is required to make these wording corrections. Figures 1–3 and all reported numerical results are outside this review's edit scope and remain unchanged.

## Implemented protocol-language revision

The subsequent authorized edit updates only `paper/sections/appendix_protocol.tex`: it streamlines the scoring, training, reader-fitting, comparison, and uncertainty descriptions; explicitly limits the 32-token completion statement to CoReTrace; and states that restoration settings were fixed before the reported evaluation suite. Recorded-run determinism, batch settings, paired references, and all scoring definitions remain explicit without repeated caveats.

A direct comparison against the reviewed Git snapshot confirms identical numeric-token multisets, table blocks, labels, and citation keys. `git diff --check` reports no whitespace errors. Integrated typesetting and page-layout review are handled with the complete manuscript revision.
