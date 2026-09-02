#!/usr/bin/env python3
"""Measure or explicitly certify Cicada adaptive-backoff constants.

The default performance mode is unchanged: it builds trace-disabled binaries,
never uses perf, and makes no correctness claim.  Only ``--mode certify`` runs
the trace-enabled, fail-closed serializability contract.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing
import os
import re
import resource
import signal
import statistics
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from orchestrator.calibrator.runner import measure_point  # noqa: E402
from orchestrator.campaign import buildcache, env_contract, site_policy, source_digest  # noqa: E402
from orchestrator.campaign.build_admission import (  # noqa: E402
    GeneratorId,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.model import Genome  # noqa: E402
from orchestrator.campaign.patchharness import applied, assert_pinned_clean  # noqa: E402
from orchestrator.campaign.pin import CURRENT_PIN  # noqa: E402

SCHEMA_VERSION = "izanagi-cicada-adaptive-3const-probe/v1"
CERTIFICATION_SCHEMA_VERSION = "izanagi-cicada-adaptive-3const-certification/v1"
GROUP_RECEIPT_SCHEMA_VERSION = (
    "izanagi-cicada-adaptive-3const-certification-group/v1"
)
NOT_CERTIFIED = (
    "trace-disabled performance runs only; no serializability check was run"
)
PIN_FULL = "511c9538e4e8efa54b45cda62e72389ed3b706ec"
PATCH = ROOT / "patches" / "cicada-adaptive-params.patch"

CONTRACT = env_contract.lookup("pegasus")
ENV_TAG = CONTRACT.env_tag
CLOCKS_PER_US = CONTRACT.clocks_per_us
NUMA = list(CONTRACT.numactl)

LOGICAL_CORES = 48
DEFAULT_THREADS = (48,)
DEFAULT_WORKLOADS = ("write-heavy", "balanced", "read-heavy")
EXTIME = 3
RUN_TIMEOUT_S = 180.0

CERT_RECORDS = 1_000_000
CERT_THREADS = (48,)
CERT_EXTIME = 3
CERT_REPS_PER_JOB = 1
CERT_SLOTS = tuple(range(8))
CERT_WORKLOADS = ("write-heavy", "balanced", "read-heavy")
POSITIVE_CONTROL_EXPECTED_COMMITS = 288
POSITIVE_CONTROL_TIMEOUT_S = 120.0
DEFAULT_VERIFIER_TIMEOUT_S = 5_400.0
DEFAULT_BUILD_BUDGET_S = 900.0
DEFAULT_PROLOGUE_BUDGET_S = 540.0
DEFAULT_OUTER_WALLTIME_S = 8_100.0
DEFAULT_EXIT_MARGIN_S = 300.0
GROUP_RECEIPT_WAIT_S = 300.0
POSITIVE_CONTROL_TRACE = (
    ROOT / "orchestrator" / "tests" / "fixtures" / "r8_silo_broken_norw"
)
VERIFIER_ENTRY = ROOT / "orchestrator" / "verify.py"
VERIFIER_PACKAGE = ROOT / "orchestrator" / "verifier"
ALLOWED_GROUP_CLAIM = (
    "固定条件 (records=1,000,000 / threads=48 / extime=3 / max_ope=10 / "
    "zipf=0.9 / rmw=0、workload rr5・rr50・rr95、独立反復 8、計 24 trace) "
    "の下で、調整済み定数の trace-enabled 走行 24 件すべてが verifier で "
    "certified serializable となり、anomaly を 1 件も観測しなかった。"
)
CLAIM_LIMITATIONS = (
    "固定条件外へ直列化可能性を一般化しない",
    "未測定の thread 数・records・extime・workload へ外挿しない",
    "trace-disabled performance 値そのものが認証されたとは表現しない",
    "RNG seed を制御していないため形式的信頼度を算出しない",
)

STOCK_STEP_US = 100.0
STOCK_INCR_MILLI = 100_000
STOCK_MAX_US = 1_000
STOCK_UPDATE_US = 10

BASE = {
    "NO_WAIT_LOCKING_IN_VALIDATION": 1,
    "NO_WAIT_OF_TICTOC": 0,
    "WAL": 0,
}

WORKLOADS = {
    "write-heavy": {
        "ycsb_zipf_skew": "0.9",
        "ycsb_rratio": "5",
        "ycsb_rmw": "0",
        "ycsb_max_ope": "10",
    },
    "balanced": {
        "ycsb_zipf_skew": "0.9",
        "ycsb_rratio": "50",
        "ycsb_rmw": "0",
        "ycsb_max_ope": "10",
    },
    "read-heavy": {
        "ycsb_zipf_skew": "0.9",
        "ycsb_rratio": "95",
        "ycsb_rmw": "0",
        "ycsb_max_ope": "10",
    },
}

_LABEL_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_INTEGER_RE = re.compile(r"[0-9]+")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")


@dataclass(frozen=True)
class Cell:
    """One runtime grid cell, normalized to an exact 1/1000 us build value."""

    label: str
    back_off: int
    step_us: float
    ceiling_us: int
    update_us: int

    @property
    def incr_milli(self) -> int:
        return int(Decimal(str(self.step_us)) * 1000)

    @property
    def is_stock_control(self) -> bool:
        return is_stock_control(self)


CERT_CELL = Cell("tuned", 1, 1.0, 1_000, 2_560)


class CertificationReject(RuntimeError):
    """One fail-closed certification rejection with a stable reason."""

    def __init__(self, reason: str, detail: str):
        self.reason = reason
        self.detail = detail
        super().__init__(f"{reason}: {detail}")


def is_stock_control(cell: Cell) -> bool:
    """Return true only for exact stock adaptive settings."""
    return (
        cell.back_off == 1
        and cell.step_us == STOCK_STEP_US
        and cell.ceiling_us == STOCK_MAX_US
        and cell.update_us == STOCK_UPDATE_US
    )


def _parse_positive_integer(text: str, field: str) -> int:
    if _INTEGER_RE.fullmatch(text) is None:
        raise ValueError(f"{field} must be a positive integer: {text!r}")
    value = int(text)
    if value <= 0:
        raise ValueError(f"{field} must be positive: {value}")
    return value


def _parse_step_us(text: str) -> tuple[float, int]:
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"step_us is not a decimal: {text!r}") from exc
    if not value.is_finite() or value <= 0:
        raise ValueError(f"step_us must be finite and positive: {text!r}")
    milli = value * 1000
    integral = milli.to_integral_value()
    if milli != integral:
        raise ValueError(
            f"step_us cannot be represented exactly in 1/1000 us: {text!r}"
        )
    return float(value), int(integral)


def parse_cells(text: str) -> tuple[Cell, ...]:
    """Parse ``label:back_off:step_us:ceiling_us:update_us`` cells."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("cells must not be empty")
    cells: list[Cell] = []
    labels: set[str] = set()
    for index, raw_cell in enumerate(text.split(",")):
        fields = [field.strip() for field in raw_cell.split(":")]
        if len(fields) != 5 or any(not field for field in fields):
            raise ValueError(
                f"cell {index} must have five nonempty colon-separated fields: "
                f"{raw_cell!r}"
            )
        label, back_off_text, step_text, ceiling_text, update_text = fields
        if _LABEL_RE.fullmatch(label) is None:
            raise ValueError(f"cell label is unsafe: {label!r}")
        if label in labels:
            raise ValueError(f"duplicate cell label: {label!r}")
        if back_off_text not in {"0", "1"}:
            raise ValueError(f"back_off must be 0 or 1: {back_off_text!r}")
        step_us, incr_milli = _parse_step_us(step_text)
        ceiling_us = _parse_positive_integer(ceiling_text, "ceiling_us")
        update_us = _parse_positive_integer(update_text, "update_us")
        cell = Cell(label, int(back_off_text), step_us, ceiling_us, update_us)
        if cell.incr_milli != incr_milli:
            raise ValueError(f"step_us normalization changed value: {step_text!r}")
        cells.append(cell)
        labels.add(label)
    if not cells:
        raise ValueError("cells must not be empty")
    return tuple(cells)


_parse_cells = parse_cells


def _validate_grid_contract(cells: tuple[Cell, ...]) -> None:
    disabled = [cell for cell in cells if cell.back_off == 0]
    if len(disabled) != 1 or disabled[0] != Cell(
        "none", 0, STOCK_STEP_US, STOCK_MAX_US, STOCK_UPDATE_US
    ):
        raise ValueError(
            "grid must contain exactly none:0:100:1000:10 as its disabled cell"
        )
    if sum(cell.is_stock_control for cell in cells) != 1:
        raise ValueError("grid must contain exactly one stock adaptive control")
    configurations = {
        (cell.back_off, cell.incr_milli, cell.ceiling_us, cell.update_us)
        for cell in cells
    }
    if len(configurations) != len(cells):
        raise ValueError("grid contains duplicate build configurations")


def _parse_threads(text: str) -> tuple[int, ...]:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("threads must not be empty")
    values = []
    for token in text.split(","):
        token = token.strip()
        if _INTEGER_RE.fullmatch(token) is None:
            raise ValueError(f"thread count must be an integer: {token!r}")
        value = int(token)
        if value <= 0 or value > LOGICAL_CORES:
            raise ValueError(f"thread count is outside 1..{LOGICAL_CORES}: {value}")
        values.append(value)
    if len(set(values)) != len(values):
        raise ValueError(f"thread list contains duplicates: {text!r}")
    return tuple(values)


def _parse_workloads(text: str) -> tuple[str, ...]:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("workloads must not be empty")
    values = tuple(token.strip() for token in text.split(","))
    if any(not token for token in values):
        raise ValueError(f"workload list contains an empty item: {text!r}")
    unknown = [token for token in values if token not in WORKLOADS]
    if unknown:
        raise ValueError(f"unknown workloads: {unknown}")
    if len(set(values)) != len(values):
        raise ValueError(f"workload list contains duplicates: {text!r}")
    return values


def _nonnegative_int(text: str) -> int:
    value = int(text)
    if value < 0:
        raise argparse.ArgumentTypeError("must be nonnegative")
    return value


def _positive_int(text: str) -> int:
    value = int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return value


def _ccbench_head(submodule: Path) -> str:
    head = subprocess.run(
        ["git", "-C", str(submodule), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if CURRENT_PIN != PIN_FULL[: len(CURRENT_PIN)] or head != PIN_FULL:
        raise RuntimeError(
            f"ccbench HEAD {head!r} does not match required pin {PIN_FULL!r}"
        )
    return head


@contextmanager
def isolated_checkout(submodule: Path, pin_commit: str):
    """Create a node-local ``--shared`` clone under ``$TMPDIR``."""
    tmpdir = os.environ.get("TMPDIR")
    if not tmpdir:
        raise RuntimeError("TMPDIR is required for the node-local checkout")
    path = Path(tmpdir) / "ccbench-src"
    if path.exists():
        raise FileExistsError(f"isolated checkout already exists: {path}")
    subprocess.run(
        ["git", "clone", "--shared", "--no-checkout", str(submodule), str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "checkout", "--detach", pin_commit],
        check=True,
        capture_output=True,
        text=True,
    )
    assert_pinned_clean(str(path), pin_commit)
    try:
        yield str(path)
    finally:
        assert_pinned_clean(str(path), pin_commit)


def genome_for(cell: Cell) -> Genome:
    return Genome(
        "silo",
        {
            **BASE,
            "BACK_OFF": cell.back_off,
            "BACKOFF_INCR_MILLI": cell.incr_milli,
            "BACKOFF_MAX_US": cell.ceiling_us,
            "BACKOFF_UPDATE_US": cell.update_us,
        },
    )


def _cpu_seconds() -> float:
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime


def _assert_single_tenant() -> None:
    """Load the existing tenant gate only after a concrete mode is selected."""
    from orchestrator.campaign.p2_2 import _assert_single_tenant as check

    check()


def _validate_output_path(out: Path) -> None:
    if out.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {out}")


def _positive_float(text: str) -> float:
    try:
        value = float(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive number") from exc
    if not value > 0:
        raise argparse.ArgumentTypeError("must be a positive number")
    return value


def _certification_contract(args: argparse.Namespace) -> tuple[Cell, str, int]:
    """Return the exact one-request certification axes or reject widening."""
    cells = parse_cells(args.cells)
    workloads = _parse_workloads(args.workloads)
    threads = _parse_threads(args.threads)
    if cells != (CERT_CELL,):
        raise CertificationReject(
            "certification-cell-mismatch",
            "certify requires exactly tuned:1:1:1000:2560",
        )
    if len(workloads) != 1 or workloads[0] not in CERT_WORKLOADS:
        raise CertificationReject(
            "certification-workload-mismatch",
            "certify requires exactly one of write-heavy, balanced, read-heavy",
        )
    if threads != CERT_THREADS or args.extime != CERT_EXTIME:
        raise CertificationReject(
            "certification-workload-shape-mismatch",
            "certify requires records=1000000, threads=48, extime=3",
        )
    if args.reps_per_job != CERT_REPS_PER_JOB:
        raise CertificationReject(
            "certification-repetition-mismatch",
            "certify requires reps-per-job=1",
        )
    if args.rep_index not in CERT_SLOTS:
        raise CertificationReject(
            "certification-slot-mismatch",
            "certify requires rep-index in 0..7",
        )
    if (
        args.group_receipt_out is None
        or args.performance_artifact is None
        or args.performance_artifact_sha256 is None
        or args.expected_verifier_identity is None
        or args.expected_verifier_identity_sha256 is None
        or args.attempt_id is None
    ):
        raise CertificationReject(
            "certification-group-binding-missing",
            "certify requires group, performance, verifier, and attempt bindings",
        )
    if _LABEL_RE.fullmatch(args.attempt_id) is None:
        raise CertificationReject(
            "certification-attempt-invalid", "attempt id is not a safe exact label"
        )
    if any(
        not path.is_absolute()
        for path in (
            args.group_receipt_out,
            args.performance_artifact,
            args.expected_verifier_identity,
        )
    ):
        raise CertificationReject(
            "certification-group-binding-invalid",
            "group/performance/verifier binding paths must be absolute",
        )
    if (
        type(args.prologue_elapsed_s) is not float
        or args.prologue_elapsed_s < 0
        or type(args.prologue_cpu_s) is not float
        or args.prologue_cpu_s < 0
    ):
        raise CertificationReject(
            "certification-prologue-measurement-invalid",
            "prologue elapsed/CPU measurements must be nonnegative",
        )
    result_paths = [path.resolve(strict=False) for path in args.group_result_path]
    if (
        len(result_paths) != 24
        or len(set(result_paths)) != 24
        or any(not path.is_absolute() for path in args.group_result_path)
        or Path(args.out).resolve(strict=False) not in set(result_paths)
    ):
        raise CertificationReject(
            "certification-result-path-set-invalid",
            "certify requires 24 unique absolute result paths including --out",
        )
    inner_budget = (
        args.prologue_budget_s
        + args.build_budget_s
        + RUN_TIMEOUT_S
        + POSITIVE_CONTROL_TIMEOUT_S
        + args.verifier_timeout_s
        + args.exit_margin_s
    )
    if not inner_budget < args.outer_walltime_s:
        raise CertificationReject(
            "certification-time-budget-invalid",
            "build + run + positive-control + target-verifier + exit margin "
            "must be strictly below the outer walltime",
        )
    return cells[0], workloads[0], threads[0]


def _validate_verifier_identity_shape(identity: object) -> dict:
    if type(identity) is not dict or set(identity) != {
        "repository_commit",
        "module_sha256",
    }:
        raise CertificationReject(
            "verifier-identity-invalid", "verifier identity has an invalid schema"
        )
    commit = identity.get("repository_commit")
    modules = identity.get("module_sha256")
    if (
        type(commit) is not str
        or _COMMIT_RE.fullmatch(commit) is None
        or type(modules) is not dict
        or not modules
        or any(
            type(name) is not str
            or not name
            or type(digest) is not str
            or _SHA256_RE.fullmatch(digest) is None
            for name, digest in modules.items()
        )
    ):
        raise CertificationReject(
            "verifier-identity-invalid",
            "verifier commit/modules are not exact full identities",
        )
    return identity


def _load_expected_verifier_identity(
    path: Path, expected_file_sha256: str
) -> tuple[dict, str]:
    try:
        raw = path.read_bytes()
        identity = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CertificationReject(
            "verifier-identity-invalid", "expected verifier identity is unavailable"
        ) from exc
    actual_file_sha256 = hashlib.sha256(raw).hexdigest()
    if (
        type(expected_file_sha256) is not str
        or _SHA256_RE.fullmatch(expected_file_sha256) is None
        or actual_file_sha256 != expected_file_sha256
    ):
        raise CertificationReject(
            "verifier-identity-mismatch",
            "expected verifier identity file does not match its preregistered SHA",
        )
    validated = _validate_verifier_identity_shape(identity)
    return validated, actual_file_sha256


def _require_expected_verifier_identity(actual: object, expected: dict) -> None:
    if _validate_verifier_identity_shape(actual) != expected:
        raise CertificationReject(
            "verifier-identity-mismatch",
            "verifier closure does not match the preregistered identity",
        )


def _build_worker(connection, builder) -> None:
    """Run one build in its own process group and return a pickled result."""
    try:
        os.setsid()
        connection.send(("ok", builder()))
    except BaseException as exc:  # child boundary: parent converts to one reject
        connection.send(("error", f"{type(exc).__name__}: {exc}"))
    finally:
        connection.close()


def _run_build_with_deadline(builder, timeout_s: float):
    """Enforce the build budget while also terminating spawned descendants."""
    context = multiprocessing.get_context("fork")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=_build_worker, args=(sender, builder))
    process.start()
    sender.close()
    if not receiver.poll(timeout_s):
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            process.terminate()
        process.join(timeout=2.0)
        if process.is_alive():
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                process.kill()
            process.join()
        receiver.close()
        raise CertificationReject(
            "trace-build-budget-exceeded",
            "trace build exceeded its preregistered hard deadline",
        )
    try:
        status, value = receiver.recv()
    except EOFError as exc:
        raise RuntimeError("trace build worker exited without a result") from exc
    finally:
        receiver.close()
        process.join()
    if status != "ok":
        raise RuntimeError(f"trace build failed in deadline worker: {value}")
    if process.exitcode != 0:
        raise RuntimeError(f"trace build worker exited {process.exitcode}")
    return value


def _phase_measurement(started_wall: float, started_cpu: float) -> dict:
    elapsed = max(0.0, time.monotonic() - started_wall)
    cpu = max(0.0, _cpu_seconds() - started_cpu)
    return {
        "elapsed_seconds": elapsed,
        "cpu_seconds": cpu,
        "cpu_over_elapsed": cpu / elapsed if elapsed > 0 else None,
    }


def _verifier_identity() -> dict:
    """Bind the verifier entry and complete Python package closure."""
    commit = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10.0,
    ).stdout.strip()
    paths = [VERIFIER_ENTRY, *sorted(VERIFIER_PACKAGE.glob("*.py"))]
    modules = {}
    for path in paths:
        if not path.is_file():
            raise CertificationReject(
                "verifier-identity-unavailable", f"missing verifier module: {path}"
            )
        modules[path.relative_to(ROOT).as_posix()] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
    return {"repository_commit": commit, "module_sha256": modules}


def _verifier_argv(trace_dir: Path, expected_commits: int) -> list[str]:
    return [
        sys.executable,
        "-B",
        "orchestrator/verify.py",
        str(trace_dir.resolve(strict=True)),
        "--json",
        "--expected-commits",
        str(expected_commits),
    ]


def _run_verifier(
    trace_dir: Path, expected_commits: int, timeout_s: float
) -> dict:
    """Run the exact verifier child and collect per-child CPU/RSS with wait4."""
    argv = _verifier_argv(trace_dir, expected_commits)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    started = time.monotonic()
    timed_out = False
    with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
        proc = subprocess.Popen(
            argv,
            cwd=ROOT,
            env=env,
            stdout=stdout_file,
            stderr=stderr_file,
        )
        status = None
        usage = None
        while status is None:
            waited_pid, waited_status, waited_usage = os.wait4(proc.pid, os.WNOHANG)
            if waited_pid == proc.pid:
                status = waited_status
                usage = waited_usage
                break
            if time.monotonic() - started >= timeout_s:
                timed_out = True
                proc.kill()
                _waited_pid, status, usage = os.wait4(proc.pid, 0)
                break
            time.sleep(0.05)
        assert status is not None and usage is not None
        proc.returncode = os.waitstatus_to_exitcode(status)
        stdout_file.seek(0)
        stderr_file.seek(0)
        stdout = stdout_file.read().decode("utf-8", errors="replace")
        stderr = stderr_file.read().decode("utf-8", errors="replace")
    elapsed = max(0.0, time.monotonic() - started)
    cpu = max(0.0, usage.ru_utime + usage.ru_stime)
    parsed = None
    parse_error = None
    try:
        parsed = json.loads(stdout)
    except (json.JSONDecodeError, TypeError) as exc:
        parse_error = f"{type(exc).__name__}: {exc}"
    return {
        "argv": argv,
        "environment": {"PYTHONDONTWRITEBYTECODE": "1"},
        "exit_code": proc.returncode,
        "timed_out": timed_out,
        "timeout_seconds": timeout_s,
        "elapsed_seconds": elapsed,
        "cpu_seconds": cpu,
        "cpu_over_elapsed": cpu / elapsed if elapsed > 0 else None,
        "max_rss_kib": usage.ru_maxrss,
        "stdout": stdout,
        "stderr": stderr,
        "json": parsed,
        "json_parse_error": parse_error,
    }


def _normalized_path(value: object) -> str | None:
    if type(value) is not str:
        return None
    try:
        return str(Path(value).resolve(strict=True))
    except (OSError, RuntimeError):
        return None


def _single_result(invocation: dict, reason_prefix: str) -> tuple[dict, dict]:
    document = invocation.get("json")
    if type(document) is not dict or type(document.get("results")) is not list:
        raise CertificationReject(
            f"{reason_prefix}-json-invalid", "verifier did not return structured JSON"
        )
    if len(document["results"]) != 1 or type(document["results"][0]) is not dict:
        raise CertificationReject(
            f"{reason_prefix}-json-invalid", "verifier must return exactly one result"
        )
    return document, document["results"][0]


def _validate_positive_control(invocation: dict) -> None:
    if invocation.get("timed_out") is not False or invocation.get("exit_code") != 1:
        raise CertificationReject(
            "positive-control-exit", "static broken-Silo fixture must exit exactly 1"
        )
    document, result = _single_result(invocation, "positive-control")
    if (
        document.get("runs") != 1
        or document.get("non_serializable") != 1
        or document.get("certified_serializable") != 0
        or result.get("verdict") != "non-serializable"
        or result.get("certified") is not False
        or _normalized_path(result.get("trace_dir"))
        != str(POSITIVE_CONTROL_TRACE.resolve(strict=True))
        or result.get("total_cycles") != 4
    ):
        raise CertificationReject(
            "positive-control-contract", "broken-Silo aggregate/result contract mismatch"
        )
    anomalies = result.get("anomalies")
    if type(anomalies) is not list or not anomalies:
        raise CertificationReject(
            "positive-control-anomalies", "broken-Silo fixture has no anomaly witness"
        )
    saw_rw = False
    for anomaly in anomalies:
        if type(anomaly) is not dict or anomaly.get("phenomenon") != "G2":
            raise CertificationReject(
                "positive-control-phenomenon", "every positive-control anomaly must be G2"
            )
        edges = anomaly.get("edges")
        if type(edges) is not list or not edges:
            raise CertificationReject(
                "positive-control-edge", "every G2 witness must have edges"
            )
        for edge in edges:
            if (
                type(edge) is not dict
                or type(edge.get("from")) is not int
                or type(edge.get("to")) is not int
                or type(edge.get("reasons")) is not list
                or not edge["reasons"]
            ):
                raise CertificationReject(
                    "positive-control-edge", "every edge must have endpoints and reasons"
                )
            for reason in edge["reasons"]:
                if type(reason) is not dict or reason.get("type") not in {"ww", "wr", "rw"}:
                    raise CertificationReject(
                        "positive-control-reason", "unknown or malformed edge reason"
                    )
                required = {"type", "key", "u_ver"}
                if reason["type"] in {"ww", "rw"}:
                    required.add("v_ver")
                if not required.issubset(reason) or not reason.get("key"):
                    raise CertificationReject(
                        "positive-control-version", "edge reason lacks type-specific versions"
                    )
                saw_rw = saw_rw or reason["type"] == "rw"
    if not saw_rw:
        raise CertificationReject(
            "positive-control-rw-missing", "positive control must contain an rw reason"
        )


def _validate_target(
    invocation: dict,
    trace_dir: Path,
    trace_result: object,
    expected_verifier_identity: dict,
    verifier_identity_after: dict,
) -> tuple[dict, dict]:
    _require_expected_verifier_identity(
        verifier_identity_after, expected_verifier_identity
    )
    if invocation.get("timed_out") is not False or invocation.get("exit_code") != 0:
        raise CertificationReject(
            "target-verifier-exit", "target verifier must exit exactly 0"
        )
    argv = invocation.get("argv")
    if (
        type(argv) is not list
        or argv[:3] != [sys.executable, "-B", "orchestrator/verify.py"]
        or "--lenient" in argv
    ):
        raise CertificationReject(
            "verifier-argv-contract",
            "target verifier argv must use python -B without --lenient",
        )
    document, result = _single_result(invocation, "target")
    if _normalized_path(result.get("trace_dir")) != str(trace_dir.resolve(strict=True)):
        raise CertificationReject(
            "target-trace-dir-mismatch", "verifier result is not bound to the generated trace"
        )
    if (
        document.get("runs") != 1
        or document.get("certified_serializable") != 1
        or document.get("non_serializable") != 0
        or document.get("indeterminate") != 0
        or result.get("verdict") != "serializable"
        or result.get("certified") is not True
    ):
        raise CertificationReject(
            "target-verdict", "target is not exactly one certified serializable result"
        )
    integrity = result.get("integrity")
    if type(integrity) is not dict or integrity.get("clean") is not True:
        raise CertificationReject("target-integrity", "target integrity is not clean")
    stats = result.get("stats")
    if type(stats) is not dict:
        raise CertificationReject("target-stats", "target stats are missing")
    for field, lower_bound in (("txns", 2), ("reads", 1), ("writes", 1), ("edges", 1)):
        value = stats.get(field)
        if type(value) is not int or value < lower_bound:
            reason = "target-edges-empty" if field == "edges" else f"target-{field}-empty"
            raise CertificationReject(reason, f"target stats.{field} is below {lower_bound}")
    abort_count_stdout = getattr(trace_result, "abort_counts", None)
    if type(abort_count_stdout) is not int or abort_count_stdout <= 0:
        raise CertificationReject(
            "target-abort-empty",
            "target abort_count_stdout must be a positive exact integer",
        )
    if (
        getattr(trace_result, "returncode", None) != 0
        or getattr(trace_result, "commit_count_witness", None) is None
        or getattr(trace_result, "batch_commit_count_witness", None) != 0
        or getattr(trace_result, "trace_c_lines", None)
        != getattr(trace_result, "commit_count_witness", None)
    ):
        raise CertificationReject(
            "target-commit-witness", "run rc/commit line/batch/trace-C witness mismatch"
        )
    return document, result


def _trace_manifest(trace_dir: Path) -> dict:
    files = []
    total_bytes = 0
    total_lines = 0
    for path in sorted(trace_dir.glob("trace_*.log")):
        size = path.stat().st_size
        digest = hashlib.sha256()
        lines = 0
        last_byte = b""
        with path.open("rb") as stream:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
                lines += chunk.count(b"\n")
                last_byte = chunk[-1:]
        if size and last_byte != b"\n":
            lines += 1
        files.append(
            {
                "name": path.name,
                "size_bytes": size,
                "lines": lines,
                "sha256": digest.hexdigest(),
            }
        )
        total_bytes += size
        total_lines += lines
    return {
        "file_count": len(files),
        "bytes": total_bytes,
        "lines": total_lines,
        "files": files,
    }


def _write_json_create_only(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def _performance_artifact_identity(path: Path, expected_sha256: str) -> dict:
    if type(expected_sha256) is not str or _SHA256_RE.fullmatch(expected_sha256) is None:
        raise CertificationReject(
            "performance-artifact-identity-mismatch",
            "expected performance artifact sha256 is not exact",
        )
    raw = path.read_bytes()
    try:
        document = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CertificationReject(
            "performance-artifact-invalid", "performance artifact is not JSON"
        ) from exc
    if (
        type(document) is not dict
        or document.get("schema_version") != SCHEMA_VERSION
        or document.get("kind") != "performance-only-probe"
        or document.get("not_certified") != NOT_CERTIFIED
    ):
        raise CertificationReject(
            "performance-artifact-invalid",
            "performance artifact lacks the exact performance-only identity",
        )
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    if actual_sha256 != expected_sha256:
        raise CertificationReject(
            "performance-artifact-identity-mismatch",
            "performance artifact does not match the preregistered path/SHA",
        )
    return {
        "path": str(path.resolve(strict=True)),
        "sha256": actual_sha256,
    }


@dataclass(frozen=True)
class _ReceiptTraceResult:
    trace_c_lines: object
    returncode: object
    abort_counts: object
    commit_count_witness: object
    batch_commit_count_witness: object


def _validate_trace_manifest_receipt(trace_dir: Path, manifest: object) -> None:
    if not (trace_dir / "log").is_dir():
        raise CertificationReject(
            "group-trace-dir-invalid", "raw trace directory no longer has log/"
        )
    if type(manifest) is not dict or set(manifest) != {
        "file_count",
        "bytes",
        "lines",
        "files",
    }:
        raise CertificationReject(
            "group-trace-manifest-mismatch", "trace manifest schema is invalid"
        )
    files = manifest.get("files")
    if (
        type(files) is not list
        or not files
        or manifest.get("file_count") != len(files)
        or type(manifest.get("bytes")) is not int
        or manifest["bytes"] <= 0
        or type(manifest.get("lines")) is not int
        or manifest["lines"] <= 0
    ):
        raise CertificationReject(
            "group-trace-manifest-mismatch", "trace manifest totals are invalid"
        )
    names = set()
    total_bytes = 0
    total_lines = 0
    for item in files:
        if type(item) is not dict or set(item) != {
            "name",
            "size_bytes",
            "lines",
            "sha256",
        }:
            raise CertificationReject(
                "group-trace-manifest-mismatch", "trace file manifest is invalid"
            )
        name = item.get("name")
        size = item.get("size_bytes")
        lines = item.get("lines")
        digest = item.get("sha256")
        if (
            type(name) is not str
            or re.fullmatch(r"trace_[0-9]+\.log", name) is None
            or name in names
            or type(size) is not int
            or size <= 0
            or type(lines) is not int
            or lines <= 0
            or type(digest) is not str
            or _SHA256_RE.fullmatch(digest) is None
        ):
            raise CertificationReject(
                "group-trace-manifest-mismatch", "trace file metadata is invalid"
            )
        trace_file = trace_dir / name
        if not trace_file.is_file() or trace_file.stat().st_size != size:
            raise CertificationReject(
                "group-trace-manifest-mismatch",
                "raw trace is missing or its size differs before aggregation",
            )
        names.add(name)
        total_bytes += size
        total_lines += lines
    if total_bytes != manifest["bytes"] or total_lines != manifest["lines"]:
        raise CertificationReject(
            "group-trace-manifest-mismatch", "trace manifest totals do not add up"
        )


def _validated_certification_row(
    path: Path,
    *,
    attempt_id: str,
    expected_verifier_identity: dict,
    expected_verifier_identity_file_sha256: str,
    performance_identity: dict,
) -> tuple[dict, tuple[str, int]]:
    try:
        raw = path.read_bytes()
        document = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CertificationReject(
            "group-result-invalid", f"certification result is unreadable: {path}"
        ) from exc
    if (
        type(document) is not dict
        or document.get("schema_version") != CERTIFICATION_SCHEMA_VERSION
        or document.get("kind") != "correctness-certification-request"
        or document.get("terminal_status") != "certified"
        or document.get("certified") is not True
        or document.get("certification_gate") != "all-10-conditions-passed"
        or document.get("attempt_id") != attempt_id
        or document.get("performance_artifact") != performance_identity
    ):
        raise CertificationReject(
            "group-result-not-certified",
            f"result is not one certified receipt for attempt {attempt_id}: {path}",
        )
    workload = document.get("workload")
    slot = document.get("independent_run_slot")
    if workload not in CERT_WORKLOADS or type(slot) is not int or slot not in CERT_SLOTS:
        raise CertificationReject(
            "group-result-invalid", f"result workload/slot is invalid: {path}"
        )
    expected_workload_flags = {
        **WORKLOADS[workload],
        "ycsb_tuple_num": str(CERT_RECORDS),
        "thread_num": str(CERT_THREADS[0]),
        "extime": str(CERT_EXTIME),
    }
    if (
        document.get("workload_flags") != expected_workload_flags
        or document.get("records") != CERT_RECORDS
        or document.get("threads") != CERT_THREADS[0]
        or document.get("extime_s") != CERT_EXTIME
        or document.get("cell") != CERT_CELL.label
        or document.get("back_off") != CERT_CELL.back_off
        or document.get("step_us") != CERT_CELL.step_us
        or document.get("ceiling_us") != CERT_CELL.ceiling_us
        or document.get("update_us") != CERT_CELL.update_us
        or document.get("rng_seed_controlled") is not False
    ):
        raise CertificationReject(
            "group-workload-contract-mismatch",
            f"result workload constants/flags are invalid: {path}",
        )
    request_id = document.get("pbs_jobid")
    if type(request_id) is not str or not request_id:
        raise CertificationReject(
            "group-result-invalid", f"result request id is invalid: {path}"
        )
    actual_identity = _validate_verifier_identity_shape(
        document.get("verifier_identity")
    )
    _require_expected_verifier_identity(actual_identity, expected_verifier_identity)
    if document.get("expected_verifier_identity_file_sha256") != (
        expected_verifier_identity_file_sha256
    ):
        raise CertificationReject(
            "group-verifier-identity-mismatch",
            "result is not bound to the preregistered verifier manifest file",
        )
    if (
        document.get("build_trace_enabled") is not True
        or type(document.get("build_cache_key")) is not str
        or not document["build_cache_key"].endswith("_t1")
        or type(document.get("binary_sha256")) is not str
        or _SHA256_RE.fullmatch(document["binary_sha256"]) is None
        or document.get("patch_sha256")
        != hashlib.sha256(PATCH.read_bytes()).hexdigest()
        or document.get("ccbench_commit") != PIN_FULL
        or type(document.get("build_admission_receipt_sha256")) is not str
        or _SHA256_RE.fullmatch(document["build_admission_receipt_sha256"]) is None
        or type(document.get("source_evidence")) is not dict
        or document["source_evidence"].get("ccbench_commit") != CURRENT_PIN
        or type(document["source_evidence"].get("genome_sha256")) is not str
        or _SHA256_RE.fullmatch(
            document["source_evidence"]["genome_sha256"]
        )
        is None
        or type(document["source_evidence"].get("source_bytes_sha256")) is not str
        or _SHA256_RE.fullmatch(
            document["source_evidence"]["source_bytes_sha256"]
        )
        is None
    ):
        raise CertificationReject(
            "group-build-identity-mismatch",
            f"result build/pin/patch/trace identity is invalid: {path}",
        )
    trace_value = document.get("trace_directory")
    normalized_trace = _normalized_path(trace_value)
    if normalized_trace is None or normalized_trace != trace_value:
        raise CertificationReject(
            "group-trace-dir-invalid", f"result trace_dir is not exact: {path}"
        )
    trace_dir = Path(normalized_trace)
    _validate_trace_manifest_receipt(trace_dir, document.get("trace_manifest"))
    positive = document.get("positive_control")
    if type(positive) is not dict:
        raise CertificationReject(
            "group-result-invalid", f"positive-control receipt is missing: {path}"
        )
    try:
        positive_stdout_json = json.loads(positive.get("stdout"))
    except (TypeError, json.JSONDecodeError) as exc:
        raise CertificationReject(
            "group-result-invalid", f"positive-control stdout is invalid: {path}"
        ) from exc
    if positive.get("json_parse_error") is not None or positive_stdout_json != positive.get(
        "json"
    ):
        raise CertificationReject(
            "group-result-invalid", f"positive-control JSON binding differs: {path}"
        )
    _validate_positive_control(positive)
    run = document.get("run")
    target = document.get("target_verifier")
    if type(run) is not dict or type(target) is not dict:
        raise CertificationReject(
            "group-result-invalid", f"run/verifier receipt is missing: {path}"
        )
    try:
        target_stdout_json = json.loads(target.get("stdout"))
    except (TypeError, json.JSONDecodeError) as exc:
        raise CertificationReject(
            "group-result-invalid", f"target verifier stdout is invalid: {path}"
        ) from exc
    if target.get("json_parse_error") is not None or target_stdout_json != target.get(
        "json"
    ):
        raise CertificationReject(
            "group-result-invalid", f"target verifier JSON binding differs: {path}"
        )
    trace_result = _ReceiptTraceResult(
        trace_c_lines=run.get("trace_c_lines"),
        returncode=run.get("exit_code"),
        abort_counts=run.get("abort_count_stdout"),
        commit_count_witness=run.get("commit_count"),
        batch_commit_count_witness=run.get("batch_commit_count"),
    )
    target_document, target_result = _validate_target(
        target,
        trace_dir,
        trace_result,
        expected_verifier_identity,
        actual_identity,
    )
    if document.get("verifier_json") != target_document:
        raise CertificationReject(
            "group-result-invalid", f"verifier JSON binding differs: {path}"
        )
    abort_reasons = target_result.get("stats", {}).get("abort_reasons")
    if type(abort_reasons) is not dict or any(
        type(value) is not int or value < 0 for value in abort_reasons.values()
    ):
        raise CertificationReject(
            "group-result-invalid", f"abort reason information is malformed: {path}"
        )
    return (
        {
            "path": str(path.resolve(strict=True)),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "workload": workload,
            "independent_run_slot": slot,
            "request_id": request_id,
            "terminal_status": "certified",
            "certified": True,
            "trace_dir": normalized_trace,
            "verifier_identity": actual_identity,
            "binary_sha256": document["binary_sha256"],
            "build_cache_key": document["build_cache_key"],
            "build_admission_receipt_sha256": document[
                "build_admission_receipt_sha256"
            ],
            "patch_sha256": document["patch_sha256"],
            "ccbench_commit": document["ccbench_commit"],
            "attempt_id": attempt_id,
        },
        (workload, slot),
    )


def _group_receipt_payload(
    result_files: list[Path],
    performance_artifact: Path,
    performance_artifact_sha256: str,
    attempt_id: str,
    expected_verifier_identity: dict,
    expected_verifier_identity_file_sha256: str,
) -> dict:
    expected = {(workload, slot) for workload in CERT_WORKLOADS for slot in CERT_SLOTS}
    normalized_files = [path.resolve(strict=False) for path in result_files]
    if len(normalized_files) != 24:
        raise CertificationReject(
            "group-incomplete",
            "group aggregation requires exactly 24 explicit result paths",
        )
    if len(set(normalized_files)) != 24:
        raise CertificationReject(
            "group-result-path-set-invalid",
            "group aggregation requires 24 unique result paths",
        )
    rows = []
    actual = set()
    performance_identity = _performance_artifact_identity(
        performance_artifact, performance_artifact_sha256
    )
    for path in sorted(normalized_files):
        row, pair = _validated_certification_row(
            path,
            attempt_id=attempt_id,
            expected_verifier_identity=expected_verifier_identity,
            expected_verifier_identity_file_sha256=(
                expected_verifier_identity_file_sha256
            ),
            performance_identity=performance_identity,
        )
        if pair in actual:
            raise CertificationReject("group-duplicate-request", f"duplicate pair: {pair}")
        actual.add(pair)
        rows.append(row)
    if actual != expected or len(rows) != 24:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected, key=repr)
        raise CertificationReject(
            "group-incomplete",
            f"group requires exact 24 workload/slot pairs; missing={missing} extra={extra}",
        )
    if len({row["request_id"] for row in rows}) != 24:
        raise CertificationReject(
            "group-request-identity-duplicate", "request ids must be unique"
        )
    if (
        len({row["trace_dir"] for row in rows}) != 24
        or len({row["binary_sha256"] for row in rows}) != 1
        or len({row["patch_sha256"] for row in rows}) != 1
        or len({row["ccbench_commit"] for row in rows}) != 1
        or any(
            type(row[field]) is not str
            or re.fullmatch(r"[0-9a-f]{64}", row[field]) is None
            for row in rows
            for field in ("binary_sha256", "patch_sha256")
        )
        or any(
            type(row["ccbench_commit"]) is not str
            or re.fullmatch(r"[0-9a-f]{40}", row["ccbench_commit"]) is None
            for row in rows
        )
    ):
        raise CertificationReject(
            "group-build-identity-mismatch",
            "a complete group requires unique traces and exact build identities",
        )
    return {
        "schema_version": GROUP_RECEIPT_SCHEMA_VERSION,
        "complete": True,
        "attempt_id": attempt_id,
        "expected_requests": 24,
        "terminal_requests": 24,
        "certified_requests": 24,
        "claim": ALLOWED_GROUP_CLAIM,
        "claim_limitations": list(CLAIM_LIMITATIONS),
        # The correctness campaign binds the trace-disabled performance
        # artifact, but never relabels its measurements as verifier outputs.
        "performance_values_remain_uncertified": True,
        "verifier_identity": expected_verifier_identity,
        "expected_verifier_identity_file_sha256": (
            expected_verifier_identity_file_sha256
        ),
        "performance_artifact": performance_identity,
        "results": rows,
    }


def _validate_published_group(
    group_out: Path,
    result_files: list[Path],
    performance_artifact: Path,
    performance_artifact_sha256: str,
    attempt_id: str,
    expected_verifier_identity: dict,
    expected_verifier_identity_file_sha256: str,
) -> None:
    try:
        receipt = json.loads(group_out.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CertificationReject(
            "group-receipt-collision", "published group receipt is incomplete"
        ) from exc
    if type(receipt) is not dict:
        raise CertificationReject(
            "group-receipt-collision", "published group receipt is not an object"
        )
    expected_paths = {str(path.resolve(strict=True)): path for path in result_files}
    rows = receipt.get("results")
    if (
        receipt.get("schema_version") != GROUP_RECEIPT_SCHEMA_VERSION
        or receipt.get("complete") is not True
        or receipt.get("certified_requests") != 24
        or receipt.get("attempt_id") != attempt_id
        or receipt.get("verifier_identity") != expected_verifier_identity
        or receipt.get("expected_verifier_identity_file_sha256")
        != expected_verifier_identity_file_sha256
        or receipt.get("performance_artifact")
        != _performance_artifact_identity(
            performance_artifact, performance_artifact_sha256
        )
        or type(rows) is not list
        or len(rows) != 24
        or {row.get("path") for row in rows if type(row) is dict}
        != set(expected_paths)
    ):
        raise CertificationReject(
            "group-receipt-collision", "published group receipt has another identity"
        )
    for row in rows:
        path = expected_paths[row["path"]]
        if row.get("sha256") != hashlib.sha256(path.read_bytes()).hexdigest():
            raise CertificationReject(
                "group-receipt-collision", "published group result hash differs"
            )


def _try_finalize_group(
    result_files: list[Path],
    group_out: Path,
    performance_artifact: Path,
    performance_artifact_sha256: str,
    attempt_id: str,
    expected_verifier_identity: dict,
    expected_verifier_identity_file_sha256: str,
) -> bool:
    if any(not path.is_file() for path in result_files):
        return False
    group_out.parent.mkdir(parents=True, exist_ok=True)
    reservation = group_out.with_name(group_out.name + ".reserve")
    deadline = time.monotonic() + GROUP_RECEIPT_WAIT_S
    while True:
        if group_out.is_file():
            _validate_published_group(
                group_out,
                result_files,
                performance_artifact,
                performance_artifact_sha256,
                attempt_id,
                expected_verifier_identity,
                expected_verifier_identity_file_sha256,
            )
            return True
        try:
            reservation.mkdir(mode=0o700)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise CertificationReject(
                    "group-receipt-timeout",
                    "timed out waiting for the reserved group receipt",
                )
            time.sleep(0.1)

    temporary = reservation / "group-receipt.tmp"
    try:
        if group_out.exists():
            _validate_published_group(
                group_out,
                result_files,
                performance_artifact,
                performance_artifact_sha256,
                attempt_id,
                expected_verifier_identity,
                expected_verifier_identity_file_sha256,
            )
            return True
        try:
            receipt = _group_receipt_payload(
                result_files,
                performance_artifact,
                performance_artifact_sha256,
                attempt_id,
                expected_verifier_identity,
                expected_verifier_identity_file_sha256,
            )
        except CertificationReject:
            return False
        encoded = (
            json.dumps(receipt, indent=2, ensure_ascii=False) + "\n"
        ).encode("utf-8")
        with temporary.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        if group_out.exists():
            raise CertificationReject(
                "group-receipt-collision", "group receipt appeared under reservation"
            )
        os.rename(temporary, group_out)
        parent_fd = os.open(
            group_out.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        )
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
        return True
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        try:
            reservation.rmdir()
        except OSError:
            pass


def _remove_group_traces(group_out: Path) -> None:
    """Delete raw traces only after a complete group receipt is published."""
    import shutil

    receipt = json.loads(group_out.read_text(encoding="utf-8"))
    for row in receipt["results"]:
        trace_dir = row.get("trace_dir")
        if type(trace_dir) is str:
            shutil.rmtree(trace_dir, ignore_errors=True)


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", choices=("performance", "certify"), default="performance"
    )
    parser.add_argument("--cells", required=True)
    parser.add_argument(
        "--workloads", default=",".join(DEFAULT_WORKLOADS)
    )
    parser.add_argument(
        "--threads", default=",".join(str(value) for value in DEFAULT_THREADS)
    )
    parser.add_argument("--rep-index", type=_nonnegative_int, default=0)
    parser.add_argument("--reps-per-job", type=_positive_int, default=1)
    parser.add_argument("--stage", type=int, choices=(1, 2, 3), default=1)
    parser.add_argument("--extime", type=_positive_int, default=EXTIME)
    parser.add_argument(
        "--verifier-timeout-s",
        type=_positive_float,
        default=DEFAULT_VERIFIER_TIMEOUT_S,
    )
    parser.add_argument(
        "--build-budget-s", type=_positive_float, default=DEFAULT_BUILD_BUDGET_S
    )
    parser.add_argument(
        "--prologue-budget-s",
        type=_positive_float,
        default=DEFAULT_PROLOGUE_BUDGET_S,
    )
    parser.add_argument("--prologue-elapsed-s", type=float, default=0.0)
    parser.add_argument("--prologue-cpu-s", type=float, default=0.0)
    parser.add_argument(
        "--outer-walltime-s",
        type=_positive_float,
        default=DEFAULT_OUTER_WALLTIME_S,
    )
    parser.add_argument(
        "--exit-margin-s", type=_positive_float, default=DEFAULT_EXIT_MARGIN_S
    )
    parser.add_argument("--group-receipt-out", type=Path)
    parser.add_argument("--group-result-path", action="append", type=Path, default=[])
    parser.add_argument("--attempt-id")
    parser.add_argument("--performance-artifact", type=Path)
    parser.add_argument("--performance-artifact-sha256")
    parser.add_argument("--expected-verifier-identity", type=Path)
    parser.add_argument("--expected-verifier-identity-sha256")
    parser.add_argument("--out", required=True)
    return parser


def _certify_main(args: argparse.Namespace) -> int:
    """Run one exact workload × independent-slot certification request."""
    out = Path(args.out)
    _validate_output_path(out)
    cell, workload_id, threads = _certification_contract(args)
    assert args.group_receipt_out is not None
    assert args.performance_artifact is not None
    assert args.performance_artifact_sha256 is not None
    assert args.expected_verifier_identity is not None
    assert args.expected_verifier_identity_sha256 is not None
    assert args.attempt_id is not None
    group_out = args.group_receipt_out
    performance_artifact = args.performance_artifact
    performance_artifact_sha256 = args.performance_artifact_sha256
    result_files = [path.resolve(strict=False) for path in args.group_result_path]
    expected_verifier_identity, expected_verifier_identity_file_sha256 = (
        _load_expected_verifier_identity(
            args.expected_verifier_identity,
            args.expected_verifier_identity_sha256,
        )
    )
    if not performance_artifact.is_file():
        raise FileNotFoundError(
            f"performance artifact is missing: {performance_artifact}"
        )
    performance_identity = _performance_artifact_identity(
        performance_artifact, performance_artifact_sha256
    )
    if not PATCH.is_file():
        raise FileNotFoundError(f"patch is missing: {PATCH}")

    site = site_policy.current_site()
    if site_policy.refuses_heavy_work(site):
        raise RuntimeError(
            site_policy.heavy_work_refusal(
                site, "T-2187 adaptive constant certification"
            )
        )
    _assert_single_tenant()

    started_utc = datetime.now(timezone.utc).isoformat()
    job_wall_started = time.monotonic()
    job_cpu_started = _cpu_seconds()
    out.parent.mkdir(parents=True, exist_ok=True)
    trace_dir: Path | None = None
    payload = {
        "schema_version": CERTIFICATION_SCHEMA_VERSION,
        "kind": "correctness-certification-request",
        "claim_status": "not-yet-group-certified",
        "allowed_group_claim": ALLOWED_GROUP_CLAIM,
        "claim_limitations": list(CLAIM_LIMITATIONS),
        "performance_values_remain_uncertified": True,
        "attempt_id": args.attempt_id,
        "stage": args.stage,
        "site": "pegasus",
        "host": os.uname().nodename,
        "pbs_jobid": os.environ.get("PBS_JOBID"),
        "workload": workload_id,
        "workload_flags": {
            **WORKLOADS[workload_id],
            "ycsb_tuple_num": str(CERT_RECORDS),
            "thread_num": str(threads),
            "extime": str(CERT_EXTIME),
        },
        "records": CERT_RECORDS,
        "threads": threads,
        "extime_s": CERT_EXTIME,
        "independent_run_slot": args.rep_index,
        "rng_seed_controlled": False,
        "cell": cell.label,
        "back_off": cell.back_off,
        "step_us": cell.step_us,
        "ceiling_us": cell.ceiling_us,
        "update_us": cell.update_us,
        "ccbench_commit": PIN_FULL,
        "patch_sha256": hashlib.sha256(PATCH.read_bytes()).hexdigest(),
        "performance_artifact": performance_identity,
        "expected_verifier_identity": expected_verifier_identity,
        "expected_verifier_identity_file_sha256": (
            expected_verifier_identity_file_sha256
        ),
        "positive_control_provenance": {
            "kind": "static-fixture-not-live-broken-build",
            "trace_dir": str(POSITIVE_CONTROL_TRACE.resolve(strict=True)),
            "producer_patch": "patches/broken-silo-norw-validation.patch",
            "producer_function": (
                "orchestrator/campaign/s2_verify_calibration.py:"
                "_broken_build_and_verify"
            ),
            "producer_change": "TxExecutor::validationPhase()",
            "defines": {
                "IZANAGI_BREAK_NOREAD_VALIDATION": 1,
                "CCBENCH_TRACE": 1,
            },
            "workload": {
                "records": 200,
                "rratio": 50,
                "rmw": True,
                "threads": 4,
                "extime_s": 1,
            },
        },
        "time_budget": {
            "prologue_seconds": args.prologue_budget_s,
            "build_seconds": args.build_budget_s,
            "run_seconds": RUN_TIMEOUT_S,
            "positive_control_seconds": POSITIVE_CONTROL_TIMEOUT_S,
            "target_verifier_seconds": args.verifier_timeout_s,
            "exit_margin_seconds": args.exit_margin_s,
            "outer_walltime_seconds": args.outer_walltime_s,
        },
        "prologue_phase": {
            "elapsed_seconds": args.prologue_elapsed_s,
            "cpu_seconds": args.prologue_cpu_s,
            "cpu_over_elapsed": (
                args.prologue_cpu_s / args.prologue_elapsed_s
                if args.prologue_elapsed_s > 0
                else None
            ),
        },
        "started_utc": started_utc,
    }
    rejected: CertificationReject | None = None
    try:
        # Trace and pipeline dependencies stay wholly inside the explicit mode.
        from orchestrator.campaign.pipeline import _run_trace

        submodule = ROOT / "external" / "ccbench"
        head = _ccbench_head(submodule)
        assert_pinned_clean(str(submodule), CURRENT_PIN)
        cc, cxx = buildcache.compilers_for_current_site()
        cache_root = Path(os.environ["TMPDIR"]) / "build-variants"
        cache_root.mkdir(mode=0o700)
        genome = genome_for(cell)

        build_wall_started = time.monotonic()
        build_cpu_started = _cpu_seconds()
        with isolated_checkout(submodule, CURRENT_PIN) as work_root:
            with applied(str(PATCH), CURRENT_PIN, work_root):
                evidence = source_digest.resolve_evidence(
                    genome,
                    CURRENT_PIN,
                    cxx=cxx,
                    ccbench_dir=work_root,
                )
                build_context = build_run_context(
                    generator_id=GeneratorId.BACKOFF_SWEEP
                )
                receipt = attest_generator_output(
                    build_context,
                    evidence,
                    generator_input_sha256=hashlib.sha256(
                        (
                            f"{CERTIFICATION_SCHEMA_VERSION}|"
                            f"{evidence.genome_sha256}"
                        ).encode("utf-8")
                    ).hexdigest(),
                )
                admission = derive_build_admission(
                    build_context, evidence, generator_receipt=receipt
                )
                build_cache_key = buildcache.cache_key(
                    genome,
                    CURRENT_PIN,
                    True,
                    src_token=evidence.src_token,
                    cc=cc,
                    cxx=cxx,
                    admission=admission,
                )
                if not build_cache_key.endswith("_t1"):
                    raise CertificationReject(
                        "trace-build-identity",
                        "trace build cache identity is not trace-enabled",
                    )

                def _build_trace_binary():
                    return buildcache.build(
                        genome,
                        ccbench_commit=CURRENT_PIN,
                        trace=True,
                        cc=cc,
                        cxx=cxx,
                        admission=admission,
                        build_context=build_context,
                        source_evidence=evidence,
                        cache_root=str(cache_root),
                        ccbench_dir=work_root,
                    )

                build = _run_build_with_deadline(
                    _build_trace_binary, args.build_budget_s
                )
                payload["build_phase"] = _phase_measurement(
                    build_wall_started, build_cpu_started
                )
                if payload["build_phase"]["elapsed_seconds"] > args.build_budget_s:
                    raise CertificationReject(
                        "trace-build-budget-exceeded",
                        "trace build exceeded its preregistered inner budget",
                    )
                payload["build_trace_enabled"] = True
                payload["build_cache_key"] = build_cache_key
                payload["build_admission_receipt_sha256"] = (
                    admission.receipt_sha256
                )
                payload["source_evidence"] = {
                    "ccbench_commit": evidence.ccbench_commit,
                    "genome_sha256": evidence.genome_sha256,
                    "src_token": evidence.src_token,
                    "source_bytes_sha256": evidence.source_bytes_sha256,
                }
                payload["binary_sha256"] = build.bin_sha256
                payload["ccbench_head"] = head
                payload["genome"] = genome.canonical()
                if (
                    getattr(build, "trace", None) is not True
                    or not re.fullmatch(r"[0-9a-f]{64}", build.bin_sha256)
                ):
                    raise CertificationReject(
                        "trace-build-identity",
                        "trace binary lacks trace identity or a full sha256",
                    )

                trace_dir = Path(
                    tempfile.mkdtemp(
                        prefix=(
                            f"t2187-cert-{workload_id}-slot{args.rep_index}-"
                        ),
                        dir=out.parent,
                    )
                )
                if any(trace_dir.iterdir()):
                    raise CertificationReject(
                        "trace-directory-not-empty",
                        "new trace directory was not empty immediately before run",
                    )
                payload["trace_directory"] = str(trace_dir.resolve(strict=True))

                run_wall_started = time.monotonic()
                run_cpu_started = _cpu_seconds()
                trace_result = _run_trace(
                    build.binary,
                    str(trace_dir),
                    payload["workload_flags"],
                    CLOCKS_PER_US,
                    timeout_s=RUN_TIMEOUT_S,
                    numactl=NUMA,
                )
                payload["run_phase"] = _phase_measurement(
                    run_wall_started, run_cpu_started
                )
                payload["run"] = {
                    "exit_code": trace_result.returncode,
                    "trace_c_lines": trace_result.trace_c_lines,
                    "commit_count": trace_result.commit_count_witness,
                    "batch_commit_count": trace_result.batch_commit_count_witness,
                    "abort_count_stdout": trace_result.abort_counts,
                }
                if trace_result.returncode != 0:
                    raise CertificationReject(
                        "target-run-exit", "trace-enabled target run must exit 0"
                    )
                if not (trace_dir / "log").is_dir():
                    raise CertificationReject(
                        "trace-directory-log-missing", "target trace directory lacks log/"
                    )
                if (
                    trace_result.commit_count_witness is None
                    or trace_result.batch_commit_count_witness != 0
                    or trace_result.trace_c_lines
                    != trace_result.commit_count_witness
                ):
                    raise CertificationReject(
                        "target-commit-witness",
                        "commit_counts/batch_commit_counts/trace C-line witness mismatch",
                    )

                verifier_identity_before = _verifier_identity()
                _require_expected_verifier_identity(
                    verifier_identity_before, expected_verifier_identity
                )
                payload["verifier_identity"] = verifier_identity_before
                positive = _run_verifier(
                    POSITIVE_CONTROL_TRACE,
                    POSITIVE_CONTROL_EXPECTED_COMMITS,
                    POSITIVE_CONTROL_TIMEOUT_S,
                )
                payload["positive_control"] = positive
                _validate_positive_control(positive)

                target = _run_verifier(
                    trace_dir,
                    trace_result.commit_count_witness,
                    args.verifier_timeout_s,
                )
                payload["target_verifier"] = target
                verifier_identity_after = _verifier_identity()
                target_document, target_result = _validate_target(
                    target,
                    trace_dir,
                    trace_result,
                    expected_verifier_identity,
                    verifier_identity_after,
                )
                payload["verify_phase"] = {
                    key: target[key]
                    for key in (
                        "elapsed_seconds",
                        "cpu_seconds",
                        "cpu_over_elapsed",
                        "max_rss_kib",
                    )
                }
                payload["trace_manifest"] = _trace_manifest(trace_dir)
                payload["abort_reasons"] = target_result["stats"]["abort_reasons"]
                payload["abort_count"] = trace_result.abort_counts
                payload["verifier_json"] = target_document
    except CertificationReject as exc:
        rejected = exc
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        rejected = CertificationReject(
            "certification-execution-error", f"{type(exc).__name__}: {exc}"
        )
    finally:
        if trace_dir is not None and trace_dir.is_dir():
            if "trace_manifest" not in payload:
                try:
                    payload["trace_manifest"] = _trace_manifest(trace_dir)
                except OSError:
                    pass
        driver_wall_seconds = max(0.0, time.monotonic() - job_wall_started)
        driver_cpu_seconds = max(0.0, _cpu_seconds() - job_cpu_started)
        wall_seconds = args.prologue_elapsed_s + driver_wall_seconds
        cpu_seconds = args.prologue_cpu_s + driver_cpu_seconds
        if (
            rejected is None
            and wall_seconds + args.exit_margin_s >= args.outer_walltime_s
        ):
            rejected = CertificationReject(
                "certification-outer-budget-exhausted",
                "completed phases left less than the preregistered exit margin",
            )
        payload["job_phase"] = {
            "elapsed_seconds": wall_seconds,
            "cpu_seconds": cpu_seconds,
            "cpu_over_elapsed": cpu_seconds / wall_seconds if wall_seconds > 0 else None,
            "driver_elapsed_seconds": driver_wall_seconds,
            "driver_cpu_seconds": driver_cpu_seconds,
        }
        payload["finished_utc"] = datetime.now(timezone.utc).isoformat()
        if rejected is None:
            payload["terminal_status"] = "certified"
            payload["certified"] = True
            payload["certification_gate"] = "all-10-conditions-passed"
        else:
            payload["terminal_status"] = "rejected"
            payload["certified"] = False
            payload["reject_reason"] = rejected.reason
            payload["reject_detail"] = rejected.detail
            payload["performance_values_remain_uncertified"] = True
        _write_json_create_only(out, payload)

    group_complete = _try_finalize_group(
        result_files,
        group_out,
        performance_artifact,
        performance_artifact_sha256,
        args.attempt_id,
        expected_verifier_identity,
        expected_verifier_identity_file_sha256,
    )
    if group_complete:
        _remove_group_traces(group_out)
    if rejected is not None:
        print(f"[reject] {rejected}", file=sys.stderr, flush=True)
        return 1
    print(f"[certified-request] {out}", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _argument_parser().parse_args(argv)
    if args.mode == "certify":
        return _certify_main(args)
    cells = parse_cells(args.cells)
    _validate_grid_contract(cells)
    workloads = _parse_workloads(args.workloads)
    threads_axis = _parse_threads(args.threads)
    out = Path(args.out)
    _validate_output_path(out)
    from orchestrator.campaign.p2_2 import RECORDS

    if not PATCH.is_file():
        raise FileNotFoundError(f"patch is missing: {PATCH}")

    site = site_policy.current_site()
    if site_policy.refuses_heavy_work(site):
        raise RuntimeError(
            site_policy.heavy_work_refusal(site, "T-2187 adaptive constant probe")
        )
    _assert_single_tenant()

    started_utc = datetime.now(timezone.utc).isoformat()
    wall_started = time.monotonic()
    cpu_started = _cpu_seconds()

    submodule = ROOT / "external" / "ccbench"
    head = _ccbench_head(submodule)
    assert_pinned_clean(str(submodule), CURRENT_PIN)
    cc, cxx = buildcache.compilers_for_current_site()
    cache_root = Path(os.environ["TMPDIR"]) / "build-variants"
    cache_root.mkdir(mode=0o700)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "kind": "performance-only-probe",
        "not_certified": NOT_CERTIFIED,
        "stage": args.stage,
        "grid_spec": args.cells,
        "env_tag": ENV_TAG,
        "site": "pegasus",
        "host": os.uname().nodename,
        "pbs_jobid": os.environ.get("PBS_JOBID"),
        "rep_index": args.rep_index,
        "records": RECORDS,
        "extime_s": args.extime,
        "reps_per_job": args.reps_per_job,
        "clocks_per_us": CLOCKS_PER_US,
        "numactl": NUMA,
        "use_perf": False,
        "ccbench_commit": CURRENT_PIN,
        "ccbench_head": head,
        "cc": cc,
        "cxx": cxx,
        "patch_sha256": hashlib.sha256(PATCH.read_bytes()).hexdigest(),
        "stock": {
            "step_us": STOCK_STEP_US,
            "ceiling_us": STOCK_MAX_US,
            "update_us": STOCK_UPDATE_US,
        },
        "started_utc": started_utc,
        "cells": [],
    }

    with isolated_checkout(submodule, CURRENT_PIN) as work_root:
        with applied(str(PATCH), CURRENT_PIN, work_root):
            build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
            built = []
            for cell in cells:
                genome = genome_for(cell)
                evidence = source_digest.resolve_evidence(
                    genome,
                    CURRENT_PIN,
                    cxx=cxx,
                    ccbench_dir=work_root,
                )
                receipt = attest_generator_output(
                    build_context,
                    evidence,
                    generator_input_sha256=hashlib.sha256(
                        f"{SCHEMA_VERSION}|{evidence.genome_sha256}".encode("utf-8")
                    ).hexdigest(),
                )
                admission = derive_build_admission(
                    build_context, evidence, generator_receipt=receipt
                )
                build_started = time.monotonic()
                build = buildcache.build(
                    genome,
                    ccbench_commit=CURRENT_PIN,
                    trace=False,
                    cc=cc,
                    cxx=cxx,
                    admission=admission,
                    build_context=build_context,
                    source_evidence=evidence,
                    cache_root=str(cache_root),
                    ccbench_dir=work_root,
                )
                built.append((cell, genome, build))
                print(
                    f"[build] {cell.label} sha={build.bin_sha256[:16]} "
                    f"cached={build.cached} "
                    f"{time.monotonic() - build_started:.1f}s",
                    flush=True,
                )

            binary_shas = {
                cell.label: build.bin_sha256 for cell, _genome, build in built
            }
            if len(set(binary_shas.values())) != len(binary_shas):
                raise RuntimeError(
                    "cells produced duplicate binaries; a build define may be inert: "
                    f"{binary_shas}"
                )

            for workload_id in workloads:
                workload = WORKLOADS[workload_id]
                for threads in threads_axis:
                    for cell, genome, build in built:
                        measure_started = time.monotonic()
                        point = measure_point(
                            build.binary,
                            records=RECORDS,
                            threads=threads,
                            clocks_per_us=CLOCKS_PER_US,
                            extime=args.extime,
                            reps=args.reps_per_job,
                            workload=workload,
                            numactl=NUMA,
                            timeout_s=RUN_TIMEOUT_S,
                            use_perf=False,
                        )
                        throughputs = list(point.throughputs)
                        median_tps = (
                            statistics.median(throughputs) if throughputs else None
                        )
                        payload["cells"].append(
                            {
                                "cell": cell.label,
                                "workload": workload_id,
                                "workload_flags": dict(workload),
                                "threads": threads,
                                "back_off": cell.back_off,
                                "step_us": cell.step_us,
                                "ceiling_us": cell.ceiling_us,
                                "update_us": cell.update_us,
                                "is_stock_control": cell.is_stock_control,
                                "genome": genome.canonical(),
                                "binary_sha256": build.bin_sha256,
                                "throughputs": throughputs,
                                "median_tps": median_tps,
                                "abort_rate": point.abort_rate,
                                "latency_ns": point.latency_ns,
                                "run_cmd": point.run_cmd,
                                "measured_utc": datetime.now(timezone.utc).isoformat(),
                            }
                        )
                        shown = (
                            "none" if median_tps is None else f"{median_tps:,.0f}"
                        )
                        print(
                            f"[run] workload={workload_id} t={threads:2d} "
                            f"cell={cell.label} median={shown} tps "
                            f"({time.monotonic() - measure_started:.1f}s)",
                            flush=True,
                        )

    wall_seconds = time.monotonic() - wall_started
    cpu_seconds = _cpu_seconds() - cpu_started
    payload["finished_utc"] = datetime.now(timezone.utc).isoformat()
    payload["wall_seconds"] = wall_seconds
    payload["cpu_seconds"] = cpu_seconds
    payload["cpu_over_elapsed"] = cpu_seconds / wall_seconds

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(
        f"[done] {out} wall={wall_seconds:.1f}s cpu={cpu_seconds:.1f}s "
        f"cpu/wall={payload['cpu_over_elapsed']:.2f}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
