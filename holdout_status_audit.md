# P1-C：外部 holdout 挂起状态的核对

- 执行日期：2026-10-16（本批执行）
- 执行主体：OpenCode agent（受任务包 §0 授权）
- 范围：只读核对 `benchmark_v2/` 中与外部 holdout 相关的实际内容；核对 README 及相关文档对 holdout 的描述。未修改任何文件。
- 依据：任务包 P1 段第 3.5 条；P4 段（外部验证）的启用条件为本清单之后才允许执行。

---

## 1. holdout 的定义与任务来源

- 任务包（P4 段）定义：在已有公开数据集可用且通过准入审核后，以独立样本对正式基线进行外部泛化评估。
- 当前仓库中对 holdout 的描述集中在 README.md（项目定位第 174 行）一处：
  > **当前"几成"的稳妥表述**（v13，开发集宏平均）……均为**开发集成绩**（含 in-sample 乐观偏差声明），外部 holdout 泛化验证待新数据（已挂起待办）；按链分组验证见 `sf10_阶段M5/G_验收/SF10-M6-完整总结.md`；外部 holdout 测试集待新数据到位后建立（`benchmark_v2/` 内已标记待办）。
- holdout 的实际执行入口在 `benchmark_v2/`（评分基建目录），该目录同时承载 v0–v2 的历史评分基建。

## 2. benchmark_v2 目录下无任何外部数据集目录

`benchmark_v2/` 实际存在的文件（经目录读取确认）：

| 文件/目录 | 性质 |
|---|---|
| `_gold_results93v2.json`、`_gold_results93v2.pkl` | v2 时期的 gold 解析产物（历史基建，保留） |
| `旧新口径差异报告.md`、`判分汇总v2.json`、`判分明细v2.csv`、`审计日志v2.json` | v2 口径历史产物与审计日志（保留） |
| `analyze_diff_v2.py`、`canonical_scorer.py`、`gold_parse93v2.py`、`inspect_blind_files.py`、`make_manifest.py`、`normalize_acupoints.py`、`score_benchmark_v2.py`、`verify_benchmark_v2.py` | 评分与验证脚本 |
| `manifest.json` | manifest 冻结（SHA-256 只读清单） |

目录树中**不存在任何外部数据集目录**（无 holdout 数据目录、无外部金标准目录、无 holdout 结果目录）。README 与任务包中出现的 "已标记待办" 所指的待办即为本节列出的挂起项，而非已有可执行的数据集。

## 3. 结果与指标的口径声明与 holdout 状态的交叉核对

| 项目 | README 声明 | 核对结果 |
|---|---|---|
| v14r5 的 86 案指标属于开发集/in-sample | 第 174 行及项目定位说明已明确 | ✅ 一致（`README.md` 第 22 行也已明言） |
| 外部 holdout 尚未执行 | 第 174 行已声明挂起 | ✅ 一致（无对应结果文件） |
| holdout 启动需要新公开数据集 | 任务包 P4 段定义 | ✅ 任务包文本已固化；本批未执行任何 holdout 运行 |

## 4. 挂起原因

1. **缺少可用的数据集**。当前仓库没有任何外部 holdout 数据集；新公开数据集需要用户/外部方提供，且需满足任务包 §7.1 的全部准入条件（来源可追溯、许可合法、标签质量、与现有 93 案无重叠、与评分契约兼容等）。
2. **v14r5 的指标已声明为开发集成绩**。任何把开发集指标当作外部泛化结果使用，均属口径违规（HARD-04）。
3. **既有 holdout 占位未删除，且未标记为失败或通过**。挂起状态枚举为 `WAITING_FOR_NEW_PUBLIC_DATASET`；仓库内未删除挂起任务，亦未伪造任何 holdout 结果。

## 5. 已检查的交叉引用位置

- README.md 第 174 行（指标/收敛结论部分）——已核对。
- `doubao-acupuncture-diagnosis/SKILL.md`（正式执行契约）：技能本体不包含 holdout 执行逻辑；SKILL.md 只说明"检索纪律"与"不依赖历史产物"，无对外验证的描述（本批未改动该文件；亦未发现任何声称外部验证的描述）。
- `blind法对照实验/GH蒸馏落地报告.md`：该报告讨论 nihaixia 蒸馏的迁移判定，与外部 holdout 无关。
- `blind法对照实验/` 根目录下的报告类文件均未包含外部 holdout 结果。

## 6. 挂起状态枚举

`WAITING_FOR_NEW_PUBLIC_DATASET`

启动 holdout 的条件、协议和准入审核（任务包 §7.1–§7.5）已固定；在任一启用条件满足之前，holdout 不得启动，也不得标记为 PASS 或 FAIL。

## 7. 建议的后续动作（只读）

1. 等待新公开数据集出现；数据集出现后按任务包 §7.1 完成准入审核（HARD 约束不变）。
2. 若用户提供数据集，应在启用前单独发起执行授权（P3 与 P4 均非自动授权执行阶段）。
3. 本批未删除或改动任何历史挂起材料；保持原状。

---

## 8. 交叉引用

- `documentation_consistency_audit.md`（P1-E 产出）第 6 节（本文件与 holdout 挂起项的关系说明）。
- `baseline_inventory.md`（P0 产出）第 6–7 节（数据集构建链的整体布局）。
