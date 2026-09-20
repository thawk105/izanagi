#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""段 8a 段階 C driver: trigger-gating 骨格の要因記録 positive control (D48 必須条件 3)。

silo-backoff-trigger-gating 軸の骨格 (要因 enum + thread_local + 7 store + sentinel
リセット + gate) が導入する新たな検証可能主張 = **記録の正確性** に歯があることを機械
実証する。trace schema は abort 要因を持たない (シートの verifier 死角欄) ため、誤記録
された要因で発火する gate は定数縮退 gate と区別不能になる — その死角を、検証専用の
計装 patch (A 行 tally) + 構造ゼロ検査で閉じ、misattribution mutation が赤になることを
実走証明する (AUD-4)。s3_lock_coverage.py / s5_permutation_coverage.py と対称の様式。

**計装が別 patch である理由 (規律1 と一次防壁の整合):** A 行 emit を骨格 (template
patch) に入れると variant の TRACE=1/TRACE=0 preprocess 差分が pinned HEAD のそれと
食い違い、assert_trace_diff_matches_head (diff-of-diffs) が全ループ評価で fails-closed
になる。PIN 前進は D48 決定 2 で却下済み。よって計装は本 driver の characterization
run でのみ骨格の上に重ねる。**この分離が偽陰性を生まない根拠:** 骨格の store は coder
不可触 (DiffQuarantine が hole 外改変を行単位で機械拒否) なので、ここで一度証明した
記録正確性はループ中も構造的に不変 — 常設監視は不要 (D48 決定 3 の執行主体内訳)。

検査の設計 (シート positive control 欄の実装):
  1. skeleton_multi (骨格+計装, t4): 骨格は stock 等価 (hole 初期値 true) で
     certified。**保存則** (A 行総数 == stdout abort_counts_) と **構造ゼロ**
     (YCSB update/read-only では node-vali / insert-node / scan-node /
     update-absent / unset の要因は構造的に発生不能 == 0、かつ early_aborts == 0)
     を確認。abort > 0 を前提検査に含める (競合が出ていない run での空虚な緑を
     fails-closed に拒否)。
  2. skeleton_single (骨格+計装, t1): 単一スレッド = 競合なし → abort == 0 かつ
     A 行 == 0 (決定的 characterization の基底、s3/s5 裁定 9 と同型)。
  3. misattr_multi (+ broken patch, IZANAGI_BREAK_TRIGGER_MISATTR): 施錠競合を
     kNodeVali に故意誤記録。**verifier は緑のまま** (serializability 無傷 = 死角の
     実走証明) だが、構造ゼロ検査が node-vali > 0 で赤 → 検査に歯がある。保存則は
     misattr でも破れない (合計不変) ことも確認 = 保存則だけでは捕まらない証明。

裸マクロ (IZANAGI_BREAK_TRIGGER_MISATTR) は CCBENCH_ 名前空間外ゆえ pipeline からは
定義不能 = この driver + 手動 -D でのみビルド可能 (壊した CC を baseline に混ぜない、
規律2)。PIN = pin.CURRENT_PIN。実行は直列 (単一テナント確認)。fitness は測らない
(正しさ検証のみ — 性能数値を一切出力しない)。
"""
from __future__ import annotations

import json
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import (buildcache, condition_meaning_gate, site_policy, # noqa: E402
               source_digest)
from .build_admission import (GeneratorId, attest_generator_output,  # noqa: E402
                                      build_run_context, derive_build_admission,
                                      require_build_admission)
from .axis_trigger_gating import (                             # noqa: E402
    INSTR_PATCH, MISATTR_DEFINE, MISATTR_PATCH, PIN, TEMPLATE_PATCH, _BASE)
from .layout import repo_output_root                           # noqa: E402
from .model import Genome                                      # noqa: E402
from .p2_2 import _assert_single_tenant                        # noqa: E402
from .patchharness import applied, apply_patch, assert_pinned_clean  # noqa: E402


ENV_TAG = "linux-baremetal"
CLK = 2100
RUN_TIMEOUT_S = 120.0
VERIFIER_TIMEOUT_S = 300.0

SKELETON_PATCH = TEMPLATE_PATCH          # 軸定数の正本 = axis_trigger_gating (D48 条件 5)

# 骨格が生きた状態 (BACKOFF_TRIGGER_GATING=1、hole は stock 等価の初期値) で記録の
# 正確性を測る。ADD_ANALYSIS=1 は early_aborts 整合検査のため (カウンタのみ、挙動不変)。
GENOME = Genome("silo", dict(_BASE, ADD_ANALYSIS=1))

# t4 = 競合を出す最小規模 (broken-silo-norw の実証と同系の高競合設定)。
# 数値は正しさ検証の動作点であって性能計測ではない (規律4 の対象外)。
MULTI_FLAGS = {"ycsb_tuple_num": "200", "ycsb_zipf_skew": "0.9",
               "ycsb_rratio": "50", "ycsb_rmw": "true", "ycsb_max_ope": "5",
               "thread_num": "4", "extime": "1"}
SINGLE_FLAGS = dict(MULTI_FLAGS, thread_num="1")

# YCSB (update/read のみ、insert/scan/delete なし) で構造的に発生不能な要因 +
# 未記録 sentinel。ここが非ゼロ = 誤記録 (misattribution) の露出点。
STRUCTURALLY_ZERO = ("unset", "update-absent", "node-vali", "insert-node",
                     "scan-node")

_ABORT_RE = re.compile(r"^abort_counts_:\s*(\d+)", re.MULTILINE)
_EARLY_RE = re.compile(r"early_aborts.*?(\d+)")


def _repo_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _require_condition_gate(
    source_root: str,
    *,
    driver_id: str,
    macro: str,
    configure_args: list[str],
) -> dict:
    captured = condition_meaning_gate.capture_define_inputs(
        source_root, configure_args=tuple(configure_args),
    )
    request = condition_meaning_gate.make_define_request(
        driver_id=driver_id,
        macro=macro,
        requested_value=1,
        default_value=None if macro == MISATTR_DEFINE else 0,
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


def _preflight_condition_gates(
    root: str,
    sub: str,
    *,
    driver_id: str,
    include_misattr: bool,
    genome: Genome | None = None,
) -> list[dict]:
    patches = os.path.join(root, "patches")
    configure_args = (genome or GENOME).cmake_defines() + ["-DCCBENCH_TRACE=1"]
    records = []
    with applied(os.path.join(patches, SKELETON_PATCH), PIN, sub):
        apply_patch(os.path.join(patches, INSTR_PATCH), sub)
        records.append(_require_condition_gate(
            sub,
            driver_id=driver_id,
            macro="BACKOFF_TRIGGER_GATING",
            configure_args=configure_args,
        ))
    if include_misattr:
        with applied(os.path.join(patches, SKELETON_PATCH), PIN, sub):
            apply_patch(os.path.join(patches, INSTR_PATCH), sub)
            apply_patch(os.path.join(patches, MISATTR_PATCH), sub)
            records.append(_require_condition_gate(
                sub,
                driver_id=driver_id,
                macro=MISATTR_DEFINE,
                configure_args=configure_args,
            ))
    return records


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


def _build(
        bdir: str, extra_cxx_define: str = "", genome: Genome = None, *,
        site=None, admission_receipts: list[dict] | None = None,
        condition_driver_id: str = "orchestrator.campaign.s8a_trigger_coverage",
) -> str:
    """working-tree (patch 適用済み) を TRACE=1 で fresh build し binary パスを返す。

    genome は明示引数 (省略時は本モジュールの GENOME)。s8a_trigger_freq.py が import
    再利用するため、呼び出し側の genome でビルドし「JSON の genome 欄 ≠ 実ビルド」の
    無警告ドリフトを塞ぐ (実装レビュー 2026-07-11 F1)。patched source と generator
    input を registered S8A receipt に束縛し、検証後の canonical admission を呼出側へ返す。"""
    sub = os.path.join(_repo_root(), "external", "ccbench")
    defines = (genome or GENOME).cmake_defines() + ["-DCCBENCH_TRACE=1"]
    if extra_cxx_define:
        defines.append(f"-DCMAKE_CXX_FLAGS=-D{extra_cxx_define}=1")
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
    _require_condition_gate(
        sub,
        driver_id=condition_driver_id,
        macro="BACKOFF_TRIGGER_GATING",
        configure_args=defines,
    )
    if extra_cxx_define:
        _require_condition_gate(
            sub,
            driver_id=condition_driver_id,
            macro=extra_cxx_define,
            configure_args=[
                argument for argument in defines
                if not argument.startswith("-DCMAKE_CXX_FLAGS=")
            ],
        )
    evidence = source_digest.resolve_evidence(
        genome or GENOME, PIN, ccbench_dir=sub,
    )
    build_context = build_run_context(
        generator_id=GeneratorId.S8A_TRIGGER_SWEEP,
    )
    generator_input = {
        "schema": "s8a-trigger-characterization-input/v1",
        "genome": (genome or GENOME).canonical(),
        "trace": True,
        "extra_cxx_define": extra_cxx_define,
    }
    input_sha256 = hashlib.sha256(json.dumps(
        generator_input, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")).hexdigest()
    capability = attest_generator_output(
        build_context, evidence, generator_input_sha256=input_sha256,
    )
    admission = derive_build_admission(
        build_context, evidence, generator_receipt=capability,
    )
    require_build_admission(
        admission, expected_policy=build_context.policy, expected_source=evidence,
    )
    if admission_receipts is not None:
        admission_receipts.append(admission.as_wal_receipt())
    subprocess.run(cfg, check=True, capture_output=True, text=True)
    _run_cmake_build(
        ["cmake", "--build", bdir, "--target", "ycsb_silo.exe"],
        site=resolved_site,
    )
    return os.path.join(bdir, "cc", "silo", "ycsb_silo.exe")


def _run_trace(binary: str, flags: dict) -> tuple:
    """trace-enabled binary を 1 run し (trace_dir, stdout) を返す。"""
    tdir = tempfile.mkdtemp(prefix="izanagi_s8a_trace_")
    os.makedirs(os.path.join(tdir, "log"), exist_ok=True)
    args = [binary] + [f"-{k}={v}" for k, v in flags.items()] \
        + [f"-clocks_per_us={CLK}"]
    env = dict(os.environ, IZANAGI_TRACE_DIR=tdir)
    proc = subprocess.run(args, env=env, capture_output=True, text=True,
                          timeout=RUN_TIMEOUT_S, cwd=tdir)
    if proc.returncode != 0:
        shutil.rmtree(tdir, ignore_errors=True)
        raise RuntimeError(f"run rc={proc.returncode}: {proc.stderr.strip()[-300:]}")
    return tdir, proc.stdout


def _parse_abort_counts(stdout: str) -> int:
    m = _ABORT_RE.search(stdout)
    if not m:
        raise RuntimeError("stdout に abort_counts_ が無い — 整合検査の分母を確定"
                           "できず fails-closed (result.cc の出力形式変更を疑え)")
    return int(m.group(1))


def _parse_early_aborts(stdout: str) -> int:
    """early_aborts 行 (ADD_ANALYSIS 時のみ、非ゼロのときだけ表示) — 無ければ 0。"""
    for line in stdout.splitlines():
        if "early_aborts" in line:
            m = _EARLY_RE.search(line)
            if m:
                return int(m.group(1))
    return 0


def _verify(trace_dir: str) -> dict:
    """verifier を別プロセスで実走し abort_reasons (A 行集計) 込みで返す。"""
    cmd = [
        sys.executable, "-m", "verifier", trace_dir, "--json", "--quiet",
        "--protocol", "silo", "--ccbench-root",
        os.path.join(_repo_root(), "external", "ccbench"),
    ]
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
        "abort_reasons": r["stats"]["abort_reasons"],
        "txns": r["stats"]["txns"],
    }


def _one_run(binary: str, flags: dict, label: str) -> dict:
    tdir, stdout = _run_trace(binary, flags)
    try:
        v = _verify(tdir)
    finally:
        shutil.rmtree(tdir, ignore_errors=True)
    v["abort_counts"] = _parse_abort_counts(stdout)
    v["early_aborts"] = _parse_early_aborts(stdout)
    v["a_total"] = sum(v["abort_reasons"].values())
    print(f"  [{label}] verdict={v['verdict']} aborts={v['abort_counts']} "
          f"A={v['a_total']} reasons={v['abort_reasons']}")
    return v


def _structural_zero_ok(reasons: dict) -> bool:
    return all(reasons.get(k, 0) == 0 for k in STRUCTURALLY_ZERO)


def main() -> int:
    _assert_single_tenant()
    root = _repo_root()
    sub = os.path.join(root, "external", "ccbench")
    assert_pinned_clean(sub, PIN)
    patches = os.path.join(root, "patches")
    condition_gates = _preflight_condition_gates(
        root,
        sub,
        driver_id="orchestrator.campaign.s8a_trigger_coverage",
        include_misattr=True,
    )

    result = {"env_tag": ENV_TAG, "ccbench_commit": PIN,
              "genome": GENOME.canonical(), "clocks_per_us": CLK,
              "condition_gates": condition_gates,
              "build_admissions": [],
              "runs": {}}

    bdir_sk = tempfile.mkdtemp(prefix="izanagi_s8a_sk_")
    bdir_mi = tempfile.mkdtemp(prefix="izanagi_s8a_mi_")
    try:
        # applied() は骨格のみ管理。計装/misattr は body 内で重ね当て — exit の
        # revert_worktree (git checkout -- .) が 3 枚まとめて戻す (新規ファイルなし)。
        with applied(os.path.join(patches, SKELETON_PATCH), PIN, sub):
            apply_patch(os.path.join(patches, INSTR_PATCH), sub)
            print("== build skeleton+instr (TRACE=1) ==")
            bin_sk = _build(
                bdir_sk, admission_receipts=result["build_admissions"],
            )
            apply_patch(os.path.join(patches, MISATTR_PATCH), sub)
            print(f"== build +misattr (-D{MISATTR_DEFINE}=1) ==")
            bin_mi = _build(
                bdir_mi, MISATTR_DEFINE,
                admission_receipts=result["build_admissions"],
            )

            print("== skeleton multi-thread (t4) ==")
            result["runs"]["skeleton_multi"] = _one_run(bin_sk, MULTI_FLAGS,
                                                        "skeleton/t4")
            print("== skeleton single-thread (t1) ==")
            result["runs"]["skeleton_single"] = _one_run(bin_sk, SINGLE_FLAGS,
                                                         "skeleton/t1")
            print("== misattr multi-thread (t4) ==")
            result["runs"]["misattr_multi"] = _one_run(bin_mi, MULTI_FLAGS,
                                                       "misattr/t4")
    finally:
        shutil.rmtree(bdir_sk, ignore_errors=True)
        shutil.rmtree(bdir_mi, ignore_errors=True)
    assert_pinned_clean(sub, PIN)

    sk = result["runs"]["skeleton_multi"]
    sg = result["runs"]["skeleton_single"]
    mi = result["runs"]["misattr_multi"]
    checks = {
        # 骨格 (hole 初期値 = stock 等価) は certified — gate が正しさに不干渉の基底
        "skeleton_certified": sk["certified"] and sk["verdict"] == "serializable",
        # 前提: 競合が実在 (abort が出ない run での空虚な緑を拒否、fails-closed)
        "skeleton_aborts_present": sk["abort_counts"] > 0,
        # 保存則: A 行総数 == abort 総数 (記録が全 abort を漏れなく覆う)
        "skeleton_conservation": sk["a_total"] == sk["abort_counts"],
        # 構造ゼロ: YCSB で発生不能な要因 + sentinel 未記録 == 0 (誤記録なし)
        "skeleton_structural_zero": _structural_zero_ok(sk["abort_reasons"]),
        # YCSB の早期 abort は構造的にゼロ (read/update は abort をセットしない)
        "skeleton_no_early_aborts": sk["early_aborts"] == 0,
        # 実際に発生する要因 (施錠競合 / read-vali) が記録されている
        "skeleton_live_reasons_present": (
            sk["abort_reasons"].get("lock-conflict", 0)
            + sk["abort_reasons"].get("readvali-tid", 0)
            + sk["abort_reasons"].get("readvali-locked", 0) > 0),
        # 単一スレッド = 競合なし → abort 0 / A 行 0 (決定的基底)
        "single_no_aborts": (sg["abort_counts"] == 0 and sg["a_total"] == 0
                             and sg["certified"]),
        # misattr: verifier は緑のまま (= trace schema の死角の実走証明)
        "misattr_verifier_blind": mi["certified"] and mi["total_cycles"] == 0,
        # misattr: 構造ゼロ検査だけが赤にできる (node-vali へ誤記録が露出 = 歯)
        "misattr_exposed_by_structural_zero": (
            mi["abort_reasons"].get("node-vali", 0) > 0
            and not _structural_zero_ok(mi["abort_reasons"])),
        # misattr: 誤記録は完全な付け替え (lock-conflict が消える)
        "misattr_lock_conflict_gone": mi["abort_reasons"].get("lock-conflict", 0) == 0,
        # misattr でも保存則は破れない = 保存則だけでは捕まらないことの機械証明
        "misattr_conservation_still_holds": mi["a_total"] == mi["abort_counts"],
    }
    result["checks"] = checks
    all_pass = all(checks.values())
    result["all_pass"] = all_pass

    outdir = os.path.join(repo_output_root(), "env", ENV_TAG, "calibration")
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, "s8a_trigger_gating_coverage.json")
    with open(outpath, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)

    print("\n== checks ==")
    for k, v in checks.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print(f"all_pass={all_pass}  -> {outpath}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
