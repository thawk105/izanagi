# -*- coding: utf-8 -*-
"""Phase 3 8c trial manifest registration and acceptance gates.

The registry records declarations only.  In particular, a successful
acceptance result does not certify that the declared experimental arm was the
arm that ran.
"""
from __future__ import annotations

import argparse
import dataclasses
import fcntl
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import threading
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from .autonomous_trial_completeness import (
    AutonomousTrialCompletenessError,
    assert_autonomous_trial_completeness,
)
from . import s8c_preregistration
from . import s8c_acceptance_receipt

if TYPE_CHECKING:
    from .reflux_formal_consumer import OriginTerminalProjection
    from .reflux_origin_binding import OriginBindingCapability




MANIFEST_SCHEMA_VERSION = "p3-8c-trial-manifest/v2"
REGISTRATION_SCHEMA_VERSION = "p3-8c-trial-registration/v2"
DEFAULT_REGISTRY_PATH = Path("output/s8c-trial-registry/registry.jsonl")
DEFAULT_LIFECYCLE_PATH = Path("output/s8c-trial-registry/lifecycle.jsonl")
LIFECYCLE_SCHEMA_VERSION = "p3-8c-trial-lifecycle/v1"
ARMS = ("on", "off", "swapped")
HOLDOUTS = ("H1", "H2")
HOLDOUT_BINDINGS: Mapping[str, Mapping[str, str]] = {
    "H1": {"workload": "rr80", "ycsb_rratio": "80"},
    "H2": {"workload": "rr20", "ycsb_rratio": "20"},
}
HOLDOUT_WORKLOADS = frozenset(
    binding["workload"] for binding in HOLDOUT_BINDINGS.values()
)

_TRIAL_ID_RE = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}")
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_MANIFEST_KEYS = frozenset({"schema_version", "prereg_commit", "trials"})
_TRIAL_KEYS = frozenset({
    "trial_id", "arm", "holdout", "campaign_id", "generations",
})
_REGISTRATION_KEYS = frozenset({
    "schema_version", "manifest_sha256", "prereg_commit", "trials",
})
_TRIAL_BINDING_SEAL = object()
_TRIAL_LAUNCH_ADMISSION_SEAL = object()
_TRIAL_LIFECYCLE_TOKEN_SEAL = object()
_LIFECYCLE_START_KEYS = frozenset({
    "schema_version", "event", "trial_id", "run_root", "mode",
    "manifest_sha256", "measurement_head", "activation_report_digest_sha256",
    "launch_admission_sha256",
})
_LIFECYCLE_TERMINAL_BASE_KEYS = frozenset({
    "schema_version", "event", "trial_id", "terminal_status",
    "report_sha256", "attempt_journal_sha256",
})
_LIFECYCLE_TERMINAL_KEYS = frozenset({
    _LIFECYCLE_TERMINAL_BASE_KEYS,
    _LIFECYCLE_TERMINAL_BASE_KEYS | {"origin_terminal_projection"},
})
_ORIGIN_BINDING_KEYS = frozenset({
    "authority_blob_sha256", "source_closure_sha256", "origin_id", "cell_key",
    "authority_workload", "axis_semantics_sha256", "verifier_policy_sha256",
    "environment_contract_sha256", "campaign_id", "trial_workload",
    "measurement_head", "store_scope", "issuer_seal",
})
_LAUNCH_ADMISSION_BASE_KEYS = frozenset({
    "mode", "certifying", "reason_code", "trial_id", "workloads", "binding",
    "activation_report_digest_sha256",
})
_LAUNCH_ADMISSION_KEYS = frozenset({
    _LAUNCH_ADMISSION_BASE_KEYS,
    _LAUNCH_ADMISSION_BASE_KEYS | {"origin_binding"},
})
_ORIGIN_WORKLOAD_KEYS = frozenset({"descriptor_sha256", "records", "threads"})
_ORIGIN_TERMINAL_PROJECTION_KEYS = frozenset({
    "schema_version", "reason_code", "formal_receipt_sha256",
    "evidence_root_sha256", "authority_blob_sha256", "origin_id", "cell_key",
    "terminal_payload_sha256",
})
_FORMAL_REASON_CODES = frozenset({
    "FC01", "FC02", "FC03", "FC04", "FC05a", "FC05b", "FC05c", "FC06",
    "FC07", "FC09", "FC10", "P6Unavailable",
})
_GIT_ENV_ALLOW = frozenset({
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "PATH",
    "SYSTEMROOT",
    "TMPDIR",
})


class TrialRegistryError(RuntimeError):
    """A fail-closed trial registry gate rejected its input."""


def _fail(gate: str, message: str) -> None:
    raise TrialRegistryError(f"[{gate}] {message}")


@dataclasses.dataclass(frozen=True, slots=True)
class TrialSpec:
    trial_id: str
    arm: str
    holdout: str
    campaign_id: str
    generations: int


@dataclasses.dataclass(frozen=True, slots=True)
class TrialManifest:
    schema_version: str
    prereg_commit: str
    trials: tuple[TrialSpec, ...]
    sha256: str
    raw_bytes: bytes = dataclasses.field(repr=False, compare=False)


@dataclasses.dataclass(frozen=True, slots=True)
class TrialRegistration:
    schema_version: str
    manifest_sha256: str
    prereg_commit: str
    trials: tuple[TrialSpec, ...]


@dataclasses.dataclass(frozen=True, slots=True)
class TrialBinding:
    manifest_sha256: str
    prereg_commit: str
    measurement_head: str
    trial_id: str
    arm: str
    holdout: str
    campaign_id: str
    workload: str
    ycsb_rratio: str
    _seal: object = dataclasses.field(repr=False, compare=False)


@dataclasses.dataclass(frozen=True, slots=True)
class TrialLaunchAdmission:
    mode: Literal[
        "registered-effective", "explicit-unregistered-exploratory"
    ]
    certifying: bool
    reason_code: str
    trial_id: str
    workloads: tuple[str, ...]
    binding: TrialBinding | None
    activation_report_digest_sha256: str | None
    _seal: object = dataclasses.field(repr=False, compare=False)


@dataclasses.dataclass(frozen=True, slots=True)
class TrialLifecycleToken:
    """単一 lifecycle ledger 内だけの start-once token。

    committed ledger の append-only 履歴は単一 Git repository 内で検査する。
    この token は、同じ ledger と repository history を共有しない別 clone を横断する
    project-global な一回性を保証しない。
    """

    repository_root: Path = dataclasses.field(repr=False, compare=False)
    lifecycle_path: Path
    trial_id: str
    run_root: str
    start_row_sha256: str
    launch_admission_sha256: str
    _seal: object = dataclasses.field(repr=False, compare=False)


@dataclasses.dataclass(slots=True)
class _TrialLifecycleCapabilityState:
    token: TrialLifecycleToken
    repository_root: Path
    lifecycle_path: Path
    trial_id: str
    run_root: str
    start_row_sha256: str
    launch_admission_sha256: str
    origin_binding: OriginBindingCapability | None
    consumed: bool = False


_TRIAL_LIFECYCLE_CAPABILITIES: dict[int, _TrialLifecycleCapabilityState] = {}
_TRIAL_LIFECYCLE_CAPABILITIES_LOCK = threading.Lock()


@dataclasses.dataclass(frozen=True, slots=True)
class AcceptedTrial:
    trial_id: str
    status: str
    measurement_head: str


@dataclasses.dataclass(frozen=True, slots=True)
class AcceptanceSummary:
    manifest_sha256: str
    trials: tuple[AcceptedTrial, ...]
    receipt_path: str
    receipt_sha256: str
    certifying: bool = False
    arm_binding: str = "declared-only"


@dataclasses.dataclass(slots=True)
class _LoadedReport:
    report: dict[str, Any]
    report_path: Path
    report_bytes: bytes
    journal_path: Path
    journal_fd: int
    journal_bytes: bytes
    events: list[Mapping[str, Any]]

    def assert_snapshot_unchanged(self) -> None:
        info = os.fstat(self.journal_fd)
        current = bytearray()
        offset = 0
        while offset < info.st_size:
            chunk = os.pread(
                self.journal_fd,
                min(1024 * 1024, info.st_size - offset),
                offset,
            )
            if not chunk:
                _fail("journal-snapshot", "journal fd read stopped early")
            current.extend(chunk)
            offset += len(chunk)
        if bytes(current) != self.journal_bytes:
            _fail("journal-snapshot", "journal fd bytes changed during acceptance")
        try:
            rebound = self.journal_path.stat()
        except OSError as exc:
            raise TrialRegistryError(
                "[journal-snapshot] journal path disappeared during acceptance"
            ) from exc
        if (rebound.st_dev, rebound.st_ino) != (info.st_dev, info.st_ino):
            _fail("journal-snapshot", "journal path changed during acceptance")

    def close(self) -> None:
        os.close(self.journal_fd)


def _canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise TrialRegistryError(f"[json] value is not canonical JSON: {exc}") from exc


def _reject_constant(value: str) -> None:
    _fail("json", f"non-finite JSON number is forbidden: {value}")


def _object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("json", f"duplicate object key: {key!r}")
        result[key] = value
    return result


def _decode_json(data: bytes, *, label: str) -> Any:
    try:
        return json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except TrialRegistryError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        _fail("json", f"{label} is not strict UTF-8 JSON: {exc}")


def _read_regular_bytes(path: Path, *, gate: str, label: str) -> bytes:
    path = Path(path)
    try:
        before = path.lstat()
    except OSError as exc:
        raise TrialRegistryError(f"[{gate}] {label} cannot be stated: {path}") from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        _fail(gate, f"{label} must be a regular non-symlink file: {path}")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
        try:
            opened = os.fstat(fd)
            if not stat.S_ISREG(opened.st_mode):
                _fail(gate, f"{label} changed away from a regular file: {path}")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            after = os.fstat(fd)
        finally:
            os.close(fd)
    except TrialRegistryError:
        raise
    except OSError as exc:
        raise TrialRegistryError(f"[{gate}] {label} cannot be read: {path}") from exc
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if identity_before != identity_after:
        _fail(gate, f"{label} changed while it was being read: {path}")
    return b"".join(chunks)


def _exact_keys(value: Mapping[str, Any], expected: frozenset[str], *, label: str) -> None:
    actual = frozenset(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        _fail("schema", f"{label} key set differs: missing={missing}, unknown={unknown}")


def _validate_origin_binding_record(
    record: object,
    *,
    trial: TrialSpec | None = None,
    measurement_head: str | None = None,
    gate: str,
) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        _fail(gate, "origin_binding must be a non-null object")
    if frozenset(record) != _ORIGIN_BINDING_KEYS:
        _fail(gate, "origin_binding exact keys differ")
    workload = record.get("authority_workload")
    if not isinstance(workload, Mapping) or frozenset(workload) != _ORIGIN_WORKLOAD_KEYS:
        _fail(gate, "origin authority_workload exact keys differ")
    for field in (
        "authority_blob_sha256", "source_closure_sha256",
        "axis_semantics_sha256", "verifier_policy_sha256",
        "environment_contract_sha256",
    ):
        value = record.get(field)
        if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
            _fail(gate, f"origin_binding {field} is invalid")
    descriptor = workload.get("descriptor_sha256")
    if type(descriptor) is not str or _SHA256_RE.fullmatch(descriptor) is None:
        _fail(gate, "origin authority descriptor is invalid")
    for field in ("records", "threads"):
        value = workload.get(field)
        if type(value) is not int or value < 1:
            _fail(gate, f"origin authority {field} is invalid")
    for field in ("origin_id", "cell_key", "campaign_id", "trial_workload"):
        value = record.get(field)
        if type(value) is not str or not value:
            _fail(gate, f"origin_binding {field} is invalid")
    commit = record.get("measurement_head")
    if type(commit) is not str or _COMMIT_RE.fullmatch(commit) is None:
        _fail(gate, "origin_binding measurement_head is invalid")
    if (
        record.get("store_scope") != "fixture"
        or record.get("issuer_seal") != "launch-admission-gate/v1"
    ):
        _fail(gate, "origin_binding issuer projection is invalid")
    if trial is not None:
        expected_workload = HOLDOUT_BINDINGS[trial.holdout]["workload"]
        if (
            record.get("campaign_id") != trial.campaign_id
            or record.get("trial_workload") != expected_workload
        ):
            _fail(gate, "origin_binding differs from the registered trial")
    if measurement_head is not None and commit != measurement_head:
        _fail(gate, "origin_binding measurement_head differs from the report")
    return dict(record)


def _validate_origin_terminal_projection(
    value: object,
    *,
    gate: str,
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        _fail(gate, "origin_terminal_projection must be an object")
    if frozenset(value) != _ORIGIN_TERMINAL_PROJECTION_KEYS:
        _fail(gate, "origin_terminal_projection exact keys differ")
    reason = value.get("reason_code")
    if reason not in _FORMAL_REASON_CODES:
        _fail(gate, "origin terminal reason_code is outside the closed set")
    rejected = reason != "P6Unavailable"
    for field in ("formal_receipt_sha256", "evidence_root_sha256"):
        digest = value.get(field)
        if rejected:
            if digest is not None:
                _fail(gate, f"rejected origin terminal {field} must be null")
        elif type(digest) is not str or _SHA256_RE.fullmatch(digest) is None:
            _fail(gate, f"P6Unavailable origin terminal {field} is invalid")
    for field in ("authority_blob_sha256", "terminal_payload_sha256"):
        digest = value.get(field)
        if type(digest) is not str or _SHA256_RE.fullmatch(digest) is None:
            _fail(gate, f"origin terminal {field} is invalid")
    for field in ("origin_id", "cell_key"):
        token = value.get(field)
        if type(token) is not str or not token:
            _fail(gate, f"origin terminal {field} is invalid")
    if value.get("schema_version") != "OriginTerminalProjection/v1":
        _fail(gate, "origin terminal schema_version is invalid")
    return dict(value)


def _parse_trials(
    value: Any,
    *,
    label: str,
    require_canonical_order: bool = False,
) -> tuple[TrialSpec, ...]:
    if not isinstance(value, list):
        _fail("schema", f"{label} must be an array")
    if len(value) != 6:
        _fail("trial-universe", f"{label} must contain exactly 6 trials")
    trials: list[TrialSpec] = []
    for index, raw_trial in enumerate(value):
        if not isinstance(raw_trial, Mapping):
            _fail("schema", f"{label}[{index}] must be an object")
        _exact_keys(raw_trial, _TRIAL_KEYS, label=f"{label}[{index}]")
        trial_id = raw_trial["trial_id"]
        arm = raw_trial["arm"]
        holdout = raw_trial["holdout"]
        campaign_id = raw_trial["campaign_id"]
        generations = raw_trial["generations"]
        if not isinstance(trial_id, str) or _TRIAL_ID_RE.fullmatch(trial_id) is None:
            _fail("field", f"{label}[{index}].trial_id is not lexically valid")
        if not isinstance(arm, str) or arm not in ARMS:
            _fail("field", f"{label}[{index}].arm is outside the closed set")
        if not isinstance(holdout, str) or holdout not in HOLDOUTS:
            _fail("field", f"{label}[{index}].holdout is outside the closed set")
        if not isinstance(campaign_id, str) or not campaign_id:
            _fail("field", f"{label}[{index}].campaign_id must be a non-empty string")
        if not (type(generations) is int and generations == 2):
            _fail("field", f"{label}[{index}].generations must be the integer 2")
        trials.append(TrialSpec(trial_id, arm, holdout, campaign_id, generations))
    if len({item.trial_id for item in trials}) != len(trials):
        _fail("uniqueness", f"{label} reuses a trial_id")
    if len({item.campaign_id for item in trials}) != len(trials):
        _fail("uniqueness", f"{label} reuses a campaign_id")
    expected_universe = {(holdout, arm) for holdout in HOLDOUTS for arm in ARMS}
    actual_universe = {(item.holdout, item.arm) for item in trials}
    if actual_universe != expected_universe:
        _fail("trial-universe", f"{label} is not the H1/H2 x on/off/swapped product")
    holdout_order = {value: index for index, value in enumerate(HOLDOUTS)}
    arm_order = {value: index for index, value in enumerate(ARMS)}
    canonical = tuple(sorted(
        trials,
        key=lambda item: (holdout_order[item.holdout], arm_order[item.arm]),
    ))
    if require_canonical_order and tuple(trials) != canonical:
        _fail("registration-binding", f"{label} is not in canonical trial order")
    return canonical


def load_trial_manifest(path: Path) -> TrialManifest:
    """Load and validate one exact six-trial preregistration manifest."""
    raw_bytes = _read_regular_bytes(Path(path), gate="manifest-read", label="manifest")
    value = _decode_json(raw_bytes, label="manifest")
    if not isinstance(value, Mapping):
        _fail("schema", "manifest root must be an object")
    _exact_keys(value, _MANIFEST_KEYS, label="manifest")
    if value["schema_version"] != MANIFEST_SCHEMA_VERSION:
        _fail("schema", "manifest schema_version is not supported")
    prereg_commit = value["prereg_commit"]
    if not isinstance(prereg_commit, str) or _COMMIT_RE.fullmatch(prereg_commit) is None:
        _fail("field", "manifest.prereg_commit is not a 40-digit lowercase commit ID")
    trials = _parse_trials(value["trials"], label="manifest.trials")
    return TrialManifest(
        schema_version=MANIFEST_SCHEMA_VERSION,
        prereg_commit=prereg_commit,
        trials=trials,
        sha256=hashlib.sha256(raw_bytes).hexdigest(),
        raw_bytes=raw_bytes,
    )


def _trial_dict(trial: TrialSpec) -> dict[str, str | int]:
    return {
        "trial_id": trial.trial_id,
        "arm": trial.arm,
        "holdout": trial.holdout,
        "campaign_id": trial.campaign_id,
        "generations": trial.generations,
    }


def _registration_dict(registration: TrialRegistration) -> dict[str, Any]:
    return {
        "schema_version": registration.schema_version,
        "manifest_sha256": registration.manifest_sha256,
        "prereg_commit": registration.prereg_commit,
        "trials": [_trial_dict(trial) for trial in registration.trials],
    }


def _registration_for(manifest: TrialManifest) -> TrialRegistration:
    return TrialRegistration(
        schema_version=REGISTRATION_SCHEMA_VERSION,
        manifest_sha256=manifest.sha256,
        prereg_commit=manifest.prereg_commit,
        trials=manifest.trials,
    )


def _load_registry_bytes(data: bytes, *, label: str) -> tuple[TrialRegistration, ...]:
    if not data or not data.endswith(b"\n"):
        _fail("registry-framing", f"{label} must be non-empty and newline terminated")
    registrations: list[TrialRegistration] = []
    for lineno, line in enumerate(data.splitlines(), 1):
        if not line:
            _fail("registry-framing", f"{label} has a blank line at {lineno}")
        value = _decode_json(line, label=f"{label} line {lineno}")
        if not isinstance(value, Mapping):
            _fail("registry-framing", f"{label} line {lineno} is not an object")
        if _canonical_json_bytes(value) != line:
            _fail("registry-canonical", f"{label} line {lineno} is not canonical JSON")
        _exact_keys(value, _REGISTRATION_KEYS, label=f"{label} line {lineno}")
        if value["schema_version"] != REGISTRATION_SCHEMA_VERSION:
            _fail("schema", f"{label} line {lineno} has an unsupported schema_version")
        manifest_sha256 = value["manifest_sha256"]
        prereg_commit = value["prereg_commit"]
        if not isinstance(manifest_sha256, str) or _SHA256_RE.fullmatch(manifest_sha256) is None:
            _fail("field", f"{label} line {lineno} has an invalid manifest_sha256")
        if not isinstance(prereg_commit, str) or _COMMIT_RE.fullmatch(prereg_commit) is None:
            _fail("field", f"{label} line {lineno} has an invalid prereg_commit")
        registrations.append(TrialRegistration(
            schema_version=REGISTRATION_SCHEMA_VERSION,
            manifest_sha256=manifest_sha256,
            prereg_commit=prereg_commit,
            trials=_parse_trials(
                value["trials"],
                label=f"{label} line {lineno}.trials",
                require_canonical_order=True,
            ),
        ))
    _assert_registry_unique(tuple(registrations))
    return tuple(registrations)


def _assert_registry_unique(registrations: tuple[TrialRegistration, ...]) -> None:
    manifest_hashes: set[str] = set()
    trial_ids: set[str] = set()
    campaign_ids: set[str] = set()
    for registration in registrations:
        if registration.manifest_sha256 in manifest_hashes:
            _fail("registry-index", "registry reuses a manifest_sha256")
        manifest_hashes.add(registration.manifest_sha256)
        for trial in registration.trials:
            if trial.trial_id in trial_ids:
                _fail("registry-index", f"registry reuses trial_id {trial.trial_id!r}")
            if trial.campaign_id in campaign_ids:
                _fail("registry-index", f"registry reuses campaign_id {trial.campaign_id!r}")
            trial_ids.add(trial.trial_id)
            campaign_ids.add(trial.campaign_id)


def load_trial_registry(path: Path) -> tuple[TrialRegistration, ...]:
    """Load a canonical, globally unique registration JSONL file."""
    data = _read_regular_bytes(Path(path), gate="registry-read", label="registry")
    return _load_registry_bytes(data, label="registry")


def _git_env() -> dict[str, str]:
    env = {
        key: value for key, value in os.environ.items()
        if key in _GIT_ENV_ALLOW
    }
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_LITERAL_PATHSPECS"] = "1"
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def _git(
    repository_root: Path,
    args: Sequence[str],
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", os.fspath(repository_root), *args],
        env=_git_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _repository_root(path: Path) -> Path:
    try:
        root = Path(path).resolve(strict=True)
    except OSError as exc:
        raise TrialRegistryError(f"[repo-path] repository root cannot be resolved: {path}") from exc
    if not root.is_dir():
        _fail("repo-path", f"repository root is not a directory: {root}")
    result = _git(root, ("rev-parse", "--show-toplevel"))
    if result.returncode != 0:
        raise TrialRegistryError("[git] repository root is not a Git work tree")
    try:
        actual = Path(result.stdout.decode("utf-8").strip()).resolve(strict=True)
    except (OSError, UnicodeDecodeError) as exc:
        raise TrialRegistryError("[git] Git returned an invalid repository root") from exc
    if actual != root:
        _fail("repo-path", f"repository_root is not the Git top level: {root}")
    return root


def _repo_relative(path: Path, repository_root: Path, *, label: str) -> tuple[Path, str]:
    try:
        resolved = Path(path).resolve(strict=True)
    except OSError as exc:
        raise TrialRegistryError(f"[repo-path] {label} cannot be resolved: {path}") from exc
    try:
        relative = resolved.relative_to(repository_root)
    except ValueError:
        _fail("repo-path", f"{label} is outside repository_root: {resolved}")
    if relative == Path("."):
        _fail("repo-path", f"{label} cannot be repository_root")
    return resolved, relative.as_posix()


def _registry_relative_target(
    path: Path,
    repository_root: Path,
) -> tuple[Path, Path, str]:
    """Validate the registry's lexical tracked-worktree namespace."""
    raw = Path(path)
    candidate = Path(os.path.abspath(os.fspath(
        raw if raw.is_absolute() else repository_root / raw
    )))
    try:
        relative = candidate.relative_to(repository_root)
    except ValueError:
        _fail("registry-path", f"registry is outside repository_root: {candidate}")
    if relative == Path(".") or relative.name in {"", ".", ".."}:
        _fail("registry-path", "registry path must name a file")
    if ".git" in relative.parts:
        _fail("registry-path", "registry path must not contain a .git component")
    return candidate, relative, relative.as_posix()


def _registry_target(
    path: Path,
    repository_root: Path,
    *,
    create_parent: bool,
) -> tuple[Path, str]:
    path, _relative_path, relative = _registry_relative_target(
        Path(path), repository_root,
    )
    if path.exists() or path.is_symlink():
        if path.is_symlink():
            _fail("registry-path", f"registry must not be a symlink: {path}")
        resolved, resolved_relative = _repo_relative(
            path, repository_root, label="registry",
        )
        if resolved_relative != relative:
            _fail("registry-path", "registry path traverses a symlink component")
        return resolved, relative
    parent = path.parent
    existing_ancestor = parent
    while not existing_ancestor.exists() and not existing_ancestor.is_symlink():
        if existing_ancestor == existing_ancestor.parent:
            break
        existing_ancestor = existing_ancestor.parent
    try:
        existing_ancestor.resolve(strict=True).relative_to(repository_root)
    except (OSError, ValueError) as exc:
        raise TrialRegistryError(
            "[registry-path] registry parent real path is outside repository"
        ) from exc
    if create_parent:
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise TrialRegistryError(f"[registry-path] registry parent cannot be created: {parent}") from exc
    try:
        real_parent = parent.resolve(strict=True)
        real_parent.relative_to(repository_root)
    except (OSError, ValueError) as exc:
        raise TrialRegistryError("[registry-path] registry parent real path is outside repository") from exc
    resolved = real_parent / path.name
    return resolved, relative


def _canonical_lifecycle_target(
    path: Path,
    repository_root: Path,
    *,
    create_parent: bool,
) -> tuple[Path, str]:
    """Resolve only the repository's fixed lifecycle ledger authority."""
    _candidate, _relative_path, relative = _registry_relative_target(
        Path(path), repository_root,
    )
    if relative != DEFAULT_LIFECYCLE_PATH.as_posix():
        _fail(
            "lifecycle-path",
            "lifecycle_path must name the canonical repository ledger",
        )
    return _registry_target(
        DEFAULT_LIFECYCLE_PATH,
        repository_root,
        create_parent=create_parent,
    )


def _directory_open_flags() -> int:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return flags


def _open_registry_parent(
    repository_root: Path,
    relative_parent: Path,
    *,
    create: bool,
) -> int:
    """Open each parent component relative to an anchored repository fd."""
    flags = _directory_open_flags()
    try:
        current_fd = os.open(repository_root, flags)
    except OSError as exc:
        raise TrialRegistryError(
            f"[registry-path] repository root cannot be opened: {exc}"
        ) from exc
    try:
        for component in relative_parent.parts:
            try:
                next_fd = os.open(component, flags, dir_fd=current_fd)
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(component, 0o755, dir_fd=current_fd)
                next_fd = os.open(component, flags, dir_fd=current_fd)
            info = os.fstat(next_fd)
            if not stat.S_ISDIR(info.st_mode):
                os.close(next_fd)
                _fail("registry-path", "registry parent component is not a directory")
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except TrialRegistryError:
        os.close(current_fd)
        raise
    except OSError as exc:
        os.close(current_fd)
        raise TrialRegistryError(
            f"[registry-path] registry parent cannot be opened safely: {exc}"
        ) from exc


def resolve_measurement_commit(repository_root: Path) -> str:
    """Resolve the operation's measurement HEAD exactly once."""
    root = _repository_root(repository_root)
    result = _git(root, ("rev-parse", "--verify", "HEAD^{commit}"))
    if result.returncode != 0:
        raise TrialRegistryError("[git] HEAD cannot be resolved to a commit")
    try:
        commit_id = result.stdout.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise TrialRegistryError("[git] HEAD resolution returned non-ASCII output") from exc
    if _COMMIT_RE.fullmatch(commit_id) is None:
        _fail("git", "HEAD did not resolve to a 40-digit lowercase commit ID")
    return commit_id


def require_commit_object(repository_root: Path, commit_id: str) -> None:
    """Require a full lowercase SHA-1 that resolves to that exact commit."""
    root = _repository_root(repository_root)
    if not isinstance(commit_id, str) or _COMMIT_RE.fullmatch(commit_id) is None:
        _fail("commit", "commit ID is not 40-digit lowercase hexadecimal")
    result = _git(root, ("rev-parse", "--verify", f"{commit_id}^{{commit}}"))
    if result.returncode != 0:
        _fail("commit", f"commit object does not exist: {commit_id}")
    try:
        resolved = result.stdout.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise TrialRegistryError("[git] commit resolution returned non-ASCII output") from exc
    if resolved != commit_id:
        _fail("commit", f"commit resolution changed object identity: {commit_id}")


def _assert_not_shallow(repository_root: Path) -> None:
    result = _git(repository_root, ("rev-parse", "--is-shallow-repository"))
    if result.returncode != 0:
        raise TrialRegistryError("[git] shallow-repository state cannot be determined")
    if result.stdout.strip() != b"false":
        _fail("ancestry", "shallow repositories are not accepted")


def _assert_ancestor(
    repository_root: Path,
    *,
    ancestor: str,
    descendant: str,
    gate: str,
    message: str,
) -> None:
    require_commit_object(repository_root, ancestor)
    require_commit_object(repository_root, descendant)
    _assert_not_shallow(repository_root)
    result = _git(repository_root, ("merge-base", "--is-ancestor", ancestor, descendant))
    if result.returncode == 0:
        return
    if result.returncode == 1:
        _fail(gate, message)
    stderr = result.stderr.decode("utf-8", errors="replace").strip()
    raise TrialRegistryError(
        f"[git-operational] merge-base --is-ancestor failed with rc={result.returncode}: {stderr}"
    )


def assert_prereg_ancestor(
    repository_root: Path,
    *,
    prereg_commit: str,
    measurement_commit: str,
) -> None:
    """Require preregistration to be an ancestor of the measurement commit."""
    root = _repository_root(repository_root)
    _assert_ancestor(
        root,
        ancestor=prereg_commit,
        descendant=measurement_commit,
        gate="ancestry",
        message="prereg_commit is not an ancestor of measurement_head",
    )


def _blob_at_commit(
    repository_root: Path,
    *,
    commit_id: str,
    relative_path: str,
) -> bytes | None:
    if relative_path.startswith("/") or relative_path in {"", ".", ".."}:
        _fail("repo-path", "Git blob path is not repository-relative")
    listing = _git(repository_root, (
        "ls-tree", "-z", "--full-name", commit_id, "--", relative_path,
    ))
    if listing.returncode != 0:
        raise TrialRegistryError("[git-operational] committed path existence check failed")
    entries = [entry for entry in listing.stdout.split(b"\0") if entry]
    if not entries:
        return None
    if len(entries) != 1:
        _fail("committed-mode", "committed path did not resolve to one tree entry")
    metadata, separator, entry_path = entries[0].partition(b"\t")
    fields = metadata.split()
    if separator != b"\t" or len(fields) != 3:
        raise TrialRegistryError("[git-operational] committed tree entry is malformed")
    mode, object_type, object_id = fields
    if entry_path != os.fsencode(relative_path):
        _fail("committed-mode", "committed tree entry path differs from the literal path")
    if object_type != b"blob" or mode not in {b"100644", b"100755"}:
        _fail("committed-mode", "committed path is not a regular file entry")
    result = _git(repository_root, ("cat-file", "blob", object_id.decode("ascii")))
    if result.returncode != 0:
        raise TrialRegistryError("[git-operational] committed blob cannot be read")
    return result.stdout


def _require_committed_file(
    *,
    repository_root: Path,
    commit_id: str,
    path: Path,
    label: str,
    expected_bytes: bytes,
) -> str:
    _resolved, relative = _repo_relative(path, repository_root, label=label)
    blob = _blob_at_commit(
        repository_root, commit_id=commit_id, relative_path=relative,
    )
    if blob is None:
        _fail("committed-file", f"{label} is absent from commit {commit_id}")
    if blob != expected_bytes:
        _fail("committed-file", f"{label} bytes differ from commit {commit_id}")
    return relative


def _find_registration(
    registrations: tuple[TrialRegistration, ...],
    expected: TrialRegistration,
) -> TrialRegistration:
    selected = [
        item for item in registrations
        if item.manifest_sha256 == expected.manifest_sha256
    ]
    if len(selected) != 1 or selected[0] != expected:
        _fail("registration-binding", "manifest has no single exact registry registration")
    return selected[0]


def append_trial_registration(
    *,
    manifest_path: Path,
    repository_root: Path,
    registry_path: Path,
) -> TrialRegistration:
    """Append one manifest registration in a single fsynced critical section."""
    root = _repository_root(repository_root)
    manifest = load_trial_manifest(Path(manifest_path))
    measurement_head = resolve_measurement_commit(root)
    _require_committed_file(
        repository_root=root,
        commit_id=measurement_head,
        path=Path(manifest_path),
        label="manifest",
        expected_bytes=manifest.raw_bytes,
    )
    assert_prereg_ancestor(
        root,
        prereg_commit=manifest.prereg_commit,
        measurement_commit=measurement_head,
    )
    registry, relative_path, relative = _registry_relative_target(
        Path(registry_path), root,
    )
    committed = _blob_at_commit(
        root, commit_id=measurement_head, relative_path=relative,
    )
    registration = _registration_for(manifest)
    payload = _canonical_json_bytes(_registration_dict(registration)) + b"\n"
    try:
        parent_fd = _open_registry_parent(
            root, relative_path.parent, create=True,
        )
        try:
            try:
                path_info = os.stat(
                    relative_path.name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
            except FileNotFoundError:
                path_info = None
            if path_info is not None and not stat.S_ISREG(path_info.st_mode):
                _fail("registry-path", "registry must be a regular non-symlink file")
            if committed is None and path_info is not None:
                _fail("append-state", "untracked registry already exists")
            if committed is not None and path_info is None:
                _fail("append-state", "committed registry is missing from the working tree")
            flags = os.O_RDWR | os.O_APPEND
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            if path_info is None:
                flags |= os.O_CREAT | os.O_EXCL
            fd = os.open(
                relative_path.name,
                flags,
                0o644,
                dir_fd=parent_fd,
            )
            try:
                fcntl.flock(fd, fcntl.LOCK_EX)
                rebound_parent_fd = _open_registry_parent(
                    root, relative_path.parent, create=False,
                )
                try:
                    held_parent = os.fstat(parent_fd)
                    rebound_parent = os.fstat(rebound_parent_fd)
                    if (
                        held_parent.st_dev,
                        held_parent.st_ino,
                    ) != (
                        rebound_parent.st_dev,
                        rebound_parent.st_ino,
                    ):
                        _fail(
                            "append-state",
                            "registry parent changed before locked validation",
                        )
                finally:
                    os.close(rebound_parent_fd)
                info = os.fstat(fd)
                if not stat.S_ISREG(info.st_mode):
                    _fail("append-state", "opened registry is not a regular file")
                rebound = os.stat(
                    relative_path.name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
                if (rebound.st_dev, rebound.st_ino) != (info.st_dev, info.st_ino):
                    _fail("append-state", "registry path changed before locked validation")
                current = bytearray()
                offset = 0
                while offset < info.st_size:
                    chunk = os.pread(fd, min(1024 * 1024, info.st_size - offset), offset)
                    if not chunk:
                        _fail("append-state", "registry read stopped before fstat size")
                    current.extend(chunk)
                    offset += len(chunk)
                after_read = os.fstat(fd)
                if (
                    info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns
                ) != (
                    after_read.st_dev, after_read.st_ino,
                    after_read.st_size, after_read.st_mtime_ns,
                ):
                    _fail("append-state", "registry changed during locked validation")
                rebound_after_read = os.stat(
                    relative_path.name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
                if (
                    rebound_after_read.st_dev,
                    rebound_after_read.st_ino,
                ) != (after_read.st_dev, after_read.st_ino):
                    _fail("append-state", "registry path changed during locked validation")
                current_bytes = bytes(current)
                if committed is None:
                    if current_bytes:
                        _fail("append-state", "first registration did not start from empty bytes")
                    registrations: tuple[TrialRegistration, ...] = ()
                else:
                    if current_bytes != committed:
                        _fail("append-state", "working registry differs from the HEAD blob")
                    registrations = _load_registry_bytes(current_bytes, label="registry")
                _assert_registry_unique((*registrations, registration))
                view = memoryview(payload)
                while view:
                    written = os.write(fd, view)
                    if written <= 0:
                        raise OSError("registry append did not advance")
                    view = view[written:]
                rebound_after_append = os.stat(
                    relative_path.name,
                    dir_fd=parent_fd,
                    follow_symlinks=False,
                )
                appended = os.fstat(fd)
                if (
                    rebound_after_append.st_dev,
                    rebound_after_append.st_ino,
                ) != (appended.st_dev, appended.st_ino):
                    _fail("append-state", "registry path changed during append")
                os.fsync(fd)
                os.fsync(parent_fd)
            finally:
                os.close(fd)
        finally:
            os.close(parent_fd)
    except TrialRegistryError:
        raise
    except OSError as exc:
        raise TrialRegistryError(f"[append-io] registry append failed: {exc}") from exc
    return registration


def _load_committed_registry(
    *,
    repository_root: Path,
    registry_path: Path,
    commit_id: str,
) -> tuple[tuple[TrialRegistration, ...], bytes, str]:
    registry, relative = _registry_target(
        registry_path, repository_root, create_parent=False,
    )
    working_bytes = _read_regular_bytes(
        registry, gate="registry-read", label="registry",
    )
    committed = _blob_at_commit(
        repository_root, commit_id=commit_id, relative_path=relative,
    )
    if committed is None:
        _fail("committed-registry", "registry is not committed at the operation HEAD")
    if committed != working_bytes:
        _fail("committed-registry", "working registry differs from the operation HEAD blob")
    return _load_registry_bytes(committed, label="committed registry"), committed, relative


def _derive_launch_binding(
    *,
    manifest_path: Path,
    trial_id: str,
    workloads: Sequence[str],
    repository_root: Path,
    registry_path: Path,
    measurement_head: str,
) -> TrialBinding:
    """Derive one binding at an already pinned measurement commit."""
    root = repository_root
    manifest = load_trial_manifest(Path(manifest_path))
    _require_committed_file(
        repository_root=root,
        commit_id=measurement_head,
        path=Path(manifest_path),
        label="manifest",
        expected_bytes=manifest.raw_bytes,
    )
    registrations, _registry_bytes, _relative = _load_committed_registry(
        repository_root=root,
        registry_path=Path(registry_path),
        commit_id=measurement_head,
    )
    _find_registration(registrations, _registration_for(manifest))
    selected = [trial for trial in manifest.trials if trial.trial_id == trial_id]
    if len(selected) != 1:
        _fail("trial-membership", "trial_id is not in the selected manifest")
    trial = selected[0]
    binding = HOLDOUT_BINDINGS[trial.holdout]
    if list(workloads) != [binding["workload"]]:
        _fail("workload-binding", "workloads do not match the trial holdout singleton")
    assert_prereg_ancestor(
        root,
        prereg_commit=manifest.prereg_commit,
        measurement_commit=measurement_head,
    )
    return TrialBinding(
        manifest_sha256=manifest.sha256,
        prereg_commit=manifest.prereg_commit,
        measurement_head=measurement_head,
        trial_id=trial.trial_id,
        arm=trial.arm,
        holdout=trial.holdout,
        campaign_id=trial.campaign_id,
        workload=binding["workload"],
        ycsb_rratio=binding["ycsb_rratio"],
        _seal=_TRIAL_BINDING_SEAL,
    )


def load_launch_binding(
    *,
    manifest_path: Path,
    trial_id: str,
    workloads: Sequence[str],
    repository_root: Path,
    registry_path: Path,
) -> TrialBinding:
    """Bind one declared trial to the operation's committed HEAD snapshot."""
    root = _repository_root(repository_root)
    measurement_head = resolve_measurement_commit(root)
    return _derive_launch_binding(
        manifest_path=manifest_path,
        trial_id=trial_id,
        workloads=workloads,
        repository_root=root,
        registry_path=registry_path,
        measurement_head=measurement_head,
    )


def assert_issued_trial_binding(binding: TrialBinding) -> None:
    """Reject caller-constructed values at the CLI-to-runner handoff."""
    if (
        not isinstance(binding, TrialBinding)
        or binding._seal is not _TRIAL_BINDING_SEAL
    ):
        _fail("launch-binding", "binding was not issued by the registry gate")


def assert_rederived_launch_binding(
    binding: TrialBinding,
    *,
    manifest_path: Path,
    trial_id: str,
    workloads: Sequence[str],
    repository_root: Path,
    registry_path: Path,
) -> None:
    """Require every supplied field to equal a derivation at its pinned commit."""
    assert_issued_trial_binding(binding)
    root = _repository_root(repository_root)
    derived = _derive_launch_binding(
        manifest_path=manifest_path,
        trial_id=trial_id,
        workloads=workloads,
        repository_root=root,
        registry_path=registry_path,
        measurement_head=binding.measurement_head,
    )
    for field in dataclasses.fields(TrialBinding):
        supplied = getattr(binding, field.name)
        expected = getattr(derived, field.name)
        matches = (
            supplied is expected
            if field.name == "_seal"
            else supplied == expected
        )
        if not matches:
            _fail(
                "launch-binding",
                f"supplied binding differs from pinned derivation: {field.name}",
            )


def _validate_launch_inputs(
    *,
    trial_id: str,
    workloads: Sequence[str],
) -> tuple[str, ...]:
    if not isinstance(trial_id, str) or _TRIAL_ID_RE.fullmatch(trial_id) is None:
        _fail("field", "launch trial_id is not lexically valid")
    selected = tuple(workloads)
    if not selected:
        _fail("workloads", "launch workloads must be non-empty")
    if any(type(workload) is not str or not workload for workload in selected):
        _fail("workloads", "launch workload names must be non-empty plain strings")
    if len(selected) != len(set(selected)):
        _fail("workloads", "launch workloads contain duplicates")
    return selected


def admit_unregistered_exploratory(
    *,
    trial_id: str,
    workloads: Sequence[str],
    allow_unregistered_exploratory: bool,
    repository_root: Path,
    registry_path: Path,
) -> TrialLaunchAdmission:
    """Admit an explicitly opted-in, non-holdout, non-certifying launch."""
    selected = _validate_launch_inputs(trial_id=trial_id, workloads=workloads)
    root = _repository_root(repository_root)
    if allow_unregistered_exploratory is not True:
        _fail(
            "u4-exploratory-opt-in",
            "unregistered exploratory launch requires explicit opt-in",
        )
    holdouts = sorted(set(selected) & HOLDOUT_WORKLOADS)
    if holdouts:
        _fail(
            "u4-holdout-workload",
            f"holdout workloads cannot use exploratory admission: {holdouts}",
        )
    registry_path = Path(registry_path)
    if not registry_path.is_absolute():
        registry_path = root / registry_path
    working_present = registry_path.exists() or registry_path.is_symlink()
    measurement_head = resolve_measurement_commit(root)
    if working_present:
        registrations, _bytes, _relative = _load_committed_registry(
            repository_root=root,
            registry_path=registry_path,
            commit_id=measurement_head,
        )
    else:
        _candidate, _relative_path, relative = _registry_relative_target(
            registry_path, root,
        )
        committed = _blob_at_commit(
            root, commit_id=measurement_head, relative_path=relative,
        )
        if committed is None:
            registrations = ()
        else:
            registrations = _load_registry_bytes(
                committed, label="committed registry",
            )
    registered = {
        trial.trial_id for registration in registrations for trial in registration.trials
    }
    if trial_id in registered:
        _fail(
            "exploratory-registry",
            "registered trial_id cannot run without its manifest",
        )
    return TrialLaunchAdmission(
        mode="explicit-unregistered-exploratory",
        certifying=False,
        reason_code="explicit-unregistered-exploratory",
        trial_id=trial_id,
        workloads=selected,
        binding=None,
        activation_report_digest_sha256=None,
        _seal=_TRIAL_LAUNCH_ADMISSION_SEAL,
    )


def admit_registered_launch(
    *,
    effective_preregistration: s8c_preregistration.EffectivePreregistration,
    manifest_path: Path,
    trial_id: str,
    workloads: Sequence[str],
    repository_root: Path,
    registry_path: Path,
) -> TrialLaunchAdmission:
    """Admit one registered launch after exact activation recomputation."""
    selected = _validate_launch_inputs(trial_id=trial_id, workloads=workloads)
    root = _repository_root(repository_root)
    manifest = load_trial_manifest(Path(manifest_path))
    if (
        not isinstance(
            effective_preregistration,
            s8c_preregistration.EffectivePreregistration,
        )
        or effective_preregistration.commit != manifest.prereg_commit
    ):
        _fail(
            "effective-preregistration",
            "manifest prereg_commit requires an exact EffectivePreregistration capability",
        )
    try:
        s8c_preregistration.require_effective_preregistration(
            effective_preregistration,
            repo_root=root,
            commit=manifest.prereg_commit,
        )
    except s8c_preregistration.PreregistrationError as exc:
        _fail("effective-preregistration", f"{exc.reason}: {exc}")
    binding = load_launch_binding(
        manifest_path=Path(manifest_path),
        trial_id=trial_id,
        workloads=selected,
        repository_root=root,
        registry_path=Path(registry_path),
    )
    return TrialLaunchAdmission(
        mode="registered-effective",
        certifying=False,
        reason_code="registered-effective-non-certifying",
        trial_id=trial_id,
        workloads=selected,
        binding=binding,
        activation_report_digest_sha256=(
            effective_preregistration.report_digest_sha256
        ),
        _seal=_TRIAL_LAUNCH_ADMISSION_SEAL,
    )


def assert_issued_trial_launch_admission(
    admission: TrialLaunchAdmission,
) -> None:
    """Reject caller-constructed launch admission values."""
    if (
        not isinstance(admission, TrialLaunchAdmission)
        or admission._seal is not _TRIAL_LAUNCH_ADMISSION_SEAL
    ):
        _fail("launch-admission", "admission was not issued by the registry gate")
    if admission.mode not in {
        "registered-effective", "explicit-unregistered-exploratory",
    }:
        _fail("launch-admission", "admission mode is outside the closed set")
    if admission.certifying is not False:
        _fail("launch-admission", "this wiring wave cannot issue certifying launches")
    _validate_launch_inputs(
        trial_id=admission.trial_id,
        workloads=admission.workloads,
    )
    if admission.mode == "registered-effective":
        if admission.binding is None:
            _fail("launch-admission", "registered admission is missing its binding")
        assert_issued_trial_binding(admission.binding)
        if admission.reason_code != "registered-effective-non-certifying":
            _fail("launch-admission", "registered admission reason_code is inconsistent")
        if admission.binding.trial_id != admission.trial_id:
            _fail("launch-admission", "registered admission trial_id is inconsistent")
        if admission.workloads != (admission.binding.workload,):
            _fail("launch-admission", "registered admission workload is inconsistent")
        if (
            admission.activation_report_digest_sha256 is None
            or _SHA256_RE.fullmatch(admission.activation_report_digest_sha256) is None
        ):
            _fail("launch-admission", "registered admission has no activation digest")
    else:
        if (
            admission.reason_code != "explicit-unregistered-exploratory"
            or admission.binding is not None
            or admission.activation_report_digest_sha256 is not None
            or set(admission.workloads) & HOLDOUT_WORKLOADS
        ):
            _fail("launch-admission", "exploratory admission fields are inconsistent")


def launch_admission_record(
    admission: TrialLaunchAdmission,
    *,
    origin_binding: OriginBindingCapability | None = None,
) -> dict[str, Any]:
    """Return the shared exact record, omitting unissued origin projection."""
    assert_issued_trial_launch_admission(admission)
    binding = admission.binding
    binding_record = None
    if binding is not None:
        binding_record = {
            field: getattr(binding, field)
            for field in (
                "manifest_sha256", "prereg_commit", "measurement_head",
                "trial_id", "arm", "holdout", "campaign_id", "workload",
                "ycsb_rratio",
            )
        }
    record = {
        "mode": admission.mode,
        "certifying": admission.certifying,
        "reason_code": admission.reason_code,
        "trial_id": admission.trial_id,
        "workloads": list(admission.workloads),
        "binding": binding_record,
        "activation_report_digest_sha256": (
            admission.activation_report_digest_sha256
        ),
    }
    if origin_binding is not None:
        from . import reflux_origin_binding

        origin_record = (
            reflux_origin_binding.origin_binding_capability_record(origin_binding)
        )
        if (
            binding is None
            or admission.mode != "registered-effective"
            or origin_record["campaign_id"] != binding.campaign_id
            or origin_record["trial_workload"] != binding.workload
            or origin_record["measurement_head"] != binding.measurement_head
        ):
            _fail(
                "launch-admission",
                "origin capability differs from the registered launch binding",
            )
        record["origin_binding"] = origin_record
    return record


def assert_rederived_launch_admission(
    admission: TrialLaunchAdmission,
    *,
    effective_preregistration,
    manifest_path: Path | None,
    trial_id: str,
    workloads: Sequence[str],
    allow_unregistered_exploratory: bool,
    repository_root: Path,
    registry_path: Path,
    origin_binding: OriginBindingCapability | None = None,
) -> None:
    """Require a supplied admission to equal a fresh public-gate derivation."""
    assert_issued_trial_launch_admission(admission)
    if manifest_path is None:
        if effective_preregistration is not None:
            _fail("launch-admission", "exploratory launch received formal capability")
        derived = admit_unregistered_exploratory(
            trial_id=trial_id,
            workloads=workloads,
            allow_unregistered_exploratory=allow_unregistered_exploratory,
            repository_root=repository_root,
            registry_path=registry_path,
        )
    else:
        derived = admit_registered_launch(
            effective_preregistration=effective_preregistration,
            manifest_path=manifest_path,
            trial_id=trial_id,
            workloads=workloads,
            repository_root=repository_root,
            registry_path=registry_path,
        )
    if launch_admission_record(
        admission, origin_binding=origin_binding,
    ) != launch_admission_record(
        derived, origin_binding=origin_binding,
    ):
        _fail("launch-admission", "supplied admission differs from fresh derivation")


def _load_lifecycle_rows(data: bytes) -> tuple[dict[str, Any], ...]:
    if data and not data.endswith(b"\n"):
        _fail("lifecycle-framing", "lifecycle ledger is not newline terminated")
    rows: list[dict[str, Any]] = []
    starts: set[str] = set()
    terminals: set[str] = set()
    for lineno, line in enumerate(data.splitlines(), 1):
        if not line:
            _fail("lifecycle-framing", f"lifecycle ledger has a blank line at {lineno}")
        value = _decode_json(line, label=f"lifecycle line {lineno}")
        if not isinstance(value, Mapping):
            _fail("lifecycle-schema", f"lifecycle line {lineno} is not an object")
        if _canonical_json_bytes(value) != line:
            _fail("lifecycle-canonical", f"lifecycle line {lineno} is not canonical JSON")
        if value.get("schema_version") != LIFECYCLE_SCHEMA_VERSION:
            _fail("lifecycle-schema", f"lifecycle line {lineno} has bad schema_version")
        event = value.get("event")
        if event == "start":
            _exact_keys(value, _LIFECYCLE_START_KEYS, label=f"lifecycle line {lineno}")
        elif event == "terminal":
            if frozenset(value) not in _LIFECYCLE_TERMINAL_KEYS:
                _fail(
                    "lifecycle-schema",
                    f"lifecycle line {lineno} terminal exact keys differ",
                )
        else:
            _fail("lifecycle-schema", f"lifecycle line {lineno} has unknown event")
        trial_id = value.get("trial_id")
        if not isinstance(trial_id, str) or _TRIAL_ID_RE.fullmatch(trial_id) is None:
            _fail("lifecycle-schema", f"lifecycle line {lineno} has invalid trial_id")
        if event == "start":
            if trial_id in starts:
                _fail("lifecycle-duplicate-start", f"trial_id already started: {trial_id}")
            starts.add(trial_id)
            if value["mode"] != "registered-effective":
                _fail("lifecycle-schema", "only registered-effective starts are recorded")
            if not isinstance(value["run_root"], str) or not value["run_root"]:
                _fail("lifecycle-schema", "start run_root must be a non-empty string")
            for field, pattern in (
                ("manifest_sha256", _SHA256_RE),
                ("measurement_head", _COMMIT_RE),
                ("activation_report_digest_sha256", _SHA256_RE),
                ("launch_admission_sha256", _SHA256_RE),
            ):
                raw = value[field]
                if not isinstance(raw, str) or pattern.fullmatch(raw) is None:
                    _fail("lifecycle-schema", f"start {field} is invalid")
        else:
            if trial_id not in starts:
                _fail("lifecycle-terminal", f"terminal precedes start: {trial_id}")
            if trial_id in terminals:
                _fail("lifecycle-terminal", f"trial_id already has terminal row: {trial_id}")
            terminals.add(trial_id)
            if value["terminal_status"] not in {"complete", "partial", "indeterminate"}:
                _fail("lifecycle-schema", "terminal_status is outside the closed set")
            for field in ("report_sha256", "attempt_journal_sha256"):
                raw = value[field]
                if raw is not None and (
                    not isinstance(raw, str) or _SHA256_RE.fullmatch(raw) is None
                ):
                    _fail("lifecycle-schema", f"terminal {field} is invalid")
            if "origin_terminal_projection" in value:
                _validate_origin_terminal_projection(
                    value["origin_terminal_projection"],
                    gate="lifecycle-schema",
                )
        rows.append(dict(value))
    return tuple(rows)


def _lifecycle_history_tip(
    *,
    repository_root: Path,
    relative_path: str,
    current_head: str,
) -> bytes | None:
    """Validate committed append-only history within one Git repository.

    Independent clones and repositories remain outside this guarantee.  Every
    committed version in this repository must be a strict prefix extension;
    deletion followed by recreation and edit followed by revert are rejected.
    """
    result = _git(repository_root, (
        "log", "--format=%H", "--reverse", "--full-history", current_head,
        "--", relative_path,
    ))
    if result.returncode != 0:
        raise TrialRegistryError("[git-operational] lifecycle history walk failed")
    previous: bytes | None = None
    for raw_commit in result.stdout.splitlines():
        try:
            commit_id = raw_commit.decode("ascii")
        except UnicodeDecodeError as exc:
            raise TrialRegistryError(
                "[git-operational] lifecycle history returned non-ASCII"
            ) from exc
        if _COMMIT_RE.fullmatch(commit_id) is None:
            _fail("lifecycle-history", "history returned an invalid commit ID")
        blob = _blob_at_commit(
            repository_root, commit_id=commit_id, relative_path=relative_path,
        )
        if blob is None:
            _fail("lifecycle-history", "lifecycle path was deleted in committed history")
        _load_lifecycle_rows(blob)
        if previous is not None and (
            not blob.startswith(previous) or len(blob) <= len(previous)
        ):
            _fail(
                "lifecycle-history",
                "lifecycle history is not a strict prefix extension",
            )
        previous = blob
    return previous


def _locked_lifecycle_update(
    *,
    repository_root: Path,
    lifecycle_path: Path,
    update,
):
    root = _repository_root(repository_root)
    _candidate, relative_path, relative = _registry_relative_target(
        lifecycle_path, root,
    )
    history_tip = _lifecycle_history_tip(
        repository_root=root,
        relative_path=relative,
        current_head=resolve_measurement_commit(root),
    )
    parent_fd = _open_registry_parent(root, relative_path.parent, create=True)
    try:
        flags = os.O_RDWR | os.O_APPEND | os.O_CREAT
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(relative_path.name, flags, 0o644, dir_fd=parent_fd)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                _fail("lifecycle-path", "lifecycle ledger is not a regular file")
            rebound = os.stat(
                relative_path.name, dir_fd=parent_fd, follow_symlinks=False,
            )
            if (rebound.st_dev, rebound.st_ino) != (info.st_dev, info.st_ino):
                _fail("lifecycle-path", "lifecycle path changed under lock")
            current = bytearray()
            offset = 0
            while offset < info.st_size:
                chunk = os.pread(fd, min(1024 * 1024, info.st_size - offset), offset)
                if not chunk:
                    _fail("lifecycle-read", "lifecycle read stopped before fstat size")
                current.extend(chunk)
                offset += len(chunk)
            rows = _load_lifecycle_rows(bytes(current))
            if history_tip is not None and not bytes(current).startswith(history_tip):
                _fail(
                    "lifecycle-history",
                    "working lifecycle ledger does not extend committed history",
                )
            payload, result = update(rows)
            if payload is not None:
                view = memoryview(payload)
                while view:
                    written = os.write(fd, view)
                    if written <= 0:
                        raise OSError("lifecycle append did not advance")
                    view = view[written:]
                os.fsync(fd)
                os.fsync(parent_fd)
            return result
        finally:
            os.close(fd)
    except TrialRegistryError:
        raise
    except OSError as exc:
        raise TrialRegistryError(f"[lifecycle-io] lifecycle update failed: {exc}") from exc
    finally:
        os.close(parent_fd)


def record_trial_start_once(
    *,
    admission: TrialLaunchAdmission,
    effective_preregistration: s8c_preregistration.EffectivePreregistration,
    manifest_path: Path,
    run_root: Path,
    repository_root: Path,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    lifecycle_path: Path = DEFAULT_LIFECYCLE_PATH,
    origin_binding: OriginBindingCapability | None = None,
) -> TrialLifecycleToken:
    """Atomically record one formal start in a single shared lifecycle ledger.

    Runtime start-once is limited to processes sharing this ledger.  Committed
    append-only history is checked within one Git repository; no guarantee is
    claimed across independent clones or repositories.
    """
    assert_rederived_launch_admission(
        admission,
        effective_preregistration=effective_preregistration,
        manifest_path=Path(manifest_path),
        trial_id=admission.trial_id,
        workloads=admission.workloads,
        allow_unregistered_exploratory=False,
        repository_root=repository_root,
        registry_path=registry_path,
        origin_binding=origin_binding,
    )
    if admission.mode != "registered-effective" or admission.binding is None:
        _fail("lifecycle-start", "only registered-effective admission may start")
    binding = admission.binding
    admission_sha256 = hashlib.sha256(
        _canonical_json_bytes(
            launch_admission_record(admission, origin_binding=origin_binding)
        )
    ).hexdigest()
    row = {
        "schema_version": LIFECYCLE_SCHEMA_VERSION,
        "event": "start",
        "trial_id": admission.trial_id,
        "run_root": os.path.abspath(os.fspath(run_root)),
        "mode": admission.mode,
        "manifest_sha256": binding.manifest_sha256,
        "measurement_head": binding.measurement_head,
        "activation_report_digest_sha256": (
            admission.activation_report_digest_sha256
        ),
        "launch_admission_sha256": admission_sha256,
    }
    raw = _canonical_json_bytes(row)
    payload = raw + b"\n"
    root = _repository_root(repository_root)
    ledger, _relative = _canonical_lifecycle_target(
        lifecycle_path, root, create_parent=True,
    )

    def append_start(rows):
        if any(item["event"] == "start" and item["trial_id"] == admission.trial_id for item in rows):
            _fail(
                "lifecycle-start-once",
                f"trial_id already has a start row: {admission.trial_id}",
            )
        token = TrialLifecycleToken(
            repository_root=root,
            lifecycle_path=ledger,
            trial_id=admission.trial_id,
            run_root=row["run_root"],
            start_row_sha256=hashlib.sha256(raw).hexdigest(),
            launch_admission_sha256=admission_sha256,
            _seal=_TRIAL_LIFECYCLE_TOKEN_SEAL,
        )
        state = _TrialLifecycleCapabilityState(
            token=token,
            repository_root=root,
            lifecycle_path=ledger,
            trial_id=admission.trial_id,
            run_root=row["run_root"],
            start_row_sha256=token.start_row_sha256,
            launch_admission_sha256=admission_sha256,
            origin_binding=origin_binding,
        )
        return payload, (token, state)

    token, state = _locked_lifecycle_update(
        repository_root=root,
        lifecycle_path=ledger,
        update=append_start,
    )
    with _TRIAL_LIFECYCLE_CAPABILITIES_LOCK:
        if id(token) in _TRIAL_LIFECYCLE_CAPABILITIES:
            _fail("lifecycle-token", "issued token identity is not unique")
        _TRIAL_LIFECYCLE_CAPABILITIES[id(token)] = state
    return token


def record_trial_terminal(
    token: TrialLifecycleToken,
    *,
    terminal_status: str,
    origin_terminal_projection: OriginTerminalProjection | None = None,
) -> None:
    """Consume one start token and append the optional formal projection."""
    if (
        type(token) is not TrialLifecycleToken
        or token._seal is not _TRIAL_LIFECYCLE_TOKEN_SEAL
    ):
        _fail("lifecycle-token", "token was not issued by record_trial_start_once")
    if terminal_status not in {"complete", "partial", "indeterminate"}:
        _fail("lifecycle-terminal", "terminal_status is outside the closed set")
    projection_record = None
    if origin_terminal_projection is not None:
        from . import reflux_formal_consumer

        projection_record = (
            reflux_formal_consumer.origin_terminal_projection_record(
                origin_terminal_projection
            )
        )
    with _TRIAL_LIFECYCLE_CAPABILITIES_LOCK:
        state = _TRIAL_LIFECYCLE_CAPABILITIES.get(id(token))
        if state is None or state.token is not token:
            _fail(
                "lifecycle-token",
                "terminal requires the exact object issued at lifecycle start",
            )
        if state.consumed:
            _fail("lifecycle-token", "lifecycle capability was already consumed")
        if (state.origin_binding is None) != (projection_record is None):
            _fail(
                "lifecycle-origin",
                "origin binding and terminal projection presence differ",
            )
        if state.origin_binding is not None:
            from . import reflux_origin_binding

            origin_record = reflux_origin_binding.origin_binding_capability_record(
                state.origin_binding
            )
            terminal_record = projection_record["origin_terminal_projection"]
            if any(
                terminal_record[field] != origin_record[field]
                for field in ("authority_blob_sha256", "origin_id", "cell_key")
            ):
                _fail(
                    "lifecycle-origin",
                    "terminal projection differs from the start origin binding",
                )
        state.consumed = True

    if terminal_status == "indeterminate":
        report_sha256 = None
        attempt_journal_sha256 = None
    else:
        run_root = Path(state.run_root)
        report_bytes = _read_regular_bytes(
            run_root / "report.json",
            gate="lifecycle-terminal-artifact",
            label="terminal report",
        )
        journal_bytes = _read_regular_bytes(
            run_root / "attempts.jsonl",
            gate="lifecycle-terminal-artifact",
            label="attempt journal",
        )
        report_sha256 = hashlib.sha256(report_bytes).hexdigest()
        attempt_journal_sha256 = hashlib.sha256(journal_bytes).hexdigest()
    row = {
        "schema_version": LIFECYCLE_SCHEMA_VERSION,
        "event": "terminal",
        "trial_id": state.trial_id,
        "terminal_status": terminal_status,
        "report_sha256": report_sha256,
        "attempt_journal_sha256": attempt_journal_sha256,
    }
    if projection_record is not None:
        row.update(projection_record)
    payload = _canonical_json_bytes(row) + b"\n"

    def append_terminal(rows):
        starts = [
            item for item in rows
            if item["event"] == "start" and item["trial_id"] == state.trial_id
        ]
        if len(starts) != 1:
            _fail("lifecycle-token", "token start row is absent or ambiguous")
        start_raw = _canonical_json_bytes(starts[0])
        if (
            hashlib.sha256(start_raw).hexdigest() != state.start_row_sha256
            or starts[0]["run_root"] != state.run_root
            or starts[0]["launch_admission_sha256"]
            != state.launch_admission_sha256
        ):
            _fail("lifecycle-token", "token does not match its start row")
        if any(
            item["event"] == "terminal" and item["trial_id"] == state.trial_id
            for item in rows
        ):
            _fail("lifecycle-terminal-once", "trial already has a terminal row")
        return payload, None

    _locked_lifecycle_update(
        repository_root=state.repository_root,
        lifecycle_path=state.lifecycle_path,
        update=append_terminal,
    )


def assert_campaign_binding(
    binding: TrialBinding,
    *,
    actual_campaign_id: str,
) -> None:
    """Compare producer-derived campaign identity with the declaration."""
    if not isinstance(binding, TrialBinding):
        _fail("campaign-binding", "binding is not a TrialBinding")
    if actual_campaign_id != binding.campaign_id:
        _fail("campaign-binding", "producer campaign_id differs from the manifest")


def _open_regular_snapshot(
    path: Path,
    *,
    gate: str,
    label: str,
) -> tuple[int, bytes]:
    """Read one regular-file snapshot while retaining its bound descriptor."""
    path = Path(path)
    try:
        before = path.lstat()
    except OSError as exc:
        raise TrialRegistryError(f"[{gate}] {label} cannot be stated: {path}") from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        _fail(gate, f"{label} must be a regular non-symlink file: {path}")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise TrialRegistryError(f"[{gate}] {label} cannot be opened: {path}") from exc
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode):
            _fail(gate, f"{label} changed away from a regular file: {path}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(fd)
        identity_before = (
            before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns,
        )
        identity_after = (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns,
        )
        if identity_before != identity_after:
            _fail(gate, f"{label} changed while it was being read: {path}")
        os.lseek(fd, 0, os.SEEK_SET)
        return fd, b"".join(chunks)
    except BaseException:
        os.close(fd)
        raise


def _read_report_and_journal(
    report_path: Path,
) -> _LoadedReport:
    original = Path(report_path)
    report_bytes = _read_regular_bytes(original, gate="report-path", label="report")
    try:
        resolved_report = original.resolve(strict=True)
    except OSError as exc:
        raise TrialRegistryError(f"[report-path] report cannot be resolved: {original}") from exc
    journal = resolved_report.parent / "attempts.jsonl"
    journal_fd, journal_bytes = _open_regular_snapshot(
        journal, gate="report-path", label="attempts journal",
    )
    try:
        expected_report = (journal.resolve(strict=True).parent / "report.json").resolve(strict=True)
    except OSError as exc:
        os.close(journal_fd)
        raise TrialRegistryError("[report-path] report/journal sibling identity cannot be resolved") from exc
    try:
        if resolved_report != expected_report:
            _fail("report-path", "report argument is not the attempts.jsonl sibling report.json")
        report = _decode_json(report_bytes, label="report")
        if not isinstance(report, dict):
            _fail("report-shape", "report root is not an object")
        if not journal_bytes or not journal_bytes.endswith(b"\n"):
            _fail("run-start-binding", "attempt journal is not newline terminated")
        events: list[Mapping[str, Any]] = []
        for lineno, line in enumerate(journal_bytes.splitlines(), 1):
            event = _decode_json(line, label=f"attempt journal line {lineno}")
            if not isinstance(event, Mapping):
                _fail("run-start-binding", f"attempt journal line {lineno} is not an object")
            events.append(event)
        return _LoadedReport(
            report,
            resolved_report,
            report_bytes,
            journal,
            journal_fd,
            journal_bytes,
            events,
        )
    except BaseException:
        os.close(journal_fd)
        raise


def _assert_snapshot_completeness(item: _LoadedReport) -> None:
    """Run the existing path API over a private view of the one read snapshot."""
    with tempfile.TemporaryDirectory(prefix="izanagi-trial-accept-") as raw_dir:
        snapshot_dir = Path(raw_dir)
        os.chmod(snapshot_dir, 0o700)
        snapshot_report_path = snapshot_dir / "report.json"
        fd, raw_path = tempfile.mkstemp(
            prefix="attempts-", suffix=".jsonl", dir=snapshot_dir,
        )
        snapshot_path = Path(raw_path)
        rebound_events = []
        for event in item.events:
            rebound = dict(event)
            if rebound.get("event") == "run-finish":
                rebound["report"] = str(snapshot_report_path)
            rebound_events.append(rebound)
        snapshot_bytes = b"".join(
            _canonical_json_bytes(event) + b"\n" for event in rebound_events
        )
        snapshot_report = dict(item.report)
        snapshot_report["attempt_journal"] = str(snapshot_path)
        snapshot_report["attempt_journal_sha256"] = hashlib.sha256(
            snapshot_bytes
        ).hexdigest()
        try:
            view = memoryview(snapshot_bytes)
            while view:
                written = os.write(fd, view)
                if written <= 0:
                    raise OSError("journal snapshot copy did not advance")
                view = view[written:]
            os.fsync(fd)
        except OSError as exc:
            raise TrialRegistryError(
                f"[journal-snapshot] private snapshot cannot be written: {exc}"
            ) from exc
        finally:
            os.close(fd)
        try:
            snapshot_report_path.write_bytes(_canonical_json_bytes(snapshot_report))
        except OSError as exc:
            raise TrialRegistryError(
                f"[journal-snapshot] private report cannot be written: {exc}"
            ) from exc
        try:
            assert_autonomous_trial_completeness(
                report=snapshot_report,
                attempt_journal=snapshot_path,
            )
        except AutonomousTrialCompletenessError as exc:
            raise TrialRegistryError(f"[terminal-completeness] {exc}") from exc
        expected_hash = hashlib.sha256(item.journal_bytes).hexdigest()
        if item.report.get("attempt_journal_sha256") != expected_hash:
            _fail(
                "terminal-completeness",
                "attempt_journal_sha256 does not match the captured journal bytes",
            )
        journal_reference = item.report.get("attempt_journal")
        if not isinstance(journal_reference, str) or not journal_reference:
            _fail(
                "terminal-completeness",
                "report attempt_journal is not a non-empty path string",
            )
        try:
            same_journal = Path(journal_reference).samefile(item.journal_path)
        except OSError as exc:
            raise TrialRegistryError(
                "[terminal-completeness] report attempt_journal cannot be resolved"
            ) from exc
        if not same_journal:
            _fail(
                "terminal-completeness",
                "report attempt_journal differs from the captured journal path",
            )
        finishes = [
            event for event in item.events if event.get("event") == "run-finish"
        ]
        if len(finishes) != 1:
            _fail(
                "terminal-completeness",
                "captured journal must contain exactly one run-finish event",
            )
        finish_report = finishes[0].get("report")
        if (
            not isinstance(finish_report, str)
            or Path(finish_report).resolve()
            != (item.journal_path.parent / "report.json").resolve()
        ):
            _fail(
                "terminal-completeness",
                "run-finish report differs from the captured report path",
            )


def _assert_history_append_only(
    *,
    repository_root: Path,
    relative_path: str,
    measurement_head: str,
    current_head: str,
    measurement_bytes: bytes,
    current_bytes: bytes,
) -> None:
    _assert_ancestor(
        repository_root,
        ancestor=measurement_head,
        descendant=current_head,
        gate="registry-history",
        message="measurement_head is not an ancestor of current HEAD",
    )
    result = _git(repository_root, (
        "rev-list", "--full-history", "--reverse", "--topo-order",
        f"{measurement_head}..{current_head}", "--", relative_path,
    ))
    if result.returncode != 0:
        raise TrialRegistryError("[git-operational] registry history walk failed")
    previous = measurement_bytes
    for raw_commit in result.stdout.splitlines():
        try:
            commit_id = raw_commit.decode("ascii")
        except UnicodeDecodeError as exc:
            raise TrialRegistryError("[git-operational] history returned non-ASCII commit") from exc
        if _COMMIT_RE.fullmatch(commit_id) is None:
            _fail("registry-history", "history returned an invalid commit ID")
        blob = _blob_at_commit(
            repository_root, commit_id=commit_id, relative_path=relative_path,
        )
        if blob is None:
            _fail("registry-history", "registry path was deleted in committed history")
        if not blob.startswith(previous) or len(blob) <= len(previous):
            _fail("registry-history", "registry history is not a strict prefix extension")
        _load_registry_bytes(blob, label=f"registry at {commit_id}")
        previous = blob
    if previous != current_bytes:
        _fail("registry-history", "history endpoint differs from current registry blob")


def _registry_introduction_commit(
    *,
    repository_root: Path,
    relative_path: str,
    current_head: str,
) -> str:
    """Return the sole commit that introduced the registry path.

    This proves only that the registry path has one history genesis.  It is
    not an approval-authority attestation and must never be interpreted as
    evidence that T-468 approval authority exists.
    """
    result = _git(repository_root, (
        "log", "--format=%H", "--diff-filter=A", "--full-history",
        current_head, "--", relative_path,
    ))
    if result.returncode != 0:
        raise TrialRegistryError(
            "[git-operational] registry introduction history walk failed"
        )
    introductions: list[str] = []
    for raw in result.stdout.splitlines():
        try:
            commit_id = raw.decode("ascii")
        except UnicodeDecodeError as exc:
            raise TrialRegistryError(
                "[git-operational] registry introduction returned non-ASCII"
            ) from exc
        if _COMMIT_RE.fullmatch(commit_id) is None:
            _fail("registry-introduction", "history returned an invalid commit ID")
        if _blob_at_commit(
            repository_root,
            commit_id=commit_id,
            relative_path=relative_path,
        ) is None:
            _fail("registry-introduction", "introduction commit has no registry blob")
        introductions.append(commit_id)
    if len(introductions) != 1:
        _fail(
            "registry-introduction",
            "registry path must have exactly one introduction commit",
        )
    return introductions[0]


def _receipt_lifecycle_snapshot(
    *,
    repository_root: Path,
    lifecycle_path: Path,
    manifest: TrialManifest,
    accepted_by_id: Mapping[str, AcceptedTrial],
    loaded_by_id: Mapping[str, _LoadedReport],
    activation_report_digest_sha256: str,
) -> tuple[bytes, str]:
    lifecycle, relative = _canonical_lifecycle_target(
        lifecycle_path, repository_root, create_parent=False,
    )
    lifecycle_bytes = _read_regular_bytes(
        lifecycle, gate="lifecycle-read", label="lifecycle ledger",
    )
    history_tip = _lifecycle_history_tip(
        repository_root=repository_root,
        relative_path=relative,
        current_head=resolve_measurement_commit(repository_root),
    )
    if history_tip is not None and not lifecycle_bytes.startswith(history_tip):
        _fail(
            "lifecycle-history",
            "working lifecycle ledger does not extend committed history",
        )
    rows = _load_lifecycle_rows(lifecycle_bytes)
    for trial in manifest.trials:
        starts = [
            row for row in rows
            if row["event"] == "start" and row["trial_id"] == trial.trial_id
        ]
        terminals = [
            row for row in rows
            if row["event"] == "terminal" and row["trial_id"] == trial.trial_id
        ]
        if len(starts) != 1:
            _fail(
                "acceptance-lifecycle",
                f"trial {trial.trial_id!r} must have exactly one start row",
            )
        if len(terminals) != 1:
            _fail(
                "acceptance-lifecycle",
                f"trial {trial.trial_id!r} must have exactly one terminal row",
            )
        accepted = accepted_by_id[trial.trial_id]
        item = loaded_by_id[trial.trial_id]
        start = starts[0]
        try:
            start_run_root = Path(start["run_root"]).resolve(strict=True)
            report_parent = item.report_path.parent.resolve(strict=True)
            journal_parent = item.journal_path.parent.resolve(strict=True)
        except OSError as exc:
            raise TrialRegistryError(
                "[acceptance-lifecycle] run artifact parent cannot be resolved"
            ) from exc
        if start_run_root != report_parent or start_run_root != journal_parent:
            _fail(
                "acceptance-lifecycle",
                f"trial {trial.trial_id!r} start run_root differs from "
                "report/journal parent",
            )
        if (
            start["manifest_sha256"] != manifest.sha256
            or start["measurement_head"] != accepted.measurement_head
            or start["activation_report_digest_sha256"]
            != activation_report_digest_sha256
            or start["launch_admission_sha256"]
            != hashlib.sha256(
                _canonical_json_bytes(item.report["launch_admission"])
            ).hexdigest()
        ):
            _fail(
                "acceptance-lifecycle",
                f"trial {trial.trial_id!r} start row differs from accepted bytes",
            )
        terminal = terminals[0]
        report_has_origin = "origin_terminal_projection" in item.report
        terminal_has_origin = "origin_terminal_projection" in terminal
        if report_has_origin != terminal_has_origin:
            _fail(
                "acceptance-lifecycle",
                f"trial {trial.trial_id!r} origin terminal projection presence differs",
            )
        if report_has_origin:
            report_projection = _validate_origin_terminal_projection(
                item.report["origin_terminal_projection"],
                gate="acceptance-lifecycle",
            )
            lifecycle_projection = _validate_origin_terminal_projection(
                terminal["origin_terminal_projection"],
                gate="acceptance-lifecycle",
            )
            if _canonical_json_bytes(report_projection) != _canonical_json_bytes(
                lifecycle_projection
            ):
                _fail(
                    "acceptance-lifecycle",
                    f"trial {trial.trial_id!r} origin terminal projection differs",
                )
        if (
            terminal["terminal_status"] != accepted.status
            or terminal["report_sha256"]
            != hashlib.sha256(item.report_bytes).hexdigest()
            or terminal["attempt_journal_sha256"]
            != hashlib.sha256(item.journal_bytes).hexdigest()
        ):
            _fail(
                "acceptance-lifecycle",
                f"trial {trial.trial_id!r} terminal row differs from accepted bytes",
            )
    return lifecycle_bytes, relative


def _expected_registered_launch_admission_record(
    *,
    manifest_path: Path,
    registry_path: Path,
    repository_root: Path,
    trial: TrialSpec,
    measurement_head: str,
    activation_report_digest_sha256: str,
    origin_binding_record: object | None = None,
) -> dict[str, Any]:
    workload = HOLDOUT_BINDINGS[trial.holdout]["workload"]
    manifest = load_trial_manifest(manifest_path)
    manifest_relative = _require_committed_file(
        repository_root=repository_root,
        commit_id=measurement_head,
        path=manifest_path,
        label="manifest",
        expected_bytes=manifest.raw_bytes,
    )
    _registry, registry_relative = _registry_target(
        registry_path, repository_root, create_parent=False,
    )
    registry_bytes = _blob_at_commit(
        repository_root,
        commit_id=measurement_head,
        relative_path=registry_relative,
    )
    if registry_bytes is None:
        _fail("historical-binding", "measurement registry blob is absent")
    _find_registration(
        _load_registry_bytes(registry_bytes, label="measurement registry"),
        _registration_for(manifest),
    )
    assert_prereg_ancestor(
        repository_root,
        prereg_commit=manifest.prereg_commit,
        measurement_commit=measurement_head,
    )
    if manifest_relative == registry_relative:
        _fail("historical-binding", "manifest and registry paths alias")
    binding = {
        "manifest_sha256": manifest.sha256,
        "prereg_commit": manifest.prereg_commit,
        "measurement_head": measurement_head,
        "trial_id": trial.trial_id,
        "arm": trial.arm,
        "holdout": trial.holdout,
        "campaign_id": trial.campaign_id,
        "workload": workload,
        "ycsb_rratio": HOLDOUT_BINDINGS[trial.holdout]["ycsb_rratio"],
    }
    record = {
        "mode": "registered-effective",
        "certifying": False,
        "reason_code": "registered-effective-non-certifying",
        "trial_id": trial.trial_id,
        "workloads": [workload],
        "binding": binding,
        "activation_report_digest_sha256": activation_report_digest_sha256,
    }
    if origin_binding_record is not None:
        record["origin_binding"] = _validate_origin_binding_record(
            origin_binding_record,
            trial=trial,
            measurement_head=measurement_head,
            gate="acceptance-launch-admission",
        )
    return record


def _exclusive_create_acceptance_receipt(
    *,
    repository_root: Path,
    manifest_sha256: str,
    value: Mapping[str, Any],
) -> tuple[str, str]:
    relative_path = Path(
        s8c_acceptance_receipt.DEFAULT_RECEIPT_DIR.as_posix()
    ) / f"{manifest_sha256}.json"
    parent_fd = _open_registry_parent(
        repository_root, relative_path.parent, create=True,
    )
    payload = _canonical_json_bytes(value) + b"\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        try:
            fd = os.open(relative_path.name, flags, 0o644, dir_fd=parent_fd)
        except FileExistsError as exc:
            raise TrialRegistryError(
                "[receipt-exclusive-create] acceptance receipt already exists"
            ) from exc
        try:
            view = memoryview(payload)
            while view:
                written = os.write(fd, view)
                if written <= 0:
                    raise OSError("receipt write did not advance")
                view = view[written:]
            os.fsync(fd)
            os.fsync(parent_fd)
        finally:
            os.close(fd)
    except TrialRegistryError:
        raise
    except OSError as exc:
        raise TrialRegistryError(f"[receipt-io] receipt cannot be created: {exc}") from exc
    finally:
        os.close(parent_fd)
    return relative_path.as_posix(), hashlib.sha256(payload).hexdigest()


def assert_trial_registry_acceptance(
    *,
    effective_preregistration: s8c_preregistration.EffectivePreregistration,
    manifest_path: Path,
    report_paths: Sequence[Path],
    repository_root: Path,
    registry_path: Path,
    lifecycle_path: Path = DEFAULT_LIFECYCLE_PATH,
) -> AcceptanceSummary:
    """Verify formal acceptance and exclusively issue its canonical receipt."""
    if len(report_paths) != 6:
        _fail("report-count", "acceptance requires exactly 6 report paths")
    root = _repository_root(repository_root)
    current_head = resolve_measurement_commit(root)
    manifest = load_trial_manifest(Path(manifest_path))
    if (
        not isinstance(
            effective_preregistration,
            s8c_preregistration.EffectivePreregistration,
        )
        or effective_preregistration.commit != manifest.prereg_commit
    ):
        _fail(
            "effective-preregistration",
            "acceptance requires the manifest's exact EffectivePreregistration",
        )
    try:
        s8c_preregistration.require_effective_preregistration(
            effective_preregistration,
            repo_root=root,
            commit=manifest.prereg_commit,
        )
    except s8c_preregistration.PreregistrationError as exc:
        _fail("effective-preregistration", f"{exc.reason}: {exc}")
    manifest_relative = _require_committed_file(
        repository_root=root,
        commit_id=current_head,
        path=Path(manifest_path),
        label="manifest",
        expected_bytes=manifest.raw_bytes,
    )
    registrations, current_registry_bytes, registry_relative = _load_committed_registry(
        repository_root=root,
        registry_path=Path(registry_path),
        commit_id=current_head,
    )
    expected_registration = _registration_for(manifest)
    _find_registration(registrations, expected_registration)
    assert_prereg_ancestor(
        root,
        prereg_commit=manifest.prereg_commit,
        measurement_commit=current_head,
    )

    loaded: list[_LoadedReport] = []
    try:
        for path in report_paths:
            loaded.append(_read_report_and_journal(Path(path)))
        trial_ids = [item.report.get("trial_id") for item in loaded]
        expected_ids = {trial.trial_id for trial in manifest.trials}
        if (
            any(not isinstance(trial_id, str) for trial_id in trial_ids)
            or len(set(trial_ids)) != len(trial_ids)
            or set(trial_ids) != expected_ids
        ):
            _fail("trial-set", "report trial_id set is not the exact manifest trial set")

        manifest_by_id = {trial.trial_id: trial for trial in manifest.trials}
        accepted: list[AcceptedTrial] = []
        history_checked: set[str] = set()
        for item in loaded:
            report = item.report
            events = item.events
            trial_id = report["trial_id"]
            trial = manifest_by_id[trial_id]
            _assert_snapshot_completeness(item)
            item.assert_snapshot_unchanged()
            if (
                report.get("generation_budget_per_workload")
                != trial.generations
            ):
                _fail(
                    "generation-binding",
                    "report generation_budget_per_workload differs from "
                    f"manifest.trials[{trial_id!r}].generations",
                )
            starts = [event for event in events if event.get("event") == "run-start"]
            if len(starts) != 1:
                _fail("run-start-binding", "journal must contain exactly one run-start event")
            start = starts[0]
            for field in ("prereg_commit", "measurement_head", "manifest_sha256"):
                if field not in report or field not in start or report[field] != start[field]:
                    _fail("run-start-binding", f"report/run-start mismatch or missing field: {field}")
            if report["prereg_commit"] != manifest.prereg_commit:
                _fail("acceptance-binding", "report prereg_commit differs from manifest")
            if report["manifest_sha256"] != manifest.sha256:
                _fail("acceptance-binding", "report manifest_sha256 differs from manifest bytes")
            measurement_head = report["measurement_head"]
            if not isinstance(measurement_head, str) or _COMMIT_RE.fullmatch(measurement_head) is None:
                _fail("acceptance-binding", "report measurement_head is not a full commit ID")
            assert_prereg_ancestor(
                root,
                prereg_commit=manifest.prereg_commit,
                measurement_commit=measurement_head,
            )
            report_admission = report.get("launch_admission")
            start_admission = start.get("launch_admission")
            if (
                not isinstance(report_admission, Mapping)
                or not isinstance(start_admission, Mapping)
                or dict(report_admission) != dict(start_admission)
            ):
                _fail(
                    "acceptance-launch-admission",
                    "report and run-start launch_admission must exist and match exactly",
                )
            if frozenset(report_admission) not in _LAUNCH_ADMISSION_KEYS:
                _fail(
                    "acceptance-launch-admission",
                    "launch_admission exact keys are not the closed 7/8 alternatives",
                )
            origin_binding_record = None
            if "origin_binding" in report_admission:
                origin_binding_record = _validate_origin_binding_record(
                    report_admission["origin_binding"],
                    trial=trial,
                    measurement_head=measurement_head,
                    gate="acceptance-launch-admission",
                )
            expected_admission = _expected_registered_launch_admission_record(
                manifest_path=Path(manifest_path),
                registry_path=Path(registry_path),
                repository_root=root,
                trial=trial,
                measurement_head=measurement_head,
                activation_report_digest_sha256=(
                    effective_preregistration.report_digest_sha256
                ),
                origin_binding_record=origin_binding_record,
            )
            if dict(report_admission) != expected_admission:
                _fail(
                    "acceptance-launch-admission",
                    "launch_admission differs from the accepted binding derivation",
                )
            has_terminal_projection = "origin_terminal_projection" in report
            if (origin_binding_record is None) != (not has_terminal_projection):
                _fail(
                    "acceptance-origin",
                    "origin binding and terminal projection presence differ",
                )
            if origin_binding_record is not None:
                terminal_projection = _validate_origin_terminal_projection(
                    report["origin_terminal_projection"],
                    gate="acceptance-origin",
                )
                if any(
                    terminal_projection[field] != origin_binding_record[field]
                    for field in (
                        "authority_blob_sha256", "origin_id", "cell_key",
                    )
                ):
                    _fail(
                        "acceptance-origin",
                        "terminal projection differs from launch origin binding",
                    )
            historical_manifest = _blob_at_commit(
                root, commit_id=measurement_head, relative_path=manifest_relative,
            )
            if historical_manifest != manifest.raw_bytes:
                _fail("historical-binding", "measurement manifest blob differs or is absent")
            historical_registry = _blob_at_commit(
                root, commit_id=measurement_head, relative_path=registry_relative,
            )
            if historical_registry is None:
                _fail("historical-binding", "measurement registry blob is absent")
            historical_registrations = _load_registry_bytes(
                historical_registry, label="measurement registry",
            )
            _find_registration(historical_registrations, expected_registration)
            if not current_registry_bytes.startswith(historical_registry):
                _fail("registry-prefix", "measurement registry is not a current registry prefix")
            if measurement_head not in history_checked:
                _assert_history_append_only(
                    repository_root=root,
                    relative_path=registry_relative,
                    measurement_head=measurement_head,
                    current_head=current_head,
                    measurement_bytes=historical_registry,
                    current_bytes=current_registry_bytes,
                )
                history_checked.add(measurement_head)
            expected_workload = HOLDOUT_BINDINGS[trial.holdout]
            if report.get("workloads_requested") != [expected_workload["workload"]]:
                _fail("terminal-projection", "report workload does not match trial holdout")
            cells = report.get("cells")
            if not isinstance(cells, list) or len(cells) > 1:
                _fail("terminal-projection", "report cells must contain zero or one cell")
            if cells:
                cell = cells[0]
                if not isinstance(cell, Mapping):
                    _fail("terminal-projection", "report cell is not an object")
                flags = cell.get("workload_flags")
                if (
                    cell.get("workload") != expected_workload["workload"]
                    or not isinstance(flags, Mapping)
                    or flags.get("ycsb_rratio") != expected_workload["ycsb_rratio"]
                    or cell.get("campaign_id") != trial.campaign_id
                ):
                    _fail("terminal-projection", "report cell differs from manifest projection")
            status = report.get("status")
            if not isinstance(status, str):
                _fail("terminal-projection", "report status is not a string")
            accepted.append(AcceptedTrial(trial_id, status, measurement_head))
        accepted.sort(key=lambda accepted_trial: accepted_trial.trial_id)
        accepted_by_id = {item.trial_id: item for item in accepted}
        loaded_by_id = {item.report["trial_id"]: item for item in loaded}
        lifecycle_bytes, lifecycle_relative = _receipt_lifecycle_snapshot(
            repository_root=root,
            lifecycle_path=Path(lifecycle_path),
            manifest=manifest,
            accepted_by_id=accepted_by_id,
            loaded_by_id=loaded_by_id,
            activation_report_digest_sha256=(
                effective_preregistration.report_digest_sha256
            ),
        )
        introduction_commit = _registry_introduction_commit(
            repository_root=root,
            relative_path=registry_relative,
            current_head=current_head,
        )
        receipt_trials: list[dict[str, Any]] = []
        for trial in sorted(manifest.trials, key=lambda item: item.trial_id):
            item = loaded_by_id[trial.trial_id]
            accepted_trial = accepted_by_id[trial.trial_id]
            item.assert_snapshot_unchanged()
            if _read_regular_bytes(
                item.report_path, gate="report-snapshot", label="trial report",
            ) != item.report_bytes:
                _fail(
                    "report-snapshot",
                    f"trial {trial.trial_id!r} report changed during acceptance",
                )
            _resolved_report, report_relative = _repo_relative(
                item.report_path, root, label="trial report",
            )
            _resolved_journal, journal_relative = _repo_relative(
                item.journal_path, root, label="attempt journal",
            )
            receipt_trial = {
                "trial_id": trial.trial_id,
                "arm": trial.arm,
                "holdout": trial.holdout,
                "campaign_id": trial.campaign_id,
                "status": accepted_trial.status,
                "measurement_head": accepted_trial.measurement_head,
                "report_path": report_relative,
                "report_sha256": hashlib.sha256(item.report_bytes).hexdigest(),
                "attempt_journal_path": journal_relative,
                "attempt_journal_sha256": hashlib.sha256(
                    item.journal_bytes
                ).hexdigest(),
            }
            if "origin_terminal_projection" in item.report:
                receipt_trial["origin_terminal_projection"] = (
                    _validate_origin_terminal_projection(
                        item.report["origin_terminal_projection"],
                        gate="acceptance-trial-projection",
                    )
                )
            receipt_trials.append(receipt_trial)
        reason_codes = sorted(
            s8c_acceptance_receipt.MANDATORY_NON_CERTIFYING_REASONS
        )
        receipt_value = {
            "schema_version": s8c_acceptance_receipt.SCHEMA_VERSION,
            "manifest_path": manifest_relative,
            "manifest_sha256": manifest.sha256,
            "prereg_commit": manifest.prereg_commit,
            "activation_report_digest_sha256": (
                effective_preregistration.report_digest_sha256
            ),
            "registry_path": registry_relative,
            "registry_blob_sha256": hashlib.sha256(
                current_registry_bytes
            ).hexdigest(),
            "registry_introduction_commit": introduction_commit,
            "lifecycle_path": lifecycle_relative,
            "lifecycle_prefix_bytes": len(lifecycle_bytes),
            "lifecycle_prefix_sha256": hashlib.sha256(
                lifecycle_bytes
            ).hexdigest(),
            "certifying": False,
            "non_certifying_reason_codes": reason_codes,
            "trials": receipt_trials,
        }
        receipt_path, receipt_sha256 = _exclusive_create_acceptance_receipt(
            repository_root=root,
            manifest_sha256=manifest.sha256,
            value=receipt_value,
        )
        return AcceptanceSummary(
            manifest_sha256=manifest.sha256,
            trials=tuple(accepted),
            receipt_path=receipt_path,
            receipt_sha256=receipt_sha256,
        )
    finally:
        for item in loaded:
            item.close()


def _summary_dict(summary: AcceptanceSummary) -> dict[str, Any]:
    return {
        "check": "trial-ID completeness (registry)",
        "manifest_sha256": summary.manifest_sha256,
        "receipt_path": summary.receipt_path,
        "receipt_sha256": summary.receipt_sha256,
        "certifying": summary.certifying,
        "arm_binding": summary.arm_binding,
        "trials": [dataclasses.asdict(trial) for trial in summary.trials],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 3 8c trial registry")
    subparsers = parser.add_subparsers(dest="command", required=True)
    register = subparsers.add_parser("register", help="append one manifest registration")
    register.add_argument("--manifest", required=True)
    register.add_argument("--repo-root", required=True)
    register.add_argument("--registry", required=True)
    accept = subparsers.add_parser("accept", help="verify trial-ID completeness")
    accept.add_argument("--manifest", required=True)
    accept.add_argument("--repo-root", required=True)
    accept.add_argument("--registry", required=True)
    accept.add_argument("reports", nargs="+")
    args = parser.parse_args(argv)
    try:
        if args.command == "register":
            registration = append_trial_registration(
                manifest_path=Path(args.manifest),
                repository_root=Path(args.repo_root),
                registry_path=Path(args.registry),
            )
            output = {
                "manifest_sha256": registration.manifest_sha256,
                "registered_trials": len(registration.trials),
                "commit_required": True,
            }
        else:
            manifest = load_trial_manifest(Path(args.manifest))
            effective = s8c_preregistration.effective_at(
                Path(args.repo_root), manifest.prereg_commit,
            )
            summary = assert_trial_registry_acceptance(
                effective_preregistration=effective,
                manifest_path=Path(args.manifest),
                report_paths=[Path(path) for path in args.reports],
                repository_root=Path(args.repo_root),
                registry_path=Path(args.registry),
            )
            output = _summary_dict(summary)
    except TrialRegistryError as exc:
        parser.error(str(exc))
    print(_canonical_json_bytes(output).decode("utf-8"))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
