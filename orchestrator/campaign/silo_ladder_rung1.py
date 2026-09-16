#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Silo ladder rung 1 専用 characterization driver。

通常 campaign へは接続しない ability-probe 専用 entry である。結果 JSON 内の
``checks`` は表示用にすぎず、受理時には raw field から全 predicate を再計算する。
object / binary の生 bytes はサイズ上 raw bundle へ保持せず、compile replay、
nm/readelf、run の command receipt と build record を sha256 鎖で結ぶ。したがって
第三者が再導出できる範囲は、この鎖の整合性までである。NQSV の scheduler
会計エピローグから exit status は取得できない。in-job 成功は success sentinel、
failure receipt の不在、gap ``status=complete`` の既存三検査で証明する。
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import functools
import hashlib
import io
import json
import os
import random
import re
import secrets
import shlex
import shutil
import statistics
import subprocess
import sys
import tarfile
import tempfile
import time
from typing import Any, Iterable, Mapping, Sequence
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

_IMPORT_ROOT = Path(__file__).resolve().parents[2]
_ORCHESTRATOR_ROOT = Path(__file__).resolve().parents[1]

from . import (
    condition_meaning_gate,
    env_attestation,
    env_contract,
    execution_guard,
    patchharness,
    toolchain_binding,
)
from . import silo_ladder_rung1_contract as patch_contract
from .toolchain_binding import tool_version_body


SCHEMA_VERSION = "silo_ladder_rung1/v1"
SCHEDULE_SCHEMA = "silo_ladder_rung1-schedule/v1"
RAW_MANIFEST_SCHEMA = "silo_ladder_rung1-raw-manifest/v1"
COMMAND_RECEIPT_SCHEMA = "silo_ladder_rung1-command-receipt/v1"
ARTIFACT_ID = "silo_ladder_rung1"
PIN = "511c9538e4e8efa54b45cda62e72389ed3b706ec"
RUNG_MACRO = patch_contract.RUNG_MACRO
REPORT_MACRO = patch_contract.REPORT_MACRO
IDENTITY_SYMBOL = patch_contract.IDENTITY_SYMBOL
SOURCE_FILES = patch_contract.SOURCE_FILES
THIRD_PARTY_NAMES = ("masstree", "mimalloc", "googletest")
THIRD_PARTY_SOURCE_ROOT_ENV = "IZANAGI_THIRDPARTY_SOURCE_ROOT"
THIRD_PARTY_STAGING_RELATIVE = Path(
    "output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src"
)
WORKLOADS = {
    "W-cal": {
        "calibration_status": "registered",
        "argv": [
            "-ycsb_rmw=false", "-ycsb_rratio=50", "-ycsb_zipf_skew=0.9",
            "-ycsb_tuple_num=1000000", "-ycsb_max_ope=10",
            "-thread_num=48", "-extime=3",
        ],
    },
    "W-hw": {
        "calibration_status": "contract-transfer-only",
        "argv": [
            "-ycsb_rmw=true", "-ycsb_zipf_skew=0.9",
            "-ycsb_tuple_num=1000000", "-ycsb_max_ope=10",
            "-thread_num=48", "-extime=3",
        ],
    },
}
CORRECTNESS_WORKLOAD = [
    "-ycsb_rmw=true", "-ycsb_zipf_skew=0.9", "-ycsb_tuple_num=50",
    "-ycsb_max_ope=5", "-thread_num=4", "-extime=1",
]
INFRA_REASON_CODES = frozenset({
    "attestation", "timeout", "nonzero_returncode", "parse_failure",
    "process_competition",
})
WRAPPER_INFRA_STAGES = frozenset({
    "interpreter_resolution",
    "qstat_initial",
    "qstat_driver",
    "dependency_acquire",
    "dependency_extract",
    "attestation_acquisition",
    "post_driver_finalize",
})
WRAPPER_STAGES = WRAPPER_INFRA_STAGES | frozenset({
    "contract_bootstrap",
    "submit_binding_contract",
    "policy_contract",
    "schema_contract",
    "json_contract",
    "source_identity_contract",
    "third_party_copy_contract",
    "dependency_policy_contract",
    "dependency_build",
    "driver_gap",
})
FORBIDDEN_ARG_PREFIXES = (
    "-U", "-include", "-imacros", "-B", "-specs", "-flto",
)
_ENV_ALLOW_EXACT = frozenset({
    "HOME", "USER", "LOGNAME", "SHELL", "PATH", "TMPDIR", "TEMP", "TMP",
    "LANG", "LANGUAGE", "LC_ALL", "LC_CTYPE", "TZ", "TERM",
    "PBS_JOBID", "PBS_O_WORKDIR", "PBS_NODEFILE", "PBS_QUEUE",
    "IZANAGI_SUBMISSION_NONCE", "IZANAGI_GFLAGS_INSTALL",
    "IZANAGI_GLOG_INSTALL", "IZANAGI_ATTEMPT_NUMBER",
    THIRD_PARTY_SOURCE_ROOT_ENV,
})
_ENV_FORBIDDEN_EXACT = frozenset({
    "CC", "CXX", "CPP", "CFLAGS", "CXXFLAGS", "CPPFLAGS", "LDFLAGS",
    "LD_PRELOAD", "LD_LIBRARY_PATH", "CPATH", "CPLUS_INCLUDE_PATH",
    "LIBRARY_PATH", "COMPILER_PATH", "GCC_EXEC_PREFIX", "CMAKE_PREFIX_PATH",
    "CMAKE_TOOLCHAIN_FILE", "CMAKE_PROJECT_INCLUDE",
    "CMAKE_PROJECT_INCLUDE_BEFORE", "CMAKE_PROJECT_TOP_LEVEL_INCLUDES",
    "CMAKE_C_COMPILER_LAUNCHER", "CMAKE_CXX_COMPILER_LAUNCHER",
    "PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "MAKEFLAGS",
})
_ENV_FORBIDDEN_PREFIXES = (
    "GIT_", "CCACHE_", "SCCACHE_", "DISTCC_", "ICECC_",
)
_HEX64 = re.compile(r"[0-9a-f]{64}")
_RFC3339 = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z")
_TPS_RE = re.compile(r"(?m)^throughput\[tps\]:\s*(\d+)\s*$")
_COMMIT_RE = re.compile(r"(?m)^commit_counts_:\s*(\d+)\s*$")
_BATCH_RE = re.compile(r"(?m)^batch_commit_counts_:\s*(\d+)\s*$")
_WORKER_RE = re.compile(
    r"(?m)^silo_ladder_rung1\.worker_commit\[(\d+)\]=(\d+)\s*$"
)
_WORKER_BATCH_RE = re.compile(
    r"(?m)^silo_ladder_rung1\.worker_batch_commit\[(\d+)\]=(\d+)\s*$"
)
_ACCOUNTING_RE = re.compile(
    r"(?i)(nqsv|request\s*(?:id|name)|(?:started|ended)\s+request\s+time|"
    r"exit[_ ]?status|resources_used|cpu\s*time|memory|"
    r"elap(?:se|sed|stim)|walltime)"
)
_NQSV_REQUEST_ID_RE = re.compile(
    r"(?m)^[ \t]*Request ID:[ \t]*(\S+)[ \t]*$"
)
_NQSV_STARTED_RE = re.compile(
    r"(?m)^[ \t]*Started Request Time:[ \t]*\S.*$"
)
_NQSV_ENDED_RE = re.compile(
    r"(?m)^[ \t]*Ended Request Time:[ \t]*\S.*$"
)
_NQSV_ELAPSE_RE = re.compile(
    r"(?m)^[ \t]*Elapse:[ \t]*\S.*$"
)


class DriverError(RuntimeError):
    """Characterization を fail-closed で停止する。"""


class ContractFailure(DriverError):
    """入力・source・binding の契約破綻。再試行しない。"""


class InfraFailure(DriverError):
    """閉じた reason enum に属する取得系 failure。"""

    def __init__(self, reason_code: str, detail: str) -> None:
        if reason_code not in INFRA_REASON_CODES:
            raise ValueError(f"unknown infra reason code: {reason_code}")
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}: {detail}")


class SubstantiveNegative(DriverError):
    """有効測定が ability-probe predicate を満たさない。再試行しない。"""


def classify_wrapper_failure(stage: str, returncode: int) -> tuple[str, str]:
    """shell failure の retry 集合を事前列挙した段階だけに閉じる。"""
    if stage not in WRAPPER_STAGES:
        return ("contract", "contract_failure")
    if stage in WRAPPER_INFRA_STAGES:
        return (
            "infra",
            "timeout" if returncode == 124 else "nonzero_returncode",
        )
    if stage == "dependency_build" and returncode == 124:
        return ("infra", "timeout")
    return ("contract", "contract_failure")


@dataclass(frozen=True)
class EvidenceFailure:
    reason_code: str
    detail: str


@dataclass(frozen=True)
class Deadline:
    """policy 由来の monotonic absolute deadline。"""

    expires_monotonic: float
    label: str

    @classmethod
    def after(cls, seconds: int | float, label: str) -> "Deadline":
        if seconds <= 0:
            raise ContractFailure(f"{label} deadline must be positive")
        return cls(time.monotonic() + float(seconds), label)

    def remaining(self) -> float:
        remaining = self.expires_monotonic - time.monotonic()
        if remaining <= 0:
            raise InfraFailure("timeout", f"{self.label} deadline exhausted")
        return remaining

    def subprocess_timeout(self, requested: int | float) -> float:
        if requested <= 0:
            raise ContractFailure("subprocess timeout must be positive")
        return min(float(requested), self.remaining())

    def capped(self, seconds: int | float, label: str) -> "Deadline":
        self.remaining()
        return Deadline(
            min(self.expires_monotonic, time.monotonic() + float(seconds)),
            label,
        )


_COMMAND_RECEIPT_ROOT: Path | None = None
_COMMAND_RECEIPT_INDEX = 0


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _runtime_module_paths(repo: Path) -> list[Path]:
    """取得・検証の実行意味論を持つ Python module の閉じた binding 集合。"""
    verifier = repo / "orchestrator/verifier"
    activation_records = (
        repo / "orchestrator/campaign/env_contract_activations"
    )
    paths = [
        repo / "orchestrator/campaign/__init__.py",
        repo / "orchestrator/campaign/silo_ladder_rung1_contract.py",
        repo / "orchestrator/campaign/toolchain_binding.py",
        repo / "orchestrator/campaign/env_contract.py",
        repo / "orchestrator/campaign/env_contract_activation.py",
        *sorted(activation_records.glob("*.json")),
        repo / "orchestrator/campaign/env_attestation.py",
        repo / "orchestrator/campaign/calibration_verify.py",
        repo / "orchestrator/campaign/execution_guard.py",
        repo / "orchestrator/calibrator/__init__.py",
        repo / "orchestrator/calibrator/effective_clock_policy.py",
        repo / "orchestrator/calibrator/schema_v2.py",
        repo / "orchestrator/calibrator/tsc.py",
        repo / "orchestrator/campaign/patchharness.py",
        repo / "tools/pegasus/run_probe.py",
        *sorted(verifier.rglob("*.py")),
    ]
    return sorted(set(paths))


def runtime_modules_binding(repo: Path) -> list[dict[str, str]]:
    return [
        {
            "path": path.relative_to(repo).as_posix(),
            "sha256": sha256_file(path),
        }
        for path in _runtime_module_paths(repo)
    ]


def runtime_modules_sha256(repo: Path) -> str:
    return sha256_bytes(json.dumps(
        runtime_modules_binding(repo),
        sort_keys=True, separators=(",", ":"),
    ).encode("utf-8"))


def scrub_environment(
    source: Mapping[str, str] | None = None, *, install: bool = False,
) -> dict[str, str]:
    """明示 allowlist だけを残す。flag/cache/wrapper/GIT 注入面は常に除く。"""
    original = dict(os.environ if source is None else source)
    cleaned = {
        key: value for key, value in original.items()
        if key in _ENV_ALLOW_EXACT
        and key not in _ENV_FORBIDDEN_EXACT
        and not key.startswith(_ENV_FORBIDDEN_PREFIXES)
    }
    if install:
        os.environ.clear()
        os.environ.update(cleaned)
    return cleaned


def _run(
    argv: Sequence[str], *, cwd: Path | None = None, timeout: int = 60,
    stdout_path: Path | None = None, stderr_path: Path | None = None,
    deadline: Deadline | None = None,
    receipt_path: Path | None = None,
    target_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    global _COMMAND_RECEIPT_INDEX
    env = scrub_environment()
    effective_timeout = (
        deadline.subprocess_timeout(timeout) if deadline is not None else float(timeout)
    )
    if receipt_path is None and _COMMAND_RECEIPT_ROOT is not None:
        executable = re.sub(r"[^A-Za-z0-9_.-]+", "-", Path(argv[0]).name)[:40]
        receipt_path = (
            _COMMAND_RECEIPT_ROOT
            / f"{_COMMAND_RECEIPT_INDEX:04d}-{executable}.command.json"
        )
        _COMMAND_RECEIPT_INDEX += 1
    argv0 = Path(argv[0])
    try:
        argv0_resolved = argv0.resolve(strict=True)
    except OSError:
        argv0_resolved = argv0
    argv0_sha256 = (
        sha256_file(argv0_resolved)
        if argv0_resolved.is_file() else None
    )
    target_sha256 = (
        sha256_file(target_path)
        if target_path is not None
        and target_path.is_file()
        and not target_path.is_symlink()
        else None
    )
    started_at = utc_now()
    started_monotonic = time.monotonic()
    timed_out = False
    try:
        if stdout_path is None and stderr_path is None:
            result = subprocess.run(
                list(argv), cwd=cwd, env=env, text=True, capture_output=True,
                timeout=effective_timeout, check=False,
            )
        else:
            if stdout_path is None or stderr_path is None:
                raise ContractFailure(
                    "stdout/stderr raw path must be supplied together"
                )
            stdout_path.parent.mkdir(parents=True, exist_ok=True)
            with stdout_path.open("x", encoding="utf-8") as out, stderr_path.open(
                "x", encoding="utf-8"
            ) as err:
                result = subprocess.run(
                    list(argv), cwd=cwd, env=env, text=True, stdout=out, stderr=err,
                    timeout=effective_timeout, check=False,
                )
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        if receipt_path is not None:
            stdout_raw = (
                stdout_path.read_bytes()
                if stdout_path is not None and stdout_path.is_file()
                else (exc.stdout or "").encode() if isinstance(exc.stdout, str)
                else (exc.stdout or b"")
            )
            stderr_raw = (
                stderr_path.read_bytes()
                if stderr_path is not None and stderr_path.is_file()
                else (exc.stderr or "").encode() if isinstance(exc.stderr, str)
                else (exc.stderr or b"")
            )
            _write_raw_json(receipt_path, {
                "schema_version": COMMAND_RECEIPT_SCHEMA,
                "argv": list(argv),
                "cwd": str((cwd or Path.cwd()).resolve()),
                "started_at_utc": started_at,
                "completed_at_utc": utc_now(),
                "elapsed_monotonic_s": time.monotonic() - started_monotonic,
                "timeout_s": effective_timeout,
                "timed_out": True,
                "returncode": None,
                "stdout_sha256": sha256_bytes(stdout_raw),
                "stderr_sha256": sha256_bytes(stderr_raw),
                "argv0_sha256": argv0_sha256,
                "target_sha256": target_sha256,
            })
        raise InfraFailure("timeout", f"command timed out: {argv[0]}") from exc
    if receipt_path is not None:
        stdout_raw = (
            stdout_path.read_bytes()
            if stdout_path is not None
            else result.stdout.encode("utf-8")
        )
        stderr_raw = (
            stderr_path.read_bytes()
            if stderr_path is not None
            else result.stderr.encode("utf-8")
        )
        _write_raw_json(receipt_path, {
            "schema_version": COMMAND_RECEIPT_SCHEMA,
            "argv": list(argv),
            "cwd": str((cwd or Path.cwd()).resolve()),
            "started_at_utc": started_at,
            "completed_at_utc": utc_now(),
            "elapsed_monotonic_s": time.monotonic() - started_monotonic,
            "timeout_s": effective_timeout,
            "timed_out": timed_out,
            "returncode": result.returncode,
            "stdout_sha256": sha256_bytes(stdout_raw),
            "stderr_sha256": sha256_bytes(stderr_raw),
            "argv0_sha256": argv0_sha256,
            "target_sha256": target_sha256,
        })
    return result


def _tool_identity(name: str, executable: str | None = None) -> dict[str, Any]:
    candidate = executable or shutil.which(name, path=os.environ.get("PATH"))
    if candidate is None:
        raise DriverError(f"required tool is not resolvable: {name}")
    real = Path(candidate).resolve(strict=True)
    if not real.is_file():
        raise DriverError(f"tool is not a regular file: {real}")
    version_argv = [str(real), "--version"]
    result = _run(version_argv, timeout=30)
    if result.returncode != 0:
        raise InfraFailure(
            "nonzero_returncode",
            f"tool version failed: {name}: rc={result.returncode}",
        )
    return {
        "name": name,
        "realpath": str(real),
        "version": (result.stdout + result.stderr).strip(),
        "sha256": sha256_file(real),
    }


def capture_tool_identities() -> list[dict[str, Any]]:
    """A-4 の tool identity 集合。python は実行中 interpreter 自身を束縛する。"""
    return [
        _tool_identity(name, sys.executable if name == "python" else None)
        for name in ("git", "nm", "readelf", "cmake", "gcc", "g++", "python")
    ]


def generate_schedule(seed: str | None = None) -> dict[str, Any]:
    """CSPRNG seed から、両方向が各3回の 24-run schedule を凍結する。"""
    chosen = seed or secrets.token_hex(32)
    if re.fullmatch(r"[0-9a-f]{64}", chosen) is None:
        raise ValueError("schedule seed must be 64 lowercase hex")
    rng = random.Random(int(chosen, 16))
    stock_first = [True] * 3 + [False] * 3
    workload_first = [True] * 3 + [False] * 3
    rng.shuffle(stock_first)
    rng.shuffle(workload_first)
    rows: list[dict[str, Any]] = []
    for rep in range(1, 7):
        workload_order = (
            ("W-cal", "W-hw") if workload_first[rep - 1]
            else ("W-hw", "W-cal")
        )
        variant_order = (
            ("stock", "rung-perf") if stock_first[rep - 1]
            else ("rung-perf", "stock")
        )
        for workload in workload_order:
            for variant in variant_order:
                rows.append({
                    "ordinal": len(rows),
                    "workload": workload,
                    "rep": rep,
                    "variant": variant,
                })
    return {
        "schema_version": SCHEDULE_SCHEMA,
        "algorithm": "python-random-v1-from-csprng-256",
        "seed": chosen,
        "runs": rows,
    }


def validate_schedule(receipt: Mapping[str, Any]) -> EvidenceFailure | None:
    if type(receipt) is not dict or set(receipt) != {
        "schema_version", "algorithm", "seed", "runs",
    }:
        return EvidenceFailure("schedule_balance", "schedule schema is not closed")
    if (
        receipt["schema_version"] != SCHEDULE_SCHEMA
        or receipt["algorithm"] != "python-random-v1-from-csprng-256"
        or type(receipt["seed"]) is not str
        or re.fullmatch(r"[0-9a-f]{64}", receipt["seed"]) is None
    ):
        return EvidenceFailure("schedule_balance", "schedule identity is invalid")
    runs = receipt["runs"]
    if type(runs) is not list or len(runs) != 24:
        return EvidenceFailure("schedule_balance", "schedule must have 24 runs")
    expected_keys = {"ordinal", "workload", "rep", "variant"}
    if any(type(row) is not dict or set(row) != expected_keys for row in runs):
        return EvidenceFailure("schedule_balance", "schedule row schema mismatch")
    if [row["ordinal"] for row in runs] != list(range(24)):
        return EvidenceFailure("schedule_balance", "ordinals are not complete")
    for workload in WORKLOADS:
        first_by_workload: list[str] = []
        for rep in range(1, 7):
            indexes = [
                index for index, row in enumerate(runs)
                if row["workload"] == workload and row["rep"] == rep
            ]
            pair = [runs[index] for index in indexes]
            if len(pair) != 2 or {row["variant"] for row in pair} != {
                "stock", "rung-perf",
            }:
                return EvidenceFailure("schedule_balance", "pair is incomplete")
            if indexes[1] != indexes[0] + 1:
                return EvidenceFailure(
                    "schedule_balance", "workload/rep pair is not adjacent",
                )
            first_by_workload.append(pair[0]["variant"])
        if first_by_workload.count("stock") != 3:
            return EvidenceFailure(
                "schedule_balance",
                f"{workload} stock/rung first is not 3/3",
            )
    first_variants = []
    first_workloads = []
    for rep in range(1, 7):
        rep_rows = [row for row in runs if row["rep"] == rep]
        if len(rep_rows) != 4:
            return EvidenceFailure("schedule_balance", "rep size mismatch")
        first_variants.append(rep_rows[0]["variant"])
        first_workloads.append(rep_rows[0]["workload"])
    if first_variants.count("stock") != 3:
        return EvidenceFailure("schedule_balance", "stock/rung first is not 3/3")
    if first_workloads.count("W-cal") != 3:
        return EvidenceFailure("schedule_balance", "workload first is not 3/3")
    return None


def validate_compile_argv(
    argv: Sequence[str], *, expected_macro: str | None,
    ledger_macros: Iterable[str] = (RUNG_MACRO, REPORT_MACRO),
    require_report: bool = False,
    expected_compiler_realpath: str | None = None,
) -> tuple[str, ...]:
    """response/wrapper/LTO 面を拒否し、active macro 集合を返す。"""
    if type(argv) not in (list, tuple) or not argv:
        raise DriverError("compile argv must be a non-empty sequence")
    if expected_compiler_realpath is not None:
        compiler = os.path.realpath(argv[0])
        expected = os.path.realpath(expected_compiler_realpath)
        if compiler != expected:
            raise ContractFailure(
                f"compiler argv[0] differs from recorded g++: {compiler} != {expected}"
            )
    normalized_tokens: list[str] = []
    index = 0
    while index < len(argv):
        token = argv[index]
        if type(token) is not str:
            raise DriverError("compile argv contains a non-string token")
        if token.startswith("-Wp,"):
            forwarded = token[4:].split(",")
            normalized_tokens.extend(forwarded)
        elif token == "-Xpreprocessor":
            if index + 1 >= len(argv):
                raise DriverError("-Xpreprocessor has no forwarded token")
            normalized_tokens.append(argv[index + 1])
            index += 1
        else:
            normalized_tokens.append(token)
        index += 1
    for token in normalized_tokens:
        if (
            token == "-D"
            or token.startswith("@")
            or token.startswith(FORBIDDEN_ARG_PREFIXES)
        ):
            raise DriverError(f"forbidden compile argv token: {token}")
    macro_tokens: dict[str, list[str]] = {macro: [] for macro in ledger_macros}
    for token in normalized_tokens:
        matched = False
        for macro in macro_tokens:
            if token in (f"-D{macro}", f"-D{macro}=1"):
                macro_tokens[macro].append(token)
                matched = True
            elif token.startswith(f"-D{macro}="):
                raise DriverError(f"non-one ledger macro value: {token}")
        if not matched and any(macro in token for macro in macro_tokens):
            raise DriverError(f"unrecognized ledger macro carrier: {token}")
    active = tuple(sorted(macro for macro, tokens in macro_tokens.items() if tokens))
    if expected_macro is None:
        if active:
            raise DriverError(f"stock compile argv activates ledger macros: {active}")
    else:
        if macro_tokens.get(expected_macro) is None:
            raise DriverError(f"unknown expected macro: {expected_macro}")
        if len(macro_tokens[expected_macro]) != 1:
            raise DriverError(
                f"{expected_macro} occurrence count is not exactly one"
            )
        allowed = {expected_macro}
        if require_report:
            allowed.add(REPORT_MACRO)
        if require_report and len(macro_tokens[REPORT_MACRO]) != 1:
            raise DriverError(
                f"{REPORT_MACRO} occurrence count is not exactly one"
            )
        if not require_report and macro_tokens.get(REPORT_MACRO):
            raise DriverError(
                f"{REPORT_MACRO} occurrence count must be exactly zero"
            )
        if set(active) - allowed:
            raise DriverError(f"unexpected active ledger macro: {active}")
    return active


_TARGET_OBJECT_DIR_PARTS = ("CMakeFiles", "ycsb_silo.exe.dir")


def _compile_entry_argv(entry: Mapping[str, Any]) -> list[Any] | None:
    if type(entry.get("arguments")) is list:
        return list(entry["arguments"])
    if type(entry.get("command")) is str:
        return shlex.split(entry["command"])
    return None


def _compile_output_from_argv(argv: Sequence[Any]) -> str | None:
    outputs = [
        argv[index + 1]
        for index, token in enumerate(argv[:-1])
        if token == "-o"
    ]
    if not outputs:
        return None
    if len(outputs) != 1 or type(outputs[0]) is not str or not outputs[0]:
        raise DriverError("compile argv object output is ambiguous")
    return outputs[0]


def _compile_output_path(
    entry: Mapping[str, Any], argv: Sequence[Any] | None,
) -> Path | None:
    directory = entry.get("directory")
    if type(directory) is not str or not directory:
        raise DriverError("compile_commands entry directory is missing")
    explicit = entry.get("output")
    if explicit is not None and (type(explicit) is not str or not explicit):
        raise DriverError("compile_commands entry output is invalid")
    derived = _compile_output_from_argv(argv) if argv is not None else None
    output = explicit if explicit is not None else derived
    if output is None:
        return None
    path = Path(output)
    if not path.is_absolute():
        path = Path(directory) / path
    return path.resolve()


def _is_target_object_path(path: Path) -> bool:
    parts = path.parts
    return any(
        parts[index:index + 2] == _TARGET_OBJECT_DIR_PARTS
        and index + 2 < len(parts)
        for index in range(len(parts) - 1)
    )


def _compile_source_rel(
    entry: Mapping[str, Any], source_root: Path | None,
) -> str | None:
    file_value = entry.get("file")
    if type(file_value) is not str or not file_value:
        return None
    file_path = Path(file_value)
    if source_root is not None:
        if not file_path.is_absolute():
            file_path = Path(str(entry.get("directory", ""))) / file_path
        try:
            return file_path.resolve().relative_to(
                source_root.resolve()
            ).as_posix()
        except (OSError, ValueError):
            return None
    source_name = file_value.replace("\\", "/")
    matches = [
        relative for relative in SOURCE_FILES
        if source_name == relative or source_name.endswith("/" + relative)
    ]
    return matches[0] if len(matches) == 1 else None


def compile_commands_for_sources(
    document: Sequence[Mapping[str, Any]], source_root: Path | None,
) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    wanted = set(SOURCE_FILES)
    for entry in document:
        if type(entry) is not dict:
            raise DriverError("compile_commands entry is not an object")
        source_rel = _compile_source_rel(entry, source_root)
        if source_rel not in wanted:
            continue
        argv = _compile_entry_argv(entry)
        object_path = _compile_output_path(entry, argv)
        if object_path is None or not _is_target_object_path(object_path):
            continue
        if argv is None:
            raise DriverError(f"compile argv missing for {source_rel}")
        if entry.get("output") is not None:
            derived_entry = dict(entry)
            derived_entry["output"] = None
            derived_path = _compile_output_path(derived_entry, argv)
            if derived_path is None or object_path != derived_path:
                raise DriverError(
                    "compile_commands output differs from "
                    "compile argv object output"
                )
        found.append({
            "source_rel": source_rel,
            "directory": str(entry["directory"]),
            "argv": argv,
            "output": str(object_path),
        })
    counts = {path: sum(item["source_rel"] == path for item in found) for path in wanted}
    if counts != {path: 1 for path in wanted}:
        raise DriverError(f"target TU compile command count mismatch: {counts}")
    return sorted(found, key=lambda item: item["source_rel"])


def reexecute_compile_and_compare(
    invocation: Mapping[str, Any], *, deadline: Deadline | None = None,
) -> dict[str, Any]:
    """compile_commands の同一 argv を再実行し、生成 object bytes の一致を確認する。"""
    argv = list(invocation["argv"])
    output = invocation.get("output")
    if not output:
        for index, token in enumerate(argv[:-1]):
            if token == "-o":
                output = argv[index + 1]
                break
    if type(output) is not str or not output:
        raise DriverError("compile invocation has no object output")
    object_path = Path(output)
    if not object_path.is_absolute():
        object_path = Path(str(invocation["directory"])) / object_path
    before = sha256_file(object_path)
    result = _run(
        argv, cwd=Path(str(invocation["directory"])), timeout=900,
        deadline=deadline,
    )
    if result.returncode != 0:
        raise InfraFailure(
            "nonzero_returncode",
            f"compile argv replay failed: rc={result.returncode}",
        )
    after = sha256_file(object_path)
    if before != after:
        raise DriverError("compile argv replay object sha256 mismatch")
    return {
        "source_rel": invocation["source_rel"],
        "argv": argv,
        "object_path": str(object_path),
        "object_sha256": before,
        "replay_object_sha256": after,
        "replay_match": True,
    }


def parse_run_stdout(text: str, *, liveness: bool) -> dict[str, Any]:
    throughputs = _TPS_RE.findall(text)
    commits = _COMMIT_RE.findall(text)
    batches = _BATCH_RE.findall(text)
    if len(commits) != 1 or len(batches) != 1:
        raise DriverError("run stdout aggregate counters are ambiguous")
    result: dict[str, Any] = {
        "commit_count": int(commits[0]),
        "batch_commit_count": int(batches[0]),
    }
    if not liveness:
        if len(throughputs) != 1:
            raise DriverError("performance stdout throughput is ambiguous")
        result["throughput_tps"] = int(throughputs[0])
        return result
    worker_pairs = [(int(worker), int(value)) for worker, value in _WORKER_RE.findall(text)]
    batch_pairs = [
        (int(worker), int(value)) for worker, value in _WORKER_BATCH_RE.findall(text)
    ]
    if len(worker_pairs) != 48 or len(batch_pairs) != 48:
        raise DriverError("liveness footer does not contain exactly 48 workers")
    if len({worker for worker, _ in worker_pairs}) != 48:
        raise DriverError("liveness worker ordinals are duplicated")
    result["per_worker_commits"] = [
        {"worker": worker, "commits": value}
        for worker, value in sorted(worker_pairs)
    ]
    result["per_worker_batch_commits"] = [
        {"worker": worker, "commits": value}
        for worker, value in sorted(batch_pairs)
    ]
    return result


def _validate_correctness_commit_witness(
        verifier: Mapping[str, Any], stdout: str,
) -> None:
    """凍結 verifier JSON の外側で raw stdout counter と txns を照合する。"""
    witness = parse_run_stdout(stdout, liveness=False)
    recorded_txns = verifier["results"][0]["stats"]["txns"]
    if witness["batch_commit_count"] != 0:
        raise DriverError("raw correctness batch commit count is not zero")
    if witness["commit_count"] != recorded_txns:
        raise DriverError(
            "raw correctness commit witness differs from verifier txns"
        )


def _exact_keys(value: Any, keys: set[str]) -> bool:
    return type(value) is dict and set(value) == keys


def _dependency_pins(repo: Path | None = None) -> dict[str, str]:
    document = _load_json(
        (repo or _repo_root()) / "tools/pegasus/policy.json"
    )
    policy = document["silo_ladder_rung1"]["dependency_pins"]
    if (
        not _exact_keys(policy, {"gflags", "glog"})
        or any(
            type(value) is not str
            or re.fullmatch(r"[0-9a-f]{40}", value) is None
            for value in policy.values()
        )
        or policy["gflags"] != document["gflags_expected_head"]
        or policy["glog"] != document["glog_expected_head"]
    ):
        raise ContractFailure("dependency pin policy is invalid")
    return dict(policy)


def third_party_policy_path(repo: Path | None = None) -> Path:
    """共有 third-party policy の所有側 path を返す。"""
    root = repo if repo is not None else _repo_root()
    return Path(root) / "tools/pegasus/policy.json"


def third_party_policy(repo: Path | None = None) -> tuple[dict[str, str], ...]:
    """offline build source policy と CCBench FetchContent literal を同期検査する。"""
    root = (repo or _repo_root()).resolve()
    document = _load_json(third_party_policy_path(root))
    value = document["silo_ladder_rung1"].get("third_party_sources")
    keys = {"name", "source_name", "url", "fetchcontent_ref", "pin"}
    if (
        type(value) is not list
        or len(value) != len(THIRD_PARTY_NAMES)
        or any(not _exact_keys(item, keys) for item in value)
        or tuple(item["name"] for item in value) != THIRD_PARTY_NAMES
        or any(
            type(item[key]) is not str or not item[key]
            for item in value
            for key in keys
        )
        or any(item["source_name"] != item["name"] for item in value)
        or any(re.fullmatch(r"[a-z][a-z0-9_-]*", item["source_name"]) is None
               for item in value)
        or any(not item["url"].startswith("https://github.com/")
               or not item["url"].endswith(".git") for item in value)
        or any(re.fullmatch(r"[0-9a-f]{40}", item["pin"]) is None
               for item in value)
    ):
        raise ContractFailure("third-party source policy is invalid")

    cmake = (
        root / "external/ccbench/cmake/ThirdParty.cmake"
    ).read_text(encoding="utf-8", errors="strict")
    for item in value:
        prefix = f"CCBENCH_{item['name'].upper()}"
        observed: dict[str, str] = {}
        for suffix in ("REPO", "TAG"):
            matches = re.findall(
                rf'(?m)^\s*set\({prefix}_{suffix}\s+"([^"]+)"\)',
                cmake,
            )
            if len(matches) != 1:
                raise ContractFailure(
                    f"ThirdParty.cmake {prefix}_{suffix} literal is ambiguous"
                )
            observed[suffix] = matches[0]
        if (
            observed["REPO"] != item["url"]
            or observed["TAG"] != item["fetchcontent_ref"]
        ):
            raise ContractFailure(
                f"third-party policy/ThirdParty.cmake drift: {item['name']}"
            )
        if (
            re.fullmatch(r"[0-9a-f]{40}", item["fetchcontent_ref"])
            and item["fetchcontent_ref"] != item["pin"]
        ):
            raise ContractFailure(
                f"third-party SHA ref/pin drift: {item['name']}"
            )
    return tuple(dict(item) for item in value)


def third_party_source_contract(
    repo: Path | None = None, *, source_root: Path | None = None,
) -> list[dict[str, Any]]:
    """configure に渡す local source 3 本を pinned-clean と実証する。"""
    root = (repo or _repo_root()).resolve()
    policy = third_party_policy(root)
    configured_root = (
        source_root
        if source_root is not None
        else Path(os.environ[THIRD_PARTY_SOURCE_ROOT_ENV])
        if os.environ.get(THIRD_PARTY_SOURCE_ROOT_ENV)
        else root / THIRD_PARTY_STAGING_RELATIVE
    )
    try:
        resolved_root = Path(configured_root).resolve(strict=True)
    except OSError as exc:
        raise ContractFailure(
            f"third-party source root is absent: {configured_root}"
        ) from exc
    if not resolved_root.is_dir() or Path(configured_root).is_symlink():
        raise ContractFailure("third-party source root is not a real directory")

    records: list[dict[str, Any]] = []
    for item in policy:
        unresolved = resolved_root / item["source_name"]
        try:
            source = unresolved.resolve(strict=True)
        except OSError as exc:
            raise ContractFailure(
                f"third-party source is absent: {item['name']}"
            ) from exc
        if not source.is_dir() or unresolved.is_symlink():
            raise ContractFailure(
                f"third-party source is not a real directory: {item['name']}"
            )
        head = _run([
            "git", "-C", str(source), "rev-parse", "--verify", "HEAD",
        ])
        status = _run([
            "git", "-C", str(source), "status", "--porcelain",
            "--untracked-files=all",
        ])
        if (
            head.returncode != 0
            or head.stdout != item["pin"] + "\n"
            or status.returncode != 0
            or status.stdout
        ):
            raise ContractFailure(
                f"third-party source is not pinned-clean: {item['name']}"
            )
        records.append({
            **item,
            "resolved_path": str(source),
            "git_head_raw": head.stdout,
            "git_status_porcelain_raw": status.stdout,
            "clean": True,
        })
    return records


def _copy_third_party_sources(
    records: Sequence[Mapping[str, Any]], destination_root: Path,
    *, repo: Path | None = None,
) -> list[dict[str, Any]]:
    """pinned-clean staging を build 専用 tree へ複製し、複製後も再照合する。"""
    destination_root.mkdir(parents=True, exist_ok=False)
    by_name = {item["name"]: item for item in records}
    if set(by_name) != set(THIRD_PARTY_NAMES):
        raise ContractFailure("third-party copy source set mismatch")
    for name in THIRD_PARTY_NAMES:
        item = by_name[name]
        shutil.copytree(
            item["resolved_path"],
            destination_root / item["source_name"],
            symlinks=True,
        )
    return third_party_source_contract(
        repo or _repo_root(), source_root=destination_root,
    )


def _valid_third_party_sources(value: Any) -> bool:
    try:
        policy = third_party_policy()
    except (ContractFailure, OSError, KeyError, TypeError, ValueError):
        return False
    keys = {
        "name", "source_name", "url", "fetchcontent_ref", "pin",
        "resolved_path", "git_head_raw", "git_status_porcelain_raw", "clean",
    }
    if (
        type(value) is not list
        or len(value) != len(policy)
        or any(not _exact_keys(item, keys) for item in value)
    ):
        return False
    by_name = {item["name"]: item for item in value}
    return (
        set(by_name) == set(THIRD_PARTY_NAMES)
        and all(
            all(item[key] == expected[key] for key in (
                "name", "source_name", "url", "fetchcontent_ref", "pin",
            ))
            and type(item["resolved_path"]) is str
            and Path(item["resolved_path"]).is_absolute()
            and item["git_head_raw"] == item["pin"] + "\n"
            and item["git_status_porcelain_raw"] == ""
            and item["clean"] is True
            for expected in policy
            for item in (by_name[expected["name"]],)
        )
    )


def _third_party_configure_flags(
    records: Sequence[Mapping[str, Any]],
) -> list[str]:
    by_name = {item["name"]: item for item in records}
    if set(by_name) != set(THIRD_PARTY_NAMES):
        raise ContractFailure("third-party source record set mismatch")
    return [
        f"-DFETCHCONTENT_SOURCE_DIR_{name.upper()}="
        f"{by_name[name]['resolved_path']}"
        for name in THIRD_PARTY_NAMES
    ]


def _compile_invocations_complete(value: Any) -> bool:
    return (
        type(value) is list
        and len(value) == len(SOURCE_FILES)
        and {item.get("source_rel") for item in value} == set(SOURCE_FILES)
    )


def _valid_dependencies(
    value: Any, *, expected_pins: Mapping[str, str] | None = None,
) -> bool:
    if type(value) is not list or len(value) != 2:
        return False
    if any(not _exact_keys(item, {
        "name", "resolved_path", "pin", "git_head_raw",
        "git_status_porcelain_raw",
    }) for item in value):
        return False
    by_name = {item["name"]: item for item in value}
    pins = dict(expected_pins or _dependency_pins())
    return (
        set(by_name) == {"gflags", "glog"}
        and set(pins) == set(by_name)
        and all(
            type(item["resolved_path"]) is str
            and Path(item["resolved_path"]).is_absolute()
            and type(item["pin"]) is str
            and item["pin"] == pins[name]
            and item["git_head_raw"] == item["pin"] + "\n"
            and item["git_status_porcelain_raw"] == ""
            for name, item in by_name.items()
        )
    )


def _validate_correctness(leg: Mapping[str, Any]) -> list[EvidenceFailure]:
    failures: list[EvidenceFailure] = []
    if leg["workload"] != {"argv": CORRECTNESS_WORKLOAD, "threads": 4}:
        failures.append(EvidenceFailure(
            "correctness_workload", "correctness workload differs from t4 contract",
        ))
    build = leg["build"]
    dependencies = build["dependencies"]
    dependency_pins = _dependency_pins()
    dependency_prefix = ";".join(
        item["resolved_path"] for item in dependencies
    )
    third_party_sources = leg["provenance"]["third_party_sources"]
    third_party_flags = _third_party_configure_flags(third_party_sources)
    if not (
        build["id"] == "correctness"
        and build["trace"] is True
        and build["macros"] == [RUNG_MACRO]
        and build["identity_defined_count"] == 1
        and build["activation_ok"] is True
        and _compile_invocations_complete(build["compile_invocations"])
        and _valid_dependencies(dependencies, expected_pins=dependency_pins)
        and f"-DCMAKE_PREFIX_PATH={dependency_prefix}" in build["configure_argv"]
        and f"-DIZANAGI_GFLAGS_SRC_HEAD={dependency_pins['gflags']}"
        in build["configure_argv"]
        and f"-DIZANAGI_GLOG_SRC_HEAD={dependency_pins['glog']}"
        in build["configure_argv"]
        and _valid_third_party_sources(third_party_sources)
        and all(flag in build["configure_argv"] for flag in third_party_flags)
        and all(
            item["replay_match"] is True
            and item["object_sha256"] == item["replay_object_sha256"]
            for item in build["compile_invocations"]
        )
    ):
        failures.append(EvidenceFailure(
            "correctness_activation", "trace build activation/replay witness failed",
        ))
    verifier = leg["verifier"]
    result = verifier["results"][0]
    accepted = (
        leg["verifier_rc"] == 0
        and verifier["runs"] == 1
        and verifier["certified_serializable"] == 1
        and verifier["non_serializable"] == 0
        and verifier["indeterminate"] == 0
        and result["verdict"] == "serializable"
        and result["certified"] is True
        and result["stats"]["txns"] > 0
        and result["stats"]["writes"] > 0
        and result["integrity"]["clean"] is True
        and result["integrity"]["framing_violations"] == 0
        and result["integrity"]["write_intent_violations"] == 0
        and result["anomaly_count"] == 0
        and result["total_cycles"] == 0
    )
    if not accepted:
        failures.append(EvidenceFailure(
            "correctness_certified",
            "verifier results[0] is not certified serializable and clean",
        ))
    if (
        type(leg["trace_files"]) is not list or len(leg["trace_files"]) != 4
        or any(item["commits"] <= 0 or item["non_insert_write_witness"] is not True
               for item in leg["trace_files"])
    ):
        failures.append(EvidenceFailure("correctness_trace", "t4 trace witness failed"))
    return failures


def _validate_liveness(runs: Sequence[Mapping[str, Any]]) -> EvidenceFailure | None:
    expected_cells = {(workload, rep) for workload in WORKLOADS for rep in (1, 2)}
    actual_cells = {(run["workload"], run["rep"]) for run in runs}
    if len(runs) != 4 or actual_cells != expected_cells:
        return EvidenceFailure("per_worker_ever_committed", "liveness cells mismatch")
    if sorted(run["ordinal"] for run in runs) != list(range(24, 28)):
        return EvidenceFailure(
            "per_worker_ever_committed", "liveness ordinals are not 24-27",
        )
    for run in runs:
        workers = run["per_worker_commits"]
        batches = run["per_worker_batch_commits"]
        if (
            run["variant"] != "rung-liveness"
            or len(workers) != 48
            or [item["worker"] for item in workers] != list(range(48))
            or any(type(item["commits"]) is not int or item["commits"] <= 0 for item in workers)
            or sum(item["commits"] for item in workers) != run["commit_count"]
            or len(batches) != 48
            or [item["worker"] for item in batches] != list(range(48))
            or any(item["commits"] != 0 for item in batches)
            or run["batch_commit_count"] != 0
        ):
            return EvidenceFailure(
                "per_worker_ever_committed",
                "ordinal/all-positive/conservation/batch-zero witness failed",
            )
    return None


def _validate_bounded_completion(
    runs: Sequence[Mapping[str, Any]],
) -> EvidenceFailure | None:
    if (
        len(runs) != 4
        or any(
            run["returncode"] != 0
            or run["bounded_completion"] is not True
            for run in runs
        )
    ):
        return EvidenceFailure(
            "bounded_completion", "liveness run did not complete within bound",
        )
    return None


def _validate_performance(runs: Sequence[Mapping[str, Any]]) -> EvidenceFailure | None:
    if len(runs) != 24:
        return EvidenceFailure("performance_direction", "performance run count is not 24")
    if [run["ordinal"] for run in runs] != list(range(24)):
        return EvidenceFailure(
            "performance_direction", "performance ordinals are not complete",
        )
    if any(
        run["variant"] == "stock"
        and (
            run["commit_count"] <= 0
            or run["batch_commit_count"] != 0
        )
        for run in runs
    ):
        return EvidenceFailure(
            "performance_direction",
            "stock aggregate commit witness is absent or batch is nonzero",
        )
    for workload in WORKLOADS:
        stock = [
            run["throughput_tps"] for run in runs
            if run["workload"] == workload and run["variant"] == "stock"
            and run["returncode"] == 0
        ]
        rung = [
            run["throughput_tps"] for run in runs
            if run["workload"] == workload and run["variant"] == "rung-perf"
            and run["returncode"] == 0
        ]
        if len(stock) != 6 or len(rung) != 6 or max(rung) >= min(stock):
            return EvidenceFailure(
                "performance_direction",
                f"{workload}: max(rung) < min(stock) is false",
            )
    return None


def _validate_schema(document: Any) -> EvidenceFailure | None:
    top = {
        "schema_version", "artifact_id", "generated_at_utc", "classification",
        "activation_contract", "binding", "provenance", "correctness_leg",
        "gap_leg", "retry_policy", "raw_bundle", "limitations", "checks",
        "all_pass",
    }
    if not _exact_keys(document, top):
        return EvidenceFailure("schema", "top-level schema is not closed")
    if (
        document["schema_version"] != SCHEMA_VERSION
        or document["artifact_id"] != ARTIFACT_ID
        or type(document["generated_at_utc"]) is not str
        or _RFC3339.fullmatch(document["generated_at_utc"]) is None
    ):
        return EvidenceFailure("schema", "top-level identity is invalid")
    if not _exact_keys(document["classification"], {
        "evaluation_role", "research_goal_eligible",
        "recovery_measurement_eligibility",
    }):
        return EvidenceFailure("schema", "classification schema mismatch")
    if document["classification"] != {
        "evaluation_role": "ability_probe",
        "research_goal_eligible": False,
        "recovery_measurement_eligibility": False,
    }:
        return EvidenceFailure("schema", "classification values mismatch")
    if document["activation_contract"] != {
        "macro": RUNG_MACRO,
        "symbols": [IDENTITY_SYMBOL],
    }:
        return EvidenceFailure("schema", "activation contract mismatch")
    if document["limitations"] != {
        "raw_object_binary_bytes_retained": False,
        "nqsv_scheduler_exit_status": "unavailable",
        "third_party_rederivation": "sha256-chain-consistency-only",
    }:
        return EvidenceFailure("schema", "limitations contract mismatch")
    binding = document["binding"]
    if not _exact_keys(binding, {
        "patch", "ledger", "driver", "pbs_job", "submitter",
        "verifier_module", "policy", "runtime_modules", "ccbench_pin_full",
        "calibration",
    }):
        return EvidenceFailure("schema", "binding schema mismatch")
    for key in (
        "patch", "ledger", "driver", "pbs_job", "submitter",
        "verifier_module", "policy",
    ):
        if not _exact_keys(binding[key], {"path", "sha256"}):
            return EvidenceFailure("schema", f"binding.{key} schema mismatch")
        if type(binding[key]["path"]) is not str or not binding[key]["path"]:
            return EvidenceFailure("schema", f"binding.{key}.path is invalid")
    if (
        type(binding["runtime_modules"]) is not list
        or not binding["runtime_modules"]
        or any(
            not _exact_keys(item, {"path", "sha256"})
            or type(item["path"]) is not str
            or not item["path"]
            or type(item["sha256"]) is not str
            or _HEX64.fullmatch(item["sha256"]) is None
            for item in binding["runtime_modules"]
        )
        or [item["path"] for item in binding["runtime_modules"]]
        != sorted({item["path"] for item in binding["runtime_modules"]})
    ):
        return EvidenceFailure("schema", "runtime module binding schema mismatch")
    calibration = binding["calibration"]
    if not _exact_keys(calibration, {
        "path", "sha256", "contract_sha256", "quality_status",
        "records", "threads", "transfer_scope",
    }):
        return EvidenceFailure("schema", "calibration binding schema mismatch")
    for item in (
        *(binding[key]["sha256"] for key in (
            "patch", "ledger", "driver", "pbs_job", "submitter",
            "verifier_module", "policy",
        )),
        calibration["sha256"], calibration["contract_sha256"],
    ):
        if type(item) is not str or _HEX64.fullmatch(item) is None:
            return EvidenceFailure("schema", "binding sha256 is invalid")
    provenance = document["provenance"]
    if not _exact_keys(provenance, {
        "environment_scrubbed", "tools", "third_party_sources",
        "source_witness",
    }):
        return EvidenceFailure("schema", "provenance schema mismatch")
    if provenance["environment_scrubbed"] is not True:
        return EvidenceFailure("schema", "environment scrub witness mismatch")
    if (
        type(provenance["tools"]) is not list
        or any(not _exact_keys(item, {
            "name", "realpath", "version", "sha256",
        }) for item in provenance["tools"])
        or {item["name"] for item in provenance["tools"]} != {
            "git", "nm", "readelf", "cmake", "gcc", "g++", "python",
        }
        or not _valid_third_party_sources(provenance["third_party_sources"])
    ):
        return EvidenceFailure("schema", "tool identity schema mismatch")
    if not _exact_keys(provenance["source_witness"], {
        "submit_whole_tree_clean", "job_source_surface_clean",
        "job_source_exclusions", "job_prologue_manifest_sha256",
        "expected_patched_source_sha256", "observed_patched_source_sha256",
    }):
        return EvidenceFailure("schema", "source witness schema mismatch")
    source_witness = provenance["source_witness"]
    expected_patched = source_witness["expected_patched_source_sha256"]
    observed_patched = source_witness["observed_patched_source_sha256"]
    if (
        source_witness["submit_whole_tree_clean"] is not True
        or source_witness["job_source_surface_clean"] is not True
        or source_witness["job_source_exclusions"] != ["output"]
        or type(source_witness["job_prologue_manifest_sha256"]) is not str
        or _HEX64.fullmatch(source_witness["job_prologue_manifest_sha256"]) is None
        or type(expected_patched) is not dict
        or type(observed_patched) is not dict
        or set(expected_patched) != set(SOURCE_FILES)
        or expected_patched != observed_patched
        or any(
            type(value) is not str or _HEX64.fullmatch(value) is None
            for value in expected_patched.values()
        )
    ):
        return EvidenceFailure("schema", "source witness values mismatch")
    correctness = document["correctness_leg"]
    if not _exact_keys(correctness, {
        "workload", "build", "provenance", "verifier_rc", "verifier",
        "trace_files", "raw_paths",
    }):
        return EvidenceFailure("schema", "correctness leg schema mismatch")
    verifier = correctness["verifier"]
    if not _exact_keys(correctness["workload"], {"argv", "threads"}):
        return EvidenceFailure("schema", "correctness workload schema mismatch")
    if not _exact_keys(correctness["provenance"], {
        "environment_scrubbed", "tools", "ccbench_pin_full",
        "expected_patched_source_sha256", "observed_patched_source_sha256",
        "dependencies", "third_party_sources",
    }):
        return EvidenceFailure("schema", "correctness provenance schema mismatch")
    correctness_provenance = correctness["provenance"]
    if (
        correctness_provenance["environment_scrubbed"] is not True
        or correctness_provenance["ccbench_pin_full"] != PIN
        or type(correctness_provenance["tools"]) is not list
        or any(not _exact_keys(item, {
            "name", "realpath", "version", "sha256",
        }) for item in correctness_provenance["tools"])
        or {item["name"] for item in correctness_provenance["tools"]} != {
            "git", "nm", "readelf", "cmake", "gcc", "g++", "python",
        }
        or type(correctness_provenance["expected_patched_source_sha256"]) is not dict
        or correctness_provenance["expected_patched_source_sha256"]
        != correctness_provenance["observed_patched_source_sha256"]
        or set(correctness_provenance["expected_patched_source_sha256"])
        != set(SOURCE_FILES)
        or correctness_provenance["dependencies"]
        != correctness["build"]["dependencies"]
        or not _valid_third_party_sources(
            correctness_provenance["third_party_sources"]
        )
    ):
        return EvidenceFailure("schema", "correctness provenance values mismatch")
    if not _exact_keys(correctness["build"], {
        "id", "trace", "macros", "identity_defined_count",
        "transaction_object_sha256", "activation_ok", "configure_argv",
        "build_argv", "binary_sha256", "compile_invocations",
        "cmake_cache_sha256", "source_sha256", "raw_paths", "dependencies",
    }):
        return EvidenceFailure("schema", "correctness build schema mismatch")
    if (
        not _compile_invocations_complete(
            correctness["build"]["compile_invocations"]
        )
        or any(not _exact_keys(item, {
            "source_rel", "argv", "object_path", "object_sha256",
            "replay_object_sha256", "replay_match",
        }) for item in correctness["build"]["compile_invocations"])
        or type(correctness["build"]["source_sha256"]) is not dict
        or set(correctness["build"]["source_sha256"]) != set(SOURCE_FILES)
        or not _valid_dependencies(correctness["build"]["dependencies"])
    ):
        return EvidenceFailure("schema", "correctness build provenance schema mismatch")
    if (
        type(correctness["trace_files"]) is not list
        or any(not _exact_keys(item, {
            "path", "commits", "non_insert_write_witness",
        }) for item in correctness["trace_files"])
        or type(correctness["raw_paths"]) is not list
        or any(type(item) is not str for item in correctness["raw_paths"])
    ):
        return EvidenceFailure("schema", "correctness raw/trace schema mismatch")
    if not _exact_keys(verifier, {
        "runs", "certified_serializable", "non_serializable",
        "indeterminate", "results",
    }) or type(verifier["results"]) is not list or len(verifier["results"]) != 1:
        return EvidenceFailure("schema", "verifier envelope schema mismatch")
    result = verifier["results"][0]
    if not _exact_keys(result, {
        "trace_dir", "verdict", "certified", "serializable", "stats",
        "integrity", "anomaly_count", "total_cycles", "anomalies",
    }):
        return EvidenceFailure("schema", "verifier results[0] schema mismatch")
    if not _exact_keys(result["stats"], {
        "txns", "reads", "writes", "keys", "edges", "abort_reasons",
    }):
        return EvidenceFailure("schema", "verifier stats schema mismatch")
    if not _exact_keys(result["integrity"], {
        "clean", "orphan_reads", "version_dups", "dup_txids",
        "genesis_commits", "missing_txids", "write_version_mismatch",
        "malformed_keys", "framing_violations", "framing_violation_details",
        "lock_coverage_violations",
        "write_intent_violations", "permutation_violations",
        "permutation_violation_details", "notes",
    }):
        return EvidenceFailure("schema", "verifier integrity schema mismatch")
    gap = document["gap_leg"]
    if not _exact_keys(gap, {
        "workloads", "schedule_receipt", "builds", "performance_runs",
        "liveness_runs", "attestation", "attempts", "status",
    }):
        return EvidenceFailure("schema", "gap leg schema mismatch")
    if gap["status"] != "complete":
        return EvidenceFailure("schema", "terminal gap status is not complete")
    if (
        type(gap["workloads"]) is not list
        or any(not _exact_keys(item, {
            "id", "calibration_status", "argv",
        }) for item in gap["workloads"])
        or type(gap["builds"]) is not list
        or any(not _exact_keys(item, {
            "id", "trace", "macros", "identity_defined_count",
            "transaction_object_sha256", "activation_ok", "configure_argv",
            "build_argv", "binary_sha256", "compile_invocations",
            "cmake_cache_sha256", "source_sha256", "raw_paths", "dependencies",
        }) for item in gap["builds"])
        or type(gap["performance_runs"]) is not list
        or any(not _exact_keys(item, {
            "ordinal", "workload", "rep", "variant", "binary_id",
            "workload_argv", "argv", "started_at_utc",
            "completed_at_utc", "returncode", "throughput_tps",
            "commit_count", "batch_commit_count",
            "stdout_sha256", "stderr_sha256", "raw_path",
        }) for item in gap["performance_runs"])
        or type(gap["liveness_runs"]) is not list
        or any(not _exact_keys(item, {
            "ordinal", "workload", "rep", "variant", "binary_id",
            "workload_argv", "returncode", "bounded_completion",
            "commit_count", "batch_commit_count", "per_worker_commits",
            "per_worker_batch_commits", "argv", "started_at_utc",
            "completed_at_utc", "stdout_sha256", "stderr_sha256", "raw_path",
        }) for item in gap["liveness_runs"])
    ):
        return EvidenceFailure("schema", "gap run/build schema mismatch")
    for build in gap["builds"]:
        if (
            not _compile_invocations_complete(build["compile_invocations"])
            or any(not _exact_keys(item, {
                "source_rel", "argv", "object_path", "object_sha256",
                "replay_object_sha256", "replay_match",
            }) for item in build["compile_invocations"])
            or type(build["source_sha256"]) is not dict
            or set(build["source_sha256"]) != set(SOURCE_FILES)
            or not _valid_dependencies(build["dependencies"])
        ):
            return EvidenceFailure("schema", "build provenance schema mismatch")
    for run in gap["liveness_runs"]:
        if any(not _exact_keys(item, {"worker", "commits"})
               for item in run["per_worker_commits"] + run["per_worker_batch_commits"]):
            return EvidenceFailure("schema", "worker counter schema mismatch")
    attestation = gap["attestation"]
    if not _exact_keys(attestation, {
        "contract_sha256", "calibration_sha256", "cpu_model_match",
        "effective_clock_match", "cpuset_match", "ht_match", "numa_match",
        "per_sample_solo_checks", "all_pass",
    }):
        return EvidenceFailure("schema", "attestation schema mismatch")
    if (
        type(attestation["per_sample_solo_checks"]) is not list
        or len(attestation["per_sample_solo_checks"]) != 28
        or [item.get("ordinal") for item in attestation["per_sample_solo_checks"]]
        != list(range(28))
        or any(not _exact_keys(item, {
            "ordinal", "pgrep_returncode", "competing_processes", "load1",
            "load_threshold", "passed",
        }) for item in attestation["per_sample_solo_checks"])
    ):
        return EvidenceFailure("schema", "solo check schema mismatch")
    if (
        type(gap["attempts"]) is not list
        or any(not _exact_keys(item, {
            "attempt", "failure_class", "reason_code", "raw_root",
            "attempt_receipt_sha256", "job_id", "nonce",
            "submit_receipt_sha256", "campaign_attempt_root_receipt",
        }) for item in gap["attempts"])
        or any(
            not _exact_keys(item["campaign_attempt_root_receipt"], {
                "path", "sha256",
            })
            for item in gap["attempts"]
        )
    ):
        return EvidenceFailure("schema", "attempt schema mismatch")
    if not _exact_keys(document["retry_policy"], {
        "max_attempts", "infra_reason_codes", "substantive_negative_retried",
    }):
        return EvidenceFailure("schema", "retry policy schema mismatch")
    if not _exact_keys(document["raw_bundle"], {"root", "paths"}):
        return EvidenceFailure("schema", "raw bundle schema mismatch")
    raw_root = document["raw_bundle"]["root"]
    raw_paths = document["raw_bundle"]["paths"]
    if (
        type(raw_root) is not str or not raw_root
        or Path(raw_root).is_absolute() or ".." in Path(raw_root).parts
        or type(raw_paths) is not list
        or raw_paths != sorted(set(raw_paths))
        or any(
            type(item) is not str or not item or Path(item).is_absolute()
            or ".." in Path(item).parts
            for item in raw_paths
        )
    ):
        return EvidenceFailure("schema", "raw bundle relative paths are invalid")
    if not _exact_keys(document["checks"], {
        "correctness", "schedule", "per_worker_ever_committed",
        "bounded_completion", "performance_direction", "activation",
        "attestation", "raw_recomputed",
    }):
        return EvidenceFailure("schema", "checks schema mismatch")
    if any(type(value) is not bool for value in document["checks"].values()):
        return EvidenceFailure("schema", "check values must be bool")
    if type(document["all_pass"]) is not bool:
        return EvidenceFailure("schema", "all_pass must be bool")
    return None


def validate_evidence(document: Any) -> tuple[EvidenceFailure, ...]:
    """全 predicate を独立再計算し、表示用 check field は判定に使わない。"""
    schema_failure = _validate_schema(document)
    if schema_failure is not None:
        return (schema_failure,)
    failures = _validate_correctness(document["correctness_leg"])
    correctness_tools = {
        (item["name"], item["realpath"], item["version"], item["sha256"])
        for item in document["correctness_leg"]["provenance"]["tools"]
        if item["name"] in {"gcc", "g++"}
    }
    gap_tools = {
        (item["name"], item["realpath"], item["version"], item["sha256"])
        for item in document["provenance"]["tools"]
        if item["name"] in {"gcc", "g++"}
    }
    if correctness_tools != gap_tools:
        failures.append(EvidenceFailure(
            "correctness_activation",
            "correctness/gap toolchain identity differs",
        ))
    third_party_identity_keys = (
        "name", "source_name", "url", "fetchcontent_ref", "pin",
        "git_head_raw", "git_status_porcelain_raw", "clean",
    )
    correctness_third_party = {
        item["name"]: tuple(item[key] for key in third_party_identity_keys)
        for item in document["correctness_leg"]["provenance"][
            "third_party_sources"
        ]
    }
    gap_third_party = {
        item["name"]: tuple(item[key] for key in third_party_identity_keys)
        for item in document["provenance"]["third_party_sources"]
    }
    if correctness_third_party != gap_third_party:
        failures.append(EvidenceFailure(
            "correctness_activation",
            "correctness/gap third-party source identity differs",
        ))
    expected_patched = document["provenance"]["source_witness"][
        "expected_patched_source_sha256"
    ]
    if (
        document["correctness_leg"]["provenance"][
            "expected_patched_source_sha256"
        ] != expected_patched
        or document["correctness_leg"]["provenance"][
            "observed_patched_source_sha256"
        ] != expected_patched
    ):
        failures.append(EvidenceFailure(
            "correctness_activation",
            "correctness patched source differs from gap expected source",
        ))
    calibration = document["binding"]["calibration"]
    if (
        calibration["quality_status"] != "accepted"
        or calibration["records"] != 1_000_000
        or calibration["threads"] != 48
        or calibration["transfer_scope"] != [
            "build_contract", "records", "threads",
        ]
    ):
        failures.append(EvidenceFailure(
            "calibration_status", "registered calibration binding mismatch"
        ))
    gap = document["gap_leg"]
    schedule_failure = validate_schedule(gap["schedule_receipt"])
    if schedule_failure:
        failures.append(schedule_failure)
    liveness_failure = _validate_liveness(gap["liveness_runs"])
    if liveness_failure:
        failures.append(liveness_failure)
    bounded_failure = _validate_bounded_completion(gap["liveness_runs"])
    if bounded_failure:
        failures.append(bounded_failure)
    performance_failure = _validate_performance(gap["performance_runs"])
    if performance_failure:
        failures.append(performance_failure)
    workload_map = {item["id"]: item for item in gap["workloads"]}
    if workload_map != {
        name: {"id": name, **value} for name, value in WORKLOADS.items()
    }:
        failures.append(EvidenceFailure(
            "calibration_status", "per-workload calibration status mismatch"
        ))
    builds = gap["builds"]
    dependency_pins = _dependency_pins()
    gap_third_party_flags = _third_party_configure_flags(
        document["provenance"]["third_party_sources"]
    )
    build_by_id = {
        item["id"]: item for item in builds
        if type(item) is dict and set(item) == {
            "id", "trace", "macros", "identity_defined_count",
            "transaction_object_sha256", "activation_ok", "configure_argv",
            "build_argv", "binary_sha256", "compile_invocations",
            "cmake_cache_sha256", "source_sha256", "raw_paths", "dependencies",
        }
    }
    activation_ok = (
        len(builds) == 3
        and len({item["id"] for item in builds}) == 3
        and set(build_by_id) == {"stock", "rung-perf", "rung-liveness"}
        and build_by_id["stock"]["identity_defined_count"] == 0
        and build_by_id["stock"]["macros"] == []
        and build_by_id["rung-perf"]["identity_defined_count"] == 1
        and build_by_id["rung-perf"]["macros"] == [RUNG_MACRO]
        and build_by_id["rung-liveness"]["identity_defined_count"] == 1
        and build_by_id["rung-liveness"]["macros"] == [RUNG_MACRO, REPORT_MACRO]
        and all(item["trace"] is False and item["activation_ok"] is True
                for item in build_by_id.values())
        and all(
            f"-DIZANAGI_GFLAGS_SRC_HEAD={dependency_pins['gflags']}"
            in item["configure_argv"]
            and f"-DIZANAGI_GLOG_SRC_HEAD={dependency_pins['glog']}"
            in item["configure_argv"]
            and all(flag in item["configure_argv"]
                    for flag in gap_third_party_flags)
            for item in build_by_id.values()
        )
        and build_by_id["rung-perf"]["transaction_object_sha256"]
        == build_by_id["rung-liveness"]["transaction_object_sha256"]
        and build_by_id["rung-perf"]["source_sha256"]
        == document["provenance"]["source_witness"][
            "observed_patched_source_sha256"
        ]
        and build_by_id["rung-liveness"]["source_sha256"]
        == document["provenance"]["source_witness"][
            "observed_patched_source_sha256"
        ]
    )
    if not activation_ok:
        failures.append(EvidenceFailure("activation", "three-build witness failed"))
    attestation = gap["attestation"]
    if not _exact_keys(attestation, {
        "contract_sha256", "calibration_sha256", "cpu_model_match",
        "effective_clock_match", "cpuset_match", "ht_match", "numa_match",
        "per_sample_solo_checks", "all_pass",
    }) or (
        attestation.get("contract_sha256")
        != document["binding"]["calibration"]["contract_sha256"]
        or attestation.get("calibration_sha256")
        != document["binding"]["calibration"]["sha256"]
        or type(attestation.get("per_sample_solo_checks")) is not list
        or len(attestation["per_sample_solo_checks"]) != 28
        or [item.get("ordinal") for item in attestation["per_sample_solo_checks"]]
        != list(range(28))
    ) or attestation.get("all_pass") is not True or not all(
        attestation.get(key) is True for key in (
            "cpu_model_match", "effective_clock_match", "cpuset_match",
            "ht_match", "numa_match",
        )
    ) or any(item.get("passed") is not True for item in attestation.get(
        "per_sample_solo_checks", []
    )):
        failures.append(EvidenceFailure("attestation", "environment attestation failed"))
    retry = document["retry_policy"]
    attempts = gap["attempts"]
    substantive_indexes = [
        index for index, item in enumerate(attempts)
        if item.get("failure_class") == "substantive-negative"
    ] if type(attempts) is list else []
    attempt_numbers = [
        item.get("attempt") for item in attempts
    ] if type(attempts) is list else []
    if (
        retry["max_attempts"] != 2
        or set(retry["infra_reason_codes"]) != INFRA_REASON_CODES
        or retry["substantive_negative_retried"] is not False
        or type(attempts) is not list or not 1 <= len(attempts) <= 2
        or attempt_numbers not in ([1], [1, 2])
        or attempts[-1].get("failure_class") is not None
        or attempts[-1].get("reason_code") is not None
        or gap.get("status") != "complete"
        or (
            attempt_numbers == [1, 2]
            and (
                attempts[0].get("failure_class") != "infra"
                or attempts[0].get("reason_code") not in INFRA_REASON_CODES
            )
        )
        or any(
            item.get("failure_class") not in (
                None, "infra", "substantive-negative", "contract",
            )
            or (
                item.get("failure_class") == "infra"
                and item.get("reason_code") not in INFRA_REASON_CODES
            )
            for item in attempts
        )
        or any(
            type(item.get("attempt_receipt_sha256")) is not str
            or _HEX64.fullmatch(item["attempt_receipt_sha256"]) is None
            for item in attempts
        )
        or len(substantive_indexes) > 1
        or (
            substantive_indexes
            and substantive_indexes[0] != len(attempts) - 1
        )
    ):
        failures.append(EvidenceFailure("retry_policy", "attempt policy mismatch"))
    paths = document["raw_bundle"]["paths"]
    if (
        type(paths) is not list or not paths
        or any(type(path) is not str or path.startswith("/") or ".." in Path(path).parts
               for path in paths)
        or not any("schedule" in path for path in paths)
        or not any("compile_commands" in path for path in paths)
        or not any("verifier" in path for path in paths)
        or not any("accounting" in path for path in paths)
    ):
        failures.append(EvidenceFailure("raw_bundle", "raw relative path set is incomplete"))
    return tuple(failures)


def publish_create_only_json(
    destination: Path, document: Mapping[str, Any], *, staging_dir: Path | None = None,
) -> Path:
    """staging fsync → create-only hardlink → destination dir fsync。"""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage_parent = Path(staging_dir) if staging_dir else destination.parent
    stage_parent.mkdir(parents=True, exist_ok=True)
    if os.stat(stage_parent).st_dev != os.stat(destination.parent).st_dev:
        raise DriverError("staging and destination must be on the same filesystem")
    payload = (
        json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    ).encode("utf-8")
    fd, name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".staging", dir=stage_parent,
    )
    staged = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(staged, destination)
        except FileExistsError as exc:
            raise DriverError(f"destination already exists: {destination}") from exc
        dir_fd = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        staged.unlink(missing_ok=True)
    return destination


def _load_json(path: Path) -> Any:
    def no_duplicates(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ContractFailure(f"duplicate JSON key {key!r} in {path}")
            result[key] = value
        return result

    try:
        with Path(path).open(encoding="utf-8") as handle:
            value = json.load(handle, object_pairs_hook=no_duplicates)
            if handle.read():
                raise ContractFailure(f"trailing bytes after JSON document: {path}")
            return value
    except ContractFailure:
        raise
    except (OSError, json.JSONDecodeError, UnicodeError) as exc:
        raise DriverError(f"cannot load JSON {path}: {exc}") from exc


def _write_raw_json(path: Path, document: Mapping[str, Any]) -> None:
    publish_create_only_json(path, document, staging_dir=path.parent)


def _create_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(value)
        handle.flush()
        os.fsync(handle.fileno())


def _copy_raw(source: Path, destination: Path) -> None:
    if source.is_symlink() or not source.is_file():
        raise DriverError(f"raw source must be a non-symlink regular file: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as src, destination.open("xb") as dst:
        shutil.copyfileobj(src, dst)
        dst.flush()
        os.fsync(dst.fileno())


def _expected_patched_source_hashes(
    base: Path, patch: Path, raw: Path | None = None,
) -> dict[str, str]:
    """pin blobs + patch bytes だけから期待 patched source SHA を独立計算する。"""
    _snapshot, immutable_hashes = _pinned_patched_source_model(
        os.path.realpath(base), PIN, patch.read_bytes(),
    )
    result = dict(immutable_hashes)
    if raw is not None:
        _write_raw_json(raw / "expected-patched-source-sha256.json", result)
    return result


@functools.lru_cache(maxsize=4)
def _pinned_patched_source_model(
        base: str, pin: str, patch_bytes: bytes,
) -> tuple[Any, tuple[tuple[str, str], ...]]:
    """Build one immutable Silo source snapshot from Git objects, never checkout.

    The exact ``pin`` subtree is exported to a disposable directory and the
    frozen patch is applied only to that copy.  The result is cached by Git
    repository, full pin, and exact patch bytes so repeated raw validation in
    one process does not repeat archive extraction or patch application.
    """
    from orchestrator.verifier.model import (
        capture_compiled_protocol_source_snapshot,
    )

    try:
        archived = subprocess.run(
            ["git", "-C", base, "archive", "--format=tar", pin, "cc/silo"],
            env=scrub_environment(), capture_output=True, timeout=60,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise DriverError(f"cannot archive pinned Silo source: {exc}") from exc
    if archived.returncode != 0:
        detail = archived.stderr.decode("utf-8", errors="replace").strip()[-500:]
        raise DriverError(
            f"cannot archive pinned Silo source: rc={archived.returncode}: {detail}"
        )

    with tempfile.TemporaryDirectory(prefix="rung1-pinned-source-") as temp:
        model = Path(temp)
        try:
            with tarfile.open(
                fileobj=io.BytesIO(archived.stdout), mode="r:",
            ) as tar:
                for member in tar.getmembers():
                    relative = Path(member.name)
                    if (relative.is_absolute()
                            or ".." in relative.parts
                            or member.issym()
                            or member.islnk()):
                        raise DriverError(
                            f"unsafe path in pinned Silo archive: {member.name}"
                        )
                    target = model / relative
                    if member.isdir():
                        target.mkdir(parents=True, exist_ok=True)
                        continue
                    if not member.isfile():
                        raise DriverError(
                            f"non-file in pinned Silo archive: {member.name}"
                        )
                    source = tar.extractfile(member)
                    if source is None:
                        raise DriverError(
                            f"cannot read pinned Silo archive member: {member.name}"
                        )
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with source, target.open("xb") as destination:
                        shutil.copyfileobj(source, destination)
            applied = subprocess.run(
                ["git", "apply", "--whitespace=nowarn", "-"],
                cwd=model, input=patch_bytes, env=scrub_environment(),
                capture_output=True, timeout=60, check=False,
            )
        except (OSError, subprocess.SubprocessError, tarfile.TarError) as exc:
            raise DriverError(
                f"cannot materialize pinned patched Silo source: {exc}"
            ) from exc
        if applied.returncode != 0:
            detail = applied.stderr.decode(
                "utf-8", errors="replace",
            ).strip()[-500:]
            raise DriverError(
                "cannot apply frozen patch to pinned Silo source copy: "
                f"rc={applied.returncode}: {detail}"
            )
        snapshot = capture_compiled_protocol_source_snapshot("silo", model)
        if snapshot.normalized_sources is None:
            raise DriverError("pinned patched Silo proof source is unavailable")
        hashes = tuple(
            (relative, sha256_file(model / relative))
            for relative in SOURCE_FILES
        )
    return snapshot, hashes


def _solo_check(
    raw: Path, ordinal: int, *, deadline: Deadline | None = None,
) -> dict[str, Any]:
    pgrep = _run(
        ["pgrep", "-a", "-f", r"ycsb_.*\.exe"],
        timeout=30, deadline=deadline,
    )
    _create_text(raw / f"solo-{ordinal:02d}.pgrep.stdout", pgrep.stdout)
    _create_text(raw / f"solo-{ordinal:02d}.pgrep.stderr", pgrep.stderr)
    if pgrep.returncode not in (0, 1):
        raise InfraFailure(
            "nonzero_returncode", f"pgrep probe failed: rc={pgrep.returncode}",
        )
    competitors = [line for line in pgrep.stdout.splitlines() if line.strip()]
    load1, load5, load15 = os.getloadavg()
    policy = _load_json(_repo_root() / "tools/pegasus/policy.json")[
        "silo_ladder_rung1"
    ]
    load_threshold = policy["solo_load1_threshold"]
    if type(load_threshold) not in (int, float) or load_threshold <= 0:
        raise ContractFailure("policy solo_load1_threshold is invalid")
    _write_raw_json(raw / f"solo-{ordinal:02d}.load.json", {
        "load1": load1, "load5": load5, "load15": load15,
    })
    return {
        "ordinal": ordinal,
        "pgrep_returncode": pgrep.returncode,
        "competing_processes": competitors,
        "load1": load1,
        "load_threshold": load_threshold,
        "passed": (
            pgrep.returncode == 1
            and not competitors
            and load1 <= load_threshold
        ),
    }


def _attest_environment(
    raw: Path, *, deadline: Deadline | None = None,
) -> dict[str, Any]:
    repo = _repo_root()
    contract = env_contract.lookup("pegasus")
    calibration_path = repo / contract.calibration_ref.path
    try:
        verified = env_attestation.load_verified_calibration(contract, repo)
    except env_attestation.AttestationError as exc:
        raise DriverError(f"registered calibration admission failed: {exc}") from exc
    if verified.calibration is None:
        raise DriverError("registered calibration has no attestation profile")
    probe_path = raw / "attestation-job.json"
    probe = _run(
        [sys.executable, str(repo / "tools/pegasus/run_probe.py"),
         "--output", str(probe_path)],
        cwd=repo, timeout=120, deadline=deadline,
        stdout_path=raw / "attestation-job.stdout",
        stderr_path=raw / "attestation-job.stderr",
    )
    if probe.returncode != 0:
        raise InfraFailure(
            "nonzero_returncode",
            f"environment attestation probe rc={probe.returncode}",
        )
    try:
        parsed_probe = env_attestation.parse_probe_output(probe_path.read_bytes())
    except (OSError, env_attestation.AttestationError) as exc:
        raise InfraFailure(
            "parse_failure", f"attestation JSON parse failed: {exc}",
        ) from exc
    if not parsed_probe.ok or parsed_probe.profile is None:
        raise InfraFailure("attestation", "environment attestation probe is not ok")
    actual = env_attestation.observed_profile_to_dict(parsed_probe.profile)
    expected = env_attestation.profile_to_dict(verified.attestation_profile)
    expected_clock = {
        "samples_mhz": list(expected["effective_clock"]["samples_mhz"]),
        "tolerance_pct": expected["effective_clock"]["tolerance_pct"],
    }
    observed_clock = {
        "samples_mhz": list(actual["effective_clock"]["samples_mhz"]),
    }
    clock_match = execution_guard.effective_clock_comparison_passes(
        expected_clock, observed_clock,
    )
    result = {
        "contract_sha256": contract.contract_sha256,
        "calibration_sha256": contract.calibration_ref.sha256,
        "cpu_model_match": actual["cpu"]["model_name_normalized"]
        == expected["cpu"]["model_name_normalized"],
        "effective_clock_match": (
            clock_match
            and actual["effective_clock"]["method"]
            == expected["effective_clock"]["method"]
            and actual["effective_clock"]["governor"]
            == expected["effective_clock"]["governor"]
        ),
        "cpuset_match": (
            actual["cores"]["affinity_visible"] == 48
            and actual["cores"]["physical"] == 48
            and verified.calibration.acquisition_receipt.allocation.cpuset_size == 48
        ),
        "ht_match": (
            actual["cores"]["smt_active"] is False
            and verified.calibration.acquisition_receipt.allocation.ht_off is True
        ),
        "numa_match": actual["numa"] == expected["numa"],
        "per_sample_solo_checks": [],
        "all_pass": False,
    }
    result["all_pass"] = all(result[key] is True for key in (
        "cpu_model_match", "effective_clock_match", "cpuset_match",
        "ht_match", "numa_match",
    ))
    if not result["all_pass"]:
        raise InfraFailure(
            "attestation", f"environment attestation mismatch: {result}",
        )
    return result


def _configure_argv(
    *, source: Path, build: Path, tools: Mapping[str, str],
    prefix: str, macros: Sequence[str], trace: int,
    third_party_sources: Sequence[Mapping[str, Any]],
) -> list[str]:
    flags = " ".join(f"-D{macro}=1" for macro in macros)
    dependency_pins = _dependency_pins()
    return [
        tools["cmake"], "-S", str(source), "-B", str(build),
        "-DCMAKE_BUILD_TYPE=Release", "-DENABLE_SANITIZER=OFF",
        f"-DCCBENCH_TRACE={trace}", "-DCCBENCH_BACK_OFF=0",
        "-DCCBENCH_BACKOFF_FIXED=-1",
        "-DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1",
        "-DCCBENCH_NO_WAIT_OF_TICTOC=0", "-DCCBENCH_WAL=0",
        "-DCCBENCH_CCACHE=OFF", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        "-DCMAKE_C_COMPILER_LAUNCHER=", "-DCMAKE_CXX_COMPILER_LAUNCHER=",
        "-DRULE_LAUNCH_COMPILE=", "-DCMAKE_TOOLCHAIN_FILE=",
        f"-DCMAKE_PREFIX_PATH={prefix}",
        f"-DIZANAGI_GFLAGS_SRC_HEAD={dependency_pins['gflags']}",
        f"-DIZANAGI_GLOG_SRC_HEAD={dependency_pins['glog']}",
        *_third_party_configure_flags(third_party_sources),
        f"-DCMAKE_C_COMPILER={tools['gcc']}",
        f"-DCMAKE_CXX_COMPILER={tools['g++']}",
        f"-DCMAKE_CXX_FLAGS={flags}",
    ]


def _require_condition_gates(
    *,
    patched_source: Path,
    stock_source: Path,
    tools: Mapping[str, str],
    configure_argv: Sequence[str],
) -> list[dict[str, Any]]:
    if len(configure_argv) < 5 or tuple(configure_argv[:4]) != (
        tools["cmake"], "-S", str(patched_source), "-B",
    ):
        raise DriverError("condition gate configure argv has an unexpected prefix")
    tail = tuple(configure_argv[5:])
    fixed_values = [
        argument.split("=", 1)[1]
        for argument in tail
        if argument.startswith("-DCCBENCH_BACKOFF_FIXED=")
    ]
    if fixed_values != ["-1"]:
        raise DriverError(
            "condition gate requires the actual BACKOFF_FIXED=-1 configure value"
        )
    cxx_flags = [
        argument.split("=", 1)[1]
        for argument in tail if argument.startswith("-DCMAKE_CXX_FLAGS=")
    ]
    if len(cxx_flags) != 1:
        raise DriverError("condition gate requires one CMAKE_CXX_FLAGS value")
    actual_cxx_defines: dict[str, int] = {}
    for token in shlex.split(cxx_flags[0]):
        if not token.startswith("-D"):
            continue
        name, separator, value = token[2:].partition("=")
        if name in {RUNG_MACRO, REPORT_MACRO}:
            try:
                actual_cxx_defines[name] = int(value if separator else "1")
            except ValueError as exc:
                raise DriverError(
                    f"condition gate macro value is not an integer: {token}"
                ) from exc
    declared_requests = {
        RUNG_MACRO: (RUNG_MACRO, 1, 0, False),
        REPORT_MACRO: (REPORT_MACRO, 1, 0, False),
    }
    requests = [("BACKOFF_FIXED", -1, None, True)]
    for macro, requested in actual_cxx_defines.items():
        declared = declared_requests[macro]
        if requested != declared[1]:
            raise DriverError(
                f"condition gate request differs from actual {macro}={requested}"
            )
        requests.append(declared)
    supply_records = []
    meaning_records = []
    for macro, requested, default, stock_comparison in requests:
        companion_names = {
            name for name, _value
            in condition_meaning_gate.DEFINE_SPECS[macro].companion_defines
        }
        configure_args = []
        for argument in tail:
            if macro == "BACKOFF_FIXED" \
                    and argument.startswith("-DCCBENCH_BACKOFF_FIXED="):
                continue
            if argument.startswith("-DCMAKE_CXX_FLAGS="):
                kept = []
                for token in shlex.split(argument.split("=", 1)[1]):
                    name = token[2:].partition("=")[0] \
                        if token.startswith("-D") else None
                    if name == macro or name in companion_names:
                        continue
                    kept.append(token)
                configure_args.append("-DCMAKE_CXX_FLAGS=" + " ".join(kept))
            else:
                configure_args.append(argument)
        captured = condition_meaning_gate.capture_define_inputs(
            patched_source,
            stock_root=stock_source,
            configure_args=tuple(configure_args),
        )
        request = condition_meaning_gate.make_define_request(
            driver_id="orchestrator.campaign.silo_ladder_rung1",
            macro=macro,
            requested_value=requested,
            default_value=default,
            stock_comparison=stock_comparison,
        )
        supply_records.append(
            condition_meaning_gate.evaluate_define_supply_effectuation(
                captured,
                request=request,
                cxx=tools["g++"],
                cmake=tools["cmake"],
            )
        )
        meaning_records.append(
            condition_meaning_gate.evaluate_define_runtime_meaning(
                captured,
                request=request,
                declaration=None,
                cxx=tools["g++"],
            )
        )
    admission = condition_meaning_gate.require_condition_gate_family(
        supply_records, meaning_records, use_class="raw-measurement",
    )
    if not admission.admitted:
        states = ", ".join(
            f"{record.macro}={record.terminal_status}/{record.reason_code}"
            for record in (*supply_records, *meaning_records)
        )
        raise DriverError(f"condition gate rejected rung1 driver: {states}")
    return [
        *(json.loads(record.canonical_json()) for record in supply_records),
        *(json.loads(record.canonical_json()) for record in meaning_records),
        json.loads(admission.canonical_json()),
    ]


def _dependency_contract() -> list[dict[str, Any]]:
    source_root = Path(os.environ.get(THIRD_PARTY_SOURCE_ROOT_ENV)
                       or _repo_root() / THIRD_PARTY_STAGING_RELATIVE)
    pins = _dependency_pins()
    records = []
    for name, variable in (
        ("gflags", "IZANAGI_GFLAGS_INSTALL"),
        ("glog", "IZANAGI_GLOG_INSTALL"),
    ):
        pin = pins[name]
        value = os.environ.get(variable)
        if not value:
            raise ContractFailure(f"missing dependency prefix: {variable}")
        path = Path(value).resolve(strict=True)
        if not path.is_dir():
            raise ContractFailure(f"dependency prefix is not a directory: {path}")
        source = (source_root / name).resolve(strict=True)
        head = _run([
            "git", "-C", str(source), "rev-parse", "--verify", "HEAD",
        ])
        status = _run([
            "git", "-C", str(source), "status", "--porcelain",
            "--untracked-files=all",
        ])
        if (
            head.returncode != 0
            or head.stdout.strip() != pin
            or status.returncode != 0
            or status.stdout
        ):
            raise ContractFailure(f"{name} dependency is not pinned-clean")
        records.append({
            "name": name,
            "resolved_path": str(path),
            "pin": pin,
            "git_head_raw": head.stdout,
            "git_status_porcelain_raw": status.stdout,
        })
    return records


def _validate_cmake_cache(
    path: Path, *, expected_c: str, expected_cxx: str,
    expected_flags: str, expected_trace: str,
) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="strict")
    selected: dict[str, str] = {}
    for line in text.splitlines():
        if not line or line.startswith(("#", "//")) or "=" not in line:
            continue
        left, value = line.split("=", 1)
        key = left.split(":", 1)[0]
        selected[key] = value
    exact = {
        "CCBENCH_CCACHE": "OFF",
        "CCBENCH_TRACE": expected_trace,
        "CMAKE_C_COMPILER": expected_c,
        "CMAKE_CXX_COMPILER": expected_cxx,
        "CMAKE_CXX_FLAGS": expected_flags,
    }
    for key, expected in exact.items():
        if selected.get(key) != expected:
            raise DriverError(
                f"CMakeCache {key} mismatch: {selected.get(key)!r} != {expected!r}"
            )
    empty = (
        "CMAKE_C_COMPILER_LAUNCHER", "CMAKE_CXX_COMPILER_LAUNCHER",
        "CMAKE_TOOLCHAIN_FILE", "CMAKE_PROJECT_INCLUDE",
        "CMAKE_PROJECT_INCLUDE_BEFORE", "CMAKE_PROJECT_TOP_LEVEL_INCLUDES",
        "RULE_LAUNCH_COMPILE",
    )
    for key in empty:
        if selected.get(key, ""):
            raise DriverError(f"CMakeCache injection channel is non-empty: {key}")
    return {key: selected.get(key, "") for key in (*exact, *empty)}


def _build_variant(
    *, variant: str, source: Path, build: Path, raw: Path,
    tool_paths: Mapping[str, str], prefix: str, macros: Sequence[str],
    deadline: Deadline, third_party_sources: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], Path]:
    if build.exists():
        raise DriverError(f"build directory is not fresh: {build}")
    build_raw = raw / f"build-{variant}"
    build_raw.mkdir()
    configure = _configure_argv(
        source=source, build=build, tools=tool_paths, prefix=prefix,
        macros=macros, trace=0, third_party_sources=third_party_sources,
    )
    configured = _run(
        configure, timeout=900, deadline=deadline,
        stdout_path=build_raw / "configure.stdout",
        stderr_path=build_raw / "configure.stderr",
    )
    if configured.returncode != 0:
        raise InfraFailure(
            "nonzero_returncode",
            f"{variant} configure rc={configured.returncode}",
        )
    build_argv = [
        tool_paths["cmake"], "--build", str(build), "--target",
        "ycsb_silo.exe", "--verbose", "-j", "48",
    ]
    built = _run(
        build_argv,
        timeout=2700, deadline=deadline, stdout_path=build_raw / "build.stdout",
        stderr_path=build_raw / "build.stderr",
    )
    if built.returncode != 0:
        raise InfraFailure(
            "nonzero_returncode",
            f"{variant} build rc={built.returncode}",
        )
    cache = build / "CMakeCache.txt"
    commands_path = build / "compile_commands.json"
    expected_flags = " ".join(f"-D{macro}=1" for macro in macros)
    selected_cache = _validate_cmake_cache(
        cache, expected_c=tool_paths["gcc"], expected_cxx=tool_paths["g++"],
        expected_flags=expected_flags, expected_trace="0",
    )
    _copy_raw(cache, build_raw / "CMakeCache.txt")
    _copy_raw(commands_path, build_raw / "compile_commands.json")
    commands = _load_json(commands_path)
    invocations = compile_commands_for_sources(commands, source)
    replayed = []
    active_macros: set[str] = set()
    for invocation in invocations:
        active_macros.update(validate_compile_argv(
            invocation["argv"],
            expected_macro=None if variant == "stock" else RUNG_MACRO,
            require_report=variant == "rung-liveness",
            expected_compiler_realpath=tool_paths["g++"],
        ))
        replayed.append(reexecute_compile_and_compare(
            invocation, deadline=deadline,
        ))
    _write_raw_json(build_raw / "compile-replay.json", {"invocations": replayed})
    _write_raw_json(build_raw / "cmake-cache-witness.json", {
        "sha256": sha256_file(cache),
        "selected_entries": selected_cache,
    })
    transaction = next(
        item for item in replayed if item["source_rel"] == SOURCE_FILES[0]
    )
    binary = build / "cc/silo/ycsb_silo.exe"
    nm_binary = _run(
        [tool_paths["nm"], "-g", "--defined-only", str(binary)],
        receipt_path=build_raw / "binary.nm.command.json",
        target_path=binary,
    )
    _create_text(build_raw / "binary.nm.txt", nm_binary.stdout)
    _create_text(build_raw / "binary.nm.stderr", nm_binary.stderr)
    if nm_binary.returncode != 0:
        raise InfraFailure(
            "nonzero_returncode", f"{variant} binary nm failed",
        )
    readelf = _run(
        [tool_paths["readelf"], "-Ws", str(binary)], timeout=60,
        receipt_path=build_raw / "binary.readelf.command.json",
        target_path=binary,
    )
    _create_text(build_raw / "binary.readelf.txt", readelf.stdout)
    _create_text(build_raw / "binary.readelf.stderr", readelf.stderr)
    if readelf.returncode != 0:
        raise InfraFailure(
            "nonzero_returncode", f"{variant} readelf failed",
        )
    transaction_nm = _run(
        [tool_paths["nm"], "-g", "--defined-only", transaction["object_path"]],
        receipt_path=build_raw / "transaction.nm.command.json",
        target_path=Path(transaction["object_path"]),
    )
    _create_text(build_raw / "transaction.nm.txt", transaction_nm.stdout)
    _create_text(build_raw / "transaction.nm.stderr", transaction_nm.stderr)
    if transaction_nm.returncode != 0:
        raise InfraFailure(
            "nonzero_returncode",
            f"{variant} transaction object nm failed",
        )
    identity_count = sum(
        line.split()[-1] == IDENTITY_SYMBOL
        for line in nm_binary.stdout.splitlines() if line.split()
    )
    object_identity_count = sum(
        line.split()[-1] == IDENTITY_SYMBOL
        for line in transaction_nm.stdout.splitlines() if line.split()
    )
    expected_count = 0 if variant == "stock" else 1
    trace_symbols = sum("izanagi_trace" in line for line in nm_binary.stdout.splitlines())
    activation_ok = (
        identity_count == expected_count
        and object_identity_count == expected_count
        and trace_symbols == 0
    )
    if not activation_ok:
        raise DriverError(f"{variant} nm/trace activation witness failed")
    record = {
        "id": variant,
        "trace": False,
        "macros": [
            macro for macro in (RUNG_MACRO, REPORT_MACRO)
            if macro in active_macros
        ],
        "identity_defined_count": identity_count,
        "transaction_object_sha256": transaction["object_sha256"],
        "activation_ok": True,
        "configure_argv": configure,
        "build_argv": build_argv,
        "binary_sha256": sha256_file(binary),
        "compile_invocations": replayed,
        "cmake_cache_sha256": sha256_file(cache),
        "source_sha256": {
            relative: sha256_file(source / relative) for relative in SOURCE_FILES
        },
        "dependencies": _dependency_contract(),
        "raw_paths": [
            path.relative_to(raw).as_posix()
            for path in sorted(build_raw.rglob("*")) if path.is_file()
        ],
    }
    return record, binary


def _validate_submit_binding(
    submit: Mapping[str, Any], *, attempt_number: int, repo: Path,
) -> Mapping[str, Any]:
    expected_top = {
        "schema_version", "nonce", "source_commit", "whole_tree_clean",
        "attempt_number", "prior_gap_result_sha256", "prior_attempt",
        "bindings", "request", "qsub", "preflight", "schedule_receipt",
        "submitted_epoch", "dry_run", "campaign_id",
        "campaign_root_receipt", "submission_cwd",
    }
    if not _exact_keys(submit, expected_top):
        raise DriverError("submit receipt top-level schema mismatch")
    if (
        submit["schema_version"] != "silo_ladder_rung1-submit-receipt/v1"
        or submit["dry_run"] is not False
        or submit["whole_tree_clean"] is not True
        or submit["nonce"] != os.environ.get("IZANAGI_SUBMISSION_NONCE")
        or submit["attempt_number"] != attempt_number
        or type(submit["campaign_id"]) is not str
        or _HEX64.fullmatch(submit["campaign_id"]) is None
    ):
        raise DriverError("submit receipt identity mismatch")
    if attempt_number == 1 and submit["prior_gap_result_sha256"] is not None:
        raise DriverError("attempt 1 receipt unexpectedly binds a prior result")
    if attempt_number == 1 and submit["prior_attempt"] is not None:
        raise DriverError("attempt 1 receipt unexpectedly embeds a prior attempt")
    if (
        attempt_number == 2
        and (
            type(submit["prior_gap_result_sha256"]) is not str
            or _HEX64.fullmatch(submit["prior_gap_result_sha256"]) is None
        )
    ):
        raise DriverError("attempt 2 receipt lacks prior infra result hash")
    if attempt_number == 2 and (
        not _exact_keys(submit["prior_attempt"], {
            "attempt", "failure_class", "reason_code", "raw_root",
            "attempt_receipt_sha256", "job_id", "nonce",
            "submit_receipt_sha256", "campaign_attempt_root_receipt",
        })
        or submit["prior_attempt"]["attempt"] != 1
        or submit["prior_attempt"]["failure_class"] != "infra"
        or submit["prior_attempt"]["reason_code"] not in INFRA_REASON_CODES
    ):
        raise DriverError("attempt 2 prior attempt summary is invalid")
    if attempt_number == 2:
        prior_root = Path(submit["prior_attempt"]["raw_root"])
        if prior_root.is_absolute() or ".." in prior_root.parts:
            raise DriverError("prior attempt raw root is not repo-relative")
        validate_attempt_subtree(repo / prior_root, 1)
        try:
            prior_result_path = repo / prior_root.parents[1] / "gap-result.json"
        except IndexError as exc:
            raise DriverError("prior attempt raw root is too shallow") from exc
        if (
            not prior_result_path.is_file()
            or prior_result_path.is_symlink()
            or sha256_file(prior_result_path)
            != submit["prior_gap_result_sha256"]
        ):
            raise DriverError("prior attempt result hash/path binding mismatch")
        prior_result = _load_json(prior_result_path)
        if (
            prior_result.get("attempt_number") != 1
            or prior_result.get("status") != "infra-failure"
            or prior_result.get("reason_code")
            != submit["prior_attempt"]["reason_code"]
            or prior_result.get("schedule_receipt")
            != submit["schedule_receipt"]
        ):
            raise DriverError("prior infra attempt content/schedule mismatch")
        seal_ref = submit["prior_attempt"]["campaign_attempt_root_receipt"]
        if (
            not _exact_keys(seal_ref, {"path", "sha256"})
            or Path(seal_ref["path"]).is_absolute()
            or ".." in Path(seal_ref["path"]).parts
        ):
            raise DriverError("prior campaign attempt root reference is invalid")
        seal_path = repo / seal_ref["path"]
        seal = _load_json(seal_path)
        if (
            sha256_file(seal_path) != seal_ref["sha256"]
            or seal.get("schema_version")
            != "silo_ladder_rung1-campaign-attempt-root/v1"
            or seal.get("campaign_id") != submit["campaign_id"]
            or seal.get("attempt") != 1
            or seal.get("job_id") != submit["prior_attempt"]["job_id"]
            or seal.get("nonce") != submit["prior_attempt"]["nonce"]
            or seal.get("submit_receipt_sha256")
            != submit["prior_attempt"]["submit_receipt_sha256"]
            or seal.get("attempt_receipt_sha256")
            != submit["prior_attempt"]["attempt_receipt_sha256"]
            or seal.get("failure_class") != "infra"
            or seal.get("reason_code") != submit["prior_attempt"]["reason_code"]
        ):
            raise DriverError("prior campaign attempt root receipt mismatch")
    head = _run(["git", "-C", str(repo), "rev-parse", "--verify", "HEAD"])
    if head.returncode != 0 or submit["source_commit"] != head.stdout.strip():
        raise DriverError("submit receipt source commit mismatch")
    request = submit["request"]
    policy = _load_json(repo / "tools/pegasus/policy.json")["silo_ladder_rung1"]
    if request != {
        "project": policy["project"],
        "queue": policy["queue"],
        "nodes": policy["nodes"],
        "elapstim_req_s": policy["walltime_s"],
    }:
        raise DriverError("submit request differs from rung1 policy")
    qsub = submit["qsub"]
    if not _exact_keys(qsub, {
        "request_id", "rc", "stdout_raw", "stderr_raw", "qstat_rc",
        "qstat_stdout_raw", "qstat_stderr_raw",
    }):
        raise DriverError("submit qsub receipt schema mismatch")
    if (
        qsub["rc"] != 0 or qsub["qstat_rc"] != 0
        or _normalize_job_id(qsub["request_id"])
        != _normalize_job_id(os.environ["PBS_JOBID"])
        or not qsub["qstat_stdout_raw"]
    ):
        raise DriverError("qsub/qstat immediate visibility binding mismatch")
    preflight = submit["preflight"]
    if (
        not _exact_keys(preflight, {
            "qstat_Q", "pegasusinfo", "rbudgetcheck", "check_quota",
        })
        or any(
            not _exact_keys(capture, {"rc", "stdout_raw", "stderr_raw"})
            or type(capture["rc"]) is not int
            or type(capture["stdout_raw"]) is not str
            or type(capture["stderr_raw"]) is not str
            for capture in preflight.values()
        )
        or any(capture["rc"] != 0 for capture in preflight.values())
    ):
        raise DriverError("submit preflight receipt schema/status mismatch")
    bindings = submit["bindings"]
    if not _exact_keys(bindings, {
        "job_script_sha256", "driver_sha256", "patch_sha256",
        "ledger_sha256", "correctness_sha256", "schedule_sha256",
        "submitter_sha256", "verifier_module_sha256", "policy_sha256",
        "runtime_modules_sha256", "third_party_heads",
    }):
        raise DriverError("submit binding hash schema mismatch")
    expected_third_party_heads = {
        item["name"]: item["pin"] for item in third_party_policy(repo)
    }
    if bindings["third_party_heads"] != expected_third_party_heads:
        raise ContractFailure("submit third-party HEAD binding mismatch")
    current = {
        "job_script_sha256": sha256_file(
            repo / "tools/pegasus/silo_ladder_rung1.sh"
        ),
        "driver_sha256": sha256_file(Path(__file__).resolve()),
        "patch_sha256": sha256_file(repo / patch_contract.PATCH_PATH),
        "ledger_sha256": sha256_file(repo / "patches/ledger.json"),
        "submitter_sha256": sha256_file(
            repo / "tools/pegasus/submit_silo_ladder_rung1.sh"
        ),
        "verifier_module_sha256": sha256_file(
            repo / "orchestrator/verifier/report.py"
        ),
        "policy_sha256": sha256_file(repo / "tools/pegasus/policy.json"),
        "runtime_modules_sha256": runtime_modules_sha256(repo),
    }
    if any(bindings[key] != value for key, value in current.items()):
        raise DriverError("submit receipt source bytes mismatch")
    schedule_bytes = (
        json.dumps(
            submit["schedule_receipt"], ensure_ascii=False,
            sort_keys=True, indent=2,
        ) + "\n"
    ).encode("utf-8")
    if bindings["schedule_sha256"] != sha256_bytes(schedule_bytes):
        raise DriverError("submit receipt schedule bytes mismatch")
    if (
        type(bindings["correctness_sha256"]) is not str
        or _HEX64.fullmatch(bindings["correctness_sha256"]) is None
    ):
        raise DriverError("correctness binding hash is invalid")
    if (
        not _exact_keys(submit["submission_cwd"], {
            "caller", "repo_root_realpath", "qsub_cwd_realpath",
        })
        or submit["submission_cwd"]["repo_root_realpath"]
        != str(repo.resolve())
        or submit["submission_cwd"]["qsub_cwd_realpath"]
        != str(repo.resolve())
    ):
        raise ContractFailure("submission cwd/repo realpath binding mismatch")
    campaign_ref = submit["campaign_root_receipt"]
    if not _exact_keys(campaign_ref, {"path", "sha256"}):
        raise ContractFailure("campaign root receipt reference schema mismatch")
    if (
        type(campaign_ref["path"]) is not str
        or Path(campaign_ref["path"]).is_absolute()
        or ".." in Path(campaign_ref["path"]).parts
    ):
        raise ContractFailure("campaign root receipt path is not confined")
    campaign_path = repo / campaign_ref["path"]
    if (
        not campaign_path.is_file()
        or campaign_path.is_symlink()
        or sha256_file(campaign_path) != campaign_ref["sha256"]
    ):
        raise ContractFailure("campaign root receipt hash/path mismatch")
    campaign = _load_json(campaign_path)
    if (
        campaign.get("schema_version") != "silo_ladder_rung1-campaign-root/v1"
        or campaign.get("campaign_id") != submit["campaign_id"]
        or campaign.get("first_attempt") != 1
        or campaign.get("attempt_chain") != [1, 2]
        or campaign.get("schedule_receipt") != submit["schedule_receipt"]
        or campaign.get("bindings", {}).get("schedule_sha256")
        != bindings["schedule_sha256"]
    ):
        raise ContractFailure("campaign root receipt content mismatch")
    if attempt_number == 2:
        prior = submit["prior_attempt"]
        prior_seal = repo / prior["campaign_attempt_root_receipt"]["path"]
        expected_prior_seal = (
            campaign_path.parent / "attempt-1" / "attempt-root-receipt.json"
        )
        prior_submit = repo / prior["raw_root"] / "submit-receipt.json"
        prior_submit_document = _load_json(prior_submit)
        if (
            prior_seal.resolve() != expected_prior_seal.resolve()
            or sha256_file(prior_submit) != prior["submit_receipt_sha256"]
            or prior_submit_document.get("campaign_id") != submit["campaign_id"]
            or prior_submit_document.get("nonce") != prior["nonce"]
            or _normalize_job_id(
                prior_submit_document.get("qsub", {}).get("request_id", "")
            ) != _normalize_job_id(prior["job_id"])
            or prior_submit_document.get("campaign_root_receipt")
            != submit["campaign_root_receipt"]
        ):
            raise ContractFailure("prior attempt is not rooted in this campaign")
    campaign_bindings = campaign["bindings"]
    expected_campaign_hashes = {
        "job_script_sha256": current["job_script_sha256"],
        "driver_sha256": current["driver_sha256"],
        "submitter_sha256": current["submitter_sha256"],
        "verifier_module_sha256": current["verifier_module_sha256"],
        "policy_sha256": current["policy_sha256"],
        "runtime_modules_sha256": current["runtime_modules_sha256"],
        "patch_sha256": current["patch_sha256"],
        "ledger_sha256": current["ledger_sha256"],
        "correctness_sha256": bindings["correctness_sha256"],
        "schedule_sha256": bindings["schedule_sha256"],
    }
    if (
        any(
            campaign_bindings.get(key) != value
            for key, value in expected_campaign_hashes.items()
        )
        or campaign_bindings.get("ccbench_pin_full") != PIN
        or campaign_bindings.get("third_party_heads")
        != expected_third_party_heads
    ):
        raise ContractFailure("campaign root frozen input hash drift")
    expected_patched = _expected_patched_source_hashes(
        repo / "external/ccbench", repo / patch_contract.PATCH_PATH,
    )
    if campaign_bindings.get("expected_patched_source_sha256") != expected_patched:
        raise ContractFailure("campaign root pin+patch source hash drift")
    return submit["schedule_receipt"]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _raw_manifest(root: Path) -> list[str]:
    result = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise DriverError(f"raw bundle contains symlink: {path}")
        if path.is_file():
            result.append(path.relative_to(root).as_posix())
    return result


def write_raw_manifest(root: Path) -> Path:
    """raw-manifest 自身を除く全 raw file を path+sha256 で束縛する。"""
    destination = root / "raw-manifest.json"
    if destination.exists():
        raise ContractFailure(f"raw manifest already exists: {destination}")
    files = [
        {"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)}
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink() and path != destination
    ]
    publish_create_only_json(destination, {
        "schema_version": RAW_MANIFEST_SCHEMA,
        "files": files,
    }, staging_dir=root)
    return destination


def validate_raw_manifest(root: Path) -> list[str]:
    manifest_path = root / "raw-manifest.json"
    manifest = _load_json(manifest_path)
    if not _exact_keys(manifest, {"schema_version", "files"}):
        raise ContractFailure("raw manifest schema is not closed")
    if manifest["schema_version"] != RAW_MANIFEST_SCHEMA:
        raise ContractFailure("raw manifest schema version mismatch")
    files = manifest["files"]
    if type(files) is not list or not files:
        raise ContractFailure("raw manifest files must be non-empty")
    paths: list[str] = []
    for receipt in files:
        if (
            not _exact_keys(receipt, {"path", "sha256"})
            or type(receipt["path"]) is not str
            or not receipt["path"]
            or Path(receipt["path"]).is_absolute()
            or ".." in Path(receipt["path"]).parts
            or type(receipt["sha256"]) is not str
            or _HEX64.fullmatch(receipt["sha256"]) is None
        ):
            raise ContractFailure("raw manifest file receipt is invalid")
        path = root / receipt["path"]
        if (
            not path.is_file()
            or path.is_symlink()
            or sha256_file(path) != receipt["sha256"]
        ):
            raise ContractFailure(
                f"raw manifest hash/path mismatch: {receipt['path']}"
            )
        paths.append(receipt["path"])
    if len(paths) != len(set(paths)):
        raise ContractFailure("raw manifest paths are duplicated")
    actual = set(_raw_manifest(root)) - {"raw-manifest.json"}
    if set(paths) != actual:
        raise ContractFailure("raw manifest does not cover exact raw file set")
    return sorted([*paths, "raw-manifest.json"])


def write_attempt_receipt(root: Path, attempt: int) -> Path:
    destination = root / "attempt-receipt.json"
    publish_create_only_json(destination, {
        "schema_version": "silo_ladder_rung1-attempt-receipt/v1",
        "attempt": attempt,
        "files": [
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": sha256_file(path),
            }
            for path in sorted(root.rglob("*"))
            if path.is_file()
            and not path.is_symlink()
            and path != destination
            and path.name != "raw-manifest.json"
        ],
    }, staging_dir=root)
    return destination


def validate_attempt_receipt(root: Path, attempt: int) -> list[str]:
    """attempt receipt の内部 hash と subtree の完全・一意集合を再計算する。"""
    destination = root / "attempt-receipt.json"
    receipt = _load_json(destination)
    if (
        not _exact_keys(receipt, {"schema_version", "attempt", "files"})
        or receipt["schema_version"] != "silo_ladder_rung1-attempt-receipt/v1"
        or receipt["attempt"] != attempt
        or type(receipt["files"]) is not list
        or not receipt["files"]
    ):
        raise ContractFailure("attempt receipt schema/content mismatch")
    paths: list[str] = []
    for item in receipt["files"]:
        if (
            not _exact_keys(item, {"path", "sha256"})
            or type(item["path"]) is not str
            or not item["path"]
            or Path(item["path"]).is_absolute()
            or ".." in Path(item["path"]).parts
            or type(item["sha256"]) is not str
            or _HEX64.fullmatch(item["sha256"]) is None
        ):
            raise ContractFailure("attempt receipt file entry is invalid")
        path = root / item["path"]
        if (
            not path.is_file()
            or path.is_symlink()
            or sha256_file(path) != item["sha256"]
        ):
            raise ContractFailure(
                f"attempt receipt hash/path mismatch: {item['path']}"
            )
        paths.append(item["path"])
    if len(paths) != len(set(paths)):
        raise ContractFailure("attempt receipt paths are duplicated")
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
        and not path.is_symlink()
        and path != destination
        and path.name != "raw-manifest.json"
    }
    if set(paths) != actual:
        raise ContractFailure("attempt receipt does not cover exact subtree")
    return sorted(paths)


def validate_attempt_subtree(root: Path, attempt: int) -> list[str]:
    """self-manifest と attempt receipt の両 seal を同じ現物へ再束縛する。"""
    manifest_paths = validate_raw_manifest(root)
    validate_attempt_receipt(root, attempt)
    return manifest_paths


def write_campaign_attempt_root_receipt(
    repo: Path, submit: Mapping[str, Any], *, attempt: int, job_id: str,
    attempt_receipt_sha256: str, failure_class: str | None,
    reason_code: str | None, submit_receipt_sha256: str,
) -> Path:
    """campaign root 配下で job/nonce/submit/attempt seal を相互束縛する。"""
    identity = repo / submit["campaign_root_receipt"]["path"]
    destination = (
        identity.parent / f"attempt-{attempt}" / "attempt-root-receipt.json"
    )
    return publish_create_only_json(destination, {
        "schema_version": "silo_ladder_rung1-campaign-attempt-root/v1",
        "campaign_id": submit["campaign_id"],
        "attempt": attempt,
        "job_id": job_id,
        "nonce": submit["nonce"],
        "submit_receipt_sha256": submit_receipt_sha256,
        "attempt_receipt_sha256": attempt_receipt_sha256,
        "failure_class": failure_class,
        "reason_code": reason_code,
    }, staging_dir=destination.parent)


def _tree_manifest_sha256(root: Path) -> str:
    records = [
        {
            "path": path.relative_to(root).as_posix(),
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    ]
    return sha256_bytes(json.dumps(
        records, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8"))


def _command_receipt_link_ok(
    receipt: Mapping[str, Any], *, expected_argv0: str,
    argv_tail: Sequence[str], target_sha256: str,
    stdout_path: Path, stderr_path: Path, returncode: int = 0,
    argv0_sha256: str,
) -> bool:
    """command receipt を argv0 full path/rc/target/stdout/stderr へ結ぶ。"""
    argv = receipt.get("argv")
    return (
        type(argv) is list
        and len(argv) == len(argv_tail) + 1
        and argv[0] == expected_argv0
        and argv[1:] == list(argv_tail)
        and receipt.get("returncode") == returncode
        and receipt.get("timed_out") is False
        and receipt.get("target_sha256") == target_sha256
        and receipt.get("stdout_sha256") == sha256_file(stdout_path)
        and receipt.get("stderr_sha256") == sha256_file(stderr_path)
        and receipt.get("argv0_sha256") == argv0_sha256
    )


def validate_raw_bundle(
    document: Mapping[str, Any], raw_root: Path,
) -> tuple[EvidenceFailure, ...]:
    """raw 現物から主要 predicate を再計算する。summary check は参照しない。"""
    try:
        actual_paths = validate_raw_manifest(raw_root)
        if actual_paths != document["raw_bundle"]["paths"]:
            raise DriverError("raw manifest path set differs from final JSON")
        attempt_number = document["gap_leg"]["attempts"][-1]["attempt"]
        active_root = raw_root / "attempts" / str(attempt_number)
        for attempt in document["gap_leg"]["attempts"]:
            validate_attempt_subtree(
                raw_root / "attempts" / str(attempt["attempt"]),
                attempt["attempt"],
            )
        command_receipts = []
        for path in sorted(active_root.rglob("*.command.json")) + sorted(
            (raw_root / "correctness").rglob("*.command.json")
        ):
            receipt = _load_json(path)
            if (
                not _exact_keys(receipt, {
                    "schema_version", "argv", "cwd", "started_at_utc",
                    "completed_at_utc", "elapsed_monotonic_s", "timeout_s",
                    "timed_out", "returncode", "stdout_sha256",
                    "stderr_sha256", "argv0_sha256", "target_sha256",
                })
                or receipt["schema_version"] != COMMAND_RECEIPT_SCHEMA
                or type(receipt["argv"]) is not list
                or not receipt["argv"]
                or type(receipt["cwd"]) is not str
                or not Path(receipt["cwd"]).is_absolute()
                or type(receipt["timed_out"]) is not bool
                or (
                    receipt["returncode"] is not None
                    and type(receipt["returncode"]) is not int
                )
                or any(
                    type(receipt[key]) is not str
                    or _HEX64.fullmatch(receipt[key]) is None
                    for key in ("stdout_sha256", "stderr_sha256")
                )
                or any(
                    receipt[key] is not None
                    and (
                        type(receipt[key]) is not str
                        or _HEX64.fullmatch(receipt[key]) is None
                    )
                    for key in ("argv0_sha256", "target_sha256")
                )
                or (
                    Path(str(receipt["argv"][0])).name in {"nm", "readelf"}
                    and receipt["argv0_sha256"] is None
                )
            ):
                raise DriverError(f"invalid command receipt: {path}")
            command_receipts.append(receipt)
        if not command_receipts:
            raise DriverError("raw bundle has no command receipts")
        pgrep_receipts = [
            receipt for receipt in command_receipts
            if Path(receipt["argv"][0]).name == "pgrep"
        ]
        schedule = _load_json(active_root / "schedule-receipt.json")
        if schedule != document["gap_leg"]["schedule_receipt"]:
            raise DriverError("raw schedule differs from final JSON")
        gap_receipt = _load_json(raw_root / "gap-result-receipt.json")
        if (
            not _exact_keys(gap_receipt, {"schema_version", "gap_leg"})
            or gap_receipt["schema_version"]
            != "silo_ladder_rung1-gap-receipt/v1"
            or gap_receipt["gap_leg"] != document["gap_leg"]
        ):
            raise DriverError("raw gap receipt differs from final JSON")
        provenance_receipt = _load_json(raw_root / "provenance-receipt.json")
        if (
            not _exact_keys(
                provenance_receipt, {"schema_version", "provenance"},
            )
            or provenance_receipt["schema_version"]
            != "silo_ladder_rung1-provenance-receipt/v1"
            or provenance_receipt["provenance"] != document["provenance"]
        ):
            raise DriverError("raw provenance receipt differs from final JSON")
        verifier = _load_json(raw_root / "correctness/verifier.json")
        if verifier != document["correctness_leg"]["verifier"]:
            raise DriverError("raw verifier JSON differs from final JSON")
        _validate_correctness_commit_witness(
            verifier,
            (raw_root / "correctness/run.stdout").read_text(
                encoding="utf-8", errors="strict",
            ),
        )
        trace_root = raw_root / "correctness/traces"
        trace_paths = sorted(trace_root.glob("trace_*.log"))
        if len(trace_paths) != 4:
            raise DriverError("raw correctness trace count is not four")
        from orchestrator.verifier.core import verify_trace_dir
        from orchestrator.verifier.report import result_to_dict
        repo = _repo_root()
        proof_snapshot, _source_hashes = _pinned_patched_source_model(
            os.path.realpath(repo / "external/ccbench"),
            PIN,
            (repo / patch_contract.PATCH_PATH).read_bytes(),
        )
        recomputed_result = result_to_dict(verify_trace_dir(
            str(trace_root), _proof_source_snapshot=proof_snapshot,
        ))
        # trace_dir is a storage location, not a verifier predicate.
        recomputed_result["trace_dir"] = verifier["results"][0]["trace_dir"]
        recomputed = {
            "runs": 1,
            "certified_serializable": int(recomputed_result["certified"] is True),
            "non_serializable": int(
                recomputed_result["verdict"] == "non-serializable"
            ),
            "indeterminate": int(recomputed_result["verdict"] == "indeterminate"),
            "results": [recomputed_result],
        }
        if recomputed != verifier:
            raise DriverError("raw traces recompute to a different verifier result")
        correctness_raw = raw_root / "correctness"
        correctness_replay = _load_json(correctness_raw / "compile-replay.json")
        correctness_build = document["correctness_leg"]["build"]
        correctness_tools = {
            item["name"]: item
            for item in document["correctness_leg"]["provenance"]["tools"]
        }
        correctness_commands = _load_json(
            correctness_raw / "compile_commands.json"
        )
        correctness_invocations = compile_commands_for_sources(
            correctness_commands, None,
        )
        correctness_targets = [
            (item["source_rel"], item["argv"])
            for item in correctness_invocations
        ]
        correctness_output_by_source = {
            item["source_rel"]: item["output"]
            for item in correctness_invocations
        }
        correctness_gxx = next(
            item["realpath"]
            for item in document["correctness_leg"]["provenance"]["tools"]
            if item["name"] == "g++"
        )
        correctness_gcc = next(
            item["realpath"]
            for item in document["correctness_leg"]["provenance"]["tools"]
            if item["name"] == "gcc"
        )
        _validate_cmake_cache(
            correctness_raw / "CMakeCache.txt",
            expected_c=correctness_gcc,
            expected_cxx=correctness_gxx,
            expected_flags=f"-D{RUNG_MACRO}=1",
            expected_trace="1",
        )
        if (
            len(correctness_targets) != 2
            or {item[0] for item in correctness_targets} != set(SOURCE_FILES)
            or any(
                validate_compile_argv(
                    argv,
                    expected_macro=RUNG_MACRO,
                    expected_compiler_realpath=correctness_gxx,
                ) != (RUNG_MACRO,)
                for _, argv in correctness_targets
            )
        ):
            raise DriverError("raw correctness compile argv witness failed")
        correctness_target_argv = dict(correctness_targets)
        correctness_binary_nm = (
            correctness_raw / "binary.nm.txt"
        ).read_text(encoding="utf-8", errors="strict")
        correctness_object_nm = (
            correctness_raw / "transaction.nm.txt"
        ).read_text(encoding="utf-8", errors="strict")
        correctness_readelf = (
            correctness_raw / "binary.readelf.txt"
        ).read_text(encoding="utf-8", errors="strict")
        correctness_binary_count = sum(
            line.split()[-1] == IDENTITY_SYMBOL
            for line in correctness_binary_nm.splitlines() if line.split()
        )
        correctness_object_count = sum(
            line.split()[-1] == IDENTITY_SYMBOL
            for line in correctness_object_nm.splitlines() if line.split()
        )
        correctness_binary_nm_receipt = _load_json(
            correctness_raw / "binary.nm.command.json"
        )
        correctness_object_nm_receipt = _load_json(
            correctness_raw / "transaction.nm.command.json"
        )
        correctness_readelf_receipt = _load_json(
            correctness_raw / "binary.readelf.command.json"
        )
        correctness_run_receipt = _load_json(
            correctness_raw / "run.command.json"
        )
        correctness_binary_path = correctness_run_receipt["argv"][0]
        correctness_transaction = next(
            item for item in correctness_replay["invocations"]
            if item["source_rel"] == SOURCE_FILES[0]
        )
        if (
            type(correctness_replay) is not dict
            or set(correctness_replay) != {"invocations"}
            or not _compile_invocations_complete(
                correctness_replay["invocations"]
            )
            or correctness_replay["invocations"]
            != correctness_build["compile_invocations"]
            or any(
                item["argv"] != correctness_target_argv.get(item["source_rel"])
                for item in correctness_replay["invocations"]
            )
            or any(
                item["object_path"]
                != correctness_output_by_source.get(item["source_rel"])
                for item in correctness_replay["invocations"]
            )
            or any(
                type(item) is not dict
                or item.get("replay_match") is not True
                or item.get("object_sha256") != item.get("replay_object_sha256")
                for item in correctness_replay["invocations"]
            )
            or not (correctness_raw / "CMakeCache.txt").is_file()
            or not (correctness_raw / "compile_commands.json").is_file()
            or not (correctness_raw / "binary.nm.txt").is_file()
            or not (correctness_raw / "binary.readelf.txt").is_file()
            or next(
                item for item in correctness_replay["invocations"]
                if item["source_rel"] == SOURCE_FILES[0]
            )["object_sha256"]
            != correctness_build["transaction_object_sha256"]
            or correctness_object_nm_receipt["target_sha256"]
            != correctness_build["transaction_object_sha256"]
            or correctness_binary_nm_receipt["target_sha256"]
            != correctness_build["binary_sha256"]
            or correctness_readelf_receipt["target_sha256"]
            != correctness_build["binary_sha256"]
            or not _command_receipt_link_ok(
                correctness_object_nm_receipt,
                expected_argv0=correctness_tools["nm"]["realpath"],
                argv_tail=[
                    "-g", "--defined-only",
                    correctness_transaction["object_path"],
                ],
                target_sha256=correctness_build[
                    "transaction_object_sha256"
                ],
                stdout_path=correctness_raw / "transaction.nm.txt",
                stderr_path=correctness_raw / "transaction.nm.stderr",
                argv0_sha256=correctness_tools["nm"]["sha256"],
            )
            or not _command_receipt_link_ok(
                correctness_binary_nm_receipt,
                expected_argv0=correctness_tools["nm"]["realpath"],
                argv_tail=[
                    "-g", "--defined-only", correctness_binary_path,
                ],
                target_sha256=correctness_build["binary_sha256"],
                stdout_path=correctness_raw / "binary.nm.txt",
                stderr_path=correctness_raw / "binary.nm.stderr",
                argv0_sha256=correctness_tools["nm"]["sha256"],
            )
            or not _command_receipt_link_ok(
                correctness_readelf_receipt,
                expected_argv0=correctness_tools["readelf"]["realpath"],
                argv_tail=["-Ws", correctness_binary_path],
                target_sha256=correctness_build["binary_sha256"],
                stdout_path=correctness_raw / "binary.readelf.txt",
                stderr_path=correctness_raw / "binary.readelf.stderr",
                argv0_sha256=correctness_tools["readelf"]["sha256"],
            )
            or not _command_receipt_link_ok(
                correctness_run_receipt,
                expected_argv0=correctness_binary_path,
                argv_tail=CORRECTNESS_WORKLOAD,
                target_sha256=correctness_build["binary_sha256"],
                stdout_path=correctness_raw / "run.stdout",
                stderr_path=correctness_raw / "run.stderr",
                argv0_sha256=correctness_build["binary_sha256"],
            )
            or correctness_binary_count != 1
            or correctness_object_count != 1
            or sum(
                line.split()[-1] == IDENTITY_SYMBOL
                for line in correctness_readelf.splitlines() if line.split()
            ) != 1
        ):
            raise DriverError("raw correctness build witness failed")
        performance_by_cell = {
            (item["workload"], item["rep"], item["variant"]): item
            for item in document["gap_leg"]["performance_runs"]
        }
        for row in schedule["runs"]:
            run_dir = active_root / "runs" / (
                f"perf-{row['ordinal']:02d}-{row['workload']}-"
                f"{row['variant']}-r{row['rep']}"
            )
            parsed = parse_run_stdout(
                (run_dir / "stdout.txt").read_text(encoding="utf-8"),
                liveness=False,
            )
            recorded = performance_by_cell[
                (row["workload"], row["rep"], row["variant"])
            ]
            command = _load_json(run_dir / "run.command.json")
            build_record = next(
                item for item in document["gap_leg"]["builds"]
                if item["id"] == recorded["binary_id"]
            )
            if (
                parsed["throughput_tps"] != recorded["throughput_tps"]
                or parsed["commit_count"] != recorded["commit_count"]
                or parsed["batch_commit_count"] != recorded["batch_commit_count"]
                or recorded["ordinal"] != row["ordinal"]
                or recorded["returncode"] != 0
                or recorded["binary_id"] != row["variant"]
                or recorded["workload_argv"]
                != WORKLOADS[row["workload"]]["argv"]
                or recorded["argv"][1:] != recorded["workload_argv"]
                or recorded["raw_path"] != run_dir.relative_to(active_root).as_posix()
                or recorded["stdout_sha256"] != sha256_file(run_dir / "stdout.txt")
                or recorded["stderr_sha256"] != sha256_file(run_dir / "stderr.txt")
                or not (run_dir / "stderr.txt").is_file()
                or not _command_receipt_link_ok(
                    command,
                    expected_argv0=recorded["argv"][0],
                    argv_tail=recorded["workload_argv"],
                    target_sha256=build_record["binary_sha256"],
                    stdout_path=run_dir / "stdout.txt",
                    stderr_path=run_dir / "stderr.txt",
                    returncode=recorded["returncode"],
                    argv0_sha256=build_record["binary_sha256"],
                )
            ):
                raise DriverError("raw performance run differs from final JSON")
        live_by_cell = {
            (item["workload"], item["rep"]): item
            for item in document["gap_leg"]["liveness_runs"]
        }
        ordinal = 24
        for workload in WORKLOADS:
            for rep in (1, 2):
                run_dir = active_root / "runs" / (
                    f"liveness-{ordinal:02d}-{workload}-r{rep}"
                )
                parsed = parse_run_stdout(
                    (run_dir / "stdout.txt").read_text(encoding="utf-8"),
                    liveness=True,
                )
                recorded = live_by_cell[(workload, rep)]
                command = _load_json(run_dir / "run.command.json")
                build_record = next(
                    item for item in document["gap_leg"]["builds"]
                    if item["id"] == recorded["binary_id"]
                )
                for key in (
                    "commit_count", "batch_commit_count",
                    "per_worker_commits", "per_worker_batch_commits",
                ):
                    if parsed[key] != recorded[key]:
                        raise DriverError(
                            f"raw liveness {workload}/r{rep} {key} mismatch"
                        )
                if (
                    recorded["ordinal"] != ordinal
                    or recorded["returncode"] != 0
                    or recorded["binary_id"] != "rung-liveness"
                    or recorded["workload_argv"] != WORKLOADS[workload]["argv"]
                    or recorded["argv"][1:] != recorded["workload_argv"]
                    or recorded["raw_path"] != run_dir.relative_to(active_root).as_posix()
                    or recorded["stdout_sha256"] != sha256_file(run_dir / "stdout.txt")
                    or recorded["stderr_sha256"] != sha256_file(run_dir / "stderr.txt")
                    or not (run_dir / "stderr.txt").is_file()
                    or not _command_receipt_link_ok(
                        command,
                        expected_argv0=recorded["argv"][0],
                        argv_tail=recorded["workload_argv"],
                        target_sha256=build_record["binary_sha256"],
                        stdout_path=run_dir / "stdout.txt",
                        stderr_path=run_dir / "stderr.txt",
                        returncode=recorded["returncode"],
                        argv0_sha256=build_record["binary_sha256"],
                    )
                ):
                    raise DriverError("raw liveness completion witness mismatch")
                ordinal += 1
        builds = document["gap_leg"]["builds"]
        gap_tools = {
            item["name"]: item
            for item in document["provenance"]["tools"]
        }
        if (
            len(builds) != 3
            or len({build["id"] for build in builds}) != 3
            or {build["id"] for build in builds}
            != {"stock", "rung-perf", "rung-liveness"}
        ):
            raise DriverError("raw build set is not exactly three unique IDs")
        recorded_gxx = next(
            item["realpath"] for item in document["provenance"]["tools"]
            if item["name"] == "g++"
        )
        recorded_gcc = next(
            item["realpath"] for item in document["provenance"]["tools"]
            if item["name"] == "gcc"
        )
        binary_paths_by_id: dict[str, set[str]] = {
            build["id"]: set() for build in builds
        }
        for run in (
            *document["gap_leg"]["performance_runs"],
            *document["gap_leg"]["liveness_runs"],
        ):
            binary_paths_by_id[run["binary_id"]].add(run["argv"][0])
        if any(len(paths) != 1 for paths in binary_paths_by_id.values()):
            raise DriverError("run argv does not identify one binary path per build")
        for build in builds:
            build_raw = active_root / f"build-{build['id']}"
            replay = _load_json(build_raw / "compile-replay.json")
            compile_commands = _load_json(build_raw / "compile_commands.json")
            target_invocations = compile_commands_for_sources(
                compile_commands, None,
            )
            target_commands = [
                (item["source_rel"], item["argv"])
                for item in target_invocations
            ]
            if (
                len(target_commands) != 2
                or {item[0] for item in target_commands} != set(SOURCE_FILES)
            ):
                raise DriverError(
                    f"raw compile command target set mismatch: {build['id']}"
                )
            expected_macro = None if build["id"] == "stock" else RUNG_MACRO
            target_argv_by_source = dict(target_commands)
            target_output_by_source = {
                item["source_rel"]: item["output"]
                for item in target_invocations
            }
            active_sets = [
                validate_compile_argv(
                    argv,
                    expected_macro=expected_macro,
                    require_report=build["id"] == "rung-liveness",
                    expected_compiler_realpath=recorded_gxx,
                )
                for _, argv in target_commands
            ]
            _validate_cmake_cache(
                build_raw / "CMakeCache.txt",
                expected_c=recorded_gcc,
                expected_cxx=recorded_gxx,
                expected_flags=" ".join(
                    f"-D{macro}=1" for macro in build["macros"]
                ),
                expected_trace="0",
            )
            active = [
                macro for macro in (RUNG_MACRO, REPORT_MACRO)
                if all(macro in item for item in active_sets)
            ]
            binary_nm = (build_raw / "binary.nm.txt").read_text(
                encoding="utf-8", errors="strict",
            )
            transaction_nm = (build_raw / "transaction.nm.txt").read_text(
                encoding="utf-8", errors="strict",
            )
            readelf_text = (build_raw / "binary.readelf.txt").read_text(
                encoding="utf-8", errors="strict",
            )
            binary_nm_receipt = _load_json(
                build_raw / "binary.nm.command.json"
            )
            transaction_nm_receipt = _load_json(
                build_raw / "transaction.nm.command.json"
            )
            readelf_receipt = _load_json(
                build_raw / "binary.readelf.command.json"
            )
            transaction = next(
                item for item in replay["invocations"]
                if item["source_rel"] == SOURCE_FILES[0]
            )
            binary_path = next(iter(binary_paths_by_id[build["id"]]))
            expected_count = 0 if build["id"] == "stock" else 1
            binary_identity_count = sum(
                line.split()[-1] == IDENTITY_SYMBOL
                for line in binary_nm.splitlines() if line.split()
            )
            object_identity_count = sum(
                line.split()[-1] == IDENTITY_SYMBOL
                for line in transaction_nm.splitlines() if line.split()
            )
            if (
                type(replay) is not dict
                or set(replay) != {"invocations"}
                or not _compile_invocations_complete(replay["invocations"])
                or any(
                    type(item) is not dict
                    or item.get("replay_match") is not True
                    or item.get("object_sha256") != item.get("replay_object_sha256")
                    for item in replay["invocations"]
                )
                or replay["invocations"] != build["compile_invocations"]
                or any(
                    item["argv"] != target_argv_by_source.get(item["source_rel"])
                    for item in replay["invocations"]
                )
                or any(
                    item["object_path"]
                    != target_output_by_source.get(item["source_rel"])
                    for item in replay["invocations"]
                )
                or next(
                    item for item in replay["invocations"]
                    if item["source_rel"] == SOURCE_FILES[0]
                )["object_sha256"] != build["transaction_object_sha256"]
                or not (build_raw / "CMakeCache.txt").is_file()
                or not (build_raw / "compile_commands.json").is_file()
                or not (build_raw / "binary.nm.txt").is_file()
                or not (build_raw / "binary.readelf.txt").is_file()
                or not _command_receipt_link_ok(
                    transaction_nm_receipt,
                    expected_argv0=gap_tools["nm"]["realpath"],
                    argv_tail=[
                        "-g", "--defined-only", transaction["object_path"],
                    ],
                    target_sha256=build["transaction_object_sha256"],
                    stdout_path=build_raw / "transaction.nm.txt",
                    stderr_path=build_raw / "transaction.nm.stderr",
                    argv0_sha256=gap_tools["nm"]["sha256"],
                )
                or not _command_receipt_link_ok(
                    binary_nm_receipt,
                    expected_argv0=gap_tools["nm"]["realpath"],
                    argv_tail=["-g", "--defined-only", binary_path],
                    target_sha256=build["binary_sha256"],
                    stdout_path=build_raw / "binary.nm.txt",
                    stderr_path=build_raw / "binary.nm.stderr",
                    argv0_sha256=gap_tools["nm"]["sha256"],
                )
                or not _command_receipt_link_ok(
                    readelf_receipt,
                    expected_argv0=gap_tools["readelf"]["realpath"],
                    argv_tail=["-Ws", binary_path],
                    target_sha256=build["binary_sha256"],
                    stdout_path=build_raw / "binary.readelf.txt",
                    stderr_path=build_raw / "binary.readelf.stderr",
                    argv0_sha256=gap_tools["readelf"]["sha256"],
                )
                or binary_identity_count != expected_count
                or object_identity_count != expected_count
                or build["identity_defined_count"] != binary_identity_count
                or build["macros"] != active
                or sum(
                    line.split()[-1] == IDENTITY_SYMBOL
                    for line in readelf_text.splitlines() if line.split()
                ) != expected_count
                or any(
                    "izanagi_trace" in line
                    for line in readelf_text.splitlines()
                )
            ):
                raise DriverError(f"raw build witness failed: {build['id']}")
        by_id = {build["id"]: build for build in builds}
        if (
            by_id["rung-perf"]["transaction_object_sha256"]
            != by_id["rung-liveness"]["transaction_object_sha256"]
        ):
            raise DriverError("raw rung perf/liveness object bytes differ")
        campaign_root = _load_json(raw_root / "campaign-root-receipt.json")
        if (
            not _exact_keys(campaign_root, {
                "schema_version", "campaign_id", "schedule_receipt",
                "bindings", "attempts",
            })
            or campaign_root["schema_version"]
            != "silo_ladder_rung1-campaign-root-final/v1"
            or campaign_root["schedule_receipt"] != schedule
            or len(campaign_root["attempts"])
            != len(document["gap_leg"]["attempts"])
        ):
            raise DriverError("final campaign root receipt mismatch")
        for attempt in document["gap_leg"]["attempts"]:
            receipt_path = (
                raw_root / "attempts" / str(attempt["attempt"])
                / "attempt-receipt.json"
            )
            if (
                not receipt_path.is_file()
                or sha256_file(receipt_path)
                != attempt["attempt_receipt_sha256"]
            ):
                raise DriverError(
                    f"attempt receipt hash mismatch: {attempt['attempt']}"
                )
            if attempt["failure_class"] == "infra":
                wrapper = _load_json(receipt_path.parent / "wrapper-failure.json")
                if (
                    wrapper.get("failure_class") != "infra"
                    or wrapper.get("reason_code") != attempt["reason_code"]
                    or wrapper.get("pbs_jobid") != attempt["job_id"]
                    or wrapper.get("attempt_number") != attempt["attempt"]
                ):
                    raise DriverError("prior infra wrapper failure mismatch")
            attempt_submit_path = receipt_path.parent / "submit-receipt.json"
            attempt_submit = _load_json(attempt_submit_path)
            if (
                sha256_file(attempt_submit_path)
                != attempt["submit_receipt_sha256"]
                or attempt_submit.get("nonce") != attempt["nonce"]
                or _normalize_job_id(
                    attempt_submit.get("qsub", {}).get("request_id", "")
                ) != _normalize_job_id(attempt["job_id"])
                or attempt_submit.get("campaign_id") != campaign_root["campaign_id"]
            ):
                raise DriverError("attempt submit receipt chain mismatch")
            seal_ref = attempt["campaign_attempt_root_receipt"]
            if not _exact_keys(seal_ref, {"path", "sha256"}):
                raise DriverError("campaign attempt root reference schema mismatch")
            seal_copy = (
                raw_root / "campaign-attempt-root-receipts"
                / f"{attempt['attempt']}.json"
            )
            seal = _load_json(seal_copy)
            if (
                sha256_file(seal_copy) != seal_ref["sha256"]
                or seal.get("campaign_id") != campaign_root["campaign_id"]
                or seal.get("attempt") != attempt["attempt"]
                or seal.get("job_id") != attempt["job_id"]
                or seal.get("nonce") != attempt["nonce"]
                or seal.get("submit_receipt_sha256")
                != attempt["submit_receipt_sha256"]
                or seal.get("attempt_receipt_sha256")
                != attempt["attempt_receipt_sha256"]
                or seal.get("failure_class") != attempt["failure_class"]
                or seal.get("reason_code") != attempt["reason_code"]
            ):
                raise DriverError("campaign attempt root receipt mismatch")
        if campaign_root["attempts"] != [
            _load_json(
                raw_root / "campaign-attempt-root-receipts"
                / f"{item['attempt']}.json"
            )
            for item in document["gap_leg"]["attempts"]
        ]:
            raise DriverError("campaign root does not bind exact attempt chain")
        dependency_pins = _dependency_pins()
        for name, pin in dependency_pins.items():
            head_path = (
                active_root / "job-prologue" / f"{name}-source-head.txt"
            )
            status_path = (
                active_root / "job-prologue" / f"{name}-source-status.txt"
            )
            if (
                head_path.read_text(encoding="utf-8", errors="strict")
                != pin + "\n"
                or status_path.read_text(encoding="utf-8", errors="strict")
                != ""
            ):
                raise DriverError(
                    f"raw dependency HEAD/status differs from policy: {name}"
                )
        attestation = document["gap_leg"]["attestation"]
        calibration = _load_json(
            _repo_root() / document["binding"]["calibration"]["path"]
        )
        parsed_probe = env_attestation.parse_probe_output(
            (active_root / "attestation-job.json").read_bytes()
        )
        if not parsed_probe.ok or parsed_probe.profile is None:
            raise DriverError("raw attestation probe is not ok")
        actual_profile = env_attestation.observed_profile_to_dict(parsed_probe.profile)
        expected_profile = calibration["attestation_profile"]
        expected_clock = {
            "samples_mhz": list(expected_profile["effective_clock"]["samples_mhz"]),
            "tolerance_pct": expected_profile["effective_clock"]["tolerance_pct"],
        }
        observed_clock = {
            "samples_mhz": list(actual_profile["effective_clock"]["samples_mhz"]),
        }
        derived_attestation = {
            "cpu_model_match": (
                actual_profile["cpu"]["model_name_normalized"]
                == expected_profile["cpu"]["model_name_normalized"]
            ),
            "effective_clock_match": (
                execution_guard.effective_clock_comparison_passes(
                    expected_clock, observed_clock,
                )
                and actual_profile["effective_clock"]["method"]
                == expected_profile["effective_clock"]["method"]
                and actual_profile["effective_clock"]["governor"]
                == expected_profile["effective_clock"]["governor"]
            ),
            "cpuset_match": (
                actual_profile["cores"]["affinity_visible"] == 48
                and actual_profile["cores"]["physical"] == 48
                and calibration["acquisition_receipt"]["allocation"][
                    "cpuset_size"
                ] == 48
            ),
            "ht_match": (
                actual_profile["cores"]["smt_active"] is False
                and calibration["acquisition_receipt"]["allocation"][
                    "ht_off"
                ] is True
            ),
            "numa_match": (
                actual_profile["numa"] == expected_profile["numa"]
            ),
        }
        if (
            attestation["contract_sha256"]
            != document["binding"]["calibration"]["contract_sha256"]
            or attestation["calibration_sha256"]
            != document["binding"]["calibration"]["sha256"]
            or len(attestation["per_sample_solo_checks"]) != 28
            or [item["ordinal"] for item in attestation["per_sample_solo_checks"]]
            != list(range(28))
            or any(
                attestation[key] is not value
                for key, value in derived_attestation.items()
            )
        ):
            raise DriverError("raw attestation binding/ordinal set mismatch")
        if len(pgrep_receipts) != 28:
            raise DriverError("raw attestation needs exactly 28 pgrep receipts")
        load_threshold = _load_json(
            _repo_root() / "tools/pegasus/policy.json"
        )["silo_ladder_rung1"]["solo_load1_threshold"]
        for solo in attestation["per_sample_solo_checks"]:
            ordinal = solo["ordinal"]
            pgrep_text = (
                active_root / f"solo-{ordinal:02d}.pgrep.stdout"
            ).read_text(encoding="utf-8", errors="strict")
            load = _load_json(active_root / f"solo-{ordinal:02d}.load.json")
            competitors = [
                line for line in pgrep_text.splitlines() if line.strip()
            ]
            passed = (
                solo["pgrep_returncode"] == 1
                and not competitors
                and load["load1"] <= load_threshold
            )
            if (
                solo["competing_processes"] != competitors
                or solo["load1"] != load["load1"]
                or solo["load_threshold"] != load_threshold
                or solo["passed"] is not passed
                or pgrep_receipts[ordinal]["returncode"]
                != solo["pgrep_returncode"]
                or pgrep_receipts[ordinal]["stdout_sha256"]
                != sha256_file(
                    active_root / f"solo-{ordinal:02d}.pgrep.stdout"
                )
            ):
                raise DriverError(f"raw solo check mismatch: {ordinal}")
        accounting = active_root / "pbs-accounting.txt"
        if not accounting.is_file():
            raise DriverError("raw PBS accounting is absent")
        validate_nqsv_accounting_epilogue(
            accounting.read_text(encoding="utf-8", errors="replace"),
            document["gap_leg"]["attempts"][-1]["job_id"],
        )
    except (DriverError, OSError, KeyError, RuntimeError, TypeError, ValueError,
            env_attestation.AttestationError) as exc:
        return (EvidenceFailure("raw_bundle", str(exc)),)
    return ()


def validate_current_bindings(
    document: Mapping[str, Any], repo: Path,
) -> tuple[EvidenceFailure, ...]:
    """committed result を現行 patch/ledger/verifier/PBS bytes へ再束縛する。"""
    paths = {
        "patch": repo / patch_contract.PATCH_PATH,
        "ledger": repo / "patches/ledger.json",
        "driver": Path(__file__).resolve(),
        "pbs_job": repo / "tools/pegasus/silo_ladder_rung1.sh",
        "submitter": repo / "tools/pegasus/submit_silo_ladder_rung1.sh",
        "verifier_module": repo / "orchestrator/verifier/report.py",
        "policy": repo / "tools/pegasus/policy.json",
    }
    try:
        binding = document["binding"]
        for key, path in paths.items():
            if (
                binding[key]["path"] != path.relative_to(repo).as_posix()
                or binding[key]["sha256"] != sha256_file(path)
            ):
                raise DriverError(f"current binding mismatch: {key}")
        if binding["runtime_modules"] != runtime_modules_binding(repo):
            raise DriverError("current runtime module binding mismatch")
        contract = env_contract.lookup("pegasus")
        calibration = repo / contract.calibration_ref.path
        if (
            binding["ccbench_pin_full"] != PIN
            or binding["calibration"]["path"] != contract.calibration_ref.path
            or binding["calibration"]["sha256"] != sha256_file(calibration)
            or binding["calibration"]["contract_sha256"] != contract.contract_sha256
        ):
            raise DriverError("current calibration/pin binding mismatch")
        calibration_document = _load_json(calibration)
        registered_build = calibration_document["acquisition_receipt"][
            "ccbench"
        ]["build_argv"]
        registered_c, registered_cxx = (
            toolchain_binding.extract_silo_compiler_paths(registered_build)
        )
        registered_dependency_pins = {
            name: next(
                token.split("=", 1)[1] for token in registered_build
                if token.startswith(f"-DIZANAGI_{name.upper()}_SRC_HEAD=")
            )
            for name in ("gflags", "glog")
        }
        dependency_pins = _dependency_pins(repo)
        third_party = third_party_policy(repo)
        tools = {
            item["name"]: item for item in document["provenance"]["tools"]
        }
        if not toolchain_binding.silo_toolchain_matches(
            registered_dependency_pins=registered_dependency_pins,
            dependency_pins=dependency_pins,
            registered_cc_realpath=registered_c,
            registered_cxx_realpath=registered_cxx,
            receipt_cc_realpath=calibration_document[
                "acquisition_receipt"
            ]["toolchain"]["compiler_path"],
            receipt_cc_version=calibration_document[
                "acquisition_receipt"
            ]["toolchain"]["compiler_version"],
            observed_cc_realpath=tools["gcc"]["realpath"],
            observed_cxx_realpath=tools["g++"]["realpath"],
            observed_cc_version=tools["gcc"]["version"],
        ):
            raise DriverError("gap toolchain differs from registered calibration")
        build_by_id = {
            item["id"]: item for item in document["gap_leg"]["builds"]
        }
        if (
            not _valid_dependencies(
                document["correctness_leg"]["build"]["dependencies"],
                expected_pins=dependency_pins,
            )
            or any(
                not _valid_dependencies(
                    build["dependencies"], expected_pins=dependency_pins,
                )
                for build in build_by_id.values()
            )
        ):
            raise DriverError("dependency raw HEAD/status differs from policy pins")
        for provenance in (
            document["correctness_leg"]["provenance"],
            document["provenance"],
        ):
            records = provenance["third_party_sources"]
            by_name = {item["name"]: item for item in records}
            if (
                not _valid_third_party_sources(records)
                or any(
                    by_name[item["name"]]["pin"] != item["pin"]
                    or by_name[item["name"]]["git_head_raw"]
                    != item["pin"] + "\n"
                    or by_name[item["name"]]["clean"] is not True
                    for item in third_party
                )
            ):
                raise DriverError("third-party provenance differs from policy pins")
        correctness_flags = _third_party_configure_flags(
            document["correctness_leg"]["provenance"]["third_party_sources"]
        )
        gap_flags = _third_party_configure_flags(
            document["provenance"]["third_party_sources"]
        )
        if (
            any(
                flag not in document["correctness_leg"]["build"]["configure_argv"]
                for flag in correctness_flags
            )
            or any(
                flag not in build["configure_argv"]
                for build in build_by_id.values()
                for flag in gap_flags
            )
        ):
            raise DriverError("configure argv lacks offline third-party sources")
        stock_expected = {}
        for relative in SOURCE_FILES:
            shown = _run([
                "git", "-C", str(repo / "external/ccbench"),
                "show", f"{PIN}:{relative}",
            ])
            if shown.returncode != 0:
                raise DriverError(f"cannot rebind pinned stock source: {relative}")
            stock_expected[relative] = sha256_bytes(shown.stdout.encode("utf-8"))
        if build_by_id["stock"]["source_sha256"] != stock_expected:
            raise DriverError("stock build source is not exact pinned unpatched bytes")
        expected_patched = _expected_patched_source_hashes(
            repo / "external/ccbench", repo / patch_contract.PATCH_PATH,
        )
        if (
            document["provenance"]["source_witness"][
                "expected_patched_source_sha256"
            ] != expected_patched
            or document["correctness_leg"]["provenance"][
                "expected_patched_source_sha256"
            ] != expected_patched
            or document["correctness_leg"]["provenance"][
                "observed_patched_source_sha256"
            ] != expected_patched
            or build_by_id["rung-perf"]["source_sha256"] != expected_patched
            or build_by_id["rung-liveness"]["source_sha256"] != expected_patched
        ):
            raise DriverError("correctness/gap patched source binding mismatch")
    except (DriverError, OSError, KeyError, TypeError, ValueError) as exc:
        return (EvidenceFailure("binding", str(exc)),)
    return ()


def _normalize_job_id(value: str) -> str:
    if type(value) is not str or not value:
        raise DriverError("job ID must be a non-empty string")
    if value.startswith("0:"):
        value = value[2:]
    if value.startswith(tuple(f"{digit}:" for digit in "123456789")):
        raise DriverError(f"unsupported PBS subrequest prefix: {value}")
    return value


def validate_nqsv_accounting_epilogue(
    accounting_text: str, submit_job_id: str,
) -> tuple[str, ...]:
    """実在する NQSV 会計 field を検査し、保存対象行を返す。

    NQSV は scheduler 側の exit status を会計エピローグへ出力しないため、
    Request ID の submit 束縛と開始・終了・経過時間だけをここで検査する。
    in-job 成功の証明は collect の success sentinel、failure receipt 不在、
    gap ``status=complete`` 検査が別途担う。
    """
    if type(accounting_text) is not str:
        raise ContractFailure("terminal NQSV accounting must be text")
    request_ids = _NQSV_REQUEST_ID_RE.findall(accounting_text)
    if len(request_ids) != 1:
        raise ContractFailure(
            "terminal NQSV accounting needs exactly one Request ID"
        )
    observed_id = _normalize_job_id(request_ids[0])
    expected_id = _normalize_job_id(submit_job_id)
    if observed_id != expected_id:
        raise ContractFailure(
            "terminal NQSV accounting Request ID mismatch: "
            f"submit={submit_job_id!r} accounting={request_ids[0]!r}"
        )
    missing = [
        label for label, pattern in (
            ("Started Request Time", _NQSV_STARTED_RE),
            ("Ended Request Time", _NQSV_ENDED_RE),
            ("Elapse", _NQSV_ELAPSE_RE),
        )
        if pattern.search(accounting_text) is None
    ]
    if missing:
        raise ContractFailure(
            "terminal NQSV accounting field is absent: " + ", ".join(missing)
        )
    return tuple(
        line for line in accounting_text.splitlines()
        if _ACCOUNTING_RE.search(line)
    )


def _scheduler_name_matches(path: Path, stream: str, job_id: str) -> bool:
    suffix = ".o" if stream == "stdout" else ".e"
    normalized = _normalize_job_id(job_id)
    forms = {normalized, normalized.split(".", 1)[0]}
    return any(path.name.endswith(suffix + form) for form in forms)


def _copy_tree_create_only(source: Path, destination: Path) -> None:
    if not source.is_dir() or source.is_symlink():
        raise DriverError(f"raw source directory is invalid: {source}")
    destination.mkdir(parents=True, exist_ok=False)
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        target = destination / relative
        if path.is_symlink():
            raise DriverError(f"raw source contains symlink: {path}")
        if path.is_dir():
            target.mkdir()
        elif path.is_file():
            _copy_raw(path, target)


def _correctness_command(attempt_dir: Path) -> dict[str, Any]:
    """correctness leg。実 build 用 seam（通常 pytest からは呼ばない）。"""
    attempt_dir.mkdir(parents=True, exist_ok=False)
    raw = attempt_dir / "raw"
    raw.mkdir()
    global _COMMAND_RECEIPT_ROOT, _COMMAND_RECEIPT_INDEX
    _COMMAND_RECEIPT_ROOT = raw / "commands"
    _COMMAND_RECEIPT_INDEX = 0
    repo = _repo_root()
    patch = repo / patch_contract.PATCH_PATH
    ledger = repo / "patches/ledger.json"
    calibration_path = repo / env_contract.lookup("pegasus").calibration_ref.path
    toolchain = capture_tool_identities()
    dependencies = _dependency_contract()
    staged_third_party_sources = third_party_source_contract(repo)
    third_party_sources = _copy_third_party_sources(
        staged_third_party_sources,
        attempt_dir / "thirdparty-src",
        repo=repo,
    )
    prefix = ";".join(item["resolved_path"] for item in dependencies)
    base = repo / "external/ccbench"
    correctness_build: dict[str, Any] | None = None
    with patchharness.checkout(PIN, str(base)) as source:
        source_path = Path(source)
        stock_sources = {
            rel: (source_path / rel).read_text(encoding="utf-8")
            for rel in SOURCE_FILES
        }
        failures = patch_contract.validate(
            patch.read_text(encoding="utf-8"),
            stock_sources,
            ledger.read_text(encoding="utf-8"),
        )
        if failures:
            raise DriverError(f"unit A contract failed: {failures}")
        expected_patched = _expected_patched_source_hashes(base, patch, raw)
        with patchharness.applied(str(patch), PIN, source):
            observed_patched = {
                relative: sha256_file(source_path / relative)
                for relative in SOURCE_FILES
            }
            if observed_patched != expected_patched:
                raise DriverError(
                    "correctness patched-source sha differs from pin+patch model"
                )
            _write_raw_json(raw / "observed-patched-source-sha256.json",
                            observed_patched)
            build = attempt_dir / "build-trace"
            run_dir = attempt_dir / "run-trace"
            run_dir.mkdir()
            cmake = next(item["realpath"] for item in toolchain if item["name"] == "cmake")
            gcc = next(item["realpath"] for item in toolchain if item["name"] == "gcc")
            cxx = next(item["realpath"] for item in toolchain if item["name"] == "g++")
            nm_path = next(
                item["realpath"] for item in toolchain if item["name"] == "nm"
            )
            readelf_path = next(
                item["realpath"] for item in toolchain if item["name"] == "readelf"
            )
            configure = _configure_argv(
                source=source_path, build=build,
                tools={"cmake": cmake, "gcc": gcc, "g++": cxx},
                prefix=prefix, macros=[RUNG_MACRO], trace=1,
                third_party_sources=third_party_sources,
            )
            with patchharness.checkout(PIN, str(base)) as gate_stock_source:
                condition_gates = _require_condition_gates(
                    patched_source=source_path,
                    stock_source=Path(gate_stock_source),
                    tools={"cmake": cmake, "gcc": gcc, "g++": cxx},
                    configure_argv=configure,
                )
            correctness_deadline = Deadline.after(
                _load_json(repo / "tools/pegasus/policy.json")[
                    "silo_ladder_rung1"
                ]["build_cap_s"],
                "correctness configure/build/replay",
            )
            configured = _run(
                configure, timeout=900, deadline=correctness_deadline,
                stdout_path=raw / "configure.stdout",
                stderr_path=raw / "configure.stderr",
            )
            if configured.returncode:
                raise DriverError(f"correctness configure rc={configured.returncode}")
            build_argv = [
                cmake, "--build", str(build), "--target", "ycsb_silo.exe",
                "--verbose", "-j", "48",
            ]
            built = _run(
                build_argv,
                timeout=2700, deadline=correctness_deadline,
                stdout_path=raw / "build.stdout",
                stderr_path=raw / "build.stderr",
            )
            if built.returncode:
                raise DriverError(f"correctness build rc={built.returncode}")
            cache = build / "CMakeCache.txt"
            commands_path = build / "compile_commands.json"
            selected_cache = _validate_cmake_cache(
                cache, expected_c=gcc, expected_cxx=cxx,
                expected_flags=f"-D{RUNG_MACRO}=1", expected_trace="1",
            )
            _copy_raw(cache, raw / "CMakeCache.txt")
            _copy_raw(commands_path, raw / "compile_commands.json")
            invocations = compile_commands_for_sources(
                _load_json(commands_path), source_path,
            )
            replayed = []
            active_macros: set[str] = set()
            for invocation in invocations:
                active_macros.update(validate_compile_argv(
                    invocation["argv"], expected_macro=RUNG_MACRO,
                    expected_compiler_realpath=cxx,
                ))
                replayed.append(reexecute_compile_and_compare(
                    invocation, deadline=correctness_deadline,
                ))
            _write_raw_json(raw / "compile-replay.json", {
                "invocations": replayed,
            })
            _write_raw_json(raw / "cmake-cache-witness.json", {
                "sha256": sha256_file(cache),
                "selected_entries": selected_cache,
            })
            binary = build / "cc/silo/ycsb_silo.exe"
            nm = _run(
                [nm_path, "-g", "--defined-only", str(binary)], timeout=60,
                receipt_path=raw / "binary.nm.command.json",
                target_path=binary,
            )
            _create_text(raw / "binary.nm.txt", nm.stdout)
            _create_text(raw / "binary.nm.stderr", nm.stderr)
            if (
                nm.returncode != 0
                or sum(
                    line.split()[-1] == IDENTITY_SYMBOL
                    for line in nm.stdout.splitlines() if line.split()
                ) != 1
            ):
                raise DriverError("correctness activation identity witness failed")
            readelf = _run(
                [readelf_path, "-Ws", str(binary)], timeout=60,
                receipt_path=raw / "binary.readelf.command.json",
                target_path=binary,
            )
            _create_text(raw / "binary.readelf.txt", readelf.stdout)
            _create_text(raw / "binary.readelf.stderr", readelf.stderr)
            if readelf.returncode != 0:
                raise DriverError("correctness readelf witness failed")
            transaction = next(
                item for item in replayed
                if item["source_rel"] == SOURCE_FILES[0]
            )
            transaction_nm = _run(
                [
                    nm_path, "-g", "--defined-only", transaction["object_path"],
                ],
                receipt_path=raw / "transaction.nm.command.json",
                target_path=Path(transaction["object_path"]),
            )
            _create_text(raw / "transaction.nm.txt", transaction_nm.stdout)
            _create_text(raw / "transaction.nm.stderr", transaction_nm.stderr)
            object_identity_count = sum(
                line.split()[-1] == IDENTITY_SYMBOL
                for line in transaction_nm.stdout.splitlines() if line.split()
            )
            if transaction_nm.returncode != 0 or object_identity_count != 1:
                raise ContractFailure(
                    "correctness transaction object identity witness failed"
                )
            correctness_build = {
                "id": "correctness",
                "trace": True,
                "macros": [
                    macro for macro in (RUNG_MACRO, REPORT_MACRO)
                    if macro in active_macros
                ],
                "identity_defined_count": 1,
                "transaction_object_sha256": transaction["object_sha256"],
                "activation_ok": True,
                "condition_gates": condition_gates,
                "configure_argv": configure,
                "build_argv": build_argv,
                "binary_sha256": sha256_file(binary),
                "compile_invocations": replayed,
                "cmake_cache_sha256": sha256_file(cache),
                "source_sha256": observed_patched,
                "dependencies": dependencies,
                "raw_paths": [
                    "CMakeCache.txt", "compile_commands.json",
                    "compile-replay.json", "cmake-cache-witness.json",
                    "binary.nm.txt", "binary.readelf.txt",
                ],
            }
            run_result = _run(
                [str(binary), *CORRECTNESS_WORKLOAD], cwd=run_dir, timeout=300,
                stdout_path=raw / "run.stdout", stderr_path=raw / "run.stderr",
                receipt_path=raw / "run.command.json",
                target_path=binary,
            )
            if run_result.returncode:
                raise DriverError(f"correctness run rc={run_result.returncode}")
            verifier_result = _run(
                [
                    sys.executable, "-m", "orchestrator.verifier", "--json",
                    "--protocol", "silo", "--ccbench-root", str(source_path),
                    str(run_dir),
                ],
                cwd=repo, timeout=600, stdout_path=raw / "verifier.json",
                stderr_path=raw / "verifier.stderr",
            )
            verifier = _load_json(raw / "verifier.json")
            trace_files = []
            for trace in sorted(run_dir.glob("trace_*.log")):
                lines = trace.read_text(encoding="utf-8", errors="strict").splitlines()
                _copy_raw(trace, raw / "traces" / trace.name)
                trace_files.append({
                    "path": trace.name,
                    "commits": sum(line.startswith("C ") for line in lines),
                    "non_insert_write_witness": any(
                        len(parts := line.split()) == 6
                        and parts[0] == "W"
                        and parts[3] in {"U", "D"}
                        for line in lines
                    ),
                })
    leg = {
        "workload": {"argv": CORRECTNESS_WORKLOAD, "threads": 4},
        "build": correctness_build,
        "provenance": {
            "environment_scrubbed": True,
            "tools": toolchain,
            "ccbench_pin_full": PIN,
            "expected_patched_source_sha256": expected_patched,
            "observed_patched_source_sha256": observed_patched,
            "dependencies": dependencies,
            "third_party_sources": third_party_sources,
        },
        "verifier_rc": verifier_result.returncode,
        "verifier": verifier,
        "trace_files": trace_files,
        "raw_paths": [],
    }
    leg["raw_paths"] = _raw_manifest(raw)
    _write_raw_json(attempt_dir / "correctness.json", leg)
    return leg


def _gap_job_command(
    job_staging: Path, submit_receipt_path: Path,
    scheduler_deadline_epoch: int,
) -> dict[str, Any]:
    """PBS allocation 内 entry。schedule/receipt を束縛して raw attempt を作る。"""
    job_staging.mkdir(parents=True, exist_ok=True)
    submit = _load_json(submit_receipt_path)
    attempt_number = int(os.environ.get("IZANAGI_ATTEMPT_NUMBER", "1"))
    if attempt_number not in (1, 2):
        raise DriverError("attempt number must be 1 or 2")
    # Build/run machinery is deliberately kept behind this PBS-only seam.  The
    # wrapper supplies dependency prefixes and raw allocation material.
    required = (
        "PBS_JOBID", "IZANAGI_GFLAGS_INSTALL", "IZANAGI_GLOG_INSTALL",
        THIRD_PARTY_SOURCE_ROOT_ENV,
    )
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise DriverError(f"gap-job missing PBS environment: {missing}")
    repo = _repo_root()
    raw = job_staging / f"attempt-{attempt_number}" / "raw"
    raw.mkdir(parents=True)
    global _COMMAND_RECEIPT_ROOT, _COMMAND_RECEIPT_INDEX
    _COMMAND_RECEIPT_ROOT = raw / "commands"
    _COMMAND_RECEIPT_INDEX = 0
    schedule = _validate_submit_binding(
        submit, attempt_number=attempt_number, repo=repo,
    )
    failure = validate_schedule(schedule)
    if failure:
        raise DriverError(failure.detail)
    receipt_copy = job_staging / "submit-receipt.json"
    publish_create_only_json(receipt_copy, submit, staging_dir=job_staging)
    _write_raw_json(raw / "submit-receipt.json", submit)
    prologue = raw / "job-prologue"
    prologue.mkdir()
    for name in (
        "python.realpath", "python.version", "source-surface-status.txt",
        "source-head.txt", "ccbench-gitlink.txt", "qstat-f.stdout",
        "qstat-f.stderr", "scheduler-elapse.json", "load-before.txt",
        "pgrep-before.txt", "qstat-driver.stdout", "qstat-driver.stderr",
        "gflags-configure.stdout",
        "gflags-source-head.txt", "gflags-source-status.txt",
        "gflags-configure.stderr", "gflags-build.stdout",
        "gflags-build.stderr", "gflags-install.stdout",
        "gflags-install.stderr", "glog-configure.stdout",
        "glog-source-head.txt", "glog-source-status.txt",
        "glog-configure.stderr", "glog-build.stdout", "glog-build.stderr",
        "glog-install.stdout", "glog-install.stderr",
        "masstree-thirdparty-persistent-head.txt",
        "masstree-thirdparty-persistent-status.txt",
        "masstree-thirdparty-scratch-head.txt",
        "masstree-thirdparty-scratch-status.txt",
        "mimalloc-thirdparty-persistent-head.txt",
        "mimalloc-thirdparty-persistent-status.txt",
        "mimalloc-thirdparty-scratch-head.txt",
        "mimalloc-thirdparty-scratch-status.txt",
        "googletest-thirdparty-persistent-head.txt",
        "googletest-thirdparty-persistent-status.txt",
        "googletest-thirdparty-scratch-head.txt",
        "googletest-thirdparty-scratch-status.txt",
    ):
        source = job_staging / name
        if not source.is_file() or source.is_symlink():
            raise DriverError(f"required job prologue raw file is missing: {name}")
        _copy_raw(source, prologue / name)
    prologue_manifest_sha256 = _tree_manifest_sha256(prologue)
    _write_raw_json(raw / "schedule-receipt.json", schedule)
    base = repo / "external/ccbench"
    patch = repo / patch_contract.PATCH_PATH
    stock_sources: dict[str, str] = {}
    for relative in SOURCE_FILES:
        shown = _run(
            ["git", "-C", str(base), "show", f"{PIN}:{relative}"], timeout=60,
        )
        if shown.returncode != 0:
            raise DriverError(f"cannot read pinned source for contract: {relative}")
        stock_sources[relative] = shown.stdout
    unit_a_failures = patch_contract.validate(
        patch.read_text(encoding="utf-8"),
        stock_sources,
        (repo / "patches/ledger.json").read_text(encoding="utf-8"),
    )
    if unit_a_failures:
        raise DriverError(f"unit A contract failed in gap job: {unit_a_failures}")
    expected_source_hashes = _expected_patched_source_hashes(base, patch, raw)
    tools: list[dict[str, Any]] = []
    tool_paths: dict[str, str] = {}
    prefix = (
        os.environ["IZANAGI_GFLAGS_INSTALL"] + ";"
        + os.environ["IZANAGI_GLOG_INSTALL"]
    )
    third_party_sources = third_party_source_contract(repo)
    scratch = Path(os.environ.get("TMPDIR", "/tmp"))
    policy = _load_json(repo / "tools/pegasus/policy.json")[
        "silo_ladder_rung1"
    ]
    scheduler_elapse = _load_json(job_staging / "scheduler-elapse.json")
    scheduler_budget_s = float(scheduler_deadline_epoch) - time.time()
    if scheduler_budget_s <= 0:
        raise InfraFailure("timeout", "scheduler absolute deadline already expired")
    driver_budget_s = min(
        policy["walltime_s"] - policy["finalize_reserve_s"],
        scheduler_budget_s,
    )
    overall_deadline = Deadline.after(
        driver_budget_s,
        "PBS acquisition before finalize reserve",
    )
    build_records: list[dict[str, Any]] = []
    binaries: dict[str, Path] = {}
    patched_surface: dict[str, str] = {}
    condition_gates: list[dict[str, Any]] = []
    try:
        tools = capture_tool_identities()
        tool_paths = {item["name"]: item["realpath"] for item in tools}
        attestation = _attest_environment(
            raw,
            deadline=overall_deadline.capped(
                policy["attestation_cap_s"], "attestation group",
            ),
        )
        with patchharness.checkout(PIN, str(base)) as gate_stock_source:
            with patchharness.checkout(PIN, str(base)) as gate_rung_source:
                with patchharness.applied(str(patch), PIN, gate_rung_source):
                    perf_gate_configure = _configure_argv(
                        source=Path(gate_rung_source),
                        build=scratch / "condition-gate-rung-perf",
                        tools=tool_paths,
                        prefix=prefix,
                        macros=[RUNG_MACRO],
                        trace=0,
                        third_party_sources=third_party_sources,
                    )
                    condition_gates.extend(_require_condition_gates(
                        patched_source=Path(gate_rung_source),
                        stock_source=Path(gate_stock_source),
                        tools=tool_paths,
                        configure_argv=perf_gate_configure,
                    ))
                    liveness_gate_configure = _configure_argv(
                        source=Path(gate_rung_source),
                        build=scratch / "condition-gate-rung-liveness",
                        tools=tool_paths,
                        prefix=prefix,
                        macros=[RUNG_MACRO, REPORT_MACRO],
                        trace=0,
                        third_party_sources=third_party_sources,
                    )
                    condition_gates.extend(_require_condition_gates(
                        patched_source=Path(gate_rung_source),
                        stock_source=Path(gate_stock_source),
                        tools=tool_paths,
                        configure_argv=liveness_gate_configure,
                    ))
        build_deadline = overall_deadline.capped(
            policy["build_cap_s"], "three configure/build/replay group",
        )
        with patchharness.checkout(PIN, str(base)) as stock_source:
            stock = Path(stock_source)
            stock_record, stock_binary = _build_variant(
                variant="stock", source=stock,
                build=scratch / "build-stock", raw=raw,
                tool_paths=tool_paths, prefix=prefix, macros=[],
                deadline=build_deadline,
                third_party_sources=third_party_sources,
            )
            build_records.append(stock_record)
            binaries["stock"] = stock_binary
            with patchharness.checkout(PIN, str(base)) as rung_source:
                rung = Path(rung_source)
                with patchharness.applied(str(patch), PIN, str(rung)):
                    patched_surface = {
                        relative: sha256_file(rung / relative)
                        for relative in SOURCE_FILES
                    }
                    if patched_surface != expected_source_hashes:
                        raise DriverError(
                            "build tree patched-source sha256 differs from pin+patch model"
                        )
                    perf_record, perf_binary = _build_variant(
                        variant="rung-perf", source=rung,
                        build=scratch / "build-rung-perf", raw=raw,
                        tool_paths=tool_paths, prefix=prefix, macros=[RUNG_MACRO],
                        deadline=build_deadline,
                        third_party_sources=third_party_sources,
                    )
                    live_record, live_binary = _build_variant(
                        variant="rung-liveness", source=rung,
                        build=scratch / "build-rung-liveness", raw=raw,
                        tool_paths=tool_paths, prefix=prefix,
                        macros=[RUNG_MACRO, REPORT_MACRO],
                        deadline=build_deadline,
                        third_party_sources=third_party_sources,
                    )
                    build_records.extend([perf_record, live_record])
                    binaries.update({
                        "rung-perf": perf_binary,
                        "rung-liveness": live_binary,
                    })
                    if (
                        perf_record["transaction_object_sha256"]
                        != live_record["transaction_object_sha256"]
                    ):
                        raise DriverError(
                            "rung perf/liveness transaction.cc object SHA mismatch"
                        )

                    run_deadline = overall_deadline.capped(
                        policy["run_group_cap_s"], "28-run group",
                    )
                    performance_runs: list[dict[str, Any]] = []
                    for row in schedule["runs"]:
                        solo = _solo_check(
                            raw, row["ordinal"], deadline=run_deadline,
                        )
                        attestation["per_sample_solo_checks"].append(solo)
                        if solo["passed"] is not True:
                            raise InfraFailure(
                                "process_competition",
                                f"process/load competition before sample {row['ordinal']}",
                            )
                        run_raw = raw / "runs" / (
                            f"perf-{row['ordinal']:02d}-{row['workload']}-"
                            f"{row['variant']}-r{row['rep']}"
                        )
                        run_raw.mkdir(parents=True)
                        run_argv = [
                            str(binaries[row["variant"]]),
                            *WORKLOADS[row["workload"]]["argv"],
                        ]
                        started_at = utc_now()
                        run = _run(
                            run_argv,
                            cwd=run_raw, timeout=240, deadline=run_deadline,
                            stdout_path=run_raw / "stdout.txt",
                            stderr_path=run_raw / "stderr.txt",
                            receipt_path=run_raw / "run.command.json",
                            target_path=binaries[row["variant"]],
                        )
                        text = (run_raw / "stdout.txt").read_text(
                            encoding="utf-8", errors="strict"
                        )
                        completed_at = utc_now()
                        try:
                            parsed = parse_run_stdout(text, liveness=False)
                        except DriverError as exc:
                            raise InfraFailure("parse_failure", str(exc)) from exc
                        performance_runs.append({
                            "ordinal": row["ordinal"],
                            "workload": row["workload"],
                            "rep": row["rep"],
                            "variant": row["variant"],
                            "binary_id": row["variant"],
                            "workload_argv": list(
                                WORKLOADS[row["workload"]]["argv"]
                            ),
                            "argv": run_argv,
                            "started_at_utc": started_at,
                            "completed_at_utc": completed_at,
                            "returncode": run.returncode,
                            "throughput_tps": parsed["throughput_tps"],
                            "commit_count": parsed["commit_count"],
                            "batch_commit_count": parsed["batch_commit_count"],
                            "stdout_sha256": sha256_file(run_raw / "stdout.txt"),
                            "stderr_sha256": sha256_file(run_raw / "stderr.txt"),
                            "raw_path": run_raw.relative_to(raw).as_posix(),
                        })
                        if run.returncode != 0:
                            raise InfraFailure(
                                "nonzero_returncode",
                                f"performance run rc={run.returncode}: {row}",
                            )

                    performance_failure = _validate_performance(performance_runs)
                    if performance_failure is not None:
                        _write_raw_json(raw / "driver-failure.json", {
                            "schema_version":
                                "silo_ladder_rung1-driver-failure/v1",
                            "failure_class": "substantive-negative",
                            "reason_code": "performance_direction",
                            "message": performance_failure.detail,
                        })
                        _write_raw_json(
                            job_staging / "pending-gap-result.json", {
                            "schema_version": "silo_ladder_rung1-gap-job/v1",
                            "pbs_jobid": os.environ["PBS_JOBID"],
                            "attempt_number": attempt_number,
                            "schedule_receipt": schedule,
                            "status": "substantive-negative",
                            "failure_class": "substantive-negative",
                            "reason_code": "performance_direction",
                            "message": performance_failure.detail,
                            "performance_runs": performance_runs,
                            "builds": build_records,
                            "raw_paths": _raw_manifest(raw),
                        })
                        raise SubstantiveNegative(
                            performance_failure.detail + "; no retry"
                        )

                    liveness_runs: list[dict[str, Any]] = []
                    next_ordinal = 24
                    for workload in WORKLOADS:
                        for rep in (1, 2):
                            solo = _solo_check(
                                raw, next_ordinal, deadline=run_deadline,
                            )
                            attestation["per_sample_solo_checks"].append(solo)
                            if solo["passed"] is not True:
                                raise InfraFailure(
                                    "process_competition",
                                    f"process/load competition before sample {next_ordinal}",
                                )
                            run_raw = raw / "runs" / (
                                f"liveness-{next_ordinal:02d}-{workload}-r{rep}"
                            )
                            run_raw.mkdir(parents=True)
                            run_argv = [
                                str(binaries["rung-liveness"]),
                                *WORKLOADS[workload]["argv"],
                            ]
                            started_at = utc_now()
                            run = _run(
                                run_argv,
                                cwd=run_raw, timeout=240,
                                deadline=run_deadline,
                                stdout_path=run_raw / "stdout.txt",
                                stderr_path=run_raw / "stderr.txt",
                                receipt_path=run_raw / "run.command.json",
                                target_path=binaries["rung-liveness"],
                            )
                            try:
                                parsed = parse_run_stdout(
                                    (run_raw / "stdout.txt").read_text(
                                        encoding="utf-8", errors="strict"
                                    ),
                                    liveness=True,
                                )
                            except DriverError as exc:
                                raise InfraFailure(
                                    "parse_failure", str(exc),
                                ) from exc
                            completed_at = utc_now()
                            liveness_runs.append({
                                "ordinal": next_ordinal,
                                "workload": workload,
                                "rep": rep,
                                "variant": "rung-liveness",
                                "binary_id": "rung-liveness",
                                "workload_argv": list(WORKLOADS[workload]["argv"]),
                                "argv": run_argv,
                                "started_at_utc": started_at,
                                "completed_at_utc": completed_at,
                                "returncode": run.returncode,
                                "bounded_completion": run.returncode == 0,
                                "stdout_sha256": sha256_file(run_raw / "stdout.txt"),
                                "stderr_sha256": sha256_file(run_raw / "stderr.txt"),
                                "raw_path": run_raw.relative_to(raw).as_posix(),
                                **parsed,
                            })
                            if run.returncode != 0:
                                raise InfraFailure(
                                    "nonzero_returncode",
                                    f"liveness run rc={run.returncode}",
                                )
                            next_ordinal += 1
        collection_deadline = overall_deadline.capped(
            policy["collection_cap_s"], "raw collection/finalization",
        )
        collection_deadline.remaining()
    except SubstantiveNegative:
        raise
    except InfraFailure as exc:
        _write_raw_json(raw / "driver-failure.json", {
            "schema_version": "silo_ladder_rung1-driver-failure/v1",
            "failure_class": "infra",
            "reason_code": exc.reason_code,
            "message": exc.detail,
        })
        raise
    except (DriverError, OSError, subprocess.SubprocessError) as exc:
        _write_raw_json(raw / "driver-failure.json", {
            "schema_version": "silo_ladder_rung1-driver-failure/v1",
            "failure_class": "contract",
            "reason_code": "contract_failure",
            "message": str(exc),
        })
        raise

    collection_deadline.remaining()
    attestation["all_pass"] = (
        attestation["all_pass"]
        and len(attestation["per_sample_solo_checks"]) == 28
        and all(
            item["passed"] is True
            for item in attestation["per_sample_solo_checks"]
        )
    )
    performance_failure = None
    liveness_failure = _validate_liveness(liveness_runs)
    substantive_reason = (
        "performance_direction" if performance_failure is not None
        else "per_worker_ever_committed" if liveness_failure is not None
        else None
    )
    substantive = substantive_reason is not None
    attempt_record = {
        "attempt": attempt_number,
        "failure_class": "substantive-negative" if substantive else None,
        "reason_code": substantive_reason,
        "raw_root": f"attempt-{attempt_number}/raw",
        "attempt_receipt_sha256": None,
        "job_id": os.environ["PBS_JOBID"],
        "nonce": submit["nonce"],
        "submit_receipt_sha256": sha256_file(submit_receipt_path),
        "campaign_attempt_root_receipt": None,
    }
    attempts = (
        [submit["prior_attempt"], attempt_record]
        if submit["prior_attempt"] is not None else [attempt_record]
    )
    gap_leg = {
        "status": "substantive-negative" if substantive else "complete",
        "workloads": [
            {"id": name, **value} for name, value in WORKLOADS.items()
        ],
        "schedule_receipt": schedule,
        "condition_gates": condition_gates,
        "builds": build_records,
        "performance_runs": performance_runs,
        "liveness_runs": liveness_runs,
        "attestation": attestation,
        "attempts": attempts,
    }
    checks = {
        "correctness": False,
        "schedule": validate_schedule(schedule) is None,
        "per_worker_ever_committed": liveness_failure is None,
        "bounded_completion": all(
            run["returncode"] == 0 and run["bounded_completion"] is True
            for run in liveness_runs
        ),
        "performance_direction": not substantive,
        "activation": all(record["activation_ok"] for record in build_records),
        "attestation": attestation["all_pass"],
        "raw_recomputed": True,
    }
    result = {
        "schema_version": "silo_ladder_rung1-gap-job/v1",
        "pbs_jobid": os.environ["PBS_JOBID"],
        "attempt_number": attempt_number,
        "status": "substantive-negative" if substantive else "complete",
        "failure_class": "substantive-negative" if substantive else None,
        "reason_code": substantive_reason,
        "provenance": {
            "environment_scrubbed": True,
            "tools": tools,
            "third_party_sources": third_party_sources,
            "source_witness": {
                "submit_whole_tree_clean": submit["whole_tree_clean"],
                "job_source_surface_clean": True,
                "job_source_exclusions": ["output"],
                "job_prologue_manifest_sha256": prologue_manifest_sha256,
                "expected_patched_source_sha256": expected_source_hashes,
                "observed_patched_source_sha256": patched_surface,
            },
        },
        "gap_leg": gap_leg,
        "checks": checks,
        "raw_paths": _raw_manifest(raw),
    }
    collection_deadline.remaining()
    if substantive:
        _write_raw_json(raw / "driver-failure.json", {
            "schema_version": "silo_ladder_rung1-driver-failure/v1",
            "failure_class": "substantive-negative",
            "reason_code": substantive_reason,
            "message": f"substantive negative: {substantive_reason}",
        })
        _write_raw_json(job_staging / "pending-gap-result.json", result)
        raise SubstantiveNegative(
            f"substantive negative: {substantive_reason}; no retry"
        )
    _write_raw_json(job_staging / "gap-result.json", result)
    return result


def _binding(repo: Path) -> dict[str, Any]:
    contract = env_contract.lookup("pegasus")
    calibration = _load_json(repo / contract.calibration_ref.path)
    verifier_module = repo / "orchestrator/verifier/report.py"
    refs = {
        "patch": repo / patch_contract.PATCH_PATH,
        "ledger": repo / "patches/ledger.json",
        "driver": Path(__file__).resolve(),
        "pbs_job": repo / "tools/pegasus/silo_ladder_rung1.sh",
        "submitter": repo / "tools/pegasus/submit_silo_ladder_rung1.sh",
        "verifier_module": verifier_module,
        "policy": repo / "tools/pegasus/policy.json",
    }
    result = {
        key: {"path": path.relative_to(repo).as_posix(), "sha256": sha256_file(path)}
        for key, path in refs.items()
    }
    result.update({
        "runtime_modules": runtime_modules_binding(repo),
        "ccbench_pin_full": PIN,
        "calibration": {
            "path": contract.calibration_ref.path,
            "sha256": sha256_file(repo / contract.calibration_ref.path),
            "contract_sha256": contract.contract_sha256,
            "quality_status": calibration["quality"]["status"],
            "records": calibration["saturation"]["records"],
            "threads": calibration["threads"],
            "transfer_scope": ["build_contract", "records", "threads"],
        },
    })
    return result


def _collect_command(
    correctness_json: Path, job_staging: Path, stdout: Path,
    stderr: Path, output: Path,
) -> Path:
    collect_deadline = Deadline.after(
        _load_json(_repo_root() / "tools/pegasus/policy.json")[
            "silo_ladder_rung1"
        ]["collection_cap_s"],
        "post-job collection/finalization",
    )
    correctness = _load_json(correctness_json)
    gap = _load_json(job_staging / "gap-result.json")
    success_path = job_staging / "success.json"
    failure_path = job_staging / "failure.json"
    if failure_path.is_file() and not failure_path.is_symlink():
        wrapper_failure = _load_json(failure_path)
        if not _exact_keys(wrapper_failure, {
            "schema_version", "pbs_jobid", "rc", "stage", "message",
            "recorded_epoch", "failure_class", "reason_code",
            "attempt_number",
        }) or (
            wrapper_failure["schema_version"]
            != "silo_ladder_rung1-failure/v1"
            or wrapper_failure["stage"] not in WRAPPER_STAGES
            or wrapper_failure["failure_class"]
            not in {"infra", "contract", "substantive-negative"}
            or (
                wrapper_failure["failure_class"] == "infra"
                and wrapper_failure["reason_code"] not in INFRA_REASON_CODES
            )
        ):
            raise ContractFailure("wrapper failure receipt schema is not closed")
        if wrapper_failure["failure_class"] == "infra":
            raise InfraFailure(
                wrapper_failure["reason_code"],
                "job wrapper failed after/beside driver: "
                + wrapper_failure["stage"],
            )
        raise ContractFailure(
            "job wrapper contract failure: " + wrapper_failure["stage"]
        )
    if gap.get("status") != "complete":
        if (
            gap.get("failure_class") == "infra"
            and gap.get("reason_code") in INFRA_REASON_CODES
        ):
            raise InfraFailure(
                gap["reason_code"],
                f"gap attempt is an infrastructure failure: "
                f"{gap.get('message', 'no detail')}",
            )
        raise ContractFailure(
            f"gap attempt is not complete: {gap.get('reason_code', 'unknown')}"
        )
    if not success_path.is_file() or success_path.is_symlink():
        raise InfraFailure(
            "nonzero_returncode",
            "gap-result is complete but final success sentinel is absent",
        )
    attempt_number = gap["attempt_number"]
    source_raw = job_staging / f"attempt-{attempt_number}" / "raw"
    raw_root = job_staging / f"raw-bundle-attempt-{attempt_number}"
    active_root = raw_root / "attempts" / str(attempt_number)
    _copy_tree_create_only(source_raw, active_root)
    collect_deadline.remaining()
    global _COMMAND_RECEIPT_ROOT, _COMMAND_RECEIPT_INDEX
    # active attempt はこの後 self-manifest/receipt で封印する。collect 時の
    # validation subprocess は attempt 外へ隔離し、top-level manifest だけで束縛する。
    _COMMAND_RECEIPT_ROOT = raw_root / "commands-collect"
    _COMMAND_RECEIPT_INDEX = 0
    submit = _load_json(job_staging / "submit-receipt.json")
    if failure_path.exists():
        raise ContractFailure("job failure receipt exists beside success sentinel")
    success = _load_json(success_path)
    if (
        not _exact_keys(success, {
            "schema_version", "pbs_jobid", "exit_status", "completed_at_utc",
        })
        or success["schema_version"]
        != "silo_ladder_rung1-success-sentinel/v1"
        or success["exit_status"] != 0
    ):
        raise ContractFailure("job success sentinel is invalid")
    if (
        submit.get("bindings", {}).get("correctness_sha256")
        != sha256_file(correctness_json)
    ):
        raise DriverError("correctness JSON differs from submit receipt binding")
    frozen = submit["bindings"]
    collect_current = {
        "job_script_sha256": sha256_file(
            _repo_root() / "tools/pegasus/silo_ladder_rung1.sh"
        ),
        "driver_sha256": sha256_file(Path(__file__).resolve()),
        "patch_sha256": sha256_file(
            _repo_root() / patch_contract.PATCH_PATH
        ),
        "ledger_sha256": sha256_file(
            _repo_root() / "patches/ledger.json"
        ),
        "submitter_sha256": sha256_file(
            _repo_root() / "tools/pegasus/submit_silo_ladder_rung1.sh"
        ),
        "verifier_module_sha256": sha256_file(
            _repo_root() / "orchestrator/verifier/report.py"
        ),
        "policy_sha256": sha256_file(
            _repo_root() / "tools/pegasus/policy.json"
        ),
        "runtime_modules_sha256": runtime_modules_sha256(_repo_root()),
    }
    if any(frozen.get(key) != value for key, value in collect_current.items()):
        raise ContractFailure("collect observed source drift from submit receipt")
    if frozen.get("third_party_heads") != {
        item["name"]: item["pin"] for item in third_party_policy(_repo_root())
    }:
        raise ContractFailure("collect third-party HEAD binding drift")
    schedule_bytes = (
        json.dumps(
            gap["gap_leg"]["schedule_receipt"],
            ensure_ascii=False, sort_keys=True, indent=2,
        ) + "\n"
    ).encode("utf-8")
    if frozen.get("schedule_sha256") != sha256_bytes(schedule_bytes):
        raise ContractFailure("collect schedule drift from submit receipt")
    campaign_ref = submit["campaign_root_receipt"]
    campaign_path = _repo_root() / campaign_ref["path"]
    if (
        sha256_file(campaign_path) != campaign_ref["sha256"]
        or _load_json(campaign_path)["bindings"][
            "expected_patched_source_sha256"
        ] != _expected_patched_source_hashes(
            _repo_root() / "external/ccbench",
            _repo_root() / patch_contract.PATCH_PATH,
        )
    ):
        raise ContractFailure("collect campaign root/source model drift")
    submit_id = submit.get("qsub", {}).get("request_id")
    gap_id = gap.get("pbs_jobid")
    if (
        type(submit_id) is not str or type(gap_id) is not str
        or _normalize_job_id(submit_id) != _normalize_job_id(gap_id)
    ):
        raise DriverError(
            f"submit/gap job ID mismatch: submit={submit_id!r} gap={gap_id!r}"
        )
    if not _scheduler_name_matches(stdout, "stdout", submit_id):
        raise DriverError("scheduler stdout filename does not carry job ID")
    if not _scheduler_name_matches(stderr, "stderr", submit_id):
        raise DriverError("scheduler stderr filename does not carry job ID")
    _copy_raw(stdout, active_root / "scheduler.stdout")
    _copy_raw(stderr, active_root / "scheduler.stderr")
    collect_deadline.remaining()
    stderr_text = stderr.read_text(encoding="utf-8", errors="replace")
    accounting = validate_nqsv_accounting_epilogue(stderr_text, submit_id)
    _create_text(active_root / "pbs-accounting.txt", "\n".join(accounting) + "\n")
    correctness_raw = correctness_json.parent / "raw"
    _copy_tree_create_only(correctness_raw, raw_root / "correctness")
    collect_deadline.remaining()
    repo = _repo_root()
    campaign_ref = submit["campaign_root_receipt"]
    _copy_raw(
        repo / campaign_ref["path"],
        raw_root / "campaign-identity-receipt.json",
    )
    if attempt_number == 2:
        prior = submit["prior_attempt"]
        prior_source = repo / prior["raw_root"]
        if (
            sha256_file(prior_source / "attempt-receipt.json")
            != prior["attempt_receipt_sha256"]
        ):
            raise ContractFailure("prior attempt receipt hash drift")
        validate_attempt_subtree(prior_source, 1)
        _copy_tree_create_only(prior_source, raw_root / "attempts/1")
    current_attempt = next(
        item for item in gap["gap_leg"]["attempts"]
        if item["attempt"] == attempt_number
    )
    current_attempt["raw_root"] = f"attempts/{attempt_number}"
    if attempt_number == 2:
        gap["gap_leg"]["attempts"][0]["raw_root"] = "attempts/1"
    attempt_receipt_path = write_attempt_receipt(active_root, attempt_number)
    current_attempt["attempt_receipt_sha256"] = sha256_file(attempt_receipt_path)
    write_raw_manifest(active_root)
    campaign_attempt_root = write_campaign_attempt_root_receipt(
        repo, submit, attempt=attempt_number, job_id=gap["pbs_jobid"],
        attempt_receipt_sha256=current_attempt["attempt_receipt_sha256"],
        failure_class=None, reason_code=None,
        submit_receipt_sha256=sha256_file(job_staging / "submit-receipt.json"),
    )
    current_attempt["campaign_attempt_root_receipt"] = {
        "path": campaign_attempt_root.relative_to(repo).as_posix(),
        "sha256": sha256_file(campaign_attempt_root),
    }
    seals = raw_root / "campaign-attempt-root-receipts"
    _copy_raw(campaign_attempt_root, seals / f"{attempt_number}.json")
    if attempt_number == 2:
        prior_seal = repo / gap["gap_leg"]["attempts"][0][
            "campaign_attempt_root_receipt"
        ]["path"]
        _copy_raw(prior_seal, seals / "1.json")
    identity_receipt = _load_json(raw_root / "campaign-identity-receipt.json")
    final_attempts = [
        _load_json(path)
        for path in sorted(seals.glob("*.json"), key=lambda item: int(item.stem))
    ]
    _write_raw_json(raw_root / "campaign-root-receipt.json", {
        "schema_version": "silo_ladder_rung1-campaign-root-final/v1",
        "campaign_id": identity_receipt["campaign_id"],
        "schedule_receipt": identity_receipt["schedule_receipt"],
        "bindings": identity_receipt["bindings"],
        "attempts": final_attempts,
    })
    collect_deadline.remaining()
    _write_raw_json(raw_root / "gap-result-receipt.json", {
        "schema_version": "silo_ladder_rung1-gap-receipt/v1",
        "gap_leg": gap["gap_leg"],
    })
    _write_raw_json(raw_root / "provenance-receipt.json", {
        "schema_version": "silo_ladder_rung1-provenance-receipt/v1",
        "provenance": gap["provenance"],
    })
    document = {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": ARTIFACT_ID,
        "generated_at_utc": utc_now(),
        "classification": {
            "evaluation_role": "ability_probe",
            "research_goal_eligible": False,
            "recovery_measurement_eligibility": False,
        },
        "activation_contract": {
            "macro": RUNG_MACRO,
            "symbols": [IDENTITY_SYMBOL],
        },
        "binding": _binding(repo),
        "provenance": gap["provenance"],
        "correctness_leg": correctness,
        "gap_leg": gap["gap_leg"],
        "retry_policy": {
            "max_attempts": 2,
            "infra_reason_codes": sorted(INFRA_REASON_CODES),
            "substantive_negative_retried": False,
        },
        "limitations": {
            "raw_object_binary_bytes_retained": False,
            "nqsv_scheduler_exit_status": "unavailable",
            "third_party_rederivation": "sha256-chain-consistency-only",
        },
        "raw_bundle": {"root": raw_root.relative_to(repo).as_posix(), "paths": []},
        "checks": {
            "correctness": False,
            "schedule": False,
            "per_worker_ever_committed": False,
            "bounded_completion": False,
            "performance_direction": False,
            "activation": False,
            "attestation": False,
            "raw_recomputed": False,
        },
        "all_pass": False,
    }
    binding_failures = validate_current_bindings(document, repo)
    write_raw_manifest(raw_root)
    collect_deadline.remaining()
    document["raw_bundle"]["paths"] = validate_raw_manifest(raw_root)
    build_by_id = {
        item["id"]: item for item in document["gap_leg"]["builds"]
    }
    activation_ok = (
        len(document["gap_leg"]["builds"]) == 3
        and len(build_by_id) == 3
        and set(build_by_id) == {"stock", "rung-perf", "rung-liveness"}
        and build_by_id["stock"]["macros"] == []
        and build_by_id["stock"]["identity_defined_count"] == 0
        and build_by_id["rung-perf"]["macros"] == [RUNG_MACRO]
        and build_by_id["rung-perf"]["identity_defined_count"] == 1
        and build_by_id["rung-liveness"]["macros"]
        == [RUNG_MACRO, REPORT_MACRO]
        and build_by_id["rung-liveness"]["identity_defined_count"] == 1
        and build_by_id["rung-perf"]["transaction_object_sha256"]
        == build_by_id["rung-liveness"]["transaction_object_sha256"]
    )
    attestation = document["gap_leg"]["attestation"]
    checks = {
        "correctness": not _validate_correctness(correctness),
        "schedule": validate_schedule(
            document["gap_leg"]["schedule_receipt"]
        ) is None,
        "per_worker_ever_committed": _validate_liveness(
            document["gap_leg"]["liveness_runs"]
        ) is None,
        "bounded_completion": all(
            item["returncode"] == 0
            and item["bounded_completion"] is True
            for item in document["gap_leg"]["liveness_runs"]
        ),
        "performance_direction": _validate_performance(
            document["gap_leg"]["performance_runs"]
        ) is None,
        "activation": activation_ok,
        "attestation": (
            attestation["contract_sha256"]
            == document["binding"]["calibration"]["contract_sha256"]
            and attestation["calibration_sha256"]
            == document["binding"]["calibration"]["sha256"]
            and len(attestation["per_sample_solo_checks"]) == 28
            and [item["ordinal"] for item in attestation["per_sample_solo_checks"]]
            == list(range(28))
            and attestation["all_pass"] is True
            and all(item["passed"] is True
                    for item in attestation["per_sample_solo_checks"])
        ),
        "raw_recomputed": False,
    }
    document["checks"] = checks
    raw_failures = validate_raw_bundle(document, raw_root)
    checks["raw_recomputed"] = not raw_failures
    document["all_pass"] = all(checks.values())
    failures = (
        validate_evidence(document)
        + raw_failures
        + binding_failures
    )
    if failures:
        raise DriverError(f"collected evidence rejected: {failures}")
    collect_deadline.remaining()
    return publish_create_only_json(output, document, staging_dir=output.parent)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    correctness = commands.add_parser("correctness")
    correctness.add_argument("--attempt-dir", type=Path, required=True)
    gap = commands.add_parser("gap-job")
    gap.add_argument("--job-staging", type=Path, required=True)
    gap.add_argument("--submit-receipt", type=Path, required=True)
    gap.add_argument("--scheduler-deadline-epoch", type=int, required=True)
    collect = commands.add_parser("collect")
    collect.add_argument("--correctness-json", type=Path, required=True)
    collect.add_argument("--job-staging", type=Path, required=True)
    collect.add_argument("--stdout", type=Path, required=True)
    collect.add_argument("--stderr", type=Path, required=True)
    collect.add_argument("--output", type=Path, required=True)
    verify = commands.add_parser("verify-result")
    verify.add_argument("--json", type=Path, required=True, dest="json_path")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    scrub_environment(install=True)
    try:
        if args.command == "correctness":
            _correctness_command(args.attempt_dir)
        elif args.command == "gap-job":
            _gap_job_command(
                args.job_staging, args.submit_receipt,
                args.scheduler_deadline_epoch,
            )
        elif args.command == "collect":
            _collect_command(
                args.correctness_json, args.job_staging, args.stdout,
                args.stderr, args.output,
            )
        elif args.command == "verify-result":
            document = _load_json(args.json_path)
            repo = _repo_root()
            failures = validate_evidence(document)
            if not failures and type(document) is dict:
                raw_root = repo / document["raw_bundle"]["root"]
                failures += (
                    validate_raw_bundle(document, raw_root)
                    + validate_current_bindings(document, repo)
                )
            if failures:
                print(json.dumps(
                    {"ok": False, "failures": [
                        {"reason_code": item.reason_code, "detail": item.detail}
                        for item in failures
                    ]},
                    ensure_ascii=False, sort_keys=True,
                ), file=sys.stderr)
                return 1
        return 0
    except (DriverError, OSError, subprocess.SubprocessError) as exc:
        print(f"silo_ladder_rung1: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
