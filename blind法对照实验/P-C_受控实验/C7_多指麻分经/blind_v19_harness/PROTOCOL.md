# v19 盲法重跑协议（Path A）

> 目的：取得本仓库**第一次真正洁净**的 v19 盲法测量，作为 `0.5991` 的外部校验。
> 执行者＝**与本仓库历史无关的新会话／外部 agent**；本仓库只做评分与登记。

---

## 0. 为什么必须交给外部执行者

本仓库内已存在的全部数字（v14r5 `0.5185`、v18 `0.5949`、v19 `0.5991`、C7′ 的触发案与加穴明细）都是**预测级离线复算**。任何在已读过 gold / 历史预测的会话里"重跑"出的结果，都属于本项目 `N-B` 已登记的**协议泄漏**，只能登记为"含泄漏的上界跑"，不得称为盲法。

因此本协议把"生成"与"评分"物理分开：外部只生成，本仓库只评分。

---

## 1. 交付物与路径

构建（在本仓库内执行，只写 `_blind_bundle_out/`）：

```powershell
python "blind法对照实验\P-C_受控实验\C7_多指麻分经\blind_v19_harness\_build_harness.py"
```

产出：

| 路径 | 内容 |
|---|---|
| `D:\projectAGI\nhx\_blind_bundle_out\blind_v19_bundle\` | 交付目录 |
| `D:\projectAGI\nhx\_blind_bundle_out\blind_v19_bundle.zip` | 同一内容的 zip（推荐直接给这个） |

交付目录结构：

```
blind_v19_bundle/
├── PROTOCOL.md              本文件
├── README_执行者须知.md       给外部 agent 的一页纸
├── manifest.sha256          全部输入件哈希（skill/ + cases/ + prompts/）
├── run_plan.json            分片与执行顺序
├── skill/doubao-acupuncture-diagnosis/    v19 冻结技能整目录
├── cases/<case_id>.md        86 案输入包（只有症状四诊字段）
├── cases/_index.json         case → 分片 / 链 / 上一诊
├── prompts/<shard>_<n>_<case>.txt   逐案可直接发送的 prompt
└── runs/                     ← 执行者把输出放这里（每案一个 JSON）
```

**交付时只给对方这个目录（或 zip）。不要给仓库访问权。**

---

## 2. 技能安装（把 `skill/doubao-acupuncture-diagnosis/` 装进外部 agent）

技能是**目录形态**：`<技能根目录>/doubao-acupuncture-diagnosis/SKILL.md`，同目录下的 `references/`、`针灸篇-知识条目整理.md`、`教程_utf8.txt` 等都是 `SKILL.md` 用**相对路径**引用的必需件——**必须整目录复制，不能只拷 SKILL.md**。

**目录名就是技能 ID**（OpenCode 按路径取 ID，`doubao-acupuncture-diagnosis` 已是合法 kebab-case），**不要改名**。

| 宿主 | 全局安装路径 | 项目级安装路径 |
|---|---|---|
| **OpenCode V2**（官方文档核实） | `~/.config/opencode/skills/doubao-acupuncture-diagnosis/` | `<项目>/.opencode/skills/doubao-acupuncture-diagnosis/` |
| OpenCode 兼容源（同一约定） | `~/.claude/skills/…`、`~/.agents/skills/…` | `<项目>/.claude/skills/…`、`.agents/skills/…` |
| **Claude Code** 及同约定宿主 | `~/.claude/skills/doubao-acupuncture-diagnosis/` | `<项目>/.claude/skills/doubao-acupuncture-diagnosis/` |
| 其它支持 Agent Skills 的宿主 | 其 skills 根目录下同名子目录 | 同左（项目级） |

Windows 上 `~` 即 `C:\Users\<你的用户名>`。

复制示例（PowerShell，Windows 全局安装到 OpenCode）：

```powershell
$dst = "$env:USERPROFILE\.config\opencode\skills\doubao-acupuncture-diagnosis"
New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
Copy-Item -Recurse -Force "D:\projectAGI\nhx\_blind_bundle_out\blind_v19_bundle\skill\doubao-acupuncture-diagnosis" $dst
Get-ChildItem $dst | Select-Object Name     # 应看到 SKILL.md 与 references\
```

Claude Code 只需把上面的 `$dst` 换成 `$env:USERPROFILE\.claude\skills\doubao-acupuncture-diagnosis`。

**安装后自检**（必须做，否则整批作废）：

1. `SKILL.md` 第 2 行 `name: doubao-acupuncture-diagnosis` 存在；
2. `SKILL.md` 含 `**v19 变更基线**` 与 `★ v19·M2-03 触发闸门精化`（确认装的是 v19 而不是旧版）；
3. `references/诊断与针灸实施指南.md`、`references/特效库全量.json`、`针灸篇-知识条目整理.md` 都在；
4. 与 `manifest.sha256` 中 `skill/` 段逐行对哈希一致。

---

## 3. 执行协议（Arm A-1，主臂）

1. 按 `run_plan.json` 的 `shards` **一片一片**跑；片内严格按 `prompts/` 文件名中的序号递增。
2. 每次调用**只发一个 prompt 文件**，一次性发送，不追加提示、不追问、不"重试到满意"。
3. 每案**新开会话/新上下文**（防跨案记忆）；唯一跨案信息就是 prompt 里写的「上游_上一诊主穴」。
4. 输出存为 `runs/<case_id>.json`（一案一文件，UTF-8，不加工）。
5. 全部跑完压缩 `runs/` 回传即可（附每案的 model 名与 timestamp，这两项已在 schema 里）。

**R-FU 上游语义**：v19 的复诊延续层需要"上一诊主穴"通道。本协议用**执行者自己先前输出**充当该通道（＝v18 部署语义"用技能自己对上次案的输出"，不是 gold）。是否采纳由技能规则自行判定。跨片不共享上游（片内链已整组保序，见 `cases/_index.json` 的 `chain` / `prev_case`）。

**允许的次要臂（Arm A-2，可选，预算允许再做一次）**：把 prompt 里「上游_上一诊主穴」一律填 `null`（等价"无上游通道"），可分离出"C7′ + 基础四层"的盲法水平。两臂结果分开报，**不得混算**。

---

## 4. 评分（本仓库执行，外部不参与）

外部回传后：

```powershell
python "blind法对照实验\P-C_受控实验\C7_多指麻分经\blind_v19_harness\score_blind_runs.py" --runs <runs目录>
```

评分器行为：

1. **完整性闸门**：86/86 案必须存在且 `status=OK`，否则**拒绝出 F1**（只报缺哪些案）。
2. 用唯一正式评分器 `benchmark_v2/canonical_scorer.py` 的 `normalize_units` + `_gold_results93v2.pkl` 算 TP/FP/FN/宏平均 F1。
3. 与三个参照并列：v14r5 `362/316/331/0.5185`、v18 `420/263/273/0.5949`、v19 预测级 `424/265/269/0.5991`。
4. **泄漏探测**：计算外部输出与 `_blind93v14r5_results.json`（历史跑）逐案主穴**完全一致率**；若 >50% 则告警，提示该批可能接触过仓库历史结果，**不得作为盲法结论**。
5. 输出 `blind_v19_score.txt`（含逐案差异清单），由我登记进计划与提案。

---

## 5. 结论口径（提前锁死，防事后拔高）

| 允许 | 禁止 |
|---|---|
| "v19 盲法重跑：`TP/FP/FN / F1 = a/b/c / d`（外部执行，`runs/` 独立回传）" | 用该数字宣称"临床复现率"或"外部泛化成立" |
| 与预测级 `0.5991` 并列，并给出差值 | 把预测级与盲法级混为一个数 |
| 若盲法 F1 显著低于预测级，登记为**该规则的部署损失** | 事后调整规则再跑同一批并把新数字当盲法 |

已知先验（必须随结果一并披露）：本仓库 `WS-5` 已实测——同一 86 案、同一 gold，canonical 口径与真盲法口径**差约 29 pp**，且**未证实**为诊断泄漏（`symptoms_v2` 无辨证字段）。因此**盲法 F1 大幅低于 `0.5991` 是预期内的**，不构成"v19 变差"的证据。

---

## 6. 纪律

- `skills/` 副本是**v19 冻结快照**；若 `SKILL.md` 后续变更，必须重建包并作废旧批。
- 外部执行者**不得**读取本仓库任何目录；一旦发生，整批登记为"协议泄漏上界跑"。
- 本协议不改变 `HARD-01`～`HARD-06`：v19 已合入 `main`，本重跑**只测量、不回改规则**。
