# SF10 git 提交说明

- 日期：2026-10-14 · 仓库根：`D:\projectAGI\nhx`
- **流程要求：先本地 commit，push 前需用户确认（任务书要求）。本文不执行任何 git 写操作。**

## 一、建议 git add 清单

```powershell
git add doubao-acupuncture-diagnosis_v10/
git add "盲法对照实验/benchmark_v2/score_benchmark_v2.py"
git add "盲法对照实验/benchmark_v2/verify_benchmark_v2.py"
git add "盲法对照实验/benchmark_v2/gold_parse93v2.py"
git add "盲法对照实验/benchmark_v2/make_manifest.py"
git add "盲法对照实验/benchmark_v2/inspect_blind_files.py"
git add "盲法对照实验/sf10_阶段A/"
git add "盲法对照实验/sf10_阶段C/"
git add "盲法对照实验/sf10_阶段D/"
git add "盲法对照实验/sf10_阶段E/"
git add "盲法对照实验/sf10_阶段F/"
git add "盲法对照实验/盲法93_v10/"
git add "盲法对照实验/盲法93_v10_hist/"
```

（对应 `git status --short` 实测：5 个 `M` 与 8 个 `??` 条目，无遗漏。）

## 二、建议提交信息

```
SF10：原案复现优化 A–F 阶段，保留 v9 基线，v10 受控对照

- A：新点级评分口径冻结，三连跑哈希一致，修复 benchmark_v2 5 个 .py 硬编码路径
- B：v10 受控版本（七条主变更+三处矛盾修复，其余逐字保留 v9）
- C：93 案 symptoms_v2 输入补全（复诊58/首诊35，处方零泄漏）
- v10 symptom-only：main 宏 R.4125/P.3732/F1.3685/J.2440（precision +0.8pp、recall -2.7pp，不作推荐候选）
- D：history-aware 全集 F1.3892，followup 层 recall +8.4pp，复诊场景推荐输入模式
- E：误差归因与候选改动（建议 C1/C2/C3/C5，撤回 C4/C6）
- F：横向汇总验收，86 案为内部开发/原案复现集，非外部泛化验证
```

## 三、受保护文件确认未改动（git status 中无记录）

- `doubao-acupuncture-diagnosis\skill\SKILL.md`（v9 本体）
- `doubao-acupuncture-diagnosis\_backup\` 链
- `盲法对照实验\盲法93\symptoms\`、`盲法93\prescriptions\`、gold 文件（_gold_results93v2.pkl/.json 等）
- 盲法93_v3/v4/v5/v6/v7/v8/v9 既有结果目录

## 四、push 前待用户确认事项

1. 确认上述 add 清单无遗漏、无误纳中间调试文件（各阶段 `_*.py`/`_*.json` 为可复跑脚本与审计日志，随产物入库）。
2. 确认提交信息文案。
3. 确认后再执行 `git push`（任务书要求：push 前需用户确认）。
