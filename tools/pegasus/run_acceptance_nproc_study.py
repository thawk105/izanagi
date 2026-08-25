#!/usr/bin/env python3
"""Run the preregistered T-1563 acceptance-nproc study in one PBS allocation."""
from __future__ import annotations

import argparse
import contextlib
from dataclasses import dataclass
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any, Callable, Iterable, Mapping, Sequence
import xml.etree.ElementTree as ET


SCHEMA_VERSION = "izanagi-acceptance-nproc-study/v1"
JOB_FAILURE_SCHEMA_VERSION = "izanagi-acceptance-nproc-study-job-failure/v1"
SCHEDULE_ALGORITHM = "sha256-rank-v1"
ARMS = (16, 32, 48)
SHARD_COUNT = 2
FULL_MEASUREMENT_BLOCKS = 6
PER_SHARD_POSTRUN_RESERVE_S = 30
EXCLUDED_ESTIMANDS = (
    {
        "excluded": True,
        "id": "current-k2-default-worker-count-change",
        "statement_ja": "現行 K=2 既定 worker 数の変更根拠には使わない",
    },
)
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_SUBMODULE_RE = re.compile(
    r"^(?P<prefix>[ +U-])(?P<head>[0-9a-f]{40}) (?P<path>[^ ]+)(?: .*)?$"
)
_CACHE_ENV_PREFIXES = ("CCACHE_", "SCCACHE_", "DISTCC_", "ICECC_")
_CACHE_ENV_NAMES = {
    "CMAKE_BUILD_PARALLEL_LEVEL",
    "GCC_EXEC_PREFIX",
    "PYTHONPYCACHEPREFIX",
}


class ContractError(RuntimeError):
    """The run no longer matches the fixed study contract."""


class PostrunDirt(ContractError):
    """A child changed the scratch superproject or one of its submodules."""


class StudyInterrupted(ContractError):
    """The job received a signal that requires process-tree recovery."""


@dataclass(frozen=True)
class ScheduleBlock:
    global_block_index: int
    phase: str
    analysis_block_index: int | None
    cycle: str
    arm_order: tuple[int, ...]


@dataclass(frozen=True)
class StudyConfig:
    repo_root: Path
    output: Path
    scratch_root: Path
    mode: str
    seed: str
    requested_elapstim_s: int
    setup_cap_s: int
    arm_timeout_s: Mapping[int, int]
    finalize_reserve_s: int
    margin_s: int
    python_command: str = "python3.10"


@dataclass(frozen=True)
class ExecRequest:
    purpose: str
    argv: tuple[str, ...]
    cwd: Path
    env: Mapping[str, str]
    timeout_s: float
    stdout_path: Path | None = None
    stderr_path: Path | None = None
    sample_isolation: bool = False
    expected_host: str = ""


@dataclass(frozen=True)
class ExecResult:
    returncode: int
    stdout: bytes
    stderr: bytes
    duration_s: float
    timed_out: bool
    stdout_sha256: str
    stderr_sha256: str
    isolation: Mapping[str, Any]
    process_cleanup: Mapping[str, Any]


Executor = Callable[[ExecRequest], ExecResult]


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rank(seed: str, cycle: str, permutation: Sequence[int]) -> str:
    payload = "\0".join(
        (seed, cycle, ",".join(str(value) for value in permutation))
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_schedule(mode: str, seed: str) -> tuple[ScheduleBlock, ...]:
    """Return the fixed schedule without consulting clocks, files, or processes."""
    if mode not in {"smoke", "full"} or not isinstance(seed, str) or not seed:
        raise ContractError("mode must be smoke/full and seed must be nonempty")
    permutations = tuple(itertools.permutations(ARMS))
    blocks: list[ScheduleBlock] = []
    if mode == "full":
        warmup = min(permutations, key=lambda item: (_rank(seed, "warmup", item), item))
        blocks.append(ScheduleBlock(0, "warmup", None, "warmup", warmup))
        ranked = sorted(
            permutations, key=lambda item: (_rank(seed, "measurement-0", item), item)
        )
        blocks.extend(
            ScheduleBlock(index + 1, "measurement", index, "measurement-0", order)
            for index, order in enumerate(ranked)
        )
    else:
        order = min(permutations, key=lambda item: (_rank(seed, "smoke-0", item), item))
        blocks.append(ScheduleBlock(0, "measurement", 0, "smoke-0", order))
    validate_schedule(blocks, mode=mode)
    return tuple(blocks)


def validate_schedule(blocks: Sequence[ScheduleBlock], *, mode: str) -> None:
    expected_count = 7 if mode == "full" else 1
    if len(blocks) != expected_count:
        raise ContractError(f"schedule block count mismatch: {len(blocks)} != {expected_count}")
    for index, block in enumerate(blocks):
        if block.global_block_index != index or sorted(block.arm_order) != list(ARMS):
            raise ContractError("schedule has an invalid block index or arm permutation")
    measured = [block for block in blocks if block.phase == "measurement"]
    if mode == "full":
        if blocks[0].phase != "warmup" or blocks[0].analysis_block_index is not None:
            raise ContractError("full schedule must begin with one excluded warm-up block")
        expected = set(itertools.permutations(ARMS))
        if {block.arm_order for block in measured} != expected or len(measured) != 6:
            raise ContractError("full measurement schedule must use all six permutations once")
    elif any(block.phase != "measurement" for block in blocks):
        raise ContractError("smoke schedule must not contain warm-up")


def validate_budget(
    *,
    setup_cap_s: int,
    block_count: int,
    arm_timeout_s: Mapping[int, int],
    finalize_reserve_s: int,
    requested_elapstim_s: int,
) -> int:
    if set(arm_timeout_s) != set(ARMS):
        raise ContractError("arm timeout map must contain exactly 16/32/48")
    values = (
        setup_cap_s,
        block_count,
        finalize_reserve_s,
        requested_elapstim_s,
        *arm_timeout_s.values(),
    )
    if any(type(value) is not int or value <= 0 for value in values):
        raise ContractError("all budget values must be positive integers")
    planned = setup_cap_s + block_count * sum(arm_timeout_s.values()) + finalize_reserve_s
    if planned >= requested_elapstim_s:
        raise ContractError(
            "setup + blocks * sum(arm timeouts) + finalize must be strictly below elapstim"
        )
    return planned


def validate_remaining_budget(
    *, remaining_s: int, remaining_arm_timeout_s: int,
    finalize_reserve_s: int, margin_s: int, stage_extra_s: int = 0,
) -> int:
    values = (remaining_s, remaining_arm_timeout_s, finalize_reserve_s, margin_s, stage_extra_s)
    if any(type(value) is not int or value < 0 for value in values):
        raise ContractError("remaining-budget values must be nonnegative integers")
    required = remaining_arm_timeout_s + finalize_reserve_s + margin_s + stage_extra_s
    if remaining_s <= required:
        raise ContractError(
            f"remaining walltime is not strictly above reserve: {remaining_s} <= {required}"
        )
    return required


def allocate_shard_timeout(*, arm_remaining_s: float, remaining_shards: int) -> float:
    """Reserve a postrun fingerprint window for every still-pending shard."""
    if (
        not math.isfinite(arm_remaining_s)
        or arm_remaining_s <= 0
        or type(remaining_shards) is not int
        or remaining_shards <= 0
    ):
        raise ContractError("invalid arm remainder or shard count")
    available = arm_remaining_s - remaining_shards * PER_SHARD_POSTRUN_RESERVE_S
    timeout = available / remaining_shards
    if timeout <= 0:
        raise ContractError("arm cap cannot preserve all postrun fingerprint windows")
    return timeout


def _parse_duration(value: str | None, context: str) -> float:
    try:
        result = float(value or "0")
    except ValueError as exc:
        raise ContractError(f"invalid JUnit duration for {context}") from exc
    if not math.isfinite(result) or result < 0:
        raise ContractError(f"invalid JUnit duration for {context}")
    return result


def analyze_junit(xml_bytes: bytes) -> dict[str, Any]:
    """Validate one shard JUnit document and derive the preregistered diagnostics."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise ContractError(f"JUnit XML is malformed: {exc}") from exc
    if root.tag not in {"testsuite", "testsuites"}:
        raise ContractError(f"unexpected JUnit root: {root.tag}")
    cases = list(root.iter("testcase"))
    if not cases:
        raise ContractError("JUnit contains no testcase")
    identities: list[tuple[str, str, str]] = []
    serial_work = 0.0
    real_repo_chain = 0.0
    real_repo_count = 0
    failures = errors = skipped = 0
    for index, case in enumerate(cases):
        classname = case.attrib.get("classname", "")
        name = case.attrib.get("name", "")
        file_name = case.attrib.get("file", "")
        identity = (classname, name, file_name)
        identity_label = "::".join(identity)
        if not classname and not name:
            raise ContractError(f"JUnit testcase {index} lacks identity")
        identities.append(identity)
        duration = _parse_duration(case.attrib.get("time"), identity_label)
        serial_work += duration
        failures += sum(1 for _ in case.findall("failure"))
        errors += sum(1 for _ in case.findall("error"))
        skipped += sum(1 for _ in case.findall("skipped"))
        marker_text = " ".join((classname, name, file_name)).lower()
        properties = case.find("properties")
        if properties is not None:
            marker_text += " " + " ".join(
                f"{item.attrib.get('name', '')}={item.attrib.get('value', '')}".lower()
                for item in properties.findall("property")
            )
        if "real_repo" in marker_text or "real-repo" in marker_text:
            real_repo_chain += duration
            real_repo_count += 1
    if len(identities) != len(set(identities)):
        raise ContractError("JUnit testcase identities are duplicated")
    return {
        "error_count": errors,
        "failure_count": failures,
        "nodeids_sha256": _sha256(
            "\n".join("::".join(identity) for identity in identities).encode("utf-8")
        ),
        "real_repo_exclusive_chain_s": real_repo_chain,
        "real_repo_test_count": real_repo_count,
        "serial_work_sum_s": serial_work,
        "skipped_count": skipped,
        "testcase_identity_set_sha256": _sha256(
            _canonical_json_bytes(sorted(identities))
        ),
        "test_count": len(cases),
    }


def validate_measurement_argv(argv: Sequence[str], *, clone: Path, session: Path,
                              shard_index: int, python_command: str) -> None:
    expected = [
        python_command,
        str(clone / "tools/run_tests.py"),
        f"--izanagi-acceptance-shard-session={session}",
        "--izanagi-acceptance-shard-count=2",
        f"--izanagi-acceptance-shard-index={shard_index}",
    ]
    if list(argv) != expected:
        raise ContractError(f"internal shard argv differs from the pinned empty-argv form: {argv}")
    if any(token == "-n" or token.startswith("-n=") for token in argv):
        raise ContractError("-n is forbidden for internal shard execution")


def _proc_row(snapshot: Mapping[tuple[int, int], Mapping[str, Any]],
              identity: tuple[int, int]) -> Mapping[str, Any] | None:
    value = snapshot.get(identity)
    return value if isinstance(value, Mapping) else None


def summarize_isolation_samples(
    samples: Sequence[Mapping[str, Any]], *, own_uid: int,
    exempt_pgroups: Iterable[int], expected_host: str, interval_s: float = 1.0,
) -> dict[str, Any]:
    """Summarize continuous samples; process creation between endpoints remains visible."""
    if len(samples) < 2:
        raise ContractError("isolation sampler produced fewer than two samples")
    exempt = set(exempt_pgroups)
    times = [float(sample["monotonic_s"]) for sample in samples]
    gaps = [right - left for left, right in zip(times, times[1:])]
    read_errors = [
        str(error) for sample in samples for error in sample.get("read_errors", [])
    ]
    identities = set().union(
        *(set(sample.get("processes", {})) for sample in samples)
    )
    process_rows: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for identity in sorted(identities):
        seen = [
            _proc_row(sample.get("processes", {}), identity) for sample in samples
        ]
        present = [row for row in seen if row is not None]
        if not present:
            continue
        first = present[0]
        last = present[-1]
        first_ticks = int(first["ticks"])
        last_ticks = int(last["ticks"])
        created = seen[0] is None
        disappeared = seen[-1] is None
        delta = max(0, last_ticks - first_ticks)
        if created:
            delta = max(delta, last_ticks)
        pgroup = int(last["pgroup"])
        row = {
            "command": str(last["command"]),
            "cpu_ticks_delta": delta,
            "created": created,
            "disappeared": disappeared,
            "exempt": pgroup in exempt,
            "first_ticks": first_ticks,
            "last_ticks": last_ticks,
            "pgroup": pgroup,
            "pid": int(identity[0]),
            "starttime": int(identity[1]),
            "uid": int(last["uid"]),
        }
        if delta or created or disappeared:
            process_rows.append(row)
        if not row["exempt"] and delta >= 2:
            candidates.append({
                **row,
                "uid_relation": "same" if row["uid"] == own_uid else "other",
            })
    hosts = [str(sample.get("hostname", "")) for sample in samples]
    max_gap = max(gaps, default=0.0)
    host_match = all(host == expected_host for host in hosts)
    valid = not read_errors and max_gap <= interval_s * 1.75 and host_match
    return {
        "disturbance_candidates": candidates,
        "disturbance_rule": "non-exempt process CPU delta >=2 ticks over continuous samples",
        "disturbed": bool(candidates),
        "host_end": hosts[-1],
        "host_match": host_match,
        "host_start": hosts[0],
        "interval_s": interval_s,
        "max_gap_s": max_gap,
        "processes": process_rows,
        "read_errors": read_errors,
        "sample_count": len(samples),
        "valid": valid,
    }


def validate_process_cleanup(cleanup: Mapping[str, Any]) -> None:
    _expect_keys(
        cleanup,
        {"kill_sent", "reaped", "residual_pids", "term_sent"},
        "process_cleanup",
    )
    if cleanup["reaped"] is not True or cleanup["residual_pids"] != []:
        raise ContractError("measurement process group was not fully reaped")


def _read_proc_snapshot() -> dict[str, Any]:
    processes: dict[tuple[int, int], dict[str, Any]] = {}
    errors: list[str] = []
    try:
        entries = list(Path("/proc").iterdir())
    except OSError as exc:
        return {"processes": {}, "read_errors": [f"proc:{type(exc).__name__}"]}
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            raw = (entry / "stat").read_text(encoding="utf-8")
            closing = raw.rfind(")")
            if closing < 0:
                raise ValueError("stat-comm")
            tail = raw[closing + 2:].split()
            pid = int(entry.name)
            pgroup = int(tail[2])
            ticks = int(tail[11]) + int(tail[12])
            starttime = int(tail[19])
            uid = entry.stat().st_uid
            command = (entry / "cmdline").read_bytes().replace(b"\0", b" ").decode(
                "utf-8", "replace"
            ).strip()[:512]
        except FileNotFoundError:
            continue
        except (OSError, ValueError, IndexError) as exc:
            errors.append(f"{entry.name}:{type(exc).__name__}")
            continue
        processes[(pid, starttime)] = {
            "command": command,
            "pgroup": pgroup,
            "ticks": ticks,
            "uid": uid,
        }
    return {"processes": processes, "read_errors": errors}


class _IsolationSampler:
    def __init__(self, *, arm_pgroup: int, expected_host: str, interval_s: float = 1.0):
        self.arm_pgroup = arm_pgroup
        self.expected_host = expected_host
        self.interval_s = interval_s
        self.samples: list[dict[str, Any]] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, name="nproc-isolation", daemon=True)

    def _sample(self) -> None:
        snapshot = _read_proc_snapshot()
        self.samples.append({
            "hostname": socket.gethostname(),
            "monotonic_s": time.monotonic(),
            **snapshot,
        })

    def _loop(self) -> None:
        next_sample = time.monotonic()
        while not self._stop.is_set():
            self._sample()
            next_sample += self.interval_s
            self._stop.wait(max(0.0, next_sample - time.monotonic()))

    def start(self) -> None:
        self._thread.start()

    def finish(self) -> dict[str, Any]:
        self._stop.set()
        self._thread.join(timeout=5.0)
        if self._thread.is_alive():
            raise ContractError("isolation sampler did not stop")
        self._sample()
        return summarize_isolation_samples(
            self.samples,
            own_uid=os.getuid(),
            exempt_pgroups=(os.getpgrp(), self.arm_pgroup),
            expected_host=self.expected_host,
            interval_s=self.interval_s,
        )


def _pgroup_members(pgroup: int) -> list[int]:
    members: list[int] = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            if os.getpgid(int(entry.name)) == pgroup:
                members.append(int(entry.name))
        except (ProcessLookupError, PermissionError, OSError, ValueError):
            continue
    return sorted(members)


def _terminate_group(process: subprocess.Popen[bytes], pgroup: int) -> dict[str, Any]:
    term_sent = kill_sent = False
    members = _pgroup_members(pgroup)
    if process.poll() is None or members:
        try:
            os.killpg(pgroup, signal.SIGTERM)
            term_sent = True
        except ProcessLookupError:
            pass
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline and _pgroup_members(pgroup):
            time.sleep(0.05)
    members = _pgroup_members(pgroup)
    if members:
        try:
            os.killpg(pgroup, signal.SIGKILL)
            kill_sent = True
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=2.0)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(pgroup, signal.SIGKILL)
            kill_sent = True
        except ProcessLookupError:
            pass
        process.wait(timeout=2.0)
    residual = _pgroup_members(pgroup)
    return {
        "kill_sent": kill_sent,
        "reaped": process.poll() is not None and not residual,
        "residual_pids": residual,
        "term_sent": term_sent,
    }


class ProcessExecutor:
    """The sole production process-creation surface used by the driver."""

    def __call__(self, request: ExecRequest) -> ExecResult:
        if request.timeout_s <= 0 or not math.isfinite(request.timeout_s):
            raise ContractError(f"invalid executor timeout for {request.purpose}")
        for path in (request.stdout_path, request.stderr_path):
            if path is not None and path.exists():
                raise ContractError(f"executor output already exists: {path}")
        stdout_handle = (
            request.stdout_path.open("x+b") if request.stdout_path is not None else tempfile.TemporaryFile()
        )
        stderr_handle = (
            request.stderr_path.open("x+b") if request.stderr_path is not None else tempfile.TemporaryFile()
        )
        started = time.monotonic()
        process_ended = started
        process: subprocess.Popen[bytes] | None = None
        sampler: _IsolationSampler | None = None
        timed_out = False
        cleanup: Mapping[str, Any] = {
            "kill_sent": False, "reaped": False, "residual_pids": [], "term_sent": False,
        }
        try:
            process = subprocess.Popen(
                list(request.argv), cwd=request.cwd, env=dict(request.env),
                stdin=subprocess.DEVNULL, stdout=stdout_handle, stderr=stderr_handle,
                start_new_session=True,
            )
            if request.sample_isolation:
                sampler = _IsolationSampler(
                    arm_pgroup=process.pid, expected_host=request.expected_host
                )
                sampler.start()
            try:
                process.wait(timeout=request.timeout_s)
            except subprocess.TimeoutExpired:
                timed_out = True
            process_ended = time.monotonic()
        finally:
            if process is not None:
                cleanup = _terminate_group(process, process.pid)
            isolation: Mapping[str, Any]
            if sampler is not None:
                isolation = sampler.finish()
            else:
                isolation = {
                    "disturbance_candidates": [],
                    "disturbance_rule": "not-sampled-for-nonmeasurement-command",
                    "disturbed": False,
                    "host_end": "",
                    "host_match": True,
                    "host_start": "",
                    "interval_s": 1.0,
                    "max_gap_s": 0.0,
                    "processes": [],
                    "read_errors": [],
                    "sample_count": 0,
                    "valid": True,
                }
            stdout_handle.flush()
            stderr_handle.flush()
            stdout_handle.seek(0)
            stderr_handle.seek(0)
            stdout = stdout_handle.read()
            stderr = stderr_handle.read()
            stdout_handle.close()
            stderr_handle.close()
        validate_process_cleanup(cleanup)
        return ExecResult(
            returncode=int(process.returncode if process is not None else 127),
            stdout=stdout,
            stderr=stderr,
            duration_s=process_ended - started,
            timed_out=timed_out,
            stdout_sha256=_sha256(stdout),
            stderr_sha256=_sha256(stderr),
            isolation=isolation,
            process_cleanup=cleanup,
        )


def _base_env() -> dict[str, str]:
    env = dict(os.environ)
    for key in list(env):
        if key in _CACHE_ENV_NAMES or key.startswith(_CACHE_ENV_PREFIXES):
            env.pop(key, None)
    env.update({
        "GIT_ALLOW_PROTOCOL": "file",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
    })
    return env


def _execute_checked(executor: Executor, request: ExecRequest) -> ExecResult:
    result = executor(request)
    validate_process_cleanup(result.process_cleanup)
    if result.timed_out or result.returncode != 0:
        message = result.stderr.decode("utf-8", "replace")[-2000:]
        raise ContractError(
            f"executor command failed purpose={request.purpose} rc={result.returncode} "
            f"timeout={result.timed_out}: {message}"
        )
    return result


def _capture(
    executor: Executor, *, purpose: str, argv: Sequence[str], cwd: Path,
    timeout_s: float, env: Mapping[str, str] | None = None,
) -> str:
    result = _execute_checked(executor, ExecRequest(
        purpose=purpose, argv=tuple(argv), cwd=cwd,
        env=_base_env() if env is None else env, timeout_s=timeout_s,
    ))
    return result.stdout.decode("utf-8", "strict")


def _parse_submodules(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        match = _SUBMODULE_RE.fullmatch(line)
        if match is None:
            raise ContractError(f"malformed recursive submodule status: {line!r}")
        path = match.group("path")
        if path.startswith("/") or ".." in Path(path).parts:
            raise ContractError(f"unsafe submodule path: {path}")
        rows.append({
            "head": match.group("head"), "path": path, "status_prefix": match.group("prefix")
        })
    if not rows or any(row["status_prefix"] != " " for row in rows):
        raise ContractError("all recursive submodules must be initialized at their gitlinks")
    if len({row["path"] for row in rows}) != len(rows):
        raise ContractError("recursive submodule paths are duplicated")
    return rows


def _git(executor: Executor, repo: Path, args: Sequence[str], *, purpose: str,
         timeout_s: float) -> str:
    return _capture(
        executor, purpose=purpose, argv=("git", "-C", str(repo), *args),
        cwd=repo.parent, timeout_s=timeout_s,
    )


def collect_fingerprint(executor: Executor, repo: Path, *, label: str,
                        timeout_s: float) -> dict[str, Any]:
    head = _git(executor, repo, ("rev-parse", "HEAD"), purpose=f"{label}:head",
                timeout_s=timeout_s).strip()
    status = _git(
        executor, repo,
        ("status", "--porcelain=v1", "--untracked-files=all", "--ignore-submodules=none"),
        purpose=f"{label}:status", timeout_s=timeout_s,
    )
    diff = _git(executor, repo, ("diff", "--binary"), purpose=f"{label}:diff",
                timeout_s=timeout_s)
    cached = _git(executor, repo, ("diff", "--cached", "--binary"),
                  purpose=f"{label}:cached-diff", timeout_s=timeout_s)
    submodule_text = _git(
        executor, repo, ("submodule", "status", "--recursive"),
        purpose=f"{label}:submodule-status", timeout_s=timeout_s,
    )
    submodules = _parse_submodules(submodule_text)
    sub_rows: list[dict[str, Any]] = []
    for row in submodules:
        child = repo / row["path"]
        child_head = _git(executor, child, ("rev-parse", "HEAD"),
                          purpose=f"{label}:submodule-head:{row['path']}",
                          timeout_s=timeout_s).strip()
        child_status = _git(
            executor, child, ("status", "--porcelain=v1", "--untracked-files=all"),
            purpose=f"{label}:submodule-clean:{row['path']}", timeout_s=timeout_s,
        )
        child_diff = _git(executor, child, ("diff", "--binary"),
                          purpose=f"{label}:submodule-diff:{row['path']}",
                          timeout_s=timeout_s)
        child_cached = _git(executor, child, ("diff", "--cached", "--binary"),
                            purpose=f"{label}:submodule-cached:{row['path']}",
                            timeout_s=timeout_s)
        sub_rows.append({
            "cached_diff_sha256": _sha256(child_cached.encode()),
            "diff_sha256": _sha256(child_diff.encode()),
            "head": child_head,
            "path": row["path"],
            "status": child_status,
        })
    snapshot = {
        "cached_diff_sha256": _sha256(cached.encode()),
        "diff_sha256": _sha256(diff.encode()),
        "head": head,
        "status": status,
        "submodules": sub_rows,
    }
    return {**snapshot, "digest_sha256": _sha256(_canonical_json_bytes(snapshot))}


def _require_clean_fingerprint(fingerprint: Mapping[str, Any], *, context: str) -> None:
    if fingerprint.get("status") != "":
        raise ContractError(f"{context} superproject is dirty")
    for row in fingerprint.get("submodules", []):
        if row.get("status") != "":
            raise ContractError(f"{context} submodule is dirty: {row.get('path')}")


def _remaining(deadline: float) -> float:
    value = deadline - time.monotonic()
    if value <= 0:
        raise ContractError("stage deadline exhausted")
    return value


def _prepare_clone(
    config: StudyConfig, executor: Executor, *, deadline: float,
) -> tuple[Path, dict[str, Any]]:
    repo = config.repo_root
    canonical_head = _git(executor, repo, ("rev-parse", "HEAD"),
                          purpose="canonical-head", timeout_s=_remaining(deadline)).strip()
    canonical_submodules = _parse_submodules(_git(
        executor, repo, ("submodule", "status", "--recursive"),
        purpose="canonical-submodules", timeout_s=_remaining(deadline),
    ))
    canonical_gitlink = _git(
        executor, repo, ("ls-tree", "HEAD", "external/ccbench"),
        purpose="canonical-gitlink", timeout_s=_remaining(deadline),
    ).strip()
    if not canonical_gitlink:
        raise ContractError("external/ccbench gitlink is missing")
    clone = config.scratch_root / "acceptance-nproc-clone"
    if clone.exists():
        raise ContractError(f"scratch clone path already exists: {clone}")
    _execute_checked(executor, ExecRequest(
        purpose="clone-superproject",
        argv=(
            "git", "-c", "protocol.file.allow=always", "clone", "--local",
            "--no-hardlinks", "--no-recurse-submodules", str(repo), str(clone),
        ),
        cwd=config.scratch_root, env=_base_env(), timeout_s=_remaining(deadline),
    ))
    _execute_checked(executor, ExecRequest(
        purpose="checkout-superproject",
        argv=("git", "-C", str(clone), "checkout", "--detach", canonical_head),
        cwd=config.scratch_root, env=_base_env(), timeout_s=_remaining(deadline),
    ))
    for row in sorted(canonical_submodules, key=lambda item: len(Path(item["path"]).parts)):
        source = repo / row["path"]
        destination = clone / row["path"]
        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        _execute_checked(executor, ExecRequest(
            purpose=f"materialize-submodule:{row['path']}",
            argv=(
                "git", "-c", "protocol.file.allow=always", "clone", "--local",
                "--no-hardlinks", "--no-recurse-submodules", str(source), str(destination),
            ),
            cwd=config.scratch_root, env=_base_env(), timeout_s=_remaining(deadline),
        ))
        _execute_checked(executor, ExecRequest(
            purpose=f"checkout-submodule:{row['path']}",
            argv=("git", "-C", str(destination), "checkout", "--detach", row["head"]),
            cwd=config.scratch_root, env=_base_env(), timeout_s=_remaining(deadline),
        ))
    scratch_head = _git(executor, clone, ("rev-parse", "HEAD"),
                        purpose="scratch-head", timeout_s=_remaining(deadline)).strip()
    scratch_submodules = _parse_submodules(_git(
        executor, clone, ("submodule", "status", "--recursive"),
        purpose="scratch-submodules", timeout_s=_remaining(deadline),
    ))
    scratch_gitlink = _git(
        executor, clone, ("ls-tree", "HEAD", "external/ccbench"),
        purpose="scratch-gitlink", timeout_s=_remaining(deadline),
    ).strip()
    if (
        scratch_head != canonical_head
        or scratch_submodules != canonical_submodules
        or scratch_gitlink != canonical_gitlink
    ):
        raise ContractError("scratch clone HEAD/gitlink/recursive submodule status mismatch")
    baseline = collect_fingerprint(
        executor, clone, label="clone-baseline", timeout_s=_remaining(deadline)
    )
    _require_clean_fingerprint(baseline, context="scratch baseline")
    return clone, {
        "canonical_gitlink": canonical_gitlink,
        "canonical_submodules": canonical_submodules,
        "clone_baseline_fingerprint": baseline,
        "repo_head": canonical_head,
        "scratch_gitlink": scratch_gitlink,
        "scratch_submodules": scratch_submodules,
    }


def _parse_qstat(text: str) -> dict[str, Any]:
    limits = re.findall(
        r"(?im)^\s*\(Per-Req\)\s+Elapse Time Limit\s*=\s*Max:\s*([0-9]+)S(?:\s|$)",
        text,
    )
    remaining = re.findall(r"(?im)^\s*Remaining Elapse\s*=\s*([0-9]+)S\s*$", text)
    if len(limits) != 1 or len(remaining) != 1:
        raise ContractError("qstat elapstim fields are absent or ambiguous")
    hosts: list[str] = []
    for value in re.findall(
        r"(?im)^\s*(?:Execution Host|Exec Host)\s*=\s*(\S.*?)\s*$", text
    ):
        hosts.extend(
            token.split("/")[0].split(":")[0]
            for token in re.split(r"[,+\s]+", value)
            if token
        )
    limit_s = int(limits[0])
    remaining_s = int(remaining[0])
    if remaining_s < 0 or remaining_s > limit_s:
        raise ContractError("qstat remaining elapstim is outside its limit")
    return {"execution_hosts": sorted(set(hosts)), "limit_s": limit_s,
            "remaining_s": remaining_s}


def _qstat(executor: Executor, config: StudyConfig, *, purpose: str,
           timeout_s: float = 30.0) -> dict[str, Any]:
    jobid = os.environ.get("PBS_JOBID", "").removeprefix("0:")
    if not jobid:
        raise ContractError("PBS_JOBID is required")
    text = _capture(
        executor, purpose=purpose, argv=("qstat", "-f", jobid),
        cwd=config.repo_root, timeout_s=timeout_s,
    )
    return _parse_qstat(text)


def _allocation_hosts(qstat: Mapping[str, Any]) -> list[str]:
    hosts: list[str] = []
    nodefile = os.environ.get("PBS_NODEFILE", "")
    if nodefile:
        path = Path(nodefile)
        if not path.is_file() or path.is_symlink():
            raise ContractError("PBS_NODEFILE is not a regular file")
        hosts.extend(line.strip() for line in path.read_text(encoding="utf-8").splitlines()
                     if line.strip())
    hosts.extend(str(item) for item in qstat.get("execution_hosts", []))
    result = sorted(set(hosts))
    if not result:
        raise ContractError("allocated host identity is unavailable")
    return result


def _short_host(value: str) -> str:
    return value.split(".", 1)[0]


def _budget_check(
    executor: Executor, config: StudyConfig, checks: list[dict[str, Any]], *,
    stage: str, remaining_arm_timeout_s: int, stage_extra_s: int = 0,
) -> None:
    qstat = _qstat(executor, config, purpose=f"qstat:{stage}")
    required = validate_remaining_budget(
        remaining_s=int(qstat["remaining_s"]),
        remaining_arm_timeout_s=remaining_arm_timeout_s,
        finalize_reserve_s=config.finalize_reserve_s,
        margin_s=config.margin_s,
        stage_extra_s=stage_extra_s,
    )
    checks.append({
        "passed": True,
        "remaining_s": int(qstat["remaining_s"]),
        "required_s": required,
        "stage": stage,
    })


def _create_session(executor: Executor, config: StudyConfig, clone: Path,
                    *, timeout_s: float) -> Path:
    script = clone / "tools/pegasus/run_acceptance_nproc_study.py"
    text = _capture(
        executor, purpose="create-acceptance-shard-session",
        argv=(config.python_command, str(script), "--internal-create-session", str(clone)),
        cwd=clone, timeout_s=timeout_s,
    ).strip()
    if len(text.splitlines()) != 1:
        raise ContractError("acceptance shard session helper returned ambiguous output")
    session = Path(text).resolve()
    if session.parent == clone or clone in session.parents:
        raise ContractError("acceptance shard session was created inside the clone")
    if not all((session / f"shard-{index}").is_dir() for index in range(SHARD_COUNT)):
        raise ContractError("acceptance shard session directories are incomplete")
    return session


def _run_environment(config: StudyConfig, *, global_run_index: int, arm: int,
                     root: Path) -> dict[str, str]:
    env = _base_env()
    for key in ("HOME", "TMPDIR", "XDG_CACHE_HOME", "XDG_CONFIG_HOME",
                "XDG_DATA_HOME", "XDG_STATE_HOME", "PYTEST_ADDOPTS",
                "PYTEST_PLUGINS", "IZANAGI_ACCEPTANCE_SHARDS"):
        env.pop(key, None)
    for key in list(env):
        if key.startswith(("XDG_", *_CACHE_ENV_PREFIXES)) or key in _CACHE_ENV_NAMES:
            env.pop(key, None)
    run_root = root / f"run-{global_run_index:03d}"
    paths = {
        "HOME": run_root / "home",
        "TMPDIR": run_root / "tmp",
        "XDG_CACHE_HOME": run_root / "xdg-cache",
        "XDG_CONFIG_HOME": run_root / "xdg-config",
        "XDG_DATA_HOME": run_root / "xdg-data",
        "XDG_STATE_HOME": run_root / "xdg-state",
    }
    for path in paths.values():
        path.mkdir(mode=0o700, parents=True, exist_ok=False)
    env.update({key: str(value) for key, value in paths.items()})
    env["IZANAGI_TEST_NPROC"] = str(arm)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _schedule_document(blocks: Sequence[ScheduleBlock], *, seed: str) -> list[dict[str, Any]]:
    return [{
        "analysis_block_index": block.analysis_block_index,
        "arm_order": list(block.arm_order),
        "cycle": block.cycle,
        "global_block_index": block.global_block_index,
        "phase": block.phase,
        "rank_sha256": _rank(seed, block.cycle, block.arm_order),
    } for block in blocks]


def _expected_run_manifest(
    blocks: Sequence[ScheduleBlock],
) -> tuple[dict[str, Any], ...]:
    """Expand the block schedule into the exact fixed order of shard runs."""
    manifest: list[dict[str, Any]] = []
    for block in blocks:
        for order_index, arm in enumerate(block.arm_order):
            for shard_index in range(SHARD_COUNT):
                manifest.append({
                    "analysis_block_index": block.analysis_block_index,
                    "analysis_included": block.phase == "measurement",
                    "arm": arm,
                    "global_block_index": block.global_block_index,
                    "global_run_index": len(manifest),
                    "order_index": order_index,
                    "phase": block.phase,
                    "shard_index": shard_index,
                })
    return tuple(manifest)


def validate_run_manifest(
    runs: Sequence[Mapping[str, Any]], blocks: Sequence[ScheduleBlock],
) -> None:
    """Bind every recorded run and shard-pair session to the seeded schedule."""
    expected = _expected_run_manifest(blocks)
    if len(runs) != len(expected):
        raise ContractError(
            f"run manifest length differs from schedule: {len(runs)} != {len(expected)}"
        )
    for index, (run, expected_run) in enumerate(zip(runs, expected)):
        for field, expected_value in expected_run.items():
            observed = run.get(field)
            if type(observed) is not type(expected_value) or observed != expected_value:
                raise ContractError(
                    f"run manifest differs from schedule at run {index} field {field}: "
                    f"{observed!r} != {expected_value!r}"
                )
    for pair_start in range(0, len(runs), SHARD_COUNT):
        pair = runs[pair_start:pair_start + SHARD_COUNT]
        session_roots = [run.get("session_root") for run in pair]
        if (
            any(type(value) is not str or not value for value in session_roots)
            or len(set(session_roots)) != 1
        ):
            raise ContractError(
                f"same-arm shard pair has different session_root at run {pair_start}"
            )


def validate_junit_identity_sets(runs: Sequence[Mapping[str, Any]]) -> None:
    """Require each shard index to execute one exact testcase set in every arm/block."""
    expected_by_shard: dict[int, str] = {}
    for index, run in enumerate(runs):
        shard_index = run.get("shard_index")
        if type(shard_index) is not int or shard_index not in range(SHARD_COUNT):
            raise ContractError(f"run {index} has an invalid shard index")
        junit = run.get("junit")
        if not isinstance(junit, Mapping):
            raise ContractError(f"run {index} has no JUnit diagnostics")
        digest = junit.get("testcase_identity_set_sha256")
        if not isinstance(digest, str) or _HASH_RE.fullmatch(digest) is None:
            raise ContractError(f"run {index} testcase identity set digest is invalid")
        expected_digest = expected_by_shard.setdefault(shard_index, digest)
        if digest != expected_digest:
            raise ContractError(
                f"JUnit testcase identity set differs for shard {shard_index} at run {index}"
            )
    if set(expected_by_shard) != set(range(SHARD_COUNT)):
        raise ContractError("JUnit testcase identity sets do not cover every shard")


def _derive_analysis(runs: Sequence[Mapping[str, Any]], *, mode: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    measured = [run for run in runs if run["analysis_included"]]
    expected_runs = (FULL_MEASUREMENT_BLOCKS if mode == "full" else 1) * len(ARMS) * SHARD_COUNT
    if len(measured) != expected_runs:
        raise ContractError(f"measured run count mismatch: {len(measured)} != {expected_runs}")
    outcomes: list[dict[str, Any]] = []
    block_count = FULL_MEASUREMENT_BLOCKS if mode == "full" else 1
    for block_index in range(block_count):
        for arm in ARMS:
            pair = [
                run for run in measured
                if run["analysis_block_index"] == block_index and run["arm"] == arm
            ]
            if len(pair) != SHARD_COUNT or {run["shard_index"] for run in pair} != {0, 1}:
                raise ContractError("analysis shard pair is incomplete or duplicated")
            walls = [float(run["wall_s"]) for run in sorted(pair, key=lambda row: row["shard_index"])]
            outcome = max(walls)
            chain = max(float(run["junit"]["real_repo_exclusive_chain_s"]) for run in pair)
            outcomes.append({
                "analysis_block_index": block_index,
                "arm": arm,
                "outcome_wall_s": outcome,
                "real_repo_exclusive_chain_s": chain,
                "serial_work_sum_s": sum(float(run["junit"]["serial_work_sum_s"]) for run in pair),
                "shard_walls_s": walls,
                "wall_minus_chain_s": outcome - chain,
            })
    contrasts: list[dict[str, Any]] = []
    for block_index in range(block_count):
        values = {
            row["arm"]: row["outcome_wall_s"]
            for row in outcomes if row["analysis_block_index"] == block_index
        }
        for arm, priority in ((32, "primary"), (16, "secondary")):
            contrasts.append({
                "analysis_block_index": block_index,
                "arm": arm,
                "difference_s": values[arm] - values[48],
                "priority": priority,
                "reference_arm": 48,
            })
    return outcomes, contrasts


def _new_receipt(config: StudyConfig, schedule: Sequence[ScheduleBlock], *,
                 planned_total_s: int) -> dict[str, Any]:
    schedule_doc = _schedule_document(schedule, seed=config.seed)
    return {
        "arm_outcomes": [],
        "budget": {
            "arm_timeout_s": {str(arm): int(config.arm_timeout_s[arm]) for arm in ARMS},
            "budget_checks": [],
            "finalize_reserve_s": config.finalize_reserve_s,
            "margin_s": config.margin_s,
            "planned_total_s": planned_total_s,
            "requested_elapstim_s": config.requested_elapstim_s,
            "setup_cap_s": config.setup_cap_s,
            "strict_inequality": True,
        },
        "cleanup": {
            "canonical_fingerprint_after_sha256": "",
            "canonical_fingerprint_before_sha256": "",
            "canonical_unchanged": False,
            "scratch_clone_preserved_until_job_end": True,
        },
        "completed_epoch_s": 0,
        "contrasts": [],
        "design": {
            "arm_outcome": "max(shard_0_wall_s, shard_1_wall_s)",
            "arm_timeout_scope": "session creation + two shard runs + before/after fingerprints",
            "arms": list(ARMS),
            "measurement_blocks": FULL_MEASUREMENT_BLOCKS if config.mode == "full" else 1,
            "paired_difference": "outcome(N) - outcome(48), within analysis block",
            "per_shard_postrun_reserve_s": PER_SHARD_POSTRUN_RESERVE_S,
            "primary_contrast": {"arm": 32, "reference_arm": 48},
            "real_repo_chain_rule": (
                "sum JUnit testcase time whose identity/property contains real_repo or real-repo; "
                "arm chain is max across its two shards"
            ),
            "secondary_contrast": {"arm": 16, "reference_arm": 48},
            "shard_count": SHARD_COUNT,
            "warmup_blocks": 1 if config.mode == "full" else 0,
        },
        "excluded_estimands": [dict(item) for item in EXCLUDED_ESTIMANDS],
        "failure": None,
        "inputs": {
            "canonical_gitlink": "",
            "canonical_submodules": [],
            "clone_baseline_fingerprint": {
                "cached_diff_sha256": _sha256(b""), "diff_sha256": _sha256(b""),
                "digest_sha256": _sha256(b""), "head": "", "status": "", "submodules": [],
            },
            "clone_root": "",
            "repo_head": "",
            "repo_root": str(config.repo_root),
            "scratch_gitlink": "",
            "scratch_submodules": [],
        },
        "invariant_checks": {
            "all_junit_valid": False,
            "all_process_groups_reaped": False,
            "all_run_fingerprints_match": False,
            "budget_strict": True,
            "canonical_unchanged": False,
            "host_match": False,
            "isolation_valid_and_undisturbed": False,
            "junit_identity_sets_match_by_shard": False,
            "remaining_budget_all_stages": False,
            "run_manifest_matches_schedule": False,
            "submodules_materialized": False,
        },
        "mode": config.mode,
        "occasion": {
            "allocation_hosts": [], "host_match": False,
            "hostname": socket.gethostname(), "pbs_jobid": os.environ.get("PBS_JOBID", ""),
        },
        "runs": [],
        "schedule": schedule_doc,
        "schedule_algorithm": SCHEDULE_ALGORITHM,
        "schema_version": SCHEMA_VERSION,
        "seed": config.seed,
        "status": "running",
    }


@contextlib.contextmanager
def _signal_contract() -> Iterable[None]:
    old: dict[int, Any] = {}

    def handler(signum: int, _frame: Any) -> None:
        raise StudyInterrupted(f"received signal {signum}")

    for signum in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        old[signum] = signal.signal(signum, handler)
    try:
        yield
    finally:
        for signum, previous in old.items():
            signal.signal(signum, previous)


def run_study(config: StudyConfig, executor: Executor) -> tuple[int, dict[str, Any]]:
    if not config.output.is_absolute():
        raise ContractError("output must be an absolute path")
    if config.python_command != "python3.10":
        raise ContractError("measurement interpreter command must be exactly python3.10")
    repo = config.repo_root.resolve(strict=True)
    scratch = config.scratch_root.resolve(strict=True)
    output = config.output.resolve()
    config = StudyConfig(
        repo, output, scratch, config.mode, config.seed, config.requested_elapstim_s,
        config.setup_cap_s, dict(config.arm_timeout_s), config.finalize_reserve_s,
        config.margin_s, config.python_command,
    )
    if output.exists() or output.parent.is_symlink():
        raise ContractError("output must be an absent absolute path under a real parent")
    schedule = build_schedule(config.mode, config.seed)
    planned = validate_budget(
        setup_cap_s=config.setup_cap_s, block_count=len(schedule),
        arm_timeout_s=config.arm_timeout_s,
        finalize_reserve_s=config.finalize_reserve_s,
        requested_elapstim_s=config.requested_elapstim_s,
    )
    output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    artifact_root = output.parent / f"{output.name}.artifacts"
    artifact_root.mkdir(mode=0o700, exist_ok=False)
    env_root = scratch / "acceptance-nproc-run-env"
    env_root.mkdir(mode=0o700, exist_ok=False)
    receipt = _new_receipt(config, schedule, planned_total_s=planned)
    error: BaseException | None = None
    current_stage = "bootstrap"
    canonical_before: Mapping[str, Any] | None = None
    clone: Path | None = None
    started = time.monotonic()
    remaining_caps = [
        int(config.arm_timeout_s[arm]) for block in schedule for arm in block.arm_order
    ]
    try:
        with _signal_contract():
            current_stage = "initial-qstat"
            initial_qstat = _qstat(executor, config, purpose="qstat:initial")
            if int(initial_qstat["limit_s"]) != config.requested_elapstim_s:
                raise ContractError("qstat requested elapstim differs from the pinned CLI value")
            allocation_hosts = _allocation_hosts(initial_qstat)
            hostname = socket.gethostname()
            if not _short_host(hostname).startswith("bnode"):
                raise ContractError("acceptance nproc study must run on a Pegasus bnode")
            host_match = all(_short_host(host) == _short_host(hostname) for host in allocation_hosts)
            if not host_match:
                raise ContractError("allocated host does not match hostname")
            receipt["occasion"].update({
                "allocation_hosts": allocation_hosts, "host_match": True, "hostname": hostname,
            })
            current_stage = "setup-budget"
            _budget_check(
                executor, config, receipt["budget"]["budget_checks"], stage="setup",
                remaining_arm_timeout_s=sum(remaining_caps), stage_extra_s=config.setup_cap_s,
            )
            current_stage = "setup"
            setup_deadline = time.monotonic() + config.setup_cap_s
            canonical_before = collect_fingerprint(
                executor, repo, label="canonical-before", timeout_s=_remaining(setup_deadline)
            )
            _require_clean_fingerprint(canonical_before, context="canonical input")
            clone, clone_inputs = _prepare_clone(config, executor, deadline=setup_deadline)
            receipt["inputs"].update({
                **clone_inputs, "clone_root": str(clone), "repo_root": str(repo),
            })
            receipt["cleanup"]["canonical_fingerprint_before_sha256"] = canonical_before["digest_sha256"]
            receipt["invariant_checks"]["submodules_materialized"] = True
            global_run_index = 0
            flat_arm_index = 0
            for block in schedule:
                current_stage = f"block-{block.global_block_index}"
                block_remaining = sum(remaining_caps[flat_arm_index:])
                _budget_check(
                    executor, config, receipt["budget"]["budget_checks"],
                    stage=f"block-{block.global_block_index}",
                    remaining_arm_timeout_s=block_remaining,
                )
                for order_index, arm in enumerate(block.arm_order):
                    current_stage = f"block-{block.global_block_index}-arm-{arm}"
                    arm_remaining = sum(remaining_caps[flat_arm_index:])
                    _budget_check(
                        executor, config, receipt["budget"]["budget_checks"],
                        stage=f"block-{block.global_block_index}-arm-{arm}",
                        remaining_arm_timeout_s=arm_remaining,
                    )
                    arm_deadline = time.monotonic() + config.arm_timeout_s[arm]
                    session = _create_session(
                        executor, config, clone, timeout_s=_remaining(arm_deadline)
                    )
                    for shard_index in range(SHARD_COUNT):
                        current_stage = (
                            f"block-{block.global_block_index}-arm-{arm}-shard-{shard_index}"
                        )
                        before = collect_fingerprint(
                            executor, clone,
                            label=f"run-{global_run_index}-before",
                            timeout_s=_remaining(arm_deadline),
                        )
                        baseline = receipt["inputs"]["clone_baseline_fingerprint"]
                        if before["digest_sha256"] != baseline["digest_sha256"]:
                            raise ContractError("prerun fingerprint differs from clone baseline")
                        argv = [
                            config.python_command,
                            str(clone / "tools/run_tests.py"),
                            f"--izanagi-acceptance-shard-session={session}",
                            "--izanagi-acceptance-shard-count=2",
                            f"--izanagi-acceptance-shard-index={shard_index}",
                        ]
                        validate_measurement_argv(
                            argv, clone=clone, session=session, shard_index=shard_index,
                            python_command=config.python_command,
                        )
                        child_env = _run_environment(
                            config, global_run_index=global_run_index, arm=arm, root=env_root
                        )
                        child_timeout_s = allocate_shard_timeout(
                            arm_remaining_s=_remaining(arm_deadline),
                            remaining_shards=SHARD_COUNT - shard_index,
                        )
                        stdout_path = artifact_root / f"run-{global_run_index:03d}.stdout"
                        stderr_path = artifact_root / f"run-{global_run_index:03d}.stderr"
                        run_started = time.monotonic()
                        result: ExecResult | None = None
                        child_error: BaseException | None = None
                        try:
                            result = executor(ExecRequest(
                                purpose=f"measurement:{global_run_index}", argv=tuple(argv),
                                cwd=clone, env=child_env, timeout_s=child_timeout_s,
                                stdout_path=stdout_path, stderr_path=stderr_path,
                                sample_isolation=True, expected_host=hostname,
                            ))
                            validate_process_cleanup(result.process_cleanup)
                        except BaseException as exc:
                            child_error = exc
                        after = collect_fingerprint(
                            executor, clone,
                            label=f"run-{global_run_index}-after",
                            timeout_s=_remaining(arm_deadline),
                        )
                        if after["digest_sha256"] != before["digest_sha256"]:
                            raise PostrunDirt(
                                f"run {global_run_index} changed superproject/submodule fingerprint"
                            ) from child_error
                        if child_error is not None:
                            raise child_error
                        assert result is not None
                        junit_path = session / f"shard-{shard_index}" / "junit.xml"
                        if not junit_path.is_file() or junit_path.is_symlink():
                            raise ContractError(f"run {global_run_index} JUnit is missing or unsafe")
                        junit = analyze_junit(junit_path.read_bytes())
                        run_record = {
                            "analysis_block_index": block.analysis_block_index,
                            "analysis_included": block.phase == "measurement",
                            "arm": arm,
                            "argv": argv,
                            "child_returncode": result.returncode,
                            "child_timeout_s": child_timeout_s,
                            "elapsed_end_s": time.monotonic() - started,
                            "elapsed_start_s": run_started - started,
                            "env_nproc": str(arm),
                            "fingerprint_after_sha256": after["digest_sha256"],
                            "fingerprint_before_sha256": before["digest_sha256"],
                            "global_block_index": block.global_block_index,
                            "global_run_index": global_run_index,
                            "host": hostname,
                            "isolation": dict(result.isolation),
                            "junit": junit,
                            "order_index": order_index,
                            "phase": block.phase,
                            "process_cleanup": dict(result.process_cleanup),
                            "session_root": str(session),
                            "shard_index": shard_index,
                            "stderr_sha256": result.stderr_sha256,
                            "stdout_sha256": result.stdout_sha256,
                            "timed_out": result.timed_out,
                            "wall_minus_chain_s": (
                                result.duration_s - junit["real_repo_exclusive_chain_s"]
                            ),
                            "wall_s": result.duration_s,
                        }
                        receipt["runs"].append(run_record)
                        if (
                            result.timed_out or result.returncode != 0
                            or junit["failure_count"] or junit["error_count"]
                        ):
                            raise ContractError(
                                f"run {global_run_index} did not complete green: "
                                f"rc={result.returncode} timeout={result.timed_out}"
                            )
                        if (
                            result.isolation.get("valid") is not True
                            or result.isolation.get("disturbed") is not False
                            or result.isolation.get("host_match") is not True
                        ):
                            raise ContractError(f"run {global_run_index} isolation is invalid/disturbed")
                        global_run_index += 1
                    flat_arm_index += 1
            expected_total = (7 if config.mode == "full" else 1) * len(ARMS) * SHARD_COUNT
            if global_run_index != expected_total:
                raise ContractError("global run count differs from the fixed design")
            validate_run_manifest(receipt["runs"], schedule)
            validate_junit_identity_sets(receipt["runs"])
            outcomes, contrasts = _derive_analysis(receipt["runs"], mode=config.mode)
            receipt["arm_outcomes"] = outcomes
            receipt["contrasts"] = contrasts
            current_stage = "finalize-budget"
            _budget_check(
                executor, config, receipt["budget"]["budget_checks"], stage="finalize",
                remaining_arm_timeout_s=0,
            )
            current_stage = "finalize"
            finalize_deadline = time.monotonic() + config.finalize_reserve_s
            canonical_after = collect_fingerprint(
                executor, repo, label="canonical-after", timeout_s=_remaining(finalize_deadline)
            )
            canonical_unchanged = (
                canonical_before is not None
                and canonical_after["digest_sha256"] == canonical_before["digest_sha256"]
            )
            if not canonical_unchanged:
                raise PostrunDirt("canonical repo fingerprint changed during the study")
            receipt["cleanup"].update({
                "canonical_fingerprint_after_sha256": canonical_after["digest_sha256"],
                "canonical_unchanged": True,
            })
            receipt["invariant_checks"] = {
                "all_junit_valid": True,
                "all_process_groups_reaped": True,
                "all_run_fingerprints_match": True,
                "budget_strict": True,
                "canonical_unchanged": True,
                "host_match": True,
                "isolation_valid_and_undisturbed": True,
                "junit_identity_sets_match_by_shard": True,
                "remaining_budget_all_stages": True,
                "run_manifest_matches_schedule": True,
                "submodules_materialized": True,
            }
            receipt["status"] = "complete"
    except BaseException as exc:
        error = exc
        receipt["status"] = "failed"
        receipt["failure"] = {
            "message": str(exc), "stage": current_stage, "type": type(exc).__name__,
        }
        if canonical_before is not None:
            try:
                canonical_after = collect_fingerprint(
                    executor, repo, label="canonical-failure-finalize",
                    timeout_s=max(1.0, min(60.0, float(config.finalize_reserve_s))),
                )
                unchanged = canonical_after["digest_sha256"] == canonical_before["digest_sha256"]
                receipt["cleanup"].update({
                    "canonical_fingerprint_after_sha256": canonical_after["digest_sha256"],
                    "canonical_unchanged": unchanged,
                })
                receipt["invariant_checks"]["canonical_unchanged"] = unchanged
                if not unchanged and not isinstance(error, PostrunDirt):
                    error = PostrunDirt("canonical repo changed while handling a study failure")
                    receipt["failure"] = {
                        "message": str(error), "stage": "failure-finalize",
                        "type": type(error).__name__,
                    }
            except BaseException as finalize_exc:
                if not isinstance(error, PostrunDirt):
                    receipt["failure"] = {
                        "message": str(finalize_exc), "stage": "failure-finalize",
                        "type": type(finalize_exc).__name__,
                    }
                    error = finalize_exc
    receipt["completed_epoch_s"] = int(time.time())
    validate_receipt(receipt, expected_mode=config.mode, require_complete=False)
    return (0 if error is None and receipt["status"] == "complete" else 1), receipt


def _expect_keys(value: Any, keys: set[str], context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError(f"{context} must be an object")
    actual = set(value)
    if actual != keys:
        raise ContractError(
            f"{context} is not a closed map: missing={sorted(keys - actual)} "
            f"unknown={sorted(actual - keys)}"
        )
    return value


def _validate_fingerprint(value: Any, context: str) -> None:
    row = _expect_keys(
        value,
        {"cached_diff_sha256", "diff_sha256", "digest_sha256", "head", "status", "submodules"},
        context,
    )
    for key in ("cached_diff_sha256", "diff_sha256", "digest_sha256"):
        if not _HASH_RE.fullmatch(str(row[key])):
            raise ContractError(f"{context}.{key} is not sha256")
    if not isinstance(row["submodules"], list):
        raise ContractError(f"{context}.submodules must be a list")
    for index, submodule in enumerate(row["submodules"]):
        _expect_keys(
            submodule,
            {"cached_diff_sha256", "diff_sha256", "head", "path", "status"},
            f"{context}.submodules[{index}]",
        )


def _validate_isolation(value: Any, context: str) -> None:
    row = _expect_keys(
        value,
        {"disturbance_candidates", "disturbance_rule", "disturbed", "host_end", "host_match",
         "host_start", "interval_s", "max_gap_s", "processes", "read_errors", "sample_count", "valid"},
        context,
    )
    process_keys = {
        "command", "cpu_ticks_delta", "created", "disappeared", "exempt", "first_ticks",
        "last_ticks", "pgroup", "pid", "starttime", "uid",
    }
    for index, process in enumerate(row["processes"]):
        _expect_keys(process, process_keys, f"{context}.processes[{index}]")
    for index, process in enumerate(row["disturbance_candidates"]):
        _expect_keys(process, process_keys | {"uid_relation"},
                     f"{context}.disturbance_candidates[{index}]")


def validate_receipt(document: Mapping[str, Any], *, expected_mode: str,
                     require_complete: bool = True) -> None:
    root = _expect_keys(
        document,
        {"arm_outcomes", "budget", "cleanup", "completed_epoch_s", "contrasts", "design",
         "excluded_estimands", "failure", "inputs", "invariant_checks", "mode", "occasion",
         "runs", "schedule", "schedule_algorithm", "schema_version", "seed", "status"},
        "receipt",
    )
    if root["schema_version"] != SCHEMA_VERSION or root["mode"] != expected_mode:
        raise ContractError("receipt schema or mode mismatch")
    if root["schedule_algorithm"] != SCHEDULE_ALGORITHM:
        raise ContractError("receipt schedule algorithm mismatch")
    if root["excluded_estimands"] != [dict(item) for item in EXCLUDED_ESTIMANDS]:
        raise ContractError("receipt excluded_estimands differs from the fixed exclusion")
    _expect_keys(
        root["design"],
        {"arm_outcome", "arms", "measurement_blocks", "paired_difference", "primary_contrast",
         "arm_timeout_scope", "per_shard_postrun_reserve_s", "real_repo_chain_rule",
         "secondary_contrast", "shard_count", "warmup_blocks"},
        "receipt.design",
    )
    _expect_keys(root["design"]["primary_contrast"], {"arm", "reference_arm"},
                 "receipt.design.primary_contrast")
    _expect_keys(root["design"]["secondary_contrast"], {"arm", "reference_arm"},
                 "receipt.design.secondary_contrast")
    if root["design"]["primary_contrast"] != {"arm": 32, "reference_arm": 48}:
        raise ContractError("primary contrast must be 32 versus 48")
    budget = _expect_keys(
        root["budget"],
        {"arm_timeout_s", "budget_checks", "finalize_reserve_s", "margin_s", "planned_total_s",
         "requested_elapstim_s", "setup_cap_s", "strict_inequality"},
        "receipt.budget",
    )
    _expect_keys(budget["arm_timeout_s"], {"16", "32", "48"}, "receipt.budget.arm_timeout_s")
    for index, check in enumerate(budget["budget_checks"]):
        _expect_keys(check, {"passed", "remaining_s", "required_s", "stage"},
                     f"receipt.budget.budget_checks[{index}]")
    inputs = _expect_keys(
        root["inputs"],
        {"canonical_gitlink", "canonical_submodules", "clone_baseline_fingerprint", "clone_root",
         "repo_head", "repo_root", "scratch_gitlink", "scratch_submodules"},
        "receipt.inputs",
    )
    _validate_fingerprint(inputs["clone_baseline_fingerprint"],
                          "receipt.inputs.clone_baseline_fingerprint")
    submodule_keys = {"head", "path", "status_prefix"}
    for field in ("canonical_submodules", "scratch_submodules"):
        for index, row in enumerate(inputs[field]):
            _expect_keys(row, submodule_keys, f"receipt.inputs.{field}[{index}]")
    _expect_keys(
        root["cleanup"],
        {"canonical_fingerprint_after_sha256", "canonical_fingerprint_before_sha256",
         "canonical_unchanged", "scratch_clone_preserved_until_job_end"},
        "receipt.cleanup",
    )
    _expect_keys(root["occasion"], {"allocation_hosts", "host_match", "hostname", "pbs_jobid"},
                 "receipt.occasion")
    invariant_keys = {
        "all_junit_valid", "all_process_groups_reaped", "all_run_fingerprints_match",
        "budget_strict", "canonical_unchanged", "host_match",
        "isolation_valid_and_undisturbed", "junit_identity_sets_match_by_shard",
        "remaining_budget_all_stages", "run_manifest_matches_schedule",
        "submodules_materialized",
    }
    invariants = _expect_keys(root["invariant_checks"], invariant_keys,
                              "receipt.invariant_checks")
    schedule_keys = {
        "analysis_block_index", "arm_order", "cycle", "global_block_index", "phase", "rank_sha256",
    }
    for index, block in enumerate(root["schedule"]):
        _expect_keys(block, schedule_keys, f"receipt.schedule[{index}]")
    expected_blocks = build_schedule(expected_mode, str(root["seed"]))
    expected_schedule = _schedule_document(expected_blocks, seed=str(root["seed"]))
    if root["schedule"] != expected_schedule:
        raise ContractError("receipt schedule differs from the seeded fixed algorithm")
    run_keys = {
        "analysis_block_index", "analysis_included", "arm", "argv", "child_returncode",
        "child_timeout_s", "elapsed_end_s", "elapsed_start_s", "env_nproc", "fingerprint_after_sha256",
        "fingerprint_before_sha256", "global_block_index", "global_run_index", "host", "isolation",
        "junit", "order_index", "phase", "process_cleanup", "session_root", "shard_index",
        "stderr_sha256", "stdout_sha256", "timed_out", "wall_minus_chain_s", "wall_s",
    }
    junit_keys = {
        "error_count", "failure_count", "nodeids_sha256", "real_repo_exclusive_chain_s",
        "real_repo_test_count", "serial_work_sum_s", "skipped_count",
        "testcase_identity_set_sha256", "test_count",
    }
    for index, run in enumerate(root["runs"]):
        _expect_keys(run, run_keys, f"receipt.runs[{index}]")
        _expect_keys(run["junit"], junit_keys, f"receipt.runs[{index}].junit")
        for digest_field in ("nodeids_sha256", "testcase_identity_set_sha256"):
            if _HASH_RE.fullmatch(str(run["junit"][digest_field])) is None:
                raise ContractError(
                    f"receipt.runs[{index}].junit.{digest_field} is not sha256"
                )
        _validate_isolation(run["isolation"], f"receipt.runs[{index}].isolation")
        validate_process_cleanup(run["process_cleanup"])
        validate_measurement_argv(
            run["argv"],
            clone=Path(str(inputs["clone_root"])),
            session=Path(str(run["session_root"])),
            shard_index=int(run["shard_index"]),
            python_command="python3.10",
        )
        if run["env_nproc"] != str(run["arm"]):
            raise ContractError(f"receipt.runs[{index}] env_nproc differs from arm")
    outcome_keys = {
        "analysis_block_index", "arm", "outcome_wall_s", "real_repo_exclusive_chain_s",
        "serial_work_sum_s", "shard_walls_s", "wall_minus_chain_s",
    }
    for index, row in enumerate(root["arm_outcomes"]):
        _expect_keys(row, outcome_keys, f"receipt.arm_outcomes[{index}]")
    contrast_keys = {"analysis_block_index", "arm", "difference_s", "priority", "reference_arm"}
    for index, row in enumerate(root["contrasts"]):
        _expect_keys(row, contrast_keys, f"receipt.contrasts[{index}]")
    if root["failure"] is not None:
        _expect_keys(root["failure"], {"message", "stage", "type"}, "receipt.failure")
    if root["status"] not in {"complete", "failed"}:
        raise ContractError("receipt status is invalid")
    if require_complete or root["status"] == "complete":
        if root["status"] != "complete" or root["failure"] is not None:
            raise ContractError("completed receipt was required")
        if any(value is not True for value in invariants.values()):
            raise ContractError("completed receipt has a false invariant")
        expected_runs = (42 if expected_mode == "full" else 6)
        if len(root["runs"]) != expected_runs:
            raise ContractError("completed receipt has the wrong total run count")
        validate_run_manifest(root["runs"], expected_blocks)
        validate_junit_identity_sets(root["runs"])
        measured = [run for run in root["runs"] if run["analysis_included"]]
        if len(measured) != (36 if expected_mode == "full" else 6):
            raise ContractError("warm-up leaked into or measurement escaped the analysis set")
        baseline_digest = inputs["clone_baseline_fingerprint"]["digest_sha256"]
        if any(
            run["fingerprint_before_sha256"] != baseline_digest
            or run["fingerprint_after_sha256"] != baseline_digest
            for run in root["runs"]
        ):
            raise ContractError("completed receipt contains a non-baseline run fingerprint")
        expected_outcomes, expected_contrasts = _derive_analysis(root["runs"], mode=expected_mode)
        if root["arm_outcomes"] != expected_outcomes or root["contrasts"] != expected_contrasts:
            raise ContractError("receipt analysis differs from the pinned paired estimator")
        if inputs["canonical_submodules"] != inputs["scratch_submodules"]:
            raise ContractError("completed receipt submodule manifests differ")
        if inputs["canonical_gitlink"] != inputs["scratch_gitlink"]:
            raise ContractError("completed receipt top-level gitlink differs")
        planned = validate_budget(
            setup_cap_s=int(budget["setup_cap_s"]),
            block_count=len(root["schedule"]),
            arm_timeout_s={arm: int(budget["arm_timeout_s"][str(arm)]) for arm in ARMS},
            finalize_reserve_s=int(budget["finalize_reserve_s"]),
            requested_elapstim_s=int(budget["requested_elapstim_s"]),
        )
        if planned != budget["planned_total_s"] or budget["strict_inequality"] is not True:
            raise ContractError("completed receipt budget arithmetic differs")
        if not budget["budget_checks"] or any(
            check["passed"] is not True or check["remaining_s"] <= check["required_s"]
            for check in budget["budget_checks"]
        ):
            raise ContractError("completed receipt has a failed remaining-walltime check")


def validate_job_failure_receipt(document: Mapping[str, Any]) -> None:
    row = _expect_keys(
        document,
        {"message", "mode", "pbs_jobid", "recorded_epoch_s", "returncode", "schema_version", "stage"},
        "job_failure_receipt",
    )
    if row["schema_version"] != JOB_FAILURE_SCHEMA_VERSION:
        raise ContractError("job failure receipt schema mismatch")


def _write_json_create_once(path: Path, document: Mapping[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise ContractError(f"refusing to replace receipt: {path}")
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(document, handle, ensure_ascii=True, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
        os.unlink(temporary)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _parse_arm_timeout(values: Sequence[str]) -> dict[int, int]:
    result: dict[int, int] = {}
    for value in values:
        arm_text, separator, timeout_text = value.partition("=")
        if not separator:
            raise argparse.ArgumentTypeError("--arm-timeout-s requires ARM=SECONDS")
        try:
            arm = int(arm_text)
            timeout = int(timeout_text)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("arm timeout values must be integers") from exc
        if arm in result:
            raise argparse.ArgumentTypeError("duplicate arm timeout")
        result[arm] = timeout
    return result


def _internal_create_session(repo_text: str) -> int:
    repo = Path(repo_text).resolve(strict=True)
    sys.path.insert(0, str(repo))
    from tools import acceptance_shards

    session = acceptance_shards.create_session(repo, SHARD_COUNT)
    print(session, flush=True)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--scratch-root", type=Path)
    parser.add_argument("--mode", choices=("smoke", "full"))
    parser.add_argument("--seed")
    parser.add_argument("--requested-elapstim-s", type=int)
    parser.add_argument("--setup-cap-s", type=int)
    parser.add_argument("--arm-timeout-s", action="append", default=[])
    parser.add_argument("--finalize-reserve-s", type=int)
    parser.add_argument("--margin-s", type=int)
    parser.add_argument("--python-command", choices=("python3.10",), default="python3.10")
    parser.add_argument("--validate-receipt", type=Path)
    parser.add_argument("--expected-mode", choices=("smoke", "full"))
    parser.add_argument("--internal-create-session")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.internal_create_session is not None:
        return _internal_create_session(args.internal_create_session)
    if args.validate_receipt is not None:
        if args.expected_mode is None:
            raise SystemExit("--expected-mode is required with --validate-receipt")
        document = json.loads(args.validate_receipt.read_text(encoding="utf-8"))
        validate_receipt(document, expected_mode=args.expected_mode, require_complete=True)
        return 0
    required = {
        "repo_root": args.repo_root, "output": args.output, "scratch_root": args.scratch_root,
        "mode": args.mode, "seed": args.seed,
        "requested_elapstim_s": args.requested_elapstim_s,
        "setup_cap_s": args.setup_cap_s,
        "finalize_reserve_s": args.finalize_reserve_s, "margin_s": args.margin_s,
    }
    missing = sorted(key for key, value in required.items() if value is None)
    if missing:
        raise SystemExit(f"missing required study arguments: {missing}")
    arm_timeouts = _parse_arm_timeout(args.arm_timeout_s)
    config = StudyConfig(
        repo_root=args.repo_root, output=args.output, scratch_root=args.scratch_root,
        mode=args.mode, seed=args.seed,
        requested_elapstim_s=args.requested_elapstim_s,
        setup_cap_s=args.setup_cap_s, arm_timeout_s=arm_timeouts,
        finalize_reserve_s=args.finalize_reserve_s, margin_s=args.margin_s,
        python_command=args.python_command,
    )
    try:
        rc, document = run_study(config, ProcessExecutor())
        _write_json_create_once(config.output.resolve(), document)
        return rc
    except BaseException as exc:
        print(
            f"acceptance nproc study failed before receipt publication: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
