# -*- coding: utf-8 -*-
"""S2 縮小 verify 構成の校正ドライバ (phase3.md 後続段 1、D36)。

S2 = 「certify workload と perf workload の乖離」リスク (phase2.md、insight
2026-06-22 follow-up [P1])。sort 等データパス分岐変異の前提として、perf 構成の
データパスを verify (trace-enabled) でも踏む縮小構成を **実測 gate で** 確定する。

構成の設計 (2026-07-06 敵対検証で確定):
- S2 構成 = perf 代表 workload (calibration_t48_skew0p9_rr50_rmw0) と**完全同一フラグ**。
  縮小軸は extime のみ。extime=3 (perf 完全一致) を優先候補にし、gate を通れば採用 —
  verify/perf の FLAGS_extime 判別子が消える (coder が verify 判別述語を書けない)。
  落ちたら extime=1 にフォールバック。records=1m の正当性は既存 calibration (D15
  下限基準、2026-06-18 実走) の継承 — 同一 workload 署名ゆえ再 calibration 不要。
- 既存 CorrectnessWorkload (tuple200/t4/rmw=true) は置き換えず**併存** (検出力担当 /
  S2 = データパス被覆担当)。配線 (verify 2 本立て) は段 5 — 本ドライバは構成確定のみ。

gate 3 点 (すべて実測・機械判定。基準の根拠は D36):
1. contention 再現 — trace-enabled abort 率が同 genome・同構成の trace-disabled 対照の
   [0.5, 2.0] 倍 (オーダー一致。対照も本ドライバが実測する — BACK_OFF=0 の歴史値
   0.7047 を対照にしない: genome が違う)。かつ abort 絶対数 >= 10,000。
2. trace 規模 — trace run が 120s (pipeline._run_trace timeout と同値) 内、
   verifier 処理 <= 600s、verifier maxrss <= 32GB。規模実測値を全記録。
3. 赤検出力 — (a) broken-silo (norw) が S2 構成で non-serializable (total_cycles >= 1、
   exit 1)。(b) broken-silo-highkey (key id >= 1000 のみ検証を抜く) が S2 構成で赤、
   かつ既存 CorrectnessWorkload 構成で緑 = 「小 workload では踏まないデータパスの違反を
   S2 だけが検出する」ablation の機械実証 (規律5: 効果を測れる ablation 点)。

trace-enabled の数値は verify 専用 — 性能比較に使わない (規律1)。broken build は
buildcache 非経由 (allowlist 検査があるため通らない・通してはいけない) の一時 build
dir (TMPDIR 配下、毎回 fresh — stale CMakeCache の沈黙再利用を構造的に排除)。

  python3 orchestrator/campaign/s2_verify_calibration.py    # 全 gate 実測 → JSON/md
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import (buildcache, condition_meaning_gate, site_policy, # noqa: E402
               source_digest)
from .layout import repo_output_root                           # noqa: E402
from .model import Genome                                      # noqa: E402
from .p2_2 import _assert_single_tenant                        # noqa: E402
from .patchharness import applied, assert_pinned_clean         # noqa: E402
from .build_admission import (GeneratorId, build_run_context,  # noqa: E402
                                      derive_build_admission)
from .pipeline import (CorrectnessWorkload, S2_FLAGS,           # noqa: E402
                       _parse_abort_counts, _parse_commit_witness)
from .materializer_admission import non_admissible_materializer  # noqa: E402


PIN = "dff0f1e"
ENV_TAG = "linux-baremetal"
CLK = 1800
REPS = 3
NUMA = ["numactl", "--interleave=all"]   # perf 計測 (p2_2/calibrator) と同条件。
                                         # 段 5 配線 (pipeline.evaluate) も同じ interleave で回す (D36)

_BASE = {"NO_WAIT_LOCKING_IN_VALIDATION": 1, "NO_WAIT_OF_TICTOC": 0, "WAL": 0}
STOCK_G = Genome("silo", {**_BASE, "BACK_OFF": 1})

# S2_FLAGS (perf 代表 workload と同一。max_ope=10 は ccbench 既定と同値だが明示凍結) は
# pipeline.py が正本 (段 5 pipeline 配線の CorrectnessWorkload と共有、二重定義防止)。
EXTIME_CANDIDATES = (3, 1)     # 3 優先 (perf 完全一致 = extime 判別子の除去)

GATE1_RATIO_BAND = (0.5, 2.0)
GATE1_MIN_ABORTS = 10_000
GATE2_RUN_TIMEOUT_S = 120.0
GATE2_VERIFIER_WALL_S = 600.0
GATE2_VERIFIER_RSS_GB = 32.0
MIN_FREE_DISK_GB = 20.0        # trace (extime3 で GB 級) + broken build 2 面

NORW_PATCH = "broken-silo-norw-validation.patch"
HIGHKEY_PATCH = "broken-silo-highkey-validation.patch"
NORW_DEFINE = "IZANAGI_BREAK_NOREAD_VALIDATION"
HIGHKEY_DEFINE = "IZANAGI_BREAK_HIGHKEY_VALIDATION"

def _repo_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(here))


def _require_condition_gate(source_root: str, macro: str) -> dict:
    captured = condition_meaning_gate.capture_define_inputs(
        source_root,
        configure_args=(*STOCK_G.cmake_defines(), "-DCCBENCH_TRACE=1"),
    )
    request = condition_meaning_gate.make_define_request(
        driver_id="orchestrator.campaign.s2_verify_calibration",
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
        (NORW_PATCH, NORW_DEFINE),
        (HIGHKEY_PATCH, HIGHKEY_DEFINE),
    ):
        with applied(os.path.join(root, "patches", patch_name), PIN, sub):
            records.append(_require_condition_gate(sub, macro))
    return records


def _assert_free_disk(path: str) -> float:
    free_gb = shutil.disk_usage(path).free / 2**30
    if free_gb < MIN_FREE_DISK_GB:
        raise RuntimeError(
            f"空きディスク {free_gb:.1f}GB < {MIN_FREE_DISK_GB}GB ({path}) — "
            "trace/broken build の置き場が足りない。清掃してから再実行。")
    return free_gb


def _run_once(binary: str, flags: dict, extime: int, trace: bool):
    """1 run。返り値 dict (commits/aborts/abort_rate/walltime_s/trace_stats)。

    fails-closed: rc != 0・commit/abort パース不能は即 RuntimeError (規律2 —
    壊れた run の数値で gate を判定しない)。"""
    args = NUMA + [binary] + [f"-{k}={v}" for k, v in flags.items()] \
        + [f"-extime={extime}", f"-clocks_per_us={CLK}"]
    tdir = tempfile.mkdtemp(prefix="izanagi_s2cal_trace_")
    env = dict(os.environ)
    if trace:
        env["IZANAGI_TRACE_DIR"] = tdir
    os.makedirs(os.path.join(tdir, "log"), exist_ok=True)
    t0 = time.monotonic()
    proc = subprocess.run(args, env=env, capture_output=True, text=True,
                          timeout=GATE2_RUN_TIMEOUT_S, cwd=tdir)
    wall = time.monotonic() - t0
    if proc.returncode != 0:
        shutil.rmtree(tdir, ignore_errors=True)
        raise RuntimeError(f"run rc={proc.returncode} (trace={trace}): "
                           f"{proc.stderr.strip()[-300:]}")
    commits, batch_commits = _parse_commit_witness(proc.stdout)
    aborts = _parse_abort_counts(proc.stdout)
    if commits is None or batch_commits is None or aborts is None:
        shutil.rmtree(tdir, ignore_errors=True)
        raise RuntimeError("stdout の commit_counts_/batch_commit_counts_/"
                           "abort_counts_ が欠落または不正 — "
                           "gate 判定不能 (fails-closed)")
    if batch_commits != 0:
        shutil.rmtree(tdir, ignore_errors=True)
        raise RuntimeError("stdout の batch_commit_counts_ が非 0 — "
                           "trace C 行へ帰属不能 (fails-closed)")
    out = {
        "commits": commits, "aborts": aborts,
        "abort_rate": aborts / (commits + aborts) if (commits + aborts) else None,
        "walltime_s": round(wall, 2),
    }
    if trace:
        files = [os.path.join(tdir, f) for f in os.listdir(tdir)
                 if f.startswith("trace_") and f.endswith(".log")]
        out["trace_stats"] = {
            "files": len(files),
            "bytes": sum(os.path.getsize(f) for f in files),
            "lines": sum(1 for f in files for _ in open(f, errors="replace")),
        }
        out["_trace_dir"] = tdir            # 呼び手が verifier 実走 or 清掃
    else:
        shutil.rmtree(tdir, ignore_errors=True)
    return out


def _verifier_run(trace_dir: str, expected_commits: int):
    """verifier を別プロセスで実走し (時間/maxrss を計測)、構造化結果を返す。"""
    cmd = ["/usr/bin/time", "-v", sys.executable, "-m", "verifier",
           trace_dir, "--json", "--quiet", "--protocol", "silo",
           "--ccbench-root", os.path.join(_repo_root(), "external", "ccbench"),
           "--expected-commits", str(expected_commits)]
    t0 = time.monotonic()
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          timeout=GATE2_VERIFIER_WALL_S,
                          cwd=os.path.join(_repo_root(), "orchestrator"))
    wall = time.monotonic() - t0
    m = re.search(r"Maximum resident set size \(kbytes\):\s*(\d+)", proc.stderr)
    maxrss_gb = int(m.group(1)) / 2**20 if m else None
    try:
        payload = json.loads(proc.stdout)
        r = payload["results"][0]
    except (json.JSONDecodeError, KeyError, IndexError):
        raise RuntimeError(f"verifier 出力のパース不能 (rc={proc.returncode}): "
                           f"{proc.stdout[:200]} / {proc.stderr[-200:]}")
    return {
        "exit_code": proc.returncode,
        "verdict": r["verdict"], "certified": r["certified"],
        "total_cycles": r["total_cycles"],
        "txns": r["stats"]["txns"], "edges": r["stats"]["edges"],
        "walltime_s": round(wall, 2), "maxrss_gb": round(maxrss_gb, 2) if maxrss_gb else None,
    }


def _median(xs):
    s = sorted(xs)
    return s[len(s) // 2]


def _measure_candidate(bin_trace: str, bin_perf: str, extime: int) -> dict:
    """extime 候補 1 つを実測し gate1/gate2 を判定する。"""
    print(f"\n--- S2 候補 extime={extime}: 対照 (trace-disabled) {REPS} reps ---")
    ctl = [_run_once(bin_perf, S2_FLAGS, extime, trace=False) for _ in range(REPS)]
    for r in ctl:
        print(f"  commits={r['commits']} aborts={r['aborts']} "
              f"abort_rate={r['abort_rate']:.4f} wall={r['walltime_s']}s")

    print(f"--- S2 候補 extime={extime}: 本測 (trace-enabled) {REPS} reps ---")
    runs, verifier = [], None
    for i in range(REPS):
        r = _run_once(bin_trace, S2_FLAGS, extime, trace=True)
        print(f"  commits={r['commits']} aborts={r['aborts']} "
              f"abort_rate={r['abort_rate']:.4f} wall={r['walltime_s']}s "
              f"trace={r['trace_stats']['bytes'] / 2**20:.0f}MB/{r['trace_stats']['lines']}行")
        tdir = r.pop("_trace_dir")
        if i == 0:                       # verifier 実走は 1 rep 分 (規律4: 規模計測に反復不要)
            print("  verifier 実走中...")
            verifier = _verifier_run(tdir, r["commits"])
            print(f"  verdict={verifier['verdict']} total_cycles={verifier['total_cycles']} "
                  f"wall={verifier['walltime_s']}s rss={verifier['maxrss_gb']}GB")
        shutil.rmtree(tdir, ignore_errors=True)
        runs.append(r)

    ctl_rate = _median([r["abort_rate"] for r in ctl])
    en_rate = _median([r["abort_rate"] for r in runs])
    en_aborts = _median([r["aborts"] for r in runs])
    ratio = en_rate / ctl_rate if ctl_rate else None
    gate1 = {
        "control_abort_rate_median": round(ctl_rate, 4),
        "enabled_abort_rate_median": round(en_rate, 4),
        "ratio": round(ratio, 3) if ratio else None,
        "enabled_aborts_median": en_aborts,
        "pass": (ratio is not None and GATE1_RATIO_BAND[0] <= ratio <= GATE1_RATIO_BAND[1]
                 and en_aborts >= GATE1_MIN_ABORTS),
    }
    # stock は緑のはず — 赤/indeterminate なら構成以前の問題 (fails-closed)
    stock_green = bool(verifier and verifier["certified"])
    gate2 = {
        "run_walltime_max_s": max(r["walltime_s"] for r in runs),
        "verifier": verifier,
        "stock_certified": stock_green,
        "pass": (stock_green
                 and max(r["walltime_s"] for r in runs) <= GATE2_RUN_TIMEOUT_S
                 and verifier["walltime_s"] <= GATE2_VERIFIER_WALL_S
                 and (verifier["maxrss_gb"] or 0) <= GATE2_VERIFIER_RSS_GB),
    }
    return {"extime": extime, "control_runs": ctl, "trace_runs": runs,
            "gate1": gate1, "gate2": gate2}


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


def _broken_build_and_verify(
        patch_name: str, define: str, workloads: dict, *, site=None,
) -> dict:
    """broken patch を applied() 下で一時 build し、各 workload で run→verifier。

    build は buildcache 非経由 (allowlist 検査を通らない・通してはいけない)。
    build dir は毎回 fresh な TMPDIR 配下 → 終了時に丸ごと削除 (stale CMakeCache 対策)。"""
    root = _repo_root()
    sub = os.path.join(root, "external", "ccbench")
    patch = os.path.join(root, "patches", patch_name)
    bdir = tempfile.mkdtemp(prefix=f"izanagi_s2cal_broken_")
    out = {"patch": patch_name, "define": define, "runs": {}}
    try:
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
            binary = os.path.join(bdir, "cc", "silo", "ycsb_silo.exe")
            for name, (flags, extime) in workloads.items():
                r = _run_once(binary, flags, extime, trace=True)
                tdir = r.pop("_trace_dir")
                v = _verifier_run(tdir, r["commits"])
                shutil.rmtree(tdir, ignore_errors=True)
                out["runs"][name] = {"run": r, "verifier": v}
                print(f"  [{patch_name} @ {name}] verdict={v['verdict']} "
                      f"total_cycles={v['total_cycles']} exit={v['exit_code']}")
    finally:
        shutil.rmtree(bdir, ignore_errors=True)
    return out


def main() -> int:
    root = _repo_root()
    sub = os.path.join(root, "external", "ccbench")
    _assert_single_tenant()
    free_gb = _assert_free_disk(tempfile.gettempdir())
    assert_pinned_clean(sub, PIN)
    condition_gates = _preflight_condition_gates(root, sub)

    print("=== stock build (buildcache — kickoff seed が残っていれば cache-hit) ===")
    build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    evidence = source_digest.resolve_evidence(STOCK_G, PIN)
    stock_admission = derive_build_admission(build_context, evidence)
    build_args = {"admission": stock_admission, "build_context": build_context,
                  "source_evidence": evidence}
    bt = buildcache.build(STOCK_G, PIN, trace=True, **build_args)
    bp = buildcache.build(STOCK_G, PIN, trace=False, **build_args)
    print(f"  trace={bt.bin_hash[:12]} ({'cache' if bt.cached else 'fresh'}) / "
          f"perf={bp.bin_hash[:12]} ({'cache' if bp.cached else 'fresh'})")

    results = {
        "config_name": "s2-verify",
        "env_tag": ENV_TAG, "ccbench_commit": PIN, "clocks_per_us": CLK,
        "genome": STOCK_G.canonical(), "s2_flags": S2_FLAGS,
        "condition_gates": condition_gates,
        "diagnostic_build_admission": non_admissible_materializer(
            "orchestrator.campaign.s2_verify_calibration._broken_build_and_verify"
        ),
        "legacy_correctness_flags": CorrectnessWorkload().flags,
        "gate_thresholds": {
            "gate1_ratio_band": GATE1_RATIO_BAND, "gate1_min_aborts": GATE1_MIN_ABORTS,
            "gate2_run_timeout_s": GATE2_RUN_TIMEOUT_S,
            "gate2_verifier_wall_s": GATE2_VERIFIER_WALL_S,
            "gate2_verifier_rss_gb": GATE2_VERIFIER_RSS_GB,
        },
        "free_disk_gb_at_start": round(free_gb, 1),
        "candidates": [], "chosen_extime": None,
    }

    chosen = None
    for extime in EXTIME_CANDIDATES:
        cand = _measure_candidate(bt.binary, bp.binary, extime)
        results["candidates"].append(cand)
        if cand["gate1"]["pass"] and cand["gate2"]["pass"]:
            chosen = extime
            break                        # 3 が通れば 1 は測らない (規律4)
        print(f"  extime={extime} は gate1={cand['gate1']['pass']} "
              f"gate2={cand['gate2']['pass']} → 次候補へ")
    if chosen is None:
        print("\n!!! 全 extime 候補が gate1/gate2 を落とした — S2 構成は未確定 "
              "(構成の再設計が必要。JSON に実測を残す)")
    results["chosen_extime"] = chosen

    gate3 = None
    if chosen is not None:
        s2 = (dict(S2_FLAGS), chosen)
        legacy_wl = CorrectnessWorkload().flags
        legacy = ({k: v for k, v in legacy_wl.items() if k != "extime"},
                  int(legacy_wl["extime"]))
        print(f"\n=== gate 3a: {NORW_PATCH} を S2 構成で (期待: 赤) ===")
        g3a = _broken_build_and_verify(NORW_PATCH, NORW_DEFINE, {"s2": s2})
        print(f"\n=== gate 3b: {HIGHKEY_PATCH} を S2 + legacy 構成で "
              "(期待: S2 赤 / legacy 緑 = ablation 実証) ===")
        g3b = _broken_build_and_verify(HIGHKEY_PATCH, HIGHKEY_DEFINE,
                                       {"s2": s2, "legacy": legacy})
        a = g3a["runs"]["s2"]["verifier"]
        b_s2 = g3b["runs"]["s2"]["verifier"]
        b_leg = g3b["runs"]["legacy"]["verifier"]
        gate3 = {
            "norw": g3a, "highkey": g3b,
            "norw_red": a["verdict"] == "non-serializable" and a["total_cycles"] >= 1
                        and a["exit_code"] == 1,
            "highkey_s2_red": b_s2["verdict"] == "non-serializable"
                              and b_s2["total_cycles"] >= 1,
            "highkey_legacy_green": b_leg["certified"],
            "pass": None,
        }
        gate3["pass"] = (gate3["norw_red"] and gate3["highkey_s2_red"]
                         and gate3["highkey_legacy_green"])
    results["gate3"] = gate3
    results["all_pass"] = bool(chosen is not None and gate3 and gate3["pass"])

    outdir = os.path.join(repo_output_root(), "env", ENV_TAG, "calibration")
    os.makedirs(outdir, exist_ok=True)
    base = os.path.join(outdir, "s2_verify_t48_skew0p9_rr50_rmw0")
    with open(base + ".json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    _write_md(base + ".md", results)
    print(f"\n結果: {base}.json / .md")
    print(f"all_pass={results['all_pass']} chosen_extime={chosen}")
    return 0 if results["all_pass"] else 1


def _write_md(path: str, r: dict) -> None:
    lines = [
        "# S2 縮小 verify 構成の校正結果 (phase3.md 後続段 1、D36)", "",
        f"- env: {r['env_tag']} / ccbench pin: {r['ccbench_commit']} / genome: `{r['genome']}`",
        f"- S2 構成: {r['s2_flags']} + extime={r['chosen_extime']} (perf 代表 workload と同一フラグ)",
        f"- 判定: **all_pass = {r['all_pass']}**", "",
        "## 候補別 gate 1/2", "",
    ]
    for c in r["candidates"]:
        g1, g2 = c["gate1"], c["gate2"]
        lines += [
            f"### extime={c['extime']}",
            f"- gate1 (contention 再現): {'PASS' if g1['pass'] else 'FAIL'} — "
            f"abort率 対照 {g1['control_abort_rate_median']} / trace時 "
            f"{g1['enabled_abort_rate_median']} (比 {g1['ratio']}, 帯 {r['gate_thresholds']['gate1_ratio_band']}), "
            f"aborts 中央値 {g1['enabled_aborts_median']}",
            f"- gate2 (trace 規模): {'PASS' if g2['pass'] else 'FAIL'} — "
            f"run 最大 {g2['run_walltime_max_s']}s, verifier {g2['verifier']['walltime_s']}s / "
            f"RSS {g2['verifier']['maxrss_gb']}GB / txns {g2['verifier']['txns']}, "
            f"stock certified = {g2['stock_certified']}", "",
        ]
    if r["gate3"]:
        g3 = r["gate3"]
        lines += [
            "## gate 3 (赤検出力 + ablation)", "",
            f"- norw @ S2: {'赤 PASS' if g3['norw_red'] else 'FAIL'} "
            f"(total_cycles={g3['norw']['runs']['s2']['verifier']['total_cycles']})",
            f"- highkey @ S2: {'赤 PASS' if g3['highkey_s2_red'] else 'FAIL'} "
            f"(total_cycles={g3['highkey']['runs']['s2']['verifier']['total_cycles']})",
            f"- highkey @ legacy (tuple200/t4): "
            f"{'緑 PASS' if g3['highkey_legacy_green'] else 'FAIL'} — "
            "S2 だけが検出する違反の機械実証 (ablation 点)", "",
        ]
    lines += ["## 生データ", "", "同名 .json (全 rep・全 run・閾値・環境)。", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
