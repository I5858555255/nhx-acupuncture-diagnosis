#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""构建 v19 盲法重跑交付包（Path A：交外部 agent 执行，本仓库只做评分）。

产出（默认 `D:\\projectAGI\\nhx\\_blind_bundle_out\\blind_v19_bundle\\` + 同名 .zip）：
  PROTOCOL.md            协议与硬规则（由本目录静态文件复制）
  skill/                 **v19 冻结**技能整目录（SKILL.md + references/ + 明细库）
  cases/<case_id>.md     86 案输入包（仅症状四诊字段，**无 gold、无处方、无历史预测**）
  prompts/<shard>_<n>_<case_id>.txt   逐案**可直接发送**的 prompt（含上游占位符）
  cases/_index.json      case → shard / 链 / 上一诊
  run_plan.json          分片与执行顺序（链内保序，R-FU 依赖）
  manifest.sha256        skill/ 与 cases/ 与 prompts/ 全部文件哈希
  README_执行者须知.md    给外部 agent 的一页纸

纪律（本脚本自身）：
- **只读** 冻结数据（`symptoms_v2`、`gold pkl`（仅取案号列表）、`PN_followup_rule.json`）；
- 产出**不含** gold 穴、不含处方、不含 v14r5/v18/v19 任何预测；
- 不写仓库内除 `_blind_bundle_out/`（已 gitignore）以外的路径。

用法：
  python _build_harness.py                # 默认输出
  python _build_harness.py --out <dir>    # 指定输出
"""
import argparse
import csv
import hashlib
import io
import json
import os
import pickle
import shutil
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
EXP = None
for _n in sorted(os.listdir(ROOT)):
    if os.path.isfile(os.path.join(ROOT, _n, "benchmark_v2", "canonical_scorer.py")):
        EXP = os.path.join(ROOT, _n)
        break
BENCH = os.path.join(EXP, "benchmark_v2")
SD = os.path.join(EXP, "sf10_阶段C", "symptoms_v2")
SKILL_DIR = os.path.join(ROOT, "doubao-acupuncture-diagnosis")
RULE = os.path.join(ROOT, "blind法对照实验", "P-N_开放重提炼", "PN_followup_rule.json")

SKIP_KEYS = {"case_id", "doc", "block"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def render_field(k, v):
    """把 symptoms_v2 的单个字段渲染成可读文本（保真，不改写）。"""
    out = []
    if isinstance(v, dict):
        frag = str(v.get("片段", "") or "")
        unit = str(v.get("单位", "") or "")
        if frag.strip():
            out.append(frag.rstrip())
        if unit.strip():
            out.append("（定位/依据：%s）" % unit.strip())
    elif isinstance(v, list):
        if v:
            out.append("；".join(str(x) for x in v))
    else:
        s = str(v or "")
        if s.strip():
            out.append(s.rstrip())
    if not out:
        out.append("（原文未记录）")
    return "\n".join(out)


def render_case(cid):
    d = json.load(io.open(os.path.join(SD, "%s_symptoms_v2.json" % cid), encoding="utf-8"))
    lines = ["# 就诊记录 %s" % cid, ""]
    lines.append("> 说明：以下为本案**全部可用输入**。未出现的字段即原文未记录，不得补猜。")
    lines.append("")
    for k, v in d.items():
        if k in SKIP_KEYS:
            continue
        lines.append("## %s" % k)
        lines.append(render_field(k, v))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "_blind_bundle_out"))
    ap.add_argument("--arm", default="A-1", choices=["A-1", "A-2"],
                    help="A-1=带上游（全 86 案）；A-2=上游置空（仅重跑有上一诊的 25 案）")
    a = ap.parse_args()

    gold = pickle.load(open(os.path.join(BENCH, "_gold_results93v2.pkl"), "rb"))
    SC = [c for c in gold["case_ids"] if len(gold["results"][c]["gold_members"]) > 0]
    for c in SC:
        assert os.path.exists(os.path.join(SD, "%s_symptoms_v2.json" % c)), c

    rule = json.load(io.open(RULE, encoding="utf-8"))
    chains = rule["患者分组(仅多案组)"]
    chain_of, prev_of = {}, {}
    for g, ids in chains.items():
        ids = sorted(ids, key=lambda x: (int(x.split("_")[1]), x))
        for i, c in enumerate(ids):
            chain_of[c] = g
            prev_of[c] = ids[i - 1] if i else None

    # ---- 分片：链整组不拆；S1–S3 先放链，再用单案填到 17 案，余下均分 S4/S5 ----
    chains_sorted = {g: sorted(ids, key=lambda x: (int(x.split("_")[1]), x))
                     for g, ids in chains.items()}
    if a.arm == "A-1":
        base = [("S1", ["66"]), ("S2", ["198", "216"]), ("S3", ["146", "156"])]
        shards, used = [], set()
        for name, groups in base:
            ids = [c for g in groups for c in chains_sorted[g]]
            used |= set(ids)
            shards.append([name, ids])
        rest = [c for c in sorted(SC, key=lambda x: (int(x.split("_")[1]), x)) if c not in used]
        TARGET = 17
        for sh in shards:
            while len(sh[1]) < TARGET and rest:
                sh[1].append(rest.pop(0))
        half = (len(rest) + 1) // 2
        shards.append(["S4", rest[:half]])
        shards.append(["S5", rest[half:]])
        assert sum(len(v) for _, v in shards) == len(SC) == 86, (sum(len(v) for _, v in shards), len(SC))
    else:
        # A-2：只重跑「有上一诊」的 25 案；其余 61 案 prompt 与 A-1 逐字节相同，直接复用。
        sel = [c for c in SC if prev_of.get(c)]
        assert len(sel) == 25, len(sel)
        shards = [["A2-S1", [c for c in chains_sorted["66"] if prev_of.get(c)]],
                  ["A2-S2", [c for g in ("156", "198") for c in chains_sorted[g] if prev_of.get(c)]],
                  ["A2-S3", [c for g in ("146", "216") for c in chains_sorted[g] if prev_of.get(c)]]]
        assert sum(len(v) for _, v in shards) == 25, [len(v) for _, v in shards]

    bundle = os.path.join(a.out, "blind_v19_bundle" if a.arm == "A-1" else "blind_v19_bundle_A2")
    if os.path.isdir(bundle):
        shutil.rmtree(bundle)
    for sub in ("cases", "prompts", "skill", "runs"):
        os.makedirs(os.path.join(bundle, sub), exist_ok=True)

    # ---- 技能副本（v19 冻结） ----
    skill_dst = os.path.join(bundle, "skill", "doubao-acupuncture-diagnosis")
    shutil.copytree(SKILL_DIR, skill_dst)

    # ---- 案例 ----
    index = {"arm": a.arm, "skill_version": "v19", "total": sum(len(v) for _, v in shards),
             "cases": {}}
    order = []
    for name, ids in shards:
        for n, c in enumerate(ids, 1):
            text = render_case(c)
            io.open(os.path.join(bundle, "cases", "%s.md" % c), "w",
                    encoding="utf-8", newline="\n").write(text)
            index["cases"][c] = {"shard": name, "order_in_shard": n,
                                 "chain": chain_of.get(c), "prev_case": prev_of.get(c)}
            order.append((name, n, c))
    io.open(os.path.join(bundle, "cases", "_index.json"), "w",
            encoding="utf-8", newline="\n").write(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n")

    run_plan = {"arm": a.arm, "skill_version": "v19",
                "note": "链内必须按 order_in_shard 递增执行；跨片不共享上游。" if a.arm == "A-1"
                        else "A-2 臂：本臂不提供任何上游信息；链内仍按 order_in_shard 递增执行以便追溯。",
                "shards": {name: [c for _, _, c in order if _ == name] for name, _ in shards}}
    io.open(os.path.join(bundle, "run_plan.json"), "w",
            encoding="utf-8", newline="\n").write(
        json.dumps(run_plan, ensure_ascii=False, indent=2) + "\n")

    tpl = io.open(os.path.join(HERE, "prompt_template.md" if a.arm == "A-1"
                               else "prompt_template_A2.md"), encoding="utf-8").read()
    for name, n, c in order:
        case_text = io.open(os.path.join(bundle, "cases", "%s.md" % c), encoding="utf-8").read()
        prev = prev_of.get(c)
        body = tpl.replace("{{CASE_ID}}", c)
        body = body.replace("{{SHARD}}", name).replace("{{N}}", str(n))
        body = body.replace("{{PREV_CASE}}", prev or "（无）")
        body = body.replace("{{CASE_TEXT}}", case_text)
        io.open(os.path.join(bundle, "prompts", "%s_%02d_%s.txt" % (name, n, c)), "w",
                encoding="utf-8", newline="\n").write(body)

    for f in (("README_执行者须知.md",) if a.arm == "A-1" else ("README_执行者须知_A2.md",)):
        src = os.path.join(HERE, f)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(bundle, f))

    # ---- manifest ----
    lines = []
    for r, _, fs in os.walk(bundle):
        for f in sorted(fs):
            p = os.path.join(r, f)
            rel = os.path.relpath(p, bundle).replace("\\", "/")
            if rel.startswith("runs/") or rel == "manifest.sha256":
                continue
            lines.append("%s  %s" % (sha256(p), rel))
    mani = "\n".join(sorted(lines)) + "\n"
    io.open(os.path.join(bundle, "manifest.sha256"), "w", encoding="utf-8", newline="\n").write(mani)

    # ---- zip ----
    zpath = os.path.join(a.out, "blind_v19_bundle.zip" if a.arm == "A-1" else "blind_v19_bundle_A2.zip")
    if os.path.exists(zpath):
        os.remove(zpath)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for r, _, fs in os.walk(bundle):
            for f in sorted(fs):
                p = os.path.join(r, f)
                z.write(p, os.path.relpath(p, bundle).replace("\\", "/"))

    msg = ["arm    = %s" % a.arm,
           "bundle = %s" % bundle,
           "zip    = %s (%.2f MB)" % (zpath, os.path.getsize(zpath) / 1048576.0),
           "cases  = %d（%s）" % (sum(len(v) for _, v in shards),
                                 "、".join("%s:%d" % (n, len(v)) for n, v in shards)),
           "skill  = %d files" % sum(len(fs) for _, _, fs in os.walk(skill_dst)),
           "manifest lines = %d" % len(mani.splitlines())]
    sys.stdout.buffer.write(("\n".join(msg) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
