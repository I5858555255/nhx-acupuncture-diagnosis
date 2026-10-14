# -*- coding: utf-8 -*-
"""SF10 阶段A：三连跑 + SHA-256 记录（避免 PowerShell 编码问题）"""
import hashlib, json, os, subprocess, sys

BENCH = r"D:\projectAGI\nhx\盲法对照实验\benchmark_v2"
OUT = r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段A"
BACKUP = os.path.join(OUT, "备份_运行前")
TARGETS = ["判分明细v2.csv", "判分汇总v2.json", "审计日志v2.json"]
GOLD = ["_gold_results93v2.json", "_gold_results93v2.pkl"]

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

result = {"backup_hashes": {}, "runs": []}

# 备份基线哈希
for fn in TARGETS + GOLD:
    result["backup_hashes"][fn] = sha256(os.path.join(BACKUP, fn))

# 三连跑
for i in range(1, 4):
    r = subprocess.run([sys.executable, "score_benchmark_v2.py"], cwd=BENCH,
                        capture_output=True, text=True, encoding="utf-8")
    run = {"run": i, "returncode": r.returncode, "stdout_tail": r.stdout.strip().splitlines()[-3:] if r.stdout else [],
           "hashes": {}}
    for fn in TARGETS:
        run["hashes"][fn] = sha256(os.path.join(BENCH, fn))
    result["runs"].append(run)
    print(f"run{i} rc={r.returncode}")
    for fn in TARGETS:
        print(f"  {fn}: {run['hashes'][fn]}")

# 一致性判定
consistent = True
for fn in TARGETS:
    hashes = [run["hashes"][fn] for run in result["runs"]]
    same_three = len(set(hashes)) == 1
    same_backup = hashes[0] == result["backup_hashes"][fn]
    result.setdefault("checks", {})[fn] = {
        "three_runs_pairwise_consistent": same_three,
        "equals_backup": same_backup}
    print(f"CHECK {fn}: 三连跑两两一致={same_three}, 与备份一致={same_backup}")
    if not (same_three and same_backup):
        consistent = False
result["all_consistent"] = consistent
print("ALL_CONSISTENT =", consistent)

with open(os.path.join(OUT, "sha256_基线记录.json"), "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
