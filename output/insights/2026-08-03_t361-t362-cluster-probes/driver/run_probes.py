#!/usr/bin/env python3
"""Fail-closed login-side controller for the T-361/T-362 probe wave.

The controller owns the submission transaction.  It preserves every raw
command response and derives admissibility only after the compute marker,
scheduler visibility, accounting, output collection, and (for T-361)
Execution Host binding have all been checked.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import secrets
import shutil
import stat
import subprocess
import sys
import time
from typing import Any, Iterable, Mapping, Sequence


SCHEMA = "izanagi-t361-t362-controller/v1"
ATTEMPT_SCHEMA = "izanagi-t361-t362-controller-attempt/v1"
PREFLIGHT_SCHEMA = "izanagi-t361-t362-controller-preflight/v1"
TRACKING_SCHEMA = "izanagi-t361-t362-controller-tracking/v1"
WAVE_STATE_SCHEMA = "izanagi-t361-t362-controller-wave-state/v1"
T361_RESULT_SCHEMA = "izanagi-t361-flock-result/v1"
T361_FINAL_SCHEMA = "izanagi-t361-flock-controller-final/v1"
T362_MARKER_SCHEMA = "t362-signal-marker/v2"
WORK_BASE = Path("/work/1/SFC/tanab/izanagi-jobs/3a7f810a/probe-runs")
EVIDENCE_RELATIVE = Path(
    "output/insights/2026-08-03_t361-t362-cluster-probes/evidence"
)
REQUEST_LIMIT = 6
REQUESTED_NODE_MIN_LIMIT = 40
INITIAL_POINT_STOP = Decimal("20")
QUEUE_DEADLINE_SECONDS = 3600
EXECUTION_GRACE_SECONDS = 300
COMMAND_TIMEOUT_SECONDS = 15
POLL_SECONDS = 5.0

SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
REQUEST_SUBMITTED_RE = re.compile(r"Request\s+(\S+)\s+submitted", re.IGNORECASE)
REQUEST_ID_FIELD_RE = re.compile(
    r"(?im)^\s*Request\s+ID\s*[:=]\s*(\S+)\s*$"
)
STATE_RE = re.compile(
    r"(?im)^\s*(?:Request\s+)?State\s*=\s*(QUE|RUN|HLD|STG|EXT)\s*$"
)
CURRENT_STATE_RE = re.compile(
    r"(?im)^\s*Current\s+State\s*=\s*([^\r\n]+?)\s*$"
)
EXECUTION_HOST_SECTION_RE = re.compile(
    r"(?im)^\s*Execution\s+Hosts\(JSVNO\):\s*$"
)
ACCOUNTING_STARTED_RE = re.compile(
    r"(?im)^\s*Started\s+Request\s+Time\s*:\s*\S.*$"
)
ACCOUNTING_ENDED_RE = re.compile(
    r"(?im)^\s*Ended\s+Request\s+Time\s*:\s*\S.*$"
)
ACCOUNTING_ELAPSE_RE = re.compile(r"(?im)^\s*Elapse\s*:\s*\S.*$")

QSTAT_ERROR_MARKERS = {
    "permission": (
        "not permitted",
        "permission",
        "eacces",
        "not authorized",
        "unauthorized",
        "access denied",
        "not owner",
        "ownership",
    ),
    "transient": (
        "connection",
        "cannot connect",
        "timeout",
        "timed out",
        "server busy",
        "temporarily unavailable",
        "try again",
    ),
}

REQUIRED_EXTERNAL_COMMANDS = (
    "qsub",
    "qstat",
    "qdel",
    "qwait",
    "racctjob",
    "racctreq",
    "rbudgetcheck",
    "git",
)

DRIVER_FILES = (
    "flock_cross_node.pbs",
    "flock_interpreter_probe.py",
    "flock_probe.py",
    "signal_interpreter_probe.py",
    "signal_job_body.sh",
    "signal_observer.py",
    "signal_probe.py",
    "signal_walltime_default.pbs",
    "signal_walltime_mitigation.pbs",
    "signal_walltime_split_warning.pbs",
    "run_probes.py",
    "README.md",
)


class ControllerError(RuntimeError):
    """The transaction cannot continue without weakening an evidence gate."""


@dataclass(frozen=True)
class Leg:
    key: str
    script: str
    mode: str | None
    nodes: int
    walltime_seconds: int
    requested_node_min: int


LEGS = (
    Leg("t361-flock", "flock_cross_node.pbs", None, 2, 300, 10),
    Leg("t362-default", "signal_walltime_default.pbs", "default", 1, 180, 3),
    Leg(
        "t362-split-warning",
        "signal_walltime_split_warning.pbs",
        "split-warning",
        1,
        180,
        3,
    ),
    Leg(
        "t362-mitigation",
        "signal_walltime_mitigation.pbs",
        "mitigation",
        1,
        180,
        3,
    ),
)
LEG_BY_KEY = {leg.key: leg for leg in LEGS}


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _fsync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}.{secrets.token_hex(8)}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(temporary, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(descriptor)
    os.replace(temporary, path)
    _fsync_directory(path.parent)


def _atomic_json(path: Path, value: Any) -> None:
    _atomic_write(path, _json_bytes(value))


def _append_jsonl(path: Path, value: Any) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "ab", closefd=False) as stream:
            stream.write(
                (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(
                    "utf-8"
                )
            )
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(descriptor)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json_object(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ControllerError(f"required JSON is absent or unsafe: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ControllerError(f"cannot read JSON object {path}: {exc}") from exc
    if type(value) is not dict:
        raise ControllerError(f"JSON value is not an object: {path}")
    return value


def _normalize_request_id(value: str) -> str:
    normalized = value.strip().rstrip(".")
    match = re.fullmatch(r"[0-9]+:(.+)", normalized)
    if match is not None:
        normalized = match.group(1)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", normalized):
        raise ControllerError(f"request ID is outside the closed grammar: {value!r}")
    return normalized


def _parse_request_id(stdout: str) -> str:
    match = REQUEST_SUBMITTED_RE.search(stdout)
    if match is not None:
        return _normalize_request_id(match.group(1))
    tokens = stdout.split()
    if len(tokens) == 1:
        return _normalize_request_id(tokens[0])
    raise ControllerError("qsub rc=0 output does not contain one request ID")


def _request_visible(stdout: str, request_id: str) -> bool:
    expected = _normalize_request_id(request_id)
    observed: list[str] = []
    for raw in REQUEST_ID_FIELD_RE.findall(stdout):
        try:
            observed.append(_normalize_request_id(raw))
        except ControllerError:
            continue
    return expected in observed


def _scheduler_state(stdout: str) -> str | None:
    """Byte-for-byte semantic copy of dispatch_compute._scheduler_state."""

    match = STATE_RE.search(stdout)
    if match is not None:
        abbreviated = match.group(1).upper()
        if abbreviated == "STG":
            return "QUE"
        if abbreviated == "EXT":
            return "END"
        return abbreviated
    match = CURRENT_STATE_RE.search(stdout)
    if match is None:
        return None
    value = match.group(1).strip().lower()
    if value in {"running", "pre-running", "run"}:
        return "RUN"
    if value in {"queued", "queue", "waiting", "wait", "staging", "stg"}:
        return "QUE"
    if value in {"held", "hold", "holding"}:
        return "HLD"
    if value in {
        "completed",
        "complete",
        "finished",
        "ended",
        "exited",
        "exit",
        "terminated",
        "exiting",
        "post-running",
        "ext",
    }:
        return "END"
    return None


def _classify_qstat(returncode: int, stdout: str, stderr: str) -> str:
    combined = f"{stdout}\n{stderr}".casefold()
    if any(marker in combined for marker in QSTAT_ERROR_MARKERS["permission"]):
        return "permission"
    if any(marker in combined for marker in QSTAT_ERROR_MARKERS["transient"]):
        return "transient"
    if returncode == 0:
        return "ok"
    return "transient"


def _normalize_host(value: str) -> str:
    token = value.strip().lower().split(".", 1)[0]
    if not re.fullmatch(r"bnode[0-9]+", token):
        raise ControllerError(f"invalid compute host token: {value!r}")
    return token


def _execution_hosts(stdout: str) -> list[str]:
    lines = stdout.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if EXECUTION_HOST_SECTION_RE.fullmatch(line):
            start = index + 1
            break
    if start is None:
        return []
    hosts: list[str] = []
    for line in lines[start:]:
        if not line.startswith((" ", "\t")):
            break
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.endswith(":") or "=" in stripped:
            break
        match = re.match(r"([^\s(),:+/]+)", stripped)
        if match is None:
            break
        try:
            hosts.append(_normalize_host(match.group(1)))
        except ControllerError:
            break
    return hosts


def _request_job_number(raw: str) -> int | None:
    match = re.fullmatch(r"([0-9]+):(.+)", raw.strip().rstrip("."))
    return int(match.group(1)) if match is not None else None


def _extract_marker_identity(marker: Mapping[str, Any]) -> tuple[str, str, int | None]:
    raw_jobid: Any = marker.get("pbs_jobid_raw")
    if type(raw_jobid) is not str:
        pbs_env = marker.get("pbs_environment_raw")
        if type(pbs_env) is dict:
            raw_jobid = pbs_env.get("PBS_JOBID")
    if type(raw_jobid) is not str:
        raw_jobid = marker.get("pbs_jobid")
    if type(raw_jobid) is not str:
        raise ControllerError("compute marker has no string PBS job ID")

    host: Any = marker.get("hostname_short_normalized")
    if type(host) is not str:
        host_object = marker.get("host")
        if type(host_object) is dict:
            host = host_object.get("short_normalized")
    if type(host) is not str:
        host = marker.get("hostname")
    if type(host) is not str:
        raise ControllerError("compute marker has no string hostname")
    return _normalize_request_id(raw_jobid), _normalize_host(host), _request_job_number(raw_jobid)


def _safe_component(value: str, label: str) -> str:
    if not SAFE_COMPONENT.fullmatch(value):
        raise ControllerError(f"unsafe {label}: {value!r}")
    return value


def _assert_absolute_below(path: Path, base: Path, label: str) -> None:
    if not path.is_absolute() or not base.is_absolute():
        raise ControllerError(f"{label} must be absolute")
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise ControllerError(f"{label} is outside {base}: {path}") from exc


def _assert_no_symlink_components(path: Path) -> None:
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        if current.exists() and current.is_symlink():
            raise ControllerError(f"symlink component is forbidden: {current}")


def _mkdir_fresh(base: Path, leg: str, attempt_id: str) -> Path:
    _safe_component(leg, "leg")
    _safe_component(attempt_id, "attempt ID")
    _assert_no_symlink_components(base)
    base.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(base, 0o700)
    leg_root = base / leg
    leg_root.mkdir(mode=0o700, exist_ok=True)
    root = leg_root / attempt_id
    try:
        root.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise ControllerError(f"fresh attempt root already exists: {root}") from exc
    _fsync_directory(leg_root)
    return root


def _driver_root() -> Path:
    return Path(__file__).resolve().parent


def _repo_root(driver_root: Path) -> Path:
    try:
        root = driver_root.parents[3]
    except IndexError as exc:
        raise ControllerError("driver path is not below output/insights") from exc
    expected = root / EVIDENCE_RELATIVE.parent / "driver"
    if expected.resolve() != driver_root:
        raise ControllerError(f"unexpected driver location: {driver_root}")
    return root


def _home_base() -> Path:
    home = Path(pwd.getpwuid(os.getuid()).pw_dir)
    if not home.is_absolute() or not str(home).startswith("/home/"):
        raise ControllerError(f"login home is not below /home: {home}")
    return home / ".izanagi-t361" / "probe-runs"


def _command_paths() -> dict[str, str]:
    paths: dict[str, str] = {}
    for name in REQUIRED_EXTERNAL_COMMANDS:
        resolved = shutil.which(name)
        if resolved is None:
            raise ControllerError(f"required external command is absent from PATH: {name}")
        candidate = Path(resolved)
        if not candidate.exists() or not os.access(candidate, os.X_OK):
            raise ControllerError(f"external command is not executable: {name}={resolved}")
        paths[name] = str(candidate.resolve())
    return paths


def _driver_hashes(driver_root: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for name in DRIVER_FILES:
        path = driver_root / name
        if path.is_symlink() or not path.is_file() or not os.access(path, os.R_OK):
            raise ControllerError(f"driver file is absent, unreadable, or a symlink: {path}")
        result[name] = {"sha256": _sha256(path), "size": path.stat().st_size}
    return result


def _literal_candidates(canonical_source: str) -> tuple[str, ...]:
    tree = ast.parse(canonical_source)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "_INTERPRETER_CANDIDATES":
                    value = ast.literal_eval(node.value)
                    if (
                        type(value) is tuple
                        and value
                        and all(type(item) is str for item in value)
                    ):
                        return value
    raise ControllerError("cannot extract _INTERPRETER_CANDIDATES from canonical dispatcher")


def _byte_comparison(repo_root: Path, driver_root: Path) -> dict[str, Any]:
    canonical = repo_root / "tools/pegasus/dispatch_compute.py"
    if canonical.is_symlink() or not canonical.is_file():
        raise ControllerError(f"canonical dispatcher is absent or a symlink: {canonical}")
    canonical_bytes = canonical.read_bytes()
    canonical_text = canonical_bytes.decode("utf-8")
    candidates = _literal_candidates(canonical_text)
    canonical_template = (
        'selected=""\n'
        "for candidate in {candidates}; do\n"
        '    resolved=$(command -v "$candidate" 2>/dev/null || true)\n'
        '    if [[ -n "$resolved" ]] && "$resolved" "$PROBE" >/dev/null 2>&1; then\n'
        "        selected=$resolved\n"
        "        break\n"
        "    fi\n"
        "done\n"
    )
    canonical_path_line = 'export PATH="$(dirname "$selected"):$PATH"\n'
    if canonical_template.encode("utf-8") not in canonical_bytes:
        raise ControllerError("canonical interpreter template bytes changed")
    if canonical_path_line.encode("utf-8") not in canonical_bytes:
        raise ControllerError("canonical PATH line bytes changed")
    rendered = canonical_template.format(candidates=" ".join(candidates)).encode("utf-8")
    path_bytes = canonical_path_line.encode("utf-8")
    comparison: dict[str, Any] = {
        "canonical_path": str(canonical),
        "canonical_sha256": hashlib.sha256(canonical_bytes).hexdigest(),
        "canonical_template_sha256": hashlib.sha256(
            canonical_template.encode("utf-8")
        ).hexdigest(),
        "rendered_interpreter_loop_sha256": hashlib.sha256(rendered).hexdigest(),
        "path_line_sha256": hashlib.sha256(path_bytes).hexdigest(),
        "candidates": list(candidates),
        "files": {},
    }
    files = (
        "flock_cross_node.pbs",
        "signal_walltime_default.pbs",
        "signal_walltime_mitigation.pbs",
        "signal_job_body.sh",
    )
    for name in files:
        payload = (driver_root / name).read_bytes()
        loop_count = payload.count(rendered)
        path_count = payload.count(path_bytes)
        comparison["files"][name] = {
            "interpreter_loop_exact_byte_matches": loop_count,
            "path_line_exact_byte_matches": path_count,
            "file_sha256": hashlib.sha256(payload).hexdigest(),
        }
        if loop_count != 1 or path_count != 1:
            raise ControllerError(
                f"{name} does not contain exactly one canonical interpreter loop and PATH line"
            )
    return comparison


def _referenced_t36x_names(paths: Iterable[Path], prefix: str) -> set[str]:
    pattern = re.compile(rf"\b{re.escape(prefix)}[A-Z0-9_]*\b")
    names: set[str] = set()
    for path in paths:
        names.update(pattern.findall(path.read_text(encoding="utf-8")))
    return names


def _environment_for(
    leg: Leg, work_root: Path, home_root: Path, driver_root: Path, attempt_id: str
) -> dict[str, str]:
    if leg.key == "t361-flock":
        values = {
            "T361_RUN_ROOT": str(work_root),
            "T361_HOME_ROOT": str(home_root),
            "T361_DRIVER_ROOT": str(driver_root),
            "T361_RECON_ONLY": "0",
            "T361_RUN_NONCE": attempt_id,
            "T361_ATTEMPT_ID": attempt_id,
        }
        referenced = _referenced_t36x_names(
            (driver_root / leg.script, driver_root / "flock_probe.py"), "T361_"
        )
    else:
        assert leg.mode is not None
        values = {
            "T362_RUN_ROOT": str(work_root),
            "T362_DRIVER_ROOT": str(driver_root),
            "T362_MODE": leg.mode,
            "T362_RUN_NONCE": attempt_id,
            "T362_ATTEMPT_ID": attempt_id,
        }
        referenced = _referenced_t36x_names(
            (
                driver_root / leg.script,
                driver_root / "signal_job_body.sh",
                driver_root / "signal_probe.py",
                driver_root / "signal_observer.py",
            ),
            "T362_",
        )
    missing = sorted(referenced - values.keys())
    if missing:
        raise ControllerError(f"qsub environment map omits referenced variables: {missing}")
    for name, value in values.items():
        if not re.fullmatch(r"T36[12]_[A-Z0-9_]+", name):
            raise ControllerError(f"unsafe qsub environment name: {name}")
        if not value or any(character in value for character in ",\n\r"):
            raise ControllerError(f"unsafe qsub environment value for {name}")
    return values


def _qsub_argv(
    leg: Leg,
    work_root: Path,
    home_root: Path,
    driver_root: Path,
    attempt_id: str,
) -> tuple[list[str], dict[str, str], dict[str, str]]:
    environment = _environment_for(leg, work_root, home_root, driver_root, attempt_id)
    env_spec = ",".join(f"{name}={environment[name]}" for name in sorted(environment))
    scheduler_root = work_root / "scheduler"
    scheduler_root.mkdir(mode=0o700)
    stdout_template = scheduler_root / f"{leg.key}.%r.%03j.o"
    stderr_template = scheduler_root / f"{leg.key}.%r.%03j.e"
    argv = [
        "qsub",
        "-v",
        env_spec,
        "-o",
        str(stdout_template),
        "-e",
        str(stderr_template),
        str(driver_root / leg.script),
    ]
    return argv, environment, {
        "stdout_template": str(stdout_template),
        "stderr_template": str(stderr_template),
    }


def _write_probe(path: Path) -> dict[str, Any]:
    payload = secrets.token_bytes(32)
    _atomic_write(path, payload)
    observed = path.read_bytes()
    if observed != payload:
        raise ControllerError(f"read/write probe byte mismatch: {path}")
    return {"path": str(path), "sha256": hashlib.sha256(observed).hexdigest()}


def _preflight(
    *,
    leg: Leg,
    work_root: Path,
    home_root: Path,
    driver_root: Path,
    repo_root: Path,
    attempt_id: str,
    qsub_argv: Sequence[str],
    environment: Mapping[str, str],
    output_templates: Mapping[str, str],
) -> dict[str, Any]:
    path_raw = os.environ.get("PATH")
    if not path_raw:
        raise ControllerError("PATH is unset or empty")
    _assert_absolute_below(work_root, WORK_BASE, "work attempt root")
    home_base = _home_base()
    _assert_absolute_below(home_root, home_base, "home attempt root")
    _assert_no_symlink_components(work_root)
    _assert_no_symlink_components(home_root)
    if stat.S_IMODE(work_root.stat().st_mode) != 0o700:
        raise ControllerError(f"work attempt root mode is not 0700: {work_root}")
    if stat.S_IMODE(home_root.stat().st_mode) != 0o700:
        raise ControllerError(f"home attempt root mode is not 0700: {home_root}")
    if not os.access(driver_root, os.R_OK | os.X_OK):
        raise ControllerError(f"driver root is not readable/searchable: {driver_root}")
    if not os.access(repo_root, os.R_OK | os.W_OK | os.X_OK):
        raise ControllerError(f"repository root is not readable/writable/searchable: {repo_root}")
    command_paths = _command_paths()
    hashes = _driver_hashes(driver_root)
    comparison = _byte_comparison(repo_root, driver_root)
    top_level = _run_git(repo_root, ["git", "rev-parse", "--show-toplevel"])
    head = _run_git(repo_root, ["git", "rev-parse", "HEAD"])
    if top_level.returncode != 0 or Path(
        top_level.stdout.decode("utf-8", errors="strict").strip()
    ) != repo_root:
        raise ControllerError("git top-level does not match the controller repository")
    if head.returncode != 0:
        raise ControllerError("cannot resolve source HEAD")
    source_commit = head.stdout.decode("ascii", errors="strict").strip()
    if not re.fullmatch(r"[0-9a-f]{40,64}", source_commit):
        raise ControllerError("source HEAD is not a full hexadecimal object ID")
    driver_relatives = [str((driver_root / name).relative_to(repo_root)) for name in DRIVER_FILES]
    tracked = _run_git(
        repo_root,
        ["git", "ls-files", "--error-unmatch", "--", *driver_relatives],
    )
    if tracked.returncode != 0:
        raise ControllerError("one or more driver files are not tracked at submission time")
    probes = {
        "work": _write_probe(work_root / "controller" / "work-read-write.probe.raw"),
        "home": _write_probe(home_root / "home-read-write.probe.raw"),
    }
    value = {
        "schema": PREFLIGHT_SCHEMA,
        "leg": leg.key,
        "attempt_id": attempt_id,
        "time_ns": time.time_ns(),
        "path_env_raw": path_raw,
        "command_paths": command_paths,
        "source_commit": source_commit,
        "driver_files_tracked": driver_relatives,
        "driver_hashes": hashes,
        "canonical_byte_comparison": comparison,
        "paths": {
            "repo_root": str(repo_root),
            "driver_root": str(driver_root),
            "work_attempt_root": str(work_root),
            "home_attempt_root": str(home_root),
            **output_templates,
        },
        "read_write_probes": probes,
        "qsub_environment": dict(environment),
        "qsub_argv": list(qsub_argv),
    }
    _atomic_json(work_root / "controller" / "preflight.json", value)
    return value


class Recorder:
    def __init__(self, root: Path):
        self.root = root
        self.raw_root = root / "raw"
        self.raw_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.events = root / "commands.jsonl"
        self.sequence = 0

    def record(
        self,
        argv: Sequence[str],
        purpose: str,
        *,
        timeout: int = COMMAND_TIMEOUT_SECONDS,
    ) -> dict[str, Any]:
        self.sequence += 1
        sequence = self.sequence
        started_ns = time.time_ns()
        monotonic_started = time.monotonic_ns()
        try:
            completed = subprocess.run(
                list(argv),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,
                timeout=timeout,
                check=False,
            )
            returncode = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
            timed_out = False
            error_type = None
        except subprocess.TimeoutExpired as exc:
            returncode = 124
            stdout = exc.stdout if isinstance(exc.stdout, bytes) else b""
            stderr = exc.stderr if isinstance(exc.stderr, bytes) else b""
            timed_out = True
            error_type = "TimeoutExpired"
        except OSError as exc:
            returncode = 127
            stdout = b""
            stderr = str(exc).encode("utf-8", errors="replace")
            timed_out = False
            error_type = type(exc).__name__
        safe_purpose = re.sub(r"[^A-Za-z0-9._-]", "_", purpose)
        stem = f"{sequence:05d}-{safe_purpose}"
        stdout_path = self.raw_root / f"{stem}.stdout.raw"
        stderr_path = self.raw_root / f"{stem}.stderr.raw"
        _atomic_write(stdout_path, stdout)
        _atomic_write(stderr_path, stderr)
        receipt = {
            "schema": SCHEMA,
            "sequence": sequence,
            "purpose": purpose,
            "argv": list(argv),
            "returncode": returncode,
            "timed_out": timed_out,
            "error_type": error_type,
            "started_time_ns": started_ns,
            "duration_ns": time.monotonic_ns() - monotonic_started,
            "stdout_path": str(stdout_path.relative_to(self.root)),
            "stderr_path": str(stderr_path.relative_to(self.root)),
            "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
        }
        _append_jsonl(self.events, receipt)
        return receipt | {
            "stdout_bytes": stdout,
            "stderr_bytes": stderr,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
        }


def _start_background(
    recorder: Recorder,
    argv: Sequence[str],
    purpose: str,
    *,
    environment: Mapping[str, str] | None = None,
) -> tuple[subprocess.Popen[bytes], dict[str, Any], Any, Any]:
    recorder.sequence += 1
    sequence = recorder.sequence
    safe_purpose = re.sub(r"[^A-Za-z0-9._-]", "_", purpose)
    stem = f"{sequence:05d}-{safe_purpose}"
    stdout_path = recorder.raw_root / f"{stem}.stdout.raw"
    stderr_path = recorder.raw_root / f"{stem}.stderr.raw"
    stdout_stream = stdout_path.open("xb", buffering=0)
    stderr_stream = stderr_path.open("xb", buffering=0)
    merged_env = None
    if environment is not None:
        merged_env = dict(os.environ)
        merged_env.update(environment)
        merged_env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        process = subprocess.Popen(
            list(argv),
            stdin=subprocess.DEVNULL,
            stdout=stdout_stream,
            stderr=stderr_stream,
            env=merged_env,
        )
    except OSError:
        stdout_stream.close()
        stderr_stream.close()
        raise
    receipt = {
        "schema": SCHEMA,
        "sequence": sequence,
        "purpose": purpose,
        "argv": list(argv),
        "pid": process.pid,
        "started_time_ns": time.time_ns(),
        "stdout_path": str(stdout_path.relative_to(recorder.root)),
        "stderr_path": str(stderr_path.relative_to(recorder.root)),
    }
    try:
        _append_jsonl(recorder.events, receipt | {"event": "background_started"})
    except BaseException:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        stdout_stream.close()
        stderr_stream.close()
        raise
    return process, receipt, stdout_stream, stderr_stream


def _finish_background(
    recorder: Recorder,
    process: subprocess.Popen[bytes],
    receipt: Mapping[str, Any],
    stdout_stream: Any,
    stderr_stream: Any,
    *,
    timeout: int,
) -> dict[str, Any]:
    timed_out = False
    terminated = False
    try:
        returncode = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.terminate()
        terminated = True
        try:
            returncode = process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            returncode = process.wait(timeout=5)
    finally:
        stdout_stream.close()
        stderr_stream.close()
    stdout_path = recorder.root / str(receipt["stdout_path"])
    stderr_path = recorder.root / str(receipt["stderr_path"])
    stdout = stdout_path.read_bytes()
    stderr = stderr_path.read_bytes()
    result = dict(receipt) | {
        "event": "background_finished",
        "returncode": returncode,
        "timed_out": timed_out,
        "terminated_by_controller": terminated,
        "finished_time_ns": time.time_ns(),
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
        "stdout": stdout.decode("utf-8", errors="replace"),
        "stderr": stderr.decode("utf-8", errors="replace"),
    }
    _append_jsonl(recorder.events, {key: value for key, value in result.items() if key not in {"stdout", "stderr"}})
    return result


def _qstat(recorder: Recorder, request_id: str, purpose: str) -> dict[str, Any]:
    result = recorder.record(["qstat", "-J", "-f", request_id], purpose)
    classification = _classify_qstat(
        int(result["returncode"]), str(result["stdout"]), str(result["stderr"])
    )
    visible = (
        result["returncode"] == 0
        and _request_visible(str(result["stdout"]), request_id)
    )
    return result | {
        "classification": classification,
        "visible": visible,
        "state": _scheduler_state(str(result["stdout"])),
        "execution_hosts": _execution_hosts(str(result["stdout"])),
    }


def _bounded_qstat(recorder: Recorder, request_id: str, purpose: str) -> dict[str, Any]:
    latest: dict[str, Any] | None = None
    classifications: list[str] = []
    for attempt in range(1, 4):
        latest = _qstat(recorder, request_id, f"{purpose}-attempt-{attempt}")
        classifications.append(str(latest["classification"]))
        if latest["classification"] in {"ok", "permission"}:
            break
        if attempt < 3:
            time.sleep(2)
    assert latest is not None
    return latest | {
        "bounded_attempt_classifications": classifications,
        "transient_during_retries": "transient" in classifications,
    }


def _monitor_request(
    recorder: Recorder, request_id: str, walltime_seconds: int
) -> dict[str, Any]:
    started = time.monotonic()
    queue_deadline = started + QUE_DEADLINE_SECONDS
    execution_deadline: float | None = None
    seen_visible = False
    seen_run = False
    saw_transient = False
    best_hosts: list[str] = []
    best_hosts_evidence: dict[str, Any] | None = None
    terminal_reason = "UNSET"
    permission_error = False
    active_at_deadline = False
    qdel_receipt: dict[str, Any] | None = None

    while True:
        observation = _bounded_qstat(recorder, request_id, "lifecycle-qstat")
        classification = str(observation["classification"])
        if classification == "permission":
            permission_error = True
            terminal_reason = "PERMISSION_ERROR"
            break
        if classification == "transient" or observation.get("transient_during_retries"):
            saw_transient = True
        if bool(observation["visible"]):
            seen_visible = True
        hosts = observation.get("execution_hosts")
        if type(hosts) is list and len(hosts) > len(best_hosts):
            best_hosts = list(hosts)
            best_hosts_evidence = {
                "command_sequence": observation.get("sequence"),
                "stdout_path": observation.get("stdout_path"),
                "stdout_sha256": observation.get("stdout_sha256"),
            }
        state = observation.get("state")
        now = time.monotonic()
        if state == "RUN":
            if not seen_run:
                seen_run = True
                execution_deadline = now + walltime_seconds + EXECUTION_GRACE_SECONDS
        elif state == "END":
            terminal_reason = "QSTAT_TERMINAL"
            break
        elif observation["returncode"] == 0 and seen_visible and not observation["visible"]:
            terminal_reason = "VISIBLE_REQUEST_DISAPPEARED"
            break

        if execution_deadline is not None and now >= execution_deadline:
            final = _bounded_qstat(recorder, request_id, "execution-deadline-recheck")
            if final.get("state") == "RUN":
                active_at_deadline = True
                terminal_reason = "ACTIVE_AT_EXECUTION_DEADLINE"
                break
            terminal_reason = "EXECUTION_DEADLINE_TERMINAL_RECHECK"
            break

        if not seen_run and now >= queue_deadline:
            final = _bounded_qstat(recorder, request_id, "queue-deadline-recheck")
            if final.get("state") == "RUN":
                seen_run = True
                execution_deadline = now + walltime_seconds + EXECUTION_GRACE_SECONDS
            else:
                qdel_receipt = recorder.record(
                    ["qdel", request_id], "queue-timeout-bounded-qdel"
                )
                terminal_reason = "QUEUE_TIMEOUT_QDEL_REQUESTED"
                break
        time.sleep(POLL_SECONDS if not seen_run else 1.0)

    return {
        "qstat_visible": seen_visible,
        "qstat_run_seen": seen_run,
        "qstat_transient_error_seen": saw_transient,
        "qstat_permission_error": permission_error,
        "active_at_execution_deadline": active_at_deadline,
        "terminal_reason": terminal_reason,
        "execution_hosts_raw_order": best_hosts,
        "execution_hosts_raw_evidence": best_hosts_evidence,
        "qdel_receipt": qdel_receipt,
    }


def _accounting_valid(text: str, request_id: str, minimum_records: int) -> dict[str, Any]:
    expected = _normalize_request_id(request_id)
    observed: list[str] = []
    invalid_ids: list[str] = []
    for raw in REQUEST_ID_FIELD_RE.findall(text):
        try:
            normalized = _normalize_request_id(raw)
        except ControllerError:
            invalid_ids.append(raw)
            continue
        observed.append(normalized)
    matches = [item for item in observed if item == expected]
    return {
        "expected_request_id": expected,
        "observed_normalized_request_ids": observed,
        "invalid_request_id_fields": invalid_ids,
        "matching_request_record_count": len(matches),
        "minimum_matching_records": minimum_records,
        "started_field_present": ACCOUNTING_STARTED_RE.search(text) is not None,
        "ended_field_present": ACCOUNTING_ENDED_RE.search(text) is not None,
        "elapse_field_present": ACCOUNTING_ELAPSE_RE.search(text) is not None,
        "valid": (
            len(matches) >= minimum_records
            and not invalid_ids
            and all(item == expected for item in observed)
            and ACCOUNTING_STARTED_RE.search(text) is not None
            and ACCOUNTING_ENDED_RE.search(text) is not None
            and ACCOUNTING_ELAPSE_RE.search(text) is not None
        ),
    }


def _collect_accounting(
    recorder: Recorder, request_id: str, expected_jobs: int
) -> dict[str, Any]:
    collected: dict[str, Any] = {}
    for command, minimum in (("racctjob", expected_jobs), ("racctreq", 1)):
        latest: dict[str, Any] | None = None
        for attempt in range(1, 6):
            latest = recorder.record(
                [command, "-I", request_id], f"final-{command}-attempt-{attempt}"
            )
            validity = _accounting_valid(str(latest["stdout"]), request_id, minimum)
            latest = latest | {"accounting_validation": validity}
            if latest["returncode"] == 0 and validity["valid"]:
                break
            if attempt < 5:
                time.sleep(2)
        assert latest is not None
        collected[command] = latest
    return {
        "commands": collected,
        "valid": all(
            value["returncode"] == 0
            and value["accounting_validation"]["valid"]
            for value in collected.values()
        ),
    }


def _collect_job_outputs(work_root: Path, expected_jobs: int) -> dict[str, Any]:
    scheduler_root = work_root / "scheduler"
    manifest: list[dict[str, Any]] = []
    errors: list[str] = []
    counts = {"stdout": 0, "stderr": 0}
    for suffix, label, replacement in (
        (".o", "stdout", ".stdout.raw"),
        (".e", "stderr", ".stderr.raw"),
    ):
        for source in sorted(scheduler_root.glob(f"*{suffix}")):
            if source.is_symlink() or not source.is_file():
                errors.append(f"unsafe scheduler output: {source}")
                continue
            destination = source.with_name(source.name[: -len(suffix)] + replacement)
            if destination.exists():
                errors.append(f"scheduler raw destination exists: {destination}")
                continue
            original = {
                "original_name": source.name,
                "original_path": str(source),
                "original_sha256": _sha256(source),
                "original_size": source.stat().st_size,
            }
            os.replace(source, destination)
            _fsync_directory(scheduler_root)
            counts[label] += 1
            manifest.append(
                original
                | {
                    "stream": label,
                    "saved_name": destination.name,
                    "saved_path": str(destination),
                }
            )
    value = {
        "schema": SCHEMA,
        "expected_job_count_per_stream": expected_jobs,
        "observed_counts": counts,
        "files": manifest,
        "errors": errors,
        "note": ".o/.e are auxiliary; absence is preserved but is not alone an admissibility failure",
        "time_ns": time.time_ns(),
    }
    _atomic_json(work_root / "controller" / "job-output-manifest.json", value)
    return value


def _t361_marker_validation(
    work_root: Path, request_id: str, execution_hosts: Sequence[str]
) -> dict[str, Any]:
    marker_paths = sorted((work_root / "job-markers").glob("marker.*.json"))
    if not marker_paths:
        marker_paths = sorted((work_root / "recon" / "job-markers").glob("marker.*.json"))
    errors: list[str] = []
    markers: list[dict[str, Any]] = []
    identities: list[dict[str, Any]] = []
    for path in marker_paths:
        try:
            marker = _read_json_object(path)
            normalized_id, host, job_number = _extract_marker_identity(marker)
            markers.append(marker)
            identities.append(
                {
                    "path": str(path),
                    "sha256": _sha256(path),
                    "normalized_request_id": normalized_id,
                    "host": host,
                    "job_number": job_number,
                }
            )
        except ControllerError as exc:
            errors.append(str(exc))
    expected_id = _normalize_request_id(request_id)
    normalized_hosts = [_normalize_host(host) for host in execution_hosts]
    marker_hosts = [str(item["host"]) for item in identities]
    job_numbers = [item["job_number"] for item in identities]
    one_to_one = (
        len(identities) == 2
        and all(type(number) is int for number in job_numbers)
        and set(job_numbers) == {0, 1}
        and all(
            normalized_hosts[int(item["job_number"])] == item["host"]
            for item in identities
            if type(item["job_number"]) is int
        )
    ) if len(normalized_hosts) == 2 else False
    valid = (
        not errors
        and len(marker_paths) == 2
        and len(identities) == 2
        and all(item["normalized_request_id"] == expected_id for item in identities)
        and len(set(marker_hosts)) == 2
        and len(normalized_hosts) == 2
        and len(set(normalized_hosts)) == 2
        and set(marker_hosts) == set(normalized_hosts)
        and one_to_one
    )
    return {
        "marker_paths": [str(path) for path in marker_paths],
        "marker_identities": identities,
        "execution_hosts_raw_order": list(execution_hosts),
        "execution_hosts_normalized_order": normalized_hosts,
        "marker_host_set": sorted(set(marker_hosts)),
        "one_to_one_job_number_host_binding": one_to_one,
        "errors": errors,
        "valid": valid,
    }


def _finalize_t361_result(
    work_root: Path,
    attempt_id: str,
    marker_validation: Mapping[str, Any],
) -> dict[str, Any]:
    path = work_root / "flock-result.json"
    final_path = work_root / "controller" / "t361-finalized-result.json"
    try:
        result = _read_json_object(path)
    except ControllerError as exc:
        value = {
            "schema": T361_FINAL_SCHEMA,
            "source_probe_result_path": str(path),
            "source_probe_result_sha256": None,
            "attempt_id": attempt_id,
            "execution_host_validation": dict(marker_validation),
            "result_state": "INVALID_NOT_AUTHORITATIVE",
            "valid_for_safety_conclusion": False,
            "dangerous": None,
            "filesystem_results": {},
            "errors": [str(exc)],
            "time_ns": time.time_ns(),
        }
        _atomic_json(final_path, value)
        return {"path": str(final_path), "valid": False, "errors": value["errors"], "finalized_result_raw": value}

    filesystems = result.get("filesystem_results")
    errors: list[str] = []
    if result.get("schema") != T361_RESULT_SCHEMA:
        errors.append("provisional result schema mismatch")
    if result.get("run_nonce") != attempt_id:
        errors.append("provisional result run_nonce does not bind attempt-id")
    if result.get("result_state") != "PROVISIONAL_NOT_AUTHORITATIVE":
        errors.append("probe result is not explicitly provisional")
    if result.get("overall_verdict") != "PENDING_EXECUTION_HOST_VALIDATION":
        errors.append("provisional overall verdict is not pending host validation")
    if result.get("probe_self_checks_valid_before_execution_host_validation") is not True:
        errors.append("provisional overall probe self-checks are not valid")
    if result.get("valid_for_safety_conclusion") is not False:
        errors.append("provisional result prematurely claims safety validity")
    if result.get("dangerous") is not None:
        errors.append("provisional result dangerous must be null")
    if marker_validation.get("valid") is not True:
        errors.append("qstat Execution Host binding is not valid")
    if result.get("exact_host_pair") != marker_validation.get("marker_host_set"):
        errors.append("provisional exact_host_pair does not bind validated marker hosts")

    finalized_filesystems: dict[str, Any] = {}
    if type(filesystems) is not dict or set(filesystems) != {"work", "home"}:
        errors.append("filesystem_results must contain exactly work and home")
    else:
        for name in ("work", "home"):
            item = filesystems.get(name)
            if type(item) is not dict:
                errors.append(f"{name} result is not an object")
                continue
            if item.get("probe_self_checks_valid_before_execution_host_validation") is not True:
                errors.append(f"{name} probe self-checks are not valid")
            if item.get("verdict") != "PENDING_EXECUTION_HOST_VALIDATION":
                errors.append(f"{name} provisional verdict is not pending host validation")
            if item.get("valid_for_safety_conclusion") is not False:
                errors.append(f"{name} provisional validity must be false")
            if item.get("dangerous") is not None:
                errors.append(f"{name} provisional dangerous must be null")
            observed = item.get(
                "observed_flock_verdict_before_execution_host_validation"
            )
            if observed not in {
                "BLOCKED_EXPECTED",
                "ACQUIRED_SILENT_FAIL_OPEN",
                "ERROR",
                "MIXED",
            }:
                errors.append(f"{name} observed verdict is not finalizable: {observed!r}")
                continue
            finalized_filesystems[name] = {
                "filesystem": name,
                "verdict": observed,
                "valid_for_safety_conclusion": True,
                "dangerous": observed != "BLOCKED_EXPECTED",
                "source_provisional_verdict": item.get("verdict"),
                "execution_host_validation": "VALIDATED_BY_LOGIN_CONTROLLER",
                "raw_attempt_outcomes": item.get("raw_attempt_outcomes"),
                "raw_attempt_outcome_set": item.get("raw_attempt_outcome_set"),
            }

    final_valid = not errors and set(finalized_filesystems) == {"work", "home"}
    if not final_valid:
        for item in finalized_filesystems.values():
            item["valid_for_safety_conclusion"] = False
            item["dangerous"] = None
            item["execution_host_validation"] = "INVALID_OR_INCOMPLETE"
    finalized_dangerous: bool | None = (
        any(item["dangerous"] is True for item in finalized_filesystems.values())
        if final_valid
        else None
    )
    final_verdict: str
    if not final_valid:
        final_verdict = "INVALID_CONTROL"
    else:
        verdicts = {str(item["verdict"]) for item in finalized_filesystems.values()}
        final_verdict = next(iter(verdicts)) if len(verdicts) == 1 else "PATH_DEPENDENT"
    finalized = {
        "schema": T361_FINAL_SCHEMA,
        "source_probe_result_path": str(path),
        "source_probe_result_sha256": _sha256(path),
        "attempt_id": attempt_id,
        "execution_host_validation": dict(marker_validation),
        "overall_verdict": final_verdict,
        "result_state": "FINAL" if final_valid else "INVALID_NOT_AUTHORITATIVE",
        "valid_for_safety_conclusion": final_valid,
        "dangerous": finalized_dangerous,
        "filesystem_results": finalized_filesystems,
        "errors": errors,
        "time_ns": time.time_ns(),
    }
    _atomic_json(final_path, finalized)
    return {
        "path": str(final_path),
        "sha256": _sha256(final_path),
        "source_path": str(path),
        "source_sha256": _sha256(path),
        "overall_verdict_raw": final_verdict,
        "filesystem_results_raw": finalized_filesystems,
        "errors": errors,
        "valid": final_valid,
        "finalized_result_raw": finalized,
    }


def _t362_marker_validation(
    work_root: Path, request_id: str, leg: Leg, attempt_id: str
) -> dict[str, Any]:
    path = work_root / "run_marker.json"
    errors: list[str] = []
    try:
        marker = _read_json_object(path)
        raw_id = marker.get("pbs_jobid")
        if type(raw_id) is not str or _normalize_request_id(raw_id) != _normalize_request_id(request_id):
            errors.append("run marker PBS request ID mismatch")
        if marker.get("normalized_request_id") != _normalize_request_id(request_id):
            errors.append("run marker normalized request ID mismatch")
        if marker.get("mode") != leg.mode:
            errors.append("run marker mode mismatch")
        if marker.get("run_nonce") != attempt_id:
            errors.append("run marker run_nonce mismatch or absence")
        host = marker.get("hostname")
        if type(host) is not str:
            errors.append("run marker hostname missing")
        else:
            _normalize_host(host)
        if marker.get("schema_version") != T362_MARKER_SCHEMA:
            errors.append("run marker schema mismatch")
    except ControllerError as exc:
        marker = None
        errors.append(str(exc))
    return {
        "path": str(path),
        "sha256": _sha256(path) if path.is_file() and not path.is_symlink() else None,
        "marker_raw": marker,
        "errors": errors,
        "valid": not errors,
    }


def _signal_observation_valid(work_root: Path, observer_rc: int) -> dict[str, Any]:
    path = work_root / "observer" / "final_observation.json"
    errors: list[str] = []
    try:
        observation = _read_json_object(path)
    except ControllerError as exc:
        observation = None
        errors.append(str(exc))
    if observer_rc != 0:
        errors.append(f"observer return code is nonzero: {observer_rc}")
    if type(observation) is dict:
        admissible = observation.get("valid_for_safety_conclusion")
        if admissible is None:
            admissible = observation.get("admissible")
        if admissible is not True:
            errors.append("observer final observation is not explicitly admissible")
    return {
        "path": str(path),
        "sha256": _sha256(path) if path.is_file() and not path.is_symlink() else None,
        "observer_returncode": observer_rc,
        "observation_raw": observation,
        "errors": errors,
        "valid": not errors,
    }


def _qwait_valid(leg: Leg, qwait: Mapping[str, Any]) -> dict[str, Any]:
    returncode = qwait.get("returncode")
    combined = f"{qwait.get('stdout', '')}\n{qwait.get('stderr', '')}".casefold()
    if leg.key == "t361-flock":
        valid = returncode == 0
        reason = "T-361 requires normal request completion"
    else:
        valid = returncode == 9 and "elapse" in combined and "limit" in combined
        reason = "T-362 requires qwait code 9 plus raw ELAPSE limit text; this does not identify a signal"
    return {
        "returncode_raw": returncode,
        "valid": valid,
        "requirement": reason,
    }


def _budget_remaining(text: str) -> tuple[str, Decimal] | None:
    matches: list[tuple[str, Decimal]] = []
    for line in text.splitlines():
        fields = line.split()
        if len(fields) != 4 or not re.fullmatch(r"[A-Za-z0-9._-]+", fields[0]):
            continue
        try:
            remaining, estimate, initial = (
                Decimal(fields[1]),
                Decimal(fields[2]),
                Decimal(fields[3]),
            )
        except InvalidOperation:
            continue
        if remaining < 0 or estimate < 0 or initial <= 0:
            continue
        matches.append((fields[0], remaining))
    return matches[0] if len(matches) == 1 else None


def _budget_capture(recorder: Recorder, purpose: str) -> dict[str, Any]:
    result = recorder.record(["rbudgetcheck"], purpose)
    parsed = _budget_remaining(str(result["stdout"])) if result["returncode"] == 0 else None
    value = {
        "purpose": purpose,
        "returncode": result["returncode"],
        "budget_identity_raw": parsed[0] if parsed is not None else None,
        "remaining_point_raw": str(parsed[1]) if parsed is not None else None,
        "point_conversion": "UNDETERMINED; no node-minute conversion is inferred",
        "command_sequence": result["sequence"],
    }
    return value


def _budget_delta(before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, Any]:
    before_identity = before.get("budget_identity_raw")
    after_identity = after.get("budget_identity_raw")
    before_remaining = before.get("remaining_point_raw")
    after_remaining = after.get("remaining_point_raw")
    if (
        type(before_identity) is not str
        or before_identity != after_identity
        or type(before_remaining) is not str
        or type(after_remaining) is not str
    ):
        return {
            "valid": False,
            "decrease_point_raw": None,
            "reason": "budget identity or remaining point is unavailable/mismatched",
            "point_conversion": "UNDETERMINED",
        }
    return {
        "valid": True,
        "budget_identity_raw": before_identity,
        "before_remaining_point_raw": before_remaining,
        "after_remaining_point_raw": after_remaining,
        "decrease_point_raw": str(Decimal(before_remaining) - Decimal(after_remaining)),
        "point_conversion": "UNDETERMINED",
    }


def _tree_inventory(root: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    directories: list[str] = ["."]
    for path in sorted(root.rglob("*")):
        relative = str(path.relative_to(root))
        if path.is_symlink():
            raise ControllerError(f"symlink in evidence tree: {path}")
        if path.is_dir():
            directories.append(relative)
        elif path.is_file():
            files.append(
                {
                    "path": relative,
                    "sha256": _sha256(path),
                    "size": path.stat().st_size,
                }
            )
        else:
            raise ControllerError(f"non-regular evidence entry: {path}")
    return {"root": str(root), "directories": directories, "files": files}


def _run_git(repo_root: Path, argv: Sequence[str]) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            list(argv),
            cwd=repo_root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ControllerError(f"git evidence command failed to execute: {argv}: {exc}") from exc


def _track_evidence(repo_root: Path, evidence_root: Path) -> dict[str, Any]:
    inventory = _tree_inventory(evidence_root)
    paths = [
        str((evidence_root / str(item["path"])).relative_to(repo_root))
        for item in inventory["files"]
    ]
    ignored: list[str] = []
    for relative in paths:
        result = _run_git(repo_root, ["git", "check-ignore", "--", relative])
        if result.returncode == 0:
            ignored.append(relative)
        elif result.returncode != 1:
            raise ControllerError(
                f"git check-ignore failed for {relative}: "
                f"{result.stderr.decode('utf-8', errors='replace')}"
            )
    if ignored:
        raise ControllerError(f"evidence paths are ignored; external roots retained: {ignored}")
    add = _run_git(repo_root, ["git", "add", "--", *paths])
    if add.returncode != 0:
        raise ControllerError(
            "git add failed; external roots retained: "
            + add.stderr.decode("utf-8", errors="replace")
        )
    untracked: list[str] = []
    for relative in paths:
        result = _run_git(
            repo_root, ["git", "ls-files", "--error-unmatch", "--", relative]
        )
        if result.returncode != 0:
            untracked.append(relative)
    if untracked:
        raise ControllerError(
            f"git ls-files did not confirm all evidence; external roots retained: {untracked}"
        )
    return {
        "schema": TRACKING_SCHEMA,
        "evidence_root": str(evidence_root),
        "file_count": len(paths),
        "git_check_ignore_all_not_ignored": True,
        "git_add_returncode": add.returncode,
        "git_ls_files_all_matched": True,
        "inventory": inventory,
        "time_ns": time.time_ns(),
    }


def _copy_attempt_evidence(
    *,
    repo_root: Path,
    session_id: str,
    leg: Leg,
    attempt_id: str,
    work_root: Path,
    home_root: Path,
) -> dict[str, Any]:
    destination = repo_root / EVIDENCE_RELATIVE / session_id / "attempts" / leg.key / attempt_id
    if destination.exists():
        raise ControllerError(f"attempt evidence destination already exists: {destination}")
    destination.mkdir(mode=0o700, parents=True)
    shutil.copytree(work_root, destination / "work", copy_function=shutil.copy2)
    shutil.copytree(home_root, destination / "home", copy_function=shutil.copy2)
    source_inventory = {
        "work": _tree_inventory(work_root),
        "home": _tree_inventory(home_root),
    }
    _atomic_json(destination / "source-tree-inventory.json", source_inventory)
    copied_inventory = {
        "work": _tree_inventory(destination / "work"),
        "home": _tree_inventory(destination / "home"),
    }
    source_projection = {
        name: [(item["path"], item["sha256"], item["size"]) for item in value["files"]]
        for name, value in source_inventory.items()
    }
    copied_projection = {
        name: [(item["path"], item["sha256"], item["size"]) for item in value["files"]]
        for name, value in copied_inventory.items()
    }
    if source_projection != copied_projection:
        raise ControllerError("copied evidence differs from external attempt roots")
    tracking = _track_evidence(repo_root, destination)
    _atomic_json(destination / "tracking-receipt.json", tracking)
    tracking = _track_evidence(repo_root, destination)
    return {"destination": str(destination), "tracking": tracking}


def _remove_attempt_roots(
    *, work_root: Path, home_root: Path, leg: Leg, attempt_id: str
) -> dict[str, Any]:
    expected_work = WORK_BASE / leg.key / attempt_id
    expected_home = _home_base() / leg.key / attempt_id
    if work_root != expected_work or home_root != expected_home:
        raise ControllerError("cleanup target does not exactly match attempt roots")
    _assert_absolute_below(work_root, WORK_BASE, "work cleanup root")
    _assert_absolute_below(home_root, _home_base(), "home cleanup root")
    _assert_no_symlink_components(work_root)
    _assert_no_symlink_components(home_root)
    if work_root.is_symlink() or home_root.is_symlink():
        raise ControllerError("attempt cleanup root became a symlink")
    removed: list[str] = []
    errors: list[str] = []
    for root in (work_root, home_root):
        try:
            shutil.rmtree(root)
            removed.append(str(root))
        except OSError as exc:
            errors.append(f"{root}: {type(exc).__name__}: {exc}")
    receipt = {
        "removed": removed,
        "errors": errors,
        "time_ns": time.time_ns(),
        "valid": not errors,
    }
    if errors:
        raise ControllerError(f"attempt cleanup failed after tracking: {errors}")
    return receipt


class Controller:
    def __init__(self):
        self.driver_root = _driver_root()
        self.repo_root = _repo_root(self.driver_root)
        self.home_base = _home_base()
        controller_base = WORK_BASE / "_controller"
        _assert_no_symlink_components(controller_base)
        controller_base.mkdir(mode=0o700, parents=True, exist_ok=True)
        lock_path = controller_base / "controller.lock"
        self.lock_descriptor = os.open(
            lock_path,
            os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        lock_stat = os.fstat(self.lock_descriptor)
        if not stat.S_ISREG(lock_stat.st_mode) or stat.S_IMODE(lock_stat.st_mode) != 0o600:
            os.close(self.lock_descriptor)
            raise ControllerError("controller.lock is not a regular 0600 file")
        try:
            fcntl.flock(
                self.lock_descriptor,
                fcntl.LOCK_EX | fcntl.LOCK_NB,
            )
        except OSError as exc:
            os.close(self.lock_descriptor)
            raise ControllerError("another probe controller holds controller.lock") from exc
        sessions_root = controller_base / "sessions"
        sessions_root.mkdir(mode=0o700, exist_ok=True)
        stale_sessions = [path for path in sessions_root.iterdir()]
        if stale_sessions:
            raise ControllerError(
                "an earlier controller session is unresolved; no new request may be submitted: "
                + ", ".join(str(path) for path in sorted(stale_sessions))
            )
        self.wave_state_path = controller_base / "wave-state.json"
        if self.wave_state_path.exists():
            self.wave_state = _read_json_object(self.wave_state_path)
        else:
            self.wave_state = {
                "schema": WAVE_STATE_SCHEMA,
                "request_limit": REQUEST_LIMIT,
                "requested_node_min_limit": REQUESTED_NODE_MIN_LIMIT,
                "request_count": 0,
                "cumulative_requested_node_min": 0,
                "requests": [],
                "authoritative_attempts": {},
                "initial_budget": None,
                "initial_four_budget_after": None,
                "latest_budget_after_request": None,
                "created_time_ns": time.time_ns(),
                "updated_time_ns": time.time_ns(),
            }
            _atomic_json(self.wave_state_path, self.wave_state)
        self._validate_wave_state()
        self.request_count = int(self.wave_state["request_count"])
        self.cumulative_node_min = int(
            self.wave_state["cumulative_requested_node_min"]
        )
        self.permanent_stop = False
        self.initial_budget = self.wave_state.get("initial_budget")
        self.latest_budget = self.wave_state.get("latest_budget_after_request")
        self.authoritative = dict(self.wave_state["authoritative_attempts"])
        self.leg_attempt_counts = {
            leg.key: sum(
                request.get("leg") == leg.key
                for request in self.wave_state["requests"]
            )
            for leg in LEGS
        }
        unresolved = [
            request.get("attempt_id")
            for request in self.wave_state["requests"]
            if request.get("completed") is not True
            or (
                request.get("qsub_returncode") == 0
                and request.get("external_root_terminal_proven") is not True
            )
        ]
        if unresolved:
            raise ControllerError(
                "persistent wave state contains an active or terminal-unproven attempt; "
                "no new request may be submitted: "
                + ", ".join(str(value) for value in unresolved)
            )
        timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        self.session_id = f"{timestamp}-{secrets.token_hex(8)}"
        self.runtime_root = _mkdir_fresh(
            WORK_BASE / "_controller", "sessions", self.session_id
        )
        self.recorder = Recorder(self.runtime_root / "controller")
        self.ledger = self.runtime_root / "request-ledger.jsonl"
        self.attempts = self.runtime_root / "attempts.jsonl"

    def _validate_wave_state(self) -> None:
        state = self.wave_state
        if state.get("schema") != WAVE_STATE_SCHEMA:
            raise ControllerError("persistent wave state schema mismatch")
        if state.get("request_limit") != REQUEST_LIMIT:
            raise ControllerError("persistent wave state request limit mismatch")
        if state.get("requested_node_min_limit") != REQUESTED_NODE_MIN_LIMIT:
            raise ControllerError("persistent wave state node-minute limit mismatch")
        requests = state.get("requests")
        authoritative = state.get("authoritative_attempts")
        if type(requests) is not list or type(authoritative) is not dict:
            raise ControllerError("persistent wave state collections are malformed")
        if type(state.get("request_count")) is not int:
            raise ControllerError("persistent request count is not an integer")
        if type(state.get("cumulative_requested_node_min")) is not int:
            raise ControllerError("persistent node-minute total is not an integer")
        seen_attempts: set[str] = set()
        cumulative = 0
        first_admissible: dict[str, str] = {}
        for ordinal, request in enumerate(requests, 1):
            if type(request) is not dict:
                raise ControllerError("persistent wave request is not an object")
            leg_key = request.get("leg")
            if type(leg_key) is not str or leg_key not in LEG_BY_KEY:
                raise ControllerError("persistent wave request has an unknown leg")
            attempt_id = request.get("attempt_id")
            if type(attempt_id) is not str or not SAFE_COMPONENT.fullmatch(attempt_id):
                raise ControllerError("persistent wave request has an unsafe attempt-id")
            if attempt_id in seen_attempts:
                raise ControllerError("persistent wave state repeats an attempt-id")
            seen_attempts.add(attempt_id)
            leg = LEG_BY_KEY[leg_key]
            cumulative += leg.requested_node_min
            if (
                type(request.get("request_ordinal")) is not int
                or request.get("request_ordinal") != ordinal
            ):
                raise ControllerError("persistent request ordinals are not contiguous")
            if (
                type(request.get("requested_node_min")) is not int
                or request.get("requested_node_min") != leg.requested_node_min
            ):
                raise ControllerError("persistent request node-minute charge mismatch")
            if (
                type(request.get("cumulative_requested_node_min")) is not int
                or request.get("cumulative_requested_node_min") != cumulative
            ):
                raise ControllerError("persistent cumulative node-minute charge mismatch")
            argv = request.get("qsub_argv")
            if type(argv) is not list or not argv or not all(type(item) is str for item in argv):
                raise ControllerError("persistent request qsub argv is malformed")
            admissible = request.get("admissible")
            if admissible is True and leg_key not in first_admissible:
                first_admissible[leg_key] = attempt_id
            elif admissible is not None and type(admissible) is not bool:
                raise ControllerError("persistent request admissibility is malformed")
            completed = request.get("completed")
            if type(completed) is not bool:
                raise ControllerError("persistent request completion flag is malformed")
            qsub_returncode = request.get("qsub_returncode")
            request_id = request.get("request_id")
            if qsub_returncode is not None and type(qsub_returncode) is not int:
                raise ControllerError("persistent qsub return code is malformed")
            if request_id is not None:
                if type(request_id) is not str:
                    raise ControllerError("persistent request ID is malformed")
                _normalize_request_id(request_id)
            if completed and type(qsub_returncode) is not int:
                raise ControllerError("completed request lacks a qsub return code")
            if completed and type(request.get("budget_after")) is not dict:
                raise ControllerError("completed request lacks its post-request budget record")
            terminal_proven = request.get("external_root_terminal_proven")
            if completed and type(terminal_proven) is not bool:
                raise ControllerError("completed request lacks terminal-proof state")
            if not completed and terminal_proven is not None:
                raise ControllerError("incomplete request has a terminal-proof state")
        if state.get("request_count") != len(requests):
            raise ControllerError("persistent request count does not match its ledger")
        if state.get("cumulative_requested_node_min") != cumulative:
            raise ControllerError("persistent node-minute total does not match its ledger")
        if len(requests) > REQUEST_LIMIT or cumulative > REQUESTED_NODE_MIN_LIMIT:
            raise ControllerError("persistent wave state already exceeds a fixed limit")
        if authoritative != first_admissible:
            raise ControllerError(
                "persistent authoritative selection is not the first admissible attempt"
            )
        for budget_name in (
            "initial_budget",
            "initial_four_budget_after",
            "latest_budget_after_request",
        ):
            budget = state.get(budget_name)
            if budget is not None and type(budget) is not dict:
                raise ControllerError(f"persistent {budget_name} is malformed")

    def _persist_wave_state(self) -> None:
        self.wave_state["request_count"] = self.request_count
        self.wave_state["cumulative_requested_node_min"] = self.cumulative_node_min
        self.wave_state["authoritative_attempts"] = dict(self.authoritative)
        self.wave_state["initial_budget"] = self.initial_budget
        self.wave_state["latest_budget_after_request"] = self.latest_budget
        self.wave_state["updated_time_ns"] = time.time_ns()
        self._validate_wave_state()
        _atomic_json(self.wave_state_path, self.wave_state)

    def _attempt_id(self, leg: Leg, ordinal: int) -> str:
        timestamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        return f"{timestamp}-{leg.key}-a{ordinal}-{secrets.token_hex(8)}"

    def _reserve_request(
        self, leg: Leg, attempt_id: str, argv: Sequence[str], reserved_time_ns: int
    ) -> None:
        if self.request_count + 1 > REQUEST_LIMIT:
            raise ControllerError("request count limit 6 would be exceeded before qsub")
        if self.cumulative_node_min + leg.requested_node_min > REQUESTED_NODE_MIN_LIMIT:
            raise ControllerError("requested node-minute limit 40 would be exceeded before qsub")
        self.request_count += 1
        self.cumulative_node_min += leg.requested_node_min
        self.leg_attempt_counts[leg.key] += 1
        self.wave_state["requests"].append(
            {
                "request_ordinal": self.request_count,
                "leg": leg.key,
                "attempt_id": attempt_id,
                "requested_node_min": leg.requested_node_min,
                "cumulative_requested_node_min": self.cumulative_node_min,
                "qsub_argv": list(argv),
                "reserved_before_qsub_time_ns": reserved_time_ns,
                "submitted_time_ns": None,
                "qsub_returncode": None,
                "request_id": None,
                "completed": False,
                "admissible": None,
            }
        )
        self._persist_wave_state()

    def _ledger_entry(
        self,
        *,
        leg: Leg,
        attempt_id: str,
        request_id: str | None,
        argv: Sequence[str],
        submitted_time_ns: int,
        qsub_returncode: int,
    ) -> None:
        request = self.wave_state["requests"][-1]
        if request.get("attempt_id") != attempt_id or request.get("leg") != leg.key:
            raise ControllerError("persistent request reservation does not match qsub result")
        request["request_id"] = request_id
        request["qsub_returncode"] = qsub_returncode
        request["submitted_time_ns"] = submitted_time_ns
        self._persist_wave_state()
        _append_jsonl(
            self.ledger,
            {
                "schema": SCHEMA,
                "request_ordinal": self.request_count,
                "request_id": request_id,
                "leg": leg.key,
                "attempt_id": attempt_id,
                "requested_node_min": leg.requested_node_min,
                "cumulative_requested_node_min": self.cumulative_node_min,
                "qsub_argv": list(argv),
                "submitted_time_ns": submitted_time_ns,
                "qsub_returncode": qsub_returncode,
            },
        )

    def _record_attempt_outcome(
        self,
        *,
        leg: Leg,
        attempt_id: str,
        request_id: str | None,
        admissible: bool,
        terminal_proven: bool,
        budget_after: Mapping[str, Any],
    ) -> None:
        request = self.wave_state["requests"][-1]
        if request.get("attempt_id") != attempt_id or request.get("leg") != leg.key:
            raise ControllerError("persistent request reservation does not match attempt result")
        request["request_id"] = request_id
        request["completed"] = True
        request["admissible"] = admissible
        request["external_root_terminal_proven"] = terminal_proven
        request["budget_after"] = dict(budget_after)
        request["completed_time_ns"] = time.time_ns()
        self.latest_budget = dict(budget_after)
        if self.wave_state.get("initial_four_budget_after") is None and all(
            any(
                item.get("leg") == candidate.key and item.get("completed") is True
                for item in self.wave_state["requests"]
            )
            for candidate in LEGS
        ):
            self.wave_state["initial_four_budget_after"] = dict(budget_after)
        if admissible and leg.key not in self.authoritative:
            self.authoritative[leg.key] = attempt_id
            request["selected_as_authoritative"] = True
        else:
            request["selected_as_authoritative"] = False
        self._persist_wave_state()

    def run_attempt(self, leg: Leg, ordinal: int) -> dict[str, Any]:
        attempt_id = self._attempt_id(leg, ordinal)
        work_root = _mkdir_fresh(WORK_BASE, leg.key, attempt_id)
        home_root = _mkdir_fresh(self.home_base, leg.key, attempt_id)
        _append_jsonl(
            self.attempts,
            {
                "event": "attempt_roots_created",
                "leg": leg.key,
                "attempt_id": attempt_id,
                "work_root": str(work_root),
                "home_root": str(home_root),
                "time_ns": time.time_ns(),
            },
        )
        controller_root = work_root / "controller"
        controller_root.mkdir(mode=0o700)
        attempt_recorder = Recorder(controller_root)
        argv, environment, output_templates = _qsub_argv(
            leg, work_root, home_root, self.driver_root, attempt_id
        )
        _preflight(
            leg=leg,
            work_root=work_root,
            home_root=home_root,
            driver_root=self.driver_root,
            repo_root=self.repo_root,
            attempt_id=attempt_id,
            qsub_argv=argv,
            environment=environment,
            output_templates=output_templates,
        )
        budget_before = _budget_capture(attempt_recorder, "rbudgetcheck-before-qsub")
        if budget_before["returncode"] != 0:
            raise ControllerError("pre-qsub rbudgetcheck failed; qsub is forbidden")
        reserved_time_ns = time.time_ns()
        self._reserve_request(leg, attempt_id, argv, reserved_time_ns)
        submitted_time_ns = time.time_ns()
        qsub = attempt_recorder.record(argv, "qsub")
        request_id: str | None = None
        if qsub["returncode"] == 0:
            try:
                request_id = _parse_request_id(str(qsub["stdout"]))
            except ControllerError:
                request_id = None
        self._ledger_entry(
            leg=leg,
            attempt_id=attempt_id,
            request_id=request_id,
            argv=argv,
            submitted_time_ns=submitted_time_ns,
            qsub_returncode=int(qsub["returncode"]),
        )

        validity: dict[str, Any] = {
            "qsub_rc_zero": qsub["returncode"] == 0,
            "request_id_parsed": request_id is not None,
        }
        observer_bundle: tuple[subprocess.Popen[bytes], dict[str, Any], Any, Any] | None = None
        qwait_bundle: tuple[subprocess.Popen[bytes], dict[str, Any], Any, Any] | None = None
        monitor: dict[str, Any] = {}
        qwait: dict[str, Any] = {"returncode": None, "stdout": "", "stderr": ""}
        observer: dict[str, Any] = {"returncode": None}
        accounting: dict[str, Any] = {"valid": False, "commands": {}}

        if request_id is not None:
            qwait_bundle = _start_background(
                attempt_recorder,
                [
                    "qwait",
                    "-t",
                    str(QUEUE_DEADLINE_SECONDS + leg.walltime_seconds + EXECUTION_GRACE_SECONDS),
                    request_id,
                ],
                "qwait",
            )
            if leg.mode is not None:
                observer_env = dict(environment)
                observer_bundle = _start_background(
                    attempt_recorder,
                    [
                        sys.executable,
                        str(self.driver_root / "signal_observer.py"),
                        "--request-id",
                        request_id,
                        "--requested-walltime-seconds",
                        str(leg.walltime_seconds),
                    ],
                    "signal-observer",
                    environment=observer_env,
                )
            try:
                monitor = _monitor_request(
                    attempt_recorder, request_id, leg.walltime_seconds
                )
            except BaseException:
                if observer_bundle is not None:
                    _finish_background(
                        attempt_recorder,
                        *observer_bundle,
                        timeout=0,
                    )
                _finish_background(
                    attempt_recorder,
                    *qwait_bundle,
                    timeout=0,
                )
                raise
            if monitor.get("qstat_permission_error"):
                self.permanent_stop = True
            assert qwait_bundle is not None
            qwait = _finish_background(
                attempt_recorder,
                *qwait_bundle,
                timeout=(
                    QUEUE_DEADLINE_SECONDS
                    + leg.walltime_seconds
                    + EXECUTION_GRACE_SECONDS
                    + 30
                    if monitor.get("qstat_permission_error")
                    else 30
                ),
            )
            if observer_bundle is not None:
                observer = _finish_background(
                    attempt_recorder,
                    *observer_bundle,
                    timeout=60,
                )
            accounting = _collect_accounting(attempt_recorder, request_id, leg.nodes)

        outputs = _collect_job_outputs(work_root, leg.nodes)
        budget_after = _budget_capture(attempt_recorder, "rbudgetcheck-after-request")
        self.latest_budget = budget_after
        qwait_validation = _qwait_valid(leg, qwait)
        validity.update(
            {
                "qstat_visible": bool(monitor.get("qstat_visible")),
                "qstat_no_transient_error": not bool(
                    monitor.get("qstat_transient_error_seen", True)
                ),
                "qstat_no_permission_error": not bool(
                    monitor.get("qstat_permission_error", True)
                ),
                "request_not_active_at_deadline": not bool(
                    monitor.get("active_at_execution_deadline", True)
                ),
                "accounting_valid": bool(accounting.get("valid")),
                "qwait_valid": bool(qwait_validation["valid"]),
                "job_output_collection_error_free": not outputs["errors"],
                "rbudgetcheck_before_rc_zero": budget_before["returncode"] == 0,
                "rbudgetcheck_after_rc_zero": budget_after["returncode"] == 0,
            }
        )

        if request_id is not None and leg.key == "t361-flock":
            marker_validation = _t361_marker_validation(
                work_root,
                request_id,
                monitor.get("execution_hosts_raw_order", []),
            )
            _atomic_json(
                controller_root / "t361-qstat-execution-host-comparison.json",
                marker_validation,
            )
            result_validation = _finalize_t361_result(
                work_root, attempt_id, marker_validation
            )
            observer_validation = None
            validity["compute_marker_valid"] = marker_validation["valid"]
            validity["execution_host_binding_valid"] = marker_validation["valid"]
            validity["probe_result_self_checks_valid"] = result_validation["valid"]
        elif request_id is not None:
            marker_validation = _t362_marker_validation(
                work_root, request_id, leg, attempt_id
            )
            result_validation = None
            observer_validation = _signal_observation_valid(
                work_root, int(observer.get("returncode", 127))
            )
            validity["compute_marker_valid"] = marker_validation["valid"]
            validity["observer_acceptance_valid"] = observer_validation["valid"]
        else:
            marker_validation = {"valid": False, "errors": ["request ID unavailable"]}
            result_validation = None
            observer_validation = None
            validity["compute_marker_valid"] = False

        admissible = all(value is True for value in validity.values())
        external_root_terminal_proof = {
            "request_id_available": request_id is not None,
            "request_not_active_at_controller_stop": not bool(
                monitor.get("active_at_execution_deadline", True)
            ),
            "qwait_terminal_receipt_valid": bool(qwait_validation["valid"]),
            "accounting_ended_request_valid": bool(accounting.get("valid")),
        }
        external_root_terminal_proof["valid"] = all(
            value is True for value in external_root_terminal_proof.values()
        )
        if qsub["returncode"] == 0 and not external_root_terminal_proof["valid"]:
            self.permanent_stop = True
        attempt_result = {
            "schema": ATTEMPT_SCHEMA,
            "session_id": self.session_id,
            "leg": leg.key,
            "attempt_id": attempt_id,
            "request_id": request_id,
            "request_ordinal": self.request_count,
            "requested_node_min": leg.requested_node_min,
            "cumulative_requested_node_min": self.cumulative_node_min,
            "qsub_argv": argv,
            "qsub_receipt": {key: value for key, value in qsub.items() if key not in {"stdout_bytes", "stderr_bytes", "stdout", "stderr"}},
            "monitor": monitor,
            "qwait_validation": qwait_validation,
            "accounting_validation": {
                "valid": accounting.get("valid"),
                "commands": {
                    name: value.get("accounting_validation")
                    for name, value in accounting.get("commands", {}).items()
                },
            },
            "job_output_manifest": outputs,
            "marker_validation": marker_validation,
            "probe_result_validation": result_validation,
            "observer_validation": observer_validation,
            "external_root_terminal_proof": external_root_terminal_proof,
            "budget_before": budget_before,
            "budget_after": budget_after,
            "budget_delta": _budget_delta(budget_before, budget_after),
            "validity_conjunction": validity,
            "admissible": admissible,
            "dangerous": None,
            "dangerous_note": (
                "controller admissibility is not a safety verdict; raw probe results retain "
                "the dangerous/safe observation"
            ),
            "time_ns": time.time_ns(),
        }
        _atomic_json(controller_root / "attempt-result.json", attempt_result)
        copied = _copy_attempt_evidence(
            repo_root=self.repo_root,
            session_id=self.session_id,
            leg=leg,
            attempt_id=attempt_id,
            work_root=work_root,
            home_root=home_root,
        )
        self._record_attempt_outcome(
            leg=leg,
            attempt_id=attempt_id,
            request_id=request_id,
            admissible=admissible,
            terminal_proven=bool(external_root_terminal_proof["valid"]),
            budget_after=budget_after,
        )
        if external_root_terminal_proof["valid"]:
            cleanup = _remove_attempt_roots(
                work_root=work_root,
                home_root=home_root,
                leg=leg,
                attempt_id=attempt_id,
            )
            event = "attempt_staged_tracked_and_terminal_roots_removed"
        else:
            cleanup = {
                "removed": [],
                "errors": [],
                "valid": False,
                "retained": [str(work_root), str(home_root)],
                "reason": "external roots retained because request terminal state is unproven",
                "time_ns": time.time_ns(),
            }
            event = "attempt_staged_tracked_but_unproven_roots_retained"
        _append_jsonl(
            self.attempts,
            {
                "event": event,
                "leg": leg.key,
                "attempt_id": attempt_id,
                "request_id": request_id,
                "admissible": admissible,
                "evidence_destination": copied["destination"],
                "cleanup": cleanup,
                "time_ns": time.time_ns(),
            },
        )
        return attempt_result

    def _initial_point_gate(self) -> dict[str, Any]:
        before_raw = None if self.initial_budget is None else self.initial_budget.get("remaining_point_raw")
        initial_four_after = self.wave_state.get("initial_four_budget_after")
        after_raw = (
            None
            if initial_four_after is None
            else initial_four_after.get("remaining_point_raw")
        )
        before_identity = None if self.initial_budget is None else self.initial_budget.get("budget_identity_raw")
        after_identity = (
            None
            if initial_four_after is None
            else initial_four_after.get("budget_identity_raw")
        )
        if type(before_raw) is not str or type(after_raw) is not str:
            return {
                "valid": False,
                "stop_before_retry": True,
                "reason": "rbudgetcheck remaining point could not be parsed; no conversion inferred",
                "before_raw": before_raw,
                "after_raw": after_raw,
            }
        if (
            type(before_identity) is not str
            or before_identity != after_identity
        ):
            return {
                "valid": False,
                "stop_before_retry": True,
                "reason": "rbudgetcheck budget identity changed or is absent",
                "before_identity_raw": before_identity,
                "after_identity_raw": after_identity,
            }
        decrease = Decimal(before_raw) - Decimal(after_raw)
        return {
            "valid": True,
            "stop_before_retry": decrease > INITIAL_POINT_STOP,
            "reason": (
                "initial four requests exceeded 20 point"
                if decrease > INITIAL_POINT_STOP
                else "initial four requests did not exceed 20 point"
            ),
            "before_raw": before_raw,
            "after_raw": after_raw,
            "budget_identity_raw": before_identity,
            "decrease_point_raw": str(decrease),
            "point_conversion": "UNDETERMINED",
        }

    def _finalize_runtime(self, summary: Mapping[str, Any]) -> None:
        _atomic_json(self.runtime_root / "wave-state-snapshot.json", self.wave_state)
        _atomic_json(self.runtime_root / "session-summary.json", summary)
        destination = self.repo_root / EVIDENCE_RELATIVE / self.session_id / "controller"
        if destination.exists():
            raise ControllerError(f"controller evidence destination exists: {destination}")
        shutil.copytree(self.runtime_root, destination, copy_function=shutil.copy2)
        source = _tree_inventory(self.runtime_root)
        copied = _tree_inventory(destination)
        source_projection = [(item["path"], item["sha256"], item["size"]) for item in source["files"]]
        copied_projection = [(item["path"], item["sha256"], item["size"]) for item in copied["files"]]
        if source_projection != copied_projection:
            raise ControllerError("controller runtime copy differs from source")
        tracking = _track_evidence(self.repo_root, destination)
        _atomic_json(destination / "tracking-receipt.json", tracking)
        _track_evidence(self.repo_root, destination)
        expected = WORK_BASE / "_controller" / "sessions" / self.session_id
        if self.runtime_root != expected:
            raise ControllerError("controller runtime cleanup target mismatch")
        _assert_no_symlink_components(self.runtime_root)
        if self.runtime_root.is_symlink():
            raise ControllerError("controller runtime cleanup root became a symlink")
        shutil.rmtree(self.runtime_root)

    def run(self) -> int:
        session_started_ns = time.time_ns()
        session_initial_budget = _budget_capture(
            self.recorder, "rbudgetcheck-before-controller-session"
        )
        if session_initial_budget["returncode"] != 0:
            raise ControllerError("initial rbudgetcheck failed; qsub is forbidden")
        if self.initial_budget is None:
            self.initial_budget = session_initial_budget
            self._persist_wave_state()
        results: dict[str, list[dict[str, Any]]] = {leg.key: [] for leg in LEGS}
        ordinals = dict(self.leg_attempt_counts)

        for leg in LEGS:
            if self.permanent_stop:
                break
            if self.leg_attempt_counts[leg.key] != 0:
                continue
            ordinals[leg.key] += 1
            result = self.run_attempt(leg, ordinals[leg.key])
            results[leg.key].append(result)

        initial_complete = all(
            any(
                request.get("leg") == leg.key and request.get("completed") is True
                for request in self.wave_state["requests"]
            )
            for leg in LEGS
        )
        point_gate = self._initial_point_gate() if initial_complete else {
            "valid": False,
            "stop_before_retry": True,
            "reason": "initial four requests did not all complete",
        }

        retry_queue = [leg for leg in LEGS if leg.key not in self.authoritative]
        retry_index = 0
        while (
            retry_queue
            and not self.permanent_stop
            and not point_gate["stop_before_retry"]
            and self.request_count < REQUEST_LIMIT
        ):
            leg = retry_queue[retry_index % len(retry_queue)]
            if self.cumulative_node_min + leg.requested_node_min > REQUESTED_NODE_MIN_LIMIT:
                break
            ordinals[leg.key] += 1
            result = self.run_attempt(leg, ordinals[leg.key])
            results[leg.key].append(result)
            if result["admissible"]:
                retry_queue = [item for item in retry_queue if item.key != leg.key]
                retry_index = 0
            else:
                retry_index += 1

        final_budget = _budget_capture(self.recorder, "rbudgetcheck-after-wave")
        all_authoritative = set(self.authoritative) == set(LEG_BY_KEY)
        transaction_complete = all_authoritative and final_budget["returncode"] == 0
        summary = {
            "schema": SCHEMA,
            "session_id": self.session_id,
            "session_started_time_ns": session_started_ns,
            "session_finished_time_ns": time.time_ns(),
            "session_initial_budget": session_initial_budget,
            "request_count": self.request_count,
            "cumulative_requested_node_min": self.cumulative_node_min,
            "request_limit": REQUEST_LIMIT,
            "requested_node_min_limit": REQUESTED_NODE_MIN_LIMIT,
            "initial_four_point_gate": point_gate,
            "initial_budget": self.initial_budget,
            "final_budget": final_budget,
            "wave_budget_delta": _budget_delta(self.initial_budget, final_budget),
            "authoritative_attempts": self.authoritative,
            "all_legs_have_authoritative_attempt": all_authoritative,
            "final_rbudgetcheck_rc_zero": final_budget["returncode"] == 0,
            "transaction_complete": transaction_complete,
            "permanent_stop": self.permanent_stop,
            "attempts_by_leg": {
                key: [
                    {
                        "attempt_id": value.get("attempt_id"),
                        "request_id": value.get("request_id"),
                        "admissible": value.get("admissible"),
                        "request_ordinal": value.get("request_ordinal"),
                    }
                    for value in self.wave_state["requests"]
                    if value.get("leg") == key
                ]
                for key in results
            },
            "verdict_note": (
                "This summary selects the first admissible attempt only. Safety conclusions must "
                "be reconstructed from the staged raw probe observations."
            ),
        }
        self._finalize_runtime(summary)
        evidence = self.repo_root / EVIDENCE_RELATIVE / self.session_id
        print(f"controller evidence staged and tracked: {evidence}")
        print(f"all legs authoritative: {all_authoritative}")
        return 0 if transaction_complete else 3


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "run",
        help="run the fixed four-leg transaction and bounded failed-leg retries",
    )
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    if arguments.command == "run":
        return Controller().run()
    raise AssertionError(arguments.command)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ControllerError as exc:
        print(f"probe controller stopped fail-closed: {exc}", file=sys.stderr)
        raise SystemExit(16) from exc
