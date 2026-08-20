# -*- coding: utf-8 -*-
"""8b floor holdout admission backed by a worktree-shared durable ledger.

The cell claim, not the JSONL evidence row, is the one-shot authority.  Claims
and attempt-consumption markers use ``O_EXCL`` under a root derived only from
Git's common directory, so linked worktrees contend on the same inodes.

保証境界: read-only inspector は現在状態だけを見る。
台帳を削除して同一 bytes を再構成する攻撃は検出できない。全 field は公開かつ決定的で、
``O_EXCL`` は file が存在する間だけ効く。
この耐性は本 wave の保証範囲外である。
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
import secrets
import stat
import subprocess
import threading
from typing import Any, Literal

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
    "FloorHoldoutEvidenceInspection",
    "FloorHoldoutEvidenceError",
    "FloorHoldoutReservation",
    "HoldoutAdmissionError",
    "NPilotReservationReceipt",
    "TransactionInspection",
    "NPilotCellHoldoutAdmission",
    "OracleCellHoldoutAdmission",
    "OBSERVATION_ROLE_FLOOR_CAMPAIGN",
    "OBSERVATION_ROLE_N_PILOT",
    "OBSERVATION_ROLE_N_PILOT_R33",
    "OBSERVATION_ROLE_ORACLE_DRIVER",
    "assert_cell_holdout_admission",
    "consume_attempt_ticket",
    "consume_n_pilot_attempt_ticket",
    "consume_oracle_attempt_ticket",
    "abort_unpublished_n_pilot_transaction",
    "write_guarded_create_bytes",
    "assert_holdout_safe_bytes",
    "_canonical_n_pilot_attempt_ledger_row",
    "_inspect_n_pilot_transaction_locked",
    "_recover_n_pilot_attempt_ledger_locked",
    "_recover_n_pilot_transactions_locked",
    "finalize_floor_holdout_admissions",
    "inspect_floor_holdout_admission_evidence",
    "provision_shared_admission_root",
    "reserve_oracle_holdout_observations",
    "reserve_n_pilot_holdout_observations",
    "reserve_floor_holdout_observations",
    "shared_admission_root",
)

_FREEZE_REL = "output/s8b-freeze/holdout_freeze.json"
_ROOT_REL = Path("izanagi") / "s8b-holdout-admission-v1"
_LOCK_NAME = "ledger.lock"
_LEDGER_NAME = "ledger.jsonl"
_ATTEMPT_LEDGER_NAME = "attempt-ledger.jsonl"
_R33_RECEIPT_SCHEMA = "s8b-n-pilot-reservation/v2"
_R33_MANIFEST_SCHEMA = "s8b-n-pilot-admission-manifest/v1"
_R33_TRANSACTION_SCHEMA = "s8b-n-pilot-admission-transaction/v2"
_R33_ABORT_SCHEMA = "s8b-n-pilot-transaction-abort/v1"
_R33_TRANSACTION_DIR = "transactions"
_R33_RECEIPT_DIR = "receipts"
_R33_MANIFEST_DIR = "manifests"
_R33_QUARANTINE_DIR = "transaction-quarantine"
_R33_CLAIM_SCHEMA = "s8b-n-pilot-r33-cell-claim/v1"
_CLAIM_SCHEMA_V1 = "s8b-holdout-cell-claim/v1"
_CLAIM_SCHEMA_V2 = "s8b-holdout-cell-claim/v2"
_CLAIM_SCHEMA = _CLAIM_SCHEMA_V2
_LEDGER_SCHEMA = "s8b-holdout-observation-ledger/v1"
_ATTEMPT_SCHEMA = "s8b-holdout-attempt-consumption/v1"
_LEDGER_PROJECTION_SCHEMA = "s8b-floor-admission-ledger-projection/v1"
_REFREEZE_DISQUALIFICATION_SCHEMA = "s8b-refreeze-disqualification/v1"
_REFREEZE_DISQUALIFICATION_DIR = "refreeze-disqualifications"
_MAX_LEDGER_BYTES = 16 * 1024 * 1024
_HEX64 = frozenset("0123456789abcdef")
OBSERVATION_ROLE_FLOOR_CAMPAIGN = "floor_campaign"
OBSERVATION_ROLE_N_PILOT = "n_pilot"
OBSERVATION_ROLE_N_PILOT_R33 = "n_pilot_r33"
OBSERVATION_ROLE_ORACLE_DRIVER = "oracle_driver"
_OBSERVATION_ROLES = {
    OBSERVATION_ROLE_FLOOR_CAMPAIGN: {},
    OBSERVATION_ROLE_N_PILOT: {},
    OBSERVATION_ROLE_ORACLE_DRIVER: {},
    "n_pilot_r33": {
        "generation_id": "n-pilot-r33",
        "pilot_rounds": 33,
        "allocation_count": 3,
        "cell_count": 12,
        "schedule_row_count": 396,
        "decision_pin": "t1142-n-pilot-r33-admission-authority",
    },
}


class HoldoutAdmissionError(RuntimeError):
    """The fixed authority or durable one-shot admission cannot be proven."""


class FloorHoldoutEvidenceError(HoldoutAdmissionError):
    """Read-only floor evidence inspection の構造化された拒否。"""

    category: Literal["unverifiable", "mismatch"]
    reason: str

    def __init__(
        self, *, category: Literal["unverifiable", "mismatch"], reason: str,
    ):
        if category not in {"unverifiable", "mismatch"}:
            raise ValueError("unknown floor holdout evidence category")
        if type(reason) is not str or not reason:
            raise ValueError("floor holdout evidence reason must be nonempty")
        self.category = category
        self.reason = reason
        super().__init__(f"{category}: {reason}")


class FloorHoldoutEvidenceInspection(dict[str, object]):
    """Receipt-shaped inspection result with a mandatory derived policy bit.

    The mapping bytes remain exactly the portable v1 receipt.  Keeping the
    derived value out of the mapping preserves the result/receipt schema while
    making it impossible for the live verifier to omit the comparison.
    """

    __slots__ = ("derived_eligible_for_refreeze",)

    derived_eligible_for_refreeze: bool

    def __init__(
        self, receipt: Mapping[str, object], *, derived_eligible_for_refreeze: bool,
    ) -> None:
        if type(derived_eligible_for_refreeze) is not bool:
            raise TypeError("derived_eligible_for_refreeze must be an exact bool")
        super().__init__(receipt)
        self.derived_eligible_for_refreeze = derived_eligible_for_refreeze


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
class NPilotCellHoldoutAdmission:
    """Pilot cell capability whose complete-block tickets are separate."""

    freeze_holdout_key: str
    freeze_candidate_id: str
    trial_workload_name: str
    configuration_id: str
    cell_id: str


class NPilotReservationReceipt(dict[str, object]):
    """Durable R33 reservation receipt.

    The mapping is the authoritative receipt document.  The two private
    attributes only identify where the document was published; they are not
    serialized and therefore cannot accidentally become part of the public
    schema.  Keeping this as a mapping also makes a JSON-loaded receipt usable
    by a later process without any reservation state in this interpreter.
    """

    __slots__ = ("_receipt_sha256", "_root")

    def __init__(
        self, document: Mapping[str, object], *, receipt_sha256: str, root: Path,
    ) -> None:
        super().__init__(_mutable_json_tree(document))
        self._receipt_sha256 = receipt_sha256
        self._root = root

    @property
    def receipt_sha256(self) -> str:
        return self._receipt_sha256

    @property
    def document(self) -> Mapping[str, object]:
        return self

    def __getattr__(self, name: str) -> object:
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    @property
    def root(self) -> Path:
        return self._root

    @property
    def receipt_path(self) -> Path:
        return self._root / _R33_RECEIPT_DIR / f"{self._receipt_sha256}.json"

    @property
    def authoritative_receipt_path(self) -> Path:
        return self.receipt_path

    @property
    def manifest_path(self) -> Path:
        return self._root / _R33_MANIFEST_DIR / f"{self._receipt_sha256}.json"

    @property
    def external_manifest_path(self) -> Path:
        return self.manifest_path


class TransactionInspection(dict[str, object]):
    """Read-only transaction inspection result used by recovery and tooling."""

    __slots__ = ()

    @property
    def transaction_id(self) -> str:
        return str(self["transaction_id"])

    @property
    def state(self) -> str:
        return str(self["state"])

    @property
    def visible_publish(self) -> bool:
        return bool(self["visible_publish"])

    @property
    def manual_reconcile_required(self) -> bool:
        return bool(self["manual_reconcile_required"])

    def __getattr__(self, name: str) -> object:
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


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
    retry_slots_per_cell: int


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


@dataclass(frozen=True, slots=True)
class _NPilotCellState:
    token: NPilotCellHoldoutAdmission
    root: Path
    row: dict[str, Any]
    claim_digest: str
    attempt_ids_by_schedule_index: Mapping[int, str]
    verified_freeze: dict[str, Any]
    neutral_holdouts: Mapping[str, Mapping[str, object]]
    pilot_reps: int


_reservation_states: dict[int, _ReservationState] = {}
_cell_states: dict[int, _CellState] = {}
_oracle_cell_states: dict[int, _OracleCellState] = {}
_n_pilot_cell_states: dict[int, _NPilotCellState] = {}
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
    for name in (
        "claims", "consumed", _REFREEZE_DISQUALIFICATION_DIR,
        _R33_TRANSACTION_DIR, _R33_RECEIPT_DIR, _R33_MANIFEST_DIR,
        _R33_QUARANTINE_DIR,
    ):
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


@contextmanager
def _locked_readonly(root: Path):
    """既存 lock inode を変更せず shared lock 下で現在状態を読む。"""

    path = root / _LOCK_NAME
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise FloorHoldoutEvidenceError(
            category="unverifiable", reason="nofollow-unavailable",
        )
    try:
        fd = os.open(path, os.O_RDONLY | nofollow)
    except OSError as exc:
        raise FloorHoldoutEvidenceError(
            category="unverifiable", reason="lock-unavailable",
        ) from exc
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise FloorHoldoutEvidenceError(
                category="unverifiable", reason="lock-not-regular",
            )
        fcntl.flock(fd, fcntl.LOCK_SH)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def _head_blob(repo_root: Path, relpath: str, commit_oid: str) -> tuple[str, bytes]:
    """固定 commit の衛生化 100644 blob と working tree の一致を検査する。"""
    try:
        # s8b_floor_campaign imports this module, so keep the reverse edge local.
        from . import s8b_floor_campaign as _floor_campaign

        raw = _floor_campaign._head_blob_100644(
            repo_root, relpath, commit_oid,
        )
    except Exception as exc:
        raise HoldoutAdmissionError(
            f"cannot read fixed commit blob: {commit_oid}:{relpath}"
        ) from exc
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
    return commit_oid, raw


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
    try:
        # s8b_floor_campaign imports this module, so keep the reverse edge local.
        from . import s8b_floor_campaign as _floor_campaign

        protocol_record = _floor_campaign.resolve_current_floor_protocol(
            root=root,
        )
    except Exception as exc:
        raise HoldoutAdmissionError(
            f"cannot resolve current floor protocol: {exc}"
        ) from exc
    if type(protocol_record) is not _floor_campaign.IndexedFloorProtocol:
        raise HoldoutAdmissionError(
            "current floor protocol resolver returned an invalid record type"
        )
    fixed_commit_oid = protocol_record.commit_oid
    if (
        type(fixed_commit_oid) is not str
        or len(fixed_commit_oid) != 40
        or any(char not in _HEX64 for char in fixed_commit_oid)
    ):
        raise HoldoutAdmissionError(
            "resolved protocol record has an invalid fixed commit OID"
        )
    _protocol_oid, protocol_raw = _head_blob(
        root, protocol_record.path, fixed_commit_oid,
    )
    if protocol_raw != protocol_record.raw_bytes:
        raise HoldoutAdmissionError(
            "resolved protocol bytes do not match the indexed record"
        )
    protocol_sha256 = hashlib.sha256(protocol_raw).hexdigest()
    if protocol_sha256 != protocol_record.sha256:
        raise HoldoutAdmissionError(
            "resolved protocol sha256 does not match the indexed record"
        )
    protocol_document = _strict_json(protocol_raw, "floor protocol")
    if protocol_document != dict(protocol):
        raise HoldoutAdmissionError("fixed protocol bytes do not match the supplied protocol")
    freeze_ref = protocol_document.get("freeze")
    if not isinstance(freeze_ref, Mapping) or freeze_ref.get("path") != _FREEZE_REL:
        raise HoldoutAdmissionError("protocol freeze path is not the fixed canonical path")
    _freeze_oid, freeze_raw = _head_blob(root, _FREEZE_REL, fixed_commit_oid)
    freeze_document = _strict_json(freeze_raw, "holdout freeze")
    actual_freeze_sha256 = hashlib.sha256(freeze_raw).hexdigest()
    if freeze_ref.get("sha256") != actual_freeze_sha256:
        raise HoldoutAdmissionError("fixed protocol freeze hash does not match freeze bytes")
    if _require_sha256(freeze_sha256, "freeze_sha256") != actual_freeze_sha256:
        raise HoldoutAdmissionError("verified freeze hash does not match fixed freeze bytes")
    if freeze_document != dict(freeze):
        raise HoldoutAdmissionError("fixed freeze bytes do not match the verified freeze document")
    measurement_head = fixed_commit_oid
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


def _refreeze_disqualification_name(campaign_run_id: str) -> str:
    digest = hashlib.sha256(campaign_run_id.encode("utf-8")).hexdigest()
    return f"{digest}.json"


def _refreeze_disqualification_path(root: Path, campaign_run_id: str) -> Path:
    return (
        root / _REFREEZE_DISQUALIFICATION_DIR
        / _refreeze_disqualification_name(campaign_run_id)
    )


def _refreeze_disqualification_document(
    *, campaign_run_id: str, run_relpath: str, protocol_sha256: str,
    freeze_sha256: str,
) -> dict[str, object]:
    return {
        "schema_version": _REFREEZE_DISQUALIFICATION_SCHEMA,
        "reason": "resume",
        "campaign_run_id": _require_text(campaign_run_id, "campaign_run_id"),
        "run_relpath": _portable_run_relpath(run_relpath),
        "protocol_sha256": _require_sha256(protocol_sha256, "protocol_sha256"),
        "freeze_sha256": _require_sha256(freeze_sha256, "freeze_sha256"),
    }


def _read_refreeze_markers_for_write(
    root: Path,
) -> dict[str, dict[str, Any]]:
    marker_root = root / _REFREEZE_DISQUALIFICATION_DIR
    markers: dict[str, dict[str, Any]] = {}
    try:
        paths = sorted(marker_root.iterdir(), key=lambda path: path.name)
    except OSError as exc:
        raise HoldoutAdmissionError(
            "resume disqualification marker directory is unavailable"
        ) from exc
    for path in paths:
        marker = _read_canonical_document(path)
        if (
            set(marker) != set(_REFREEZE_DISQUALIFICATION_KEYS)
            or marker.get("schema_version") != _REFREEZE_DISQUALIFICATION_SCHEMA
            or marker.get("reason") != "resume"
        ):
            raise HoldoutAdmissionError(
                "resume disqualification marker shape is unknown"
            )
        marker_campaign = marker.get("campaign_run_id")
        if type(marker_campaign) is not str or not marker_campaign:
            raise HoldoutAdmissionError(
                "resume disqualification marker identity is invalid"
            )
        if marker_campaign in markers:
            raise HoldoutAdmissionError(
                "resume disqualification marker is duplicated"
            )
        markers[marker_campaign] = marker
        if path.name != _refreeze_disqualification_name(marker_campaign):
            raise HoldoutAdmissionError(
                "resume disqualification marker name is noncanonical"
            )
    return markers


def _record_floor_resume_disqualification(
    *, repo_root: Path, campaign_run_id: str, run_relpath: str,
    protocol_sha256: str, freeze_sha256: str,
) -> None:
    """Create or exact-check the run-wide resume marker under the ledger lock."""

    document = _refreeze_disqualification_document(
        campaign_run_id=campaign_run_id, run_relpath=run_relpath,
        protocol_sha256=protocol_sha256, freeze_sha256=freeze_sha256,
    )
    root = provision_shared_admission_root(Path(repo_root))
    path = _refreeze_disqualification_path(root, campaign_run_id)
    with _locked(root):
        markers = _read_refreeze_markers_for_write(root)
        prior = markers.get(campaign_run_id)
        if prior is None:
            _write_exclusive(path, document)
        elif prior != document:
            raise HoldoutAdmissionError(
                "resume disqualification marker identity mismatch"
            )


def _canonical_nondefault_seams(value: object) -> list[str]:
    if type(value) is not list or any(type(item) is not str for item in value):
        raise HoldoutAdmissionError("nondefault_seams must be a list of exact strings")
    if len(value) != len(set(value)):
        raise HoldoutAdmissionError("nondefault_seams contains duplicates")
    if value != sorted(value):
        raise HoldoutAdmissionError("nondefault_seams is not in canonical order")
    unknown = set(value) - _floor_contract.REFREEZE_DISQUALIFYING_SEAM_NAMES
    if unknown:
        raise HoldoutAdmissionError(
            f"nondefault_seams contains unknown names: {sorted(unknown)}"
        )
    return list(value)


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


def _assert_holdout_safe_bytes(logical_name: str, payload: bytes) -> None:
    """Apply the same literal holdout gate used by result writers.

    Importing the freeze scanner locally keeps the admission module below the
    campaign/driver layer and avoids the circular import that existed when
    the driver owned the guarded writer.
    """

    if type(logical_name) is not str or not logical_name:
        raise HoldoutAdmissionError("guarded writer logical_name is invalid")
    if type(payload) is not bytes:
        raise HoldoutAdmissionError("guarded writer payload must be bytes")
    try:
        from .s8b_holdout_freeze import holdout_conjunction_hits

        hits = holdout_conjunction_hits({logical_name: payload.decode("utf-8")})
    except UnicodeError as exc:
        raise HoldoutAdmissionError(
            f"{logical_name} is not valid UTF-8 for holdout-safe scanning"
        ) from exc
    except Exception as exc:
        raise HoldoutAdmissionError("holdout-safe scanner is unavailable") from exc
    contaminated = {key: value for key, value in hits.items() if value}
    if contaminated:
        raise HoldoutAdmissionError(
            f"holdout conjunction contamination: {sorted(contaminated)}"
        )


def assert_holdout_safe_bytes(logical_name: str, payload: bytes) -> None:
    """Public admission-side spelling of the shared holdout-safe byte gate."""

    _assert_holdout_safe_bytes(logical_name, payload)


def _assert_no_symlink_components(path: Path) -> None:
    absolute = Path(os.path.abspath(os.fspath(path)))
    components = [Path(absolute.anchor)]
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        components.append(current)
    for component in components:
        try:
            mode = component.lstat().st_mode
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise HoldoutAdmissionError(
                f"guarded writer path is unavailable: {component}"
            ) from exc
        if component.is_symlink():
            raise HoldoutAdmissionError(
                f"guarded writer path is symlinked: {component}"
            )
        if component != absolute and not stat.S_ISDIR(mode):
            raise HoldoutAdmissionError(
                f"guarded writer parent is not a directory: {component}"
            )


def write_guarded_create_bytes(
    path: Path,
    payload: bytes,
    *,
    logical_name: str,
) -> str:
    """Holdout-scan and durably create one file without replacing it.

    The scan deliberately happens before parent creation and before opening
    the destination.  This is the authoritative-receipt equivalent of the
    driver's guarded result writer, with ``O_EXCL`` rather than replacement
    semantics.
    """

    assert_holdout_safe_bytes(logical_name, payload)
    destination = Path(os.path.abspath(os.fspath(path)))
    parent = destination.parent
    _assert_no_symlink_components(parent)
    parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    _assert_no_symlink_components(parent)
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise HoldoutAdmissionError("O_NOFOLLOW is unavailable")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | nofollow
    try:
        fd = os.open(destination, flags, 0o600)
    except FileExistsError:
        raise
    except OSError as exc:
        raise HoldoutAdmissionError(
            f"guarded durable create failed: {destination.name}"
        ) from exc
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise HoldoutAdmissionError("guarded destination is not regular")
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise HoldoutAdmissionError("short guarded durable write")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_directory(parent)
    return hashlib.sha256(payload).hexdigest()


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


def _read_canonical_json_bytes(path: Path) -> dict[str, Any]:
    """Read a canonical JSON object whose bytes intentionally have no LF."""

    try:
        mode = path.lstat().st_mode
        raw = path.read_bytes()
    except OSError as exc:
        raise HoldoutAdmissionError(
            f"cannot read durable JSON record: {path.name}"
        ) from exc
    if not stat.S_ISREG(mode) or path.is_symlink():
        raise HoldoutAdmissionError(
            f"durable JSON record is not regular: {path.name}"
        )
    value = _strict_json(raw, path.name)
    if _canonical_bytes(value) != raw:
        raise HoldoutAdmissionError(
            f"durable JSON record is not canonical bytes: {path.name}"
        )
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
    mode: str, resume: bool, nondefault_seams: list[str],
    irreversible_pilot_approved: bool,
) -> FloorHoldoutReservation:
    """Production reservation entrypoint with the fixed neutral signature table."""

    return _reserve_floor_holdout_observations_core(
        repo_root=repo_root, protocol=protocol,
        verified_freeze_document=verified_freeze_document,
        freeze_sha256=freeze_sha256, cells=cells, schedule=schedule,
        campaign_run_id=campaign_run_id, out_root=out_root, run_dir=run_dir,
        run_relpath=run_relpath, mode=mode, resume=resume,
        nondefault_seams=nondefault_seams,
        irreversible_pilot_approved=irreversible_pilot_approved,
    )


def _reserve_floor_holdout_observations_core(
    *, repo_root: Path, protocol: Mapping[str, object],
    verified_freeze_document: Mapping[str, object], freeze_sha256: str,
    cells: Sequence[Mapping[str, object]], schedule: Sequence[Mapping[str, object]],
    campaign_run_id: str, out_root: Path, run_dir: Path, run_relpath: str,
    mode: str, resume: bool, nondefault_seams: list[str],
    irreversible_pilot_approved: bool,
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
    if mode not in {"pilot", "official"}:
        raise HoldoutAdmissionError("mode is not pilot or official")
    nondefault_seams = _canonical_nondefault_seams(nondefault_seams)
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
            "schema_version": _CLAIM_SCHEMA_V2,
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
            "entry_kind": "resume" if resume else "fresh",
            "nondefault_seams": nondefault_seams,
            "irreversible_pilot_approved": irreversible_pilot_approved,
            "attempt_ids": list(attempts),
        })

    marker_document = _refreeze_disqualification_document(
        campaign_run_id=campaign_run_id, run_relpath=run_relpath,
        protocol_sha256=protocol_sha256, freeze_sha256=freeze_sha256,
    )
    marker_path = _refreeze_disqualification_path(root, campaign_run_id)

    # Run-wide fresh/resume transition table.  Every claim-count decision and
    # immutable-schema compatibility branch is made under the same ledger lock.
    with _locked(root):
        existing: dict[str, dict[str, Any]] = {}
        for claim in claims:
            digest = _claim_digest(claim["key"])
            path = _claim_path(root, digest)
            if path.exists():
                existing[digest] = _read_canonical_document(path)

        existing_schemas = {
            document.get("schema_version") for document in existing.values()
        }
        if not resume and existing:
            raise HoldoutAdmissionError(
                "holdout cell key was already consumed by another fresh run"
            )
        if resume and not existing_schemas.issubset(
            {_CLAIM_SCHEMA_V1, _CLAIM_SCHEMA_V2}
        ):
            raise HoldoutAdmissionError("resume cell claim schema is unknown")
        if resume and len(existing_schemas) > 1:
            raise HoldoutAdmissionError(
                "resume cell claims mix incompatible schema generations"
            )
        create_schema = (
            _CLAIM_SCHEMA_V1
            if existing_schemas == {_CLAIM_SCHEMA_V1}
            else _CLAIM_SCHEMA_V2
        )

        existing_v2_basis: tuple[str, list[str]] | None = None

        for claim in claims:
            digest = _claim_digest(claim["key"])
            path = _claim_path(root, digest)
            prior = existing.get(digest)
            if prior is not None:
                expected = dict(claim)
                if prior.get("schema_version") == _CLAIM_SCHEMA_V1:
                    expected["schema_version"] = _CLAIM_SCHEMA_V1
                    expected.pop("entry_kind")
                    expected.pop("nondefault_seams")
                else:
                    prior_entry_kind = prior.get("entry_kind")
                    if prior_entry_kind not in {"fresh", "resume"}:
                        raise HoldoutAdmissionError(
                            "resume v2 cell claim entry_kind is invalid"
                        )
                    try:
                        prior_nondefault_seams = _canonical_nondefault_seams(
                            prior.get("nondefault_seams")
                        )
                    except HoldoutAdmissionError as exc:
                        raise HoldoutAdmissionError(
                            "resume v2 cell claim nondefault_seams is invalid"
                        ) from exc
                    prior_basis = (
                        prior_entry_kind, prior_nondefault_seams,
                    )
                    if existing_v2_basis is None:
                        existing_v2_basis = prior_basis
                    elif existing_v2_basis != prior_basis:
                        raise HoldoutAdmissionError(
                            "resume v2 cell claims mix incompatible eligibility basis"
                        )
                    expected["entry_kind"] = prior_entry_kind
                    expected["nondefault_seams"] = prior_nondefault_seams
                if prior != expected:
                    raise HoldoutAdmissionError(
                        "resume cell claim does not match the same run identity"
                    )

        markers = _read_refreeze_markers_for_write(root)
        prior_marker = markers.get(campaign_run_id)
        if resume:
            if prior_marker is None:
                _write_exclusive(marker_path, marker_document)
            elif prior_marker != marker_document:
                raise HoldoutAdmissionError(
                    "resume disqualification marker identity mismatch"
                )
        elif prior_marker is not None:
            raise HoldoutAdmissionError(
                "fresh reservation has a resume disqualification marker"
            )

        for claim in claims:
            digest = _claim_digest(claim["key"])
            path = _claim_path(root, digest)
            if digest in existing:
                continue
            if resume and measurement_started:
                raise HoldoutAdmissionError(
                    "cannot backfill a missing cell claim after measurement started"
                )
            document = dict(claim)
            if create_schema == _CLAIM_SCHEMA_V1:
                document["schema_version"] = _CLAIM_SCHEMA_V1
                document.pop("entry_kind")
                document.pop("nondefault_seams")
            try:
                _write_exclusive(path, document)
            except FileExistsError as exc:  # pragma: no cover - lock invariant
                raise HoldoutAdmissionError(
                    "claim appeared while the ledger lock was held"
                ) from exc
        effective_claims = [
            _read_canonical_document(
                _claim_path(root, _claim_digest(claim["key"]))
            )
            for claim in claims
        ]

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
        claims=tuple(effective_claims), signatures=signature_by_key,
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
            retry_slots_per_cell=state.protocol["retry_slots_per_cell"],
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
            "schema_version": _CLAIM_SCHEMA_V1,
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


def _is_r33_reservation_request(
    protocol: Mapping[str, object],
    cells: Sequence[Mapping[str, object]],
    schedule: Sequence[Mapping[str, object]],
) -> bool:
    """Distinguish the new generation from the retained legacy n-pilot API."""

    if not isinstance(protocol, Mapping):
        return False
    design = protocol.get("design")
    if not isinstance(design, Mapping):
        return protocol.get("observation_role") == OBSERVATION_ROLE_N_PILOT_R33
    return (
        protocol.get("observation_role") == OBSERVATION_ROLE_N_PILOT_R33
        or (
            design.get("pilot_rounds") == 33
            and design.get("allocation_count") == 3
            and design.get("allocation_role") == "primary-segment"
            and len(cells) == 12
            and len(schedule) == 396
        )
    )


def _canonical_value_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _r33_protocol_and_freeze(
    *, protocol: Mapping[str, object], protocol_sha256: str,
    verified_freeze_document: Mapping[str, object], freeze_sha256: str,
) -> tuple[dict[str, Any], str, dict[str, Any], str, str, str, int]:
    protocol_document = _mutable_json_tree(protocol)
    if not isinstance(protocol_document, dict):
        raise HoldoutAdmissionError("n pilot R33 protocol document is invalid")
    protocol_sha256 = _require_sha256(protocol_sha256, "protocol_sha256")
    actual_protocol_sha256 = _canonical_value_sha256(protocol_document)
    if actual_protocol_sha256 != protocol_sha256:
        raise HoldoutAdmissionError(
            "n pilot R33 protocol digest does not match canonical JSON bytes"
        )
    freeze_document = _mutable_json_tree(verified_freeze_document)
    if not isinstance(freeze_document, dict):
        raise HoldoutAdmissionError("n pilot R33 verified freeze document is invalid")
    freeze_sha256 = _require_sha256(freeze_sha256, "freeze_sha256")
    freeze_canonical_sha256 = _canonical_value_sha256(freeze_document)
    if freeze_canonical_sha256 != freeze_sha256:
        raise HoldoutAdmissionError(
            "n pilot R33 freeze digest does not match canonical JSON bytes"
        )
    freeze_ref = protocol_document.get("freeze")
    if (
        not isinstance(freeze_ref, Mapping)
        or freeze_ref.get("path") != _FREEZE_REL
        or freeze_ref.get("sha256") != freeze_sha256
    ):
        raise HoldoutAdmissionError("n pilot R33 protocol is not bound to the freeze hash")
    environment = protocol_document.get("environment")
    design = protocol_document.get("design")
    if not isinstance(environment, Mapping) or not isinstance(design, Mapping):
        raise HoldoutAdmissionError("n pilot R33 protocol authority fields are unavailable")
    if design.get("pilot_rounds") != 33:
        raise HoldoutAdmissionError("n pilot R33 pilot_rounds must be exactly 33")
    if design.get("allocation_count") != 3:
        raise HoldoutAdmissionError("n pilot R33 allocation_count must be exactly 3")
    if design.get("allocation_role") != "primary-segment":
        raise HoldoutAdmissionError("n pilot R33 allocation_role is not the fixed protocol value")
    ccbench_pin = _require_text(environment.get("ccbench_pin"), "ccbench_pin")
    env_tag = _require_text(environment.get("env_tag"), "env_tag")
    pilot_reps = design.get("reps")
    if type(pilot_reps) is not int or pilot_reps <= 0:
        raise HoldoutAdmissionError("n pilot R33 protocol reps is invalid")
    return (
        protocol_document, protocol_sha256, freeze_document, freeze_sha256,
        freeze_canonical_sha256, ccbench_pin, env_tag, pilot_reps,
    )


def _r33_cells_and_schedule(
    *, freeze_document: Mapping[str, object], cells: Sequence[Mapping[str, object]],
    schedule: Sequence[Mapping[str, object]], signatures: Sequence[MinimalHoldoutSignature],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], str]:
    holdouts = freeze_document.get("holdouts")
    if not isinstance(holdouts, Mapping):
        raise HoldoutAdmissionError("n pilot R33 freeze holdouts are unavailable")
    signature_by_key = {item.freeze_holdout_key: item for item in signatures}
    normalized_cells = [dict(cell) for cell in cells]
    allowed_cell_keys = {
        "cell_id", "holdout_id", "freeze_holdout_key", "configuration_id",
        "records", "threads", "workload",
    }
    if len(normalized_cells) != 12:
        raise HoldoutAdmissionError("n pilot R33 cell set is not exact 12-cell schema")
    cells_by_id: dict[str, dict[str, Any]] = {}
    for cell in normalized_cells:
        if set(cell) - allowed_cell_keys or "cell_id" not in cell:
            raise HoldoutAdmissionError("n pilot R33 cell set has an unknown field")
        raw_holdout = cell.get("holdout_id", cell.get("freeze_holdout_key"))
        freeze_holdout_key = _require_text(raw_holdout, "holdout_id")
        configuration_id = _require_text(
            cell.get("configuration_id"), "configuration_id",
        )
        cell_id = _require_text(cell.get("cell_id"), "cell_id")
        if cell_id != f"{freeze_holdout_key}::{configuration_id}":
            raise HoldoutAdmissionError(
                "n pilot R33 cell_id does not bind holdout and configuration"
            )
        if cell_id in cells_by_id:
            raise HoldoutAdmissionError("n pilot R33 cell_id is duplicated")
        signature = signature_by_key.get(freeze_holdout_key)
        freeze_entry = holdouts.get(freeze_holdout_key)
        if signature is None or not isinstance(freeze_entry, Mapping):
            raise HoldoutAdmissionError("n pilot R33 cell freeze key is not protected")
        variant_binding = freeze_entry.get("variant_binding")
        entries = (
            variant_binding.get("entries")
            if isinstance(variant_binding, Mapping) else None
        )
        if not isinstance(entries, Mapping) or configuration_id not in entries:
            raise HoldoutAdmissionError("n pilot R33 configuration is not freeze-bound")
        workload = freeze_entry.get("ycsb")
        if not isinstance(workload, Mapping) or (
            cell.get("records") != freeze_entry.get("records")
            or cell.get("threads") != freeze_entry.get("threads")
            or cell.get("workload") != dict(workload)
        ):
            raise HoldoutAdmissionError("n pilot R33 cell differs from freeze projection")
        normalized = dict(cell)
        normalized["holdout_id"] = freeze_holdout_key
        normalized.pop("freeze_holdout_key", None)
        cells_by_id[cell_id] = normalized

    normalized_schedule = [dict(row) for row in schedule]
    if len(normalized_schedule) != 396:
        raise HoldoutAdmissionError("n pilot R33 schedule must contain 396 rows")
    schedule_indexes_by_cell: dict[str, list[int]] = {
        cell_id: [] for cell_id in cells_by_id
    }
    cells_by_round: dict[int, set[str]] = {}
    for expected_seq, row in enumerate(normalized_schedule):
        required = {"seq", "pilot_round", "cell_id"}
        if not required.issubset(row) or set(row) - {
            "seq", "pilot_round", "cell_id", "global_schedule_index",
            "global_pilot_round",
        }:
            raise HoldoutAdmissionError("n pilot R33 schedule row schema is invalid")
        if row.get("seq") != expected_seq:
            raise HoldoutAdmissionError("n pilot R33 schedule seq is not contiguous")
        if "global_schedule_index" in row and row["global_schedule_index"] != expected_seq:
            raise HoldoutAdmissionError("n pilot R33 global schedule index is not canonical")
        pilot_round = row.get("pilot_round")
        if type(pilot_round) is not int or not 1 <= pilot_round <= 33:
            raise HoldoutAdmissionError("n pilot R33 schedule round is invalid")
        if "global_pilot_round" in row and row["global_pilot_round"] != pilot_round:
            raise HoldoutAdmissionError("n pilot R33 global pilot round is not canonical")
        cell_id = _require_text(row.get("cell_id"), "cell_id")
        if cell_id not in cells_by_id:
            raise HoldoutAdmissionError("n pilot R33 schedule contains an unknown cell")
        if cell_id in cells_by_round.setdefault(pilot_round, set()):
            raise HoldoutAdmissionError("n pilot R33 schedule repeats a cell within a round")
        cells_by_round[pilot_round].add(cell_id)
        schedule_indexes_by_cell[cell_id].append(expected_seq)
    if (
        sorted(cells_by_round) != list(range(1, 34))
        or any(cell_set != set(cells_by_id) for cell_set in cells_by_round.values())
    ):
        raise HoldoutAdmissionError("n pilot R33 schedule is not 33 complete blocks")
    schedule_sha256 = _canonical_value_sha256(normalized_schedule)
    for cell_id, normalized in cells_by_id.items():
        normalized["schedule_indexes"] = schedule_indexes_by_cell[cell_id]
    return cells_by_id, normalized_schedule, schedule_sha256


def _r33_claim_and_ledger_documents(
    *, cells_by_id: Mapping[str, Mapping[str, object]], signatures: Sequence[MinimalHoldoutSignature],
    protocol_sha256: str, freeze_sha256: str, schedule_sha256: str,
    ccbench_pin: str, env_tag: str, campaign_run_id: str, pilot_reps: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    signature_by_key = {item.freeze_holdout_key: item for item in signatures}
    claims: list[dict[str, Any]] = []
    ledger_rows: list[dict[str, Any]] = []
    for cell_id in sorted(cells_by_id):
        cell = cells_by_id[cell_id]
        freeze_holdout_key = _require_text(cell.get("holdout_id"), "holdout_id")
        configuration_id = _require_text(
            cell.get("configuration_id"), "configuration_id",
        )
        signature = signature_by_key[freeze_holdout_key]
        schedule_indexes = list(cell["schedule_indexes"])
        attempt_ids = [
            f"{campaign_run_id}::{cell_id}::schedule{schedule_index}"
            for schedule_index in schedule_indexes
        ]
        key = _key_fields(
            freeze_sha256=freeze_sha256,
            freeze_holdout_key=freeze_holdout_key,
            configuration_id=configuration_id,
            ccbench_pin=ccbench_pin,
            env_tag=env_tag,
            observation_role=OBSERVATION_ROLE_N_PILOT_R33,
        )
        common = {
            "protocol_sha256": protocol_sha256,
            "freeze_sha256": freeze_sha256,
            "schedule_sha256": schedule_sha256,
            "freeze_candidate_id": signature.freeze_candidate_id,
            "trial_workload_name": signature.trial_workload_name,
            "cell_id": cell_id,
            "records": cell["records"],
            "threads": cell["threads"],
            "workload": dict(cell["workload"]),
            "campaign_run_id": campaign_run_id,
            "irreversible_pilot_approved": True,
            "schedule_indexes": schedule_indexes,
            "attempt_ids": attempt_ids,
            "attempt_count": len(attempt_ids),
        }
        claims.append({
            "schema_version": _R33_CLAIM_SCHEMA,
            "event": "claim",
            "key": key,
            **common,
        })
        ledger_rows.append({
            "schema_version": _LEDGER_SCHEMA,
            "event": "admit",
            **key,
            **common,
            "reps": pilot_reps,
        })
    return claims, ledger_rows


def _r33_transaction_root(root: Path, transaction_id: str) -> Path:
    transaction_id = _require_sha256(transaction_id, "transaction_id")
    return root / _R33_TRANSACTION_DIR / transaction_id


def _r33_raw(path: Path, *, missing: bytes | None = None) -> bytes:
    try:
        mode = path.lstat().st_mode
        raw = path.read_bytes()
    except FileNotFoundError:
        if missing is not None:
            return missing
        raise HoldoutAdmissionError(f"durable R33 file is missing: {path.name}")
    except OSError as exc:
        raise HoldoutAdmissionError(f"cannot read durable R33 file: {path.name}") from exc
    if not stat.S_ISREG(mode) or path.is_symlink():
        raise HoldoutAdmissionError(f"durable R33 file is not regular: {path.name}")
    return raw


def _r33_create_raw(path: Path, payload: bytes) -> None:
    """Create internal transaction bytes without treating private claims as public."""

    parent = path.parent
    _ensure_private_directory(parent)
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise HoldoutAdmissionError("O_NOFOLLOW is unavailable")
    try:
        fd = os.open(
            path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | nofollow, 0o600,
        )
    except FileExistsError:
        raise
    except OSError as exc:
        raise HoldoutAdmissionError(f"internal R33 create failed: {path.name}") from exc
    try:
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise HoldoutAdmissionError("short internal R33 write")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_directory(parent)


def _r33_line_rows(raw: bytes, field: str) -> list[dict[str, Any]]:
    if raw and not raw.endswith(b"\n"):
        raise HoldoutAdmissionError(f"R33 {field} has a truncated final row")
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(raw.splitlines(), 1):
        if not line:
            raise HoldoutAdmissionError(f"R33 {field} has a blank row: {index}")
        row = _strict_json(line, f"{field}:{index}")
        if _canonical_line(row) != line + b"\n":
            raise HoldoutAdmissionError(f"R33 {field} row is not canonical: {index}")
        rows.append(row)
    return rows


def _r33_staged_bytes_sha256(transaction_root: Path) -> str:
    staged = transaction_root / "staged"
    digest = hashlib.sha256()
    try:
        paths = sorted(
            path for path in staged.rglob("*") if path.is_file() and not path.is_symlink()
        )
    except OSError as exc:
        raise HoldoutAdmissionError("R33 transaction staging cannot be enumerated") from exc
    for path in paths:
        relative = path.relative_to(transaction_root).as_posix().encode("utf-8")
        payload = _r33_raw(path)
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def _r33_claim_key_digest(document: Mapping[str, object]) -> str:
    key = document.get("key")
    if not isinstance(key, Mapping):
        raise HoldoutAdmissionError("R33 claim key is unavailable")
    normalized = _key_fields(
        freeze_sha256=key.get("freeze_sha256"),
        freeze_holdout_key=key.get("freeze_holdout_key"),
        configuration_id=key.get("configuration_id"),
        ccbench_pin=key.get("ccbench_pin"),
        env_tag=key.get("env_tag"),
        observation_role=key.get("observation_role"),
    )
    if normalized["observation_role"] != OBSERVATION_ROLE_N_PILOT_R33:
        raise HoldoutAdmissionError("R33 transaction contains a non-R33 claim")
    return _claim_digest(normalized)


def _r33_ledger_key_digest(row: Mapping[str, object]) -> str:
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
        raise HoldoutAdmissionError("R33 ledger row key is invalid") from exc
    if key["observation_role"] != OBSERVATION_ROLE_N_PILOT_R33:
        raise HoldoutAdmissionError("R33 ledger identity is not n_pilot_r33")
    return _claim_digest(key)


def _r33_read_staged_claims(transaction_root: Path) -> list[tuple[str, dict[str, Any], bytes]]:
    claims_root = transaction_root / "staged" / "claims"
    try:
        paths = sorted(claims_root.iterdir(), key=lambda path: path.name)
    except OSError as exc:
        raise HoldoutAdmissionError("R33 staged claim directory is unavailable") from exc
    claims: list[tuple[str, dict[str, Any], bytes]] = []
    for path in paths:
        if path.suffix != ".claim" or path.name != f"{path.stem}.claim":
            raise HoldoutAdmissionError("R33 staged claim filename is noncanonical")
        raw = _r33_raw(path)
        document = _read_canonical_document(path)
        digest = _r33_claim_key_digest(document)
        if path.stem != digest:
            raise HoldoutAdmissionError("R33 staged claim filename does not bind its key")
        claims.append((digest, document, raw))
    if len(claims) != 12:
        raise HoldoutAdmissionError("R33 transaction must stage exactly 12 claims")
    return claims


def _r33_read_staged_transaction(
    root: Path, transaction_id: str,
) -> tuple[Path, dict[str, Any], list[tuple[str, dict[str, Any], bytes]], list[dict[str, Any]], bytes, dict[str, Any], bytes]:
    transaction_root = _r33_transaction_root(root, transaction_id)
    staged = transaction_root / "staged"
    claims = _r33_read_staged_claims(transaction_root)
    base_raw = _r33_raw(staged / "base-ledger.jsonl", missing=b"")
    _r33_line_rows(base_raw, "staged base ledger")
    append_raw = _r33_raw(staged / "ledger-append.jsonl")
    append_rows = _r33_line_rows(append_raw, "staged ledger append")
    if len(append_rows) != 12:
        raise HoldoutAdmissionError("R33 transaction must stage exactly 12 ledger rows")
    receipt_path = staged / "receipt.json"
    receipt_raw = _r33_raw(receipt_path)
    receipt = _read_canonical_json_bytes(receipt_path)
    manifest_path = staged / "manifest.json"
    manifest_raw = _r33_raw(manifest_path)
    manifest = _read_canonical_json_bytes(manifest_path)
    return (
        transaction_root, receipt, claims, append_rows, append_raw,
        manifest, manifest_raw,
    )


_R33_RECEIPT_KEYS = frozenset({
    "schema_version", "observation_role", "campaign_run_id",
    "protocol_sha256", "freeze_sha256", "freeze_canonical_sha256",
    "schedule_sha256", "pilot_rounds", "allocation_count",
    "schedule_row_count", "cell_count", "attempt_count", "transaction_id",
    "receipt_ref", "cells", "allocation_slices",
})
_R33_RECEIPT_CELL_KEYS = frozenset({
    "cell_ref", "cell_id", "global_schedule_indexes", "claim_digest",
    "claim_file_sha256", "ledger_row_sha256",
})
_R33_MANIFEST_KEYS = frozenset({
    "schema_version", "observation_role", "campaign_run_id",
    "authoritative_receipt_sha256", "receipt_ref", "protocol_sha256",
    "freeze_sha256", "schedule_sha256", "pilot_rounds", "allocation_count",
    "cells", "allocation_slices",
})
_R33_MANIFEST_CELL_KEYS = frozenset({"cell_ref", "global_schedule_indexes"})
_R33_TRANSACTION_KEYS = frozenset({
    "schema_version", "transaction_id", "state", "base_ledger_sha256",
    "base_ledger_line_count", "ledger_append_sha256", "ledger_append_row_count",
    "claim_files", "receipt_path", "receipt_sha256",
})


def _r33_validate_receipt(
    receipt: Mapping[str, object], *, expected_transaction_id: str | None = None,
) -> dict[str, Any]:
    if not isinstance(receipt, Mapping) or set(receipt) != set(_R33_RECEIPT_KEYS):
        raise HoldoutAdmissionError("R33 authoritative receipt schema is invalid")
    if receipt.get("schema_version") != _R33_RECEIPT_SCHEMA:
        raise HoldoutAdmissionError("R33 authoritative receipt schema version is invalid")
    if receipt.get("observation_role") != OBSERVATION_ROLE_N_PILOT_R33:
        raise HoldoutAdmissionError("R33 authoritative receipt role is invalid")
    for field in (
        "campaign_run_id", "protocol_sha256", "freeze_sha256",
        "freeze_canonical_sha256", "schedule_sha256", "transaction_id",
        "receipt_ref",
    ):
        _require_text(receipt.get(field), f"receipt.{field}")
    for field in (
        "protocol_sha256", "freeze_sha256", "freeze_canonical_sha256",
        "schedule_sha256", "transaction_id", "receipt_ref",
    ):
        _require_sha256(receipt.get(field), f"receipt.{field}")
    if expected_transaction_id is not None and receipt["transaction_id"] != expected_transaction_id:
        raise HoldoutAdmissionError("R33 receipt transaction identity mismatch")
    for field, expected in (
        ("pilot_rounds", 33), ("allocation_count", 3),
        ("schedule_row_count", 396), ("cell_count", 12), ("attempt_count", 396),
    ):
        if receipt.get(field) != expected:
            raise HoldoutAdmissionError(f"R33 receipt {field} is not fixed")
    cells = receipt.get("cells")
    if not isinstance(cells, list) or len(cells) != 12:
        raise HoldoutAdmissionError("R33 receipt cells are not exact 12-cell coverage")
    indexes_seen: set[int] = set()
    cell_ids: set[str] = set()
    for cell in cells:
        if not isinstance(cell, Mapping) or set(cell) != set(_R33_RECEIPT_CELL_KEYS):
            raise HoldoutAdmissionError("R33 receipt cell schema is invalid")
        _require_sha256(cell.get("cell_ref"), "receipt.cell_ref")
        _require_sha256(cell.get("claim_digest"), "receipt.claim_digest")
        _require_sha256(cell.get("claim_file_sha256"), "receipt.claim_file_sha256")
        _require_sha256(cell.get("ledger_row_sha256"), "receipt.ledger_row_sha256")
        cell_id = _require_text(cell.get("cell_id"), "receipt.cell_id")
        if cell_id in cell_ids:
            raise HoldoutAdmissionError("R33 receipt cell identity is duplicated")
        cell_ids.add(cell_id)
        indexes = cell.get("global_schedule_indexes")
        if (
            not isinstance(indexes, list)
            or any(type(index) is not int or not 0 <= index < 396 for index in indexes)
            or indexes != sorted(indexes)
            or len(indexes) != 33
            or len(set(indexes)) != len(indexes)
        ):
            raise HoldoutAdmissionError("R33 receipt cell schedule indexes are invalid")
        overlap = indexes_seen.intersection(indexes)
        if overlap:
            raise HoldoutAdmissionError("R33 receipt schedule indexes overlap")
        indexes_seen.update(indexes)
    if indexes_seen != set(range(396)):
        raise HoldoutAdmissionError("R33 receipt schedule coverage is incomplete")
    slices = receipt.get("allocation_slices")
    if not isinstance(slices, list) or len(slices) != 3:
        raise HoldoutAdmissionError("R33 receipt allocation slices are invalid")
    expected_slices = []
    for allocation_index in range(3):
        start = allocation_index * 132
        expected_slices.append({
            "allocation_index": allocation_index,
            "global_schedule_start": start,
            "global_schedule_end": start + 131,
        })
    if slices != expected_slices:
        raise HoldoutAdmissionError("R33 receipt allocation slices are not canonical")
    return dict(receipt)


def _r33_manifest_from_receipt(
    receipt: Mapping[str, object], receipt_sha256: str,
) -> dict[str, object]:
    _r33_validate_receipt(receipt)
    return {
        "schema_version": _R33_MANIFEST_SCHEMA,
        "observation_role": receipt["observation_role"],
        "campaign_run_id": receipt["campaign_run_id"],
        "authoritative_receipt_sha256": receipt_sha256,
        "receipt_ref": receipt["receipt_ref"],
        "protocol_sha256": receipt["protocol_sha256"],
        "freeze_sha256": receipt["freeze_sha256"],
        "schedule_sha256": receipt["schedule_sha256"],
        "pilot_rounds": receipt["pilot_rounds"],
        "allocation_count": receipt["allocation_count"],
        "cells": [
            {
                "cell_ref": cell["cell_ref"],
                "global_schedule_indexes": list(cell["global_schedule_indexes"]),
            }
            for cell in receipt["cells"]  # type: ignore[index]
        ],
        "allocation_slices": [dict(item) for item in receipt["allocation_slices"]],
    }


def _r33_validate_manifest(
    manifest: Mapping[str, object], *, receipt: Mapping[str, object], receipt_sha256: str,
) -> None:
    if not isinstance(manifest, Mapping) or set(manifest) != set(_R33_MANIFEST_KEYS):
        raise HoldoutAdmissionError("R33 public admission manifest schema is invalid")
    expected = _r33_manifest_from_receipt(receipt, receipt_sha256)
    if dict(manifest) != expected:
        raise HoldoutAdmissionError("R33 public admission manifest is not the receipt projection")
    cells = manifest.get("cells")
    if not isinstance(cells, list) or any(
        not isinstance(cell, Mapping) or set(cell) != set(_R33_MANIFEST_CELL_KEYS)
        for cell in cells
    ):
        raise HoldoutAdmissionError("R33 public admission manifest cell schema is invalid")
    forbidden = {
        "claim_digest", "claim_file_sha256", "ledger_row_sha256", "ledger_row",
        "claim", "workload", "ycsb", "records", "threads", "run_cmd",
        "binary_path", "absolute_binary_path",
    }
    if any(forbidden.intersection(cell) for cell in cells if isinstance(cell, Mapping)):
        raise HoldoutAdmissionError("R33 public admission manifest contains private fields")


def _r33_validate_commit(
    root: Path, transaction_id: str,
) -> tuple[dict[str, Any], Path, dict[str, Any], list[tuple[str, dict[str, Any], bytes]], list[dict[str, Any]], bytes, dict[str, Any], bytes]:
    transaction_root, receipt, claims, append_rows, append_raw, manifest, manifest_raw = (
        _r33_read_staged_transaction(root, transaction_id)
    )
    commit_path = transaction_root / "commit.json"
    commit = _read_canonical_document(commit_path)
    if set(commit) != set(_R33_TRANSACTION_KEYS):
        raise HoldoutAdmissionError("R33 transaction commit marker schema is invalid")
    if commit.get("schema_version") != _R33_TRANSACTION_SCHEMA:
        raise HoldoutAdmissionError("R33 transaction commit marker version is invalid")
    if commit.get("transaction_id") != transaction_id or commit.get("state") != "committed":
        raise HoldoutAdmissionError("R33 transaction commit marker identity is invalid")
    base_raw = _r33_raw(transaction_root / "staged" / "base-ledger.jsonl")
    if _r33_line_rows(base_raw, "staged base ledger") is None:  # pragma: no cover
        raise HoldoutAdmissionError("unreachable base ledger state")
    if commit.get("base_ledger_sha256") != hashlib.sha256(base_raw).hexdigest():
        raise HoldoutAdmissionError("R33 transaction base ledger digest mismatch")
    if commit.get("base_ledger_line_count") != len(_r33_line_rows(base_raw, "staged base ledger")):
        raise HoldoutAdmissionError("R33 transaction base ledger line count mismatch")
    if commit.get("ledger_append_sha256") != hashlib.sha256(append_raw).hexdigest():
        raise HoldoutAdmissionError("R33 transaction ledger append digest mismatch")
    if commit.get("ledger_append_row_count") != len(append_rows):
        raise HoldoutAdmissionError("R33 transaction ledger append count mismatch")
    receipt_raw = _r33_raw(transaction_root / "staged" / "receipt.json")
    receipt_sha256 = hashlib.sha256(receipt_raw).hexdigest()
    _r33_validate_receipt(receipt, expected_transaction_id=transaction_id)
    if receipt_sha256 != commit.get("receipt_sha256"):
        raise HoldoutAdmissionError("R33 transaction receipt digest mismatch")
    if commit.get("receipt_path") != f"{_R33_RECEIPT_DIR}/{receipt_sha256}.json":
        raise HoldoutAdmissionError("R33 transaction receipt path is not canonical")
    _r33_validate_manifest(manifest, receipt=receipt, receipt_sha256=receipt_sha256)
    if hashlib.sha256(manifest_raw).hexdigest() != hashlib.sha256(
        _canonical_bytes(manifest)
    ).hexdigest():
        raise HoldoutAdmissionError("R33 transaction manifest bytes are not canonical")
    commit_claim_files = commit.get("claim_files")
    if not isinstance(commit_claim_files, list) or len(commit_claim_files) != len(claims):
        raise HoldoutAdmissionError("R33 transaction claim file list is invalid")
    expected_claim_files = [
        {
            "claim_digest": digest,
            "path": f"claims/{digest}.claim",
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
        for digest, _claim, raw in claims
    ]
    if commit_claim_files != expected_claim_files:
        raise HoldoutAdmissionError("R33 transaction claim file binding is invalid")
    claim_by_digest = {digest: claim for digest, claim, _raw in claims}
    row_by_digest: dict[str, dict[str, Any]] = {}
    for row in append_rows:
        digest = _r33_ledger_key_digest(row)
        if digest in row_by_digest or digest not in claim_by_digest:
            raise HoldoutAdmissionError("R33 transaction ledger identity is invalid")
        row_by_digest[digest] = row
    if set(row_by_digest) != set(claim_by_digest):
        raise HoldoutAdmissionError("R33 transaction claim/ledger coverage is incomplete")
    for digest, claim, raw in claims:
        row = row_by_digest[digest]
        if (
            claim.get("campaign_run_id") != receipt["campaign_run_id"]
            or row.get("campaign_run_id") != receipt["campaign_run_id"]
            or claim.get("protocol_sha256") != receipt["protocol_sha256"]
            or claim.get("freeze_sha256") != receipt["freeze_sha256"]
            or claim.get("schedule_sha256") != receipt["schedule_sha256"]
            or row.get("protocol_sha256") != receipt["protocol_sha256"]
            or row.get("freeze_sha256") != receipt["freeze_sha256"]
            or row.get("schedule_sha256") != receipt["schedule_sha256"]
        ):
            raise HoldoutAdmissionError("R33 transaction campaign identity is invalid")
        # The role is part of the effect key; an explicit duplicate role field
        # in a claim is forbidden so it cannot drift independently.
        if claim.get("observation_role") is not None:
            raise HoldoutAdmissionError("R33 claim has a duplicate role field")
        if row.get("observation_role") != OBSERVATION_ROLE_N_PILOT_R33:
            raise HoldoutAdmissionError("R33 transaction ledger role is invalid")
        try:
            receipt_cell = next(
                cell for cell in receipt["cells"]
                if cell["claim_digest"] == digest  # type: ignore[index]
            )
        except StopIteration as exc:
            raise HoldoutAdmissionError(
                "R33 receipt claim coverage is incomplete"
            ) from exc
        if receipt_cell["claim_file_sha256"] != hashlib.sha256(raw).hexdigest():
            raise HoldoutAdmissionError("R33 receipt claim file hash mismatch")
        row_raw = _canonical_line(row)
        if receipt_cell["ledger_row_sha256"] != hashlib.sha256(row_raw).hexdigest():
            raise HoldoutAdmissionError("R33 receipt ledger row hash mismatch")
    return (
        commit, transaction_root, receipt, claims, append_rows, append_raw,
        manifest, manifest_raw,
    )


def _r33_transaction_visible_publish(
    root: Path, transaction_id: str, *, receipt_sha256: str | None,
    claim_digests: Sequence[str],
) -> bool:
    if receipt_sha256 is not None and (
        root / _R33_RECEIPT_DIR / f"{receipt_sha256}.json"
    ).exists():
        return True
    if any((root / "claims" / f"{digest}.claim").exists() for digest in claim_digests):
        return True
    receipts_root = root / _R33_RECEIPT_DIR
    if receipts_root.is_dir() and not receipts_root.is_symlink():
        for path in sorted(receipts_root.iterdir(), key=lambda item: item.name):
            if not path.is_file() or path.is_symlink():
                raise HoldoutAdmissionError("R33 receipt directory contains an unsafe entry")
            raw = _r33_raw(path)
            document = _read_canonical_json_bytes(path)
            _r33_validate_receipt(document)
            digest = hashlib.sha256(raw).hexdigest()
            if path.name != f"{digest}.json":
                raise HoldoutAdmissionError("R33 receipt filename is not canonical")
            if document.get("transaction_id") == transaction_id:
                return True
    ledger_path = root / _LEDGER_NAME
    if ledger_path.exists():
        for row in _read_ledger(ledger_path):
            if row.get("observation_role") != OBSERVATION_ROLE_N_PILOT_R33:
                continue
            try:
                if _r33_ledger_key_digest(row) in claim_digests:
                    return True
            except HoldoutAdmissionError:
                raise
    return False


def _inspect_n_pilot_transaction_locked(
    root: Path,
    transaction_id: str,
) -> TransactionInspection:
    """Inspect one R33 transaction while the shared admission lock is held."""

    transaction_root = _r33_transaction_root(root, transaction_id)
    if not transaction_root.is_dir() or transaction_root.is_symlink():
        raise HoldoutAdmissionError("R33 transaction is unavailable")
    abort_path = transaction_root / "abort.json"
    commit_path = transaction_root / "commit.json"
    if abort_path.exists():
        abort = _read_canonical_document(abort_path)
        if set(abort) != {
            "schema_version", "transaction_id", "reason", "approved_by",
            "approval_ref", "staged_bytes_sha256", "base_ledger_sha256",
            "visible_publish",
        } or abort.get("schema_version") != _R33_ABORT_SCHEMA:
            raise HoldoutAdmissionError("R33 abort marker schema is invalid")
        if (
            abort.get("transaction_id") != transaction_id
            or abort.get("reason") != "crash-before-commit-marker"
            or abort.get("visible_publish") is not False
        ):
            raise HoldoutAdmissionError("R33 abort marker identity is invalid")
        _require_text(abort.get("approved_by"), "abort.approved_by")
        _require_text(abort.get("approval_ref"), "abort.approval_ref")
        _require_sha256(abort.get("staged_bytes_sha256"), "abort.staged_bytes_sha256")
        _require_sha256(abort.get("base_ledger_sha256"), "abort.base_ledger_sha256")
        return TransactionInspection({
            "transaction_id": transaction_id,
            "state": "aborted",
            "visible_publish": False,
            "manual_reconcile_required": False,
            "staged_bytes_sha256": abort["staged_bytes_sha256"],
            "base_ledger_sha256": abort["base_ledger_sha256"],
            "claim_count": 0,
            "ledger_row_count": 0,
        })

    if commit_path.exists():
        commit, staged_root, receipt, claims, rows, _append_raw, _manifest, _manifest_raw = (
            _r33_validate_commit(root, transaction_id)
        )
        claim_digests = [digest for digest, _claim, _raw in claims]
        receipt_sha256 = hashlib.sha256(
            _r33_raw(staged_root / "staged" / "receipt.json")
        ).hexdigest()
        visible = _r33_transaction_visible_publish(
            root, transaction_id, receipt_sha256=receipt_sha256,
            claim_digests=claim_digests,
        )
        return TransactionInspection({
            "transaction_id": transaction_id,
            "state": "committed",
            "visible_publish": visible,
            "manual_reconcile_required": False,
            "staged_bytes_sha256": _r33_staged_bytes_sha256(staged_root),
            "base_ledger_sha256": commit["base_ledger_sha256"],
            "receipt_sha256": receipt_sha256,
            "claim_count": len(claims),
            "ledger_row_count": len(rows),
        })

    staged = transaction_root / "staged"
    if not staged.is_dir() or staged.is_symlink():
        raise HoldoutAdmissionError("R33 transaction staging directory is unavailable")
    claim_digests: list[str] = []
    claims_root = staged / "claims"
    if claims_root.is_dir() and not claims_root.is_symlink():
        for path in sorted(claims_root.iterdir(), key=lambda item: item.name):
            if path.is_file() and path.suffix == ".claim":
                claim = _read_canonical_document(path)
                digest = _r33_claim_key_digest(claim)
                if path.stem != digest:
                    raise HoldoutAdmissionError("R33 staged claim filename is invalid")
                claim_digests.append(digest)
    receipt_sha256 = None
    receipt_path = staged / "receipt.json"
    if receipt_path.exists():
        receipt_raw = _r33_raw(receipt_path)
        receipt = _read_canonical_json_bytes(receipt_path)
        _r33_validate_receipt(receipt, expected_transaction_id=transaction_id)
        receipt_sha256 = hashlib.sha256(receipt_raw).hexdigest()
    visible = _r33_transaction_visible_publish(
        root, transaction_id, receipt_sha256=receipt_sha256,
        claim_digests=claim_digests,
    )
    if visible:
        return TransactionInspection({
            "transaction_id": transaction_id,
            "state": "manual-reconcile-required",
            "visible_publish": True,
            "manual_reconcile_required": True,
            "staged_bytes_sha256": _r33_staged_bytes_sha256(transaction_root),
            "claim_count": len(claim_digests),
        })
    base_path = staged / "base-ledger.jsonl"
    base_raw = _r33_raw(base_path, missing=b"")
    _r33_line_rows(base_raw, "staged base ledger")
    return TransactionInspection({
        "transaction_id": transaction_id,
        "state": "staged",
        "visible_publish": False,
        "manual_reconcile_required": False,
        "staged_bytes_sha256": _r33_staged_bytes_sha256(transaction_root),
        "base_ledger_sha256": hashlib.sha256(base_raw).hexdigest(),
        "claim_count": len(claim_digests),
    })


def _r33_existing_ledger_rows(root: Path) -> tuple[bytes, list[dict[str, Any]]]:
    ledger_path = root / _LEDGER_NAME
    raw = _r33_raw(ledger_path, missing=b"")
    return raw, _read_ledger(ledger_path) if raw else []


def _r33_publish_exact(path: Path, payload: bytes, *, logical_name: str, guarded: bool) -> None:
    try:
        if guarded:
            write_guarded_create_bytes(path, payload, logical_name=logical_name)
        else:
            _r33_create_raw(path, payload)
    except FileExistsError:
        existing = _r33_raw(path)
        if existing != payload:
            raise HoldoutAdmissionError(
                f"R33 published file differs from staged bytes: {path.name}"
            )


def _r33_apply_committed_transaction_locked(root: Path, transaction_id: str) -> None:
    (
        commit, transaction_root, receipt, claims, append_rows, append_raw,
        manifest, manifest_raw,
    ) = _r33_validate_commit(root, transaction_id)
    base_raw = _r33_raw(transaction_root / "staged" / "base-ledger.jsonl")
    current_raw, current_rows = _r33_existing_ledger_rows(root)
    if not current_raw.startswith(base_raw):
        raise HoldoutAdmissionError(
            "R33 transaction base ledger prefix changed; manual reconcile required"
        )
    current_by_digest: dict[str, dict[str, Any]] = {}
    for row in current_rows:
        if row.get("observation_role") != OBSERVATION_ROLE_N_PILOT_R33:
            continue
        digest = _r33_ledger_key_digest(row)
        if digest in current_by_digest and current_by_digest[digest] != row:
            raise HoldoutAdmissionError("R33 ledger identity has conflicting rows")
        current_by_digest[digest] = row
    base_rows = _r33_line_rows(base_raw, "staged base ledger")
    base_r33_digests = {
        _r33_ledger_key_digest(row)
        for row in base_rows
        if row.get("observation_role") == OBSERVATION_ROLE_N_PILOT_R33
    }
    append_by_digest: dict[str, dict[str, Any]] = {}
    for row in append_rows:
        digest = _r33_ledger_key_digest(row)
        if digest in append_by_digest and append_by_digest[digest] != row:
            raise HoldoutAdmissionError("R33 staged ledger identity is duplicated")
        append_by_digest[digest] = row
        prior = current_by_digest.get(digest)
        if prior is not None and prior != row:
            raise HoldoutAdmissionError("R33 ledger row conflicts with staged row")
    unexpected_r33 = set(current_by_digest) - base_r33_digests - set(append_by_digest)
    if unexpected_r33:
        raise HoldoutAdmissionError(
            "R33 ledger contains an unknown partial publication; manual reconcile required"
        )
    missing_rows = [row for digest, row in append_by_digest.items() if digest not in current_by_digest]
    if missing_rows:
        # Only the missing suffix is appended.  Other roles may have appended
        # after the captured prefix while this transaction was staged.
        _append_ledger(root / _LEDGER_NAME, missing_rows)

    for digest, _claim, raw in claims:
        _r33_publish_exact(
            root / "claims" / f"{digest}.claim", raw,
            logical_name=f"{digest}.claim", guarded=False,
        )
    receipt_raw = _r33_raw(transaction_root / "staged" / "receipt.json")
    receipt_sha256 = hashlib.sha256(receipt_raw).hexdigest()
    _r33_publish_exact(
        root / _R33_RECEIPT_DIR / f"{receipt_sha256}.json", receipt_raw,
        logical_name=f"{receipt_sha256}.json", guarded=True,
    )
    _r33_publish_exact(
        root / _R33_MANIFEST_DIR / f"{receipt_sha256}.json", manifest_raw,
        logical_name=f"{receipt_sha256}.json", guarded=True,
    )
    # A marker must be self-consistent even if recovery is invoked after all
    # final files already exist.
    if commit["ledger_append_sha256"] != hashlib.sha256(append_raw).hexdigest():
        raise HoldoutAdmissionError("R33 transaction append bytes changed")


def _recover_n_pilot_transactions_locked(root: Path) -> None:
    """Recover every committed R33 transaction without replacing shared ledger bytes."""

    transaction_root = root / _R33_TRANSACTION_DIR
    if not transaction_root.exists():
        return
    try:
        paths = sorted(transaction_root.iterdir(), key=lambda path: path.name)
    except OSError as exc:
        raise HoldoutAdmissionError("R33 transaction directory is unavailable") from exc
    for path in paths:
        if not path.is_dir() or path.is_symlink():
            raise HoldoutAdmissionError("R33 transaction directory contains an unsafe entry")
        transaction_id = path.name
        _require_sha256(transaction_id, "transaction_id")
        if (path / "abort.json").exists():
            _inspect_n_pilot_transaction_locked(root, transaction_id)
            continue
        if (path / "commit.json").exists():
            _r33_apply_committed_transaction_locked(root, transaction_id)
            continue
        inspection = _inspect_n_pilot_transaction_locked(root, transaction_id)
        if inspection.manual_reconcile_required:
            raise HoldoutAdmissionError("R33 transaction manual reconcile required")


def _r33_copy_tree_create(source: Path, destination: Path) -> None:
    if source.is_symlink() or not source.is_dir():
        raise HoldoutAdmissionError("R33 quarantine source is unsafe")
    _ensure_private_directory(destination)
    for path in sorted(source.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(source)
        target = destination / relative
        if path.is_symlink():
            raise HoldoutAdmissionError("R33 quarantine refuses symlink staging")
        if path.is_dir():
            _ensure_private_directory(target)
            continue
        if not path.is_file():
            raise HoldoutAdmissionError("R33 quarantine source contains an unsafe entry")
        _r33_publish_exact(
            target, _r33_raw(path), logical_name=target.name, guarded=False,
        )


def abort_unpublished_n_pilot_transaction(
    *,
    repo_root: Path,
    transaction_id: str,
    approval: Mapping[str, object],
) -> Path:
    """Quarantine a pre-commit R33 transaction after explicit operator approval."""

    root = provision_shared_admission_root(Path(repo_root))
    transaction_id = _require_sha256(transaction_id, "transaction_id")
    if not isinstance(approval, Mapping):
        raise HoldoutAdmissionError("R33 abort approval is unavailable")
    approved_by = _require_text(approval.get("approved_by"), "approved_by")
    approval_ref = _require_text(approval.get("approval_ref"), "approval_ref")
    path = _r33_transaction_root(root, transaction_id)
    abort_path = path / "abort.json"
    with _locked(root):
        if not path.is_dir() or path.is_symlink():
            raise HoldoutAdmissionError("R33 transaction is unavailable")
        if abort_path.exists():
            existing = _read_canonical_document(abort_path)
            if (
                existing.get("approved_by") != approved_by
                or existing.get("approval_ref") != approval_ref
            ):
                raise HoldoutAdmissionError("R33 abort approval does not match existing marker")
            return abort_path
        if (path / "commit.json").exists():
            raise HoldoutAdmissionError("manual reconcile required: R33 commit marker exists")
        staged = path / "staged"
        if not staged.is_dir() or staged.is_symlink():
            raise HoldoutAdmissionError("R33 transaction staging is unavailable")
        staged_bytes_sha256 = _r33_staged_bytes_sha256(path)
        base_raw = _r33_raw(staged / "base-ledger.jsonl", missing=b"")
        _r33_line_rows(base_raw, "staged base ledger")
        claim_digests: list[str] = []
        claims_root = staged / "claims"
        if claims_root.is_dir() and not claims_root.is_symlink():
            for claim_path in sorted(claims_root.iterdir(), key=lambda item: item.name):
                if not claim_path.is_file() or claim_path.suffix != ".claim":
                    raise HoldoutAdmissionError("R33 staged claim entry is unsafe")
                claim = _read_canonical_document(claim_path)
                digest = _r33_claim_key_digest(claim)
                if claim_path.stem != digest:
                    raise HoldoutAdmissionError("R33 staged claim filename is invalid")
                claim_digests.append(digest)
        receipt_sha256 = None
        receipt_path = staged / "receipt.json"
        if receipt_path.exists():
            receipt_raw = _r33_raw(receipt_path)
            receipt = _read_canonical_json_bytes(receipt_path)
            _r33_validate_receipt(receipt, expected_transaction_id=transaction_id)
            receipt_sha256 = hashlib.sha256(receipt_raw).hexdigest()
        visible = _r33_transaction_visible_publish(
            root, transaction_id, receipt_sha256=receipt_sha256,
            claim_digests=claim_digests,
        )
        if visible:
            raise HoldoutAdmissionError(
                "manual reconcile required: R33 transaction has visible publication"
            )
        quarantine = root / _R33_QUARANTINE_DIR / transaction_id
        _r33_copy_tree_create(path, quarantine)
        document = {
            "schema_version": _R33_ABORT_SCHEMA,
            "transaction_id": transaction_id,
            "reason": "crash-before-commit-marker",
            "approved_by": approved_by,
            "approval_ref": approval_ref,
            "staged_bytes_sha256": staged_bytes_sha256,
            "base_ledger_sha256": hashlib.sha256(base_raw).hexdigest(),
            "visible_publish": False,
        }
        _write_exclusive(abort_path, document)
    return abort_path


def _r33_build_receipt(
    *, transaction_id: str, campaign_run_id: str, protocol_sha256: str,
    freeze_sha256: str, freeze_canonical_sha256: str, schedule_sha256: str,
    claims: Sequence[Mapping[str, object]], ledger_rows: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object], str, dict[str, object]]:
    row_by_digest = {
        _r33_ledger_key_digest(row): row for row in ledger_rows
    }
    claim_by_digest = {
        _r33_claim_key_digest(claim): claim for claim in claims
    }
    if set(row_by_digest) != set(claim_by_digest) or len(claims) != 12:
        raise HoldoutAdmissionError("R33 receipt claim/ledger coverage is incomplete")
    receipt_cells: list[dict[str, object]] = []
    for digest in sorted(claim_by_digest):
        claim = claim_by_digest[digest]
        row = row_by_digest[digest]
        claim_raw = _canonical_line(claim)
        row_raw = _canonical_line(row)
        indexes = claim.get("schedule_indexes")
        if not isinstance(indexes, list) or len(indexes) != 33:
            raise HoldoutAdmissionError("R33 claim attempt coverage is invalid")
        receipt_cells.append({
            "cell_ref": secrets.token_hex(32),
            "cell_id": claim["cell_id"],
            "global_schedule_indexes": list(indexes),
            "claim_digest": digest,
            "claim_file_sha256": hashlib.sha256(claim_raw).hexdigest(),
            "ledger_row_sha256": hashlib.sha256(row_raw).hexdigest(),
        })
    receipt_ref = secrets.token_hex(32)
    receipt: dict[str, object] = {
        "schema_version": _R33_RECEIPT_SCHEMA,
        "observation_role": OBSERVATION_ROLE_N_PILOT_R33,
        "campaign_run_id": campaign_run_id,
        "protocol_sha256": protocol_sha256,
        "freeze_sha256": freeze_sha256,
        "freeze_canonical_sha256": freeze_canonical_sha256,
        "schedule_sha256": schedule_sha256,
        "pilot_rounds": 33,
        "allocation_count": 3,
        "schedule_row_count": 396,
        "cell_count": 12,
        "attempt_count": 396,
        "transaction_id": transaction_id,
        "receipt_ref": receipt_ref,
        "cells": receipt_cells,
        "allocation_slices": [
            {
                "allocation_index": allocation_index,
                "global_schedule_start": allocation_index * 132,
                "global_schedule_end": allocation_index * 132 + 131,
            }
            for allocation_index in range(3)
        ],
    }
    _r33_validate_receipt(receipt, expected_transaction_id=transaction_id)
    receipt_raw = _canonical_bytes(receipt)
    receipt_sha256 = hashlib.sha256(receipt_raw).hexdigest()
    manifest = _r33_manifest_from_receipt(receipt, receipt_sha256)
    return receipt, receipt_sha256, manifest


def _r33_stage_and_commit(
    *, root: Path, campaign_run_id: str, protocol_sha256: str,
    freeze_sha256: str, freeze_canonical_sha256: str, schedule_sha256: str,
    claims: Sequence[Mapping[str, object]], ledger_rows: Sequence[Mapping[str, object]],
) -> NPilotReservationReceipt:
    transaction_id = secrets.token_hex(32)
    transaction_root = root / _R33_TRANSACTION_DIR / transaction_id
    staged = transaction_root / "staged"
    _ensure_private_directory(transaction_root)
    _ensure_private_directory(staged)
    _ensure_private_directory(staged / "claims")
    current_raw, current_rows = _r33_existing_ledger_rows(root)
    current_r33: dict[str, dict[str, Any]] = {}
    for row in current_rows:
        if row.get("observation_role") != OBSERVATION_ROLE_N_PILOT_R33:
            continue
        digest = _r33_ledger_key_digest(row)
        if digest in current_r33:
            raise HoldoutAdmissionError("R33 admission ledger has a duplicate cell key")
        current_r33[digest] = row
    claim_digests = [_r33_claim_key_digest(claim) for claim in claims]
    if len(set(claim_digests)) != len(claim_digests):
        raise HoldoutAdmissionError("R33 claim key is duplicated")
    if set(current_r33).intersection(claim_digests):
        raise HoldoutAdmissionError("n pilot R33 holdout cell key was already consumed")
    for digest in claim_digests:
        if (root / "claims" / f"{digest}.claim").exists():
            raise HoldoutAdmissionError("n pilot R33 durable claim was already published")

    _r33_create_raw(staged / "base-ledger.jsonl", current_raw)
    append_raw = b"".join(_canonical_line(dict(row)) for row in ledger_rows)
    _r33_create_raw(staged / "ledger-append.jsonl", append_raw)
    for claim in claims:
        digest = _r33_claim_key_digest(claim)
        _r33_create_raw(
            staged / "claims" / f"{digest}.claim", _canonical_line(dict(claim))
        )
    receipt, receipt_sha256, manifest = _r33_build_receipt(
        transaction_id=transaction_id, campaign_run_id=campaign_run_id,
        protocol_sha256=protocol_sha256, freeze_sha256=freeze_sha256,
        freeze_canonical_sha256=freeze_canonical_sha256,
        schedule_sha256=schedule_sha256,
        claims=claims, ledger_rows=ledger_rows,
    )
    receipt_raw = _canonical_bytes(receipt)
    manifest_raw = _canonical_bytes(manifest)
    # These are intentionally the only transaction bytes that pass the public
    # holdout-safe writer before the commit marker exists.
    write_guarded_create_bytes(
        staged / "receipt.json", receipt_raw, logical_name="receipt.json",
    )
    write_guarded_create_bytes(
        staged / "manifest.json", manifest_raw, logical_name="manifest.json",
    )
    commit = {
        "schema_version": _R33_TRANSACTION_SCHEMA,
        "transaction_id": transaction_id,
        "state": "committed",
        "base_ledger_sha256": hashlib.sha256(current_raw).hexdigest(),
        "base_ledger_line_count": len(current_rows),
        "ledger_append_sha256": hashlib.sha256(append_raw).hexdigest(),
        "ledger_append_row_count": len(ledger_rows),
        "claim_files": [
            {
                "claim_digest": digest,
                "path": f"claims/{digest}.claim",
                "sha256": hashlib.sha256(_canonical_line(dict(claim))).hexdigest(),
            }
            for digest, claim in sorted(
                zip(claim_digests, claims, strict=True), key=lambda item: item[0]
            )
        ],
        "receipt_path": f"{_R33_RECEIPT_DIR}/{receipt_sha256}.json",
        "receipt_sha256": receipt_sha256,
    }
    _write_exclusive(transaction_root / "commit.json", commit)
    _r33_apply_committed_transaction_locked(root, transaction_id)
    return NPilotReservationReceipt(
        receipt, receipt_sha256=receipt_sha256, root=root,
    )


def _reserve_n_pilot_r33_holdout_observations(
    *, repo_root: Path, protocol: Mapping[str, object], protocol_sha256: str,
    verified_freeze_document: Mapping[str, object], freeze_sha256: str,
    cells: Sequence[Mapping[str, object]], schedule: Sequence[Mapping[str, object]],
    campaign_run_id: str, irreversible_pilot_approved: bool,
) -> NPilotReservationReceipt:
    if irreversible_pilot_approved is not True:
        raise HoldoutAdmissionError(
            "n pilot holdout observation requires irreversible one-shot approval"
        )
    campaign_run_id = _require_text(campaign_run_id, "campaign_run_id")
    (
        protocol_document, protocol_sha256, freeze_document, freeze_sha256,
        freeze_canonical_sha256, ccbench_pin, env_tag, pilot_reps,
    ) = _r33_protocol_and_freeze(
        protocol=protocol, protocol_sha256=protocol_sha256,
        verified_freeze_document=verified_freeze_document, freeze_sha256=freeze_sha256,
    )
    try:
        signatures = _protected_signatures_from_verified_freeze_core(freeze_document)
    except HoldoutObservationError as exc:
        raise HoldoutAdmissionError(
            f"cannot derive n pilot R33 protected signatures: {exc}"
        ) from exc
    cells_by_id, normalized_schedule, schedule_sha256 = _r33_cells_and_schedule(
        freeze_document=freeze_document, cells=cells, schedule=schedule,
        signatures=signatures,
    )
    claims, ledger_rows = _r33_claim_and_ledger_documents(
        cells_by_id=cells_by_id, signatures=signatures,
        protocol_sha256=protocol_sha256, freeze_sha256=freeze_sha256,
        schedule_sha256=schedule_sha256, ccbench_pin=ccbench_pin, env_tag=env_tag,
        campaign_run_id=campaign_run_id, pilot_reps=pilot_reps,
    )
    root = provision_shared_admission_root(Path(repo_root))
    with _locked(root):
        _recover_n_pilot_transactions_locked(root)
        _recover_n_pilot_attempt_ledger_locked(root)
        return _r33_stage_and_commit(
            root=root, campaign_run_id=campaign_run_id,
            protocol_sha256=protocol_sha256, freeze_sha256=freeze_sha256,
            freeze_canonical_sha256=freeze_canonical_sha256,
            schedule_sha256=schedule_sha256, claims=claims, ledger_rows=ledger_rows,
        )


def reserve_n_pilot_holdout_observations(
    *, repo_root: Path, protocol: Mapping[str, object], protocol_sha256: str,
    verified_freeze_document: Mapping[str, object], freeze_sha256: str,
    cells: Sequence[Mapping[str, object]], schedule: Sequence[Mapping[str, object]],
    campaign_run_id: str, irreversible_pilot_approved: bool,
) -> NPilotReservationReceipt | dict[int, NPilotCellHoldoutAdmission]:
    """Reserve legacy n-pilot cells or a receipt-backed R33 admission.

    The legacy branch is intentionally retained for the already-issued
    ``observation_role=n_pilot`` generation.  A protocol carrying the fixed
    R33 contract always takes the receipt/transaction branch and never creates
    an ``NPilotCellHoldoutAdmission`` or process-local cell state.
    """

    if _is_r33_reservation_request(protocol, cells, schedule):
        return _reserve_n_pilot_r33_holdout_observations(
            repo_root=repo_root, protocol=protocol, protocol_sha256=protocol_sha256,
            verified_freeze_document=verified_freeze_document,
            freeze_sha256=freeze_sha256, cells=cells, schedule=schedule,
            campaign_run_id=campaign_run_id,
            irreversible_pilot_approved=irreversible_pilot_approved,
        )

    if irreversible_pilot_approved is not True:
        raise HoldoutAdmissionError(
            "n pilot holdout observation requires irreversible one-shot approval"
        )
    campaign_run_id = _require_text(campaign_run_id, "campaign_run_id")
    protocol_sha256 = _require_sha256(protocol_sha256, "protocol_sha256")
    protocol_document = _mutable_json_tree(protocol)
    if not isinstance(protocol_document, dict):
        raise HoldoutAdmissionError("n pilot protocol document is invalid")
    if hashlib.sha256(_canonical_line(protocol_document)).hexdigest() != protocol_sha256:
        raise HoldoutAdmissionError(
            "n pilot protocol digest does not match its canonical document"
        )
    freeze_sha256 = _require_sha256(freeze_sha256, "freeze_sha256")
    freeze_ref = protocol_document.get("freeze")
    if not isinstance(freeze_ref, Mapping) or freeze_ref.get("sha256") != freeze_sha256:
        raise HoldoutAdmissionError("n pilot protocol is not bound to the freeze hash")
    environment = protocol_document.get("environment")
    design = protocol_document.get("design")
    if not isinstance(environment, Mapping) or not isinstance(design, Mapping):
        raise HoldoutAdmissionError("n pilot protocol authority fields are unavailable")
    ccbench_pin = _require_text(environment.get("ccbench_pin"), "ccbench_pin")
    env_tag = _require_text(environment.get("env_tag"), "env_tag")
    pilot_reps = design.get("reps")
    if type(pilot_reps) is not int or pilot_reps <= 0:
        raise HoldoutAdmissionError("n pilot protocol reps is invalid")

    fixed_freeze = _mutable_json_tree(verified_freeze_document)
    if not isinstance(fixed_freeze, dict):
        raise HoldoutAdmissionError("n pilot verified freeze document is invalid")
    try:
        signatures = _protected_signatures_from_verified_freeze_core(fixed_freeze)
    except HoldoutObservationError as exc:
        raise HoldoutAdmissionError(
            f"cannot derive n pilot protected signatures: {exc}"
        ) from exc
    signature_by_key = {item.freeze_holdout_key: item for item in signatures}
    neutral_holdouts = {
        item.freeze_holdout_key: {
            "candidate_id": item.freeze_candidate_id,
            "ycsb": {"ycsb_rratio": item.ycsb_rratio},
        }
        for item in signatures
    }
    holdouts = fixed_freeze.get("holdouts")
    if not isinstance(holdouts, Mapping):
        raise HoldoutAdmissionError("n pilot freeze holdouts are unavailable")

    normalized_cells = [dict(cell) for cell in cells]
    cell_keys = {
        "cell_id", "holdout_id", "configuration_id",
        "records", "threads", "workload",
    }
    if len(normalized_cells) != 12 or any(
        set(cell) != cell_keys for cell in normalized_cells
    ):
        raise HoldoutAdmissionError("n pilot cell set is not exact 12-cell schema")
    cells_by_id: dict[str, dict[str, Any]] = {}
    for cell in normalized_cells:
        freeze_holdout_key = _require_text(cell.get("holdout_id"), "holdout_id")
        configuration_id = _require_text(
            cell.get("configuration_id"), "configuration_id"
        )
        cell_id = _require_text(cell.get("cell_id"), "cell_id")
        if cell_id != f"{freeze_holdout_key}::{configuration_id}":
            raise HoldoutAdmissionError(
                "n pilot cell_id does not bind holdout and configuration"
            )
        if cell_id in cells_by_id:
            raise HoldoutAdmissionError("n pilot cell_id is duplicated")
        signature = signature_by_key.get(freeze_holdout_key)
        freeze_entry = holdouts.get(freeze_holdout_key)
        if signature is None or not isinstance(freeze_entry, Mapping):
            raise HoldoutAdmissionError("n pilot cell freeze key is not protected")
        variant_binding = freeze_entry.get("variant_binding")
        entries = (
            variant_binding.get("entries")
            if isinstance(variant_binding, Mapping) else None
        )
        if not isinstance(entries, Mapping) or configuration_id not in entries:
            raise HoldoutAdmissionError("n pilot configuration is not freeze-bound")
        workload = freeze_entry.get("ycsb")
        if not isinstance(workload, Mapping) or (
            cell.get("records") != freeze_entry.get("records")
            or cell.get("threads") != freeze_entry.get("threads")
            or cell.get("workload") != dict(workload)
        ):
            raise HoldoutAdmissionError("n pilot cell differs from freeze projection")
        cells_by_id[cell_id] = cell

    normalized_schedule = [dict(row) for row in schedule]
    schedule_indexes_by_cell: dict[str, list[int]] = {
        cell_id: [] for cell_id in cells_by_id
    }
    cells_by_round: dict[int, set[str]] = {}
    for expected_seq, row in enumerate(normalized_schedule):
        if set(row) != {"seq", "pilot_round", "cell_id"}:
            raise HoldoutAdmissionError("n pilot schedule row schema is invalid")
        if row.get("seq") != expected_seq:
            raise HoldoutAdmissionError("n pilot schedule seq is not contiguous")
        pilot_round = row.get("pilot_round")
        if type(pilot_round) is not int or pilot_round <= 0:
            raise HoldoutAdmissionError("n pilot schedule round is invalid")
        cell_id = _require_text(row.get("cell_id"), "cell_id")
        if cell_id not in cells_by_id:
            raise HoldoutAdmissionError("n pilot schedule contains an unknown cell")
        if cell_id in cells_by_round.setdefault(pilot_round, set()):
            raise HoldoutAdmissionError("n pilot schedule repeats a cell within a round")
        cells_by_round[pilot_round].add(cell_id)
        schedule_indexes_by_cell[cell_id].append(expected_seq)
    rounds = sorted(cells_by_round)
    if (
        not rounds
        or rounds != list(range(1, len(rounds) + 1))
        or any(cell_set != set(cells_by_id) for cell_set in cells_by_round.values())
        or len(normalized_schedule) != len(cells_by_id) * len(rounds)
    ):
        raise HoldoutAdmissionError("n pilot schedule is not complete blocks")
    schedule_sha256 = hashlib.sha256(
        _canonical_line(normalized_schedule)
    ).hexdigest()

    claims: list[dict[str, Any]] = []
    ledger_rows: list[dict[str, Any]] = []
    for cell_id, cell in cells_by_id.items():
        freeze_holdout_key = str(cell["holdout_id"])
        configuration_id = str(cell["configuration_id"])
        signature = signature_by_key[freeze_holdout_key]
        schedule_indexes = schedule_indexes_by_cell[cell_id]
        attempt_ids = [
            f"{campaign_run_id}::{cell_id}::schedule{schedule_index}"
            for schedule_index in schedule_indexes
        ]
        key = _key_fields(
            freeze_sha256=freeze_sha256,
            freeze_holdout_key=freeze_holdout_key,
            configuration_id=configuration_id,
            ccbench_pin=ccbench_pin,
            env_tag=env_tag,
            observation_role=OBSERVATION_ROLE_N_PILOT,
        )
        claim = {
            "schema_version": _CLAIM_SCHEMA_V1,
            "event": "claim",
            "key": key,
            "protocol_sha256": protocol_sha256,
            "schedule_sha256": schedule_sha256,
            "freeze_candidate_id": signature.freeze_candidate_id,
            "trial_workload_name": signature.trial_workload_name,
            "cell_id": cell_id,
            "records": cell["records"],
            "threads": cell["threads"],
            "workload": dict(cell["workload"]),
            "campaign_run_id": campaign_run_id,
            "irreversible_pilot_approved": True,
            "schedule_indexes": schedule_indexes,
            "attempt_ids": attempt_ids,
        }
        claims.append(claim)
        ledger_rows.append({
            "schema_version": _LEDGER_SCHEMA,
            "event": "admit",
            **key,
            "protocol_sha256": protocol_sha256,
            "schedule_sha256": schedule_sha256,
            "freeze_candidate_id": signature.freeze_candidate_id,
            "trial_workload_name": signature.trial_workload_name,
            "cell_id": cell_id,
            "records": cell["records"],
            "threads": cell["threads"],
            "workload": dict(cell["workload"]),
            "campaign_run_id": campaign_run_id,
            "irreversible_pilot_approved": True,
            "reps": pilot_reps,
            "schedule_indexes": schedule_indexes,
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
                    "n pilot holdout cell key was already consumed"
                ) from exc
            if digest in indexed:
                raise HoldoutAdmissionError(
                    "n pilot ledger evidence existed without its durable claim"
                )
        _append_ledger(root / _LEDGER_NAME, ledger_rows)

    admissions_by_schedule_index: dict[int, NPilotCellHoldoutAdmission] = {}
    for claim, row in zip(claims, ledger_rows, strict=True):
        token = NPilotCellHoldoutAdmission(
            freeze_holdout_key=row["freeze_holdout_key"],
            freeze_candidate_id=row["freeze_candidate_id"],
            trial_workload_name=row["trial_workload_name"],
            configuration_id=row["configuration_id"],
            cell_id=row["cell_id"],
        )
        state = _NPilotCellState(
            token=token,
            root=root,
            row=row,
            claim_digest=_claim_digest(claim["key"]),
            attempt_ids_by_schedule_index=dict(zip(
                row["schedule_indexes"], row["attempt_ids"], strict=True,
            )),
            verified_freeze=fixed_freeze,
            neutral_holdouts=neutral_holdouts,
            pilot_reps=pilot_reps,
        )
        with _state_lock:
            _n_pilot_cell_states[id(token)] = state
        for schedule_index in row["schedule_indexes"]:
            admissions_by_schedule_index[schedule_index] = token
    if set(admissions_by_schedule_index) != set(range(len(normalized_schedule))):
        raise HoldoutAdmissionError("n pilot schedule admission coverage is incomplete")
    return admissions_by_schedule_index


_R33_ATTEMPT_MARKER_KEYS = frozenset({
    "schema_version", "event", "claim_digest", "attempt_id",
    "protocol_sha256", "freeze_sha256", "schedule_sha256",
    "campaign_run_id", "schedule_index", "cell_id", "freeze_holdout_key",
    "configuration_id", "observation_role",
})


def _r33_canonical_marker_path(root: Path, marker: Mapping[str, object]) -> Path:
    marker_raw = _canonical_line(dict(marker))
    marker_digest = hashlib.sha256(marker_raw).hexdigest()
    claim_digest = _require_sha256(marker.get("claim_digest"), "claim_digest")
    return root / "consumed" / f"{claim_digest}-{marker_digest}.json"


def _canonical_n_pilot_attempt_ledger_row(
    *,
    root: Path,
    marker: Mapping[str, object],
) -> dict[str, object]:
    """Rebuild one R33 attempt row from its marker and private claim."""

    if not isinstance(marker, Mapping) or set(marker) != set(_R33_ATTEMPT_MARKER_KEYS):
        raise HoldoutAdmissionError("R33 consume marker schema is invalid")
    if marker.get("schema_version") != _ATTEMPT_SCHEMA or marker.get("event") != "consume":
        raise HoldoutAdmissionError("R33 consume marker version is invalid")
    if marker.get("observation_role") != OBSERVATION_ROLE_N_PILOT_R33:
        raise HoldoutAdmissionError("R33 consume marker role is invalid")
    claim_digest = _require_sha256(marker.get("claim_digest"), "claim_digest")
    attempt_id = _require_text(marker.get("attempt_id"), "attempt_id")
    schedule_index = marker.get("schedule_index")
    if type(schedule_index) is not int or not 0 <= schedule_index < 396:
        raise HoldoutAdmissionError("R33 consume marker schedule index is invalid")
    claim_path = _claim_path(root, claim_digest)
    claim = _read_canonical_document(claim_path)
    if claim.get("schema_version") != _R33_CLAIM_SCHEMA or claim.get("event") != "claim":
        raise HoldoutAdmissionError("R33 consume claim schema is invalid")
    if _r33_claim_key_digest(claim) != claim_digest:
        raise HoldoutAdmissionError("R33 consume claim digest mismatch")
    indexes = claim.get("schedule_indexes")
    attempt_ids = claim.get("attempt_ids")
    if (
        not isinstance(indexes, list) or not isinstance(attempt_ids, list)
        or len(indexes) != len(attempt_ids)
        or schedule_index not in indexes
    ):
        raise HoldoutAdmissionError("R33 consume claim attempt coverage is invalid")
    ordinal = indexes.index(schedule_index)
    expected_attempt_id = attempt_ids[ordinal]
    if expected_attempt_id != attempt_id:
        raise HoldoutAdmissionError("R33 consume marker attempt identity mismatch")
    key = claim["key"]
    if not isinstance(key, Mapping):
        raise HoldoutAdmissionError("R33 consume claim key is invalid")
    expected = {
        "schema_version": _ATTEMPT_SCHEMA,
        "event": "consume",
        "claim_digest": claim_digest,
        "attempt_id": attempt_id,
        "protocol_sha256": claim["protocol_sha256"],
        "freeze_sha256": claim["freeze_sha256"],
        "schedule_sha256": claim["schedule_sha256"],
        "campaign_run_id": claim["campaign_run_id"],
        "schedule_index": schedule_index,
        "cell_id": claim["cell_id"],
        "freeze_holdout_key": key["freeze_holdout_key"],
        "configuration_id": key["configuration_id"],
        "observation_role": OBSERVATION_ROLE_N_PILOT_R33,
    }
    if dict(marker) != expected:
        raise HoldoutAdmissionError("R33 consume marker does not match its claim")
    return expected


def _recover_n_pilot_attempt_ledger_locked(root: Path) -> None:
    """Recover missing R33 attempt-ledger rows from durable consume markers."""

    attempt_path = root / _ATTEMPT_LEDGER_NAME
    existing_rows = _read_ledger(attempt_path)
    by_identity: dict[tuple[str, str], dict[str, Any]] = {}
    for row in existing_rows:
        if row.get("observation_role") != OBSERVATION_ROLE_N_PILOT_R33:
            continue
        expected = _canonical_n_pilot_attempt_ledger_row(root=root, marker=row)
        identity = (str(row["claim_digest"]), str(row["attempt_id"]))
        if identity in by_identity:
            raise HoldoutAdmissionError("R33 attempt ledger has a duplicate identity")
        if row != expected:
            raise HoldoutAdmissionError("R33 attempt ledger row differs from canonical marker row")
        by_identity[identity] = row

    consumed = root / "consumed"
    try:
        paths = sorted(consumed.iterdir(), key=lambda path: path.name)
    except OSError as exc:
        raise HoldoutAdmissionError("R33 consumed marker directory is unavailable") from exc
    expected_rows: dict[tuple[str, str], dict[str, object]] = {}
    for path in paths:
        if not path.is_file() or path.is_symlink():
            raise HoldoutAdmissionError("R33 consumed marker directory contains an unsafe entry")
        marker = _read_canonical_document(path)
        if marker.get("observation_role") != OBSERVATION_ROLE_N_PILOT_R33:
            continue
        expected = _canonical_n_pilot_attempt_ledger_row(root=root, marker=marker)
        expected_path = _r33_canonical_marker_path(root, expected)
        if path != expected_path:
            raise HoldoutAdmissionError("R33 consume marker filename is not canonical")
        identity = (str(expected["claim_digest"]), str(expected["attempt_id"]))
        if identity in expected_rows and expected_rows[identity] != expected:
            raise HoldoutAdmissionError("R33 consume marker identity is conflicting")
        expected_rows[identity] = expected
    for identity, row in by_identity.items():
        if identity not in expected_rows:
            raise HoldoutAdmissionError("R33 attempt ledger row has no consume marker")
    missing = [row for identity, row in expected_rows.items() if identity not in by_identity]
    if missing:
        _append_ledger(attempt_path, missing)


def _r33_receipt_from_input(
    *, receipt: NPilotReservationReceipt | Mapping[str, object], root: Path,
) -> tuple[dict[str, Any], str]:
    if not isinstance(receipt, Mapping):
        raise HoldoutAdmissionError("R33 consume requires a reservation receipt")
    supplied = dict(_mutable_json_tree(receipt))
    supplied_raw = _canonical_bytes(supplied)
    receipt_sha256 = hashlib.sha256(supplied_raw).hexdigest()
    path = root / _R33_RECEIPT_DIR / f"{receipt_sha256}.json"
    stored_raw = _r33_raw(path)
    if stored_raw != supplied_raw:
        raise HoldoutAdmissionError("R33 supplied receipt does not match authoritative bytes")
    stored = _read_canonical_json_bytes(path)
    _r33_validate_receipt(stored)
    return stored, receipt_sha256


def _consume_n_pilot_r33_attempt_ticket(
    receipt: NPilotReservationReceipt | Mapping[str, object], *, repo_root: Path,
    protocol: Mapping[str, object], verified_freeze_document: Mapping[str, object],
    freeze_sha256: str, schedule_sha256: str, global_schedule_index: int,
    expected_cell_id: str,
) -> HoldoutObservationAdmission:
    if type(global_schedule_index) is not int or not 0 <= global_schedule_index < 396:
        raise HoldoutAdmissionError("global_schedule_index must be in the R33 schedule")
    expected_cell_id = _require_text(expected_cell_id, "expected_cell_id")
    root = provision_shared_admission_root(Path(repo_root))
    supplied_receipt = receipt
    # The receipt is read before entering the lock, but the authoritative file
    # and all claim/ledger checks below remain under the lock.
    receipt_document, receipt_sha256 = _r33_receipt_from_input(
        receipt=supplied_receipt, root=root,
    )
    _r33_protocol_and_freeze(
        protocol=protocol, protocol_sha256=receipt_document["protocol_sha256"],
        verified_freeze_document=verified_freeze_document,
        freeze_sha256=freeze_sha256,
    )
    if schedule_sha256 != receipt_document["schedule_sha256"]:
        raise HoldoutAdmissionError("R33 schedule digest is not receipt-bound")
    _require_sha256(schedule_sha256, "schedule_sha256")
    if receipt_document["freeze_sha256"] != freeze_sha256:
        raise HoldoutAdmissionError("R33 freeze digest is not receipt-bound")
    if receipt_document["freeze_canonical_sha256"] != _canonical_value_sha256(
        verified_freeze_document
    ):
        raise HoldoutAdmissionError("R33 canonical freeze digest is not receipt-bound")
    if receipt_document["protocol_sha256"] != _canonical_value_sha256(protocol):
        raise HoldoutAdmissionError("R33 protocol digest is not canonical")
    manifest_path = root / _R33_MANIFEST_DIR / f"{receipt_sha256}.json"
    manifest = _read_canonical_json_bytes(manifest_path)
    _r33_validate_manifest(
        manifest, receipt=receipt_document, receipt_sha256=receipt_sha256,
    )
    cell = next(
        (
            item for item in receipt_document["cells"]
            if global_schedule_index in item["global_schedule_indexes"]
        ),
        None,
    )
    if not isinstance(cell, Mapping) or cell.get("cell_id") != expected_cell_id:
        raise HoldoutAdmissionError("R33 global schedule index does not match expected cell")
    claim_digest = _require_sha256(cell.get("claim_digest"), "claim_digest")
    with _locked(root):
        _recover_n_pilot_transactions_locked(root)
        _recover_n_pilot_attempt_ledger_locked(root)
        claim_path = _claim_path(root, claim_digest)
        claim = _read_canonical_document(claim_path)
        claim_raw = _r33_raw(claim_path)
        if hashlib.sha256(claim_raw).hexdigest() != cell["claim_file_sha256"]:
            raise HoldoutAdmissionError("R33 claim file hash is not receipt-bound")
        if _r33_claim_key_digest(claim) != claim_digest:
            raise HoldoutAdmissionError("R33 claim digest is not receipt-bound")
        row_candidates = [
            row for row in _read_ledger(root / _LEDGER_NAME)
            if row.get("observation_role") == OBSERVATION_ROLE_N_PILOT_R33
            and _r33_ledger_key_digest(row) == claim_digest
        ]
        if len(row_candidates) != 1:
            raise HoldoutAdmissionError("R33 claim has no unique durable ledger row")
        row = row_candidates[0]
        if hashlib.sha256(_canonical_line(row)).hexdigest() != cell["ledger_row_sha256"]:
            raise HoldoutAdmissionError("R33 ledger row hash is not receipt-bound")
        if (
            claim.get("protocol_sha256") != receipt_document["protocol_sha256"]
            or claim.get("freeze_sha256") != receipt_document["freeze_sha256"]
            or claim.get("schedule_sha256") != receipt_document["schedule_sha256"]
            or row.get("protocol_sha256") != claim.get("protocol_sha256")
            or row.get("freeze_sha256") != claim.get("freeze_sha256")
            or row.get("schedule_sha256") != claim.get("schedule_sha256")
            or claim.get("campaign_run_id") != receipt_document["campaign_run_id"]
            or row.get("campaign_run_id") != receipt_document["campaign_run_id"]
            or row.get("reps") is None
        ):
            raise HoldoutAdmissionError("R33 claim/ledger receipt binding is invalid")
        marker = {
            "schema_version": _ATTEMPT_SCHEMA,
            "event": "consume",
            "claim_digest": claim_digest,
            "attempt_id": claim["attempt_ids"][claim["schedule_indexes"].index(global_schedule_index)],
            "protocol_sha256": claim["protocol_sha256"],
            "freeze_sha256": claim["freeze_sha256"],
            "schedule_sha256": claim["schedule_sha256"],
            "campaign_run_id": claim["campaign_run_id"],
            "schedule_index": global_schedule_index,
            "cell_id": claim["cell_id"],
            "freeze_holdout_key": claim["key"]["freeze_holdout_key"],
            "configuration_id": claim["key"]["configuration_id"],
            "observation_role": OBSERVATION_ROLE_N_PILOT_R33,
        }
        marker = _canonical_n_pilot_attempt_ledger_row(root=root, marker=marker)
        marker_path = _r33_canonical_marker_path(root, marker)
        try:
            _write_exclusive(marker_path, marker)
        except FileExistsError as exc:
            raise HoldoutAdmissionError(
                "n pilot R33 attempt ticket was already consumed"
            ) from exc
        _append_ledger(root / _ATTEMPT_LEDGER_NAME, [marker])
        try:
            signatures = _protected_signatures_from_verified_freeze_core(
                _mutable_json_tree(verified_freeze_document)
            )
        except HoldoutObservationError as exc:
            raise HoldoutAdmissionError(
                f"cannot derive n pilot R33 protected signatures: {exc}"
            ) from exc
        neutral_holdouts = {
            item.freeze_holdout_key: {
                "candidate_id": item.freeze_candidate_id,
                "ycsb": {"ycsb_rratio": item.ycsb_rratio},
            }
            for item in signatures
        }
        freeze_document = _mutable_json_tree(verified_freeze_document)
        pilot_reps = row.get("reps")
        if type(pilot_reps) is not int or pilot_reps <= 0:
            raise HoldoutAdmissionError("R33 ledger reps is invalid")
    try:
        observation_receipt = _new_durable_attempt_consumption_receipt(
            attempt_id=marker["attempt_id"], permitted_run_once_calls=pilot_reps,
        )
        observation = _issue_holdout_observation_admission_from_receipt(
            receipt=observation_receipt,
            verified_freeze_document=freeze_document,
            freeze_holdout_key=marker["freeze_holdout_key"],
            _neutral_holdouts=neutral_holdouts,
        )
        assert_issued_holdout_observation(observation)
    except HoldoutObservationError as exc:
        raise HoldoutAdmissionError(
            f"cannot issue n pilot R33 attempt observation: {exc}"
        ) from exc
    return observation


def _n_pilot_cell_state(admission: object) -> _NPilotCellState:
    with _state_lock:
        state = _n_pilot_cell_states.get(id(admission))
    if state is None or state.token is not admission:
        raise HoldoutAdmissionError("n pilot cell holdout admission was not issued")
    return state


def consume_n_pilot_attempt_ticket(
    receipt: NPilotReservationReceipt | Mapping[str, object] | NPilotCellHoldoutAdmission,
    *, repo_root: Path | None = None, protocol: Mapping[str, object] | None = None,
    verified_freeze_document: Mapping[str, object] | None = None,
    freeze_sha256: str | None = None, schedule_sha256: str | None = None,
    global_schedule_index: int | None = None, expected_cell_id: str | None = None,
    schedule_index: int | None = None,
) -> HoldoutObservationAdmission:
    """Consume an R33 receipt or retain the legacy n-pilot cell API.

    The R33 branch has no dependency on ``_n_pilot_cell_states``.  The final
    ``schedule_index`` keyword exists solely for the already-issued legacy
    ``n_pilot`` role and is intentionally not accepted by the receipt branch.
    """

    if isinstance(receipt, Mapping) or isinstance(receipt, NPilotReservationReceipt):
        if (
            repo_root is None or protocol is None
            or verified_freeze_document is None or freeze_sha256 is None
            or schedule_sha256 is None or global_schedule_index is None
            or expected_cell_id is None
        ):
            raise HoldoutAdmissionError(
                "R33 consume requires receipt, repo_root, protocol, freeze, schedule, and cell"
            )
        return _consume_n_pilot_r33_attempt_ticket(
            receipt, repo_root=repo_root, protocol=protocol,
            verified_freeze_document=verified_freeze_document,
            freeze_sha256=freeze_sha256, schedule_sha256=schedule_sha256,
            global_schedule_index=global_schedule_index,
            expected_cell_id=expected_cell_id,
        )
    admission = receipt
    if not isinstance(admission, NPilotCellHoldoutAdmission):
        raise HoldoutAdmissionError("n pilot admission is not a recognized receipt or legacy token")
    if schedule_index is None:
        raise HoldoutAdmissionError("legacy n pilot consume requires schedule_index")

    state = _n_pilot_cell_state(admission)
    if type(schedule_index) is not int or schedule_index < 0:
        raise HoldoutAdmissionError("schedule_index must be a nonnegative exact int")
    attempt_id = state.attempt_ids_by_schedule_index.get(schedule_index)
    if attempt_id is None:
        raise HoldoutAdmissionError("schedule_index is not in the n pilot ticket set")
    marker = {
        "schema_version": _ATTEMPT_SCHEMA,
        "event": "consume",
        "claim_digest": state.claim_digest,
        "attempt_id": attempt_id,
        "protocol_sha256": state.row["protocol_sha256"],
        "freeze_sha256": state.row["freeze_sha256"],
        "schedule_sha256": state.row["schedule_sha256"],
        "campaign_run_id": state.row["campaign_run_id"],
        "schedule_index": schedule_index,
        "cell_id": state.row["cell_id"],
        "freeze_holdout_key": state.row["freeze_holdout_key"],
        "configuration_id": state.row["configuration_id"],
        "observation_role": OBSERVATION_ROLE_N_PILOT,
    }
    marker_digest = hashlib.sha256(attempt_id.encode("utf-8")).hexdigest()
    path = state.root / "consumed" / f"{state.claim_digest}-{marker_digest}.json"
    with _locked(state.root):
        try:
            _write_exclusive(path, marker)
        except FileExistsError as exc:
            raise HoldoutAdmissionError(
                "n pilot attempt ticket was already consumed"
            ) from exc
        _append_ledger(state.root / _ATTEMPT_LEDGER_NAME, [marker])
    try:
        receipt = _new_durable_attempt_consumption_receipt(
            attempt_id=attempt_id,
            permitted_run_once_calls=state.pilot_reps,
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
            f"cannot issue n pilot attempt observation: {exc}"
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
    try:
        _floor_contract.validate_session_start_authorizations(
            [row for row in records if row.get("event") == "session-start"],
            schedule=state.schedule,
            retry_slots_per_cell=state.retry_slots_per_cell,
        )
    except _floor_contract.FloorContractError as exc:
        raise HoldoutAdmissionError(
            f"session-start authorization is not canonical: {exc}"
        ) from exc
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


_FLOOR_CLAIM_KEYS_V1 = frozenset({
    "schema_version", "event", "key", "measurement_head", "protocol_sha256",
    "freeze_candidate_id", "trial_workload_name", "cell_id", "records", "threads",
    "workload", "campaign_run_id", "run_relpath", "mode",
    "irreversible_pilot_approved", "attempt_ids",
})
_FLOOR_CLAIM_KEYS_V2 = _FLOOR_CLAIM_KEYS_V1 | frozenset({
    "entry_kind", "nondefault_seams",
})
_REFREEZE_DISQUALIFICATION_KEYS = frozenset({
    "schema_version", "reason", "campaign_run_id", "run_relpath",
    "protocol_sha256", "freeze_sha256",
})
_FLOOR_LEDGER_KEYS = frozenset({
    "schema_version", "event", "freeze_sha256", "freeze_holdout_key",
    "configuration_id", "ccbench_pin", "env_tag", "observation_role",
    "measurement_head", "protocol_sha256", "manifest_sha256",
    "freeze_candidate_id", "trial_workload_name", "cell_id", "records", "threads",
    "workload", "campaign_run_id", "run_relpath", "mode",
    "irreversible_pilot_approved", "attempt_ids", "attempt_count",
})
_FLOOR_ATTEMPT_KEYS = frozenset({
    "schema_version", "event", "claim_digest", "attempt_id", "campaign_run_id",
    "manifest_sha256", "run_relpath", "cell_id", "freeze_holdout_key",
    "configuration_id", "observation_role",
})


def _portable_admission_projection_row(
    row: Mapping[str, object],
) -> dict[str, object]:
    """Project an exact live row without its repository-local Git identity.

    ``measurement_head`` is checked above as an exact claim/ledger field, but it
    identifies the measurement authority repository rather than the portable
    campaign result.  Keeping it in the result receipt would make otherwise
    identical artifact bytes depend on which clean repository performed the run.

    ``measurement_head`` は台帳内部の非権威的な同値確認用 field であり、成果物の
    identity を束縛しない。ledger と claim を同期して書き換えれば portable receipt も
    受理集合も変わらない。測定 commit の権威的束縛は本 wave の保証範囲外である。
    """

    if set(row) != set(_FLOOR_LEDGER_KEYS):
        raise FloorHoldoutEvidenceError(
            category="mismatch", reason="main-ledger-shape-mismatch",
        )
    return {
        key: row[key]
        for key in sorted(_FLOOR_LEDGER_KEYS - {"measurement_head"})
    }


def _evidence_path_kind(path: Path, *, kind: str, missing_reason: str) -> None:
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError as exc:
        raise FloorHoldoutEvidenceError(
            category="unverifiable", reason=missing_reason,
        ) from exc
    except OSError as exc:
        raise FloorHoldoutEvidenceError(
            category="unverifiable", reason=f"{missing_reason}-unavailable",
        ) from exc
    expected = stat.S_ISDIR(mode) if kind == "directory" else stat.S_ISREG(mode)
    if not expected or path.is_symlink():
        raise FloorHoldoutEvidenceError(
            category="unverifiable", reason=f"{missing_reason}-unsafe-type",
        )


def _read_evidence_ledger(
    path: Path, *, missing_reason: str, empty_reason: str,
    allow_missing: bool = False, allow_empty: bool = False,
    empty_category: Literal["unverifiable", "mismatch"] = "mismatch",
) -> list[dict[str, Any]]:
    try:
        info = path.lstat()
    except FileNotFoundError as exc:
        if allow_missing:
            return []
        raise FloorHoldoutEvidenceError(
            category="unverifiable", reason=missing_reason,
        ) from exc
    except OSError as exc:
        raise FloorHoldoutEvidenceError(
            category="unverifiable", reason=f"{missing_reason}-unavailable",
        ) from exc
    if not stat.S_ISREG(info.st_mode) or path.is_symlink():
        raise FloorHoldoutEvidenceError(
            category="unverifiable", reason=f"{missing_reason}-unsafe-type",
        )
    if info.st_size == 0:
        if allow_empty:
            return []
        raise FloorHoldoutEvidenceError(
            category=empty_category, reason=empty_reason,
        )
    try:
        return _read_ledger(path)
    except HoldoutAdmissionError as exc:
        raise FloorHoldoutEvidenceError(
            category="mismatch", reason=f"{path.name}-malformed",
        ) from exc


def _read_evidence_document(
    path: Path, *, missing_reason: str, malformed_reason: str | None = None,
) -> dict[str, Any]:
    try:
        path.lstat()
    except FileNotFoundError as exc:
        raise FloorHoldoutEvidenceError(
            category="unverifiable", reason=missing_reason,
        ) from exc
    except OSError as exc:
        raise FloorHoldoutEvidenceError(
            category="unverifiable", reason=f"{missing_reason}-unavailable",
        ) from exc
    try:
        return _read_canonical_document(path)
    except HoldoutAdmissionError as exc:
        raise FloorHoldoutEvidenceError(
            category="mismatch",
            reason=malformed_reason or f"{path.name}-malformed",
        ) from exc


def _inspect_refreeze_disqualification_markers(
    root: Path, *, campaign_run_id: str,
) -> list[dict[str, Any]]:
    marker_root = root / _REFREEZE_DISQUALIFICATION_DIR
    try:
        info = marker_root.lstat()
    except FileNotFoundError:
        # Backward compatibility for roots created before marker support.
        return []
    except OSError as exc:
        raise FloorHoldoutEvidenceError(
            category="unverifiable", reason="refreeze-marker-root-unavailable",
        ) from exc
    if not stat.S_ISDIR(info.st_mode) or marker_root.is_symlink():
        raise FloorHoldoutEvidenceError(
            category="unverifiable", reason="refreeze-marker-root-unsafe-type",
        )
    try:
        paths = sorted(marker_root.iterdir(), key=lambda path: path.name)
    except OSError as exc:
        raise FloorHoldoutEvidenceError(
            category="unverifiable", reason="refreeze-marker-root-unavailable",
        ) from exc

    selected: list[dict[str, Any]] = []
    seen_campaigns: set[str] = set()
    for path in paths:
        marker = _read_evidence_document(
            path, missing_reason="refreeze-marker-missing",
        )
        if set(marker) != set(_REFREEZE_DISQUALIFICATION_KEYS):
            raise FloorHoldoutEvidenceError(
                category="mismatch", reason="refreeze-marker-shape-mismatch",
            )
        marker_campaign = marker.get("campaign_run_id")
        if type(marker_campaign) is not str or not marker_campaign:
            raise FloorHoldoutEvidenceError(
                category="mismatch", reason="refreeze-marker-identity-mismatch",
            )
        if marker_campaign in seen_campaigns:
            raise FloorHoldoutEvidenceError(
                category="mismatch", reason="refreeze-marker-count-mismatch",
            )
        seen_campaigns.add(marker_campaign)
        if path.name != _refreeze_disqualification_name(marker_campaign):
            raise FloorHoldoutEvidenceError(
                category="mismatch", reason="refreeze-marker-name-mismatch",
            )
        if (
            marker.get("schema_version") != _REFREEZE_DISQUALIFICATION_SCHEMA
            or marker.get("reason") != "resume"
        ):
            raise FloorHoldoutEvidenceError(
                category="mismatch", reason="refreeze-marker-shape-mismatch",
            )
        if marker_campaign == campaign_run_id:
            selected.append(marker)
    return selected


def _floor_row_claim_digest(row: Mapping[str, object]) -> str:
    try:
        return _claim_digest(_key_fields(
            freeze_sha256=row["freeze_sha256"],
            freeze_holdout_key=row["freeze_holdout_key"],
            configuration_id=row["configuration_id"],
            ccbench_pin=row["ccbench_pin"], env_tag=row["env_tag"],
            observation_role=row["observation_role"],
        ))
    except (KeyError, HoldoutAdmissionError) as exc:
        raise FloorHoldoutEvidenceError(
            category="mismatch", reason="main-ledger-key-invalid",
        ) from exc


def inspect_floor_holdout_admission_evidence(
    *, repo_root: Path, protocol: Mapping[str, object],
    verified_freeze_document: Mapping[str, object], freeze_sha256: str,
    manifest_sha256: str, campaign_run_id: str, run_relpath: str, mode: str,
    cells: Sequence[Mapping[str, object]], schedule: Sequence[Mapping[str, object]],
    sessions: Sequence[Mapping[str, object]],
) -> FloorHoldoutEvidenceInspection:
    """共有 admission filesystem を検査し receipt と derived eligibility を返す。

    保証境界: この inspector は現在状態だけを見る。
    台帳を削除して同一 bytes を再構成する攻撃は検出できない。全 field は公開かつ決定的で、
    ``O_EXCL`` は file が存在する間だけ効く。この耐性は本 wave の保証範囲外である。
    """

    if not isinstance(cells, Sequence) or isinstance(cells, (str, bytes, bytearray)):
        raise FloorHoldoutEvidenceError(category="mismatch", reason="cells-invalid")
    if not cells:
        raise FloorHoldoutEvidenceError(category="mismatch", reason="cells-empty")
    if not isinstance(schedule, Sequence) or isinstance(schedule, (str, bytes, bytearray)):
        raise FloorHoldoutEvidenceError(category="mismatch", reason="schedule-invalid")
    if not isinstance(sessions, Sequence) or isinstance(sessions, (str, bytes, bytearray)):
        raise FloorHoldoutEvidenceError(category="mismatch", reason="sessions-invalid")
    try:
        freeze_sha256 = _require_sha256(freeze_sha256, "freeze_sha256")
        manifest_sha256 = _require_sha256(manifest_sha256, "manifest_sha256")
        campaign_run_id = _require_text(campaign_run_id, "campaign_run_id")
        run_relpath = _portable_run_relpath(run_relpath)
        mode = _require_text(mode, "mode")
    except HoldoutAdmissionError as exc:
        raise FloorHoldoutEvidenceError(
            category="mismatch", reason="inspection-identity-invalid",
        ) from exc
    if run_relpath == "." or "\\" in run_relpath:
        raise FloorHoldoutEvidenceError(category="mismatch", reason="run-relpath-invalid")
    if not isinstance(protocol, Mapping) or not isinstance(
        verified_freeze_document, Mapping,
    ):
        raise FloorHoldoutEvidenceError(category="mismatch", reason="authority-invalid")
    protocol_sha256 = _sha256(dict(protocol))
    ccbench_pin = protocol.get("ccbench_pin")
    env_tag = protocol.get("env_tag")
    retry_slots = protocol.get("retry_slots_per_cell")
    if (
        type(ccbench_pin) is not str or not ccbench_pin
        or type(env_tag) is not str or not env_tag
        or type(retry_slots) is not int or retry_slots < 0
    ):
        raise FloorHoldoutEvidenceError(category="mismatch", reason="protocol-invalid")

    holdouts = verified_freeze_document.get("holdouts")
    if not isinstance(holdouts, Mapping) or not holdouts:
        raise FloorHoldoutEvidenceError(category="mismatch", reason="freeze-holdouts-invalid")
    cell_by_id: dict[str, dict[str, object]] = {}
    claim_identities: dict[str, str] = {}
    expected_claims: dict[str, dict[str, object]] = {}
    expected_attempt_ids: dict[str, frozenset[str]] = {}
    for raw_cell in cells:
        if not isinstance(raw_cell, Mapping):
            raise FloorHoldoutEvidenceError(category="mismatch", reason="cell-invalid")
        try:
            cell_id = _require_text(raw_cell.get("cell_id"), "cell_id")
            holdout_id = _require_text(raw_cell.get("holdout_id"), "holdout_id")
            configuration_id = _require_text(
                raw_cell.get("configuration_id"), "configuration_id",
            )
        except HoldoutAdmissionError as exc:
            raise FloorHoldoutEvidenceError(category="mismatch", reason="cell-invalid") from exc
        if cell_id in cell_by_id or cell_id != f"{holdout_id}::{configuration_id}":
            raise FloorHoldoutEvidenceError(category="mismatch", reason="cell-identity-invalid")
        freeze_entry = holdouts.get(holdout_id)
        if not isinstance(freeze_entry, Mapping):
            raise FloorHoldoutEvidenceError(category="mismatch", reason="cell-holdout-missing")
        candidate_id = freeze_entry.get("candidate_id")
        if type(candidate_id) is not str or not candidate_id:
            raise FloorHoldoutEvidenceError(category="mismatch", reason="freeze-candidate-invalid")
        key = _key_fields(
            freeze_sha256=freeze_sha256, freeze_holdout_key=holdout_id,
            configuration_id=configuration_id, ccbench_pin=ccbench_pin,
            env_tag=env_tag, observation_role=OBSERVATION_ROLE_FLOOR_CAMPAIGN,
        )
        digest = _claim_digest(key)
        attempt_ids = _attempt_ids(
            cell_id=cell_id, schedule=schedule, retry_slots=retry_slots,
        )
        claim_identities[cell_id] = digest
        expected_attempt_ids[cell_id] = frozenset(attempt_ids)
        cell_by_id[cell_id] = dict(raw_cell)
        expected_claims[cell_id] = {
            "key": key,
            "freeze_candidate_id": candidate_id,
            "trial_workload_name": holdout_id,
            "records": raw_cell.get("records"),
            "threads": raw_cell.get("threads"),
            "workload": dict(raw_cell.get("workload", {}))
            if isinstance(raw_cell.get("workload"), Mapping) else None,
            "attempt_ids": list(attempt_ids),
        }
        if expected_claims[cell_id]["workload"] is None:
            raise FloorHoldoutEvidenceError(category="mismatch", reason="cell-workload-invalid")

    try:
        root = shared_admission_root(Path(repo_root))
    except HoldoutAdmissionError as exc:
        raise FloorHoldoutEvidenceError(
            category="unverifiable", reason="shared-root-unavailable",
        ) from exc
    _evidence_path_kind(root, kind="directory", missing_reason="root-missing")
    claims_root = root / "claims"
    consumed_root = root / "consumed"
    _evidence_path_kind(claims_root, kind="directory", missing_reason="claims-missing")
    _evidence_path_kind(consumed_root, kind="directory", missing_reason="consumed-missing")
    _evidence_path_kind(root / _LOCK_NAME, kind="file", missing_reason="lock-missing")

    with _locked_readonly(root):
        try:
            if not any(claims_root.iterdir()):
                raise FloorHoldoutEvidenceError(
                    category="unverifiable", reason="claims-empty",
                )
        except OSError as exc:
            raise FloorHoldoutEvidenceError(
                category="unverifiable", reason="claims-unavailable",
            ) from exc
        resume_markers = _inspect_refreeze_disqualification_markers(
            root, campaign_run_id=campaign_run_id,
        )
        if len(resume_markers) > 1:
            raise FloorHoldoutEvidenceError(
                category="mismatch", reason="refreeze-marker-count-mismatch",
            )
        expected_resume_marker = _refreeze_disqualification_document(
            campaign_run_id=campaign_run_id, run_relpath=run_relpath,
            protocol_sha256=protocol_sha256, freeze_sha256=freeze_sha256,
        )
        if resume_markers and resume_markers[0] != expected_resume_marker:
            raise FloorHoldoutEvidenceError(
                category="mismatch", reason="refreeze-marker-identity-mismatch",
            )
        main_rows = _read_evidence_ledger(
            root / _LEDGER_NAME, missing_reason="main-ledger-missing",
            empty_reason="main-ledger-empty",
        )
        selected_main = [
            row for row in main_rows if row.get("campaign_run_id") == campaign_run_id
        ]
        if not selected_main:
            raise FloorHoldoutEvidenceError(
                category="mismatch", reason="main-ledger-campaign-missing",
            )
        main_by_cell: dict[str, dict[str, Any]] = {}
        for row in selected_main:
            if set(row) != set(_FLOOR_LEDGER_KEYS):
                raise FloorHoldoutEvidenceError(
                    category="mismatch", reason="main-ledger-shape-mismatch",
                )
            cell_id = row.get("cell_id")
            if type(cell_id) is not str or cell_id in main_by_cell:
                raise FloorHoldoutEvidenceError(
                    category="mismatch", reason="main-ledger-cell-duplicate",
                )
            main_by_cell[cell_id] = row
        if set(main_by_cell) != set(cell_by_id):
            raise FloorHoldoutEvidenceError(
                category="mismatch", reason="main-ledger-cell-coverage-mismatch",
            )

        claim_schemas: set[str] = set()
        claim_entry_kinds: set[str] = set()
        claim_seam_lists: set[tuple[str, ...]] = set()
        for cell_id, row in main_by_cell.items():
            cell = cell_by_id[cell_id]
            expected = expected_claims[cell_id]
            digest = claim_identities[cell_id]
            if _floor_row_claim_digest(row) != digest:
                raise FloorHoldoutEvidenceError(
                    category="mismatch", reason="main-ledger-claim-identity-mismatch",
                )
            measurement_head = row.get("measurement_head")
            approval = row.get("irreversible_pilot_approved")
            if (
                type(measurement_head) is not str or len(measurement_head) != 40
                or any(char not in _HEX64 for char in measurement_head)
                or type(approval) is not bool or (mode == "pilot" and approval is not True)
            ):
                raise FloorHoldoutEvidenceError(
                    category="mismatch", reason="main-ledger-run-authority-mismatch",
                )
            expected_row = {
                "schema_version": _LEDGER_SCHEMA,
                "event": "admit",
                **expected["key"],
                "measurement_head": measurement_head,
                "protocol_sha256": protocol_sha256,
                "manifest_sha256": manifest_sha256,
                "freeze_candidate_id": expected["freeze_candidate_id"],
                "trial_workload_name": expected["trial_workload_name"],
                "cell_id": cell_id,
                "records": cell.get("records"),
                "threads": cell.get("threads"),
                "workload": expected["workload"],
                "campaign_run_id": campaign_run_id,
                "run_relpath": run_relpath,
                "mode": mode,
                "irreversible_pilot_approved": approval,
                "attempt_ids": expected["attempt_ids"],
                "attempt_count": len(expected["attempt_ids"]),
            }
            if row != expected_row:
                raise FloorHoldoutEvidenceError(
                    category="mismatch", reason="main-ledger-row-mismatch",
                )
            expected_claim_v1 = {
                "schema_version": _CLAIM_SCHEMA_V1,
                "event": "claim",
                "key": expected["key"],
                "measurement_head": measurement_head,
                "protocol_sha256": protocol_sha256,
                "freeze_candidate_id": expected["freeze_candidate_id"],
                "trial_workload_name": expected["trial_workload_name"],
                "cell_id": cell_id,
                "records": cell.get("records"),
                "threads": cell.get("threads"),
                "workload": expected["workload"],
                "campaign_run_id": campaign_run_id,
                "run_relpath": run_relpath,
                "mode": mode,
                "irreversible_pilot_approved": approval,
                "attempt_ids": expected["attempt_ids"],
            }
            claim = _read_evidence_document(
                _claim_path(root, digest), missing_reason="claim-file-missing",
                malformed_reason="claim-file-mismatch",
            )
            claim_schema = claim.get("schema_version")
            if claim_schema == _CLAIM_SCHEMA_V1:
                if (
                    set(claim) != set(_FLOOR_CLAIM_KEYS_V1)
                    or claim != expected_claim_v1
                ):
                    raise FloorHoldoutEvidenceError(
                        category="mismatch", reason="claim-file-mismatch",
                    )
            elif claim_schema == _CLAIM_SCHEMA_V2:
                if set(claim) != set(_FLOOR_CLAIM_KEYS_V2):
                    raise FloorHoldoutEvidenceError(
                        category="mismatch", reason="claim-file-mismatch",
                    )
                entry_kind = claim.get("entry_kind")
                if entry_kind not in {"fresh", "resume"}:
                    raise FloorHoldoutEvidenceError(
                        category="mismatch", reason="claim-entry-kind-invalid",
                    )
                try:
                    seams = _canonical_nondefault_seams(
                        claim.get("nondefault_seams")
                    )
                except HoldoutAdmissionError as exc:
                    raise FloorHoldoutEvidenceError(
                        category="mismatch", reason="claim-nondefault-seams-invalid",
                    ) from exc
                expected_claim_v2 = {
                    **expected_claim_v1,
                    "schema_version": _CLAIM_SCHEMA_V2,
                    "entry_kind": entry_kind,
                    "nondefault_seams": seams,
                }
                if claim != expected_claim_v2:
                    raise FloorHoldoutEvidenceError(
                        category="mismatch", reason="claim-file-mismatch",
                    )
                claim_entry_kinds.add(entry_kind)
                claim_seam_lists.add(tuple(seams))
            elif (
                type(claim_schema) is str
                and frozenset(claim) in {
                    frozenset(_FLOOR_CLAIM_KEYS_V1),
                    frozenset(_FLOOR_CLAIM_KEYS_V2),
                }
            ):
                raise FloorHoldoutEvidenceError(
                    category="mismatch", reason="claim-schema-unsupported",
                )
            else:
                raise FloorHoldoutEvidenceError(
                    category="mismatch", reason="claim-file-mismatch",
                )
            claim_schemas.add(str(claim_schema))

        if len(claim_schemas) != 1:
            raise FloorHoldoutEvidenceError(
                category="mismatch", reason="claim-basis-cell-mismatch",
            )
        if claim_schemas == {_CLAIM_SCHEMA_V2}:
            if len(claim_seam_lists) != 1:
                raise FloorHoldoutEvidenceError(
                    category="mismatch", reason="claim-basis-cell-mismatch",
                )
            if len(claim_entry_kinds) != 1 and not (
                claim_entry_kinds == {"fresh", "resume"} and resume_markers
            ):
                raise FloorHoldoutEvidenceError(
                    category="mismatch", reason="claim-basis-cell-mismatch",
                )
            if "resume" in claim_entry_kinds and len(resume_markers) != 1:
                raise FloorHoldoutEvidenceError(
                    category="mismatch", reason="refreeze-marker-count-mismatch",
                )

        derived_eligible_for_refreeze = (
            claim_schemas == {_CLAIM_SCHEMA_V2}
            and mode == "official"
            and claim_entry_kinds == {"fresh"}
            and claim_seam_lists == {()}
            and not resume_markers
        )

        # session-start is the durable authorization, not proof that a ticket was
        # consumed.  A crash may leave only that start either before or after
        # consume_attempt_ticket().  For an authorized start, the O_EXCL marker is
        # therefore the durable fact from which exact ledger coverage is derived.
        # Completed sessions still constrain that fact in both directions:
        # non-competing must have consumed, while pre-probe competing must not.
        starts_by_attempt: dict[tuple[str, str], Mapping[str, object]] = {}
        completed_by_attempt: dict[tuple[str, str], Mapping[str, object]] = {}
        for session in sessions:
            if not isinstance(session, Mapping):
                raise FloorHoldoutEvidenceError(category="mismatch", reason="session-invalid")
            event = session.get("event")
            is_start = event == "session-start"
            if event not in (None, "session", "session-start"):
                raise FloorHoldoutEvidenceError(category="mismatch", reason="session-invalid")
            cell_id = session.get("cell_id")
            attempt_id = session.get("attempt_id")
            if (
                type(cell_id) is not str or cell_id not in cell_by_id
                or type(attempt_id) is not str
                or attempt_id not in expected_attempt_ids[cell_id]
            ):
                raise FloorHoldoutEvidenceError(category="mismatch", reason="session-invalid")
            session_key = (cell_id, attempt_id)
            destination = starts_by_attempt if is_start else completed_by_attempt
            if session_key in destination:
                raise FloorHoldoutEvidenceError(
                    category="mismatch", reason="session-attempt-duplicate",
                )
            destination[session_key] = session
            if not is_start:
                probe_before = session.get("probe_before")
                if (
                    not isinstance(probe_before, Mapping)
                    or type(probe_before.get("competing")) is not bool
                ):
                    raise FloorHoldoutEvidenceError(
                        category="mismatch", reason="session-invalid",
                    )

        if not set(completed_by_attempt).issubset(starts_by_attempt):
            raise FloorHoldoutEvidenceError(
                category="mismatch", reason="session-start-coverage-mismatch",
            )
        try:
            _floor_contract.validate_session_start_authorizations(
                list(starts_by_attempt.values()), schedule=schedule,
                retry_slots_per_cell=retry_slots,
            )
        except _floor_contract.FloorContractError as exc:
            raise FloorHoldoutEvidenceError(
                category="mismatch", reason="session-start-invalid",
            ) from exc
        for session_key, start in starts_by_attempt.items():
            cell_id, _attempt_id = session_key
            if start.get("kind") == "retry":
                trigger = start.get("trigger")
                triggering = [
                    session for (_cell, candidate), session
                    in completed_by_attempt.items() if candidate == trigger
                ]
                if (
                    type(trigger) is not str or len(triggering) != 1
                    or triggering[0].get("cell_id") != cell_id
                    or triggering[0].get("kind") != "planned"
                    or triggering[0].get("valid") is not False
                ):
                    raise FloorHoldoutEvidenceError(
                        category="mismatch", reason="session-start-invalid",
                    )

        frozen_markers: dict[tuple[str, str], dict[str, object]] = {}
        for cell_id, attempt_ids in expected_attempt_ids.items():
            cell = cell_by_id[cell_id]
            digest = claim_identities[cell_id]
            for attempt_id in attempt_ids:
                frozen_markers[(digest, attempt_id)] = {
                    "schema_version": _ATTEMPT_SCHEMA,
                    "event": "consume",
                    "claim_digest": digest,
                    "attempt_id": attempt_id,
                    "campaign_run_id": campaign_run_id,
                    "manifest_sha256": manifest_sha256,
                    "run_relpath": run_relpath,
                    "cell_id": cell_id,
                    "freeze_holdout_key": cell["holdout_id"],
                    "configuration_id": cell["configuration_id"],
                    "observation_role": OBSERVATION_ROLE_FLOOR_CAMPAIGN,
                }

        expected_attempt_rows: dict[tuple[str, str], dict[str, object]] = {}
        for key, expected_marker in frozen_markers.items():
            digest, attempt_id = key
            marker_path = consumed_root / (
                f"{digest}-{hashlib.sha256(attempt_id.encode('utf-8')).hexdigest()}.json"
            )
            try:
                marker_path.lstat()
            except FileNotFoundError:
                marker = None
            except OSError as exc:
                raise FloorHoldoutEvidenceError(
                    category="unverifiable", reason="consumed-marker-unavailable",
                ) from exc
            else:
                marker = _read_evidence_document(
                    marker_path, missing_reason="consumed-marker-missing",
                )
                if (expected_marker["cell_id"], attempt_id) not in starts_by_attempt:
                    raise FloorHoldoutEvidenceError(
                        category="mismatch",
                        reason="attempt-ledger-coverage-mismatch",
                    )
                if marker != expected_marker:
                    raise FloorHoldoutEvidenceError(
                        category="mismatch", reason="consumed-marker-mismatch",
                    )
                expected_attempt_rows[key] = expected_marker

            completed = completed_by_attempt.get((expected_marker["cell_id"], attempt_id))
            if completed is None:
                continue
            competing = completed["probe_before"]["competing"]
            if (competing is False and marker is None) or (
                competing is True and marker is not None
            ):
                raise FloorHoldoutEvidenceError(
                    category="mismatch", reason="attempt-ledger-coverage-mismatch",
                )

        attempt_rows = _read_evidence_ledger(
            root / _ATTEMPT_LEDGER_NAME,
            missing_reason="attempt-ledger-missing",
            empty_reason="attempt-ledger-empty",
            allow_missing=not expected_attempt_rows,
            allow_empty=not expected_attempt_rows,
        )
        selected_attempts = [
            row for row in attempt_rows if row.get("campaign_run_id") == campaign_run_id
        ]
        actual_attempt_rows: dict[tuple[str, str], dict[str, Any]] = {}
        for row in selected_attempts:
            if set(row) != set(_FLOOR_ATTEMPT_KEYS):
                raise FloorHoldoutEvidenceError(
                    category="mismatch", reason="attempt-ledger-shape-mismatch",
                )
            key = (row.get("claim_digest"), row.get("attempt_id"))
            if not all(type(item) is str for item in key) or key in actual_attempt_rows:
                raise FloorHoldoutEvidenceError(
                    category="mismatch", reason="attempt-ledger-row-duplicate",
                )
            actual_attempt_rows[key] = row
        if set(actual_attempt_rows) != set(expected_attempt_rows):
            raise FloorHoldoutEvidenceError(
                category="mismatch", reason="attempt-ledger-coverage-mismatch",
            )
        for key, expected_marker in expected_attempt_rows.items():
            row = actual_attempt_rows[key]
            if row != expected_marker:
                raise FloorHoldoutEvidenceError(
                    category="mismatch", reason="attempt-ledger-row-mismatch",
                )

        sorted_main = sorted(
            selected_main, key=lambda row: (row["cell_id"], _floor_row_claim_digest(row)),
        )
        sorted_attempts = sorted(
            selected_attempts,
            key=lambda row: (row["cell_id"], row["attempt_id"], row["claim_digest"]),
        )
        projection = {
            "schema": _LEDGER_PROJECTION_SCHEMA,
            "campaign_run_id": campaign_run_id,
            "admission_rows": [
                _portable_admission_projection_row(row) for row in sorted_main
            ],
            "attempt_rows": sorted_attempts,
        }
        receipt = {
            "schema": _floor_contract.FLOOR_HOLDOUT_ADMISSION_SCHEMA,
            "campaign_run_id": campaign_run_id,
            "run_relpath": run_relpath,
            "mode": mode,
            "protocol_sha256": protocol_sha256,
            "freeze_sha256": freeze_sha256,
            "manifest_sha256": manifest_sha256,
            "claim_identities": dict(sorted(claim_identities.items())),
            "admission_row_count": len(sorted_main),
            "attempt_row_count": len(sorted_attempts),
            "ledger_projection_sha256": hashlib.sha256(
                _canonical_bytes(projection)
            ).hexdigest(),
        }
        try:
            validated_receipt = (
                _floor_contract.validate_floor_holdout_admission_receipt(receipt)
            )
            return FloorHoldoutEvidenceInspection(
                validated_receipt,
                derived_eligible_for_refreeze=derived_eligible_for_refreeze,
            )
        except _floor_contract.FloorContractError as exc:
            raise FloorHoldoutEvidenceError(
                category="mismatch", reason="receipt-invalid",
            ) from exc
