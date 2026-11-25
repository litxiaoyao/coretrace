# CoReTrace V5 执行报告

## 工作区与复用

起点为本地及远端 `main` 的 `5ff9f52179a72f911db319c52270121d78de92b0`。在已安装的覆盖包和未提交修订上继续。覆盖包的 39 项原始哈希保存在 [覆盖清单](V5_OVERLAY_MANIFEST.json)。本次改动限定在 `paper/` 和 `analysis/`。

[既有采集盘点](V5_EXISTING_CAPTURE_INVENTORY.json)记录了对本仓库 `outputs/`、`analysis/`、`coretrace_internal` 和 `test` 的本地搜索。原始 readout 支持段落级再分析。归档的 factorial 记录没有完整同输入四状态 token 条件向量。本轮复用了已有的头消融、质量校准、四臂干预、互换、projection restoration 和通用能力结果。未重新训练、生成基准预测或重复这些实验。Figure 9 的联合纠正计数与原始逐格 CSV 一致，Figure 10 的互换准确率及稳定地址数已从旧逐样本记录重新计数。Figure 11 的 readout 和歧义对照核对了原表。Figure 12 直接读取真实 restoration 消融，三个模型的 first-hop 差值为 +5.0/+2.4/+27.3 pp，all-three 为 +2.4/+0.8/+17.5 pp。

## Seed 42 段落路由离线再分析

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

## 同输入 token 采集

样本来自原冻结的 25 个 discovery quadruplets。各模型按原 tokenizer 和 chat template，以完整共享上下文运行原生组合问、原生显式同关系问、原生显式另一关系问、适配并恢复投影后的组合问。状态间校验桥段 token IDs、索引和上下文前缀。在最后一个问题 token 行记录每头桥段质量 (m)、完整条件向量 (ho) 和两种真实关系的 span。绝对权重先求每头 (m_hho_h) 再对共同有效头取均值。区间使用全部 25 个 quadruplets（10,000 次整簇重采样）。主分析保留目标减另一关系的有符号差值及每 token 长度归一化值。

源文件逐项 SHA-256 写入每个 raw bank 的 `source_files_sha256` 字段，其中包括语料和视图、冻结头集、已保存的 seed 42 checkpoint、固定 scope、模型配置和 tokenizer 文件。[采集代码](capture_paired_relation_reading.py) · [聚合代码](derive_story_relation_reading.py)

| 模型 | 有效 / 原始 receiver | 共同有效头 | 冻结 restoration scope | 新 prefill | 来源集合 SHA-256 |
|---|---:|---:|---|---:|---|
| Qwen3-4B | 98 / 100 | 20 | VO，`prefix_before_question`，16–19 层 | 294 | `da08f2af46a2dd31e44b2dc5b1e4018b2bd18a2ac788e839f42e2d856d15f0ef` |
| Qwen3-8B | 98 / 100 | 20 | VO，`question_prefill`，12–19 层 | 294 | `e4e4d640328f6c3fa63b3957f3b41a06bf25339c7bba2096212a22821db7063f` |
| Llama-3.1-8B-Instruct | 98 / 100 | 40 | V，`prefix_before_question`，选中层 | 290 | `4e269c429cfe5e191c8d08a9d0aa4bee6767d74a161d58dd2859af803a963856` |

三个模型均排除 `natural_crossed_901c815fb5a1839eb3e1__C21` 和 `natural_crossed_901c815fb5a1839eb3e1__C22`，原因都是两个关系 span 在分词后重叠。两例及原因保留在各自原始 100 receiver 分母中。全量含 294 个有效模型–receiver 配对和 1,176 行状态记录。每模型去重后的唯一 prefill 数为 294，其中 Llama 四次已在 pilot 采集并逐字段验证复用，故本次续跑新增 878 次前向。Qwen3-4B 的执行日志被下一模型复用同名路径时覆盖，新前向数由该模型的 294 个逐次落盘缓存项与完整 raw bank 核实。

采集在 GPU2 的 systemd unit 内顺序运行，限额为 8 CPU、64 GiB、256 tasks。实际研究前向期间 PID 71457 的占位计算保持暂停。队列完成后核对同一 PID 已恢复，占用 45,746 MiB；只使用了 GPU2。运行中系统可用内存约 465 GiB，交换使用约 1 MiB。占位计算单独记录，未计入实验进展。

### 四状态均值和配对差值

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
- 单例 Angela 面板来自已保存的 [Llama pilot](figure_data/data_revision_relation_reading_llama3_8b_pilot.json)，与全量四状态和 raw banks 完全一致。冻结 C12/T12 问 Rebecca Miller 的母亲，支持句记录 Inge Morath。C11/T11 对应国籍，支持句写作 American。Figure 9 的原生生成错误仍是 Arthur Miller。[兼容面板 JSON](figure_data/data_revision_token_capture.json)
- 可审阅补图为 [桥段与根段路由](../paper/figures/data_main_adapted_routing_optional.pdf)、[Angela 四状态](../paper/figures/data_main_token_reading_optional.pdf) 和 [总体关系偏好](../paper/figures/data_main_relation_population_optional.pdf)。三张均有 PNG，正文采用既定 V5 结构。

## 正式编译与视觉检查

用原 ICML2027 模板及 Tectonic fallback 正式编译，字号和页边距沿用模板。全文 26 页，正文五个一级章节占第 1–8 页，Conclusion 在第 8 页，Impact Statement 从第 9 页开始。正文保留 Figure 1–12。正文 PDF 和 `main.bbl` 与同一次正式构建逐字节相符。参考文献共 24 条。无未解析引用、`??`、正文占位图或 overfull 警告。日志保留 Tectonic 的输入编码提示、首页空锚提示和部分 underfull 提示。

已逐页查看第 1–26 页的独立 130 dpi 渲染。第 1–3 页检查标题、摘要和框架图。第 4–8 页检查实验图表、图注、列边界和结论。第 9–10 页检查声明与参考文献。第 11–26 页检查附录 A–F、图 A1–A8 和表 A1–A19。发现并修正 Figure 1 中间标签伸出框线、Figure 10 底行散点裁切，重新查看第 1、7 页，并确认其余 24 页逐页渲染哈希一致。随后为附录图表设置独立 PDF 链接目标，避免与正文重置前的计数器冲突。该构建的 26 页渲染与视觉验收版本逐页哈希一致。关键附录交叉引用指向正文 Figure 5、7、9 和 Equation (2)、(4)。

[正式 PDF](../paper/main.pdf) · [正式 bibliography](../paper/main.bbl) · [修订绘图输入清单](figure_data/input_manifest_story_revision.csv)

本地正式 Overleaf 包位于 `analysis/build_story_revision/CoReTrace_Overleaf_full.zip`，已通过 ZIP 完整性检查。最终 PDF SHA-256 为 `24900a8518780b4939b4b921bf3619da0a170a4870bbec7bf998082ae825aaec`，`main.bbl` SHA-256 为 `5dde75d8d6a4ba0017519819a3f88e6ef4585a18b46555e3d50df6a85947ca1f`。

## 提交范围

交付包含 V5 正文、附录案例及附件锚点修订、PDF、绘图入口及 V5 图 PDF/PNG、编译 fallback、采集和离线统计脚本、汇总与逐样本结果、压缩原始数据、来源清单和执行报告。根目录覆盖包、构建产物、缓存、权重、训练配置和原始数据目录均留在本地原位置或原提交中。计划中的采集、构建和分析均已完成，独立测试集上的 token 层验证超出本次 discovery 采集范围。
