# -*- coding: utf-8 -*-
"""最终生成：误差分类表v10.csv / 高频漏穴表.csv / 高频误加穴表.csv"""
import json, os, sys, re, csv
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding='utf-8')
BASE = r"D:\projectAGI\nhx\盲法对照实验"
OUT = os.path.join(BASE, "sf10_阶段E")
with open(os.path.join(OUT, "_consolidated.json"), encoding='utf-8') as f:
    cons = json.load(f)
ORDER = list(cons.keys())

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

EIGHT = {'公孙','内关','后溪','申脉','列缺','照海','外关','足临泣','临泣','带脉'}
BEISHU = {'肺俞','心俞','肝俞','脾俞','肾俞','督俞','厥阴俞','胆俞','胃俞','膈俞','大杼','膏肓','天宗','至阳'}
MU = {'中脘','巨阙','关元','中极','日月','京门','章门','期门','天枢','膻中'}
SPECIAL_SINGLE = {'肝关','极泉','第十椎压痛点','耳眼点','眼四针','腰腿点','筑宾','膝关','金津玉液'}

pt_layer = defaultdict(Counter)
for cid,c in cons.items():
    for p,recs in c['pointmap'].items():
        for r in recs:
            pt_layer[p][r['层']] += 1
def v10_layer(p):
    return pt_layer[p].most_common(1)[0][0] if p in pt_layer else None
def gold_side_layer(p):
    if p in EIGHT: return '八脉交会'
    if p in BEISHU or p in MU: return '俞募背俞'
    if p in SPECIAL_SINGLE: return '特效奇穴'
    return '对症'
def layer_of(p, is_fn):
    l = v10_layer(p)
    base = l if l else gold_side_layer(p)
    return base + ('(gold侧)' if is_fn else '')

# gold 侧该穴出现案数（判断个体偏好）
gold_freq = Counter()
for cid,c in cons.items():
    for p in set(c['gold_members']):
        gold_freq[p] += 1

# 繁简归一（仅用于透刺匹配）
TRAD2SIM = {'養老':'养老','間使':'间使','太陽':'太阳','陽白':'阳白','魚腰':'鱼腰','地倉':'地仓',
            '頰車':'颊车','三間':'三间','後谿':'后溪','陰谷':'阴谷','承山':'承山','委中':'委中',
            '商丘':'商丘','丘墟':'丘墟','俠谿':'侠溪','足臨泣':'足临泣','頭臨泣':'头临泣',
            '睛明':'睛明','攢竹':'攒竹','解谿':'解溪','陽輔':'阳辅','頰車':'颊车','地倉透頬車':'地仓透颊车'}
def norm_t2s(s):
    for k,v in sorted(TRAD2SIM.items(), key=lambda kv:-len(kv[0])):
        s=s.replace(k,v)
    return s

def touxi_ends(raw, tp_set):
    """返回 FN 中属于透刺另一未命中端点的穴集合"""
    res=set()
    for m in re.finditer(r'([\u4e00-\u9fff]{1,4})透([\u4e00-\u9fff]{1,4})', raw or ''):
        a = norm_t2s(m.group(1)); b = norm_t2s(m.group(2))
        # 取最后 2 字
        a2,b2 = a[-2:], b[-2:]
        if a2 in tp_set and b2 not in tp_set: res.add(b2)
        if b2 in tp_set and a2 not in tp_set: res.add(a2)
    return res

# ============ 分类 ============
fn_rows={}; fp_rows={}; layer_rows={}
for cid in ORDER:
    c=cons[cid]
    missing=set(c['missing'])
    pure_chain = ('链解析' in c['gold_note'])
    tp=set(c['TP'])
    tx = touxi_ends(c['gold_raw'], tp)
    fl=[]
    for p in c['FN']:
        if p in tx:
            lab='透刺-单元口径'
        elif p.startswith('耳') and '耳穴' in missing:
            lab='资料缺失'
        elif p.endswith('俞') and '触诊压痛' in missing:
            lab='资料缺失'
        elif p in ('廉泉','金津玉液') and ('舌象' in missing or '問診' in missing):
            lab='资料缺失'
        elif p=='第十椎压痛点' and '触诊压痛' in missing:
            lab='资料缺失'
        elif pure_chain:
            lab='复诊历史缺失'
        elif p in SPECIAL_SINGLE or gold_freq[p]<=2:
            lab='个体偏好'
        else:
            lab='规则未命中'
        fl.append((p,lab))
    fn_rows[cid]=fl
    pl=[]
    for p in c['FP']:
        recs=c['pointmap'].get(p,[])
        unit=recs[0]['单元'] if recs else ''
        rule=recs[0]['直接规则'] if recs else ''
        layer=recs[0]['层'] if recs else ''
        infer=recs[0]['推断'] if recs else ''
        if p in EIGHT:
            lab='八脉普遍加组'
        elif ('+' in unit) or ('透' in unit) or unit in ('膝五针','三皇穴','开四关'):
            lab='组穴展开'
        elif ('背俞' in rule) or ('脏象' in rule) or ('特效库' in rule) or layer=='俞募背俞':
            lab='证据不足仍出'
        elif infer=='是':
            lab='兼证误入主穴'
        else:
            lab='其他'
        pl.append((p,lab,unit,rule))
    fp_rows[cid]=pl
    # 四层归因
    fn_layers=Counter(layer_of(p,True) for p in c['FN'])
    fp_layers=Counter(layer_of(p,False) for p in c['FP'])
    fns=';'.join(f"{k}×{v}" for k,v in fn_layers.most_common()) or '无'
    fps=';'.join(f"{k}×{v}" for k,v in fp_layers.most_common()) or '无'
    layer_rows[cid]=f"FN:{fns} | FP:{fps}"

# ============ 写 误差分类表v10.csv ============
cols=['case_id','主诉类型','首复诊','输入完整度(缺失字段数/14)','四层分类',
      '主穴点数','gold点数','TP','FN数','FP数','FN穴清单','FP穴清单','FN归类','FP归类']
with open(os.path.join(OUT,'误差分类表v10.csv'),'w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f); w.writerow(cols)
    for cid in ORDER:
        c=cons[cid]
        fcc=Counter(l for _,l in fn_rows[cid])
        fpc=Counter(l for _,l,_,_ in fp_rows[cid])
        w.writerow([
            cid, COMPLAINT[cid], c['visit_type'][:2], f"{c['n_missing']}/14",
            layer_rows[cid], c['v10_points'], c['gold_n_csv'], len(c['TP']),
            len(c['FN']), len(c['FP']),
            ';'.join(c['FN']), ';'.join(c['FP']),
            ';'.join(f"{k}:{v}" for k,v in fcc.most_common()) or '无',
            ';'.join(f"{k}:{v}" for k,v in fpc.most_common()) or '无',
        ])

# ============ 高频漏穴表 ============
fn_cases=defaultdict(list)
for cid in ORDER:
    for p in cons[cid]['FN']:
        fn_cases[p].append(cid)
rows=[]
for p,cs in fn_cases.items():
    comps=sorted(set(COMPLAINT[x] for x in cs))
    fu=sum(1 for x in cs if cons[x]['visit_type'].startswith('复'))
    chain_n=sum(1 for x in cs if '链解析' in cons[x]['gold_note'])
    L=layer_of(p,True).replace('(gold侧)','')
    role = '链继承(同前)主方组成穴' if chain_n>=len(cs)*0.5 else ('本案首方组成穴' if chain_n==0 else f'半链半首({chain_n}/{len(cs)})')
    rows.append([p,len(cs),'/'.join(comps),L,
                 f"复诊{fu}/首诊{len(cs)-fu}",
                 ';'.join(cs[:4]), role])
rows.sort(key=lambda r:-r[1])
with open(os.path.join(OUT,'高频漏穴表.csv'),'w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f)
    w.writerow(['归一化后点','出现案数','涉及主诉类型','四层(gold侧)','首复诊分布','典型案号','在gold链解析中的角色'])
    w.writerows(rows)

# ============ 高频误加穴表 ============
fp_cases=defaultdict(list)
fp_rule=defaultdict(Counter)
fp_isexpand=defaultdict(lambda:[0,0])
for cid in ORDER:
    for p,lab,unit,rule in fp_rows[cid]:
        fp_cases[p].append(cid)
        fp_rule[p][rule]+=1
        if lab=='组穴展开': fp_isexpand[p][0]+=1
        if lab=='八脉普遍加组': fp_isexpand[p][1]+=1
rows2=[]
for p,cs in fp_cases.items():
    comps=sorted(set(COMPLAINT[x] for x in cs))
    top_rule=fp_rule[p].most_common(1)[0][0]
    exp,eight=fp_isexpand[p]
    tag='组穴/透刺端点' if exp>=max(1,len(cs)*0.5) else ('八脉对组成端' if eight>=max(1,len(cs)*0.5) else '单点规则')
    L=v10_layer(p) or gold_side_layer(p)
    rows2.append([p,len(cs),'/'.join(comps),L,top_rule,';'.join(cs[:4]),tag])
rows2.sort(key=lambda r:-r[1])
with open(os.path.join(OUT,'高频误加穴表.csv'),'w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f)
    w.writerow(['穴名','出现案数','涉及主诉','四层(v10)','触发规则(主穴记录.直接规则)','典型案号','是否组穴展开/透刺端点'])
    w.writerows(rows2)

print("written. FN unique points:",len(fn_cases)," FP unique points:",len(fp_cases))
print("\n== 漏穴 Top15 ==")
for r in rows[:15]: print(r[:5])
print("\n== 误加 Top15 ==")
for r in rows2[:15]: print(r[:5])
