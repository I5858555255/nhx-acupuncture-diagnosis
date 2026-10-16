#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P5-B：路径完整性校验（只读检查，不写入任何文件）。

检查项（均只读）：
1. 正式技能子树（doubao-acupuncture-diagnosis）下所有被契约引用的路径均存在；
2. 正式基线 SKILL.md 与 references/ 四个随技能携带文件齐全（与 P5-A 契约一致）；
3. README.md 与 holdout_status_audit.md 位于仓库根目录且存在；
4. 评分实现 canonical_scorer.py 位于盲法对照实验目录下的 benchmark_v2 子目录中
   （通过遍历目录自动定位，避免依赖中文目录名的硬编码）。

本脚本不做任何写入；退出码 0 表示全部通过，1 表示存在失败。
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))


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
    """定位 sf10_阶段M5/G_验收 目录（自动遍历实验根的子目录）。"""
    for name in sorted(os.listdir(exp_root)):
        candidate = os.path.join(exp_root, name)
        if not os.path.isdir(candidate):
            continue
        if os.path.isfile(os.path.join(
                candidate, "G_验收", "判分汇总v14r5.json")):
            return candidate
    return None


MUST_EXIST_SKILL = [
    # --- 正式技能（SKILL.md 与 references 契约交叉核对）---
    "doubao-acupuncture-diagnosis/SKILL.md",
    "doubao-acupuncture-diagnosis/诊断与针灸实施指南.md",
    "doubao-acupuncture-diagnosis/针灸篇-知识条目整理.md",
    "doubao-acupuncture-diagnosis/教程.txt",
    "doubao-acupuncture-diagnosis/教程_utf8.txt",
    "doubao-acupuncture-diagnosis/针灸诊断交互页.html",
    "doubao-acupuncture-diagnosis/针灸实施全流程.html",
    "doubao-acupuncture-diagnosis/指南-覆盖对照表.md",
    "doubao-acupuncture-diagnosis/知识条目对照审计.md",
    "doubao-acupuncture-diagnosis/移植说明.md",
    "doubao-acupuncture-diagnosis/样例-髋酸胆经虚证-米粒灸鸡眼.md",
    "doubao-acupuncture-diagnosis/references/诊断与针灸实施指南.md",
    "doubao-acupuncture-diagnosis/references/特效库全量.json",
    "doubao-acupuncture-diagnosis/references/治则手法库.json",
    "doubao-acupuncture-diagnosis/references/典型案例示范集.md",
    "doubao-acupuncture-diagnosis/变更记录_SF10_v11.md",
    "doubao-acupuncture-diagnosis/变更记录_SF10_v12.md",
    "doubao-acupuncture-diagnosis/变更记录_SF10_v13.md",
    "doubao-acupuncture-diagnosis/变更记录_SF10_v14.md",
]

MUST_EXIST_ROOT = [
    "README.md",
    "holdout_status_audit.md",
]


def main():
    failures = 0

    # 1. 正式技能子树
    for rel in MUST_EXIST_SKILL:
        path = os.path.join(ROOT, rel)
        if os.path.isfile(path):
            print("[PASS] %s" % rel)
        else:
            failures += 1
            print("[FAIL] 缺失: %s（解析路径: %s）" % (rel, path))

    # 2. 仓库根目录的两个核心登记文档
    for rel in MUST_EXIST_ROOT:
        path = os.path.join(ROOT, rel)
        if os.path.isfile(path):
            print("[PASS] %s" % rel)
        else:
            failures += 1
            print("[FAIL] 缺失: %s（解析路径: %s）" % (rel, path))

    # 3. 评分实现位于实验目录的 benchmark_v2 子目录中
    exp_root = find_experiment_root(ROOT)
    if exp_root is None:
        failures += 1
        print("[FAIL] 未定位到含评分实现的实验目录")
        return 1 if failures else 0
    scorer_path = os.path.join(
        exp_root, "benchmark_v2", "canonical_scorer.py")
    if os.path.isfile(scorer_path):
        print("[PASS] %s" % os.path.relpath(scorer_path, ROOT))
    else:
        failures += 1
        print("[FAIL] 缺失: canonical_scorer.py")
    g_accept = find_g_accept_dir(exp_root)
    if g_accept is not None:
        summary = os.path.join(
            g_accept, "G_验收", "判分汇总v14r5.json")
        if os.path.isfile(summary):
            print("[PASS] %s" % os.path.relpath(summary, ROOT))
        else:
            failures += 1
            print("[FAIL] 缺失: 判分汇总v14r5.json")
    else:
        print("[WARN] 未定位到 G_验收 目录，跳过该项")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
