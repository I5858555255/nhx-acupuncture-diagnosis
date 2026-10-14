# -*- coding: utf-8 -*-
"""canonical_scorer.py — 点级判分唯一 canonical 实现（M5 阶段F）。

收敛对象：
  - benchmark_v2/score_benchmark_v2.py 的 per_case_metrics / macro / micro
  - 盲法93_v12/score_sf10_v12.py 的 pm / macro / micro
两版公式语义经逐行比对一致，本模块保留其逐行写法，作为唯一实现；
旧脚本不改、可继续运行，但新工作一律走本模块。

约定：
  1. 穴位归一化一律委托 normalize_acupoints.normalize_acupoints
     （gold 与所有轮次预测共用；本模块不改 normalize 与 gold）。
  2. 每案点级指标 = per_case_metrics(gold_set, pred_set)，
     返回 tp/fp/fn/recall/prec/f1/jac。
  3. 宏平均 = 逐案先算、None 跳过、再算术平均；
     微平均 = 全案 TP/FP/FN 求和后统一算 R/P/F1/Jac。
  4. 路径不硬编码：默认从本脚本位置解析项目根
     （Path(__file__).resolve().parent.parent = 盲法对照实验），
     也允许调用方显式传 root，支持任意工作目录运行。
"""
from __future__ import annotations

import json
import pickle
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # benchmark_v2 目录
DEFAULT_ROOT = HERE.parent                     # 盲法对照实验目录
sys.path.insert(0, str(HERE))
from normalize_acupoints import normalize_acupoints  # noqa: E402

GOLD_PKL_NAME = "_gold_results93v2.pkl"


# ---------------------------------------------------------------- 路径解析
def resolve_root(root=None) -> Path:
    """项目根（盲法对照实验目录）。显式 root 优先；缺省从脚本位置推导。"""
    if root is not None:
        return Path(root).resolve()
    return DEFAULT_ROOT


def gold_pkl_path(root=None) -> Path:
    """gold 打包文件路径（benchmark_v2/_gold_results93v2.pkl）。"""
    return resolve_root(root) / "benchmark_v2" / GOLD_PKL_NAME


# ---------------------------------------------------------------- 数据加载
def load_gold(root=None):
    """加载 gold 打包文件，返回 (results, case_ids, summary)。

    results[cid]['gold_members'] 为规范穴列表；summary['chain_map'] 为复诊链映射。
    """
    with open(gold_pkl_path(root), "rb") as f:
        g = pickle.load(f)
    return g["results"], g["case_ids"], g["summary"]


def load_blind(path) -> dict:
    """加载一轮盲法预测结果 JSON（dict: case_id -> 处方记录）。"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def blind_result_paths(root=None) -> dict:
    """各轮次盲法结果 JSON 的默认位置（按项目内目录约定）。"""
    root = resolve_root(root)
    return {
        "v140": root / "盲法140" / "_blind140_results.json",
        "v2": root / "盲法93" / "_blind93_results.json",
        "v3": root / "盲法93_v3" / "_blind93v3_results.json",
        "v4": root / "盲法93_v4" / "_blind93v4_results.json",
        "v5": root / "盲法93_v5" / "_blind93v5_results.json",
        "v6": root / "盲法93_v6" / "_blind93v6_results.json",
        "v7": root / "盲法93_v7" / "_blind93v7_results.json",
        "v8": root / "盲法93_v8" / "_blind93v8_results.json",
        "v9": root / "盲法93_v9" / "_blind93v9_results.json",
        "v10": root / "盲法93_v10" / "_blind93v10_results.json",
        "v11": root / "盲法93_v11" / "_blind93v11_results.json",
    }


# ---------------------------------------------------------------- 点级指标
def normalize_units(units):
    """穴名输出单元列表 -> 规范化穴位集合（去重）。委托 normalize_acupoints。"""
    return normalize_acupoints(units or [])


def per_case_metrics(gold_set, pred_set):
    """点级指标：TP/FP/FN + R/P/F1/Jac。两个入参均为规范穴 set。

    与旧两版逐行一致的语义：
      recall = TP/|G|（G 空 -> None）；prec = TP/|P|（P 空 -> None）；
      F1：R、P 均可算且 R+P>0 时调和平均；否则 TP=0 -> 0.0，其余 -> None；
      Jac = |G∪P|>0 时 TP/|G∪P|，否则 0.0。
    """
    gold_set = set(gold_set or set())
    pred_set = set(pred_set or set())
    tp = len(pred_set & gold_set)
    fp = len(pred_set - gold_set)
    fn = len(gold_set - pred_set)
    recall = tp / len(gold_set) if gold_set else None
    prec = tp / len(pred_set) if pred_set else None
    if prec is not None and recall is not None and (prec + recall) > 0:
        f1 = 2 * prec * recall / (prec + recall)
    else:
        f1 = 0.0 if (tp == 0) else None
    jac = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0.0
    return dict(tp=tp, fp=fp, fn=fn, recall=recall, prec=prec, f1=f1, jac=jac)


def score_prediction(gold_set, main_units, aux_units=None, layers=None):
    """对一案一轮预测算点级指标，返回与旧 PER[c]['new'][lab] 同构（超集）的字典。

    main_units：主穴输出单元列表；aux_units：佐穴输出单元列表（可空）。
    main = 仅主穴口径；all = 主+佐口径。
    返回键：units_main/units_aux/points_main/points_all/main/all/pred_main/pred_all/main_units/layers。
    """
    main_units = list(main_units or [])
    aux_units = list(aux_units or [])
    Pm = normalize_acupoints(main_units)
    Pa = normalize_acupoints(main_units + aux_units)
    return dict(
        units_main=len(main_units),
        units_aux=len(aux_units),
        points_main=len(Pm),
        points_all=len(Pa),
        main=per_case_metrics(gold_set, Pm),
        all=per_case_metrics(gold_set, Pa),
        pred_main=sorted(Pm),
        pred_all=sorted(Pa),
        main_units=main_units,
        layers=layers or {},
    )


# ---------------------------------------------------------------- 宏/微平均
def macro_average(values):
    """宏平均：逐案指标值列表，丢 None 后算术平均；空列表 -> None。"""
    vals = [v for v in values if v is not None]
    return statistics.mean(vals) if vals else None


def macro_metric(per, lab, subset, metric, cids):
    """从 PER 结构取逐案值再宏平均。per[c]['new'][lab][subset][metric]。"""
    vals = []
    for c in cids:
        d = per[c]["new"].get(lab)
        if d is None:
            continue
        v = d[subset][metric]
        if v is not None:
            vals.append(v)
    return macro_average(vals)


def micro_metric(per, lab, subset, metric, cids):
    """微平均：全案 TP/FP/FN 求和后统一算 recall/prec/f1/jac。"""
    tp = fp = fn = 0
    for c in cids:
        d = per[c]["new"].get(lab)
        if d is None:
            continue
        m = d[subset]
        tp += m["tp"]
        fp += m["fp"]
        fn += m["fn"]
    if metric == "recall":
        return tp / (tp + fn) if (tp + fn) else None
    if metric == "prec":
        return tp / (tp + fp) if (tp + fp) else None
    if metric == "f1":
        r = tp / (tp + fn) if (tp + fn) else 0
        p = tp / (tp + fp) if (tp + fp) else 0
        return 2 * p * r / (p + r) if (p + r) else 0.0
    if metric == "jac":
        return tp / (tp + fp + fn) if (tp + fp + fn) else 0.0
    raise ValueError(f"unknown metric: {metric}")


def round_or(x, nd=4):
    """None 原样；否则 round(x, nd)。"""
    return None if x is None else round(x, nd)
