"""Produce B-4 raw records at issuer-planned attempt paths.

One published attempt artifact contains the two arm source objects for one
manifest block.  Assembly returns those objects as distinct canonical byte
strings in manifest/on/off order, which is the order consumed by the frozen
analysis path.  No CLI, experiment runner, or cross-ablation framework lives
here.

All caller input is evidence location data.  Outcome and analysis fields are
derived from snapshotted bytes.  A visible planned target is never overwritten:
identical bytes are an idempotent success and different bytes are a typed
conflict.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
import fcntl
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import types
from typing import Any, Callable, NoReturn, TypeVar

from . import campaign_lock as campaign_lock_codec
from . import p3_b4_closed_critic as closed_critic
from . import p3_b4_launcher as launcher
from . import p3_s4_loop
from . import wal
from .attempt_registry_core import canonical_json_bytes
from .layout import CampaignLayout, campaign_lock_path
from .lock import CampaignBusy, campaign_lock
from .model import STAGE_ABORT, STAGE_COMMIT
from .p3_b4_analysis_adapter import RAW_ANALYSIS_SCHEMA_VERSION
from .p3_b4_prerun_issuer import (
    B4_RAW_RECORD_REJECTIONS_NAME,
    B4PrerunPublication,
    load_b4_prerun_publication,
)
from orchestrator.verifier import CAMPAIGN_WAL_SINK, RECEIPT_PAYLOAD_KEY
from orchestrator.verifier.commit_receipt import (
    campaign_lock_bytes_sha256,
    validate_serialized_receipt,
)


B4_ATTEMPT_RESULT_SCHEMA_VERSION = "p3-b4-attempt-result/v1"
B4_ARM_SOURCE_SCHEMA_VERSION = "p3-b4-arm-source-artifact/v1"
B4_RAW_RECORD_REJECTION_SCHEMA_VERSION = "p3-b4-raw-record-rejection/v1"
B4_RAW_RECORD_REJECTION_EVENT_SCHEMA_VERSION = (
    "p3-b4-raw-record-rejection-event/v1"
)
B4_RAW_RECORD_DEFERRED_SCHEMA_VERSION = "p3-b4-raw-record-deferred/v1"

B4_RAW_RECORD_NON_GUARANTEES = (
    "`initial_proposal_sha256` を計算・記録する経路が repo に無いため、precursor と実 campaign の束縛は転記に留まる",
    "flock は advisory である",
    "flock は advisory であり、非協力 process と一度終わった campaign の後日の再開を排除しない",
    "flock は campaign 実行の内側区間しか覆わず、その外側で実行中の campaign を終了と誤判定しうる",
    "model hash は存在せず `model_snapshot` は非 hash の識別子である",
    "treatment_fired は receipt 水準の意味に限定され、その decision で次を合成したことを証明しない",
    "treatment precursor の詳細 class は現状の証拠から作れない",
    "producer は凍結された analysis source closure の外にあり、source hash が producer 意味論を識別しない",
)

_REQUEST_KEYS = frozenset(
    {
        "attempt_id",
        "on_campaign_root",
        "off_campaign_root",
        "on_terminal_receipt_path",
        "off_terminal_receipt_path",
    }
)
_JUDGMENT_FIELDS = frozenset(
    {
        "treatment_fired",
        "contaminated",
        "protocol_ok",
        "execution_disposition",
        "precursor_hash",
        "assignment_observation",
        "throughput",
    }
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_JSON_NUMBER_RE = re.compile(
    r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?$"
)
_RED_SECTION = "\n\n# rejections —"
_RECEIPT_BUNDLE_STEMS = (
    ("receipt", "_start.json"),
    ("payload", ".json"),
    ("admitted_view", ".wal"),
    ("loop_state", ".json"),
    ("argv", ".json"),
    ("effective_prompt", ".txt"),
    ("neutral_root_identity", ".json"),
    ("envelope", ".json"),
)


class B4RawRecordIssueCode(str, Enum):
    UNKNOWN_FIELD = "unknown_field"
    ILL_TYPED = "ill_typed"
    EVIDENCE_UNAVAILABLE = "evidence_unavailable"
    EVIDENCE_SYMLINK = "evidence_symlink"
    EVIDENCE_SCHEMA = "evidence_schema"
    EVIDENCE_BINDING = "evidence_binding"
    ASSIGNMENT_UNAVAILABLE = "assignment_unavailable"
    DECIMAL_NOT_TERMINATING = "decimal_not_terminating"
    PLANNED_PATH_CONFLICT = "planned_path_conflict"
    PUBLICATION_CONFLICT = "publication_conflict"
    INCOMPLETE_SET = "incomplete_set"
    IO_ERROR = "io_error"


@dataclass(frozen=True, slots=True)
class B4RawRecordIssue:
    artifact: str
    field: str
    code: B4RawRecordIssueCode
    detail: str


@dataclass(frozen=True, slots=True)
class B4RawRecordRejection:
    schema_version: str
    attempt_id: str | None
    issues: tuple[B4RawRecordIssue, ...]


@dataclass(frozen=True, slots=True)
class B4RawRecordDurableRejection(B4RawRecordRejection):
    rejection_history_fragment_discarded: bool


@dataclass(frozen=True, slots=True)
class B4RawRecordRejectionEvent:
    schema_version: str
    issuer_commitment_sha256: str
    attempt_id: str | None
    issues: tuple[B4RawRecordIssue, ...]


@dataclass(frozen=True, slots=True)
class B4RawRecordRejectionHistory:
    path: str
    status: str
    fragment_discarded: bool
    events: tuple[B4RawRecordRejectionEvent, ...]
    detail: str | None


@dataclass(frozen=True, slots=True)
class B4RawAnalysisRejection(B4RawRecordRejection):
    rejection_history: B4RawRecordRejectionHistory


@dataclass(frozen=True, slots=True)
class B4RawRecordDeferred:
    schema_version: str
    attempt_id: str
    busy_campaign_roots: tuple[str, ...]
    checkpoint_campaign_roots: tuple[str, ...] = ()
    wal_changed_campaign_roots: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class B4AttemptResultWrite:
    schema_version: str
    attempt_id: str
    artifact_path: str
    canonical_bytes: bytes
    sha256: str
    idempotent: bool


@dataclass(frozen=True, slots=True)
class B4RawAnalysisAssembly:
    schema_version: str
    canonical_bytes: bytes
    sha256: str
    source_artifact_bytes: tuple[bytes, ...]
    planned_attempt_artifact_paths: tuple[str, ...]
    rejection_history: B4RawRecordRejectionHistory


@dataclass(frozen=True, slots=True)
class _DecimalToken:
    text: str

    def __post_init__(self) -> None:
        if type(self.text) is not str or _JSON_NUMBER_RE.fullmatch(self.text) is None:
            raise ValueError("invalid JSON decimal token")
        try:
            value = Decimal(self.text)
        except InvalidOperation as exc:
            raise ValueError("invalid JSON decimal token") from exc
        if not value.is_finite():
            raise ValueError("JSON decimal token is not finite")


@dataclass(frozen=True, slots=True)
class _Snapshot:
    path: str
    data: bytes
    sha256: str


@dataclass(frozen=True, slots=True)
class _ReceiptBundle:
    terminal: closed_critic.B4ClosedCriticReceipt
    payload: dict[str, Any]
    snapshots: tuple[_Snapshot, ...]
    admitted_wal: bytes
    loop_state: bytes
    terminal_path: str
    terminal_sha256: str
    transitive_snapshots: tuple[_Snapshot, ...]


@dataclass(frozen=True, slots=True)
class _ArmObservation:
    arm: str
    source: dict[str, Any]
    campaign_id: str
    iteration: int
    pair_id: str
    wal_first_ts: Decimal
    terminal_present: bool
    execution_lock_path: str
    checkpoint_deferred: bool
    wal_changed_after_lock: bool


@dataclass(slots=True)
class _EvidenceValidationContext:
    """One-call cache for invariant evidence bytes, never a cross-call seal."""

    invariant_snapshots: dict[str, _Snapshot]
    projection_sha256s: dict[str, str]
    receipt_verifiers: dict[tuple[str, str, str], Callable[[Path], Any]]

    @classmethod
    def create(cls) -> "_EvidenceValidationContext":
        return cls(
            invariant_snapshots={},
            projection_sha256s={},
            receipt_verifiers={},
        )

    def invariant_snapshot(
        self,
        path: str,
        *,
        artifact: str,
        field: str,
    ) -> _Snapshot:
        cached = self.invariant_snapshots.get(path)
        if cached is None:
            cached = _snapshot_regular(path, artifact=artifact, field=field)
            self.invariant_snapshots[path] = cached
        return cached


_T = TypeVar("_T")


@dataclass(frozen=True, slots=True)
class _SnapshotByteReader:
    data: bytes

    def read_bytes(self) -> bytes:
        return self.data


class _Reject(Exception):
    def __init__(self, issue: B4RawRecordIssue) -> None:
        super().__init__(issue.detail)
        self.issue = issue


def _issue(
    artifact: str,
    field: str,
    code: B4RawRecordIssueCode,
    detail: str,
) -> NoReturn:
    raise _Reject(B4RawRecordIssue(artifact, field, code, detail))


def _rejection(
    attempt_id: str | None,
    *issues: B4RawRecordIssue,
) -> B4RawRecordRejection:
    return B4RawRecordRejection(
        schema_version=B4_RAW_RECORD_REJECTION_SCHEMA_VERSION,
        attempt_id=attempt_id,
        issues=tuple(issues),
    )


def _recording_attempt_id(
    publication: B4PrerunPublication,
    request: object,
) -> str | None:
    """Recover only an issuer-planned ID without changing request validation."""

    if type(request) is not dict:
        return None
    candidate = request.get("attempt_id")
    if type(candidate) is not str:
        return None
    if any(
        planned.attempt_id == candidate
        for planned in publication.planned_result_artifacts
    ):
        return candidate
    return None


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_sha256(value: object) -> bool:
    return type(value) is str and _SHA256_RE.fullmatch(value) is not None


def _json_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> NoReturn:
    raise ValueError(f"non-finite JSON constant: {value}")


def _strict_json(data: bytes, *, decimal_tokens: bool = False) -> Any:
    kwargs: dict[str, Any] = {
        "object_pairs_hook": _json_pairs,
        "parse_constant": _reject_constant,
    }
    if decimal_tokens:
        kwargs["parse_int"] = int
        kwargs["parse_float"] = _DecimalToken
    return json.loads(data.decode("utf-8"), **kwargs)


def _encode_json(value: Any) -> bytes:
    """Encode the small closed value domain while preserving decimal lexemes."""

    if value is None:
        return b"null"
    if value is True:
        return b"true"
    if value is False:
        return b"false"
    if type(value) is int:
        return str(value).encode("ascii")
    if isinstance(value, _DecimalToken):
        return value.text.encode("ascii")
    if type(value) is str:
        return json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    if type(value) in (list, tuple):
        return b"[" + b",".join(_encode_json(item) for item in value) + b"]"
    if type(value) is dict:
        if any(type(key) is not str for key in value):
            raise TypeError("JSON object key is not str")
        return b"{" + b",".join(
            _encode_json(key) + b":" + _encode_json(value[key])
            for key in sorted(value)
        ) + b"}"
    raise TypeError(f"unsupported canonical JSON value: {type(value).__name__}")


def _fraction_token(value: object) -> int | _DecimalToken:
    if (
        type(value) is not tuple
        or len(value) != 2
        or type(value[0]) is not int
        or type(value[1]) is not int
        or value[1] == 0
    ):
        raise ValueError("reference_tps is not an exact ratio")
    exact = Fraction(value[0], value[1])
    if exact <= 0:
        raise ValueError("reference_tps is not positive")
    denominator = exact.denominator
    while denominator % 2 == 0:
        denominator //= 2
    while denominator % 5 == 0:
        denominator //= 5
    if denominator != 1:
        raise ArithmeticError("reference_tps has no finite decimal expansion")
    exponent = max(
        _factor_count(exact.denominator, 2),
        _factor_count(exact.denominator, 5),
    )
    scaled = exact.numerator * (10**exponent // exact.denominator)
    sign = "-" if scaled < 0 else ""
    digits = str(abs(scaled))
    if exponent == 0:
        return scaled
    digits = digits.rjust(exponent + 1, "0")
    integer = digits[:-exponent]
    fraction = digits[-exponent:].rstrip("0")
    return _DecimalToken(sign + integer + ("." + fraction if fraction else ""))


def _factor_count(value: int, factor: int) -> int:
    count = 0
    while value % factor == 0:
        value //= factor
        count += 1
    return count


def _canonical_absolute_path(value: object, *, artifact: str, field: str) -> str:
    if type(value) is not str or not value or "\x00" in value:
        _issue(artifact, field, B4RawRecordIssueCode.ILL_TYPED, "path is invalid")
    if not os.path.isabs(value) or value.startswith("//"):
        _issue(artifact, field, B4RawRecordIssueCode.ILL_TYPED, "path is not absolute")
    components = value.split("/")[1:]
    if not components or any(item in ("", ".", "..") for item in components):
        _issue(artifact, field, B4RawRecordIssueCode.ILL_TYPED, "path is not canonical")
    if os.path.normpath(value) != value:
        _issue(artifact, field, B4RawRecordIssueCode.ILL_TYPED, "path is not canonical")
    return value


def _snapshot_regular(path_value: object, *, artifact: str, field: str) -> _Snapshot:
    path = _canonical_absolute_path(path_value, artifact=artifact, field=field)
    components = path.split("/")[1:]
    directory_fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    leaf_fd = -1
    try:
        for component in components[:-1]:
            try:
                next_fd = os.open(
                    component,
                    os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0),
                    dir_fd=directory_fd,
                )
            except OSError as exc:
                code = (
                    B4RawRecordIssueCode.EVIDENCE_SYMLINK
                    if exc.errno == getattr(os, "ELOOP", 40)
                    else B4RawRecordIssueCode.EVIDENCE_UNAVAILABLE
                )
                _issue(artifact, field, code, f"cannot open evidence component: {component}")
            os.close(directory_fd)
            directory_fd = next_fd
        try:
            leaf_fd = os.open(
                components[-1],
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=directory_fd,
            )
        except OSError as exc:
            code = (
                B4RawRecordIssueCode.EVIDENCE_SYMLINK
                if exc.errno == getattr(os, "ELOOP", 40)
                else B4RawRecordIssueCode.EVIDENCE_UNAVAILABLE
            )
            _issue(artifact, field, code, "cannot open evidence leaf")
        info = os.fstat(leaf_fd)
        if not stat.S_ISREG(info.st_mode):
            _issue(
                artifact,
                field,
                B4RawRecordIssueCode.EVIDENCE_SCHEMA,
                "evidence leaf is not a regular file",
            )
        chunks: list[bytes] = []
        while True:
            chunk = os.read(leaf_fd, 65536)
            if not chunk:
                break
            chunks.append(chunk)
        data = b"".join(chunks)
        return _Snapshot(path=path, data=data, sha256=_sha256(data))
    finally:
        if leaf_fd >= 0:
            os.close(leaf_fd)
        os.close(directory_fd)


def _ensure_real_parent(path: str) -> None:
    parent = os.path.dirname(path)
    current = "/"
    for component in parent.split("/")[1:]:
        current = os.path.join(current, component)
        try:
            os.mkdir(current, 0o700)
        except FileExistsError:
            pass
        try:
            info = os.lstat(current)
        except OSError as exc:
            _issue(path, "artifact_path", B4RawRecordIssueCode.IO_ERROR, str(exc))
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            _issue(
                path,
                "artifact_path",
                B4RawRecordIssueCode.EVIDENCE_SYMLINK,
                "planned path parent is not a real directory",
            )


def _publish_exact(path: str, data: bytes) -> bool:
    """Publish bytes without replacement; return True for an idempotent hit."""

    _ensure_real_parent(path)
    parent = os.path.dirname(path)
    name = os.path.basename(path)
    parent_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0))
    temp_name = f".{name}.tmp-{os.getpid()}-{os.urandom(16).hex()}"
    temp_fd = -1
    published = False
    try:
        try:
            existing = _snapshot_regular(path, artifact=path, field="artifact_path")
        except _Reject as exc:
            if exc.issue.code is not B4RawRecordIssueCode.EVIDENCE_UNAVAILABLE:
                raise
        else:
            if existing.data == data:
                return True
            _issue(
                path,
                "artifact_path",
                B4RawRecordIssueCode.PLANNED_PATH_CONFLICT,
                "planned target already contains different bytes",
            )

        temp_fd = os.open(
            temp_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=parent_fd,
        )
        offset = 0
        while offset < len(data):
            count = os.write(temp_fd, data[offset:])
            if count <= 0:
                raise OSError("temporary write made no progress")
            offset += count
        os.fsync(temp_fd)
        os.close(temp_fd)
        temp_fd = -1
        try:
            os.link(
                temp_name,
                name,
                src_dir_fd=parent_fd,
                dst_dir_fd=parent_fd,
                follow_symlinks=False,
            )
            published = True
        except FileExistsError:
            existing = _snapshot_regular(path, artifact=path, field="artifact_path")
            if existing.data != data:
                _issue(
                    path,
                    "artifact_path",
                    B4RawRecordIssueCode.PLANNED_PATH_CONFLICT,
                    "concurrent planned target contains different bytes",
                )
            return True
        os.fsync(parent_fd)
        os.unlink(temp_name, dir_fd=parent_fd)
        os.fsync(parent_fd)
        return False
    except _Reject:
        raise
    except OSError as exc:
        if published:
            try:
                visible = _snapshot_regular(path, artifact=path, field="artifact_path")
            except _Reject:
                pass
            else:
                if visible.data == data:
                    return True
        _issue(path, "artifact_path", B4RawRecordIssueCode.IO_ERROR, str(exc))
    finally:
        if temp_fd >= 0:
            os.close(temp_fd)
        try:
            os.unlink(temp_name, dir_fd=parent_fd)
        except OSError:
            pass
        os.close(parent_fd)


def _rejection_event_payload(
    publication: B4PrerunPublication,
    rejection: B4RawRecordRejection,
) -> dict[str, Any]:
    return {
        "schema_version": B4_RAW_RECORD_REJECTION_EVENT_SCHEMA_VERSION,
        "issuer_commitment_sha256": publication.issuer_commitment_sha256,
        "attempt_id": rejection.attempt_id,
        "issues": [
            {
                "artifact": issue.artifact,
                "field": issue.field,
                "code": issue.code.value,
                "detail": issue.detail,
            }
            for issue in rejection.issues
        ],
    }


def _fragment_discarded_rejection(path: str) -> B4RawRecordRejection:
    return _rejection(
        None,
        B4RawRecordIssue(
            artifact=path,
            field="rejection_history",
            code=B4RawRecordIssueCode.IO_ERROR,
            detail="unterminated rejection ledger fragment was discarded before append",
        ),
    )


def _last_complete_line_offset(fd: int, size: int) -> int:
    end = size
    while end > 0:
        start = max(0, end - 65536)
        chunk = os.pread(fd, end - start, start)
        newline = chunk.rfind(b"\n")
        if newline >= 0:
            return start + newline + 1
        end = start
    return 0


def _append_rejection_event(
    publication: B4PrerunPublication,
    rejection: B4RawRecordRejection,
) -> bool:
    """Append one event and return whether an unterminated tail was removed."""

    path = os.path.join(
        publication.publication_root,
        B4_RAW_RECORD_REJECTIONS_NAME,
    )
    _ensure_real_parent(path)
    root_fd = os.open(
        publication.publication_root,
        os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0),
    )
    ledger_fd = -1
    created = False
    flags = (
        os.O_RDWR
        | os.O_APPEND
        | os.O_CREAT
        | getattr(os, "O_NOFOLLOW", 0)
    )
    rejection_line = canonical_json_bytes(
        _rejection_event_payload(publication, rejection)
    ) + b"\n"
    try:
        try:
            ledger_fd = os.open(
                B4_RAW_RECORD_REJECTIONS_NAME,
                flags | os.O_EXCL,
                0o600,
                dir_fd=root_fd,
            )
            created = True
        except FileExistsError:
            ledger_fd = os.open(
                B4_RAW_RECORD_REJECTIONS_NAME,
                flags,
                0o600,
                dir_fd=root_fd,
            )
        info = os.fstat(ledger_fd)
        if not stat.S_ISREG(info.st_mode):
            raise OSError("rejection ledger is not a regular file")
        fcntl.flock(ledger_fd, fcntl.LOCK_EX)
        size = os.lseek(ledger_fd, 0, os.SEEK_END)
        fragment_discarded = False
        if size > 0 and os.pread(ledger_fd, 1, size - 1) != b"\n":
            os.ftruncate(ledger_fd, _last_complete_line_offset(ledger_fd, size))
            fragment_discarded = True
        append_offset = os.lseek(ledger_fd, 0, os.SEEK_END)
        lines = [rejection_line]
        if fragment_discarded:
            lines.insert(0, canonical_json_bytes(_rejection_event_payload(
                publication,
                _fragment_discarded_rejection(path),
            )) + b"\n")
        for line in lines:
            written = os.write(ledger_fd, line)
            if written != len(line):
                raise OSError("rejection ledger write was incomplete")
        try:
            os.fsync(ledger_fd)
            if created:
                os.fsync(root_fd)
        except Exception as sync_exc:
            try:
                os.ftruncate(ledger_fd, append_offset)
                os.fsync(ledger_fd)
            except Exception as rollback_exc:
                raise OSError(
                    "rejection ledger fsync failed and append rollback failed: "
                    f"{type(rollback_exc).__name__}: {rollback_exc}"
                ) from sync_exc
            raise
        return fragment_discarded
    finally:
        if ledger_fd >= 0:
            os.close(ledger_fd)
        os.close(root_fd)


def _durably_record_rejection(
    publication: B4PrerunPublication,
    rejection: B4RawRecordRejection,
) -> B4RawRecordDurableRejection:
    path = os.path.join(
        publication.publication_root,
        B4_RAW_RECORD_REJECTIONS_NAME,
    )
    try:
        fragment_discarded = _append_rejection_event(publication, rejection)
    except Exception as exc:
        return B4RawRecordDurableRejection(
            schema_version=rejection.schema_version,
            attempt_id=rejection.attempt_id,
            issues=rejection.issues + (
                B4RawRecordIssue(
                    artifact=path,
                    field="rejection_history",
                    code=B4RawRecordIssueCode.IO_ERROR,
                    detail=f"rejection ledger append failed: {type(exc).__name__}: {exc}",
                ),
            ),
            rejection_history_fragment_discarded=False,
        )
    return B4RawRecordDurableRejection(
        schema_version=rejection.schema_version,
        attempt_id=rejection.attempt_id,
        issues=rejection.issues,
        rejection_history_fragment_discarded=fragment_discarded,
    )


def _parse_rejection_event(
    line: bytes,
    *,
    publication: B4PrerunPublication,
) -> B4RawRecordRejectionEvent:
    value = _strict_json(line)
    if type(value) is not dict or set(value) != {
        "schema_version",
        "issuer_commitment_sha256",
        "attempt_id",
        "issues",
    }:
        raise ValueError("rejection event fields differ")
    if canonical_json_bytes(value) != line:
        raise ValueError("rejection event is not canonical JSON")
    if value["schema_version"] != B4_RAW_RECORD_REJECTION_EVENT_SCHEMA_VERSION:
        raise ValueError("rejection event schema differs")
    if value["issuer_commitment_sha256"] != publication.issuer_commitment_sha256:
        raise ValueError("rejection event issuer commitment differs")
    attempt_id = value["attempt_id"]
    if attempt_id is not None and (
        type(attempt_id) is not str
        or not attempt_id
        or attempt_id.strip() != attempt_id
    ):
        raise ValueError("rejection event attempt_id is invalid")
    raw_issues = value["issues"]
    if type(raw_issues) is not list or not raw_issues:
        raise ValueError("rejection event issues are invalid")
    issues: list[B4RawRecordIssue] = []
    for raw_issue in raw_issues:
        if type(raw_issue) is not dict or set(raw_issue) != {
            "artifact",
            "field",
            "code",
            "detail",
        }:
            raise ValueError("rejection event issue fields differ")
        if any(
            type(raw_issue[field]) is not str
            for field in ("artifact", "field", "code", "detail")
        ):
            raise ValueError("rejection event issue values are invalid")
        try:
            code = B4RawRecordIssueCode(raw_issue["code"])
        except ValueError as exc:
            raise ValueError("rejection event issue code is invalid") from exc
        issues.append(B4RawRecordIssue(
            artifact=raw_issue["artifact"],
            field=raw_issue["field"],
            code=code,
            detail=raw_issue["detail"],
        ))
    return B4RawRecordRejectionEvent(
        schema_version=value["schema_version"],
        issuer_commitment_sha256=value["issuer_commitment_sha256"],
        attempt_id=attempt_id,
        issues=tuple(issues),
    )


def load_b4_raw_record_rejection_history(
    publication: B4PrerunPublication,
) -> B4RawRecordRejectionHistory:
    """Read a best-effort ledger snapshot without changing assembly validity."""

    path = os.path.join(
        publication.publication_root,
        B4_RAW_RECORD_REJECTIONS_NAME,
    )
    if not os.path.lexists(path):
        return B4RawRecordRejectionHistory(
            path=path,
            status="absent",
            fragment_discarded=False,
            events=(),
            detail=None,
        )
    try:
        snapshot = _snapshot_regular(
            path,
            artifact=path,
            field="rejection_history",
        )
    except Exception as exc:
        return B4RawRecordRejectionHistory(
            path=path,
            status="invalid",
            fragment_discarded=False,
            events=(),
            detail=f"{type(exc).__name__}: {exc}",
        )
    data = snapshot.data
    fragment_discarded = bool(data and not data.endswith(b"\n"))
    complete = data if not fragment_discarded else data[: data.rfind(b"\n") + 1]
    events: list[B4RawRecordRejectionEvent] = []
    try:
        for raw_line in complete.splitlines(keepends=True):
            if not raw_line.endswith(b"\n"):
                raise ValueError("completed rejection event lacks a newline")
            events.append(_parse_rejection_event(
                raw_line[:-1],
                publication=publication,
            ))
    except Exception as exc:
        return B4RawRecordRejectionHistory(
            path=path,
            status="invalid",
            fragment_discarded=fragment_discarded,
            events=tuple(events),
            detail=f"{type(exc).__name__}: {exc}",
        )
    return B4RawRecordRejectionHistory(
        path=path,
        status="readable",
        fragment_discarded=fragment_discarded,
        events=tuple(events),
        detail=None,
    )


def _validated_publication(value: object) -> B4PrerunPublication:
    if type(value) is not B4PrerunPublication:
        _issue(
            "publication",
            "publication",
            B4RawRecordIssueCode.ILL_TYPED,
            "exact B4PrerunPublication is required",
        )
    try:
        loaded = load_b4_prerun_publication(value.publication_root)
    except Exception as exc:
        _issue(
            "publication",
            "publication_root",
            B4RawRecordIssueCode.EVIDENCE_BINDING,
            f"pre-run publication reload failed: {type(exc).__name__}",
        )
    if loaded != value:
        _issue(
            "publication",
            "publication",
            B4RawRecordIssueCode.EVIDENCE_BINDING,
            "supplied publication differs from its reloaded bytes",
        )
    return loaded


def _request(value: object) -> dict[str, Any]:
    if type(value) is not dict:
        _issue("request", "request", B4RawRecordIssueCode.ILL_TYPED, "request is not an exact dict")
    unknown = set(value) - _REQUEST_KEYS
    missing = _REQUEST_KEYS - set(value)
    if unknown:
        field = sorted(unknown)[0]
        detail = "judgment field is caller-controlled" if field in _JUDGMENT_FIELDS else "unknown request field"
        _issue("request", field, B4RawRecordIssueCode.UNKNOWN_FIELD, detail)
    if missing:
        field = sorted(missing)[0]
        _issue("request", field, B4RawRecordIssueCode.ILL_TYPED, "required locator is missing")
    attempt_id = value["attempt_id"]
    if type(attempt_id) is not str or not attempt_id or attempt_id.strip() != attempt_id:
        _issue("request", "attempt_id", B4RawRecordIssueCode.ILL_TYPED, "attempt_id is invalid")
    for field in (
        "on_campaign_root",
        "off_campaign_root",
        "on_terminal_receipt_path",
        "off_terminal_receipt_path",
    ):
        _canonical_absolute_path(value[field], artifact="request", field=field)
    return dict(value)


def _manifest_row(publication: B4PrerunPublication, attempt_id: str):
    rows = [row for row in publication.manifest.rows if row.attempt_id == attempt_id]
    if len(rows) != 1:
        _issue(
            "publication",
            "attempt_id",
            B4RawRecordIssueCode.EVIDENCE_BINDING,
            "attempt_id is not one unique analysis manifest row",
        )
    return rows[0]


def _attempt_input(publication: B4PrerunPublication, attempt_id: str):
    rows = [
        row for row in publication.registry.scheduled_attempts
        if row.attempt_id == attempt_id
    ]
    if len(rows) != 1:
        _issue(
            "publication",
            "attempt_id",
            B4RawRecordIssueCode.EVIDENCE_BINDING,
            "attempt_id is not one unique sealed registry row",
        )
    return rows[0]


def _planned_path(publication: B4PrerunPublication, attempt_id: str) -> str:
    rows = [
        item.artifact_path for item in publication.planned_result_artifacts
        if item.attempt_id == attempt_id
    ]
    if len(rows) != 1:
        _issue(
            "publication",
            "planned_result_artifacts",
            B4RawRecordIssueCode.EVIDENCE_BINDING,
            "attempt has no unique issuer-planned result path",
        )
    return rows[0]


def _projection_paths(driver_kind: str) -> tuple[tuple[str, Path], ...]:
    paths = [
        ("orchestrator/campaign/p3_b4_closed_critic.py", closed_critic.MODULE_FILE),
        ("orchestrator/campaign/claude_projected_provider.py", closed_critic.PROVIDER_FILE),
        ("orchestrator/campaign/p3_s4_loop.py", closed_critic.LOOP_FILE),
        ("orchestrator/campaign/artifact_admission.py", closed_critic.ARTIFACT_ADMISSION_FILE),
        ("orchestrator/campaign/s8b_prediction_runner.py", closed_critic.PREDICTION_RUNNER_FILE),
        ("orchestrator/campaign/role_session_isolation.py", closed_critic.ROLE_SESSION_ISOLATION_FILE),
        ("orchestrator/campaign/p3_b4_admission_record.py", closed_critic.ADMISSION_VALIDATOR_FILE),
        ("orchestrator/campaign/p3_b4_launcher.py", closed_critic.LAUNCHER_FILE),
        ("orchestrator/campaign/p3_b4_protocol.py", closed_critic.PROTOCOL_FILE),
        ("orchestrator/critic/digest.py", closed_critic.DIGEST_FILE),
        ("orchestrator/critic/identity_projection.py", closed_critic.IDENTITY_PROJECTION_FILE),
        (".claude/agents/critic.md", closed_critic.ROLE_FILE),
    ]
    if driver_kind == "sort":
        paths.append(("orchestrator/campaign/p3_s4_loop_sort.py", closed_critic.SORT_LOOP_FILE))
    elif driver_kind == "trigger":
        paths.append((
            "orchestrator/campaign/p3_s4_loop_trigger_gating.py",
            closed_critic.TRIGGER_LOOP_FILE,
        ))
    elif driver_kind != "base":
        _issue(
            "terminal_receipt",
            "driver_kind",
            B4RawRecordIssueCode.EVIDENCE_SCHEMA,
            "projection closure driver_kind is invalid",
        )
    return tuple(paths)


def _projection_sha256(
    driver_kind: str,
    *,
    context: _EvidenceValidationContext,
) -> tuple[str, tuple[_Snapshot, ...]]:
    snapshots = tuple(
        context.invariant_snapshot(
            str(path),
            artifact="projection_closure",
            field=relative,
        )
        for relative, path in _projection_paths(driver_kind)
    )
    cached = context.projection_sha256s.get(driver_kind)
    if cached is None:
        entries = {
            relative: snapshot.sha256
            for (relative, _path), snapshot in zip(
                _projection_paths(driver_kind), snapshots,
            )
        }
        entries["mediated-contract:utf-8"] = _sha256(
            closed_critic.MEDIATED_CRITIC_CONTRACT.encode("utf-8")
        )
        cached = _sha256(canonical_json_bytes({
            "schema_version": "p3-b4-projection-closure/v1",
            "entries": entries,
        }))
        context.projection_sha256s[driver_kind] = cached
    return cached, snapshots


def _receipt_verifier(
    *,
    context: _EvidenceValidationContext,
    role_snapshot: _Snapshot,
    executable_snapshot: _Snapshot,
    campaign_root: str,
    campaign_id: str,
) -> Callable[[Path], Any]:
    """Bind the existing verifier to this call's invariant byte snapshots."""

    key = (role_snapshot.path, executable_snapshot.path, campaign_root)
    cached = context.receipt_verifiers.get(key)
    if cached is not None:
        return cached

    original = closed_critic._read_verified_terminal_receipt
    verifier_globals = dict(original.__globals__)
    original_read_bytes = closed_critic._read_bytes

    def cached_projection(driver_kind: str = "base") -> str:
        value, _snapshots = _projection_sha256(driver_kind, context=context)
        return value

    def snapshot_read_bytes(path: Path, *, purpose: str) -> bytes:
        if os.fspath(path) == executable_snapshot.path:
            return executable_snapshot.data
        return original_read_bytes(path, purpose=purpose)

    def snapshotted_campaign_layout(requested_campaign_id: str) -> CampaignLayout:
        if requested_campaign_id != campaign_id:
            raise closed_critic.B4ReceiptError(
                "terminal receipt campaign differs from snapshotted campaign root"
            )
        return CampaignLayout(campaign_root)

    verifier_globals["projection_sha256"] = cached_projection
    verifier_globals["ROLE_FILE"] = _SnapshotByteReader(role_snapshot.data)
    verifier_globals["_read_bytes"] = snapshot_read_bytes
    verifier_globals["exploration_campaign_layout"] = snapshotted_campaign_layout
    cached = types.FunctionType(
        original.__code__,
        verifier_globals,
        name=original.__name__,
        argdefs=original.__defaults__,
        closure=original.__closure__,
    )
    cached.__kwdefaults__ = original.__kwdefaults__
    context.receipt_verifiers[key] = cached
    return cached


def _receipt_bundle(
    path: str,
    *,
    label: str,
    campaign_root: str,
    context: _EvidenceValidationContext,
) -> _ReceiptBundle:
    terminal_snapshot = _snapshot_regular(path, artifact=label, field="terminal_receipt")
    try:
        terminal_value = _strict_json(terminal_snapshot.data)
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        _issue(label, "terminal_receipt", B4RawRecordIssueCode.EVIDENCE_SCHEMA, str(exc))
    if type(terminal_value) is not dict:
        _issue(label, "terminal_receipt", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "terminal receipt is not an object")
    invocation_id = terminal_value.get("invocation_id")
    if type(invocation_id) is not str or not invocation_id:
        _issue(label, "invocation_id", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "invocation_id is invalid")
    campaign_id = terminal_value.get("campaign_id")
    root = _canonical_absolute_path(
        campaign_root,
        artifact=label,
        field="campaign_root",
    )
    if type(campaign_id) is not str or not campaign_id:
        _issue(label, "campaign_id", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "campaign_id is invalid")
    if os.path.basename(root) != campaign_id:
        _issue(
            label,
            "campaign_root",
            B4RawRecordIssueCode.EVIDENCE_BINDING,
            "campaign root leaf differs from terminal receipt campaign_id",
        )
    parent = os.path.dirname(path)
    expected_names = [os.path.basename(path)]
    expected_names.extend(
        (
            f"receipt_{invocation_id}{suffix}"
            if stem == "receipt"
            else f"{stem}_{invocation_id}{suffix}"
        )
        for stem, suffix in _RECEIPT_BUNDLE_STEMS
    )
    snapshots_by_name = {os.path.basename(path): terminal_snapshot}
    for name in expected_names[1:]:
        snapshots_by_name[name] = _snapshot_regular(
            os.path.join(parent, name),
            artifact=label,
            field=name,
        )
    executable_path = terminal_value.get("evidence_executable_path")
    executable_sha256 = terminal_value.get("evidence_executable_sha256")
    role_file_sha256 = terminal_value.get("role_file_sha256")
    projection_sha256 = terminal_value.get("projection_sha256")
    driver_kind = terminal_value.get("driver_kind")
    executable_snapshot = context.invariant_snapshot(
        _canonical_absolute_path(
            executable_path,
            artifact=label,
            field="evidence_executable_path",
        ),
        artifact=label,
        field="evidence_executable_path",
    )
    role_snapshot = context.invariant_snapshot(
        _canonical_absolute_path(
            str(closed_critic.ROLE_FILE),
            artifact=label,
            field="role_file",
        ),
        artifact=label,
        field="role_file",
    )
    derived_projection, projection_snapshots = _projection_sha256(
        driver_kind,
        context=context,
    )
    if executable_snapshot.sha256 != executable_sha256:
        _issue(
            label,
            "evidence_executable_sha256",
            B4RawRecordIssueCode.EVIDENCE_BINDING,
            "executable snapshot hash differs from terminal receipt",
        )
    if role_snapshot.sha256 != role_file_sha256:
        _issue(
            label,
            "role_file_sha256",
            B4RawRecordIssueCode.EVIDENCE_BINDING,
            "role snapshot hash differs from terminal receipt",
        )
    if derived_projection != projection_sha256:
        _issue(
            label,
            "projection_sha256",
            B4RawRecordIssueCode.EVIDENCE_BINDING,
            "projection closure snapshot hash differs from terminal receipt",
        )
    with tempfile.TemporaryDirectory(prefix="izanagi-b4-receipt-snapshot-") as temp:
        temp_root = Path(temp)
        for name, snapshot in snapshots_by_name.items():
            (temp_root / name).write_bytes(snapshot.data)
        try:
            verified = _receipt_verifier(
                context=context,
                role_snapshot=role_snapshot,
                executable_snapshot=executable_snapshot,
                campaign_root=root,
                campaign_id=campaign_id,
            )(temp_root / os.path.basename(path))
        except Exception as exc:
            _issue(
                label,
                "terminal_receipt",
                B4RawRecordIssueCode.EVIDENCE_SCHEMA,
                f"closed critic receipt verification failed: {type(exc).__name__}",
            )
    payload_name = f"payload_{invocation_id}.json"
    payload = _strict_json(snapshots_by_name[payload_name].data)
    admitted_name = f"admitted_view_{invocation_id}.wal"
    state_name = f"loop_state_{invocation_id}.json"
    return _ReceiptBundle(
        terminal=verified,
        payload=payload,
        snapshots=tuple(snapshots_by_name[name] for name in sorted(snapshots_by_name)),
        admitted_wal=snapshots_by_name[admitted_name].data,
        loop_state=snapshots_by_name[state_name].data,
        terminal_path=terminal_snapshot.path,
        terminal_sha256=terminal_snapshot.sha256,
        transitive_snapshots=tuple({
            snapshot.path: snapshot
            for snapshot in (
                executable_snapshot,
                role_snapshot,
                *projection_snapshots,
            )
        }.values()),
    )


def _decode_campaign_identity(snapshot: _Snapshot, *, label: str):
    try:
        decoded = campaign_lock_codec.decode_campaign_lock(snapshot.data.decode("utf-8"))
        if not wal._has_exact_b4_protocol_marker(decoded):
            raise ValueError("exact B-4 protocol marker is absent")
        campaign_id = wal._b4_campaign_id_from_lock(decoded)
        driver_kind = wal._b4_driver_kind_from_lock(decoded)
        _identity, search = wal._b4_classification_fields(decoded)
        arm = search.get("reflux")
        if arm not in {"on", "off"}:
            raise ValueError("reflux arm is invalid")
        return campaign_id, driver_kind, arm
    except Exception as exc:
        _issue(label, "campaign.lock", B4RawRecordIssueCode.EVIDENCE_SCHEMA, str(exc))


def _strict_canonical_object(snapshot: _Snapshot, *, label: str, keys: set[str]) -> dict[str, Any]:
    try:
        value = _strict_json(snapshot.data)
    except Exception as exc:
        _issue(label, os.path.basename(snapshot.path), B4RawRecordIssueCode.EVIDENCE_SCHEMA, str(exc))
    if type(value) is not dict or set(value) != keys or canonical_json_bytes(value) != snapshot.data:
        _issue(
            label,
            os.path.basename(snapshot.path),
            B4RawRecordIssueCode.EVIDENCE_SCHEMA,
            "evidence is not one exact canonical object",
        )
    return value


def _wal_frames(snapshot: _Snapshot, *, label: str) -> tuple[list[Any], list[dict[str, Any]], list[bytes]]:
    if not snapshot.data or not snapshot.data.endswith(b"\n"):
        _issue(label, "runs/wal.jsonl", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "WAL is empty or not newline framed")
    records: list[Any] = []
    lexical: list[dict[str, Any]] = []
    frames = snapshot.data.splitlines(keepends=True)
    for index, frame in enumerate(frames):
        try:
            line = frame[:-1].decode("utf-8")
            records.append(wal.parse_line(line))
            value = _strict_json(frame[:-1], decimal_tokens=True)
        except Exception as exc:
            _issue(label, f"runs/wal.jsonl:{index + 1}", B4RawRecordIssueCode.EVIDENCE_SCHEMA, str(exc))
        if type(value) is not dict:
            _issue(label, f"runs/wal.jsonl:{index + 1}", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "WAL frame is not an object")
        lexical.append(value)
    return records, lexical, frames


def _red_detail_present(digest: str) -> bool:
    """Recognize an entry from one of the four preregistered red classes."""

    marker = digest.find(_RED_SECTION)
    if marker < 0:
        return False
    red = digest[marker + len(_RED_SECTION):]
    return any(
        line.startswith("## [")
        or line.startswith("その他の abort (非 liveness")
        for line in red.splitlines()
    )


def _structured_evidence_issue(issue: B4RawRecordIssue) -> dict[str, str]:
    return {
        "artifact": issue.artifact,
        "field": issue.field,
        "code": issue.code.value,
        "detail": issue.detail,
    }


def _optional_terminal_evidence(
    load: Callable[[], _T],
) -> tuple[_T | None, B4RawRecordIssue | None]:
    try:
        return load(), None
    except _Reject as exc:
        if exc.issue.code in {
            B4RawRecordIssueCode.EVIDENCE_UNAVAILABLE,
            B4RawRecordIssueCode.EVIDENCE_SCHEMA,
            B4RawRecordIssueCode.EVIDENCE_BINDING,
        }:
            return None, exc.issue
        raise


def _execution_lock_for_root(campaign_root: str) -> str:
    root = Path(campaign_root)
    if root.parent.name != "campaigns" or root.parent.parent.name != "exploration":
        _issue(
            campaign_root,
            "campaign_root",
            B4RawRecordIssueCode.EVIDENCE_BINDING,
            "campaign root is outside the exploration campaign layout",
        )
    output_root = root.parent.parent.parent
    return campaign_lock_path(
        CampaignLayout(campaign_root),
        declared_use_class="exploration",
        output_root=str(output_root),
    )


def _admission_sidecar_path_for_pair(
    on_path: str,
    off_path: str,
) -> str:
    on_parent = Path(on_path).parent
    off_parent = Path(off_path).parent
    if on_parent.name != "on" or off_parent.name != "off" or on_parent.parent != off_parent.parent:
        _issue(
            "receipt_pair",
            "terminal_receipt_path",
            B4RawRecordIssueCode.EVIDENCE_BINDING,
            "receipt paths do not identify one on/off pair root",
        )
    return str(on_parent.parent / "admission_record_sidecar.json")


def _admission_sidecar_for_pair(on_path: str, off_path: str) -> _Snapshot:
    return _snapshot_regular(
        _admission_sidecar_path_for_pair(on_path, off_path),
        artifact="receipt_pair",
        field="admission_record_sidecar.json",
    )


def _arm_observation(
    *,
    arm: str,
    campaign_root: str,
    receipt: _ReceiptBundle,
    peer: _ReceiptBundle,
    admission_sidecar: dict[str, Any],
    admission_sidecar_path: str,
    admission_sidecar_snapshot: _Snapshot | None,
    pair_evidence_issues: tuple[B4RawRecordIssue, ...],
    pair_common_ok: bool,
    pair_views_equal: bool,
    pair_states_equal: bool,
    pair_iterations_equal: bool,
) -> _ArmObservation:
    label = f"{arm}_arm"
    evidence_issues: list[B4RawRecordIssue] = list(pair_evidence_issues)
    root = _canonical_absolute_path(campaign_root, artifact=label, field="campaign_root")
    lock_snapshot = _snapshot_regular(os.path.join(root, "campaign.lock"), artifact=label, field="campaign.lock")
    campaign_id, driver_kind, lock_arm = _decode_campaign_identity(lock_snapshot, label=label)
    if Path(root).name != campaign_id or lock_arm != arm:
        _issue(label, "campaign.lock", B4RawRecordIssueCode.EVIDENCE_BINDING, "campaign identity or arm differs from root")
    terminal = receipt.terminal
    if (
        terminal.arm != arm
        or terminal.campaign_id != campaign_id
        or terminal.driver_kind != driver_kind
        or terminal.evidence_class != "certified"
    ):
        _issue(label, "terminal_receipt", B4RawRecordIssueCode.EVIDENCE_BINDING, "receipt identity differs from campaign evidence")
    try:
        closed_critic.assert_no_campaign_identity(
            _encode_json(receipt.payload),
            campaign_path=Path(root).resolve(strict=True),
            campaign_id=campaign_id,
        )
    except Exception as exc:
        _issue(
            label,
            "critic_payload",
            B4RawRecordIssueCode.EVIDENCE_BINDING,
            f"critic payload identity projection failed: {type(exc).__name__}",
        )

    launch_path = os.path.join(root, launcher.B4_LAUNCH_SIDECAR)
    launch_snapshot, launch_snapshot_issue = _optional_terminal_evidence(
        lambda: _snapshot_regular(
            launch_path,
            artifact=label,
            field=launcher.B4_LAUNCH_SIDECAR,
        )
    )
    launch_value: dict[str, Any] | None = None
    if launch_snapshot is not None:
        launch_value, launch_schema_issue = _optional_terminal_evidence(
            lambda: _strict_canonical_object(
                launch_snapshot,
                label=label,
                keys={
                    "schema_version",
                    "campaign_id",
                    "arm",
                    "driver_kind",
                    "admission_record_sha256",
                    "launch_context_sha256",
                },
            )
        )
        if launch_schema_issue is not None:
            evidence_issues.append(launch_schema_issue)
    elif launch_snapshot_issue is not None:
        evidence_issues.append(launch_snapshot_issue)
    launch_ok = (
        launch_value is not None
        and launch_value.get("schema_version") == launcher.B4_LAUNCH_SIDECAR_SCHEMA
        and launch_value.get("campaign_id") == campaign_id
        and launch_value.get("arm") == arm
        and launch_value.get("driver_kind") == driver_kind
        and launch_value.get("admission_record_sha256")
        == admission_sidecar.get("admission_record_sha256")
        and _is_sha256(launch_value.get("launch_context_sha256"))
    )

    wal_snapshot = _snapshot_regular(os.path.join(root, "runs", "wal.jsonl"), artifact=label, field="runs/wal.jsonl")
    records, lexical, frames = _wal_frames(wal_snapshot, label=label)
    if not wal_snapshot.data.startswith(receipt.admitted_wal):
        _issue(label, "runs/wal.jsonl", B4RawRecordIssueCode.EVIDENCE_BINDING, "receipt WAL is not an exact current-WAL prefix")
    suffix = wal_snapshot.data[len(receipt.admitted_wal):]
    suffix_records: list[Any] = []
    suffix_lexical: list[dict[str, Any]] = []
    if suffix:
        if not suffix.endswith(b"\n"):
            _issue(label, "runs/wal.jsonl", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "WAL suffix is not newline framed")
        for index, frame in enumerate(suffix.splitlines(keepends=True)):
            try:
                suffix_records.append(wal.parse_line(frame[:-1].decode("utf-8")))
                suffix_lexical.append(_strict_json(frame[:-1], decimal_tokens=True))
            except Exception as exc:
                _issue(label, f"runs/wal.jsonl:suffix:{index + 1}", B4RawRecordIssueCode.EVIDENCE_SCHEMA, str(exc))
    if not suffix_lexical:
        _issue(
            label,
            "runs/wal.jsonl:attempt-first.ts",
            B4RawRecordIssueCode.ASSIGNMENT_UNAVAILABLE,
            "attempt WAL has no first record after the admitted precursor",
        )
    first_ts = suffix_lexical[0].get("ts")
    if type(first_ts) is int:
        first_ts_decimal = Decimal(first_ts)
    elif isinstance(first_ts, _DecimalToken):
        try:
            first_ts_decimal = Decimal(first_ts.text)
        except InvalidOperation as exc:
            _issue(
                label,
                "runs/wal.jsonl:attempt-first.ts",
                B4RawRecordIssueCode.ASSIGNMENT_UNAVAILABLE,
                str(exc),
            )
    else:
        _issue(
            label,
            "runs/wal.jsonl:attempt-first.ts",
            B4RawRecordIssueCode.ASSIGNMENT_UNAVAILABLE,
            "attempt WAL first-record ts is not a decimal token",
        )
    terminal_indices = [
        index for index, record in enumerate(suffix_records)
        if record.stage in {STAGE_COMMIT, STAGE_ABORT}
    ]
    terminal_index = terminal_indices[0] if terminal_indices else None
    terminal_record = None if terminal_index is None else suffix_records[terminal_index]
    terminal_raw = None if terminal_index is None else suffix_lexical[terminal_index]
    wal_terminal_ok = (
        terminal_index is None
        or (
            terminal_indices == [terminal_index]
            and terminal_index == len(suffix_records) - 1
        )
    )

    consumption_path = os.path.join(
        root,
        f"b4_closed_critic_consumption_{receipt.terminal_sha256}.json",
    )
    consumption_snapshot, consumption_snapshot_issue = _optional_terminal_evidence(
        lambda: _snapshot_regular(
            consumption_path,
            artifact=label,
            field="critic_consumption",
        )
    )
    consumption: dict[str, Any] | None = None
    if consumption_snapshot is not None:
        consumption, consumption_schema_issue = _optional_terminal_evidence(
            lambda: _strict_canonical_object(
                consumption_snapshot,
                label=label,
                keys={
                    "terminal_receipt_sha256",
                    "campaign_id",
                    "arm",
                    "iteration",
                    "pair_id",
                    "decision_sha256",
                },
            )
        )
        if consumption_schema_issue is not None:
            evidence_issues.append(consumption_schema_issue)
    elif consumption_snapshot_issue is not None:
        evidence_issues.append(consumption_snapshot_issue)
    consumption_ok = consumption == {
        "terminal_receipt_sha256": receipt.terminal_sha256,
        "campaign_id": campaign_id,
        "arm": arm,
        "iteration": terminal.iteration,
        "pair_id": terminal.pair_id,
        "decision_sha256": terminal.decision_sha256,
    }

    digest = receipt.payload.get("projected_digest")
    peer_digest = peer.payload.get("projected_digest")
    if type(digest) is not str or type(peer_digest) is not str:
        _issue(label, "projected_digest", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "projected digest is invalid")
    red_detail = _red_detail_present(digest)
    peer_red_detail = _red_detail_present(peer_digest)
    on_red_detail = red_detail if arm == "on" else peer_red_detail
    if not on_red_detail:
        _issue(
            "receipt_pair",
            "projected_digest.red_details",
            B4RawRecordIssueCode.EVIDENCE_BINDING,
            "on digest has no entry from the four preregistered red classes",
        )
    if arm == "on":
        treatment_fired = red_detail and not peer_red_detail and digest.startswith(peer_digest + "\n\n")
        contaminated = False
    else:
        treatment_fired = not red_detail and peer_red_detail and peer_digest.startswith(digest + "\n\n")
        contaminated = red_detail

    current_state_path = os.path.join(root, "loop_state.json")
    current_state_snapshot, current_state_snapshot_issue = _optional_terminal_evidence(
        lambda: _snapshot_regular(
            current_state_path,
            artifact=label,
            field="loop_state.json",
        )
    )
    current_state = None
    if current_state_snapshot is not None:
        try:
            current_state = p3_s4_loop.state_from_dict(
                _strict_json(current_state_snapshot.data)
            )
        except Exception as exc:
            evidence_issues.append(B4RawRecordIssue(
                label,
                "loop_state.json",
                B4RawRecordIssueCode.EVIDENCE_SCHEMA,
                str(exc),
            ))
    elif current_state_snapshot_issue is not None:
        evidence_issues.append(current_state_snapshot_issue)

    execution_lock = _execution_lock_for_root(root)
    lock_acquired: bool | None = None
    execution_disposition: str
    terminal_stage: str | None = None
    terminal_reason: str | None = None
    whiteboard_result: str | None = None
    throughput: _DecimalToken | None = None
    checkpoint_ok = True
    checkpoint_deferred = False
    wal_changed_after_lock = False
    commit_receipt_ok = True
    if terminal_record is None:
        if evidence_issues:
            raise _Reject(evidence_issues[0])
        try:
            with campaign_lock(execution_lock, blocking=False):
                lock_acquired = True
                locked_wal_snapshot = _snapshot_regular(
                    wal_snapshot.path,
                    artifact=label,
                    field="runs/wal.jsonl:after-lock",
                )
                wal_changed_after_lock = locked_wal_snapshot.data != wal_snapshot.data
        except CampaignBusy:
            lock_acquired = False
        execution_disposition = "terminal-record-absent"
    else:
        execution_disposition = "executed"
        terminal_stage = "COMMIT" if terminal_record.stage == STAGE_COMMIT else "ABORT"
        expected_result = "success" if terminal_stage == "COMMIT" else (
            "rejected" if terminal_record.payload.get("reason") == "diff-quarantine" else "fail"
        )
        if current_state is None:
            checkpoint_ok = False
        elif (
            current_state.iteration != terminal.iteration + 1
            or not current_state.whiteboard
            or current_state.whiteboard[-1].iteration != current_state.iteration
            or current_state.whiteboard[-1].result != expected_result
        ):
            checkpoint_deferred = True
        else:
            whiteboard_result = expected_result
        if terminal_stage == "ABORT":
            reason = terminal_record.payload.get("reason")
            if type(reason) is not str or not reason or reason.strip() != reason:
                _issue(label, "terminal_reason", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "ABORT reason is invalid")
            terminal_reason = reason
        else:
            if terminal_raw is None:
                _issue(
                    label,
                    "terminal_record",
                    B4RawRecordIssueCode.EVIDENCE_SCHEMA,
                    "COMMIT lexical frame is unavailable",
                )
            raw_payload = terminal_raw.get("payload")
            raw_tps = raw_payload.get("fitness_tps") if type(raw_payload) is dict else None
            semantic_tps = terminal_record.payload.get("fitness_tps")
            if not isinstance(raw_tps, _DecimalToken) or type(semantic_tps) not in (int, float) or semantic_tps <= 0:
                _issue(label, "throughput", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "COMMIT fitness_tps is invalid")
            throughput = raw_tps
            stored_receipt = terminal_record.payload.get(RECEIPT_PAYLOAD_KEY)
            payload_without_receipt = dict(terminal_record.payload)
            payload_without_receipt.pop(RECEIPT_PAYLOAD_KEY, None)
            try:
                validate_serialized_receipt(
                    stored_receipt,
                    sink_kind=CAMPAIGN_WAL_SINK,
                    lock_identity_sha256=campaign_lock_bytes_sha256(lock_snapshot.data),
                    variant=terminal_record.variant,
                    terminal_payload=payload_without_receipt,
                )
            except Exception:
                commit_receipt_ok = False

    protocol_ok = all(
        (
            launch_ok,
            consumption_ok,
            pair_common_ok,
            pair_views_equal,
            pair_states_equal,
            pair_iterations_equal,
            wal_terminal_ok,
            checkpoint_ok,
            commit_receipt_ok,
            not evidence_issues,
        )
    )
    source = {
        "schema_version": B4_ARM_SOURCE_SCHEMA_VERSION,
        "identity": {
            "arm": arm,
            "campaign_id": campaign_id,
            "driver_kind": driver_kind,
            "iteration": terminal.iteration,
            "pair_id": terminal.pair_id,
        },
        "raw": {
            "execution_disposition": execution_disposition,
            "whiteboard_result": whiteboard_result,
            "terminal_stage": terminal_stage,
            "terminal_reason": terminal_reason,
            "throughput": throughput,
            "treatment_fired": treatment_fired,
            "contaminated": contaminated,
            "protocol_ok": protocol_ok,
        },
        "receipt_projection": {
            "model_snapshot": terminal.model_snapshot,
            "role_file_sha256": terminal.role_file_sha256,
            "effective_prompt_sha256": terminal.effective_prompt_sha256,
            "projection_sha256": terminal.projection_sha256,
            "digest_sha256": terminal.digest_sha256,
        },
        "evidence": {
            "campaign_lock": {"path": lock_snapshot.path, "sha256": lock_snapshot.sha256},
            "launch_sidecar": {
                "path": launch_path,
                "sha256": None if launch_snapshot is None else launch_snapshot.sha256,
            },
            "wal": {
                "path": wal_snapshot.path,
                "sha256": wal_snapshot.sha256,
                "first_record_position": len(receipt.admitted_wal.splitlines()) + 1,
                "first_record_ts": first_ts,
                "terminal_record_present": terminal_record is not None,
                "terminal_record_suffix_position": None if terminal_index is None else terminal_index + 1,
            },
            "loop_state": {
                "path": current_state_path,
                "sha256": (
                    None
                    if current_state_snapshot is None
                    else current_state_snapshot.sha256
                ),
            },
            "terminal_receipt": {"path": receipt.terminal_path, "sha256": receipt.terminal_sha256},
            "admission_sidecar": {
                "path": admission_sidecar_path,
                "sha256": (
                    None
                    if admission_sidecar_snapshot is None
                    else admission_sidecar_snapshot.sha256
                ),
            },
            "receipt_bundle": [
                {"path": snapshot.path, "sha256": snapshot.sha256}
                for snapshot in receipt.snapshots
            ],
            "transitive_evidence": [
                {"path": snapshot.path, "sha256": snapshot.sha256}
                for snapshot in receipt.transitive_snapshots
            ],
            "critic_consumption": {
                "path": consumption_path,
                "sha256": (
                    None
                    if consumption_snapshot is None
                    else consumption_snapshot.sha256
                ),
            },
            "execution_lock": {"path": execution_lock, "acquired": lock_acquired},
        },
        "evidence_issues": [
            _structured_evidence_issue(issue)
            for issue in evidence_issues
        ],
        "non_guarantees": list(B4_RAW_RECORD_NON_GUARANTEES),
    }
    return _ArmObservation(
        arm=arm,
        source=source,
        campaign_id=campaign_id,
        iteration=terminal.iteration,
        pair_id=terminal.pair_id,
        wal_first_ts=first_ts_decimal,
        terminal_present=terminal_record is not None,
        execution_lock_path=execution_lock,
        checkpoint_deferred=checkpoint_deferred,
        wal_changed_after_lock=wal_changed_after_lock,
    )


def _load_attempt_value(path: str) -> tuple[_Snapshot, dict[str, Any]]:
    snapshot = _snapshot_regular(path, artifact=path, field="artifact_path")
    try:
        value = _strict_json(snapshot.data, decimal_tokens=True)
    except Exception as exc:
        _issue(path, "artifact_path", B4RawRecordIssueCode.EVIDENCE_SCHEMA, str(exc))
    if type(value) is not dict or _encode_json(value) != snapshot.data:
        _issue(path, "artifact_path", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "attempt artifact is not canonical")
    return snapshot, value


def _existing_identity_triples(publication: B4PrerunPublication, *, exclude: str) -> set[tuple[str, int, str]]:
    triples: set[tuple[str, int, str]] = set()
    planned = {item.attempt_id: item.artifact_path for item in publication.planned_result_artifacts}
    for row in publication.manifest.rows:
        if row.attempt_id == exclude:
            continue
        path = planned[row.attempt_id]
        if not os.path.lexists(path):
            continue
        _snapshot, value = _load_attempt_value(path)
        sources = value.get("arm_sources") if type(value) is dict else None
        if type(sources) is not list or len(sources) != 2:
            _issue(path, "arm_sources", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "attempt arm source set is invalid")
        for source in sources:
            identity = source.get("identity") if type(source) is dict else None
            if type(identity) is not dict:
                _issue(path, "identity", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "source identity is invalid")
            triple = (identity.get("campaign_id"), identity.get("iteration"), identity.get("arm"))
            if type(triple[0]) is not str or type(triple[1]) is not int or triple[2] not in {"on", "off"}:
                _issue(path, "identity", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "source identity tuple is invalid")
            if triple in triples:
                _issue(path, "identity", B4RawRecordIssueCode.PUBLICATION_CONFLICT, "publication duplicates one campaign/iteration/arm tuple")
            triples.add(triple)
    return triples


def _request_from_attempt_artifact(
    value: dict[str, Any],
    *,
    path: str,
) -> dict[str, object]:
    sources = value.get("arm_sources")
    if type(sources) is not list or len(sources) != 2:
        _issue(path, "arm_sources", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "arm source count differs")
    by_arm: dict[str, dict[str, Any]] = {}
    for source in sources:
        if type(source) is not dict or type(source.get("identity")) is not dict:
            _issue(path, "arm_sources", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "arm source identity is invalid")
        arm = source["identity"].get("arm")
        if arm not in {"on", "off"} or arm in by_arm:
            _issue(path, "arm_sources", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "arm source identity is duplicated or invalid")
        by_arm[arm] = source
    if set(by_arm) != {"on", "off"}:
        _issue(path, "arm_sources", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "arm identities differ")

    request: dict[str, object] = {"attempt_id": value.get("attempt_id")}
    for arm in ("on", "off"):
        evidence = by_arm[arm].get("evidence")
        if type(evidence) is not dict:
            _issue(path, f"{arm}.evidence", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "source evidence is absent")
        campaign_lock = evidence.get("campaign_lock")
        terminal_receipt = evidence.get("terminal_receipt")
        if type(campaign_lock) is not dict or type(terminal_receipt) is not dict:
            _issue(path, f"{arm}.evidence", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "source evidence pointer is absent")
        lock_path = _canonical_absolute_path(
            campaign_lock.get("path"),
            artifact=path,
            field=f"{arm}.evidence.campaign_lock.path",
        )
        if os.path.basename(lock_path) != "campaign.lock":
            _issue(path, f"{arm}.evidence.campaign_lock.path", B4RawRecordIssueCode.EVIDENCE_BINDING, "campaign lock pointer has the wrong leaf")
        request[f"{arm}_campaign_root"] = os.path.dirname(lock_path)
        request[f"{arm}_terminal_receipt_path"] = _canonical_absolute_path(
            terminal_receipt.get("path"),
            artifact=path,
            field=f"{arm}.evidence.terminal_receipt.path",
        )
    return request


def _derive_b4_attempt_data(
    publication: B4PrerunPublication,
    request: dict[str, Any],
    *,
    context: _EvidenceValidationContext,
    check_publication_uniqueness: bool,
) -> tuple[str, bytes] | B4RawRecordDeferred:
    attempt_id = request["attempt_id"]
    row = _manifest_row(publication, attempt_id)
    registry_attempt = _attempt_input(publication, attempt_id)
    planned_path = _planned_path(publication, attempt_id)
    try:
        reference_token = _fraction_token(row.reference_tps)
    except ArithmeticError:
        _issue(
            "publication",
            "reference_tps",
            B4RawRecordIssueCode.DECIMAL_NOT_TERMINATING,
            "reference_tps has no finite decimal JSON representation",
        )
    except ValueError as exc:
        _issue("publication", "reference_tps", B4RawRecordIssueCode.EVIDENCE_SCHEMA, str(exc))

    on_receipt = _receipt_bundle(
        request["on_terminal_receipt_path"],
        label="on_receipt",
        campaign_root=request["on_campaign_root"],
        context=context,
    )
    off_receipt = _receipt_bundle(
        request["off_terminal_receipt_path"],
        label="off_receipt",
        campaign_root=request["off_campaign_root"],
        context=context,
    )
    admission_path = _admission_sidecar_path_for_pair(
        request["on_terminal_receipt_path"], request["off_terminal_receipt_path"],
    )
    admission_snapshot, admission_snapshot_issue = _optional_terminal_evidence(
        lambda: _admission_sidecar_for_pair(
            request["on_terminal_receipt_path"],
            request["off_terminal_receipt_path"],
        )
    )
    admission_sidecar: dict[str, Any] = {}
    pair_evidence_issues: list[B4RawRecordIssue] = []
    if admission_snapshot is not None:
        admission_value, admission_schema_issue = _optional_terminal_evidence(
            lambda: _strict_canonical_object(
                admission_snapshot,
                label="receipt_pair",
                keys={
                    "schema_version",
                    "admission_record_repository_path",
                    "admission_record_sha256",
                    "verification_head_commit",
                    "preregistration_repository_path",
                    "preregistration_content_commit",
                    "preregistration_content_sha256",
                    "expected_claude_model_snapshot",
                    "expected_effective_critic_prompt_sha256",
                    "expected_closed_critic_projection_closure_sha256",
                },
            )
        )
        if admission_value is not None:
            admission_sidecar = admission_value
        if admission_schema_issue is not None:
            pair_evidence_issues.append(admission_schema_issue)
    elif admission_snapshot_issue is not None:
        pair_evidence_issues.append(admission_snapshot_issue)
    pair_common_ok = all(
        getattr(on_receipt.terminal, name) == getattr(off_receipt.terminal, name)
        for name in (
            "driver_kind",
            "provider_kind",
            "model_snapshot",
            "role_file_sha256",
            "effective_prompt_sha256",
            "projection_sha256",
            "evidence_executable_path",
            "evidence_executable_sha256",
        )
    ) and (
        admission_sidecar.get("schema_version") == closed_critic.ADMISSION_SIDECAR_SCHEMA_VERSION
        and admission_sidecar.get("expected_claude_model_snapshot") == on_receipt.terminal.model_snapshot
        and admission_sidecar.get("expected_effective_critic_prompt_sha256") == on_receipt.terminal.effective_prompt_sha256
        and admission_sidecar.get("expected_closed_critic_projection_closure_sha256") == on_receipt.terminal.projection_sha256
    )
    pair_views_equal = on_receipt.terminal.admitted_view_sha256 == off_receipt.terminal.admitted_view_sha256
    pair_states_equal = on_receipt.terminal.loop_state_sha256 == off_receipt.terminal.loop_state_sha256
    pair_iterations_equal = on_receipt.terminal.iteration == off_receipt.terminal.iteration

    observations = tuple(
        _arm_observation(
            arm=arm,
            campaign_root=request[f"{arm}_campaign_root"],
            receipt=receipt,
            peer=peer,
            admission_sidecar=admission_sidecar,
            admission_sidecar_path=admission_path,
            admission_sidecar_snapshot=admission_snapshot,
            pair_evidence_issues=tuple(pair_evidence_issues),
            pair_common_ok=pair_common_ok,
            pair_views_equal=pair_views_equal,
            pair_states_equal=pair_states_equal,
            pair_iterations_equal=pair_iterations_equal,
        )
        for arm, receipt, peer in (
            ("on", on_receipt, off_receipt),
            ("off", off_receipt, on_receipt),
        )
    )
    on, off = observations
    if any(row.driver != receipt.terminal.driver_kind for receipt in (on_receipt, off_receipt)):
        _issue(
            "publication",
            "driver",
            B4RawRecordIssueCode.EVIDENCE_BINDING,
            "manifest driver differs from the campaign and receipt driver_kind",
        )
    busy = tuple(
        item.source["evidence"]["campaign_lock"]["path"].rsplit("/campaign.lock", 1)[0]
        for item in observations
        if not item.terminal_present
        and item.source["evidence"]["execution_lock"]["acquired"] is False
    )
    checkpoint_deferred = tuple(
        item.source["evidence"]["campaign_lock"]["path"].rsplit("/campaign.lock", 1)[0]
        for item in observations if item.checkpoint_deferred
    )
    wal_changed = tuple(
        item.source["evidence"]["campaign_lock"]["path"].rsplit("/campaign.lock", 1)[0]
        for item in observations if item.wal_changed_after_lock
    )
    if busy or checkpoint_deferred or wal_changed:
        return B4RawRecordDeferred(
            schema_version=B4_RAW_RECORD_DEFERRED_SCHEMA_VERSION,
            attempt_id=attempt_id,
            busy_campaign_roots=busy,
            checkpoint_campaign_roots=checkpoint_deferred,
            wal_changed_campaign_roots=wal_changed,
        )
    if on.wal_first_ts == off.wal_first_ts:
        _issue(
            "assignment",
            "wal_first_record.ts",
            B4RawRecordIssueCode.ASSIGNMENT_UNAVAILABLE,
            "arm WAL first-record timestamps are equal",
        )
    assignment = ["on", "off"] if on.wal_first_ts < off.wal_first_ts else ["off", "on"]

    if check_publication_uniqueness:
        existing = _existing_identity_triples(publication, exclude=attempt_id)
        for observed in observations:
            triple = (observed.campaign_id, observed.iteration, observed.arm)
            if triple in existing:
                _issue(
                    "publication",
                    "campaign_id,iteration,arm",
                    B4RawRecordIssueCode.PUBLICATION_CONFLICT,
                    "publication already contains this campaign/iteration/arm tuple",
                )
            existing.add(triple)

    binding = {
        "attempt_id": attempt_id,
        "block_id": row.block_id,
        "driver": row.driver,
        "registry_sha256": publication.registry.sha256,
        "manifest_sha256": publication.manifest.sha256,
        "precursor_hash": registry_attempt.initial_proposal_sha256,
        "reference_tps": reference_token,
        "reference_snapshot_hash": row.reference_snapshot_hash,
        "reference_receipt_hash": row.reference_receipt_hash,
    }
    sources = []
    for observation in observations:
        source = dict(observation.source)
        source["binding"] = binding
        source["pair_comparison"] = {
            "admitted_view_sha256_equal": pair_views_equal,
            "loop_state_sha256_equal": pair_states_equal,
            "iteration_equal": pair_iterations_equal,
        }
        sources.append(source)
    return planned_path, _encode_json({
        "schema_version": B4_ATTEMPT_RESULT_SCHEMA_VERSION,
        "attempt_id": attempt_id,
        "block_id": row.block_id,
        "assignment_observation": assignment,
        "arm_sources": sources,
    })


def publish_b4_attempt_result(
    *,
    publication: object,
    request: object,
) -> B4AttemptResultWrite | B4RawRecordDeferred | B4RawRecordRejection:
    """Derive and exclusively publish one paired attempt result.

    Exact B-4 marker-bearing campaign locks are mandatory here.  A lockless
    receipt admitted by a broader COMMIT sink is not a B-4 sample, so this
    producer intentionally has the narrower acceptance set.
    """

    attempt_id: str | None = None
    checked_publication: B4PrerunPublication | None = None
    try:
        checked_publication = _validated_publication(publication)
        attempt_id = _recording_attempt_id(checked_publication, request)
        checked_request = _request(request)
        attempt_id = checked_request["attempt_id"]
        derived = _derive_b4_attempt_data(
            checked_publication,
            checked_request,
            context=_EvidenceValidationContext.create(),
            check_publication_uniqueness=True,
        )
        if isinstance(derived, B4RawRecordDeferred):
            return derived
        planned_path, data = derived
        idempotent = _publish_exact(planned_path, data)
        return B4AttemptResultWrite(
            schema_version=B4_ATTEMPT_RESULT_SCHEMA_VERSION,
            attempt_id=attempt_id,
            artifact_path=planned_path,
            canonical_bytes=data,
            sha256=_sha256(data),
            idempotent=idempotent,
        )
    except _Reject as exc:
        rejection = _rejection(attempt_id, exc.issue)
    except Exception as exc:
        rejection = _rejection(
            attempt_id,
            B4RawRecordIssue(
                artifact="producer",
                field="internal",
                code=B4RawRecordIssueCode.IO_ERROR,
                detail=f"{type(exc).__name__}: {exc}",
            ),
        )
    if checked_publication is None:
        return rejection
    return _durably_record_rejection(checked_publication, rejection)


def publish_b4_attempt_results(
    *,
    publication: object,
    requests: object,
) -> tuple[B4AttemptResultWrite | B4RawRecordDeferred | B4RawRecordRejection, ...]:
    """Publish a fixed B-4 batch while sharing only invariant evidence reads."""

    if type(requests) not in (list, tuple):
        return (_rejection(
            None,
            B4RawRecordIssue(
                "requests",
                "requests",
                B4RawRecordIssueCode.ILL_TYPED,
                "requests must be an exact list or tuple",
            ),
        ),)
    try:
        checked = _validated_publication(publication)
    except _Reject as exc:
        return (_rejection(None, exc.issue),)
    except Exception as exc:
        return (_rejection(
            None,
            B4RawRecordIssue(
                "producer",
                "internal",
                B4RawRecordIssueCode.IO_ERROR,
                f"{type(exc).__name__}: {exc}",
            ),
        ),)

    context = _EvidenceValidationContext.create()
    owners: dict[tuple[str, int, str], str] = {}
    results: list[B4AttemptResultWrite | B4RawRecordDeferred | B4RawRecordRejection] = []
    planned = {item.attempt_id: item.artifact_path for item in checked.planned_result_artifacts}
    try:
        for row in checked.manifest.rows:
            path = planned[row.attempt_id]
            if not os.path.lexists(path):
                continue
            _snapshot, value = _load_attempt_value(path)
            sources = value.get("arm_sources")
            if type(sources) is not list or len(sources) != 2:
                _issue(path, "arm_sources", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "attempt arm source set is invalid")
            for source in sources:
                identity = source.get("identity") if type(source) is dict else None
                if type(identity) is not dict:
                    _issue(path, "identity", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "source identity is invalid")
                triple = (
                    identity.get("campaign_id"),
                    identity.get("iteration"),
                    identity.get("arm"),
                )
                if (
                    type(triple[0]) is not str
                    or type(triple[1]) is not int
                    or triple[2] not in {"on", "off"}
                    or triple in owners
                ):
                    _issue(path, "identity", B4RawRecordIssueCode.PUBLICATION_CONFLICT, "publication identity tuple is duplicated or invalid")
                owners[triple] = row.attempt_id
    except _Reject as exc:
        rejection = _rejection(None, exc.issue)
        return (_durably_record_rejection(checked, rejection),)
    for item in requests:
        attempt_id = _recording_attempt_id(checked, item)
        try:
            checked_request = _request(item)
            attempt_id = checked_request["attempt_id"]
            derived = _derive_b4_attempt_data(
                checked,
                checked_request,
                context=context,
                check_publication_uniqueness=False,
            )
            if isinstance(derived, B4RawRecordDeferred):
                results.append(derived)
                continue
            planned_path, data = derived
            value = _strict_json(data, decimal_tokens=True)
            for source in value["arm_sources"]:
                identity = source["identity"]
                triple = (
                    identity["campaign_id"],
                    identity["iteration"],
                    identity["arm"],
                )
                owner = owners.get(triple)
                if owner is not None and owner != attempt_id:
                    _issue(
                        "publication",
                        "campaign_id,iteration,arm",
                        B4RawRecordIssueCode.PUBLICATION_CONFLICT,
                        "publication batch duplicates one campaign/iteration/arm tuple",
                    )
                owners[triple] = attempt_id
            idempotent = _publish_exact(planned_path, data)
            results.append(B4AttemptResultWrite(
                schema_version=B4_ATTEMPT_RESULT_SCHEMA_VERSION,
                attempt_id=attempt_id,
                artifact_path=planned_path,
                canonical_bytes=data,
                sha256=_sha256(data),
                idempotent=idempotent,
            ))
        except _Reject as exc:
            results.append(_durably_record_rejection(
                checked,
                _rejection(attempt_id, exc.issue),
            ))
        except Exception as exc:
            results.append(_durably_record_rejection(
                checked,
                _rejection(
                    attempt_id,
                    B4RawRecordIssue(
                        "producer",
                        "internal",
                        B4RawRecordIssueCode.IO_ERROR,
                        f"{type(exc).__name__}: {exc}",
                    ),
                ),
            ))
    return tuple(results)


def assemble_b4_raw_analysis(
    *,
    publication: object,
) -> B4RawAnalysisAssembly | B4RawRecordRejection:
    """Assemble all 201 planned attempt artifacts without writing another path."""

    checked: B4PrerunPublication | None = None
    rejection_history: B4RawRecordRejectionHistory | None = None
    try:
        checked = _validated_publication(publication)
        rejection_history = load_b4_raw_record_rejection_history(checked)
        planned = {item.attempt_id: item.artifact_path for item in checked.planned_result_artifacts}
        raw_blocks: list[dict[str, Any]] = []
        source_bytes: list[bytes] = []
        paths: list[str] = []
        triples: set[tuple[str, int, str]] = set()
        validation_context = _EvidenceValidationContext.create()
        for row in checked.manifest.rows:
            path = planned.get(row.attempt_id)
            if path is None or not os.path.lexists(path):
                _issue(
                    "publication",
                    row.attempt_id,
                    B4RawRecordIssueCode.INCOMPLETE_SET,
                    "planned attempt artifact is absent",
                )
            attempt_snapshot, value = _load_attempt_value(path)
            if set(value) != {
                "schema_version",
                "attempt_id",
                "block_id",
                "assignment_observation",
                "arm_sources",
            } or value.get("schema_version") != B4_ATTEMPT_RESULT_SCHEMA_VERSION:
                _issue(path, "schema_version", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "attempt artifact schema differs")
            if value.get("attempt_id") != row.attempt_id or value.get("block_id") != row.block_id:
                _issue(path, "binding", B4RawRecordIssueCode.EVIDENCE_BINDING, "attempt artifact differs from manifest row")
            derivation = _derive_b4_attempt_data(
                checked,
                _request(_request_from_attempt_artifact(value, path=path)),
                context=validation_context,
                check_publication_uniqueness=False,
            )
            if isinstance(derivation, B4RawRecordDeferred):
                _issue(
                    path,
                    "source_rederivation",
                    B4RawRecordIssueCode.EVIDENCE_BINDING,
                    "source evidence is not in a final observable state",
                )
            derived_path, derived_data = derivation
            if derived_path != path or derived_data != attempt_snapshot.data:
                _issue(
                    path,
                    "source_rederivation",
                    B4RawRecordIssueCode.EVIDENCE_BINDING,
                    "recorded judgments differ from source evidence rederivation",
                )
            sources = value.get("arm_sources")
            if type(sources) is not list or len(sources) != 2:
                _issue(path, "arm_sources", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "arm source count differs")
            by_arm = {
                source.get("identity", {}).get("arm"): source
                for source in sources
                if type(source) is dict and type(source.get("identity")) is dict
            }
            if set(by_arm) != {"on", "off"}:
                _issue(path, "arm_sources", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "arm identities differ")
            if by_arm["on"]["identity"].get("pair_id") != by_arm["off"]["identity"].get("pair_id"):
                _issue(path, "pair_id", B4RawRecordIssueCode.EVIDENCE_BINDING, "on/off pair_id differs at final assembly")

            binding = by_arm["on"].get("binding")
            if type(binding) is not dict or binding != by_arm["off"].get("binding"):
                _issue(path, "binding", B4RawRecordIssueCode.EVIDENCE_BINDING, "arm source bindings differ")
            registry_attempt = _attempt_input(checked, row.attempt_id)
            try:
                reference_token = _fraction_token(row.reference_tps)
            except ArithmeticError:
                _issue(
                    "publication",
                    "reference_tps",
                    B4RawRecordIssueCode.DECIMAL_NOT_TERMINATING,
                    "reference_tps has no finite decimal JSON representation",
                )
            expected_binding = {
                "attempt_id": row.attempt_id,
                "block_id": row.block_id,
                "driver": row.driver,
                "registry_sha256": checked.registry.sha256,
                "manifest_sha256": checked.manifest.sha256,
                "precursor_hash": registry_attempt.initial_proposal_sha256,
                "reference_tps": reference_token,
                "reference_snapshot_hash": row.reference_snapshot_hash,
                "reference_receipt_hash": row.reference_receipt_hash,
            }
            if binding != expected_binding:
                _issue(path, "binding", B4RawRecordIssueCode.EVIDENCE_BINDING, "source binding differs from sealed publication")

            raw_arms = []
            for arm in ("on", "off"):
                source = by_arm[arm]
                identity = source["identity"]
                triple = (identity.get("campaign_id"), identity.get("iteration"), arm)
                if type(triple[0]) is not str or type(triple[1]) is not int or triple in triples:
                    _issue(path, "campaign_id,iteration,arm", B4RawRecordIssueCode.PUBLICATION_CONFLICT, "publication identity tuple is duplicated or invalid")
                triples.add(triple)
                source_data = _encode_json(source)
                source_bytes.append(source_data)
                raw = source.get("raw")
                if type(raw) is not dict or set(raw) != {
                    "execution_disposition",
                    "whiteboard_result",
                    "terminal_stage",
                    "terminal_reason",
                    "throughput",
                    "treatment_fired",
                    "contaminated",
                    "protocol_ok",
                }:
                    _issue(path, "raw", B4RawRecordIssueCode.EVIDENCE_SCHEMA, "raw projection is invalid")
                raw_arms.append(
                    {
                        "arm": arm,
                        "execution_disposition": raw["execution_disposition"],
                        "whiteboard_result": raw["whiteboard_result"],
                        "terminal_stage": raw["terminal_stage"],
                        "terminal_reason": raw["terminal_reason"],
                        "throughput": raw["throughput"],
                        "precursor_hash": binding["precursor_hash"],
                        "treatment_fired": raw["treatment_fired"],
                        "contaminated": raw["contaminated"],
                        "protocol_ok": raw["protocol_ok"],
                        "source_artifact_sha256": _sha256(source_data),
                    }
                )
            raw_blocks.append(
                {
                    "block_id": row.block_id,
                    "reference_tps": reference_token,
                    "reference_snapshot_hash": row.reference_snapshot_hash,
                    "reference_receipt_hash": row.reference_receipt_hash,
                    "assignment_observation": value["assignment_observation"],
                    "arms": raw_arms,
                }
            )
            paths.append(path)
        raw_data = _encode_json(
            {"schema_version": RAW_ANALYSIS_SCHEMA_VERSION, "blocks": raw_blocks}
        )
        return B4RawAnalysisAssembly(
            schema_version=RAW_ANALYSIS_SCHEMA_VERSION,
            canonical_bytes=raw_data,
            sha256=_sha256(raw_data),
            source_artifact_bytes=tuple(source_bytes),
            planned_attempt_artifact_paths=tuple(paths),
            rejection_history=rejection_history,
        )
    except _Reject as exc:
        rejection = _rejection(None, exc.issue)
    except Exception as exc:
        rejection = _rejection(
            None,
            B4RawRecordIssue(
                artifact="producer",
                field="internal",
                code=B4RawRecordIssueCode.IO_ERROR,
                detail=f"{type(exc).__name__}: {exc}",
            ),
        )
    if checked is None or rejection_history is None:
        return rejection
    return B4RawAnalysisRejection(
        schema_version=rejection.schema_version,
        attempt_id=rejection.attempt_id,
        issues=rejection.issues,
        rejection_history=rejection_history,
    )


__all__ = [
    "B4_ARM_SOURCE_SCHEMA_VERSION",
    "B4_ATTEMPT_RESULT_SCHEMA_VERSION",
    "B4_RAW_RECORD_DEFERRED_SCHEMA_VERSION",
    "B4_RAW_RECORD_NON_GUARANTEES",
    "B4_RAW_RECORD_REJECTION_EVENT_SCHEMA_VERSION",
    "B4_RAW_RECORD_REJECTION_SCHEMA_VERSION",
    "B4AttemptResultWrite",
    "B4RawAnalysisAssembly",
    "B4RawAnalysisRejection",
    "B4RawRecordDeferred",
    "B4RawRecordDurableRejection",
    "B4RawRecordIssue",
    "B4RawRecordIssueCode",
    "B4RawRecordRejection",
    "B4RawRecordRejectionEvent",
    "B4RawRecordRejectionHistory",
    "assemble_b4_raw_analysis",
    "load_b4_raw_record_rejection_history",
    "publish_b4_attempt_result",
    "publish_b4_attempt_results",
]
