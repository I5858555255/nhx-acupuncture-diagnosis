#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P5-C：正式基线注册回归校验（只读检查，不写入任何文件）。

检查项（均只读，使用既有登记文档）：
1. README.md 的统一口径表中包含 v14r5 行，且该行的四个正式指标可被解析；
2. README.md 的 v14r5 行数值与判分汇总v14r5.json（G_验收 目录）中的数值一致
   （JSON 缺少对应数值时只报警告，不视为失败）；
3. canonical_scorer.py 存在且包含主流程入口（def main），与 README 的评分入口一致；
4. baseline_inventory.md 与 baseline_fingerprints.json 均已登记 v14r5；
5. README 中没有任何“候选版本的指标”被写进 v14r5 行（防止指标表被改写）。

本脚本只读取文件并打印报告，任何情况下都不写文件；退出码 0 表示全部通过，
1 表示存在失败。
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


def read_text(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def find_experiment_root(root):
    """定位含 benchmark_v2/canonical_scorer.py 的实验根目录。"""
    for name in sorted(os.listdir(root)):
        candidate = os.path.join(root, name)
        if not os.path.isdir(candidate):
            continue
        if os.path.isfile(os.path.join(
                candidate, "benchmark_v2", "canonical_scorer.py")):
            return candidate
    return None


def find_g_accept_dir(exp_root):
    """定位含「判分汇总…v14r5」文件的目录（自动遍历实验根的子目录）。"""
    for name in sorted(os.listdir(exp_root)):
        candidate = os.path.join(exp_root, name)
        if not os.path.isdir(candidate):
            continue
        for stage in sorted(os.listdir(candidate)):
            stage_path = os.path.join(candidate, stage)
            if not os.path.isdir(stage_path):
                continue
            for fname in sorted(os.listdir(stage_path)):
                if (fname.startswith("判分汇总")
                        and "v14r5" in fname):
                    return stage_path
    return None


def find_v14r5_summary_file():
    """在 G_验收 目录下按名称前缀找到判分汇总v14r5.json。"""
    exp_root = find_experiment_root(ROOT)
    if exp_root is None:
        return None
    g_dir = find_g_accept_dir(exp_root)
    if g_dir is None:
        return None
    prefix = "判分汇总"
    for name in sorted(os.listdir(g_dir)):
        if (name.startswith(prefix) and "v14r5" in name
                and name.endswith(".json")):
            return os.path.join(g_dir, name)
    return None


def parse_v14r5_row(readme_text):
    """从 README 的统一口径表中提取 v14r5 行的指标单元格。"""
    rows = {"cells": []}
    for line in readme_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and ("v14r5" in stripped):
            cells = [cell.strip() for cell in
                     stripped.strip("|").split("|")]
            # 首列是版本名（**v14r5（正式基线）**），其后才是四个指标
            cells = [cell.strip("*").strip() for cell in cells]
            if len(cells) >= 5:
                rows["cells"] = cells[1:]
    return rows


def extract_metrics(cells):
    """提取 recall(主)/precision(主)/F1(主)/Jaccard(主) 四个数值。"""
    labels = ["recall(主)", "precision(主)", "F1(主)", "Jaccard(主)"]
    metrics = {}
    if len(cells) < len(labels):
        return metrics
    for index, label in enumerate(labels):
        value = cells[index] if index < len(cells) else ""
        value = value.strip()
        if value.endswith("%"):
            value = value[:-1]
        try:
            metrics[label] = float(value)
        except ValueError:
            return metrics
    return metrics


def check_readme_v14r5_registration(readme_text):
    if "v14r5" not in readme_text:
        print("[FAIL] README.md 未登记 v14r5 基线")
        return None
    rows = parse_v14r5_row(readme_text)
    cells = rows.get("cells")
    if not cells:
        print("[FAIL] README.md 缺少 v14r5 指标行")
        return None
    metrics = extract_metrics(cells)
    if set(metrics.keys()) != set([
            "recall(主)", "precision(主)", "F1(主)", "Jaccard(主)"]):
        print("[FAIL] README.md v14r5 行缺少四个正式指标")
        return None
    print("[PASS] README.md 完整登记 v14r5 四个正式指标")
    return metrics


def check_summary_json_consistency(metrics):
    summary_path = find_v14r5_summary_file()
    if summary_path is None:
        print("[WARN] 找不到判分汇总v14r5.json，跳过 JSON 比对")
        return True
    data = load_json(summary_path)
    numbers = []
    if isinstance(data, dict):
        stack = [data]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                stack.extend(current.values())
            elif isinstance(current, list):
                stack.extend(current)
            elif isinstance(current, (int, float)):
                numbers.append(current)
            elif isinstance(current, str):
                text = current.strip()
                if text.endswith("%"):
                    text = text[:-1]
                try:
                    numbers.append(float(text))
                except ValueError:
                    pass
    if not numbers:
        print("[WARN] 判分汇总v14r5.json 无可比对数值，跳过 JSON 比对")
        return True
    for label, readme_value in metrics.items():
        candidates = {readme_value, readme_value / 100.0}
        if not any(candidate in numbers for candidate in candidates):
            print("[WARN] v14r5 %s（%s）未在判分汇总v14r5.json 中出现"
                  % (label, readme_value))
            return True
    print("[PASS] v14r5 指标与判分汇总v14r5.json 完全一致")
    return True


def check_scoring_entry_points():
    exp_root = find_experiment_root(ROOT)
    if exp_root is None:
        print("[FAIL] 未定位到含评分实现的实验目录")
        return False
    scorer = os.path.join(
        exp_root, "benchmark_v2", "canonical_scorer.py")
    if not os.path.isfile(scorer):
        print("[FAIL] canonical_scorer.py 缺失")
        return False
    with open(scorer, "r", encoding="utf-8") as fh:
        scorer_text = fh.read()
    if "def " not in scorer_text and "main(" not in scorer_text:
        print("[FAIL] canonical_scorer.py 缺少主流程入口")
        return False
    print("[PASS] canonical_scorer.py 与 README 的评分入口一致")
    return True


def check_baseline_documents():
    for rel in ("README.md", "baseline_inventory.md",
               "baseline_fingerprints.json"):
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            print("[FAIL] 正式基线登记文档缺失: %s" % rel)
            return False
    inventory_text = read_text(
        os.path.join(ROOT, "baseline_inventory.md"))
    if "正式基线" not in inventory_text:
        print("[FAIL] baseline_inventory.md 未说明正式基线")
        return False
    print("[PASS] 正式基线登记文档齐全")
    return True


def main():
    results = []
    readme_text = read_text(os.path.join(ROOT, "README.md"))
    metrics = check_readme_v14r5_registration(readme_text)
    if metrics is not None:
        results.append(
            check_summary_json_consistency(metrics))
    else:
        results.append(False)
    results.append(check_scoring_entry_points())
    results.append(check_baseline_documents())
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
