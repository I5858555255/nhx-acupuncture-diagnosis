# SF10 阶段G · 文件清单

- 日期：2026-10-14 · 仓库根：`D:\projectAGI\nhx`

## 一、本目录产物（`盲法对照实验\sf10_阶段G\`）

| 文件 | 内容 |
|---|---|
| `最终中文总结报告.md` | v11 实测总结（判定：推荐候选；五改动分差；双轨数字；边界声明） |
| `横向对照表_v11.md` | 五版本 × 双轨 × main/all × 宏/微 八张表 + 量级 + visit/chain 分层 |
| `文件清单_阶段G.md` | 本件 |

## 二、数据源指针（只读引用，非本目录产物）

### `盲法对照实验\盲法93_v11\`（v11 盲法与评分产物）

| 文件 | 内容 |
|---|---|
| `判分汇总v11.json` | 核心数据：86/64 五版本横向、visit/chain 分层、零命中/满分、主穴统计、执行方差、控制组核对、改动前后分差 |
| `判分明细v11.csv` | 86 案逐案 TP/FP/FN 与指标（三连跑哈希一致，=74CB29C2…） |
| `逐案新旧差异表v11_vs_v9.csv` | 86 行 v11 vs v9 逐案差异 |
| `误差分类表v11.csv` | 逐案 FN 漏穴 / FP 误加穴及归类标签 |
| `run1.txt` | 控制组核对输出 + 横向打印 |
| `score_sf10_v11.py` | v11 评分脚本 |
| `_blind93v11_part1..5.json`、`_blind93v11_results.json` | 盲法原始输出（只读） |
| `_build_v11_part4.py`、`_inspect11.py` | 构建/核查脚本 |

### `doubao-acupuncture-diagnosis_v11\`（v11 技能）

| 文件 | 内容 |
|---|---|
| `skill\SKILL.md` | v11 受控技能（基底 v9 + C1/C2/C3/C5 + 318 补强 4 条） |
| `skill\references\` | 4 文件，SHA-256 与 v9 逐字节一致 |
| `变更记录.md` | 5 条主改动前后对照 + 模拟分差 + 保留规则 10 项声明 |

## 三、未改动受保护文件（git status 确认）

- `doubao-acupuncture-diagnosis\skill\SKILL.md`（v9 本体）
- `doubao-acupuncture-diagnosis\_backup\` 链
- `盲法对照实验\盲法93\symptoms\`、`prescriptions\`、gold 文件
- `benchmark_v2\` 评分器（normalize/score/verify 等，本阶段零改动）

## 四、git 状态（2026-10-14 实测）

untracked（待纳入下次提交，是否提交/推送由 MainAgent 向用户确认）：
- `doubao-acupuncture-diagnosis_v11/`
- `盲法对照实验/盲法93_v11/`
- `盲法对照实验/sf10_阶段G/`
