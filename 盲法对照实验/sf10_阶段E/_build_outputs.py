# -*- coding: utf-8 -*-
"""生成 误差分类表v10.csv / 高频漏穴表.csv / 高频误加穴表.csv 的核心逻辑，先打印核对。"""
import json, os, sys, re
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding='utf-8')
BASE = r"D:\projectAGI\nhx\盲法对照实验"
with open(os.path.join(BASE, r"sf10_阶段E\_consolidated.json"), encoding='utf-8') as f:
    cons = json.load(f)
ORDER = list(cons.keys())

# ============ 主诉类型人工归类（阅读來診原因后人工判定） ============
COMPLAINT = {
 '107_01':'肺病','117_01':'乳癌','118_01':'乳癌','136_01':'关节痛','137_01':'关节痛',
 '13_01':'胃病','140_01':'水肿','141_01':'水肿','142_01':'水肿','143_01':'水肿','144_01':'水肿',
 '145_01':'水肿','146_01':'水肿','148_01':'水肿','149_01':'水肿','156_03':'水肿','156_04':'水肿',
 '156_05':'水肿','156_06':'水肿','160_01':'其他','194_01':'关节痛','195_01':'其他','198_01':'其他',
 '199_01':'弱视','1_01':'肺病','200_01':'弱视','201_01':'弱视','202_01':'弱视','207_01':'关节痛',
 '208_01':'关节痛','209_01':'其他','212_01':'头痛','213_01':'头痛','214_01':'面瘫','216_01':'面瘫',
 '216_02':'面瘫','216_03':'面瘫','216_04':'面瘫','216_05':'面瘫','221_01':'关节痛','223_01':'关节痛',
 '225_01':'关节痛','22_01':'关节痛','234_01':'其他','236_01':'关节痛','23_01':'关节痛','249_01':'其他',
 '270_01':'其他','274_01':'其他','298_01':'其他','303_01':'其他','311_01':'其他','312_01':'其他',
 '318_01':'其他','323_01':'其他','340_01':'其他','342_01':'其他','345_01':'其他','346_01':'其他',
 '347_01':'乳癌','355_01':'其他','37_01':'其他','38_01':'其他','49_01':'肺病','55_01':'肺病',
 '57_01':'肺病','60_01':'乳癌','61_01':'乳癌','62_01':'乳癌','63_01':'乳癌','64_01':'乳癌','65_01':'乳癌',
 '66_01':'乳癌','67_01':'乳癌','68_01':'乳癌','69_01':'乳癌','70_01':'乳癌','71_01':'乳癌','72_01':'乳癌',
 '73_01':'乳癌','74_01':'乳癌','75_01':'乳癌','76_01':'乳癌','77_01':'乳癌','78_01':'乳癌','8_01':'关节痛',
 '116_01':'乳癌','178_01':'乳癌','268_01':'其他','278_01':'其他','284_01':'其他','285_01':'其他','80_01':'肺病',
}
assert len(COMPLAINT)==93, len(COMPLAINT)

# ============ 全局点->层 映射（v10 主穴记录中该点最常出现的层） ============
pt_layer = defaultdict(Counter)
for cid,c in cons.items():
    for p,recs in c['pointmap'].items():
        for r in recs:
            pt_layer[p][r['层']] += 1
def v10_layer(p):
    return pt_layer[p].most_common(1)[0][0] if p in pt_layer else None

# gold 侧常识层（v10 从未输出过的穴）
EIGHT = {'公孙','内关','后溪','申脉','列缺','照海','外关','足临泣','临泣','带脉'}
BEISHU = {'肺俞','心俞','肝俞','脾俞','肾俞','督俞','厥阴俞','胆俞','胃俞','膈俞','大杼','膏肓','天宗','至阳'}
MU = {'中脘','巨阙','关元','中极','日月','京门','章门','期门','天枢','膻中'}
SPECIAL = {'耳眼点','耳胆点','耳肾点','耳肝点','耳心点','定喘','腰腿点','天应','第十椎压痛点',
           '肝关','筑宾','眼四针','膝关','金津玉液','肘尖','痞根','大包','消积','通天','上星',
           '瞳子髎','少府','隐白','中渚','天府','少海','然谷','大杼','玉液','金津','极泉','睛明'}
def gold_side_layer(p):
    if p in EIGHT: return '八脉交会'
    if p in BEISHU or p in MU: return '俞募背俞'
    if p in SPECIAL: return '特效奇穴'
    return '对症'

def layer_of(p, is_fn):
    l = v10_layer(p)
    if l: return l + ('(gold侧)' if is_fn else '')
    return gold_side_layer(p) + '(gold侧)'

# ============ 透刺对检测（gold raw） ============
def touxi_pairs(raw):
    pairs = []
    for m in re.finditer(r'([\u4e00-\u9fff]{1,4})透([\u4e00-\u9fff]{1,4})', raw or ''):
        a,b = m.group(1), m.group(2)
        # 取最后2字以内作为穴名（OCR噪声）
        pairs.append((a,b))
    return pairs

# ============ 每案分类 ============
fn_rows = {}   # cid -> list of (point, label)
fp_rows = {}
for cid,c in cons.items():
    missing = set(c['missing'])
    is_chain = ('链解析' in c['gold_note']) or ('同前' in (c['gold_raw'] or '') and c['gold_note'])
    # 更准确：gold_note 有链解析 或 raw 是"同前/針同前穴/同穴"这类纯继承
    raw = c['gold_raw'] or ''
    pure_chain = ('链解析' in c['gold_note'])
    pairs = touxi_pairs(raw)
    tp = set(c['TP'])
    # FN 分类
    fl = []
    for p in c['FN']:
        label = None
        # 透刺口径：p 是 gold raw 中某透刺对的一端，且另一端在 TP
        for a,b in pairs:
            if p.endswith(a[-2:]) or p==a[-2:] or a.endswith(p):
                other = b[-2:]
                if other in tp:
                    label = '透刺-单元口径'
            if p.endswith(b[-2:]) or p==b[-2:] or b.endswith(p):
                other = a[-2:]
                if other in tp:
                    label = '透刺-单元口径'
        if label is None:
            # 资料缺失：耳穴/背俞/压痛点类而对应输入缺
            if p.startswith('耳') and '耳穴' in missing:
                label = '资料缺失'
            elif p.endswith('俞') and '触诊压痛' in missing:
                label = '资料缺失'
            elif p in ('廉泉','金津玉液') and ('舌象' in missing or '問診' in missing):
                label = '资料缺失'
            elif p == '第十椎压痛点' and '触诊压痛' in missing:
                label = '资料缺失'
        if label is None and pure_chain:
            label = '复诊历史缺失'
        if label is None:
            # 个体偏好：仅在很少案出现的特殊奇穴
            gold_freq = sum(1 for cc in cons.values() if p in cc['gold_members'])
            if p in ('肝关','极泉','第十椎压痛点','耳眼点','眼四针','腰腿点','筑宾','膝关') or gold_freq<=2:
                label = '个体偏好'
        if label is None:
            label = '规则未命中'
        fl.append((p,label))
    fn_rows[cid] = fl
    # FP 分类
    pl = []
    for p in c['FP']:
        recs = c['pointmap'].get(p, [])
        unit = recs[0]['单元'] if recs else ''
        rule = recs[0]['直接规则'] if recs else ''
        layer = recs[0]['层'] if recs else ''
        infer = recs[0]['推断'] if recs else ''
        label = None
        # 组穴展开：来自复合单元（+/透/组穴名）
        if '+' in unit or '透' in unit or unit in ('膝五针','三皇穴','开四关'):
            label = '组穴展开'
        elif layer=='八脉交会' or p in EIGHT:
            label = '八脉普遍加组'
        elif '兼证' in unit or infer=='是' and layer=='八脉交会':
            label = '兼证误入主穴'
        elif recs and ('背俞' in rule or '脏象' in rule or '眼诊' in (recs[0]['依据'] or '')):
            label = '证据不足仍出'
        if label is None:
            label = '其他'
        pl.append((p,label,unit,rule))
    fp_rows[cid] = pl

# ============ 打印核对 ============
print("=== 每案 FN归类分布 ===")
for cid in ORDER:
    fl = fn_rows[cid]
    if not fl: continue
    cc = Counter(l for _,l in fl)
    print(f"{cid} [{COMPLAINT[cid]}|{cons[cid]['visit_type'][:2]}] " +
          " ".join(f"{k}:{v}" for k,v in cc.most_common()))

print("\n=== 每案 FP归类分布 ===")
for cid in ORDER:
    pl = fp_rows[cid]
    if not pl: continue
    cc = Counter(l for _,l,_,_ in pl)
    print(f"{cid} " + " ".join(f"{k}:{v}" for k,v in cc.most_common()))

# 透刺口径命中检查
print("\n=== 透刺-单元口径 FN 命中 ===")
for cid in ORDER:
    for p,l in fn_rows[cid]:
        if l=='透刺-单元口径':
            print(f"  {cid}: {p}  gold_raw={cons[cid]['gold_raw'][:80]}")
