#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""[T-139] 劣化梯子の生死 probe — correctness leg (使い捨て、DW-G01)。

candidate A (CAS 中央 gate) / B (writePhase 直列化) を patchharness.applied() 下で
trace build し、高競合 t4 run → verifier certified → per-worker liveness → nm 活性証明
を機械判定する。性能値は一切主張しない (login node、動作確認扱い)。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path.cwd()
assert (REPO / "orchestrator").is_dir(), "run from the repo (worktree) root"
sys.path.insert(0, str(REPO / "orchestrator"))
from campaign import patchharness, pin  # noqa: E402

WAVE = Path(os.environ["T139_WAVE_DIR"])
SUB = str(REPO / "external" / "ccbench")
PATCH = str(WAVE / "t139-probe-degradation.patch")
PREFIX = f"{WAVE}/gflags-install;{WAVE}/glog-install"
WORKLOAD = ["-ycsb_rmw=true", "-ycsb_zipf_skew=0.9", "-ycsb_tuple_num=50",
            "-ycsb_max_ope=5", "-thread_num=4", "-extime=1"]
CANDIDATES = {"A": "IZANAGI_T139_PROBE_CAS_GATE",
              "B": "IZANAGI_T139_PROBE_COMMIT_GATE"}


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"rc={r.returncode}: {cmd}\n{r.stdout[-800:]}\n{r.stderr[-800:]}")
    return r


def characterize(name: str, macro: str) -> dict:
    build = WAVE / f"build-trace-{name}"
    rundir = WAVE / f"run-{name}"
    rundir.mkdir()
    run(["cmake", "-S", SUB, "-B", str(build), "-DCMAKE_BUILD_TYPE=Release",
         "-DENABLE_SANITIZER=OFF", "-DCCBENCH_TRACE=1",
         f"-DCMAKE_PREFIX_PATH={PREFIX}", f"-DCMAKE_CXX_FLAGS=-D{macro}=1"])
    run(["cmake", "--build", str(build), "--target", "ycsb_silo.exe", "-j", "8"])
    exe = build / "cc" / "silo" / "ycsb_silo.exe"
    nm = subprocess.run(["nm", "-C", str(exe)], capture_output=True, text=True)
    macro_active = "izanagi_t139_probe" in nm.stdout
    run([str(exe), *WORKLOAD], cwd=str(rundir), timeout=300)
    traces = sorted(rundir.glob("trace_*.log"))
    per_worker = {t.name: sum(1 for line in t.open() if line.startswith("C "))
                  for t in traces}
    ver = subprocess.run([sys.executable, "-m", "orchestrator.verifier", str(rundir)],
                         capture_output=True, text=True, cwd=str(REPO), timeout=600)
    checks = {
        "macro_symbol_in_binary": macro_active,
        "trace_files_expected": len(traces) == 4,
        "per_worker_liveness": bool(per_worker) and all(v > 0 for v in per_worker.values()),
        "verifier_exit_zero": ver.returncode == 0,
        "verifier_certified": "serializable(certified)" in ver.stdout,
    }
    return {"candidate": name, "macro": macro, "checks": checks,
            "per_worker_commits": per_worker,
            "verifier_tail": ver.stdout.strip().splitlines()[-2:],
            "all_pass": all(checks.values())}


def main() -> int:
    patchharness.assert_pinned_clean(SUB, pin.CURRENT_PIN)
    results = []
    with patchharness.applied(PATCH, pin.CURRENT_PIN, SUB):
        for name, macro in CANDIDATES.items():
            results.append(characterize(name, macro))
    patchharness.assert_pinned_clean(SUB, pin.CURRENT_PIN)
    out = {
        "probe": "t139-ladder-correctness-leg",
        "pin": pin.CURRENT_PIN,
        "host_role": "pegasus-login-node (動作確認扱い、性能主張なし)",
        "workload": " ".join(WORKLOAD),
        "results": results,
        "revert_clean": True,
        "all_pass": all(r["all_pass"] for r in results),
    }
    (WAVE / "t139-probe-correctness.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({r["candidate"]: r["all_pass"] for r in results}))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
