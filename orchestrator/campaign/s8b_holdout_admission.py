# -*- coding: utf-8 -*-
"""8b floor holdout admission backed by a worktree-shared durable ledger.

The cell claim, not the JSONL evidence row, is the one-shot authority.  Claims
and attempt-consumption markers use ``O_EXCL`` under a root derived only from
Git's common directory, so linked worktrees contend on the same inodes.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import threading
from typing import Any

from ..holdout_observation import (
    HoldoutObservationAdmission,
    HoldoutObservationError,
    MinimalHoldoutSignature,
    _issue_holdout_observation_admission_from_receipt,
    _new_durable_attempt_consumption_receipt,
    _protected_signatures_from_verified_freeze_core,
    assert_issued_holdout_observation,
)
from . import s8b_floor_contract as _floor_contract
from . import s8b_oracle_manifest as _oracle_manifest
from . import s8b_ratified_freeze as _ratified_freeze

__all__ = (
    "CellHoldoutAdmission",
    "FloorHoldoutReservation",
    "HoldoutAdmissionError",
    "OracleCellHoldoutAdmission",
    "OBSERVATION_ROLE_FLOOR_CAMPAIGN",
    "OBSERVATION_ROLE_ORACLE_DRIVER",
    "assert_cell_holdout_admission",
    "consume_attempt_ticket",
    "consume_oracle_attempt_ticket",
    "finalize_floor_holdout_admissions",
    "provision_shared_admission_root",
    "reserve_oracle_holdout_observations",
    "reserve_floor_holdout_observations",
    "shared_admission_root",
)

_PROTOCOL_REL = "output/s8b-freeze/floor_protocol.json"
_FREEZE_REL = "output/s8b-freeze/holdout_freeze.json"
_ROOT_REL = Path("izanagi") / "s8b-holdout-admission-v1"
_LOCK_NAME = "ledger.lock"
_LEDGER_NAME = "ledger.jsonl"
_ATTEMPT_LEDGER_NAME = "attempt-ledger.jsonl"
_CLAIM_SCHEMA = "s8b-holdout-cell-claim/v1"
_LEDGER_SCHEMA = "s8b-holdout-observation-ledger/v1"
_ATTEMPT_SCHEMA = "s8b-holdout-attempt-consumption/v1"
_MAX_LEDGER_BYTES = 16 * 1024 * 1024
_HEX64 = frozenset("0123456789abcdef")
OBSERVATION_ROLE_FLOOR_CAMPAIGN = "floor_campaign"
OBSERVATION_ROLE_ORACLE_DRIVER = "oracle_driver"
_OBSERVATION_ROLES = frozenset({
    OBSERVATION_ROLE_FLOOR_CAMPAIGN,
    OBSERVATION_ROLE_ORACLE_DRIVER,
})


class HoldoutAdmissionError(RuntimeError):
    """The fixed authority or durable one-shot admission cannot be proven."""


@dataclass(frozen=True, slots=True)
class FloorHoldoutReservation:
    """Opaque-by-identity result of the pre-effect cell-claim phase."""

    campaign_run_id: str
    run_relpath: str
    protocol_sha256: str
    freeze_sha256: str


@dataclass(frozen=True, slots=True)
class CellHoldoutAdmission:
    """Opaque cell capability whose attempt tickets are consumed separately."""

    freeze_holdout_key: str
    freeze_candidate_id: str
    trial_workload_name: str
    configuration_id: str
    cell_id: str


@dataclass(frozen=True, slots=True)
class OracleCellHoldoutAdmission:
    """Oracle cell capability whose manifest-derived tickets are separate."""

    freeze_holdout_key: str
    freeze_candidate_id: str
    trial_workload_name: str
    configuration_id: str
    cell_id: str


@dataclass(frozen=True, slots=True)
class _ReservationState:
    token: FloorHoldoutReservation
    root: Path
    measurement_head: str
    protocol: dict[str, Any]
    freeze: dict[str, Any]
    cells: tuple[dict[str, Any], ...]
    schedule: tuple[dict[str, Any], ...]
    claims: tuple[dict[str, Any], ...]
    signatures: Mapping[str, MinimalHoldoutSignature]
    neutral_holdouts: Mapping[str, Mapping[str, object]]
    mode: str
    resume: bool
    measurement_started: bool
    run_dir: Path
    manifest_sha256: str
    protocol_reps: int
    irreversible_pilot_approved: bool


@dataclass(frozen=True, slots=True)
class _CellState:
    token: CellHoldoutAdmission
    root: Path
    row: dict[str, Any]
    claim_digest: str
    attempt_ids: frozenset[str]
    run_dir: Path
    schedule: tuple[dict[str, Any], ...]
    verified_freeze: dict[str, Any]
    neutral_holdouts: Mapping[str, Mapping[str, object]]
    protocol_reps: int


@dataclass(frozen=True, slots=True)
class _OracleCellState:
    token: OracleCellHoldoutAdmission
    root: Path
    row: dict[str, Any]
    claim_digest: str
    attempt_ids_by_schedule_index: Mapping[int, str]
    verified_freeze: dict[str, Any]
    neutral_holdouts: Mapping[str, Mapping[str, object]]
    oracle_reps: int


_reservation_states: dict[int, _ReservationState] = {}
_cell_states: dict[int, _CellState] = {}
_oracle_cell_states: dict[int, _OracleCellState] = {}
_state_lock = threading.RLock()


def _canonical_bytes(value: object) -> bytes:
    try:
        text = json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise HoldoutAdmissionError("admission evidence is not canonical JSON") from exc
    return text.encode("utf-8")


def _canonical_line(value: object) -> bytes:
    return _canonical_bytes(value) + b"\n"


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _mutable_json_tree(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _mutable_json_tree(child) for key, child in value.items()}
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray),
    ):
        return [_mutable_json_tree(child) for child in value]
    return value


def _require_text(value: object, field: str) -> str:
    if type(value) is not str or not value:
        raise HoldoutAdmissionError(f"{field} must be a nonempty exact str")
    return value


def _require_sha256(value: object, field: str) -> str:
    text = _require_text(value, field)
    if len(text) != 64 or any(char not in _HEX64 for char in text):
        raise HoldoutAdmissionError(f"{field} must be lowercase sha256")
    return text


def _portable_run_relpath(value: object) -> str:
    text = _require_text(value, "run_relpath")
    path = PurePosixPath(text)
    if path.is_absolute() or ".." in path.parts or str(path) != text:
        raise HoldoutAdmissionError("run_relpath must be canonical and relative")
    return text


def _run_git(repo_root: Path, *args: str) -> bytes:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), *args], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise HoldoutAdmissionError(f"git authority query failed: {' '.join(args)}") from exc
    return completed.stdout


def _repo_root(repo_root: Path) -> Path:
    candidate = Path(repo_root).resolve()
    top = Path(_run_git(candidate, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    if top != candidate:
        raise HoldoutAdmissionError("repo_root is not the exact Git worktree root")
    return candidate


def shared_admission_root(repo_root: Path) -> Path:
    """Resolve the physical root shared by all worktrees of one repository."""

    root = _repo_root(repo_root)
    raw = _run_git(root, "rev-parse", "--git-common-dir").decode("utf-8").strip()
    if not raw:
        raise HoldoutAdmissionError("git common directory is empty")
    common = Path(raw)
    if not common.is_absolute():
        common = root / common
    common = common.resolve()
    try:
        mode = common.lstat().st_mode
    except OSError as exc:
        raise HoldoutAdmissionError("git common directory is unavailable") from exc
    if not stat.S_ISDIR(mode):
        raise HoldoutAdmissionError("git common directory is not a directory")
    return common / _ROOT_REL


def _fsync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _ensure_private_directory(path: Path) -> None:
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    mode = path.lstat().st_mode
    if not stat.S_ISDIR(mode) or path.is_symlink():
        raise HoldoutAdmissionError(f"admission path is not a real directory: {path}")


def _ensure_lock_file(path: Path) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise HoldoutAdmissionError("O_NOFOLLOW is unavailable")
    try:
        fd = os.open(path, flags | nofollow, 0o600)
    except FileExistsError:
        try:
            mode = path.lstat().st_mode
        except OSError as exc:
            raise HoldoutAdmissionError("admission lock is unavailable") from exc
        if not stat.S_ISREG(mode) or path.is_symlink():
            raise HoldoutAdmissionError("admission lock is not a regular file")
        return
    except OSError as exc:
        raise HoldoutAdmissionError("cannot create admission lock") from exc
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_directory(path.parent)


def provision_shared_admission_root(repo_root: Path) -> Path:
    """Create every ledger parent explicitly before any claim is attempted."""

    root = shared_admission_root(repo_root)
    _ensure_private_directory(root)
    for name in ("claims", "consumed"):
        child = root / name
        _ensure_private_directory(child)
        _fsync_directory(child)
    _ensure_lock_file(root / _LOCK_NAME)
    _fsync_directory(root)
    return root


@contextmanager
def _locked(root: Path):
    path = root / _LOCK_NAME
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise HoldoutAdmissionError("O_NOFOLLOW is unavailable")
    try:
        fd = os.open(path, os.O_RDWR | nofollow)
    except OSError as exc:
        raise HoldoutAdmissionError("cannot open admission lock") from exc
    try:
        mode = os.fstat(fd).st_mode
        if not stat.S_ISREG(mode):
            raise HoldoutAdmissionError("admission lock fd is not regular")
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def _head_blob(repo_root: Path, relpath: str) -> tuple[str, bytes]:
    listed = _run_git(repo_root, "ls-tree", "-z", "HEAD", "--", relpath)
    entries = [entry for entry in listed.split(b"\0") if entry]
    if len(entries) != 1:
        raise HoldoutAdmissionError(f"fixed authority is not one HEAD blob: {relpath}")
    try:
        meta, actual = entries[0].decode("utf-8").split("\t", 1)
        mode, kind, oid = meta.split(" ")
    except (UnicodeError, ValueError) as exc:
        raise HoldoutAdmissionError(f"cannot parse HEAD blob identity: {relpath}") from exc
    if actual != relpath or mode != "100644" or kind != "blob":
        raise HoldoutAdmissionError(f"fixed authority is not a 100644 blob: {relpath}")
    raw = _run_git(repo_root, "show", f"HEAD:{relpath}")
    worktree_path = repo_root / relpath
    try:
        worktree_mode = worktree_path.lstat().st_mode
        worktree_raw = worktree_path.read_bytes()
    except OSError as exc:
        raise HoldoutAdmissionError(f"cannot read fixed working-tree bytes: {relpath}") from exc
    if not stat.S_ISREG(worktree_mode) or worktree_path.is_symlink():
        raise HoldoutAdmissionError(f"fixed authority is not a regular worktree file: {relpath}")
    if raw != worktree_raw:
        raise HoldoutAdmissionError(f"HEAD and working-tree bytes differ: {relpath}")
    return oid, raw


def _strict_json(raw: bytes, field: str) -> dict[str, Any]:
    def reject_constant(token: str):
        raise ValueError(token)

    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate key: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(
            raw.decode("utf-8"), parse_constant=reject_constant,
            object_pairs_hook=no_duplicates,
        )
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise HoldoutAdmissionError(f"fixed {field} is not strict JSON") from exc
    if type(value) is not dict:
        raise HoldoutAdmissionError(f"fixed {field} is not a JSON object")
    return value


def _authority(
    repo_root: Path,
    protocol: Mapping[str, object],
    freeze: Mapping[str, object],
    freeze_sha256: str,
) -> tuple[str, str, dict[str, Any], dict[str, Any]]:
    root = _repo_root(repo_root)
    _protocol_oid, protocol_raw = _head_blob(root, _PROTOCOL_REL)
    protocol_document = _strict_json(protocol_raw, "floor protocol")
    if protocol_document != dict(protocol):
        raise HoldoutAdmissionError("fixed protocol bytes do not match the supplied protocol")
    freeze_ref = protocol_document.get("freeze")
    if not isinstance(freeze_ref, Mapping) or freeze_ref.get("path") != _FREEZE_REL:
        raise HoldoutAdmissionError("protocol freeze path is not the fixed canonical path")
    _freeze_oid, freeze_raw = _head_blob(root, _FREEZE_REL)
    freeze_document = _strict_json(freeze_raw, "holdout freeze")
    actual_freeze_sha256 = hashlib.sha256(freeze_raw).hexdigest()
    if freeze_ref.get("sha256") != actual_freeze_sha256:
        raise HoldoutAdmissionError("fixed protocol freeze hash does not match freeze bytes")
    if _require_sha256(freeze_sha256, "freeze_sha256") != actual_freeze_sha256:
        raise HoldoutAdmissionError("verified freeze hash does not match fixed freeze bytes")
    if freeze_document != dict(freeze):
        raise HoldoutAdmissionError("fixed freeze bytes do not match the verified freeze document")
    protocol_sha256 = hashlib.sha256(protocol_raw).hexdigest()
    measurement_head = _run_git(root, "rev-parse", "HEAD").decode().strip()
    if len(measurement_head) != 40:
        raise HoldoutAdmissionError("measurement HEAD is not a full SHA-1")
    return measurement_head, protocol_sha256, protocol_document, freeze_document


def _key_fields(
    *, freeze_sha256: str, freeze_holdout_key: str, configuration_id: str,
    ccbench_pin: str, env_tag: str, observation_role: str,
) -> dict[str, str]:
    # protocol_sha256 is deliberately evidence only and must never enter here.
    observation_role = _require_text(observation_role, "observation_role")
    if observation_role not in _OBSERVATION_ROLES:
        raise HoldoutAdmissionError(
            f"observation_role is not recognized: {observation_role}"
        )
    return {
        "freeze_sha256": _require_sha256(freeze_sha256, "freeze_sha256"),
        "freeze_holdout_key": _require_text(
            freeze_holdout_key, "freeze_holdout_key"),
        "configuration_id": _require_text(configuration_id, "configuration_id"),
        "ccbench_pin": _require_text(ccbench_pin, "ccbench_pin"),
        "env_tag": _require_text(env_tag, "env_tag"),
        "observation_role": observation_role,
    }


def _claim_digest(key: Mapping[str, str]) -> str:
    return _sha256(dict(key))


def _claim_path(root: Path, digest: str) -> Path:
    return root / "claims" / f"{digest}.claim"


def _write_exclusive(path: Path, document: Mapping[str, object]) -> None:
    payload = _canonical_line(document)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise HoldoutAdmissionError("O_NOFOLLOW is unavailable")
    try:
        fd = os.open(path, flags | nofollow, 0o600)
    except FileExistsError:
        raise
    except OSError as exc:
        raise HoldoutAdmissionError(f"exclusive durable create failed: {path.name}") from exc
    try:
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise HoldoutAdmissionError("short durable write")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_directory(path.parent)


def _read_canonical_document(path: Path) -> dict[str, Any]:
    try:
        mode = path.lstat().st_mode
        raw = path.read_bytes()
    except OSError as exc:
        raise HoldoutAdmissionError(f"cannot read durable admission record: {path.name}") from exc
    if not stat.S_ISREG(mode) or path.is_symlink():
        raise HoldoutAdmissionError(f"durable admission record is not regular: {path.name}")
    if not raw.endswith(b"\n") or raw.count(b"\n") != 1:
        raise HoldoutAdmissionError(f"durable admission record is not one JSON line: {path.name}")
    value = _strict_json(raw[:-1], path.name)
    if _canonical_line(value) != raw:
        raise HoldoutAdmissionError(f"durable admission record is not canonical: {path.name}")
    return value


def _read_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        mode = path.lstat().st_mode
        raw = path.read_bytes()
    except OSError as exc:
        raise HoldoutAdmissionError(f"cannot read ledger: {path.name}") from exc
    if not stat.S_ISREG(mode) or path.is_symlink():
        raise HoldoutAdmissionError(f"ledger is not a regular file: {path.name}")
    if len(raw) > _MAX_LEDGER_BYTES:
        raise HoldoutAdmissionError(f"ledger exceeds byte bound: {path.name}")
    if raw and not raw.endswith(b"\n"):
        raise HoldoutAdmissionError(f"ledger has a truncated final row: {path.name}")
    rows = []
    for index, line in enumerate(raw.splitlines(), 1):
        if not line:
            raise HoldoutAdmissionError(f"ledger has a blank row: {path.name}:{index}")
        row = _strict_json(line, f"{path.name}:{index}")
        if _canonical_line(row) != line + b"\n":
            raise HoldoutAdmissionError(f"ledger row is not canonical: {path.name}:{index}")
        rows.append(row)
    return rows


def _read_run_journal(path: Path) -> list[dict[str, Any]]:
    """Read the canonical run journal without trusting caller summaries."""

    if not path.exists():
        return []
    try:
        mode = path.lstat().st_mode
        raw = path.read_bytes()
    except OSError as exc:
        raise HoldoutAdmissionError("cannot read canonical run journal") from exc
    if not stat.S_ISREG(mode) or path.is_symlink():
        raise HoldoutAdmissionError("canonical run journal is not a regular file")
    if len(raw) > _MAX_LEDGER_BYTES:
        raise HoldoutAdmissionError("canonical run journal exceeds byte bound")
    if raw and not raw.endswith(b"\n"):
        raise HoldoutAdmissionError("canonical run journal has a truncated final row")
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(raw.splitlines(), 1):
        if not line:
            raise HoldoutAdmissionError(
                f"canonical run journal has a blank row: {index}"
            )
        rows.append(_strict_json(line, f"journal.jsonl:{index}"))
    return rows


def _canonical_run_artifacts(
    *, out_root: Path, run_dir: Path, run_relpath: str,
    campaign_run_id: str, resume: bool, protocol_sha256: str,
    freeze_sha256: str, protocol_reps: int,
) -> tuple[Path, str, dict[str, Any], list[dict[str, Any]], bool]:
    """Verify actual manifest/journal bytes in the canonical run directory."""

    out_root = Path(out_root).resolve(strict=False)
    supplied = Path(run_dir)
    expected = out_root / PurePosixPath(run_relpath)
    if supplied.resolve(strict=False) != expected.resolve(strict=False):
        raise HoldoutAdmissionError("run_dir does not match canonical run_relpath")
    try:
        mode = supplied.lstat().st_mode
    except OSError as exc:
        raise HoldoutAdmissionError("canonical run directory is unavailable") from exc
    if not stat.S_ISDIR(mode) or supplied.is_symlink() or supplied.name != campaign_run_id:
        raise HoldoutAdmissionError("canonical run directory identity is invalid")

    manifest_path = supplied / "manifest.json"
    try:
        manifest_mode = manifest_path.lstat().st_mode
        manifest_raw = manifest_path.read_bytes()
    except OSError as exc:
        raise HoldoutAdmissionError("canonical run manifest is unavailable") from exc
    if not stat.S_ISREG(manifest_mode) or manifest_path.is_symlink():
        raise HoldoutAdmissionError("canonical run manifest is not a regular file")
    manifest = _strict_json(manifest_raw, "manifest.json")
    expected_manifest = {
        "protocol_sha256": protocol_sha256,
        "freeze_sha256": freeze_sha256,
        "reps": protocol_reps,
    }
    for field, value in expected_manifest.items():
        if manifest.get(field) != value:
            raise HoldoutAdmissionError(
                f"canonical run manifest identity mismatch: {field}"
            )
    manifest_sha256 = hashlib.sha256(manifest_raw).hexdigest()

    journal_path = supplied / "journal.jsonl"
    records = _read_run_journal(journal_path)
    measurement_started = any(
        row.get("event") in {"session-start", "session"} for row in records
    )
    terminals = [row for row in records if row.get("event") == "terminal"]
    if terminals:
        raise HoldoutAdmissionError("completed or terminal run cannot reissue admission")
    if resume:
        if not journal_path.is_file():
            raise HoldoutAdmissionError(
                "resume journal is absent after admission ledger issuance"
            )
        starts = [row for row in records if row.get("event") == "campaign-start"]
        if len(starts) > 1:
            raise HoldoutAdmissionError("resume journal has duplicate campaign-start")
        if starts:
            start = starts[0]
            for field, value in {
                "protocol_sha256": protocol_sha256,
                "freeze_sha256": freeze_sha256,
                "manifest_sha256": manifest_sha256,
            }.items():
                if start.get(field) != value:
                    raise HoldoutAdmissionError(
                        f"resume journal identity mismatch: {field}"
                    )
        try:
            _floor_contract.classify_journal_resume_state(
                records, manifest_exists=True,
                result_published=(supplied / "result.json").is_file(),
                markdown_published=(supplied / "result.md").is_file(),
            )
        except _floor_contract.FloorContractError as exc:
            raise HoldoutAdmissionError(
                f"canonical resume state is invalid: {exc}"
            ) from exc
    elif measurement_started:
        raise HoldoutAdmissionError("fresh admission cannot follow measurement")
    return supplied, manifest_sha256, manifest, records, measurement_started


def _append_ledger(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        return
    payload = b"".join(_canonical_line(dict(row)) for row in rows)
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise HoldoutAdmissionError("O_NOFOLLOW is unavailable")
    try:
        fd = os.open(path, flags | nofollow, 0o600)
    except OSError as exc:
        raise HoldoutAdmissionError(f"cannot append ledger: {path.name}") from exc
    try:
        mode = os.fstat(fd).st_mode
        if not stat.S_ISREG(mode):
            raise HoldoutAdmissionError(f"ledger fd is not regular: {path.name}")
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise HoldoutAdmissionError("short ledger append")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_directory(path.parent)


def _attempt_ids(
    *, cell_id: str, schedule: Sequence[Mapping[str, object]], retry_slots: int,
) -> tuple[str, ...]:
    planned = [
        f"{cell_id}::seq{row['seq']}"
        for row in schedule if row.get("cell_id") == cell_id
    ]
    retry = [f"{cell_id}::retry{ordinal}" for ordinal in range(1, retry_slots + 1)]
    return tuple(planned + retry)


def reserve_floor_holdout_observations(
    *, repo_root: Path, protocol: Mapping[str, object],
    verified_freeze_document: Mapping[str, object], freeze_sha256: str,
    cells: Sequence[Mapping[str, object]], schedule: Sequence[Mapping[str, object]],
    campaign_run_id: str, out_root: Path, run_dir: Path, run_relpath: str,
    mode: str, resume: bool, irreversible_pilot_approved: bool,
) -> FloorHoldoutReservation:
    """Production reservation entrypoint with the fixed neutral signature table."""

    return _reserve_floor_holdout_observations_core(
        repo_root=repo_root, protocol=protocol,
        verified_freeze_document=verified_freeze_document,
        freeze_sha256=freeze_sha256, cells=cells, schedule=schedule,
        campaign_run_id=campaign_run_id, out_root=out_root, run_dir=run_dir,
        run_relpath=run_relpath, mode=mode, resume=resume,
        irreversible_pilot_approved=irreversible_pilot_approved,
    )


def _reserve_floor_holdout_observations_core(
    *, repo_root: Path, protocol: Mapping[str, object],
    verified_freeze_document: Mapping[str, object], freeze_sha256: str,
    cells: Sequence[Mapping[str, object]], schedule: Sequence[Mapping[str, object]],
    campaign_run_id: str, out_root: Path, run_dir: Path, run_relpath: str,
    mode: str, resume: bool, irreversible_pilot_approved: bool,
    _neutral_holdouts: Mapping[str, Mapping[str, object]] | None = None,
) -> FloorHoldoutReservation:
    """Verify fixed authority and atomically reserve every frozen cell.

    Callers cannot summarize resume state: this boundary reads the actual
    canonical manifest and journal bytes itself.  A pilot claim also records
    the explicit acknowledgement that it irreversibly consumes the same
    one-shot key a future official run would need.
    """

    if type(resume) is not bool:
        raise HoldoutAdmissionError("resume must be an exact bool")
    if type(irreversible_pilot_approved) is not bool:
        raise HoldoutAdmissionError(
            "irreversible_pilot_approved must be an exact bool"
        )
    campaign_run_id = _require_text(campaign_run_id, "campaign_run_id")
    run_relpath = _portable_run_relpath(run_relpath)
    mode = _require_text(mode, "mode")
    if mode == "pilot" and not irreversible_pilot_approved:
        raise HoldoutAdmissionError(
            "pilot holdout observation requires irreversible one-shot approval"
        )
    root = provision_shared_admission_root(Path(repo_root))
    measurement_head, protocol_sha256, fixed_protocol, fixed_freeze = _authority(
        Path(repo_root), protocol, verified_freeze_document, freeze_sha256,
    )
    protocol_reps = fixed_protocol.get("reps")
    if type(protocol_reps) is not int or protocol_reps <= 0:
        raise HoldoutAdmissionError("canonical protocol reps is invalid")
    canonical_run_dir, manifest_sha256, manifest, _run_records, measurement_started = (
        _canonical_run_artifacts(
            out_root=Path(out_root), run_dir=Path(run_dir), run_relpath=run_relpath,
            campaign_run_id=campaign_run_id, resume=resume,
            protocol_sha256=protocol_sha256, freeze_sha256=freeze_sha256,
            protocol_reps=protocol_reps,
        )
    )
    try:
        signatures = _protected_signatures_from_verified_freeze_core(
            fixed_freeze,
            _neutral_holdouts=_neutral_holdouts,
        )
        contract_cells = _floor_contract.enumerate_cells(
            fixed_freeze,
            stock_configuration=fixed_protocol["stock_configuration"],
        )
        expected_schedule = _floor_contract.build_schedule(
            cells=contract_cells, master_seed=fixed_protocol["master_seed"],
            n_sessions=fixed_protocol["n_sessions"],
        )
    except (HoldoutObservationError, _floor_contract.FloorContractError, KeyError) as exc:
        raise HoldoutAdmissionError(f"cannot derive frozen admission schedule: {exc}") from exc
    normalized_cells = [dict(cell) for cell in cells]
    normalized_schedule = [dict(row) for row in schedule]
    admission_cell_keys = {
        "cell_id", "freeze_holdout_key", "configuration_id",
        "records", "threads", "workload",
    }
    if any(set(cell) != admission_cell_keys for cell in normalized_cells):
        raise HoldoutAdmissionError("admission cell key set is not exact")
    evidence_fields = (
        "cell_id", "configuration_id", "records", "threads", "workload",
    )
    supplied_evidence = [
        {field: cell[field] for field in evidence_fields}
        for cell in normalized_cells
    ]
    expected_evidence = [
        {field: cell[field] for field in evidence_fields}
        for cell in contract_cells
    ]
    if supplied_evidence != expected_evidence:
        raise HoldoutAdmissionError("supplied cells differ from the fixed freeze projection")
    if normalized_schedule != expected_schedule:
        raise HoldoutAdmissionError("supplied schedule differs from the frozen schedule")
    manifest_schedule = manifest.get("schedule")
    if manifest_schedule is not None and manifest_schedule != normalized_schedule:
        raise HoldoutAdmissionError(
            "canonical run manifest schedule differs from the frozen schedule"
        )
    signature_by_key = {item.freeze_holdout_key: item for item in signatures}
    neutral_holdouts = {
        item.freeze_holdout_key: {
            "candidate_id": item.freeze_candidate_id,
            "ycsb": {"ycsb_rratio": item.ycsb_rratio},
        }
        for item in signatures
    }
    retry_slots = fixed_protocol.get("retry_slots_per_cell")
    if type(retry_slots) is not int or retry_slots < 0:
        raise HoldoutAdmissionError("protocol retry_slots_per_cell is invalid")

    claims: list[dict[str, Any]] = []
    for cell in normalized_cells:
        freeze_holdout_key = _require_text(
            cell.get("freeze_holdout_key"), "freeze_holdout_key",
        )
        signature = signature_by_key.get(freeze_holdout_key)
        if signature is None:
            raise HoldoutAdmissionError("cell freeze key is not protected")
        cell_id = _require_text(cell.get("cell_id"), "cell_id")
        configuration_id = _require_text(
            cell.get("configuration_id"), "configuration_id")
        if cell_id != f"{freeze_holdout_key}::{configuration_id}":
            raise HoldoutAdmissionError(
                "cell_id does not bind freeze_holdout_key and configuration_id"
            )
        key = _key_fields(
            freeze_sha256=freeze_sha256,
            freeze_holdout_key=freeze_holdout_key,
            configuration_id=configuration_id,
            ccbench_pin=fixed_protocol["ccbench_pin"],
            env_tag=fixed_protocol["env_tag"],
            observation_role=OBSERVATION_ROLE_FLOOR_CAMPAIGN,
        )
        attempts = _attempt_ids(
            cell_id=cell_id, schedule=normalized_schedule, retry_slots=retry_slots,
        )
        if len(attempts) != fixed_protocol["n_sessions"] + retry_slots:
            raise HoldoutAdmissionError("frozen attempt count is inconsistent")
        claims.append({
            "schema_version": _CLAIM_SCHEMA,
            "event": "claim",
            "key": key,
            "measurement_head": measurement_head,
            "protocol_sha256": protocol_sha256,
            "freeze_candidate_id": signature.freeze_candidate_id,
            "trial_workload_name": signature.trial_workload_name,
            "cell_id": cell_id,
            "records": cell.get("records"),
            "threads": cell.get("threads"),
            "workload": dict(cell.get("workload", {})),
            "campaign_run_id": campaign_run_id,
            "run_relpath": run_relpath,
            "mode": mode,
            "irreversible_pilot_approved": irreversible_pilot_approved,
            "attempt_ids": list(attempts),
        })

    with _locked(root):
        for claim in claims:
            digest = _claim_digest(claim["key"])
            path = _claim_path(root, digest)
            if resume:
                if path.exists():
                    if _read_canonical_document(path) != claim:
                        raise HoldoutAdmissionError(
                            "resume cell claim does not match the same run identity"
                        )
                    continue
                if measurement_started:
                    raise HoldoutAdmissionError(
                        "cannot backfill a missing cell claim after measurement started"
                    )
            try:
                _write_exclusive(path, claim)
            except FileExistsError as exc:
                raise HoldoutAdmissionError(
                    "holdout cell key was already consumed by another fresh run"
                ) from exc

    token = FloorHoldoutReservation(
        campaign_run_id=campaign_run_id,
        run_relpath=run_relpath,
        protocol_sha256=protocol_sha256,
        freeze_sha256=freeze_sha256,
    )
    state = _ReservationState(
        token=token, root=root, measurement_head=measurement_head,
        protocol=fixed_protocol, freeze=fixed_freeze,
        cells=tuple(normalized_cells), schedule=tuple(normalized_schedule),
        claims=tuple(claims), signatures=signature_by_key,
        neutral_holdouts=neutral_holdouts, mode=mode,
        resume=resume, measurement_started=measurement_started,
        run_dir=canonical_run_dir, manifest_sha256=manifest_sha256,
        protocol_reps=protocol_reps,
        irreversible_pilot_approved=irreversible_pilot_approved,
    )
    with _state_lock:
        _reservation_states[id(token)] = state
    return token


def _reservation_state(reservation: object) -> _ReservationState:
    with _state_lock:
        state = _reservation_states.get(id(reservation))
    if state is None or state.token is not reservation:
        raise HoldoutAdmissionError("floor holdout reservation was not issued")
    return state


def finalize_floor_holdout_admissions(
    reservation: FloorHoldoutReservation,
) -> dict[str, CellHoldoutAdmission]:
    """Durably append evidence rows, then issue cell capabilities only."""

    state = _reservation_state(reservation)
    manifest_sha256 = state.manifest_sha256
    expected_rows: list[dict[str, Any]] = []
    for claim in state.claims:
        key = dict(claim["key"])
        expected_rows.append({
            "schema_version": _LEDGER_SCHEMA,
            "event": "admit",
            **key,
            "measurement_head": state.measurement_head,
            "protocol_sha256": state.token.protocol_sha256,
            "manifest_sha256": manifest_sha256,
            "freeze_candidate_id": claim["freeze_candidate_id"],
            "trial_workload_name": claim["trial_workload_name"],
            "cell_id": claim["cell_id"],
            "records": claim["records"],
            "threads": claim["threads"],
            "workload": claim["workload"],
            "campaign_run_id": state.token.campaign_run_id,
            "run_relpath": state.token.run_relpath,
            "mode": state.mode,
            "irreversible_pilot_approved": state.irreversible_pilot_approved,
            "attempt_ids": claim["attempt_ids"],
            "attempt_count": len(claim["attempt_ids"]),
        })

    with _locked(state.root):
        rows = _read_ledger(state.root / _LEDGER_NAME)
        by_key: dict[str, dict[str, Any]] = {}
        for row in rows:
            if row.get("schema_version") != _LEDGER_SCHEMA or row.get("event") != "admit":
                raise HoldoutAdmissionError("admission ledger contains an unknown row")
            try:
                digest = _claim_digest(_key_fields(
                    freeze_sha256=row["freeze_sha256"],
                    freeze_holdout_key=row["freeze_holdout_key"],
                    configuration_id=row["configuration_id"],
                    ccbench_pin=row["ccbench_pin"], env_tag=row["env_tag"],
                    observation_role=row["observation_role"],
                ))
            except (KeyError, HoldoutAdmissionError) as exc:
                raise HoldoutAdmissionError("admission ledger row key is invalid") from exc
            if digest in by_key:
                raise HoldoutAdmissionError("admission ledger has a duplicate cell key")
            by_key[digest] = row
        missing = []
        for expected in expected_rows:
            key = _key_fields(
                freeze_sha256=expected["freeze_sha256"],
                freeze_holdout_key=expected["freeze_holdout_key"],
                configuration_id=expected["configuration_id"],
                ccbench_pin=expected["ccbench_pin"], env_tag=expected["env_tag"],
                observation_role=expected["observation_role"],
            )
            digest = _claim_digest(key)
            claim = _read_canonical_document(_claim_path(state.root, digest))
            matching = by_key.get(digest)
            if matching is not None:
                if not state.resume:
                    raise HoldoutAdmissionError(
                        "fresh run cannot reuse an existing admission ledger row"
                    )
                if matching != expected or claim not in state.claims:
                    raise HoldoutAdmissionError(
                        "resume admission evidence does not match the same run identity"
                    )
            else:
                if state.measurement_started:
                    raise HoldoutAdmissionError(
                        "cannot backfill admission evidence after measurement started"
                    )
                missing.append(expected)
        _append_ledger(state.root / _LEDGER_NAME, missing)

    admissions: dict[str, CellHoldoutAdmission] = {}
    for row in expected_rows:
        token = CellHoldoutAdmission(
            freeze_holdout_key=row["freeze_holdout_key"],
            freeze_candidate_id=row["freeze_candidate_id"],
            trial_workload_name=row["trial_workload_name"],
            configuration_id=row["configuration_id"],
            cell_id=row["cell_id"],
        )
        cell_state = _CellState(
            token=token, root=state.root, row=row,
            claim_digest=_claim_digest(_key_fields(
                freeze_sha256=row["freeze_sha256"],
                freeze_holdout_key=row["freeze_holdout_key"],
                configuration_id=row["configuration_id"],
                ccbench_pin=row["ccbench_pin"], env_tag=row["env_tag"],
                observation_role=row["observation_role"],
            )),
            attempt_ids=frozenset(row["attempt_ids"]),
            run_dir=state.run_dir, schedule=state.schedule,
            verified_freeze=state.freeze, neutral_holdouts=state.neutral_holdouts,
            protocol_reps=state.protocol_reps,
        )
        with _state_lock:
            _cell_states[id(token)] = cell_state
        admissions[token.cell_id] = token
    return admissions


def reserve_oracle_holdout_observations(
    *, repo_root: Path, verified_manifest: object,
    launch_validated: object, block_id: str,
) -> dict[int, OracleCellHoldoutAdmission]:
    """Atomically reserve manifest-enumerated oracle cells before measurement.

    Cell identities, attempt tickets, environment pins, and the run-once
    allowance all come from the already-verified oracle manifest.  The caller
    selects only a manifest-owned block and cannot submit its own cells or rep
    allowance.
    """

    if type(verified_manifest) is not _oracle_manifest.VerifiedManifest:
        raise HoldoutAdmissionError(
            "oracle authority requires an exact VerifiedManifest"
        )
    manifest = verified_manifest.document
    manifest_sha256 = _require_sha256(
        verified_manifest.sha256, "manifest_sha256",
    )
    if _sha256(manifest) != manifest_sha256:
        raise HoldoutAdmissionError(
            "verified oracle manifest digest does not match its document"
        )
    if type(launch_validated) is not _ratified_freeze.LaunchValidatedFreeze:
        raise HoldoutAdmissionError(
            "oracle authority requires an exact LaunchValidatedFreeze"
        )
    freeze_sha256 = _require_sha256(
        launch_validated.ratified.sha256, "freeze_sha256",
    )
    freeze_ref = manifest.get("freeze")
    if not isinstance(freeze_ref, Mapping) or freeze_ref.get("sha256") != freeze_sha256:
        raise HoldoutAdmissionError(
            "verified oracle manifest is not bound to the verified freeze hash"
        )
    fixed_freeze = _mutable_json_tree(launch_validated.ratified.document)
    if not isinstance(fixed_freeze, dict):
        raise HoldoutAdmissionError(
            "launch-validated oracle freeze document is invalid"
        )
    try:
        signatures = _protected_signatures_from_verified_freeze_core(fixed_freeze)
        block = _oracle_manifest.config_for_block(manifest, block_id)
    except (HoldoutObservationError, _oracle_manifest.ManifestError) as exc:
        raise HoldoutAdmissionError(
            f"cannot derive oracle admission authority: {exc}"
        ) from exc
    run_contract = block.get("run_contract")
    if not isinstance(run_contract, Mapping):
        raise HoldoutAdmissionError("verified oracle run_contract is unavailable")
    oracle_reps = run_contract.get("reps")
    if type(oracle_reps) is not int or oracle_reps <= 0:
        raise HoldoutAdmissionError("verified oracle reps is invalid")
    ccbench_pin = _require_text(run_contract.get("ccbench_pin"), "ccbench_pin")
    env_tag = _require_text(run_contract.get("env_tag"), "env_tag")
    schedule_sha256 = _require_sha256(
        manifest.get("schedule_sha256"), "schedule_sha256",
    )
    campaign_id = _require_text(block.get("campaign_id"), "campaign_id")
    block_id = _require_text(block.get("block_id"), "block_id")
    schedule = block.get("schedule")
    if not isinstance(schedule, Sequence) or isinstance(
        schedule, (str, bytes, bytearray),
    ):
        raise HoldoutAdmissionError("verified oracle block schedule is invalid")

    signature_by_key = {item.freeze_holdout_key: item for item in signatures}
    neutral_holdouts = {
        item.freeze_holdout_key: {
            "candidate_id": item.freeze_candidate_id,
            "ycsb": {"ycsb_rratio": item.ycsb_rratio},
        }
        for item in signatures
    }
    rows_by_cell: dict[tuple[str, str], list[Mapping[str, object]]] = {}
    seen_schedule_indexes: set[int] = set()
    for raw_row in schedule:
        if not isinstance(raw_row, Mapping):
            raise HoldoutAdmissionError("verified oracle schedule row is invalid")
        schedule_index = raw_row.get("schedule_index")
        if type(schedule_index) is not int or schedule_index < 0:
            raise HoldoutAdmissionError("verified oracle schedule_index is invalid")
        if schedule_index in seen_schedule_indexes:
            raise HoldoutAdmissionError("verified oracle schedule_index is duplicated")
        seen_schedule_indexes.add(schedule_index)
        pair = (
            _require_text(raw_row.get("holdout_id"), "holdout_id"),
            _require_text(raw_row.get("configuration_id"), "configuration_id"),
        )
        rows_by_cell.setdefault(pair, []).append(raw_row)
    if not rows_by_cell:
        raise HoldoutAdmissionError("verified oracle block schedule is empty")

    claims: list[dict[str, Any]] = []
    ledger_rows: list[dict[str, Any]] = []
    for (freeze_holdout_key, configuration_id), cell_rows in rows_by_cell.items():
        signature = signature_by_key.get(freeze_holdout_key)
        if signature is None:
            raise HoldoutAdmissionError("oracle schedule freeze key is not protected")
        freeze_entry = fixed_freeze.get("holdouts", {}).get(freeze_holdout_key)
        if not isinstance(freeze_entry, Mapping):
            raise HoldoutAdmissionError("oracle freeze holdout entry is invalid")
        workload = freeze_entry.get("ycsb")
        if not isinstance(workload, Mapping):
            raise HoldoutAdmissionError("oracle freeze workload is invalid")
        cell_id = f"{freeze_holdout_key}::{configuration_id}"
        key = _key_fields(
            freeze_sha256=freeze_sha256,
            freeze_holdout_key=freeze_holdout_key,
            configuration_id=configuration_id,
            ccbench_pin=ccbench_pin,
            env_tag=env_tag,
            observation_role=OBSERVATION_ROLE_ORACLE_DRIVER,
        )
        attempt_ids = [
            f"{campaign_id}::{block_id}::schedule{row['schedule_index']}"
            for row in cell_rows
        ]
        claim = {
            "schema_version": _CLAIM_SCHEMA,
            "event": "claim",
            "key": key,
            "manifest_sha256": manifest_sha256,
            "schedule_sha256": schedule_sha256,
            "freeze_candidate_id": signature.freeze_candidate_id,
            "trial_workload_name": signature.trial_workload_name,
            "cell_id": cell_id,
            "records": freeze_entry.get("records"),
            "threads": freeze_entry.get("threads"),
            "workload": dict(workload),
            "campaign_id": campaign_id,
            "block_id": block_id,
            "schedule_indexes": [row["schedule_index"] for row in cell_rows],
            "attempt_ids": attempt_ids,
        }
        claims.append(claim)
        ledger_rows.append({
            "schema_version": _LEDGER_SCHEMA,
            "event": "admit",
            **key,
            "manifest_sha256": manifest_sha256,
            "schedule_sha256": schedule_sha256,
            "freeze_candidate_id": signature.freeze_candidate_id,
            "trial_workload_name": signature.trial_workload_name,
            "cell_id": cell_id,
            "records": freeze_entry.get("records"),
            "threads": freeze_entry.get("threads"),
            "workload": dict(workload),
            "campaign_id": campaign_id,
            "block_id": block_id,
            "schedule_indexes": [row["schedule_index"] for row in cell_rows],
            "attempt_ids": attempt_ids,
            "attempt_count": len(attempt_ids),
        })

    root = provision_shared_admission_root(Path(repo_root))
    with _locked(root):
        indexed: dict[str, dict[str, Any]] = {}
        for row in _read_ledger(root / _LEDGER_NAME):
            if row.get("schema_version") != _LEDGER_SCHEMA or row.get("event") != "admit":
                raise HoldoutAdmissionError("admission ledger contains an unknown row")
            try:
                key = _key_fields(
                    freeze_sha256=row["freeze_sha256"],
                    freeze_holdout_key=row["freeze_holdout_key"],
                    configuration_id=row["configuration_id"],
                    ccbench_pin=row["ccbench_pin"],
                    env_tag=row["env_tag"],
                    observation_role=row["observation_role"],
                )
            except (KeyError, HoldoutAdmissionError) as exc:
                raise HoldoutAdmissionError("admission ledger row key is invalid") from exc
            digest = _claim_digest(key)
            if digest in indexed:
                raise HoldoutAdmissionError("admission ledger has a duplicate cell key")
            indexed[digest] = row
        for claim in claims:
            digest = _claim_digest(claim["key"])
            try:
                _write_exclusive(_claim_path(root, digest), claim)
            except FileExistsError as exc:
                raise HoldoutAdmissionError(
                    "oracle holdout cell key was already consumed"
                ) from exc
            if digest in indexed:
                raise HoldoutAdmissionError(
                    "oracle ledger evidence existed without its durable claim"
                )
        _append_ledger(root / _LEDGER_NAME, ledger_rows)

    admissions_by_schedule_index: dict[int, OracleCellHoldoutAdmission] = {}
    for claim, row in zip(claims, ledger_rows, strict=True):
        token = OracleCellHoldoutAdmission(
            freeze_holdout_key=row["freeze_holdout_key"],
            freeze_candidate_id=row["freeze_candidate_id"],
            trial_workload_name=row["trial_workload_name"],
            configuration_id=row["configuration_id"],
            cell_id=row["cell_id"],
        )
        attempt_ids_by_schedule_index = dict(zip(
            row["schedule_indexes"], row["attempt_ids"], strict=True,
        ))
        state = _OracleCellState(
            token=token,
            root=root,
            row=row,
            claim_digest=_claim_digest(claim["key"]),
            attempt_ids_by_schedule_index=attempt_ids_by_schedule_index,
            verified_freeze=fixed_freeze,
            neutral_holdouts=neutral_holdouts,
            oracle_reps=oracle_reps,
        )
        with _state_lock:
            _oracle_cell_states[id(token)] = state
        for schedule_index in row["schedule_indexes"]:
            admissions_by_schedule_index[schedule_index] = token
    if set(admissions_by_schedule_index) != seen_schedule_indexes:
        raise HoldoutAdmissionError("oracle schedule admission coverage is incomplete")
    return admissions_by_schedule_index


def _oracle_cell_state(admission: object) -> _OracleCellState:
    with _state_lock:
        state = _oracle_cell_states.get(id(admission))
    if state is None or state.token is not admission:
        raise HoldoutAdmissionError("oracle cell holdout admission was not issued")
    return state


def consume_oracle_attempt_ticket(
    admission: OracleCellHoldoutAdmission, *, schedule_index: int,
) -> HoldoutObservationAdmission:
    """Consume one manifest schedule ticket and issue its reps-bound token."""

    state = _oracle_cell_state(admission)
    if type(schedule_index) is not int or schedule_index < 0:
        raise HoldoutAdmissionError("schedule_index must be a nonnegative exact int")
    attempt_id = state.attempt_ids_by_schedule_index.get(schedule_index)
    if attempt_id is None:
        raise HoldoutAdmissionError(
            "schedule_index is not in the oracle manifest ticket set"
        )
    marker = {
        "schema_version": _ATTEMPT_SCHEMA,
        "event": "consume",
        "claim_digest": state.claim_digest,
        "attempt_id": attempt_id,
        "manifest_sha256": state.row["manifest_sha256"],
        "campaign_id": state.row["campaign_id"],
        "block_id": state.row["block_id"],
        "schedule_index": schedule_index,
        "cell_id": state.row["cell_id"],
        "freeze_holdout_key": state.row["freeze_holdout_key"],
        "configuration_id": state.row["configuration_id"],
        "observation_role": OBSERVATION_ROLE_ORACLE_DRIVER,
    }
    marker_digest = hashlib.sha256(attempt_id.encode("utf-8")).hexdigest()
    path = state.root / "consumed" / f"{state.claim_digest}-{marker_digest}.json"
    with _locked(state.root):
        try:
            _write_exclusive(path, marker)
        except FileExistsError as exc:
            raise HoldoutAdmissionError(
                "oracle attempt ticket was already consumed"
            ) from exc
        _append_ledger(state.root / _ATTEMPT_LEDGER_NAME, [marker])
    try:
        receipt = _new_durable_attempt_consumption_receipt(
            attempt_id=attempt_id,
            permitted_run_once_calls=state.oracle_reps,
        )
        observation = _issue_holdout_observation_admission_from_receipt(
            receipt=receipt,
            verified_freeze_document=state.verified_freeze,
            freeze_holdout_key=state.row["freeze_holdout_key"],
            _neutral_holdouts=state.neutral_holdouts,
        )
        assert_issued_holdout_observation(observation)
    except HoldoutObservationError as exc:
        raise HoldoutAdmissionError(
            f"cannot issue oracle attempt observation: {exc}"
        ) from exc
    return observation


def _cell_state(admission: object) -> _CellState:
    with _state_lock:
        state = _cell_states.get(id(admission))
    if state is None or state.token is not admission:
        raise HoldoutAdmissionError("cell holdout admission was not issued")
    return state


def assert_cell_holdout_admission(
    admission: object, *, cell: Mapping[str, object], protocol: Mapping[str, object],
    freeze_sha256: str, protocol_sha256: str, manifest_sha256: str,
) -> None:
    """Recheck an issued cell capability against the exact live run evidence."""

    state = _cell_state(admission)
    row = state.row
    expected = {
        "cell_id": cell.get("cell_id"),
        "freeze_holdout_key": cell.get("freeze_holdout_key"),
        "configuration_id": cell.get("configuration_id"),
        "records": cell.get("records"),
        "threads": cell.get("threads"),
        "workload": dict(cell.get("workload", {})),
        "freeze_sha256": freeze_sha256,
        "protocol_sha256": protocol_sha256,
        "manifest_sha256": manifest_sha256,
        "ccbench_pin": protocol.get("ccbench_pin"),
        "env_tag": protocol.get("env_tag"),
    }
    for field, value in expected.items():
        if row.get(field) != value:
            raise HoldoutAdmissionError(f"cell holdout admission mismatch: {field}")


def _assert_attempt_authorized_by_journal(
    state: _CellState, *, attempt_id: str,
) -> None:
    records = _read_run_journal(state.run_dir / "journal.jsonl")
    if any(row.get("event") == "terminal" for row in records):
        raise HoldoutAdmissionError("terminal run cannot consume another attempt")
    starts = [
        row for row in records
        if row.get("event") == "session-start"
        and row.get("attempt_id") == attempt_id
    ]
    if len(starts) != 1 or starts[0].get("cell_id") != state.row["cell_id"]:
        raise HoldoutAdmissionError(
            "attempt ticket lacks one canonical session-start authorization"
        )
    start = starts[0]
    if start.get("kind") == "planned":
        schedule_by_seq = {row.get("seq"): row for row in state.schedule}
        scheduled = schedule_by_seq.get(start.get("seq"))
        if (scheduled is None or scheduled.get("cell_id") != state.row["cell_id"]
                or scheduled.get("round") != start.get("round")
                or start.get("trigger") is not None):
            raise HoldoutAdmissionError("planned attempt authorization is inconsistent")
        return
    if start.get("kind") != "retry":
        raise HoldoutAdmissionError("attempt authorization kind is unknown")
    trigger = start.get("trigger")
    triggering_rows = [
        row for row in records
        if row.get("event") == "session" and row.get("attempt_id") == trigger
    ]
    if (type(trigger) is not str or len(triggering_rows) != 1
            or triggering_rows[0].get("cell_id") != state.row["cell_id"]
            or triggering_rows[0].get("kind") != "planned"
            or triggering_rows[0].get("valid") is not False):
        raise HoldoutAdmissionError(
            "retry attempt lacks its canonical failed planned trigger"
        )


def consume_attempt_ticket(
    admission: CellHoldoutAdmission, *, attempt_id: str,
) -> HoldoutObservationAdmission:
    """Atomically and durably consume one frozen attempt immediately before measure."""

    state = _cell_state(admission)
    attempt_id = _require_text(attempt_id, "attempt_id")
    if attempt_id not in state.attempt_ids:
        raise HoldoutAdmissionError("attempt_id is not in the frozen ticket set")
    _assert_attempt_authorized_by_journal(state, attempt_id=attempt_id)
    marker = {
        "schema_version": _ATTEMPT_SCHEMA,
        "event": "consume",
        "claim_digest": state.claim_digest,
        "attempt_id": attempt_id,
        "campaign_run_id": state.row["campaign_run_id"],
        "manifest_sha256": state.row["manifest_sha256"],
        "run_relpath": state.row["run_relpath"],
        "cell_id": state.row["cell_id"],
        "freeze_holdout_key": state.row["freeze_holdout_key"],
        "configuration_id": state.row["configuration_id"],
        "observation_role": OBSERVATION_ROLE_FLOOR_CAMPAIGN,
    }
    marker_digest = hashlib.sha256(attempt_id.encode("utf-8")).hexdigest()
    path = state.root / "consumed" / f"{state.claim_digest}-{marker_digest}.json"
    with _locked(state.root):
        try:
            _write_exclusive(path, marker)
        except FileExistsError as exc:
            raise HoldoutAdmissionError("attempt ticket was already consumed") from exc
        _append_ledger(state.root / _ATTEMPT_LEDGER_NAME, [marker])
    try:
        receipt = _new_durable_attempt_consumption_receipt(
            attempt_id=attempt_id,
            permitted_run_once_calls=state.protocol_reps,
        )
        observation = _issue_holdout_observation_admission_from_receipt(
            receipt=receipt,
            verified_freeze_document=state.verified_freeze,
            freeze_holdout_key=state.row["freeze_holdout_key"],
            _neutral_holdouts=state.neutral_holdouts,
        )
        assert_issued_holdout_observation(observation)
    except HoldoutObservationError as exc:
        raise HoldoutAdmissionError(f"cannot issue attempt observation: {exc}") from exc
    return observation
