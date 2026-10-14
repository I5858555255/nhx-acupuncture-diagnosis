# -*- coding: utf-8 -*-
"""F1 横向数字交叉核对（只读，不改任何源数据）"""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

B = r"D:\projectAGI\nhx\盲法对照实验"
v2 = json.load(open(B + r"\benchmark_v2\判分汇总v2.json", encoding="utf-8"))
base = json.load(open(B + r"\sf10_阶段A\baseline_冻结.json", encoding="utf-8"))
v10 = json.load(open(B + r"\盲法93_v10\判分汇总v10.json", encoding="utf-8"))

def pick(d, k):
    """提取某版本 4 指标(recall/prec/f1/jac) x (main/all) x (macro/micro) + mean/sum"""
    if k not in d:
        return None
    e = d[k]
    out = {}
    for scope in ("main", "all"):
        for agg in ("macro", "micro"):
            m = e["metrics"][scope][agg]
            out[f"{scope}_{agg}_r"] = m["recall"]
            out[f"{scope}_{agg}_p"] = m["prec"]
            out[f"{scope}_{agg}_f1"] = m["f1"]
            out[f"{scope}_{agg}_jac"] = m["jac"]
    out["mean_units_main"] = e["mean_units_main"]
    out["mean_points_main"] = e["mean_points_main"]
    out["sum_tp_main"] = e["sum_tp_main"]
    out["sum_points_main"] = e.get("sum_points_main")
    return out

versions = ["v5", "v6", "v9", "v10"]
report = {}
all_ok = True
for v in versions:
    a = pick(v2, v)          # 来自统一评分器 benchmark_v2
    b = pick(base, v)        # 来自阶段A冻结
    c = pick(v10, v)         # 来自 v10 评分器自己的汇总
    entry = {"v2": a, "baseline": b, "v10file": c}
    # 比对
    diffs = []
    def cmp(label, x, y, tol=0.0):
        if x is None or y is None:
            return
        if tol > 0:
            if abs(x - y) > tol:
                diffs.append(f"{label}: {x} != {y} (tol={tol})")
        else:
            if x != y:
                diffs.append(f"{label}: {x} != {y}")
    if b is not None and a is not None:
        for kk in b:
            tol = 0.001 if kk in ("mean_units_main", "mean_points_main") else 0.0
            cmp(f"v2 vs baseline {v}.{kk}", a.get(kk), b[kk], tol)
    if a is not None and c is not None:
        for kk in a:
            if kk == "sum_points_main":
                continue  # v10 文件不输出该字段
            if a.get(kk) is None or c.get(kk) is None:
                continue
            tol = 0.001 if kk in ("mean_units_main", "mean_points_main") else 0.0
            cmp(f"v10file vs v2 {v}.{kk}", c.get(kk), a[kk], tol)
    entry["diffs"] = diffs
    if diffs:
        all_ok = False
    report[v] = entry

# 86案口径
print("n_cases:", v2["n_cases"], "n_scorable:", v2["n_scorable"], "n_unscored:", v2["n_unscored"])
print("unscored keys v2:", sorted(v2["unscored"].keys()))
print("unscored keys baseline:", sorted(base["unscored"].keys()))
print("unscored keys v10:", sorted(v10["unscored"].keys()))

# 横向表核心数字 (main macro / main micro / all macro / all micro 的 r,p)
print("\n=== 横向表（main/all × macro/micro 的 recall/prec）===")
hdr = f"{'ver':5} | {'MmacR':>7} {'MmacP':>7} | {'MmicR':>7} {'MmicP':>7} | {'AmacR':>7} {'AmacP':>7} | {'AmicR':>7} {'AmicP':>7} | {'meanU':>7} {'meanP':>7} {'tpMain':>6}"
print(hdr)
for v in versions:
    a = report[v]["v2"] or report[v]["v10file"]
    if a is None:
        print(v, "无")
        continue
    print(f"{v:5} | {a['main_macro_r']:7.4f} {a['main_macro_p']:7.4f} | {a['main_micro_r']:7.4f} {a['main_micro_p']:7.4f} | {a['all_macro_r']:7.4f} {a['all_macro_p']:7.4f} | {a['all_micro_r']:7.4f} {a['all_micro_p']:7.4f} | {a['mean_units_main']:7.4f} {a['mean_points_main']:7.4f} {a['sum_tp_main']:6d}")

print("\n=== 差异清单 ===")
any_diff = False
for v in versions:
    for d in report[v]["diffs"]:
        any_diff = True
        print("DIFF:", d)
if not any_diff:
    print("（无差异：v5/v6/v9 在 v2汇总=基线冻结=v10文件三处完全一致；v10 仅在 v10文件中存在）")

print("\nALL_OK =", all_ok)
json.dump(report, open(B + r"\sf10_阶段F\_crosscheck_result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
