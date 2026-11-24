# CoReTrace

Mechanistic analysis and repair of contextual multi-hop composition: why can a model answer each constituent hop correctly, yet fail to compose them?

The repository contains the fixed **CoRe-2Wiki v1.0** data, complete data-construction code, mechanism experiments, repair and comparison methods, and completed formal experiment results. Exploratory results and model checkpoints are excluded.

## Completed results and paper materials

The formal suite finished on November 13, 2026. Results cover Qwen3-4B, Qwen3-8B and Llama-3.1-8B-Instruct, with training seeds 42, 43 and 44.

- [Main result table (CSV)](outputs/tables/tables.csv) and [JSON](outputs/tables/tables.json): per-model results, seed means and standard deviations.
- [Result figures](outputs/figures): phenomenon, localization, causal interventions, repair ablations and benchmark comparisons, in PDF and PNG.
- [Table sources](outputs/tables/sources.json): links from reported cells to their underlying experiment files.
- [Dataset statistics](outputs/tables/dataset_statistics.csv), [training costs](outputs/tables/training_costs.csv) and [inference costs](outputs/tables/inference_costs.csv).
- [Experiment protocol](docs/experiments.md): prompts, metrics, controls and figure/table definitions.
- [Paper materials](paper): manuscript source, compiled preview and editable Figures 1–3.

Dataset JSONL files and per-example experiment records are stored as lossless `.jsonl.gz` files. Large archives are split into `.part0000`, `.part0001`, etc. After cloning, join the parts and restore the original files with the standard-library-only command:

```bash
python scripts/restore_results.py
```

This restores the original paths used by all experiment scripts. Summaries and tables are directly readable on GitHub. The repository includes 72 completed core/capability evaluation summaries (three models, three seeds, two evaluation pipelines, four datasets), plus mechanism experiment outputs. Run `python scripts/run.py --stage report --run` after restoration to regenerate tables and figures. Local service state, model weights and execution logs are excluded.

## Layout

```
configs/                Fixed scientific settings and separate local model paths
coretrace/              Data, model interventions, training, repair, evaluation
scripts/                Data construction and experiment entry points
data/CoRe-2Wiki-v1.0/    100 discovery / 2,000 train / 1,000 test sources
data/benchmarks/         Complete HotpotQA, MMLU and GSM8K evaluation splits
docs/                   Dataset, protocol and figure/table instructions
```

## Setup

```bash
conda env create -f environment.yml
conda activate coretrace
pip install -e . --no-deps
cp configs/models.example.json configs/models.local.json
```

Set the three model directories in `configs/models.local.json`. Use Qwen3-4B, Qwen3-8B and Llama-3.1-8B-Instruct; no model above 14B is supported. A prefilled, git-ignored local configuration is included for this server. Model files are external dependencies; the repository does not depend on any earlier research directory or its services.

## Reconstruct the data

The packaged data are ready to use. Rebuild the same CoRe-2Wiki sources, questions, aliases and splits from the original 2Wiki release:

```bash
python scripts/build_data.py --archive /path/to/data_ids.zip --output /path/to/rebuilt/CoRe-2Wiki-v1.0
```

Build all three complete capability benchmarks from their original public sources:

```bash
python scripts/build_benchmarks.py --download --output /path/to/rebuilt/benchmarks
```

Local raw parquet inputs can replace downloads. See [data sources and construction](docs/data.md). No model is needed for data construction. Fixed source selection is distributed as IDs and support/document indices, rather than copies of generated questions used as builder inputs.

## Experiments

Preview the complete sequential experiment plan without loading a model:

```bash
python scripts/run.py
```

After choosing an available GPU, start the suite with an explicit `--run`:

```bash
CUDA_VISIBLE_DEVICES=2 python scripts/run.py --run
```

Run one model or stage with `--model qwen3_4b` and `--stage discover|train|readout|evaluate|causal|fullft|report`. A stage consumes the completed artifacts of preceding stages. Completed evaluations and training stages are reused on subsequent invocations; failed stages stop the queue. Seeds are fixed at **42, 43, 44**. FullFT checkpoints are removed only after all their evaluations complete; use `--keep-fullft` to retain them. Optimizer states are not saved.

`--stage report --run` regenerates CSV/JSON tables and PDF/PNG figures from completed predictions. It does not run a model. See [experiment protocol and outputs](docs/experiments.md) for every figure/table input and the exact metric definitions.

## Data and result conventions

- **CoRe-2Wiki:** fixed source-level splits, three question types, original paragraph texts and official entity aliases. Only composed training questions update LLM weights.
- **Capability retention:** full HotpotQA distractor validation **7,405**, full MMLU test **14,042**, and full GSM8K test **1,319** examples. These are full splits under our explicitly defined zero-shot prompts, not a claim of reproducing another paper's unspecified prompting.
- Results are reported per model, with all three seed results and mean/standard deviation for trained pipelines. The deterministic native-model reference is reported once. MMLU uses option probabilities as the primary metric.
- Mechanism probes using annotated paragraph addresses are diagnostic experiments. The deployed repair selects evidence from the input graph and a train-only readout, without support or answer labels.
- Model-specific scopes are fixed in `configs/experiments.json`; test performance does not select them. These settings came from the preceding development study. Source overlap with that study is allowed, so the final test panel is not described as untouched.

This repository does not include the earlier exploratory project's code, failed directions, internal audit files, SHA verification framework, logs, or pilot results.
