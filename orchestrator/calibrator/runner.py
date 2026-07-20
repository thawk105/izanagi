# -*- coding: utf-8 -*-
"""1 測定点 = (records, threads) 固定で ccbench を perf 下で回し ScalePoint を組む。

絶対規律1: 性能計測は **trace-disabled build** (`build/`, `-DCCBENCH_TRACE=0`) に当てる。
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
import re
import select
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Callable, Dict, List, Optional, Sequence

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

# C2-5/C3-7: composite probe は bench と同じ process pattern を一度だけ観測する。
COMPOSITE_PROBE_TIMEOUT_S = 10.0
CANARY_START_TIMEOUT_S = 5.0
CANARY_STOP_TIMEOUT_S = 5.0


class CompositeProbeViolation(RuntimeError):
    """canary 不可視、競合検出、または canary lifecycle 異常による fatal gate。"""

    def __init__(self, kind: str, detail: str, *, competitors: Optional[List[str]] = None):
        self.kind = kind
        self.detail = detail
        self.competitors = list(competitors or [])
        super().__init__(f"composite probe violation ({kind}): {detail}")

    def as_reason(self) -> str:
        suffix = "" if not self.competitors else f" competitors={self.competitors!r}"
        return f"probe-{self.kind}: {self.detail}{suffix}"


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


# stdout/stderr 抜粋の上限 (WAL abort payload の肥大防止, B-6)。
_PROBE_EXCERPT_LIMIT = 2000


class CompetingBenchProbeError(RuntimeError):
    """競合ベンチ検知 pgrep の実行自体が失敗し、競合の有無を確定できない (fail-closed)。

    握りつぶして「競合なし」と誤認すると汚染計測を採用しうる (規律4)。呼び手 (pipeline)
    はこの専用型だけを捕捉し、構造化 abort (bench-probe-error / verify-probe-error) に
    変換する。原因追跡のため kind / argv / returncode / errno / stdout・stderr の上限付き
    抜粋を保持する (B-6): kind は exec-failure (起動失敗) / unexpected-rc (rc>1・負値・
    rc==1 に付随出力) / inconsistent-output (rc==0 なのに空出力)。"""

    def __init__(self, kind: str, argv: Sequence[str],
                 returncode: Optional[int] = None, errno: Optional[int] = None,
                 stdout: str = "", stderr: str = ""):
        self.kind = kind
        self.argv = list(argv)
        self.returncode = returncode
        self.errno = errno
        self.stdout_excerpt = (stdout or "")[:_PROBE_EXCERPT_LIMIT]
        self.stderr_excerpt = (stderr or "")[:_PROBE_EXCERPT_LIMIT]
        super().__init__(
            f"competing_bench_pids probe 失敗 (kind={kind}, rc={returncode}, "
            f"errno={errno})")

    def as_dict(self) -> Dict[str, object]:
        """WAL abort payload に載せる構造化表現 (B-6: 再起動後も原因を区別できる)。"""
        return {"kind": self.kind, "argv": self.argv,
                "returncode": self.returncode, "errno": self.errno,
                "stdout_excerpt": self.stdout_excerpt,
                "stderr_excerpt": self.stderr_excerpt}


def classify_competing_probe(rc: int, stdout: str, stderr: str,
                             argv: Sequence[str], *,
                             own_pid: Optional[int] = None) -> List[str]:
    """pgrep の (rc, stdout, stderr) を strict 契約で分類し、他者/孤児の PID 行を返す。

    競合検知 probe の**単一の分類器** (C4-5: 二重実装の排除)。runner の
    `competing_bench_pids` と floor campaign の `strict_probe` が共にこれを消費する。
    raw stdout は呼び手が journal / WAL に残せるよう手を付けずに渡す。

    fail-closed 契約 (B-1): 競合の有無を確定できないときは握りつぶさず
    `CompetingBenchProbeError` を送出する。無競合と確定できるのは
    「rc==1 かつ stdout・stderr とも空」のときだけ (procps-ng pgrep の rc 契約:
    0=一致あり / 1=一致なし / >1=エラー)。BusyBox 等の option 構文エラーが rc==1+空
    stdout になる罠を stderr 非空で弾く。rc==0 は非空 stdout 必須 (空は
    inconsistent-output)。それ以外 (rc>1・負値・rc==1 に付随出力) はすべて例外。

    除外 (B-2): 自プロセス **自身 (`os.getpid()`) のみ**を非競合として落とす。
    自分がこれから起こす bench・直前 subprocess の残骸・二重 fork 孤児は、すべて
    「他者/孤児」として競合側に残す (自分の子孫まで除外していた旧実装からの縮小 —
    孤児 livelock 汚染は除外されず検出される)。PID がパースできない行も
    fails-closed で競合側に残す (素性不明を non-competing 扱いにしない)。"""
    if own_pid is None:
        own_pid = os.getpid()
    if isinstance(own_pid, bool) or not isinstance(own_pid, int) or own_pid <= 0:
        raise CompetingBenchProbeError(
            "invalid-own-pid", argv, stdout=stdout or "", stderr=stderr or "")
    stdout = stdout or ""
    stderr = stderr or ""
    # 無競合の確定信号: rc==1 かつ出力が完全に空。それ以外の rc==1 (付随出力あり) は
    # 素性が怪しいので下の unexpected-rc に倒す。
    if rc == 1 and not stdout.strip() and not stderr.strip():
        return []
    if rc == 0:
        lines = [ln for ln in stdout.splitlines() if ln.strip()]
        if not lines:
            # 一致ありを示す rc==0 なのに PID が 1 つも無い = 想定外の内部矛盾。
            raise CompetingBenchProbeError(
                "inconsistent-output", argv, returncode=rc,
                stdout=stdout, stderr=stderr)
        others = []
        for ln in lines:
            pid_field = ln.split(None, 1)[0]
            try:
                pid = int(pid_field)
            except ValueError:
                others.append(ln)          # PID 不明 = fails-closed で残す
                continue
            if pid != own_pid:             # B-2: 自 PID 自身のみ除外 (子孫は残す)
                others.append(ln)
        return others
    # rc>1 / 負値 (シグナル終了) / rc==1 に付随出力 → probe 故障。
    raise CompetingBenchProbeError(
        "unexpected-rc", argv, returncode=rc, stdout=stdout, stderr=stderr)


def competing_bench_pids() -> List[str]:
    """他に走っている ccbench ベンチ (`ycsb_*.exe`) の PID 行 (F3 admission 強化)。

    settle() の load average は 1 分 EMA で laggy (汚染直後は検知できず、自分の直前 run の
    残像で誤検知する)。競合プロセスの直接確認はラグなしの確定信号なので、これを計測前の
    admission の一次ゲートにする (絶対規律4)。bench_lock は flock advisory で izanagi 自身の
    bench 同士しか排他せず、孤児化した子・他者が手起動した ycsb はロックを触らない
    (孤児 livelock 汚染インシデントの犯人) → pgrep で構造的に捕える。

    パターンは binary path 非依存 (`ycsb_.*\\.exe` のみ、path 接頭辞なし)。旧パターン
    `build-variants/.*ycsb_.*\\.exe` は従来ビルド木限定で、8b oracle の
    `<output_root>/s8b-build-cache` 配下の孤児 bench を素通りさせていた (F3、
    docs/failures.md)。path を落とすと自プロセスがこれから起こす bench 自身も同じパターンに
    当たりうるので、自 PID (`os.getpid()`) だけを除外し「他者/孤児/自分の子」を残す
    (B-2: 子孫まで除外していた旧実装からの縮小 — 自分の子でも競合として検出する。
    孤児は除外されず検出される)。

    分類・fail-closed 契約 (B-1) の詳細は `classify_competing_probe` の docstring。
    起動失敗 (OSError/SubprocessError) は exec-failure として例外にする。

    呼ぶのは自分のベンチが走り出す前 (各測定点の手前)。拾えるのは他者/孤児/自分の子。"""
    argv = ["pgrep", "-af", r"ycsb_.*\.exe"]
    try:
        r = subprocess.run(argv, capture_output=True, text=True)
    except OSError as e:
        raise CompetingBenchProbeError(
            "exec-failure", argv, errno=getattr(e, "errno", None),
            stderr=str(e)) from e
    except subprocess.SubprocessError as e:
        raise CompetingBenchProbeError(
            "exec-failure", argv, stderr=str(e)) from e
    return classify_competing_probe(
        r.returncode, r.stdout or "", r.stderr or "", argv)


_NONCE_RE = re.compile(r"[A-Za-z0-9_-]{8,128}")


def _proc_starttime(pid: int) -> str:
    """Linux /proc stat の starttime を読む。PID reuse を fail-closed で弾く。"""
    try:
        with open(f"/proc/{pid}/stat", encoding="ascii") as f:
            fields = f.read().split()
    except OSError as exc:
        raise CompositeProbeViolation("canary-starttime", str(exc)) from exc
    if len(fields) <= 21 or not fields[21].isdigit():
        raise CompositeProbeViolation("canary-starttime", "invalid /proc stat")
    return fields[21]


def composite_competing_probe(
        *, nonce: str,
        subprocess_runner: Callable[..., object] = subprocess.run,
        popen_factory: Callable[..., subprocess.Popen] = subprocess.Popen,
        probe_timeout_s: float = COMPOSITE_PROBE_TIMEOUT_S) -> Dict[str, object]:
    """nonce canary を生かしたまま pgrep を一度だけ実行する composite gate。

    C2-5 の凍結契約: ``ycsb_.*\\.exe`` に一致する blocking child を pipe で起動同期し、
    同じ pgrep の出力に exact PID と nonce を含む行が見えることを要求する。その行だけを
    除外し、残りはすべて競合とする。低水準 ``classify_competing_probe`` の rc 契約は
    変更しない。canary は成功・失敗を問わず finally で terminate/wait する。
    """
    if type(nonce) is not str or _NONCE_RE.fullmatch(nonce) is None:
        raise CompositeProbeViolation("invalid-nonce", repr(nonce))

    ready_r, ready_w = os.pipe()
    release_r, release_w = os.pipe()
    child: Optional[subprocess.Popen] = None
    starttime = ""
    canary_name = f"ycsb_calibrator_canary_{nonce}.exe"
    script = (
        "import os,sys; "
        "os.write(int(sys.argv[1]),b'1'); "
        "os.read(int(sys.argv[2]),1)"
    )
    try:
        try:
            child = popen_factory(
                [sys.executable, "-c", script, str(ready_w), str(release_r), canary_name],
                pass_fds=(ready_w, release_r), close_fds=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise CompositeProbeViolation("canary-start", str(exc)) from exc
        os.close(ready_w)
        ready_w = -1
        os.close(release_r)
        release_r = -1
        readable, _, _ = select.select([ready_r], [], [], CANARY_START_TIMEOUT_S)
        if not readable or os.read(ready_r, 1) != b"1" or child.poll() is not None:
            raise CompositeProbeViolation("canary-sync", "blocking child did not become ready")
        starttime = _proc_starttime(child.pid)

        argv = ["pgrep", "-af", r"ycsb_.*\.exe"]
        try:
            raw = subprocess_runner(
                argv, capture_output=True, text=True, timeout=probe_timeout_s,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise CompetingBenchProbeError(
                "exec-failure", argv, errno=getattr(exc, "errno", None), stderr=str(exc),
            ) from exc
        lines = classify_competing_probe(
            raw.returncode, raw.stdout or "", raw.stderr or "", argv,
        )
        matches = []
        for index, line in enumerate(lines):
            fields = line.split(None, 1)
            if (fields and fields[0] == str(child.pid)
                    and line.count(canary_name) == 1):
                matches.append(index)
        if len(matches) != 1:
            raise CompositeProbeViolation(
                "visibility", f"expected one exact canary line, observed {len(matches)}",
            )
        competitors = [line for index, line in enumerate(lines) if index != matches[0]]
        if competitors:
            raise CompositeProbeViolation(
                "competition", "non-canary ycsb process observed", competitors=competitors,
            )
        if child.poll() is not None or _proc_starttime(child.pid) != starttime:
            raise CompositeProbeViolation("canary-lifecycle", "PID/starttime changed during probe")
        return {
            "status": "passed", "canary_pid": child.pid,
            "canary_nonce": nonce, "canary_starttime": starttime,
            "argv": argv,
        }
    finally:
        for fd in (ready_r, ready_w, release_r):
            if fd >= 0:
                try:
                    os.close(fd)
                except OSError:
                    pass
        try:
            os.write(release_w, b"x")
        except OSError:
            pass
        try:
            os.close(release_w)
        except OSError:
            pass
        if child is not None:
            try:
                child.terminate()
            except OSError:
                pass
            try:
                child.wait(timeout=CANARY_STOP_TIMEOUT_S)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=CANARY_STOP_TIMEOUT_S)


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
             extra_env: Optional[Dict[str, str]] = None,
             strict_returncode: bool = False,
             subprocess_runner: Callable[..., object] = subprocess.run,
             rep_returncodes: Optional[List[int]] = None):
    """ccbench を perf 下で 1 回回し (bench_metrics, perf_counters, walltime) を返す。

    extra_env (D36 決定4-5): verify run にのみ設定される環境変数 (IZANAGI_TRACE_DIR
    等) を perf run にも対称に設定するための差し込み口。既定 None は環境変数を
    一切足さず (親プロセスの環境をそのまま継承)、既存呼び出し元の挙動を変えない。
    rep_returncodes を指定した場合は subprocess 完了直後、出力や strict rc の検査より
    前に return code を追記する。戻り値の 3-tuple は変えない。"""
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
        proc = subprocess_runner(cmd, capture_output=True, text=True,
                                 timeout=timeout_s, cwd=tmp, env=env)
        if rep_returncodes is not None:
            rep_returncodes.append(proc.returncode)
        wall = time.monotonic() - t0
        if strict_returncode and proc.returncode != 0:
            raise RuntimeError(
                f"ccbench failed. rc={proc.returncode} stderr={(proc.stderr or '')[:400]}")
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
                  extra_env: Optional[Dict[str, str]] = None,
                  timeout_s: float = 120.0,
                  require_all_reps: bool = False,
                  require_complete_metrics: bool = False,
                  subprocess_runner: Callable[..., object] = subprocess.run,
                  rep_returncodes: Optional[List[int]] = None) -> ScalePoint:
    """1 測定点を reps 回反復して ScalePoint を組む。

    throughput は全 rep 分を残す (分布として扱う, roadmap §3.6)。perf counters は
    代表として中央 throughput の rep のものを採る (miss 率は run 間で安定)。

    settle_first は既定 False。admission control の静定待ちは campaign 冒頭で
    1 回行えば足り、点ごとに待つと load EMA の残像で無駄に時間を食う (settle の
    docstring 参照)。冒頭の 1 回は呼び手 (calibrate) が担う。

    rep_returncodes 未指定時は run_once へ同名 kwarg を送らず、既存 monkeypatch seam を
    保つ。指定時だけ各 rep の subprocess 完了順 rc を同じ list に蓄積する。
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
            run_kwargs = {
                "numactl": numactl, "extra_env": extra_env,
                "timeout_s": timeout_s,
            }
            # 非 certify の既存 monkeypatch seam/signature を変えない。
            if require_all_reps or require_complete_metrics:
                run_kwargs["strict_returncode"] = require_all_reps
                run_kwargs["subprocess_runner"] = subprocess_runner
            if rep_returncodes is not None:
                run_kwargs["rep_returncodes"] = rep_returncodes
            metrics, counters, wall = run_once(binary, base_flags, **run_kwargs)
        except (RuntimeError, subprocess.TimeoutExpired) as e:
            if require_all_reps:
                raise RuntimeError(
                    f"rep{i}/{reps} fatal at records={records} threads={threads}: "
                    f"{type(e).__name__}: {str(e)[:200]}") from e
            n_exec_fail += 1
            pt.notes.append(f"rep{i} failed: {type(e).__name__}: {str(e)[:200]}")
            continue
        tps = throughput_tps(metrics)
        maxrss = _maxrss_kb(metrics)
        if require_complete_metrics:
            missing = []
            if tps is None:
                missing.append("throughput")
            for name in ("llc_load_misses", "llc_loads", "instructions", "cycles"):
                if getattr(counters, name) is None:
                    missing.append(name)
            if maxrss is None:
                missing.append("maxrss")
            if missing:
                raise RuntimeError(
                    f"rep{i}/{reps} missing required metrics at records={records}: "
                    + ",".join(missing))
        if tps is not None:
            pt.throughputs.append(tps)
        rep_results.append((tps, counters, wall, maxrss,
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
