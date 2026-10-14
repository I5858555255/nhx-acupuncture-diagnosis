# 说明_F_canonical.md — canonical_scorer 模块说明（M5 阶段F）

## 1. 目标

把 v5..v12 各轮共用的点级判分逻辑收敛为单一实现，消除
`benchmark_v2\score_benchmark_v2.py`（`per_case_metrics`/`macro`/`micro`）与
`盲法93_v12\score_sf10_v12.py`（`pm`/`macro`/`micro`）的双实现，
并修复 v12 脚本硬编码 `D:\projectAGI\nhx\盲法对照实验` 绝对路径的问题。

## 2. 交付物清单

| 文件 | 说明 |
|---|---|
| `benchmark_v2\canonical_scorer.py` | 点级判分唯一 canonical 模块（新文件） |
| `sf10_阶段M5\F_canonical\test_canonical_scorer.py` | 单元测试（unittest，30 例） |
| `sf10_阶段M5\F_canonical\test_log.txt` | 测试日志（30 tests / OK） |
| `sf10_阶段M5\F_canonical\recompute_v12.py` | v12 复算驱动（编排复刻旧脚本，指标走 canonical） |
| `sf10_阶段M5\F_canonical\复算核验.md` | 旧哈希 vs 新哈希、双目录一致性、差异定位 |
| `sf10_阶段M5\F_canonical\说明_F_canonical.md` | 本文件 |

未改动：`normalize_acupoints.py`、`_gold_results93v2.pkl/.json`、`score_benchmark_v2.py`。
旧脚本可继续运行，新工作一律走 canonical。

## 3. 模块 API（canonical_scorer.py）

路径常量：
- `HERE` = 脚本所在目录（`benchmark_v2`）。
- `DEFAULT_ROOT` = `HERE.parent`（盲法对照实验目录）。

函数：
- `resolve_root(root=None) -> Path`：项目根解析。显式 root 优先；缺省从 `Path(__file__).resolve().parent.parent` 推导。
- `gold_pkl_path(root=None) -> Path`：`benchmark_v2/_gold_results93v2.pkl`。
- `load_gold(root=None) -> (results, case_ids, summary)`：加载 gold 打包文件。
- `load_blind(path) -> dict`：加载一轮盲法预测 JSON。
- `blind_result_paths(root=None) -> dict`：各轮次结果 JSON 默认位置（Path 对象）。
- `normalize_units(units) -> set`：穴名单元列表 → 规范穴集（去重），委托 `normalize_acupoints`。
- `per_case_metrics(gold_set, pred_set) -> dict`：点级指标 `tp/fp/fn/recall/prec/f1/jac`。
- `score_prediction(gold_set, main_units, aux_units=None, layers=None) -> dict`：一案一轮打分，返回键
  `units_main/units_aux/points_main/points_all/main/all/pred_main/pred_all/main_units/layers`，
  与旧 `PER[c]['new'][lab]` 结构兼容（为其超集）。
- `macro_average(values)` / `macro_metric(per, lab, subset, metric, cids)`：宏平均（逐案先算，None 跳过）。
- `micro_metric(per, lab, subset, metric, cids)`：微平均（全案 TP/FP/FN 求和后统一算 R/P/F1/Jac）。
- `round_or(x, nd=4)`：None 原样，否则 round。

## 4. 路径解析规则

1. 不写死任何绝对路径；模块内所有路径相对 `resolve_root()` 展开。
2. 缺省 root：`Path(__file__).resolve().parent.parent` = 盲法对照实验。
3. 调用方可显式传 `root`（如跨机器/跨目录运行），覆盖缺省。
4. `import normalize_acupoints` 时把 `HERE` 注入 `sys.path`，与 cwd 无关。

## 5. 与旧实现的差异清单

逐行比对结论：**点级指标公式两版语义一致，canonical 取 v2 版逐行写法**，无行为差异。

| 项 | score_benchmark_v2.py | score_sf10_v12.py | canonical |
|---|---|---|---|
| 点级指标函数 | `per_case_metrics` | `pm` | `per_case_metrics`（唯一实现） |
| F1 分支 | `prec is not None and recall is not None` | `prec and recall`（None/0.0 均假） | 同 v2；语义与 v12 等价（tp=0 时两分支都得 0.0） |
| 宏平均 | 逐案值丢 None 后 mean | 同 | 一致 |
| 微平均 | TP/FP/FN 求和再算 | 同 | 一致 |
| 路径 | `os.path.dirname(__file__)` 推导 | 硬编码 `D:\projectAGI\nhx\...` | 脚本位置推导 + 显式 root 参数 |
| 旧口径复算 | 内含（expand_pre/expand_post、旧 pkl） | 无 | 不纳入 canonical（属历史归因，非新评分路径） |
| 组穴展开/透刺/耳穴别名 | 共用 normalize_acupoints | 同 | 仍委托 normalize_acupoints，未复制规则表 |

## 6. 验证记录

- 单测：30 例全部通过（指标公式/复合穴展开/透刺端点/别名归并/gold 去重/空预测空 gold/宏微平均/路径解析）。
- 双目录：cwd=项目根 与 cwd=C:\Users\JM.RADE 各跑一次，输出 SHA-256 相同。
- 哈希复算：canonical 重算 v12 明细/汇总与旧文件逐字节一致
  （明细 `30898461…AD7D`、汇总 `A73A13B9…845B`），无差异。
