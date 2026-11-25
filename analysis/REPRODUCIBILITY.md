# Reproducibility scope and verified evidence

Audit date: 2026-11-24. Audited repository revision: `cf00035eb9b71bebf3ae88f76caf30ee9b58065c`.

The current revision is supported by fresh reaggregation of recorded predictions and reapplication of released paragraph readers. Figure/table reconstruction uses these existing experiment artifacts. It does not execute new model training or inference.

## Verified coverage

| Verification | Coverage | Recorded outcome | Evidence file |
| --- | --- | --- | --- |
| Prediction manifests, IDs, populations, and summary counts | 90 experiment directories; 991,680 prediction records | Zero recorded errors | `analysis/internal/current_audit/result.json`, `analysis/internal/prediction_validation.json` |
| Released reader weights reapplied to archived paragraph features | 12 native/adapted readers, with full/attention/metadata variants | Stored train/test counts reproduced | `analysis/internal/readout_validation.json` |
| Aggregate result entries | 144 model/benchmark/method/query entries | Counts, means, and sample SDs reproduced | `analysis/internal/table_validation.json`, `analysis/internal/current_audit/additional_checks.json` |
| Factorial contrasts and clustered intervals | Three models; 100 receivers each | Recorded estimates reproduced | `analysis/internal/current_audit/additional_checks.json`, `analysis/internal/current_evidence_audit.md` |
| Identity interventions | 300 model/source pairs | All generated token sequences match native | `analysis/internal/current_audit/additional_checks.json` |
| Reciprocal content experiments | Nine model/run directories; 800 rows per directory | Outcome counts and valid exchanges reproduced | `analysis/internal/current_audit/additional_checks.json` |
| Head metadata | Nine recorded model/run configurations | Ranked selections, trained selections, and parameter counts agree | `analysis/internal/current_audit/head_metadata_checks.json` |

The detailed report is `analysis/internal/current_evidence_audit.md`. The duplicate audit files have been consolidated at their canonical paths under `analysis/internal/`; distinct additional audit checks remain under `analysis/internal/current_audit/`. The underlying audit records are unchanged.

## Recorded runs and populations

Selected-head runs 42/43/44 use fixed source order, zero-initialized deltas, and model evaluation mode during adaptation. Within each model, all three 2,000-example source, loss, and gradient-norm sequences agree. Reported sample SD describes the recorded executions, including their evaluation settings; it is not an estimate across independent stochastic initializations. Source-bootstrap intervals and quadruplet-bootstrap intervals retain their stated sampling units.

The formal split uses 100 discovery, 2,000 training, and 1,000 test source IDs. The factorial analysis uses 25 discovery quadruplets, yielding 100 receivers. The 1,000-source address-specificity evaluation is a separate test population. Development provenance, entity overlap, batch sizes, and the model-specific restoration choices are reported in the appendix.

## Implementation boundary

The original audit found four imported runtime modules absent from its checkout:

- `coretrace/models/native`
- `coretrace/models/deployment`
- `coretrace/models/head_slices`
- `coretrace/models/cpu_adamw`

These original runtime sources have now been restored from the experiment workspace, together with `coretrace/models/__init__.py` and the deployment dependency `scoped_rollback.py`. The omission came from the unanchored `models/` Git ignore rule; `/models/` now excludes only the root model-weight directory. `analysis/internal/missing_modules.json` remains the historical audit finding. A complete GPU rerun requires external model weights and the declared execution environment. CPU import and optimizer checks validate the restored source; they do not constitute a fresh GPU experiment rerun.

| Model | Declared native restoration | Prefill scope |
| --- | --- | --- |
| Qwen3-4B | V and O; layers 16–19 | Prefix before the question |
| Qwen3-8B | V and O; layers 12–19 | Question tokens |
| Llama-3.1-8B | V; selected layers | Prefix before the question |

These settings were checked in `outputs/{model}/seed42/evaluation/core/manifest.json`, under `provenance.config.methods` for `final`, and agree with the manuscript's scope table. The restored restoration/head-slice implementation is available in `coretrace/models/` for inspection and execution.

## Reconstructing the displayed evidence

From a complete Git checkout:

```bash
python analysis/plot_results.py
python analysis/build_tables.py
```

The current plotting entry loads the verified base source from commit `4990754cb73512599adfea9519862868b4260dbf`; retain that history when cloning. It regenerates the final figure set from recorded inputs, retaining the author-selected PNGs for Figures 1–3. The table builder uses the recorded experiment summaries and retained audit data. See [README.md](README.md) for the current inventory and analysis commands. No GPU or model weights are needed to reconstruct the displayed figures and tables from the stored summaries.

The metadata file `analysis/internal/source_snapshot.json` preserves the original scientific baseline `a00e62230ab83d4e050e3da29a9e9cfd5e239dd6` and the audit revision. The original source and data identities are also retained in the derivation manifests and raw captures. 

## Compiling the submission

Run `bash analysis/compile_paper.sh`, inspect `analysis/build_final/main.pdf` page by page, and resolve layout/reference issues. Only after visual QA should the compiled PDF and bibliography output be copied to `paper/main.pdf` and `paper/main.bbl`. See `paper/README.md` and `analysis/tex_build_notes.md` for the build commands.

## Recorded routing and paired-relation experiment execution

The following original-language execution record preserves the scientific portions of the completed experiment report, including the actual sample counts, capture provenance, runtime details, and measured results. The manuscript-editing and delivery sections are not part of this record. All linked data files are retained.

### Seed 42 段落路由离线再分析

每模型 1,000 个匹配测试来源，共 3,000 行。脚本验证 canonical 三问、源和问题 ID、冻结头集、prompt token 总数、段落顺序和 token 几何。保留 raw root/bridge mass，允许 BF16 归档中的轻微行和误差。下表数值单位为百分比和百分点，区间为同源配对 bootstrap 的 95% 区间。固定失败子集由两个原生 constituent 正确且原生 composed 失败定义。

| 模型 | 样本 | n | 位置 | Native % | Adapted % | Δ pp [95% CI] |
|---|---|---:|---|---:|---:|---:|
| qwen3_4b | 测试集 | 1000 | root | 30.63 | 29.54 | -1.09 [-1.28, -0.90] |
| qwen3_4b | 测试集 | 1000 | bridge | 8.14 | 14.18 | +6.04 [+5.80, +6.28] |
| qwen3_4b | 固定失败 | 234 | root | 31.02 | 29.97 | -1.06 [-1.43, -0.67] |
| qwen3_4b | 固定失败 | 234 | bridge | 7.63 | 12.99 | +5.36 [+4.87, +5.87] |
| qwen3_8b | 测试集 | 1000 | root | 31.56 | 31.13 | -0.43 [-0.55, -0.32] |
| qwen3_8b | 测试集 | 1000 | bridge | 8.96 | 13.29 | +4.33 [+4.17, +4.50] |
| qwen3_8b | 固定失败 | 236 | root | 32.58 | 32.19 | -0.39 [-0.63, -0.14] |
| qwen3_8b | 固定失败 | 236 | bridge | 8.18 | 11.88 | +3.71 [+3.40, +4.02] |
| llama3_8b | 测试集 | 1000 | root | 25.33 | 23.03 | -2.29 [-2.48, -2.11] |
| llama3_8b | 测试集 | 1000 | bridge | 8.84 | 15.81 | +6.97 [+6.72, +7.22] |
| llama3_8b | 固定失败 | 243 | root | 26.32 | 24.32 | -1.99 [-2.37, -1.61] |
| llama3_8b | 固定失败 | 243 | bridge | 7.38 | 13.84 | +6.46 [+5.93, +7.00] |

三个模型的同输入状态差异均表现为 bridge mass 上升、root mass 下降。实验设计只支持状态差异的观测解释。[汇总 CSV](figure_data/data_revision_adapted_routing.csv) · [逐来源 CSV](figure_data/data_revision_adapted_routing_receivers.csv) · [输入 SHA-256](figure_data/data_revision_adapted_routing.manifest.json)

### 同输入 token 采集

样本来自原冻结的 25 个 discovery quadruplets。各模型按原 tokenizer 和 chat template，以完整共享上下文运行原生组合问、原生显式同关系问、原生显式另一关系问、适配并恢复投影后的组合问。状态间校验桥段 token IDs、索引和上下文前缀。在最后一个问题 token 行记录每头桥段质量 (m)、完整条件向量 (ho) 和两种真实关系的 span。绝对权重先求每头 (m_hho_h) 再对共同有效头取均值。区间使用全部 25 个 quadruplets（10,000 次整簇重采样）。主分析保留目标减另一关系的有符号差值及每 token 长度归一化值。

源文件逐项 SHA-256 写入每个 raw bank 的 `source_files_sha256` 字段，其中包括语料和视图、冻结头集、已保存的 seed 42 checkpoint、固定 scope、模型配置和 tokenizer 文件。[采集代码](capture_paired_relation_reading.py) · [聚合代码](derive_story_relation_reading.py)

| 模型 | 有效 / 原始 receiver | 共同有效头 | 冻结 restoration scope | 新 prefill | 来源集合 SHA-256 |
|---|---:|---:|---|---:|---|
| Qwen3-4B | 98 / 100 | 20 | VO，`prefix_before_question`，16–19 层 | 294 | `da08f2af46a2dd31e44b2dc5b1e4018b2bd18a2ac788e839f42e2d856d15f0ef` |
| Qwen3-8B | 98 / 100 | 20 | VO，`question_prefill`，12–19 层 | 294 | `e4e4d640328f6c3fa63b3957f3b41a06bf25339c7bba2096212a22821db7063f` |
| Llama-3.1-8B-Instruct | 98 / 100 | 40 | V，`prefix_before_question`，选中层 | 290 | `4e269c429cfe5e191c8d08a9d0aa4bee6767d74a161d58dd2859af803a963856` |

三个模型均排除 `natural_crossed_901c815fb5a1839eb3e1__C21` 和 `natural_crossed_901c815fb5a1839eb3e1__C22`，原因都是两个关系 span 在分词后重叠。两例及原因保留在各自原始 100 receiver 分母中。全量含 294 个有效模型–receiver 配对和 1,176 行状态记录。每模型去重后的唯一 prefill 数为 294，其中 Llama 四次已在 pilot 采集并逐字段验证复用，故本次续跑新增 878 次前向。Qwen3-4B 的执行日志被下一模型复用同名路径时覆盖，新前向数由该模型的 294 个逐次落盘缓存项与完整 raw bank 核实。

采集在 GPU2 的 systemd unit 内顺序运行，限额为 8 CPU、64 GiB、256 tasks。实际研究前向期间 PID 71457 的占位计算保持暂停。队列完成后核对同一 PID 已恢复，占用 45,746 MiB；只使用了 GPU2。运行中系统可用内存约 465 GiB，交换使用约 1 MiB。占位计算单独记录，未计入实验进展。

#### 四状态均值和配对差值

下表各状态为均值百分比，差值为百分点。每个模型保留全部通过几何匹配的 98 个 receiver，25 个簇均有数据。

| 模型 | 指标 | 原生组合 | 原生直接同关系 | 原生直接另一关系 | 适配组合 | 适配−原生 [95% CI] | 直接同−另一 [95% CI] |
|---|---|---:|---:|---:|---:|---:|---:|
| qwen3_4b | 桥段质量 | 11.87 | 23.41 | 23.41 | 26.91 | +15.04 [+13.64, +16.49] | +0.00 [+0.00, +0.00] |
| qwen3_4b | 条件差 | 3.93 | 4.54 | -4.54 | 7.40 | +3.47 [+2.89, +4.03] | +9.09 [+6.94, +11.41] |
| qwen3_4b | 每 token 条件差 | 2.24 | 1.78 | -1.78 | 4.09 | +1.85 [+1.43, +2.29] | +3.55 [+2.79, +4.41] |
| qwen3_4b | 绝对差 | 0.85 | 1.96 | -1.96 | 3.47 | +2.62 [+2.15, +3.13] | +3.92 [+2.54, +5.45] |
| qwen3_8b | 桥段质量 | 13.98 | 21.91 | 21.91 | 29.91 | +15.93 [+14.63, +17.29] | +0.00 [+0.00, +0.00] |
| qwen3_8b | 条件差 | 4.28 | 4.62 | -4.62 | 8.44 | +4.16 [+3.49, +4.83] | +9.23 [+6.64, +12.04] |
| qwen3_8b | 每 token 条件差 | 2.28 | 1.85 | -1.85 | 4.82 | +2.54 [+1.91, +3.22] | +3.70 [+2.65, +4.87] |
| qwen3_8b | 绝对差 | 1.31 | 2.33 | -2.33 | 4.92 | +3.61 [+3.00, +4.20] | +4.66 [+2.88, +6.63] |
| llama3_8b | 桥段质量 | 21.39 | 28.54 | 28.54 | 40.77 | +19.38 [+16.13, +22.86] | +0.00 [+0.00, +0.00] |
| llama3_8b | 条件差 | 12.67 | 12.98 | -12.98 | 25.73 | +13.06 [+11.58, +14.59] | +25.97 [+20.70, +31.07] |
| llama3_8b | 每 token 条件差 | 6.91 | 5.40 | -5.40 | 13.70 | +6.79 [+5.69, +7.91] | +10.80 [+8.74, +13.02] |
| llama3_8b | 绝对差 | 4.41 | 6.97 | -6.97 | 14.70 | +10.29 [+9.24, +11.36] | +13.94 [+10.42, +17.63] |

两种直接状态交换的是同一组问句，因而汇总桥段质量的差值按设计相消。三个模型的适配组合相对原生组合，在这批 discovery 样本上均有正向的条件、每 token 和绝对目标偏好差值。完整 CSV 保留两个 span 各自的统计和两个对照的全部区间。这项同输入测量与既有因果干预互补，结论限于本批观测及已冻结模型状态。

[模型及对照汇总](figure_data/data_revision_relation_reading_summary.csv) · [逐 receiver 四状态](figure_data/data_revision_relation_reading_receivers.csv) · [压缩档与解压后 JSON 的 SHA-256](figure_data/data_revision_relation_reading_manifest.json)

- 完整 raw banks（逐头条件向量、原始分子与总量、token IDs 和索引、来源哈希）为 [Qwen3-4B](figure_data/data_revision_relation_reading_qwen3_4b.json.gz)、[Qwen3-8B](figure_data/data_revision_relation_reading_qwen3_8b.json.gz) 和 [Llama](figure_data/data_revision_relation_reading_llama3_8b.json.gz)。无损 `.json.gz` 用于远端交付，原始 `.json` 另存于本地 `analysis/build_story_revision/raw_captures/`。聚合脚本直接读取两种格式。
- 单例 Angela 面板来自已保存的 [Llama pilot](figure_data/data_revision_relation_reading_llama3_8b_pilot.json)，与全量四状态和 raw banks 完全一致。冻结 C12/T12 问 Rebecca Miller 的母亲，支持句记录 Inge Morath。C11/T11 对应国籍，支持句写作 American。该诊断案例的原生生成错误仍是 Arthur Miller。[兼容面板 JSON](figure_data/data_revision_token_capture.json)

For a new capture, resolve the original model weights and checkpoint paths from the frozen manifests and use the recorded model-specific scope under `figure_data/v5_frozen_scope_*.json`. Example plan-only invocation (replace local paths with verified existing files):

```bash
python analysis/capture_paired_relation_reading.py \
  --model-id llama3_8b --dataset data/CoRe-2Wiki-v1.0 \
  --model "$MODEL" --budget outputs/llama3_8b/discovery/SELECTION_FROZEN.json \
  --checkpoint "$CHECKPOINT" \
  --scope analysis/figure_data/v5_frozen_scope_llama3_8b.json
```

The capture tool defaults to plan-only. The `--run` option performs the read-only forwards; `--case-only` selects the Llama pilot. Existing complete verified captures should be reused rather than rerun. The paired-relation derivation accepts both JSON and losslessly compressed JSON.gz captures, and uses a 10,000-replicate quadruplet bootstrap by default.
