# 任务包 P0–P5 最终总报告（含 §10 结束声明）

> 本文件是任务包 P0 至 P5 阶段的累计交付与收尾报告。所有阶段均已在本会话内完成；本文件为新建文件，未改写任何既有文档的内容（HARD-01/HARD-02 范围内）。

- 执行日期：2026-10-16（本报告产出）
- 执行主体：OpenCode agent（受任务包 §0 授权执行 P0、P1、P2、P5；P3、P4 仅草案，未执行任何实验）
- 分支：`main`；本地提交链：`e403fdb → f98992d → ab0087e → 94851de → 6d01e27 → fe960e5`，均已推送至远端。

---

## 一、总述

本会话已完成任务包全部已授权阶段：

| 阶段 | 状态 | 关键交付 |
|---|---|---|
| P0 启动盘点 | ✅ 完成并推送 | `baseline_inventory.md`、`baseline_fingerprints.json`、`evidence_chain_inventory.md`、`p0_discrepancies.md` |
| P1 短期治理 | ✅ 完成并推送 | 收敛报告扩展（v10–v14 表、局限清单）、66 链状态清单、holdout 挂起声明、指南/覆盖对照差异与自动化核对依据 |
| P2 中期方案设计（只读） | ✅ 完成并推送 | 五份候选规则实验方案（M12-2 / 假阳性归因 / 次级信号 recall / 知识条目审计 / 链级归因） |
| P3 受控实验执行 | ⛔ 草案，未执行 | `P3_controlled_experiment_execution_protocol.md`（`BLOCKED_PENDING_AUTHORIZATION`） |
| P4 外部 holdout | ⛔ 草案，未执行 | `P4_external_holdout_execution_protocol.md`（`BLOCKED_PENDING_AUTHORIZATION`） |
| P5 自动化校验 | ✅ 完成并推送 | `check_contract_consistency.py`、`check_path_integrity.py`、`check_baseline_regression.py`（均只读，运行均通过） |

P3/P4 两个阶段未运行任何实验：任务包默认授权不包含受控实验执行与外部 holdout，这两个执行协议已按要求以草案形式交付，并明确标注阻塞，等待用户单独授权后再启用。

---

## 二、P0 — 启动盘点（只读核对）

- `baseline_inventory.md`：v14r5 为唯一正式基线；正式指标登记与基线指纹均与磁盘事实一致。
- `baseline_fingerprints.json`：`doubao-acupuncture-diagnosis/SKILL.md` 与 `doubao-acupuncture-disease...`（v14r5 副本）的 SHA-256 已登记，均与正式基线声明一致。
- `evidence_chain_inventory.md`：66 链、v12/v13 每链结果、v14r5 无每链结果、触发规则 9 条、holdout 挂起等全部核对完毕。
- `p0_discrepancies.md`：登记了发现的缺失/不一致项（`sf10_阶段B` 目录缺失、`盲法93_v2` 缺失、`盲法v14r5` 目录名引用错误、`失败模式归因.md` 缺失等），均仅登记，未自动更正。

## 三、P1 — 短期治理（只读核对 + 产物）

| 交付物 | 内容 |
|---|---|
| `blind法对照实验/技能迭代收敛报告.md` 扩展 | 追加 v10–v14 扩展表、当前局限清单（6.1–6.3）、P1 待办；未改写已有任何历史内容 |
| `blind法对照实验/sf10_阶段M5/E_分组验证/66_chain_status_inventory.md` 及 `.json` | 66 链状态；v12/v13 每链结果齐备、v14r5 无每链结果；v13 触发规则 9 条已登记 |
| `holdout_status_audit.md`（根目录） | holdout 挂起：`WAITING_FOR_NEW_PUBLIC_DATASET`，附挂起原因与准入条件 |
| `guide_asset_audit.md`（根目录） | 两份同名《诊断与针灸实施指南》差异（references 版为增量）已完整登记 |
| `documentation_consistency_audit.md`（根目录） | README / 移植说明 / 覆盖对照表 / 知识条目对照审计 / 变更记录交叉核对；登记 7 处差异（见 §七） |
| SKILL.md ↔ 针灸诊断交互页 交叉核对 | 契约 1–9、导出字段、输出模板语义一致；SKILL.md 未做任何改动 |

## 四、P2 — 中期方案设计（只读，未执行任何候选规则实验）

| 交付物 | 授权状态 | 说明 |
|---|---|---|
| `blind法对照实验/M12_2_ablation_protocol.md` | 设计完成，P3 执行 `BLOCKED_PENDING_AUTHORIZATION` | 验证 v14r5 = v14r2 + M12-2 的唯一性 |
| `blind法对照实验/false_positive_attribution_protocol.md` | 同上 | v12→v13 FP 逐一规则归因 |
| `blind法对照实验/secondary_signal_recall_protocol.md` | 同上 | 次级信号通道 recall 测量 |
| `blind法对照实验/knowledge_131_audit_protocol.md` | 同上 | 知识条目库 131 节可达性审计 |
| `blind法对照实验/chain_level_attribution_protocol.md` | 同上 | 66 链的链级归因；leave-one-chain-out 为未执行项 |

五份方案均为只读设计，未修改任何正式规则（HARD-01）或评分实现（HARD-03），未启动任何实验。

## 五、P3 / P4 — 执行阶段（未授权，未执行）

- `blind法对照实验/P3_controlled_experiment_execution_protocol.md`：受控实验执行协议草案。设计了隔离分支、只读对正式基线、不自动合入门禁、结果登记隔离等要求；执行入口标注 `BLOCKED_PENDING_AUTHORIZATION`。**未运行任何候选规则实验。**
- `blind法对照实验/P4_external_holdout_execution_protocol.md`：外部 holdout 执行协议草案，同样标注 `BLOCKED_PENDING_AUTHORIZATION`；holdout 挂起状态保持不变（`holdout_status_audit.md`）。

## 六、P5 — 自动化校验（只读，已实现并通过）

三个脚本均只读取文件、只打印报告、不写任何文件；均已实际运行并全部通过：

| 脚本 | 验证内容 | 结果 |
|---|---|---|
| `blind法对照实验/自动化校验/check_contract_consistency.py` | SKILL.md 引用的随技能携带文件齐全；references 目录无缺无余；v14r5 标记存在；九环节契约标记齐全；交互页具备问诊步骤与摘要导出 | ✅ 6/6 PASS |
| `blind法对照实验/自动化校验/check_path_integrity.py` | README 声明的核心路径（含 G_验收汇总、scorer、holdout 登记）均存在；实验目录由程序自动定位 | ✅ 全部 PASS |
| `blind法对照实验/自动化校验/check_baseline_regression.py` | README 的 v14r5 指标行可完整解析；canonical_scorer.py 存在且含主流程入口；正式基线登记文档齐全；JSON 比对为软校验（不一致只警告） | ✅ 通过 |

## 七、差异清单（只读登记，未自动更正）

1. README 第 214 行：`blind法对照实验/盲法v14r5/` 不存在，实际目录为 `盲法140/`（D1）。
2. README 第 74 行：`失败模式归因.md` 不存在，其内容疑承载于 `真盲法对照实验报告.md`（D2）。
3. `移植说明.md` 第 10–17 行：包结构描述仍按旧 `skill包/` 嵌套结构（D3）。
4. `移植说明.md` 第 13、16 行：references 实际有四份随技能携带文件，但声明为“三份”（D4）。
5. `移植说明.md` 第 32–33 行：知识条目库数量写为 “2239 条”，实际为 131 节（D5）。
6. `知识条目对照审计.md` 第 4–7 行：审计对象声明 “（2239 条）”，与知识条目库实际 131 节不一致（D6）。
7. 另有两处非阻塞信息：`sf10_阶段B` 目录缺失、`盲法93_v2` 目录缺失（README 第 61–64 行通配写法未覆盖实际缺口，D1 中已登记）；`教程.txt` 为 GBK 编码而 `教程_utf8.txt` 为 UTF-8 版（README 未作说明，属轻微口径不严，非阻塞，D7）。

更正以上任何一项都须经单独授权，且不得触碰正式规则文件或正式指标登记（HARD-01/03/05）。

## 八、交付物清单（含路径）

- 根目录：`baseline_inventory.md`、`baseline_fingerprints.json`、`evidence_chain_inventory.md`、`p0_discrepancies.md`（P0）；`holdout_status_audit.md`、`guide_asset_audit.md`、`documentation_consistency_audit.md`、`final_task_package_report.md`（本文件，P1/P5 产物）；`局限与目标整理.md` 为既有文件，未改动。
- `blind法对照实验/`：`技能迭代收敛报告.md`（扩展）、`sf10_阶段M5/E_分组验证/` 下 66 链状态清单；`M12_2_ablation_protocol.md`、`false_positive_attribution_protocol.md`、`secondary_signal_recall_protocol.md`、`knowledge_131_audit_protocol.md`、`chain_level_attribution_protocol.md`；`P3_controlled_experiment_execution_protocol.md`、`P4_external_holdout_execution_protocol.md`；`自动化校验/` 下三个校验脚本。
- 正式基线目录 `doubao-acupuncture-diagnosis/` 与 `canonical_scorer.py` 均未做任何改动（SHA-256 完全一致）。

## 九、授权与合入门禁回顾

- 默认授权范围内已执行：P0（只读核对）、P1（只读核对/产物）、P2（只读方案设计）、P5（只读自动化）。
- 超出默认授权的执行（P3 实验执行、P4 holdout、任何正式基线变更、任何规则编辑）未执行，未自动合入任何结果；全部已按 `BLOCKED_PENDING_AUTHORIZATION` 标记交付。
- 正式指标登记未被改写；候选规则实验全部在本地隔离，未合入 `main`。

## 十、停止声明

任务包授权范围内已完成全部可执行工作（P0、P1、P2、P5 完成并推送；P3、P4 仅草案并明确阻塞）。

**本会话即刻停止：不自动进入下一阶段，不自动发布 Release，不自动合入任何候选结果。用户如需启用 P3（受控实验执行）或 P4（外部 holdout），须单独授权；授权后由用户明确指示，由授权阶段接手执行。**


---

## 十一、后续文档差异修正状态（2026-10-17，追加）

本节记录最终总报告产出后的后续工作；不改写前述 P0–P5 历史执行记录。

- **隔离分支**：`docs/correct-documentation-drift-2026-10-17`
- **审查入口**：[Draft PR #1](https://github.com/I5858555255/nhx-acupuncture-diagnosis/pull/1)
- **当前状态**：文档更正已提交并完成静态路径核对；PR 尚未合并。原 `main` 基线不变。
- **修正范围**：README 的失效路径和缺失目录说明；移植说明的当前目录结构、四份 references、131 节当前计数与完整目录复制要求；知识条目审计中历史“2239 条”与当前“131 节”的范围隔离；教程编码说明。
- **保护声明**：没有修改 `SKILL.md`、正式诊断规则、`canonical_scorer.py`、正式指标、数据集、原始实验结果、`_backup/` 或 `_archive/`。
- **验证限制**：已通过 GitHub API 检查文件和目录存在性；当前环境无法直接克隆仓库，因此本次未重跑 P5 三个 Python 脚本。此前总报告记录的脚本通过结果是历史运行记录，不应被说成本次复测结果。
- **未执行事项**：P3 受控实验仍为 `BLOCKED_PENDING_AUTHORIZATION`；P4 外部 holdout 仍为 `WAITING_FOR_NEW_PUBLIC_DATASET` / `BLOCKED_PENDING_AUTHORIZATION`。本次授权范围为文档修正，不扩大到实验或规则合入。
- **下一门槛**：审查 PR diff；在用户另行批准前，不合并到 `main`。

---

## 十二、P5 复测补记（2026-10-17，追加）

第 11 节「验证限制」记载的“本次未重跑 P5 三个 Python 脚本”，对应当时的执行环境（无法克隆仓库）。后续已在本机完整仓库副本中完成复测：将 PR 分支检出到独立 `git worktree`（未改动 `main` 工作区），运行三个只读脚本：

- `check_contract_consistency.py`：6/6 PASS，exit 0。
- `check_path_integrity.py`：全部 PASS，exit 0。
- `check_baseline_regression.py`：exit 0，4 项中 3 PASS、1 WARN。

已知 WARN：正式判分 JSON（`sf10_阶段M5/G_验收/判分汇总v14r5.json`）为 0–1 小数口径（实测如 `0.3762`、`0.5185`），README 为百分比口径；脚本按设计告警但不判失败，该口径差异未修复，也不得表述为“全部无警告通过”。

本补记只更新复测状态，不覆盖第 11 节及第一至十节的历史记录；复测不扩大既有验证结论的适用范围（不构成诊断规则验证、外部泛化验证或 131 节知识条目全量审计完成的证明）。PR #1 仍为 Draft、未合并；P3 / P4 仍未执行。
