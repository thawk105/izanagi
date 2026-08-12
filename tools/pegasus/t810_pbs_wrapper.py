"""Fail-closed PBS argv construction and node wrapper for T-810."""
from __future__ import annotations

import argparse
from dataclasses import dataclass, fields as dataclass_fields
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import sys
import time
from typing import Any, Callable, Mapping, Sequence

try:
    from tools.pegasus import t810_harness_schema as schema
    from tools.pegasus import t810_runner_policy as runner_policy
except ModuleNotFoundError:  # standalone node package under python3.10 -I
    import t810_harness_schema as schema  # type: ignore[no-redef]
    import t810_runner_policy as runner_policy  # type: ignore[no-redef]


class T810WrapperError(RuntimeError):
    """A fail-closed wrapper construction or preflight violation."""


_QSUB_FIELDS = frozenset({"status", "project", "queue", "walltime_by_run_kind"})
_WALLTIME = re.compile(r"[0-9]{2,}:[0-5][0-9]:[0-5][0-9]\Z")
_HARDWARE_FIELDS = frozenset({
    "cpu_model", "physical_cores", "hyperthreading", "memory",
    "numa_nodes", "cache", "frequency_policy",
})
LIMITATIONS = {
    "shared_mount_repository_reachability_not_eliminated": True,
    "execution_mediation_incomplete": False,
    "guard_snapshot_to_release_race_not_eliminated": False,
    "approval_receipt_trust_root_absent": False,
    "repository_absence_not_proven_from_node": True,
    "budget_ledger_trust_root_absent": False,
}


def _is_sha256(value: Any) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))


@dataclass(frozen=True)
class ProcessScan:
    competing_processes: tuple[Mapping[str, Any], ...]
    unreadable: tuple[Mapping[str, Any], ...]


@dataclass(frozen=True)
class WrapperRequest:
    group_manifest_sha256: str
    group_id: str
    slot_id: str
    logical_request_id: str
    pbs_request_id: str
    run_kind: str
    preregistration_sha256: str
    prereg_approval_id: str
    admission_policy_sha256: str
    launch_authorization: Mapping[str, Any] | None
    release_token_commitment: str
    release_marker_path: Path
    cancel_marker_path: Path
    node_receipt_path: Path
    request_path: Path
    assigned_hostname: str
    allocated_cpus: frozenset[int]
    expected_submission_argv: tuple[str, ...]
    observed_submission_argv: tuple[str, ...]
    work_root: Path
    output_root: Path
    control_root: Path
    pbs_workdir: Path
    binary_source_path: Path
    binary_copy_path: Path
    runner_policy_path: Path
    runner_policy_sha256: str
    dependency_manifest_path: Path
    expected_dependency_manifest_sha256: str
    expected_module_list_sha256: str
    expected_numa_nodes: int
    round_count: int
    interpreter_realpath: Path


@dataclass(frozen=True)
class WrapperProbes:
    actual_hostname: Callable[[], str]
    hardware: Callable[[], Mapping[str, Any]]
    interpreter: Callable[[], Mapping[str, str]]
    process_scan: Callable[[frozenset[int]], ProcessScan]
    load1_reader: Callable[[], float]
    sleep: Callable[[float], None]
    monotonic_ns: Callable[[], int]
    wall_clock: Callable[[], str]
    module_list_sha256: Callable[[], str]
    trace_symbols: Callable[[Path], Sequence[str]]
    isolation: Callable[[], Mapping[str, str]]
    effective_clock: Callable[[], int | float]


@dataclass(frozen=True)
class WrapperOutcome:
    state: str
    reason_codes: tuple[str, ...]
    events: tuple[Mapping[str, Any], ...]
    measurement_started: bool


MeasurementRun = Callable[..., Any]


def _canonical_external_path(
    path: str | Path, name: str, repo_root: Path | None,
) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        raise T810WrapperError(f"{name} must be absolute")
    resolved = candidate.resolve(strict=False)
    if repo_root is not None:
        repository = repo_root.resolve(strict=True)
        if resolved == repository or repository in resolved.parents:
            raise T810WrapperError(f"{name} must be outside the repository")
    return resolved


def _qsub_policy(admission_policy: Mapping[str, Any], run_kind: str) -> tuple[str, str, str]:
    if not isinstance(admission_policy, Mapping):
        raise T810WrapperError("admission policy must be an object")
    qsub = admission_policy.get("qsub")
    if not isinstance(qsub, Mapping) or qsub.get("status") != "ratified":
        raise T810WrapperError("qsub admission fields are unratified")
    if set(qsub) != _QSUB_FIELDS:
        raise T810WrapperError("qsub admission policy has unknown or missing fields")
    project, queue = qsub["project"], qsub["queue"]
    walltimes = qsub["walltime_by_run_kind"]
    if (not isinstance(project, str) or not project or not isinstance(queue, str)
            or not queue or any(char.isspace() for char in project + queue)):
        raise T810WrapperError("qsub project or queue is invalid")
    if not isinstance(walltimes, Mapping) or set(walltimes) != set(schema.RUN_KINDS):
        raise T810WrapperError("qsub walltime map is not exact")
    walltime = walltimes.get(run_kind)
    if not isinstance(walltime, str) or _WALLTIME.fullmatch(walltime) is None:
        raise T810WrapperError("qsub walltime is invalid or run_kind is unknown")
    if walltime == "00:00:00":
        raise T810WrapperError("qsub walltime must be positive")
    return project, queue, walltime


def canonical_qsub_argv(
    slot: Mapping[str, Any], *, admission_policy: Mapping[str, Any],
    run_kind: str, submission_cwd: str | Path, repo_root: str | Path,
) -> tuple[str, ...]:
    """Build the sole canonical qsub spelling from ratified policy values."""
    repository = Path(repo_root)
    _canonical_external_path(submission_cwd, "qsub cwd", repository)
    project, queue, walltime = _qsub_policy(admission_policy, run_kind)
    required = ("job_name", "pbs_stdout_path", "pbs_stderr_path", "script_path")
    if not isinstance(slot, Mapping) or any(field not in slot for field in required):
        raise T810WrapperError("slot lacks canonical qsub fields")
    job_name = slot["job_name"]
    if not isinstance(job_name, str) or not job_name or any(char.isspace() for char in job_name):
        raise T810WrapperError("job_name is invalid")
    stdout = _canonical_external_path(slot["pbs_stdout_path"], "PBS stdout", repository)
    stderr = _canonical_external_path(slot["pbs_stderr_path"], "PBS stderr", repository)
    script = _canonical_external_path(slot["script_path"], "PBS script", repository)
    return (
        "qsub", "-A", project, "-q", queue, "-b", "1",
        "-l", f"elapstim_req={walltime}", "-N", job_name,
        "-o", str(stdout), "-e", str(stderr), str(script),
    )


def render_pbs_script(
    slot: Mapping[str, Any], *, interpreter_realpath: str | Path,
    repo_root: str | Path,
) -> bytes:
    """Render a repository-independent launcher with an exact Python 3.10 check."""
    repository = Path(repo_root)
    interpreter = _canonical_external_path(interpreter_realpath, "interpreter", repository)
    if interpreter.name != "python3.10":
        raise T810WrapperError("interpreter realpath must name python3.10")
    if not isinstance(slot, Mapping) or set(("wrapper_path", "request_path")) - set(slot):
        raise T810WrapperError("slot lacks wrapper script fields")
    wrapper = _canonical_external_path(slot["wrapper_path"], "wrapper", repository)
    request = _canonical_external_path(slot["request_path"], "wrapper request", repository)
    for value in (str(wrapper), str(request)):
        lowered = value.lower()
        if any(word in lowered for word in ("calibration", "certify", "floor", "oracle", "trace")):
            raise T810WrapperError("forbidden entrypoint in PBS script")
    lines = (
        "#!/bin/sh", "set -eu",
        f"expected_python={shlex.quote(str(interpreter))}",
        'actual_python="$(readlink -f "$(command -v python3.10)")"',
        '[ "$actual_python" = "$expected_python" ] || exit 70',
        "python3.10 -I -B -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 10) else 71)'",
        "exec python3.10 -I -B -c "
        + shlex.quote(
            "import runpy,sys; sys.path.insert(0,sys.argv[1]); "
            "sys.argv=[sys.argv[2],*sys.argv[3:]]; "
            "runpy.run_path(sys.argv[0],run_name='__main__')"
        )
        + f" {shlex.quote(str(wrapper.parent))} {shlex.quote(str(wrapper))}"
        + f" --request {shlex.quote(str(request))}",
    )
    rendered = ("\n".join(lines) + "\n").encode("utf-8")
    if str(repository.resolve(strict=True)).encode() in rendered:
        raise T810WrapperError("repository path leaked into PBS script")
    return rendered


def _require_token(token: Any) -> schema.AuthorizationToken:
    if not isinstance(token, schema.AuthorizationToken):
        raise T810WrapperError("verified AuthorizationToken is required")
    return token


def _request_path_from_slot(slot: Mapping[str, Any]) -> Path:
    argv = slot["wrapper_argv"]
    if (not isinstance(argv, list) or len(argv) != 4
            or argv[:2] != ["python3.10", slot["wrapper_path"]]
            or argv[2] != "--request"):
        raise T810WrapperError("slot wrapper argv does not bind one request path")
    path = Path(argv[3])
    if not path.is_absolute():
        raise T810WrapperError("wrapper request path must be absolute")
    return path


def build_wrapper_request(
    launch_intent: Mapping[str, Any], group_manifest: Mapping[str, Any],
    preregistration: Any, token: schema.AuthorizationToken, *, slot_id: str,
    pbs_request_id: str, assigned_hostname: str, allocated_cpus: Sequence[int],
    observed_submission_argv: Sequence[str], dependency_manifest_path: str | Path,
    interpreter_realpath: str | Path,
) -> WrapperRequest:
    """Build one request only from a bound intent/manifest and verified preregistration."""
    verified = _require_token(token)
    try:
        intent = schema.validate_launch_intent(launch_intent)
        manifest = schema.validate_group_manifest(group_manifest)
        from orchestrator.campaign.t810_preregistration import VerifiedT810Preregistration
    except (schema.T810SchemaError, ModuleNotFoundError) as exc:
        raise T810WrapperError("cannot validate wrapper request producer inputs") from exc
    if not isinstance(preregistration, VerifiedT810Preregistration):
        raise T810WrapperError("verified preregistration from loader is required")
    if (manifest["group_id"] != intent["group_id"]
            or manifest["launch_intent_sha256"] != schema.canonical_sha256(intent)
            or intent["preregistration_sha256"] != preregistration.sha256
            or intent["prereg_approval_id"] != preregistration.approval_id
            or verified.preregistration_sha256 != preregistration.sha256
            or verified.policy_sha256 != intent["policy_sha256"]
            or verified.run_kind != intent["run_kind"]
            or verified.document["approval_id"] != preregistration.approval_id):
        raise T810WrapperError("intent, manifest, preregistration, or token binding mismatch")
    matches = [slot for slot in intent["slots"] if slot["slot_id"] == slot_id]
    if len(matches) != 1:
        raise T810WrapperError("wrapper request slot is not unique in launch intent")
    slot = matches[0]
    policy = runner_policy.build_runner_policy(
        preregistration, executable_sha256=slot["binary_sha256"],
    )
    policy_sha256 = schema.canonical_sha256(policy)
    if policy_sha256 != slot["runner_policy_sha256"]:
        raise T810WrapperError("launch intent runner policy digest mismatch")
    cpus = tuple(allocated_cpus)
    observed = tuple(observed_submission_argv)
    if (not cpus or any(isinstance(cpu, bool) or not isinstance(cpu, int) or cpu < 0 for cpu in cpus)
            or len(cpus) != len(set(cpus))):
        raise T810WrapperError("allocated CPU set is invalid")
    if (not observed or any(not isinstance(item, str) or not item for item in observed)):
        raise T810WrapperError("observed submission argv is invalid")
    work_root, output_root = Path(intent["work_root"]), Path(intent["output_root"])
    benchmark_name = policy["benchmark_executable_name"]
    return WrapperRequest(
        group_manifest_sha256=schema.canonical_sha256(manifest),
        group_id=intent["group_id"], slot_id=slot["slot_id"],
        logical_request_id=slot["logical_request_id"], pbs_request_id=pbs_request_id,
        run_kind=intent["run_kind"], preregistration_sha256=preregistration.sha256,
        prereg_approval_id=preregistration.approval_id,
        admission_policy_sha256=intent["policy_sha256"],
        launch_authorization=dict(verified.document),
        release_token_commitment=manifest["release_token_commitment"],
        release_marker_path=work_root / "control/release.json",
        cancel_marker_path=work_root / "control/cancel.json",
        node_receipt_path=work_root / slot_id / "node-receipt.jsonl",
        request_path=_request_path_from_slot(slot), assigned_hostname=assigned_hostname,
        allocated_cpus=frozenset(cpus),
        expected_submission_argv=tuple(slot["qsub_argv"]),
        observed_submission_argv=observed, work_root=work_root,
        output_root=output_root, control_root=work_root / "control",
        pbs_workdir=work_root / slot_id,
        binary_source_path=Path(slot["binary_source_path"]),
        binary_copy_path=work_root / slot_id / benchmark_name,
        runner_policy_path=Path(slot["runner_policy_path"]),
        runner_policy_sha256=policy_sha256,
        dependency_manifest_path=Path(dependency_manifest_path),
        expected_dependency_manifest_sha256=slot["expected_dependency_manifest_sha256"],
        expected_module_list_sha256=slot["expected_module_list_sha256"],
        expected_numa_nodes=slot["expected_numa_nodes"],
        round_count=intent["round_count"], interpreter_realpath=Path(interpreter_realpath),
    )


def _write_bytes_create_only(
    token: schema.AuthorizationToken, path: Path, raw: bytes, *, mode: int = 0o600,
) -> None:
    _require_token(token)
    if not isinstance(raw, bytes):
        raise T810WrapperError("publication bytes must be exact bytes")
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags, mode)
        try:
            offset = 0
            while offset < len(raw):
                written = os.write(fd, raw[offset:])
                if written <= 0:
                    raise T810WrapperError("short create-only publication write")
                offset += written
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError as exc:
        raise T810WrapperError("create-only publication failed") from exc


def publish_wrapper_request(
    launch_intent: Mapping[str, Any], group_manifest: Mapping[str, Any],
    preregistration: Any, token: schema.AuthorizationToken, *, slot_id: str,
    pbs_request_id: str, assigned_hostname: str, allocated_cpus: Sequence[int],
    observed_submission_argv: Sequence[str], dependency_manifest_path: str | Path,
    interpreter_realpath: str | Path,
) -> WrapperRequest:
    """Publish the prereg-derived policy and request through token-gated effects."""
    verified = _require_token(token)
    request = build_wrapper_request(
        launch_intent, group_manifest, preregistration, verified, slot_id=slot_id,
        pbs_request_id=pbs_request_id, assigned_hostname=assigned_hostname,
        allocated_cpus=allocated_cpus, observed_submission_argv=observed_submission_argv,
        dependency_manifest_path=dependency_manifest_path,
        interpreter_realpath=interpreter_realpath,
    )
    policy = runner_policy.build_runner_policy(
        preregistration, executable_sha256=_sha256_file(request.binary_source_path),
    )
    if (schema.canonical_sha256(policy) != request.runner_policy_sha256
            or verified.preregistration_sha256 != request.preregistration_sha256):
        raise T810WrapperError("published wrapper request binding mismatch")
    _write_bytes_create_only(
        verified, request.runner_policy_path, schema.canonical_json_bytes(policy) + b"\n",
    )
    document: dict[str, Any] = {}
    for field in dataclass_fields(WrapperRequest):
        value = getattr(request, field.name)
        if isinstance(value, Path):
            value = str(value)
        elif isinstance(value, frozenset):
            value = sorted(value)
        elif isinstance(value, tuple):
            value = list(value)
        elif isinstance(value, Mapping):
            value = dict(value)
        document[field.name] = value
    _write_bytes_create_only(
        verified, request.request_path, schema.canonical_json_bytes(document) + b"\n",
    )
    return request


def _has_git_ancestor(path: Path) -> bool:
    resolved = path.resolve(strict=False)
    current = resolved if resolved.is_dir() else resolved.parent
    for ancestor in (current, *current.parents):
        marker = ancestor / ".git"
        if marker.exists() or marker.is_symlink():
            return True
    return False


def inspect_repository_absence(
    request: WrapperRequest, *, repo_root: Path | None = None,
) -> Mapping[str, bool]:
    """Return no affirmative repository-absence claims from a compute node."""
    del request, repo_root
    return {
        "package_repo_free": False,
        "roots_repo_external": False,
        "git_ancestor_absent": False,
        "pbs_workdir_repo_external": False,
    }


def _repository_hazard_observed(request: WrapperRequest) -> bool:
    paths = (
        request.pbs_workdir, request.work_root, request.output_root, request.control_root,
        request.binary_source_path, request.binary_copy_path, request.runner_policy_path,
    )
    return any(_has_git_ancestor(path) for path in paths)


def _parse_cpu_list(raw: str) -> list[int]:
    cpus: set[int] = set()
    for piece in raw.split(","):
        bounds = piece.strip().split("-", 1)
        if not bounds[0].isdigit() or (len(bounds) == 2 and not bounds[1].isdigit()):
            raise ValueError("invalid CPU list")
        start, end = int(bounds[0]), int(bounds[-1])
        if end < start:
            raise ValueError("descending CPU range")
        cpus.update(range(start, end + 1))
    return sorted(cpus)


def scan_competing_processes(
    allocated_cpus: frozenset[int], *, proc_root: Path = Path("/proc"),
    own_pid: int | None = None,
) -> ProcessScan:
    """Inspect every visible PID; any unreadable observation remains explicit."""
    if not allocated_cpus or any(isinstance(cpu, bool) or cpu < 0 for cpu in allocated_cpus):
        raise T810WrapperError("allocated CPU set is invalid")
    own_pid = os.getpid() if own_pid is None else own_pid
    pids = sorted(int(path.name) for path in proc_root.iterdir() if path.name.isdigit())
    parent_by_pid: dict[int, int] = {}
    unreadable: list[dict[str, Any]] = []
    for pid in pids:
        try:
            stat = (proc_root / str(pid) / "stat").read_text(encoding="utf-8")
            suffix = stat.rsplit(")", 1)[1].strip().split()
            parent_by_pid[pid] = int(suffix[1])
        except (OSError, UnicodeError, ValueError, IndexError):
            unreadable.append({"pid": pid, "fields": ["command"]})
    own_tree = {own_pid}
    changed = True
    while changed:
        before = len(own_tree)
        own_tree.update(pid for pid, parent in parent_by_pid.items() if parent in own_tree)
        changed = len(own_tree) != before
    competing: list[dict[str, Any]] = []
    for pid in pids:
        if pid in own_tree:
            continue
        missing: list[str] = []
        fields: dict[str, str] = {}
        uid: int | None = None
        affinity: list[int] | None = None
        command = "<unreadable>"
        try:
            status = (proc_root / str(pid) / "status").read_text(encoding="utf-8")
            fields = dict(line.split(":", 1) for line in status.splitlines() if ":" in line)
            uid = int(fields["Uid"].split()[0])
        except (OSError, UnicodeError, ValueError, KeyError, IndexError):
            missing.append("uid")
        try:
            affinity = _parse_cpu_list(fields["Cpus_allowed_list"].strip())
        except (ValueError, KeyError):
            missing.append("cpu_affinity")
        try:
            raw_command = (proc_root / str(pid) / "cmdline").read_bytes()
            command = raw_command.replace(b"\0", b" ").decode("utf-8").strip()
            if not command:
                command = (proc_root / str(pid) / "comm").read_text(encoding="utf-8").strip()
            if not command:
                raise ValueError("empty command")
        except (OSError, UnicodeError, ValueError):
            missing.append("command")
        if missing:
            unreadable.append({"pid": pid, "fields": sorted(set(missing))})
            continue
        if allocated_cpus.intersection(affinity or ()):
            competing.append({
                "pid": pid, "uid": uid, "cpu_affinity": affinity, "command": command,
            })
    by_pid: dict[int, set[str]] = {}
    for item in unreadable:
        by_pid.setdefault(item["pid"], set()).update(item["fields"])
    return ProcessScan(
        tuple(competing),
        tuple({"pid": pid, "fields": sorted(fields)} for pid, fields in sorted(by_pid.items())),
    )


def wait_for_quiet(
    *, load1_reader: Callable[[], float], sleep: Callable[[float], None],
    monotonic_ns: Callable[[], int], wall_clock: Callable[[], str],
) -> tuple[tuple[Mapping[str, Any], ...], bool]:
    """Require three consecutive <=1.0 samples, 30 seconds apart, by 1200s."""
    started = monotonic_ns()
    deadline = started + schema.READY_TIMEOUT_SECONDS * 1_000_000_000
    consecutive = 0
    samples: list[Mapping[str, Any]] = []
    while True:
        now = monotonic_ns()
        if now > deadline:
            return tuple(samples), False
        load = load1_reader()
        if isinstance(load, bool) or not isinstance(load, (int, float)):
            raise T810WrapperError("load1 reader returned a non-number")
        samples.append({"observed_at": wall_clock(), "load_average_1m": float(load)})
        consecutive = consecutive + 1 if load <= 1.0 else 0
        if consecutive == 3:
            return tuple(samples), True
        now = monotonic_ns()
        if now >= deadline:
            return tuple(samples), False
        sleep(min(30.0, (deadline - now) / 1_000_000_000))


def _sha256_file(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise T810WrapperError(f"hash target is not a regular non-symlink file: {path}")
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        raise T810WrapperError(f"cannot hash file: {path}") from exc
    return digest.hexdigest()


def _copy_binary(
    token: schema.AuthorizationToken, source: Path, destination: Path,
) -> tuple[str, str]:
    _require_token(token)
    source_hash = _sha256_file(source)
    try:
        source_mode = source.stat().st_mode & 0o777
    except OSError as exc:
        raise T810WrapperError("cannot stat binary source") from exc
    if not source_mode & 0o111:
        raise T810WrapperError("binary source is not executable")
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with source.open("rb") as reader, destination.open("xb") as writer:
            shutil.copyfileobj(reader, writer)
        destination.chmod(source_mode)
    except OSError as exc:
        raise T810WrapperError("binary copy failed or destination already exists") from exc
    return source_hash, _sha256_file(destination)


def _read_json_file(path: Path) -> Mapping[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise T810WrapperError(f"control marker is not a regular file: {path}")
    try:
        value = schema.parse_json(path.read_bytes())
    except (OSError, schema.T810SchemaError) as exc:
        raise T810WrapperError(f"invalid control marker: {path}") from exc
    if not isinstance(value, Mapping):
        raise T810WrapperError("control marker is not an object")
    return value


def _await_release(
    request: WrapperRequest, probes: WrapperProbes,
) -> tuple[Mapping[str, Any] | None, str | None]:
    started = probes.monotonic_ns()
    deadline = started + schema.READY_TIMEOUT_SECONDS * 1_000_000_000
    while True:
        if request.release_marker_path.exists() or request.release_marker_path.is_symlink():
            return _read_json_file(request.release_marker_path), None
        if request.cancel_marker_path.exists() or request.cancel_marker_path.is_symlink():
            return None, "preflight_failed"
        now = probes.monotonic_ns()
        if now >= deadline:
            return None, "ready_timeout"
        probes.sleep(min(1.0, (deadline - now) / 1_000_000_000))


def _preflight_process_evidence(scan: ProcessScan) -> list[Mapping[str, Any]]:
    result = list(scan.competing_processes)
    result.extend({
        "pid": item["pid"], "uid": None, "cpu_affinity": None,
        "command": "<unreadable:" + ",".join(item["fields"]) + ">",
    } for item in scan.unreadable)
    return sorted(result, key=lambda item: item["pid"])


def _append_jsonl(
    token: schema.AuthorizationToken, path: Path, raw: bytes,
) -> None:
    _require_token(token)
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags, 0o600)
        try:
            offset = 0
            while offset < len(raw):
                written = os.write(fd, raw[offset:])
                if written <= 0:
                    raise T810WrapperError("short JSONL write")
                offset += written
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError as exc:
        raise T810WrapperError("JSONL append failed") from exc


def _append_event(
    token: schema.AuthorizationToken, request: WrapperRequest,
    events: list[Mapping[str, Any]], event: str, payload: Mapping[str, Any],
    observed_at: str,
) -> Mapping[str, Any]:
    document = schema.validate_node_event({
        "schema_version": schema.NODE_EVENT_SCHEMA,
        "group_manifest_sha256": request.group_manifest_sha256,
        "group_id": request.group_id, "slot_id": request.slot_id,
        "logical_request_id": request.logical_request_id,
        "pbs_request_id": request.pbs_request_id, "sequence": len(events),
        "event": event, "observed_at": observed_at,
        "previous_event_sha256": None if not events else schema.canonical_sha256(events[-1]),
        "limitations": dict(LIMITATIONS), "payload": dict(payload),
    })
    raw = schema.canonical_json_bytes(document) + b"\n"
    _append_jsonl(token, request.node_receipt_path, raw)
    _append_jsonl(
        token, request.output_root / request.slot_id / "node-receipt.jsonl", raw,
    )
    events.append(document)
    return document


def _terminal(token: schema.AuthorizationToken, request: WrapperRequest, probes: WrapperProbes,
              events: list[Mapping[str, Any]], state: str, reasons: Sequence[str],
              *, measurement_started: bool, completed_rounds: int) -> WrapperOutcome:
    _append_event(token, request, events, "terminal", {
        "state": state, "reason_codes": list(reasons),
        "measurement_started": measurement_started, "completed_rounds": completed_rounds,
    }, probes.wall_clock())
    return WrapperOutcome(state, tuple(reasons), tuple(events), measurement_started)


def _runner_document(request: WrapperRequest) -> Mapping[str, Any]:
    if request.runner_policy_path.is_symlink() or not request.runner_policy_path.is_file():
        raise T810WrapperError("runner policy is not a regular non-symlink file")
    try:
        raw = request.runner_policy_path.read_bytes()
        value = schema.parse_json(raw)
        document = runner_policy.validate_runner_policy(value)
    except (OSError, schema.T810SchemaError, runner_policy.T810RunnerPolicyError) as exc:
        raise T810WrapperError("runner policy artifact is invalid") from exc
    canonical = schema.canonical_json_bytes(document)
    if (raw != canonical + b"\n"
            or schema.sha256_bytes(canonical) != request.runner_policy_sha256
            or document["preregistration_sha256"] != request.preregistration_sha256
            or document["prereg_approval_id"] != request.prereg_approval_id):
        raise T810WrapperError("runner policy artifact binding mismatch")
    return document


def _validate_request_artifact_chain(request: WrapperRequest) -> Mapping[str, Any]:
    """Rebind a serialized request to coordinator-published intent and manifest files."""
    try:
        intent = schema.validate_launch_intent(
            _read_json_file(request.control_root / "launch-intent.json"),
        )
        manifest = schema.validate_group_manifest(
            _read_json_file(request.output_root / "group-manifest.json"),
        )
    except schema.T810SchemaError as exc:
        raise T810WrapperError("request artifact chain is invalid") from exc
    slots = [slot for slot in intent["slots"] if slot["slot_id"] == request.slot_id]
    if len(slots) != 1:
        raise T810WrapperError("request slot is not unique in launch intent")
    slot = slots[0]
    expected = (
        (manifest["group_id"], request.group_id),
        (schema.canonical_sha256(manifest), request.group_manifest_sha256),
        (manifest["launch_intent_sha256"], schema.canonical_sha256(intent)),
        (manifest["release_token_commitment"], request.release_token_commitment),
        (intent["group_id"], request.group_id),
        (intent["run_kind"], request.run_kind),
        (intent["preregistration_sha256"], request.preregistration_sha256),
        (intent["prereg_approval_id"], request.prereg_approval_id),
        (intent["policy_sha256"], request.admission_policy_sha256),
        (intent["round_count"], request.round_count),
        (Path(intent["work_root"]), request.work_root),
        (Path(intent["output_root"]), request.output_root),
        (slot["logical_request_id"], request.logical_request_id),
        (tuple(slot["qsub_argv"]), request.expected_submission_argv),
        (Path(slot["binary_source_path"]), request.binary_source_path),
        (Path(slot["runner_policy_path"]), request.runner_policy_path),
        (slot["runner_policy_sha256"], request.runner_policy_sha256),
        (slot["expected_dependency_manifest_sha256"],
         request.expected_dependency_manifest_sha256),
        (slot["expected_module_list_sha256"], request.expected_module_list_sha256),
        (slot["expected_numa_nodes"], request.expected_numa_nodes),
        (_request_path_from_slot(slot), request.request_path),
        (request.work_root / "control", request.control_root),
        (request.work_root / request.slot_id / "node-receipt.jsonl",
         request.node_receipt_path),
    )
    if any(bound != actual for bound, actual in expected):
        raise T810WrapperError("wrapper request differs from intent or manifest")
    return slot


def _parse_throughput(stdout: Any) -> float:
    text = stdout if isinstance(stdout, str) else ""
    try:
        direct = float(text.strip())
    except ValueError:
        metrics: dict[str, str] = {}
        for line in text.splitlines():
            label, separator, value = line.partition("\t")
            if separator:
                metrics[label.strip().removesuffix(":")] = value.strip()
        try:
            if "throughput[tps]" in metrics:
                direct = float(metrics["throughput[tps]"].split()[0])
            else:
                direct = (float(metrics["commit_counts_"].split()[0])
                          / float(metrics["actual_extime"].split()[0]))
        except (KeyError, ValueError, ZeroDivisionError, IndexError) as exc:
            raise T810WrapperError("benchmark stdout has no finite throughput") from exc
    if not math.isfinite(direct):
        raise T810WrapperError("benchmark stdout has no finite throughput")
    return direct


def _validate_hardware(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _HARDWARE_FIELDS:
        raise T810WrapperError("hardware probe does not have the exact seven fields")
    result = dict(value)
    if any(result[field] in (None, "") for field in result):
        raise T810WrapperError("hardware probe contains an empty value")
    return result


def _run_wrapper(
    request: WrapperRequest, *, probes: WrapperProbes,
    measurement_run: MeasurementRun,
) -> WrapperOutcome:
    """Internal fixture seam; production calls :func:`run_wrapper`."""
    if request.run_kind not in schema.RUN_KINDS:
        raise T810WrapperError("wrapper run_kind is invalid")
    if (isinstance(request.round_count, bool) or not isinstance(request.round_count, int)
            or request.round_count < 1):
        raise T810WrapperError("wrapper round_count must be a positive int")
    try:
        token = schema.verify_launch_authorization(
            request.launch_authorization, run_kind=request.run_kind,
            preregistration_sha256=request.preregistration_sha256,
            policy_sha256=request.admission_policy_sha256,
        )
    except schema.T810SchemaError as exc:
        raise T810WrapperError("wrapper launch authorization is invalid") from exc
    slot = _validate_request_artifact_chain(request)
    policy = _runner_document(request)
    expected_binary_sha256 = policy["executable_sha256"]
    benchmark_argv = tuple(policy["canonical_benchmark_argv"])
    if (expected_binary_sha256 != slot["binary_sha256"]
            or request.binary_copy_path
            != request.work_root / request.slot_id / policy["benchmark_executable_name"]):
        raise T810WrapperError("runner policy executable identity binding mismatch")
    events: list[Mapping[str, Any]] = []
    repo_absence = inspect_repository_absence(request)
    probe_failed = False
    try:
        hardware = _validate_hardware(probes.hardware())
    except (T810WrapperError, OSError, TypeError, ValueError):
        hardware = {"cpu_model": "<unreadable>", "physical_cores": 1,
                    "hyperthreading": False, "memory": "<unreadable>",
                    "numa_nodes": 1, "cache": ["<unreadable>"],
                    "frequency_policy": "<unreadable>"}
        probe_failed = True
    try:
        interpreter = dict(probes.interpreter())
    except (OSError, TypeError, ValueError):
        interpreter = {"executable": str(request.interpreter_realpath), "version": "<unreadable>"}
        probe_failed = True
    interpreter_ok = (
        set(interpreter) == {"executable", "version"}
        and interpreter["executable"] == str(request.interpreter_realpath)
        and interpreter["version"].startswith("3.10")
        and request.interpreter_realpath.resolve(strict=False) == request.interpreter_realpath
        and not request.interpreter_realpath.is_symlink()
        and request.interpreter_realpath.is_file()
        and bool(request.interpreter_realpath.stat().st_mode & 0o111)
    )
    try:
        actual_hostname = probes.actual_hostname()
        if not isinstance(actual_hostname, str) or not actual_hostname:
            raise ValueError("invalid hostname")
    except (OSError, TypeError, ValueError):
        actual_hostname = "<unreadable>"
        probe_failed = True
    try:
        first_scan = probes.process_scan(request.allocated_cpus)
        if not isinstance(first_scan, ProcessScan):
            raise TypeError("invalid process scan")
    except (OSError, T810WrapperError, TypeError, ValueError):
        first_scan = ProcessScan((), ({"pid": max(1, os.getpid()), "fields": ["uid"]},))
        probe_failed = True
    try:
        samples, quiet = wait_for_quiet(
            load1_reader=probes.load1_reader, sleep=probes.sleep,
            monotonic_ns=probes.monotonic_ns, wall_clock=probes.wall_clock,
        )
    except (OSError, T810WrapperError, TypeError, ValueError):
        samples = ({"observed_at": probes.wall_clock(), "load_average_1m": 2.0},)
        quiet = False
        probe_failed = True
    try:
        source_hash, copy_hash = _copy_binary(
            token, request.binary_source_path, request.binary_copy_path,
        )
    except T810WrapperError:
        source_hash = copy_hash = "0" * 64
    try:
        dependency_hash = _sha256_file(request.dependency_manifest_path)
    except T810WrapperError:
        dependency_hash = "0" * 64
        probe_failed = True
    try:
        module_hash = probes.module_list_sha256()
        if not _is_sha256(module_hash):
            raise ValueError("invalid module digest")
    except (OSError, TypeError, ValueError):
        module_hash = "0" * 64
        probe_failed = True
    try:
        raw_traces = probes.trace_symbols(request.binary_copy_path)
        if isinstance(raw_traces, (str, bytes)) or any(
            not isinstance(item, str) or not item for item in raw_traces
        ):
            raise ValueError("invalid trace symbol evidence")
        traces = sorted(set(raw_traces))
    except (OSError, TypeError, ValueError):
        traces = ["<unreadable>"]
        probe_failed = True
    try:
        isolation_before = dict(probes.isolation())
        if (set(isolation_before) != {"inventory_sha256", "competing_processes_sha256"}
                or not all(_is_sha256(value) for value in isolation_before.values())):
            raise ValueError("invalid isolation evidence")
    except (OSError, T810WrapperError, TypeError, ValueError):
        isolation_before = {"inventory_sha256": "0" * 64,
                            "competing_processes_sha256": "0" * 64}
        probe_failed = True
    reasons: list[str] = []
    if probe_failed:
        reasons.append("preflight_failed")
    if actual_hostname != request.assigned_hostname or not interpreter_ok:
        reasons.append("preflight_failed")
    if first_scan.competing_processes or first_scan.unreadable:
        reasons.append("preflight_failed")
    if not quiet:
        reasons.append("quiet_gate_failed")
    if source_hash != expected_binary_sha256 or copy_hash != expected_binary_sha256:
        reasons.append("binary_copy_hash_mismatch")
    if dependency_hash != request.expected_dependency_manifest_sha256 or module_hash != request.expected_module_list_sha256:
        reasons.append("pre_inventory_mismatch")
    if traces or hardware["numa_nodes"] != request.expected_numa_nodes:
        reasons.append("preflight_failed")
    if request.observed_submission_argv != request.expected_submission_argv:
        reasons.append("submission_argv_mismatch")
    if _repository_hazard_observed(request):
        reasons.append("preflight_failed")
    reasons = sorted(set(reasons))
    _append_event(token, request, events, "preflight", {
        "assigned_hostname": request.assigned_hostname,
        "actual_hostname": actual_hostname, "hardware": hardware,
        "interpreter": interpreter,
        "competing_processes": _preflight_process_evidence(first_scan),
        "quiet_samples": list(samples), "binary_source_sha256": source_hash,
        "binary_copy_sha256": copy_hash,
        "dependency_manifest_sha256": dependency_hash,
        "module_list_sha256": module_hash, "trace_symbols": traces,
        "isolation_before": isolation_before,
        "observed_submission_argv": list(request.observed_submission_argv),
        "repo_absence": dict(repo_absence), "passed": not reasons,
        "reason_codes": reasons,
    }, probes.wall_clock())
    if reasons:
        return _terminal(
            token, request, probes, events, "pre_release_invalid", reasons,
            measurement_started=False, completed_rounds=0,
        )

    try:
        release_raw, wait_reason = _await_release(request, probes)
        if wait_reason is not None:
            return _terminal(
                token, request, probes, events, "pre_release_invalid", (wait_reason,),
                measurement_started=False, completed_rounds=0,
            )
        assert release_raw is not None
        release = schema.validate_control_marker(
            release_raw,
            expected_release_token_commitment=request.release_token_commitment,
        )
    except (schema.T810SchemaError, T810WrapperError):
        return _terminal(
            token, request, probes, events, "post_release_pre_measurement_invalid",
            ("release_marker_mismatch",), measurement_started=False, completed_rounds=0,
        )
    if (release["kind"] != "release"
            or release["group_manifest_sha256"] != request.group_manifest_sha256
            or release["group_id"] != request.group_id):
        return _terminal(
            token, request, probes, events, "post_release_pre_measurement_invalid",
            ("release_marker_mismatch",), measurement_started=False, completed_rounds=0,
        )
    release_sha = schema.canonical_sha256(release)
    if request.cancel_marker_path.exists() or request.cancel_marker_path.is_symlink():
        return _terminal(
            token, request, probes, events, "post_release_pre_measurement_invalid",
            ("cancel_marker_observed",), measurement_started=False, completed_rounds=0,
        )

    second_scan = probes.process_scan(request.allocated_cpus)
    post_reasons: list[str] = []
    if second_scan.competing_processes:
        post_reasons.append("competing_process_detected")
    if second_scan.unreadable:
        post_reasons.append("process_observation_unreadable")
    if _sha256_file(request.dependency_manifest_path) != dependency_hash:
        post_reasons.append("dependency_manifest_mismatch")
    if probes.module_list_sha256() != module_hash:
        post_reasons.append("module_list_mismatch")
    if probes.trace_symbols(request.binary_copy_path):
        post_reasons.append("trace_symbols_present")
    if _validate_hardware(probes.hardware())["numa_nodes"] != hardware["numa_nodes"]:
        post_reasons.append("numa_nodes_mismatch")
    if post_reasons:
        return _terminal(
            token, request, probes, events, "post_release_pre_measurement_invalid",
            tuple(sorted(set(post_reasons))), measurement_started=False, completed_rounds=0,
        )
    _append_event(token, request, events, "start_ack", {
        "release_marker_sha256": release_sha, "cancel_marker_absent": True,
        "ack_nonce": hashlib.sha256(
            f"{request.group_id}:{request.slot_id}:{release_sha}".encode(),
        ).hexdigest(),
        "pre_measurement_process_scan": {
            "competing_processes": list(second_scan.competing_processes),
            "unreadable": list(second_scan.unreadable),
        },
    }, probes.wall_clock())
    if request.cancel_marker_path.exists() or request.cancel_marker_path.is_symlink():
        return _terminal(
            token, request, probes, events, "post_release_pre_measurement_invalid",
            ("cancel_marker_observed",), measurement_started=False, completed_rounds=0,
        )

    rounds: list[dict[str, Any]] = []
    benchmark_rc = 0
    for index in range(1, request.round_count + 1):
        started_at = probes.wall_clock()
        result = measurement_run(
            policy, request.binary_copy_path, benchmark_argv, token,
            cwd=request.pbs_workdir,
        )
        ended_at = probes.wall_clock()
        if not hasattr(result, "returncode") or not isinstance(result.returncode, int):
            raise T810WrapperError("measurement runner returned an invalid result")
        benchmark_rc = result.returncode if result.returncode != 0 else benchmark_rc
        try:
            throughput = _parse_throughput(result.stdout)
        except T810WrapperError:
            throughput = 0.0
            benchmark_rc = benchmark_rc or 1
        round_document = {
            "index": index, "started_at": started_at, "ended_at": ended_at,
            "effective_clock": probes.effective_clock(), "throughput": throughput,
            "exit_code": result.returncode,
        }
        rounds.append(round_document)
        _append_jsonl(
            token, request.output_root / request.slot_id / "measurements.jsonl",
            schema.canonical_json_bytes(round_document) + b"\n",
        )
        if result.returncode != 0:
            break
    after_hash = _sha256_file(request.binary_copy_path)
    isolation_after = dict(probes.isolation())
    _append_event(token, request, events, "measurement", {
        "rounds": rounds, "benchmark_rc": benchmark_rc,
        "binary_after_sha256": after_hash, "isolation_after": isolation_after,
    }, probes.wall_clock())
    final_reasons: list[str] = []
    if after_hash != expected_binary_sha256:
        final_reasons.append("binary_after_hash_mismatch")
    if isolation_after != isolation_before:
        final_reasons.append("post_inventory_mismatch")
    if benchmark_rc != 0 or len(rounds) != request.round_count:
        final_reasons.append("completed_rounds_missing")
    if final_reasons:
        return _terminal(
            token, request, probes, events, "incomplete_after_start",
            tuple(sorted(set(final_reasons))), measurement_started=True,
            completed_rounds=len(rounds),
        )
    return _terminal(
        token, request, probes, events, "valid", ("all_jobs_complete",),
        measurement_started=True, completed_rounds=len(rounds),
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _default_hardware() -> Mapping[str, Any]:
    cpuinfo = Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="strict")
    meminfo = Path("/proc/meminfo").read_text(encoding="utf-8", errors="strict")
    model = next((line.split(":", 1)[1].strip() for line in cpuinfo.splitlines()
                  if line.startswith("model name")), "unknown")
    cores = len({line.split(":", 1)[1].strip() for line in cpuinfo.splitlines()
                 if line.startswith("core id")}) or len(os.sched_getaffinity(0))
    siblings = sum(1 for line in cpuinfo.splitlines() if line.startswith("processor"))
    numa = len(list(Path("/sys/devices/system/node").glob("node[0-9]*"))) or 1
    caches = sorted({path.read_text().strip() for path in
                     Path("/sys/devices/system/cpu/cpu0/cache").glob("index*/size")})
    governors = sorted({path.read_text().strip() for path in
                        Path("/sys/devices/system/cpu").glob("cpu*/cpufreq/scaling_governor")})
    memory = next((line.split(":", 1)[1].strip() for line in meminfo.splitlines()
                   if line.startswith("MemTotal")), "unknown")
    return {"cpu_model": model, "physical_cores": cores,
            "hyperthreading": siblings > cores, "memory": memory,
            "numa_nodes": numa, "cache": caches or ["unknown"],
            "frequency_policy": ",".join(governors) or "unknown"}


def _default_isolation(request: WrapperRequest) -> Mapping[str, str]:
    inventory = []
    for path in (
        request.binary_copy_path, request.dependency_manifest_path,
        request.runner_policy_path,
    ):
        inventory.append({"path": str(path), "sha256": _sha256_file(path)})
    scan = scan_competing_processes(request.allocated_cpus)
    return {
        "inventory_sha256": schema.canonical_sha256(inventory),
        "competing_processes_sha256": schema.canonical_sha256({
            "competing_processes": list(scan.competing_processes),
            "unreadable": list(scan.unreadable),
        }),
    }


def _default_effective_clock() -> float:
    cpuinfo = Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="strict")
    values = [float(line.split(":", 1)[1].strip()) for line in cpuinfo.splitlines()
              if line.startswith("cpu MHz")]
    if not values:
        raise T810WrapperError("effective clock is not observable")
    return sum(values) / len(values)


def _default_probes(request: WrapperRequest) -> WrapperProbes:
    def module_hash() -> str:
        modules = sorted(filter(None, os.environ.get("LOADEDMODULES", "").split(":")))
        return schema.canonical_sha256(modules)

    def trace_symbols(path: Path) -> Sequence[str]:
        raw = path.read_bytes().lower()
        return [name for name in ("izanagi_trace", "trace_enabled", "enable_trace", "tracing")
                if name.encode() in raw]

    return WrapperProbes(
        actual_hostname=lambda: os.uname().nodename,
        hardware=_default_hardware,
        interpreter=lambda: {"executable": str(Path(sys.executable).resolve()),
                             "version": ".".join(map(str, sys.version_info[:3]))},
        process_scan=lambda cpus: scan_competing_processes(cpus),
        load1_reader=lambda: os.getloadavg()[0], sleep=time.sleep,
        monotonic_ns=time.monotonic_ns, wall_clock=_utc_now,
        module_list_sha256=module_hash, trace_symbols=trace_symbols,
        isolation=lambda: _default_isolation(request),
        effective_clock=_default_effective_clock,
    )


def run_wrapper(request: WrapperRequest) -> WrapperOutcome:
    """Run the production wrapper with fixed probes and measurement mediation."""
    return _run_wrapper(
        request, probes=_default_probes(request),
        measurement_run=runner_policy.run_allowed_measurement,
    )


def _request_from_json(value: Any) -> WrapperRequest:
    if not isinstance(value, Mapping):
        raise T810WrapperError("wrapper request is not an object")
    expected = {field.name for field in dataclass_fields(WrapperRequest)}
    if set(value) != expected:
        raise T810WrapperError("wrapper request has unknown or missing fields")
    document = dict(value)
    path_fields = {
        "release_marker_path", "cancel_marker_path", "node_receipt_path", "request_path",
        "work_root", "output_root", "control_root", "pbs_workdir",
        "binary_source_path", "binary_copy_path", "runner_policy_path",
        "dependency_manifest_path", "interpreter_realpath",
    }
    for field in path_fields:
        if not isinstance(document[field], str):
            raise T810WrapperError(f"wrapper request {field} is not a path string")
        document[field] = Path(document[field])
    for field in ("expected_submission_argv", "observed_submission_argv"):
        value_argv = document[field]
        if (not isinstance(value_argv, list) or not value_argv
                or any(not isinstance(item, str) or not item for item in value_argv)):
            raise T810WrapperError(f"wrapper request {field} is not an argv")
        document[field] = tuple(value_argv)
    cpus = document["allocated_cpus"]
    if (not isinstance(cpus, list) or not cpus
            or any(isinstance(cpu, bool) or not isinstance(cpu, int) or cpu < 0 for cpu in cpus)
            or len(cpus) != len(set(cpus))):
        raise T810WrapperError("wrapper request allocated_cpus is invalid")
    document["allocated_cpus"] = frozenset(cpus)
    witness = document["launch_authorization"]
    if witness is not None and not isinstance(witness, Mapping):
        raise T810WrapperError("wrapper request launch_authorization is not an object")
    return WrapperRequest(**document)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="run one authorized T-810 PBS slot")
    parser.add_argument("--request", required=True)
    args = parser.parse_args(argv)
    request_path = Path(args.request)
    if not request_path.is_absolute() or request_path.is_symlink() or not request_path.is_file():
        raise T810WrapperError("--request must be an absolute non-symlink regular file")
    try:
        value = schema.parse_json(request_path.read_bytes())
    except (OSError, schema.T810SchemaError) as exc:
        raise T810WrapperError("cannot parse wrapper request") from exc
    request = _request_from_json(value)
    if request.request_path.resolve(strict=True) != request_path.resolve(strict=True):
        raise T810WrapperError("wrapper request path binding mismatch")
    outcome = run_wrapper(request)
    sys.stdout.write(outcome.state + "\n")
    return 0 if outcome.state == "valid" else 2


if __name__ == "__main__":
    raise SystemExit(main())
