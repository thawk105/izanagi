#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-
"""Pegasus 計算ノード上で sandbox backend を S1〜S7 に分けて実測する。

外部 command の stdout/stderr は receipt に保存する観測データであり、probe の
命令や verdict の理由として解釈しない。verdict 核は subprocess から独立した純関数である。
"""
from __future__ import annotations

import argparse
import contextlib
import ctypes
import dataclasses
import errno
import hashlib
import json
import os
import platform
import re
import shutil
import signal
import socket
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from orchestrator.campaign import condition_meaning_gate  # noqa: E402


SCHEMA_VERSION = "t316-sandbox-backend-probe/v1"
POLICY_SCHEMA_VERSION = "t316-sandbox-backend-policy/v1"
VERDICT_VALUES = frozenset({"go", "no-go", "inconclusive", "blocked"})
S3_CATEGORIES = (
    "network_dns",
    "network_direct_ip",
    "network_proxy",
    "credential_home",
    "credential_ssh_agent",
    "credential_ssh_dir",
    "credential_codex_dir",
    "write_home",
    "write_repo",
    "write_tmp",
    "source_read_only",
)
S5_CATEGORIES = ("system_command", "network", "file_write", "infinite_loop")
S5_PROFILES = ("runtime", "build")
_JOB_ID_RE = re.compile(r"^[A-Za-z0-9._:-]+$")
_OUTPUT_LIMIT = 16 * 1024
_SENTINEL_PREFIX = "T316_SENTINEL"
_ROUTE_CONTAINMENT_ERRNOS = frozenset(
    {"EACCES", "EPERM", "ENETDOWN", "ENETUNREACH", "EHOSTUNREACH", "EAFNOSUPPORT"}
)
_WRITE_CONTAINMENT_ERRNOS = frozenset({"EACCES", "EPERM", "EROFS"})
_INVISIBLE_CONTAINMENT_ERRNOS = frozenset({"ENOENT"})
_WRITE_CATEGORIES = frozenset(
    {"write_home", "write_repo", "write_tmp", "source_read_only", "file_write"}
)
# errno と封じ込め機序の唯一の正本。テストはこの表を独立 literal と比較する。
_CONTAINMENT_ERRNOS_BY_CATEGORY: Mapping[
    str, Mapping[str, frozenset[str]]
] = {
    "network_dns": {
        "denial": frozenset({"EAI_AGAIN", "EAI_NONAME"}), "absence": frozenset()
    },
    "network_direct_ip": {"denial": _ROUTE_CONTAINMENT_ERRNOS, "absence": frozenset()},
    "network_proxy": {"denial": _ROUTE_CONTAINMENT_ERRNOS, "absence": frozenset()},
    "credential_home": {
        "denial": frozenset(), "absence": _INVISIBLE_CONTAINMENT_ERRNOS
    },
    "credential_ssh_agent": {
        "denial": frozenset(), "absence": _INVISIBLE_CONTAINMENT_ERRNOS
    },
    "credential_ssh_dir": {
        "denial": frozenset(), "absence": _INVISIBLE_CONTAINMENT_ERRNOS
    },
    "credential_codex_dir": {
        "denial": frozenset(), "absence": _INVISIBLE_CONTAINMENT_ERRNOS
    },
    "write_home": {
        "denial": _WRITE_CONTAINMENT_ERRNOS, "absence": _INVISIBLE_CONTAINMENT_ERRNOS
    },
    "write_repo": {
        "denial": _WRITE_CONTAINMENT_ERRNOS, "absence": _INVISIBLE_CONTAINMENT_ERRNOS
    },
    "write_tmp": {
        "denial": _WRITE_CONTAINMENT_ERRNOS, "absence": _INVISIBLE_CONTAINMENT_ERRNOS
    },
    "source_read_only": {
        "denial": _WRITE_CONTAINMENT_ERRNOS, "absence": _INVISIBLE_CONTAINMENT_ERRNOS
    },
    "scratch_write": {"denial": frozenset(), "absence": frozenset()},
    "system_command": {
        "denial": frozenset(), "absence": _INVISIBLE_CONTAINMENT_ERRNOS
    },
    "network": {"denial": _ROUTE_CONTAINMENT_ERRNOS, "absence": frozenset()},
    "file_write": {
        "denial": _WRITE_CONTAINMENT_ERRNOS, "absence": _INVISIBLE_CONTAINMENT_ERRNOS
    },
    "escaped_descendant": {"denial": frozenset(), "absence": frozenset()},
    "infinite_loop": {"denial": frozenset(), "absence": frozenset()},
}
# 旧 parser の state view。write の ENOENT だけは既存どおり invalid に保ち、
# verdict が同一 path と副作用なしを検査して absence として扱う。
_CONTAINMENT_DENIALS_BY_CATEGORY: Mapping[str, frozenset[str]] = {
    category: mechanisms["denial"] | (
        mechanisms["absence"] if category not in _WRITE_CATEGORIES else frozenset()
    )
    for category, mechanisms in _CONTAINMENT_ERRNOS_BY_CATEGORY.items()
}
_PAYLOAD_NORMAL_RETURN_CODES = frozenset({0})
_NETWORK_CONNECT_CATEGORIES = frozenset(
    {"network_direct_ip", "network_proxy", "network"}
)
_INERT_CONDITION_GATE_PAIRS: frozenset[tuple[str, str]] = frozenset({
    (
        "stock-inert-preprocess-identical",
        "stock-inert-identity",
    ),
    (
        "stock-inert-preprocess-root-location-only",
        "stock-inert-root-location-only",
    ),
})


@dataclasses.dataclass(frozen=True)
class StageVerdict:
    stage: str
    verdict: str
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.verdict not in VERDICT_VALUES:
            raise ValueError(f"unknown verdict: {self.verdict}")

    def as_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "verdict": self.verdict,
            "reason_codes": list(self.reason_codes),
        }


def _paired_verdict(
    stage: str, category: str, observation: Mapping[str, Any]
) -> StageVerdict:
    """正例と封じ込め負例の一対を副作用なしで判定する。"""
    prefix = f"{stage}_{category}".upper().replace("-", "_")
    if observation.get("attempted") is not True:
        return StageVerdict(stage, "blocked", (f"{prefix}_NOT_ATTEMPTED",))
    if observation.get("outside_process_state") != "normal-exit":
        return StageVerdict(
            stage, "inconclusive", (f"{prefix}_POSITIVE_PROCESS_EXIT_ABNORMAL",)
        )
    if observation.get("outside_payload_state") == "denied":
        return StageVerdict(
            stage, "inconclusive", (f"{prefix}_NODE_CAPABILITY_UNAVAILABLE",)
        )
    if observation.get("outside_payload_state") != "reached":
        return StageVerdict(stage, "inconclusive", (f"{prefix}_POSITIVE_SENTINEL_INVALID",))
    if observation.get("outside_success") is not True:
        return StageVerdict(
            stage, "inconclusive", (f"{prefix}_POSITIVE_CONTROL_FAILED",)
        )
    if observation.get("inside_side_effect_observed") is True:
        return StageVerdict(stage, "no-go", (f"{prefix}_SIDE_EFFECT_OBSERVED",))
    if observation.get("inside_noncontainment_observed") is True:
        return StageVerdict(stage, "no-go", (f"{prefix}_NONCONTAINMENT_FAILURE",))
    if observation.get("inside_process_state") != "normal-exit":
        return StageVerdict(
            stage, "inconclusive", (f"{prefix}_NEGATIVE_PROCESS_EXIT_ABNORMAL",)
        )
    inside_state = observation.get("inside_payload_state")
    sentinel_category = observation.get("sentinel_category")
    mechanisms = (
        _CONTAINMENT_ERRNOS_BY_CATEGORY.get(sentinel_category)
        if isinstance(sentinel_category, str) else None
    )
    absence_observed = (
        isinstance(mechanisms, Mapping)
        and observation.get("inside_payload_detail") in mechanisms["absence"]
        and inside_state in {"denied", "invalid"}
    )
    if absence_observed:
        if sentinel_category in _WRITE_CATEGORIES and (
            observation.get("outside_path") != observation.get("inside_path")
            or not isinstance(observation.get("outside_path"), str)
        ):
            return StageVerdict(
                stage, "inconclusive", (f"{prefix}_POSITIVE_CONTROL_TARGET_MISMATCH",)
            )
        if sentinel_category in _WRITE_CATEGORIES and (
            observation.get("inside_side_effect_observed") is not False
        ):
            return StageVerdict(stage, "no-go", (f"{prefix}_SIDE_EFFECT_UNPROVEN",))
        return StageVerdict(stage, "go", (f"{prefix}_CONTAINED_BY_ABSENCE",))
    if inside_state not in {"reached", "denied"}:
        return StageVerdict(
            stage, "inconclusive", (f"{prefix}_NEGATIVE_SENTINEL_INVALID",)
        )
    if observation.get("inside_blocked") is not True or inside_state != "denied":
        return StageVerdict(stage, "no-go", (f"{prefix}_CONTAINMENT_FAILED",))
    return StageVerdict(stage, "go", (f"{prefix}_CONTAINED",))


def _merge_stage_verdicts(stage: str, verdicts: Sequence[StageVerdict]) -> StageVerdict:
    """同一 stage のカテゴリ判定を no-go 優先で畳み込む純関数。"""
    reasons = tuple(reason for item in verdicts for reason in item.reason_codes)
    values = {item.verdict for item in verdicts}
    for value in ("no-go", "blocked", "inconclusive", "go"):
        if value in values:
            return StageVerdict(stage, value, reasons)
    return StageVerdict(stage, "blocked", (f"{stage}_EMPTY".upper(),))


def verdict_s1(observation: Mapping[str, Any]) -> StageVerdict:
    if observation.get("attempted") is not True:
        return StageVerdict("S1", "blocked", ("S1_INVENTORY_NOT_ATTEMPTED",))
    tools = observation.get("tools")
    if not isinstance(tools, Mapping):
        return StageVerdict("S1", "blocked", ("S1_TOOL_INVENTORY_MISSING",))
    bwrap = tools.get("bwrap")
    if not isinstance(bwrap, Mapping) or bwrap.get("available") is not True:
        return StageVerdict("S1", "no-go", ("S1_BWRAP_UNAVAILABLE",))
    return StageVerdict("S1", "go", ("S1_INVENTORY_COMPLETE",))


def verdict_s2(observation: Mapping[str, Any]) -> StageVerdict:
    if observation.get("attempted") is not True:
        return StageVerdict("S2", "blocked", ("S2_NAMESPACE_NOT_ATTEMPTED",))
    checks = observation.get("namespace_checks")
    if not isinstance(checks, Mapping):
        return StageVerdict("S2", "blocked", ("S2_NAMESPACE_CHECKS_MISSING",))
    missing = [name for name in ("user", "pid", "net", "mnt") if name not in checks]
    if missing:
        return StageVerdict(
            "S2", "blocked", tuple(f"S2_{name.upper()}_NOT_ATTEMPTED" for name in missing)
        )
    failed = [name for name in ("user", "pid", "net", "mnt") if checks.get(name) is not True]
    if failed:
        return StageVerdict(
            "S2", "no-go", tuple(f"S2_{name.upper()}_NAMESPACE_FAILED" for name in failed)
        )
    return StageVerdict("S2", "go", ("S2_REQUIRED_NAMESPACES_STARTED",))


def verdict_s3(observations: Mapping[str, Mapping[str, Any]]) -> StageVerdict:
    verdicts = [
        _paired_verdict("S3", category, observations.get(category, {}))
        for category in S3_CATEGORIES
    ]
    scratch = observations.get("scratch_write")
    if not isinstance(scratch, Mapping) or scratch.get("attempted") is not True:
        verdicts.append(StageVerdict("S3", "blocked", ("S3_SCRATCH_WRITE_NOT_ATTEMPTED",)))
    elif scratch.get("inside_process_state") != "normal-exit":
        verdicts.append(StageVerdict(
            "S3", "inconclusive", ("S3_SCRATCH_WRITE_PROCESS_EXIT_ABNORMAL",)
        ))
    elif scratch.get("inside_success") is not True:
        verdicts.append(StageVerdict("S3", "no-go", ("S3_SCRATCH_WRITE_FAILED",)))
    else:
        verdicts.append(StageVerdict("S3", "go", ("S3_SCRATCH_WRITE_ALLOWED",)))
    return _merge_stage_verdicts("S3", verdicts)


def _verdict_descendant(
    stage: str, prefix: str, observation: Mapping[str, Any]
) -> StageVerdict:
    if observation.get("attempted") is not True:
        return StageVerdict(stage, "blocked", (f"{prefix}_NOT_ATTEMPTED",))
    if observation.get("outside_pid_status") != "alive-same-process":
        return StageVerdict(stage, "inconclusive", (f"{prefix}_POSITIVE_PID_CONTROL_FAILED",))
    inside_status = observation.get("inside_pid_status")
    if inside_status in {"pidfile-missing", "pidfile-invalid", "identity-unresolved"}:
        return StageVerdict(stage, "inconclusive", (f"{prefix}_IDENTITY_UNPROVEN",))
    if inside_status == "alive-same-process":
        return StageVerdict(stage, "no-go", (f"{prefix}_SURVIVED",))
    if inside_status not in {"gone", "pid-reused"}:
        return StageVerdict(stage, "inconclusive", (f"{prefix}_STATUS_INVALID",))
    return StageVerdict(stage, "go", (f"{prefix}_TERMINATED",))


def verdict_s4(observation: Mapping[str, Any]) -> StageVerdict:
    return _verdict_descendant("S4", "S4_ESCAPED_DESCENDANT", observation)


def verdict_s5(observations: Mapping[str, Mapping[str, Any]]) -> StageVerdict:
    verdicts: list[StageVerdict] = []
    for profile_name in S5_PROFILES:
        profile_observations = observations.get(profile_name, {})
        if not isinstance(profile_observations, Mapping):
            profile_observations = {}
        for category in S5_CATEGORIES:
            observation = profile_observations.get(category, {})
            if category == "infinite_loop":
                verdicts.append(
                    _verdict_descendant(
                        "S5", f"S5_{profile_name}_{category}".upper(), observation
                    )
                )
            else:
                verdicts.append(
                    _paired_verdict(
                        "S5", f"{profile_name}_{category}", observation
                    )
                )
    return _merge_stage_verdicts("S5", verdicts)


def _condition_gate_receipt_summary(
    value: tuple[
        condition_meaning_gate.ConditionArmRecord,
        condition_meaning_gate.ConditionArmRecord,
        condition_meaning_gate.ConditionFamilyAdmission,
    ],
) -> list[dict[str, Any]]:
    """Persist digests and conclusions, never an arm record or issuer claim.

    The live records are re-admitted by ``_condition_gate_family_valid`` before
    this summary is accepted.  JSON readers can compare the persisted result,
    but cannot reconstruct the evaluator-only issuer capability from it.
    """
    supply, meaning, admission = value
    return [
        {
            "arm": supply.arm,
            "record_digest": supply.record_digest,
            "terminal_status": supply.terminal_status,
            "reason_code": supply.reason_code,
            "comparison": supply.evidence.get("comparison"),
        },
        {
            "arm": meaning.arm,
            "record_digest": meaning.record_digest,
            "terminal_status": meaning.terminal_status,
            "reason_code": meaning.reason_code,
        },
        {
            "kind": "family-admission",
            "admission_digest": admission.admission_digest,
            "use_class": admission.use_class,
            "admitted": admission.admitted,
        },
    ]


def _condition_gate_family_valid(
    value: object,
    receipt_summary: object,
) -> bool:
    if type(value) is not tuple or len(value) != 3:
        return False
    try:
        supply, meaning, observed = value
        if type(supply) is not condition_meaning_gate.ConditionArmRecord \
                or type(meaning) is not condition_meaning_gate.ConditionArmRecord \
                or type(observed) is not condition_meaning_gate.ConditionFamilyAdmission:
            return False
        expected = condition_meaning_gate.require_condition_gate_family(
            [supply], [meaning], use_class="raw-measurement",
        )
    except (TypeError, ValueError, condition_meaning_gate.ConditionMeaningGateError):
        return False
    return (
        observed == expected
        and receipt_summary == _condition_gate_receipt_summary(value)
        and observed.admitted is True
        and supply.driver_id == "tools.pegasus.probes.t316_sandbox_backend_probe"
        and supply.macro == meaning.macro == "BACKOFF_FIXED"
        and supply.terminal_status == "green"
        and (
            supply.reason_code,
            supply.evidence.get("comparison"),
        ) in _INERT_CONDITION_GATE_PAIRS
        and meaning.terminal_status == "unestablished"
        and meaning.reason_code == "meaning-witness-undeclared"
    )


def verdict_s6(observation: Mapping[str, Any]) -> StageVerdict:
    if observation.get("attempted") is not True:
        return StageVerdict("S6", "blocked", ("S6_BUILD_NOT_ATTEMPTED",))
    if observation.get("failure_stage") == "walltime":
        return StageVerdict("S6", "blocked", ("S6_WALLTIME_RESERVE_REACHED",))
    if observation.get("failure_stage") == "toolchain-unavailable":
        return StageVerdict("S6", "blocked", ("S6_TOOLCHAIN_UNAVAILABLE",))
    if observation.get("source_identity_valid") is not True:
        return StageVerdict("S6", "inconclusive", ("S6_SOURCE_IDENTITY_INVALID",))
    if not _condition_gate_family_valid(
        observation.get("_condition_gate_family"),
        observation.get("condition_gates"),
    ):
        return StageVerdict("S6", "inconclusive", ("S6_CONDITION_GATE_UNPROVEN",))
    toolchain = observation.get("toolchain")
    if isinstance(toolchain, Mapping) and toolchain.get("sandbox_valid") is not True:
        return StageVerdict("S6", "no-go", ("S6_SANDBOX_TOOLCHAIN_UNAVAILABLE",))
    if observation.get("outside_success") is not True:
        return StageVerdict("S6", "inconclusive", ("S6_OUTSIDE_BUILD_FAILED",))
    if observation.get("inside_success") is not True:
        return StageVerdict("S6", "no-go", ("S6_SANDBOX_BUILD_FAILED",))
    if observation.get("trace_disabled") is not True:
        return StageVerdict("S6", "no-go", ("S6_TRACE_DISABLED_NOT_PROVEN",))
    return StageVerdict("S6", "go", ("S6_SANDBOX_BUILD_SUCCEEDED",))


def verdict_s7(observation: Mapping[str, Any]) -> StageVerdict:
    if observation.get("attempted") is not True:
        return StageVerdict("S7", "blocked", ("S7_PERFORMANCE_NOT_ATTEMPTED",))
    if observation.get("cleanup_integrity_valid") is False:
        return StageVerdict(
            "S7", "inconclusive", ("S7_PREVIOUS_PAYLOAD_CLEANUP_UNPROVEN",)
        )
    if observation.get("blocked_reason"):
        return StageVerdict("S7", "blocked", ("S7_MEASUREMENT_PREREQUISITE_MISSING",))
    if observation.get("outside_success") is not True:
        return StageVerdict("S7", "inconclusive", ("S7_OUTSIDE_RUN_FAILED",))
    if observation.get("inside_success") is not True:
        return StageVerdict("S7", "no-go", ("S7_SANDBOX_RUN_FAILED",))
    if observation.get("same_binary") is not True:
        return StageVerdict("S7", "inconclusive", ("S7_BINARY_IDENTITY_MISMATCH",))
    if observation.get("trace_disabled") is not True:
        return StageVerdict("S7", "no-go", ("S7_TRACE_DISABLED_NOT_PROVEN",))
    if observation.get("exclusivity_valid") is not True:
        return StageVerdict("S7", "inconclusive", ("S7_EXCLUSIVITY_INVALID",))
    if observation.get("perf_output_valid") is not True:
        return StageVerdict("S7", "inconclusive", ("S7_PERF_OUTPUT_INVALID",))
    if observation.get("effective_thread_count_valid") is not True:
        return StageVerdict("S7", "inconclusive", ("S7_EFFECTIVE_THREAD_COUNT_INVALID",))
    if observation.get("warmup_valid") is not True:
        return StageVerdict("S7", "inconclusive", ("S7_WARMUP_FAILED",))
    ratio = observation.get("elapsed_overhead_ratio_median")
    if not isinstance(ratio, (int, float)) or isinstance(ratio, bool) or ratio <= 0:
        return StageVerdict("S7", "inconclusive", ("S7_OVERHEAD_RATIO_UNAVAILABLE",))
    return StageVerdict("S7", "go", ("S7_ELAPSED_OVERHEAD_SAMPLE_RECORDED_ONLY",))


def aggregate_verdicts(verdicts: Sequence[StageVerdict]) -> StageVerdict:
    """S1〜S7 の総合 verdict。1 個でも no-go なら決して go にしない。"""
    by_stage = {item.stage: item for item in verdicts}
    missing = [f"S{index}" for index in range(1, 8) if f"S{index}" not in by_stage]
    if missing:
        return StageVerdict(
            "overall", "blocked", tuple(f"OVERALL_{stage}_MISSING" for stage in missing)
        )
    reasons = tuple(reason for item in verdicts for reason in item.reason_codes)
    values = {item.verdict for item in verdicts}
    for value in ("no-go", "blocked", "inconclusive", "go"):
        if value in values:
            return StageVerdict("overall", value, reasons)
    return StageVerdict("overall", "blocked", ("OVERALL_EMPTY",))


def _r3_1_coverage(verdicts: Sequence[StageVerdict]) -> dict[str, Any]:
    by_stage = {item.stage: item.verdict for item in verdicts}
    discharged: list[str] = []
    if all(by_stage.get(f"S{index}") == "go" for index in range(1, 6)):
        discharged.append("compute-node backend containment observations")
    if by_stage.get("S7") == "go":
        discharged.append(
            "single stock trace-disabled binary sandbox elapsed-overhead sample"
        )
    return {
        "overall_go_does_not_mean_r3_1_complete": True,
        "discharged_by_this_probe": discharged,
        "not_discharged_by_this_probe": [
            "stock and variant performance difference",
            "trace-enabled correctness run",
            "floor recalibration requirement determination",
        ],
    }


def _error(exc: BaseException) -> dict[str, str]:
    return {"type": type(exc).__name__, "message": str(exc)}


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _bounded_output(value: bytes) -> dict[str, Any]:
    return {
        "sha256": _sha256_bytes(value),
        "bytes": len(value),
        "tail": value[-_OUTPUT_LIMIT:].decode("utf-8", errors="replace"),
        "truncated": len(value) > _OUTPUT_LIMIT,
    }


def _redact_arg(value: str) -> str:
    """URI credential/query を receipt の argv へ残さない。"""
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"} and parsed.hostname:
        port = f":{parsed.port}" if parsed.port is not None else ""
        return f"{parsed.scheme}://{parsed.hostname}{port}"
    return value


def _parse_payload_sentinel(record: Mapping[str, Any], category: str) -> dict[str, Any]:
    stdout = record.get("stdout")
    tail = stdout.get("tail", "") if isinstance(stdout, Mapping) else ""
    prefix = f"{_SENTINEL_PREFIX}|{category}|"
    matches = [line for line in str(tail).splitlines() if line.startswith(prefix)]
    if len(matches) != 1:
        return {"state": "missing", "detail": None}
    fields = matches[0].split("|")
    if len(fields) == 3 and fields[2] == "REACHED":
        return {"state": "reached", "detail": None}
    if len(fields) == 4 and fields[2] == "DENIED":
        errno_name = fields[3]
        if errno_name == "ECONNREFUSED" and category in _NETWORK_CONNECT_CATEGORIES:
            return {"state": "reached", "detail": errno_name}
        allowed_denials = _CONTAINMENT_DENIALS_BY_CATEGORY.get(category)
        return {
            "state": "denied"
            if allowed_denials is not None and errno_name in allowed_denials
            else "invalid",
            "detail": errno_name,
        }
    if len(fields) == 4 and fields[2] == "ERROR":
        return {"state": "error", "detail": fields[3]}
    return {"state": "missing", "detail": None}


def _process_exit(record: Mapping[str, Any]) -> dict[str, Any]:
    if record.get("executed") is not True:
        return {"state": "not-executed", "detail": None}
    rc = record.get("rc")
    if record.get("timed_out") is True:
        return {"state": "timed-out", "detail": rc}
    if record.get("timed_out") is not False or type(rc) is not int:
        return {"state": "invalid", "detail": rc}
    if rc < 0:
        return {"state": "signal-exit", "detail": rc}
    if rc not in _PAYLOAD_NORMAL_RETURN_CODES:
        return {"state": "unexpected-exit", "detail": rc}
    return {"state": "normal-exit", "detail": rc}


def _descendants(root_pid: int) -> set[int]:
    parents: dict[int, int] = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            fields = (entry / "stat").read_text(encoding="utf-8").split()
            parents[int(entry.name)] = int(fields[3])
        except (OSError, ValueError, IndexError):
            continue
    result: set[int] = set()
    frontier = {root_pid}
    while frontier:
        children = {pid for pid, ppid in parents.items() if ppid in frontier and pid not in result}
        result.update(children)
        frontier = children
    return result


def _kill_tree(root_pid: int) -> None:
    targets = _descendants(root_pid) | {root_pid}
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for pid in sorted(targets, reverse=True):
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                pass
        if sig == signal.SIGTERM:
            time.sleep(0.2)


def _process_tree_max_single_process_threads(root_pid: int) -> int:
    maximum = 0
    for pid in _descendants(root_pid) | {root_pid}:
        try:
            maximum = max(
                maximum,
                sum(1 for _ in (Path("/proc") / str(pid) / "task").iterdir()),
            )
        except OSError:
            continue
    return maximum


def _run_command(
    argv: Sequence[str], *, timeout_s: float, env: Optional[Mapping[str, str]] = None,
    monitor_threads: bool = False,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "attempted": True,
        "executed": False,
        "argv": [_redact_arg(value) for value in argv],
        "timeout_s": timeout_s,
        "rc": None,
        "timed_out": False,
    }
    started = time.monotonic_ns()
    process: Optional[subprocess.Popen[bytes]] = None
    monitor_stop = threading.Event()
    max_threads = 0
    monitor: Optional[threading.Thread] = None
    try:
        process = subprocess.Popen(
            list(argv),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=None if env is None else dict(env),
            start_new_session=True,
        )
        record["executed"] = True
        if monitor_threads:
            def sample_threads() -> None:
                nonlocal max_threads
                while not monitor_stop.wait(0.02):
                    max_threads = max(
                        max_threads,
                        _process_tree_max_single_process_threads(process.pid),
                    )
            monitor = threading.Thread(target=sample_threads, daemon=True)
            monitor.start()
        stdout, stderr = process.communicate(timeout=timeout_s)
        record["rc"] = process.returncode
    except subprocess.TimeoutExpired:
        record["timed_out"] = True
        assert process is not None
        _kill_tree(process.pid)
        stdout, stderr = process.communicate()
        record["rc"] = process.returncode
    except OSError as exc:
        stdout = b""
        stderr = b""
        record["error"] = _error(exc)
    finally:
        monitor_stop.set()
        if monitor is not None:
            monitor.join(timeout=1)
    record["elapsed_ns"] = time.monotonic_ns() - started
    record["stdout"] = _bounded_output(stdout)
    record["stderr"] = _bounded_output(stderr)
    if monitor_threads:
        record["max_single_process_threads"] = max_threads
    return record


def _run_group_timeout(argv: Sequence[str], *, timeout_s: float) -> dict[str, Any]:
    """process group だけを timeout kill し、setsid() escape の対照を作る。"""
    record: dict[str, Any] = {
        "attempted": True,
        "executed": False,
        "argv": list(argv),
        "timeout_s": timeout_s,
        "rc": None,
        "timed_out": False,
    }
    started = time.monotonic_ns()
    process: Optional[subprocess.Popen[bytes]] = None
    try:
        process = subprocess.Popen(
            list(argv), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, start_new_session=True,
        )
        record["executed"] = True
        try:
            stdout, stderr = process.communicate(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            record["timed_out"] = True
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
        record["rc"] = process.returncode
    except OSError as exc:
        stdout = b""
        stderr = b""
        record["error"] = _error(exc)
    record["elapsed_ns"] = time.monotonic_ns() - started
    record["stdout"] = _bounded_output(stdout)
    record["stderr"] = _bounded_output(stderr)
    return record


def _tool_record(name: str) -> dict[str, Any]:
    path = shutil.which(name)
    record: dict[str, Any] = {"available": path is not None, "path": path}
    if path is not None:
        record["version"] = _run_command([path, "--version"], timeout_s=10)
    return record


def _process_group(pairs: Sequence[tuple[int, int]]) -> dict[str, Any]:
    return {
        "present": bool(pairs),
        "count": len(pairs),
        "uids": sorted({uid for _pid, uid in pairs}),
        "pids": sorted(pid for pid, _uid in pairs),
    }


def _classify_process_owners(
    process_owners: Mapping[int, int], own_uid: int
) -> dict[str, Any]:
    pairs = sorted(process_owners.items())
    other_non_root = [
        (pid, uid) for pid, uid in pairs if uid not in (0, own_uid)
    ]
    co_tenants = [
        (pid, uid) for pid, uid in pairs if uid >= 1000 and uid != own_uid
    ]
    excluded_system = [
        (pid, uid) for pid, uid in pairs if uid < 1000 and uid != own_uid
    ]
    excluded_own = [(pid, uid) for pid, uid in pairs if uid == own_uid]
    return {
        # 旧観測を落とさず残す。専有判定には次の uid>=1000 集合だけを使う。
        "other_non_root_user_processes": _process_group(other_non_root),
        "other_non_system_user_processes": _process_group(co_tenants),
        "excluded_system_processes": _process_group(excluded_system),
        "excluded_own_processes": _process_group(excluded_own),
        "co_tenant_uid_minimum": 1000,
        "own_uid": own_uid,
    }


def _process_tenancy_evidence() -> dict[str, Any]:
    process_owners: dict[int, int] = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            line = next(
                item for item in (entry / "status").read_text(encoding="utf-8").splitlines()
                if item.startswith("Uid:")
            )
            uid = int(line.split()[1])
        except (OSError, StopIteration, ValueError, IndexError):
            continue
        process_owners[int(entry.name)] = uid
    return _classify_process_owners(process_owners, os.getuid())


def _landlock_record() -> dict[str, Any]:
    if platform.machine() not in {"x86_64", "aarch64"}:
        return {"attempted": False, "available": None, "reason": "unsupported syscall table"}
    libc = ctypes.CDLL(None, use_errno=True)
    result = int(libc.syscall(444, 0, 0, 1))
    saved_errno = ctypes.get_errno()
    return {
        "attempted": True,
        "available": result >= 1,
        "abi_version": result if result >= 1 else None,
        "errno": None if result >= 1 else saved_errno,
        "errno_name": None if result >= 1 else errno.errorcode.get(saved_errno),
    }


def observe_s1() -> dict[str, Any]:
    status = Path("/proc/self/status").read_text(encoding="utf-8")
    seccomp_lines = [line for line in status.splitlines() if line.startswith("Seccomp")]
    userns_path = Path("/proc/sys/user/max_user_namespaces")
    return {
        "attempted": True,
        "tools": {name: _tool_record(name) for name in ("bwrap", "unshare", "setpriv", "nsenter")},
        "kernel_release": platform.release(),
        "hostname": socket.gethostname(),
        "PBS_JOBID": os.environ.get("PBS_JOBID"),
        "seccomp": {
            "status": seccomp_lines,
            "actions_available": Path("/proc/sys/kernel/seccomp/actions_avail").read_text(encoding="utf-8").strip()
            if Path("/proc/sys/kernel/seccomp/actions_avail").is_file() else None,
        },
        "user_namespace": {
            "max_user_namespaces": userns_path.read_text(encoding="utf-8").strip()
            if userns_path.is_file() else None,
        },
        "landlock": _landlock_record(),
        "exclusivity_evidence": {
            "load_average": list(os.getloadavg()),
            **_process_tenancy_evidence(),
            "nproc": os.cpu_count(),
            "cpu_affinity": sorted(os.sched_getaffinity(0)),
        },
    }


class SandboxProfile:
    def __init__(
        self,
        bwrap: Optional[str],
        repo_root: Path,
        scratch: Path,
        readonly_roots: Sequence[Path],
        runner: Callable[..., dict[str, Any]] = _run_command,
    ) -> None:
        self.bwrap = bwrap
        self.repo_root = repo_root
        self.scratch = scratch
        self.runner = runner
        unique = {path.resolve(strict=True) for path in readonly_roots if path.exists()}
        unique.add(repo_root.resolve(strict=True))
        self.readonly_roots = tuple(sorted(unique, key=str))

    def argv(
        self,
        command: Sequence[str],
        *,
        build: bool = False,
        extra_env: Optional[Mapping[str, str]] = None,
    ) -> Optional[list[str]]:
        if self.bwrap is None:
            return None
        argv = [
            self.bwrap,
            "--unshare-user",
            "--unshare-pid",
            "--unshare-net",
            "--unshare-ipc",
            "--unshare-uts",
            "--die-with-parent",
            "--new-session",
            "--clearenv",
            "--proc", "/proc",
            "--dev", "/dev",
        ]
        for source in (Path("/usr"), Path("/lib"), Path("/lib64"), Path("/etc")):
            if source.exists():
                argv.extend(("--ro-bind", str(source), str(source)))
        if build and Path("/bin").exists():
            argv.extend(("--ro-bind", "/bin", "/bin"))
        else:
            argv.extend(("--dir", "/bin"))
        argv.extend(("--ro-bind", str(self.scratch / "empty-tmp"), "/tmp"))
        argv.extend(("--dir", "/home"))
        for source in self.readonly_roots:
            argv.extend(("--ro-bind", str(source), str(source)))
        argv.extend(("--bind", str(self.scratch), str(self.scratch)))
        environment = {
            "PATH": f"{self.scratch / 'python-shim'}:/usr/bin:/bin",
            "HOME": str(self.scratch / "home"),
            "TMPDIR": str(self.scratch / "tmp"),
            "LC_ALL": "C",
        }
        environment.update(extra_env or {})
        for key, value in sorted(environment.items()):
            argv.extend(("--setenv", key, value))
        argv.extend(("--chdir", str(self.scratch), "--"))
        argv.extend(command)
        return argv

    def run(
        self,
        command: Sequence[str],
        *,
        timeout_s: float,
        build: bool = False,
        extra_env: Optional[Mapping[str, str]] = None,
        monitor_threads: bool = False,
    ) -> dict[str, Any]:
        argv = self.argv(command, build=build, extra_env=extra_env)
        if argv is None:
            return {"attempted": False, "executed": False, "reason": "bwrap unavailable"}
        return self.runner(argv, timeout_s=timeout_s, monitor_threads=monitor_threads)


def observe_s2(profile: SandboxProfile, python: str) -> dict[str, Any]:
    helper = (
        "import json,os; print(json.dumps({n:os.readlink('/proc/self/ns/'+n) "
        "for n in ('user','pid','net','mnt')}))"
    )
    outside = _run_command([python, "-I", "-B", "-c", helper], timeout_s=10)
    inside = profile.run([python, "-I", "-B", "-c", helper], timeout_s=20)
    checks: dict[str, bool] = {}
    try:
        outside_ns = json.loads(outside["stdout"]["tail"])
        inside_ns = json.loads(inside["stdout"]["tail"])
        for name in ("user", "pid", "net", "mnt"):
            checks[name] = inside.get("rc") == 0 and outside_ns[name] != inside_ns[name]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        checks = {}
    return {
        "attempted": outside.get("executed") is True and inside.get("attempted") is True,
        "outside": outside,
        "inside": inside,
        "namespace_checks": checks,
    }


def _paired_command(
    profile: SandboxProfile,
    command: Sequence[str],
    *,
    sentinel_category: str,
    timeout_s: float = 15,
    build_profile: bool = False,
    extra_env: Optional[Mapping[str, str]] = None,
) -> dict[str, Any]:
    outside = profile.runner(
        command, timeout_s=timeout_s, env={**os.environ, **(extra_env or {})}
    )
    inside = profile.run(
        command, timeout_s=timeout_s, build=build_profile, extra_env=extra_env
    )
    outside_payload = _parse_payload_sentinel(outside, sentinel_category)
    inside_payload = _parse_payload_sentinel(inside, sentinel_category)
    outside_process = _process_exit(outside)
    inside_process = _process_exit(inside)
    return {
        "attempted": outside.get("executed") is True and inside.get("attempted") is True,
        "sentinel_category": sentinel_category,
        "outside_success": (
            outside_payload["state"] == "reached"
            and outside_process["state"] == "normal-exit"
        ),
        "inside_blocked": (
            inside_payload["state"] == "denied"
            and inside_process["state"] == "normal-exit"
        ),
        "outside_payload_state": outside_payload["state"],
        "outside_payload_detail": outside_payload["detail"],
        "inside_payload_state": inside_payload["state"],
        "inside_payload_detail": inside_payload["detail"],
        "outside_process_state": outside_process["state"],
        "outside_process_detail": outside_process["detail"],
        "inside_process_state": inside_process["state"],
        "inside_process_detail": inside_process["detail"],
        "outside": outside,
        "inside": inside,
    }


def _network_command(python: str, category: str, host: str, port: int) -> list[str]:
    code = (
        "import errno,socket,sys\n"
        "p,c,h,port=sys.argv[1:5]\n"
        "try:\n s=socket.create_connection((h,int(port)),4); s.close(); print(f'{p}|{c}|REACHED',flush=True)\n"
        "except socket.gaierror as e:\n name='EAI_AGAIN' if e.errno==getattr(socket,'EAI_AGAIN',-3) else ('EAI_NONAME' if e.errno==getattr(socket,'EAI_NONAME',-2) else 'GAI_ERROR'); print(f'{p}|{c}|DENIED|{name}',flush=True)\n"
        "except OSError as e:\n print(f'{p}|{c}|DENIED|{errno.errorcode.get(e.errno,\"OS_ERROR\")}',flush=True)"
    )
    return [python, "-I", "-B", "-c", code, _SENTINEL_PREFIX, category, host, str(port)]


def _proxy_command(python: str, host: str, port: int) -> list[str]:
    return _network_command(python, "network_proxy", host, port)


def _network_targets() -> tuple[str, str, int]:
    """名前解決 target、同 endpoint の直接 IP、port を返す。"""
    proxy_value = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy_value:
        parsed = urlparse(proxy_value)
        if parsed.hostname:
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            try:
                addresses = socket.getaddrinfo(parsed.hostname, port, socket.AF_INET, socket.SOCK_STREAM)
                if addresses:
                    return "example.com", str(addresses[0][4][0]), port
            except socket.gaierror:
                pass
    return "example.com", "1.1.1.1", 443


@contextlib.contextmanager
def _controlled_unix_socket(path: Path):
    _cleanup_marker(path)
    server = socket.socket(socket.AF_UNIX)
    server.bind(str(path))
    server.listen(4)
    server.settimeout(0.1)
    stop = threading.Event()

    def serve() -> None:
        while not stop.is_set():
            try:
                connection, _ = server.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            connection.close()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop.set()
        server.close()
        thread.join(timeout=1)
        _cleanup_marker(path)


def _read_command(
    python: str, category: str, path: Path, *, socket_path: bool = False
) -> list[str]:
    if socket_path:
        action = "s=socket.socket(socket.AF_UNIX); s.settimeout(3); s.connect(path); s.close()"
    else:
        action = "os.listdir(path)"
    code = (
        "import errno,os,socket,sys\n"
        "p,c,path=sys.argv[1:4]\n"
        f"try:\n {action}; print(f'{{p}}|{{c}}|REACHED',flush=True)\n"
        "except OSError as e:\n print(f'{p}|{c}|DENIED|{errno.errorcode.get(e.errno,\"OS_ERROR\")}',flush=True)"
    )
    return [python, "-I", "-B", "-c", code, _SENTINEL_PREFIX, category, str(path)]


def _write_command(python: str, category: str, path: Path) -> list[str]:
    code = (
        "import errno,os,sys\n"
        "p,c,path=sys.argv[1:4]\n"
        "try:\n fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600); os.write(fd,b't316'); os.close(fd); print(f'{p}|{c}|REACHED',flush=True)\n"
        "except OSError as e:\n print(f'{p}|{c}|DENIED|{errno.errorcode.get(e.errno,\"OS_ERROR\")}',flush=True)"
    )
    return [python, "-I", "-B", "-c", code, _SENTINEL_PREFIX, category, str(path)]


def _cleanup_marker(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _observe_write_pair(
    profile: SandboxProfile,
    outside_command: Sequence[str],
    inside_command: Sequence[str],
    outside_path: Path,
    inside_path: Path,
    category: str,
    *,
    build: bool = False,
) -> dict[str, Any]:
    """実 command seam と marker 副作用を同時に通す write observer。"""
    outside = profile.runner(outside_command, timeout_s=15, env=dict(os.environ))
    outside_payload = _parse_payload_sentinel(outside, category)
    outside_process = _process_exit(outside)
    outside_marker_present = outside_path.is_file()
    if outside_path == inside_path and outside_marker_present:
        _cleanup_marker(outside_path)
    inside = profile.run(inside_command, timeout_s=15, build=build)
    inside_payload = _parse_payload_sentinel(inside, category)
    inside_process = _process_exit(inside)
    inside_marker_present = inside_path.is_file()
    return {
        "attempted": outside.get("executed") is True and inside.get("attempted") is True,
        "sentinel_category": category,
        "outside_success": (
            outside_payload["state"] == "reached"
            and outside_process["state"] == "normal-exit"
            and outside_marker_present
        ),
        "inside_blocked": (
            inside_payload["state"] == "denied"
            and inside_process["state"] == "normal-exit"
            and not inside_marker_present
        ),
        "inside_side_effect_observed": inside_marker_present,
        "outside_payload_state": outside_payload["state"],
        "outside_payload_detail": outside_payload["detail"],
        "inside_payload_state": inside_payload["state"],
        "inside_payload_detail": inside_payload["detail"],
        "outside_process_state": outside_process["state"],
        "outside_process_detail": outside_process["detail"],
        "inside_process_state": inside_process["state"],
        "inside_process_detail": inside_process["detail"],
        "outside_path": str(outside_path),
        "inside_path": str(inside_path),
        "outside": outside,
        "inside": inside,
    }


def _observe_system_pair(
    profile: SandboxProfile,
    binary: Path,
    outside_path: Path,
    inside_path: Path,
    *,
    build: bool,
) -> dict[str, Any]:
    outside = profile.runner(
        [str(binary), "system", str(outside_path), "system_command"],
        timeout_s=15,
        env=dict(os.environ),
    )
    inside = profile.run(
        [str(binary), "system", str(inside_path), "system_command"],
        timeout_s=15,
        build=build,
    )
    outside_payload = _parse_payload_sentinel(outside, "system_command")
    inside_payload = _parse_payload_sentinel(inside, "system_command")
    outside_process = _process_exit(outside)
    inside_process = _process_exit(inside)
    inside_marker_present = inside_path.is_file()
    command_failure_details = {
        "COMMAND_ABNORMAL",
        "SIDE_EFFECT_WITH_FAILURE",
    }
    inside_detail = inside_payload["detail"]
    command_ran_but_failed = (
        inside_payload["state"] == "error"
        and isinstance(inside_detail, str)
        and (
            inside_detail.startswith("COMMAND_EXIT_")
            or inside_detail in command_failure_details
        )
    )
    return {
        "attempted": outside.get("executed") is True and inside.get("attempted") is True,
        "outside_success": (
            outside_payload["state"] == "reached"
            and outside_process["state"] == "normal-exit"
            and outside_path.is_file()
        ),
        "inside_blocked": (
            inside_payload["state"] == "denied"
            and inside_process["state"] == "normal-exit"
            and not inside_marker_present
        ),
        "inside_side_effect_observed": inside_marker_present,
        "inside_noncontainment_observed": command_ran_but_failed,
        "outside_payload_state": outside_payload["state"],
        "outside_payload_detail": outside_payload["detail"],
        "inside_payload_state": inside_payload["state"],
        "inside_payload_detail": inside_detail,
        "outside_process_state": outside_process["state"],
        "outside_process_detail": outside_process["detail"],
        "inside_process_state": inside_process["state"],
        "inside_process_detail": inside_process["detail"],
        "outside": outside,
        "inside": inside,
    }


def observe_s3(profile: SandboxProfile, python: str, repo_root: Path, scratch: Path) -> dict[str, Any]:
    job_tag = re.sub(r"[^A-Za-z0-9_.-]", "_", os.environ.get("PBS_JOBID", "unknown"))
    home = Path(os.environ.get("HOME", "/nonexistent"))
    observations: dict[str, Any] = {}
    dns_host, direct_ip, network_port = _network_targets()
    observations["network_dns"] = _paired_command(
        profile, _network_command(python, "network_dns", dns_host, network_port),
        sentinel_category="network_dns",
    )
    observations["network_dns"]["target"] = {
        "host": dns_host, "port": network_port, "requires_name_resolution": True
    }
    observations["network_direct_ip"] = _paired_command(
        profile, _network_command(python, "network_direct_ip", direct_ip, network_port),
        sentinel_category="network_direct_ip",
    )
    observations["network_direct_ip"]["target"] = {"ip": direct_ip, "port": network_port}

    proxy_env = {
        key: value for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy")
        if (value := os.environ.get(key))
    }
    if proxy_env:
        proxy_value = next(iter(proxy_env.values()))
        parsed_proxy = urlparse(proxy_value)
        proxy_host = parsed_proxy.hostname
        proxy_port = parsed_proxy.port or (443 if parsed_proxy.scheme == "https" else 80)
        if proxy_host is None:
            observations["network_proxy"] = {
                "attempted": False, "reason": "proxy environment URI has no hostname"
            }
        else:
            try:
                proxy_addresses = socket.getaddrinfo(
                    proxy_host, proxy_port, socket.AF_INET, socket.SOCK_STREAM
                )
                proxy_ip = str(proxy_addresses[0][4][0])
            except (IndexError, socket.gaierror):
                observations["network_proxy"] = {
                    "attempted": False,
                    "reason": "proxy hostname did not resolve outside sandbox",
                }
            else:
                observations["network_proxy"] = _paired_command(
                    profile, _proxy_command(python, proxy_ip, proxy_port), timeout_s=15,
                    sentinel_category="network_proxy",
                )
                observations["network_proxy"]["direct_ip"] = proxy_ip
            observations["network_proxy"]["proxy_endpoints"] = {
                key: {
                    "scheme": urlparse(value).scheme,
                    "hostname": urlparse(value).hostname,
                    "port": urlparse(value).port,
                }
                for key, value in proxy_env.items()
            }
    else:
        observations["network_proxy"] = {"attempted": False, "reason": "no HTTP(S) proxy environment variable"}

    credential_targets = {
        "credential_home": (home, False),
        "credential_ssh_dir": (home / ".ssh", False),
        "credential_codex_dir": (home / ".codex", False),
    }
    for category, (path, is_socket) in credential_targets.items():
        observations[category] = _paired_command(
            profile, _read_command(python, category, path, socket_path=is_socket),
            sentinel_category=category,
        )

    controlled_socket = Path("/tmp") / f"t316-agent-{job_tag}.sock"
    with _controlled_unix_socket(controlled_socket):
        observations["credential_ssh_agent"] = _paired_command(
            profile,
            _read_command(
                python, "credential_ssh_agent", controlled_socket, socket_path=True
            ),
            sentinel_category="credential_ssh_agent",
        )
    observations["credential_ssh_agent"]["positive_control"] = "compute-node-local-unix-socket"

    write_targets = {
        "write_home": home / f".t316-write-{job_tag}",
        "write_repo": repo_root / f".t316-write-{job_tag}",
        "write_tmp": Path("/tmp") / f"t316-write-{job_tag}",
        "source_read_only": repo_root / f".t316-source-ro-{job_tag}",
    }
    for category, base_path in write_targets.items():
        target_path = base_path.with_name(base_path.name + "-paired")
        _cleanup_marker(target_path)
        observations[category] = _observe_write_pair(
            profile,
            _write_command(python, category, target_path),
            _write_command(python, category, target_path),
            target_path,
            target_path,
            category,
        )
        _cleanup_marker(target_path)

    scratch_marker = scratch / "s3-scratch-write"
    _cleanup_marker(scratch_marker)
    inside = profile.run(
        _write_command(python, "scratch_write", scratch_marker), timeout_s=10
    )
    scratch_payload = _parse_payload_sentinel(inside, "scratch_write")
    scratch_process = _process_exit(inside)
    observations["scratch_write"] = {
        "attempted": inside.get("attempted") is True,
        "inside_success": (
            scratch_payload["state"] == "reached"
            and scratch_process["state"] == "normal-exit"
            and scratch_marker.is_file()
        ),
        "inside_payload_state": scratch_payload["state"],
        "inside_process_state": scratch_process["state"],
        "inside_process_detail": scratch_process["detail"],
        "inside": inside,
    }
    _cleanup_marker(scratch_marker)
    return observations


def _proc_identity(pid: int) -> Optional[tuple[int, bytes]]:
    try:
        fields = (Path("/proc") / str(pid) / "stat").read_text(encoding="utf-8").split()
        cmdline = (Path("/proc") / str(pid) / "cmdline").read_bytes()
        return int(fields[21]), cmdline
    except (OSError, ValueError, IndexError):
        return None


def _cmdline_has_token(cmdline: bytes, token: str) -> bool:
    return token.encode("utf-8") in cmdline.split(b"\0")


def _token_process_identities(token: str) -> dict[int, int]:
    matches: dict[int, int] = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        identity = _proc_identity(pid)
        if identity is not None and _cmdline_has_token(identity[1], token):
            matches[pid] = identity[0]
    return matches


def _find_host_pid(token: str, start_ticks: int, namespace_pid: int) -> Optional[int]:
    matches: list[int] = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        identity = _proc_identity(int(entry.name))
        try:
            status = (entry / "status").read_text(encoding="utf-8")
            nspid_line = next(line for line in status.splitlines() if line.startswith("NSpid:"))
            namespace_pids = [int(value) for value in nspid_line.split()[1:]]
        except (OSError, StopIteration, ValueError):
            continue
        if (
            identity is not None and identity[0] == start_ticks
            and _cmdline_has_token(identity[1], token) and namespace_pids
            and namespace_pids[-1] == namespace_pid
        ):
            matches.append(int(entry.name))
    return matches[0] if len(matches) == 1 else None


def _poll_pid_identity(
    pid: int, start_ticks: int, token: str, timeout_s: float
) -> str:
    deadline = time.monotonic() + timeout_s
    while True:
        identity = _proc_identity(pid)
        if identity is None:
            return "gone"
        if identity[0] != start_ticks or not _cmdline_has_token(identity[1], token):
            return "pid-reused"
        if time.monotonic() >= deadline:
            return "alive-same-process"
        time.sleep(0.05)


def _read_pidfile_identity(pidfile: Path) -> tuple[str, Optional[int], Optional[int]]:
    if not pidfile.is_file():
        return "pidfile-missing", None, None
    try:
        value = json.loads(pidfile.read_text(encoding="utf-8"))
        inner_pid = int(value["pid"])
        start_ticks = int(value["start_ticks"])
        if inner_pid <= 0 or start_ticks <= 0:
            raise ValueError("non-positive identity")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return "pidfile-invalid", None, None
    return "read", inner_pid, start_ticks


def _run_escape_trial(
    argv: Sequence[str], pidfile: Path, token: str, *,
    sentinel_category: str, timeout_s: float = 1.0,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "attempted": True, "executed": False,
        "argv": [_redact_arg(value) for value in argv], "timed_out": False,
    }
    process: Optional[subprocess.Popen[bytes]] = None
    stdout = b""
    stderr = b""
    host_pid: Optional[int] = None
    start_ticks: Optional[int] = None
    pidfile_status = "pidfile-missing"
    owned_token_pids_before = _token_process_identities(token)
    started = time.monotonic()
    try:
        process = subprocess.Popen(
            list(argv), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, start_new_session=True,
        )
        record["executed"] = True
        while time.monotonic() - started < timeout_s:
            pidfile_status, _inner_pid, start_ticks = _read_pidfile_identity(pidfile)
            if pidfile_status == "read" and start_ticks is not None:
                assert _inner_pid is not None
                host_pid = _find_host_pid(token, start_ticks, _inner_pid)
                if host_pid is not None:
                    break
            if process.poll() is not None:
                break
            time.sleep(0.02)
        remaining = max(0.01, timeout_s - (time.monotonic() - started))
        try:
            stdout, stderr = process.communicate(timeout=remaining)
        except subprocess.TimeoutExpired:
            record["timed_out"] = True
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
        record["rc"] = process.returncode
    except OSError as exc:
        record["error"] = _error(exc)
    if pidfile_status != "read":
        pid_status = pidfile_status
    elif host_pid is None or start_ticks is None:
        pid_status = "identity-unresolved"
    else:
        pid_status = _poll_pid_identity(host_pid, start_ticks, token, 1.0)
    record.update({
        "pidfile_status": pidfile_status,
        "host_pid": host_pid,
        "start_ticks": start_ticks,
        "pid_status": pid_status,
        "owned_token_pids_before": owned_token_pids_before,
        "stdout": _bounded_output(stdout),
        "stderr": _bounded_output(stderr),
    })
    payload = _parse_payload_sentinel(record, sentinel_category)
    process_exit = _process_exit(record)
    record["payload_state"] = payload["state"]
    record["payload_detail"] = payload["detail"]
    record["process_state"] = process_exit["state"]
    record["process_detail"] = process_exit["detail"]
    return record


def _cleanup_exact_process(record: Mapping[str, Any], token: str) -> dict[str, Any]:
    """起動前に存在せず、一意 token を argv に持つ payload だけを清掃する。"""
    pid = record.get("host_pid")
    start_ticks = record.get("start_ticks")
    before_raw = record.get("owned_token_pids_before")
    before = {
        int(candidate): int(ticks)
        for candidate, ticks in before_raw.items()
    } if isinstance(before_raw, Mapping) else {}
    current = _token_process_identities(token)
    candidates = {
        candidate: ticks for candidate, ticks in current.items()
        if before.get(candidate) != ticks
    }
    method = "token-fallback"
    if isinstance(pid, int) and isinstance(start_ticks, int):
        identity = _proc_identity(pid)
        if (
            identity is not None and identity[0] == start_ticks
            and _cmdline_has_token(identity[1], token)
        ):
            candidates[pid] = start_ticks
            method = "resolved-host-pid+token"

    for sig in (signal.SIGTERM, signal.SIGKILL):
        for candidate, ticks in sorted(candidates.items(), reverse=True):
            identity = _proc_identity(candidate)
            if (
                identity is None or identity[0] != ticks
                or not _cmdline_has_token(identity[1], token)
            ):
                continue
            try:
                os.kill(candidate, sig)
            except ProcessLookupError:
                pass
        time.sleep(0.05)
    residual = {
        candidate: ticks for candidate, ticks in _token_process_identities(token).items()
        if before.get(candidate) != ticks
    }
    identity_was_resolved = isinstance(pid, int) and isinstance(start_ticks, int)
    absence_proven = not residual and (
        identity_was_resolved or bool(candidates) or record.get("pid_status") in {"gone", "pid-reused"}
    )
    return {
        "attempted": True,
        "method": method,
        "identity_was_resolved": identity_was_resolved,
        "candidate_pids": sorted(candidates),
        "residual_pids": sorted(residual),
        "succeeded": absence_proven,
        "reason": None if absence_proven else "owned payload absence could not be proven",
    }


_ESCAPE_HELPER = (
    "import json,os,sys,time\n"
    "pidfile,token=sys.argv[1:3]\n"
    "print('T316_SENTINEL|escaped_descendant|REACHED',flush=True)\n"
    "pid=os.fork()\n"
    "if pid==0:\n"
    " os.setsid(); os.close(0); os.close(1); os.close(2)\n"
    " fields=open('/proc/self/stat',encoding='utf-8').read().split()\n"
    " open(pidfile,'x',encoding='utf-8').write(json.dumps({'pid':os.getpid(),'start_ticks':int(fields[21]),'token':token}))\n"
    " while True: time.sleep(1)\n"
    "time.sleep(30)"
)


def _observe_descendant_control(
    profile: SandboxProfile, python: str, scratch: Path, label: str, *, build: bool = False,
    escape_runner: Callable[..., dict[str, Any]] = _run_escape_trial,
) -> dict[str, Any]:
    outside_pidfile = scratch / f"{label}-outside-pid.json"
    inside_pidfile = scratch / f"{label}-inside-pid.json"
    outside_token = f"{label}-outside-{time.monotonic_ns()}"
    inside_token = f"{label}-inside-{time.monotonic_ns()}"
    for path in (outside_pidfile, inside_pidfile):
        _cleanup_marker(path)
    outside = escape_runner(
        [python, "-I", "-B", "-c", _ESCAPE_HELPER, str(outside_pidfile), outside_token],
        outside_pidfile, outside_token, sentinel_category="escaped_descendant",
    )
    inside_argv = profile.argv(
        [python, "-I", "-B", "-c", _ESCAPE_HELPER, str(inside_pidfile), inside_token],
        build=build,
    )
    inside = (
        escape_runner(
            inside_argv, inside_pidfile, inside_token,
            sentinel_category="escaped_descendant",
        )
        if inside_argv is not None else
        {"attempted": False, "executed": False, "pid_status": "identity-unresolved"}
    )
    outside_cleanup = _cleanup_exact_process(outside, outside_token)
    inside_cleanup = _cleanup_exact_process(inside, inside_token)
    for path in (outside_pidfile, inside_pidfile):
        _cleanup_marker(path)
    return {
        "attempted": outside.get("executed") is True and inside.get("attempted") is True,
        "outside_pid_status": outside.get("pid_status"),
        "inside_pid_status": inside.get("pid_status"),
        "outside_payload_state": outside.get("payload_state"),
        "inside_payload_state": inside.get("payload_state"),
        "outside_process_state": outside.get("process_state"),
        "inside_process_state": inside.get("process_state"),
        "outside_cleanup": outside_cleanup,
        "inside_cleanup": inside_cleanup,
        "outside": outside,
        "inside": inside,
    }


def observe_s4(
    profile: SandboxProfile, python: str, scratch: Path, *,
    escape_runner: Callable[..., dict[str, Any]] = _run_escape_trial,
) -> dict[str, Any]:
    return _observe_descendant_control(
        profile, python, scratch, "s4", escape_runner=escape_runner
    )


_THREAT_SOURCE = r'''
#include <arpa/inet.h>
#include <cerrno>
#include <cstdlib>
#include <fcntl.h>
#include <fstream>
#include <iostream>
#include <netinet/in.h>
#include <sstream>
#include <string>
#include <sys/socket.h>
#include <sys/wait.h>
#include <unistd.h>
static const char* errno_name(int value) {
  switch (value) {
    case EACCES: return "EACCES"; case EPERM: return "EPERM";
    case EROFS: return "EROFS"; case ENOENT: return "ENOENT";
    case EEXIST: return "EEXIST"; case ENETUNREACH: return "ENETUNREACH";
    case ENETDOWN: return "ENETDOWN"; case EAFNOSUPPORT: return "EAFNOSUPPORT";
    case EHOSTUNREACH: return "EHOSTUNREACH"; case ECONNREFUSED: return "ECONNREFUSED";
    case ETIMEDOUT: return "ETIMEDOUT"; default: return "OS_ERROR";
  }
}
static void reached(const char* category) {
  std::cout << "T316_SENTINEL|" << category << "|REACHED" << std::endl;
}
static void denied(const char* category, const char* detail) {
  std::cout << "T316_SENTINEL|" << category << "|DENIED|" << detail << std::endl;
}
int main(int argc, char** argv) {
  if (argc < 2) return 64;
  std::string mode(argv[1]);
  if (mode == "system" && argc == 4) {
    if (access("/bin/sh", X_OK) != 0) { denied(argv[3], errno_name(errno)); return 0; }
    std::string command = "/usr/bin/touch " + std::string(argv[2]);
    int status = std::system(command.c_str());
    bool marker_present = access(argv[2], F_OK) == 0;
    if (status == 0 && marker_present) reached(argv[3]);
    else if (marker_present) std::cout << "T316_SENTINEL|" << argv[3] << "|ERROR|SIDE_EFFECT_WITH_FAILURE" << std::endl;
    else if (status == -1) std::cout << "T316_SENTINEL|" << argv[3] << "|ERROR|SYSTEM_CALL_FAILED" << std::endl;
    else if (WIFEXITED(status)) std::cout << "T316_SENTINEL|" << argv[3] << "|ERROR|COMMAND_EXIT_" << WEXITSTATUS(status) << std::endl;
    else std::cout << "T316_SENTINEL|" << argv[3] << "|ERROR|COMMAND_ABNORMAL" << std::endl;
    return 0;
  }
  if (mode == "network" && argc == 5) {
    int fd = socket(AF_INET, SOCK_STREAM, 0); if (fd < 0) { denied(argv[4], errno_name(errno)); return 0; }
    sockaddr_in addr{}; addr.sin_family = AF_INET; addr.sin_port = htons(std::atoi(argv[3]));
    if (inet_pton(AF_INET, argv[2], &addr.sin_addr) != 1) return 3;
    int rc = connect(fd, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)); int saved = errno; close(fd);
    if (rc == 0) reached(argv[4]); else denied(argv[4], errno_name(saved));
    return 0;
  }
  if (mode == "write" && argc == 4) {
    int fd = open(argv[2], O_WRONLY|O_CREAT|O_EXCL, 0600);
    if (fd < 0) denied(argv[3], errno_name(errno));
    else { write(fd, "t316", 4); close(fd); reached(argv[3]); }
    return 0;
  }
  if (mode == "loop" && argc == 4) {
    reached("infinite_loop");
    pid_t pid = fork();
    if (pid == 0) {
      setsid(); close(0); close(1); close(2);
      std::ifstream stat("/proc/self/stat"); std::string field; long long start = 0;
      for (int index = 1; index <= 22 && stat >> field; ++index) if (index == 22) start = std::stoll(field);
      std::ofstream out(argv[2], std::ios::out | std::ios::app);
      out << "{\"pid\":" << getpid() << ",\"start_ticks\":" << start << ",\"token\":\"" << argv[3] << "\"}";
      out.close(); for (;;) {}
    }
    for (;;) {}
  }
  return 65;
}
'''


def _observe_binary_descendant(
    profile: SandboxProfile, binary: Path, scratch: Path, label: str, *, build: bool,
    escape_runner: Callable[..., dict[str, Any]] = _run_escape_trial,
) -> dict[str, Any]:
    outside_pidfile = scratch / f"{label}-outside-pid.json"
    inside_pidfile = scratch / f"{label}-inside-pid.json"
    outside_token = f"{label}-outside-{time.monotonic_ns()}"
    inside_token = f"{label}-inside-{time.monotonic_ns()}"
    for path in (outside_pidfile, inside_pidfile):
        _cleanup_marker(path)
    outside = escape_runner(
        [str(binary), "loop", str(outside_pidfile), outside_token],
        outside_pidfile, outside_token, sentinel_category="infinite_loop",
    )
    inside_argv = profile.argv(
        [str(binary), "loop", str(inside_pidfile), inside_token], build=build
    )
    inside = (
        escape_runner(
            inside_argv, inside_pidfile, inside_token,
            sentinel_category="infinite_loop",
        )
        if inside_argv is not None else
        {"attempted": False, "executed": False, "pid_status": "identity-unresolved"}
    )
    outside_cleanup = _cleanup_exact_process(outside, outside_token)
    inside_cleanup = _cleanup_exact_process(inside, inside_token)
    for path in (outside_pidfile, inside_pidfile):
        _cleanup_marker(path)
    return {
        "attempted": outside.get("executed") is True and inside.get("attempted") is True,
        "outside_pid_status": outside.get("pid_status"),
        "inside_pid_status": inside.get("pid_status"),
        "outside_payload_state": outside.get("payload_state"),
        "inside_payload_state": inside.get("payload_state"),
        "outside_process_state": outside.get("process_state"),
        "inside_process_state": inside.get("process_state"),
        "outside_cleanup": outside_cleanup,
        "inside_cleanup": inside_cleanup,
        "outside": outside,
        "inside": inside,
    }


def observe_s5(
    profile: SandboxProfile, scratch: Path, *,
    escape_runner: Callable[..., dict[str, Any]] = _run_escape_trial,
) -> dict[str, Any]:
    source = scratch / "t316-threats.cc"
    binary = scratch / "t316-threats"
    source.write_text(_THREAT_SOURCE, encoding="utf-8")
    compiler = shutil.which("g++-13") or shutil.which("g++")
    if compiler is None:
        return {
            profile_name: {
                category: {"attempted": False, "reason": "C++ compiler unavailable"}
                for category in S5_CATEGORIES
            } for profile_name in S5_PROFILES
        }
    compile_record = _run_command(
        [compiler, "-std=c++17", "-O2", str(source), "-o", str(binary)], timeout_s=120
    )
    if compile_record.get("rc") != 0 or not binary.is_file():
        return {
            profile_name: {
                category: {
                    "attempted": False, "reason": "threat fixture compilation failed",
                    "compile": compile_record,
                } for category in S5_CATEGORIES
            } for profile_name in S5_PROFILES
        }

    result: dict[str, Any] = {}
    _, direct_ip, network_port = _network_targets()
    fixture = {"source_sha256": _sha256_file(source), "binary_sha256": _sha256_file(binary)}
    for profile_name in S5_PROFILES:
        build = profile_name == "build"
        prefix = f"s5-{profile_name}"
        system_outside = scratch / f"{prefix}-system-outside"
        system_inside = scratch / f"{prefix}-system-inside"
        write_target = Path(os.environ.get("HOME", "/nonexistent")) / f"t316-{prefix}-write-paired"
        for path in (system_outside, system_inside, write_target):
            _cleanup_marker(path)
        system_pair = _observe_system_pair(
            profile, binary, system_outside, system_inside, build=build
        )

        network_pair = _paired_command(
            profile,
            [str(binary), "network", direct_ip, str(network_port), "network"],
            sentinel_category="network", build_profile=build,
        )
        network_pair["target"] = {"ip": direct_ip, "port": network_port}

        write_pair = _observe_write_pair(
            profile,
            [str(binary), "write", str(write_target), "file_write"],
            [str(binary), "write", str(write_target), "file_write"],
            write_target,
            write_target,
            "file_write",
            build=build,
        )

        loop_pair = _observe_binary_descendant(
            profile, binary, scratch, f"{prefix}-loop", build=build,
            escape_runner=escape_runner,
        )
        result[profile_name] = {
            "system_command": system_pair, "network": network_pair,
            "file_write": write_pair, "infinite_loop": loop_pair,
        }
        for observation in result[profile_name].values():
            observation["fixture"] = fixture
            observation["compile"] = compile_record
        for path in (system_outside, system_inside, write_target):
            _cleanup_marker(path)
    return result


def _git_head(path: Path) -> Optional[str]:
    record = _run_command(
        ["git", "--no-replace-objects", "-C", str(path), "rev-parse", "HEAD"], timeout_s=10
    )
    if record.get("rc") != 0:
        return None
    value = record["stdout"]["tail"].strip()
    return value if re.fullmatch(r"[0-9a-f]{40}", value) else None


def _build_step(
    profile: SandboxProfile, argv: Sequence[str], timeout_s: int
) -> dict[str, Any]:
    return profile.run(argv, timeout_s=timeout_s, build=True)


def _cmake_cache_equals(path: Path, key: str, expected: str) -> bool:
    if not path.is_file():
        return False
    prefix = f"{key}:"
    matches = [
        line.split("=", 1)[1]
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
        if line.startswith(prefix) and "=" in line
    ]
    return matches == [expected]


def _git_source_identity(path: Path, expected_head: Optional[str]) -> dict[str, Any]:
    head = _git_head(path)
    status = _run_command(
        ["git", "--no-replace-objects", "-C", str(path), "status", "--porcelain",
         "--untracked-files=all"], timeout_s=15,
    )
    replace_refs = _run_command(
        ["git", "--no-replace-objects", "-C", str(path), "for-each-ref",
         "--format=%(refname)", "refs/replace/"], timeout_s=10,
    )
    tree = _run_command(
        ["git", "--no-replace-objects", "-C", str(path), "rev-parse", "HEAD^{tree}"],
        timeout_s=10,
    )
    tree_sha = tree.get("stdout", {}).get("tail", "").strip()
    clean = status.get("rc") == 0 and not status.get("stdout", {}).get("tail", "").strip()
    no_replace = (
        replace_refs.get("rc") == 0
        and not replace_refs.get("stdout", {}).get("tail", "").strip()
    )
    valid = (
        expected_head is not None and head == expected_head and clean and no_replace
        and re.fullmatch(r"[0-9a-f]{40}", tree_sha) is not None
    )
    return {
        "path": str(path), "expected_head": expected_head, "observed_head": head,
        "tree_sha": tree_sha if re.fullmatch(r"[0-9a-f]{40}", tree_sha) else None,
        "clean_including_untracked": clean, "replace_refs_absent": no_replace,
        "valid": valid, "status": status, "replace_refs": replace_refs,
    }


def _toolchain_contract(profile: SandboxProfile, python: str) -> dict[str, Any]:
    candidates = {
        "python3": python,
        "cmake": shutil.which("cmake"),
        "c_compiler": shutil.which("gcc-13") or shutil.which("gcc"),
        "cxx_compiler": shutil.which("g++-13") or shutil.which("g++"),
    }
    tools: dict[str, Any] = {}
    for name, candidate in candidates.items():
        if candidate is None:
            tools[name] = {"available": False}
            continue
        path = str(Path(candidate).resolve(strict=True))
        version_flag = "--version"
        outside = _run_command([path, version_flag], timeout_s=15)
        inside = profile.run([path, version_flag], timeout_s=15, build=True)
        tools[name] = {
            "available": True, "path": path, "sha256": _sha256_file(Path(path)),
            "outside": outside, "inside": inside,
            "outside_valid": outside.get("rc") == 0,
            "inside_valid": inside.get("rc") == 0,
        }
    return {
        "tools": tools,
        "host_valid": all(item.get("outside_valid") is True for item in tools.values()),
        "sandbox_valid": all(item.get("inside_valid") is True for item in tools.values()),
    }


def _execute_ccbench_build(
    profile: SandboxProfile, source: Path, cache_root: Path,
    dependency_root: Path, pins: Mapping[str, str], scratch: Path,
    policy: Mapping[str, Any], deadline_ns: int, *, inside: bool,
) -> dict[str, Any]:
    mode = "inside" if inside else "outside"
    root = scratch / f"s6-{mode}"
    prefix = root / "install"
    gflags_build = root / "gflags-build"
    glog_build = root / "glog-build"
    ccbench_build = root / "ccbench-build-trace0"
    for path in (root, prefix, gflags_build, glog_build, ccbench_build):
        path.mkdir()
    compiler_c = str(Path(shutil.which("gcc-13") or shutil.which("gcc") or "").resolve(strict=True))
    compiler_cxx = str(Path(shutil.which("g++-13") or shutil.which("g++") or "").resolve(strict=True))
    cmake = str(Path(shutil.which("cmake") or "").resolve(strict=True))
    commands: list[tuple[str, list[str], int]] = [
        ("gflags-configure", [cmake, "-S", str(dependency_root / "gflags"), "-B", str(gflags_build), "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_SHARED_LIBS=OFF", "-DCMAKE_POSITION_INDEPENDENT_CODE=ON", "-DREGISTER_INSTALL_PREFIX=OFF", f"-DCMAKE_INSTALL_PREFIX={prefix}"], 180),
        ("gflags-build", [cmake, "--build", str(gflags_build), "-j", "48"], 300),
        ("gflags-install", [cmake, "--install", str(gflags_build)], 120),
        ("glog-configure", [cmake, "-S", str(dependency_root / "glog"), "-B", str(glog_build), "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_SHARED_LIBS=OFF", "-DCMAKE_POSITION_INDEPENDENT_CODE=ON", "-DWITH_GTEST=OFF", "-DBUILD_TESTING=OFF", "-DWITH_UNWIND=OFF", f"-DCMAKE_PREFIX_PATH={prefix}", f"-DCMAKE_INSTALL_PREFIX={prefix}"], 180),
        ("glog-build", [cmake, "--build", str(glog_build), "-j", "48"], 300),
        ("glog-install", [cmake, "--install", str(glog_build)], 120),
    ]
    configure = [
        cmake, "-S", str(source), "-B", str(ccbench_build),
        "-DCMAKE_BUILD_TYPE=Release", "-DENABLE_SANITIZER=OFF", "-DCCBENCH_TRACE=0",
        "-DCCBENCH_BACK_OFF=0", "-DCCBENCH_BACKOFF_FIXED=-1",
        "-DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1", "-DCCBENCH_NO_WAIT_OF_TICTOC=0",
        "-DCCBENCH_WAL=0", "-DCCBENCH_CCACHE=OFF", "-DCCBENCH_ADD_ANALYSIS=0",
        "-DCMAKE_C_COMPILER_LAUNCHER=", "-DCMAKE_CXX_COMPILER_LAUNCHER=",
        "-DRULE_LAUNCH_COMPILE=", "-DCMAKE_TOOLCHAIN_FILE=", "-DCMAKE_CXX_FLAGS=",
        f"-DCMAKE_PREFIX_PATH={prefix}",
        f"-DFETCHCONTENT_SOURCE_DIR_MASSTREE={cache_root / 'masstree'}",
        f"-DFETCHCONTENT_SOURCE_DIR_MIMALLOC={cache_root / 'mimalloc'}",
        f"-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST={cache_root / 'googletest'}",
        f"-DIZANAGI_GFLAGS_SRC_HEAD={pins['gflags']}",
        f"-DIZANAGI_GLOG_SRC_HEAD={pins['glog']}",
        f"-DCMAKE_C_COMPILER={compiler_c}", f"-DCMAKE_CXX_COMPILER={compiler_cxx}",
    ]
    steps: list[dict[str, Any]] = []
    condition_gate_family: tuple[
        condition_meaning_gate.ConditionArmRecord,
        condition_meaning_gate.ConditionArmRecord,
        condition_meaning_gate.ConditionFamilyAdmission,
    ] | tuple[()] = ()
    failure_stage: Optional[str] = None
    for label, argv, cap in commands:
        remaining_s = int((deadline_ns - time.monotonic_ns()) / 1_000_000_000)
        if remaining_s < 30:
            failure_stage = "walltime"
            break
        record = (
            _build_step(profile, argv, timeout_s=min(cap, remaining_s))
            if inside else _run_command(argv, timeout_s=min(cap, remaining_s))
        )
        steps.append({"label": label, "command": record})
        if record.get("rc") != 0:
            failure_stage = label
            break
    if failure_stage is None:
        stock_copy = root / "condition-gate-stock"
        shutil.copytree(source, stock_copy, symlinks=True)
        condition_gate_family = _require_condition_gate(
            source,
            stock_root=stock_copy,
            configure_args=configure[5:],
            cxx=compiler_cxx,
            cmake=cmake,
        )
        commands.extend((
            ("ccbench-configure", configure, 300),
            ("ccbench-build", [cmake, "--build", str(ccbench_build), "--target",
             "ycsb_silo.exe", "-j", "48"], int(policy["stage_budgets_s"]["ccbench_build_cap_s"])),
        ))
        for label, argv, cap in commands[-2:]:
            remaining_s = int(
                (deadline_ns - time.monotonic_ns()) / 1_000_000_000
            )
            if remaining_s < 30:
                failure_stage = "walltime"
                break
            record = (
                profile.run(argv, timeout_s=min(cap, remaining_s), build=True)
                if inside else _run_command(argv, timeout_s=min(cap, remaining_s))
            )
            steps.append({"label": label, "command": record})
            if record.get("rc") != 0:
                failure_stage = label
                break
    binary = ccbench_build / "cc/silo/ycsb_silo.exe"
    cache = ccbench_build / "CMakeCache.txt"
    trace_disabled = _cmake_cache_equals(cache, "CCBENCH_TRACE", "0")
    return {
        "mode": mode, "success": failure_stage is None and binary.is_file() and trace_disabled,
        "failure_stage": failure_stage, "trace_disabled": trace_disabled, "steps": steps,
        "condition_gates": (
            _condition_gate_receipt_summary(condition_gate_family)
            if condition_gate_family else []
        ),
        "_condition_gate_family": condition_gate_family,
        "binary": str(binary), "binary_sha256": _sha256_file(binary) if binary.is_file() else None,
        "cmake_cache_sha256": _sha256_file(cache) if cache.is_file() else None,
    }


def _require_condition_gate(
    source: Path,
    *,
    stock_root: Path,
    configure_args: Sequence[str],
    cxx: str,
    cmake: str,
) -> tuple[
    condition_meaning_gate.ConditionArmRecord,
    condition_meaning_gate.ConditionArmRecord,
    condition_meaning_gate.ConditionFamilyAdmission,
]:
    filtered_args = tuple(
        argument for argument in configure_args
        if argument != "-DCCBENCH_BACKOFF_FIXED=-1"
    )
    captured = condition_meaning_gate.capture_define_inputs(
        source, stock_root=stock_root, configure_args=filtered_args,
    )
    request = condition_meaning_gate.make_define_request(
        driver_id="tools.pegasus.probes.t316_sandbox_backend_probe",
        macro="BACKOFF_FIXED",
        requested_value=-1,
        default_value=None,
        stock_comparison=True,
    )
    supply = condition_meaning_gate.evaluate_define_supply_effectuation(
        captured, request=request, cxx=cxx, cmake=cmake,
    )
    meaning = condition_meaning_gate.evaluate_define_runtime_meaning(
        captured, request=request, declaration=None, cxx=cxx,
    )
    admission = condition_meaning_gate.require_condition_gate_family(
        [supply], [meaning], use_class="raw-measurement",
    )
    if not admission.admitted:
        rejection = RuntimeError(
            "condition gate rejected t316 CCBench build: "
            f"supply={supply.terminal_status}/{supply.reason_code}, "
            f"meaning={meaning.terminal_status}/{meaning.reason_code}"
        )
        try:
            for arm, record in (("supply", supply), ("meaning", meaning)):
                detail = record.evidence.get("detail")
                print(
                    f"condition gate rejected t316 CCBench build: {arm} detail="
                    f"{detail if detail else '<no detail>'}",
                    file=sys.stderr,
                )
        except Exception as diagnostic_error:
            # Preserve the rejection and retain the output failure for traceback audit.
            # BaseException control signals must still propagate.
            raise rejection from diagnostic_error
        raise rejection
    return supply, meaning, admission


def observe_s6(
    profile: SandboxProfile,
    repo_root: Path,
    scratch: Path,
    policy: Mapping[str, Any],
    deadline_ns: int,
) -> dict[str, Any]:
    minimum_ns = int(policy["stage_budgets_s"]["s6_minimum_remaining_s"]) * 1_000_000_000
    if deadline_ns - time.monotonic_ns() < minimum_ns:
        return {"attempted": False, "reason": "S6 walltime reserve reached"}
    cache_root = Path(os.environ["IZANAGI_PEGASUS_THIRDPARTY_CACHE"]).resolve(strict=True)
    dependency_root = Path(os.environ["IZANAGI_T139_DEPENDENCY_SOURCE_ROOT"]).resolve(strict=True)
    shared_policy = json.loads((repo_root / "tools/pegasus/policy.json").read_text(encoding="utf-8"))
    pins = shared_policy["silo_ladder_rung1"]["dependency_pins"]
    third_items = shared_policy["silo_ladder_rung1"]["third_party_sources"]
    source_heads = {
        "gflags": _git_head(dependency_root / "gflags"),
        "glog": _git_head(dependency_root / "glog"),
        **{item["source_name"]: _git_head(cache_root / item["source_name"]) for item in third_items},
    }
    expected_heads = {"gflags": pins["gflags"], "glog": pins["glog"], **{item["source_name"]: item["pin"] for item in third_items}}
    gitlink_record = _run_command(
        ["git", "--no-replace-objects", "-C", str(repo_root), "ls-tree", "HEAD", "external/ccbench"],
        timeout_s=10,
    )
    gitlink_fields = gitlink_record["stdout"]["tail"].strip().split()
    expected_ccbench_head = gitlink_fields[2] if len(gitlink_fields) >= 4 else None
    observed_ccbench_head = _git_head(repo_root / "external/ccbench")
    source_heads["ccbench"] = observed_ccbench_head
    expected_heads["ccbench"] = expected_ccbench_head
    if source_heads != expected_heads:
        return {
            "attempted": True,
            "success": False,
            "trace_disabled": False,
            "failure_stage": "dependency-pins",
            "source_heads": source_heads,
            "expected_heads": expected_heads,
        }

    source = repo_root / "external/ccbench"
    python = str(Path(sys.executable).resolve(strict=True))
    toolchain = _toolchain_contract(profile, python)
    if toolchain["host_valid"] is not True:
        return {
            "attempted": True,
            "outside_success": False, "inside_success": False,
            "trace_disabled": False,
            "failure_stage": "toolchain-unavailable", "toolchain": toolchain,
            "source_identity_valid": False,
        }

    identities = {
        name: _git_source_identity(
            (dependency_root / name) if name in {"gflags", "glog"}
            else (source if name == "ccbench" else cache_root / name),
            expected_heads[name],
        ) for name in expected_heads
    }
    source_identity_valid = all(item["valid"] for item in identities.values())
    if not source_identity_valid:
        return {
            "attempted": True, "outside_success": False, "inside_success": False,
            "trace_disabled": False, "failure_stage": "source-identity",
            "source_identity_valid": False, "source_identities": identities,
            "toolchain": toolchain,
        }
    outside = _execute_ccbench_build(
        profile, source, cache_root, dependency_root, pins, scratch, policy,
        deadline_ns, inside=False,
    )
    inside = (
        _execute_ccbench_build(
            profile, source, cache_root, dependency_root, pins, scratch, policy,
            deadline_ns, inside=True,
        ) if outside["success"] else {"success": False, "failure_stage": "outside-control"}
    )
    condition_gate_family = outside.pop("_condition_gate_family", ())
    inside.pop("_condition_gate_family", None)
    return {
        "attempted": True, "outside_success": outside["success"],
        "inside_success": inside["success"], "success": inside["success"],
        "failure_stage": (
            "walltime" if "walltime" in {
                outside.get("failure_stage"), inside.get("failure_stage")
            } else inside.get("failure_stage") or outside.get("failure_stage")
        ),
        "trace_disabled": outside.get("trace_disabled") is True
        and inside.get("trace_disabled") is True,
        "condition_gates": outside.get("condition_gates", []),
        "_condition_gate_family": condition_gate_family,
        "source_identity_valid": source_identity_valid,
        "source_identities": identities, "toolchain": toolchain,
        "outside_build": outside, "inside_build": inside,
        "binary": inside.get("binary"), "binary_sha256": inside.get("binary_sha256"),
    }


def _resolve_perf(repo_root: Path) -> Optional[str]:
    policy = json.loads((repo_root / "tools/pegasus/policy.json").read_text(encoding="utf-8"))
    for candidate in policy["perf_candidates"]:
        if Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    return shutil.which("perf")


def _measurement_environment() -> dict[str, Any]:
    return {
        "monotonic_ns": time.monotonic_ns(), "load_average": list(os.getloadavg()),
        **_process_tenancy_evidence(),
        "nproc": os.cpu_count(), "cpu_affinity": sorted(os.sched_getaffinity(0)),
    }


def _exclusive_snapshot_valid(snapshot: Mapping[str, Any], max_load_per_cpu: float) -> bool:
    users = snapshot.get("other_non_system_user_processes")
    load = snapshot.get("load_average")
    nproc = snapshot.get("nproc")
    return (
        isinstance(users, Mapping) and users.get("present") is False
        and isinstance(load, list) and bool(load)
        and isinstance(load[0], (int, float)) and isinstance(nproc, int) and nproc > 0
        and load[0] <= max_load_per_cpu * nproc
    )


def _perf_output_valid(record: Mapping[str, Any], expected_events: Sequence[str]) -> bool:
    stderr = record.get("stderr")
    tail = str(stderr.get("tail", "")) if isinstance(stderr, Mapping) else ""
    lowered = tail.lower()
    return (
        record.get("rc") == 0
        and all(event in tail for event in expected_events)
        and "<not supported>" not in lowered and "<not counted>" not in lowered
    )


def observe_s7(
    profile: SandboxProfile,
    repo_root: Path,
    s6: Mapping[str, Any],
    policy: Mapping[str, Any],
    deadline_ns: int,
) -> dict[str, Any]:
    minimum_ns = int(policy["stage_budgets_s"]["s7_minimum_remaining_s"]) * 1_000_000_000
    if deadline_ns - time.monotonic_ns() < minimum_ns:
        return {"attempted": False, "blocked_reason": "S7 walltime reserve reached"}
    if s6.get("success") is not True:
        return {"attempted": False, "blocked_reason": "S6 trace-disabled build unavailable"}
    perf = _resolve_perf(repo_root)
    numactl = shutil.which("numactl")
    if perf is None or numactl is None:
        missing = [name for name, value in (("numactl", numactl), ("perf", perf)) if value is None]
        return {"attempted": False, "blocked_reason": "measurement tool unavailable", "missing_tools": missing}
    binary = Path(str(s6["binary"])).resolve(strict=True)
    binary_sha = _sha256_file(binary)
    workload = [
        "-ycsb_rmw=true", "-ycsb_zipf_skew=0.9", "-ycsb_tuple_num=10000",
        "-ycsb_max_ope=10", "-thread_num=48", "-extime=3",
    ]
    expected_events = ("cycles", "instructions", "LLC-loads", "LLC-load-misses")
    perf_prefix = [
        numactl, "--physcpubind=0-47", "--membind=0", perf, "stat", "-x,",
        "-e", ",".join(expected_events), "--",
    ]
    outside_argv = [*perf_prefix, str(binary), *workload]
    inside_payload = profile.argv([str(binary), *workload])
    if inside_payload is None:
        return {"attempted": False, "blocked_reason": "bwrap unavailable"}
    inside_argv = [*perf_prefix, *inside_payload]
    run_cap = int(policy["stage_budgets_s"]["performance_run_cap_s"])
    warmup_cap = int(policy["performance_contract"]["warmup_cap_s"])
    outside_warmup = _run_command(
        [numactl, "--physcpubind=0-47", "--membind=0", str(binary), *workload],
        timeout_s=warmup_cap, monitor_threads=True,
    )
    inside_warmup = _run_command(
        [numactl, "--physcpubind=0-47", "--membind=0", *inside_payload],
        timeout_s=warmup_cap, monitor_threads=True,
    )
    repetitions = int(policy["performance_contract"]["repetitions_per_side"])
    max_load_per_cpu = float(policy["performance_contract"]["max_load_per_cpu"])
    runs: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    for pair_index in range(repetitions):
        order = ("outside", "inside") if pair_index % 2 == 0 else ("inside", "outside")
        pair_records: dict[str, Any] = {}
        for mode in order:
            if deadline_ns - time.monotonic_ns() < (run_cap + 10) * 1_000_000_000:
                return {
                    "attempted": bool(runs), "blocked_reason": "S7 deadline reached mid-sample",
                    "warmup": {"outside": outside_warmup, "inside": inside_warmup},
                    "runs": runs,
                }
            before = _measurement_environment()
            command = outside_argv if mode == "outside" else inside_argv
            command_record = _run_command(command, timeout_s=run_cap, monitor_threads=True)
            after = _measurement_environment()
            run_record = {
                "pair_index": pair_index, "order_index": len(runs), "mode": mode,
                "environment_before": before, "command": command_record,
                "environment_after": after,
                "perf_output_valid": _perf_output_valid(command_record, expected_events),
                "effective_thread_count_valid": (
                    isinstance(command_record.get("max_single_process_threads"), int)
                    and command_record["max_single_process_threads"] >= 48
                ),
                "exclusivity_valid": _exclusive_snapshot_valid(before, max_load_per_cpu)
                and _exclusive_snapshot_valid(after, max_load_per_cpu),
            }
            runs.append(run_record)
            pair_records[mode] = run_record
        outside_elapsed = pair_records["outside"]["command"].get("elapsed_ns")
        inside_elapsed = pair_records["inside"]["command"].get("elapsed_ns")
        ratio = (
            inside_elapsed / outside_elapsed
            if pair_records["outside"]["command"].get("rc") == 0
            and pair_records["inside"]["command"].get("rc") == 0
            and isinstance(outside_elapsed, int) and outside_elapsed > 0
            and isinstance(inside_elapsed, int) else None
        )
        pairs.append({"pair_index": pair_index, "order": list(order), "elapsed_overhead_ratio": ratio})
    ratios = [item["elapsed_overhead_ratio"] for item in pairs if item["elapsed_overhead_ratio"] is not None]
    ratio_median = statistics.median(ratios) if len(ratios) == repetitions else None
    ratio_mad = (
        statistics.median(abs(value - ratio_median) for value in ratios)
        if ratio_median is not None else None
    )
    return {
        "attempted": len(runs) == repetitions * 2,
        "outside_success": all(
            item["command"].get("rc") == 0 for item in runs if item["mode"] == "outside"
        ),
        "inside_success": all(
            item["command"].get("rc") == 0 for item in runs if item["mode"] == "inside"
        ),
        "same_binary": binary_sha == s6.get("binary_sha256"),
        "trace_disabled": s6.get("trace_disabled") is True,
        "elapsed_overhead_ratio_median": ratio_median,
        "elapsed_overhead_ratio_mad": ratio_mad,
        "elapsed_overhead_ratio_samples": ratios,
        "metric_semantics": "sandbox/non-sandbox wall elapsed ratio only; not TPS, CC throughput, or floor recalibration",
        "requested_thread_count": 48,
        "effective_thread_count_valid": all(item["effective_thread_count_valid"] for item in runs),
        "perf_output_valid": all(item["perf_output_valid"] for item in runs),
        "exclusivity_valid": all(item["exclusivity_valid"] for item in runs),
        "exclusivity_criteria": {
            "co_tenant_uid_minimum": 1000,
            "system_uid_range_excluded": "uid < 1000",
            "own_uid_excluded": True,
            "max_load_per_cpu": max_load_per_cpu,
        },
        "warmup_valid": outside_warmup.get("rc") == 0 and inside_warmup.get("rc") == 0,
        "warmup_separate_from_samples": True,
        "warmup": {"outside": outside_warmup, "inside": inside_warmup},
        "pairs": pairs, "runs": runs,
        "binary": str(binary),
        "binary_sha256": binary_sha,
    }


def _blocked_observation(reason: str, exc: Optional[BaseException] = None) -> dict[str, Any]:
    result: dict[str, Any] = {"attempted": False, "reason": reason}
    if exc is not None:
        result["error"] = _error(exc)
    return result


def _payload_cleanup_integrity(observations: Mapping[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    s4 = observations.get("S4")
    if isinstance(s4, Mapping):
        for side in ("outside", "inside"):
            cleanup = s4.get(f"{side}_cleanup")
            if isinstance(cleanup, Mapping):
                checks.append({"stage": "S4", "side": side, **dict(cleanup)})
    s5 = observations.get("S5")
    if isinstance(s5, Mapping):
        for profile_name in S5_PROFILES:
            profile = s5.get(profile_name)
            loop = profile.get("infinite_loop") if isinstance(profile, Mapping) else None
            if not isinstance(loop, Mapping):
                continue
            for side in ("outside", "inside"):
                cleanup = loop.get(f"{side}_cleanup")
                if isinstance(cleanup, Mapping):
                    checks.append({
                        "stage": "S5", "profile": profile_name, "side": side,
                        **dict(cleanup),
                    })
    failures = [item for item in checks if item.get("succeeded") is not True]
    return {
        "checked_cleanup_count": len(checks),
        "valid": not failures,
        "failures": failures,
    }


def _load_policy(repo_root: Path) -> Mapping[str, Any]:
    path = repo_root / "tools/pegasus/policies/t316_sandbox_backend_v1.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping) or value.get("schema_version") != POLICY_SCHEMA_VERSION:
        raise ValueError("invalid T316 policy schema")
    return value


def _git_metadata(repo_root: Path) -> dict[str, Any]:
    head = _run_command(["git", "-C", str(repo_root), "rev-parse", "HEAD"], timeout_s=10)
    status = _run_command(
        ["git", "-C", str(repo_root), "status", "--porcelain", "--untracked-files=all"], timeout_s=15
    )
    return {"head": head, "status": status}


_RUNTIME_PBS_RELATIVE_PATH = "tools/pegasus/probes/t316_sandbox_backend_probe.pbs"
_BOUND_RELATIVE_PATHS = (
    "orchestrator/campaign/condition_meaning_gate.py",
    "tools/pegasus/probes/t316_sandbox_backend_probe.py",
    _RUNTIME_PBS_RELATIVE_PATH,
    "tools/pegasus/policies/t316_sandbox_backend_v1.json",
    "tools/pegasus/policy.json",
)


def _execution_binding(repo_root: Path) -> dict[str, Any]:
    job_id = os.environ.get("PBS_JOBID", "")
    expected_commit = os.environ.get("IZANAGI_T316_EXPECTED_COMMIT", "")
    expected_root_raw = os.environ.get("IZANAGI_T316_EXPECTED_WORKTREE_ROOT", "")
    nodefile_raw = os.environ.get("PBS_NODEFILE", "")
    runtime_pbs_raw = os.environ.get("IZANAGI_T316_RUNTIME_PBS", "")
    if not _JOB_ID_RE.fullmatch(job_id):
        raise ValueError("PBS_JOBID is missing or malformed")
    if re.fullmatch(r"[0-9a-f]{40}", expected_commit) is None:
        raise ValueError("expected commit is missing or malformed")
    expected_root = Path(expected_root_raw).resolve(strict=True)
    if expected_root != repo_root:
        raise ValueError("expected worktree root mismatch")
    hostname = socket.gethostname()
    short_hostname = hostname.split(".", 1)[0]
    if re.fullmatch(r"pegasus[0-9]+", short_hostname):
        raise ValueError("login-node execution is forbidden")
    nodefile = Path(nodefile_raw).resolve(strict=True)
    if not nodefile.is_file():
        raise ValueError("PBS_NODEFILE is not a file")
    node_entries = [line.strip() for line in nodefile.read_text(encoding="utf-8").splitlines() if line.strip()]
    node_shorts = {entry.split(".", 1)[0] for entry in node_entries}
    if not node_entries or short_hostname not in node_shorts:
        raise ValueError("execution host is absent from PBS_NODEFILE")
    head_record = _run_command(
        ["git", "--no-replace-objects", "-C", str(repo_root), "rev-parse", "HEAD"],
        timeout_s=10,
    )
    observed_head = head_record.get("stdout", {}).get("tail", "").strip()
    if head_record.get("rc") != 0 or observed_head != expected_commit:
        raise ValueError("expected commit mismatch")
    dirty = _run_command(
        ["git", "--no-replace-objects", "-C", str(repo_root), "status", "--porcelain",
         "--untracked-files=all", "--", *_BOUND_RELATIVE_PATHS], timeout_s=15,
    )
    if dirty.get("rc") != 0 or dirty.get("stdout", {}).get("tail", "").strip():
        raise ValueError("bound probe paths are dirty")
    runtime_pbs = Path(runtime_pbs_raw).resolve(strict=True)
    repo_pbs = repo_root / _RUNTIME_PBS_RELATIVE_PATH
    if _sha256_file(runtime_pbs) != _sha256_file(repo_pbs):
        raise ValueError("runtime PBS bytes differ from worktree PBS bytes")
    runtime_hashes = {
        relative: _sha256_file(repo_root / relative) for relative in _BOUND_RELATIVE_PATHS
    }
    runtime_hashes["runtime_pbs_spool"] = _sha256_file(runtime_pbs)
    return {
        "PBS_JOBID": job_id, "hostname": hostname,
        "PBS_NODEFILE": str(nodefile), "PBS_NODEFILE_entries": node_entries,
        "expected_commit": expected_commit, "observed_commit": observed_head,
        "expected_worktree_root": str(expected_root), "observed_worktree_root": str(repo_root),
        "runtime_sha256": runtime_hashes,
        "login_node_rejected": True, "bound_paths_clean": True,
    }


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _link_noreplace(source: Path, destination: Path) -> None:
    """同一 filesystem 内で hard link により create-only publish する。"""
    os.link(source, destination)
    try:
        os.unlink(source)
    except BaseException:
        # link 成功後に temp の除去だけが失敗した場合も canonical 名を残さない。
        try:
            os.unlink(destination)
        except FileNotFoundError:
            pass
        raise


def _completion_predicate() -> dict[str, Any]:
    """Consumer が完成測定とみなしてよい唯一の機械可読述語。"""
    return {
        "and": [
            {"path_exists": "COMPLETED"},
            {"json_parseable": "receipt.json"},
            {"equals": [{"json_pointer": "/state"}, "complete"]},
        ]
    }


class ReceiptPublisher:
    """部分状態と canonical 完成 receipt を別 lifecycle で永続化する。"""

    def __init__(self, repo_root: Path, job_id: str) -> None:
        parent = _ensure_output_parent(repo_root)
        self.job_dir = parent / job_id
        self.job_dir.mkdir(mode=0o700, exist_ok=False)
        _fsync_directory(parent)
        self._verify_publish_mechanism()

    def _write_temp(self, name: str, value: Mapping[str, Any]) -> Path:
        temporary = self.job_dir / f".{name}.{os.getpid()}.{time.monotonic_ns()}.tmp"
        with temporary.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        return temporary

    def _write_bytes_temp(self, name: str, value: bytes) -> Path:
        temporary = self.job_dir / f".{name}.{os.getpid()}.{time.monotonic_ns()}.tmp"
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
        try:
            try:
                offset = 0
                while offset < len(value):
                    written = os.write(descriptor, value[offset:])
                    if written <= 0:
                        raise OSError(errno.EIO, "short write while publishing marker")
                    offset += written
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        except BaseException:
            _cleanup_marker(temporary)
            raise
        return temporary

    def persist_partial(self, value: Mapping[str, Any]) -> Path:
        temporary = self._write_temp("PARTIAL.json", value)
        path = self.job_dir / "PARTIAL.json"
        os.replace(temporary, path)
        _fsync_directory(self.job_dir)
        return path

    def _verify_publish_mechanism(self) -> None:
        """実 receipt と同じ directory で publish を起動直後に実測する。"""
        payload = {"sentinel": "t316-create-only-publish-preflight"}
        temporary = self._write_temp("PUBLISH-PREFLIGHT", payload)
        published = self.job_dir / ".PUBLISH-PREFLIGHT.sentinel"
        try:
            _link_noreplace(temporary, published)
            _fsync_directory(self.job_dir)
            if temporary.exists() or json.loads(published.read_text(encoding="utf-8")) != payload:
                raise OSError(errno.EIO, "publish preflight verification failed")
        finally:
            _cleanup_marker(temporary)
            _cleanup_marker(published)
            _fsync_directory(self.job_dir)

    def publish_final(self, receipt: Mapping[str, Any]) -> Path:
        if receipt.get("state") != "complete":
            raise ValueError("final receipt must carry state=complete")
        path = self.job_dir / "receipt.json"
        temporary = self._write_temp("receipt.json", receipt)
        try:
            _link_noreplace(temporary, path)
        except BaseException:
            _cleanup_marker(temporary)
            raise
        _fsync_directory(self.job_dir)
        # 完成 receipt の bytes が永続化した後は partial lifecycle を閉じる。
        # marker より先に削除するため、COMPLETED が存在する状態では残らない。
        try:
            (self.job_dir / "PARTIAL.json").unlink()
        except FileNotFoundError:
            pass
        _fsync_directory(self.job_dir)
        marker = self.job_dir / "COMPLETED"
        marker_payload = (_sha256_file(path) + "\n").encode("ascii")
        marker_temporary = self._write_bytes_temp("COMPLETED", marker_payload)
        try:
            _link_noreplace(marker_temporary, marker)
        except BaseException:
            _cleanup_marker(marker_temporary)
            raise
        _fsync_directory(self.job_dir)
        return path


def run_probe(
    repo_root: Path, scratch_root: Path, *,
    publisher: Optional[ReceiptPublisher] = None,
    execution_binding: Optional[Mapping[str, Any]] = None,
    observer_runner: Optional[
        Callable[[str, Callable[[], Mapping[str, Any]]], Mapping[str, Any]]
    ] = None,
    command_runner: Callable[..., dict[str, Any]] = _run_command,
    escape_runner: Callable[..., dict[str, Any]] = _run_escape_trial,
) -> tuple[int, dict[str, Any]]:
    job_id = os.environ.get("PBS_JOBID", "")
    if not _JOB_ID_RE.fullmatch(job_id):
        raise ValueError("PBS_JOBID is missing or malformed")
    binding = dict(execution_binding or _execution_binding(repo_root))
    policy = _load_policy(repo_root)
    started_epoch = int(time.time())
    started_ns = time.monotonic_ns()
    deadline_ns = started_ns + int(policy["probe_deadline_s"]) * 1_000_000_000
    scratch = Path(tempfile.mkdtemp(prefix=f"t316-{job_id.replace(':', '_')}-", dir=scratch_root))
    (scratch / "home").mkdir()
    (scratch / "tmp").mkdir()
    (scratch / "empty-tmp").mkdir(mode=0o555)
    python_shim = scratch / "python-shim"
    python_shim.mkdir()
    readonly_roots = [
        Path(os.environ["IZANAGI_PEGASUS_THIRDPARTY_CACHE"]),
        Path(os.environ["IZANAGI_T139_DEPENDENCY_SOURCE_ROOT"]),
    ]
    python = str(Path(sys.executable).resolve(strict=True))
    (python_shim / "python3").symlink_to(python)
    observations: dict[str, Any] = {}
    verdicts: list[StageVerdict] = []

    def observe(stage: str, observer: Callable[[], Mapping[str, Any]]) -> Mapping[str, Any]:
        return observer_runner(stage, observer) if observer_runner is not None else observer()

    def persist(stage: str) -> None:
        if publisher is None:
            return
        publisher.persist_partial({
            "schema_version": SCHEMA_VERSION, "state": "partial",
            "last_completed_stage": stage, "measurement_id": job_id,
            "execution_binding": binding, "policy": policy,
            "observations": observations,
            "stage_verdicts": [item.as_dict() for item in verdicts],
            "updated_epoch": int(time.time()),
        })
    try:
        try:
            observations["S1"] = dict(observe("S1", observe_s1))
        except Exception as exc:
            observations["S1"] = _blocked_observation("S1 raised", exc)
        verdicts.append(verdict_s1(observations["S1"]))
        persist("S1")

        bwrap = None
        tools = observations["S1"].get("tools")
        if isinstance(tools, Mapping) and isinstance(tools.get("bwrap"), Mapping):
            bwrap = tools["bwrap"].get("path")
        profile = SandboxProfile(
            bwrap, repo_root, scratch, readonly_roots, runner=command_runner
        )

        for stage, observer, judge in (
            ("S2", lambda: observe_s2(profile, python), verdict_s2),
            ("S3", lambda: observe_s3(profile, python, repo_root, scratch), verdict_s3),
            (
                "S4",
                lambda: observe_s4(
                    profile, python, scratch, escape_runner=escape_runner
                ),
                verdict_s4,
            ),
            (
                "S5",
                lambda: observe_s5(profile, scratch, escape_runner=escape_runner),
                verdict_s5,
            ),
        ):
            try:
                observations[stage] = dict(observe(stage, observer))
            except Exception as exc:
                observations[stage] = _blocked_observation(f"{stage} raised", exc)
            verdicts.append(judge(observations[stage]))
            persist(stage)

        try:
            observations["S6"] = dict(observe(
                "S6", lambda: observe_s6(profile, repo_root, scratch, policy, deadline_ns)
            ))
        except Exception as exc:
            observations["S6"] = _blocked_observation("S6 raised", exc)
        verdicts.append(verdict_s6(observations["S6"]))
        observations["S6"].pop("_condition_gate_family", None)
        persist("S6")

        cleanup_integrity = _payload_cleanup_integrity(observations)
        if cleanup_integrity["valid"] is not True:
            observations["S7"] = {
                "attempted": True,
                "cleanup_integrity_valid": False,
                "cleanup_integrity": cleanup_integrity,
            }
        else:
            try:
                observations["S7"] = dict(observe(
                    "S7", lambda: observe_s7(
                        profile, repo_root, observations["S6"], policy, deadline_ns
                    )
                ))
                observations["S7"]["cleanup_integrity_valid"] = True
                observations["S7"]["cleanup_integrity"] = cleanup_integrity
            except Exception as exc:
                observations["S7"] = _blocked_observation("S7 raised", exc)
        verdicts.append(verdict_s7(observations["S7"]))
        persist("S7")

        overall = aggregate_verdicts(verdicts)
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "state": "complete",
            "completion_predicate": _completion_predicate(),
            "measurement_id": job_id,
            "PBS_JOBID": job_id,
            "started_epoch": started_epoch,
            "finished_epoch": int(time.time()),
            "elapsed_ns": time.monotonic_ns() - started_ns,
            "hostname": socket.gethostname(),
            "repo_root": str(repo_root),
            "policy": policy,
            "execution_binding": binding,
            "profile": {
                "declared_configuration_backend": "bwrap",
                "declared_configuration_runtime_hides_bin_shell": True,
                "declared_configuration_network_namespace": "unshared",
                "declared_configuration_source_mount": "read-only",
                "declared_configuration_scratch_mount": "read-write",
                "declared_configuration_environment": "clearenv + explicit minimum",
            },
            "observations": observations,
            "stage_verdicts": [item.as_dict() for item in verdicts],
            "overall_verdict": overall.as_dict(),
            "limitations": [
                "single PBS allocation sample; do not generalize to every gen_S node",
                "S7 is a repeated elapsed-overhead sample for one trace-disabled stock binary, not TPS or an absolute CC performance claim",
                "missing external positive controls make their category inconclusive rather than proving containment",
                "condition gate receipt entries preserve live-validated digests and conclusions, not a reusable production-issuer capability",
            ],
            "r3_1_coverage": _r3_1_coverage(verdicts),
        }
        return (0 if overall.verdict == "go" else 3), receipt
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def _ensure_output_parent(repo_root: Path) -> Path:
    current = repo_root
    for component in ("output", "env", "pegasus", "t316-sandbox-backend"):
        current /= component
        if current.is_symlink():
            raise ValueError(f"receipt path component is a symlink: {current}")
        current.mkdir(exist_ok=True)
        if not current.is_dir() or current.resolve(strict=True).is_relative_to(repo_root) is False:
            raise ValueError(f"receipt path component escapes repository: {current}")
    return current


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--scratch-root", required=True, type=Path)
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve(strict=True)
    scratch_root = args.scratch_root.resolve(strict=True)
    job_id = os.environ.get("PBS_JOBID", "")
    if not _JOB_ID_RE.fullmatch(job_id):
        parser.error("PBS_JOBID is missing or malformed")
    try:
        binding = _execution_binding(repo_root)
        publisher = ReceiptPublisher(repo_root, job_id)
    except (FileExistsError, FileNotFoundError, OSError, ValueError) as exc:
        sys.stderr.write(f"probe preflight/create-only failure: {exc}\n")
        return 4
    rc, receipt = run_probe(
        repo_root, scratch_root, publisher=publisher, execution_binding=binding
    )
    try:
        path = publisher.publish_final(receipt)
    except (FileExistsError, OSError, ValueError) as exc:
        sys.stderr.write(f"create-only receipt publish failure: {exc}\n")
        return 4
    sys.stdout.write(json.dumps({"receipt": str(path), "overall_verdict": receipt["overall_verdict"]}, ensure_ascii=False) + "\n")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
