# -*- coding: utf-8 -*-
"""calibrator の CLI (タスク4b 実機実行)。

  python3 orchestrator/calibrate.py --binary <ycsb_*.exe> --env-tag linux-baremetal \\
      --threads 16 [--workload ycsb_zipf_skew=0,ycsb_rratio=50] [--numactl interleave=all]

確定した校正を env スコープ output/env/<env-tag>/calibration/ に書く (D13):
  - calibration_t<threads>_<workload>.json … 機械可読 (全測定点・飽和推移・noise floor の生値)
  - calibration_t<threads>_<workload>.md   … 「なぜそのレコード数?」の人間可読な根拠 (査読先回り)

絶対規律1: --binary は trace-disabled build (`build/`, -DCCBENCH_TRACE=0) を指すこと。
絶対規律4: その binary は -DLinux スレッドピンニング済みを前提 (submodule master に還元済みで
常に有効 — cpu.hh setThreadAffinity。旧 patches/linux-thread-pinning.patch は D16 で還元後に削除)。
"""
from __future__ import annotations

import argparse
import copy
import ctypes
import dataclasses
import errno
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import time
from typing import Callable, Dict, List, Optional

from .model import CalibrationResult, CertificationEvidence
from .perf_preflight import use_perf_from_receipt
from . import effective_clock_policy
from .report import (certification_quality_reasons, render_text,
                     result_to_dict)
from .runner import (CompositeProbeViolation, composite_competing_probe)
from .schema_v2 import (SCHEMA_VERSION, normalize_request_id,
                        validate_calibration_v2)
from .sweep import MAX_RECORDS_DEFAULT, calibrate
from .tsc import TscMeasurement, measure_tsc
from orchestrator.campaign import env_attestation as _env_attestation
from orchestrator.campaign.genome import SPACES, space_for
from orchestrator.campaign.model import (
    Genome,
    genome_axis_from_cmake_cache_variable,
)
from orchestrator.campaign.execution_guard import (
    effective_clock_comparison_diagnostics,
    effective_clock_comparison_passes,
)
from orchestrator.holdout_observation import (
    _issue_calibration_observation_capability_from_receipt,
    _new_calibration_observation_receipt,
)


# C3-3/C3-7 frozen certification coordinates. Cooldown values come directly from
# the parent ruling: load1 <= 1.0 at three observations spaced 30 seconds apart,
# with a 20 minute fatal timeout. Reservation uses worst-case sweep points.
COOLDOWN_LOAD1_MAX = 1.0
COOLDOWN_INTERVAL_S = 30.0
COOLDOWN_CONSECUTIVE = 3
COOLDOWN_TIMEOUT_S = 20 * 60.0
BENCH_TIMEOUT_S = 120.0
TSC_BUDGET_S = 10
FINALIZE_RESERVE_S = 60
HASH_TIMEOUT_S = 30.0
TRACE_CHECK_TIMEOUT_S = 30.0
RESERVATION_FORMULA = (
    "tsc + cooldown_max + points*sweep_reps*bench_timeout + "
    "noise_reps*bench_timeout + 2*sweep_reps*bench_timeout + finalize_reserve"
)
_HEX64_RE = re.compile(r"[0-9a-fA-F]{64}")
_ENV_TAG_RE = re.compile(r"[a-z0-9][a-z0-9._-]*")
_EARLY_CLOCK_REJECTION_NOT_EVALUATED = (
    "dynamic-pre-competing-process-probe",
    "benchmark-calibration",
    "post-attestation-comparison",
    "post-isolation",
    "certification-quality",
    "late-effective-clock-self-comparison",
    "final-artifact-assembly-and-schema-validation",
    "publish-policy-identity",
    "publish",
    "published-artifact-bytes-self-comparison",
)
_PUBLISHED_SELF_COMPARISON_SCHEMA = (
    "izanagi/published-effective-clock-self-comparison/v1"
)
_ATTESTATION_PROFILE_CANONICALIZATION = (
    "json.dumps(sort_keys=True,separators=(',',':'),ensure_ascii=True)/utf-8"
)


class CertificationError(RuntimeError):
    """certification attempt 全体を reject する構造化 fatal。"""

    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail else code)

    def as_reason(self) -> str:
        return f"{self.code}: {self.detail}" if self.detail else self.code


def _parse_kv(s: Optional[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not s:
        return out
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        k, _, v = part.partition("=")
        out[k.strip()] = v.strip()
    return out


def _numactl_arg(s: Optional[str]) -> Optional[List[str]]:
    """'interleave=all' → ['numactl','--interleave=all']。'none'/'' → None。"""
    if not s or s.lower() == "none":
        return None
    parts = []
    for tok in s.split(","):
        tok = tok.strip()
        if not tok:
            continue
        parts.append("--" + tok if not tok.startswith("-") else tok)
    return ["numactl"] + parts if parts else None


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="calibrate",
        description="Izanagi calibrator — レコード数飽和点 + noise floor を実機で確定")
    p.add_argument("--binary", required=True,
                   help="ycsb_*.exe (trace-disabled / -DLinux ピンニング済み build)")
    p.add_argument("--env-tag", required=True,
                   help="環境タグ (例 linux-baremetal)。出力先 env スコープを決める")
    p.add_argument("--threads", type=int, required=True,
                   help="固定 thread 数 (飽和点は thread 依存 → 必ず明示)")
    p.add_argument("--workload", default="",
                   help="ycsb gflag の k=v をカンマ区切り (例 ycsb_zipf_skew=0,ycsb_rratio=50)")
    p.add_argument("--start-records", type=int, default=1_000_000)
    p.add_argument("--max-records", type=int, default=MAX_RECORDS_DEFAULT,
                   help="倍々スイープの上限。飽和を確認したら早期打ち切り (既定 16m)")
    p.add_argument("--extime", type=int, default=3)
    p.add_argument("--sweep-reps", type=int, default=3)
    p.add_argument("--noise-reps", type=int, default=10)
    p.add_argument("--clocks-per-us", type=int, default=None,
                   help="指定すれば TSC 実測をスキップしこの値を使う")
    p.add_argument("--numactl", default="interleave=all",
                   help="numactl メモリ方針 (例 interleave=all / membind=0 / none)")
    p.add_argument("--out-root", default=None,
                   help="出力ルート (既定 = リポジトリの output/)")
    p.add_argument("--certify", action="store_true",
                   help="calibration/v2 registration certification mode")
    p.add_argument("--receipt-json", default=None,
                   help="certification job が作った acquisition receipt JSON")
    p.add_argument("--perf-preflight-json", default=None,
                   help="certification job が保存した perf preflight receipt JSON")
    p.add_argument("--binary-sha256", default=None,
                   help="certification 対象 binary の事前凍結 SHA-256")
    return p


def _workload_tag(workload: Dict[str, str]) -> str:
    """ファイル名用の短い workload 署名。飽和点は workload (特に skew) で変わる
    ので、thread だけでなく workload でも出力を分ける (D13 の『入力非依存』前提が
    skew では崩れるため。worklog/insight 参照)。"""
    parts = []
    skew = workload.get("ycsb_zipf_skew")
    if skew is not None:
        parts.append("skew" + str(skew).replace(".", "p"))
    rratio = workload.get("ycsb_rratio")
    if rratio is not None:
        parts.append("rr" + str(rratio))
    rmw = workload.get("ycsb_rmw")
    if rmw is not None:
        parts.append("rmw" + str(rmw))
    return "_".join(parts) if parts else "default"


def _output_root(explicit: Optional[str]) -> str:
    if explicit:
        return explicit
    # orchestrator/calibrator/cli.py → リポジトリルート/output
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(os.path.dirname(here))
    return os.path.join(repo, "output")


def _assert_trace_disabled_binary(
        binary: str, *, subprocess_runner: Callable[..., object] = subprocess.run) -> None:
    """--binary が trace-disabled build であることを nm で検査する (絶対規律1)。

    calibration は入力非依存の計測基盤 (以後の全 campaign の動作点) なので、trace-enabled
    バイナリで校正すると観測者効果が基盤全体へ静かに伝播する。buildcache.build() 経路の
    継続検査と同じ判定を、手渡し binary の入口にも置く (docstring の規約だけでは防壁が
    人間の注意力頼みになる)。nm 不在/失敗も fails-closed で停止する。
    ※ campaign.buildcache._assert_no_trace_symbols と同型の小検査。calibrator は campaign
    に依存しない層のため、import せず局所実装で重複させている (層の分離 > DRY)。"""
    import subprocess
    try:
        r = subprocess_runner(
            ["nm", "-C", binary], capture_output=True, text=True,
            timeout=TRACE_CHECK_TIMEOUT_S,
        )
    except (OSError, subprocess.SubprocessError) as e:
        raise SystemExit(f"規律1 検査不能: nm を起動できない ({e})。trace シンボル漏れを"
                         f"検査できない環境で calibration しない (fails-closed)")
    if r.returncode != 0:
        raise SystemExit(f"規律1 検査不能: nm が失敗 (rc={r.returncode}): "
                         f"{r.stderr[-200:]} (fails-closed で停止)")
    if any("izanagi_trace" in ln.lower() for ln in r.stdout.splitlines()):
        raise SystemExit(
            f"絶対規律1 違反: {binary} は trace-enabled build (izanagi_trace シンボル検出)。"
            f"calibration は trace-disabled build (build/, -DCCBENCH_TRACE=0) で行うこと")


def reservation_budget(start_records: int, max_records: int,
                       sweep_reps: int, noise_reps: int) -> Dict[str, object]:
    """C3-7 の worst-case 予約式と値。early stop は予算を縮める根拠にしない。"""
    points = 0
    records = start_records
    while records <= max_records:
        points += 1
        records *= 2
    required = (
        TSC_BUDGET_S + int(COOLDOWN_TIMEOUT_S)
        + points * sweep_reps * int(BENCH_TIMEOUT_S)
        + noise_reps * int(BENCH_TIMEOUT_S)
        + 2 * sweep_reps * int(BENCH_TIMEOUT_S)
        + FINALIZE_RESERVE_S
    )
    return {
        "formula": RESERVATION_FORMULA, "points": points,
        "tsc_s": TSC_BUDGET_S, "cooldown_max_s": int(COOLDOWN_TIMEOUT_S),
        "bench_timeout_s": int(BENCH_TIMEOUT_S),
        "finalize_reserve_s": FINALIZE_RESERVE_S, "required_s": required,
    }


def cooldown_gate(*, load1_fn: Callable[[], float] = lambda: os.getloadavg()[0],
                  monotonic_fn: Callable[[], float] = time.monotonic,
                  sleep_fn: Callable[[float], None] = time.sleep) -> List[float]:
    """C3-3 cooldown: load1<=1.0 を30秒間隔で3回連続、20分 timeout。

    閾値・観測間隔・連続回数・timeout は親裁定で凍結され、変更可能な CLI knob にしない。
    timeout は calibration を続行せず attempt 全体 fatal にする。
    """
    deadline = monotonic_fn() + COOLDOWN_TIMEOUT_S
    samples: List[float] = []
    consecutive = 0
    while True:
        load1 = float(load1_fn())
        samples.append(load1)
        consecutive = consecutive + 1 if load1 <= COOLDOWN_LOAD1_MAX else 0
        if consecutive >= COOLDOWN_CONSECUTIVE:
            return samples
        now = monotonic_fn()
        if now >= deadline:
            raise CertificationError(
                "cooldown-timeout",
                f"load1 did not remain <= {COOLDOWN_LOAD1_MAX} for "
                f"{COOLDOWN_CONSECUTIVE} observations; samples={samples!r}",
            )
        sleep_fn(min(COOLDOWN_INTERVAL_S, max(0.0, deadline - now)))


def _strict_json_file(path: str) -> dict:
    def pairs_hook(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise CertificationError("receipt-duplicate-key", repr(key))
            obj[key] = value
        return obj
    try:
        with open(path, "rb") as f:
            raw = f.read()
        value = json.loads(raw, object_pairs_hook=pairs_hook,
                           parse_constant=lambda token: (_ for _ in ()).throw(
                               CertificationError("receipt-nonfinite", token)))
    except CertificationError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CertificationError("receipt-invalid", str(exc)) from exc
    if type(value) is not dict:
        raise CertificationError("receipt-invalid", "top-level must be an object")
    return value


def _sanitize_job_id(value: object) -> str:
    if type(value) is not str or not value:
        raise CertificationError("receipt-job-id", "PBS job id is missing")
    sanitized = re.sub(r"[^A-Za-z0-9._-]", "_", value)
    if sanitized in {"", ".", ".."}:
        raise CertificationError("receipt-job-id", repr(value))
    return sanitized


def _write_exclusive(path: str, data: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    try:
        with os.fdopen(fd, "wb", closefd=False) as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
    finally:
        os.close(fd)


def _fsync_directory(path: str) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    fd = os.open(path, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _renameat2_noreplace(source: str, target: str) -> None:
    """Linux renameat2(RENAME_NOREPLACE) の薄い syscall wrapper。"""
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise OSError(errno.ENOSYS, "renameat2 is unavailable")
    rc = renameat2(
        ctypes.c_int(-100), os.fsencode(source), ctypes.c_int(-100),
        os.fsencode(target), ctypes.c_uint(1),
    )
    if rc != 0:
        err = ctypes.get_errno()
        raise OSError(err, os.strerror(err))


def _rename_noreplace(source: str, target: str) -> str:
    """FS 非依存の atomic create-only publish。使用経路を返す。"""
    try:
        _renameat2_noreplace(source, target)
        return "renameat2"
    except OSError as exc:
        if exc.errno not in {errno.EINVAL, errno.ENOSYS, errno.ENOTSUP}:
            code = "publish-collision" if exc.errno == errno.EEXIST else "publish-failed"
            raise CertificationError(code, os.strerror(exc.errno)) from exc

    try:
        os.link(source, target)
    except OSError as exc:
        code = "publish-collision" if exc.errno == errno.EEXIST else "publish-failed"
        raise CertificationError(code, os.strerror(exc.errno)) from exc
    try:
        os.unlink(source)
    except OSError as exc:
        raise CertificationError("publish-failed", os.strerror(exc.errno)) from exc
    return "link-unlink"


def _binary_sha256(binary: str, subprocess_runner: Callable[..., object]) -> str:
    try:
        result = subprocess_runner(
            ["sha256sum", "--", binary], capture_output=True, text=True,
            timeout=HASH_TIMEOUT_S,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise CertificationError("binary-hash-error", str(exc)) from exc
    if result.returncode != 0:
        raise CertificationError(
            "binary-hash-error", f"rc={result.returncode}: {(result.stderr or '')[:200]}")
    token = (result.stdout or "").split(None, 1)[0] if (result.stdout or "").split() else ""
    if re.fullmatch(r"[0-9a-f]{64}", token) is None:
        raise CertificationError("binary-hash-error", "sha256sum returned invalid output")
    return token


def _canonical_genome_from_receipt(receipt: dict, binary: str) -> str:
    """Derive the build's canonical genome from a certified receipt argv."""
    try:
        build_argv = receipt["ccbench"]["build_argv"]
    except (KeyError, TypeError) as exc:
        raise CertificationError("receipt-genome-invalid", str(exc)) from exc
    if type(build_argv) is not list or not all(type(item) is str for item in build_argv):
        raise CertificationError(
            "receipt-genome-invalid", "ccbench.build_argv must be a string list",
        )
    separators = [index for index, token in enumerate(build_argv) if token == "&&"]
    if len(separators) != 1:
        raise CertificationError(
            "receipt-genome-invalid", "build_argv must contain exactly one &&",
        )
    separator = separators[0]
    configure_argv = build_argv[:separator]
    build_command = build_argv[separator + 1:]
    if not configure_argv or not build_command:
        raise CertificationError(
            "receipt-genome-invalid", "configure and build argv must both be non-empty",
        )

    target_indices = [
        index for index, token in enumerate(build_command) if token == "--target"
    ]
    if len(target_indices) != 1:
        raise CertificationError(
            "receipt-genome-invalid", "build argv must contain exactly one --target",
        )
    target_index = target_indices[0]
    if target_index + 1 >= len(build_command):
        raise CertificationError(
            "receipt-genome-invalid", "--target has no value",
        )
    target = build_command[target_index + 1]
    target_match = re.fullmatch(r"ycsb_([a-z0-9][a-z0-9_-]*)\.exe", target)
    if target_match is None:
        raise CertificationError(
            "receipt-genome-invalid", "build target is not ycsb_<protocol>.exe",
        )
    protocol = target_match.group(1)
    if os.path.basename(binary) != target:
        raise CertificationError(
            "receipt-genome-invalid",
            f"binary basename {os.path.basename(binary)!r} does not match target {target!r}",
        )
    if protocol not in SPACES:
        raise CertificationError(
            "receipt-genome-invalid", f"protocol is not registered: {protocol!r}",
        )

    if any(token.startswith("-DCCBENCH_") for token in build_command):
        raise CertificationError(
            "receipt-genome-invalid", "CCBENCH define appears in build argv",
        )
    define_re = re.compile(r"-DCCBENCH_([A-Z][A-Z0-9_]*)=([+-]?[0-9]+)")
    flags: Dict[str, int] = {}
    for token in configure_argv:
        if not token.startswith("-DCCBENCH_"):
            continue
        match = define_re.fullmatch(token)
        if match is None:
            raise CertificationError(
                "receipt-genome-invalid", f"malformed CCBENCH define: {token!r}",
            )
        cache_name, encoded = match.groups()
        cache_variable = f"CCBENCH_{cache_name}"
        try:
            flag = genome_axis_from_cmake_cache_variable(
                protocol, cache_variable,
            )
        except ValueError as exc:
            raise CertificationError(
                "receipt-genome-invalid", str(exc),
            ) from exc
        if flag in flags:
            raise CertificationError(
                "receipt-genome-invalid", f"duplicate CCBENCH define: {flag}",
            )
        flags[flag] = int(encoded)

    if flags.get("TRACE") != 0:
        raise CertificationError(
            "receipt-genome-invalid", "CCBENCH_TRACE must appear exactly once with value 0",
        )
    flags.pop("TRACE")
    if not flags:
        raise CertificationError(
            "receipt-genome-invalid", "at least one non-TRACE CCBENCH define is required",
        )
    missing_axes = sorted(set(space_for(protocol).axes) - set(flags))
    if missing_axes:
        raise CertificationError(
            "receipt-genome-invalid",
            "configure argv is missing protocol axes: " + ",".join(missing_axes),
        )
    try:
        return Genome(protocol=protocol, flags=flags).canonical()
    except (TypeError, ValueError) as exc:
        raise CertificationError("receipt-genome-invalid", str(exc)) from exc


def _profile_dict(value: object) -> dict:
    try:
        return _env_attestation.observed_profile_to_dict(value)  # type: ignore[arg-type]
    except _env_attestation.AttestationError as exc:
        raise CertificationError("attestation-invalid", str(exc)) from exc


def _default_probe():
    from orchestrator.campaign import env_attestation
    fn = getattr(env_attestation, "probe", None)
    if fn is None:
        fn = getattr(env_attestation, "probe_hardware", None)
    if fn is None:
        raise CertificationError("attestation-unavailable", "probe API is not implemented")
    return fn()


def _coerce_tsc(value: object) -> TscMeasurement:
    if isinstance(value, TscMeasurement):
        measured = value
    elif dataclasses.is_dataclass(value):
        raw = dataclasses.asdict(value)
        measured = TscMeasurement(**raw)
    elif type(value) is dict:
        measured = TscMeasurement(**value)
    else:
        raise CertificationError("tsc-measurement-failed", repr(value))
    if len(measured.raw_samples_mhz) != 5:
        raise CertificationError("tsc-measurement-failed", "exactly five samples are required")
    ordered = sorted(float(v) for v in measured.raw_samples_mhz)
    median = ordered[2]
    if measured.median_mhz != median or measured.clocks_per_us_int != round(median):
        raise CertificationError("tsc-measurement-failed", "median/nearest-even mismatch")
    return measured


def _static_profile_bytes(profile: dict) -> bytes:
    static = copy.deepcopy(profile)
    static.pop("tsc", None)
    static.pop("effective_clock", None)
    return json.dumps(static, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _canonical_json_bytes(value: object) -> bytes:
    """Canonical JSON bytes used for profile and independent-input identities."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("utf-8")


def _calibration_sweep_point_count(start_records: int, max_records: int) -> int:
    points = 0
    records = start_records
    while records <= max_records:
        points += 1
        records *= 2
    return points


def _calibration_observation_marker(
    *, root: str, job_id: str, plan: dict,
) -> str:
    """Reserve one job-keyed calibration capability outside env-scoped staging.

    The path is ``<output-root>/calibration-capability-markers/<safe-job-id>.json``:
    it intentionally has no env-tag component, so changing ``--env-tag`` cannot
    create a second reservation for the same PBS job.  The JSON body retains the
    raw job id and all binding identities for audit and collision diagnosis.
    """
    marker_root = os.path.join(root, "calibration-capability-markers")
    os.makedirs(marker_root, exist_ok=True)
    safe_job_id = _sanitize_job_id(job_id)
    marker_path = os.path.join(marker_root, safe_job_id + ".json")
    plan_sha256 = hashlib.sha256(
        _canonical_json_bytes(plan)
    ).hexdigest()
    marker = {
        "schema": "izanagi/calibration-observation-reservation/v1",
        "key": {"job_id": job_id},
        **copy.deepcopy(plan),
        "plan_sha256": plan_sha256,
    }
    try:
        _write_exclusive(
            marker_path,
            _canonical_json_bytes(marker) + b"\n",
        )
        _fsync_directory(marker_root)
    except FileExistsError as exc:
        raise CertificationError("attempt-replay", marker_path) from exc
    except CertificationError:
        raise
    except OSError as exc:
        raise CertificationError(
            "calibration-marker-write-failed",
            f"{marker_path}: {type(exc).__name__}: {str(exc)[:300]}",
        ) from exc
    return plan_sha256


def _effective_clock_self_comparison_passes(profile: object) -> bool:
    """Apply the runtime consumer predicate to a profile's own clock samples."""
    if type(profile) is not dict:
        return False
    effective_clock = profile.get("effective_clock")
    if type(effective_clock) is not dict:
        return False
    expected = {
        "samples_mhz": effective_clock.get("samples_mhz"),
        "tolerance_pct": effective_clock.get("tolerance_pct"),
    }
    observed = {
        "samples_mhz": effective_clock.get("samples_mhz"),
    }
    return effective_clock_comparison_passes(
        expected,
        observed,
    )


def _effective_clock_self_comparison_diagnostics(profile: object) -> dict:
    """Project diagnostics for the same profile pair; never decide admission."""
    if type(profile) is not dict:
        return effective_clock_comparison_diagnostics(None, None)
    effective_clock = profile.get("effective_clock")
    if type(effective_clock) is not dict:
        return effective_clock_comparison_diagnostics(None, None)
    return effective_clock_comparison_diagnostics(
        {
            "samples_mhz": effective_clock.get("samples_mhz"),
            "tolerance_pct": effective_clock.get("tolerance_pct"),
        },
        {"samples_mhz": effective_clock.get("samples_mhz")},
    )


def _effective_clock_rejection_diagnostics(profile: dict) -> dict:
    """Bind an early rejection to the exact evaluated profile and clock input."""
    effective_clock = profile["effective_clock"]
    effective_clock_input = {
        field: copy.deepcopy(effective_clock[field])
        for field in ("samples_mhz", "tolerance_pct", "method", "governor")
    }
    return {
        "attestation_profile_sha256": hashlib.sha256(
            _canonical_json_bytes(profile)
        ).hexdigest(),
        "attestation_profile_canonicalization": (
            _ATTESTATION_PROFILE_CANONICALIZATION
        ),
        "attestation_profile": copy.deepcopy(profile),
        "effective_clock_input": effective_clock_input,
        "effective_clock_self_comparison": (
            _effective_clock_self_comparison_diagnostics(profile)
        ),
    }


def _effective_clock_policy_matches_current(
    profile: object, *, attempt_tolerance_pct: object,
) -> bool:
    """Independently compare attempt-profile policy with publish-time policy."""
    if type(profile) is not dict:
        return False
    effective_clock = profile.get("effective_clock")
    if type(effective_clock) is not dict:
        return False
    attempt_tolerance = effective_clock.get("tolerance_pct")
    return bool(
        type(attempt_tolerance) in (int, float)
        and attempt_tolerance == attempt_tolerance_pct
        and attempt_tolerance
        == effective_clock_policy.EFFECTIVE_CLOCK_TOLERANCE_PCT
    )


def _published_self_comparison_receipt(target: str) -> dict:
    """Re-read only published target bytes and apply the canonical predicate."""
    try:
        with open(target, "rb") as published:
            raw = published.read()
    except OSError as exc:
        raise CertificationError(
            "published-self-comparison-read-failed",
            f"{type(exc).__name__}: {str(exc)[:300]}",
        ) from exc
    receipt = {
        "schema": _PUBLISHED_SELF_COMPARISON_SCHEMA,
        "passed": False,
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "policy_identity": {
            "authority": (
                "calibrator.effective_clock_policy."
                "EFFECTIVE_CLOCK_TOLERANCE_PCT"
            ),
            "tolerance_pct": (
                effective_clock_policy.EFFECTIVE_CLOCK_TOLERANCE_PCT
            ),
        },
    }
    try:
        document = json.loads(raw)
        if type(document) is not dict:
            raise TypeError("published document is not an object")
        profile = document["attestation_profile"]
        if type(profile) is not dict:
            raise TypeError("published attestation_profile is not an object")
        clock = profile["effective_clock"]
        if type(clock) is not dict:
            raise TypeError("published effective_clock is not an object")
        passed = effective_clock_comparison_passes(
            {
                "samples_mhz": clock.get("samples_mhz"),
                "tolerance_pct": clock.get("tolerance_pct"),
            },
            {"samples_mhz": clock.get("samples_mhz")},
        )
    except (UnicodeError, json.JSONDecodeError, KeyError, TypeError,
            ValueError, OverflowError) as exc:
        receipt["error"] = {
            "type": type(exc).__name__,
            "message": str(exc)[:300],
        }
        return receipt
    receipt["passed"] = bool(passed)
    return receipt


def _acquisition_reasons(receipt: dict, *, budget: dict,
                         binary_sha256: str, profile: dict) -> List[str]:
    reasons: List[str] = []
    try:
        qsub = receipt["qsub"]
        allocation = receipt["allocation"]
        ccbench = receipt["ccbench"]
        walltime = receipt["walltime"]
        known = receipt["known_values_check"]
        cores = profile["cores"]
        cpu = profile["cpu"]
        if (normalize_request_id(qsub["request_id"])
                != normalize_request_id(allocation["pbs_jobid"])):
            reasons.append("acquisition-job-id-mismatch")
        if allocation["assigned_host_qstat"] != allocation["hostname_observed"]:
            reasons.append("acquisition-host-mismatch")
        if qsub["nodes"] != 1:
            reasons.append("acquisition-node-count-invalid")
        if ccbench["binary_sha256"] != binary_sha256:
            reasons.append("acquisition-binary-hash-mismatch")
        if (walltime["reserve_s"] <= 0
                or budget["required_s"] + walltime["reserve_s"]
                > walltime["required_s"]):
            reasons.append("reservation-mismatch")
        if walltime["required_s"] > qsub["elapstim_req_s"]:
            reasons.append("reservation-qsub-mismatch")
        observed_model = " ".join(str(cpu["model_name_normalized"]).split()).casefold()
        expected_model = " ".join(str(known["expected_cpu_model"]).split()).casefold()
        computed_known = (
            bool(known["passed"])
            and expected_model == observed_model
            and known["expected_cores"] == cores["physical"]
            and allocation["cpuset_size"] == cores["affinity_visible"]
            and bool(allocation["ht_off"])
            and not bool(cores["smt_active"])
        )
        if not computed_known:
            reasons.append("known-values-check-failed")
        if not _effective_clock_self_comparison_passes(profile):
            reasons.append("effective-clock-self-comparison-failed")
    except (KeyError, TypeError, ValueError) as exc:
        raise CertificationError("receipt-invalid", str(exc)) from exc
    return reasons


def _assemble_v2(result: CalibrationResult, *, profile: dict, receipt: dict,
                 genome: str, status: str, reasons: List[str]) -> tuple[dict, bytes]:
    doc = result_to_dict(result)
    doc["schema_version"] = SCHEMA_VERSION
    if doc["noise_floor"] is None:
        doc["noise_floor"] = {
            "kind": "within-run", "throughputs": [], "mean": None,
            "median": None, "stdev": None, "cv": None,
            "high_variance": False, "notes": [],
        }
    else:
        doc["noise_floor"]["kind"] = "within-run"
    doc["scale_sensitivity"] = "not-measured"
    doc["attestation_profile"] = profile
    doc["acquisition_receipt"] = copy.deepcopy(receipt)
    doc["genome"] = genome
    doc["quality"] = {"status": status, "reasons": reasons}
    validate_calibration_v2(doc)
    raw = (json.dumps(doc, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    validate_calibration_v2(raw)
    return doc, raw


def _write_rejection(
    staging: str,
    reasons: List[str],
    budget: dict,
    *,
    diagnostics: Optional[dict] = None,
    not_evaluated: Optional[List[str]] = None,
) -> None:
    payload = {
        "quality": {"status": "rejected", "reasons": reasons},
        "reservation": budget,
    }
    if diagnostics is not None:
        payload["diagnostics"] = diagnostics
    if not_evaluated is not None:
        payload["not_evaluated"] = list(not_evaluated)
    _write_exclusive(
        os.path.join(staging, "rejection.json"),
        (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )


def _validate_cli(args) -> Optional[str]:
    if args.perf_preflight_json and not args.certify:
        return "--perf-preflight-json requires --certify"
    if args.start_records <= 0 or args.start_records > args.max_records:
        return "require 0 < start_records <= max_records"
    for name in ("threads", "extime", "sweep_reps", "noise_reps"):
        if getattr(args, name) <= 0:
            return f"{name} must be a positive integer"
    if args.certify:
        if _ENV_TAG_RE.fullmatch(args.env_tag) is None:
            return "--env-tag must be a canonical schema slug with --certify"
        if args.clocks_per_us is not None:
            return "--clocks-per-us is forbidden with --certify"
        if not args.receipt_json:
            return "--receipt-json is required with --certify"
        if not args.binary_sha256 or _HEX64_RE.fullmatch(args.binary_sha256) is None:
            return "--binary-sha256 HEX64 is required with --certify"
        if args.out_root is not None:
            return "--out-root is forbidden with --certify"
    return None


def _certify_main(
        args, *, probe_fn: Callable[[], object], load1_fn: Callable[[], float],
        clock_fn: Callable[[], object], subprocess_runner: Callable[..., object],
        nonce_fn: Callable[[], str], monotonic_fn: Callable[[], float],
        sleep_fn: Callable[[float], None], calibrate_fn: Callable[..., CalibrationResult]) -> int:
    binary = os.path.abspath(args.binary)
    budget = reservation_budget(
        args.start_records, args.max_records, args.sweep_reps, args.noise_reps)
    receipt = _strict_json_file(args.receipt_json)
    try:
        job_id = receipt["allocation"]["pbs_jobid"]
    except (KeyError, TypeError) as exc:
        raise CertificationError("receipt-job-id", str(exc)) from exc
    root = _output_root(None)
    calibration_root = os.path.join(root, "env", args.env_tag, "calibration")
    attempts = os.path.join(calibration_root, "attempts")
    os.makedirs(attempts, exist_ok=True)
    staging = os.path.join(attempts, _sanitize_job_id(job_id))
    try:
        os.mkdir(staging, 0o755)
    except FileExistsError as exc:
        raise CertificationError("attempt-exists", staging) from exc

    static_pre: Optional[dict] = None
    profile: Optional[dict] = None
    measured_tsc: Optional[TscMeasurement] = None
    result: Optional[CalibrationResult] = None
    genome: Optional[str] = None
    attempt_tolerance_pct: object = None
    measurements = []
    window_receipts: List[dict] = []
    reasons: List[str] = []
    rejection_diagnostics: Optional[dict] = None
    rejection_not_evaluated: Optional[List[str]] = None
    try:
        # C3-3(i): no build/hash/cooldown work precedes the static hardware probe.
        static_pre = _profile_dict(probe_fn())

        perf_receipt = (_strict_json_file(args.perf_preflight_json)
                        if args.perf_preflight_json else None)
        if perf_receipt is not None:
            _write_exclusive(
                os.path.join(staging, "perf-preflight.json"),
                _canonical_json_bytes(perf_receipt),
            )
        use_perf = use_perf_from_receipt(perf_receipt)

        _assert_trace_disabled_binary(binary, subprocess_runner=subprocess_runner)
        actual_hash = _binary_sha256(binary, subprocess_runner)
        expected_hash = args.binary_sha256.lower()
        if actual_hash != expected_hash:
            raise CertificationError(
                "binary-hash-mismatch", f"expected={expected_hash} actual={actual_hash}")
        genome = _canonical_genome_from_receipt(receipt, binary)

        # C3-3(ii): fatal cooldown; no best-effort settle in this path.
        cooldown_gate(load1_fn=load1_fn, monotonic_fn=monotonic_fn, sleep_fn=sleep_fn)

        # C3-3(iii): dynamic pre-receipt (TSC/effective clock/governor + isolation).
        dynamic_pre = _profile_dict(probe_fn())
        visibility = dynamic_pre.get("visibility")
        if (not isinstance(visibility, dict)
                or visibility.get("hidepid") != "0"
                or visibility.get("pid_ns_shared_with_host") is not True):
            raise CertificationError("visibility-not-host")
        if _static_profile_bytes(static_pre) != _static_profile_bytes(dynamic_pre):
            raise CertificationError(
                "pre-attestation-mismatch", "static hardware changed across cooldown")
        measured_tsc = _coerce_tsc(clock_fn())
        profile = copy.deepcopy(dynamic_pre)
        profile["tsc"] = dataclasses.asdict(measured_tsc)
        attempt_tolerance_pct = (
            effective_clock_policy.EFFECTIVE_CLOCK_TOLERANCE_PCT
        )
        profile["effective_clock"]["tolerance_pct"] = attempt_tolerance_pct
        # The rejected empty document is a schema-only preflight for the acquisition
        # material. It catches unknown/missing nested receipt fields before any bench.
        _assemble_v2(
            CalibrationResult(
                env_tag=args.env_tag, threads=args.threads,
                clocks_per_us=measured_tsc.clocks_per_us_int,
            ),
            profile=profile, receipt=receipt, genome=genome, status="rejected",
            reasons=["receipt-schema-preflight"],
        )
        acquisition_reasons = _acquisition_reasons(
            receipt, budget=budget, binary_sha256=actual_hash, profile=profile)
        if acquisition_reasons:
            if "effective-clock-self-comparison-failed" in acquisition_reasons:
                rejection_not_evaluated = list(
                    _EARLY_CLOCK_REJECTION_NOT_EVALUATED
                )
                rejection_diagnostics = _effective_clock_rejection_diagnostics(
                    profile
                )
            reasons.extend(acquisition_reasons)
            raise CertificationError(
                "acquisition-invalid", ",".join(acquisition_reasons))

        def window_probe(label: str) -> object:
            try:
                observed = composite_competing_probe(
                    nonce=nonce_fn(), subprocess_runner=subprocess_runner)
            except CompositeProbeViolation as exc:
                raise CertificationError("probe-violation", exc.as_reason()) from exc
            except Exception as exc:
                raise CertificationError("probe-error", str(exc)) from exc
            receipt_item = dict(observed)
            receipt_item["window"] = label
            window_receipts.append(receipt_item)
            return observed

        window_probe("dynamic-pre")
        memory_policy = "interleave=all"
        numactl = None if len(profile["numa"]) == 1 else ["numactl", "--" + memory_policy]
        workload = _parse_kv(args.workload)
        calibration_observation_capability = None
        ratio = workload.get("ycsb_rratio")
        if ratio in ("20", "80"):
            permitted_run_once_calls = (
                _calibration_sweep_point_count(
                    args.start_records, args.max_records,
                ) * args.sweep_reps + args.noise_reps
            )
            sweep_gflags = [
                f"-thread_num={args.threads}",
                f"-extime={args.extime}",
                f"-clocks_per_us={measured_tsc.clocks_per_us_int}",
            ]
            sweep_gflags.extend(
                f"-{key}={value}" for key, value in workload.items()
            )
            receipt_sha256 = hashlib.sha256(
                _canonical_json_bytes(receipt)
            ).hexdigest()
            plan = {
                "attempt_id": job_id,
                "job_id": job_id,
                "env_tag": args.env_tag,
                "receipt_sha256": receipt_sha256,
                "binary_sha256": actual_hash,
                "ycsb_rratio": ratio,
                "permitted_run_once_calls": permitted_run_once_calls,
                "sweep_gflags": list(sweep_gflags),
                "sweep_reps": args.sweep_reps,
                "noise_reps": args.noise_reps,
                "start_records": args.start_records,
                "max_records": args.max_records,
                "records_multiplier": 2,
                "numactl": list(numactl or ()),
                "timeout_s": BENCH_TIMEOUT_S,
                "use_perf": use_perf,
                "extra_env": {},
            }
            plan_sha256 = _calibration_observation_marker(
                root=root, job_id=job_id, plan=plan,
            )
            calibration_receipt = _new_calibration_observation_receipt(
                attempt_id=job_id,
                env_tag=args.env_tag,
                receipt_sha256=receipt_sha256,
                binary_sha256=actual_hash,
                ycsb_rratio=ratio,
                permitted_run_once_calls=permitted_run_once_calls,
                sweep_gflags=tuple(sweep_gflags),
                sweep_reps=args.sweep_reps,
                noise_reps=args.noise_reps,
                start_records=args.start_records,
                max_records=args.max_records,
                records_multiplier=2,
                numactl=tuple(numactl or ()),
                timeout_s=BENCH_TIMEOUT_S,
                use_perf=use_perf,
                extra_env=None,
                plan_sha256=plan_sha256,
            )
            calibration_observation_capability = (
                _issue_calibration_observation_capability_from_receipt(
                    receipt=calibration_receipt,
                )
            )

        # C3-3(iv): every sweep/noise/scale group is bracketed in sweep.calibrate.
        perf_kwargs = {} if use_perf else {"use_perf": False}
        result = calibrate_fn(
            binary=binary, env_tag=args.env_tag, threads=args.threads,
            workload=workload, start_records=args.start_records,
            max_records=args.max_records, extime=args.extime,
            sweep_reps=args.sweep_reps, noise_reps=args.noise_reps,
            numactl=numactl, clocks_per_us=measured_tsc.clocks_per_us_int,
            certify=True, skip_settle=True, window_probe=window_probe,
            measurement_sink=measurements, bench_timeout_s=BENCH_TIMEOUT_S,
            subprocess_runner=subprocess_runner,
            calibration_observation_capability=(
                calibration_observation_capability
            ),
            **perf_kwargs,
        )
        if not use_perf:
            result.host["perf"] = "unavailable"
            result.notes.append(
                "perf unavailable: counters not acquired; compare only within "
                "the same perf condition; certification records cannot be selected."
            )

        # C3-3(v): reacquire static profile, compare, then final isolation probe.
        static_post = _profile_dict(probe_fn())
        post_matches = _static_profile_bytes(static_pre) == _static_profile_bytes(static_post)
        window_probe("post-receipt")
        evidence = CertificationEvidence(
            tsc_measured=True, cooldown_settled=True, measurements=measurements,
            all_subprocesses_succeeded=True, all_windows_isolated=True,
            post_static_matches=post_matches,
        )
        reasons.extend(certification_quality_reasons(result, evidence))
        if not _effective_clock_self_comparison_passes(profile):
            reasons.append("effective-clock-self-comparison-failed")
        status = "accepted" if not reasons else "rejected"
        _, artifact = _assemble_v2(
            result, profile=profile, receipt=receipt, genome=genome,
            status=status, reasons=reasons)
        staging_artifact = os.path.join(
            staging, "calibration.json" if status == "rejected" else "candidate.json")
        _write_exclusive(staging_artifact, artifact)
        report = (
            f"# certification attempt {job_id}\n\nquality: {status}\n\n"
            + "```\n" + render_text(result) + "\n```\n"
        ).encode("utf-8")
        _write_exclusive(os.path.join(staging, "calibration.md"), report)
        _write_exclusive(
            os.path.join(staging, "window-probes.json"),
            (json.dumps(window_receipts, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        )
        if status != "accepted":
            print("certification rejected: " + "; ".join(reasons), file=sys.stderr)
            return 1

        registered = os.path.join(calibration_root, "registered")
        os.makedirs(registered, exist_ok=True)
        digest = hashlib.sha256(artifact).hexdigest()
        target = os.path.join(registered, f"calibration-{digest[:16]}.json")
        safe_job_id = _sanitize_job_id(job_id)
        temporary = os.path.join(
            registered, f".publish-{safe_job_id}-{secrets.token_hex(8)}.tmp")
        if not _effective_clock_policy_matches_current(
            profile, attempt_tolerance_pct=attempt_tolerance_pct,
        ):
            profile_tolerance = profile["effective_clock"].get("tolerance_pct")
            raise CertificationError(
                "effective-clock-policy-changed",
                "attempt=" + repr(attempt_tolerance_pct)
                + " profile=" + repr(profile_tolerance)
                + " publish="
                + repr(effective_clock_policy.EFFECTIVE_CLOCK_TOLERANCE_PCT),
            )
        try:
            _write_exclusive(temporary, artifact)
        except FileExistsError:
            raise
        except Exception as write_exc:
            raise CertificationError(
                "publish-temporary-write-failed",
                "temporary-path=" + temporary
                + ": left in place after exclusive write failure: "
                + f"{type(write_exc).__name__}: {str(write_exc)[:300]}",
            ) from write_exc
        try:
            publish_method = _rename_noreplace(temporary, target)
        except Exception as publish_exc:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
            except OSError as cleanup_exc:
                raise CertificationError(
                    "publish-temporary-cleanup-failed",
                    f"{type(cleanup_exc).__name__}: {str(cleanup_exc)[:300]}",
                ) from publish_exc
            raise
        published_self_comparison = _published_self_comparison_receipt(target)
        _write_exclusive(
            os.path.join(staging, "published-self-comparison.json"),
            (json.dumps(
                published_self_comparison, indent=2, sort_keys=True,
            ) + "\n").encode("utf-8"),
        )
        if not published_self_comparison["passed"]:
            raise CertificationError(
                "published-effective-clock-self-comparison-failed"
            )
        os.rename(staging_artifact, os.path.join(staging, "calibration.json"))
        _write_exclusive(
            os.path.join(staging, "publish.json"),
            (json.dumps({
                "method": publish_method,
                "target": os.path.basename(target),
            }, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        )
        print(f"wrote {os.path.join(staging, 'calibration.json')}")
        print(f"published {target} via {publish_method}")
        return 0
    except (Exception, SystemExit) as exc:
        if isinstance(exc, CertificationError):
            reason = exc.as_reason()
        elif isinstance(exc, SystemExit):
            reason = f"preflight-failed: {exc}"
        else:
            reason = f"attempt-fatal: {type(exc).__name__}: {str(exc)[:500]}"
        if not (
            isinstance(exc, CertificationError)
            and exc.code == "acquisition-invalid"
            and reasons == ["effective-clock-self-comparison-failed"]
        ):
            reasons = reasons + [reason]
        try:
            candidate_path = os.path.join(staging, "candidate.json")
            if os.path.lexists(candidate_path):
                os.unlink(candidate_path)
            calibration_path = os.path.join(staging, "calibration.json")
            if os.path.exists(calibration_path):
                _write_rejection(
                    staging, reasons, budget,
                    diagnostics=rejection_diagnostics,
                    not_evaluated=rejection_not_evaluated,
                )
            elif result is not None and profile is not None and genome is not None:
                _, artifact = _assemble_v2(
                    result, profile=profile, receipt=receipt, genome=genome,
                    status="rejected", reasons=reasons)
                _write_exclusive(calibration_path, artifact)
            else:
                _write_rejection(
                    staging, reasons, budget,
                    diagnostics=rejection_diagnostics,
                    not_evaluated=rejection_not_evaluated,
                )
        except Exception as receipt_exc:
            print(f"failed to write rejection receipt: {receipt_exc}", file=sys.stderr)
        print("certification rejected: " + "; ".join(reasons), file=sys.stderr)
        return 1


def main(argv: Optional[List[str]] = None, *,
         probe_fn: Optional[Callable[[], object]] = None,
         load1_fn: Optional[Callable[[], float]] = None,
         clock_fn: Optional[Callable[[], object]] = None,
         subprocess_runner: Optional[Callable[..., object]] = None,
         nonce_fn: Optional[Callable[[], str]] = None,
         monotonic_fn: Optional[Callable[[], float]] = None,
         sleep_fn: Optional[Callable[[float], None]] = None,
         calibrate_fn: Optional[Callable[..., CalibrationResult]] = None) -> int:
    args = build_parser().parse_args(argv)
    invalid = _validate_cli(args)
    if invalid:
        print(f"invalid arguments: {invalid}", file=sys.stderr)
        return 2

    if not os.path.exists(args.binary):
        print(f"binary not found: {args.binary}", file=sys.stderr)
        return 2
    if args.certify:
        try:
            return _certify_main(
                args, probe_fn=probe_fn or _default_probe,
                load1_fn=load1_fn or (lambda: os.getloadavg()[0]),
                clock_fn=clock_fn or measure_tsc,
                subprocess_runner=subprocess_runner or subprocess.run,
                nonce_fn=nonce_fn or (lambda: secrets.token_hex(16)),
                monotonic_fn=monotonic_fn or time.monotonic,
                sleep_fn=sleep_fn or time.sleep,
                calibrate_fn=calibrate_fn or calibrate,
            )
        except CertificationError as exc:
            print("certification rejected: " + exc.as_reason(), file=sys.stderr)
            return 1

    _assert_trace_disabled_binary(
        os.path.abspath(args.binary),
        subprocess_runner=subprocess_runner or subprocess.run,
    )
    result = (calibrate_fn or calibrate)(
        binary=os.path.abspath(args.binary), env_tag=args.env_tag,
        threads=args.threads, workload=_parse_kv(args.workload),
        start_records=args.start_records, max_records=args.max_records,
        extime=args.extime, sweep_reps=args.sweep_reps,
        noise_reps=args.noise_reps, numactl=_numactl_arg(args.numactl),
        clocks_per_us=args.clocks_per_us,
    )

    # env スコープに従来の固定 stem で書く。certify はこの経路へ入らない。
    out_dir = os.path.join(_output_root(args.out_root), "env", args.env_tag, "calibration")
    os.makedirs(out_dir, exist_ok=True)
    stem = f"calibration_t{args.threads}_{_workload_tag(_parse_kv(args.workload))}"
    json_path = os.path.join(out_dir, stem + ".json")
    md_path = os.path.join(out_dir, stem + ".md")
    with open(json_path, "w") as f:
        json.dump(result_to_dict(result), f, indent=2, ensure_ascii=False)
    with open(md_path, "w") as f:
        f.write("# calibration: " + args.env_tag + f" / threads={args.threads}\n\n")
        f.write("```\n" + render_text(result) + "\n```\n")
    print()
    print(render_text(result))
    print()
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")
    return 0
