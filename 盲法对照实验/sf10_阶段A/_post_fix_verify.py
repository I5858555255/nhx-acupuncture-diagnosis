# -*- coding: utf-8 -*-
"""SF10 阶段A：路径修复后回归验证（gold重跑×score三连跑，哈希对基线）"""
import hashlib, json, os, subprocess, sys

BENCH = r"D:\projectAGI\nhx\盲法对照实验\benchmark_v2"
OUT = r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段A"
BACKUP = os.path.join(OUT, "备份_运行前")
SCORE_FILES = ["判分明细v2.csv", "判分汇总v2.json", "审计日志v2.json"]
GOLD_FILES = ["_gold_results93v2.json", "_gold_results93v2.pkl"]

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

report = {}

# 基线哈希
base = {fn: sha256(os.path.join(BACKUP, fn)) for fn in SCORE_FILES + GOLD_FILES}
report["baseline"] = base

# 1) 重跑 gold_parse93v2.py
r = subprocess.run([sys.executable, "gold_parse93v2.py"], cwd=BENCH,
                   capture_output=True, text=True, encoding="utf-8")
report["gold_rerun_rc"] = r.returncode
report["gold_rerun_tail"] = r.stdout.strip().splitlines()[-4:] if r.stdout else []
gold_after = {fn: sha256(os.path.join(BENCH, fn)) for fn in GOLD_FILES}
report["gold_after_rerun"] = gold_after
report["gold_hashes_equal_baseline"] = all(
    gold_after[fn] == base[fn] for fn in GOLD_FILES)
print("gold 重跑 rc=", r.returncode, " 哈希=基线:", report["gold_hashes_equal_baseline"])
for fn in GOLD_FILES:
    print(f"  {fn}: after={gold_after[fn][:16]}... base={base[fn][:16]}... match={gold_after[fn]==base[fn]}")

# 2) score 三连跑
runs = []
for i in range(1, 4):
    r = subprocess.run([sys.executable, "score_benchmark_v2.py"], cwd=BENCH,
                       capture_output=True, text=True, encoding="utf-8")
    h = {fn: sha256(os.path.join(BENCH, fn)) for fn in SCORE_FILES}
    runs.append({"run": i, "rc": r.returncode, "hashes": h})
    print(f"score run{i} rc={r.returncode}")
report["score_runs"] = runs
consistent = True
for fn in SCORE_FILES:
    hs = [run["hashes"][fn] for run in runs]
    ok3 = len(set(hs)) == 1
    okb = hs[0] == base[fn]
    print(f"  CHECK {fn}: 三连跑一致={ok3} 与基线一致={okb}")
    if not (ok3 and okb):
        consistent = False
report["score_all_consistent"] = consistent
print("SCORE_ALL_CONSISTENT =", consistent)

with open(os.path.join(OUT, "_post_fix_verify.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
