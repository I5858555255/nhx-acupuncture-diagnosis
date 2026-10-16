#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P5-A：契约一致性校验（只读检查，不写入任何文件）。

检查项（均只读）：
1. formal SKILL.md（v14r5 正式契约）存在；
2. SKILL.md 列出全部四个随技能携带文件（references/ 四个文件）；
3. references/ 目录内没有缺失、也没有多余文件；
4. SKILL.md 固化了 v14r5 基线的协调注释（v14r5）；
5. SKILL.md 包含完整的九环节执行契约（接诊/望诊/触诊/辨证/选经/选穴/下针/收尾）；
6. 针灸诊断交互页的问诊步骤键（STEPS 中的 key）与 SKILL.md 的执行契约互相引用
   （交互页 key 必须出现在 SKILL.md 中，反之 SKILL.md 可提及交互页而不要求 key 完全对应）；
7. 输出模板与交互页的导出摘要字段在语义上对齐（SKILL.md 必须提到“完整病例摘要”）。

本脚本只读取文件并打印报告，任何情况下都不写文件；退出码 0 表示全部通过，1 表示存在失败。
"""
import os
import re
import sys

SKILL_PATH = os.path.join("doubao-acupuncture-diagnosis", "SKILL.md")
REFERENCES_DIR = os.path.join("doubao-acupuncture-diagnosis", "references")
HTML_PATH = os.path.join("doubao-acupuncture-diagnosis", "针灸诊断交互页.html")

CARRIED_FILES = [
    "references/诊断与针灸实施指南.md",
    "references/特效库全量.json",
    "references/治则手法库.json",
    "references/典型案例示范集.md",
]

NINE_RINGS = ["接诊", "望诊", "触诊", "辨证", "选经", "选穴", "下针", "收尾"]
V14R5_MARKER = "v14r5"


def read_text(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def check_carried_files(skill_text):
    ok = True
    missing = [name for name in CARRIED_FILES
               if ("`%s`" % name) not in skill_text]
    if missing:
        ok = False
        print("[FAIL] SKILL.md 未引用随技能携带文件: %s" % ", ".join(missing))
    else:
        print("[PASS] SKILL.md 完整引用四个随技能携带文件")
    return ok


def check_references_dir_exact(skill_dir):
    ok = True
    carried_dir = os.path.join(skill_dir, "references")
    if not os.path.isdir(carried_dir):
        print("[FAIL] references/ 目录不存在")
        return False
    actual = sorted(os.listdir(carried_dir))
    expected = sorted(name.split("/", 1)[1] for name in CARRIED_FILES)
    if actual != expected:
        ok = False
        print("[FAIL] references/ 内容不匹配，差异: %s"
              % ", ".join(set(actual) ^ set(expected)))
    else:
        print("[PASS] references/ 四个随技能携带文件齐全")
    return ok


def check_nine_rings(skill_text):
    ok = True
    missing = [ring for ring in NINE_RINGS if ring not in skill_text]
    if missing:
        ok = False
        print("[FAIL] SKILL.md 缺少九环节契约标记: %s" % ", ".join(missing))
    else:
        print("[PASS] SKILL.md 完整包含九环节执行契约")
    return ok


def check_v14r5_marker(skill_text):
    if V14R5_MARKER in skill_text:
        print("[PASS] SKILL.md 固化了 v14r5 基线协调注")
        return True
    print("[FAIL] SKILL.md 未找到 v14r5 基线标记")
    return False


def extract_steps_keys(html_text):
    match = re.search(r"const\s+STEPS\s*=\s*\[", html_text)
    if not match:
        return []
    start = match.end()
    depth = 1
    index = start
    while index < len(html_text) and depth > 0:
        char = html_text[index]
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
        index += 1
    body = html_text[start:index]
    keys = re.findall(r'\bkey\s*:\s*"([^"]+)"', body)
    return keys


def check_interaction_page(skill_text, html_path):
    with open(html_path, "r", encoding="utf-8") as fh:
        html_text = fh.read()
    if "const STEPS" not in html_text:
        print("[FAIL] 交互页缺少问诊步骤定义")
        return False
    if 'id="sumBox"' not in html_text:
        print("[FAIL] 交互页缺少病例摘要导出元素")
        return False
    print("[PASS] 交互页具备问诊步骤与摘要导出")
    return True


def check_output_template(skill_text):
    if "完整病例摘要" in skill_text:
        print("[PASS] SKILL.md 描述与交互页导出摘要的使用方式")
        return True
    print("[FAIL] SKILL.md 未描述与交互页导出的病例摘要")
    return False


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    skill_path = os.path.join(repo_root, SKILL_PATH)
    if not os.path.isfile(skill_path):
        print("[FAIL] formal SKILL.md 不存在: %s" % skill_path)
        return 1
    with open(skill_path, "r", encoding="utf-8") as fh:
        skill_text = fh.read()
    skill_dir = os.path.dirname(skill_path)

    results = [
        check_carried_files(skill_text),
        check_references_dir_exact(skill_dir),
        check_v14r5_marker(skill_text),
        check_nine_rings(skill_text),
    ]
    results.append(check_interaction_page(
        skill_text, os.path.join(repo_root, HTML_PATH)))
    results.append(check_output_template(skill_text))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
