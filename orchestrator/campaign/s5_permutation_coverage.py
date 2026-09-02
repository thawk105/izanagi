#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""段 5 driver: write_set permutation-preservation assert の機械 gate (D41 決定2)。

validationPhase の #if TRACE assert (izanagi-trace 511c953) が「歯を持つ」ことを
positive control で機械実証する。s3_lock_coverage.py (D38, lock 被覆 assert) と
対称の様式 — こちらは sort が write_set_ の要素を欠落/複製させていないかを検査する。

D41 の新規死角1 (非 strict-weak-order comparator の std::sort UB) は「comparator に
関わらず常に通る恒真化した保証」であってはならない、という要求への一次防壁。実際に
要素を erase/複製する broken 変異を当てて赤になることを実証する:
  1. stock control (no patch)              → P==0, verdict=serializable/certified
     (assert が正しい sort で沈黙 = 非恒真の基底)。
  2. erase (要素 1 個を pop_back)           → 単一スレッドで total_cycles==0 なのに
     P>=1 (size-changed) → verdict=indeterminate。characterization = 同一 run で
     cycles==0 かつ P>=1。
  3. swap (要素数不変・rcdptr_ のみ入替)     → P>=1 だが rcdptr-set-changed のみ
     (size は不変) → 2 検査点 (size / rcdptr multiset) が別々に歯を持つ実証。

裸マクロ (IZANAGI_BREAK_PERMUTATION*) は CCBENCH_ 名前空間外ゆえ pipeline からは
定義不能 = この driver + 手動 -D でのみビルド (s3_lock_coverage.py と同じ理由)。
PIN = pin.CURRENT_PIN (511c953、permutation 保存 assert 込み)。実行は直列 (単一
テナント確認済み前提)。fitness は測らない (正しさ検証のみ)。
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

from . import (buildcache, condition_meaning_gate, pin,        # noqa: E402
               site_policy, source_digest)
from .build_admission import (GeneratorId, build_run_context,  # noqa: E402
                                      derive_build_admission)
from .layout import repo_output_root                           # noqa: E402
from .model import Genome                                      # noqa: E402
from .p2_2 import _assert_single_tenant                        # noqa: E402
from .patchharness import applied, assert_pinned_clean         # noqa: E402
from .materializer_admission import non_admissible_materializer  # noqa: E402


PIN = pin.CURRENT_PIN                    # 511c953 (izanagi-trace, permutation 保存 assert 込み)
ENV_TAG = "linux-baremetal"
CLK = 2100
RUN_TIMEOUT_S = 120.0
VERIFIER_TIMEOUT_S = 300.0

_BASE = {"BACK_OFF": 1, "NO_WAIT_LOCKING_IN_VALIDATION": 1,
         "NO_WAIT_OF_TICTOC": 0, "WAL": 0}
STOCK_G = Genome("silo", _BASE)

ERASE_PATCH = "broken-silo-permutation-erase.patch"
SWAP_PATCH = "broken-silo-permutation-swap.patch"
ERASE_DEFINE = "IZANAGI_BREAK_PERMUTATION"
SWAP_DEFINE = "IZANAGI_BREAK_PERMUTATION_SWAP"

# 単一スレッド = 並行性なし = cycle 構造的に不可能 → verifier certify 側を固定し、
# permutation 保存 assert だけが赤にできる characterization を決定的にする
# (s3_lock_coverage.py 裁定 9 と同型)。
SINGLE_FLAGS = {"ycsb_tuple_num": "200", "ycsb_zipf_skew": "0.9",
                "ycsb_rratio": "50", "ycsb_rmw": "true", "ycsb_max_ope": "5",
                "thread_num": "1", "extime": "1"}


def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _require_condition_gate(source_root: str, macro: str) -> dict:
    """Require the two independent condition records before any benchmark build."""
    captured = condition_meaning_gate.capture_define_inputs(
        source_root,
        configure_args=(*STOCK_G.cmake_defines(), "-DCCBENCH_TRACE=1"),
    )
    request = condition_meaning_gate.make_define_request(
        driver_id="orchestrator.campaign.s5_permutation_coverage",
        macro=macro,
        requested_value=1,
        default_value=0,
    )
    supply = condition_meaning_gate.evaluate_define_supply_effectuation(
        captured, request=request, cxx=buildcache.DEFAULT_CXX, cmake="cmake",
    )
    meaning = condition_meaning_gate.evaluate_define_runtime_meaning(
        captured, request=request,
        declaration=condition_meaning_gate.declare_define_runtime_meaning(request),
        cxx=buildcache.DEFAULT_CXX,
    )
    admission = condition_meaning_gate.require_condition_gate_family(
        [supply], [meaning], use_class="raw-measurement",
    )
    if not admission.admitted:
        raise RuntimeError(
            f"condition gate rejected {macro}: "
            f"supply={supply.terminal_status}/{supply.reason_code}, "
            f"meaning={meaning.terminal_status}/{meaning.reason_code}"
        )
    return {
        "supply": json.loads(supply.canonical_json()),
        "meaning": json.loads(meaning.canonical_json()),
        "admission": json.loads(admission.canonical_json()),
    }


def _preflight_condition_gates(root: str, sub: str) -> list[dict]:
    records = []
    for patch_name, macro in (
        (ERASE_PATCH, ERASE_DEFINE),
        (SWAP_PATCH, SWAP_DEFINE),
    ):
        with applied(os.path.join(root, "patches", patch_name), PIN, sub):
            records.append(_require_condition_gate(sub, macro))
    return records


def _run_trace(binary: str, flags: dict) -> str:
    """trace-enabled binary を 1 run し trace_dir を返す (呼び手が verify 後に清掃)。"""
    tdir = tempfile.mkdtemp(prefix="izanagi_s5_trace_")
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


def _count_p_reasons(trace_dir: str) -> dict:
    """trace の P 行を reason 別に数える独立 oracle。"""
    reasons: dict = {}
    for f in os.listdir(trace_dir):
        if not (f.startswith("trace_") and f.endswith(".log")):
            continue
        with open(os.path.join(trace_dir, f), errors="replace") as fh:
            for line in fh:
                if line.startswith("P "):
                    parts = line.split()
                    if len(parts) >= 2:
                        reasons[parts[1]] = reasons.get(parts[1], 0) + 1
    return reasons


def _oracle_cross_check(p_reasons: dict, details: dict) -> bool:
    """独立 raw oracle と verifier の構造化 counts を fail-closed で突き合わせる。"""
    try:
        if not isinstance(p_reasons, dict) or not isinstance(details, dict):
            return False
        counts = details["counts"]
        if not isinstance(counts, dict):
            return False
        if set(counts) != {"size-changed", "rcdptr-set-changed", "unknown"}:
            return False
        if any(
                not isinstance(value, int) or isinstance(value, bool) or value < 0
                for value in counts.values()
        ):
            return False
        if any(
                not isinstance(value, int) or isinstance(value, bool) or value < 0
                for value in p_reasons.values()
        ):
            return False
        return (
            p_reasons.get("size-changed", 0) == counts["size-changed"]
            and p_reasons.get("rcdptr-set-changed", 0)
            == counts["rcdptr-set-changed"]
            and sum(
                value for key, value in p_reasons.items()
                if key not in ("size-changed", "rcdptr-set-changed")
            ) == counts["unknown"]
        )
    except (KeyError, TypeError, ValueError):
        return False


def _verify(trace_dir: str) -> dict:
    """verifier を別プロセスで実走し permutation_violations 込みで構造化して返す。"""
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
        "permutation_violations": r["integrity"]["permutation_violations"],
        "permutation_violation_details": (
            r["integrity"]["permutation_violation_details"]
        ),
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
        _require_condition_gate(sub, define)
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
        v["p_reasons"] = _count_p_reasons(tdir)
        v["oracle_cross_check_matches"] = _oracle_cross_check(
            v["p_reasons"], v["permutation_violation_details"])
    finally:
        shutil.rmtree(tdir, ignore_errors=True)
    print(f"  [{label}] verdict={v['verdict']} cycles={v['total_cycles']} "
          f"pv={v['permutation_violations']} reasons={v['p_reasons']}")
    return v


def main() -> int:
    _assert_single_tenant()
    root = _repo_root()
    sub = os.path.join(root, "external", "ccbench")
    assert_pinned_clean(sub, PIN)
    condition_gates = _preflight_condition_gates(root, sub)

    result = {"env_tag": ENV_TAG, "ccbench_commit": PIN,
              "genome": STOCK_G.canonical(), "clocks_per_us": CLK,
              "condition_gates": condition_gates,
              "diagnostic_build_admission": non_admissible_materializer(
                  "orchestrator.campaign.s5_permutation_coverage._build_broken"),
              "runs": {}}

    # --- 1. stock control (no patch): assert は正しい sort で沈黙するはず ---
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

    # --- 2. erase (要素欠落): characterization = 単一スレッドで cycles==0 かつ P>=1 ---
    print("== erase (IZANAGI_BREAK_PERMUTATION, TRACE=1) ==")
    bdir_er = tempfile.mkdtemp(prefix="izanagi_s5_erase_")
    try:
        bin_er = _build_broken(ERASE_PATCH, ERASE_DEFINE, bdir_er)
        result["runs"]["erase_single"] = _variant_run(bin_er, SINGLE_FLAGS,
                                                        "erase/single")
    finally:
        shutil.rmtree(bdir_er, ignore_errors=True)

    # --- 3. swap (要素数不変・rcdptr_ のみ入替): rcdptr-set-changed のみ ---
    print("== swap (IZANAGI_BREAK_PERMUTATION_SWAP, TRACE=1) ==")
    bdir_sw = tempfile.mkdtemp(prefix="izanagi_s5_swap_")
    try:
        bin_sw = _build_broken(SWAP_PATCH, SWAP_DEFINE, bdir_sw)
        result["runs"]["swap_single"] = _variant_run(bin_sw, SINGLE_FLAGS,
                                                       "swap/single")
    finally:
        shutil.rmtree(bdir_sw, ignore_errors=True)

    # --- 機械判定 (D41 決定2 の実走確認、宣言でなくレコード) ---
    st = result["runs"]["stock_single"]
    er = result["runs"]["erase_single"]
    sw = result["runs"]["swap_single"]
    checks = {
        # 点: assert は正しい sort で沈黙 (非恒真の基底)
        "stock_silent_certified": (st["permutation_violations"] == 0
                                   and st["verdict"] == "serializable"
                                   and st["certified"]),
        # 点: characterization — 単一 run で cycles==0 (verifier certify) かつ P>=1
        "erase_characterization": (er["total_cycles"] == 0
                                   and er["permutation_violations"] > 0
                                   and er["verdict"] == "indeterminate"),
        # 点: erase は size-changed のみ発火 (要素数が実際に変わった)
        "erase_size_changed_only": (
            er["permutation_violation_details"]["counts"]["size-changed"] > 0
            and er["permutation_violation_details"]["counts"][
                "rcdptr-set-changed"] == 0
            and er["permutation_violation_details"]["counts"]["unknown"] == 0
        ),
        # 点: swap は要素数不変で cycles==0 かつ P>=1 (rcdptr multiset 検査が単独で歯を持つ)
        "swap_characterization": (sw["total_cycles"] == 0
                                  and sw["permutation_violations"] > 0
                                  and sw["verdict"] == "indeterminate"),
        # 点: swap は rcdptr-set-changed のみ発火 (size 検査は通る = 2 検査点が別々に歯を持つ)
        "swap_rcdptr_changed_only": (
            sw["permutation_violation_details"]["counts"]["rcdptr-set-changed"] > 0
            and sw["permutation_violation_details"]["counts"]["size-changed"] == 0
            and sw["permutation_violation_details"]["counts"]["unknown"] == 0
        ),
        "oracle_cross_check_stock": st["oracle_cross_check_matches"],
        "oracle_cross_check_erase": er["oracle_cross_check_matches"],
        "oracle_cross_check_swap": sw["oracle_cross_check_matches"],
    }
    result["checks"] = checks
    all_pass = all(checks.values())
    result["all_pass"] = all_pass

    outdir = os.path.join(repo_output_root(), "env", ENV_TAG, "calibration")
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, "s5_permutation_coverage.json")
    with open(outpath, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)

    print("\n== checks ==")
    for k, v in checks.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print(f"all_pass={all_pass}  -> {outpath}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
