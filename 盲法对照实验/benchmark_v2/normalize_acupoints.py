# -*- coding: utf-8 -*-
"""normalize_acupoints.py — 统一穴位归一化器（BENCHMARK-AUDIT-01 工作项 B）

契约：gold 与所有轮次（v140..v9）的预测共用同一实现。
语义：输入"穴名输出单元"列表（可含操作注、透刺、X+Y 复合、组穴名），
     输出规范化穴位集合（穴位级口径：组合只展开成组成穴，不保留父级组名）。

三个拆分函数：
  normalize_procedure_note(u)  — 操作注/手法注 → 穴位本体
  normalize_point_name(u)      — 单个点 → 规范名（操作注、耳穴、别名、繁简）
  expand_composite_point(u)    — 一个输出单元 → 规范穴集（组穴、透刺、X+Y）
  normalize_acupoints(units)   — 单元列表 → 规范穴集
"""

# ---- 操作注 / 手法注 → 穴位本体（长串优先；对整单元做）----
PROCEDURE_NOTES = [
    ('天应隔姜灸', '天应'),
    ('天應隔姜灸', '天应'),
    ('灸关元', '关元'),
    ('灸中脘', '中脘'),
    ('灸天枢', '天枢'),
    ('上星米粒灸', '上星'),
    ('耳尖放血', '耳尖'),
    ('委中放血', '委中'),
    ('少商放血', '少商'),
    ('商阳放血', '商阳'),
]

# ---- 耳穴别名统一表（合并旧 gold preprocess 与旧 score expand_post 两侧规则）----
EAR_ALIAS = {
    '耳胆石点': '耳胆点',
    '双耳肾点': '耳肾点',
    '右耳肾点': '耳肾点',
    '左耳肾点': '耳肾点',
    '耳针肾点': '耳肾点',
    '耳针肾膀胱区压痛点': '耳肾点',
    '耳针胆点': '耳胆点',
    '埋耳针<胆>': '耳胆点',
    '耳穴肝点': '耳肝点',
    '耳针埋肝点': '耳肝点',
    '耳针心点': '耳心点',
    '心脏点': '耳心点',
    '正心点': '耳心点',
    '耳针埋心的压痛点': '耳心点',
    '耳针心的压痛点': '耳心点',
    '埋耳针(眼)': '耳眼点',
}

# ---- 穴名别名（gold 与预测共用）----
POINT_ALIAS = {
    '肩禺': '肩髃',
    '肩臑': '肩髃',
    '中睕': '中脘',
    '大凌': '大陵',
    '太谿': '太溪',
    '腿腰点': '腰腿点',
    '肾石点': '肾结石点',
    '三里': '足三里',
    '膀胱募': '中极',
    '第十椎': '第十椎压痛点',
}

# ---- 组穴展开（穴位级口径：只保留组成穴，不保留父级组名）----
COMPOSITE_GROUPS = {
    '膝五针': ['鹤顶', '内膝眼', '外膝眼', '阴陵泉'],
    '三皇穴': ['阴陵泉', '地机', '三阴交'],
    '开四关': ['合谷', '太冲'],
}


def normalize_procedure_note(u):
    """操作注/手法注 → 穴位本体。输入应为单个单元。"""
    u = u.strip()
    for src, dst in PROCEDURE_NOTES:
        if u == src:
            return dst
    return u


def normalize_point_name(u):
    """单个点（已剥离透刺/复合）→ 规范名。"""
    u = normalize_procedure_note(u)
    u = EAR_ALIAS.get(u, u)
    u = POINT_ALIAS.get(u, u)
    return u


def expand_composite_point(u):
    """一个输出单元 → 规范穴集（组穴 → 组成穴；A透B → 两端；X+Y → 拆开）。"""
    u = u.strip()
    if not u:
        return set()
    if u in COMPOSITE_GROUPS:
        return set(normalize_point_name(x) for x in COMPOSITE_GROUPS[u])
    u = normalize_procedure_note(u)
    if u in EAR_ALIAS:
        u = EAR_ALIAS[u]
    if '透' in u:
        a, b = u.split('透', 1)
        return {normalize_point_name(a), normalize_point_name(b)}
    if '+' in u:
        return set(normalize_point_name(x) for x in u.split('+'))
    return {normalize_point_name(u)}


def normalize_acupoints(units):
    """穴名单元列表 → 规范化穴位集合（去重）。units 可为 None。"""
    out = set()
    for u in (units or []):
        out |= expand_composite_point(u)
    return out


# ================= 单元测试 =================
def _run_tests():
    cases = [
        # (输入单元列表, 期望集合)
        (['合谷透后溪'], {'合谷', '后溪'}),
        (['公孙+内关'], {'公孙', '内关'}),
        (['膝五针'], {'鹤顶', '内膝眼', '外膝眼', '阴陵泉'}),
        (['三皇穴'], {'阴陵泉', '地机', '三阴交'}),
        (['开四关'], {'合谷', '太冲'}),
        (['灸关元'], {'关元'}),
        (['灸中脘'], {'中脘'}),
        (['委中放血'], {'委中'}),
        (['少商放血'], {'少商'}),
        (['耳胆石点'], {'耳胆点'}),
        (['心脏点'], {'耳心点'}),
        (['肩禺'], {'肩髃'}),
        (['肩臑'], {'肩髃'}),
        (['天應隔姜灸'], {'天应'}),
        (['天应隔姜灸'], {'天应'}),
        (['第十椎'], {'第十椎压痛点'}),
        (['三里'], {'足三里'}),
        ([], set()),
        (None, set()),
        ([' 足三里 '], {'足三里'}),
        # 精确率不超 100% 契约：单透刺单元两端都命中，规范集 2 点、TP 2
        (['合谷透后溪'], {'合谷', '后溪'}),
    ]
    ok = True
    for units, expected in cases:
        got = normalize_acupoints(units)
        if got != expected:
            ok = False
            print(f"FAIL: {units!r} -> {got!r} != {expected!r}")
    # 契约：透刺单元两端命中时点级精确率 = TP/|P| <= 1.0
    p = normalize_acupoints(['合谷透后溪'])
    g = {'合谷', '后溪'}
    tp = len(p & g)
    prec = tp / len(p)
    if not (len(p) == 2 and tp == 2 and prec == 1.0):
        ok = False
        print(f"FAIL: 透刺契约 p={p} tp={tp} prec={prec}")
    print("PASS" if ok else "FAIL")
    return ok


if __name__ == '__main__':
    _run_tests()
