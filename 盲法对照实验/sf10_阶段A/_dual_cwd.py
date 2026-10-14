# -*- coding: utf-8 -*-
"""SF10 阶段A：双 cwd 验证"""
import hashlib, json, os, subprocess, sys

BENCH = r"D:\projectAGI\nhx\盲法对照实验\benchmark_v2"
OUT = r"D:\projectAGI\nhx\盲法对照实验\sf10_阶段A"
SCORE_FILES = ["判分明细v2.csv", "判分汇总v2.json", "审计日志v2.json"]
BASELINE = {  # 来自 sha256_基线记录.json
    "判分明细v2.csv": "9aceb9971cb950905d4cc1a9ede3d5c3cc77bfe327fc0f728318c6a43b6ee882",
    "判分汇总v2.json": "da91f5d16e0f620defcd63b06d14605aa132830fdd81a05192d00284bbd9f1eb",
    "审计日志v2.json": "506a2e8aaea8d1c40a78a6deae13d8c30e250a8db8963e94eb0c9ec4444e4bbc",
}

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

log = []
for cwd in [r"D:\projectAGI\nhx", r"C:\Users\JM.RADE"]:
    cmd = [sys.executable, r"D:\projectAGI\nhx\盲法对照实验\benchmark_v2\score_benchmark_v2.py"]
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    entry = {"cwd": cwd, "command": " ".join(cmd), "returncode": r.returncode, "hashes": {}}
    ok = True
    for fn in SCORE_FILES:
        p = os.path.join(BENCH, fn)
        h = sha256(p)
        entry["hashes"][fn] = h
        if h != BASELINE[fn]:
            ok = False
    entry["output_in_benchmark_v2"] = all(os.path.exists(os.path.join(BENCH, fn)) for fn in SCORE_FILES)
    entry["hashes_equal_baseline"] = ok
    log.append(entry)
    print(f"cwd={cwd} rc={r.returncode} 输出在benchmark_v2={entry['output_in_benchmark_v2']} 哈希=基线={ok}")
    for fn in SCORE_FILES:
        print(f"   {fn}: {entry['hashes'][fn][:16]}...  base={BASELINE[fn][:16]}...")

with open(os.path.join(OUT, "双cwd验证日志.json"), "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=2)
print("ALL_OK =", all(e["hashes_equal_baseline"] and e["output_in_benchmark_v2"] for e in log))
