# -*- coding: utf-8 -*-
"""評価パイプライン状態機械 — build → verify → [bench] → commit (orchestrator-design.md A/I/D)。

Phase 1 の全コンポーネントを束ねる統合点:
  buildcache (trace/perf 別ビルド, 絶対規律1) → verifier (正しさゲート, 絶対規律2) →
  calibrator.runner (bench_lock 下で perf, I) → WAL commit (A)。

**A (atomicity):** 各段を WAL に先行書き込みし、全段通過した瞬間だけ commit。
verifier が非 certified を返したら **abort** (絶対規律2: 正しさを破る variant は失格、
fitness を付けない)。**I (isolation):** bench は bench_lock + settle で排他・静定。
**D:** WAL 追記で再起動時に再開可能。
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

import sys as _sys
_HERE = os.path.dirname(os.path.abspath(__file__))
_sys.path.insert(0, os.path.dirname(_HERE))   # orchestrator/ を import パスに

from calibrator.runner import (competing_bench_pids,            # noqa: E402
                               measure_point, settle)
from calibrator.stability import remeasure_until_stable         # noqa: E402
from verifier import verify_trace_dir                           # noqa: E402
from verifier.parse import ParseError                           # noqa: E402

from . import buildcache, wal                                   # noqa: E402
from .layout import CampaignLayout                              # noqa: E402
from .lock import bench_lock                                    # noqa: E402
from .model import (Genome, STAGE_ABORT, STAGE_BENCH_DONE,      # noqa: E402
                    STAGE_BUILD_DONE, STAGE_BUILD_START, STAGE_COMMIT,
                    STAGE_VERIFY_DONE)


def variant_id(genome: Genome) -> str:
    """genome 正準表現の安定ハッシュ = variant の id (WAL キー)。"""
    return hashlib.sha256(genome.canonical().encode("utf-8")).hexdigest()[:12]


@dataclass
class CorrectnessWorkload:
    """verify 用の小規模・高 contention workload (trace を verifier に回せる規模)。"""
    flags: Dict[str, str] = field(default_factory=lambda: {
        "ycsb_tuple_num": "200", "ycsb_zipf_skew": "0.9", "ycsb_rratio": "50",
        "ycsb_rmw": "true", "ycsb_max_ope": "5", "thread_num": "4", "extime": "1"})


@dataclass
class PerfConfig:
    """bench 用の確定 calibration (records/threads/workload)。"""
    records: int
    threads: int
    workload: Dict[str, str] = field(default_factory=dict)
    extime: int = 3
    reps: int = 5


@dataclass
class EvalResult:
    genome: Genome
    variant: str
    certified: bool
    aborted: bool
    fitness_tps: Optional[float] = None
    cv: Optional[float] = None
    unstable: bool = False           # 規定ラウンドでも CV が収束しなかった (§3.6(2))
    verdict: str = ""
    notes: List[str] = field(default_factory=list)


def _run_trace(binary: str, trace_dir: str, flags: Dict[str, str],
               clocks_per_us: int, timeout_s: float = 120.0):
    """trace-enabled binary を回し IZANAGI_TRACE_DIR に trace を吐く。

    返り値 `(ncommit, returncode)`。**呼び手は returncode を必ず検査する** —
    異常終了した run の部分トレースを certified にしないため (規律2)。"""
    args = [binary] + [f"-{k}={v}" for k, v in flags.items()] \
        + [f"-clocks_per_us={clocks_per_us}"]
    env = dict(os.environ, IZANAGI_TRACE_DIR=trace_dir)
    # WAL=1 の genome は cwd/log/log<thid> に log を書く (CCBench fileio.hh genLogFileName)。
    # log/ が無いと open 失敗で LibcError → uncaught → SIGABRT。cwd を trace_dir にし log/ を
    # 用意する (trace_dir は使い捨て → log も一緒に消える。trace 出力は IZANAGI_TRACE_DIR で別制御)。
    os.makedirs(os.path.join(trace_dir, "log"), exist_ok=True)
    proc = subprocess.run(args, env=env, capture_output=True, text=True,
                          timeout=timeout_s, cwd=trace_dir)
    n = 0
    if os.path.isdir(trace_dir):
        for fn in os.listdir(trace_dir):
            if fn.startswith("trace_") and fn.endswith(".log"):
                with open(os.path.join(trace_dir, fn)) as f:
                    n += sum(1 for line in f if line.startswith("C "))
    return n, proc.returncode


def evaluate(genome: Genome, layout: CampaignLayout, env_tag: str,
             ccbench_commit: str, perf: PerfConfig,
             clocks_per_us: int, numactl: Optional[Sequence[str]] = None,
             correctness: Optional[CorrectnessWorkload] = None,
             do_bench: bool = True, do_settle: bool = True,
             log=print) -> EvalResult:
    """1 genome を評価し WAL に記録する。

    **正しさを確証できない variant は全て abort (fitness なし)** — verifier red だけで
    なく、ビルド失敗・trace 異常終了・空トレース・パース不能・bench 測定失敗も「採用
    しない」に倒す (規律2: certified を安売りしない / 空 DSG を緑と誤認させない)。
    abort も commit も terminal だが、abort は **fitness を付けず採用しない**。
    """
    correctness = correctness or CorrectnessWorkload()
    v = variant_id(genome)
    res = EvalResult(genome=genome, variant=v, certified=False, aborted=False)
    wal.log(layout, v, STAGE_BUILD_START, env_tag, {"genome": genome.canonical()})

    def _abort(reason: str, note: str, extra: Optional[Dict] = None) -> EvalResult:
        wal.log(layout, v, STAGE_ABORT, env_tag, {"reason": reason, **(extra or {})})
        res.aborted = True
        res.notes.append(note)
        log(f"  [eval {v}] abort: {reason}")
        return res

    # --- build (trace + perf 別ビルド, 絶対規律1)。ビルド失敗はこの variant 固有の
    #     失敗として abort 隔離 (campaign 全体を落とさず前進, overnight 耐性) ---
    try:
        tr = buildcache.build(genome, ccbench_commit, trace=True)
        pf = buildcache.build(genome, ccbench_commit, trace=False)
    except (RuntimeError, subprocess.SubprocessError) as e:
        return _abort("build-error", f"ビルド失敗 → reject ({e})")
    wal.log(layout, v, STAGE_BUILD_DONE, env_tag,
            {"trace_bin": tr.bin_hash, "perf_bin": pf.bin_hash,
             "trace_cached": tr.cached, "perf_cached": pf.cached,
             # fitness 計測に使う perf (trace-disabled) build の再現コマンド (規律1)。
             "perf_configure_cmd": pf.configure_cmd, "perf_build_cmd": pf.build_cmd})
    log(f"  [eval {v}] built trace={tr.bin_hash}{'(cache)' if tr.cached else ''} "
        f"perf={pf.bin_hash}{'(cache)' if pf.cached else ''}")

    # --- verify (正しさゲート, 絶対規律2) ---
    tdir = tempfile.mkdtemp(prefix="izanagi_eval_trace_")   # TMPDIR=/home 配下
    try:
        try:
            ncommit, rc = _run_trace(tr.binary, tdir, correctness.flags, clocks_per_us)
        except subprocess.TimeoutExpired:
            return _abort("trace-timeout", "trace 取得タイムアウト → reject")
        # 異常終了・空トレースは「正しさ未確定」。verifier に渡すと空 DSG が
        # serializable=True に化け false-green になる (規律2 違反) → 手前で reject。
        if rc != 0:
            return _abort("trace-run-nonzero-exit",
                          f"trace バイナリ異常終了 rc={rc} → reject",
                          {"rc": rc, "commits": ncommit})
        if ncommit == 0:
            return _abort("trace-empty",
                          "空トレース (commit 0) → 検証不能 reject", {"commits": 0})
        try:
            vr = verify_trace_dir(tdir)
        except ParseError as e:
            return _abort("trace-parse-error", f"trace パース不能 → reject ({e})")
        res.verdict = vr.verdict
        wal.log(layout, v, STAGE_VERIFY_DONE, env_tag,
                {"verdict": vr.verdict, "certified": vr.certified,
                 "commits": ncommit, "anomalies": len(vr.anomalies)})
        log(f"  [eval {v}] verify: {vr.verdict} ({ncommit} commits, "
            f"{len(vr.anomalies)} anomalies)")
        if not vr.certified:
            # 正しさを破る/確証できない variant は即 reject。fitness を付けない (規律2)。
            return _abort(vr.verdict, f"正しさゲート不通過 ({vr.verdict}) → reject")
        res.certified = True
    finally:
        shutil.rmtree(tdir, ignore_errors=True)

    if not do_bench:
        # 配線テストでベンチを省くとき: certified だけで commit (fitness なし)。
        wal.log(layout, v, STAGE_COMMIT, env_tag, {"fitness_tps": None,
                                                   "note": "no-bench"})
        return res

    # --- bench (排他 + 静定, I/Admission) ---
    # records は measure_point が -ycsb_tuple_num として渡す → workload に入れない
    # (入れると gflags last-wins で calibration の records を無言上書きする)。
    assert "ycsb_tuple_num" not in perf.workload, \
        "PerfConfig.workload に ycsb_tuple_num を入れない (records を上書きする)"

    def _measure():
        return measure_point(pf.binary, perf.records, perf.threads, clocks_per_us,
                             extime=perf.extime, reps=perf.reps,
                             workload=perf.workload, numactl=numactl)

    # 外れ値 → 自動再測定 (§3.6(2)): 反復内 CV が閾値超なら静定して測り直す。規定ラウンドで
    # 収束しなければ unstable。再測定の実走も全て bench_lock 下 = 単一テナント直列 (絶対規律4)。
    with bench_lock():
        # admission を fails-closed に (絶対規律4): bench_lock 取得直後・自分の bench 開始前に
        # 競合/孤児ベンチを pgrep で直接確認し、居たら**汚染計測を採用せず abort** する
        # (settle の load EMA は laggy なので一次ゲートはこの確定信号)。孤児は規律6 に従い
        # **自動 kill せず PID を表に出して停止** — 人間が処遇を判断する。driver の pre-flight が
        # campaign 冒頭で 1 回見るのに対し、ここは genome ごと = campaign 途中で湧いた競合も捕える。
        comp = competing_bench_pids()
        if comp:
            return _abort("bench-competing-tenant",
                          "競合 ccbench ベンチを検知 → 汚染計測を採用せず reject (規律4)",
                          {"competing": comp})
        settled = settle() if do_settle else None
        rem = remeasure_until_stable(_measure,
                                     settle_fn=settle if do_settle else None)
    pt, nf = rem.point, rem.nf
    if nf is None or nf.median is None:
        # 全 rep で throughput が取れず測定不能 → fitness 無しの COMMIT を書かない。
        # 半端な評価を terminal commit にして永久 skip させない (A: atomicity)。
        return _abort("bench-no-throughput", "bench 測定失敗 (throughput 無し) → reject",
                      {"tps": getattr(pt, "throughputs", None), "rounds": rem.rounds})
    res.fitness_tps, res.cv, res.unstable = nf.median, nf.cv, rem.unstable
    wal.log(layout, v, STAGE_BENCH_DONE, env_tag,
            {"median_tps": nf.median, "cv": nf.cv,
             "high_variance": nf.high_variance, "unstable": rem.unstable,
             "rounds": rem.rounds, "cv_history": rem.cv_history,
             "tps": pt.throughputs,
             # admission: load が静定したか (settle の戻り)。fails-closed の一次ゲートは
             # competing_bench_pids だが、settled=False の測定は forensic に残す (規律4)。
             "settled": (settled.get("settled") if settled else None),
             # leading indicators (§3.5): fitness を設計選択に帰属させる材料。
             # critic が abort率/latency/cache/IPC を読んで次の genome 方向を出す。
             "leading_indicators": pt.leading_indicators(),
             "run_cmd": pt.run_cmd})              # この測定点を再現する実行コマンド
    log(f"  [eval {v}] bench: median {nf.median:,.0f} tps (CV {nf.cv*100:.2f}%"
        f"{f', {rem.rounds}rounds' if rem.rounds > 1 else ''}"
        f"{' ⚠UNSTABLE' if rem.unstable else ''})")

    # --- commit (A: 全段通過した瞬間だけ) ---
    # unstable は規定ラウンドでも CV が収束しなかった印 = この 1 点を信用するな。正しさは
    # 通っているので reject はしないが、採否の分布比較から呼び手が除外する
    # (§3.6(4): 沈黙して 1 点を採用しない)。high_variance は採用ラウンド自体の騒がしさ。
    wal.log(layout, v, STAGE_COMMIT, env_tag,
            {"fitness_tps": nf.median, "cv": nf.cv,
             "high_variance": nf.high_variance, "unstable": rem.unstable})
    return res
