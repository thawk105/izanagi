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
import hmac
import math
import json
import os
import signal
from pathlib import Path
import re
import secrets
import shlex
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, NamedTuple, Optional, Sequence, Tuple

from ..calibrator import perf_preflight as _perf_preflight                # noqa: E402
from ..calibrator.analyze import noise_floor                     # noqa: E402
from ..calibrator.runner import (CompetingBenchProbeError,        # noqa: E402
                               competing_bench_pids, measure_point, settle)
from ..calibrator.stability import remeasure_until_stable         # noqa: E402
from ..holdout_observation import HoldoutObservationAdmission     # noqa: E402
from ..verifier import (                                        # noqa: E402
    CAMPAIGN_WAL_SINK,
    QUALIFICATION_SINK,
    issue_commit_receipt,
    verify_trace_dir_with_capability,
)
from ..verifier.core import result_to_dict_v3                 # noqa: E402
from ..verifier.commit_receipt import (                          # noqa: E402
    admit_remote_verification_receipt,
    campaign_lock_sha256_or_absent,
    serialize_remote_verification_receipt,
)
from ..verifier.parse import ParseError                           # noqa: E402
from ..verifier.model import (                                   # noqa: E402
    VerifyResult,
    capture_compiled_protocol_source_snapshot,
)

from . import (buildcache, campaign_lock as _campaign_lock,
               env_contract as _env_contract, execution_guard, ident,
               source_digest, wal)  # noqa: E402
from .build_admission import (  # noqa: E402
    BuildAdmission,
    BuildAdmissionError,
    BuildRunContext,
    GeneratorId,
    GeneratorReceipt,
    ReviewReceipt,
    derive_build_admission,
    require_build_admission,
)
from .buildcache import (_resolve_site as _buildcache_resolve_site,  # noqa: E402
                         require_heavy_work_site)
from .layout import CampaignLayout                              # noqa: E402
from .lock import bench_lock                                    # noqa: E402
from .env_contract import ExecutionEnvironmentContract          # noqa: E402
from .axis_trigger_gating import (  # noqa: E402
    MARKER_ID as TRIGGER_MARKER_ID,
    PREDICATE_HOLE_INDENT as TRIGGER_PREDICATE_HOLE_INDENT,
    SOURCE_REL as TRIGGER_SOURCE_REL,
)
from .diff_quarantine import parse_template_file                # noqa: E402
from .model import (COMMIT_CONTRACT_SHA256_KEY, Genome, STAGE_ABORT,
                    STAGE_BENCH_DONE,                           # noqa: E402
                    STAGE_BUILD_DONE, STAGE_BUILD_START, STAGE_COMMIT,
                    STAGE_VERIFY_DONE)
from .reflux_ir import TriggerGateIR, emit_predicate             # noqa: E402
from .trigger_gate_binding import SourceBinding, TriggerGateBinding
from .source_digest import (                                     # noqa: E402
    SourceEvidence,
    _sanitized_git_env,
    serialize_compiled_protocol_source_snapshot,
)

_DEFAULT_CXX = buildcache.DEFAULT_CXX
_compilers_for_current_site = buildcache.compilers_for_current_site

BuildCapability = GeneratorReceipt | ReviewReceipt | None
AdmissionCapabilityResolver = Callable[[SourceEvidence], BuildCapability]


_TRIGGER_PREDICATE_REJECTION = (
    "trigger binding predicate が materialized source と不一致"
)


def _require_materialized_trigger_predicate(
        evidence: SourceEvidence, binding: TriggerGateBinding,
) -> None:
    """Bind one candidate mask to the exact one-line materialized source hole."""
    source_path = os.path.join(evidence.source_root, TRIGGER_SOURCE_REL)
    try:
        marker = parse_template_file(source_path, TRIGGER_MARKER_ID)
        with open(source_path, "rb") as stream:
            raw_source = stream.read()
        raw_lines = []
        line_start = 0
        for newline in re.finditer(br"\r\n?|\n", raw_source):
            payload = raw_source[line_start:newline.start()]
            # Keep CR in the physical-line payload even though it delimits a
            # line for the parser's universal-newline line numbering.
            if newline.group(0).startswith(b"\r"):
                payload += b"\r"
            raw_lines.append(payload)
            line_start = newline.end()
        raw_lines.append(raw_source[line_start:])
        hole_lines = None if marker is None else tuple(
            raw_lines[marker.hole_first - 1:marker.hole_last]
        )
        expected = (
            TRIGGER_PREDICATE_HOLE_INDENT
            + emit_predicate(TriggerGateIR(binding.mask))
        ).encode("utf-8")
    except (OSError, UnicodeError, TypeError, ValueError):
        raise BuildAdmissionError(_TRIGGER_PREDICATE_REJECTION) from None
    if (hole_lines is None or len(hole_lines) != 1
            or hole_lines[0] != expected):
        raise BuildAdmissionError(_TRIGGER_PREDICATE_REJECTION) from None


def variant_id(genome: Genome, src_token: str = source_digest.STOCK) -> str:
    """genome 正準表現 + コード差 (src_token, D23) の安定ハッシュ = variant の id (WAL キー)。

    stock (working-tree==HEAD baseline) は src を省き旧 id を温存 (後方互換: silo 8 genome の
    既存 WAL キーが不変)。coder が EVOLVE-BLOCK を書き換えた variant だけ src 込みの新 id。"""
    src = "" if src_token == source_digest.STOCK else f"|src={src_token}"
    return hashlib.sha256(f"{genome.canonical()}{src}".encode("utf-8")).hexdigest()[:12]


@dataclass
class CorrectnessWorkload:
    """verify 用の小規模・高 contention workload (trace を verifier に回せる規模)。"""
    flags: Dict[str, str] = field(default_factory=lambda: {
        "ycsb_tuple_num": "200", "ycsb_zipf_skew": "0.9", "ycsb_rratio": "50",
        "ycsb_rmw": "true", "ycsb_max_ope": "5", "thread_num": "4", "extime": "1"})
    reps: int = 1


# --- S2 verify 構成 (D36 決定1/決定3: perf 代表 workload と完全同一、extime=3 で
# gate 3 点 all_pass — 正本 output/env/linux-baremetal/calibration/
# s2_verify_t48_skew0p9_rr50_rmw0.json)。s2_verify_calibration.py もこの定数を
# import する (二重定義によるドリフト防止)。 ---
S2_FLAGS: Dict[str, str] = {
    "ycsb_tuple_num": "1000000", "ycsb_zipf_skew": "0.9", "ycsb_rratio": "50",
    "ycsb_rmw": "false", "ycsb_max_ope": "10", "thread_num": "48",
}
S2_EXTIME = "3"
LEGACY_TAG = "legacy"
S2_TAG = "s2"
# CampaignConfig.search_config のキー (D36 決定4-1): S2 on/off はここに焼き込み
# campaign_id に反映する (別 campaign になり WAL terminal skip の汚染を防ぐ)。
SEARCH_CONFIG_VERIFY_KEY = "verify"
VERIFY_LEGACY_PLUS_S2 = f"{LEGACY_TAG}+{S2_TAG}"
PERFORMANCE_TAG = "performance"
VERIFY_LEGACY_PLUS_PERFORMANCE = f"{LEGACY_TAG}+{PERFORMANCE_TAG}"
# bench-first screening の terminal abort reason。WAL writer/reader が共有する暗黙 API。
SCREEN_REJECTION_REASON = "screen-slower-than-floor"


def s2_correctness_workload() -> CorrectnessWorkload:
    """S2 verify 構成 (D36 決定3 gate all_pass の確定値)。evaluate() の
    extra_correctness に渡す (search_config[SEARCH_CONFIG_VERIFY_KEY] ==
    VERIFY_LEGACY_PLUS_S2 のとき、loop.run_campaign が組み立てる)。"""
    return CorrectnessWorkload(flags={**S2_FLAGS, "extime": S2_EXTIME})


@dataclass
class PerfConfig:
    """bench 用の確定 calibration (records/threads/workload)。"""
    records: int
    threads: int
    workload: Dict[str, str] = field(default_factory=dict)
    extime: int = 3
    reps: int = 5


def performance_correctness_workload(perf: PerfConfig) -> CorrectnessWorkload:
    """Build an exact full-scale trace workload from one performance config.

    The constructor is intentionally generic and contains no A-2 workload
    numbers.  It rejects ambiguous or widened workload maps before callers can
    authorize a measurement or create campaign state.
    """
    if type(perf) is not PerfConfig:
        raise TypeError("perf must be an exact PerfConfig")
    for name, value in (
        ("records", perf.records), ("threads", perf.threads),
        ("extime", perf.extime), ("reps", perf.reps),
    ):
        if type(value) is not int or value <= 0:
            raise ValueError(f"PerfConfig.{name} must be a positive exact integer")
    required = {
        "ycsb_zipf_skew", "ycsb_rratio", "ycsb_rmw", "ycsb_max_ope",
    }
    if type(perf.workload) is not dict or set(perf.workload) != required:
        raise ValueError("PerfConfig.workload must have the exact YCSB workload keys")
    if not all(type(value) is str and value for value in perf.workload.values()):
        raise ValueError("PerfConfig workload values must be nonempty strings")
    return CorrectnessWorkload(
        flags={
            "ycsb_tuple_num": str(perf.records),
            "thread_num": str(perf.threads),
            **perf.workload,
            "extime": str(perf.extime),
        },
        reps=perf.reps,
    )


_QUALIFICATION_POLICY_TOKEN = object()


@dataclass(frozen=True, init=False)
class QualificationPipelinePolicy:
    """Exact T-126 opt-in for the shared evaluation seam.

    This separates full-scale isolation from the launch prefix, supplies
    bounded subprocess timeouts, and routes events to a qualification-only
    sink.  It grants no formal authority.
    """

    event_sink: object
    member_cap_s: int
    build_timeout_s: int
    bench_timeout_s: float
    require_settled: bool

    def __init__(self, *, _token: object, event_sink: object):
        if _token is not _QUALIFICATION_POLICY_TOKEN:
            raise TypeError("use QualificationPipelinePolicy.t126_pegasus()")
        from ..qualification.artifacts import QualificationEventSink
        if type(event_sink) is not QualificationEventSink:
            raise TypeError(
                "qualification event_sink must be exact QualificationEventSink")
        event_sink.assert_pipeline_binding(event_sink.layout)
        object.__setattr__(self, "event_sink", event_sink)
        object.__setattr__(self, "member_cap_s", 900)
        object.__setattr__(self, "build_timeout_s", 900)
        object.__setattr__(self, "bench_timeout_s", 120.0)
        object.__setattr__(self, "require_settled", True)

    @classmethod
    def t126_pegasus(cls, event_sink: object) -> "QualificationPipelinePolicy":
        return cls(_token=_QUALIFICATION_POLICY_TOKEN, event_sink=event_sink)


@dataclass(frozen=True, kw_only=True)
class ScreeningConfig:
    """bench-first screening の固定方針と、driver が再アンカーする基準点。"""
    baseline_tps: float
    baseline_ref: str
    baseline_measured_at: float
    floor: float
    k: float = 1.5
    baseline_abort_rate: float
    high_abort_factor: float = 2.0
    reanchor_threshold_s: float = 1800.0

    def __post_init__(self) -> None:
        if type(self.baseline_ref) is not str or not self.baseline_ref:
            raise ValueError("baseline_ref は non-empty exact str でなければならない")
        numeric_fields = (
            "baseline_tps", "baseline_measured_at", "floor", "k",
            "baseline_abort_rate", "high_abort_factor", "reanchor_threshold_s",
        )
        for name in numeric_fields:
            if type(getattr(self, name)) not in (int, float):
                raise ValueError(
                    f"{name} は bool でない exact int/float でなければならない")
        checks = (
            (self.k >= 1.5, "k は 1.5 以上でなければならない"),
            (self.baseline_tps > 0, "baseline_tps は正でなければならない"),
            (0 < self.floor < 1, "floor は 0 より大きく 1 未満でなければならない"),
            (self.baseline_abort_rate >= 0,
             "baseline_abort_rate は 0 以上でなければならない"),
            (self.high_abort_factor >= 1.0,
             "high_abort_factor は 1.0 以上でなければならない"),
            (self.reanchor_threshold_s > 0,
             "reanchor_threshold_s は正でなければならない"),
        )
        for valid, message in checks:
            if not valid:
                raise ValueError(message)


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
    build_attempt_id: str = ""
    verify_result: Optional[VerifyResult] = None


# ccbench 正常終了時の集計行 (common/result.cc displayAbortCounts、displayAllResult が
# 無条件に出す)。^ アンカー必須 — batch_abort_counts_ 行を誤マッチさせない。
_ABORT_COUNTS_RE = re.compile(r"(?m)^abort_counts_:\s*(\d+)\s*$")


def _parse_abort_counts(stdout: str) -> Optional[int]:
    """ccbench stdout から総 abort 数を読む。行が無ければ None (呼び手が fails-closed に倒す)。"""
    m = _ABORT_COUNTS_RE.search(stdout or "")
    return int(m.group(1)) if m else None


def _parse_witness_counter(stdout: str, label: str) -> Optional[int]:
    """CCBench 集計 counter を一意な非負整数行からだけ読む。

    `parse_bench_stdout` は重複 label を last-wins で潰すため、正しさ witness の
    権威には使わない。`#` 前置行はコメントとして除外し、同一 label が 0 行または
    2 行以上、値が十進非負整数でない場合はすべて None に倒す。
    """
    values: List[str] = []
    for line in (stdout or "").splitlines():
        if line.startswith("#"):
            continue
        key, separator, raw = line.partition(":")
        if separator and key == label:
            values.append(raw.strip())
    if len(values) != 1 or re.fullmatch(r"[0-9]+", values[0]) is None:
        return None
    return int(values[0])


def _parse_commit_witness(stdout: str) -> Tuple[Optional[int], Optional[int]]:
    return (
        _parse_witness_counter(stdout, "commit_counts_"),
        _parse_witness_counter(stdout, "batch_commit_counts_"),
    )


# trace run の timeout。S2 verify 構成の gate2 run timeout (120s) と同値に揃えてある
# (s2_verify_calibration.py)。abort payload (trace-timeout) にも記録する — 「どの上限で
# 打ち切られたか」が無いと liveness-red の次手入力が空になる (規律3)。
TRACE_TIMEOUT_S = 120.0


class _TraceRunResult(NamedTuple):
    """trace run と同じ stdout/trace_dir から得た正しさ入力。"""
    trace_c_lines: int
    returncode: int
    abort_counts: Optional[int]
    commit_count_witness: Optional[int]
    batch_commit_count_witness: Optional[int]


class _TraceDirNotEmpty(ValueError):
    def __init__(self, paths: Sequence[str]):
        self.paths = tuple(paths)
        super().__init__("trace_dir に既存 trace_*.log がある")


class _TraceDirUnavailable(ValueError):
    def __init__(self, path: str, reason: str):
        self.path = path
        self.reason = reason
        super().__init__(f"trace_dir を検査できない ({reason}): {path}")


class _TraceWitnessUnsupportedWorkload(ValueError):
    def __init__(self, binary: str):
        self.workload = os.path.basename(binary)
        super().__init__(f"commit witness 未対応 workload: {self.workload}")


def _exc_summary(e: BaseException, limit: int = 1000) -> str:
    """例外由来 abort の WAL payload に載せる要約 (D50 教訓: reason だけの WAL では
    build-error の現地調査を一次資料から始められず、kill 残骸毒の特定が遅延した)。
    ビルドログ等の長い出力は本命 (error: 行) が末尾に出やすいので末尾優先で畳む。
    limit は 200 超が前提 (先頭 200 + 末尾 limit-200 の算術が退化する。既定 1000 のみで使用)。"""
    s = f"{type(e).__name__}: {e}"
    if len(s) <= limit:
        return s
    return s[:200] + " …[中略]… " + s[-(limit - 200):]


def _resolve_site(site: Optional[str]) -> str:
    """buildcache と同じ site seam。テストはこの関数だけを差し替える。"""
    return _buildcache_resolve_site(site)


def _require_measurement_site(what: str) -> str:
    """計測 producer/COMMIT を login と suspect で拒否する。"""
    return require_heavy_work_site(_resolve_site(None), what)


def _run_trace(binary: str, trace_dir: str, flags: Dict[str, str],
               clocks_per_us: int, timeout_s: float = TRACE_TIMEOUT_S,
               numactl: Optional[Sequence[str]] = None) -> _TraceRunResult:
    """trace-enabled binary を回し IZANAGI_TRACE_DIR に trace を吐く。

    返り値は `_TraceRunResult`。**呼び手は returncode を必ず検査する** —
    異常終了した run の部分トレースを certified にしないため (規律2)。aborts は stdout の
    `abort_counts_:` 集計 (完了条件「verify 中に合成枝 = abort-path が実行された証拠」の
    材料, phase3.md)。パース不能なら None — 呼び手が reject する (空振り認証の検査可能性を
    落としたまま緑を出さない)。numactl (D36 決定4-4): S2 相当の全規模 run はメモリ配置を
    bench と揃える (既定 legacy はメモリ配置に鈍感な小規模ゆえ None のまま)。"""
    _require_measurement_site("campaign trace 実行")
    if not os.path.exists(trace_dir):
        raise _TraceDirUnavailable(trace_dir, "missing")
    if not os.path.isdir(trace_dir):
        raise _TraceDirUnavailable(trace_dir, "not-directory")
    try:
        existing_traces = sorted(
            fn for fn in os.listdir(trace_dir)
            if fn.startswith("trace_") and fn.endswith(".log")
        )
    except OSError as e:
        raise _TraceDirUnavailable(trace_dir, type(e).__name__) from e
    if existing_traces:
        raise _TraceDirNotEmpty(existing_traces)
    name = os.path.basename(binary)
    # YCSB は既存の commit witness 対象。TPC-C 段 1 は設計 §3.5 の
    # CCBench 側 commit 計数修正を前提に、57:43 のみ trace を許す。
    # TPC-C の v3 schema は trace の verifier 後に要求する。
    tpcc_stage1 = (
        name.startswith("tpcc_")
        and flags.get("tpcc_perc_payment") == "43"
        and flags.get("tpcc_perc_order_status") == "0"
        and flags.get("tpcc_perc_delivery") == "0"
        and flags.get("tpcc_perc_stock_level") == "0"
    )
    if not (name.startswith("ycsb_") or tpcc_stage1):
        raise _TraceWitnessUnsupportedWorkload(binary)
    args = (list(numactl) if numactl else []) + [binary] \
        + [f"-{k}={v}" for k, v in flags.items()] \
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
    commit_witness, batch_witness = _parse_commit_witness(proc.stdout)
    return _TraceRunResult(
        trace_c_lines=n,
        returncode=proc.returncode,
        abort_counts=_parse_abort_counts(proc.stdout),
        commit_count_witness=commit_witness,
        batch_commit_count_witness=batch_witness,
    )


@dataclass(frozen=True)
class _RepetitionAbortOutcome:
    """WAL-independent projection of one existing verification abort."""

    reason: str
    message: str
    detail: Dict[str, Any]
    workload_tag: str


@dataclass(frozen=True)
class _RepetitionExecutionOutcome:
    """One repetition result before the owning process writes its WAL."""

    verify_payload: Optional[Dict[str, Any]] = None
    verification_capability: Optional[object] = None
    abort: Optional[_RepetitionAbortOutcome] = None
    verify_result: Optional[VerifyResult] = None
    commit_count_witness: Optional[int] = None


def _collect_verification_trace(
        binary: str, trace_dir: str, flags: Mapping[str, str],
        clocks_per_us: int, *, timeout_s: float,
        numactl: Optional[Sequence[str]], receipt_workload_tag: str,
        trace_runner: Callable[..., _TraceRunResult],
) -> tuple[Optional[_TraceRunResult], Optional[_RepetitionExecutionOutcome]]:
    """Collect and validate a trace before any concurrent verifier starts."""
    run_trace = trace_runner
    archive_witness = None

    def abort(reason: str, message: str,
              detail: Optional[Dict[str, Any]] = None) -> _RepetitionExecutionOutcome:
        return _RepetitionExecutionOutcome(abort=_RepetitionAbortOutcome(
            reason, message, dict(detail or {}), receipt_workload_tag,
        ), commit_count_witness=archive_witness)

    try:
        trace_result = run_trace(
            binary, trace_dir, dict(flags), clocks_per_us,
            timeout_s=timeout_s, numactl=numactl,
        )
    except subprocess.TimeoutExpired:
        return None, abort(
            "trace-timeout",
            f"trace 取得タイムアウト ({receipt_workload_tag}) → reject",
            {"timeout_s": timeout_s},
        )
    except _TraceDirNotEmpty as exc:
        return None, abort(
            "trace-no-commit-witness",
            f"trace_dir に既存 trace がある ({receipt_workload_tag}) → "
            "witness を帰属できず reject",
            {
                "commit_witness": {
                    "commit_counts": None,
                    "batch_commit_counts": None,
                },
                "preexisting_trace_files": list(exc.paths),
            },
        )
    except _TraceDirUnavailable as exc:
        return None, abort(
            "trace-no-commit-witness",
            f"trace_dir を検査できない ({exc.reason}, {receipt_workload_tag}) → "
            "witness を帰属できず reject",
            {
                "commit_witness": {
                    "commit_counts": None,
                    "batch_commit_counts": None,
                },
                "trace_dir": exc.path,
                "trace_dir_error": exc.reason,
            },
        )
    except _TraceWitnessUnsupportedWorkload as exc:
        return None, abort(
            "trace-witness-unsupported-workload",
            f"commit witness 未対応 workload ({exc.workload}, "
            f"{receipt_workload_tag}) → reject",
            {
                "commit_witness": {
                    "commit_counts": None,
                    "batch_commit_counts": None,
                },
                "binary_workload": exc.workload,
            },
        )

    ncommit = trace_result.trace_c_lines
    rc = trace_result.returncode
    aborts = trace_result.abort_counts
    commit_witness = {
        "commit_counts": trace_result.commit_count_witness,
        "batch_commit_counts": trace_result.batch_commit_count_witness,
    }
    if rc != 0:
        return None, abort(
            "trace-run-nonzero-exit",
            f"trace バイナリ異常終了 ({receipt_workload_tag}) rc={rc} → reject",
            {"rc": rc, "commits": ncommit},
        )
    if ncommit == 0:
        return None, abort(
            "trace-empty",
            f"空トレース ({receipt_workload_tag}, commit 0) → 検証不能 reject",
            {"commits": 0, "aborts": aborts},
        )
    if aborts is None:
        return None, abort(
            "trace-no-abort-counts",
            f"ccbench stdout に abort_counts_ 集計が無い "
            f"({receipt_workload_tag}) → 空振り認証を検査できず reject",
            {"commits": ncommit},
        )
    if (trace_result.commit_count_witness is None
            or trace_result.batch_commit_count_witness is None):
        return None, abort(
            "trace-no-commit-witness",
            f"ccbench stdout の commit witness が欠落または不正 "
            f"({receipt_workload_tag}) → reject",
            {"commits": ncommit, "commit_witness": commit_witness},
        )
    if trace_result.batch_commit_count_witness != 0:
        return None, abort(
            "trace-batch-commits-unattributed",
            f"batch commit を trace C 行へ帰属できない "
            f"({receipt_workload_tag}) → reject",
            {"commits": ncommit, "commit_witness": commit_witness},
        )
    return trace_result, None


def _execute_verification_repetition(
        binary: str, trace_dir: str, flags: Mapping[str, str],
        clocks_per_us: int, *, timeout_s: float,
        numactl: Optional[Sequence[str]], genome: Genome,
        source_evidence: SourceEvidence, build_admission: BuildAdmission,
        receipt_sink_kind: str, receipt_lock_identity_sha256: str,
        receipt_variant: str, receipt_operation_identity: str,
        receipt_workload_tag: str, build_attempt_id: str,
        trace_binary_sha256: str, include_qualification_evidence: bool,
        payload_binary: Optional[str] = None,
        trace_runner: Optional[Callable[..., _TraceRunResult]] = None,
        verifier_runner: Optional[Callable[..., tuple[object, object]]] = None,
        collected_trace_result: Optional[_TraceRunResult] = None,
) -> _RepetitionExecutionOutcome:
    """Run the existing trace witness and verifier gates without WAL access.

    The caller owns trace-directory creation/removal and projects this outcome
    to its local sink.  Optional callables are narrow test seams; production
    resolves the live module bindings so existing pipeline patch fixtures keep
    exercising this executor.
    """
    run_trace = _run_trace if trace_runner is None else trace_runner
    run_verifier = (
        verify_trace_dir_with_capability
        if verifier_runner is None else verifier_runner
    )
    archive_witness = None

    def abort(
            reason: str, message: str, detail: Optional[Dict[str, Any]] = None,
    ) -> _RepetitionExecutionOutcome:
        return _RepetitionExecutionOutcome(abort=_RepetitionAbortOutcome(
            reason=reason,
            message=message,
            detail=dict(detail or {}),
            workload_tag=receipt_workload_tag,
        ), commit_count_witness=archive_witness)

    if collected_trace_result is None:
        trace_result, trace_abort = _collect_verification_trace(
            binary, trace_dir, flags, clocks_per_us, timeout_s=timeout_s,
            numactl=numactl, receipt_workload_tag=receipt_workload_tag,
            trace_runner=run_trace,
        )
        if trace_abort is not None:
            return trace_abort
    else:
        trace_result = collected_trace_result
    assert trace_result is not None
    ncommit = trace_result.trace_c_lines
    aborts = trace_result.abort_counts
    commit_witness = {
        "commit_counts": trace_result.commit_count_witness,
        "batch_commit_counts": trace_result.batch_commit_count_witness,
    }
    archive_witness = trace_result.commit_count_witness
    try:
        verify_result, verification_capability = run_verifier(
            trace_dir,
            expected_commits=trace_result.commit_count_witness,
            genome=genome,
            source_evidence=source_evidence,
            build_admission=build_admission,
            receipt_sink_kind=receipt_sink_kind,
            receipt_lock_identity_sha256=receipt_lock_identity_sha256,
            receipt_variant=receipt_variant,
            receipt_operation_identity=receipt_operation_identity,
            receipt_workload_tag=receipt_workload_tag,
        )
    except ParseError as exc:
        return abort(
            "trace-parse-error",
            f"trace パース不能 ({receipt_workload_tag}) → reject ({exc})",
            {"error": _exc_summary(exc)},
        )

    if (os.path.basename(binary).startswith("tpcc_")
            and verify_result.integrity.existence_violation_details is None):
        return abort(
            "trace-witness-unsupported-workload",
            f"v3 trace でない TPC-C workload ({receipt_workload_tag}) → reject",
            {"trace_schema": "v2"},
        )

    verify_payload: Dict[str, Any] = {
        "build_attempt_id": build_attempt_id,
        "verdict": verify_result.verdict,
        "certified": verify_result.certified,
        "commits": ncommit,
        "aborts": aborts,
        "commit_witness": commit_witness,
        "anomalies": len(verify_result.anomalies),
        "workload": {"tag": receipt_workload_tag},
        "proof_surfaces": verify_result.integrity.proof_surfaces.as_record(),
    }
    if include_qualification_evidence:
        verify_payload.update({
            "argv": (
                list(numactl or ())
                + [payload_binary or binary]
                + [f"-{key}={value}" for key, value in flags.items()]
                + [f"-clocks_per_us={clocks_per_us}"]
            ),
            "binary_sha256": trace_binary_sha256,
        })
    rejected = None
    if not verify_result.certified:
        diagnostic = result_to_dict_v3(verify_result)
        diagnostic.pop("trace_dir", None)
        rejected = _RepetitionAbortOutcome(
            reason=verify_result.verdict,
            message=(
                f"正しさゲート不通過 ({verify_result.verdict}, "
                f"{receipt_workload_tag}) → reject"
            ),
            detail={"verify": diagnostic},
            workload_tag=receipt_workload_tag,
        )
    return _RepetitionExecutionOutcome(
        verify_payload=verify_payload,
        verification_capability=verification_capability,
        abort=rejected,
        verify_result=verify_result,
        commit_count_witness=archive_witness,
    )


_VERIFY_FANOUT_TASK_SCHEMA = "verify-fanout-task/v1"
_VERIFY_FANOUT_RESULT_SCHEMA = "verify-fanout-result/v1"
_VERIFY_FANOUT_COMPONENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")


def _json_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _write_create_only_json(path: str, value: object) -> None:
    """Publish one canonical JSON object without replacing prior evidence."""
    encoded = _canonical_json_bytes(value) + b"\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        offset = 0
        while offset < len(encoded):
            written = os.write(descriptor, encoded[offset:])
            if written <= 0:
                raise OSError("short create-only JSON write")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    parent = os.open(
        os.path.dirname(path) or ".",
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
    )
    try:
        os.fsync(parent)
    finally:
        os.close(parent)


def _read_exact_json(path: str) -> dict[str, Any]:
    def exact_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    descriptor = os.open(
        path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        with os.fdopen(descriptor, "rb") as stream:
            raw = stream.read()
            descriptor = -1
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    value = json.loads(raw.decode("ascii"), object_pairs_hook=exact_object)
    if type(value) is not dict or raw != _canonical_json_bytes(value) + b"\n":
        raise ValueError("JSON evidence is not one canonical object")
    return value


def _current_repo_head(repo_root: str) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, check=True,
        capture_output=True, text=True,
    ).stdout.strip()


def _campaign_lock_contract_loader_binding(
        layout: CampaignLayout,
) -> tuple[str, dict[str, str]]:
    """Read the fixed enforcement closure from this campaign's v2 lock."""
    lock_text = wal.read_lock(layout)
    if type(lock_text) is not str or not lock_text:
        raise ValueError("verify fan-out requires a campaign-lock/v2 authority")
    decoded = _campaign_lock.decode_campaign_lock(lock_text)
    authority = decoded.authority
    if authority is None:
        raise ValueError("verify fan-out requires a campaign-lock/v2 authority")
    return (
        authority.contract_loader_commit,
        dict(authority.contract_loader_blob_sha256s),
    )


def _make_verify_fanout_task(
        *, campaign_lock_sha256: str, variant: str, build_attempt_id: str,
        tag: str, rep: int, trace_binary: str, trace_bin_sha256: str,
        workload_flags: Mapping[str, str], clocks_per_us: int,
        numactl_prefix: Sequence[str], genome: Genome,
        source_evidence: SourceEvidence, build_admission: BuildAdmission,
        receipt_sink_kind: str, expected_repo_head: str,
        contract_loader_blob_sha256s: Mapping[str, str],
        generator_id: GeneratorId,
) -> dict[str, Any]:
    if (type(trace_binary) is not str or not os.path.isabs(trace_binary)
            or type(rep) is not int or isinstance(rep, bool) or rep < 1
            or type(workload_flags) is not dict
            or any(type(key) is not str or not key or type(value) is not str
                   for key, value in workload_flags.items())
            or type(numactl_prefix) not in {tuple, list}
            or any(type(item) is not str or not item for item in numactl_prefix)):
        raise ValueError("verify fan-out task inputs are not exact")
    if (receipt_sink_kind != CAMPAIGN_WAL_SINK
            or generator_id is not GeneratorId.BACKOFF_REPRO
            or type(contract_loader_blob_sha256s) is not dict
            or not contract_loader_blob_sha256s
            or any(type(path) is not str or not path
                   or type(digest) is not str
                   or re.fullmatch(r"[0-9a-f]{64}", digest) is None
                   for path, digest in contract_loader_blob_sha256s.items())
            or source_evidence.proof_source_snapshot is None):
        raise ValueError("verify fan-out task is outside the admitted scope")
    body: dict[str, Any] = {
        "schema": _VERIFY_FANOUT_TASK_SCHEMA,
        "campaign_lock_sha256": campaign_lock_sha256,
        "variant": variant,
        "build_attempt_id": build_attempt_id,
        "tag": tag,
        "rep": rep,
        "trace_binary": trace_binary,
        "trace_bin_sha256": trace_bin_sha256,
        "workload_flags": [
            [key, value] for key, value in workload_flags.items()
        ],
        "clocks_per_us": clocks_per_us,
        "numactl_prefix": list(numactl_prefix),
        "TRACE_TIMEOUT_S": TRACE_TIMEOUT_S,
        "genome": genome.canonical(),
        "source_evidence": source_evidence.as_receipt(),
        "proof_source_snapshot": (
            serialize_compiled_protocol_source_snapshot(
                source_evidence.proof_source_snapshot
            )
        ),
        "build_admission": dict(build_admission.as_wal_receipt()),
        "receipt_sink_kind": receipt_sink_kind,
        "generator_id": generator_id.value,
        "expected_repo_head": expected_repo_head,
        "contract_loader_blob_sha256s": dict(
            contract_loader_blob_sha256s
        ),
    }
    return {**body, "task_sha256": _json_sha256(body)}


def _default_verify_fanout_launcher(
        host: str, task_path: str, result_path: str, result_secret: bytes,
) -> subprocess.CompletedProcess:
    if type(result_secret) is not bytes or len(result_secret) != 32:
        raise ValueError("verify fan-out result secret must be exactly 32 bytes")
    pbs_jobid = os.environ["PBS_JOBID"]
    repo_root = os.path.realpath(os.path.join(os.path.dirname(__file__), "../.."))
    remote_command = (
        f"cd {shlex.quote(repo_root)} && exec env "
        f"PBS_JOBID={shlex.quote(pbs_jobid)} {shlex.quote(sys.executable)} "
        "-B -m orchestrator.campaign.verify_fanout_worker "
        f"--task {shlex.quote(task_path)} --result {shlex.quote(result_path)}"
    )
    return subprocess.run(
        [
            "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
            # OpenSSH joins all post-host argv with spaces before the remote
            # shell parses them.  Keep quotes in that wire command so bash -c
            # receives the complete ``cd ... && exec ...`` string as argv[0].
            host, "bash", "-c", shlex.quote(remote_command),
        ],
        capture_output=True, input=result_secret,
    )


def _remote_unavailable_outcome(
        *, host: str, rep: int, rc: Optional[int], stderr: str,
        error: Optional[str] = None,
) -> _RepetitionExecutionOutcome:
    stderr_tail = stderr[-2000:]
    if error:
        stderr_tail = (stderr_tail + ("\n" if stderr_tail else "") + error)[-2000:]
    return _RepetitionExecutionOutcome(
        abort=_RepetitionAbortOutcome(
            reason="verify-remote-unavailable",
            message=(
                f"remote verify result を確定できない "
                f"(host={host}, rep={rep}) → reject"
            ),
            detail={
                "remote": {
                    "host": host,
                    "rep": rep,
                    "rc": rc,
                    "stderr_tail": stderr_tail,
                },
            },
            workload_tag="",
        ),
        verify_result=None,
    )


def _admit_verify_fanout_result(
        task: Mapping[str, Any], *, host: str, result_path: str,
        launch_result: object, result_secret: bytes,
        admitted_task_sha256s: Optional[set[str]] = None,
) -> _RepetitionExecutionOutcome:
    """Validate one worker result and issue only task-bound main evidence."""
    rc = getattr(launch_result, "returncode", None)
    stderr = getattr(launch_result, "stderr", "")
    if type(stderr) is bytes:
        stderr = stderr.decode("utf-8", errors="backslashreplace")
    if type(stderr) is not str:
        stderr = repr(stderr)
    rep = task.get("rep")
    tag = task.get("tag")
    if type(rep) is not int or isinstance(rep, bool) or type(tag) is not str:
        return _remote_unavailable_outcome(
            host=host, rep=(-1 if type(rep) is not int else rep), rc=rc,
            stderr=stderr, error="head task identity is malformed",
        )
    if type(rc) is not int or isinstance(rc, bool) or rc != 0:
        unavailable = _remote_unavailable_outcome(
            host=host, rep=rep, rc=rc, stderr=stderr,
        )
        return _RepetitionExecutionOutcome(
            abort=_RepetitionAbortOutcome(
                unavailable.abort.reason, unavailable.abort.message,
                unavailable.abort.detail, tag,
            ),
            verify_result=None,
        )
    try:
        result = _read_exact_json(result_path)
        unsigned_result = dict(result)
        result_mac = unsigned_result.pop("result_mac", None)
        if (type(result_secret) is not bytes or len(result_secret) != 32
                or type(result_mac) is not str
                or re.fullmatch(r"[0-9a-f]{64}", result_mac) is None
                or not hmac.compare_digest(
                    result_mac,
                    hmac.new(
                        result_secret, _canonical_json_bytes(unsigned_result),
                        hashlib.sha256,
                    ).hexdigest(),
                )):
            raise ValueError("remote result HMAC mismatch or missing")
        if set(result) != {
                "schema", "task_sha256", "build_attempt_id", "tag", "rep",
                "trace_bin_sha256", "outcome", "result_mac"}:
            raise ValueError("remote result key set mismatch")
        if (result["schema"] != _VERIFY_FANOUT_RESULT_SCHEMA
                or result["task_sha256"] != task["task_sha256"]
                or result["build_attempt_id"] != task["build_attempt_id"]
                or result["tag"] != tag
                or result["rep"] != rep
                or result["trace_bin_sha256"] != task["trace_bin_sha256"]):
            raise ValueError("remote result task echo mismatch")
        if admitted_task_sha256s is not None:
            if type(admitted_task_sha256s) is not set:
                raise TypeError("admitted task set must be exact set")
            if result["task_sha256"] in admitted_task_sha256s:
                raise ValueError("remote task was already admitted")
            admitted_task_sha256s.add(result["task_sha256"])
        outcome = result["outcome"]
        if type(outcome) is not dict or type(outcome.get("kind")) is not str:
            raise ValueError("remote result outcome is malformed")

        def validate_verify_payload(
                verify_payload: object, *, require_certified: bool,
        ) -> Dict[str, Any]:
            expected_verify_keys = {
                "build_attempt_id", "verdict", "certified", "commits", "aborts",
                "commit_witness", "anomalies", "workload", "proof_surfaces",
            }
            if task["receipt_sink_kind"] == QUALIFICATION_SINK:
                expected_verify_keys.update({"argv", "binary_sha256"})
            if (type(verify_payload) is not dict
                    or set(verify_payload) != expected_verify_keys
                    or verify_payload.get("build_attempt_id")
                    != task["build_attempt_id"]
                    or type(verify_payload.get("verdict")) is not str
                    or not verify_payload.get("verdict")
                    or verify_payload.get("certified") is not require_certified
                    or verify_payload.get("workload") != {"tag": tag}):
                raise ValueError("remote verify payload binding mismatch")
            if task["receipt_sink_kind"] == QUALIFICATION_SINK:
                expected_argv = (
                    list(task["numactl_prefix"])
                    + [task["trace_binary"]]
                    + [f"-{key}={value}" for key, value in task["workload_flags"]]
                    + [f"-clocks_per_us={task['clocks_per_us']}"]
                )
                if (verify_payload["argv"] != expected_argv
                        or verify_payload["binary_sha256"]
                        != task["trace_bin_sha256"]):
                    raise ValueError("remote qualification payload binding mismatch")
            return verify_payload

        if outcome["kind"] == "abort":
            if set(outcome) != {
                    "kind", "reason", "message", "detail", "workload_tag",
                    "verify_payload"}:
                raise ValueError("remote abort outcome key set mismatch")
            if (type(outcome["reason"]) is not str or not outcome["reason"]
                    or type(outcome["message"]) is not str
                    or type(outcome["detail"]) is not dict
                    or outcome["workload_tag"] != tag
                    or (outcome["verify_payload"] is not None
                        and type(outcome["verify_payload"]) is not dict)):
                raise ValueError("remote abort outcome binding mismatch")
            if outcome["verify_payload"] is not None:
                validate_verify_payload(
                    outcome["verify_payload"], require_certified=False,
                )
            detail = dict(outcome["detail"])
            if outcome["reason"] == "verify-remote-unavailable":
                detail = {
                    **detail,
                    "remote": {
                        "host": host, "rep": rep, "rc": rc,
                        "stderr_tail": stderr[-2000:],
                    },
                }
            return _RepetitionExecutionOutcome(
                verify_payload=outcome["verify_payload"],
                abort=_RepetitionAbortOutcome(
                    outcome["reason"], outcome["message"], detail, tag,
                ),
                verify_result=None,
            )
        if outcome["kind"] != "success" or set(outcome) != {
                "kind", "verify_payload", "remote_verification_receipt"}:
            raise ValueError("remote success outcome key set mismatch")
        verify_payload = outcome["verify_payload"]
        validate_verify_payload(verify_payload, require_certified=True)
        if verify_payload["verdict"] != "serializable":
            raise ValueError("remote success verdict is not serializable")
        remote_receipt = outcome["remote_verification_receipt"]
        if (type(remote_receipt) is not dict
                or remote_receipt.get("sink_kind")
                != task["receipt_sink_kind"]
                or remote_receipt.get("verify_payload_sha256")
                != _json_sha256(verify_payload)):
            raise ValueError("remote receipt sink binding mismatch")
        remote_evidence = admit_remote_verification_receipt(
            remote_receipt,
            expected_task_sha256=task["task_sha256"],
            lock_identity_sha256=task["campaign_lock_sha256"],
            variant=task["variant"],
            operation_identity=task["build_attempt_id"],
            workload_tag=tag,
            authenticated_result=result,
            result_secret=result_secret,
        )
        return _RepetitionExecutionOutcome(
            verify_payload=verify_payload,
            verification_capability=remote_evidence,
            verify_result=None,
        )
    except Exception as exc:  # all malformed/missing remote evidence fails closed
        unavailable = _remote_unavailable_outcome(
            host=host, rep=rep, rc=rc, stderr=stderr,
            error=_exc_summary(exc),
        )
        return _RepetitionExecutionOutcome(
            abort=_RepetitionAbortOutcome(
                unavailable.abort.reason, unavailable.abort.message,
                unavailable.abort.detail, tag,
            ),
            verify_result=None,
        )


@dataclass(frozen=True)
class _BenchResult:
    """bench 成功時に COMMIT 判定へ渡す、既測値の最小集合。"""
    median_tps: float
    cv: float
    high_variance: bool
    unstable: bool
    leading_indicators: Dict


@dataclass(frozen=True)
class _BenchRound:
    """1 回の measure_point と、その rep 実行順 return code の対応。"""
    point: object
    rep_returncodes: List[int]


BALANCED_PAIRING_DESIGN = "balanced-a5b5-b5a5-v1"
BALANCED_SCHEDULE_RECEIPT_SCHEMA = (
    "paper-story-a1-balanced-schedule-receipt/v1"
)
BALANCED_BLOCK_REPS = 5


class _CanonicalBuildSourceStateError(RuntimeError):
    """The build-local CCBench checkout cannot satisfy the canonical policy."""

    def __init__(self, build_kind: str, detail: str):
        super().__init__(detail)
        self.build_kind = build_kind


def _require_canonical_build_source_state(
        ccbench_dir: str, canonical_pin: str, *, build_kind: str,
        subprocess_runner: Callable[..., object] = subprocess.run,
        a1_source_context=None,
) -> None:
    """Require exact HEAD and tracked-clean CCBench immediately before a build."""
    if build_kind not in {"trace", "perf"}:
        raise ValueError("build_kind must be trace or perf")
    if (type(canonical_pin) is not str
            or re.fullmatch(r"[0-9a-f]{40}", canonical_pin) is None):
        raise _CanonicalBuildSourceStateError(
            build_kind, "canonical CCBench pin must be 40 lowercase hex characters",
        )
    if a1_source_context is not None:
        from .paper_story_a1_source import SourceContext
        try:
            if type(a1_source_context) is not SourceContext:
                raise RuntimeError("A1 source context type differs")
            a1_source_context.validate(ccbench_dir, canonical_pin)
        except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
            raise _CanonicalBuildSourceStateError(build_kind, str(exc)) from exc
        return
    checkout = ccbench_dir or buildcache._ccbench_dir()

    def _git(*args: str) -> str:
        try:
            completed = subprocess_runner(
                ["git", "-C", checkout, *args],
                capture_output=True,
                text=True,
                timeout=10.0,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise _CanonicalBuildSourceStateError(
                build_kind,
                f"cannot inspect CCBench checkout: {type(exc).__name__}: {exc}",
            ) from exc
        returncode = getattr(completed, "returncode", None)
        stdout = getattr(completed, "stdout", "")
        stderr = getattr(completed, "stderr", "")
        if type(returncode) is not int or returncode != 0 or type(stdout) is not str:
            raise _CanonicalBuildSourceStateError(
                build_kind,
                "cannot inspect CCBench checkout: "
                f"rc={returncode!r} stderr={str(stderr)[-400:]}",
            )
        return stdout.strip()

    observed_head = _git("rev-parse", "--verify", "HEAD^{commit}")
    if observed_head != canonical_pin:
        raise _CanonicalBuildSourceStateError(
            build_kind,
            f"CCBench HEAD differs from canonical pin: {observed_head!r}",
        )
    tracked_status = _git(
        "status", "--porcelain=v1", "--untracked-files=no",
    )
    if tracked_status:
        raise _CanonicalBuildSourceStateError(
            build_kind, "CCBench tracked files are not clean",
        )


@dataclass(frozen=True)
class BalancedScheduleConfig:
    """Opt-in contract for one two-arm balanced A-1 workload schedule."""

    workload: str
    root_seed: str
    arm_names: Tuple[str, str]
    receipt_name: str = "balanced-schedule-receipt.json"

    def __post_init__(self) -> None:
        if type(self.workload) is not str or not self.workload:
            raise ValueError("balanced workload must be a non-empty exact str")
        if (type(self.root_seed) is not str
                or re.fullmatch(r"[0-9a-f]{64}", self.root_seed) is None):
            raise ValueError("balanced root_seed must be 64 lowercase hex characters")
        if (type(self.arm_names) is not tuple
                or len(self.arm_names) != 2
                or any(type(name) is not str or not name for name in self.arm_names)
                or self.arm_names[0] == self.arm_names[1]):
            raise ValueError("balanced arm_names must be two distinct non-empty exact strings")
        if (type(self.receipt_name) is not str
                or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", self.receipt_name) is None):
            raise ValueError("balanced receipt_name must be one plain file name")


@dataclass(frozen=True)
class _BalancedSchedule:
    effective_root_seed: str
    seed_counter: int
    group_bits: Tuple[int, ...]
    blocks: Tuple[Tuple[str, ...], ...]


@dataclass
class _PreparedEvaluation:
    """Verified evaluation state whose bench and commit are still pending."""

    result: EvalResult
    layout: CampaignLayout
    env_tag: str
    perf_binary: str
    perf: PerfConfig
    clocks_per_us: int
    numactl: Optional[Sequence[str]]
    do_bench: bool
    do_settle: bool
    log: Callable
    abort: Callable[[str, str, Optional[Dict]], EvalResult]
    emit: Callable
    build_attempt_id: str
    build_admission_receipt_sha256: str
    contract_sha256: str
    verify_tags: List[str]
    receipt_for: Callable[[Dict], object]
    bench_max_rounds: int
    record_rep_returncodes: bool
    qualification_policy: Optional[QualificationPipelinePolicy]
    holdout_observation_admission: Optional[HoldoutObservationAdmission]
    use_perf: bool
    perf_preflight_receipt: Optional[dict]
    active_screening: Optional[ScreeningConfig]
    screening_disabled_payload: Optional[Dict]
    bench: Optional[_BenchResult] = None
    record_rep_integer_counters: bool = False
    verify_performance_concurrent: bool = False


def derive_balanced_schedule(
        root_seed: str, workload: str, groups: int,
) -> _BalancedSchedule:
    """Derive A5/B5 blocks; retry a homogeneous bit vector deterministically."""
    if type(root_seed) is not str or re.fullmatch(r"[0-9a-f]{64}", root_seed) is None:
        raise ValueError("root_seed must be 64 lowercase hex characters")
    if type(workload) is not str or not workload:
        raise ValueError("workload must be a non-empty exact str")
    if type(groups) is not int or isinstance(groups, bool) or groups < 2:
        raise ValueError("balanced schedule needs at least two exact-integer groups")
    for counter in range(16):
        effective_seed = root_seed if counter == 0 else hashlib.sha256(
            f"{root_seed}|counter={counter}".encode("utf-8")
        ).hexdigest()
        bits = tuple(
            hashlib.sha256(
                (effective_seed
                 + f"a1-balanced5/v1|workload={workload}|group={group}")
                .encode("utf-8")
            ).digest()[-1] & 1
            for group in range(groups)
        )
        if len(set(bits)) == 2:
            blocks = tuple(
                (("A",) * 5 + ("B",) * 10 + ("A",) * 5)
                if bit == 0 else
                (("B",) * 5 + ("A",) * 10 + ("B",) * 5)
                for bit in bits
            )
            return _BalancedSchedule(
                effective_root_seed=effective_seed,
                seed_counter=counter,
                group_bits=bits,
                blocks=blocks,
            )
    raise ValueError("balanced schedule root_seed retry counter exhausted")


_BENCH_DONE_REQUIRED_PAYLOAD_KEYS = frozenset({
    "build_attempt_id",
    "median_tps", "cv", "bench_wall_s", "high_variance", "unstable",
    "rounds", "cv_history", "tps", "settled", "leading_indicators",
    "rep_notes", "run_cmd",
})
_BENCH_DONE_CONDITIONAL_PAYLOAD_KEYS = frozenset({
    "perf_observation", "screening", "rep_returncodes", "reps",
})
_BENCH_PAYLOAD_EXTRA_KEYS = frozenset({"screening_disabled"})
_BENCH_DONE_PAYLOAD_KEYS = (
    _BENCH_DONE_REQUIRED_PAYLOAD_KEYS
    | _BENCH_DONE_CONDITIONAL_PAYLOAD_KEYS
    | _BENCH_PAYLOAD_EXTRA_KEYS
)


def _assert_bench_done_payload_keys(payload: Mapping[str, object]) -> None:
    """Fail closed when pipeline._run_bench would leave its declared key set."""
    actual = set(payload)
    missing = sorted(_BENCH_DONE_REQUIRED_PAYLOAD_KEYS - actual)
    unexpected = sorted(actual - _BENCH_DONE_PAYLOAD_KEYS)
    if missing or unexpected:
        raise ValueError(
            "bench_done payload key closure violation: "
            f"{{'missing': {missing!r}, 'unexpected': {unexpected!r}}}"
        )


def _assert_bench_payload_extra_keys(
        bench_payload: Dict[str, object], bench_payload_extra: object,
) -> None:
    """Accept only the exact caller-owned extension after overlap rejection."""
    if type(bench_payload_extra) is not dict:
        raise TypeError("bench_payload_extra は exact dict でなければならない")
    extra_keys = set(bench_payload_extra)
    overlap = sorted(set(bench_payload) & extra_keys)
    if overlap:
        raise ValueError(
            "bench_payload_extra overlaps assembled payload: "
            f"{{'overlap': {overlap!r}}}"
        )
    missing = sorted(_BENCH_PAYLOAD_EXTRA_KEYS - extra_keys)
    unexpected = sorted(extra_keys - _BENCH_PAYLOAD_EXTRA_KEYS)
    if missing or unexpected:
        raise ValueError(
            "bench_payload_extra key closure violation: "
            f"{{'missing': {missing!r}, 'unexpected': {unexpected!r}}}"
        )


def _run_bench(perf_binary: str, perf: PerfConfig, clocks_per_us: int,
               numactl: Optional[Sequence[str]], do_settle: bool,
               layout: CampaignLayout, variant: str, env_tag: str,
               abort: Callable[[str, str, Optional[Dict]], EvalResult],
               log=print, screening: bool = False,
               bench_payload_extra: Optional[Dict] = None,
               bench_max_rounds: int = 3,
               record_rep_returncodes: bool = False,
               bench_timeout_s: Optional[float] = None,
               require_all_reps: bool = False,
               require_settled: bool = False,
               emit: Optional[Callable[[object, str, str, str, Dict], None]] = None,
               holdout_observation_admission: Optional[
                   HoldoutObservationAdmission
               ] = None,
               use_perf: bool = True,
               perf_preflight_receipt: Optional[dict] = None,
               *,
               build_attempt_id: str,
               record_rep_integer_counters: bool = False,
               verify_performance_concurrent: bool = False,
               ) -> Tuple[Optional[EvalResult], Optional[_BenchResult]]:
    """現行の full bench を実行し、成功時は WAL に既測値を残す。"""
    if type(build_attempt_id) is not str or not build_attempt_id:
        raise TypeError("build_attempt_id は non-empty str が必要")
    _require_measurement_site("campaign throughput 測定")
    # records は measure_point が -ycsb_tuple_num として渡す → workload に入れない
    # (入れると gflags last-wins で calibration の records を無言上書きする)。
    if "ycsb_tuple_num" in perf.workload:
        # assert だと python -O で消える。calibration の records を gflags last-wins で
        # 無言上書きする事故 (規律4 の動作点破壊) への唯一の防壁なので例外文にする。
        raise ValueError(
            "PerfConfig.workload に ycsb_tuple_num を入れない (records を上書きする)")

    # IZANAGI_TRACE_DIR を perf run にも対称に設定する (D36 決定4-5): verify run だけが
    # この環境変数を持つと、EVOLVE_BLOCK の共有コード (#if TRACE の外) が getenv 有無で
    # verify/perf を判別する経路になりうる (auditor.md 型3 の判別述語)。perf build は
    # TRACE がコンパイルアウトされ実際には未使用だが、変数の「有無」自体を判別子に
    # できなくする (値の中身までは踏み込まない — 残りは auditor の静的検査が担う)。
    dummy_tdir = tempfile.mkdtemp(prefix="izanagi_eval_notrace_")

    measured_rounds: List[_BenchRound] = []

    def _measure():
        qualification_kwargs = {}
        if record_rep_integer_counters:
            qualification_kwargs["record_rep_integer_counters"] = True
            qualification_kwargs["rep_observations"] = []
            qualification_kwargs["require_all_reps"] = True
        if bench_timeout_s is not None:
            qualification_kwargs["timeout_s"] = bench_timeout_s
        if require_all_reps:
            qualification_kwargs["require_all_reps"] = True
        if holdout_observation_admission is not None:
            qualification_kwargs["holdout_observation_admission"] = (
                holdout_observation_admission
            )
        if not use_perf:
            qualification_kwargs["use_perf"] = False
        if not record_rep_returncodes:
            return measure_point(
                perf_binary, perf.records, perf.threads, clocks_per_us,
                extime=perf.extime, reps=perf.reps,
                workload=perf.workload, numactl=numactl,
                extra_env={"IZANAGI_TRACE_DIR": dummy_tdir},
                **qualification_kwargs,
            )
        rep_returncodes: List[int] = []
        point = measure_point(
            perf_binary, perf.records, perf.threads, clocks_per_us,
            extime=perf.extime, reps=perf.reps,
            workload=perf.workload, numactl=numactl,
            extra_env={"IZANAGI_TRACE_DIR": dummy_tdir},
            rep_returncodes=rep_returncodes,
            **qualification_kwargs,
        )
        measured_rounds.append(_BenchRound(
            point=point, rep_returncodes=rep_returncodes,
        ))
        return point

    bench_wall_s = 0.0
    try:
        # 外れ値 → 自動再測定 (§3.6(2)): 反復内 CV が閾値超なら静定して測り直す。規定
        # ラウンドで収束しなければ unstable。再測定の実走も全て bench_lock 下 = 単一
        # テナント直列 (絶対規律4)。
        with bench_lock():
            # admission を fails-closed に (絶対規律4): bench_lock 取得直後・自分の bench
            # 開始前に競合/孤児ベンチを pgrep で直接確認し、居たら**汚染計測を採用せず
            # abort** する (settle の load EMA は laggy なので一次ゲートはこの確定信号)。
            # 孤児は規律6 に従い**自動 kill せず PID を表に出して停止** — 人間が処遇を
            # 判断する。driver の pre-flight が campaign 冒頭で 1 回見るのに対し、ここは
            # genome ごと = campaign 途中で湧いた競合も捕える。
            try:
                comp = competing_bench_pids()
            except CompetingBenchProbeError as e:
                # probe (pgrep) の実行自体が失敗 → 競合の有無を確定できない。握りつぶさず
                # 専用 reason で abort し、故障詳細を WAL payload に構造化して残す (規律3/4,
                # B-6)。この reason は transient infra 失敗として retryable 扱いされる (B-3)。
                return abort("bench-probe-error",
                             "競合検知 probe (pgrep) 実行失敗 → 競合の有無を確定できず "
                             "reject (環境故障・再評価可能, 規律3/4)",
                             {"probe_error": e.as_dict(),
                              "bench_wall_s": bench_wall_s}), None
            if comp:
                return abort("bench-competing-tenant",
                             "競合 ccbench ベンチを検知 → 汚染計測を採用せず reject (規律4)",
                             {"competing": comp, "bench_wall_s": bench_wall_s}), None
            settled = (settle(timeout_s=60.0) if verify_performance_concurrent
                       else settle()) if do_settle else None
            bench_started = time.monotonic()
            try:
                rem = remeasure_until_stable(_measure,
                                             settle_fn=settle if do_settle else None,
                                             max_rounds=bench_max_rounds)
            finally:
                bench_wall_s = float(max(0.0, time.monotonic() - bench_started))
    finally:
        shutil.rmtree(dummy_tdir, ignore_errors=True)
    pt, nf = rem.point, rem.nf
    if require_settled and (not settled or settled.get("settled") is not True):
        return abort(
            "bench-unsettled",
            "qualification bench did not reach settled=true → reject",
            {"settled": (settled.get("settled") if settled else None),
             "rounds": rem.rounds, "bench_wall_s": bench_wall_s},
        ), None
    selected_returncodes: Optional[List[int]] = None
    if record_rep_returncodes:
        selected_rounds = [item for item in measured_rounds if rem.point is item.point]
        if len(selected_rounds) != 1:
            return abort(
                "bench-returncodes-round-unbound",
                "採用 bench round と rep return code の対応が一意でない → reject",
                {"matching_rounds": len(selected_rounds),
                 "measured_rounds": len(measured_rounds),
                 "bench_wall_s": bench_wall_s},
            ), None
        selected_returncodes = list(selected_rounds[0].rep_returncodes)
    if nf is None or nf.median is None:
        # 全 rep で throughput が取れず測定不能 → fitness 無しの COMMIT を書かない。
        # 半端な評価を terminal commit にして永久 skip させない (A: atomicity)。
        return abort("bench-no-throughput", "bench 測定失敗 (throughput 無し) → reject",
                     {"tps": getattr(pt, "throughputs", None), "rounds": rem.rounds,
                      "rep_notes": getattr(pt, "notes", []),
                      "bench_wall_s": bench_wall_s}), None
    if nf.cv is None:
        # 有効 rep が 1 点のみ (残りは rep 失敗) / 全 rep tps=0 だと CV が定義できず、
        # within-run 品質ゲート (P2-1) を通せない → fitness として採用しない (規律4)。
        # 旧実装はここを素通りし直後の log f-string の nf.cv*100 で TypeError →
        # 意図しない eval-exception abort (permanent skip) になっていた (洗練検査 MED)。
        return abort("bench-cv-undefined",
                     f"CV 算出不能 (有効 rep {len(pt.throughputs)} 点) → reject",
                     {"tps": pt.throughputs, "rounds": rem.rounds,
                      "rep_notes": getattr(pt, "notes", []),
                      "bench_wall_s": bench_wall_s}), None
    leading_indicators = pt.leading_indicators()
    bench_payload = {
        "build_attempt_id": build_attempt_id,
        "median_tps": nf.median, "cv": nf.cv,
        "bench_wall_s": bench_wall_s,
        "high_variance": nf.high_variance, "unstable": rem.unstable,
        "rounds": rem.rounds, "cv_history": rem.cv_history,
        "tps": pt.throughputs,
        # admission: load が静定したか (settle の戻り)。fails-closed の一次ゲートは
        # competing_bench_pids だが、settled=False の測定は forensic に残す (規律4)。
        "settled": (settled.get("settled") if settled else None),
        # leading indicators (§3.5): fitness を設計選択に帰属させる材料。
        # critic が abort率/latency/cache/IPC を読んで次の genome 方向を出す。
        "leading_indicators": leading_indicators,
        # rep 単位の失敗記録 (1e2c01c, 規律3)。部分失敗 (例 2/5 rep timeout) は
        # fitness が残り rep の median で成立するため、ここに載せないと「なぜ標本が
        # 痩せたか」が WAL の機械可読経路から消える (洗練検査 MED)
        "rep_notes": getattr(pt, "notes", []),
        "run_cmd": pt.run_cmd,                    # この測定点を再現する実行コマンド
    }
    perf_observation = _perf_preflight.build_perf_observation(
        perf_preflight_receipt,
        run_cmd=pt.run_cmd,
        leading_indicators=leading_indicators,
    )
    if perf_observation is not None:
        bench_payload["perf_observation"] = perf_observation
    if screening:
        bench_payload["screening"] = True
    if selected_returncodes is not None:
        bench_payload["rep_returncodes"] = selected_returncodes
    if record_rep_integer_counters:
        observations = getattr(pt, "rep_observations", None)
        if (not isinstance(observations, list) or len(observations) != perf.reps
                or len(pt.throughputs) != perf.reps):
            raise ValueError("integer counter reps must match requested throughput reps")
        reps = []
        for index, observation in enumerate(observations):
            rep_index = observation.get("rep_index")
            aborts = observation.get("abort_counts_")
            commits = observation.get("commit_counts_")
            throughput = observation.get("throughput")
            if (type(rep_index) is not int or rep_index != index
                    or type(aborts) is not int or aborts < 0
                    or type(commits) is not int or commits < 0
                    or aborts + commits == 0
                    or type(throughput) not in (int, float)
                    or not math.isfinite(throughput) or throughput <= 0
                    or throughput != pt.throughputs[index]):
                raise ValueError(f"invalid integer counter observation at rep {index}")
            reps.append({
                "rep_index": rep_index, "abort_counts_": aborts,
                "commit_counts_": commits, "throughput_tps": throughput,
            })
        bench_payload["reps"] = reps
    if bench_payload_extra is not None:
        _assert_bench_payload_extra_keys(bench_payload, bench_payload_extra)
        bench_payload.update(bench_payload_extra)
    # Attempt ownership is part of the producer contract.
    bench_payload["build_attempt_id"] = build_attempt_id
    _assert_bench_done_payload_keys(bench_payload)
    (emit or wal.log)(layout, variant, STAGE_BENCH_DONE, env_tag, bench_payload)
    log(f"  [eval {variant}] bench: median {nf.median:,.0f} tps (CV {nf.cv*100:.2f}%"
        f"{f', {rem.rounds}rounds' if rem.rounds > 1 else ''}"
        f"{' ⚠UNSTABLE' if rem.unstable else ''})")
    return None, _BenchResult(
        median_tps=nf.median, cv=nf.cv, high_variance=nf.high_variance,
        unstable=rem.unstable, leading_indicators=leading_indicators)


def _validate_fetchcontent_prebuild_inputs(
        *, env_contract: Optional[ExecutionEnvironmentContract],
        fetchcontent_base_dir: object = "",
        masstree_source_dir: Optional[object] = None,
        mimalloc_source_dir: Optional[object] = None,
        googletest_source_dir: Optional[object] = None,
        fetchcontent_dependency_receipt: Optional[
            Mapping[str, object]
        ] = None,
) -> bool:
    """Require the FetchContent prebuild transport as one v2-only tuple."""
    present = (
        bool(fetchcontent_base_dir),
        masstree_source_dir is not None,
        mimalloc_source_dir is not None,
        googletest_source_dir is not None,
        fetchcontent_dependency_receipt is not None,
    )
    if any(present) and not all(present):
        raise ValueError(
            "FetchContent prebuild は base/source 3 本/dependency receipt の "
            "5 値同時指定が必要"
        )
    if all(present) and env_contract is None:
        raise ValueError(
            "FetchContent prebuild は env_contract 付き v2 build に限る"
        )
    return all(present)


def _prepare_evaluation_core(genome: Genome, layout: CampaignLayout, env_tag: str,
             ccbench_commit: str, perf: PerfConfig,
             clocks_per_us: int, numactl: Optional[Sequence[str]] = None,
             correctness: Optional[CorrectnessWorkload] = None,
             extra_correctness: Optional[Sequence[Tuple[str, CorrectnessWorkload]]] = None,
             do_bench: bool = True, do_settle: bool = True,
             src_token: Optional[str] = None, log=print,
             ccbench_dir: str = "", cache_root: str = "",
             screening: Optional[ScreeningConfig] = None,
             bench_max_rounds: int = 3,
             expected_perf_sha256: Optional[str] = None,
             env_contract: Optional[ExecutionEnvironmentContract] = None,
             record_rep_returncodes: bool = False,
             qualification_policy: Optional[QualificationPipelinePolicy] = None,
             dependency_prefix: str = "",
             fetchcontent_base_dir: str = "",
             masstree_source_dir: Optional[object] = None,
             mimalloc_source_dir: Optional[object] = None,
             googletest_source_dir: Optional[object] = None,
             fetchcontent_dependency_receipt: Optional[
                 Mapping[str, object]
             ] = None, *,
             record_rep_integer_counters: bool = False,
             authorization_contract: _env_contract.AuthorizedContract,
             build_context: BuildRunContext,
             capability_resolver: Optional[AdmissionCapabilityResolver] = None,
             source_evidence: Optional[SourceEvidence] = None,
             backoff_grammar_version: Optional[int] = None,
             sort_oracle_contract_id: Optional[str] = None,
             expected_toolchain_manifest: Optional[Mapping[str, object]] = None,
             declared_use_class: Optional[str] = None,
             trigger_gate_binding=None,
             holdout_observation_admission: Optional[
                 HoldoutObservationAdmission
             ] = None,
             use_perf: bool = True,
             perf_preflight_receipt: Optional[dict] = None,
             canonical_build_pin: Optional[str] = None,
             a1_source_context=None,
             verify_fanout_hosts: tuple[str, ...] = (),
             verify_fanout_launcher: Optional[Callable[..., object]] = None,
             verify_performance_concurrent: bool = False,
             ) -> EvalResult | _PreparedEvaluation:
    """Build and verify one genome, preserving state for later bench/commit.

    `ccbench_dir`/`cache_root` (段5 git worktree 隔離): 省略時は共有固定パス既定 (既存動作と
    完全互換)。呼び手が `patchharness.isolated()` で作った worktree を `ccbench_dir` に渡すと
    ソースはその worktree から読み、`cache_root` を固定パス配下に据え置けばビルドキャッシュは
    campaign 非依存のまま共有される (worktree 間で内容キーが揃う)。campaign-id には含めない
    (ビルド結果に影響しない実装詳細 — numactl/do_bench と同じ実行時引数の扱い)。
    `bench_max_rounds` も同じ runtime-only 軸で campaign-id には含めない。既定 3 は従来の
    `remeasure_until_stable` 既定と同一で、事前登録が 1 measure_point に固定した driver
    だけ 1 を明示する。

    **正しさを確証できない variant は全て abort (fitness なし)** — verifier red だけで
    なく、ビルド失敗・trace 異常終了・空トレース・パース不能・bench 測定失敗も「採用
    しない」に倒す (規律2: certified を安売りしない / 空 DSG を緑と誤認させない)。
    abort も commit も terminal だが、abort は **fitness を付けず採用しない**。

    `expected_perf_sha256` (A-1, exact 64 lowercase hex): 指定時のみ、両ビルド完了直後・
    trace/bench 起動前に perf バイナリの full sha256 を厳密照合し、不一致 (期待値の形不正・
    照合不能を含む) は trace/bench を一切起動せず `bench-binary-mismatch` で abort する。
    期待値の供給元は freeze v2 で配線するため今回はデフォルト None のまま (未配線=従来同一)。

    `env_contract` は v2 consumer 専用の opt-in。指定時だけ contract namespace の
    `build_v2` を使い、未指定 caller (p3 loop を含む) は legacy build の呼出し形も
    namespace も不変に保つ。`dependency_prefix` は非空時だけ v2 build へ素通しし、
    空の既存 caller では build_v2 の呼出し形を変えない。

    `expected_toolchain_manifest` は campaign 開始時に観測した v2 toolchain の束縛値で、
    指定時は source evidence と trace/perf の両 build へ同じ値を渡す。`declared_use_class`
    は v2 materializer へ渡す runtime class であり、未指定 caller の legacy 経路には
    伝播しない。

    `record_rep_returncodes` も既定 False の opt-in。True の official oracle 経路だけ、
    採用した再測定 round と identity で一意に対応する rep rc を bench_done に残す。

    `use_perf` は既定 True を維持する。False は unavailable と検証できる
    `perf_preflight_receipt` と同時に渡された探索経路だけで許可し、probe_error や
    receipt との不一致は build/WAL より前に拒否する。

    `trigger_gate_binding` は trigger proposal 専用。SourceEvidence 確定後に source-bound
    binding を作り、raw record を build_start より先に、commitment だけを start payload
    に記録する。None の既存 caller は従来 WAL 書式のまま。

    `screening` (D58) を指定したときだけ full bench を verify より前へ移し、明白な
    劣位点を uncertified のまま棄却する。COMMIT は従来どおり全 verify 構成通過後だけ。

    `extra_correctness` (D36 決定4): (tag, workload) の列。既定 correctness (tag
    LEGACY_TAG) に加え指定された構成を**全て**通した variant だけ certified にする
    (verify 2 本立て、既存 CorrectnessWorkload は置き換えず併存、決定2)。各構成は
    WAL に "workload":{"tag":...} で残り、次手生成 (critic) がどの構成で壊れたか
    帰属できる (決定4-3)。S2 相当 (t48 フルロード規模) は bench 並みの負荷ゆえ
    bench_lock + bench と同一の launch prefix 下で回す (決定4-4)。既定 legacy は
    軽量ゆえ従来どおり並列可 (lock.py の設計方針)。"""
    if a1_source_context is not None and canonical_build_pin is None:
        raise ValueError("A1 source context requires canonical build pin")
    fetchcontent_prebuild = _validate_fetchcontent_prebuild_inputs(
        env_contract=env_contract,
        fetchcontent_base_dir=fetchcontent_base_dir,
        masstree_source_dir=masstree_source_dir,
        mimalloc_source_dir=mimalloc_source_dir,
        googletest_source_dir=googletest_source_dir,
        fetchcontent_dependency_receipt=fetchcontent_dependency_receipt,
    )
    if type(build_context) is not BuildRunContext:
        raise TypeError("build_context は build_run_context() 由来の exact value が必要")
    if expected_toolchain_manifest is not None and env_contract is None:
        raise ValueError(
            "expected_toolchain_manifest は env_contract 付き v2 build に限る"
        )
    if trigger_gate_binding is not None and type(trigger_gate_binding) is not TriggerGateBinding:
        raise TypeError("trigger_gate_binding は exact TriggerGateBinding または None が必要")
    if capability_resolver is not None and not callable(capability_resolver):
        raise TypeError("capability_resolver は callable または None が必要")
    if (type(verify_fanout_hosts) is not tuple
            or any(type(host) is not str
                   or _VERIFY_FANOUT_COMPONENT_RE.fullmatch(host) is None
                   for host in verify_fanout_hosts)):
        raise ValueError("verify_fanout_hosts は safe hostname の exact tuple が必要")
    if (len(set(verify_fanout_hosts)) != len(verify_fanout_hosts)
            or socket.gethostname() in verify_fanout_hosts):
        raise ValueError("verify_fanout_hosts は重複と current host を含められない")
    if (verify_fanout_launcher is not None
            and not callable(verify_fanout_launcher)):
        raise TypeError("verify_fanout_launcher は callable または None が必要")
    if type(verify_performance_concurrent) is not bool:
        raise TypeError("verify_performance_concurrent は exact bool が必要")
    if verify_performance_concurrent and verify_fanout_hosts:
        raise ValueError("local concurrent verify と remote fan-out は併用できない")
    if verify_performance_concurrent and qualification_policy is not None:
        raise ValueError("local concurrent verify は campaign WAL に限る")
    if type(use_perf) is not bool:
        raise TypeError("use_perf は bool でなければならない")
    if (isinstance(bench_max_rounds, bool) or not isinstance(bench_max_rounds, int)
            or bench_max_rounds < 1):
        raise ValueError("bench_max_rounds は 1 以上の整数でなければならない")
    if qualification_policy is not None:
        if type(qualification_policy) is not QualificationPipelinePolicy:
            raise TypeError("qualification_policy は exact QualificationPipelinePolicy が必要")
        expected_contract = _env_contract.lookup("pegasus")
        qualification_policy.event_sink.assert_pipeline_binding(layout)
        if env_contract != expected_contract:
            raise ValueError("qualification opt-in requires the exact registered Pegasus contract")
        if (env_tag != expected_contract.env_tag
                or clocks_per_us != expected_contract.clocks_per_us
                or type(numactl) is not tuple
                or numactl != expected_contract.numactl):
            raise ValueError("qualification execution values do not exactly match Pegasus contract")
        if (perf.records != 1_000_000 or perf.threads != 48
                or perf.workload != {
                    "ycsb_zipf_skew": "0.9", "ycsb_rratio": "95",
                    "ycsb_rmw": "0", "ycsb_max_ope": "10",
                }
                or perf.extime != 3 or perf.reps != 5
                or correctness is not None
                or extra_correctness != [(S2_TAG, s2_correctness_workload())]
                or do_bench is not True or do_settle is not True
                or screening is not None or bench_max_rounds != 1
                or record_rep_returncodes is not True):
            raise ValueError("qualification opt-in evaluation shape mismatch")
    emit = (
        qualification_policy.event_sink.emit
        if qualification_policy is not None else wal.log
    )
    if screening is not None and not do_bench:
        raise ValueError("screening 指定時に do_bench=False は使えない")
    if screening is not None:
        # D58 campaign 分離: runtime 引数だけで既存 campaign へ screening を混在させない。
        # WAL/build を一切書く前に、campaign.lock の同一方針焼き込みを検証する。
        ident.verify_screening_preimage(screening, wal.read_lock(layout))
    correctness = correctness or CorrectnessWorkload()
    passes: List[Tuple[str, CorrectnessWorkload, bool]] = [(LEGACY_TAG, correctness, False)]
    for tag, wl in (extra_correctness or []):
        passes.append((tag, wl, True))
    if type(numactl) in {list, tuple}:
        # 呼び手の可変 list を契約照合後に変更できないよう、gate・認可・verify・bench が
        # 共有する launch prefix を一度だけ immutable snapshot にする。
        numactl = tuple(numactl)
    if (any(fullscale_isolated for _, _, fullscale_isolated in passes)
            and qualification_policy is None
            and tuple(numactl or ()) != authorization_contract.contract.numactl):
        # S2 相当 (fullscale_isolated=True) は D36 決定4-4 で bench と同じメモリ配置が必須。
        # launch prefix の非空性ではなく、bench の権威である解決済み環境契約との
        # exact 一致を要求する。これにより prefix 無しが契約である Pegasus は通し、
        # 非空でも bench と異なる配置を指定した verify は fail-closed で拒否する。
        # raise は run_campaign の except Exception が eval-exception abort に変換する。
        raise ValueError(
            "extra_correctness の launch prefix が bench の環境契約 numactl と一致しない "
            "(D36 決定4-4: S2 相当は bench と同じメモリ配置で回す)")
    authorized_contract = execution_guard.require_certified_writer_authorization(
        authorization_contract,
        env_tag=env_tag,
        clocks_per_us=clocks_per_us,
        numactl=numactl,
        env_contract=env_contract,
    )
    # identity (D23): coder のコード差まで覆う src_token を build 前に確定し、variant_id
    # (WAL キー) と build (cache_key) で共有する (TOCTOU 偽 hit を防ぐ)。loop は skip/abort
    # キーを同じ id に揃えるため src_token を確定済みで渡す (id 確定点の単一化, D24)。直接
    # caller (src_token=None) は自己計算し、identity を確定できない (allowlist 逸脱 /
    # preprocess 失敗 / git show 失敗) なら fails-closed で評価しない (best-effort skip を
    # identity 核に持ち込まない, 規律2)。
    build_attempt_id = secrets.token_hex(16)

    def _candidate_binding() -> Optional[TriggerGateBinding]:
        if trigger_gate_binding is None:
            return None
        return TriggerGateBinding(
            mask=trigger_gate_binding.mask,
            predicate_sha256=trigger_gate_binding.predicate_sha256,
            nonce=trigger_gate_binding.nonce,
            source=None,
        )

    def _prebuild_abort(reason: str, error: BaseException) -> EvalResult:
        v0 = variant_id(genome)
        start_payload = {
            "genome": genome.canonical(),
            "build_attempt_id": build_attempt_id,
        }
        candidate = _candidate_binding()
        if candidate is not None:
            start_payload[wal.TRIGGER_BINDING_COMMITMENT_KEY] = wal.log_trigger_binding(
                layout, v0, env_tag, build_attempt_id, candidate, emit=emit,
            )
        emit(layout, v0, STAGE_BUILD_START, env_tag, start_payload)
        emit(layout, v0, STAGE_ABORT, env_tag, {
            "reason": reason,
            "error": _exc_summary(error),
            "build_attempt_id": build_attempt_id,
        })
        log(f"  [eval {v0}] abort: {reason} ({error})")
        result = EvalResult(
            genome=genome, variant=v0, certified=False, aborted=True,
            build_attempt_id=build_attempt_id,
        )
        result.notes.append(f"pre-build evidence 確定不能 → reject ({error})")
        return result

    try:
        if expected_toolchain_manifest is None:
            _, resolved_cxx = _compilers_for_current_site()
        else:
            _, resolved_cxx = buildcache.toolchain_compilers_from_manifest(
                expected_toolchain_manifest,
            )
        evidence_cxx = _DEFAULT_CXX if resolved_cxx == _DEFAULT_CXX else resolved_cxx
        source_options = {}
        if backoff_grammar_version is not None:
            source_options["backoff_grammar_version"] = (
                backoff_grammar_version
            )
        if sort_oracle_contract_id is not None:
            source_options["sort_oracle_contract_id"] = (
                sort_oracle_contract_id
            )
        current_evidence = source_digest.resolve_evidence(
            genome,
            ccbench_commit,
            ccbench_dir=ccbench_dir,
            cxx=evidence_cxx,
            **source_options,
        )
        if source_evidence is not None:
            if type(source_evidence) is not SourceEvidence:
                raise BuildAdmissionError(
                    "source_evidence は resolve_evidence() 由来の exact value が必要"
                )
            if source_evidence != current_evidence:
                raise BuildAdmissionError(
                    "caller の SourceEvidence が current source と不一致"
                )
        # Mock/legacy in-process evidence can lack the new non-wire fields.  Bind
        # them once before either build; production resolve_evidence() already
        # returns the same immutable snapshot and variant identity.
        proof_snapshot = capture_compiled_protocol_source_snapshot(
            genome.protocol, current_evidence.source_root,
        )
        try:
            evidence = current_evidence._bind_runtime_verification(
                proof_source_snapshot=proof_snapshot,
                verification_variant=variant_id(
                    genome, current_evidence.src_token,
                ),
            )
        except ValueError as exc:
            raise BuildAdmissionError(
                "SourceEvidence resolve 中に proof source binding が変化した"
            ) from exc
        if src_token is not None and src_token != evidence.src_token:
            raise BuildAdmissionError("src_token が current SourceEvidence と不一致")
        capability = capability_resolver(evidence) if capability_resolver is not None else None
        generator_receipt = capability if type(capability) is GeneratorReceipt else None
        review_receipt = capability if type(capability) is ReviewReceipt else None
        if capability is not None and generator_receipt is None and review_receipt is None:
            raise BuildAdmissionError(
                "capability_resolver は sealed GeneratorReceipt/ReviewReceipt/None だけを返せる"
            )
        admission = derive_build_admission(
            build_context,
            evidence,
            generator_receipt=generator_receipt,
            review_receipt=review_receipt,
        )
        admission = require_build_admission(
            admission,
            expected_policy=build_context.policy,
            expected_source=evidence,
        )
    except (BuildAdmissionError, RuntimeError) as exc:
        reason = "identity-error" if isinstance(exc, RuntimeError) \
            and not isinstance(exc, BuildAdmissionError) else "admission-error"
        return _prebuild_abort(reason, exc)

    src_tok = evidence.src_token
    admission_receipt = admission.as_wal_receipt()
    bound_binding = None
    if trigger_gate_binding is not None:
        try:
            expected_source = SourceBinding(
                src_token=evidence.src_token,
                source_bytes_sha256=evidence.source_bytes_sha256,
            )
            if (trigger_gate_binding.source is not None
                    and trigger_gate_binding.source != expected_source):
                raise BuildAdmissionError(
                    "trigger binding source が current SourceEvidence と不一致"
                )
            _require_materialized_trigger_predicate(evidence, trigger_gate_binding)
            bound_binding = TriggerGateBinding(
                mask=trigger_gate_binding.mask,
                predicate_sha256=trigger_gate_binding.predicate_sha256,
                nonce=trigger_gate_binding.nonce,
                source=expected_source,
            )
            receipt_source = admission_receipt.get("source")
            if (type(receipt_source) is not dict
                    or receipt_source.get("src_token") != src_tok
                    or receipt_source.get("source_bytes_sha256")
                    != evidence.source_bytes_sha256):
                raise BuildAdmissionError(
                    "trigger binding source が build admission receipt と不一致"
                )
        except BuildAdmissionError as exc:
            return _prebuild_abort("admission-error", exc)
    v = variant_id(genome, src_tok)
    res = EvalResult(
        genome=genome, variant=v, certified=False, aborted=False,
        build_attempt_id=build_attempt_id,
    )
    start_payload = {
        "genome": genome.canonical(),
        "src_token": src_tok,
        "build_attempt_id": build_attempt_id,
        "build_admission": admission_receipt,
        "build_admission_receipt_sha256": admission.receipt_sha256,
    }
    if bound_binding is not None:
        start_payload[wal.TRIGGER_BINDING_COMMITMENT_KEY] = wal.log_trigger_binding(
            layout, v, env_tag, build_attempt_id, bound_binding, emit=emit,
        )
    emit(layout, v, STAGE_BUILD_START, env_tag, start_payload)

    def _abort(reason: str, note: str, extra: Optional[Dict] = None,
              workload_tag: Optional[str] = None, *,
              verify_result: Optional[VerifyResult] = None) -> EvalResult:
        if verify_result is not None and type(verify_result) is not VerifyResult:
            raise TypeError("verify_result must be an exact VerifyResult")
        payload = {
            "reason": reason,
            "build_attempt_id": build_attempt_id,
            "build_admission_receipt_sha256": admission.receipt_sha256,
            **(extra or {}),
        }
        if workload_tag is not None:
            # D36 決定4-3: どの verify 構成で壊れたかを次手生成が帰属できるようにする。
            payload["workload"] = {"tag": workload_tag}
        emit(layout, v, STAGE_ABORT, env_tag, payload)
        res.aborted = True
        if verify_result is not None:
            res.verify_result = verify_result
        res.notes.append(note)
        log(f"  [eval {v}] abort: {reason}")
        return res

    # --- build (trace + perf 別ビルド, 絶対規律1)。ビルド失敗はこの variant 固有の
    #     失敗として abort 隔離 (campaign 全体を落とさず前進, overnight 耐性) ---
    try:
        common = None
        if env_contract is not None:
            if not isinstance(env_contract, ExecutionEnvironmentContract):
                raise TypeError(
                    "env_contract は ExecutionEnvironmentContract でなければならない"
            )
            default_ccbench = buildcache._ccbench_dir()
            if expected_toolchain_manifest is None:
                resolved_cc, resolved_cxx = _compilers_for_current_site()
            else:
                resolved_cc, resolved_cxx = buildcache.toolchain_compilers_from_manifest(
                    expected_toolchain_manifest,
                )
            common = {
                "contract": env_contract,
                "ccbench_commit": ccbench_commit,
                "src_token": src_tok,
                "cc": resolved_cc,
                "cxx": resolved_cxx,
                "cache_root": cache_root or os.path.join(
                    default_ccbench, "build-variants",
                ),
                "ccbench_dir": ccbench_dir,
                "admission": admission,
                "build_context": build_context,
                "source_evidence": evidence,
            }
            if dependency_prefix:
                common["dependency_prefix"] = dependency_prefix
            if fetchcontent_prebuild:
                common.update({
                    "fetchcontent_base_dir": fetchcontent_base_dir,
                    "masstree_source_dir": masstree_source_dir,
                    "mimalloc_source_dir": mimalloc_source_dir,
                    "googletest_source_dir": googletest_source_dir,
                    "fetchcontent_dependency_receipt": (
                        fetchcontent_dependency_receipt
                    ),
                })
            if expected_toolchain_manifest is not None:
                common["expected_toolchain_manifest"] = expected_toolchain_manifest
            if declared_use_class is not None:
                common["declared_use_class"] = declared_use_class
            if backoff_grammar_version is not None:
                common["backoff_grammar_version"] = backoff_grammar_version
            if sort_oracle_contract_id is not None:
                common["sort_oracle_contract_id"] = sort_oracle_contract_id

        def _build_one(*, trace: bool):
            build_kind = "trace" if trace else "perf"
            if canonical_build_pin is not None:
                _require_canonical_build_source_state(
                    ccbench_dir, canonical_build_pin, build_kind=build_kind,
                    a1_source_context=a1_source_context,
                )
            if common is None:
                build_options = {}
                if backoff_grammar_version is not None:
                    build_options["backoff_grammar_version"] = (
                        backoff_grammar_version
                    )
                if sort_oracle_contract_id is not None:
                    build_options["sort_oracle_contract_id"] = (
                        sort_oracle_contract_id
                    )
                return buildcache.build(
                    genome, ccbench_commit, trace=trace, src_token=src_tok,
                    ccbench_dir=ccbench_dir, cache_root=cache_root,
                    admission=admission, build_context=build_context,
                    source_evidence=evidence,
                    **build_options,
                )
            if qualification_policy is None:
                return buildcache.build_v2(genome, trace=trace, **common)
            return buildcache.build_v2(
                genome, trace=trace,
                timeout_s=qualification_policy.build_timeout_s, **common,
            )

        tr = _build_one(trace=True)
        pf = _build_one(trace=False)
    except _CanonicalBuildSourceStateError as e:
        return _abort(
            "build-source-state-error",
            f"{e.build_kind} build 直前の CCBench source state が不正 → reject ({e})",
            {"error": _exc_summary(e), "build_kind": e.build_kind},
        )
    except (RuntimeError, subprocess.SubprocessError) as e:
        # 例外要約を payload に載せる (D50 教訓): reason="build-error" だけだと WAL から
        # 失敗原因 (configure 即死か compile error か) を帰属できず調査が build dir の
        # 実地検分から始まる。identity-error の "error" キーと同じ語彙。
        return _abort("build-error", f"ビルド失敗 → reject ({e})",
                      {"error": _exc_summary(e)})
    toolchain_payload = {}
    if env_contract is not None:
        trace_toolchain = getattr(tr, "toolchain", None)
        perf_toolchain = getattr(pf, "toolchain", None)
        trace_manifest_sha256 = getattr(tr, "toolchain_manifest_sha256", None)
        perf_manifest_sha256 = getattr(pf, "toolchain_manifest_sha256", None)
        binding_required = (
            expected_toolchain_manifest is not None
            or declared_use_class == "official"
        )
        if trace_toolchain is not None or perf_toolchain is not None or binding_required:
            if trace_toolchain != perf_toolchain:
                return _abort(
                    "build-error",
                    "trace/perf build の toolchain が一致しない → reject",
                    {"error": "trace/perf toolchain binding mismatch"},
                )
            if (trace_manifest_sha256 != perf_manifest_sha256
                    and (trace_manifest_sha256 is not None
                         or perf_manifest_sha256 is not None)):
                return _abort(
                    "build-error",
                    "trace/perf build の toolchain manifest hash が一致しない → reject",
                    {"error": "trace/perf toolchain manifest hash mismatch"},
                )
            if binding_required and (
                    trace_toolchain is None or trace_manifest_sha256 is None):
                return _abort(
                    "build-error",
                    "v2 build の toolchain 観測値が欠落 → reject",
                    {"error": "toolchain observation missing"},
                )
            if trace_toolchain is not None and trace_manifest_sha256 is not None:
                toolchain_payload = {
                    "toolchain": trace_toolchain,
                    # buildcache._v2_identity の pre-image hash とは異なる、full
                    # version を含む campaign 実行証跡用 hash。
                    "toolchain_record_sha256": trace_manifest_sha256,
                }
    # trace_bin/perf_bin (16 文字) は sha256-prefix-16 / legacy-display-only (過去 WAL との
    # 対称性維持で不変)。trace_bin_sha256/perf_bin_sha256 (exact 64 lowercase hex) が照合系列。
    build_done_payload = {
        "trace_bin": tr.bin_hash, "perf_bin": pf.bin_hash,
        "build_attempt_id": build_attempt_id,
        "build_admission_receipt_sha256": admission.receipt_sha256,
        "trace_bin_sha256": tr.bin_sha256, "perf_bin_sha256": pf.bin_sha256,
        "trace_cached": tr.cached, "perf_cached": pf.cached,
        # fitness 計測に使う perf (trace-disabled) build の再現コマンド (規律1)。
        "perf_configure_cmd": pf.configure_cmd, "perf_build_cmd": pf.build_cmd,
    }
    build_done_payload.update(toolchain_payload)
    emit(layout, v, STAGE_BUILD_DONE, env_tag, build_done_payload)
    log(f"  [eval {v}] built trace={tr.bin_hash}{'(cache)' if tr.cached else ''} "
        f"perf={pf.bin_hash}{'(cache)' if pf.cached else ''}")

    # --- pre-run binary gate (A-1): 期待値が渡されたときだけ、両ビルド完了直後・trace/bench
    #     起動前に perf バイナリの (build 時に計算済みの) full sha256 を期待値と厳密照合する。
    #     再読・再ハッシュはしない (A-4: bin_sha256 が単一ソース)。期待値の形不正 (exact 64
    #     lowercase hex 以外) も受理せず、mismatch は trace/bench を一切起動せず fails-closed で
    #     abort する。expected_perf_sha256 の供給元 (ratified v2 の期待値取得) は今回未配線 —
    #     デフォルト None では従来と完全同一挙動。
    if expected_perf_sha256 is not None:
        if (not buildcache.is_full_sha256(expected_perf_sha256)
                or pf.bin_sha256 != expected_perf_sha256):
            return _abort(
                "bench-binary-mismatch",
                "perf バイナリ sha256 が期待値と不一致/期待値の形不正 → reject "
                "(trace/bench 未起動)",
                {"expected": expected_perf_sha256,
                 "actual": pf.bin_sha256,
                 "path": pf.binary})

    # build の site gate は fresh build でしか発火しない。legacy/v2 cache hit 後も、
    # 実際に trace/throughput を作る producer へ進む直前に現在 site を再検査する。
    _require_measurement_site("campaign trace/throughput producer")

    if qualification_policy is None:
        receipt_sink_kind = CAMPAIGN_WAL_SINK
        receipt_lock_identity = campaign_lock_sha256_or_absent(layout)
    else:
        receipt_sink_kind = QUALIFICATION_SINK
        receipt_lock_identity = (
            qualification_policy.event_sink.commit_lock_identity_sha256
        )

    # --- verify (正しさゲート, 絶対規律2)。legacy (既定・軽量) + extra_correctness
    #     (S2 等・bench 並みの負荷) を順に全て通す (verify 2 本立て, D36 決定2/4) ---
    verification_capabilities = []

    def _project_repetition_outcome(
            tag: str, outcome: _RepetitionExecutionOutcome,
    ) -> Optional[EvalResult]:
        """Preserve local verify_done, abort, and capability ordering."""
        res.verify_result = None
        # Every repetition owns the visible verdict.  A remote pre-verifier
        # abort must not retain rep 0's successful verdict.
        res.verdict = ""
        if outcome.verify_payload is not None:
            verify_payload = outcome.verify_payload
            res.verdict = str(verify_payload["verdict"])
            emit(layout, v, STAGE_VERIFY_DONE, env_tag, verify_payload)
            log(
                f"  [eval {v}] verify[{tag}]: {verify_payload['verdict']} "
                f"({verify_payload['commits']} commits, "
                f"{verify_payload['aborts']} aborts, "
                f"{verify_payload['anomalies']} anomalies)"
            )
        if outcome.abort is not None:
            rejected = outcome.abort
            return _abort(
                rejected.reason, rejected.message, rejected.detail,
                workload_tag=rejected.workload_tag,
                verify_result=outcome.verify_result,
            )
        if outcome.verification_capability is None:
            raise AssertionError("successful verification has no capability")
        verification_capabilities.append(outcome.verification_capability)
        return None

    def _run_one_repetition(
            tag: str, workload: CorrectnessWorkload,
            pass_numactl: Optional[Sequence[str]],
    ) -> Optional[EvalResult]:
        """1 verify repetition を通す。成功 capability は呼出し順に保持する。"""
        # 前パスの verdict を持ち越さない (敵対レビュー 2026-07-09 で確認): このパスが
        # verify_trace_dir に到達する前に reject されたら res.verdict は空のまま返る
        # (前パスが certified で 'serializable' 等を残していても、今回 abort する結果に
        # 古い verdict を紛れ込ませない)。到達すれば下で今回の verdict に上書きされる。
        res.verdict = ""
        # TMPDIR 配下 (明示されていなければ環境既定の /tmp)。
        tdir = tempfile.mkdtemp(prefix=f"izanagi_eval_trace_{tag}_")
        outcome = None
        try:
            outcome = _execute_verification_repetition(
                tr.binary, tdir, workload.flags, clocks_per_us,
                timeout_s=TRACE_TIMEOUT_S, numactl=pass_numactl,
                genome=genome, source_evidence=evidence,
                build_admission=admission, receipt_sink_kind=receipt_sink_kind,
                receipt_lock_identity_sha256=receipt_lock_identity,
                receipt_variant=v,
                receipt_operation_identity=build_attempt_id,
                receipt_workload_tag=tag,
                build_attempt_id=build_attempt_id,
                trace_binary_sha256=tr.bin_sha256,
                include_qualification_evidence=(qualification_policy is not None),
                payload_binary=tr.binary,
            )
            return _project_repetition_outcome(tag, outcome)
        finally:
            preserved = True
            archive_root = os.environ.get("IZANAGI_TRACE_ARCHIVE_ROOT")
            if archive_root is not None:
                try:
                    _preserve_trace_directory(
                        tdir, archive_root,
                        campaign_id=os.path.basename(os.path.normpath(layout.root)),
                        variant=v, build_attempt_id=build_attempt_id, tag=tag,
                        workload_flags=workload.flags, genome=genome,
                        trace_binary_sha256=tr.bin_sha256,
                        commit_count_witness=(None if outcome is None else outcome.commit_count_witness),
                        evidence=evidence,
                    )
                except Exception as exc:
                    preserved = False
                    print(f"trace preservation failed; original retained at {tdir}: {exc}",
                          file=sys.stderr)
            if preserved:
                shutil.rmtree(tdir, ignore_errors=True)

    def _run_one_pass(tag: str, workload: CorrectnessWorkload,
                      pass_numactl: Optional[Sequence[str]]) -> Optional[EvalResult]:
        """1 verify 構成の全 repetition を通す。1 件でも失敗すれば即 reject。"""
        if type(workload.reps) is not int or workload.reps <= 0:
            raise ValueError("correctness workload reps must be a positive exact integer")
        for _repetition in range(workload.reps):
            aborted = _run_one_repetition(tag, workload, pass_numactl)
            if aborted is not None:
                return aborted
        return None

    def _run_local_concurrent_pass(
            tag: str, workload: CorrectnessWorkload,
            pass_numactl: Optional[Sequence[str]],
    ) -> Optional[EvalResult]:
        """Collect in order, verify in forked children, and project in rep order."""
        if type(workload.reps) is not int or workload.reps <= 0:
            raise ValueError("correctness workload reps must be a positive exact integer")
        if workload.reps == 1:
            return _run_one_pass(tag, workload, pass_numactl)
        collected: list[tuple[str, Optional[_TraceRunResult],
                              Optional[_RepetitionExecutionOutcome]]] = []
        children: dict[int, int] = {}  # Only direct children not yet reaped.
        groups: set[int] = set()  # Groups may outlive their reaped leaders.
        tasks: dict[int, tuple[dict[str, Any], str, bytes]] = {}
        finished: dict[int, _RepetitionExecutionOutcome] = {}
        acquisition_failure: Optional[int] = None
        workdir = tempfile.mkdtemp(prefix="izanagi_verify_local_")

        def unavailable(rep: int, detail: str) -> _RepetitionExecutionOutcome:
            return _RepetitionExecutionOutcome(abort=_RepetitionAbortOutcome(
                "verify-local-unavailable",
                f"local verify result を確定できない (rep={rep}) → reject",
                {"local": {"rep": rep, "error": detail[-2000:]}}, tag,
            ))

        def child(rep: int, trace_dir: str, trace: _TraceRunResult,
                  task: dict[str, Any], result_path: str, secret: bytes) -> None:
            try:
                # The verifier forks pool workers.  Give this repetition a
                # separate group before any of those workers can start.
                os.setpgid(0, 0)
                outcome = _execute_verification_repetition(
                    tr.binary, trace_dir, workload.flags, clocks_per_us,
                    timeout_s=TRACE_TIMEOUT_S, numactl=pass_numactl,
                    genome=genome, source_evidence=evidence,
                    build_admission=admission, receipt_sink_kind=receipt_sink_kind,
                    receipt_lock_identity_sha256=receipt_lock_identity,
                    receipt_variant=v, receipt_operation_identity=build_attempt_id,
                    receipt_workload_tag=tag, build_attempt_id=build_attempt_id,
                    trace_binary_sha256=tr.bin_sha256,
                    include_qualification_evidence=False,
                    payload_binary=tr.binary, collected_trace_result=trace,
                )
                if outcome.abort is None:
                    payload = outcome.verify_payload
                    receipt = serialize_remote_verification_receipt(
                        outcome.verification_capability,
                        task_sha256=task["task_sha256"],
                        verify_payload_sha256=_json_sha256(payload),
                    )
                    wire = {"kind": "success", "verify_payload": payload,
                            "remote_verification_receipt": receipt}
                else:
                    rejected = outcome.abort
                    wire = {
                        "kind": "abort", "reason": rejected.reason,
                        "message": rejected.message, "detail": rejected.detail,
                        "workload_tag": tag, "verify_payload": outcome.verify_payload,
                    }
                result = {
                    "schema": _VERIFY_FANOUT_RESULT_SCHEMA,
                    "task_sha256": task["task_sha256"],
                    "build_attempt_id": build_attempt_id, "tag": tag,
                    "rep": rep, "trace_bin_sha256": tr.bin_sha256,
                    "outcome": wire,
                }
                result["result_mac"] = hmac.new(
                    secret, _canonical_json_bytes(result), hashlib.sha256,
                ).hexdigest()
                _write_create_only_json(result_path, result)
                os._exit(0)
            except BaseException:
                os._exit(1)

        def kill_group(pid: int) -> None:
            # Call while the direct child is still owned (possibly a zombie),
            # so its PID cannot have been reused for an unrelated group.
            try:
                os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

        def wait_group_gone(pid: int) -> None:
            # Forked verifier workers must be gone before preserving traces.
            deadline = time.monotonic() + 5.0
            while True:
                try:
                    os.killpg(pid, 0)
                except ProcessLookupError:
                    return
                if time.monotonic() >= deadline:
                    raise RuntimeError(f"local verifier process group {pid} survived SIGKILL")
                time.sleep(0.01)

        try:
            for rep in range(workload.reps):
                trace_dir = tempfile.mkdtemp(prefix=f"izanagi_eval_trace_{tag}_")
                collected.append((trace_dir, None, None))
                trace, failure = _collect_verification_trace(
                    tr.binary, trace_dir, workload.flags, clocks_per_us,
                    timeout_s=TRACE_TIMEOUT_S, numactl=pass_numactl,
                    receipt_workload_tag=tag, trace_runner=_run_trace,
                )
                collected[rep] = (trace_dir, trace, failure)
                if failure is not None:
                    acquisition_failure = rep
                    break
            for rep, (trace_dir, trace, _failure) in enumerate(collected):
                if trace is None:
                    break
                body = {
                    "schema": "verify-local-task/v1",
                    "campaign_lock_sha256": receipt_lock_identity,
                    "variant": v, "build_attempt_id": build_attempt_id,
                    "tag": tag, "rep": rep,
                    "trace_bin_sha256": tr.bin_sha256,
                    "trace_dir": trace_dir,
                    "expected_commits": trace.commit_count_witness,
                }
                task = {**body, "task_sha256": _json_sha256(body),
                        "receipt_sink_kind": receipt_sink_kind}
                secret = secrets.token_bytes(32)
                result_path = os.path.join(workdir, f"result-{rep}.json")
                try:
                    pid = os.fork()
                except OSError as exc:
                    acquisition_failure = rep
                    finished[rep] = unavailable(rep, _exc_summary(exc))
                    break
                if pid == 0:
                    child(rep, trace_dir, trace, task, result_path, secret)
                    os._exit(1)
                children[rep] = pid
                groups.add(pid)
                try:
                    os.setpgid(pid, pid)
                except (ProcessLookupError, PermissionError):
                    # The child either already exited or won the setpgid race.
                    pass
                tasks[rep] = task, result_path, secret

            failure_rep = acquisition_failure
            admitted: set[str] = set()
            statuses: dict[int, int] = {}
            next_rep = 0
            while children:
                progress = False
                for rep, pid in list(children.items()):
                    observed = os.waitid(
                        os.P_PID, pid, os.WEXITED | os.WNOHANG | os.WNOWAIT,
                    )
                    if observed is None:
                        continue
                    progress = True
                    kill_group(pid)
                    _, status = os.waitpid(pid, 0)
                    del children[rep]
                    wait_group_gone(pid)
                    groups.discard(pid)
                    statuses[rep] = os.waitstatus_to_exitcode(status)
                while next_rep in statuses and (
                        failure_rep is None or next_rep < failure_rep):
                    rep = next_rep
                    task, result_path, secret = tasks[rep]
                    rc = statuses.pop(rep)
                    outcome = _admit_verify_fanout_result(
                        task, host="local", result_path=result_path,
                        launch_result=subprocess.CompletedProcess([], rc, "", ""),
                        result_secret=secret, admitted_task_sha256s=admitted,
                    )
                    if (outcome.abort is not None
                            and outcome.abort.reason == "verify-remote-unavailable"):
                        outcome = unavailable(rep, repr(outcome.abort.detail))
                    finished[rep] = outcome
                    if outcome.abort is not None:
                        failure_rep = rep if failure_rep is None else min(failure_rep, rep)
                    next_rep += 1
                if failure_rep is not None:
                    for rep, pid in list(children.items()):
                        if rep > failure_rep:
                            kill_group(pid)
                            os.waitpid(pid, 0)
                            del children[rep]
                            wait_group_gone(pid)
                            groups.discard(pid)
                if not progress and children:
                    time.sleep(0.01)
            limit = failure_rep if failure_rep is not None else len(collected) - 1
            for rep in range(limit + 1):
                outcome = collected[rep][2] or finished[rep]
                aborted = _project_repetition_outcome(tag, outcome)
                if aborted is not None:
                    return aborted
            return None
        finally:
            for rep, pid in list(children.items()):
                kill_group(pid)
                os.waitpid(pid, 0)
                del children[rep]
            for pid in list(groups):
                wait_group_gone(pid)
                groups.discard(pid)
            for trace_dir, trace, failure in collected:
                preserved = True
                archive_root = os.environ.get("IZANAGI_TRACE_ARCHIVE_ROOT")
                if archive_root is not None:
                    try:
                        _preserve_trace_directory(
                            trace_dir, archive_root,
                            campaign_id=os.path.basename(os.path.normpath(layout.root)),
                            variant=v, build_attempt_id=build_attempt_id, tag=tag,
                            workload_flags=workload.flags, genome=genome,
                            trace_binary_sha256=tr.bin_sha256,
                            commit_count_witness=(
                                failure.commit_count_witness if failure is not None
                                else trace.commit_count_witness if trace is not None else None
                            ), evidence=evidence,
                        )
                    except Exception as exc:
                        preserved = False
                        print(f"trace preservation failed; original retained at {trace_dir}: {exc}",
                              file=sys.stderr)
                if preserved:
                    shutil.rmtree(trace_dir, ignore_errors=True)
            shutil.rmtree(workdir, ignore_errors=True)

    def _run_fanout_pass(
            tag: str, workload: CorrectnessWorkload,
            pass_numactl: Optional[Sequence[str]],
    ) -> Optional[EvalResult]:
        """Run rep 0 locally and later reps on sibling hosts in bounded waves."""
        if type(workload.reps) is not int or workload.reps <= 0:
            raise ValueError("correctness workload reps must be a positive exact integer")
        if workload.reps == 1:
            return _run_one_repetition(tag, workload, pass_numactl)

        try:
            (
                expected_repo_head,
                contract_loader_blob_sha256s,
            ) = _campaign_lock_contract_loader_binding(layout)
        except Exception as exc:
            return _abort(
                "verify-remote-unavailable",
                f"campaign lock の remote closure を確定できない "
                f"({tag}) → reject",
                {"remote": {
                    "host": verify_fanout_hosts[0], "rep": 1, "rc": None,
                    "stderr_tail": _exc_summary(exc)[-2000:],
                }},
                workload_tag=tag,
            )
        parent = os.path.join(layout.root, "verify-fanout", v)
        os.makedirs(parent, mode=0o700, exist_ok=True)
        tasks: dict[
            int, tuple[str, str, str, dict[str, Any], bytes]
        ] = {}
        for rep in range(1, workload.reps):
            host = verify_fanout_hosts[(rep - 1) % len(verify_fanout_hosts)]
            leaf_name = f"{tag}-{rep}"
            if (_VERIFY_FANOUT_COMPONENT_RE.fullmatch(v) is None
                    or _VERIFY_FANOUT_COMPONENT_RE.fullmatch(tag) is None):
                return _abort(
                    "verify-remote-unavailable",
                    f"fan-out evidence path identity が不正 ({tag}, rep={rep}) → reject",
                    {"remote": {
                        "host": host, "rep": rep, "rc": None,
                        "stderr_tail": "unsafe fan-out path component",
                    }},
                    workload_tag=tag,
                )
            leaf = os.path.join(parent, leaf_name)
            try:
                os.mkdir(leaf, 0o700)
                task = _make_verify_fanout_task(
                    campaign_lock_sha256=receipt_lock_identity,
                    variant=v,
                    build_attempt_id=build_attempt_id,
                    tag=tag,
                    rep=rep,
                    trace_binary=tr.binary,
                    trace_bin_sha256=tr.bin_sha256,
                    workload_flags=workload.flags,
                    clocks_per_us=clocks_per_us,
                    numactl_prefix=tuple(pass_numactl or ()),
                    genome=genome,
                    source_evidence=evidence,
                    build_admission=admission,
                    receipt_sink_kind=receipt_sink_kind,
                    expected_repo_head=expected_repo_head,
                    contract_loader_blob_sha256s=(
                        contract_loader_blob_sha256s
                    ),
                    generator_id=build_context.generator_id,
                )
                task_path = os.path.join(leaf, "task.json")
                result_path = os.path.join(leaf, "result.json")
                _write_create_only_json(task_path, task)
                result_secret = secrets.token_bytes(32)
            except Exception as exc:
                return _abort(
                    "verify-remote-unavailable",
                    f"remote verify task を publish できない "
                    f"(host={host}, rep={rep}) → reject",
                    {"remote": {
                        "host": host, "rep": rep, "rc": None,
                        "stderr_tail": _exc_summary(exc)[-2000:],
                    }},
                    workload_tag=tag,
                )
            tasks[rep] = (
                host, task_path, result_path, task, result_secret,
            )

        launcher = verify_fanout_launcher or _default_verify_fanout_launcher
        next_rep = 1
        local_done = False
        admitted_task_sha256s: set[str] = set()
        while next_rep < workload.reps:
            wave_reps = tuple(
                range(next_rep, min(next_rep + len(verify_fanout_hosts), workload.reps))
            )
            launch_results: dict[int, object] = {}
            local_aborted: Optional[EvalResult] = None
            with ThreadPoolExecutor(max_workers=len(wave_reps)) as pool:
                futures = {
                    rep: pool.submit(
                        launcher, tasks[rep][0], tasks[rep][1], tasks[rep][2],
                        tasks[rep][4],
                    )
                    for rep in wave_reps
                }
                if not local_done:
                    local_aborted = _run_one_repetition(
                        tag, workload, pass_numactl,
                    )
                    local_done = True
                for rep in wave_reps:
                    try:
                        launch_results[rep] = futures[rep].result()
                    except Exception as exc:
                        launch_results[rep] = subprocess.CompletedProcess(
                            args=[], returncode=255, stdout="",
                            stderr=_exc_summary(exc),
                        )
            if local_aborted is not None:
                return local_aborted
            for rep in wave_reps:
                host, _task_path, result_path, task, result_secret = tasks[rep]
                outcome = _admit_verify_fanout_result(
                    task, host=host, result_path=result_path,
                    launch_result=launch_results[rep],
                    result_secret=result_secret,
                    admitted_task_sha256s=admitted_task_sha256s,
                )
                aborted = _project_repetition_outcome(tag, outcome)
                if aborted is not None:
                    return aborted
            next_rep += len(wave_reps)
        return None

    # baseline が古い場合は screening を無効化し、通常の verify-first 経路へ倒す。
    # 再アンカーは driver の責務であり、evaluate() は古い基準による偽棄却をしない。
    active_screening = screening
    screening_disabled_payload: Optional[Dict] = None
    if screening is not None:
        baseline_age_s = time.time() - screening.baseline_measured_at
        if baseline_age_s > screening.reanchor_threshold_s:
            active_screening = None
            screening_disabled_payload = {
                "screening_disabled": {
                    "reason": "stale-baseline",
                    "age_s": baseline_age_s,
                    "threshold_s": screening.reanchor_threshold_s,
                    "baseline_ref": screening.baseline_ref,
                }
            }
            res.notes.append(
                "stale-baseline: baseline age "
                f"{baseline_age_s:.3f}s exceeds reanchor threshold "
                f"{screening.reanchor_threshold_s:.3f}s; screening disabled")

    # screening 経路だけ bench を先行する。測定不能/CV 不定は _run_bench の既存 reason で
    # abort。unstable・abort率欠損・high-abort は曖昧側なので棄却せず verify へ送る。
    bench: Optional[_BenchResult] = None
    if active_screening is not None:
        aborted_result, bench = _run_bench(
            pf.binary, perf, clocks_per_us, numactl, do_settle,
            layout, v, env_tag, _abort, log, screening=True,
            build_attempt_id=build_attempt_id,
            bench_max_rounds=bench_max_rounds,
            record_rep_returncodes=record_rep_returncodes,
        record_rep_integer_counters=record_rep_integer_counters,
            holdout_observation_admission=holdout_observation_admission,
            use_perf=use_perf,
            perf_preflight_receipt=perf_preflight_receipt,
            **({"verify_performance_concurrent": True}
               if verify_performance_concurrent else {}))
        if aborted_result is not None:
            return aborted_result
        assert bench is not None
        screen_reject = False
        if not bench.unstable:
            abort_rate = bench.leading_indicators.get("abort_rate")
            if abort_rate is not None:
                high_abort = abort_rate > (active_screening.baseline_abort_rate *
                                           active_screening.high_abort_factor)
                if not high_abort:
                    threshold = active_screening.baseline_tps * (
                        1 - active_screening.k * active_screening.floor)
                    screen_reject = bench.median_tps < threshold
        if screen_reject:
            return _abort(
                SCREEN_REJECTION_REASON,
                "bench-first screening の保守床を明白に下回る → uncertified reject",
                {"screen": {
                    "median_tps": bench.median_tps,
                    "cv": bench.cv,
                    "baseline_tps": active_screening.baseline_tps,
                    "baseline_ref": active_screening.baseline_ref,
                    "floor": active_screening.floor,
                    "k": active_screening.k,
                    "margin": bench.median_tps / active_screening.baseline_tps - 1,
                }})

    verify_tags: List[str] = []
    verification_receipt_tags: List[str] = []
    for tag, workload, fullscale_isolated in passes:
        # 各パス開始時・probe より前で前パスの verdict を消去する (B-4)。probe (競合検知)
        # や competing-tenant で _run_one_pass に到達せず abort する場合、_run_one_pass 内の
        # 消去が走らず前パスの 'serializable' が aborted 結果へ持ち越されるのを防ぐ。
        res.verdict = ""
        if fullscale_isolated:
            # S2 相当は bench 並みの負荷 → bench と同じ排他下で回す (D36 決定4-4)。
            # 後段の bench 用 bench_lock とはネストしない (逐次 = 別セクションで別途取得、
            # 同一プロセス内での flock 二重取得によるデッドロックを避ける)。
            with bench_lock():
                # bench 本体と同じ admission (絶対規律4、敵対レビュー 2026-07-09 で確認):
                # bench_lock は izanagi 自身の bench 同士しか排他せず、孤児化した子・
                # 他者が手起動した ycsb は掴まない。S2 は bench 並みの全規模 run ゆえ
                # 同じ汚染源に晒される — pgrep で直接確認し fails-closed で reject する。
                try:
                    comp = competing_bench_pids()
                except CompetingBenchProbeError as e:
                    # probe (pgrep) 実行失敗 → 競合の有無を確定できず reject。専用 reason +
                    # 構造化 probe_error payload (規律3/4, B-6)。retryable 扱い (B-3)。
                    aborted_result = _abort(
                        "verify-probe-error",
                        f"競合検知 probe (pgrep) 実行失敗 → S2 相当の verify ({tag}) は"
                        "競合の有無を確定できず reject (環境故障・再評価可能, 規律3/4)",
                        {"probe_error": e.as_dict()}, workload_tag=tag)
                else:
                    if comp:
                        aborted_result = _abort(
                            "verify-competing-tenant",
                            f"競合 ccbench ベンチを検知 → S2 相当の verify ({tag}) は汚染"
                            "計測のまま採用せず reject (規律4)",
                            {"competing": comp}, workload_tag=tag)
                    else:
                        if (verify_performance_concurrent
                                and tag == PERFORMANCE_TAG
                                and receipt_sink_kind == CAMPAIGN_WAL_SINK):
                            aborted_result = _run_local_concurrent_pass(
                                tag, workload, numactl,
                            )
                        elif (verify_fanout_hosts
                                and tag == PERFORMANCE_TAG
                                and receipt_sink_kind == CAMPAIGN_WAL_SINK
                                and build_context.generator_id
                                is GeneratorId.BACKOFF_REPRO):
                            aborted_result = _run_fanout_pass(
                                tag, workload, numactl,
                            )
                        else:
                            aborted_result = _run_one_pass(
                                tag, workload, numactl,
                            )
        else:
            aborted_result = _run_one_pass(tag, workload, None)
        if aborted_result is not None:
            return aborted_result
        verify_tags.append(tag)
        verification_receipt_tags.extend([tag] * workload.reps)
    res.certified = True

    def _receipt_for(payload: Dict):
        return issue_commit_receipt(
            verification_capabilities,
            workload_tags=verification_receipt_tags,
            sink_kind=receipt_sink_kind,
            lock_identity_sha256=receipt_lock_identity,
            variant=v,
            operation_identity=build_attempt_id,
            terminal_payload=payload,
        )

    if not res.certified:
        raise AssertionError("verify 完了前の非認証結果は prepare 完了へ到達できない")
    return _PreparedEvaluation(
        result=res,
        layout=layout,
        env_tag=env_tag,
        perf_binary=pf.binary,
        perf=perf,
        clocks_per_us=clocks_per_us,
        numactl=numactl,
        do_bench=do_bench,
        do_settle=do_settle,
        log=log,
        abort=_abort,
        emit=emit,
        build_attempt_id=build_attempt_id,
        build_admission_receipt_sha256=admission.receipt_sha256,
        contract_sha256=authorized_contract.contract_sha256,
        verify_tags=verify_tags,
        receipt_for=_receipt_for,
        bench_max_rounds=bench_max_rounds,
        record_rep_returncodes=record_rep_returncodes,
        record_rep_integer_counters=record_rep_integer_counters,
        qualification_policy=qualification_policy,
        holdout_observation_admission=holdout_observation_admission,
        use_perf=use_perf,
        perf_preflight_receipt=perf_preflight_receipt,
        active_screening=active_screening,
        screening_disabled_payload=screening_disabled_payload,
        bench=bench,
        verify_performance_concurrent=verify_performance_concurrent,
    )


def _bench_prepared(
        prepared: _PreparedEvaluation,
) -> EvalResult | _BenchResult | None:
    """Run the legacy lock-owning bench phase for one prepared evaluation."""
    if type(prepared) is not _PreparedEvaluation:
        raise TypeError("prepared must be an exact _PreparedEvaluation")
    if not prepared.do_bench:
        return None
    if prepared.bench is not None:
        return prepared.bench
    policy = prepared.qualification_policy
    aborted, bench = _run_bench(
        prepared.perf_binary, prepared.perf, prepared.clocks_per_us,
        prepared.numactl, prepared.do_settle,
        prepared.layout, prepared.result.variant, prepared.env_tag,
        prepared.abort, prepared.log,
        build_attempt_id=prepared.build_attempt_id,
        bench_payload_extra=prepared.screening_disabled_payload,
        bench_max_rounds=prepared.bench_max_rounds,
        record_rep_returncodes=prepared.record_rep_returncodes,
        **({"record_rep_integer_counters": True}
           if prepared.record_rep_integer_counters else {}),
        bench_timeout_s=(policy.bench_timeout_s if policy is not None else None),
        require_all_reps=policy is not None,
        require_settled=(policy.require_settled if policy is not None else False),
        emit=prepared.emit,
        holdout_observation_admission=prepared.holdout_observation_admission,
        use_perf=prepared.use_perf,
        perf_preflight_receipt=prepared.perf_preflight_receipt,
        **({"verify_performance_concurrent": True}
           if prepared.verify_performance_concurrent else {}),
    )
    if aborted is not None:
        return aborted
    assert bench is not None
    prepared.bench = bench
    return bench


def _commit_prepared(
        prepared: _PreparedEvaluation, bench: Optional[_BenchResult],
) -> EvalResult:
    """Commit one verified evaluation after its optional bench has completed."""
    if type(prepared) is not _PreparedEvaluation:
        raise TypeError("prepared must be an exact _PreparedEvaluation")
    res = prepared.result
    if not res.certified or res.aborted:
        raise ValueError("only a certified non-aborted evaluation can commit")
    if prepared.do_bench and type(bench) is not _BenchResult:
        raise ValueError("bench result is required before a measured commit")
    if not prepared.do_bench and bench is not None:
        raise ValueError("no-bench evaluation cannot accept a bench result")

    if bench is None:
        commit_payload = {
            "fitness_tps": None,
            "note": "no-bench",
            "verify_configs": prepared.verify_tags,
            "build_attempt_id": prepared.build_attempt_id,
            "build_admission_receipt_sha256": (
                prepared.build_admission_receipt_sha256
            ),
        }
    else:
        res.fitness_tps, res.cv, res.unstable = (
            bench.median_tps, bench.cv, bench.unstable,
        )
        commit_payload = {
            "fitness_tps": bench.median_tps,
            "cv": bench.cv,
            "high_variance": bench.high_variance,
            "unstable": bench.unstable,
            "verify_configs": prepared.verify_tags,
            "build_attempt_id": prepared.build_attempt_id,
            "build_admission_receipt_sha256": (
                prepared.build_admission_receipt_sha256
            ),
        }
        if prepared.active_screening is not None:
            commit_payload["screened"] = True

    _require_measurement_site("campaign COMMIT 記録")
    if prepared.qualification_policy is None:
        wal_payload = {
            **commit_payload,
            COMMIT_CONTRACT_SHA256_KEY: prepared.contract_sha256,
        }
        wal.log(
            prepared.layout, res.variant, STAGE_COMMIT, prepared.env_tag,
            wal_payload,
            commit_receipt=prepared.receipt_for(wal_payload),
        )
    else:
        prepared.qualification_policy.event_sink.emit(
            prepared.layout, res.variant, STAGE_COMMIT, prepared.env_tag,
            commit_payload,
            commit_receipt=prepared.receipt_for(commit_payload),
        )
    return res


def _compress_trace_archive(stream, compressed) -> None:
    """Launch only the archive compressor; keep its failure seam local."""
    subprocess.run(["zstd", "-T0", "-3"], stdin=stream,
                   stdout=compressed, stderr=subprocess.PIPE, check=True)


def _archive_git(root: str, subcommand: str) -> bytes:
    """Read an archival HEAD or binary patch with an isolated Git environment."""
    if subcommand == "head":
        argv = ["rev-parse", "HEAD"]
    elif subcommand == "diff":
        argv = ["diff", "--binary", "HEAD", "--"]
    else:
        raise ValueError("unsupported archive git subcommand")
    return subprocess.run(
        ["git", "-C", root, *argv], check=True, capture_output=True,
        env=_sanitized_git_env(),
    ).stdout


def _preserve_trace_directory(
        tdir: str, archive_root: str, *, campaign_id: str, variant: str,
        build_attempt_id: str, tag: str, workload_flags: Mapping,
        genome: Genome, trace_binary_sha256: str,
        commit_count_witness: Optional[int] = None,
        evidence: Optional[SourceEvidence] = None,
) -> None:
    """Archive one local repetition; failures propagate to the cleanup boundary.

    inventory.json is published as complete only after all compressed files exist.
    It is an archival index, never verification or certification evidence.
    """
    if not os.path.isabs(archive_root):
        raise ValueError("IZANAGI_TRACE_ARCHIVE_ROOT must be absolute")
    destination = os.path.join(archive_root, campaign_id, variant,
                               build_attempt_id, tag, os.path.basename(tdir))
    inventory = {
        "status": "incomplete", "original_directory": tdir,
        "workload_flags": dict(workload_flags), "genome": genome.canonical(),
        "trace_binary_sha256": trace_binary_sha256, "files": [],
        "verifier_invocation": "in-process", "verifier_argv": None,
        "repo_head": None, "ccbench_pin": None, "ccbench_pin_declared": None,
        "patch_sha256": None, "patch_path": None, "patch_bytes": None,
        "tracked_diff_sha256": None, "verifier_module_sha256": None,
    }
    os.makedirs(destination, exist_ok=False)
    inventory_path = os.path.join(destination, "inventory.json")
    try:
        if not os.path.isdir(tdir):
            raise FileNotFoundError(tdir)

        def walk_error(error):
            raise error

        for directory, dirs, files in os.walk(tdir, onerror=walk_error):
            dirs.sort()
            for name in sorted(files):
                source = os.path.join(directory, name)
                relative = os.path.relpath(source, tdir)
                archive_relative = os.path.join("archive", relative + ".zst")
                archive = os.path.join(destination, archive_relative)
                os.makedirs(os.path.dirname(archive), exist_ok=True)
                digest = hashlib.sha256()
                size = lines = 0
                last = b""
                with open(source, "rb") as stream:
                    while chunk := stream.read(1024 * 1024):
                        digest.update(chunk)
                        size += len(chunk)
                        lines += chunk.count(b"\n")
                        last = chunk[-1:]
                lines += int(bool(last) and last != b"\n")
                row = {"path": relative, "sha256": digest.hexdigest(),
                       "bytes": size, "lines": lines,
                       "archive_path": archive_relative, "status": "incomplete"}
                inventory["files"].append(row)
                partial = archive + ".partial"
                with open(source, "rb") as stream, open(partial, "xb") as compressed:
                    _compress_trace_archive(stream, compressed)
                os.replace(partial, archive)
                row.update(status="complete", compressed_bytes=os.path.getsize(archive))
        repo_root = os.path.realpath(os.path.join(os.path.dirname(__file__), "../.."))
        inventory["repo_head"] = _archive_git(repo_root, "head").decode().strip()
        verifier_root = Path(repo_root) / "orchestrator" / "verifier"
        inventory["verifier_module_sha256"] = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(verifier_root.glob("*.py"))
        }
        if evidence is not None:
            inventory["ccbench_pin_declared"] = evidence.ccbench_commit
            inventory["tracked_diff_sha256"] = evidence.tracked_diff_sha256
            if commit_count_witness is not None:
                inventory["verifier_argv"] = [
                    os.path.realpath(sys.executable), "-B", "-m", "orchestrator.verifier",
                    tdir, "--json", "--expected-commits", str(commit_count_witness),
                    "--protocol", genome.protocol, "--ccbench-root", evidence.source_root,
                ]
            source_head = _archive_git(evidence.source_root, "head").decode().strip()
            inventory["ccbench_pin"] = source_head
            patch = _archive_git(evidence.source_root, "diff")
            inventory["patch_sha256"] = hashlib.sha256(patch).hexdigest()
            inventory["patch_bytes"] = len(patch)
            inventory["patch_path"] = "patch/ccbench.diff.zst"
            patch_archive = os.path.join(destination, inventory["patch_path"])
            os.makedirs(os.path.dirname(patch_archive), exist_ok=True)
            with tempfile.TemporaryFile() as patch_stream:
                patch_stream.write(patch)
                patch_stream.seek(0)
                with open(patch_archive + ".partial", "xb") as compressed:
                    _compress_trace_archive(patch_stream, compressed)
            os.replace(patch_archive + ".partial", patch_archive)
            if not evidence.ccbench_commit or not source_head.startswith(evidence.ccbench_commit):
                raise ValueError("archive source HEAD differs from source evidence")
            if inventory["patch_sha256"] != evidence.tracked_diff_sha256:
                raise ValueError("archive source patch differs from source evidence")
        inventory["status"] = "complete"
        with open(inventory_path, "x", encoding="utf-8") as stream:
            json.dump(inventory, stream, sort_keys=True)
    except Exception as exc:
        inventory.update(status="failed", error=str(exc))
        try:
            with open(inventory_path, "w", encoding="utf-8") as stream:
                json.dump(inventory, stream, sort_keys=True)
        except Exception:
            pass  # The caller reports the failure and keeps the original directory.
        raise


def evaluate(genome: Genome, layout: CampaignLayout, env_tag: str,
             ccbench_commit: str, perf: PerfConfig,
             clocks_per_us: int, numactl: Optional[Sequence[str]] = None,
             correctness: Optional[CorrectnessWorkload] = None,
             extra_correctness: Optional[Sequence[Tuple[str, CorrectnessWorkload]]] = None,
             do_bench: bool = True, do_settle: bool = True,
             src_token: Optional[str] = None, log=print,
             ccbench_dir: str = "", cache_root: str = "",
             screening: Optional[ScreeningConfig] = None,
             bench_max_rounds: int = 3,
             expected_perf_sha256: Optional[str] = None,
             env_contract: Optional[ExecutionEnvironmentContract] = None,
             record_rep_returncodes: bool = False,
             qualification_policy: Optional[QualificationPipelinePolicy] = None,
             dependency_prefix: str = "",
             fetchcontent_base_dir: str = "",
             masstree_source_dir: Optional[object] = None,
             mimalloc_source_dir: Optional[object] = None,
             googletest_source_dir: Optional[object] = None,
             fetchcontent_dependency_receipt: Optional[
                 Mapping[str, object]
             ] = None, *,
             record_rep_integer_counters: bool = False,
             authorization_contract: _env_contract.AuthorizedContract,
             build_context: BuildRunContext,
             capability_resolver: Optional[AdmissionCapabilityResolver] = None,
             source_evidence: Optional[SourceEvidence] = None,
             backoff_grammar_version: Optional[int] = None,
             sort_oracle_contract_id: Optional[str] = None,
             expected_toolchain_manifest: Optional[Mapping[str, object]] = None,
             declared_use_class: Optional[str] = None,
             trigger_gate_binding=None,
             holdout_observation_admission: Optional[
                 HoldoutObservationAdmission
             ] = None,
             use_perf: bool = True,
             perf_preflight_receipt: Optional[dict] = None,
             canonical_build_pin: Optional[str] = None,
             a1_source_context=None,
             verify_fanout_hosts: tuple[str, ...] = (),
             verify_fanout_launcher: Optional[Callable[..., object]] = None,
             verify_performance_concurrent: bool = False,
             ) -> EvalResult:
    """Preserve the historical evaluate API as prepare, bench, then commit."""
    if a1_source_context is not None and canonical_build_pin is None:
        raise ValueError("A1 source context requires canonical build pin")
    fetchcontent_prebuild = _validate_fetchcontent_prebuild_inputs(
        env_contract=env_contract,
        fetchcontent_base_dir=fetchcontent_base_dir,
        masstree_source_dir=masstree_source_dir,
        mimalloc_source_dir=mimalloc_source_dir,
        googletest_source_dir=googletest_source_dir,
        fetchcontent_dependency_receipt=fetchcontent_dependency_receipt,
    )
    if type(build_context) is not BuildRunContext:
        raise TypeError("build_context は build_run_context() 由来の exact value が必要")
    if expected_toolchain_manifest is not None and env_contract is None:
        raise ValueError(
            "expected_toolchain_manifest は env_contract 付き v2 build に限る"
        )
    if (trigger_gate_binding is not None
            and type(trigger_gate_binding) is not TriggerGateBinding):
        raise TypeError("trigger_gate_binding は exact TriggerGateBinding または None が必要")
    if capability_resolver is not None and not callable(capability_resolver):
        raise TypeError("capability_resolver は callable または None が必要")
    if type(use_perf) is not bool:
        raise TypeError("use_perf は bool でなければならない")
    if perf_preflight_receipt is None:
        if not use_perf:
            raise ValueError("use_perf=False には perf preflight receipt が必要")
    else:
        perf_preflight_receipt = (
            _perf_preflight.validate_perf_preflight_receipt(perf_preflight_receipt)
        )
    expected_use_perf = _perf_preflight.use_perf_from_receipt(
        perf_preflight_receipt
    )
    if use_perf is not expected_use_perf:
        raise ValueError("use_perf と perf preflight receipt が不一致")

    fetchcontent_options = {}
    if fetchcontent_prebuild:
        fetchcontent_options = {
            "fetchcontent_base_dir": fetchcontent_base_dir,
            "masstree_source_dir": masstree_source_dir,
            "mimalloc_source_dir": mimalloc_source_dir,
            "googletest_source_dir": googletest_source_dir,
            "fetchcontent_dependency_receipt": (
                fetchcontent_dependency_receipt
            ),
        }
    outcome = _prepare_evaluation_core(
        genome, layout, env_tag, ccbench_commit, perf, clocks_per_us,
        numactl=numactl, correctness=correctness,
        extra_correctness=extra_correctness, do_bench=do_bench,
        do_settle=do_settle, src_token=src_token, log=log,
        ccbench_dir=ccbench_dir, cache_root=cache_root, screening=screening,
        bench_max_rounds=bench_max_rounds,
        expected_perf_sha256=expected_perf_sha256, env_contract=env_contract,
        record_rep_returncodes=record_rep_returncodes,
        record_rep_integer_counters=record_rep_integer_counters,
        qualification_policy=qualification_policy,
        dependency_prefix=dependency_prefix,
        authorization_contract=authorization_contract,
        build_context=build_context,
        capability_resolver=capability_resolver,
        source_evidence=source_evidence,
        backoff_grammar_version=backoff_grammar_version,
        sort_oracle_contract_id=sort_oracle_contract_id,
        expected_toolchain_manifest=expected_toolchain_manifest,
        declared_use_class=declared_use_class,
        trigger_gate_binding=trigger_gate_binding,
        holdout_observation_admission=holdout_observation_admission,
        use_perf=use_perf,
        perf_preflight_receipt=perf_preflight_receipt,
        canonical_build_pin=canonical_build_pin,
        a1_source_context=a1_source_context,
        verify_fanout_hosts=verify_fanout_hosts,
        verify_fanout_launcher=verify_fanout_launcher,
        **({"verify_performance_concurrent": True}
           if verify_performance_concurrent else {}),
        **fetchcontent_options,
    )
    passes = (outcome,)
    for prepared in passes:
        if type(prepared) is EvalResult:
            return prepared
    assert type(outcome) is _PreparedEvaluation
    res = outcome.result
    # The prepare phase established this value from all verify passes.  Keep the
    # assignment at the compatibility boundary so every legacy COMMIT remains
    # syntactically and dynamically below the verification gate.
    res.certified = True
    bench = _bench_prepared(outcome)
    if type(bench) is EvalResult:
        return bench
    if not res.certified:
        raise AssertionError("verify completion was lost before commit")
    return _commit_prepared(outcome, bench)


def _prepare_evaluation(*args, **kwargs) -> EvalResult | _PreparedEvaluation:
    """Internal prepare-only split point after run_campaign perf preflight."""
    return _prepare_evaluation_core(*args, **kwargs)


def _exclusive_schedule_receipt(
        layout: CampaignLayout, name: str, receipt: Mapping[str, object],
) -> str:
    """Create the completed schedule receipt once; never replace prior bytes."""
    path = os.path.join(layout.root, name)
    payload = (
        json.dumps(receipt, sort_keys=True, separators=(",", ":"),
                   allow_nan=False)
        + "\n"
    ).encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        offset = 0
        while offset < len(payload):
            written = os.write(descriptor, payload[offset:])
            if written <= 0:
                raise OSError("short schedule receipt write")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    parent = os.open(
        layout.root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
    )
    try:
        os.fsync(parent)
    finally:
        os.close(parent)
    return path


def _abort_balanced_workload(
        prepared_arms: Sequence[_PreparedEvaluation], reason: str, note: str,
        extra: Optional[Dict] = None,
) -> Tuple[EvalResult, ...]:
    return tuple(
        prepared.abort(reason, note, dict(extra or {}))
        for prepared in prepared_arms
    )


def _run_balanced_schedule(
        prepared_arms: Sequence[_PreparedEvaluation],
        config: BalancedScheduleConfig,
) -> Tuple[Tuple[EvalResult, ...], dict]:
    """Measure two prepared arms under one lock and commit only after all blocks."""
    if type(config) is not BalancedScheduleConfig:
        raise TypeError("config must be an exact BalancedScheduleConfig")
    if (type(prepared_arms) not in {list, tuple}
            or len(prepared_arms) != 2
            or any(type(item) is not _PreparedEvaluation for item in prepared_arms)):
        raise ValueError("balanced schedule requires exactly two prepared evaluations")
    if any(item.record_rep_integer_counters for item in prepared_arms):
        raise ValueError("balanced schedule does not support record_rep_integer_counters")
    arm_map = {"A": prepared_arms[0], "B": prepared_arms[1]}
    arm_names = dict(zip(("A", "B"), config.arm_names))
    first = prepared_arms[0]
    if any(
        prepared.layout != first.layout
        or prepared.env_tag != first.env_tag
        or prepared.perf != first.perf
        or prepared.clocks_per_us != first.clocks_per_us
        or tuple(prepared.numactl or ()) != tuple(first.numactl or ())
        or prepared.do_bench is not True
        or prepared.active_screening is not None
        or prepared.qualification_policy is not None
        for prepared in prepared_arms
    ):
        raise ValueError("balanced prepared arm contracts differ")
    if any(prepared.bench_max_rounds != 1 for prepared in prepared_arms):
        raise ValueError("balanced schedule bench_max_rounds must be exactly integer one")
    if (type(first.perf.reps) is not int or isinstance(first.perf.reps, bool)
            or first.perf.reps < 20 or first.perf.reps % 10 != 0):
        raise ValueError("balanced arm reps must be a positive multiple of ten with two groups")

    schedule = derive_balanced_schedule(
        config.root_seed, config.workload, first.perf.reps // 10,
    )
    rows: List[Dict[str, object]] = []
    block_diagnostics: List[Dict[str, object]] = []
    arm_tps: Dict[str, List[float]] = {"A": [], "B": []}
    arm_wall_s: Dict[str, float] = {"A": 0.0, "B": 0.0}
    arm_notes: Dict[str, List[str]] = {"A": [], "B": []}
    arm_run_cmd: Dict[str, str] = {"A": "", "B": ""}
    failure: Optional[Tuple[str, str, Dict]] = None
    settled: Optional[Dict[str, object]] = None
    dummy_dirs = {
        arm: tempfile.mkdtemp(prefix="izanagi_balanced_notrace_")
        for arm in arm_map
    }
    schedule_started = time.monotonic()
    try:
        with bench_lock():
            try:
                settled = settle()
            except Exception as exc:  # fail closed: admission could not be established
                failure = (
                    "bench-unsettled",
                    "balanced schedule settle probe failed → reject workload",
                    {"error": _exc_summary(exc)},
                )
            if (failure is None
                    and (type(settled) is not dict
                         or settled.get("settled") is not True)):
                failure = (
                    "bench-unsettled",
                    "balanced schedule did not reach settled=true → reject workload",
                    {"settled": (
                        settled.get("settled") if isinstance(settled, dict) else None
                    )},
                )

            global_block = 0
            for group, physical_order in enumerate(schedule.blocks):
                if failure is not None:
                    break
                for block_in_group, offset in enumerate(range(0, len(physical_order), 5)):
                    arm = physical_order[offset]
                    if tuple(physical_order[offset:offset + 5]) != (arm,) * 5:
                        raise AssertionError("derived balanced block is not five identical arms")
                    try:
                        competing = competing_bench_pids()
                    except Exception as exc:  # probe failures are always fail-closed
                        probe_error = (
                            exc.as_dict()
                            if isinstance(exc, CompetingBenchProbeError)
                            else {"error": _exc_summary(exc)}
                        )
                        failure = (
                            "bench-probe-error",
                            "balanced block competing probe failed → reject workload",
                            {"probe_error": probe_error, "group": group,
                             "block": global_block},
                        )
                        break
                    if competing:
                        failure = (
                            "bench-competing-tenant",
                            "balanced block found a competing benchmark → reject workload",
                            {"competing": competing, "group": group,
                             "block": global_block},
                        )
                        break

                    prepared = arm_map[arm]
                    rep_timestamps: List[Dict[str, int]] = []
                    rep_observations: List[Dict[str, object]] = []
                    block_started = time.monotonic()
                    try:
                        point = measure_point(
                            prepared.perf_binary,
                            prepared.perf.records,
                            prepared.perf.threads,
                            prepared.clocks_per_us,
                            extime=prepared.perf.extime,
                            reps=BALANCED_BLOCK_REPS,
                            workload=prepared.perf.workload,
                            numactl=prepared.numactl,
                            extra_env={"IZANAGI_TRACE_DIR": dummy_dirs[arm]},
                            rep_observations=rep_observations,
                            rep_timestamps=rep_timestamps,
                            require_all_reps=True,
                            use_perf=prepared.use_perf,
                            holdout_observation_admission=(
                                prepared.holdout_observation_admission
                            ),
                        )
                    except (RuntimeError, subprocess.TimeoutExpired) as exc:
                        failure = (
                            "bench-no-throughput",
                            "balanced block produced no usable throughput → reject workload",
                            {"error": _exc_summary(exc), "group": group,
                             "block": global_block},
                        )
                        break
                    finally:
                        arm_wall_s[arm] += max(
                            0.0, time.monotonic() - block_started,
                        )
                    if (len(rep_timestamps) != BALANCED_BLOCK_REPS
                            or len(rep_observations) != BALANCED_BLOCK_REPS):
                        failure = (
                            "bench-no-throughput",
                            "balanced block did not return five rep observations → reject workload",
                            {"group": group, "block": global_block,
                             "timestamps": len(rep_timestamps),
                             "observations": len(rep_observations)},
                        )
                        break
                    block_values = [
                        observation.get("throughput")
                        for observation in rep_observations
                        if type(observation.get("throughput")) in (int, float)
                    ]
                    if len(block_values) != BALANCED_BLOCK_REPS:
                        failure = (
                            "bench-no-throughput",
                            "balanced block did not produce five throughputs → reject workload",
                            {"group": group, "block": global_block,
                             "throughputs": len(block_values)},
                        )
                        break
                    arm_tps[arm].extend(float(value) for value in block_values)
                    arm_notes[arm].extend(getattr(point, "notes", []))
                    arm_run_cmd[arm] = point.run_cmd
                    block_nf = noise_floor(block_values)
                    block_diagnostics.append({
                        "arm": arm_names[arm],
                        "group": group,
                        "block": global_block,
                        "block_in_group": block_in_group,
                        "cv": block_nf.cv,
                        "tps": list(block_values),
                    })
                    pair_base = group * 10 + (block_in_group // 2) * 5
                    for position, (timing, observation) in enumerate(zip(
                            rep_timestamps, rep_observations)):
                        rows.append({
                            "tps": observation.get("throughput"),
                            "arm": arm_names[arm],
                            "pair_index": pair_base + position,
                            "group": group,
                            "block": group * 2 + (block_in_group // 2),
                            "block_position": position,
                            "started_at_ns": timing["started_at_ns"],
                            "ended_at_ns": timing["finished_at_ns"],
                        })
                    global_block += 1
    finally:
        for directory in dummy_dirs.values():
            shutil.rmtree(directory, ignore_errors=True)

    schedule_wall_s = max(0.0, time.monotonic() - schedule_started)
    if failure is not None:
        reason, note, extra = failure
        extra["bench_wall_s"] = schedule_wall_s
        return _abort_balanced_workload(
            prepared_arms, reason, note, extra,
        ), {}

    benches: Dict[str, _BenchResult] = {}
    arm_records: Dict[str, Dict[str, object]] = {}
    for arm, prepared in arm_map.items():
        values = arm_tps[arm]
        if not values:
            raise AssertionError("completed balanced blocks lost arm throughput")
        nf = noise_floor(values)
        assert nf.median is not None
        if nf.cv is None:
            return _abort_balanced_workload(
                prepared_arms,
                "bench-cv-undefined",
                "balanced aggregate arm CV is undefined → reject workload",
                {"arm": arm, "tps": values, "bench_wall_s": schedule_wall_s},
            ), {}
        aggregate_unstable = bool(nf.high_variance)
        leading = {
            "throughput_tps": nf.median,
            "abort_rate": None,
            "latency_ns": None,
            "llc_miss_rate": None,
            "ipc": None,
        }
        benches[arm] = _BenchResult(
            median_tps=nf.median,
            cv=nf.cv,
            high_variance=nf.high_variance,
            unstable=aggregate_unstable,
            leading_indicators=leading,
        )
        arm_records[arm_names[arm]] = {
            "variant": prepared.result.variant,
            "rounds": 1,
            "tps": list(values),
            "median_tps": nf.median,
            "cv": nf.cv,
            "unstable": aggregate_unstable,
            "block_cvs": [
                item["cv"] for item in block_diagnostics
                if item["arm"] == arm_names[arm]
            ],
        }

    receipt = {
        "schema_version": BALANCED_SCHEDULE_RECEIPT_SCHEMA,
        "pairing_design": BALANCED_PAIRING_DESIGN,
        "workload": config.workload,
        "root_seed": config.root_seed,
        "effective_root_seed": schedule.effective_root_seed,
        "seed_counter": schedule.seed_counter,
        "group_bits": list(schedule.group_bits),
        "bench_max_rounds": 1,
        "rounds": 1,
        "settled": settled,
        "schedule_wall_s": schedule_wall_s,
        "arms": arm_records,
        "blocks": block_diagnostics,
        "reps": rows,
    }
    _exclusive_schedule_receipt(first.layout, config.receipt_name, receipt)

    # No WAL/file write occurs in the block loop.  Both arm completion records
    # are emitted only after the entire schedule and exclusive receipt succeed.
    for arm, prepared in arm_map.items():
        bench = benches[arm]
        payload = {
            "build_attempt_id": prepared.build_attempt_id,
            "median_tps": bench.median_tps,
            "cv": bench.cv,
            "bench_wall_s": arm_wall_s[arm],
            "high_variance": bench.high_variance,
            "unstable": bench.unstable,
            "rounds": 1,
            "cv_history": [bench.cv],
            "tps": list(arm_tps[arm]),
            "settled": True,
            "leading_indicators": bench.leading_indicators,
            "rep_notes": arm_notes[arm],
            "run_cmd": arm_run_cmd[arm],
        }
        perf_observation = _perf_preflight.build_perf_observation(
            prepared.perf_preflight_receipt,
            run_cmd=arm_run_cmd[arm],
            leading_indicators=bench.leading_indicators,
        )
        if perf_observation is not None:
            payload["perf_observation"] = perf_observation
        _assert_bench_done_payload_keys(payload)
        prepared.emit(
            prepared.layout, prepared.result.variant, STAGE_BENCH_DONE,
            prepared.env_tag, payload,
        )
        prepared.bench = bench

    results = tuple(
        _commit_prepared(arm_map[arm], benches[arm]) for arm in ("A", "B")
    )
    return results, receipt
