# Revision notes — 2026-11-24

## 最终主线与标题

**When Correct Hops Fail to Compose: Diagnosing Evidence Access and Local Reading**

全文围绕同一条证据链组织：同一上下文中，两跳 constituent answers 正确，组合回答仍然失败；失败时仍能从原生 attention features 读出 bridge paragraph；四臂干预进一步显示，段落访问量改变局部 attention pattern 的行为效用；CoReTrace 将这一诊断用于证据选择和选定头适配，再用候选歧义对照与局部事实交换验证结果。

初稿的全局诊断见 analysis/internal/current_global_diagnosis.md。四篇参考论文用于研究问题展开、干预证据呈现、对照组织与正文/附录分工；仅保留与当前问题直接相关的参考文献。

## 主要内容调整

| 部分 | 最终处理 |
| --- | --- |
| 标题、摘要、引言 | 统一到“正确事实为何未能组成正确答案”，突出 recoverable address 与 access–reading interaction；将核心发现、诊断和修复分开陈述。 |
| 方法 | 明确 behavioral gap、训练拟合的读出器、head contribution、四臂因果干预与应用修复分别提供什么证据；准确说明 receiver-computed values 和原始 output-projection weights。 |
| 核心结果 | 让 1,000-source 失败诊断、25-quadruplet 四臂实验、独立的段落地址控制承担不同角色；报告交互估计和区间。 |
| 修复证据 | 主结果加入 native evidence-selection baseline；新增简洁的组件表和 103 个歧义输入汇总表。897 个其余输入的 token sequences 完全一致，使读出器的增益位置可检查。 |
| 局部内容验证 | 同时展示 edited-value following 与 original/edited joint correctness；说明完整输入词/字符计数守恒发生在选择之前，编辑后重新运行 selector。 |
| Related Work | 按事实组合、上下文证据使用、内部信号用于修复三条研究线组织。现有 2026 年 ACL/EMNLP 工作已足够相关，核实其正式发表信息并收紧定位，避免堆砌引用。 |
| 附录 | 增加证据范围导览与数值复现说明；保留完整组成问题结果、控制、参数、打分细节、逐运行结果、能力与成本数据。 |

核心定量证据保持不变：原生 composition failure rate 为 51.2/51.1/48.5%；固定原生失败集上的完整读出器 bridge accuracy 为 72.2/74.6/86.0%；access–pattern 交互为 +8/+5/+16 pp，95% 区间分别为 [1,14]/[0,10]/[8,25]；修复后的 composed EM 为 66.8/67.2/69.7%。模型顺序始终为 Qwen3-4B、Qwen3-8B、Llama-3.1-8B。

## 证据核对

本次重新聚合覆盖 90 个实验目录、991,680 条预测记录、12 组已发布读出器/状态拟合和 144 项聚合结果。另核对四臂 bootstrap 区间、300 组 identity token sequences、内容交换结果和参数元数据，未发现数值差异。详细证据见 analysis/internal/current_evidence_audit.md 与 current_audit/。

三个记录运行的 selected-head training traces 相同，因此文中将其称为 recorded runs，并明确 BF16/批处理几何带来的评估差异；采样不确定性由 source/quadruplet bootstrap 单独表达。论文也保留正式 source splits、实体重叠、先前开发数据使用范围及固定 restoration 规则。

当前源码快照缺少 coretrace.models 下的 native、deployment、head_slices 和 cpu_adamw 四个导入模块。数值重建已验证；完整 GPU 重跑需要补齐这些运行时实现。精确范围及文件位置见 analysis/REPRODUCIBILITY.md。此次没有创建新的模型实验，也没有更改原始实验记录。

## 图表与版面

正文四幅图依次承担具体案例、失败与地址信号、因果交互与地址控制、局部事实验证四种角色。两幅较长的概念流程图移至附录；正文保留三张紧凑结果表。新案例图为代码绘制的矢量图，数值图来自现有聚合输入。

最终使用上传稿原有的官方匿名 ICML 2027 模板，五个模板文件与官方发布逐字节一致。正文及核心图表在第 1–8 页，参考文献在第 9–10 页，附录在第 11–25 页；Impact Statement 与 AI Disclosure Statement 均在第 9 页。完整 PDF 已重新编译并逐页检查，修复了结果表滞后、孤立浮动页、段落被浮动页打断、数字串断行、参考文献两栏不均与未定义交叉引用。未改变模板字号、页边距或样式文件。

analysis/internal/current_pdf_qa.json 记录最终 PDF 哈希、字体/引用/溢出检查和页面审核结果。analysis/compile_paper.sh 提供独立编译；analysis/package_delivery.py 提供 Overleaf、图表与小输入重建包，并在独立解压目录验证重建。

## 本轮：按参考论文的章节内容量扩展到八页正文

用户要求在上一版七页正文基础上扩展为八页。我们比较了四篇参考论文的 section 内容量、机制解释深度及图表分工。两篇 ICML camera-ready 的实质正文均延续到第九页，因此本轮借鉴其内容分配，并保持当前投稿正文的八页边界。

Related Work 与 Conclusion 的篇幅已接近参考论文。本轮将新增内容集中于问题动机、可执行的诊断设计和结果解释。下表使用一致的英文词数估计，排除图表、图注、引用标记与公式；参考 PDF 的计数口径另见各比较报告。

| Section | 七页版 | 八页版 | 增加 |
| --- | ---: | ---: | ---: |
| Introduction | 521 | 707 | +186 |
| Related Work | 276 | 276 | +0 |
| Framework and method | 655 | 997 | +342 |
| Experiments | 1008 | 1454 | +446 |
| Conclusion | 114 | 114 | +0 |

总计增加约 **974 个英文词**。引言解释提供上下文为何便于诊断，以及从可恢复地址到有效使用证据的研究问题。方法补充 paired-query 设计依据、读出器标准化与状态匹配、四臂各自回答的问题、共享上下文与成组重采样。实验补充 matched controls 的解释、加性交互的数值示例、组件和歧义分支的控制关系，以及联合原始／编辑正确率的含义。

Llama 的 64+47−51=60% 是由既有四臂准确率得到的加性参照；76% 的组合结果相对这一参照给出已有的 16 点交互。817/822 的唯一候选正确数从已审计的附录提升到正文。所有新增解释均使用已有设计和结果。

最终正文八页包括全部核心图表与结论。声明和参考文献从第九页开始。原有字号、页边距、图表尺寸与模板文件保持一致；附录正文内容保持一致。

比较与核验记录：

- analysis/internal/eight_page_reference_icml.md
- analysis/internal/eight_page_reference_acl_aaai.md
- analysis/internal/eight_page_section_allocation.json
- analysis/internal/eight_page_revision_review.md

## 修改范围

全部仓库修改限制在 paper/ 与 analysis/。实验代码、数据、训练记录及预测归档保持原样。交付包的 SOURCE.json 与 delivery_manifest.json 记录对应 Git 提交、输入哈希和实际重建结果。
