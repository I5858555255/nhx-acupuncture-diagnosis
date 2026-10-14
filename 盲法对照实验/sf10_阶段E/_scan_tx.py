# -*- coding: utf-8 -*-
import json, os, sys, re
sys.stdout.reconfigure(encoding='utf-8')
BASE = r"D:\projectAGI\nhx\盲法对照实验"
with open(os.path.join(BASE, r"sf10_阶段E\_consolidated.json"), encoding='utf-8') as f:
    cons = json.load(f)
TRAD2SIM = {'養老':'养老','間使':'间使','太陽':'太阳','陽白':'阳白','魚腰':'鱼腰','地倉':'地仓',
            '頰車':'颊车','三間':'三间','後谿':'后溪','陰谷':'阴谷','商丘':'商丘','丘墟':'丘墟',
            '俠谿':'侠溪','足臨泣':'足临泣','頭臨泣':'头临泣','睛明':'睛明','攢竹':'攒竹','解谿':'解溪',
            '陽輔':'阳辅','陽陵泉':'阳陵泉','陰陵泉':'阴陵泉','足三里':'足三里','公孫':'公孙',
            '內關':'内关','關元':'关元','巨闕':'巨阙','照海':'照海','復溜':'复溜','水泉':'水泉',
            '太谿':'太溪','束骨':'束骨','崑崙':'昆仑','委中':'委中','承山':'承山','漏谷':'漏谷',
            '地倉透頬車':'地仓透颊车','陽白透魚腰':'阳白透鱼腰','右太陽透率谷':'右太阳透率谷',
            '太陽透率谷':'太阳透率谷','左商丘透丘墟':'左商丘透丘墟','左養老透間使':'左养老透间使'}
def norm(s):
    for k,v in sorted(TRAD2SIM.items(), key=lambda kv:-len(kv[0])): s=s.replace(k,v)
    return s
for cid,c in cons.items():
    raw=c['gold_raw'] or ''
    tp=set(c['TP']); fn=set(c['FN'])
    for m in re.finditer(r'([\u4e00-\u9fff]{1,4})透([\u4e00-\u9fff]{1,4})', raw):
        a=norm(m.group(1))[-2:]; b=norm(m.group(2))[-2:]
        status=[]
        for x in (a,b):
            if x in tp: status.append(f"{x}=TP")
            elif x in fn: status.append(f"{x}=FN")
            else: status.append(f"{x}=?")
        print(cid, m.group(0), '->', ', '.join(status))
