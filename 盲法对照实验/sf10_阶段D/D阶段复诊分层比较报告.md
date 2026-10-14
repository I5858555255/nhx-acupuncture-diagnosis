# D阶段 复诊分层比较报告：v10 symptom-only vs v10 history-aware

- 日期：2026-10-14
- 口径：**完全沿用 benchmark_v2**（normalize_acupoints + gold pkl chain_map + 点级宏/微 P/R/F1/Jaccard，main=主穴/all=主+佐）。
- 两模式**分别评分、分数不合并**。
- 注：hist 合并文件 `_blind93v10_hist_results.json` 截断（仅 21 案，停在 160_01）；本评分从其 5 个分片 `_part1..5.json`（合计 93 案齐全）合并读入，未改动原文件。

---

## ① 两模式汇总对照表（宏平均）

### main（主穴）

| 模式 | recall | precision | F1 | Jaccard | 单元均 | 点均 | TP总 |
|---|---|---|---|---|---|---|---|
| v10 symptom-only | 0.4125 | 0.3732 | 0.3685 | 0.2440 | 6.37 | 7.87 | 245 |
| v10 history-aware | **0.4355** | **0.3931** | **0.3892** | **0.2627** | 6.50 | — | — |

### all（主+佐，宏）

| 模式 | recall | precision | F1 | Jaccard |
|---|---|---|---|---|
| v10 symptom-only | 0.4725 | 0.3494 | 0.3789 | 0.2487 |
| v10 history-aware | **0.4953** | **0.3668** | **0.3982** | **0.2652** |

history-aware 在 main/all 四项指标上**全面优于 symptom-only**：main recall +2.3pp、precision +2.0pp、F1 +2.1pp、Jaccard +1.9pp。

### 分布（recall_main）

| 档 | symptom-only | history-aware |
|---|---|---|
| 100% | 7 | 8 |
| 80–99% | 2 | 3 |
| 60–79% | 11 | 12 |
| 40–59% | 22 | 20 |
| <40% | 44 | 43 |

- **零命中案**：symptom-only = {201_01, 207_01, 318_01}；history-aware = {207_01, 318_01}。**hist 救回 201_01**（0命中→TP=2）。
- **满分案**（hist）：107_01、216_02、22_01、23_01、274_01、312_01、340_01、355_01（8 案）。

---

## ② 逐案差异表

- 86 案中：**变化 9 案、无变化 77 案**。
- 集合差异性质：history-aware 仅在复诊/延续案上补回既往针穴（如 216_02 补内庭/足三里/阳辅、156_06 补水道/章门/足三里），首诊/锚案主穴集合与 symptom-only 完全一致。
- 逐案 sym/hist 两模式 recall/f1/jac/TP 新旧列见 `判分汇总v10_hist.json.逐案`。

---

## ③ 复诊分层比较

### A. 按 chain_map（gold 复诊链）

| 层 | n | 模式 | recall | precision | F1 | Jaccard |
|---|---|---|---|---|---|---|
| followup（复诊跟随） | 20 | symptom-only | 0.2490 | 0.3206 | 0.2765 | 0.1697 |
| followup | 20 | **history-aware** | **0.3327** | **0.3995** | **0.3554** | **0.2423** |
| anchor+first_visit | 66 | symptom-only | 0.4621 | 0.3892 | 0.3963 | 0.2665 |
| anchor+first_visit | 66 | history-aware | 0.4667 | 0.3912 | 0.3995 | 0.2689 |

**followup 层是 hist-aware 的主战场**：recall +8.4pp、precision +7.9pp、F1 +7.9pp、Jaccard +7.3pp，全面大幅提升；anchor/first-visit 层几乎不动（recall +0.5pp），证明历史感知只作用于复诊案、不污染首诊。

### B. 按阶段C visit_type（组装清单.csv）

| 层 | n | 模式 | recall | precision | F1 | Jaccard |
|---|---|---|---|---|---|---|
| 复诊 | 44 | symptom-only | 0.3390 | 0.3872 | 0.3461 | 0.2192 |
| 复诊 | 44 | history-aware | 0.3504 | 0.3988 | 0.3575 | 0.2317 |
| 首诊 | 24 | 两模式 | 0.6409 | 0.4040 | 0.4690 | 0.3300 |

visit_type 口径下复诊层 recall +1.1pp、F1 +1.1pp（该口径复诊案更多、含非链案，增益小于纯 followup 链）；首诊两模式完全一致。

### C. 8 个有既往针穴清单的延续案逐案对比

| 案 | gold穴数 | sym TP | hist TP | sym recall | hist recall | 延续补穴效果 |
|---|---|---|---|---|---|---|
| 156_06 | 10 | 3 | **6** | 0.30 | **0.60** | hist 补三皇穴（水道/章门/足三里） |
| 199_01 | 7 | 1 | **2** | 0.143 | 0.286 | hist 补三阴交（=198+耳眼点链） |
| 200_01 | 7 | 1 | **2** | 0.143 | 0.286 | hist 补三阴交 |
| 201_01 | 9 | **0** | **2** | 0.000 | 0.222 | **救回零命中**（补三阴交/太冲） |
| 202_01 | 9 | 1 | **2** | 0.111 | 0.222 | hist 补三阴交 |
| 213_01 | 5 | 1 | 1 | 0.20 | 0.20 | 无变化（胆石点已命中） |
| 216_01 | 9 | 6 | 6 | 0.667 | 0.667 | 锚案本身已准 |
| 216_02 | 9 | 4 | **9** | 0.444 | **1.000** | **完美继承 216_01 链**（补内庭/足三里/阳辅，recall 满分） |

延续案补穴全部指向 gold：hist 正确恢复了复诊链应继承的既往穴（199–202 链补三阴交、216_02 全量继承 216_01）。

---

## ④ 结论

1. **history-aware 带来 followup/复诊层的实质改善**：chain_map followup 层 recall 0.249→0.333（+8.4pp）、F1 +7.9pp，是十轮迭代中复诊层最大的一次提升；8 个延续案中 6 案 TP 上升、1 案（216_02）达到 recall 满分、1 案（201_01）从零命中救回。
2. **不污染首诊层**：anchor/first_visit（66 案）recall 仅 +0.5pp、visit_type 首诊（24 案）完全一致——历史感知精准作用于复诊案，首诊精度无损。
3. **两模式适用结论**：
   - **首诊/锚案**：两模式等价，选 symptom-only 即可（更简洁、无历史依赖）。
   - **复诊/延续案**：history-aware 显著更优（recall +8pp 量级），应作为复诊默认模式。
   - **整体**：history-aware 在 86 案全集上 main F1 +2.1pp，是当前 benchmark_v2 口径下的最优版本。
4. **两模式分数不合并**：本报告两模式分别独立评分，未做任何合并；后续若上线，建议按 visit_type 路由（首诊→symptom-only，复诊→history-aware）。

---

## 附：产物与复现

- 脚本：`sf10_阶段D/score_sf10_v10_hist.py`（合并 5 分片 + gold pkl，可复算）
- 明细：`sf10_阶段D/判分明细v10_hist.csv`（93 行）
- 汇总：`sf10_阶段D/判分汇总v10_hist.json`
- 审计：`sf10_阶段D/审计日志v10_hist.json`（含 hist 主穴记录）
- 三连跑 SHA-256 一致。未改动 benchmark_v2 原文件、gold pkl、两个 `_blind93v10*_results.json`、symptoms 原文件。

免责声明：以上为学习方法论与技能评测整理，不构成医疗建议。
