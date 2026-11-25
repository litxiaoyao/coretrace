# CoReTrace V5 修订交接：直接交给 Codex 执行

## 0. 目标与约束（优先级最高）

基于已审核的 GitHub `main` 快照 `5ff9f52179a72f911db319c52270121d78de92b0`，合并本包的 V5 论文修订、利用现有结果补齐机制证据，检查确实缺失的结果后，仅补一次最有价值的 token-level 机制采集。完成正式 ICML 模板编译、逐页 QA、commit、push 和远端核验。请保留 Introduction、Related Work、Methodology、Experiments、Conclusion 五个一级章节，正文必须正好 8 页；保留 Figure 1 teaser、Figure 2 diagnosis framework、Figure 3 repair framework。

**仅允许新增或修改 `paper/`、`analysis/`。** `coretrace/`、`scripts/`、`outputs/`、`data/`、模型权重、训练设置均只读。若本地尚有未上传的合法模型模块、checkpoint 或采集缓存，优先从用户现有工作环境读取，不要覆盖、训练或修改这些目录。若必要依赖不可用，报告准确路径和缺失项，完成其余步骤。不要为了支持预期故事选取有利样本、伪造结果、修改指标或重新选择已冻结头集；也不要增加防御性正文段落。所有结果（不论方向）保留在分析文件中，按实测结果决定论文表述。没有实验数据的可选图不得当作实测图插入正文。

本包是**相对于完整仓库的覆盖包**，不是独立项目。它只包含需要替换/新增的文件。不要从独立预览中复制模板、旧附录 PDF 或 `paper/main.pdf`。本地 V5 主文预览是 8 页、12 张 Figure，已使用本地转录的 ICML 版式编译并检查。完整官方模板和全部附录尚未在该隔离环境重新编译，必须在你的完整 checkout 验证后才覆盖 `paper/main.pdf`。没有执行远端 push。

## 1. 先审核已有结果：不要重复实验

此次审核读取了当前 commit 的完整 Git tree（GitHub API 返回 1,183 个文件/目录条目，`truncated=false`），并检查下列代码与结果。链接固定在审核 commit，可直接对照。此审核可以确认**当前仓库中未见对应记录**，不能证明用户本地、未推送分支或过去所有历史从未运行过。Codex 必须再查本地及现有完整结果，不得把缺少上传文件等同于没运行过。

| 项目 | 证据路径 | 结论 |
|---|---|---|
| Ranked vs. random head knockout | `analysis/figure_data/data_main_head_causality.csv`; `outputs/{model}/causal_necessity/summary.json` | 已有 0/20/40/80 dose、1,000 test sources、三类问题。chosen dose 20/20/40；composed EM ranked 7.4/5.5/6.4，random 24.4/27.3/29.4；direct-target ranked 1.1/1.0/6.5，random 51.5/53.5/58.9。已有对照，不重复运行。每个 dose/model 只有一个 layer-matched random set，不声称随机头微调 superiority。 |
| Head function | `analysis/internal/v3_structure_evidence.md`; `analysis/figure_data/data_main_structure_function_*` | 现有真实 head profiles、query-dependent switch、random profiles；不重新定位。 |
| Bridge vs. root/other 质量校准 | `analysis/internal/v3_causal_evidence.md`; `outputs/{model}/causal_access/summary.json` | 已有，保留同一固定 subgroup 169/174/209；不要把 174 改成 176。 |
| Route × Read factorial | `scripts/factorized_causal.py`; `outputs/{model}/causal_factorization/summary.json`; `analysis/internal/v3_causal_evidence.md` | 25 discovery quadruplets/100 receivers；四臂及 identity 对照、交互区间、joint-only outcomes 已有，不重复。 |
| 事实交换 | `outputs/{model}/seed42/causal_content/summary.json`; `analysis/internal/mechanism_case_records_20261125_v2.json` | 已有；保留 Angela 双重案例，不需重新生成预测。 |
| Native vs. adapted paragraph routing | `outputs/{model}/native_readout/features.jsonl.gz.part*` 和 `outputs/{model}/seed42/readout/features.jsonl.gz.part*`; seeds 43/44 也有 | **两套原始特征档案均在当前树里**。属于已有实验的离线再分析，不是补实验；先直接读取。 |
| Projection restoration | `analysis/figure_data/data_app_ablation_aggregated.csv` | 已有，V5 Figure 12 已从原记录绘制。First-hop +5.0/+2.4/+27.3pp；all-three +2.4/+0.8/+17.5pp。 |
| General capability | `paper/tables/main_retention.tex`; `paper/tables/capability_full.tex` | 已有 HotpotQA/MMLU/GSM8K；不追加 benchmark。V5 正文说明实测正向结果，完整表保留全部数值。 |
| Native vs. adapted token-conditional reading | `coretrace/mechanisms/localization.py`, `coretrace/mechanisms/paragraph_attention.py`, `scripts/readout.py`, `scripts/factorized_causal.py`, `coretrace/mechanisms/factorized_attention.py` | 当前 `capture200` 和 `readout/features` 保存 paragraph masses（`all_question_mean`, `last_question`），factorial donor conditional 在内存中生成；ledger 写出的 events 是 mass、alpha-delta L2 等摘要，不包含完整 token 向量。V3 causal audit 明确记录该限制。**未发现完整的同输入 Native/Adapted token capture**，唯一可能需要新 GPU 采集的项目。 |

可直接阅读原始证据（固定版本）：

- https://github.com/litxiaoyao/coretrace/blob/5ff9f52179a72f911db319c52270121d78de92b0/analysis/internal/v3_causal_evidence.md
- https://github.com/litxiaoyao/coretrace/blob/5ff9f52179a72f911db319c52270121d78de92b0/analysis/figure_data/data_main_head_causality.csv
- https://github.com/litxiaoyao/coretrace/blob/5ff9f52179a72f911db319c52270121d78de92b0/coretrace/mechanisms/localization.py
- https://github.com/litxiaoyao/coretrace/blob/5ff9f52179a72f911db319c52270121d78de92b0/scripts/readout.py
- https://github.com/litxiaoyao/coretrace/blob/5ff9f52179a72f911db319c52270121d78de92b0/scripts/factorized_causal.py

不要补 LoRA、random-head fine-tuning、额外 held-out factorial、wrong-relation donor transplant 或新 benchmark；本轮目标不是完整 PEFT benchmark。wrong-relation **只读观测**可通过同一 bridge 的另一个直接问题获得，和 donor transplant 是两件事。没有新增训练对照的前提下，不写“优于随机头微调/LoRA”。

先运行：

```bash
git status --short
git rev-parse HEAD
git ls-tree -r --name-only HEAD | grep -Ei 'factorization|necessity|readout/features|capture|token.*(att|read)|relation.*donor|adapt.*rout' || true
```

再查看工作树的未跟踪/忽略文件与用户本地原始 capture/result 目录，搜索 `conditional`/`donor_bank`/`source_prefix_ids`/`bridge_token_ids` 及相同 checkpoint、head IDs、receivers 对应的输出。**只读搜索，不删除或重跑。** 发现完整合法结果就把其转换成本文要求的 analysis JSON/CSV（保留原始来源哈希），跳过对应采集。若已有部分 capture，只补缺失的状态/模型/receiver，保持原协议。请把最后的检查结论写进 `analysis/CODEX_V5_EXECUTION_REPORT.md`。

## 2. 安装 V5 覆盖包并编译

用户会把 ZIP 放到仓库根目录。若 Codex 是从包含该 ZIP 的最新 checkout 启动，首先确认工作树无未处理冲突；若已有其他版本，不要 reset，不要盲目覆盖用户的新修改，先比较差异。只提取 `paper/` 和 `analysis/`，保留目录结构。可以先 `unzip -l CoReTrace_V5_repo_overlay.zip`，再从仓库根目录 `unzip -o CoReTrace_V5_repo_overlay.zip`。若已有本地修改，手动合并。ZIP 的根路径不存在需要安装到 `data/` 或 `outputs/` 的文件。

```bash
python -m py_compile analysis/apply_story_revision.py analysis/capture_paired_relation_reading.py analysis/derive_story_relation_reading.py analysis/derive_story_adapted_routing.py
python analysis/apply_story_revision.py --compile
```

`apply_story_revision.py` 校验原版 `analysis/plot_results.py` Git blob（`4edfa337e0b9c5cabec22128f2db25d8c8e4d17a`），将 `analysis/story_revision_plot.inc` 的 V5 block 合并进原有唯一绘图入口，并保留全部旧 collectors/`--only` choices。若已合入 V4，更新该 block；如仓库有新改动导致哈希或锚点不匹配，手动合并，不能将原绘图代码替换成本地精简版。该安装器更新附录里的旧 Walter teaser 文字为 Corvinus 例子（不要破坏其他附录内容），重绘 V5 figures、调用仓库现有 `analysis/compile_paper.sh`。保留原 `paper/icml2027.sty`、`.bst`、bibliography、appendix、原表格生成器及真实原数值。本包 `paper/main.tex` 已去掉本地预览的回退分支，正式编译必须包含原有附录及 bibliography。

数值溯源：`data_revision_*` CSV/JSON 是从仓库原审计和结果提取的紧凑绘图视图，非新实验。核对其源字段和数字，尤其 `data_revision_joint_counts.csv`、`data_revision_content.csv`、`data_revision_mechanism_repair.csv`。Figure 12 直接读取已有 `data_app_ablation_aggregated.csv`，本包不覆盖该完整 CSV。优先使用已有生成结果；如果需要重建该 CSV，只用原 `plot_results.py --only ablation`。不要改已冻结实验数据。保留旧 figure 文件及附录 refs；确保 manuscript 引用新图的正确编号。

如编译失败，检查 `analysis/build_story_revision/main.log` 和 `compile_stdout.txt`。调整正文排版而不是模板。结论应在第 8 页，Impact Statement 从第 9 页开始。需要用 `pdftotext -layout` 和 `pdftoppm` 检查所有页，不能仅靠自动页数断言；本地 V5 已按原 `main_results.tex` 表格实际内容排版。正式版若有版式差异，可以调整图宽/图注/段落分页，但不得拆分一级章节、减少 Framework、缩小官方字号或更改页边距。真实论文中不要出现 placeholder 或 `??`。

## 3. 已有实验的离线再分析（必须先执行，无 GPU）

现有 archive 的代码确认保存了 `features[layer].all_question_mean[head][paragraph]`、`last_question`、`heads`、`prompt_tokens` 及 paragraph key counts，因此可直接比较适配前后 raw attention mass。不需要重新运行 readout 或训练。

```bash
python analysis/derive_story_adapted_routing.py --seed 42
```

该脚本读完整或拆分 gzip，不修改输入。比对 native/seed42 adapted+restored 的 1,000 个 test source、question ID、head set、prompt token counts、paragraph counts/keys、标题顺序、root/bridge 索引；以原始 canonical core native 三问预测定义固定 native failure subgroup 234/236/243。平均 raw paragraph mass（不取 log，不把 root+bridge 归一化为 1），按相同 source 配对计算 Native/Adapted 两个位置的变化和 95% source bootstrap。另保留 all_test 结果。归档缺失时先检查已有文件、恢复/读取本地原档案或已有上传的 split parts（不重跑推理）；脚本须能读取仓库现有 schema。不要把 test-side 未知标签用于部署 reader 或训练。

必须输出（commit 到 `analysis/figure_data/`）：

- `data_revision_adapted_routing.csv`（aggregate，all test + fixed native failures，root/bridge，各模型、n、均值、差值、CI）
- `data_revision_adapted_routing_receivers.csv`（3,000 个 matched source rows）
- `data_revision_adapted_routing.manifest.json`（source files SHA-256）

若方向没有发生预期变化，照样保存并报告，不能强写 adaptation increases bridge mass。该比较是同输入的**状态差异**，不是独立因果干预或单个 Q/K/V/O 成分的证明。若 feature alignment 失败，明确报告 mismatch 和输入路径，不用不匹配的结果绘图。

## 4. 唯一补实验：同输入的 relation-conditioned token-level reading

### 为什么确实值得补

现有 factorial 已证明在所测试设置下，routing 与 reading 的效果相互依赖；现有 case 表明正确 relation value 能被联合干预修复。现有 readout 证明 adapted/restored 的地址信息更易读出。然而没有完整的适配前后**桥段内部 token 分配实测图**，无法直观连接 Read 和修复。补一个轻量的只读 prefill capture 即可；不重新训练、不做额外对照训练、不改变原数据。

### 最小协议

优先复用本地已保存、且与同一模型 checkpoint/冻结 head set/原始输入可核验的 vector banks。若缺失，使用 `analysis/capture_paired_relation_reading.py`。这是一个实验族，建议先做 Llama-3.1-8B-Instruct：固定 `natural_crossed_3e05970d5c8422f2710d__C12` (Angela → Rebecca Miller → Inge Morath)，然后在原 25 个 discovery quadruplets 的全部 100 个 receiver 上重复同一协议。Qwen3-4B/8B 的同协议采集仅在 checkpoint 和算力方便时补全，用于检验跨模型一致性；若 Llama 一例/一模型，最终稿必须称其为代表性机制分析，不声称全部模型的 adapted token pattern 都如此。无模型训练或完整生成 benchmark。每个 eligible receiver 最多四次只读 forward，单模型完整协议最多 400 次 prefill，可复用重复的 direct-query captures。Pilot 本身不用于统计总体效果。

四个状态在相同 frozen shared context 上测量：

1. `native_composed`: native 原 composed query。
2. `native_direct_same_relation`: 显式命名同一 bridge，询问同一 relation/value 的配对直接问题。
3. `native_direct_other_relation`: 同一 bridge、同一 context、另一个已存在的 relation 的直接问题，只读观测而非 donor transfer。
4. `adapted_composed`: 已训练 seed42 head slice checkpoint + 原模型固定 V/O restoration scope，仍用**相同 full-context composed query**，不先执行 evidence selection，以免把 prompt 变化混作内部机制变化。

冻结条件：沿用 `outputs/{model}/discovery/SELECTION_FROZEN.json`（20/20/40 heads）、原 tokenizer chat template、original shared contexts、最后一个 question token row（与 native donor 一致）。严格核对 bridge token indices、source prefix token IDs、answer span offsets 和冻结 head IDs；原始支持句中定位两个 relation 对应的真实 value token spans。所有可匹配且 span 唯一不重叠的 receiver 都进入分析，按几何条件过滤、不根据预测正误/方向挑选。记录排除原因和完整 denominator。保存 per-head `m`（bridge mass / row total），完整 `rho`（within-bridge conditional distribution），两个 relation value span 的 `sum rho`、length-normalized rho、`mean_h(m_h * sum rho_h)`（绝不能用 `mean(m)*mean(rho)` 代替）。保存 token IDs、文本、精确 span indices、query/receiver ID、head IDs、raw records，核对 checkpoint、scope、budget、dataset/hash。仅在所有状态共有的有效 heads 上配对平均；不得把无效 mass 置为虚构的 uniform distribution。对差值按完整 quadruplet cluster bootstrap，报告 n、cluster 数和 CI。保留所有实际结果，无论方向。

### 实际命令（Codex 先解析真实路径）

从原 `outputs/configs/*_causal_factorization.json`、`outputs/{model}/seed42/head_tuning/training.json`、readout/evaluation manifests、`configs/experiments.json` 找本地原模型、checkpoint 与实际固定 scope；不要猜 checkpoint 或硬编码不存在路径。原 `scripts/readout.py` 的 `DeploymentBody` + `active.session(entry)` 是 adapted/restored prefill 的复用方式。若模型加载模块/权重/checkpoint 在当前 GitHub snapshot 不全，检查用户本地已有版本；若缺失则报告，不训练或改其他目录。脚本已经通过 syntax 和 plan 检查，但未在当前环境运行真实模型，Codex 应先核对模块 API 和 schema，必要修正只能在 `analysis/`。若已经有等价真实 token captures，直接导出，不执行下面的 GPU 命令。

```bash
# 替换成从原 manifest 和用户环境核实的真实路径；先 plan，再 --run。
MODEL=/absolute/path/to/original/Llama-3.1-8B-Instruct
CHECKPOINT=/absolute/path/to/existing/seed42/head_tuning/checkpoint_dir
SCOPE=/absolute/path/to/original/frozen_scope.json
BUDGET=outputs/llama3_8b/discovery/SELECTION_FROZEN.json
python analysis/capture_paired_relation_reading.py \
  --model-id llama3_8b --dataset data/CoRe-2Wiki-v1.0 \
  --model "$MODEL" --budget "$BUDGET" --checkpoint "$CHECKPOINT" --scope "$SCOPE" --case-only
# 如未找到现成 pilot，验证命令后采集。
python analysis/capture_paired_relation_reading.py \
  --model-id llama3_8b --dataset data/CoRe-2Wiki-v1.0 \
  --model "$MODEL" --budget "$BUDGET" --checkpoint "$CHECKPOINT" --scope "$SCOPE" --case-only --run
# 校验 pilot 后，完成原固定 100 receiver（不要以 pilot 为统计总体）。
python analysis/capture_paired_relation_reading.py \
  --model-id llama3_8b --dataset data/CoRe-2Wiki-v1.0 \
  --model "$MODEL" --budget "$BUDGET" --checkpoint "$CHECKPOINT" --scope "$SCOPE" --run
# 如果 Qwen 也有现成或新增的完整 capture，可在下列命令增加其真实 JSON 路径。
python analysis/derive_story_relation_reading.py \
  analysis/figure_data/data_revision_relation_reading_llama3_8b.json
```

如果 pilot 已存在，跳过 pilot 重跑；完整 script 的固定队列包括 pilot receiver，Codex 可直接复用已核验的单例四个状态，避免重复前向；若完整数据已存在，直接 derive。旧 V4 的 `capture_story_attention.py` 保留作为单例兼容入口，并非第二项必须补实验；不要重复执行两个 capture 脚本。预先检查硬件、stage 配置与 frozen scope。不要修改 `coretrace/` 或 `scripts/` 来迁就本次分析。若不能完整运行，保存已真实获得的数据和原因，不伪造其余状态。

必须保留给下一轮修改的结果：

- `data_revision_relation_reading_{model}.json`：完整 100 receiver 采集的 raw bank、有效/排除列表、真实模型/ckpt/scope/数据来源和 hash；pilot 单独命名 `_pilot.json`。
- `data_revision_token_capture.json`：Angela 的兼容测量 JSON（单例的 `span_weights`、`conditional_mean`、token IDs、原始 bank；当前 plotting 读取此文件）。若来自 pilot 与全量的同一 checkpoint 与冻结输入，核验一致即可复用；不可将不一致的状态混用。
- `data_revision_relation_reading_summary.csv`、`data_revision_relation_reading_receivers.csv`、`data_revision_relation_reading_manifest.json`：aggregate 对照、每个 receiver/状态和真实输入 SHA-256。`conditional_margin` 为目标 span 减同 bridge 另一个 relation span 的 conditional mass，`absolute_margin` 按 head 乘 `m*rho` 后平均。另保留 per-token length-normalized margin。两个 paired contrasts: adapted composed vs native composed；native direct same vs native direct other。正负值均报告。

不要把观测结果描述成 causal mediation 或 strict stage。不要把 discovery 样本误称 independent held-out。现有四臂因果证据与新观测互补，不把后者强行包装成因果。

## 5. 重绘、正式编译、QA、上传

```bash
python analysis/plot_results.py --only story_revision
python analysis/apply_story_revision.py --compile
```

`story_revision` 会产生新图的 PDF/PNG，并用现有 `data_revision_*` 真实结果填充可选 panel：`data_main_adapted_routing_optional`、`data_main_token_reading_optional`、（有完整 summary 时）`data_main_relation_population_optional`。如数据还缺失，前两图明确是 `Awaiting measured ...` placeholder；**均不在 V5 当前正文引用**。保留 V5 真实主文，生成并上传 measured optional figures 和 source data，下一轮 ChatGPT 将根据实测方向决定正文的图、结论和 8 页分配。不要擅自添加虚构的图或在主文预写支持假设的结论；不要拿可选图直接覆盖另一个图的 caption。V5 Figure 12 是已完成的 restoration 消融，不应被替换为 placeholder。

编译后的检查：

```bash
pdfinfo paper/main.pdf
pdftotext -layout paper/main.pdf analysis/build_story_revision/final_text.txt
pdftoppm -r 130 -png paper/main.pdf analysis/build_story_revision/page
# 人工逐页看渲染：正文字体/大小/图注、Fig1-3、12 张正文图、行列及留白、引用、附录编号、所有浮动、无重叠/裁切；结论第8页，Impact第9页。
git diff --check
git status --short
git diff --stat
```

检查 `paper/main.pdf` 的实际内容，不能只看 LaTeX。若正式编译图漂移，修正源文件并重新编译和渲染。`paper/main.bbl` 与正式编译一致。正式 Overleaf zip 由安装器在 `analysis/build_story_revision/CoReTrace_Overleaf_full.zip` 创建；它使用原 `.sty/.bst/.bib`、正文、附录及图表，可另存作交付，不必将全部 build/cache 文件提交。请检查原有 appendix 的 figure/table refs，保留原已生成表，尤其正确恢复 `fig:joint_rescue` / `fig:structure_function` / `eq:ranking` / `eq:interaction` / `fig:access_controls` 的交叉引用；如 `cleveref` 把 appendix 的 figure 编号识别错误，修复 labels 与 counter（不得硬编码错编号）。核对 V5 teaser、标题、running title、附录案例一致。

把以下信息写入 `analysis/CODEX_V5_EXECUTION_REPORT.md`：

- 起始 commit 与工作区检查；是否发现同实验已有本地结果（路径、hash、复用状态、哪些新采集）。
- 离线 routing：每模型有效 n、root/bridge 原始均值、delta/CI、匹配 QA；token capture：实际模型、checkpoint/scope、receiver/head counts、各状态和差值/CI、排除原因、原始数据/figure 路径；如未运行说明具体 blocker，保存已完成结果，不要求重复旧实验。
- 本轮实际修改文件、正式编译页数/引用/逐页视觉检查、未解决的问题。提供 source/figures/CSV/JSON 路径与确认 output `paper/main.pdf` 同步。

**只提交 `paper/` 和 `analysis/` 的必要修改**。不要 `git add -A`，不要提交 build 目录、TeX runtime、cache、模型或训练数据、用户上传的根目录 ZIP（若 ZIP 已由用户提交则不要删除或修改它）。先查看状态并显式 stage，含已合并的完整 `analysis/plot_results.py`、新脚本、数据视图、实际结果、图 PDF/PNG、修订 tex、原有完整附录修订、正式 `paper/main.pdf` 与 `.bbl`、本说明和执行报告。不要假设脚本编译成功等于视觉 QA。若完整 GPU capture 被阻塞，仍提交已验收的 V5 与离线结果和真实 blocker。不要把 preview PDF 或旧 backmatter 作为正式产物提交。

```bash
# 只 stage 确认过的改动；先排除所有 build/cache，再 commit。
git diff --cached --name-only
git diff --cached --check
# git commit -m "Polish CoReTrace story and derive paired mechanism evidence"
# git push origin HEAD:<target-branch>
# git fetch origin <target-branch>
# git rev-parse HEAD
# git rev-parse origin/<target-branch>
# git ls-remote origin refs/heads/<target-branch>
```

最后报告真实 commit URL `https://github.com/litxiaoyao/coretrace/commit/<verified-sha>`、是否远端一致，以及供下一轮审阅的 `paper/main.pdf`、measured figures、summary/receiver/capture 文件路径。没有完成的工作明确列出，不可声称已推送未执行的操作。

## 6. V5 已实现的文章修改（不需补实验）

- 五个一级 Section 原样保留；标题和 abstract 以 routing-reading interaction 为主科学发现。
- 前三张图保持 teaser + diagnostic framework + repair framework，统一 Corvinus 和 Angela 叙事；实际 head-level 配对、random knockout、地址可恢复性、四臂干预、joint-only corrections、reciprocal fact exchange 均有真实来源。
- 第 5–6 页加强 selected/random 直接第二跳对照，明确 same-set query preference 与 bridge-specific route 的联系；第 7 页保留 Angela 双重案例；第 8 页强化从 adaptation → 地址 readout → ambiguity choice → answer 的证据链。
- 新增 Figure 12：既有 projection restoration 消融的 first-hop 与 all-three paired comparison，帮助解释 restoration 组件为何有价值。正文已有 HotpotQA 与 GSM8K capability 结果描述，完整表保留在附录；不引入未经支持的“generalization of mechanism”或“无损”的 claim。
- 本地预览检查为 8 页、12 张 Figure；已有正向证据的写作已改，不等新实验。最终模板和附录编译由 Codex 在原 checkout 执行。
