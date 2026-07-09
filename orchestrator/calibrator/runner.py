# -*- coding: utf-8 -*-
"""1 測定点 = (records, threads) 固定で ccbench を perf 下で回し ScalePoint を組む。

絶対規律1: 性能計測は **trace-disabled build** (`build/`, `-DTRACE=0`) に当てる。
絶対規律4: スレッドピンニング (`-DLinux`、submodule master に還元済みで常に有効 —
cpu.hh setThreadAffinity) 済みの
binary を使い、OS スケジューラの socket 間 migration を止める。NUMA メモリ方針は
numactl で固定して run 間で再現可能にする (anatomy §7)。

measurement stability (roadmap §3.6): 1 点 = N 回反復し throughput を全部残す
(中央値 + CV は analyze 側)。ベンチ前に load average の静定を待つ (admission
control, calibrator.md / orchestrator-design.md)。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from typing import Dict, List, Optional, Sequence

from .benchparse import (_num, abort_rate as parse_abort_rate, latency_ns as
                         parse_latency_ns, parse_bench_stdout, throughput_tps)
from .model import ScalePoint
from .perfparse import parse_perf_stat


def _maxrss_kb(metrics: Dict[str, str]):
    """ccbench の `maxrss:\\t<N> kB` から常駐 kB を取る (working set 代理)。"""
    v = _num(metrics.get("maxrss"))
    return int(v) if v is not None else None

# 飽和シグナルに要る最小イベント + IPC 確認用。
PERF_EVENTS = ["LLC-load-misses", "LLC-loads", "instructions", "cycles"]


def settle(threshold: float = 4.0,
           timeout_s: float = 20.0, poll_s: float = 1.0) -> Dict[str, float]:
    """1 分 load average が threshold を下回るまで待つ (admission control)。

    目的は「直前ビルドの余熱や**他プロセス**の重い負荷が測定窓に漏れるのを防ぐ」
    こと。**campaign の冒頭で 1 回だけ**呼ぶ — 連続 run の間で呼んではいけない。
    自分の直前 run のスレッドは subprocess.run が join 済みで既に終了しており、
    load average (1 分 EMA) はその残像にすぎないので、点ごとに待つと EMA が
    下がりきらず無駄にタイムアウトを食う (それが初版の遅さの原因だった)。

    閾値は「他者の重い負荷」を検出する絶対値 (既定 4.0)。タイムアウトしたら
    現在値で諦めて進む (settled=False を notes に残す前提)。
    """
    deadline = time.monotonic() + timeout_s
    while True:
        load1 = os.getloadavg()[0]
        if load1 <= threshold or time.monotonic() >= deadline:
            return {"load1": load1, "threshold": threshold,
                    "settled": load1 <= threshold}
        time.sleep(poll_s)


def competing_bench_pids() -> List[str]:
    """他に走っている ccbench ベンチ (build-variants 下の ycsb_*.exe) の PID 行。

    settle() の load average は 1 分 EMA で laggy (汚染直後は検知できず、自分の直前 run の
    残像で誤検知する)。競合プロセスの直接確認はラグなしの確定信号なので、これを計測前の
    admission の一次ゲートにする (絶対規律4)。bench_lock は flock advisory で izanagi 自身の
    bench 同士しか排他せず、孤児化した子・他者が手起動した ycsb はロックを触らない
    (孤児 livelock 汚染インシデントの犯人) → pgrep で構造的に捕える。

    呼ぶのは自分のベンチが走り出す前 (各測定点の手前)。拾えるのは他者/孤児だけ。"""
    try:
        r = subprocess.run(["pgrep", "-af", r"build-variants/.*ycsb_.*\.exe"],
                           capture_output=True, text=True)
    except (OSError, subprocess.SubprocessError):
        return []
    return [ln for ln in r.stdout.splitlines() if ln.strip()]


def _build_cmd(binary: str, gflags: Sequence[str], perf_out: str,
               numactl: Optional[Sequence[str]]) -> List[str]:
    cmd: List[str] = []
    if numactl:
        cmd += list(numactl)
    cmd += ["perf", "stat", "-x,", "-o", perf_out, "-e", ",".join(PERF_EVENTS),
            "--", binary]
    cmd += list(gflags)
    return cmd


def repro_command(binary: str, gflags: Sequence[str],
                  numactl: Optional[Sequence[str]] = None) -> str:
    """測定点を手で再現するコマンド文字列。perf の `-o` 出力先 (一時ファイル) は外す =
    再現に無関係。実験再現用に ScalePoint.run_cmd / WAL に残す (forensic binding)。"""
    parts = list(numactl) if numactl else []
    parts += ["perf", "stat", "-e", ",".join(PERF_EVENTS), "--", binary]
    parts += list(gflags)
    return " ".join(parts)


def run_once(binary: str, gflags: Sequence[str],
             numactl: Optional[Sequence[str]] = None,
             timeout_s: float = 120.0,
             extra_env: Optional[Dict[str, str]] = None):
    """ccbench を perf 下で 1 回回し (bench_metrics, perf_counters, walltime) を返す。

    extra_env (D36 決定4-5): verify run にのみ設定される環境変数 (IZANAGI_TRACE_DIR
    等) を perf run にも対称に設定するための差し込み口。既定 None は環境変数を
    一切足さず (親プロセスの環境をそのまま継承)、既存呼び出し元の挙動を変えない。"""
    tmp = tempfile.mkdtemp(prefix="izanagi_run_")     # TMPDIR=/home 配下
    try:
        perf_out = os.path.join(tmp, "perf.csv")
        cmd = _build_cmd(binary, gflags, perf_out, numactl)
        # WAL=1 の genome は <cwd>/log/log<thid> に log を書く (CCBench fileio.hh
        # genLogFileName)。log/ が無いと open 失敗 → LibcError → SIGABRT で計測不能。
        # cwd を使い捨て tmp にし log/ を用意する (binary/perf_out は絶対パスなので
        # cwd 変更に非依存、tmp は finally で rmtree → WAL log も一緒に消える)。
        os.makedirs(os.path.join(tmp, "log"), exist_ok=True)
        env = dict(os.environ, **extra_env) if extra_env else None
        t0 = time.monotonic()
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout_s, cwd=tmp, env=env)
        wall = time.monotonic() - t0
        metrics = parse_bench_stdout(proc.stdout)
        perf_text = ""
        if os.path.exists(perf_out):
            with open(perf_out) as f:
                perf_text = f.read()
        counters = parse_perf_stat(perf_text)
        if not metrics:
            # bench が何も出さなかった = 異常 (stderr を添えて上げる)
            raise RuntimeError(
                f"ccbench produced no metrics. rc={proc.returncode} "
                f"stderr={proc.stderr[:400]}")
        return metrics, counters, wall
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def measure_point(binary: str, records: int, threads: int,
                  clocks_per_us: int, extime: int = 3, reps: int = 5,
                  workload: Optional[Dict[str, str]] = None,
                  numactl: Optional[Sequence[str]] = None,
                  settle_first: bool = False,
                  extra_env: Optional[Dict[str, str]] = None) -> ScalePoint:
    """1 測定点を reps 回反復して ScalePoint を組む。

    throughput は全 rep 分を残す (分布として扱う, roadmap §3.6)。perf counters は
    代表として中央 throughput の rep のものを採る (miss 率は run 間で安定)。

    settle_first は既定 False。admission control の静定待ちは campaign 冒頭で
    1 回行えば足り、点ごとに待つと load EMA の残像で無駄に時間を食う (settle の
    docstring 参照)。冒頭の 1 回は呼び手 (calibrate) が担う。
    """
    if settle_first:
        settle()

    base_flags = [
        f"-thread_num={threads}",
        f"-ycsb_tuple_num={records}",
        f"-extime={extime}",
        f"-clocks_per_us={clocks_per_us}",
    ]
    for k, v in (workload or {}).items():
        base_flags.append(f"-{k}={v}")

    pt = ScalePoint(records=records, threads=threads,
                    run_cmd=repro_command(binary, base_flags, numactl))
    rep_results = []   # (tps, counters, wall, maxrss_kb, abort_rate, latency_ns)
    n_exec_fail = 0
    for i in range(reps):
        # 規律3: 1 rep の run_once 失敗 (RuntimeError=metrics 空 / TimeoutExpired) で測定点
        # 全体を捨てず、握り潰さず notes に構造化記録して残り rep で median を取る
        # (reps>=2 の冗長性を活かす)。except: pass にはしない (沈黙させない)。
        try:
            metrics, counters, wall = run_once(binary, base_flags, numactl=numactl,
                                               extra_env=extra_env)
        except (RuntimeError, subprocess.TimeoutExpired) as e:
            n_exec_fail += 1
            pt.notes.append(f"rep{i} failed: {type(e).__name__}: {str(e)[:200]}")
            continue
        tps = throughput_tps(metrics)
        if tps is not None:
            pt.throughputs.append(tps)
        rep_results.append((tps, counters, wall, _maxrss_kb(metrics),
                            parse_abort_rate(metrics), parse_latency_ns(metrics)))
    if n_exec_fail:
        pt.notes.append(f"{n_exec_fail}/{reps} reps failed to execute")
    if not rep_results:
        # 全 rep が run_once 例外 = この測定点は本当に測れない。一部でも成功すれば上で
        # rep_results に積まれ median が取れる。全滅時のみ原因を集約して fail-closed
        # (規律3: 沈黙させず原因を添えて上げる)。
        raise RuntimeError(
            f"all {reps} reps failed at records={records} threads={threads}: "
            + " | ".join(pt.notes))

    # 代表値 = throughput が中央値に最も近い rep のもの。leading indicator (abort/
    # latency/cache) もこの代表 rep のものに揃える (同一 run の整合した断面にする)。
    valid = [r for r in rep_results if r[0] is not None]
    rep = None
    if valid:
        ts = sorted(r[0] for r in valid)
        med = ts[len(ts) // 2]
        rep = min(valid, key=lambda r: abs(r[0] - med))
    elif rep_results:
        rep = rep_results[-1]
    if rep is not None:
        (pt.counters, pt.walltime_s, pt.maxrss_kb,
         pt.abort_rate, pt.latency_ns) = rep[1], rep[2], rep[3], rep[4], rep[5]
    return pt
