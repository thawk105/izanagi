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

import contextvars
import hashlib
import io
import os
import re
import select
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import weakref
from typing import Callable, Dict, List, NamedTuple, Optional, Sequence

from orchestrator.holdout_observation import (
    CalibrationObservationCapability,
    HoldoutObservationAdmission,
    HoldoutObservationError,
    assert_holdout_observation_admitted,
    normalized_direct_gflags,
)

from .benchparse import (integer_abort_commit_counts, _num, abort_rate as parse_abort_rate, latency_ns as
                         parse_latency_ns, parse_bench_stdout, throughput_tps)
from .model import PerfCounters, ScalePoint
from .perfparse import parse_perf_stat


def _maxrss_kb(metrics: Dict[str, str]):
    """ccbench の `maxrss:\\t<N> kB` から常駐 kB を取る (working set 代理)。"""
    v = _num(metrics.get("maxrss"))
    return int(v) if v is not None else None

# 飽和シグナルに要る最小イベント + IPC 確認用。
PERF_EVENTS = ["LLC-load-misses", "LLC-loads", "instructions", "cycles"]


class MeasurementLaunchFailure(NamedTuple):
    """Sanitized pre-open fact that no completed child result was obtained."""

    exception_type: str
    errno: Optional[int]
    message: str


class CapturedMeasurement:
    """Raw measurement output sealed behind an observable one-shot open.

    The token deliberately has no instance dictionary and carries no stdout,
    stderr, or temporary perf path. Those values live in the module-private
    vault until :meth:`open` atomically removes and consumes its payload.
    ``launch_failures`` is the sole pre-open result surface: it contains only
    sanitized facts about an ``OSError`` raised without a completed child.
    """

    __slots__ = ("__launch_failures", "__opened", "__weakref__", "__lock")

    def __init__(
            self,
            launch_failures: Sequence[MeasurementLaunchFailure] = (),
    ) -> None:
        self.__launch_failures = tuple(launch_failures)
        self.__opened = False
        self.__lock = threading.Lock()

    @property
    def opened(self) -> bool:
        """Whether the one permitted open attempt has begun."""
        return self.__opened

    @property
    def launch_failures(self) -> tuple[MeasurementLaunchFailure, ...]:
        """Child-launch failures available without opening captured output."""
        return self.__launch_failures

    def open(self):
        """Decode, parse, and derive the captured result exactly once."""
        with self.__lock:
            if self.__opened:
                raise RuntimeError("captured measurement output was already opened")
            with _CAPTURED_OUTPUTS_LOCK:
                payload = _CAPTURED_OUTPUTS.pop(self, None)
            if payload is None:
                raise RuntimeError("captured measurement output is unavailable")
            self.__opened = True
        return payload.open()


class _CapturedOutputPayload:
    """Vault value whose cleanup also runs when an unopened token is dropped."""

    def __init__(self, opener: Callable[[], object],
                 cleanup: Optional[Callable[[], None]] = None) -> None:
        self._opener = opener
        self._cleanup = cleanup

    def open(self):
        try:
            return self._opener()
        finally:
            self.close()

    def close(self) -> None:
        cleanup, self._cleanup = self._cleanup, None
        self._opener = lambda: None
        if cleanup is not None:
            cleanup()

    def __del__(self) -> None:
        self.close()


_CAPTURED_OUTPUTS: weakref.WeakKeyDictionary[
    CapturedMeasurement, _CapturedOutputPayload
] = weakref.WeakKeyDictionary()
_CAPTURED_FLOW_CONTROL: weakref.WeakKeyDictionary[
    CapturedMeasurement, tuple[Optional[int], bool]
] = weakref.WeakKeyDictionary()
_CAPTURED_OUTPUTS_LOCK = threading.Lock()
_DEFER_RUN_OUTPUT = contextvars.ContextVar(
    "izanagi_defer_calibrator_run_output", default=False,
)


def _seal_captured_output(
        opener: Callable[[], object], *,
        cleanup: Optional[Callable[[], None]] = None,
        launch_failures: Sequence[
            MeasurementLaunchFailure
        ] = (),
        flow_control: tuple[Optional[int], bool] | None = None,
) -> CapturedMeasurement:
    token = CapturedMeasurement(launch_failures)
    with _CAPTURED_OUTPUTS_LOCK:
        _CAPTURED_OUTPUTS[token] = _CapturedOutputPayload(opener, cleanup)
        if flow_control is not None:
            _CAPTURED_FLOW_CONTROL[token] = flow_control
    return token


def _captured_flow_control(
        token: CapturedMeasurement,
) -> tuple[Optional[int], bool] | None:
    """Return private spawn flow control without exposing it on the token."""
    with _CAPTURED_OUTPUTS_LOCK:
        return _CAPTURED_FLOW_CONTROL.get(token)


def _decode_captured_output(raw):
    """Apply ``text=True``'s locale decode and universal-newline semantics late."""
    if not isinstance(raw, bytes):
        # Existing injected subprocess seams return text even when the real
        # invocation requests bytes. Preserve that long-standing test/API seam.
        return raw
    with io.TextIOWrapper(io.BytesIO(raw), errors="strict", newline=None) as stream:
        return stream.read()


def _open_deferred_perf_bytes(raw: bytes) -> str:
    """Open sealed perf bytes only after classification, outside all rep runs."""
    with tempfile.TemporaryDirectory(prefix="izanagi_perf_open_") as tmp:
        path = os.path.join(tmp, "perf.csv")
        descriptor = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        try:
            offset = 0
            while offset < len(raw):
                offset += os.write(descriptor, raw[offset:])
        finally:
            os.close(descriptor)
        with open(path) as stream:
            return stream.read()


def _read_perf_bytes_for_deferred_cleanup(path: str) -> Optional[bytes]:
    """Seal raw perf bytes without decoding them, then permit tmp cleanup."""
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0))
    except FileNotFoundError:
        return None
    try:
        chunks = []
        while True:
            chunk = os.read(descriptor, 65536)
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)
    finally:
        os.close(descriptor)


def _perf_raw_values(text: str) -> Dict[str, Optional[int]]:
    """perf CSV から対象 4 event の raw 値を独立に保存する。

    parser の集約値は欠損行で既存値を消さないため、証跡には使わない。同一 event が
    複数回現れた場合も曖昧なので None とし、完備性判定を fail-closed に倒す。
    """
    seen: Dict[str, List[Optional[int]]] = {event: [] for event in PERF_EVENTS}
    canonical = {event.lower(): event for event in PERF_EVENTS}
    for line in text.splitlines():
        fields = line.split(",")
        if len(fields) < 3:
            continue
        event_token = fields[2].strip().strip('"').split(":", 1)[0].lower()
        event = canonical.get(event_token)
        if event is None:
            continue
        token = fields[0].strip().strip('"').replace(",", "")
        try:
            # perf counter は整数だけを証跡として受理する。float 経由の切り捨てで
            # 小数・inf 等の不正 raw 値を valid な整数へ変換しない。
            value = int(token)
        except ValueError:
            value = None
        seen[event].append(value)
    return {
        event: values[0] if len(values) == 1 else None
        for event, values in seen.items()
    }


def _counter_observation(perf_raw: Dict[str, Optional[int]], *, use_perf: bool) -> tuple:
    """raw counter から missing 列と status を一意に導出する。"""
    if not use_perf:
        return [], "not_required"
    missing = [
        event for event in PERF_EVENTS
        if type(perf_raw.get(event)) is not int or perf_raw[event] < 0
    ]
    return missing, "complete" if not missing else "incomplete"

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
               numactl: Optional[Sequence[str]], *, use_perf: bool = True) -> List[str]:
    cmd: List[str] = []
    if numactl:
        cmd += list(numactl)
    if use_perf:
        cmd += ["perf", "stat", "-x,", "-o", perf_out, "-e", ",".join(PERF_EVENTS),
                "--"]
    cmd.append(binary)
    cmd += list(gflags)
    return cmd


def repro_command(binary: str, gflags: Sequence[str],
                  numactl: Optional[Sequence[str]] = None, *,
                  use_perf: bool = True) -> str:
    """測定点を手で再現するコマンド文字列。perf の `-o` 出力先 (一時ファイル) は外す =
    再現に無関係。実験再現用に ScalePoint.run_cmd / WAL に残す (forensic binding)。"""
    parts = list(numactl) if numactl else []
    if use_perf:
        parts += ["perf", "stat", "-e", ",".join(PERF_EVENTS), "--"]
    parts.append(binary)
    parts += list(gflags)
    return " ".join(parts)


def _point_repro_command(
        binary: str, gflags: Sequence[str],
        numactl: Optional[Sequence[str]], use_perf: bool) -> str:
    """Keep the shared point builders on one reviewed ``use_perf`` call site."""
    return repro_command(
        binary, gflags, numactl, use_perf=use_perf,
    )


def _calibration_binary_sha256(binary: str) -> str:
    """Hash the executable bytes at the spawn boundary, never a caller claim."""
    digest = hashlib.sha256()
    try:
        with open(binary, "rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise HoldoutObservationError(
            f"calibration binary cannot be hashed: {binary}: {exc}") from exc
    return digest.hexdigest()


def run_once(binary: str, gflags: Sequence[str],
             numactl: Optional[Sequence[str]] = None,
             timeout_s: float = 120.0,
             extra_env: Optional[Dict[str, str]] = None,
             strict_returncode: bool = False,
             subprocess_runner: Callable[..., object] = subprocess.run,
             rep_returncodes: Optional[List[int]] = None,
             perf_raw_sink: Optional[Dict[str, Optional[int]]] = None, *,
             use_perf: bool = True,
             holdout_observation_admission: Optional[
                 HoldoutObservationAdmission
             ] = None,
             calibration_observation_capability: Optional[
                 CalibrationObservationCapability
             ] = None,
             calibration_observation_phase: Optional[str] = None):
    """ccbench を perf 下で 1 回回し (bench_metrics, perf_counters, walltime) を返す。

    extra_env (D36 決定4-5): verify run にのみ設定される環境変数 (IZANAGI_TRACE_DIR
    等) を perf run にも対称に設定するための差し込み口。親環境と extra_env は
    FLAGS_ 接頭辞だけを除いた閉じた環境へ統合する。
    rep_returncodes を指定した場合、公開経路は従来どおり subprocess 完了直後、
    deferred 経路は output open 時に、いずれも strict rc 検査より前へ追記する。
    perf_raw_sink は parser の集約値とは独立した 4 event の証跡を受け取る。公開 API の
    戻り値の 3-tuple と例外契約は変えない。"""
    gflags_snapshot = tuple(gflags)
    execution_numactl = numactl
    execution_extra_env = extra_env
    if calibration_observation_capability is None:
        assert_holdout_observation_admitted(
            gflags=gflags_snapshot,
            admission=holdout_observation_admission,
        )
    else:
        # Preserve the gateway's no-effect ordering for malformed/indirect
        # flags before opening the executable for its binding hash.
        normalized_direct_gflags(gflags_snapshot)
        execution_numactl, execution_extra_env = (
            assert_holdout_observation_admitted(
                gflags=gflags_snapshot,
                admission=holdout_observation_admission,
                calibration_observation_capability=(
                    calibration_observation_capability
                ),
                calibration_observation_phase=calibration_observation_phase,
                binary_sha256=_calibration_binary_sha256(binary),
                numactl=numactl,
                timeout_s=timeout_s,
                use_perf=use_perf,
                extra_env=extra_env,
            )
        )
    # TMPDIR 配下 (明示されていなければ環境既定の /tmp)。
    tmp = tempfile.mkdtemp(prefix="izanagi_run_")
    capture_transferred = False
    try:
        perf_out = os.path.join(tmp, "perf.csv")
        cmd = _build_cmd(
            binary, gflags_snapshot, perf_out, execution_numactl,
            use_perf=use_perf,
        )
        # WAL=1 の genome は <cwd>/log/log<thid> に log を書く (CCBench fileio.hh
        # genLogFileName)。log/ が無いと open 失敗 → LibcError → SIGABRT で計測不能。
        # cwd を使い捨て tmp にし log/ を用意する (binary/perf_out は絶対パスなので
        # cwd 変更に非依存、tmp は finally で rmtree → WAL log も一緒に消える)。
        os.makedirs(os.path.join(tmp, "log"), exist_ok=True)
        env = dict(os.environ)
        if execution_extra_env:
            env.update(execution_extra_env)
        env = {key: value for key, value in env.items()
               if not key.startswith("FLAGS_")}
        defer_output = bool(_DEFER_RUN_OUTPUT.get())
        t0 = time.monotonic()
        proc = None
        deferred_error = None
        launch_failures: tuple[MeasurementLaunchFailure, ...] = ()
        try:
            # This exact call remains the sole reviewed CCBench spawn site.
            # Bytes are intentionally retained without decoding until token.open().
            proc = subprocess_runner(cmd, capture_output=True, text=not defer_output,
                                     timeout=timeout_s, cwd=tmp, env=env)
        except subprocess.TimeoutExpired as exc:
            if not defer_output:
                raise
            # A timeout may carry partial stdout/stderr and is therefore output-derived.
            deferred_error = exc
        except OSError as exc:
            if not defer_output:
                raise
            # No CompletedProcess exists: this is the only pre-open failure class.
            deferred_error = exc
            launch_failures = (MeasurementLaunchFailure(
                exception_type=type(exc).__name__,
                errno=getattr(exc, "errno", None),
                message=str(exc),
            ),)
            # Do not let the pre-open summary expose this frame's perf path.
            exc.__traceback__ = None
        if (
                not defer_output
                and proc is not None
                and rep_returncodes is not None
        ):
            rep_returncodes.append(proc.returncode)
        wall = time.monotonic() - t0

        deferred_perf_bytes: bytes | None = None
        if defer_output:
            if proc is not None:
                deferred_perf_bytes = _read_perf_bytes_for_deferred_cleanup(
                    perf_out
                )
            shutil.rmtree(tmp, ignore_errors=True)

        def open_run_output():
            if deferred_error is not None:
                raise deferred_error
            assert proc is not None
            stdout = _decode_captured_output(proc.stdout)
            stderr = _decode_captured_output(proc.stderr)
            if defer_output and rep_returncodes is not None:
                rep_returncodes.append(proc.returncode)
            if strict_returncode and proc.returncode != 0:
                raise RuntimeError(
                    f"ccbench failed. rc={proc.returncode} "
                    f"stderr={(stderr or '')[:400]}")
            metrics = parse_bench_stdout(stdout)
            if deferred_perf_bytes is not None:
                perf_text = _open_deferred_perf_bytes(deferred_perf_bytes)
            elif os.path.exists(perf_out):
                with open(perf_out) as f:
                    perf_text = f.read()
            else:
                perf_text = ""
            raw_values = (_perf_raw_values(perf_text) if use_perf
                          else {event: None for event in PERF_EVENTS})
            if perf_raw_sink is not None:
                perf_raw_sink.clear()
                perf_raw_sink.update(raw_values)
            try:
                counters = parse_perf_stat(perf_text)
            except OverflowError:
                # parser 本体は凍結面。inf 等は証跡側で欠損に正規化し、集約 counter も
                # fail-closed に全欠損とする。
                counters = PerfCounters()
            if not metrics:
                # bench が何も出さなかった = 異常 (stderr を添えて上げる)
                raise RuntimeError(
                    f"ccbench produced no metrics. rc={proc.returncode} "
                    f"stderr={stderr[:400]}")
            return metrics, counters, wall

        captured = _seal_captured_output(
            open_run_output,
            cleanup=(
                None if defer_output
                else lambda: shutil.rmtree(tmp, ignore_errors=True)
            ),
            launch_failures=launch_failures,
            flow_control=(
                proc.returncode if proc is not None else None,
                isinstance(deferred_error, subprocess.TimeoutExpired),
            ) if defer_output else None,
        )
        capture_transferred = True
        if defer_output:
            return captured
        return captured.open()
    finally:
        if not capture_transferred:
            shutil.rmtree(tmp, ignore_errors=True)


def capture_run_once(binary: str, gflags: Sequence[str],
                     numactl: Optional[Sequence[str]] = None,
                     timeout_s: float = 120.0,
                     extra_env: Optional[Dict[str, str]] = None,
                     strict_returncode: bool = False,
                     subprocess_runner: Callable[..., object] = subprocess.run,
                     rep_returncodes: Optional[List[int]] = None,
                     perf_raw_sink: Optional[
                         Dict[str, Optional[int]]
                     ] = None, *,
                     use_perf: bool = True,
                     holdout_observation_admission: Optional[
                         HoldoutObservationAdmission
                     ] = None,
                     calibration_observation_capability: Optional[
                         CalibrationObservationCapability
                     ] = None,
                     calibration_observation_phase: Optional[
                         str
                     ] = None) -> CapturedMeasurement:
    """Capture one run without decoding, parsing, deriving, or updating sinks.

    Raw perf bytes are copied into the opaque vault before the per-rep tmp is
    removed; no counter or performance quantity is derived at that point.
    """
    marker = _DEFER_RUN_OUTPUT.set(True)
    try:
        result = run_once(
            binary, gflags, numactl=numactl, timeout_s=timeout_s,
            extra_env=extra_env, strict_returncode=strict_returncode,
            subprocess_runner=subprocess_runner,
            rep_returncodes=rep_returncodes, perf_raw_sink=perf_raw_sink,
            use_perf=use_perf,
            holdout_observation_admission=holdout_observation_admission,
            calibration_observation_capability=calibration_observation_capability,
            calibration_observation_phase=calibration_observation_phase,
        )
    finally:
        _DEFER_RUN_OUTPUT.reset(marker)
    if isinstance(result, CapturedMeasurement):
        return result
    # Preserve the established monkeypatch seam: injected run_once functions
    # may still return the historical parsed 3-tuple.
    return _seal_captured_output(lambda: result)


def capture_measure_point(
        binary: str, records: int, threads: int,
        clocks_per_us: int, extime: int = 3, reps: int = 5,
        workload: Optional[Dict[str, str]] = None,
        numactl: Optional[Sequence[str]] = None,
        settle_first: bool = False,
        extra_env: Optional[Dict[str, str]] = None,
        timeout_s: float = 120.0,
        require_all_reps: bool = False,
        require_complete_metrics: bool = False,
        subprocess_runner: Callable[..., object] = subprocess.run,
        rep_returncodes: Optional[List[int]] = None,
        rep_observations: Optional[List[Dict[str, object]]] = None, *,
                  record_rep_integer_counters: bool = False,
        use_perf: bool = True,
        holdout_observation_admission: Optional[
            HoldoutObservationAdmission
        ] = None,
        calibration_observation_capability: Optional[
            CalibrationObservationCapability
        ] = None,
        calibration_observation_phase: Optional[str] = None,
) -> CapturedMeasurement:
    """Run all reps and return their bytes as one sealed, one-shot token.

    The subprocesses use the historical argv/environment/cwd/timeout path.
    Raw perf bytes are sealed and the rep tmp is removed before the next spawn.
    stdout/stderr decode, perf text open, parsers, metric derivation, and
    caller-owned sink updates all begin only inside ``token.open()``.
    """
    if record_rep_integer_counters and rep_observations is None:
        rep_observations = []
    if settle_first:
        settle()

    base_flags = [
        f"-thread_num={threads}",
        f"-ycsb_tuple_num={records}",
        f"-extime={extime}",
        f"-clocks_per_us={clocks_per_us}",
    ]
    for key, value in (workload or {}).items():
        base_flags.append(f"-{key}={value}")
    run_cmd = _point_repro_command(
        binary, base_flags, numactl, use_perf,
    )

    captured_reps = []
    launch_failures: List[MeasurementLaunchFailure] = []
    for _i in range(reps):
        local_returncodes: Optional[List[int]] = (
            [] if rep_observations is not None else None
        )
        perf_raw: Dict[str, Optional[int]] = {
            event: None for event in PERF_EVENTS
        }
        capture_exception = None
        try:
            run_kwargs = {
                "numactl": numactl, "extra_env": extra_env,
                "timeout_s": timeout_s,
            }
            # Keep the historical default kwarg shape, while honoring an
            # explicit runner on the deferred capture surface.
            if (require_all_reps or require_complete_metrics
                    or rep_observations is not None):
                run_kwargs["strict_returncode"] = require_all_reps
                run_kwargs["subprocess_runner"] = subprocess_runner
            elif subprocess_runner is not subprocess.run:
                run_kwargs["subprocess_runner"] = subprocess_runner
            if rep_observations is not None:
                run_kwargs["rep_returncodes"] = local_returncodes
                run_kwargs["perf_raw_sink"] = perf_raw
            elif rep_returncodes is not None:
                run_kwargs["rep_returncodes"] = rep_returncodes
            if not use_perf:
                run_kwargs["use_perf"] = False
            if holdout_observation_admission is not None:
                run_kwargs["holdout_observation_admission"] = (
                    holdout_observation_admission
                )
            if calibration_observation_capability is not None:
                run_kwargs["calibration_observation_capability"] = (
                    calibration_observation_capability
                )
                run_kwargs["calibration_observation_phase"] = (
                    calibration_observation_phase
                )
            marker = _DEFER_RUN_OUTPUT.set(True)
            try:
                result = run_once(binary, base_flags, **run_kwargs)
            finally:
                _DEFER_RUN_OUTPUT.reset(marker)
            captured = (
                result if isinstance(result, CapturedMeasurement)
                else _seal_captured_output(lambda result=result: result)
            )
        except Exception as exc:
            capture_exception = exc

            def raise_captured(error=exc):
                raise error
            captured = _seal_captured_output(raise_captured)
        launch_failures.extend(captured.launch_failures)
        captured_reps.append((captured, local_returncodes, perf_raw))
        flow_control = _captured_flow_control(captured)
        if captured.launch_failures and (
                rep_observations is None or require_all_reps):
            break
        if (
                require_all_reps
                and flow_control is not None
                and (
                    flow_control[1]
                    or (
                        flow_control[0] is not None
                        and flow_control[0] != 0
                    )
                )
        ):
            # A return code may preserve historical spawn flow control, but is
            # deliberately absent from CapturedMeasurement's public surface.
            break
        if capture_exception is not None:
            if isinstance(
                    capture_exception,
                    (RuntimeError, subprocess.TimeoutExpired),
            ):
                if require_all_reps:
                    break
            elif rep_observations is None or require_all_reps:
                break

    def open_measurement_point():
        pt = ScalePoint(
            records=records, threads=threads,
            run_cmd=run_cmd,
        )
        if rep_observations is not None:
            rep_observations[:] = [
                {
                    "rep_index": index,
                    "returncode": None,
                    "execution_failure": False,
                    "counter_status": "unknown",
                    "missing_perf_events": (
                        list(PERF_EVENTS) if use_perf else []
                    ),
                    "perf_raw": {event: None for event in PERF_EVENTS},
                    "throughput": None,
                }
                for index in range(reps)
            ]
        rep_results = []
        n_exec_fail = 0
        for index, (captured, local_returncodes, perf_raw) in enumerate(
                captured_reps):
            tps = None
            try:
                metrics, counters, wall = captured.open()
            except (RuntimeError, subprocess.TimeoutExpired) as exc:
                if rep_observations is not None:
                    rep_observations[index]["execution_failure"] = True
                if require_all_reps:
                    raise RuntimeError(
                        f"rep{index}/{reps} fatal at records={records} "
                        f"threads={threads}: {type(exc).__name__}: "
                        f"{str(exc)[:200]}") from exc
                n_exec_fail += 1
                pt.notes.append(
                    f"rep{index} failed: {type(exc).__name__}: {str(exc)[:200]}"
                )
                continue
            except Exception as exc:
                if rep_observations is None:
                    raise
                rep_observations[index]["execution_failure"] = True
                if require_all_reps:
                    raise RuntimeError(
                        f"rep{index}/{reps} fatal at records={records} "
                        f"threads={threads}: {type(exc).__name__}: "
                        f"{str(exc)[:200]}") from exc
                n_exec_fail += 1
                pt.notes.append(
                    f"rep{index} failed: {type(exc).__name__}: {str(exc)[:200]}"
                )
                continue
            finally:
                if rep_observations is not None:
                    if rep_returncodes is not None and local_returncodes:
                        rep_returncodes.extend(local_returncodes)
                    missing, status = _counter_observation(
                        perf_raw, use_perf=use_perf,
                    )
                    rep_observations[index] = {
                        "rep_index": index,
                        "returncode": (
                            local_returncodes[0]
                            if local_returncodes
                            and len(local_returncodes) == 1
                            and type(local_returncodes[0]) is int else None
                        ),
                        "execution_failure": rep_observations[index][
                            "execution_failure"
                        ],
                        "counter_status": status,
                        "missing_perf_events": missing,
                        "perf_raw": dict(perf_raw),
                        "throughput": tps,
                    }
            tps = throughput_tps(metrics)
            if rep_observations is not None:
                rep_observations[index]["throughput"] = tps
            if record_rep_integer_counters:
                aborts, commits = integer_abort_commit_counts(metrics)
                rep_observations[index].update({
                    "abort_counts_": aborts, "commit_counts_": commits,
                })
            maxrss = _maxrss_kb(metrics)
            if require_complete_metrics:
                missing = []
                if tps is None:
                    missing.append("throughput")
                for name in (
                        "llc_load_misses", "llc_loads",
                        "instructions", "cycles"):
                    if getattr(counters, name) is None:
                        missing.append(name)
                if maxrss is None:
                    missing.append("maxrss")
                if missing:
                    raise RuntimeError(
                        f"rep{index}/{reps} missing required metrics "
                        f"at records={records}: " + ",".join(missing))
            if tps is not None:
                pt.throughputs.append(tps)
            rep_results.append((
                tps, counters, wall, maxrss,
                parse_abort_rate(metrics), parse_latency_ns(metrics),
            ))
        if n_exec_fail:
            pt.notes.append(f"{n_exec_fail}/{reps} reps failed to execute")
        if not rep_results:
            raise RuntimeError(
                f"all {reps} reps failed at records={records} threads={threads}: "
                + " | ".join(pt.notes))

        valid = [result for result in rep_results if result[0] is not None]
        rep = None
        if valid:
            throughputs = sorted(result[0] for result in valid)
            median = throughputs[len(throughputs) // 2]
            rep = min(valid, key=lambda result: abs(result[0] - median))
        elif rep_results:
            rep = rep_results[-1]
        if rep is not None:
            (pt.counters, pt.walltime_s, pt.maxrss_kb,
             pt.abort_rate, pt.latency_ns) = rep[1], rep[2], rep[3], rep[4], rep[5]
        if rep_observations is not None:
            pt.rep_observations = [
                dict(observation) for observation in rep_observations
            ]
        return pt

    return _seal_captured_output(
        open_measurement_point, launch_failures=launch_failures,
    )


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
                  rep_returncodes: Optional[List[int]] = None,
                  rep_observations: Optional[List[Dict[str, object]]] = None, *,
                  record_rep_integer_counters: bool = False,
                  rep_timestamps: Optional[List[Dict[str, int]]] = None,
                  use_perf: bool = True,
                  holdout_observation_admission: Optional[
                      HoldoutObservationAdmission
                  ] = None,
                  calibration_observation_capability: Optional[
                      CalibrationObservationCapability
                  ] = None,
                  calibration_observation_phase: Optional[str] = None) -> ScalePoint:
    """1 measurement point with the historical per-rep observable order.

    Each rep is spawned, decoded, parsed, and cleaned before the next rep is
    started.  The deferred floor-only API is intentionally separate so this
    public compatibility surface retains its value, exception, sink, cleanup,
    and fail-fast behavior.
    """
    if record_rep_integer_counters and rep_observations is None:
        rep_observations = []
    if settle_first:
        settle()

    base_flags = [
        f"-thread_num={threads}",
        f"-ycsb_tuple_num={records}",
        f"-extime={extime}",
        f"-clocks_per_us={clocks_per_us}",
    ]
    for key, value in (workload or {}).items():
        base_flags.append(f"-{key}={value}")

    point = ScalePoint(
        records=records,
        threads=threads,
        run_cmd=_point_repro_command(
            binary, base_flags, numactl, use_perf,
        ),
    )
    if rep_observations is not None:
        rep_observations[:] = [
            {
                "rep_index": index,
                "returncode": None,
                "execution_failure": False,
                "counter_status": "unknown",
                "missing_perf_events": (
                    list(PERF_EVENTS) if use_perf else []
                ),
                "perf_raw": {event: None for event in PERF_EVENTS},
                "throughput": None,
            }
            for index in range(reps)
        ]
    rep_results = []
    n_exec_fail = 0
    if rep_timestamps is not None:
        rep_timestamps[:] = []
    for index in range(reps):
        local_returncodes: Optional[List[int]] = (
            [] if rep_observations is not None else None
        )
        perf_raw: Dict[str, Optional[int]] = {
            event: None for event in PERF_EVENTS
        }
        throughput = None
        started_at_ns = time.time_ns()
        try:
            run_kwargs = {
                "numactl": numactl,
                "extra_env": extra_env,
                "timeout_s": timeout_s,
            }
            # Preserve the historical monkeypatch seam and kwarg shape.
            if (require_all_reps or require_complete_metrics
                    or rep_observations is not None):
                run_kwargs["strict_returncode"] = require_all_reps
                run_kwargs["subprocess_runner"] = subprocess_runner
            elif subprocess_runner is not subprocess.run:
                run_kwargs["subprocess_runner"] = subprocess_runner
            if rep_observations is not None:
                run_kwargs["rep_returncodes"] = local_returncodes
                run_kwargs["perf_raw_sink"] = perf_raw
            elif rep_returncodes is not None:
                run_kwargs["rep_returncodes"] = rep_returncodes
            if not use_perf:
                run_kwargs["use_perf"] = False
            if holdout_observation_admission is not None:
                run_kwargs["holdout_observation_admission"] = (
                    holdout_observation_admission
                )
            if calibration_observation_capability is not None:
                run_kwargs["calibration_observation_capability"] = (
                    calibration_observation_capability
                )
                run_kwargs["calibration_observation_phase"] = (
                    calibration_observation_phase
                )
            metrics, counters, wall = run_once(
                binary, base_flags, **run_kwargs,
            )
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            if rep_observations is not None:
                rep_observations[index]["execution_failure"] = True
            if require_all_reps:
                raise RuntimeError(
                    f"rep{index}/{reps} fatal at records={records} "
                    f"threads={threads}: {type(exc).__name__}: "
                    f"{str(exc)[:200]}"
                ) from exc
            n_exec_fail += 1
            point.notes.append(
                f"rep{index} failed: {type(exc).__name__}: {str(exc)[:200]}"
            )
            continue
        except Exception as exc:
            if rep_observations is None:
                raise
            rep_observations[index]["execution_failure"] = True
            if require_all_reps:
                raise RuntimeError(
                    f"rep{index}/{reps} fatal at records={records} "
                    f"threads={threads}: {type(exc).__name__}: "
                    f"{str(exc)[:200]}"
                ) from exc
            n_exec_fail += 1
            point.notes.append(
                f"rep{index} failed: {type(exc).__name__}: {str(exc)[:200]}"
            )
            continue
        finally:
            finished_at_ns = time.time_ns()
            if rep_timestamps is not None:
                rep_timestamps.append({
                    "rep_index": index,
                    "started_at_ns": started_at_ns,
                    "finished_at_ns": finished_at_ns,
                })
            if rep_observations is not None:
                if rep_returncodes is not None and local_returncodes:
                    rep_returncodes.extend(local_returncodes)
                missing, status = _counter_observation(
                    perf_raw, use_perf=use_perf,
                )
                rep_observations[index] = {
                    "rep_index": index,
                    "returncode": (
                        local_returncodes[0]
                        if local_returncodes
                        and len(local_returncodes) == 1
                        and type(local_returncodes[0]) is int else None
                    ),
                    "execution_failure": rep_observations[index][
                        "execution_failure"
                    ],
                    "counter_status": status,
                    "missing_perf_events": missing,
                    "perf_raw": dict(perf_raw),
                    "throughput": throughput,
                }
        throughput = throughput_tps(metrics)
        if rep_observations is not None:
            rep_observations[index]["throughput"] = throughput
        if record_rep_integer_counters:
            aborts, commits = integer_abort_commit_counts(metrics)
            rep_observations[index].update({
                "abort_counts_": aborts, "commit_counts_": commits,
            })
        maxrss = _maxrss_kb(metrics)
        if require_complete_metrics:
            missing = []
            if throughput is None:
                missing.append("throughput")
            for name in (
                    "llc_load_misses", "llc_loads",
                    "instructions", "cycles"):
                if getattr(counters, name) is None:
                    missing.append(name)
            if maxrss is None:
                missing.append("maxrss")
            if missing:
                raise RuntimeError(
                    f"rep{index}/{reps} missing required metrics "
                    f"at records={records}: " + ",".join(missing)
                )
        if throughput is not None:
            point.throughputs.append(throughput)
        rep_results.append((
            throughput,
            counters,
            wall,
            maxrss,
            parse_abort_rate(metrics),
            parse_latency_ns(metrics),
        ))
    if n_exec_fail:
        point.notes.append(f"{n_exec_fail}/{reps} reps failed to execute")
    if not rep_results:
        raise RuntimeError(
            f"all {reps} reps failed at records={records} threads={threads}: "
            + " | ".join(point.notes)
        )

    valid = [result for result in rep_results if result[0] is not None]
    representative = None
    if valid:
        throughputs = sorted(result[0] for result in valid)
        median = throughputs[len(throughputs) // 2]
        representative = min(
            valid, key=lambda result: abs(result[0] - median),
        )
    elif rep_results:
        representative = rep_results[-1]
    if representative is not None:
        (
            point.counters,
            point.walltime_s,
            point.maxrss_kb,
            point.abort_rate,
            point.latency_ns,
        ) = representative[1:]
    if rep_observations is not None:
        point.rep_observations = [
            dict(observation) for observation in rep_observations
        ]
    return point
