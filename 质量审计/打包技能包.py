# -*- coding: utf-8 -*-
"""打包技能目录为 zip，并做解包自检。

用法：
    python 质量审计/打包技能包.py v20.1

输出：
    D:\\_blind_bundle_out\\doubao-acupuncture-diagnosis_<ver>.zip
    质量审计/2026-10-23_打包_<ver>_自检.txt
"""
import hashlib
import io
import os
import re
import shutil
import sys
import tempfile
import zipfile

ROOT = r"D:\projectAGI\nhx"
SK = os.path.join(ROOT, "doubao-acupuncture-diagnosis")
OUT_DIR = r"D:\_blind_bundle_out"
VER = sys.argv[1] if len(sys.argv) > 1 else "v20.1"
NAME = "doubao-acupuncture-diagnosis_%s.zip" % VER
ZPATH = os.path.join(OUT_DIR, NAME)

# ---------- 打包 ----------
files = []
for r, d, fs in os.walk(SK):
    for f in fs:
        rel = os.path.relpath(os.path.join(r, f), SK).replace("\\", "/")
        files.append(rel)
files.sort()

if os.path.exists(ZPATH):
    os.remove(ZPATH)
with zipfile.ZipFile(ZPATH, "w", zipfile.ZIP_DEFLATED) as z:
    for rel in files:
        z.write(os.path.join(SK, rel), "doubao-acupuncture-diagnosis/" + rel)

# ---------- 解包校验 ----------
tmp = tempfile.mkdtemp(prefix="verify_", dir=os.path.join(tempfile.gettempdir(), "opencode"))
with zipfile.ZipFile(ZPATH) as z:
    z.extractall(tmp)
    entries = [i.filename for i in z.infolist()]


def sha(p):
    h = hashlib.sha256()
    with io.open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


o = []
o.append("# 技能包打包自检 · %s" % VER)
o.append("")
o.append("- 包：`%s`" % ZPATH)
o.append("- 大小：**%d 字节**" % os.path.getsize(ZPATH))
o.append("- 条目：**%d**" % len(entries))
o.append("")

ok = True


def chk(name, cond, detail=""):
    global ok
    ok = ok and bool(cond)
    o.append("| %s | %s | %s |" % (name, "PASS" if cond else "FAIL", detail))


o.append("| 检查项 | 结果 | 说明 |")
o.append("|---|---|---|")
chk("条目数 = 磁盘文件数", len(entries) == len(files), "%d / %d" % (len(entries), len(files)))

# 逐文件哈希
bad = []
for rel in files:
    a = sha(os.path.join(SK, rel))
    b = sha(os.path.join(tmp, "doubao-acupuncture-diagnosis", rel))
    if a != b:
        bad.append(rel)
chk("全部文件 SHA256 一致", not bad, "不一致 %d 个 %s" % (len(bad), bad[:5]))

# 无多余条目
extra = [e for e in entries if e.split("/", 1)[-1] not in files]
chk("无多余条目", not extra, str(extra[:3]))

# 版本标记
sk = io.open(os.path.join(tmp, "doubao-acupuncture-diagnosis", "SKILL.md"),
             encoding="utf-8", errors="ignore").read()
for mark in ("**v20.1 变更基线", "**v20 变更基线", "**v19 变更基线**"):
    chk("标记 `%s`" % mark, mark in sk, "")

# 别名互通
kj = io.open(os.path.join(tmp, "doubao-acupuncture-diagnosis", "针灸篇-知识条目整理.md"),
             encoding="utf-8", errors="ignore").read()
for a in ("臑腧", "渊液", "譩嘻", "囟会", "聪会", "肩俞"):
    chk("别名词可检索 `%s`" % a, a in kj, "")

# 包内引用可解析
names = set(e.split("/", 1)[-1] for e in entries)
cands = set()
for m in re.finditer(r"`(references/[^`\s）)]+)`", sk):
    cands.add(m.group(1))
for m in re.finditer(r"`([^`\s/）)]+\.(?:md|json|txt|html))`", sk):
    cands.add(m.group(1))
unresolved = []
for c in sorted(cands):
    if "*" in c or "…" in c:
        continue          # 通配/省略写法，不当作具体文件
    rel = c if c.startswith("references/") else c
    if rel not in names:
        unresolved.append(c)
chk("包内引用可解析", not unresolved, "%d 个引用，未解析 %s" % (len(cands), unresolved))

# 关键不变量：规则条文未动（v19 的两处代表标记）
for probe in ("M2-03", "R-FU"):
    chk("不变量 `%s` 仍在 SKILL.md" % probe, probe in sk, "")

o.append("")
o.append("**总体：%s**" % ("PASS" if ok else "FAIL"))
o.append("")
o.append("## 文件清单")
o.append("")
o.append("| # | 文件 | 字节 |")
o.append("|---|---|---|")
for i, rel in enumerate(files, 1):
    o.append("| %d | %s | %d |" % (i, rel, os.path.getsize(os.path.join(SK, rel))))

ev = os.path.join(ROOT, "质量审计", "2026-10-23_打包_%s_自检.txt" % VER)
io.open(ev, "w", encoding="utf-8", newline="\n").write("\n".join(o) + "\n")
shutil.rmtree(tmp, ignore_errors=True)

sys.stdout.buffer.write(("zip=%s size=%d entries=%d result=%s\n"
                         % (NAME, os.path.getsize(ZPATH), len(entries),
                            "PASS" if ok else "FAIL")).encode("utf-8"))
