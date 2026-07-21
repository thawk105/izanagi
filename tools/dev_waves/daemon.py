"""Foreground, fake-only bounded dev-wave supervisor.

The daemon owns orchestration only.  Durable state is delegated to
``ControlLedger``; process and Git effects are delegated to the worker and the
allowlisted Git layer.  In particular this module contains no land, push,
retry, rebase, cleanup, or branch deletion operation.
"""
from __future__ import annotations

import dataclasses
import fcntl
import hashlib
import json
import os
import select
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

from .checker import (
    CheckSpec,
    VerificationInput,
    VerificationReport,
    extract_latest_next_action_ids,
    verify_wave,
)
from .git_state import (
    RepoSnapshot,
    WaveWorktree,
    branch_tip,
    create_exact_worktree,
    resolve_main_worktree,
    resolve_repo_identity,
    snapshot_repo,
    update_submodules_no_fetch,
)
from .ledger import (
    BoottimeDeadline,
    ControlLedger,
    Observation,
    RepositoryLease,
    RuntimeLayout,
    SideEffectIntent,
    SignalRelay,
    discover_runs,
    replay_run,
)
from .protocol import bind_repo_socket, receive_request, send_frame
from .receipt import (
    ReceiptBinding,
    load_receipt_schema,
    parse_claude_result,
    persist_sanitized_receipt,
    receipt_schema_digest,
    validate_child_receipt,
)
from .redaction import assert_sanitized, redact_argv, redact_value, safe_digest
from .schema import (
    DEFAULT_MAX_JSON_BYTES,
    PROTOCOL_VERSION,
    SCHEMA_VERSION,
    CancelRequest,
    CancelResponse,
    DevWavesError,
    Outcome,
    ReasonCode,
    ResourceLimits,
    Response,
    RunManifest,
    RunState,
    StatusRequest,
    StatusResponse,
    SubmitRequest,
    SubmitResponse,
    WaveManifest,
    WorkerSpec,
    canonical_bytes,
    canonical_decimal,
    encode_response,
    parse_request,
    parse_run_manifest,
    parse_wave_manifest,
    parse_worker_spec,
    strict_loads,
    validate_limits,
)
from .worker import (
    PidIdentity, build_child_argv, kill_spawned_process, pid_identity_digest, pid_identity_record,
    read_pid_identity, spawn_worker, terminate_verified_group,
)


_RUNTIME_RELATIVE = Path("output/dev-wave-supervisor/runtime")
_AUDIT_NAME = "invalid-requests.jsonl"
_PROFILE_NAME = "server-profile.json"
_MODEL_SLUG_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def _boottime_ns() -> int:
    return time.clock_gettime_ns(time.CLOCK_BOOTTIME)


def _write_all(fd: int, raw: bytes) -> None:
    view = memoryview(raw)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise OSError("write made no progress")
        view = view[written:]


def _fsync_parent(path: Path) -> None:
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _create_json(path: Path, value: object) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        _write_all(fd, canonical_bytes(value) + b"\n")
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_parent(path)


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        _write_all(fd, canonical_bytes(value) + b"\n")
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(temporary, path)
    _fsync_parent(path)


def _sha256_file(path: os.PathLike[str] | str) -> str:
    digest = hashlib.sha256()
    fd = os.open(os.fspath(path), os.O_RDONLY)
    try:
        while True:
            chunk = os.read(fd, 64 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    finally:
        os.close(fd)
    return digest.hexdigest()


def _supervisor_digest() -> str:
    digest = hashlib.sha256()
    directory = Path(__file__).resolve().parent
    for path in sorted(directory.glob("*")):
        if path.is_file() and (path.suffix in {".py", ".json"}):
            digest.update(path.name.encode("utf-8") + b"\0")
            digest.update(path.read_bytes())
    return digest.hexdigest()


def _model_slug(value: str) -> bool:
    return (
        isinstance(value, str)
        and "-" in value
        and value == value.lower()
        and value[0] != "-"
        and value[-1] != "-"
        and all(character in _MODEL_SLUG_CHARS for character in value)
    )


@dataclass(frozen=True)
class SupervisorProfile:
    """Trusted server-side values; clients select only ``name``."""

    name: str
    model: str
    effort: str
    check_specs: tuple[CheckSpec, ...]
    settings_path: Optional[str] = None
    required_hooks: tuple[tuple[str, str], ...] = ()
    max_waves: Optional[int] = None
    max_per_wave_timeout_s: Optional[int] = None
    max_total_timeout_s: Optional[int] = None
    max_per_wave_budget_usd: Optional[Decimal] = None
    max_total_budget_usd: Optional[Decimal] = None
    max_wave_output_bytes: Optional[int] = None
    max_run_bytes: Optional[int] = None
    allowed_models: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.name != "default":
            raise ValueError("T-076 exposes only the default profile")
        if not _model_slug(self.model):
            raise ValueError("model must be a complete literal slug")
        if (not self.allowed_models or self.model not in self.allowed_models or
                any(not _model_slug(item) for item in self.allowed_models) or
                len(set(self.allowed_models)) != len(self.allowed_models)):
            raise ValueError("model must literally match the explicit allowlist")
        if not self.effort or not self.effort.isascii():
            raise ValueError("effort must be an explicit ASCII name")
        if not self.check_specs:
            raise ValueError("profile must declare fixed checks")
        if sum(
            (any(Path(token).name == "check_docs.py" for token in spec.argv) or
             any(Path(token).name == "task_run_check.py" for token in spec.argv)
             and "docs-check" in spec.argv)
            for spec in self.check_specs
        ) != 1:
            raise ValueError("profile must declare check_docs exactly once")
        for matcher, command in self.required_hooks:
            if not matcher or not command or "\x00" in matcher + command:
                raise ValueError("invalid required hook")
        cap_values = (
            self.max_waves, self.max_per_wave_timeout_s, self.max_total_timeout_s,
            self.max_per_wave_budget_usd, self.max_total_budget_usd,
            self.max_wave_output_bytes, self.max_run_bytes,
        )
        if any(value is None or value <= 0 for value in cap_values):
            raise ValueError("profile must declare every positive absolute cap")
        assert self.max_run_bytes is not None and self.max_wave_output_bytes is not None
        if self.max_run_bytes < self.max_wave_output_bytes + 64 * 1024:
            raise ValueError("profile run cap must include the control reserve")


@dataclass(frozen=True)
class SupervisorConfig:
    repo_root: str
    fake_child_executable: str
    fake_child_sha256: str
    profile: SupervisorProfile
    check_timeout_s: int
    termination_grace_s: float
    runtime_dir: Optional[str] = None
    socket_read_deadline_s: float = 5.0
    audit_max_bytes: int = 1024 * 1024
    max_request_bytes: int = DEFAULT_MAX_JSON_BYTES

    def __post_init__(self) -> None:
        root = os.path.abspath(self.repo_root)
        executable = os.path.abspath(self.fake_child_executable)
        runtime = os.path.abspath(self.runtime_dir or os.path.join(root, _RUNTIME_RELATIVE))
        object.__setattr__(self, "repo_root", root)
        object.__setattr__(self, "fake_child_executable", executable)
        object.__setattr__(self, "runtime_dir", runtime)
        if not os.path.isabs(executable) or not os.path.isabs(runtime):
            raise ValueError("paths must be absolute")
        if len(self.fake_child_sha256) != 64 or any(
            character not in "0123456789abcdef" for character in self.fake_child_sha256
        ):
            raise ValueError("fake child digest must be lowercase SHA-256")
        if self.check_timeout_s < 1 or self.termination_grace_s < 0:
            raise ValueError("invalid process timing")
        if self.socket_read_deadline_s <= 0 or self.audit_max_bytes < 1:
            raise ValueError("invalid daemon bound")


CrashHook = Callable[[str, Optional[str], Optional[int]], None]
SideEffectHook = Callable[[str], None]


@dataclass(frozen=True)
class SupervisorDependencies:
    crash_hook: Optional[CrashHook] = None
    spawn_worker_fn: Callable[..., subprocess.Popen[bytes]] = spawn_worker
    verify_wave_fn: Callable[[VerificationInput], VerificationReport] = verify_wave
    ledger_fsync: Optional[Callable[[int], None]] = None
    side_effect_hook: Optional[SideEffectHook] = None


@dataclass(frozen=True)
class DoctorReport:
    ok: bool
    checks: tuple[tuple[str, bool, str], ...]


@dataclass
class _ActiveRun:
    run_id: str
    thread: threading.Thread
    cancel: threading.Event = field(default_factory=threading.Event)
    worker: Optional[subprocess.Popen[bytes]] = None
    worker_identity: Optional[PidIdentity] = None
    ledger: Optional[ControlLedger] = None
    cancel_source: Optional[str] = None
    cancel_reason: ReasonCode = ReasonCode.SIGNAL_RECEIVED
    signal_observed: bool = False


def _probe_command(executable: str, option: str, timeout_s: float) -> subprocess.CompletedProcess[bytes]:
    if option not in {"--version", "--help"}:
        raise ValueError("doctor may probe only --version and --help")
    return subprocess.run(
        [executable, option], shell=False, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout_s,
        check=False,
    )


def probe_claude_capabilities(executable: str, timeout_s: float) -> tuple[str, str]:
    """Probe an explicit executable with ``--version`` and ``--help`` only."""
    path = os.path.abspath(executable)
    if path != executable:
        raise DevWavesError(ReasonCode.CLAUDE_UNAVAILABLE, {
            "label": "doctor", "kind": "executable-not-absolute",
        })
    try:
        version = _probe_command(path, "--version", timeout_s)
        help_result = _probe_command(path, "--help", timeout_s)
    except (OSError, subprocess.TimeoutExpired):
        raise DevWavesError(ReasonCode.CLAUDE_UNAVAILABLE, {
            "label": "doctor", "kind": "probe-failed",
        }) from None
    if version.returncode != 0 or help_result.returncode != 0:
        raise DevWavesError(ReasonCode.CLAUDE_UNAVAILABLE, {
            "label": "doctor", "kind": "probe-nonzero",
        })
    try:
        version_text = version.stdout.decode("utf-8", errors="strict").strip()
        help_text = help_result.stdout.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise DevWavesError(ReasonCode.FLAG_UNAVAILABLE, {
            "label": "doctor", "kind": "non-utf8",
        }) from None
    required = (
        "--model", "--effort", "--permission-mode", "auto", "--output-format",
        "json", "--json-schema", "--max-budget-usd", "--add-dir",
    )
    if not version_text or any(token not in help_text for token in required):
        raise DevWavesError(ReasonCode.FLAG_UNAVAILABLE, {
            "label": "doctor", "kind": "required-capability",
        })
    return version_text, help_text


def _probe_filesystem(parent: Path) -> None:
    parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".dev-waves-doctor-", dir=parent) as raw:
        root = Path(raw)
        os.chmod(root, 0o700)
        layout = RuntimeLayout.create(root)
        with RepositoryLease.acquire(layout):
            probe = subprocess.run(
                [
                    sys.executable, "-c",
                    "import fcntl,os,sys\n"
                    "fd=os.open(sys.argv[1],os.O_RDWR)\n"
                    "try:\n fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)\n"
                    "except BlockingIOError:\n raise SystemExit(0)\n"
                    "raise SystemExit(3)\n",
                    str(layout.control_lock),
                ],
                shell=False, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, timeout=5, check=False,
            )
            if probe.returncode != 0:
                raise DevWavesError(ReasonCode.RUNTIME_IO_FAILURE, {
                    "label": "doctor", "kind": "flock-not-exclusive",
                })
            with bind_repo_socket(root, os.getuid()):
                pass
        canary = root / "fsync-canary"
        fd = os.open(canary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            _write_all(fd, b"dev-waves-fsync\n")
            os.fsync(fd)
        finally:
            os.close(fd)
        _fsync_parent(canary)


def doctor(
    *, repo_root: str, executable: Optional[str] = None,
    probe_cli: bool = False, probe_timeout_s: float = 5.0,
    probe_fs: bool = False,
) -> DoctorReport:
    checks: list[tuple[str, bool, str]] = []
    if probe_cli:
        if executable is None:
            return DoctorReport(False, (("cli", False, "missing-executable"),))
        try:
            version, _help = probe_claude_capabilities(executable, probe_timeout_s)
        except DevWavesError as exc:
            checks.append(("cli", False, exc.code.value))
        else:
            checks.append(("cli", True, version))
    if probe_fs:
        try:
            _probe_filesystem(Path(repo_root) / _RUNTIME_RELATIVE.parent)
        except (DevWavesError, OSError) as exc:
            detail = exc.code.value if isinstance(exc, DevWavesError) else "runtime-io-failure"
            checks.append(("fs", False, detail))
        else:
            checks.append(("fs", True, "bind-flock-fsync"))
    return DoctorReport(all(item[1] for item in checks), tuple(checks))


def _limits_wire(limits: ResourceLimits) -> dict[str, object]:
    return {
        "per_wave_timeout_s": limits.per_wave_timeout_s,
        "total_timeout_s": limits.total_timeout_s,
        "per_wave_budget_usd": None if limits.per_wave_budget_usd is None else canonical_decimal(limits.per_wave_budget_usd),
        "total_budget_usd": None if limits.total_budget_usd is None else canonical_decimal(limits.total_budget_usd),
        "max_wave_output_bytes": limits.max_wave_output_bytes,
        "max_run_bytes": limits.max_run_bytes,
    }


def _manifest_wire(manifest: RunManifest) -> dict[str, object]:
    value = asdict(manifest)
    value["limits"] = _limits_wire(manifest.limits)
    return value


def _snapshot_wire(snapshot: RepoSnapshot) -> dict[str, object]:
    return asdict(snapshot)


def _snapshot_from_wire(value: Mapping[str, object]) -> RepoSnapshot:
    return RepoSnapshot(
        str(value["head_sha"]), value["branch"] if isinstance(value["branch"], str) else None,
        bool(value["main_dirty"]), bool(value["submodule_dirty"]),
        tuple(str(item) for item in value["status_entries"]),
        tuple(str(item) for item in value["submodule_entries"]),
        tuple((str(item[0]), str(item[1])) for item in value["remote_refs"]),
        str(value["remote_config_sha256"]),
    )


class Supervisor:
    """One repository-local foreground supervisor with at most one active run."""

    def __init__(
        self, config: SupervisorConfig,
        dependencies: Optional[SupervisorDependencies] = None,
    ) -> None:
        self.config = config
        self.dependencies = dependencies or SupervisorDependencies()
        self.repo_identity = resolve_repo_identity(config.repo_root)
        self.main_worktree = resolve_main_worktree(config.repo_root)
        self.repo_root = self.main_worktree.path
        self._settings_sha256 = (
            _sha256_file(config.profile.settings_path)
            if config.profile.settings_path is not None else "-"
        )
        configured_runtime = Path(config.runtime_dir or "")
        default_from_argument = Path(config.repo_root) / _RUNTIME_RELATIVE
        runtime_path = (
            Path(self.repo_root) / _RUNTIME_RELATIVE
            if configured_runtime == default_from_argument else configured_runtime
        )
        runtime_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.layout = RuntimeLayout.create(runtime_path)
        self._lock = threading.RLock()
        self._active: Optional[_ActiveRun] = None
        self._request_index: dict[str, tuple[str, str]] = {}
        self._cancel_index: dict[str, str] = {}
        self._shutdown = threading.Event()
        self._recovery_runs: set[str] = set()
        self._load_request_index()

    def _crash(self, phase: str, run_id: Optional[str], wave_index: Optional[int]) -> None:
        if self.dependencies.crash_hook is not None:
            self.dependencies.crash_hook(phase, run_id, wave_index)

    def _load_request_index(self) -> None:
        for discovered in discover_runs(self.layout):
            if (not discovered.valid or discovered.snapshot is None or
                    discovered.snapshot.state not in {
                        RunState.COMPLETED, RunState.BLOCKED, RunState.FAILED,
                        RunState.INTERRUPTED,
                    }):
                self._recovery_runs.add(discovered.run_id)
            if not discovered.valid:
                continue
            try:
                raw = (discovered.path / "events.jsonl").read_bytes()
                manifest_raw = (discovered.path / "manifest.json").read_bytes()
                manifest = parse_run_manifest(manifest_raw.rstrip(b"\n"))
                for line in raw.splitlines():
                    event = strict_loads(line, label="request-index", max_bytes=64 * 1024)
                    if isinstance(event, dict) and event.get("event") == "client_request_recorded":
                        data = event.get("data")
                        if isinstance(data, dict) and isinstance(data.get("sha256"), str):
                            self._request_index[data["sha256"]] = (
                                str(data.get("request_digest", manifest.request_digest)), discovered.run_id,
                            )
            except (OSError, DevWavesError):
                continue

    def _refresh_recovery_runs(self) -> None:
        recovery = set()
        for discovered in discover_runs(self.layout):
            if (not discovered.valid or discovered.reason is not None or
                    discovered.snapshot is None or discovered.snapshot.state not in {
                        RunState.COMPLETED, RunState.BLOCKED, RunState.FAILED,
                        RunState.INTERRUPTED,
                    }):
                recovery.add(discovered.run_id)
        self._recovery_runs = recovery

    def _audit_invalid(self, raw: bytes, error: DevWavesError) -> None:
        record = {
            "schema_version": SCHEMA_VERSION,
            "created_utc": _utc_now(),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "reason": error.code.value,
            "detail": error.detail,
        }
        clean = redact_value(record)
        assert_sanitized(clean)
        line = canonical_bytes(clean) + b"\n"
        path = self.layout.root / _AUDIT_NAME
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            if os.fstat(fd).st_size + len(line) > self.config.audit_max_bytes:
                raise DevWavesError(ReasonCode.RUNTIME_IO_FAILURE, {
                    "label": "invalid-request-audit", "kind": "capacity",
                })
            _write_all(fd, line)
            os.fsync(fd)
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)
        _fsync_parent(path)

    def _response(
        self, action: str, ok: bool, *, run_id: Optional[str] = None,
        state: Optional[RunState] = None, wave_index: Optional[int] = None,
        elapsed_s: Optional[Decimal] = None, reason: Optional[ReasonCode] = None,
        detail: object = None,
    ) -> Response:
        return Response(
            PROTOCOL_VERSION, action, ok, run_id, state, wave_index,
            elapsed_s, reason, {} if detail is None else detail,
        )

    def dispatch(self, raw: bytes) -> bytes:
        try:
            request = parse_request(raw)
        except DevWavesError as exc:
            self._audit_invalid(raw, exc)
            return encode_response(self._response(
                "error", False, reason=exc.code, detail=exc.detail,
            ))
        try:
            if request.repo_identity != self.repo_identity.digest:
                raise DevWavesError(ReasonCode.INVALID_ARGS, {
                    "label": "repo_identity", "kind": "mismatch",
                })
            if isinstance(request, SubmitRequest):
                result = self.submit(request)
                response = self._response(
                    "submit", result.reason is None, run_id=result.run_id,
                    state=result.state, reason=result.reason,
                )
            elif isinstance(request, StatusRequest):
                result = self.status(request.run_id)
                response = self._response(
                    "status", result.ok, run_id=result.run_id, state=result.state,
                    wave_index=result.wave_index, elapsed_s=result.elapsed_s,
                    reason=result.reason,
                )
            else:
                result = self.cancel(request.run_id, request.client_request_id)
                response = self._response(
                    "cancel", result.ok, run_id=result.run_id,
                    state=result.state, reason=result.reason,
                )
        except DevWavesError as exc:
            response = self._response("error", False, reason=exc.code, detail=exc.detail)
        return encode_response(response)

    def _request_digest(self, request: SubmitRequest) -> str:
        return hashlib.sha256(canonical_bytes(request)).hexdigest()

    def _request_key(self, request_id: str) -> str:
        return hashlib.sha256(request_id.encode("ascii")).hexdigest()

    def _open_ledger(self, run_id: str) -> ControlLedger:
        manifest = parse_run_manifest(
            (self.layout.run_dir(run_id) / "manifest.json").read_bytes().rstrip(b"\n")
        )
        cap = manifest.limits.max_run_bytes or 16 * 1024 * 1024
        return ControlLedger.open(
            self.layout, run_id, max_total_bytes=min(cap, 64 * 1024),
            fsync=self.dependencies.ledger_fsync,
        )

    def _run_artifact_bytes(self, run_id: str) -> int:
        """Measure WAL plus all run artifacts; Git worktrees are excluded.

        Worktrees live under the runtime's sibling ``worktrees/`` namespace and
        are intentionally outside ``max_run_bytes`` because Git object and
        checkout growth is bounded by the repository rather than artifact I/O.
        Symlinks and non-regular objects inside a run fail closed.
        """
        total = 0
        root = self.layout.run_dir(run_id)
        for directory, names, files in os.walk(root, followlinks=False):
            names[:] = [name for name in names if name != "worktrees"]
            for name in files:
                path = Path(directory) / name
                info = path.lstat()
                if not stat.S_ISREG(info.st_mode):
                    raise DevWavesError(ReasonCode.RUNTIME_IO_FAILURE, {
                        "label": "max_run_bytes", "kind": "non-regular-artifact",
                    })
                total += info.st_size
        return total

    def _enforce_run_capacity(
        self, run_id: str, cap: int, *, reserve: int = 0,
    ) -> None:
        if self._run_artifact_bytes(run_id) + reserve > cap:
            raise DevWavesError(ReasonCode.BUDGET_INVALID, {
                "label": "max_run_bytes", "kind": "artifact-capacity",
            })

    def _validate_submit_policy(self, request: SubmitRequest) -> ResourceLimits:
        """Validate all client/profile caps before UUID or staging creation."""
        if request.profile != self.config.profile.name:
            raise DevWavesError(ReasonCode.INVALID_ARGS, {
                "label": "profile", "kind": "unknown",
            })
        limits = validate_limits(request)
        caps = self.config.profile
        comparisons = (
            (request.max_waves, caps.max_waves),
            (limits.per_wave_timeout_s, caps.max_per_wave_timeout_s),
            (limits.total_timeout_s, caps.max_total_timeout_s),
            (limits.per_wave_budget_usd, caps.max_per_wave_budget_usd),
            (limits.total_budget_usd, caps.max_total_budget_usd),
            (limits.max_wave_output_bytes, caps.max_wave_output_bytes),
            (limits.max_run_bytes, caps.max_run_bytes),
        )
        if any(cap is None for _value, cap in comparisons):
            raise DevWavesError(ReasonCode.BUDGET_INVALID, {
                "label": "server-caps", "kind": "missing",
            })
        if any(value is not None and value > cap for value, cap in comparisons):
            raise DevWavesError(ReasonCode.BUDGET_INVALID, {
                "label": "limits", "kind": "server-cap",
            })
        assert limits.max_run_bytes is not None
        assert limits.max_wave_output_bytes is not None
        if limits.max_run_bytes < limits.max_wave_output_bytes + 64 * 1024:
            raise DevWavesError(ReasonCode.BUDGET_INVALID, {
                "label": "max_run_bytes", "kind": "below-control-reserve",
            })
        return limits

    def submit(self, request: SubmitRequest) -> SubmitResponse:
        if not isinstance(request, SubmitRequest):
            raise TypeError("request must be SubmitRequest")
        digest = self._request_digest(request)
        request_key = self._request_key(request.client_request_id)
        with self._lock:
            known = self._request_index.get(request_key)
            if known is not None:
                old_digest, run_id = known
                if old_digest != digest:
                    raise DevWavesError(ReasonCode.REQUEST_CONFLICT, {
                        "label": "client_request_id", "kind": "digest-mismatch",
                    })
                current = self.status(run_id)
                return SubmitResponse(PROTOCOL_VERSION, True, run_id, current.state, current.reason)
            if self._active is not None and self._active.thread.is_alive():
                raise DevWavesError(ReasonCode.DAEMON_BUSY, {
                    "label": "submit", "kind": "active-run",
                })
            self._refresh_recovery_runs()
            if self._recovery_runs:
                raise DevWavesError(ReasonCode.AMBIGUOUS_RECOVERY, {
                    "label": "submit", "kind": "recovery-required",
                })
            try:
                limits = self._validate_submit_policy(request)
            except DevWavesError as exc:
                self._audit_invalid(canonical_bytes(request), exc)
                raise
            assert limits.total_timeout_s is not None
            deadline = BoottimeDeadline.start(limits.total_timeout_s)
            run_id = "dw-" + uuid.uuid4().hex
            manifest = RunManifest(
                SCHEMA_VERSION, run_id, self.repo_identity.digest, request.profile,
                request.max_waves, request.limits, _utc_now(),
                self.config.fake_child_sha256, _supervisor_digest(), digest,
            )
            ledger = ControlLedger.create(
                self.layout, run_id, _manifest_wire(manifest),
                max_total_bytes=min(limits.max_run_bytes, 64 * 1024),
            )
            try:
                ledger.append("client_request_recorded", data={
                    "sha256": request_key,
                    "request_digest": digest,
                })
                ledger.record_observation(Observation(
                    "run-deadline", "deadline", {
                        "boot_id": deadline.boot_id,
                        "started_ns": deadline.started_ns,
                        "deadline_ns": deadline.deadline_ns,
                    },
                ))
            finally:
                ledger.close()
            self._request_index[request_key] = (digest, run_id)
            thread = threading.Thread(
                target=self._run_entry, args=(run_id, request, deadline),
                name=f"dev-waves-{run_id}", daemon=False,
            )
            active = _ActiveRun(run_id, thread)
            self._active = active
            thread.start()
            return SubmitResponse(PROTOCOL_VERSION, True, run_id, RunState.CREATED, None)

    def _settings_preflight(self) -> None:
        profile = self.config.profile
        if profile.settings_path is None:
            if profile.required_hooks:
                raise DevWavesError(ReasonCode.SETTINGS_INVALID, {
                    "label": "settings", "kind": "missing",
                })
            return
        try:
            raw = Path(profile.settings_path).read_bytes()
            if hashlib.sha256(raw).hexdigest() != self._settings_sha256:
                raise DevWavesError(ReasonCode.SETTINGS_INVALID, {
                    "label": "settings", "kind": "digest-changed",
                })
            value = strict_loads(raw, label="settings", max_bytes=1024 * 1024)
        except (OSError, DevWavesError):
            raise DevWavesError(ReasonCode.SETTINGS_INVALID, {
                "label": "settings", "kind": "parse",
            }) from None
        if not isinstance(value, dict):
            raise DevWavesError(ReasonCode.SETTINGS_INVALID, {
                "label": "settings", "kind": "object",
            })
        hooks = value.get("hooks")
        if not isinstance(hooks, dict):
            if profile.required_hooks:
                raise DevWavesError(ReasonCode.SETTINGS_INVALID, {
                    "label": "settings", "kind": "hooks-missing",
                })
            return
        observed: set[tuple[str, str]] = set()
        for groups in hooks.values():
            if not isinstance(groups, list):
                raise DevWavesError(ReasonCode.SETTINGS_INVALID, {
                    "label": "settings", "kind": "hooks-shape",
                })
            for group in groups:
                if not isinstance(group, dict) or not isinstance(group.get("matcher"), str):
                    raise DevWavesError(ReasonCode.SETTINGS_INVALID, {
                        "label": "settings", "kind": "hook-group",
                    })
                entries = group.get("hooks")
                if not isinstance(entries, list):
                    raise DevWavesError(ReasonCode.SETTINGS_INVALID, {
                        "label": "settings", "kind": "hook-list",
                    })
                for entry in entries:
                    if isinstance(entry, dict) and isinstance(entry.get("command"), str):
                        observed.add((group["matcher"], entry["command"]))
        if not set(profile.required_hooks) <= observed:
            raise DevWavesError(ReasonCode.SETTINGS_INVALID, {
                "label": "settings", "kind": "required-hook-missing",
            })

    def _preflight(self, request: SubmitRequest) -> ResourceLimits:
        if request.profile != self.config.profile.name:
            raise DevWavesError(ReasonCode.INVALID_ARGS, {
                "label": "profile", "kind": "unknown",
            })
        limits = validate_limits(request)
        if os.environ.get("CLAUDECODE"):
            raise DevWavesError(ReasonCode.NESTED_LAUNCH_ENVIRONMENT, {
                "label": "environment", "kind": "CLAUDECODE",
            })
        if not _model_slug(self.config.profile.model):
            raise DevWavesError(ReasonCode.INVALID_ARGS, {
                "label": "model", "kind": "not-complete-literal",
            })
        self._settings_preflight()
        if _sha256_file(self.config.fake_child_executable) != self.config.fake_child_sha256:
            raise DevWavesError(ReasonCode.CLAUDE_UNAVAILABLE, {
                "label": "executable", "kind": "digest-mismatch",
            })
        probe_claude_capabilities(
            self.config.fake_child_executable,
            min(5.0, float(limits.per_wave_timeout_s or 1)),
        )
        main = snapshot_repo(self.main_worktree.path)
        if main.branch != "main":
            raise DevWavesError(ReasonCode.MAIN_NOT_FOUND, {
                "label": "main", "kind": "branch",
            })
        if main.main_dirty or main.submodule_dirty:
            raise DevWavesError(ReasonCode.MAIN_NOT_CLEAN, {
                "label": "main", "kind": "dirty",
            })
        return limits

    def _stop(
        self, ledger: ControlLedger, reason: ReasonCode, *, wave_index: Optional[int],
        terminal: RunState = RunState.FAILED,
    ) -> None:
        if ledger.snapshot.state is not RunState.STOPPING:
            ledger.transition(RunState.STOPPING, reason=reason, wave_index=wave_index)
        ledger.finish(terminal, reason=reason, wave_index=wave_index)

    def _run_entry(
        self, run_id: str, request: SubmitRequest, deadline: BoottimeDeadline,
    ) -> None:
        try:
            self._execute(run_id, request, deadline)
        except BaseException as exc:
            try:
                with self._lock:
                    active = self._active
                    identity = None if active is None else active.worker_identity
                if identity is not None:
                    current = self.status(run_id)
                    self._terminate_wave(
                        self._wave_paths(run_id, max(1, current.wave_index)), identity,
                    )
                with self._open_ledger(run_id) as ledger:
                    if ledger.snapshot.state not in {
                        RunState.COMPLETED, RunState.BLOCKED, RunState.FAILED,
                        RunState.INTERRUPTED,
                    }:
                        reason = exc.code if isinstance(exc, DevWavesError) else ReasonCode.RUNTIME_IO_FAILURE
                        self._stop(ledger, reason,
                                   wave_index=ledger.snapshot.wave_index)
            except BaseException:
                pass
        finally:
            with self._lock:
                try:
                    self._refresh_recovery_runs()
                except DevWavesError:
                    self._recovery_runs.add(run_id)
                if self._active is not None and self._active.run_id == run_id:
                    self._active = None

    def _execute(
        self, run_id: str, request: SubmitRequest, deadline: BoottimeDeadline,
    ) -> None:
        ledger = self._open_ledger(run_id)
        with self._lock:
            if self._active is not None and self._active.run_id == run_id:
                self._active.ledger = ledger
        try:
            ledger.transition(RunState.PREFLIGHT)
            try:
                limits = self._preflight(request)
            except DevWavesError as exc:
                self._stop(ledger, exc.code, wave_index=None)
                return
            if deadline.expired():
                self._stop(ledger, ReasonCode.TIMEOUT, wave_index=None)
                return
            ledger.record_observation(Observation(
                "preflight", "preflight", {"status": "green"},
            ))
            ledger.transition(RunState.READY)
            spent = Decimal(0)
            for wave_index in range(1, request.max_waves + 1):
                with self._lock:
                    active = self._active
                if active is None or active.cancel.is_set():
                    self._stop(ledger, ReasonCode.SIGNAL_RECEIVED,
                               wave_index=wave_index, terminal=RunState.INTERRUPTED)
                    return
                if deadline.expired():
                    self._stop(ledger, ReasonCode.TIMEOUT, wave_index=wave_index)
                    return
                assert limits.total_budget_usd is not None
                assert limits.per_wave_budget_usd is not None
                remaining_budget = limits.total_budget_usd - spent
                if remaining_budget <= 0:
                    self._stop(ledger, ReasonCode.BUDGET_INVALID, wave_index=wave_index)
                    return
                reservation = min(limits.per_wave_budget_usd, remaining_budget)
                report, cost = self._execute_wave(
                    ledger, request, limits, deadline, wave_index, reservation,
                )
                candidate_spent = spent + cost
                if cost > reservation or candidate_spent > limits.total_budget_usd:
                    self._stop(ledger, ReasonCode.BUDGET_INVALID, wave_index=wave_index)
                    return
                spent = candidate_spent
                if not report.ok:
                    self._stop(
                        ledger, report.reason or ReasonCode.CHECK_FAILED,
                        wave_index=wave_index, terminal=RunState.FAILED,
                    )
                    return
                assert report.receipt is not None
                self._guard_wave_side_effect(deadline, "wal-append")
                match report.receipt.outcome:
                    case Outcome.COMPLETED:
                        ledger.transition(
                            RunState.WAVE_ACCEPTED,
                            reason=report.receipt.stop_reason,
                            wave_index=wave_index,
                        )
                        self._crash("after-accepted", run_id, wave_index)
                    case Outcome.NO_ACTIONABLE_TASK:
                        self._stop(
                            ledger, ReasonCode.NO_ACTIONABLE_TASK,
                            wave_index=wave_index, terminal=RunState.COMPLETED,
                        )
                        return
                    case Outcome.USER_RULING_REQUIRED | Outcome.BLOCKED:
                        self._stop(
                            ledger, report.receipt.stop_reason,
                            wave_index=wave_index, terminal=RunState.BLOCKED,
                        )
                        return
                    case Outcome.FAILED:
                        self._stop(
                            ledger, report.receipt.stop_reason,
                            wave_index=wave_index, terminal=RunState.FAILED,
                        )
                        return
                if wave_index == request.max_waves:
                    ledger.finish(
                        RunState.COMPLETED, reason=ReasonCode.MAX_WAVES_REACHED,
                        wave_index=wave_index,
                    )
                    return
                ledger.transition(RunState.READY, wave_index=wave_index)
        finally:
            with self._lock:
                if self._active is not None and self._active.run_id == run_id:
                    self._active.ledger = None
            ledger.close()

    def _wave_paths(self, run_id: str, wave_index: int) -> dict[str, Path]:
        root = self.layout.run_dir(run_id) / "waves" / f"{wave_index:03d}"
        return {
            "root": root,
            "manifest": root / "manifest.json",
            "prompt": root / "prompt.txt",
            "spec": root / "worker-spec.json",
            "stdout": root / "stdout.json",
            "stderr": root / "stderr.log",
            "start": root / "child-start.json",
            "exit": root / "worker-exit.json",
            "trace": root / "git-trace.jsonl",
            "receipt": root / "receipt.json",
            "checks": root / "checks.json",
            "context": root / "verification-context.json",
        }

    def _guard_wave_side_effect(
        self, deadline: BoottimeDeadline, label: str,
    ) -> int:
        """Authorize one normal wave side effect against the sole deadline."""
        remaining_ns = deadline.remaining_ns()
        if remaining_ns <= 0:
            raise DevWavesError(ReasonCode.TIMEOUT, {
                "label": label, "kind": "deadline",
            })
        with self._lock:
            active = self._active
            if active is None or active.cancel.is_set():
                raise DevWavesError(active.cancel_reason if active else ReasonCode.SIGNAL_RECEIVED, {
                    "label": label, "kind": "cancelled",
                })
        if self.dependencies.side_effect_hook is not None:
            self.dependencies.side_effect_hook(label)
        return remaining_ns

    def _create_wave_json(
        self, deadline: BoottimeDeadline, run_id: str, cap: int,
        path: Path, value: object,
    ) -> None:
        raw_size = len(canonical_bytes(value)) + 1
        self._guard_wave_side_effect(deadline, "artifact-write")
        self._enforce_run_capacity(run_id, cap, reserve=raw_size)
        _create_json(path, value)

    def _remaining_worker_seconds(self, deadline: BoottimeDeadline) -> int:
        """Return the integer worker bound; sub-second remainder is expired."""
        remaining_seconds = int(
            self._guard_wave_side_effect(deadline, "worker-spec") / 1_000_000_000
        )
        if remaining_seconds <= 0:
            raise DevWavesError(ReasonCode.TIMEOUT, {
                "label": "worker-spawn", "kind": "deadline",
            })
        return remaining_seconds

    def _create_wave_text(
        self, deadline: BoottimeDeadline, run_id: str, cap: int,
        path: Path, value: str,
    ) -> None:
        raw = value.encode("utf-8")
        self._guard_wave_side_effect(deadline, "artifact-write")
        self._enforce_run_capacity(run_id, cap, reserve=len(raw))
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            _write_all(fd, raw)
            os.fsync(fd)
        finally:
            os.close(fd)
        _fsync_parent(path)

    def _child_environment(
        self, run_id: str, trace: Path, deadline: BoottimeDeadline,
    ) -> tuple[tuple[str, str], ...]:
        self._guard_wave_side_effect(deadline, "artifact-write")
        run = self.layout.run_dir(run_id)
        home = run / "child-home"
        xdg_config = run / "xdg-config"
        xdg_cache = run / "xdg-cache"
        temporary = run / "tmp"
        for path in (home, xdg_config, xdg_cache, temporary):
            path.mkdir(mode=0o700, exist_ok=True)
        empty_git = run / "gitconfig"
        if not empty_git.exists():
            fd = os.open(empty_git, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
            _fsync_parent(empty_git)
        environment = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "LC_ALL": "C", "LANG": "C", "TZ": "UTC",
            "HOME": str(home), "XDG_CONFIG_HOME": str(xdg_config),
            "XDG_CACHE_HOME": str(xdg_cache), "TMPDIR": str(temporary),
            "GIT_CONFIG_GLOBAL": str(empty_git), "GIT_TERMINAL_PROMPT": "0",
            "GIT_TRACE2_EVENT": str(trace), "PYTHONDONTWRITEBYTECODE": "1",
        }
        return tuple(sorted(environment.items()))

    def _context_wire(
        self, before: RepoSnapshot, worktree: WaveWorktree,
        before_ids: tuple[str, ...], worklog_digest: str,
        immutable: tuple[tuple[str, str], ...],
    ) -> dict[str, object]:
        return {
            "before_snapshot": _snapshot_wire(before), "wave_path": worktree.path,
            "wave_branch": worktree.branch, "before_next_task_ids": list(before_ids),
            "before_worklog_sha256": worklog_digest,
            "immutable_digests_before": [list(item) for item in immutable],
        }

    def _verification_input(
        self, run_id: str, wave_index: int, paths: Mapping[str, Path],
        limits: ResourceLimits, deadline: BoottimeDeadline,
        wave_budget: Decimal,
    ) -> VerificationInput:
        raw = strict_loads(paths["context"].read_bytes(), label="verification-context",
                           max_bytes=1024 * 1024)
        if not isinstance(raw, dict):
            raise DevWavesError(ReasonCode.INVALID_RUN, {"label": "context", "kind": "object"})
        before = _snapshot_from_wire(raw["before_snapshot"])
        immutable_before = tuple((str(item[0]), str(item[1])) for item in raw["immutable_digests_before"])
        immutable_after = (("supervisor", _supervisor_digest()),)
        assert limits.max_wave_output_bytes is not None
        return VerificationInput(
            run_id, wave_index, self.repo_root, self.main_worktree.path,
            str(raw["wave_path"]), str(raw["wave_branch"]), before.head_sha, before,
            str(paths["stdout"]), str(paths["stderr"]), limits.max_wave_output_bytes,
            str(paths["start"]), str(paths["exit"]), str(paths["trace"]),
            wave_budget,
            tuple(str(item) for item in raw["before_next_task_ids"]),
            str(raw["before_worklog_sha256"]),
            os.path.join(self.main_worktree.path, "docs", "worklog.md"),
            os.path.join(self.main_worktree.path, "output", "task-runs"),
            os.path.join(self.main_worktree.path, "docs", "handoff"),
            self.config.profile.check_specs, deadline.deadline_ns,
            immutable_before, immutable_after,
        )

    def _execute_wave(
        self, ledger: ControlLedger, request: SubmitRequest, limits: ResourceLimits,
        deadline: BoottimeDeadline, wave_index: int, wave_budget: Decimal,
    ) -> tuple[VerificationReport, Decimal]:
        assert limits.max_wave_output_bytes is not None
        assert limits.max_run_bytes is not None
        self._enforce_run_capacity(
            ledger.snapshot.run_id, limits.max_run_bytes,
            reserve=limits.max_wave_output_bytes + 48 * 1024,
        )
        paths = self._wave_paths(ledger.snapshot.run_id, wave_index)
        self._guard_wave_side_effect(deadline, "artifact-write")
        paths["root"].mkdir(mode=0o700, parents=True)
        _fsync_parent(paths["root"] / "placeholder")
        before = snapshot_repo(self.main_worktree.path)
        worklog = Path(self.main_worktree.path) / "docs" / "worklog.md"
        worklog_raw = worklog.read_bytes()
        before_ids = extract_latest_next_action_ids(worklog_raw.decode("utf-8"))
        self._guard_wave_side_effect(deadline, "wal-append")
        ledger.transition(RunState.WAVE_PREPARED, wave_index=wave_index)
        worktree_intent = SideEffectIntent(
            f"w{wave_index:03d}-worktree", "worktree-add",
            safe_digest([ledger.snapshot.run_id, wave_index, before.head_sha]),
            {"base_main_sha": before.head_sha, "wave_index": wave_index},
        )
        self._guard_wave_side_effect(deadline, "wal-append")
        ledger.prepare_side_effect(worktree_intent, wave_index=wave_index)
        remaining_ns = self._guard_wave_side_effect(deadline, "worktree-add")
        worktree = create_exact_worktree(
            self.repo_root, ledger.snapshot.run_id, wave_index, before.head_sha,
            timeout_s=min(30.0, remaining_ns / 1e9),
        )
        remaining_ns = self._guard_wave_side_effect(deadline, "submodule-update")
        update_submodules_no_fetch(
            worktree.path, timeout_s=min(30.0, remaining_ns / 1e9),
        )
        self._guard_wave_side_effect(deadline, "wal-append")
        ledger.observe_side_effect(
            worktree_intent, {"path": worktree.path, "base_main_sha": worktree.base_sha},
            wave_index=wave_index,
        )
        schema_value = load_receipt_schema()
        schema_json = canonical_bytes(schema_value).decode("utf-8")
        wave_manifest = WaveManifest(
            SCHEMA_VERSION, ledger.snapshot.run_id, wave_index, worktree.path,
            self.main_worktree.path, before.head_sha, receipt_schema_digest(),
        )
        self._create_wave_json(
            deadline, ledger.snapshot.run_id, limits.max_run_bytes,
            paths["manifest"], wave_manifest,
        )
        prompt = f"/dev-wave --supervised-manifest {paths['manifest']}"
        self._create_wave_text(
            deadline, ledger.snapshot.run_id, limits.max_run_bytes,
            paths["prompt"], prompt + "\n",
        )
        assert limits.per_wave_timeout_s is not None
        assert limits.max_wave_output_bytes is not None
        assert limits.max_run_bytes is not None
        remaining_seconds = self._remaining_worker_seconds(deadline)
        spec = WorkerSpec(
            SCHEMA_VERSION, ledger.snapshot.run_id, wave_index,
            self.config.fake_child_executable, self.config.fake_child_sha256,
            worktree.path, self._child_environment(
                ledger.snapshot.run_id, paths["trace"], deadline,
            ),
            self.config.profile.model, self.config.profile.effort,
            self.main_worktree.path, str(paths["manifest"]), schema_json,
            receipt_schema_digest(), wave_budget,
            min(limits.per_wave_timeout_s, remaining_seconds),
            limits.max_wave_output_bytes, limits.max_run_bytes,
            str(paths["stdout"]), str(paths["stderr"]), str(paths["start"]),
            str(paths["exit"]),
        )
        self._create_wave_json(
            deadline, ledger.snapshot.run_id, limits.max_run_bytes, paths["spec"], spec,
        )
        immutable = (("supervisor", _supervisor_digest()),)
        self._create_wave_json(
            deadline, ledger.snapshot.run_id, limits.max_run_bytes, paths["context"],
            self._context_wire(
                before, worktree, before_ids,
                hashlib.sha256(worklog_raw).hexdigest(), immutable,
            ),
        )
        self._enforce_run_capacity(
            ledger.snapshot.run_id, limits.max_run_bytes,
            reserve=limits.max_wave_output_bytes + 32 * 1024,
        )
        spawn_intent = SideEffectIntent(
            f"w{wave_index:03d}-worker", "worker-spawn",
            hashlib.sha256(canonical_bytes(redact_argv(build_child_argv(spec)))).hexdigest(),
            {"path": str(paths["spec"]), "wave_index": wave_index},
        )
        self._guard_wave_side_effect(deadline, "wal-append")
        ledger.prepare_side_effect(spawn_intent, wave_index=wave_index)
        self._guard_wave_side_effect(deadline, "worker-spawn")
        self._crash("before-child", ledger.snapshot.run_id, wave_index)
        process = self.dependencies.spawn_worker_fn(
            paths["spec"], termination_grace_s=self.config.termination_grace_s,
        )
        with self._lock:
            if self._active is not None:
                self._active.worker = process
        try:
            wrapper_identity = read_pid_identity(process.pid)
        except BaseException:
            kill_spawned_process(process)
            with self._lock:
                if self._active is not None and self._active.worker is process:
                    self._active.worker = None
            raise DevWavesError(ReasonCode.SPAWN_FAILED, {
                "label": "worker", "kind": "identity-unreadable",
            }) from None
        with self._lock:
            if self._active is not None:
                self._active.worker_identity = wrapper_identity
        self._guard_wave_side_effect(deadline, "wal-append")
        ledger.observe_side_effect(
            spawn_intent, {
                "status": "spawned", "sha256": pid_identity_digest(wrapper_identity),
                **pid_identity_record(wrapper_identity),
            },
            wave_index=wave_index,
        )
        self._guard_wave_side_effect(deadline, "wal-append")
        ledger.transition(RunState.CHILD_RUNNING, wave_index=wave_index)
        if self.dependencies.crash_hook is not None:
            hook_deadline = time.monotonic() + min(1.0, float(spec.per_wave_timeout_s))
            while (process.poll() is None and not paths["start"].exists() and
                   time.monotonic() < hook_deadline):
                time.sleep(0.005)
        self._crash("running", ledger.snapshot.run_id, wave_index)
        while process.poll() is None:
            with self._lock:
                active = self._active
                cancelled = active is None or active.cancel.is_set()
                if active is not None and cancelled and not active.signal_observed:
                    self._signal_cancel_locked(active)
            time.sleep(0.01)
        process.wait()
        self._enforce_run_capacity(ledger.snapshot.run_id, limits.max_run_bytes)
        with self._lock:
            active = self._active
            if active is not None:
                active.worker = None
                active.worker_identity = None
                cancelled = active.cancel.is_set()
            else:
                cancelled = True
        if cancelled:
            reason = active.cancel_reason if active is not None else ReasonCode.SIGNAL_RECEIVED
            if ledger.snapshot.state not in {
                RunState.COMPLETED, RunState.BLOCKED, RunState.FAILED, RunState.INTERRUPTED,
            }:
                self._stop(
                    ledger, reason, wave_index=wave_index,
                    terminal=(RunState.INTERRUPTED if reason is ReasonCode.SIGNAL_RECEIVED
                              else RunState.FAILED),
                )
            raise DevWavesError(reason, {"label": "worker", "kind": "cancelled"})
        self._guard_wave_side_effect(deadline, "wal-append")
        ledger.transition(RunState.CHILD_EXITED, wave_index=wave_index)
        self._crash("after-exit", ledger.snapshot.run_id, wave_index)
        self._crash("after-land", ledger.snapshot.run_id, wave_index)
        self._guard_wave_side_effect(deadline, "wal-append")
        ledger.transition(RunState.VERIFYING, wave_index=wave_index)
        verification = self._verification_input(
            ledger.snapshot.run_id, wave_index, paths, limits, deadline, wave_budget,
        )
        self._guard_wave_side_effect(deadline, "check-start")
        report = self.dependencies.verify_wave_fn(verification)
        findings = [
            {"name": item.name, "status": item.status,
             "reason": None if item.reason is None else item.reason.value,
             "detail": item.detail}
            for item in report.findings
        ]
        self._create_wave_json(
            deadline, ledger.snapshot.run_id, limits.max_run_bytes, paths["checks"], {
            "ok": report.ok,
            "reason": None if report.reason is None else report.reason.value,
            "active_checks_started": report.active_checks_started,
            "findings": findings,
            },
        )
        if report.receipt is not None:
            self._guard_wave_side_effect(deadline, "artifact-write")
            receipt_wire = strict_loads(
                canonical_bytes(report.receipt), label="receipt-capacity",
                max_bytes=DEFAULT_MAX_JSON_BYTES,
            )
            receipt_size = len(canonical_bytes(redact_value(receipt_wire))) + 1
            self._enforce_run_capacity(
                ledger.snapshot.run_id, limits.max_run_bytes, reserve=receipt_size,
            )
            persist_sanitized_receipt(paths["receipt"], report.receipt)
        self._enforce_run_capacity(ledger.snapshot.run_id, limits.max_run_bytes)
        cost = Decimal(0)
        if report.ok:
            parsed = parse_claude_result(
                paths["stdout"], max_bytes=limits.max_wave_output_bytes,
                binding=ReceiptBinding(ledger.snapshot.run_id, wave_index, before.head_sha),
            )
            cost = parsed.total_cost_usd
        self._crash("after-decision", ledger.snapshot.run_id, wave_index)
        return report, cost

    def _terminate_wave(self, paths: Mapping[str, Path], wrapper: PidIdentity) -> bool:
        if paths["start"].exists():
            try:
                raw = strict_loads(paths["start"].read_bytes(), label="child-start", max_bytes=4096)
                if not isinstance(raw, dict) or set(raw) != {
                    "pid", "boot_id", "start_ticks", "pgid",
                }:
                    raise ValueError("child identity fields")
                child = PidIdentity(
                    int(raw["pid"]), str(raw["boot_id"]), int(raw["start_ticks"]),
                )
                if raw["pgid"] != child.pid:
                    raise ValueError("child process group binding")
                if not terminate_verified_group(child, self.config.termination_grace_s):
                    return False
            except (OSError, ValueError, KeyError, DevWavesError):
                raise DevWavesError(ReasonCode.AMBIGUOUS_RECOVERY, {
                    "label": "child-start", "kind": "identity-unreadable",
                }) from None
        return terminate_verified_group(wrapper, self.config.termination_grace_s)

    def _signal_cancel_locked(self, active: _ActiveRun) -> None:
        """Durably prepare, verified-signal, and observe one cancellation."""
        if active.signal_observed or active.worker_identity is None:
            return
        if active.ledger is None:
            active.cancel_reason = ReasonCode.AMBIGUOUS_RECOVERY
            active.cancel.set()
            raise DevWavesError(ReasonCode.AMBIGUOUS_RECOVERY, {
                "label": "cancel", "kind": "ledger-unavailable",
            })
        wave_index = active.ledger.snapshot.wave_index or 0
        identity = active.worker_identity
        signal_intent = SideEffectIntent(
            f"w{wave_index:03d}-cancel", "signal",
            pid_identity_digest(identity),
            {**pid_identity_record(identity), "wave_index": wave_index},
        )
        active.ledger.prepare_side_effect(signal_intent, wave_index=wave_index)
        try:
            signalled = self._terminate_wave(
                self._wave_paths(active.run_id, wave_index), identity,
            )
        except DevWavesError:
            signalled = False
        active.signal_observed = True
        active.cancel_reason = (
            ReasonCode.SIGNAL_RECEIVED if signalled else ReasonCode.AMBIGUOUS_RECOVERY
        )
        active.ledger.observe_side_effect(
            signal_intent,
            {"status": "signalled" if signalled else "ambiguous",
             **pid_identity_record(identity)},
            wave_index=wave_index,
        )
        if not signalled and active.ledger.snapshot.state not in {
            RunState.COMPLETED, RunState.BLOCKED, RunState.FAILED, RunState.INTERRUPTED,
        }:
            self._stop(
                active.ledger, ReasonCode.AMBIGUOUS_RECOVERY,
                wave_index=wave_index,
            )

    def _request_cancel_locked(self, active: _ActiveRun, source: str) -> None:
        if active.cancel_source is None:
            active.cancel_source = source
        active.cancel.set()
        self._signal_cancel_locked(active)

    def status(self, run_id: str) -> StatusResponse:
        matches = {item.run_id: item for item in discover_runs(self.layout)}
        item = matches.get(run_id)
        if item is None or item.snapshot is None:
            reason = item.reason if item is not None else ReasonCode.INVALID_RUN
            return StatusResponse(PROTOCOL_VERSION, False, run_id, RunState.FAILED, 0,
                                  Decimal(0), reason)
        snapshot = item.snapshot
        if item.reason is not None:
            return StatusResponse(
                PROTOCOL_VERSION, False, run_id, snapshot.state,
                snapshot.wave_index or 0, Decimal(0), item.reason,
            )
        elapsed_ns = max(0, _boottime_ns() - snapshot.started_boottime_ns)
        elapsed = Decimal(elapsed_ns // 1_000_000) / Decimal(1000)
        return StatusResponse(
            PROTOCOL_VERSION, True, run_id, snapshot.state,
            snapshot.wave_index or 0, elapsed, snapshot.reason,
        )

    def cancel(self, run_id: str, request_id: Optional[str] = None) -> CancelResponse:
        with self._lock:
            if request_id is not None:
                prior = self._cancel_index.get(request_id)
                if prior is not None and prior != run_id:
                    raise DevWavesError(ReasonCode.REQUEST_CONFLICT, {
                        "label": "cancel-request-id", "kind": "run-mismatch",
                    })
                self._cancel_index[request_id] = run_id
            active = self._active
            if active is not None and active.run_id == run_id:
                self._request_cancel_locked(active, "api")
            status = self.status(run_id)
        return CancelResponse(
            PROTOCOL_VERSION, status.ok, run_id, status.state, status.reason,
        )

    def validate(self, run_id: str) -> StatusResponse:
        replay_run(self.layout.run_dir(run_id))
        return self.status(run_id)

    def resume(self, run_id: str) -> StatusResponse:
        with self._lock:
            if self._active is not None and self._active.thread.is_alive():
                raise DevWavesError(ReasonCode.DAEMON_BUSY, {
                    "label": "resume", "kind": "active-run",
                })
        ledger = self._open_ledger(run_id)
        try:
            snapshot = ledger.snapshot
            if snapshot.state in {
                RunState.COMPLETED, RunState.BLOCKED, RunState.FAILED, RunState.INTERRUPTED,
            }:
                self._recovery_runs.discard(run_id)
                return self.status(run_id)
            if snapshot.prepared_operations - snapshot.observed_operations:
                self._stop(ledger, ReasonCode.AMBIGUOUS_RECOVERY,
                           wave_index=snapshot.wave_index)
                self._recovery_runs.discard(run_id)
                return self.status(run_id)
            # T-076 never guesses whether an unobserved child or landing happened.
            # Durable accepted waves are safe to continue; every other active
            # phase is stopped without respawn, merge, or cleanup.
            if snapshot.state is not RunState.WAVE_ACCEPTED:
                if snapshot.state is RunState.CHILD_RUNNING and snapshot.wave_index:
                    paths = self._wave_paths(run_id, snapshot.wave_index)
                    try:
                        raw = strict_loads(paths["start"].read_bytes(), label="child-start", max_bytes=4096)
                        if isinstance(raw, dict):
                            terminate_verified_group(PidIdentity(
                                int(raw["pid"]), str(raw["boot_id"]), int(raw["start_ticks"]),
                            ), self.config.termination_grace_s)
                    except (OSError, ValueError, KeyError, DevWavesError):
                        pass
                self._stop(ledger, ReasonCode.AMBIGUOUS_RECOVERY,
                           wave_index=snapshot.wave_index)
                self._recovery_runs.discard(run_id)
                return self.status(run_id)
            manifest = parse_run_manifest((ledger.path / "manifest.json").read_bytes().rstrip(b"\n"))
            assert snapshot.wave_index is not None
            paths = self._wave_paths(run_id, snapshot.wave_index)
            try:
                receipt_value = strict_loads(
                    paths["receipt"].read_bytes(), label="recovery-receipt",
                    max_bytes=1024 * 1024,
                )
                wave_manifest = parse_wave_manifest(paths["manifest"].read_bytes().rstrip(b"\n"))
                receipt = validate_child_receipt(receipt_value, binding=ReceiptBinding(
                    run_id, snapshot.wave_index, wave_manifest.base_main_sha,
                ))
                current_identity = resolve_repo_identity(self.repo_root)
                current = snapshot_repo(self.main_worktree.path)
                context = strict_loads(
                    paths["context"].read_bytes(), label="recovery-context",
                    max_bytes=1024 * 1024,
                )
                wave_branch = str(context["wave_branch"]) if isinstance(context, dict) else ""
                tip = branch_tip(self.repo_root, wave_branch, timeout_s=5.0)
                accepted_matches = (
                    receipt.outcome is Outcome.COMPLETED and receipt.landed_commits and
                    current_identity.digest == self.repo_identity.digest == manifest.repo_identity and
                    os.path.realpath(current_identity.main_worktree) == os.path.realpath(
                        self.main_worktree.path
                    ) and current.branch == "main" and
                    not current.main_dirty and not current.submodule_dirty and
                    current.head_sha == receipt.landed_main_sha == receipt.landed_commits[-1] == tip
                )
            except (OSError, DevWavesError, ValueError, KeyError):
                accepted_matches = False
            if not accepted_matches:
                self._stop(ledger, ReasonCode.AMBIGUOUS_RECOVERY,
                           wave_index=snapshot.wave_index)
                self._recovery_runs.discard(run_id)
                return self.status(run_id)
            if snapshot.wave_index is not None and snapshot.wave_index >= manifest.max_waves:
                ledger.finish(RunState.COMPLETED, reason=ReasonCode.MAX_WAVES_REACHED,
                              wave_index=snapshot.wave_index)
                self._recovery_runs.discard(run_id)
                return self.status(run_id)
            # Accepted-wave continuation needs no duplicate child.  Reconstruct
            # the immutable submit request from the manifest and launch the next.
            synthetic = SubmitRequest(
                PROTOCOL_VERSION, "submit", manifest.repo_identity,
                manifest.max_waves, manifest.profile,
                "00000000-0000-4000-8000-000000000000", manifest.limits,
            )
        finally:
            ledger.close()
        thread = threading.Thread(target=self._resume_accepted,
                                  args=(run_id, synthetic), daemon=False)
        with self._lock:
            self._active = _ActiveRun(run_id, thread)
            thread.start()
        return self.status(run_id)

    def _resume_accepted(self, run_id: str, request: SubmitRequest) -> None:
        # Current implementation deliberately stops if the complete original
        # total deadline cannot be reconstructed without extending it.
        ledger = self._open_ledger(run_id)
        try:
            self._stop(ledger, ReasonCode.AMBIGUOUS_RECOVERY,
                       wave_index=ledger.snapshot.wave_index)
            self._recovery_runs.discard(run_id)
        finally:
            ledger.close()
            with self._lock:
                self._active = None

    def export(self, run_id: str, output: os.PathLike[str] | str) -> Path:
        destination = Path(output)
        if destination.exists():
            raise FileExistsError(destination)
        run = self.layout.run_dir(run_id)
        snapshot = replay_run(run)
        events = []
        for line in (run / "events.jsonl").read_bytes().splitlines():
            event = strict_loads(line, label="export-event", max_bytes=64 * 1024)
            if not isinstance(event, dict):
                raise DevWavesError(ReasonCode.INVALID_RUN, {
                    "label": "export-event", "kind": "object",
                })
            events.append({
                "action": event.get("event"), "state": event.get("state"),
                "reason": event.get("reason"), "wave_index": event.get("wave_index"),
                "detail": redact_value(event.get("data", {})),
            })
        manifest = strict_loads((run / "manifest.json").read_bytes().rstrip(b"\n"),
                                label="export-manifest", max_bytes=1024 * 1024)
        value = redact_value({
            "schema_version": SCHEMA_VERSION, "run_id": run_id,
            "detail": manifest, "artifact": events,
            "status": {"state": snapshot.state.value,
                       "reason": None if snapshot.reason is None else snapshot.reason.value,
                       "wave_index": snapshot.wave_index},
        })
        assert_sanitized(value)
        _create_json(destination, value)
        return destination

    def serve_forever(self) -> None:
        if os.environ.get("CLAUDECODE"):
            raise DevWavesError(ReasonCode.NESTED_LAUNCH_ENVIRONMENT, {
                "label": "environment", "kind": "CLAUDECODE",
            })
        self._persist_profile()
        with RepositoryLease.acquire(self.layout) as lease, SignalRelay() as relay:
            stale_socket = self.layout.root / ".s"
            try:
                info = stale_socket.lstat()
            except FileNotFoundError:
                pass
            else:
                if (not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.getuid() or
                        stat.S_IMODE(info.st_mode) != 0o600):
                    raise DevWavesError(ReasonCode.RUNTIME_IO_FAILURE, {
                        "label": "repo-socket", "kind": "unsafe-stale-socket",
                    })
                stale_socket.unlink()
                _fsync_parent(stale_socket)
            old_handlers: dict[int, Any] = {}
            if threading.current_thread() is threading.main_thread():
                for number in (signal.SIGINT, signal.SIGTERM):
                    old_handlers[number] = signal.getsignal(number)
                    signal.signal(number, relay.notify)
            try:
                with bind_repo_socket(self.layout.root, os.getuid()) as bound:
                    while not self._shutdown.is_set():
                        lease.assert_valid()
                        ready, _, _ = select.select([bound.sock, relay.fileno()], [], [], 0.25)
                        if relay.fileno() in ready:
                            if relay.drain():
                                with self._lock:
                                    active = self._active
                                    if active is not None:
                                        self._request_cancel_locked(active, "signal")
                                self._shutdown.set()
                        if bound.sock in ready:
                            conn, _ = bound.accept()
                            with conn:
                                try:
                                    raw = receive_request(
                                        conn, max_bytes=self.config.max_request_bytes,
                                        deadline_s=self.config.socket_read_deadline_s,
                                        expected_uid=os.getuid(),
                                    )
                                    response = self.dispatch(raw)
                                except DevWavesError as exc:
                                    response = encode_response(self._response(
                                        "error", False, reason=exc.code, detail=exc.detail,
                                    ))
                                send_frame(conn, response)
                                conn.shutdown(socket.SHUT_WR)
            finally:
                for number, handler in old_handlers.items():
                    signal.signal(number, handler)

    def shutdown(self) -> None:
        self._shutdown.set()
        with self._lock:
            if self._active is not None:
                self._request_cancel_locked(self._active, "shutdown")

    def _persist_profile(self) -> None:
        path = self.layout.root / _PROFILE_NAME
        profile = self.config.profile
        settings_sha256 = self._settings_sha256
        value = {
            "schema_version": SCHEMA_VERSION,
            "repo_root": self.repo_root,
            "fake_child_executable": self.config.fake_child_executable,
            "fake_child_sha256": self.config.fake_child_sha256,
            "profile": profile.name,
            "model": profile.model,
            "effort": profile.effort,
            "allowed_models": list(profile.allowed_models),
            "check_specs": [
                {"name": item.name, "argv": list(item.argv),
                 "timeout_s": item.timeout_s}
                for item in profile.check_specs
            ],
            "settings_path": profile.settings_path,
            "settings_sha256": settings_sha256,
            "required_hooks": [list(item) for item in profile.required_hooks],
            "caps": {
                "max_waves": profile.max_waves,
                "max_per_wave_timeout_s": profile.max_per_wave_timeout_s,
                "max_total_timeout_s": profile.max_total_timeout_s,
                "max_per_wave_budget_usd": canonical_decimal(
                    profile.max_per_wave_budget_usd  # type: ignore[arg-type]
                ),
                "max_total_budget_usd": canonical_decimal(
                    profile.max_total_budget_usd  # type: ignore[arg-type]
                ),
                "max_wave_output_bytes": profile.max_wave_output_bytes,
                "max_run_bytes": profile.max_run_bytes,
            },
        }
        if path.exists():
            current = strict_loads(path.read_bytes(), label="server-profile", max_bytes=64 * 1024)
            if current != value:
                raise DevWavesError(ReasonCode.SETTINGS_INVALID, {
                    "label": "server-profile", "kind": "changed",
                })
        else:
            _create_json(path, value)


__all__ = [
    "DoctorReport", "Supervisor", "SupervisorConfig", "SupervisorDependencies",
    "SupervisorProfile", "doctor", "probe_claude_capabilities",
]
