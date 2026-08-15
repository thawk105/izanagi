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
    assert_issued_holdout_observation,
    issue_holdout_observation_admission,
    protected_signatures_from_verified_freeze,
)
from . import s8b_floor_contract as _floor_contract

__all__ = (
    "CellHoldoutAdmission",
    "FloorHoldoutReservation",
    "HoldoutAdmissionError",
    "assert_cell_holdout_admission",
    "consume_attempt_ticket",
    "finalize_floor_holdout_admissions",
    "provision_shared_admission_root",
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
    mode: str
    resume: bool
    measurement_started: bool


@dataclass(frozen=True, slots=True)
class _CellState:
    token: CellHoldoutAdmission
    observation: HoldoutObservationAdmission
    root: Path
    row: dict[str, Any]
    claim_digest: str
    attempt_ids: frozenset[str]


_reservation_states: dict[int, _ReservationState] = {}
_cell_states: dict[int, _CellState] = {}
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
    ccbench_pin: str, env_tag: str,
) -> dict[str, str]:
    # protocol_sha256 is deliberately evidence only and must never enter here.
    return {
        "freeze_sha256": _require_sha256(freeze_sha256, "freeze_sha256"),
        "freeze_holdout_key": _require_text(
            freeze_holdout_key, "freeze_holdout_key"),
        "configuration_id": _require_text(configuration_id, "configuration_id"),
        "ccbench_pin": _require_text(ccbench_pin, "ccbench_pin"),
        "env_tag": _require_text(env_tag, "env_tag"),
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
    campaign_run_id: str, run_relpath: str, mode: str, resume: bool,
    journal_exists: bool, measurement_started: bool,
) -> FloorHoldoutReservation:
    """Verify fixed HEAD authority and atomically reserve every frozen cell."""

    if type(resume) is not bool or type(journal_exists) is not bool:
        raise HoldoutAdmissionError("resume and journal_exists must be exact bools")
    if type(measurement_started) is not bool:
        raise HoldoutAdmissionError("measurement_started must be an exact bool")
    if measurement_started and not journal_exists:
        raise HoldoutAdmissionError("measurement cannot precede the durable journal")
    campaign_run_id = _require_text(campaign_run_id, "campaign_run_id")
    run_relpath = _portable_run_relpath(run_relpath)
    mode = _require_text(mode, "mode")
    root = provision_shared_admission_root(Path(repo_root))
    measurement_head, protocol_sha256, fixed_protocol, fixed_freeze = _authority(
        Path(repo_root), protocol, verified_freeze_document, freeze_sha256,
    )
    try:
        signatures = protected_signatures_from_verified_freeze(fixed_freeze)
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
    signature_by_key = {item.freeze_holdout_key: item for item in signatures}
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
            "attempt_ids": list(attempts),
        })

    with _locked(root):
        ledger_rows = _read_ledger(root / _LEDGER_NAME)
        matching_run_rows = [
            row for row in ledger_rows
            if row.get("campaign_run_id") == campaign_run_id
            and row.get("run_relpath") == run_relpath
        ]
        if resume and not journal_exists and matching_run_rows:
            raise HoldoutAdmissionError(
                "resume journal is absent after admission ledger issuance"
            )
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
        claims=tuple(claims), signatures=signature_by_key, mode=mode,
        resume=resume, measurement_started=measurement_started,
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
    reservation: FloorHoldoutReservation, *, manifest_sha256: str,
) -> dict[str, CellHoldoutAdmission]:
    """Durably append evidence rows, then issue cell and attempt capabilities."""

    state = _reservation_state(reservation)
    manifest_sha256 = _require_sha256(manifest_sha256, "manifest_sha256")
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
        try:
            observation = issue_holdout_observation_admission(
                verified_freeze_document=state.freeze,
                freeze_holdout_key=row["freeze_holdout_key"],
            )
        except HoldoutObservationError as exc:
            raise HoldoutAdmissionError(f"cannot issue observation capability: {exc}") from exc
        token = CellHoldoutAdmission(
            freeze_holdout_key=row["freeze_holdout_key"],
            freeze_candidate_id=row["freeze_candidate_id"],
            trial_workload_name=row["trial_workload_name"],
            configuration_id=row["configuration_id"],
            cell_id=row["cell_id"],
        )
        cell_state = _CellState(
            token=token, observation=observation, root=state.root, row=row,
            claim_digest=_claim_digest(_key_fields(
                freeze_sha256=row["freeze_sha256"],
                freeze_holdout_key=row["freeze_holdout_key"],
                configuration_id=row["configuration_id"],
                ccbench_pin=row["ccbench_pin"], env_tag=row["env_tag"],
            )),
            attempt_ids=frozenset(row["attempt_ids"]),
        )
        with _state_lock:
            _cell_states[id(token)] = cell_state
        admissions[token.cell_id] = token
    return admissions


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
    signature = MinimalHoldoutSignature(
        freeze_holdout_key=row["freeze_holdout_key"],
        freeze_candidate_id=row["freeze_candidate_id"],
        trial_workload_name=row["trial_workload_name"],
        ycsb_rratio=row["workload"].get("ycsb_rratio"),
    )
    try:
        assert_issued_holdout_observation(
            state.observation, expected_signature=signature,
        )
    except HoldoutObservationError as exc:
        raise HoldoutAdmissionError(f"observation capability mismatch: {exc}") from exc


def consume_attempt_ticket(
    admission: CellHoldoutAdmission, *, attempt_id: str,
) -> HoldoutObservationAdmission:
    """Atomically and durably consume one frozen attempt immediately before measure."""

    state = _cell_state(admission)
    attempt_id = _require_text(attempt_id, "attempt_id")
    if attempt_id not in state.attempt_ids:
        raise HoldoutAdmissionError("attempt_id is not in the frozen ticket set")
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
        assert_issued_holdout_observation(state.observation)
    except HoldoutObservationError as exc:
        raise HoldoutAdmissionError(f"observation capability is no longer valid: {exc}") from exc
    return state.observation
