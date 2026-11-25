# CoReTrace V6 最终整合（基于 dabd68aed86ca57095e382561d882197c9475e41）

## 目的与覆盖方式

本轮只做 manuscript 整合，不要求任何新的模型训练、GPU 前向、基线或实验。已有 V5 采集完整，保留全部结果及原始证据。只覆盖 ZIP 内 `paper/` 和 `analysis/` 文件，不要清空原目录，不要运行 V4/V5 覆盖安装器。

1. 在当前仓库根目录确认 `git rev-parse HEAD` 是 `dabd68aed86ca57095e382561d882197c9475e41` 或确认后续改动不冲突。保留未提交改动。
2. 解压本包至仓库根目录（覆盖同路径文件）。ZIP 内没有旧 PDF 或旧实验结果，勿删除已有的 `paper/main.pdf`，待官方编译成功后同步。
3. 运行 `python analysis/apply_final_mechanism.py --compile`。该脚本把 V6 图函数插入唯一绘图入口 `analysis/plot_results.py`，同步已有 `story_revision_plot.inc`，从 V5 实测 JSON/CSV 生成图，调用原始编译脚本，自动检查第八页 Conclusion、第九页 Impact Statement、正文 Figure 1–13、未解析引用与 overfull；成功后同步 `paper/main.pdf`、`main.bbl`，生成 `analysis/build_final_mechanism/CoReTrace_Overleaf_full.zip`。如 V5 anchor 有冲突，只对照合并对应小段，不修改实验代码或重新采集。
4. 检查 `git status --short`，只提交 `paper/` 和 `analysis/` 允许范围内的修订文件；不要提交构建缓存、模型权重或根目录覆盖包。同步新生成的 PDF/PNG、绘图入口、源文件、新附录、正式 PDF 和 bbl，随后 commit、push 并核验远端 HEAD。交付正式 PDF 和 Overleaf 全量包路径。

**职责边界：** 本轮论文排版设计和视觉审阅由 ChatGPT 完成，不向 Codex 分派逐页 PDF 渲染、视觉验收、图表美观评估、版式微调或论文润色任务。Codex 仅完成覆盖、数据绘图集成、正式编译、自动化结构/引用检查及 Git 同步。若自动检查失败（例如正式环境出现第九页仍有正文），保留日志并报告具体冲突，不自行删减内容或改变字号、边距、图尺寸，也不覆盖上一版正式 PDF。若一切通过，直接提交即可。

## 修改内容

- 摘要、Introduction、Methodology、Conclusion 强化协调 routing/reading 的核心科学发现及实测闭环；保留既有五个一级 Section、三个概念图（Figure 3 的图注和方法映射更新，原有图形保留）。
- Fig. 8 真实 token heatmap：Angela / Rebecca Miller，同一 bridge 的 American、Arthur Miller、Inge Morath 对应的分词，四状态，原生组合、原生直接母亲、原生直接国籍、适配+恢复组合。权重取实测 `conditional_mean`，均以完整 bridge 归一化；Arthur Miller 是原生错误输出的可视化参照，不是 population 的 other-relation 控制，other-relation 控制是 American。
- Fig. 12 将 test 固定原生失败的 root/bridge mass paired change 与 discovery 的 conditional/absolute preference paired change 合并。分别 n=234/236/243 和 n=98/模型；不可把两组样本合并成同一个人口。误差区间沿用归档 bootstrap。原生 vs 适配+恢复是观测状态差异，原有四臂干预提供因果证据，不能宣称新观测独立证明每个组件的因果中介作用。
- Fig. 13 紧凑可视化 attention-only address readout 和 ambiguous bridge selection；原三面板完整图和 restoration 消融保留在 Appendix G。
- Appendix G 补齐协议、数学定义、各模型四状态均值/CI、全测试集和固定失败子集的 routing 表、restoration/selection 图。旧 appendix A–F 不覆盖。
- 不增加 LoRA、random-head training、held-out factorial 或其他非必要实验。

## 结果来源与本地验收状态

对应真实输入均在基准 commit：`analysis/figure_data/data_revision_token_capture.json`、`data_revision_adapted_routing.csv`、`data_revision_relation_reading_summary.csv`、`data_revision_mechanism_repair.csv`。新图函数直接读取上述数据，不引入新的实验结果或 placeholder。

ChatGPT 已重新检查本地八页正文预览（实际 V5 main table、已有局部模板及图文件）与单独编译的新增 Appendix G 两页：正文 Figure 1–13、五个一级 Section，第 8 页 Conclusion，图文、表格及新附录表宽/图注均在版心内；本地编译日志未见 overfull/undefined 引用。第 5、6 页仍有少量栏底余白，保留正常字号和图表清晰度。新图以核实的远端实测记录生成。此次重打包不修改 TeX、数值或图表。

**未完成的工程缺口：** 当前容器无法 git clone（DNS），无法整体重编译真实仓库的官方模板、原附录 A–F 及所有原图，故不能宣称完成 V6 全篇正式 PDF 的逐页验收，也不应将本地预览直接覆盖 `paper/main.pdf`。本包不含正式全篇 PDF；唯一留给原始仓库环境的工作是执行上述自动化构建与同步。不要求 Codex 完成视觉验收。没有任何待补实验。
