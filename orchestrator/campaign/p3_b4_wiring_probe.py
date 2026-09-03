# -*- coding: utf-8 -*-
"""B-4 reflux wiring probe with process-wide outcome interdiction.

The evidence is deliberately composite: a static candidate-main path plus a
direct call to the real switchpoint made by this probe.  It does not claim that
the candidate main traversed that edge at runtime.  Generation interdiction is
the reverse closure over statically resolved call edges from three named seeds
within the exact analyzed-module manifest recorded in evidence.  Modules
outside that manifest, producers that reach none of those seeds, and callers
within the manifest whose call binding cannot be statically resolved are not
covered by that layer.  Protected campaign viewing is handled by the audit
layer.  Arbitrary native code and an equally privileged process are outside
this probe's claim.
"""
from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import importlib
import inspect
import json
import marshal
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import sys
import tempfile
import threading
from types import ModuleType
from typing import Any, Callable, Iterable, Mapping, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"


SCHEMA_VERSION = "p3-b4-wiring-probe-evidence/v1"
EVIDENCE_CLASS = "tool-dogfood-non-adoption"
SANCTIONED_ENTRYPOINT = "orchestrator.campaign.p3_b4_wiring_probe.main"
_REPO_ROOT = Path(__file__).resolve().parents[2]
_PROBE_RELATIVE = "orchestrator/campaign/p3_b4_wiring_probe.py"
_EVIDENCE_ROOT = (
    _REPO_ROOT / "output" / "insights" /
    "2026-08-27_t1769-b4-wiring-probe"
)
_EVIDENCE_SET_RE = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}\Z")
_HEX64_RE = re.compile(r"[0-9a-f]{64}\Z")
_FIXTURE_SCHEMA = "p3-b4-probe-fixture/v1"
_FIXTURE_MARKER = "t1769-b4-probe-reserved-marker-v1"
_AUDIT_CHALLENGE_EVENT = "izanagi.p3_b4_probe.audit_challenge"
_CAMPAIGN_PACKAGE = "orchestrator.campaign"
_IDENTITY_PREIMAGE_DOMAIN = b"izanagi.p3-b4-wiring-probe.identity-preimage/v1\0"

_MODULE_RELATIVE_PATHS = {
    f"{_CAMPAIGN_PACKAGE}.execution_guard": "orchestrator/campaign/execution_guard.py",
    f"{_CAMPAIGN_PACKAGE}.loop": "orchestrator/campaign/loop.py",
    f"{_CAMPAIGN_PACKAGE}.pipeline": "orchestrator/campaign/pipeline.py",
    f"{_CAMPAIGN_PACKAGE}.p3_s4_loop": "orchestrator/campaign/p3_s4_loop.py",
    f"{_CAMPAIGN_PACKAGE}.p3_s4_loop_sort": "orchestrator/campaign/p3_s4_loop_sort.py",
    f"{_CAMPAIGN_PACKAGE}.p3_s4_loop_trigger_gating": (
        "orchestrator/campaign/p3_s4_loop_trigger_gating.py"
    ),
}
_DRIVER_MODULES = {
    "base": f"{_CAMPAIGN_PACKAGE}.p3_s4_loop",
    "sort": f"{_CAMPAIGN_PACKAGE}.p3_s4_loop_sort",
    "trigger": f"{_CAMPAIGN_PACKAGE}.p3_s4_loop_trigger_gating",
}
_RUNTIME_IMPORT_ROOTS = tuple(sorted({
    *_MODULE_RELATIVE_PATHS,
    f"{_CAMPAIGN_PACKAGE}.artifact_admission",
    f"{_CAMPAIGN_PACKAGE}.build_admission",
    f"{_CAMPAIGN_PACKAGE}.campaign_lock",
    f"{_CAMPAIGN_PACKAGE}.contract_loader_binding",
    f"{_CAMPAIGN_PACKAGE}.env_contract",
    f"{_CAMPAIGN_PACKAGE}.ident",
    f"{_CAMPAIGN_PACKAGE}.site_policy",
    f"{_CAMPAIGN_PACKAGE}.sort_swo_oracle",
}))
_GENERATION_SEEDS = (
    f"{_CAMPAIGN_PACKAGE}.execution_guard.require_certified_writer_authorization",
    f"{_CAMPAIGN_PACKAGE}.p3_s4_loop.save_loop_state",
    f"{_CAMPAIGN_PACKAGE}.p3_s4_loop.project_whiteboard",
)
_SWITCHPOINT = f"{_CAMPAIGN_PACKAGE}.p3_s4_loop.make_critic_digest"
_OVERLAY_RELATIVE = "orchestrator/campaign/legacy_admission_overlay_v1.json"
_REJECTION_HEADING = (
    "# rejections — 正しさ/liveness/frame/screening で不採用 "
    "(未認証性能数値は表示しない)"
)
_ABORT_HEADING = (
    "# verify run の abort 統計 (シグナル — reject 理由ではない。"
    "閾値判定なし、異常かどうかは読み手が stock 対照比で判断)"
)


class StaticInventoryError(RuntimeError):
    """A static proof binding or inventory edge could not be resolved."""


class ProbeIsolationError(RuntimeError):
    """The probe attempted to leave its issued isolation boundary."""


class OutcomeGenerationError(RuntimeError):
    """A sealed production outcome producer was entered."""

    def __init__(self, entry: Mapping[str, object]):
        self.module = str(entry["module"])
        self.qualname = str(entry["qualname"])
        self.path = str(entry["path"])
        self.firstlineno = int(entry["firstlineno"])
        super().__init__(
            "outcome generation interdicted before function body: "
            f"{self.module}.{self.qualname} ({self.path}:{self.firstlineno})"
        )


@dataclass(frozen=True)
class DriverSpec:
    name: str
    module: str
    relative_path: str


@dataclass(frozen=True)
class _StaticFunction:
    symbol: str
    module: str
    name: str
    node: ast.FunctionDef | ast.AsyncFunctionDef
    calls: tuple["_StaticCall", ...]
    issues: tuple[str, ...]


@dataclass(frozen=True)
class _StaticCall:
    callee: str
    line: int
    guards: tuple[str, ...]


@dataclass(frozen=True)
class _StaticModule:
    name: str
    path: Path
    relative_path: str
    source: str
    tree: ast.Module
    imports: Mapping[str, str]
    functions: Mapping[str, _StaticFunction]
    issues: tuple[str, ...]


@dataclass(frozen=True)
class _Runtime:
    modules: Mapping[str, ModuleType]
    drivers: Mapping[str, DriverSpec]
    L: ModuleType
    sort: ModuleType
    trigger: ModuleType
    pipeline: ModuleType
    ident: ModuleType
    artifact_admission: ModuleType
    build_admission: ModuleType
    env_contract: ModuleType
    campaign_lock: ModuleType
    contract_loader_binding: ModuleType
    site_policy: ModuleType
    loader_binding: object
    activation_state: object
    thread_count_before_imports: int
    thread_count_at_seal: int
    repository_head: str


@dataclass
class _CheckContext:
    runtime: _Runtime
    guard: "_ProcessGuard"
    spec: DriverSpec
    view: object
    static_switchpoint: Mapping[str, object]


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ) + "\n"
    ).encode("utf-8")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _paths_overlap(left: Path, right: Path) -> bool:
    return _is_relative_to(left, right) or _is_relative_to(right, left)


def _resolved(path: os.PathLike[str] | str) -> Path:
    try:
        return Path(path).resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise ProbeIsolationError(f"path cannot be resolved: {path!s}") from exc


def _fd_path(fd: int) -> Path:
    if type(fd) is not int or fd < 0:
        raise ProbeIsolationError(f"invalid pre-opened file descriptor: {fd!r}")
    try:
        raw = os.readlink(f"/proc/self/fd/{fd}")
    except OSError as exc:
        raise ProbeIsolationError(
            f"pre-opened file descriptor cannot be resolved: {fd}"
        ) from exc
    return _resolved(raw)


def _resolved_audit_path(
    raw: object, *, dir_fd: object = None, relative_base: Path | None = None,
) -> Path | None:
    if type(raw) is int:
        return _fd_path(raw)
    if not isinstance(raw, (str, bytes, os.PathLike)):
        return None
    path = Path(os.fsdecode(os.fspath(raw)))
    if path.is_absolute():
        return _resolved(path)
    if relative_base is not None:
        return _resolved(relative_base / path)
    if type(dir_fd) is int and dir_fd != getattr(os, "AT_FDCWD", -100):
        base = _fd_path(dir_fd)
        if not base.is_dir():
            base = base.parent
        return _resolved(base / path)
    return _resolved(Path.cwd() / path)


def _assert_no_symlink_components(path: Path, *, allow_missing_tail: bool) -> None:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            info = current.lstat()
        except FileNotFoundError:
            if allow_missing_tail:
                return
            raise ProbeIsolationError(f"required path component is missing: {current}")
        except OSError as exc:
            raise ProbeIsolationError(f"path component cannot be inspected: {current}") from exc
        if stat.S_ISLNK(info.st_mode):
            raise ProbeIsolationError(f"symlink path component is forbidden: {current}")


def _protected_campaign_roots(environ: Mapping[str, str] | None = None) -> tuple[Path, ...]:
    env = os.environ if environ is None else environ
    candidates = [
        _REPO_ROOT / "output" / "campaigns",
        _REPO_ROOT / "output" / "exploration" / "campaigns",
    ]
    official = env.get("IZANAGI_OFFICIAL_OUTPUT_ROOT")
    exploration = env.get("IZANAGI_EXPLORATION_OUTPUT_ROOT")
    if official:
        candidates.append(Path(official) / "campaigns")
    if exploration:
        candidates.append(Path(exploration) / "exploration" / "campaigns")
    unique = {_resolved(path) for path in candidates}
    return tuple(sorted(unique, key=lambda item: item.as_posix()))


def _path_access(args: tuple[object, ...]) -> tuple[Path | None, bool, bool]:
    if not args:
        return None, False, False
    path = _resolved_audit_path(args[0])
    if path is None:
        return None, False, False
    mode = args[1] if len(args) > 1 else None
    flags = args[2] if len(args) > 2 else 0
    write = False
    if isinstance(mode, str):
        write = any(letter in mode for letter in "wax+")
    if isinstance(flags, int):
        write = write or bool(flags & (
            os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
        ))
    return path, not write, write


def _mutation_paths(event: str, args: tuple[object, ...]) -> tuple[Path, ...]:
    if event in {"os.rename", "os.replace", "os.link"}:
        if len(args) < 2:
            raise ProbeIsolationError(f"{event} audit event omitted a path")
        source_fd = args[2] if len(args) > 2 else None
        destination_fd = args[3] if len(args) > 3 else None
        source = _resolved_audit_path(args[0], dir_fd=source_fd)
        destination = _resolved_audit_path(args[1], dir_fd=destination_fd)
        if source is None or destination is None:
            raise ProbeIsolationError(f"{event} audit path cannot be resolved")
        return source, destination
    if event == "os.symlink":
        if len(args) < 2:
            raise ProbeIsolationError("os.symlink audit event omitted a path")
        destination_fd = args[2] if len(args) > 2 else None
        destination = _resolved_audit_path(args[1], dir_fd=destination_fd)
        if destination is None:
            raise ProbeIsolationError("os.symlink destination cannot be resolved")
        source = _resolved_audit_path(
            args[0], relative_base=destination.parent,
        )
        if source is None:
            raise ProbeIsolationError("os.symlink source cannot be resolved")
        return source, destination
    if not args:
        raise ProbeIsolationError(f"{event} audit event omitted a path")
    dir_fd_index = {
        "os.mkdir": 2,
        "os.remove": 1,
        "os.rmdir": 1,
    }.get(event)
    dir_fd = (
        args[dir_fd_index]
        if dir_fd_index is not None and len(args) > dir_fd_index
        else None
    )
    path = _resolved_audit_path(args[0], dir_fd=dir_fd)
    if path is None:
        raise ProbeIsolationError(f"{event} audit path cannot be resolved")
    return (path,)


class _ProcessGuard:
    """One-way audit/profile guard.  Production main never restores it."""

    _PROCESS_EVENTS = frozenset({
        "subprocess.Popen", "os.system", "os.posix_spawn", "os.posix_spawnp",
        "os.spawn", "os.exec", "os.execve",
    })
    _WRITE_EVENTS = frozenset({
        "os.mkdir", "os.remove", "os.rmdir", "os.rename", "os.replace",
        "os.link", "os.symlink", "os.truncate",
    })
    _CODE_MUTATION_EVENTS = frozenset({
        "code.__new__", "compile", "exec", "function.__new__", "import",
    })

    def __init__(self, protected_roots: Sequence[Path]):
        self.protected_roots = tuple(protected_roots)
        self.overlay_path = _resolved(_REPO_ROOT / _OVERLAY_RELATIVE)
        self.overlay_read_paths: set[Path] = set()
        self.protected_read_attempts = 0
        self.protected_write_attempts = 0
        self.forbidden_subprocess_attempts = 0
        self.allowed_git_argv_sha256: list[str] = []
        self.blocked_outcome_attempts: list[dict[str, object]] = []
        self.failed_check_attempts: list[str] = []
        self.interpreter_mutation_attempts: list[str] = []
        self.profile_counts: dict[object, int] = {}
        self._inventory_by_code: dict[object, dict[str, object]] = {}
        self._forbidden_profile_codes: dict[object, str] = {}
        self._module_identity: dict[str, ModuleType] = {}
        self._code_identity: dict[str, object] = {}
        self._source_identity: dict[str, str] = {}
        self._audit_nonce = object()
        self._audit_observations: set[str] = set()
        self._audit_callable = self._audit
        self._profile_callable = self._profile
        self._profile_failure_pending = False
        self.audit_installed = False
        self.sealed = False

    def install_audit(self) -> None:
        if self.audit_installed:
            raise ProbeIsolationError("audit hook was installed more than once")
        sys.addaudithook(self._audit_callable)
        self.audit_installed = True

    def observe_audit(self, stage: str) -> bool:
        before = stage in self._audit_observations
        if before:
            raise ProbeIsolationError(f"audit observation stage was reused: {stage}")
        sys.audit(_AUDIT_CHALLENGE_EVENT, self._audit_nonce, stage)
        return stage in self._audit_observations

    def profile_active(self) -> bool:
        return sys.getprofile() is self._profile_callable

    def audit_active(self, stage: str) -> bool:
        return self.observe_audit(stage)

    def publish_boundary_active(self, stage: str) -> bool:
        active = self.profile_active() and self.audit_active(stage)
        if not active:
            raise ProbeIsolationError(
                f"publish boundary guard identity was not observed: {stage}"
            )
        self.verify_publish_boundary()
        return active

    def _under_protected(self, path: Path) -> bool:
        return any(_is_relative_to(path, root) for root in self.protected_roots)

    def _allow_read_only_git(self, args: tuple[object, ...]) -> bool:
        if len(args) < 4:
            return False
        executable, argv, _cwd, env = args[:4]
        if os.fspath(executable) != "/usr/bin/git" or not isinstance(argv, (list, tuple)):
            return False
        words = [os.fspath(item) for item in argv]
        if not words or words[0] != "/usr/bin/git":
            return False
        try:
            separator = words.index("-C")
        except ValueError:
            return False
        if separator + 2 >= len(words) or _resolved(words[separator + 1]) != _REPO_ROOT:
            return False
        operation = words[separator + 2:]
        allowed_shape = (
            operation == ["rev-parse", "--show-toplevel"]
            or (
                len(operation) == 3
                and operation[:2] == ["rev-parse", "--verify"]
            )
            or (
                len(operation) == 3
                and operation[:2] == ["cat-file", "blob"]
                and ":" in operation[2]
            )
        )
        if not allowed_shape or not isinstance(env, dict):
            return False
        required = {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
        }
        if any(env.get(key) != value for key, value in required.items()):
            return False
        if any(key.startswith("GIT_") and key not in required for key in env):
            return False
        frame = inspect.currentframe()
        caller_ok = False
        try:
            while frame is not None:
                caller = (
                    frame.f_globals.get("__name__"), frame.f_code.co_name,
                )
                if caller == (
                    f"{_CAMPAIGN_PACKAGE}.contract_loader_binding",
                    "_run_git",
                ):
                    caller_ok = True
                    break
                frame = frame.f_back
        finally:
            del frame
        if not caller_ok:
            return False
        self.allowed_git_argv_sha256.append(
            _sha256_bytes(_canonical_bytes(words).rstrip(b"\n"))
        )
        return True

    def _audit(self, event: str, args: tuple[object, ...]) -> None:
        if event == _AUDIT_CHALLENGE_EVENT:
            if len(args) == 2 and args[0] is self._audit_nonce and type(args[1]) is str:
                self._audit_observations.add(args[1])
            return
        if event == "open":
            path, read, write = _path_access(args)
            if path is not None and path == self.overlay_path and read:
                self.overlay_read_paths.add(path)
            if path is not None and self._under_protected(path):
                if read:
                    self.protected_read_attempts += 1
                if write:
                    self.protected_write_attempts += 1
                raise ProbeIsolationError("protected campaign artifact access was blocked")
            return
        if event in {"os.listdir", "os.scandir"}:
            path, _read, _write = _path_access(args)
            if path is not None and self._under_protected(path):
                self.protected_read_attempts += 1
                raise ProbeIsolationError("protected campaign directory listing was blocked")
            return
        if event in self._WRITE_EVENTS:
            paths = _mutation_paths(event, args)
            if any(self._under_protected(path) for path in paths):
                self.protected_write_attempts += 1
                raise ProbeIsolationError("protected campaign mutation was blocked")
            return
        if event == "subprocess.Popen":
            if self._allow_read_only_git(args):
                return
            self.forbidden_subprocess_attempts += 1
            raise ProbeIsolationError("process launch is forbidden in the probe window")
        if event in self._PROCESS_EVENTS:
            self.forbidden_subprocess_attempts += 1
            raise ProbeIsolationError("process launch is forbidden in the probe window")
        if self.sealed:
            if event == "sys.setprofile" and self._profile_failure_pending:
                # CPython disables a profile callback after that callback raises.
                # Preserve the primary interdiction exception, record the
                # one-shot transition, and keep publication permanently closed.
                self._profile_failure_pending = False
                self.interpreter_mutation_attempts.append(
                    "interpreter-profile-disable-after-profile-error"
                )
                return
            code_assignment = (
                event == "object.__setattr__"
                and len(args) >= 2
                and args[1] == "__code__"
            )
            if (
                event in self._CODE_MUTATION_EVENTS
                or event in {"sys.setprofile", "sys.settrace"}
                or code_assignment
            ):
                self.interpreter_mutation_attempts.append(event)
                raise ProbeIsolationError(
                    f"dynamic interpreter mutation is forbidden: {event}"
                )

    def seal(
        self,
        inventory: Sequence[Mapping[str, object]],
        modules: Mapping[str, ModuleType],
    ) -> None:
        if self.sealed:
            raise ProbeIsolationError("profile guard was sealed more than once")
        self._module_identity = dict(modules)
        for entry in inventory:
            module = modules[str(entry["module"])]
            function = getattr(module, str(entry["qualname"]))
            code = function.__code__
            self._inventory_by_code[code] = dict(entry)
            self._code_identity[
                f"{entry['module']}.{entry['qualname']}"
            ] = code
        self._source_identity = {
            name: _sha256_file(Path(module.__file__).resolve())
            for name, module in modules.items()
        }
        threading_profile_code = getattr(threading.setprofile, "__code__", None)
        # A distribution-provided excepthook may import diagnostic helpers while
        # reporting an otherwise useful primary exception.  Imports remain
        # forbidden after sealing, so use CPython's import-free fallback before
        # that boundary closes.
        sys.excepthook = sys.__excepthook__
        sys.setprofile(self._profile_callable)
        threading.setprofile(self._profile_callable)
        if threading_profile_code is not None:
            self._forbidden_profile_codes[threading_profile_code] = (
                "threading.setprofile"
            )
        self.sealed = True
        if not self.profile_active():
            raise ProbeIsolationError("installed profile hook identity was not observed")

    def watch(self, functions: Iterable[Callable[..., object]]) -> None:
        for function in functions:
            self.profile_counts.setdefault(function.__code__, 0)

    def count(self, function: Callable[..., object]) -> int:
        return self.profile_counts.get(function.__code__, 0)

    def _profile(self, frame, event: str, _arg):
        if event != "call":
            return self._profile_callable
        code = frame.f_code
        mutation = self._forbidden_profile_codes.get(code)
        if self.sealed and mutation is not None:
            self.interpreter_mutation_attempts.append(mutation)
            self._profile_failure_pending = True
            raise ProbeIsolationError(
                f"dynamic interpreter mutation is forbidden: {mutation}"
            )
        if code in self.profile_counts:
            self.profile_counts[code] += 1
        entry = self._inventory_by_code.get(code)
        if entry is not None:
            attempt = dict(entry)
            self.blocked_outcome_attempts.append(attempt)
            self._profile_failure_pending = True
            raise OutcomeGenerationError(attempt)
        return self._profile_callable

    def verify_seal(self) -> None:
        if not self.profile_active():
            raise ProbeIsolationError("profile hook identity changed after seal")
        get_thread_profile = getattr(threading, "getprofile", None)
        if get_thread_profile is not None and get_thread_profile() is not self._profile_callable:
            raise ProbeIsolationError("thread profile hook identity changed after seal")
        for name, original in self._module_identity.items():
            if sys.modules.get(name) is not original:
                raise ProbeIsolationError(f"sealed module identity changed: {name}")
            if _sha256_file(Path(original.__file__).resolve()) != self._source_identity[name]:
                raise ProbeIsolationError(f"sealed module source changed: {name}")
        for symbol, code in self._code_identity.items():
            module_name, qualname = symbol.rsplit(".", 1)
            module = self._module_identity[module_name]
            if getattr(module, qualname).__code__ is not code:
                raise ProbeIsolationError(f"sealed function code changed: {symbol}")

    def verify_publish_boundary(self) -> None:
        self.verify_seal()
        if self.blocked_outcome_attempts:
            raise ProbeIsolationError("blocked outcome attempt preceded publish")
        if self.failed_check_attempts:
            raise ProbeIsolationError("failed check attempt preceded publish")
        if self.interpreter_mutation_attempts:
            raise ProbeIsolationError("interpreter mutation attempt preceded publish")
        if self.forbidden_subprocess_attempts:
            raise ProbeIsolationError("forbidden subprocess attempt preceded publish")


def _module_import_base(module_name: str, level: int, imported: str | None) -> str:
    package = module_name.split(".")[:-1]
    keep = len(package) - max(level - 1, 0)
    if keep < 0:
        raise StaticInventoryError(f"relative import escapes package: {module_name}")
    parts = package[:keep]
    if imported:
        parts.extend(imported.split("."))
    return ".".join(parts)


def _import_bindings(module_name: str, tree: ast.Module) -> tuple[dict[str, str], tuple[str, ...]]:
    bindings: dict[str, str] = {}
    issues: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                bindings[alias.asname or alias.name.split(".")[0]] = alias.name
        elif isinstance(node, ast.ImportFrom):
            if any(alias.name == "*" for alias in node.names):
                issues.append(f"star import at line {node.lineno}")
                continue
            base = _module_import_base(module_name, node.level, node.module)
            for alias in node.names:
                local = alias.asname or alias.name
                bindings[local] = f"{base}.{alias.name}" if base else alias.name
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            if value is None:
                continue
            resolved = _resolve_expr(value, bindings, module_name, frozenset())
            if resolved is not None:
                for target in targets:
                    if isinstance(target, ast.Name):
                        bindings[target.id] = resolved
    return bindings, tuple(issues)


def _resolve_expr(
    node: ast.AST,
    bindings: Mapping[str, str],
    module_name: str,
    local_functions: frozenset[str],
) -> str | None:
    if isinstance(node, ast.Name):
        if node.id in local_functions:
            return f"{module_name}.{node.id}"
        if node.id in {"__import__", "getattr", "globals", "vars"}:
            return f"builtins.{node.id}"
        return bindings.get(node.id)
    if isinstance(node, ast.Attribute):
        base = _resolve_expr(node.value, bindings, module_name, local_functions)
        return None if base is None else f"{base}.{node.attr}"
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "getattr"
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Constant)
        and type(node.args[1].value) is str
    ):
        base = _resolve_expr(node.args[0], bindings, module_name, local_functions)
        return None if base is None else f"{base}.{node.args[1].value}"
    if isinstance(node, ast.Subscript):
        base = _resolve_expr(node.value, bindings, module_name, local_functions)
        if base == "sys.modules" or (
            base is not None and base.startswith("sys.modules[")
        ):
            return f"{base}[]"
    if isinstance(node, ast.IfExp):
        body = _resolve_expr(node.body, bindings, module_name, local_functions)
        other = _resolve_expr(node.orelse, bindings, module_name, local_functions)
        if body is not None and other is not None:
            return f"conditional[{body}|{other}]"
    return None


def _split_source_lines(source: str) -> list[str]:
    """Split CR/LF source for use only with valid nodes from ``ast.parse``."""
    lines: list[str] = []
    start = 0
    index = 0
    while index < len(source):
        character = source[index]
        if character == "\n":
            index += 1
            lines.append(source[start:index])
            start = index
        elif character == "\r":
            index += 1
            if index < len(source) and source[index] == "\n":
                index += 1
            lines.append(source[start:index])
            start = index
        else:
            index += 1
    if start < len(source):
        lines.append(source[start:])
    return lines


def _get_source_segment(
    lines: Sequence[str], node: ast.AST, *, padded: bool = False,
) -> str | None:
    """Return text only for a valid location-bearing node from ``ast.parse``."""
    lineno = getattr(node, "lineno", None)
    col_offset = getattr(node, "col_offset", None)
    end_lineno = getattr(node, "end_lineno", None)
    end_col_offset = getattr(node, "end_col_offset", None)
    if None in (lineno, col_offset, end_lineno, end_col_offset):
        return None

    lineno -= 1
    end_lineno -= 1
    if lineno == end_lineno:
        return lines[lineno].encode("utf-8")[
            col_offset:end_col_offset
        ].decode("utf-8")

    padding = ""
    if padded:
        prefix = lines[lineno].encode("utf-8")[:col_offset].decode("utf-8")
        padding = "".join(
            character if character in "\t\f" else " "
            for character in prefix
        )
    first = padding + lines[lineno].encode("utf-8")[col_offset:].decode("utf-8")
    last = lines[end_lineno].encode("utf-8")[:end_col_offset].decode("utf-8")
    return "".join((first, *lines[lineno + 1:end_lineno], last))


class _FunctionCallVisitor(ast.NodeVisitor):
    def __init__(
        self,
        source_lines: Sequence[str],
        bindings: Mapping[str, str],
        module_name: str,
        local_functions: frozenset[str],
    ):
        self.source_lines = source_lines
        self.bindings = bindings
        self.module_name = module_name
        self.local_functions = local_functions
        self.local_bindings: dict[str, str] = {}
        self.unresolved_local_assignments: set[str] = set()
        self.guards: list[str] = []
        self.calls: list[_StaticCall] = []
        self.issues: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        return

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        return

    def visit_Lambda(self, node: ast.Lambda) -> None:
        return

    def visit_If(self, node: ast.If) -> None:
        guard = _get_source_segment(self.source_lines, node.test) or ast.unparse(node.test)
        self.guards.append(guard.strip())
        for child in node.body:
            self.visit(child)
        self.guards.pop()
        if node.orelse:
            self.guards.append(f"not ({guard.strip()})")
            for child in node.orelse:
                self.visit(child)
            self.guards.pop()

    def _bindings(self) -> dict[str, str]:
        return {**self.bindings, **self.local_bindings}

    def _bind_assignment(self, target: ast.AST, value: ast.AST) -> None:
        if not isinstance(target, ast.Name):
            return
        resolved = _resolve_expr(
            value, self._bindings(), self.module_name, self.local_functions,
        )
        if resolved is None:
            self.local_bindings.pop(target.id, None)
            self.unresolved_local_assignments.add(target.id)
        else:
            self.local_bindings[target.id] = resolved
            self.unresolved_local_assignments.discard(target.id)

    def visit_Assign(self, node: ast.Assign) -> None:
        self.visit(node.value)
        for target in node.targets:
            self._bind_assignment(target, node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None:
            self.visit(node.value)
            self._bind_assignment(node.target, node.value)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        self.visit(node.value)
        self._bind_assignment(node.target, node.value)

    def visit_Call(self, node: ast.Call) -> None:
        bindings = self._bindings()
        callee = _resolve_expr(
            node.func, bindings, self.module_name, self.local_functions,
        )
        if callee in {"builtins.__import__", "importlib.import_module"}:
            self.issues.append(f"dynamic import at line {node.lineno}")
        if callee == "builtins.getattr" and (
            len(node.args) < 2
            or not isinstance(node.args[1], ast.Constant)
            or type(node.args[1].value) is not str
        ):
            self.issues.append(f"non-literal getattr at line {node.lineno}")
        if callee is not None and callee.startswith("sys.modules["):
            self.issues.append(f"sys.modules callable at line {node.lineno}")
        if (
            callee is None
            and isinstance(node.func, ast.Name)
            and node.func.id in self.unresolved_local_assignments
        ):
            self.issues.append(
                f"unresolved local assignment callable {node.func.id} "
                f"at line {node.lineno}"
            )
        if isinstance(node.func, ast.Subscript) and (
            callee is None
            and (
                "globals()" in ast.unparse(node.func)
                or "vars()" in ast.unparse(node.func)
            )
        ):
            self.issues.append(f"dynamic namespace callable at line {node.lineno}")
        if callee is not None:
            self.calls.append(_StaticCall(callee, node.lineno, tuple(self.guards)))
        self.generic_visit(node)


def _analyze_source(module_name: str, relative_path: str, source: str) -> _StaticModule:
    path = _REPO_ROOT / relative_path
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        raise StaticInventoryError(f"cannot parse {relative_path}: {exc}") from exc
    source_lines = _split_source_lines(source)
    bindings, module_issues = _import_bindings(module_name, tree)
    defs = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    local_functions = frozenset(defs)
    functions: dict[str, _StaticFunction] = {}
    for name, node in defs.items():
        parameters = {
            argument.arg: f"parameter.{argument.arg}"
            for argument in (
                *node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs,
            )
        }
        if node.args.vararg is not None:
            parameters[node.args.vararg.arg] = f"parameter.{node.args.vararg.arg}"
        if node.args.kwarg is not None:
            parameters[node.args.kwarg.arg] = f"parameter.{node.args.kwarg.arg}"
        visitor = _FunctionCallVisitor(
            source_lines,
            {**bindings, **parameters},
            module_name,
            local_functions,
        )
        for child in node.body:
            visitor.visit(child)
        symbol = f"{module_name}.{name}"
        functions[symbol] = _StaticFunction(
            symbol=symbol, module=module_name, name=name, node=node,
            calls=tuple(visitor.calls), issues=tuple(visitor.issues),
        )
    return _StaticModule(
        name=module_name, path=path, relative_path=relative_path, source=source,
        tree=tree, imports=bindings, functions=functions, issues=module_issues,
    )


def _reject_import_side_effects(module: _StaticModule) -> None:
    forbidden = {
        "atexit.register", "signal.signal", "weakref.finalize",
        "threading.Thread.start", "Thread.start",
    }

    local_functions = {
        node.name: node
        for node in module.tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    active: set[str] = set()

    def resolved(node: ast.AST) -> str | None:
        return _resolve_expr(
            node, module.imports, module.name, frozenset(local_functions),
        )

    def reject_if_forbidden(node: ast.AST, *, decorator: bool = False) -> None:
        target = resolved(node.func) if isinstance(node, ast.Call) else resolved(node)
        text = ast.unparse(node.func if isinstance(node, ast.Call) else node)
        if (
            target in forbidden
            or text in forbidden
            or text.endswith(".start")
            or (decorator and target == "atexit.register")
        ):
            raise StaticInventoryError(
                f"import-time delayed effect is forbidden in {module.relative_path}:"
                f"{getattr(node, 'lineno', 0)}: {text}"
            )
        if target in {"builtins.__import__", "importlib.import_module"}:
            raise StaticInventoryError(
                f"import-time dynamic import prevents closed preflight in "
                f"{module.relative_path}:{getattr(node, 'lineno', 0)}"
            )

    def visit_function_body(name: str) -> None:
        if name in active:
            return
        active.add(name)
        try:
            for child in local_functions[name].body:
                visit_top(child)
        finally:
            active.remove(name)

    def visit_definition_header(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        for decorator in node.decorator_list:
            reject_if_forbidden(decorator, decorator=True)
            visit_top(decorator)
        for default in (*node.args.defaults, *node.args.kw_defaults):
            if default is not None:
                visit_top(default)

    def visit_top(node: ast.AST) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            visit_definition_header(node)
            return
        if isinstance(node, ast.Lambda):
            return
        if isinstance(node, ast.ClassDef):
            for decorator in node.decorator_list:
                reject_if_forbidden(decorator, decorator=True)
                visit_top(decorator)
            for child in (*node.bases, *node.keywords, *node.body):
                visit_top(child.value if isinstance(child, ast.keyword) else child)
            return
        if isinstance(node, ast.Call):
            reject_if_forbidden(node)
            callee = resolved(node.func)
            prefix = f"{module.name}."
            if callee is not None and callee.startswith(prefix):
                name = callee[len(prefix):]
                if name in local_functions:
                    visit_function_body(name)
        for child in ast.iter_child_nodes(node):
            visit_top(child)

    for top in module.tree.body:
        visit_top(top)


def _campaign_source_catalog() -> dict[str, str]:
    root = _REPO_ROOT / "orchestrator" / "campaign"
    catalog: dict[str, str] = {}
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(_REPO_ROOT)
        parts = list(relative.with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        name = ".".join(parts)
        catalog[name] = relative.as_posix()
    return catalog


def _static_import_dependencies(
    module: _StaticModule, catalog: Mapping[str, str],
) -> set[str]:
    dependencies: set[str] = set()

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            return

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            return

        def visit_Lambda(self, node: ast.Lambda) -> None:
            return

        def visit_If(self, node: ast.If) -> None:
            if isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
                return
            self.generic_visit(node)

        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                if alias.name in catalog:
                    dependencies.add(alias.name)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            base = _module_import_base(module.name, node.level, node.module)
            if base in catalog:
                dependencies.add(base)
            for alias in node.names:
                candidate = f"{base}.{alias.name}" if base else alias.name
                if candidate in catalog:
                    dependencies.add(candidate)

    Visitor().visit(module.tree)
    return dependencies


def _load_static_modules() -> dict[str, _StaticModule]:
    catalog = _campaign_source_catalog()
    missing = sorted(set(_RUNTIME_IMPORT_ROOTS) - set(catalog))
    if missing:
        raise StaticInventoryError(f"runtime import roots have no source: {missing}")
    result: dict[str, _StaticModule] = {}
    queue = list(_RUNTIME_IMPORT_ROOTS)
    while queue:
        name = queue.pop(0)
        if name in result:
            continue
        relative = catalog[name]
        path = _REPO_ROOT / relative
        source = path.read_text(encoding="utf-8")
        module = _analyze_source(name, relative, source)
        result[name] = module
        queue.extend(sorted(_static_import_dependencies(module, catalog) - set(result)))
    for module in result.values():
        _reject_import_side_effects(module)
    return result


def _static_module_manifest(
    modules: Mapping[str, _StaticModule],
) -> list[dict[str, str]]:
    return [
        {
            "module": name,
            "path": module.relative_path,
            "source_sha256": _sha256_bytes(module.source.encode("utf-8")),
        }
        for name, module in sorted(modules.items())
    ]


def _all_functions(modules: Mapping[str, _StaticModule]) -> dict[str, _StaticFunction]:
    return {
        symbol: function
        for module in modules.values()
        for symbol, function in module.functions.items()
    }


def _proof_switchpoint(
    modules: Mapping[str, _StaticModule], spec: DriverSpec,
) -> dict[str, object]:
    functions = _all_functions(modules)
    entry = f"{spec.module}.main"
    middle = f"{spec.module}.drive_iteration"
    required = (entry, middle, _SWITCHPOINT)
    for symbol in required[:-1]:
        if symbol not in functions:
            raise StaticInventoryError(f"required proof symbol is absent: {symbol}")
    path: list[dict[str, object]] = []
    conditional: list[dict[str, object]] = []
    proof_symbols = (entry, middle)
    target_pairs = ((entry, middle), (middle, _SWITCHPOINT))
    for caller, callee in target_pairs:
        function = functions[caller]
        issues = (*modules[function.module].issues, *function.issues)
        if issues:
            raise StaticInventoryError(
                f"unresolved binding entered proof path {caller}: {issues}"
            )
        matches = [edge for edge in function.calls if edge.callee == callee]
        if not matches:
            raise StaticInventoryError(f"required static edge is absent: {caller} -> {callee}")
        edge = matches[0]
        path.append({
            "caller": caller,
            "callee": callee,
            "path": modules[function.module].relative_path,
            "line": edge.line,
            "guards": list(edge.guards),
        })
        conditional.extend({
            "caller": caller,
            "callee": callee,
            "path": modules[function.module].relative_path,
            "line": edge.line,
            "guard": guard,
        } for guard in edge.guards)
    return {
        "entrypoint": entry,
        "reachable": True,
        "path": path,
        "conditional_edges": conditional,
        "ambiguous_bindings": [],
        "evidence_kind": (
            "static candidate-main path + probe direct call to the real switchpoint"
        ),
        "runtime_candidate_main_passage_claimed": False,
        "proof_symbols": list(proof_symbols),
    }


def _reason_paths(
    functions: Mapping[str, _StaticFunction], seeds: Sequence[str],
) -> dict[str, tuple[str, ...]]:
    reverse: dict[str, set[str]] = {}
    for caller, function in functions.items():
        for edge in function.calls:
            reverse.setdefault(edge.callee, set()).add(caller)
    reasons: dict[str, tuple[str, ...]] = {}
    queue: list[tuple[str, tuple[str, ...]]] = []
    for seed in seeds:
        if seed not in functions:
            raise StaticInventoryError(f"generation seed is absent: {seed}")
        queue.append((seed, (seed,)))
    while queue:
        symbol, reason = queue.pop(0)
        previous = reasons.get(symbol)
        if previous is not None and (len(previous), previous) <= (len(reason), reason):
            continue
        reasons[symbol] = reason
        for caller in sorted(reverse.get(symbol, ())):
            queue.append((caller, (caller, *reason)))
    return reasons


def _runtime_function(runtime_modules: Mapping[str, ModuleType], symbol: str):
    module_name, name = symbol.rsplit(".", 1)
    try:
        module = runtime_modules[module_name]
        function = getattr(module, name)
    except (KeyError, AttributeError) as exc:
        raise StaticInventoryError(f"runtime symbol cannot be resolved: {symbol}") from exc
    if not inspect.isfunction(function):
        raise StaticInventoryError(f"inventory symbol is not a Python function: {symbol}")
    return function


def _build_inventory(
    static_modules: Mapping[str, _StaticModule],
    runtime_modules: Mapping[str, ModuleType],
    *, seeds: Sequence[str] = _GENERATION_SEEDS,
) -> list[dict[str, object]]:
    functions = _all_functions(static_modules)
    reasons = _reason_paths(functions, seeds)
    inventory: list[dict[str, object]] = []
    for symbol in sorted(reasons):
        module_name, qualname = symbol.rsplit(".", 1)
        static = static_modules[module_name]
        issues = (*static.issues, *functions[symbol].issues)
        if issues:
            raise StaticInventoryError(
                f"unresolved binding entered generation inventory {symbol}: {issues}"
            )
        function = _runtime_function(runtime_modules, symbol)
        inventory.append({
            "module": module_name,
            "qualname": qualname,
            "path": static.relative_path,
            "firstlineno": function.__code__.co_firstlineno,
            "code_sha256": _sha256_bytes(marshal.dumps(function.__code__)),
            "reason_path": list(reasons[symbol]),
        })
    return inventory


def _require_single_main_thread(label: str) -> None:
    live = threading.enumerate()
    current = threading.current_thread()
    if (
        len(live) != 1
        or live[0] is not current
        or current is not threading.main_thread()
    ):
        raise ProbeIsolationError(
            f"{label} requires a fresh single-main-thread process"
        )


def _load_runtime(
    guard: _ProcessGuard,
    static_modules: Mapping[str, _StaticModule] | None = None,
) -> _Runtime:
    _require_single_main_thread("campaign import preflight")
    preflight = dict(
        _load_static_modules() if static_modules is None else static_modules
    )
    before_threads = {id(thread) for thread in threading.enumerate()}
    modules = {
        name: importlib.import_module(name)
        for name in preflight
    }
    for name, module in modules.items():
        if _sha256_file(Path(module.__file__).resolve()) != _sha256_bytes(
            preflight[name].source.encode("utf-8")
        ):
            raise StaticInventoryError(
                f"campaign source changed between preflight and import: {name}"
            )
    L = modules[f"{_CAMPAIGN_PACKAGE}.p3_s4_loop"]
    sort = modules[f"{_CAMPAIGN_PACKAGE}.p3_s4_loop_sort"]
    trigger = modules[f"{_CAMPAIGN_PACKAGE}.p3_s4_loop_trigger_gating"]
    # Resolve sanctioned-path lazy imports before the dynamic-code seal.
    L.default_cfg(reflux=True)
    L.default_cfg(reflux=False)
    sort.default_cfg(reflux=True)
    sort.default_cfg(reflux=False)
    trigger_on = trigger.default_cfg(reflux=True)
    trigger_off = trigger.default_cfg(reflux=False)
    trigger._campaign_cfg_for_site(trigger_on, trigger.site_policy.OTHER)
    trigger._campaign_cfg_for_site(trigger_off, trigger.site_policy.OTHER)
    artifact_admission = modules[f"{_CAMPAIGN_PACKAGE}.artifact_admission"]
    build_admission = modules[f"{_CAMPAIGN_PACKAGE}.build_admission"]
    env_contract = modules[f"{_CAMPAIGN_PACKAGE}.env_contract"]
    contract_loader_binding = modules[
        f"{_CAMPAIGN_PACKAGE}.contract_loader_binding"
    ]
    campaign_lock = modules[f"{_CAMPAIGN_PACKAGE}.campaign_lock"]
    ident = modules[f"{_CAMPAIGN_PACKAGE}.ident"]
    site_policy = modules[f"{_CAMPAIGN_PACKAGE}.site_policy"]
    loader_binding = contract_loader_binding.capture_contract_loader_binding()
    activation_state = env_contract.verified_current_activation_state()
    head = loader_binding.contract_loader_commit
    after_threads = {id(thread) for thread in threading.enumerate()}
    if after_threads != before_threads:
        raise StaticInventoryError("campaign imports changed the live thread census")
    drivers = {
        name: DriverSpec(name, module_name, _MODULE_RELATIVE_PATHS[module_name])
        for name, module_name in _DRIVER_MODULES.items()
    }
    return _Runtime(
        modules=modules, drivers=drivers, L=L, sort=sort, trigger=trigger,
        pipeline=modules[f"{_CAMPAIGN_PACKAGE}.pipeline"], ident=ident,
        artifact_admission=artifact_admission, build_admission=build_admission,
        env_contract=env_contract, campaign_lock=campaign_lock,
        contract_loader_binding=contract_loader_binding,
        site_policy=site_policy, loader_binding=loader_binding,
        activation_state=activation_state,
        thread_count_before_imports=len(before_threads),
        thread_count_at_seal=len(after_threads),
        repository_head=head,
    )


def _bind_workspace_issuer():
    issuer_token = object()
    issued: dict[object, tuple[str, int]] = {}

    class _ProbeWorkspace:
        __slots__ = ("_nonce", "realpath")

        def __init__(self, realpath: str, token: object):
            if token is not issuer_token:
                raise TypeError("probe workspace is issuer-only")
            nonce = object()
            issued[nonce] = (realpath, os.getpid())
            self._nonce = nonce
            self.realpath = realpath

        def verify(self) -> Path:
            try:
                realpath, pid = issued[self._nonce]
            except (AttributeError, KeyError, TypeError) as exc:
                raise ProbeIsolationError("workspace capability is not issuer-backed") from exc
            if type(self) is not _ProbeWorkspace or pid != os.getpid() or realpath != self.realpath:
                raise ProbeIsolationError("workspace capability identity changed")
            return Path(realpath)

    def issue(realpath: str):
        return _ProbeWorkspace(realpath, issuer_token)

    return _ProbeWorkspace, issue


_ProbeWorkspace, _new_workspace_capability = _bind_workspace_issuer()


def _issue_probe_workspace() -> object:
    protected = _protected_campaign_roots()
    temp_parent = _resolved(tempfile.gettempdir())
    if _is_relative_to(temp_parent, _REPO_ROOT) or any(
        _is_relative_to(temp_parent, root) for root in protected
    ):
        raise ProbeIsolationError("ambient temporary root overlaps repository/campaign roots")
    raw = tempfile.mkdtemp(prefix="izanagi-p3-b4-probe-")
    try:
        path = _resolved(raw)
        _assert_no_symlink_components(path, allow_missing_tail=False)
        info = path.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid():
            raise ProbeIsolationError("issued workspace ownership/type is invalid")
        if _is_relative_to(path, _REPO_ROOT) or any(
            _paths_overlap(path, root) for root in protected
        ):
            raise ProbeIsolationError("issued workspace overlaps repository/campaign roots")
        return _new_workspace_capability(str(path))
    except BaseException as primary:
        try:
            shutil.rmtree(raw)
        except FileNotFoundError:
            pass
        except BaseException as cleanup:
            raise primary from cleanup
        raise


def _layout_for_workspace(workspace: object):
    if type(workspace) is not _ProbeWorkspace:
        raise ProbeIsolationError("layout requires exact issued workspace capability")
    root = workspace.verify()
    fixture = root / "fixture"
    _assert_no_symlink_components(fixture, allow_missing_tail=True)
    resolved_fixture = _resolved(fixture)
    if resolved_fixture != fixture or fixture.parent != root:
        raise ProbeIsolationError("fixture layout escaped issued workspace")
    runtime = _require_active_runtime()
    layout_module = importlib.import_module(f"{_CAMPAIGN_PACKAGE}.layout")
    layout = layout_module.CampaignLayout(root=str(fixture))
    if type(layout) is not layout_module.CampaignLayout:
        raise ProbeIsolationError("fixture layout type is not exact CampaignLayout")
    return layout


def _typed_fixture_value(annotation: object, field_name: str) -> object:
    if annotation in {str, "str"}:
        if field_name == "reason":
            return _FIXTURE_MARKER
        return f"p3-b4-probe-type-generated:{field_name}"
    if annotation in {dict[str, int], "dict[str, int]"}:
        return {"PROBE_RESERVED": 1}
    raise ProbeIsolationError(f"fixture type has no generator: {annotation!r}")


@dataclass(frozen=True)
class _FixtureShape:
    source_rel: str
    implementation: str
    reason: str
    flags: dict[str, int]


_FORBIDDEN_FIXTURE_FIELDS = frozenset({
    "fitness", "fitness_tps", "throughput", "performance", "receipt",
    "receipt_sha256", "campaign_id", "campaign_path", "wal_sha256",
})


def _fixture_payload_from_types() -> dict[str, object]:
    fields = {
        name: _typed_fixture_value(field.type, name)
        for name, field in _FixtureShape.__dataclass_fields__.items()
    }
    return {
        "schema_version": _FIXTURE_SCHEMA,
        "marker": _FIXTURE_MARKER,
        **fields,
    }


def _validate_fixture_payload(payload: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(payload, Mapping):
        raise ProbeIsolationError("fixture payload must be a mapping")

    def reject_forbidden(value: object) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                if type(key) is not str:
                    raise ProbeIsolationError("fixture keys must be exact strings")
                if key.lower() in _FORBIDDEN_FIXTURE_FIELDS:
                    raise ProbeIsolationError(f"fixture field is forbidden: {key}")
                reject_forbidden(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                reject_forbidden(child)

    reject_forbidden(payload)
    required = {
        "schema_version", "marker", "source_rel", "implementation", "reason", "flags",
    }
    if not required <= set(payload):
        raise ProbeIsolationError("fixture payload lacks generated schema fields")
    if payload["schema_version"] != _FIXTURE_SCHEMA or payload["marker"] != _FIXTURE_MARKER:
        raise ProbeIsolationError("fixture reservation marker/schema differs")
    if type(payload["flags"]) is not dict or payload["flags"] != {"PROBE_RESERVED": 1}:
        raise ProbeIsolationError("fixture flags are not the type-generated reservation")
    for key in ("source_rel", "implementation"):
        if (
            type(payload[key]) is not str
            or not str(payload[key]).startswith("p3-b4-probe-type-generated:")
        ):
            raise ProbeIsolationError(f"fixture {key} is not type-generated")
    if payload["reason"] != _FIXTURE_MARKER:
        raise ProbeIsolationError("fixture reason is not the reserved marker")
    return dict(payload)


def _record_probe_diff_reject(
    workspace: object,
    layout: object,
    payload: Mapping[str, object],
    *,
    backoff_grammar_version: int | None = None,
) -> str:
    runtime = _require_active_runtime()
    expected = _layout_for_workspace(workspace)
    if type(layout) is not type(expected) or _resolved(layout.root) != _resolved(expected.root):
        raise ProbeIsolationError("record_diff_reject layout is not the issued workspace")
    checked = _validate_fixture_payload(payload)
    genome_module = importlib.import_module(f"{_CAMPAIGN_PACKAGE}.model")
    diff_module = importlib.import_module(f"{_CAMPAIGN_PACKAGE}.diff_quarantine")
    genome = genome_module.Genome("probe-reserved-suite", checked["flags"])
    digest = {
        "rejection_type": "diff-quarantine",
        "subtype": "hole-escape",
        "reason": checked["reason"],
        "diff_region": checked["source_rel"],
        "template_diff_id": "p3-b4-probe-type-generated:template",
        "evidence": "probe-type-generated",
    }
    rejection = diff_module.DiffQuarantineResult(
        passed=False,
        subtype=diff_module.DiffRejectSubtype.HOLE_ESCAPE,
        reason=checked["reason"],
        digest=digest,
        violations=[digest],
    )
    return runtime.L.record_diff_reject(
        layout, genome, checked["implementation"], rejection,
        backoff_grammar_version=backoff_grammar_version,
    )


_ACTIVE_RUNTIME: _Runtime | None = None
_VIEW_WORKSPACES: dict[int, tuple[object, object, object]] = {}
_MAIN_CLAIMED = False


def _claim_fresh_dedicated_process() -> None:
    global _MAIN_CLAIMED
    if _MAIN_CLAIMED:
        raise ProbeIsolationError("probe main may run only once in its interpreter")
    _require_single_main_thread("probe main")
    thread_profile = getattr(threading, "getprofile", lambda: None)()
    if sys.getprofile() is not None or thread_profile is not None:
        raise ProbeIsolationError("probe main requires an unprofiled fresh process")
    _MAIN_CLAIMED = True


def _require_active_runtime() -> _Runtime:
    if _ACTIVE_RUNTIME is None:
        raise ProbeIsolationError("probe runtime is not active")
    return _ACTIVE_RUNTIME


def _make_probe_view():
    """Return an exact CertifiedCampaignView from a zero-argument private factory."""
    runtime = _require_active_runtime()
    workspace = _issue_probe_workspace()
    layout = None
    try:
        layout = _layout_for_workspace(workspace)
        layout.ensure()
        context = runtime.build_admission.build_run_context(
            generator_id=runtime.build_admission.GeneratorId.BACKOFF_SWEEP,
        )
        cfg = runtime.L.default_cfg(reflux=False)
        backoff_grammar_version = runtime.L._require_backoff_grammar_version(cfg)
        if cfg.search_config.get("build_admission") != context.policy.as_preimage():
            raise ProbeIsolationError("fixture config is not bound to current admission policy")
        binding = runtime.loader_binding
        activation = runtime.activation_state
        contract = cfg.bound_environment_contract
        lock_text = runtime.campaign_lock.encode_campaign_lock_v2(
            runtime.ident.canonical_preimage(cfg),
            runtime.campaign_lock.CampaignLockAuthority(
                environment_contract_sha256=contract.contract_sha256,
                activation_serial=activation.activation_serial,
                activation_state_sha256=activation.activation_state_sha256,
                contract_loader_commit=binding.contract_loader_commit,
                contract_loader_blob_sha256s=dict(
                    binding.contract_loader_blob_sha256s
                ),
            ),
        )
        runtime.L.wal.write_lock(layout, lock_text)
        _record_probe_diff_reject(
            workspace,
            layout,
            _fixture_payload_from_types(),
            backoff_grammar_version=backoff_grammar_version,
        )
        view = runtime.artifact_admission.require_admitted_campaign(
            layout,
            purpose=runtime.artifact_admission.CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
        )
        if type(view) is not runtime.artifact_admission.CertifiedCampaignView:
            raise ProbeIsolationError("admission did not issue exact CertifiedCampaignView")
        _VIEW_WORKSPACES[id(view)] = (view, workspace, layout)
        return view
    except BaseException as primary:
        try:
            shutil.rmtree(workspace.verify())
        except FileNotFoundError:
            pass
        except BaseException as cleanup:
            raise primary from cleanup
        raise


def _release_probe_view(view: object) -> tuple[str, str]:
    try:
        registered, workspace, layout = _VIEW_WORKSPACES.pop(id(view))
    except KeyError as exc:
        raise ProbeIsolationError("probe view has no issued workspace") from exc
    if registered is not view:
        raise ProbeIsolationError("probe view registry identity changed")
    workspace_path = workspace.verify()
    layout_path = _resolved(layout.root)
    workspace_hash = _sha256_bytes(str(workspace_path).encode("utf-8"))
    layout_hash = _sha256_bytes(str(layout_path).encode("utf-8"))
    shutil.rmtree(workspace_path)
    if workspace_path.exists():
        raise ProbeIsolationError("issued workspace survived cleanup")
    return workspace_hash, layout_hash


def _driver_module(runtime: _Runtime, name: str) -> ModuleType:
    return runtime.modules[runtime.drivers[name].module]


def _check_switchpoint(ctx: _CheckContext) -> dict[str, object]:
    L = ctx.runtime.L
    projection = L.make_critic_identity_projection(ctx.view)
    before = ctx.guard.count(L.make_critic_digest)
    L.make_critic_digest(
        ctx.view, tag="p3-b4-probe", reflux=True,
        identity_projection=projection,
    )
    L.make_critic_digest(
        ctx.view, tag="p3-b4-probe", reflux=False,
        identity_projection=projection,
    )
    calls = ctx.guard.count(L.make_critic_digest) - before
    dynamic = {
        "callable": _SWITCHPOINT,
        "path": _MODULE_RELATIVE_PATHS[f"{_CAMPAIGN_PACKAGE}.p3_s4_loop"],
        "line": L.make_critic_digest.__code__.co_firstlineno,
        "code_sha256": _sha256_bytes(marshal.dumps(L.make_critic_digest.__code__)),
        "call_count": calls,
        "reflux_values": [True, False],
    }
    return {
        "passed": bool(ctx.static_switchpoint["reachable"]) and calls == 2,
        "static": dict(ctx.static_switchpoint),
        "dynamic": dynamic,
    }


def _check_on_red(ctx: _CheckContext) -> dict[str, object]:
    L = ctx.runtime.L
    text = L.make_critic_digest(
        ctx.view, tag="p3-b4-probe", reflux=True,
        identity_projection=L.make_critic_identity_projection(ctx.view),
    )
    occurrences = text.count(_FIXTURE_MARKER)
    heading = _REJECTION_HEADING in text
    return {
        "passed": occurrences == 1 and heading,
        "marker_occurrences": occurrences,
        "rejection_heading_present": heading,
        "digest_sha256": _sha256_bytes(text.encode("utf-8")),
    }


def _check_off_controls(ctx: _CheckContext) -> dict[str, object]:
    L = ctx.runtime.L
    loaders = (
        L.load_rejections,
        L.load_liveness_rejections,
        L.load_verify_abort_signals,
        L.load_diff_rejections,
    )
    before_on = {function.__name__: ctx.guard.count(function) for function in loaders}
    projection = L.make_critic_identity_projection(ctx.view)
    on = L.make_critic_digest(
        ctx.view, tag="p3-b4-probe", reflux=True,
        identity_projection=projection,
    )
    after_on = {function.__name__: ctx.guard.count(function) for function in loaders}
    before_off = dict(after_on)
    off = L.make_critic_digest(
        ctx.view, tag="p3-b4-probe", reflux=False,
        identity_projection=projection,
    )
    after_off = {function.__name__: ctx.guard.count(function) for function in loaders}
    on_calls = {name: after_on[name] - before_on[name] for name in before_on}
    off_calls = {name: after_off[name] - before_off[name] for name in before_off}
    green = L.render_text([L.build_digest("p3-b4-probe", {}, ctx.view)])
    byte_equal = off.encode("utf-8") == green.encode("utf-8")
    on_headings = _REJECTION_HEADING in on and _ABORT_HEADING in on
    off_headings_absent = _REJECTION_HEADING not in off and _ABORT_HEADING not in off
    return {
        "passed": (
            all(value == 1 for value in on_calls.values())
            and all(value == 0 for value in off_calls.values())
            and byte_equal and on_headings and off_headings_absent
        ),
        "on_loader_calls": on_calls,
        "off_loader_calls": off_calls,
        "green_sha256": _sha256_bytes(green.encode("utf-8")),
        "off_sha256": _sha256_bytes(off.encode("utf-8")),
        "off_equals_green_bytes": byte_equal,
        "on_headings_present": on_headings,
        "off_headings_absent": off_headings_absent,
    }


def _cfg_without_reflux(cfg: object) -> dict[str, object]:
    return {
        **vars(cfg),
        "search_config": {
            key: value
            for key, value in cfg.search_config.items()
            if key != "reflux"
        },
    }


def _identity_preimage_sha256(runtime: _Runtime, cfg: object, preimage: str) -> str:
    digest = _sha256_bytes(
        _IDENTITY_PREIMAGE_DOMAIN + preimage.encode("utf-8")
    )
    if digest[:8] == runtime.ident.cfg_hash(cfg):
        raise ProbeIsolationError(
            "domain-separated preimage hash exposed the campaign cfg locator"
        )
    return digest


def _identity_pair_from_cfgs(
    runtime: _Runtime, on: object, off: object,
) -> dict[str, object]:
    on_preimage = runtime.ident.canonical_preimage(on)
    off_preimage = runtime.ident.canonical_preimage(off)
    only_reflux = _cfg_without_reflux(on) == _cfg_without_reflux(off)
    return {
        "on_reflux": on.search_config["reflux"],
        "off_reflux": off.search_config["reflux"],
        "only_reflux_differs": only_reflux,
        "preimage_hash_domain": _IDENTITY_PREIMAGE_DOMAIN[:-1].decode("ascii"),
        "on_preimage_sha256": _identity_preimage_sha256(
            runtime, on, on_preimage,
        ),
        "off_preimage_sha256": _identity_preimage_sha256(
            runtime, off, off_preimage,
        ),
        "domain_separated_from_campaign_locator": True,
        "different": on_preimage != off_preimage,
    }


def _identity_pair(runtime: _Runtime, driver: ModuleType) -> dict[str, object]:
    return _identity_pair_from_cfgs(
        runtime, driver.default_cfg(reflux=True), driver.default_cfg(reflux=False),
    )


def _check_identity(ctx: _CheckContext) -> dict[str, object]:
    driver = _driver_module(ctx.runtime, ctx.spec.name)
    raw = _identity_pair(ctx.runtime, driver)
    projected: dict[str, object] | None = None
    if ctx.spec.name == "trigger":
        site = driver._current_site()
        execution_guard = ctx.runtime.modules[
            f"{_CAMPAIGN_PACKAGE}.execution_guard"
        ]
        try:
            contract = driver._admit_env_contract(site)
            on = driver.default_cfg(reflux=True)
            off = driver.default_cfg(reflux=False)
            on = driver._campaign_cfg_for_site(on, site, _contract=contract)
            off = driver._campaign_cfg_for_site(off, site, _contract=contract)
            context = ctx.runtime.build_admission.build_run_context(
                generator_id=(
                    ctx.runtime.build_admission.GeneratorId.S8A_TRIGGER_SWEEP
                ),
            )
            on = ctx.runtime.ident.bind_admission_policy(on, context.policy)
            off = ctx.runtime.ident.bind_admission_policy(off, context.policy)
        except execution_guard.ExecutionGuardError as exc:
            projected = {
                "status": "not_measured",
                "site": site,
                "reason": str(exc),
            }
        else:
            projected = {
                "status": "measured",
                "site": site,
                **_identity_pair_from_cfgs(ctx.runtime, on, off),
            }
    passed = bool(raw["only_reflux_differs"] and raw["different"])
    if projected is not None and projected["status"] == "measured":
        passed = passed and bool(
            projected["only_reflux_differs"] and projected["different"]
        )
    return {"passed": passed, "raw_cfg": raw, "site_projected_cfg": projected}


_CHECKS: tuple[tuple[str, Callable[[_CheckContext], Mapping[str, object]]], ...] = (
    ("static_candidate_plus_direct_switchpoint_call", _check_switchpoint),
    ("on_red_details", _check_on_red),
    ("off_negative_controls", _check_off_controls),
    ("campaign_identity", _check_identity),
)


def _interdiction_report(guard: object, observations: Mapping[str, bool]) -> dict[str, object]:
    return {
        "profile_hook_active": bool(guard.profile_active()),
        "audit_hook_active": bool(observations["audit_hook_active"]),
        "window": {
            "opened_before_campaign_imports": bool(
                observations["opened_before_campaign_imports"]
            ),
            "sealed_before_checks": bool(observations["sealed_before_checks"]),
            "active_during_json_publish": observations.get(
                "active_during_json_publish"
            ),
            "active_during_sha256_publish": observations.get(
                "active_during_sha256_publish"
            ),
        },
    }


def _validate_evidence_target(driver: str, evidence_set_id: str) -> tuple[Path, Path]:
    if _EVIDENCE_SET_RE.fullmatch(evidence_set_id) is None:
        raise ProbeIsolationError("evidence-set-id must be a bounded lowercase slug")
    root = _resolved(_EVIDENCE_ROOT)
    protected = _protected_campaign_roots()
    if any(_paths_overlap(root, campaign_root) for campaign_root in protected):
        raise ProbeIsolationError("evidence root overlaps a campaign root")
    _assert_no_symlink_components(root, allow_missing_tail=True)
    directory = root / evidence_set_id
    json_path = directory / f"{driver}.json"
    sidecar = directory / f"{driver}.json.sha256"
    _assert_no_symlink_components(directory, allow_missing_tail=True)
    if json_path.exists() or json_path.is_symlink() or sidecar.exists() or sidecar.is_symlink():
        raise ProbeIsolationError("evidence target already exists")
    return json_path, sidecar


def _publish_evidence(
    guard: _ProcessGuard, value: dict[str, object], json_path: Path, sidecar: Path,
) -> str:
    guard.verify_publish_boundary()
    interdiction = value.get("interdiction")
    if not isinstance(interdiction, dict) or not isinstance(
        interdiction.get("window"), dict
    ):
        raise ProbeIsolationError("evidence publish window is not mutable")
    window = interdiction["window"]
    # The values are observations at the opening of the real publication
    # window.  Every write/link boundary below is observed again; a false later
    # observation rolls both published names back, so a surviving evidence file
    # represents the conjunction of the opening and all exact boundaries.
    window["active_during_json_publish"] = guard.publish_boundary_active(
        "json-publish-window-open"
    )
    window["active_during_sha256_publish"] = guard.publish_boundary_active(
        "sha256-publish-window-open"
    )
    _validate_evidence_schema(value)
    directory = json_path.parent
    guard.publish_boundary_active("directory-create-before")
    directory.mkdir(parents=True, exist_ok=True)
    guard.publish_boundary_active("directory-create-after")
    _assert_no_symlink_components(directory, allow_missing_tail=False)
    payload = _canonical_bytes(value)
    digest = _sha256_bytes(payload)
    nonce = secrets.token_hex(12)
    temporary_json = directory / f".{json_path.name}.{nonce}.tmp"
    temporary_side = directory / f".{sidecar.name}.{nonce}.tmp"
    try:
        guard.publish_boundary_active("json-write-before")
        with temporary_json.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        guard.publish_boundary_active("json-write-after")
        guard.publish_boundary_active("sha256-write-before")
        with temporary_side.open("xb") as stream:
            stream.write(f"{digest}  {json_path.name}\n".encode("ascii"))
            stream.flush()
            os.fsync(stream.fileno())
        guard.publish_boundary_active("sha256-write-after")
        guard.publish_boundary_active("sha256-link-before")
        os.link(temporary_side, sidecar)
        guard.publish_boundary_active("sha256-link-after")
        guard.publish_boundary_active("json-link-before")
        os.link(temporary_json, json_path)
        guard.publish_boundary_active("json-link-after")
        directory_fd = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        for target in (json_path, sidecar):
            try:
                target.unlink()
            except FileNotFoundError:
                pass
        raise
    finally:
        for temporary in (temporary_json, temporary_side):
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
    guard.publish_boundary_active("publish-window-closed")
    return digest


def _require_exact_keys(value: object, expected: set[str], label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != expected:
        got = sorted(value) if isinstance(value, Mapping) else type(value).__name__
        raise ProbeIsolationError(
            f"evidence {label} key set differs: expected={sorted(expected)} got={got}"
        )
    return value


def _validate_evidence_schema(value: Mapping[str, object]) -> None:
    top = _require_exact_keys(value, {
        "schema_version", "evidence_class", "sanctioned_entrypoint", "run",
        "claim", "source", "admission_reads", "isolation", "interdiction",
        "checks", "result",
    }, "top-level")
    if (
        top["schema_version"] != SCHEMA_VERSION
        or top["evidence_class"] != EVIDENCE_CLASS
        or top["sanctioned_entrypoint"] != SANCTIONED_ENTRYPOINT
    ):
        raise ProbeIsolationError("evidence identity constants differ")
    _require_exact_keys(top["run"], {
        "driver", "axis", "evidence_set_id", "argv", "started_at_utc",
        "completed_at_utc", "python_version",
    }, "run")
    claim = _require_exact_keys(top["claim"], {
        "evidence_kind", "runtime_candidate_main_passage_claimed",
    }, "claim")
    if claim != {
        "evidence_kind": (
            "static candidate-main path + probe direct call to the real switchpoint"
        ),
        "runtime_candidate_main_passage_claimed": False,
    }:
        raise ProbeIsolationError("top-level evidence claim is broader than implemented")
    _require_exact_keys(top["source"], {
        "repository_head", "probe_path", "probe_sha256", "driver_path",
        "driver_sha256", "base_driver_path", "base_driver_sha256",
    }, "source")
    admission = _require_exact_keys(top["admission_reads"], {
        "reads", "classification", "other_campaign_artifact_reads", "audit_basis",
    }, "admission_reads")
    reads = admission["reads"]
    if not isinstance(reads, list) or len(reads) != 1:
        raise ProbeIsolationError("evidence admission read set is not singleton")
    _require_exact_keys(reads[0], {"path", "sha256"}, "admission_reads.read")
    isolation = _require_exact_keys(top["isolation"], {
        "kind", "workspace_realpath_sha256", "layout_realpath_sha256",
        "outside_repository", "outside_resolved_campaign_roots",
        "workspace_removed_before_publish", "protected_read_attempts",
        "protected_write_attempts",
    }, "isolation")
    interdiction = _require_exact_keys(top["interdiction"], {
        "authority", "generation_seeds", "generation_scope",
        "generation_scope_exclusion", "viewing_scope", "inventory",
        "inventory_sha256", "analyzed_modules", "analyzed_modules_sha256",
        "profile_hook_active", "audit_hook_active", "window",
        "blocked_outcome_attempts", "forbidden_subprocess_attempts",
        "failed_check_attempts", "interpreter_mutation_attempts",
        "allowed_read_only_git", "seal_scope", "thread_census", "scope_limit",
    }, "interdiction")
    analyzed = interdiction["analyzed_modules"]
    if not isinstance(analyzed, list) or not analyzed:
        raise ProbeIsolationError("evidence analyzed module manifest is empty")
    analyzed_names: list[str] = []
    for row in analyzed:
        item = _require_exact_keys(
            row, {"module", "path", "source_sha256"},
            "interdiction.analyzed_modules entry",
        )
        if (
            type(item["module"]) is not str
            or type(item["path"]) is not str
            or type(item["source_sha256"]) is not str
            or _HEX64_RE.fullmatch(item["source_sha256"]) is None
        ):
            raise ProbeIsolationError("evidence analyzed module entry is malformed")
        analyzed_names.append(item["module"])
    if analyzed_names != sorted(set(analyzed_names)):
        raise ProbeIsolationError("evidence analyzed module set is not exact/sorted")
    if interdiction["analyzed_modules_sha256"] != _sha256_bytes(
        _canonical_bytes(analyzed).rstrip(b"\n")
    ):
        raise ProbeIsolationError("evidence analyzed module manifest hash differs")
    _require_exact_keys(interdiction["window"], {
        "opened_before_campaign_imports", "sealed_before_checks",
        "active_during_json_publish", "active_during_sha256_publish",
    }, "interdiction.window")
    checks = _require_exact_keys(top["checks"], {
        "static_candidate_plus_direct_switchpoint_call", "on_red_details",
        "off_negative_controls",
        "campaign_identity",
    }, "checks")
    _require_exact_keys(top["result"], {
        "passed", "pass_rule", "preregistration_effect",
    }, "result")
    if not all(check.get("passed") is True for check in checks.values()):
        raise ProbeIsolationError("evidence contains a failed check")
    if not all(interdiction[key] is True for key in (
        "profile_hook_active", "audit_hook_active",
    )):
        raise ProbeIsolationError("evidence hook observation is false")
    if not all(interdiction["window"].values()):
        raise ProbeIsolationError("evidence window observation is false")
    if (
        admission["other_campaign_artifact_reads"] != 0
        or isolation["protected_read_attempts"] != 0
        or isolation["protected_write_attempts"] != 0
        or interdiction["blocked_outcome_attempts"] != []
        or interdiction["failed_check_attempts"] != []
        or interdiction["forbidden_subprocess_attempts"] != 0
        or interdiction["interpreter_mutation_attempts"] != []
    ):
        raise ProbeIsolationError("evidence violation ledger is non-empty")
    serialized_identity = json.dumps(
        checks["campaign_identity"], sort_keys=True, separators=(",", ":"),
    )
    if "campaign_id" in serialized_identity:
        raise ProbeIsolationError("raw campaign locator leaked into identity evidence")
    for digest in (
        top["source"]["probe_sha256"], top["source"]["driver_sha256"],
        top["source"]["base_driver_sha256"], reads[0]["sha256"],
        isolation["workspace_realpath_sha256"],
        isolation["layout_realpath_sha256"], interdiction["inventory_sha256"],
        interdiction["analyzed_modules_sha256"],
    ):
        if type(digest) is not str or _HEX64_RE.fullmatch(digest) is None:
            raise ProbeIsolationError("evidence SHA-256 field is malformed")


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="B-4 non-sample wiring probe")
    parser.add_argument("--driver", required=True, choices=tuple(_DRIVER_MODULES))
    parser.add_argument("--evidence-set-id", required=True)
    return parser.parse_args(list(argv))


def main(argv: Sequence[str] | None = None) -> int:
    _claim_fresh_dedicated_process()
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    args = _parse_args(raw_argv)
    json_path, sidecar = _validate_evidence_target(args.driver, args.evidence_set_id)
    started = datetime.now(timezone.utc)
    guard = _ProcessGuard(_protected_campaign_roots())
    guard.install_audit()
    observations = {
        "opened_before_campaign_imports": guard.audit_active("before-campaign-imports"),
    }
    static_modules = _load_static_modules()
    runtime = _load_runtime(guard, static_modules)
    inventory = _build_inventory(static_modules, runtime.modules)
    analyzed_modules = _static_module_manifest(static_modules)
    analyzed_modules_hash = _sha256_bytes(
        _canonical_bytes(analyzed_modules).rstrip(b"\n")
    )
    switchpoint = _proof_switchpoint(static_modules, runtime.drivers[args.driver])
    guard.seal(inventory, runtime.modules)
    observations["sealed_before_checks"] = (
        guard.profile_active() and guard.audit_active("sealed-before-checks")
    )
    observations["audit_hook_active"] = guard.audit_active("audit-identity")
    watch = [
        runtime.L.make_critic_digest,
        runtime.L.load_rejections,
        runtime.L.load_liveness_rejections,
        runtime.L.load_verify_abort_signals,
        runtime.L.load_diff_rejections,
    ]
    guard.watch(watch)
    global _ACTIVE_RUNTIME
    _ACTIVE_RUNTIME = runtime
    view = None
    workspace_hash = layout_hash = ""
    admission_overlay_sha = ""
    try:
        view = _make_probe_view()
        admission_overlay_sha = view.decision.overlay_ledger_sha256
        if (
            type(admission_overlay_sha) is not str
            or _HEX64_RE.fullmatch(admission_overlay_sha) is None
        ):
            raise ProbeIsolationError(
                "admission decision lacks the overlay bytes digest"
            )
        context = _CheckContext(
            runtime=runtime, guard=guard, spec=runtime.drivers[args.driver],
            view=view, static_switchpoint=switchpoint,
        )
        checks: dict[str, Mapping[str, object]] = {}
        for name, check in _CHECKS:
            try:
                result = dict(check(context))
            except BaseException:
                guard.failed_check_attempts.append(name)
                raise
            if result.get("passed") is not True:
                guard.failed_check_attempts.append(name)
                raise ProbeIsolationError(f"probe check failed: {name}")
            checks[name] = result
        workspace_hash, layout_hash = _release_probe_view(view)
        view = None
    except BaseException as primary:
        if view is not None and id(view) in _VIEW_WORKSPACES:
            try:
                _release_probe_view(view)
            except BaseException as cleanup:
                raise primary from cleanup
        raise
    finally:
        _ACTIVE_RUNTIME = None
    guard.verify_seal()
    expected_overlay = _resolved(_REPO_ROOT / _OVERLAY_RELATIVE)
    if guard.overlay_read_paths != {expected_overlay}:
        raise ProbeIsolationError(
            "admission read set differed from the named deny-only overlay"
        )
    if guard.protected_read_attempts or guard.protected_write_attempts:
        raise ProbeIsolationError("protected campaign access occurred")
    if (
        guard.blocked_outcome_attempts
        or guard.failed_check_attempts
        or guard.forbidden_subprocess_attempts
        or guard.interpreter_mutation_attempts
    ):
        raise ProbeIsolationError("interdiction ledger is non-empty")
    completed = datetime.now(timezone.utc)
    driver_module = runtime.modules[runtime.drivers[args.driver].module]
    inventory_hash = _sha256_bytes(_canonical_bytes(inventory).rstrip(b"\n"))
    hook_report = _interdiction_report(guard, observations)
    current_overlay_sha = _sha256_file(expected_overlay)
    if current_overlay_sha != admission_overlay_sha:
        raise ProbeIsolationError(
            "overlay bytes changed after the admission decision"
        )
    evidence = {
        "schema_version": SCHEMA_VERSION,
        "evidence_class": EVIDENCE_CLASS,
        "sanctioned_entrypoint": SANCTIONED_ENTRYPOINT,
        "claim": {
            "evidence_kind": (
                "static candidate-main path + probe direct call to the real switchpoint"
            ),
            "runtime_candidate_main_passage_claimed": False,
        },
        "run": {
            "driver": args.driver,
            "axis": driver_module.MARKER_ID,
            "evidence_set_id": args.evidence_set_id,
            "argv": raw_argv,
            "started_at_utc": started.isoformat().replace("+00:00", "Z"),
            "completed_at_utc": completed.isoformat().replace("+00:00", "Z"),
            "python_version": sys.version,
        },
        "source": {
            "repository_head": runtime.repository_head,
            "probe_path": _PROBE_RELATIVE,
            "probe_sha256": _sha256_file(_REPO_ROOT / _PROBE_RELATIVE),
            "driver_path": runtime.drivers[args.driver].relative_path,
            "driver_sha256": _sha256_file(Path(driver_module.__file__).resolve()),
            "base_driver_path": _MODULE_RELATIVE_PATHS[
                f"{_CAMPAIGN_PACKAGE}.p3_s4_loop"
            ],
            "base_driver_sha256": _sha256_file(Path(runtime.L.__file__).resolve()),
        },
        "admission_reads": {
            "reads": [{
                "path": _OVERLAY_RELATIVE,
                "sha256": admission_overlay_sha,
            }],
            "classification": (
                "deny-only admission ledger; legacy identifiers and historical "
                "verification state; not a B-4 outcome"
            ),
            "other_campaign_artifact_reads": guard.protected_read_attempts,
            "audit_basis": "protected_read_attempts == 0",
        },
        "isolation": {
            "kind": "internally-issued-temporary-directory",
            "workspace_realpath_sha256": workspace_hash,
            "layout_realpath_sha256": layout_hash,
            "outside_repository": True,
            "outside_resolved_campaign_roots": True,
            "workspace_removed_before_publish": True,
            "protected_read_attempts": guard.protected_read_attempts,
            "protected_write_attempts": guard.protected_write_attempts,
        },
        "interdiction": {
            "authority": {
                "symbol": _GENERATION_SEEDS[0],
                "path": _MODULE_RELATIVE_PATHS[f"{_CAMPAIGN_PACKAGE}.execution_guard"],
                "line": runtime.modules[
                    f"{_CAMPAIGN_PACKAGE}.execution_guard"
                ].require_certified_writer_authorization.__code__.co_firstlineno,
                "source_sha256": _sha256_file(
                    Path(runtime.modules[
                        f"{_CAMPAIGN_PACKAGE}.execution_guard"
                    ].__file__).resolve()
                ),
            },
            "generation_seeds": list(_GENERATION_SEEDS),
            "generation_scope": (
                "within the exact analyzed module set, reverse closure over "
                "statically resolved call edges includes functions reaching at "
                "least one named seed"
            ),
            "generation_scope_exclusion": (
                "modules outside the exact analyzed set and producers reaching none "
                "of the three seeds, plus callers inside the analyzed set whose "
                "call binding cannot be statically resolved, are not covered by "
                "this layer"
            ),
            "viewing_scope": "protected campaign root reads and writes are audit-blocked",
            "inventory": inventory,
            "inventory_sha256": inventory_hash,
            "analyzed_modules": analyzed_modules,
            "analyzed_modules_sha256": analyzed_modules_hash,
            **hook_report,
            "blocked_outcome_attempts": guard.blocked_outcome_attempts,
            "failed_check_attempts": guard.failed_check_attempts,
            "forbidden_subprocess_attempts": guard.forbidden_subprocess_attempts,
            "interpreter_mutation_attempts": guard.interpreter_mutation_attempts,
            "allowed_read_only_git": [
                {"argv_sha256": digest, "returncode": 0}
                for digest in guard.allowed_git_argv_sha256
            ],
            "seal_scope": "sys.modules object and Python function code identity",
            "thread_census": {
                "before_campaign_imports": runtime.thread_count_before_imports,
                "at_seal": runtime.thread_count_at_seal,
                "unchanged": (
                    runtime.thread_count_before_imports
                    == runtime.thread_count_at_seal
                ),
            },
            "scope_limit": (
                "arbitrary native code and an equally privileged process are not claimed"
            ),
        },
        "checks": checks,
        "result": {
            "passed": True,
            "pass_rule": (
                "all-four-checks-and-zero-interdiction-or-protected-root-violations"
            ),
            "preregistration_effect": "none-section-5-remains-unfilled",
        },
    }
    digest = _publish_evidence(guard, evidence, json_path, sidecar)
    print(f"{json_path} {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
