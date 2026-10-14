# -*- coding: utf-8 -*-
"""recompute_v12.py — 用 canonical_scorer 重算 v12 判分明细/汇总（M5 阶段F 核验）。

编排复刻 score_sf10_v12.py，但点级指标（R/P/F1/Jac、TP/FP/FN）、宏/微平均、
穴位归一化全部委托 benchmark_v2/canonical_scorer.py，不再自带第二份实现。

用法：
    python recompute_v12.py --outdir <输出目录> [--root <盲法对照实验目录>]
输出：判分明细v12.csv、判分汇总v12.json（编码/格式与 score_sf10_v12.py 一致）。
"""
import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT_DEFAULT = HERE.parents[1]                      # 盲法对照实验目录
sys.path.insert(0, str(ROOT_DEFAULT / "benchmark_v2"))
import canonical_scorer as cs  # noqa: E402

CMP = ["v5", "v6", "v9", "v10", "v11", "v12"]
M2 = {
    "M2-01": ["60_01", "63_01", "66_01"], "M2-02": ["63_01", "66_01"],
    "M2-03": ["66_01", "318_01"],
    "M2-04": ["60_01", "61_01", "62_01", "65_01", "66_01"],
    "M2-05": ["1_01", "57_01", "140_01"], "M2-06": ["140_01", "156_05"],
    "M2-07": ["13_01"], "M2-09": ["8_01"], "M2-10": ["1_01"],
    "M2-11": ["1_01"], "M2-12": ["57_01"], "M2-13": ["198_01"],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT_DEFAULT))
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    ROOT = Path(args.root).resolve()
    OUT = Path(args.outdir)
    OUT.mkdir(parents=True, exist_ok=True)

    FILES = {
        "v5": ROOT / "盲法93_v5" / "_blind93v5_results.json",
        "v6": ROOT / "盲法93_v6" / "_blind93v6_results.json",
        "v9": ROOT / "盲法93_v9" / "_blind93v9_results.json",
        "v10": ROOT / "盲法93_v10" / "_blind93v10_results.json",
        "v11": ROOT / "盲法93_v11" / "_blind93v11_results.json",
        "v12": ROOT / "盲法93_v12" / "_blind93v12_results.json",
    }
    BLIND = {lab: json.load(open(fp, encoding="utf-8")) for lab, fp in FILES.items()}
    NEW, CASE_IDS, SUMMARY = cs.load_gold(ROOT)

    EXCLUDE = set(r["case_id"] for r in csv.DictReader(
        open(ROOT / "sf10_核心集" / "排除清单.csv", encoding="utf-8-sig")))
    VT = {}
    for r in csv.DictReader(open(ROOT / "sf10_阶段D" / "组装清单.csv", encoding="utf-8-sig")):
        v = r["visit_type"]
        VT[r["case_id"]] = "复诊" if v.startswith("复诊") else ("首诊" if v.startswith("首诊") else "其他")

    PER = {}
    for cid in CASE_IDS:
        G = set(NEW[cid]["gold_members"])
        d = {}
        for lab in CMP:
            rec = BLIND[lab].get(cid)
            if rec is None:
                d[lab] = None
                continue
            d[lab] = cs.score_prediction(G, rec.get("主穴", []), rec.get("佐穴", []))
        PER[cid] = dict(G=sorted(G), gc=len(G), new=d,
                        chain=SUMMARY["chain_map"].get(cid, "first_visit"),
                        vt=VT.get(cid, ""), note=NEW[cid]["note"], core=cid not in EXCLUDE)

    SCORED = [c for c in CASE_IDS if PER[c]["gc"] > 0]
    UNSCORED = [c for c in CASE_IDS if PER[c]["gc"] == 0]
    CORE = [c for c in SCORED if PER[c]["core"]]
    ro = lambda x: None if x is None else round(x, 4)

    def block(cids):
        S = {}
        for lab in CMP:
            ms = {}
            for subset in ("main", "all"):
                mac = dict(recall=ro(cs.macro_metric(PER, lab, subset, "recall", cids)),
                           prec=ro(cs.macro_metric(PER, lab, subset, "prec", cids)),
                           f1=ro(cs.macro_metric(PER, lab, subset, "f1", cids)),
                           jac=ro(cs.macro_metric(PER, lab, subset, "jac", cids)))
                mic = dict(recall=ro(cs.micro_metric(PER, lab, subset, "recall", cids)),
                           prec=ro(cs.micro_metric(PER, lab, subset, "prec", cids)),
                           f1=ro(cs.micro_metric(PER, lab, subset, "f1", cids)),
                           jac=ro(cs.micro_metric(PER, lab, subset, "jac", cids)))
                ms[subset] = dict(macro=mac, micro=mic)
            units = [PER[c]["new"][lab]["units_main"] for c in cids if PER[c]["new"].get(lab)]
            points = [PER[c]["new"][lab]["points_main"] for c in cids if PER[c]["new"].get(lab)]
            S[lab] = dict(metrics=ms,
                          mean_units_main=round(statistics.mean(units), 3) if units else None,
                          mean_points_main=round(statistics.mean(points), 3) if points else None,
                          sum_tp_main=sum(PER[c]["new"][lab]["main"]["tp"] for c in cids if PER[c]["new"].get(lab)))
        return S

    S = dict(n_cases=len(CASE_IDS), n_scored=len(SCORED), n_core=len(CORE),
             n_unscored=len(UNSCORED),
             unscored={c: PER[c]["note"] for c in UNSCORED},
             全量86=block(SCORED), 核心集64=block(CORE))
    for bucket in ("复诊", "首诊"):
        cs_ = [c for c in SCORED if PER[c]["vt"] == bucket]
        S.setdefault("visit分层", {})[bucket] = dict(n=len(cs_))
        for lab in CMP:
            S["visit分层"][bucket][lab] = dict(
                recall=ro(cs.macro_metric(PER, lab, "main", "recall", cs_)),
                f1=ro(cs.macro_metric(PER, lab, "main", "f1", cs_)))
    follow = [c for c in SCORED if PER[c]["chain"].startswith("followup")]
    anchor = [c for c in SCORED if PER[c]["chain"] == "first_visit" or PER[c]["chain"].startswith("anchor")]
    for nm, cs_ in [("followup", follow), ("anchor_first", anchor)]:
        S.setdefault("chain分层", {})[nm] = dict(n=len(cs_))
        for lab in CMP:
            S["chain分层"][nm][lab] = dict(
                recall=ro(cs.macro_metric(PER, lab, "main", "recall", cs_)),
                f1=ro(cs.macro_metric(PER, lab, "main", "f1", cs_)))
    S["零命中"] = {lab: [c for c in SCORED if PER[c]["new"][lab]["main"]["tp"] == 0] for lab in CMP}
    S["v12满分"] = [c for c in SCORED if PER[c]["new"]["v12"]["main"]["recall"]
                   and PER[c]["new"]["v12"]["main"]["recall"] >= 0.999]
    pts = [PER[c]["new"]["v12"]["points_main"] for c in SCORED]
    S["v12主穴统计"] = dict(
        mean_units=round(statistics.mean([PER[c]["new"]["v12"]["units_main"] for c in SCORED]), 3),
        mean_points=round(statistics.mean(pts), 3), min=min(pts), max=max(pts))
    same = diff = du = 0
    for c in CASE_IDS:
        a = set(BLIND["v11"][c].get("主穴", []))
        b = set(BLIND["v12"][c].get("主穴", []))
        if a == b:
            same += 1
        else:
            diff += 1
            du += len(a ^ b)
    S["执行方差_v12_vs_v11"] = dict(一致案=same, 差异案=diff, 差异单元=du)
    exp = {"86_v11": (S["全量86"]["v11"], dict(recall=0.4488, prec=0.4518, f1=0.4223, jac=0.2871)),
           "86_v9": (S["全量86"]["v9"], dict(recall=0.4390, prec=0.3653, f1=0.3795, jac=0.2499)),
           "核心_v11": (S["核心集64"]["v11"], dict(recall=0.4999, prec=0.4582, f1=0.4470, jac=0.3075)),
           "核心_v9": (S["核心集64"]["v9"], dict(recall=0.4914, prec=0.3827, f1=0.4074, jac=0.2722))}
    ok = True
    det = {}
    for k, (blk, w) in exp.items():
        row = {}
        for m, want in w.items():
            got = blk["metrics"]["main"]["macro"][m]
            match = got == want
            row[m] = dict(got=got, want=want, match=match)
            if not match:
                ok = False
        det[k] = row
    S["控制组核对"] = dict(一致=ok, detail=det)

    hdr = ["case_id", "visit_type", "chain", "核心集", "gold穴数"]
    for lab in CMP:
        hdr += [f"{lab}_主穴数", f"{lab}_TP", f"{lab}_FP", f"{lab}_FN",
                f"{lab}_R", f"{lab}_P", f"{lab}_F1", f"{lab}_Jac"]
    rows = []
    for c in CASE_IDS:
        row = [c, PER[c]["vt"], PER[c]["chain"], "Y" if PER[c]["core"] else "N", PER[c]["gc"]]
        for lab in CMP:
            dd = PER[c]["new"].get(lab)
            if dd is None or PER[c]["gc"] == 0:
                row += ["", "", "", "", "", "", "", ""]
            else:
                m = dd["main"]
                row += [dd["units_main"], m["tp"], m["fp"], m["fn"],
                        ro(m["recall"]), ro(m["prec"]), ro(m["f1"]), ro(m["jac"])]
        rows.append(row)
    csv.writer(open(OUT / "判分明细v12.csv", "w", newline="",
                    encoding="utf-8-sig")).writerows([hdr] + rows)

    m2rows = []
    for item, cases in M2.items():
        dTP = sum(PER[c]["new"]["v12"]["main"]["tp"] - PER[c]["new"]["v11"]["main"]["tp"]
                  for c in cases if c in PER and PER[c]["gc"] > 0)
        dFP = sum(PER[c]["new"]["v12"]["main"]["fp"] - PER[c]["new"]["v11"]["main"]["fp"]
                  for c in cases if c in PER and PER[c]["gc"] > 0)
        if dTP >= 1 and dFP <= 0:
            verdict = "有收益"
        elif dTP >= 1:
            verdict = "有收益(伴FP)"
        elif dTP == 0:
            verdict = "无收益"
        else:
            verdict = "负收益"
        m2rows.append([item, len(cases), dTP, dFP, verdict, ";".join(cases)])
    S["M2逐条收益"] = m2rows
    json.dump(S, open(OUT / "判分汇总v12.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("控制组一致=", ok)
    print("n_scored=", len(SCORED), "n_core=", len(CORE))


if __name__ == "__main__":
    main()
