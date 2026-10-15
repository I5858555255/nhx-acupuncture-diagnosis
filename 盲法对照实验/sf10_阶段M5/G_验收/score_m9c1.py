# -*- coding: utf-8 -*-
import json,os,sys,pickle,csv,statistics,glob
ROOT=r'D:\projectAGI\nhx\盲法对照实验';BENCH=os.path.join(ROOT,'benchmark_v2')
HERE=os.path.join(ROOT,'sf10_阶段M5','G_验收')
sys.path.insert(0,BENCH)
from canonical_scorer import per_case_metrics, normalize_units
g=pickle.load(open(os.path.join(BENCH,'_gold_results93v2.pkl'),'rb'))
NEW=g['results'];CASE_IDS=g['case_ids'];SUMMARY=g['summary']
EXCLUDE=set(r['case_id'] for r in csv.DictReader(open(os.path.join(ROOT,'sf10_核心集','排除清单.csv'),encoding='utf-8-sig')))
M1=set(r['case_id'] for r in csv.DictReader(open(os.path.join(ROOT,'sf10_阶段M5','A_迁移核验','迁移核验逐案表.csv'),encoding='utf-8-sig')) if r['M1审计案']=='Y')
vt={r['case_id']:r.get('visit_type','') for r in csv.DictReader(open(os.path.join(ROOT,'sf10_阶段D','组装清单.csv'),encoding='utf-8-sig'))}
# 合并 66 折
MERGE={}
foldmap={}
for p in glob.glob(os.path.join(HERE,'M9-fold_*_pred.json')):
    fid=os.path.basename(p).replace('M9-fold_','').replace('_pred.json','')
    d=json.load(open(p,encoding='utf-8'))
    for c,rec in d.items():
        MERGE[c]=rec.get('主穴',[]);foldmap[c]=fid
SC=[c for c in CASE_IDS if len(NEW[c]['gold_members'])>0]
assert set(MERGE.keys())==set(SC),(set(SC)-set(MERGE.keys()))
CORE=[c for c in SC if c not in EXCLUDE]
def score(c):
    G=set(NEW[c]['gold_members']);P=normalize_units(MERGE[c]);return per_case_metrics(G,P)
PER={c:score(c) for c in SC}
def macro(cids,key):
    if key in ('tp','fp','fn'):return sum(PER[c][key] for c in cids)
    v=[PER[c][key] for c in cids if PER[c][key] is not None]
    return round(statistics.mean(v),4)
def blk(cids):return dict(TP=macro(cids,'tp'),FP=macro(cids,'fp'),FN=macro(cids,'fn'),
    R=macro(cids,'recall'),P=macro(cids,'prec'),F1=macro(cids,'f1'),Jac=macro(cids,'jac'))
visit_fu=[c for c in SC if str(vt.get(c,'')).startswith('复诊')]
visit_fs=[c for c in SC if c not in visit_fu]
out={'全量86':blk(SC),'核心集64':blk(CORE),'M1_28':blk([c for c in SC if c in M1]),
     '未M1_58':blk([c for c in SC if c not in M1]),'复诊visit':blk(visit_fu),'首诊visit':blk(visit_fs)}
# 每折
folds=[]
for r in csv.DictReader(open(os.path.join(HERE,'M9-链分组表.csv'),encoding='utf-8-sig')):
    cs=r['案号列表'].split()
    cs=[c for c in cs if c in PER]
    if not cs:continue
    folds.append([r['链ID'],len(cs),blk(cs)['TP'],blk(cs)['FP'],blk(cs)['FN'],blk(cs)['F1'],blk(cs)['Jac']])
json.dump(out,open(os.path.join(HERE,'M9-判分汇总.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
with open(os.path.join(HERE,'M9-每折结果.csv'),'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['链','案数','TP','FP','FN','F1','Jac']);w.writerows(folds)
with open(os.path.join(HERE,'M9-判分明细.csv'),'w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['case_id','chain','折','核心集','TP','FP','FN','R','P','F1','Jac'])
    for c in SC:
        m=PER[c];w.writerow([c,SUMMARY['chain_map'].get(c,''),foldmap[c],'核心集' if c not in EXCLUDE else '排除',
            m['tp'],m['fp'],m['fn'],round(m['recall'],4),round(m['prec'],4),round(m['f1'],4),round(m['jac'],4)])
print(json.dumps(out,ensure_ascii=False,indent=1))
print('折数',len(folds),'链F1均值',round(statistics.mean([r[5] for r in folds]),4))
