# -*- coding: utf-8 -*-
"""simulate_rule_changes.py — SF10 阶段E·候选规则改动前后分差评估（E2）

方法（可复算模拟）：
- 只读 v10 盲法输出（_blind93v10_results.json）+ gold pkl + normalize_acupoints；
- 不重跑盲法：每项改动 = 对 v10 主穴单元列表的一次确定性修改（删除/追加单元），
  主穴记录（穴/层/依据/直接规则/推断）与主穴顺序一一对应，删除按记录行定位单元；
- 重算 86 个判分案逐案 TP/FP/FN → 宏平均 recall/precision/F1/Jaccard（main 与 main+all 各一组）；
- 每项改动独立评估，互不叠加。

基线（宏 main，v10 原值）：R=0.4125 P=0.3732 F1=0.3685 Jac=0.2440。
"""
import json, os, sys, csv, pickle, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = r"D:\projectAGI\nhx\盲法对照实验"
BENCH = os.path.join(ROOT, "benchmark_v2")
sys.path.insert(0, BENCH)
from normalize_acupoints import normalize_acupoints, expand_composite_point

BLIND_PATH = os.path.join(ROOT, "盲法93_v10", "_blind93v10_results.json")
GOLD_PATH = os.path.join(BENCH, "_gold_results93v2.pkl")

# ---------------- 载入 ----------------
BLIND = json.load(open(BLIND_PATH, encoding="utf-8"))
G = pickle.load(open(GOLD_PATH, "rb"))
GOLD_RES = G["results"]
CASE_IDS = G["case_ids"]
SCORED = [c for c in CASE_IDS if len(GOLD_RES[c]["gold_members"]) > 0]

# 八脉交会配对键：单元展开点 -> 配对组名
PAIR_OF_POINT = {
    "公孙": "公孙内关", "内关": "公孙内关",
    "后溪": "后溪申脉", "申脉": "后溪申脉",
    "列缺": "列缺照海", "照海": "列缺照海",
    "外关": "外关临泣", "临泣": "外关临泣", "足临泣": "外关临泣",
    "合谷": "开四关", "太冲": "开四关",
}


def pair_key_of_unit(unit):
    pts = expand_composite_point(unit)
    keys = set(PAIR_OF_POINT.get(p) for p in pts)
    keys.discard(None)
    return keys  # 该单元所属的配对组集合


def case_base(cid):
    """返回 (主穴单元列表, 佐穴单元列表, gold点集)。"""
    rec = BLIND[cid]
    return list(rec.get("主穴", [])), list(rec.get("佐穴", [])), set(GOLD_RES[cid]["gold_members"])


def metrics_of(G, P):
    tp = len(P & G); fp = len(P - G); fn = len(G - P)
    rec = tp / len(G) if G else None
    prec = tp / len(P) if P else None
    f1 = (2 * prec * rec / (prec + rec)) if (prec and rec) else (0.0 if tp == 0 else None)
    jac = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0.0
    return dict(tp=tp, fp=fp, fn=fn, recall=rec, prec=prec, f1=f1, jac=jac)


def macro_over(scored_cids, units_main_per_case, units_aux_per_case):
    """对每个判分案用给定单元列表重算，返回宏均值(main) 与 (main+all)。"""
    out = {"main": {}, "all": {}}
    for subset in ("main", "all"):
        acc = {"recall": [], "prec": [], "f1": [], "jac": []}
        for c in scored_cids:
            G = set(GOLD_RES[c]["gold_members"])
            um = units_main_per_case[c]
            ua = units_aux_per_case[c]
            Pm = normalize_acupoints(um)
            P = Pm | normalize_acupoints(ua) if subset == "all" else Pm
            m = metrics_of(G, P)
            for k in acc:
                if m[k] is not None:
                    acc[k].append(m[k])
        for k, v in acc.items():
            out[subset][k] = statistics.mean(v) if v else None
    return out


# ---------------- 基线重算 ----------------
base_main = {c: case_base(c)[0] for c in CASE_IDS}
base_aux = {c: case_base(c)[1] for c in CASE_IDS}
BASE = macro_over(SCORED, base_main, base_aux)

# ---------------- 候选改动定义 ----------------
# 每个改动: 返回 dict {case_id: 新主穴单元列表}（未触发案原样）
# 主穴记录行与主穴单元顺序一一对应，删除按记录行定位。

def change_C1(cid):
    """C1 灸法奇穴移出主穴：第4层/记录中“灸法操作奇穴”（肘尖等，特效库 plan 表述为‘灸X隔姜灸’的操作穴）
    不进针刺主穴集合，移入临床参考建议手法注。触发：主穴单元含‘肘尖’。"""
    rec = BLIND[cid]
    units = list(rec.get("主穴", []))
    recs = rec.get("主穴记录", [])
    out = []
    for u, m in zip(units, recs):
        if m.get("层") == "特效奇穴" and m["穴"] in ("肘尖", "天应", "天應"):
            continue  # 移出主穴
        out.append(u)
    return out


def change_C2(cid):
    """C2 八脉交会层同组拆穴合并计1组；异组配对并列时仅保留第1组（按主证配穴证据顺序），
    第2组起移入临床参考建议。触发：第3层展开后配对组集合 >=2。"""
    rec = BLIND[cid]
    units = list(rec.get("主穴", []))
    recs = rec.get("主穴记录", [])
    kept_groups = []
    out = []
    for u, m in zip(units, recs):
        if m.get("层") == "八脉交会":
            ks = pair_key_of_unit(u)
            if not ks:  # 非配对单元（原络等）保留
                out.append(u); continue
            new = [k for k in ks if k not in kept_groups]
            if not kept_groups:  # 第1组整体保留
                kept_groups.extend(ks); out.append(u); continue
            if all(k in kept_groups for k in ks):  # 同组拆穴：保留
                out.append(u); continue
            # 第2组及以后配对：删除（移入临床参考建议）
            kept_groups.extend(new)
            continue
        out.append(u)
    return out


def change_C3(cid):
    """C3 第2层俞募背俞收紧：仅依据含‘压痛定位/压痛点’的背俞保留主穴；
    纯脏象推断（舌/脉/眼诊/腹诊脏象）的俞募背俞移入临床参考建议。"""
    rec = BLIND[cid]
    units = list(rec.get("主穴", []))
    recs = rec.get("主穴记录", [])
    out = []
    for u, m in zip(units, recs):
        if m.get("层") == "俞募背俞" and "压痛" not in (m.get("依据") or ""):
            continue
        out.append(u)
    return out


def change_C4(cid):
    """C4 无原文依据穴移出主穴：主穴记录‘依据缺失’或‘直接规则=否’的穴
    （属兼证调理/推测）移入临床参考建议。"""
    rec = BLIND[cid]
    units = list(rec.get("主穴", []))
    recs = rec.get("主穴记录", [])
    out = []
    for u, m in zip(units, recs):
        ev = m.get("依据") or ""
        dr = m.get("直接规则") or ""
        if ("依据缺失" in ev) or (dr == "否"):
            continue
        out.append(u)
    return out


def change_C5(cid):
    """C5 乳癌硬块案第1层远取组补梁丘：第4层命中乳癌/灸条（肘尖）的案，
    若主穴尚未含梁丘，按指南留气法（胃经硬块取足三里、上巨虚、梁丘）补入梁丘。"""
    rec = BLIND[cid]
    units = list(rec.get("主穴", []))
    recs = rec.get("主穴记录", [])
    hit = any(m.get("层") == "特效奇穴" and m["穴"] in ("肘尖",) for m in recs)
    if not hit:
        return units
    P = normalize_acupoints(units)
    if "梁丘" not in P:
        return units + ["梁丘"]
    return units


def change_C6(cid):
    """C6 兼证调理穴移入临床参考建议：主穴记录 推断=是 的穴整体移出主穴集合。"""
    rec = BLIND[cid]
    units = list(rec.get("主穴", []))
    recs = rec.get("主穴记录", [])
    out = []
    for u, m in zip(units, recs):
        if m.get("推断") == "是":
            continue
        out.append(u)
    return out


CHANGES = [
    ("C1", change_C1, "灸法奇穴（肘尖等‘灸X隔姜灸’操作穴）移出主穴集合，降为临床参考建议手法注"),
    ("C2", change_C2, "八脉交会层同组拆穴合并计1组；异组配对并列仅保留第1组，第2组起移入临床参考建议"),
    ("C3", change_C3, "第2层俞募背俞仅‘压痛定位/压痛点’依据保留；纯脏象（舌/脉/眼/腹诊）推断的背俞移入临床参考建议"),
    ("C4", change_C4, "主穴记录‘依据缺失’或‘直接规则=否’的穴移出主穴集合（兼证调理入临床参考建议）"),
    ("C5", change_C5, "第4层命中乳癌灸条（肘尖）的案，第1层远取组按指南留气法补梁丘（缺则补）"),
    ("C6", change_C6, "主穴记录‘推断=是’的兼证调理穴整体移出主穴集合"),
]

# ---------------- 逐项评估 ----------------
ro = lambda x: None if x is None else round(x, 4)
rows = []
detail = []
for cid, fn, desc in CHANGES:
    new_main = {c: (fn(c) if c in BLIND else base_main[c]) for c in CASE_IDS}
    res = macro_over(SCORED, new_main, base_aux)
    triggered = [c for c in SCORED if c in BLIND and new_main[c] != base_main[c]]
    detail.append((cid, desc, triggered, BASE, res))
    rows.append(dict(
        id=cid, desc=desc,
        n_trig=len(triggered), trig_cases=triggered,
        before=BASE, after=res,
    ))

# ---------------- 控制台输出 ----------------
print("=== 基线重算（宏 main）===")
print("R=%.4f P=%.4f F1=%.4f Jac=%.4f" % (
    BASE["main"]["recall"], BASE["main"]["prec"], BASE["main"]["f1"], BASE["main"]["jac"]))
print("=== 基线重算（宏 all）===")
print("R=%.4f P=%.4f F1=%.4f Jac=%.4f" % (
    BASE["all"]["recall"], BASE["all"]["prec"], BASE["all"]["f1"], BASE["all"]["jac"]))
print()
for cid, desc, trig, b, a in detail:
    dm, da = a["main"], a["all"]
    print("=== %s %s ===" % (cid, desc))
    print("  触发案数=%d 触发案号=%s" % (len(trig), ",".join(trig[:12])))
    print("  main 前: R=%.4f P=%.4f F1=%.4f Jac=%.4f" % (b["main"]["recall"], b["main"]["prec"], b["main"]["f1"], b["main"]["jac"]))
    print("  main 后: R=%.4f P=%.4f F1=%.4f Jac=%.4f" % (dm["recall"], dm["prec"], dm["f1"], dm["jac"]))
    print("  main Δ:  dR=%+.4f dP=%+.4f dF1=%+.4f dJac=%+.4f" % (
        dm["recall"]-b["main"]["recall"], dm["prec"]-b["main"]["prec"],
        dm["f1"]-b["main"]["f1"], dm["jac"]-b["main"]["jac"]))
    print("  all  后: R=%.4f P=%.4f F1=%.4f Jac=%.4f | ΔdF1=%+.4f ΔdJac=%+.4f" % (
        da["recall"], da["prec"], da["f1"], da["jac"],
        da["f1"]-b["all"]["f1"], da["jac"]-b["all"]["jac"]))
    print()

# ---------------- 写评估 CSV ----------------
EVIDENCE = {
    "C1": "特效库全量.json《乳癌初期与中期肿块治疗》plan‘淋巴结肿胀灸肩井、肘尖’、《朝食暮吐与腹膜炎》plan‘腹膜炎灸肘尖穴（手肘尖端，三焦经）’、《盲肠炎与奔豚症》method‘腹膜炎肘尖穴隔姜灸’；SKILL.md 环节5.5‘天應隔姜灸降为备选手法注入临床参考建议’同构规则（灸法操作≠针刺主穴集合）。",
    "C2": "SKILL.md 第3层规则‘单证案出1组即可，无明确配穴证据不强加第2组，勿为扩量普遍加组稀释精确；主证跨二经或两个独立主诉并存时才取2组并列’；指南附录A八脉交会速查：公孙内关=胃心胸、后溪申脉=督脉颈项、列缺照海=任脉喉、外关临泣=阳维胸胁带脉（按所通奇经主治，非叠加）。",
    "C3": "SKILL.md 第2层规则‘背俞穴必须按4.3背俞压痛定位（压痛点→对应俞穴）；原案风格=无压痛证据不下背俞（如腰背痛案仅出委中阴谷承山）；无脏象信号或无压痛定位时第2层为空’。",
    "C4": "SKILL.md 检索纪律‘找不到原文依据的选穴须明示“依据缺失，按XX推断”，宁可少选、不编造出处’；主穴记录五字段契约（直接规则=否=无直接规则命中）。",
    "C5": "诊断与针灸实施指南.md 第492行留气法（治痞块硬块肿瘤）‘远取穴（如胃经硬块取足三里、上巨虚、梁丘）’；第304行‘乳房硬块：乳头属肝经、乳上胃经……按所在经络辨证取穴’。",
    "C6": "SKILL.md 输出契约‘原案复现处方（主穴）与临床参考建议（兼证调理建议）彻底分离；兼证调理穴一律入临床参考建议字段，严禁并入主穴数组’。",
}

out_csv = os.path.join(HERE, "候选规则改动评估表.csv")
header = ["改动ID", "改动描述", "原案依据", "触发案数", "触发案号(≤10个列举)",
          "前recall", "前prec", "前F1", "前Jac",
          "后recall", "后prec", "后F1", "后Jac", "ΔF1", "ΔJac",
          "判定(建议/撤回/条件建议)", "判定理由"]
with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(header)
    for r in rows:
        b, a = r["before"]["main"], r["after"]["main"]
        dF1 = a["f1"] - b["f1"]; dJac = a["jac"] - b["jac"]
        dR = a["recall"] - b["recall"]; dP = a["prec"] - b["prec"]
        if dF1 > 0.003:
            verdict = "建议"; reason = "宏F1 %.4f→%.4f（Δ%+.4f），精度提升且召回损失可接受" % (b["f1"], a["f1"], dF1)
        elif dF1 > -0.003 and dR > 0 and dP > -0.03:
            verdict = "条件建议"; reason = "宏F1基本持平（Δ%+.4f），召回%+.4f、精度%+.4f，视目标权衡" % (dF1, dR, dP)
        else:
            verdict = "撤回"; reason = "宏F1 %.4f→%.4f（Δ%+.4f），无可复现收益" % (b["f1"], a["f1"], dF1)
        w.writerow([
            r["id"], r["desc"], EVIDENCE[r["id"]], r["n_trig"],
            "、".join(r["trig_cases"][:10]),
            ro(b["recall"]), ro(b["prec"]), ro(b["f1"]), ro(b["jac"]),
            ro(a["recall"]), ro(a["prec"]), ro(a["f1"]), ro(a["jac"]),
            ("%+.4f" % dF1), ("%+.4f" % dJac), verdict, reason,
        ])
print("CSV written:", out_csv)
