#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""後続段 3 driver: write_set 被覆 assert の auditor-live 機械 gate (D38)。

writePhase の #if TRACE 被覆 assert (izanagi-trace 028f34d) が「歯を持つ」ことを
positive control で機械実証する。段 2 の p3_s4_red と対称 — あちらは「coder の赤 →
構造化 → critic が読む」まで、こちらは「lock 欠落 → 被覆 assert が赤 (verifier は
競合を踏まないと見逃す) → indeterminate に反映」まで。

3 変異を実ビルド実走 (broken build は buildcache 非経由 = allowlist が正しく拒否する
ため、s2_verify_calibration._broken_build_and_verify と同作法の fresh TMPDIR build):
  1. stock control (no patch)     → X==0, verdict=serializable/certified (assert が
     正しいコードで沈黙 = 非恒真の基底)。
  2. lockskip (獲得欠落)          → 単一スレッドで total_cycles==0 (verifier は certify
     するはず) なのに X>=1 (両 reason) → verdict=indeterminate。**characterization =
     同一 run で cycles==0 かつ X>=1** = assert が verifier の構造的死角を決定的に検出。
  3. early-unlock (保持破れ)       → X>=1 だが lock-lost-before-write のみ (入口検査は
     通り保持検査が捕らえる) → 2 検査点が別々に歯を持つ実証。

**段 3 ablation 点 (D38): 被覆 assert の on/off が lockskip 検出力に与える差** —
assert 有 = X 行検出 / assert 無 = verifier 単独では total_cycles==0 で見逃す。
これを単一 run 内 (cycles==0 かつ X>=1) で機械判定する (裁定 9)。

裸マクロ (IZANAGI_BREAK_*) は CCBENCH_ 名前空間外ゆえ pipeline からは定義不能 = この
driver + 手動 -D でのみビルド。PIN = pin.CURRENT_PIN (値の正本は pin.py、write_set 被覆 assert 込み)。
実行は直列 (単一テナント確認済み前提)。fitness は測らない (正しさ検証のみ)。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import buildcache, pin, site_policy, source_digest       # noqa: E402
from .build_admission import (GeneratorId, build_run_context,  # noqa: E402
                                      derive_build_admission)
from .layout import repo_output_root                           # noqa: E402
from .model import Genome                                      # noqa: E402
from .p2_2 import _assert_single_tenant                        # noqa: E402
from .patchharness import applied, assert_pinned_clean         # noqa: E402
from .materializer_admission import non_admissible_materializer  # noqa: E402


PIN = pin.CURRENT_PIN                    # izanagi-trace, 被覆 assert 込み (値の正本は pin.CURRENT_PIN)
ENV_TAG = "linux-baremetal"
CLK = 2100
RUN_TIMEOUT_S = 120.0
VERIFIER_TIMEOUT_S = 300.0

_BASE = {"BACK_OFF": 1, "NO_WAIT_LOCKING_IN_VALIDATION": 1,
         "NO_WAIT_OF_TICTOC": 0, "WAL": 0}
STOCK_G = Genome("silo", _BASE)

LOCKSKIP_PATCH = "broken-silo-lockskip-validation.patch"
EARLY_UNLOCK_PATCH = "broken-silo-early-unlock-validation.patch"
LOCKSKIP_DEFINE = "IZANAGI_BREAK_LOCK_COVERAGE"
EARLY_UNLOCK_DEFINE = "IZANAGI_BREAK_EARLY_UNLOCK"

# 単一スレッド = 並行性なし = cycle 構造的に不可能 → verifier certify 側を固定し、
# 被覆 assert だけが赤にできる characterization を決定的にする (裁定 9)。
SINGLE_FLAGS = {"ycsb_tuple_num": "200", "ycsb_zipf_skew": "0.9",
                "ycsb_rratio": "50", "ycsb_rmw": "true", "ycsb_max_ope": "5",
                "thread_num": "1", "extime": "1"}
# 高競合 4 スレッド: assert が contention 下でも発火する補助実証 (cycles も出うる)。
HIGH_FLAGS = {**SINGLE_FLAGS, "thread_num": "4"}


def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _run_trace(binary: str, flags: dict) -> str:
    """trace-enabled binary を 1 run し trace_dir を返す (呼び手が verify 後に清掃)。"""
    tdir = tempfile.mkdtemp(prefix="izanagi_s3_trace_")
    os.makedirs(os.path.join(tdir, "log"), exist_ok=True)
    args = [binary] + [f"-{k}={v}" for k, v in flags.items()] \
        + [f"-clocks_per_us={CLK}"]
    env = dict(os.environ, IZANAGI_TRACE_DIR=tdir)
    proc = subprocess.run(args, env=env, capture_output=True, text=True,
                          timeout=RUN_TIMEOUT_S, cwd=tdir)
    if proc.returncode != 0:
        shutil.rmtree(tdir, ignore_errors=True)
        raise RuntimeError(f"run rc={proc.returncode}: {proc.stderr.strip()[-300:]}")
    return tdir


def _count_x_reasons(trace_dir: str) -> dict:
    """trace の X 行を reason 別に数える (verifier は総数のみ返すため driver 側で)。"""
    reasons: dict = {}
    for f in os.listdir(trace_dir):
        if not (f.startswith("trace_") and f.endswith(".log")):
            continue
        with open(os.path.join(trace_dir, f), errors="replace") as fh:
            for line in fh:
                if line.startswith("X "):
                    parts = line.split()
                    if len(parts) >= 4:
                        reasons[parts[3]] = reasons.get(parts[3], 0) + 1
    return reasons


def _verify(trace_dir: str) -> dict:
    """verifier を別プロセスで実走し lock_coverage_violations 込みで構造化して返す。"""
    cmd = [sys.executable, "-m", "verifier", trace_dir, "--json", "--quiet"]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          timeout=VERIFIER_TIMEOUT_S,
                          cwd=os.path.join(_repo_root(), "orchestrator"))
    try:
        r = json.loads(proc.stdout)["results"][0]
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        raise RuntimeError(f"verifier 出力のパース不能 (rc={proc.returncode}): "
                           f"{proc.stdout[:200]} / {proc.stderr[-200:]}") from e
    return {
        "exit_code": proc.returncode,
        "verdict": r["verdict"], "certified": r["certified"],
        "total_cycles": r["total_cycles"],
        "lock_coverage_violations": r["integrity"]["lock_coverage_violations"],
        "txns": r["stats"]["txns"],
    }


def _run_cmake_build(cmd: list[str], *, site=None) -> None:
    resolved_site = site_policy.current_site() if site is None else site
    if site_policy.refuses_heavy_work(resolved_site):
        raise buildcache.BuildError(
            site_policy.heavy_work_refusal(resolved_site, "cmake --build")
        )
    subprocess.run(
        cmd + ["-j", str(site_policy.default_build_jobs(resolved_site))],
        check=True, capture_output=True, text=True,
    )


def _build_broken(
        patch_name: str, define: str, bdir: str, *, site=None,
) -> str:
    """broken patch を applied() 下で fresh build し binary パスを返す (buildcache 非経由)。"""
    root = _repo_root()
    sub = os.path.join(root, "external", "ccbench")
    patch = os.path.join(root, "patches", patch_name)
    with applied(patch, PIN, sub):
        defines = STOCK_G.cmake_defines() + [
            "-DCCBENCH_TRACE=1", f"-DCMAKE_CXX_FLAGS=-D{define}=1"]
        cfg = ["cmake", "-S", sub, "-B", bdir, "-DCMAKE_BUILD_TYPE=Release",
               "-DENABLE_SANITIZER=OFF",
               f"-DCMAKE_C_COMPILER={buildcache.DEFAULT_CC}",
               f"-DCMAKE_CXX_COMPILER={buildcache.DEFAULT_CXX}"] + defines
        resolved_site = site_policy.current_site() if site is None else site
        if site_policy.refuses_heavy_work(resolved_site):
            raise buildcache.BuildError(
                site_policy.heavy_work_refusal(
                    resolved_site, "cmake configure/build"
                )
            )
        subprocess.run(cfg, check=True, capture_output=True, text=True)
        _run_cmake_build(
            ["cmake", "--build", bdir, "--target", "ycsb_silo.exe"],
            site=resolved_site,
        )
    return os.path.join(bdir, "cc", "silo", "ycsb_silo.exe")


def _variant_run(binary: str, flags: dict, label: str) -> dict:
    tdir = _run_trace(binary, flags)
    try:
        v = _verify(tdir)
        v["x_reasons"] = _count_x_reasons(tdir)
    finally:
        shutil.rmtree(tdir, ignore_errors=True)
    print(f"  [{label}] verdict={v['verdict']} cycles={v['total_cycles']} "
          f"lcv={v['lock_coverage_violations']} reasons={v['x_reasons']}")
    return v


def main() -> int:
    _assert_single_tenant()
    root = _repo_root()
    sub = os.path.join(root, "external", "ccbench")
    assert_pinned_clean(sub, PIN)

    result = {"env_tag": ENV_TAG, "ccbench_commit": PIN,
              "genome": STOCK_G.canonical(), "clocks_per_us": CLK,
              "diagnostic_build_admission": non_admissible_materializer(
                  "orchestrator.campaign.s3_lock_coverage._build_broken"),
              "runs": {}}

    # --- 1. stock control (no patch): assert は正しいコードで沈黙するはず ---
    print("== stock control (no patch, TRACE=1) ==")
    build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    evidence = source_digest.resolve_evidence(STOCK_G, PIN)
    bstock = buildcache.build(
        STOCK_G, PIN, trace=True,
        admission=derive_build_admission(build_context, evidence),
        build_context=build_context, source_evidence=evidence,
    )
    result["runs"]["stock_single"] = _variant_run(bstock.binary, SINGLE_FLAGS,
                                                   "stock/single")

    # --- 2. lockskip (獲得欠落): characterization = 単一スレッドで cycles==0 かつ X>=1 ---
    print("== lockskip (IZANAGI_BREAK_LOCK_COVERAGE, TRACE=1) ==")
    bdir_ls = tempfile.mkdtemp(prefix="izanagi_s3_lockskip_")
    try:
        bin_ls = _build_broken(LOCKSKIP_PATCH, LOCKSKIP_DEFINE, bdir_ls)
        result["runs"]["lockskip_single"] = _variant_run(bin_ls, SINGLE_FLAGS,
                                                          "lockskip/single")
        result["runs"]["lockskip_high"] = _variant_run(bin_ls, HIGH_FLAGS,
                                                        "lockskip/high")
    finally:
        shutil.rmtree(bdir_ls, ignore_errors=True)

    # --- 3. early-unlock (保持破れ): lock-lost-before-write のみ ---
    print("== early-unlock (IZANAGI_BREAK_EARLY_UNLOCK, TRACE=1) ==")
    bdir_eu = tempfile.mkdtemp(prefix="izanagi_s3_earlyunlock_")
    try:
        bin_eu = _build_broken(EARLY_UNLOCK_PATCH, EARLY_UNLOCK_DEFINE, bdir_eu)
        result["runs"]["early_unlock_single"] = _variant_run(bin_eu, SINGLE_FLAGS,
                                                             "early-unlock/single")
    finally:
        shutil.rmtree(bdir_eu, ignore_errors=True)

    # --- 機械判定 (auditor-live gate の点 2/3、宣言でなくレコード) ---
    st = result["runs"]["stock_single"]
    ls = result["runs"]["lockskip_single"]
    lh = result["runs"]["lockskip_high"]
    eu = result["runs"]["early_unlock_single"]
    checks = {
        # 点: assert は正しいコードで沈黙 (非恒真の基底)
        "stock_silent_certified": (st["lock_coverage_violations"] == 0
                                   and st["verdict"] == "serializable"
                                   and st["certified"]),
        # 点: characterization — 単一 run で cycles==0 (verifier certify) かつ X>=1
        "lockskip_characterization": (ls["total_cycles"] == 0
                                      and ls["lock_coverage_violations"] > 0
                                      and ls["verdict"] == "indeterminate"),
        # 点: lockskip は両検査点を発火 (獲得欠落 = 入口 + 保持)
        "lockskip_both_reasons": ("not-locked-at-entry" in ls["x_reasons"]
                                  and "lock-lost-before-write" in ls["x_reasons"]),
        # 点: 高競合でも assert 発火 (cycles も出る = verifier と相補)
        "lockskip_high_fires": lh["lock_coverage_violations"] > 0,
        # 点: early-unlock は保持破れのみ (入口検査は通る = 2 検査点が別々に歯を持つ)
        "early_unlock_retention_only": (
            eu["lock_coverage_violations"] > 0
            and eu["total_cycles"] == 0
            and eu["verdict"] == "indeterminate"
            and list(eu["x_reasons"].keys()) == ["lock-lost-before-write"]),
    }
    result["checks"] = checks
    all_pass = all(checks.values())
    result["all_pass"] = all_pass

    outdir = os.path.join(repo_output_root(), "env", ENV_TAG, "calibration")
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, "s3_lock_coverage.json")
    with open(outpath, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)

    print("\n== checks ==")
    for k, v in checks.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print(f"all_pass={all_pass}  -> {outpath}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
