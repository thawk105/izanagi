# -*- coding: utf-8 -*-
"""WAL (write-ahead log) と クラッシュリカバリ (orchestrator-design.md D/A)。

探索は一晩回しっぱなしでクラッシュ前提。各 variant の評価を**ログ先行書き込み**で
進め (`build_start → build_done → verify_done → bench_done → commit`)、再起動時に
リプレイして「どこまで評価済みか」を復元し途中再開する。

- **D (durability):** 追記ごとに flush+fsync。クラッシュで追記済みレコードを失わない。
- **A (atomicity):** commit レコードがある variant だけ採用。なければ破棄して再評価
  (half-evaluated を population に混ぜない)。
- **末尾切れトレラント:** 追記中のクラッシュで最終行が壊れていても、その 1 行だけ
  捨ててリプレイを続ける (WAL の定石)。

各行は duplicate key と record の基本形を構造検査する。hash chain はなく、任意の
変更に対する真正性を保証するものではない。

knowledge receipt を artifact admission 経路から検査する配線は scope 外である。
"""
from __future__ import annotations

import errno
import fcntl
import hashlib
import json
import math
import os
import stat
import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Callable, Dict, Iterator, List, Mapping, Optional

from .build_admission import (
    BuildAdmissionError,
    BuildAdmissionPolicy,
    HistoricalBuildAdmissionPolicy,
    validate_historical_build_admission_receipt,
    resolve_current_build_admission_policy,
    validate_build_admission_receipt,
)
from . import backoff_hole_grammar
from . import campaign_lock as campaign_lock_codec
from . import env_contract
from .layout import CampaignLayout
from .p3_b4_protocol import (
    B4_PROTOCOL_KEY,
    B4_PROTOCOL_VALUE,
    driver_kind_from_identity,
)
from .model import (
    COMMIT_CONTRACT_SHA256_KEY,
    INCOMPLETE_ATTEMPT_RECOVERY_REASON,
    STAGE_ABORT,
    STAGE_BENCH_DONE,
    STAGE_BUILD_DONE,
    STAGE_BUILD_START,
    STAGE_COMMIT,
    STAGE_VERIFY_DONE,
    WAL_STAGES,
    BuildAttemptState,
    EvalState,
    WalRecord,
)
from . import trigger_gate_binding
from ..verifier.commit_receipt import (
    CAMPAIGN_LOCK_ABSENT_SHA256,
    RECEIPT_PAYLOAD_KEY,
    CommitReceiptError,
    campaign_lock_bytes_sha256,
    validate_serialized_receipt,
    validate_live_campaign_wal_receipt,
)


TRIGGER_BINDING_PAYLOAD_KEY = "trigger_gate_binding"
TRIGGER_BINDING_COMMITMENT_KEY = "trigger_gate_binding_commitment"
TRIGGER_BINDING_SCHEMA_MARKER_KEY = "trigger_gate_binding_schema"
TRIGGER_AXIS = "silo-backoff-trigger-gating"
_TRIGGER_PROPOSAL_INDICATORS = frozenset({"reflux"})
_TRIGGER_MACHINE_GENERATOR = "reason-subset-v1"
_TRIGGER_MACHINE_SPACE = "reason-subsets(effective)+identall+stock"
_SOURCE_NULL_ABORT_REASONS = frozenset({
    "identity-error", "admission-error", "diff-quarantine",
})
_TRIGGER_BINDING_PAYLOAD_KEYS = frozenset({
    "build_attempt_id", TRIGGER_BINDING_PAYLOAD_KEY,
})
_TRIGGER_ORPHAN_RECOVERY_REASON = "recovery-abort-trigger-binding-orphan"
_TRIGGER_ORPHAN_RECOVERY_KEYS = frozenset({"build_attempt_id", "reason"})
_KNOWN_WAL_STAGES = frozenset(WAL_STAGES) | {
    trigger_gate_binding.WAL_RECORD_STAGE,
}
_ATTEMPT_SCHEMA_KEYS = frozenset({
    "build_attempt_id",
    "build_admission",
    "build_admission_receipt_sha256",
    TRIGGER_BINDING_COMMITMENT_KEY,
})
INCOMPLETE_ATTEMPT_RECOVERY_LIMIT = 3
_LEGACY_ENVIRONMENT_CONTRACT_SEARCH_KEY = "environment_contract_sha256"
_A1_BALANCED5_PAIRING_DESIGN = "balanced-a5b5-b5a5-v1"
KNOWLEDGE_PROVENANCE_PAYLOAD_KEY = "knowledge_provenance"
KNOWLEDGE_LEVEL_SEARCH_KEY = "knowledge_level"
KNOWLEDGE_MANIFEST_SHA256_SEARCH_KEY = "knowledge_manifest_sha256"
KNOWLEDGE_RECEIPT_FILENAME = "knowledge_manifest_receipt.json"
_KNOWLEDGE_LEVEL = "K2"
_KNOWLEDGE_RECEIPT_SCHEMA_V1 = "knowledge-manifest-receipt/v1"
_KNOWLEDGE_RECEIPT_SCHEMA_V2 = "knowledge-manifest-receipt/v2"
_KNOWLEDGE_DATA_BOUNDARY = "external_knowledge_is_data_not_instructions"
_A1_NON_CERTIFYING_IDENTITIES = frozenset({
    (
        "paper-story-a1-paired-campaign/v1",
        "paper-story-a1-20260826-sized-v1",
        "arm-grouped-positional-v1",
    ),
    (
        "paper-story-a1-paired-campaign/v2",
        "paper-story-a1-20260901-balanced5-pilot-v1",
        _A1_BALANCED5_PAIRING_DESIGN,
    ),
    (
        "paper-story-a1-paired-campaign/v2",
        "paper-story-a1-20260901-balanced5-sized-v1",
        _A1_BALANCED5_PAIRING_DESIGN,
    ),
})
_A1_BALANCED5_INTERRUPTED_ATTEMPT_INVALID_REASON = (
    "a1-balanced5-interrupted-attempt-invalid"
)
_A1_IO_LAYOUT: ContextVar[str | None] = ContextVar(
    "izanagi_a1_non_certifying_wal_layout", default=None,
)


def _has_exact_a1_non_certifying_marker(decoded: object) -> bool:
    if type(decoded) is not campaign_lock_codec.DecodedNonCertifyingCampaignLock:
        return False
    identity = decoded.identity
    search = identity.get("search_config") if type(identity) is dict else None
    study_id = search.get("study_id") if type(search) is dict else None
    return (
        type(search) is dict
        and (
            search.get("schema"),
            study_id,
            search.get("pairing_design"),
        ) in _A1_NON_CERTIFYING_IDENTITIES
        and search.get("formal") is False
        and search.get("promotion_prohibited") is True
        and search.get("non_certifying_mode")
        == "registered-formal-non-certifying"
        and identity.get("trial") == study_id
    )


def _has_exact_a1_balanced5_marker(decoded: object) -> bool:
    if type(decoded) is not campaign_lock_codec.DecodedNonCertifyingCampaignLock:
        return False
    if not _has_exact_a1_non_certifying_marker(decoded):
        return False
    search = decoded.identity["search_config"]
    return search.get("pairing_design") == _A1_BALANCED5_PAIRING_DESIGN


@contextmanager
def a1_non_certifying_io(layout: CampaignLayout):
    """loop の exact A-1 marker 区間だけ dedicated append を有効にする。"""
    decoded = _campaign_lock_value(layout, allow_a1_non_certifying=True)
    if not _has_exact_a1_non_certifying_marker(decoded):
        raise AttemptTopologyError("A-1 non-certifying WAL marker が不正")
    token = _A1_IO_LAYOUT.set(os.fspath(layout.root))
    try:
        yield
    finally:
        _A1_IO_LAYOUT.reset(token)


# ---- シリアライズ ----

class WalLineError(ValueError):
    """WAL 1 行が record 契約を満たさない。"""


class WalDuplicateKeyError(WalLineError):
    """WAL の JSON object に duplicate key がある。"""


class WalFramingError(WalLineError):
    """WAL に newline 終端の無い最終 frame がある。"""


class WalPayloadTypeError(WalLineError):
    """payload の値が WAL の JSON-native 型契約を満たさない。"""

    def __init__(self, message: str, path: Optional[str] = None):
        super().__init__(message)
        self.path = path


class WalAppendError(RuntimeError):
    """WAL 追記の末尾 gate / write / fsync / close が失敗した。"""

    def __init__(self, wal_path: str, total_bytes: int, written_bytes: int,
                 phase: str, cause: BaseException):
        if phase not in {"tail-gate", "write", "fsync", "close"}:
            raise ValueError("unknown WAL append phase: %r" % phase)
        super().__init__(
            "WAL append failed during %s (%d/%d bytes): %s"
            % (phase, written_bytes, total_bytes, cause)
        )
        self.wal_path = wal_path
        self.total_bytes = total_bytes
        self.written_bytes = written_bytes
        self.phase = phase
        self.cause = cause


class AttemptTopologyError(ValueError):
    """Admission-aware WAL records do not form attempt-local transactions."""


class InterruptedAttemptRecoveryError(RuntimeError):
    """An explicit resume cannot safely terminate an interrupted attempt."""

    def __init__(
            self, *, condition: str, variant: str, attempt_ids: tuple[str, ...],
            detail: str,
    ):
        if type(condition) is not str or not condition:
            raise TypeError("condition は non-empty str が必要")
        if type(variant) is not str or not variant:
            raise TypeError("variant は non-empty str が必要")
        if (type(attempt_ids) is not tuple or not attempt_ids
                or any(type(item) is not str or not item for item in attempt_ids)):
            raise TypeError("attempt_ids は non-empty str の tuple が必要")
        self.condition = condition
        self.variant = variant
        self.attempt_ids = attempt_ids
        self.attempt_id = attempt_ids[0]
        self.detail = detail
        super().__init__(
            "interrupted attempt recovery blocked: "
            f"condition={condition} variant={variant} "
            f"attempts={','.join(attempt_ids)} detail={detail}"
        )


@dataclass(frozen=True)
class WalTailRepairResult:
    status: str
    original_size: int
    final_size: int
    removed_bytes: int
    removed_sha256: Optional[str]
    preview: str
    receipt_path: Optional[str]


@dataclass(frozen=True)
class OrderedAttemptFrame:
    """One physical WAL frame belonging to a build attempt.

    ``byte_start`` and ``byte_end`` are offsets in ``layout.wal_file`` and
    include the frame's terminating LF.  ``raw_bytes`` is therefore exactly
    ``source_wal_bytes[byte_start:byte_end]`` rather than a reserialization of
    :attr:`record`.
    """

    line_number: int
    byte_start: int
    byte_end: int
    raw_bytes: bytes
    record: WalRecord


def _reject_duplicate_keys(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise WalDuplicateKeyError("duplicate key in WAL JSON object: %r" % key)
        value[key] = item
    return value


def _reject_json_constant(value: str):
    raise WalPayloadTypeError(
        "non-finite JSON constant is not allowed: %s" % value,
        path=None,
    )


def _payload_path(parent: str, item) -> str:
    if isinstance(item, int):
        return "%s[%d]" % (parent, item)
    return "%s[%s]" % (parent, json.dumps(item, ensure_ascii=True))


def _validate_string(value: str, path: str) -> None:
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise WalPayloadTypeError(
            "lone surrogate is not allowed in WAL payload at %s" % path,
            path=path,
        )


def _validate_payload(value, path: str = "payload",
                      active: Optional[set[int]] = None) -> None:
    """JSON-native/finite payload を深部まで検査する。

    container の active recursion stack だけを cycle とし、共有 DAG は許容する。
    """
    if active is None:
        active = set()
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, str):
        _validate_string(value, path)
        return
    if isinstance(value, int):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise WalPayloadTypeError(
                "non-finite float is not allowed in WAL payload at %s" % path,
                path=path,
            )
        return
    if isinstance(value, (dict, list)):
        identity = id(value)
        if identity in active:
            raise WalPayloadTypeError(
                "cycle is not allowed in WAL payload at %s" % path,
                path=path,
            )
        active.add(identity)
        try:
            if isinstance(value, dict):
                for key, item in value.items():
                    # key 型と文字列内容は別の防壁: isinstance 後も surrogate を検査する。
                    if not isinstance(key, str):
                        key_path = "%s[<key>]" % path
                        raise WalPayloadTypeError(
                            "WAL payload object key must be a string at %s"
                            % key_path,
                            path=key_path,
                        )
                    key_path = _payload_path(path, key)
                    _validate_string(key, key_path)
                    _validate_payload(item, key_path, active)
            else:
                for index, item in enumerate(value):
                    _validate_payload(item, _payload_path(path, index), active)
        finally:
            active.remove(identity)
        return
    raise WalPayloadTypeError(
        "unsupported WAL payload type %s at %s"
        % (type(value).__name__, path),
        path=path,
    )


def parse_line(line: str) -> WalRecord:
    """WAL 1 行を duplicate-aware に parse し、基本 record 契約を検査する。

    stage は generic WAL 白名簿で fail-closed に検査する。event topology と
    payload object 内の個別 schema は consumer 側の責務。
    空行は writer が生成しないため、record として受理しない。
    """
    if not line.strip():
        raise WalLineError("WAL line must not be empty")
    value = json.loads(
        line,
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_json_constant,
    )
    if not isinstance(value, dict):
        raise WalLineError("WAL record must be a JSON object")
    required = {"variant", "stage", "env_tag", "ts", "payload"}
    if set(value) != required:
        missing = sorted(required - set(value))
        unknown = sorted(set(value) - required)
        raise WalLineError(
            "WAL record keys must be exactly %r (missing=%r, unknown=%r)"
            % (sorted(required), missing, unknown)
        )
    if not isinstance(value["variant"], str):
        raise WalLineError("WAL variant must be a string")
    if not isinstance(value["stage"], str):
        raise WalLineError("WAL stage must be a string")
    if value["stage"] not in _KNOWN_WAL_STAGES:
        raise WalLineError("unknown WAL stage: %r" % value["stage"])
    if not isinstance(value["env_tag"], str):
        raise WalLineError("WAL env_tag must be a string")
    ts = value["ts"]
    if (isinstance(ts, bool) or not isinstance(ts, (int, float))
            or (isinstance(ts, float) and not math.isfinite(ts))):
        raise WalLineError("WAL ts must be a finite number other than bool")
    if not isinstance(value["payload"], dict):
        raise WalLineError("WAL payload must be a JSON object")
    _validate_payload(value["payload"])
    return WalRecord(
        variant=value["variant"], stage=value["stage"], env_tag=value["env_tag"],
        ts=ts, payload=value["payload"],
    )


def _record_to_line(r: WalRecord) -> str:
    if not isinstance(r.variant, str):
        raise WalLineError("WAL variant must be a string")
    if not isinstance(r.stage, str):
        raise WalLineError("WAL stage must be a string")
    if r.stage not in _KNOWN_WAL_STAGES:
        raise WalLineError("unknown WAL stage: %r" % r.stage)
    if not isinstance(r.env_tag, str):
        raise WalLineError("WAL env_tag must be a string")
    if (isinstance(r.ts, bool) or not isinstance(r.ts, (int, float))
            or (isinstance(r.ts, float) and not math.isfinite(r.ts))):
        raise WalLineError("WAL ts must be a finite number other than bool")
    if not isinstance(r.payload, dict):
        raise WalPayloadTypeError(
            "WAL payload root must be a JSON object at payload", path="payload",
        )
    _validate_payload(r.payload)
    obj = {"variant": r.variant, "stage": r.stage, "env_tag": r.env_tag,
           "ts": r.ts, "payload": r.payload}
    return json.dumps(
        obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False,
    )


def _line_to_record(line: str) -> WalRecord:
    return parse_line(line)


def _iter_binary_frames(
        path: str | os.PathLike[str],
) -> Iterator[tuple[int, bytes, bool, bool]]:
    """``(line_number, bytes, is_last, terminated)`` を byte 単位で返す。"""
    with open(path, "rb") as stream:
        current = stream.readline()
        line_number = 1
        while current:
            following = stream.readline()
            yield (line_number, current, not following,
                   current.endswith(b"\n"))
            current = following
            line_number += 1


def iter_lines(path: str | os.PathLike[str]) -> Iterator[tuple[int, str, bool]]:
    """WAL の全物理行を ``(行番号, text, 最終物理行か)`` として返す。

    空行を含めて一行も省略しない。各 consumer は :func:`parse_line` を通すことで
    同じ空行・record 契約を適用する。
    """
    for line_number, frame, is_last, terminated in _iter_binary_frames(path):
        if not terminated:
            raise WalFramingError(
                "WAL line %d is not newline-terminated" % line_number
            )
        yield line_number, frame.decode("utf-8"), is_last


# ---- 追記 (D) ----

def _append_error(layout: CampaignLayout, total: int, written: int,
                  phase: str, cause: BaseException) -> WalAppendError:
    return WalAppendError(
        os.fspath(layout.wal_file), total, written, phase, cause,
    )


def _consumed_commit_receipt_ids(fd: int, size: int) -> set[str]:
    """Read the ledger held by ``fd`` and return durable receipt IDs."""
    if size == 0:
        return set()
    raw = os.pread(fd, size, 0)
    if len(raw) != size:
        raise CommitReceiptError("WAL changed while scanning commit receipts")
    consumed: set[str] = set()
    for frame in raw.splitlines(keepends=True):
        if not frame.endswith(b"\n"):
            raise WalFramingError(
                "WAL tail is not newline-terminated; explicit repair required")
        parsed = parse_line(frame.decode("utf-8"))
        receipt = parsed.payload.get(RECEIPT_PAYLOAD_KEY)
        if receipt is None:
            continue
        if type(receipt) is not dict or type(receipt.get("receipt_id")) is not str:
            raise CommitReceiptError("stored commit receipt is malformed")
        receipt_id = receipt["receipt_id"]
        if receipt_id in consumed:
            raise CommitReceiptError("stored commit receipt is duplicated")
        consumed.add(receipt_id)
    return consumed


def _decode_lock_for_b4_classification(
        layout: CampaignLayout, *, allow_a1_non_certifying: bool = False,
):
    """Return one raw/decoded snapshot, rejecting an unreadable lock."""
    if not os.path.lexists(layout.lock_file):
        return None, None
    try:
        with open(layout.lock_file, "rb") as stream:
            raw = stream.read()
        text = raw.decode("utf-8")
        decoded = (
            campaign_lock_codec.decode_non_certifying_campaign_lock(text)
            if allow_a1_non_certifying
            else campaign_lock_codec.decode_campaign_lock(text)
        )
        return raw, decoded
    except (
        OSError,
        UnicodeDecodeError,
        campaign_lock_codec.CampaignLockCodecError,
    ) as exc:
        from .p3_b4_launcher import B4LauncherAuthorizationError
        raise B4LauncherAuthorizationError(
            "existing campaign lock cannot classify the B-4 protocol"
        ) from exc


def _has_exact_b4_protocol_marker(decoded) -> bool:
    """Classify one already validated campaign lock."""
    if decoded is None:
        return False
    try:
        identity = decoded.identity
    except (AttributeError, KeyError, TypeError) as exc:
        from .p3_b4_launcher import B4LauncherAuthorizationError
        raise B4LauncherAuthorizationError(
            "existing campaign lock cannot classify the B-4 protocol"
        ) from exc
    if type(identity) is not dict:
        from .p3_b4_launcher import B4LauncherAuthorizationError
        raise B4LauncherAuthorizationError(
            "existing campaign lock cannot classify the B-4 protocol"
        )
    if "search_config" not in identity:
        return False
    search_config = identity["search_config"]
    if type(search_config) is not dict:
        from .p3_b4_launcher import B4LauncherAuthorizationError
        raise B4LauncherAuthorizationError(
            "existing campaign lock cannot classify the B-4 protocol"
        )
    return (
        search_config.get(B4_PROTOCOL_KEY) == B4_PROTOCOL_VALUE
    )


def _b4_classification_fields(decoded):
    """Extract required lock fields without leaking raw shape errors."""
    try:
        identity = decoded.identity
        search_config = identity["search_config"]
    except (AttributeError, KeyError, TypeError) as exc:
        from .p3_b4_launcher import B4LauncherAuthorizationError
        raise B4LauncherAuthorizationError(
            "existing campaign lock cannot classify the B-4 protocol"
        ) from exc
    if type(identity) is not dict or type(search_config) is not dict:
        from .p3_b4_launcher import B4LauncherAuthorizationError
        raise B4LauncherAuthorizationError(
            "existing campaign lock cannot classify the B-4 protocol"
        )
    return identity, search_config


def _b4_driver_kind_from_lock(decoded):
    identity, search_config = _b4_classification_fields(decoded)
    try:
        search_tag = identity["search_tag"]
        trial = identity["trial"]
    except KeyError as exc:
        from .p3_b4_launcher import B4LauncherAuthorizationError
        raise B4LauncherAuthorizationError(
            "existing campaign lock cannot classify the B-4 protocol"
        ) from exc
    driver_kind = driver_kind_from_identity(
        search_tag=search_tag,
        trial=trial,
        axis=search_config.get("axis"),
    )
    if driver_kind is None:
        from .p3_b4_launcher import B4LauncherAuthorizationError
        raise B4LauncherAuthorizationError(
            "B-4 campaign lock driver kind is invalid"
        )
    return driver_kind


def _b4_campaign_id_from_lock(decoded) -> str:
    """Derive the canonical campaign id from one decoded lock identity."""
    identity, _search_config = _b4_classification_fields(decoded)
    try:
        trial = identity["trial"]
        search_tag = identity["search_tag"]
        identity_preimage = decoded.identity_preimage
    except (AttributeError, KeyError, TypeError) as exc:
        from .p3_b4_launcher import B4LauncherAuthorizationError
        raise B4LauncherAuthorizationError(
            "existing campaign lock cannot derive the B-4 campaign id"
        ) from exc
    if (
        type(trial) is not str
        or not trial
        or type(search_tag) is not str
        or not search_tag
        or type(identity_preimage) is not str
        or not identity_preimage
    ):
        from .p3_b4_launcher import B4LauncherAuthorizationError
        raise B4LauncherAuthorizationError(
            "existing campaign lock cannot derive the B-4 campaign id"
        )
    cfg_hash8 = hashlib.sha256(identity_preimage.encode("utf-8")).hexdigest()[:8]
    from .ident import CampaignId
    return str(CampaignId(
        slug=trial,
        search_tag=search_tag,
        cfg_hash8=cfg_hash8,
    ))


def _knowledge_lock_binding(campaign_lock: object) -> Optional[tuple[str, str]]:
    """Return the exact K2 lock binding, rejecting a partial declaration."""
    identity = _campaign_lock_identity(campaign_lock)
    search = identity.get("search_config") if type(identity) is dict else None
    if type(search) is not dict:
        return None
    has_level = KNOWLEDGE_LEVEL_SEARCH_KEY in search
    has_digest = KNOWLEDGE_MANIFEST_SHA256_SEARCH_KEY in search
    if has_level != has_digest:
        raise AttemptTopologyError(
            "campaign.lock knowledge key が片方だけ存在する"
        )
    if not has_level:
        return None
    level = search[KNOWLEDGE_LEVEL_SEARCH_KEY]
    digest = search[KNOWLEDGE_MANIFEST_SHA256_SEARCH_KEY]
    if level != _KNOWLEDGE_LEVEL:
        raise AttemptTopologyError("campaign.lock knowledge_level は K2 が必要")
    if (type(digest) is not str or len(digest) != 64
            or any(ch not in "0123456789abcdef" for ch in digest)):
        raise AttemptTopologyError(
            "campaign.lock knowledge_manifest_sha256 が lowercase SHA-256 でない"
        )
    return level, digest


def _knowledge_exact_object(
        value: object, expected: set[str], path: str,
) -> dict:
    if type(value) is not dict:
        raise AttemptTopologyError(f"{path} は exact object が必要")
    if set(value) != expected:
        raise AttemptTopologyError(
            f"{path} の exact key 集合が不正: "
            f"missing={sorted(expected - set(value))!r} "
            f"unknown={sorted(set(value) - expected)!r}"
        )
    return value


def _knowledge_sha256(value: object, path: str) -> str:
    if (type(value) is not str or len(value) != 64
            or any(ch not in "0123456789abcdef" for ch in value)):
        raise AttemptTopologyError(f"{path} が lowercase SHA-256 でない")
    return value


def _knowledge_source(value: object, path: str) -> dict:
    source = _knowledge_exact_object(
        value, {"kind", "identity", "sha256"}, path,
    )
    if source["kind"] != "repo_artifact":
        raise AttemptTopologyError(f"{path}.kind は repo_artifact が必要")
    identity = _knowledge_exact_object(
        source["identity"], {"commit", "path"}, path + ".identity",
    )
    commit = identity["commit"]
    source_path = identity["path"]
    if (type(commit) is not str or len(commit) != 40
            or any(ch not in "0123456789abcdef" for ch in commit)):
        raise AttemptTopologyError(f"{path}.identity.commit が lowercase 40 hex でない")
    if type(source_path) is not str or not source_path:
        raise AttemptTopologyError(f"{path}.identity.path が空または非 string")
    segments = source_path.split("/")
    if (source_path.startswith("/") or "\\" in source_path
            or "\x00" in source_path
            or any(segment in {"", ".", ".."} for segment in segments)):
        raise AttemptTopologyError(
            f"{path}.identity.path が canonical repo-relative POSIX path でない"
        )
    sha256 = _knowledge_sha256(source["sha256"], path + ".sha256")
    return {
        "kind": "repo_artifact",
        "identity": {"commit": commit, "path": source_path},
        "sha256": sha256,
    }


def _knowledge_scope_entries(value: object, path: str) -> list[dict]:
    if type(value) is not list or not value:
        raise AttemptTopologyError(f"{path} は非空 array が必要")
    entries: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for index, raw_entry in enumerate(value):
        entry_path = f"{path}[{index}]"
        entry = _knowledge_exact_object(
            raw_entry, {"kind", "selector"}, entry_path,
        )
        kind = entry["kind"]
        selector = entry["selector"]
        if kind not in {"repo_artifact", "web"}:
            raise AttemptTopologyError(
                f"{entry_path}.kind は repo_artifact または web が必要"
            )
        if type(selector) is not str or not selector:
            raise AttemptTopologyError(
                f"{entry_path}.selector は空でない string が必要"
            )
        key = (kind, selector)
        if key in seen:
            raise AttemptTopologyError(f"{entry_path} が重複している")
        seen.add(key)
        entries.append({"kind": kind, "selector": selector})
    entries.sort(key=lambda item: json.dumps(
        item, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8"))
    return entries


def _knowledge_declared_scope(value: object, path: str) -> dict:
    scope = _knowledge_exact_object(
        value, {"retrieval", "injection"}, path,
    )
    return {
        "retrieval": _knowledge_scope_entries(
            scope["retrieval"], path + ".retrieval",
        ),
        "injection": _knowledge_scope_entries(
            scope["injection"], path + ".injection",
        ),
    }


def _knowledge_retrieval_result(value: object, path: str) -> dict:
    result = _knowledge_exact_object(
        value, {"status", "result_count"}, path,
    )
    status = result["status"]
    count = result["result_count"]
    if status not in {"completed_empty", "completed_nonempty"}:
        raise AttemptTopologyError(f"{path}.status が閉集合外")
    if type(count) is not int or count < 0:
        raise AttemptTopologyError(f"{path}.result_count は 0 以上の exact integer が必要")
    if (status == "completed_empty") != (count == 0):
        raise AttemptTopologyError(
            f"{path} は completed_empty と result_count=0 が同値でなければならない"
        )
    return {"status": status, "result_count": count}


_KNOWLEDGE_FIELD_ABSENT = object()


def _knowledge_manifest_digest(
        level: object, raw_sources: object, *,
        declared_scope: object = _KNOWLEDGE_FIELD_ABSENT,
        retrieval_result: object = _KNOWLEDGE_FIELD_ABSENT,
) -> tuple[str, list[dict]]:
    if level != _KNOWLEDGE_LEVEL:
        raise AttemptTopologyError("knowledge provenance level は K2 が必要")
    if type(raw_sources) is not list:
        raise AttemptTopologyError("knowledge provenance sources は array が必要")
    extended = (
        declared_scope is not _KNOWLEDGE_FIELD_ABSENT
        or retrieval_result is not _KNOWLEDGE_FIELD_ABSENT
    )
    if not raw_sources and not extended:
        raise AttemptTopologyError("knowledge provenance sources は非空 array が必要")
    checked_scope = (
        _knowledge_declared_scope(declared_scope, "knowledge declared_scope")
        if declared_scope is not _KNOWLEDGE_FIELD_ABSENT else None
    )
    checked_result = (
        _knowledge_retrieval_result(
            retrieval_result, "knowledge retrieval_result",
        )
        if retrieval_result is not _KNOWLEDGE_FIELD_ABSENT else None
    )
    if not raw_sources and (checked_scope is None or checked_result is None):
        raise AttemptTopologyError(
            "空の knowledge sources には declared_scope と retrieval_result が必要"
        )
    if (
        not raw_sources
        and checked_result is not None
        and checked_result["status"] != "completed_empty"
    ):
        raise AttemptTopologyError(
            "空の knowledge sources には completed_empty が必要"
        )
    sources: list[dict] = []
    identities: set[tuple[str, str, str]] = set()
    for index, raw_source in enumerate(raw_sources):
        source = _knowledge_source(raw_source, f"knowledge sources[{index}]")
        identity = source["identity"]
        key = (source["kind"], identity["commit"], identity["path"])
        if key in identities:
            raise AttemptTopologyError("knowledge provenance source identity が重複している")
        identities.add(key)
        sources.append(source)
    sources.sort(key=lambda item: json.dumps(
        item, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8"))
    manifest = {"knowledge_level": _KNOWLEDGE_LEVEL, "sources": sources}
    if checked_scope is not None:
        manifest["declared_scope"] = checked_scope
    if checked_result is not None:
        manifest["retrieval_result"] = checked_result
    canonical = json.dumps(
        manifest,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest(), sources


def _checked_knowledge_provenance(
        value: object, *, expected_level: str, expected_digest: str,
) -> dict:
    if type(value) is not dict:
        raise AttemptTopologyError("knowledge_provenance は exact object が必要")
    base_keys = {"knowledge_level", "knowledge_manifest_sha256", "sources"}
    extension_keys = {"declared_scope", "retrieval_result"}
    actual_keys = set(value)
    if not base_keys <= actual_keys or actual_keys - base_keys - extension_keys:
        raise AttemptTopologyError(
            "knowledge_provenance の exact key 集合が不正: "
            f"missing={sorted(base_keys - actual_keys)!r} "
            f"unknown={sorted(actual_keys - base_keys - extension_keys)!r}"
        )
    provenance = value
    level = provenance["knowledge_level"]
    stated_digest = _knowledge_sha256(
        provenance["knowledge_manifest_sha256"],
        "knowledge_provenance.knowledge_manifest_sha256",
    )
    digest_kwargs = {
        key: provenance[key]
        for key in ("declared_scope", "retrieval_result")
        if key in provenance
    }
    derived_digest, sources = _knowledge_manifest_digest(
        level, provenance["sources"], **digest_kwargs,
    )
    if level != expected_level:
        raise AttemptTopologyError(
            "knowledge_provenance knowledge_level が campaign.lock と不一致"
        )
    if stated_digest != expected_digest or derived_digest != expected_digest:
        raise AttemptTopologyError(
            "knowledge_provenance source 集合の manifest digest が campaign.lock と不一致"
        )
    checked = {
        "knowledge_level": level,
        "knowledge_manifest_sha256": stated_digest,
        "sources": sources,
    }
    if "declared_scope" in provenance:
        checked["declared_scope"] = _knowledge_declared_scope(
            provenance["declared_scope"],
            "knowledge_provenance.declared_scope",
        )
    if "retrieval_result" in provenance:
        checked["retrieval_result"] = _knowledge_retrieval_result(
            provenance["retrieval_result"],
            "knowledge_provenance.retrieval_result",
        )
    return checked


def _read_knowledge_receipt_with_sha256(
        layout: CampaignLayout,
) -> tuple[object, str]:
    path = os.path.join(layout.root, KNOWLEDGE_RECEIPT_FILENAME)
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        fd = os.open(path, flags)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                raise OSError(errno.EINVAL, "knowledge receipt is not regular")
            raw = bytearray()
            while True:
                chunk = os.read(fd, 65536)
                if not chunk:
                    break
                raw.extend(chunk)
        finally:
            os.close(fd)
        receipt_bytes = bytes(raw)
        text = receipt_bytes.decode("utf-8")
        decoded = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_json_constant,
        )
        canonical = (json.dumps(
            decoded,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ) + "\n").encode("utf-8")
        if receipt_bytes != canonical:
            raise AttemptTopologyError("knowledge receipt bytes が canonical でない")
        return decoded, hashlib.sha256(receipt_bytes).hexdigest()
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        WalLineError,
    ) as exc:
        raise AttemptTopologyError(
            "knowledge-aware BUILD_START の receipt を読めない"
        ) from exc


def _read_knowledge_receipt(layout: CampaignLayout) -> object:
    receipt, _receipt_sha256 = _read_knowledge_receipt_with_sha256(layout)
    return receipt


def _validated_knowledge_receipt(
        value: object, *, expected_level: str, expected_digest: str,
) -> tuple[dict, list[dict]]:
    """Return canonical provenance and verified sources as separate values."""
    receipt = _knowledge_exact_object(
        value,
        {
            "schema_version", "knowledge_level", "knowledge_manifest_sha256",
            "canonical_manifest", "sources", "planner_projection",
            "claim_boundary", "declaration_status",
        },
        "knowledge receipt",
    )
    schema_version = receipt["schema_version"]
    if schema_version not in {
        _KNOWLEDGE_RECEIPT_SCHEMA_V1,
        _KNOWLEDGE_RECEIPT_SCHEMA_V2,
    }:
        raise AttemptTopologyError("knowledge receipt schema_version が不正")
    level = receipt["knowledge_level"]
    stated_digest = _knowledge_sha256(
        receipt["knowledge_manifest_sha256"],
        "knowledge receipt.knowledge_manifest_sha256",
    )
    raw_canonical_manifest = receipt["canonical_manifest"]
    if schema_version == _KNOWLEDGE_RECEIPT_SCHEMA_V1:
        canonical_manifest = _knowledge_exact_object(
            raw_canonical_manifest, {"knowledge_level", "sources"},
            "knowledge receipt.canonical_manifest",
        )
    else:
        if type(raw_canonical_manifest) is not dict:
            raise AttemptTopologyError(
                "knowledge receipt.canonical_manifest は exact object が必要"
            )
        base_keys = {"knowledge_level", "sources"}
        extension_keys = {"declared_scope", "retrieval_result"}
        canonical_keys = set(raw_canonical_manifest)
        if (
            not base_keys <= canonical_keys
            or canonical_keys - base_keys - extension_keys
            or not canonical_keys & extension_keys
        ):
            raise AttemptTopologyError(
                "knowledge receipt.canonical_manifest の v2 key 集合が不正"
            )
        canonical_manifest = raw_canonical_manifest
    digest_kwargs = {
        key: canonical_manifest[key]
        for key in ("declared_scope", "retrieval_result")
        if key in canonical_manifest
    }
    derived_digest, canonical_sources = _knowledge_manifest_digest(
        canonical_manifest["knowledge_level"], canonical_manifest["sources"],
        **digest_kwargs,
    )
    if canonical_manifest["sources"] != canonical_sources:
        raise AttemptTopologyError("knowledge receipt canonical sources の順序が不正")
    if "declared_scope" in canonical_manifest:
        canonical_scope = _knowledge_declared_scope(
            canonical_manifest["declared_scope"],
            "knowledge receipt.canonical_manifest.declared_scope",
        )
        if canonical_manifest["declared_scope"] != canonical_scope:
            raise AttemptTopologyError(
                "knowledge receipt canonical declared_scope の順序が不正"
            )
    if (level != expected_level or canonical_manifest["knowledge_level"] != level
            or stated_digest != expected_digest or derived_digest != expected_digest):
        raise AttemptTopologyError("knowledge receipt と campaign.lock の binding が不一致")

    raw_verified_sources = receipt["sources"]
    if type(raw_verified_sources) is not list or len(raw_verified_sources) != len(
            canonical_sources):
        raise AttemptTopologyError("knowledge receipt verified sources が不正")
    verified_sources: list[dict] = []
    for index, raw_source in enumerate(raw_verified_sources):
        source_with_verification = _knowledge_exact_object(
            raw_source, {"kind", "identity", "sha256", "verification"},
            f"knowledge receipt.sources[{index}]",
        )
        source = _knowledge_source(
            {key: source_with_verification[key]
             for key in ("kind", "identity", "sha256")},
            f"knowledge receipt.sources[{index}]",
        )
        verification = _knowledge_exact_object(
            source_with_verification["verification"],
            {"method", "status", "observed_sha256"},
            f"knowledge receipt.sources[{index}].verification",
        )
        observed = _knowledge_sha256(
            verification["observed_sha256"],
            f"knowledge receipt.sources[{index}].verification.observed_sha256",
        )
        if (verification["method"] != "git-blob-at-commit-path"
                or verification["status"] != "verified"
                or observed != source["sha256"]):
            raise AttemptTopologyError("knowledge receipt source verification が不正")
        verified_sources.append(source)
    if verified_sources != canonical_sources:
        raise AttemptTopologyError(
            "knowledge receipt canonical manifest と verified sources が不一致"
        )

    planner = _knowledge_exact_object(
        receipt["planner_projection"], {"payload_key", "data_boundary"},
        "knowledge receipt.planner_projection",
    )
    if planner != {
        "payload_key": "knowledge_input",
        "data_boundary": _KNOWLEDGE_DATA_BOUNDARY,
    }:
        raise AttemptTopologyError("knowledge receipt planner_projection 宣言が不正")
    claim = _knowledge_exact_object(
        receipt["claim_boundary"],
        {"classification", "de_novo_claim", "pilot_comparison_eligible"},
        "knowledge receipt.claim_boundary",
    )
    if (type(claim["classification"]) is not str or not claim["classification"]
            or type(claim["de_novo_claim"]) is not bool
            or claim["pilot_comparison_eligible"] is not False):
        raise AttemptTopologyError("knowledge receipt claim_boundary 宣言が不正")
    provenance = {
        "knowledge_level": level,
        "knowledge_manifest_sha256": stated_digest,
        "sources": canonical_sources,
    }
    if "declared_scope" in canonical_manifest:
        provenance["declared_scope"] = _knowledge_declared_scope(
            canonical_manifest["declared_scope"],
            "knowledge receipt.canonical_manifest.declared_scope",
        )
    if "retrieval_result" in canonical_manifest:
        provenance["retrieval_result"] = _knowledge_retrieval_result(
            canonical_manifest["retrieval_result"],
            "knowledge receipt.canonical_manifest.retrieval_result",
        )
    return provenance, verified_sources


def _knowledge_provenance_from_receipt(
        layout: CampaignLayout, *, expected_level: str, expected_digest: str,
) -> dict:
    provenance, _verified_sources = _validated_knowledge_receipt(
        _read_knowledge_receipt(layout),
        expected_level=expected_level,
        expected_digest=expected_digest,
    )
    return provenance


def validate_knowledge_provenance_bindings(
        records: List[WalRecord], *, campaign_lock: object,
) -> None:
    """Validate every knowledge-aware BUILD_START from WAL bytes and lock."""
    expected = _knowledge_lock_binding(campaign_lock)
    if expected is None:
        for record in records:
            if KNOWLEDGE_PROVENANCE_PAYLOAD_KEY in record.payload:
                raise AttemptTopologyError(
                    "knowledge-unaware campaign の WAL に knowledge_provenance がある"
                )
        return
    expected_level, expected_digest = expected
    for record in records:
        present = KNOWLEDGE_PROVENANCE_PAYLOAD_KEY in record.payload
        if record.stage != STAGE_BUILD_START:
            if present:
                raise AttemptTopologyError(
                    "knowledge_provenance は BUILD_START 以外へ置けない"
                )
            continue
        if not present:
            raise AttemptTopologyError(
                "knowledge-aware campaign の BUILD_START に binding が欠落"
            )
        _checked_knowledge_provenance(
            record.payload[KNOWLEDGE_PROVENANCE_PAYLOAD_KEY],
            expected_level=expected_level,
            expected_digest=expected_digest,
        )


def knowledge_provenance_and_receipt_sha256_for_material_report(
        layout: CampaignLayout, records: List[WalRecord], *,
        campaign_lock: object,
) -> Optional[tuple[dict, str]]:
    """Return the receipt projection and digest from the same validated read."""
    expected = _knowledge_lock_binding(campaign_lock)
    validate_knowledge_provenance_bindings(
        records, campaign_lock=campaign_lock,
    )
    if expected is None:
        return None
    expected_level, expected_digest = expected
    receipt, receipt_sha256 = _read_knowledge_receipt_with_sha256(layout)
    provenance, verified_sources = _validated_knowledge_receipt(
        receipt,
        expected_level=expected_level,
        expected_digest=expected_digest,
    )

    def source_projection(source: dict) -> dict:
        return {
            "kind": source["kind"],
            "identity": dict(source["identity"]),
            "sha256": source["sha256"],
        }

    projection = {
        "knowledge_level": provenance["knowledge_level"],
        "knowledge_manifest_sha256": provenance[
            "knowledge_manifest_sha256"
        ],
        "declared_sources": [
            source_projection(source) for source in provenance["sources"]
        ],
        "injected_sources": [
            source_projection(source) for source in verified_sources
        ],
    }
    if "declared_scope" in provenance:
        projection["declared_scope"] = provenance["declared_scope"]
    if "retrieval_result" in provenance:
        projection["retrieval_result"] = provenance["retrieval_result"]
    return projection, receipt_sha256


def knowledge_provenance_for_material_report(
        layout: CampaignLayout, records: List[WalRecord], *,
        campaign_lock: object,
) -> Optional[dict]:
    """Return the receipt-bound two-level projection for a material report."""
    checked = knowledge_provenance_and_receipt_sha256_for_material_report(
        layout, records, campaign_lock=campaign_lock,
    )
    return None if checked is None else checked[0]


def _append_record(
        layout: CampaignLayout, record: WalRecord, *, commit_receipt=None,
        allow_a1_non_certifying: bool = False,
) -> WalRecord:
    """WAL に 1 frame を排他追記し、file/dir を fsync する。"""
    # 拒否された record で directory/file 側の効果を起こさない。
    if record.stage != STAGE_COMMIT and commit_receipt is not None:
        raise CommitReceiptError("commit receipt supplied for non-COMMIT record")
    lock_snapshot = None
    decoded_lock = None
    if (record.stage in {STAGE_BUILD_START, STAGE_COMMIT}
            or allow_a1_non_certifying):
        lock_snapshot, decoded_lock = _decode_lock_for_b4_classification(
            layout, allow_a1_non_certifying=allow_a1_non_certifying,
        )
    if allow_a1_non_certifying and not _has_exact_a1_non_certifying_marker(
            decoded_lock):
        raise AttemptTopologyError("A-1 dedicated append の exact marker が不正")
    if record.stage == STAGE_COMMIT:
        if _has_exact_b4_protocol_marker(decoded_lock):
            from .p3_b4_launcher import verify_b4_launch_context
            search_config = decoded_lock.identity["search_config"]
            verify_b4_launch_context(
                layout,
                expected_driver_kind=_b4_driver_kind_from_lock(decoded_lock),
                expected_campaign_id=_b4_campaign_id_from_lock(decoded_lock),
                expected_arm=search_config.get("reflux"),
            )
    if record.stage == STAGE_BUILD_START:
        grammar_version = _declared_backoff_grammar_version(decoded_lock)
        if grammar_version is not None:
            key = backoff_hole_grammar.BACKOFF_GRAMMAR_VERSION_KEY
            if (key in record.payload
                    and (type(record.payload[key]) is not int
                         or record.payload[key] != grammar_version)):
                raise AttemptTopologyError(
                    "build_start: backoff grammar version が campaign.lock と不一致"
                )
            record = WalRecord(
                variant=record.variant,
                stage=record.stage,
                env_tag=record.env_tag,
                ts=record.ts,
                payload={**record.payload, key: grammar_version},
            )
        knowledge_binding = _knowledge_lock_binding(decoded_lock)
        if knowledge_binding is None:
            if KNOWLEDGE_PROVENANCE_PAYLOAD_KEY in record.payload:
                raise AttemptTopologyError(
                    "knowledge-unaware campaign の BUILD_START に knowledge_provenance がある"
                )
        else:
            expected_level, expected_digest = knowledge_binding
            provenance = _knowledge_provenance_from_receipt(
                layout,
                expected_level=expected_level,
                expected_digest=expected_digest,
            )
            if KNOWLEDGE_PROVENANCE_PAYLOAD_KEY in record.payload:
                supplied = record.payload[KNOWLEDGE_PROVENANCE_PAYLOAD_KEY]
                checked = _checked_knowledge_provenance(
                    supplied,
                    expected_level=expected_level,
                    expected_digest=expected_digest,
                )
                if checked != provenance:
                    raise AttemptTopologyError(
                        "caller knowledge_provenance が receipt と不一致"
                    )
            record = WalRecord(
                variant=record.variant,
                stage=record.stage,
                env_tag=record.env_tag,
                ts=record.ts,
                payload={
                    **{
                        key: value for key, value in record.payload.items()
                        if key != KNOWLEDGE_PROVENANCE_PAYLOAD_KEY
                    },
                    KNOWLEDGE_PROVENANCE_PAYLOAD_KEY: provenance,
                },
            )
    line = _record_to_line(record) + "\n"
    parse_line(line)
    encoded = line.encode("utf-8")
    total = len(encoded)
    written = 0
    try:
        getattr(layout, "_admit_materialization", lambda: None)()
        os.makedirs(layout.runs_dir, exist_ok=True)
        flags = (os.O_RDWR | os.O_APPEND | os.O_CREAT
                 | os.O_NOFOLLOW | os.O_CLOEXEC)
        fd = os.open(layout.wal_file, flags, 0o644)
    except OSError as exc:
        raise _append_error(layout, total, written, "tail-gate", exc) from exc
    try:
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX)
                info = os.fstat(fd)
                if not stat.S_ISREG(info.st_mode):
                    raise OSError(errno.EINVAL, "WAL is not a regular file")
                if info.st_size and os.pread(fd, 1, info.st_size - 1) != b"\n":
                    raise WalFramingError(
                        "WAL tail is not newline-terminated; explicit repair required"
                    )
            except (OSError, WalFramingError) as exc:
                raise _append_error(
                    layout, total, written, "tail-gate", exc,
                ) from exc

            if record.stage == STAGE_COMMIT:
                lock_identity_sha256 = (
                    campaign_lock_bytes_sha256(lock_snapshot)
                    if lock_snapshot is not None
                    else CAMPAIGN_LOCK_ABSENT_SHA256
                )
                serialized_receipt = validate_live_campaign_wal_receipt(
                    commit_receipt,
                    lock_identity_sha256=lock_identity_sha256,
                    variant=record.variant,
                    terminal_payload=record.payload,
                )
                consumed = _consumed_commit_receipt_ids(fd, info.st_size)
                if serialized_receipt["receipt_id"] in consumed:
                    raise CommitReceiptError(
                        "commit receipt was already consumed by this WAL")
                record = WalRecord(
                    variant=record.variant,
                    stage=record.stage,
                    env_tag=record.env_tag,
                    ts=record.ts,
                    payload={
                        **record.payload,
                        RECEIPT_PAYLOAD_KEY: serialized_receipt,
                    },
                )
                line = _record_to_line(record) + "\n"
                parse_line(line)
                encoded = line.encode("utf-8")
                total = len(encoded)

            while written < total:
                try:
                    count = os.write(fd, encoded[written:])
                except OSError as exc:
                    raise _append_error(
                        layout, total, written, "write", exc,
                    ) from exc
                if count <= 0:
                    exc = OSError(errno.EIO, "os.write made no progress")
                    raise _append_error(
                        layout, total, written, "write", exc,
                    ) from exc
                written += count
            try:
                os.fsync(fd)
            except OSError as exc:
                raise _append_error(
                    layout, total, written, "fsync", exc,
                ) from exc

            # WAL の flock を保持したまま、毎 append で runs dir まで耐久化する。
            try:
                dfd = os.open(
                    layout.runs_dir,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC,
                )
            except OSError as exc:
                raise _append_error(
                    layout, total, written, "fsync", exc,
                ) from exc
            try:
                try:
                    os.fsync(dfd)
                except OSError as exc:
                    raise _append_error(
                        layout, total, written, "fsync", exc,
                    ) from exc
            except BaseException:
                try:
                    os.close(dfd)
                except OSError:
                    pass
                raise
            try:
                os.close(dfd)
            except OSError as exc:
                raise _append_error(
                    layout, total, written, "close", exc,
                ) from exc
        except BaseException:
            # 既存の write/fsync 失敗を close 失敗で覆い隠さない。
            try:
                os.close(fd)
            except OSError:
                pass
            raise
        try:
            os.close(fd)
        except OSError as exc:
            raise _append_error(
                layout, total, written, "close", exc,
            ) from exc
    except BaseException:
        raise
    return record


def append_a1_non_certifying(
        layout: CampaignLayout, record: WalRecord, *, commit_receipt=None,
) -> WalRecord:
    """A-1 non-certifying lock 専用の append entry。"""
    return _append_record(
        layout,
        record,
        commit_receipt=commit_receipt,
        allow_a1_non_certifying=True,
    )


def append(
        layout: CampaignLayout, record: WalRecord, *, commit_receipt=None,
) -> WalRecord:
    """通常 v1/v2 WAL append。A-1 は loop の専用 context だけへ分岐する。"""
    if _A1_IO_LAYOUT.get() == os.fspath(layout.root):
        return append_a1_non_certifying(
            layout, record, commit_receipt=commit_receipt,
        )
    return _append_record(layout, record, commit_receipt=commit_receipt)


def _digest_range(fd: int, start: int, size: int) -> tuple[str, bytes]:
    digest = hashlib.sha256()
    preview = bytearray()
    offset = start
    remaining = size
    while remaining:
        chunk = os.pread(fd, min(65536, remaining), offset)
        if not chunk:
            raise OSError(errno.EIO, "unexpected EOF while scanning WAL")
        digest.update(chunk)
        if len(preview) < 128:
            preview.extend(chunk[:128 - len(preview)])
        offset += len(chunk)
        remaining -= len(chunk)
    return digest.hexdigest(), bytes(preview)


def _last_frame_boundary(fd: int, size: int) -> int:
    offset = size
    while offset:
        start = max(0, offset - 65536)
        chunk = os.pread(fd, offset - start, start)
        if len(chunk) != offset - start:
            raise OSError(errno.EIO, "short pread while scanning WAL")
        newline = chunk.rfind(b"\n")
        if newline >= 0:
            return start + newline + 1
        offset = start
    return 0


def _write_receipt(layout: CampaignLayout, receipt: dict) -> str:
    body = (json.dumps(
        receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ) + "\n").encode("utf-8")
    flags = (os.O_WRONLY | os.O_CREAT | os.O_EXCL
             | os.O_NOFOLLOW | os.O_CLOEXEC)
    for attempt in range(100):
        name = "wal-tail-repair-%d-%d-%d.json" % (
            time.time_ns(), os.getpid(), attempt,
        )
        path = os.path.join(layout.runs_dir, name)
        try:
            fd = os.open(path, flags, 0o600)
            break
        except FileExistsError:
            continue
    else:
        raise OSError(errno.EEXIST, "could not allocate WAL repair receipt")
    try:
        offset = 0
        while offset < len(body):
            count = os.write(fd, body[offset:])
            if count <= 0:
                raise OSError(errno.EIO, "receipt write made no progress")
            offset += count
        os.fsync(fd)
    finally:
        os.close(fd)
    dfd = os.open(
        layout.runs_dir, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC,
    )
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)
    return path


def _repair_truncated_tail(
        layout: CampaignLayout, *, reject_active_attempt: bool = False,
        allow_a1_non_certifying: bool = False,
) -> WalTailRepairResult:
    """newline 終端後の tail だけを証拠 receipt 作成後に切り戻す。"""
    if type(reject_active_attempt) is not bool:
        raise TypeError("reject_active_attempt は exact bool が必要")
    getattr(layout, "_admit_materialization", lambda: None)()
    flags = os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        fd = os.open(layout.wal_file, flags)
    except FileNotFoundError:
        return WalTailRepairResult(
            "missing", 0, 0, 0, None, "", None,
        )
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise OSError(errno.EINVAL, "WAL is not a regular file")
        original_size = info.st_size
        if (original_size == 0
                or os.pread(fd, 1, original_size - 1) == b"\n"):
            return WalTailRepairResult(
                "noop", original_size, original_size, 0, None, "", None,
            )

        final_size = _last_frame_boundary(fd, original_size)
        prefix_records = (
            _read_records_from_locked_fd(fd, final_size) if final_size else []
        )
        validate_commit_contract_bindings(
            prefix_records,
            campaign_lock=_campaign_lock_value(
                layout,
                allow_a1_non_certifying=allow_a1_non_certifying,
            ),
        )
        if reject_active_attempt and final_size:
            if any(
                    _ATTEMPT_SCHEMA_KEYS & frozenset(record.payload)
                    for record in prefix_records):
                active_candidates = _active_attempt_candidates(prefix_records)
                if active_candidates:
                    variant, candidates = next(iter(active_candidates.items()))
                    raise InterruptedAttemptRecoveryError(
                        condition="truncated-tail-with-active-attempt",
                        variant=variant,
                        attempt_ids=tuple(item[0] for item in candidates),
                        detail=("attempt-schema WAL has an active attempt and "
                                "a truncated tail"),
                    )
        removed_bytes = original_size - final_size
        removed_sha256, removed_preview = _digest_range(
            fd, final_size, removed_bytes,
        )
        # binary tail を損失なく、256 byte 相当以下の ASCII で示す。
        preview = removed_preview.hex()
        receipt = {
            "kind": "wal-tail-repair",
            "wal_path": os.fspath(layout.wal_file),
            "cut_offset": final_size,
            "original_size": original_size,
            "final_size": final_size,
            "removed_bytes": removed_bytes,
            "removed_sha256": removed_sha256,
            "preview": preview,
        }
        receipt_path = _write_receipt(layout, receipt)
        os.ftruncate(fd, final_size)
        os.fsync(fd)
        return WalTailRepairResult(
            "repaired", original_size, final_size, removed_bytes,
            removed_sha256, preview, receipt_path,
        )
    finally:
        os.close(fd)


def repair_truncated_tail(
        layout: CampaignLayout, *, reject_active_attempt: bool = False,
) -> WalTailRepairResult:
    """通常 v1/v2 lock の truncated tail を修復する。"""
    return _repair_truncated_tail(
        layout, reject_active_attempt=reject_active_attempt,
    )


def repair_truncated_tail_a1_non_certifying(
        layout: CampaignLayout, *, reject_active_attempt: bool = False,
) -> WalTailRepairResult:
    """A-1 non-certifying lock 専用の truncated tail repair。"""
    return _repair_truncated_tail(
        layout,
        reject_active_attempt=reject_active_attempt,
        allow_a1_non_certifying=True,
    )


def log(layout: CampaignLayout, variant: str, stage: str, env_tag: str,
        payload: Optional[Dict] = None, ts: Optional[float] = None, *,
        commit_receipt=None) -> WalRecord:
    """WalRecord を組んで追記する糖衣。ts 省略時は現在時刻。"""
    rec = WalRecord(variant=variant, stage=stage, env_tag=env_tag,
                    ts=ts if ts is not None else time.time(),
                    payload={} if payload is None else payload)
    return append(layout, rec, commit_receipt=commit_receipt)


def log_trigger_binding(
        layout: CampaignLayout, variant: str, env_tag: str,
        build_attempt_id: str, binding: trigger_gate_binding.TriggerGateBinding, *,
        emit=None,
) -> str:
    """Write one raw trigger binding immediately before its build_start."""
    if type(build_attempt_id) is not str or not build_attempt_id:
        raise trigger_gate_binding.TriggerGateBindingError(
            "invalid trigger gate binding"
        )
    raw = trigger_gate_binding.to_record(binding)
    sink = log if emit is None else emit
    sink(layout, variant, trigger_gate_binding.WAL_RECORD_STAGE, env_tag, {
        "build_attempt_id": build_attempt_id,
        TRIGGER_BINDING_PAYLOAD_KEY: raw,
    })
    return trigger_gate_binding.commitment(binding)


# ---- リプレイ / リカバリ (D, A) ----

def read_records_collected(
        layout: CampaignLayout,
) -> tuple[list[WalRecord], list[tuple[int, str]], bool]:
    """WAL の有効行と行単位 issue、末尾切断の有無を返す。

    ``line_issues`` は ``(物理行番号, 理由)``。終端済みの不正行を除外して
    後続の有効 record も集める。内容によらず newline 無終端の最終 frame だけを
    crash prefix として ``truncated_tail`` へ分離する。
    """
    if not os.path.exists(layout.wal_file):
        return [], [], False
    records: list[WalRecord] = []
    line_issues: list[tuple[int, str]] = []
    truncated_tail = False
    for line_number, frame, _is_last, terminated in _iter_binary_frames(
            layout.wal_file):
        if not terminated:
            truncated_tail = True
            break
        try:
            line = frame.decode("utf-8")
            records.append(_line_to_record(line))
        except (UnicodeDecodeError, json.JSONDecodeError, WalLineError) as exc:
            line_issues.append((
                line_number, f"{type(exc).__name__}: {exc}",
            ))
    return records, line_issues, truncated_tail


def read_records_checked(layout: CampaignLayout) -> tuple[list[WalRecord], bool]:
    """WAL を読み、``(records, truncated_tail)`` を返す。

    内容によらず newline 無終端の最終 frame だけを crash prefix として許容する。
    終端済み frame の decode / JSON / record 契約違反は最終行でも伝播する。
    """
    if not os.path.exists(layout.wal_file):
        return [], False
    out: list[WalRecord] = []
    truncated_tail = False
    for _line_number, frame, _is_last, terminated in _iter_binary_frames(
            layout.wal_file):
        if not terminated:
            truncated_tail = True
            break
        line = frame.decode("utf-8")
        out.append(_line_to_record(line))
    return out, truncated_tail


def read_records(layout: CampaignLayout) -> List[WalRecord]:
    """WAL を全レコード読む。最終行の crash prefix は従来どおり捨てる。"""
    records, _ = read_records_checked(layout)
    return records


def ordered_attempt_frames(
        layout: CampaignLayout, build_attempt_id: str,
) -> tuple[OrderedAttemptFrame, ...]:
    """Return physical frames and byte offsets for one exact attempt.

    Unlike :func:`records_by_stage`, this API neither projects by stage nor
    applies last-wins semantics.  A truncated tail is rejected because its
    byte range cannot be frozen as complete result evidence.
    """

    if type(build_attempt_id) is not str or not build_attempt_id:
        raise TypeError("build_attempt_id must be a non-empty str")
    if not os.path.exists(layout.wal_file):
        return ()

    selected: list[OrderedAttemptFrame] = []
    byte_start = 0
    for line_number, frame, _is_last, terminated in _iter_binary_frames(
            layout.wal_file):
        byte_end = byte_start + len(frame)
        if not terminated:
            raise WalFramingError(
                "WAL line %d is not newline-terminated" % line_number
            )
        try:
            record = _line_to_record(frame.decode("utf-8"))
        except UnicodeDecodeError as exc:
            raise WalLineError(
                "WAL line %d is not valid UTF-8" % line_number
            ) from exc
        if record.payload.get("build_attempt_id") == build_attempt_id:
            selected.append(OrderedAttemptFrame(
                line_number=line_number,
                byte_start=byte_start,
                byte_end=byte_end,
                raw_bytes=frame,
                record=record,
            ))
        byte_start = byte_end
    return tuple(selected)


def _campaign_lock_value(
        layout: CampaignLayout, *, allow_a1_non_certifying: bool = False,
) -> object:
    stored = read_lock(layout)
    if stored is None:
        return None
    try:
        return (
            campaign_lock_codec.decode_non_certifying_campaign_lock(stored)
            if allow_a1_non_certifying
            else campaign_lock_codec.decode_campaign_lock(stored)
        )
    except campaign_lock_codec.CampaignLockCodecError as exc:
        raise AttemptTopologyError(
            "campaign.lock が既知の v1/v2 wire contract を満たさない"
        ) from exc


def _decoded_campaign_lock_value(
        lock_value: object,
) -> Optional[
    campaign_lock_codec.DecodedCampaignLock
    | campaign_lock_codec.DecodedNonCertifyingCampaignLock
]:
    """Normalize a decoded lock or a v2 object supplied by a direct caller.

    WAL file readers always pass a codec-validated ``DecodedCampaignLock``.
    Historical direct unit/helper callers pass an already extracted v1 identity
    dict, sometimes with only the fields relevant to the helper; keep that API
    compatible without weakening the file-reading boundary.
    """
    if lock_value is None:
        return None
    if type(lock_value) is campaign_lock_codec.DecodedCampaignLock:
        return lock_value
    if type(lock_value) is campaign_lock_codec.DecodedNonCertifyingCampaignLock:
        return lock_value
    if type(lock_value) is dict and "schema_version" not in lock_value:
        return None
    if type(lock_value) is not dict:
        raise AttemptTopologyError("campaign.lock value が object でない")
    try:
        encoded = campaign_lock_codec.canonical_json(lock_value)
        return campaign_lock_codec.decode_campaign_lock(encoded)
    except campaign_lock_codec.CampaignLockCodecError as exc:
        raise AttemptTopologyError(
            "campaign.lock が既知の v1/v2 wire contract を満たさない"
        ) from exc


def _campaign_lock_identity(lock_value: object) -> object:
    decoded = _decoded_campaign_lock_value(lock_value)
    if decoded is not None:
        return decoded.identity
    return lock_value


def _declared_backoff_grammar_version(campaign_lock: object) -> Optional[int]:
    """Read an exact positive grammar version only from campaign identity."""

    identity = _campaign_lock_identity(campaign_lock)
    search = identity.get("search_config") if type(identity) is dict else None
    key = backoff_hole_grammar.BACKOFF_GRAMMAR_VERSION_KEY
    if type(search) is not dict or key not in search:
        return None
    version = search.get(key)
    if type(version) is not int or version < 1:
        raise AttemptTopologyError(
            "campaign.lock backoff grammar version が exact positive integer でない"
        )
    return version


def validate_backoff_grammar_bindings(
    records: List[WalRecord], *, campaign_lock: object,
) -> None:
    """Require every BUILD_START to repeat a versioned lock's exact value."""

    expected = _declared_backoff_grammar_version(campaign_lock)
    if expected is None:
        return
    key = backoff_hole_grammar.BACKOFF_GRAMMAR_VERSION_KEY
    for record in records:
        if record.stage != STAGE_BUILD_START:
            continue
        actual = record.payload.get(key)
        if type(actual) is not int or actual != expected:
            raise AttemptTopologyError(
                "build_start: backoff grammar version が欠落または campaign.lock と不一致"
            )


def is_trigger_proposal_campaign_lock(campaign_lock: object) -> bool:
    """Classify proposal-driven trigger campaigns from their search config."""
    identity = _campaign_lock_identity(campaign_lock)
    search = identity.get("search_config") if type(identity) is dict else None
    if type(search) is not dict:
        return False
    if TRIGGER_BINDING_SCHEMA_MARKER_KEY in search:
        return True
    return (
        search.get("axis") == TRIGGER_AXIS
        and any(key in search for key in _TRIGGER_PROPOSAL_INDICATORS)
    )


def is_trigger_machine_campaign_lock(campaign_lock: object) -> bool:
    """Recognize marker-free mechanical trigger enumeration, not proposals."""
    identity = _campaign_lock_identity(campaign_lock)
    search = identity.get("search_config") if type(identity) is dict else None
    return (
        type(search) is dict
        and search.get("axis") == TRIGGER_AXIS
        and TRIGGER_BINDING_SCHEMA_MARKER_KEY not in search
        and not any(key in search for key in _TRIGGER_PROPOSAL_INDICATORS)
        and search.get("generator") == _TRIGGER_MACHINE_GENERATOR
        and search.get("space") == _TRIGGER_MACHINE_SPACE
    )


def _is_trigger_orphan_tombstone(
        binding_record: WalRecord, record: WalRecord,
) -> bool:
    attempt_id = binding_record.payload.get("build_attempt_id")
    return (
        binding_record.stage == trigger_gate_binding.WAL_RECORD_STAGE
        and record.stage == STAGE_ABORT
        and record.variant == binding_record.variant
        and record.env_tag == binding_record.env_tag
        and type(record.payload) is dict
        and frozenset(record.payload) == _TRIGGER_ORPHAN_RECOVERY_KEYS
        and record.payload.get("build_attempt_id") == attempt_id
        and record.payload.get("reason") == _TRIGGER_ORPHAN_RECOVERY_REASON
    )


def _is_trigger_orphan_tombstone_at(
        records: List[WalRecord], index: int,
) -> bool:
    """Accept an exact tombstone, including a concurrent replay duplicate."""
    if not 0 < index < len(records):
        return False
    record = records[index]
    if (record.stage != STAGE_ABORT or type(record.payload) is not dict
            or frozenset(record.payload) != _TRIGGER_ORPHAN_RECOVERY_KEYS
            or record.payload.get("reason") != _TRIGGER_ORPHAN_RECOVERY_REASON):
        return False
    attempt_id = record.payload.get("build_attempt_id")
    previous = index - 1
    while previous >= 0:
        candidate = records[previous]
        if candidate.stage == trigger_gate_binding.WAL_RECORD_STAGE:
            return _is_trigger_orphan_tombstone(candidate, record)
        if (candidate.stage != STAGE_ABORT
                or candidate.variant != record.variant
                or candidate.env_tag != record.env_tag
                or type(candidate.payload) is not dict
                or frozenset(candidate.payload) != _TRIGGER_ORPHAN_RECOVERY_KEYS
                or candidate.payload.get("build_attempt_id") != attempt_id
                or candidate.payload.get("reason")
                != _TRIGGER_ORPHAN_RECOVERY_REASON):
            return False
        previous -= 1
    return False


def _tail_trigger_orphan(records: List[WalRecord]) -> Optional[WalRecord]:
    if not records or records[-1].stage != trigger_gate_binding.WAL_RECORD_STAGE:
        return None
    attempt_id = records[-1].payload.get("build_attempt_id")
    if any(
        record.stage == STAGE_BUILD_START
        and record.payload.get("build_attempt_id") == attempt_id
        for record in records
    ):
        return None
    return records[-1]


def validate_trigger_bindings(
        records: List[WalRecord], *, campaign_lock: object,
        require_build_start: bool = False,
) -> Dict[str, trigger_gate_binding.TriggerGateBinding]:
    """Validate the shared trigger-binding record/start/source proof chain."""
    if type(require_build_start) is not bool:
        raise TypeError("require_build_start は exact bool が必要")
    identity = _campaign_lock_identity(campaign_lock)
    search = identity.get("search_config") if type(identity) is dict else None
    proposal_campaign = is_trigger_proposal_campaign_lock(campaign_lock)
    binding_records = [
        (index, record) for index, record in enumerate(records)
        if record.stage == trigger_gate_binding.WAL_RECORD_STAGE
    ]
    starts_with_commitment = [
        record for record in records
        if record.stage == STAGE_BUILD_START
        and TRIGGER_BINDING_COMMITMENT_KEY in record.payload
    ]
    if not proposal_campaign:
        if binding_records or starts_with_commitment:
            raise AttemptTopologyError("non-trigger campaign に trigger binding が混在")
        if (type(search) is dict and search.get("axis") == TRIGGER_AXIS
                and not is_trigger_machine_campaign_lock(campaign_lock)):
            raise AttemptTopologyError("post-policy trigger campaign の分類が unknown")
        return {}

    if (type(search) is not dict
            or search.get("axis") != TRIGGER_AXIS
            or search.get(TRIGGER_BINDING_SCHEMA_MARKER_KEY)
            != trigger_gate_binding.SCHEMA_VERSION):
        raise AttemptTopologyError("trigger proposal campaign の binding marker が不正")

    starts: Dict[str, tuple[int, WalRecord]] = {}
    for index, record in enumerate(records):
        if record.stage != STAGE_BUILD_START:
            continue
        attempt_id = record.payload.get("build_attempt_id")
        if type(attempt_id) is not str or not attempt_id:
            raise AttemptTopologyError("trigger build_start の attempt id が不正")
        if attempt_id in starts:
            raise AttemptTopologyError("trigger build_start の attempt id が重複")
        starts[attempt_id] = (index, record)
    if require_build_start and not starts:
        raise AttemptTopologyError("trigger proposal campaign に build_start がない")

    raw_by_attempt: Dict[str, tuple[int, WalRecord]] = {}
    for index, record in binding_records:
        payload = record.payload
        if (type(payload) is not dict
                or frozenset(payload) != _TRIGGER_BINDING_PAYLOAD_KEYS):
            raise AttemptTopologyError("trigger binding payload の key 集合が不正")
        attempt_id = payload.get("build_attempt_id")
        if type(attempt_id) is not str or not attempt_id:
            raise AttemptTopologyError("trigger binding の attempt id が不正")
        if attempt_id in raw_by_attempt:
            raise AttemptTopologyError("trigger binding が attempt 内で重複")
        raw_by_attempt[attempt_id] = (index, record)

    if set(starts) - set(raw_by_attempt):
        raise AttemptTopologyError("trigger build_start と binding が一対一でない")

    for attempt_id in set(raw_by_attempt) - set(starts):
        binding_index, binding_record = raw_by_attempt[attempt_id]
        try:
            trigger_gate_binding.validate_record(
                binding_record.payload[TRIGGER_BINDING_PAYLOAD_KEY],
                require_source=False,
            )
        except trigger_gate_binding.TriggerGateBindingError as exc:
            raise AttemptTopologyError("trigger binding record が不正") from exc
        is_tail_orphan = binding_index == len(records) - 1
        has_recovery_tombstone = (
            binding_index + 1 < len(records)
            and _is_trigger_orphan_tombstone(
                binding_record, records[binding_index + 1],
            )
        )
        if not (is_tail_orphan or has_recovery_tombstone):
            raise AttemptTopologyError(
                "trigger build_start と binding が一対一でない"
            )

    validated: Dict[str, trigger_gate_binding.TriggerGateBinding] = {}
    for attempt_id, (start_index, start) in starts.items():
        binding_index, binding_record = raw_by_attempt[attempt_id]
        if (binding_index != start_index - 1
                or binding_record.variant != start.variant
                or binding_record.env_tag != start.env_tag):
            raise AttemptTopologyError("trigger binding の順序または variant が不正")
        receipt = start.payload.get("build_admission")
        require_source = receipt is not None
        try:
            binding = trigger_gate_binding.validate_record(
                binding_record.payload[TRIGGER_BINDING_PAYLOAD_KEY],
                require_source=require_source,
            )
        except trigger_gate_binding.TriggerGateBindingError as exc:
            raise AttemptTopologyError("trigger binding record が不正") from exc
        if not require_source and binding.source is not None:
            raise AttemptTopologyError("receiptless trigger binding の source が non-null")
        expected_commitment = trigger_gate_binding.commitment(binding)
        if start.payload.get(TRIGGER_BINDING_COMMITMENT_KEY) != expected_commitment:
            raise AttemptTopologyError("trigger binding commitment が build_start と不一致")

        if require_source:
            receipt_source = receipt.get("source") if type(receipt) is dict else None
            outer_src_token = start.payload.get("src_token")
            source = binding.source
            if (type(receipt_source) is not dict or source is None
                    or type(outer_src_token) is not str
                    or source.src_token != outer_src_token
                    or source.src_token != receipt_source.get("src_token")
                    or source.source_bytes_sha256
                    != receipt_source.get("source_bytes_sha256")):
                raise AttemptTopologyError("trigger binding source が receipt/WAL と不一致")
        else:
            for later in records[start_index + 1:]:
                if later.variant != start.variant:
                    continue
                if later.stage == STAGE_BUILD_START:
                    break
                if "verify" in later.payload:
                    raise AttemptTopologyError(
                        "receiptless trigger attempt に verify payload が続く"
                    )
                if (later.stage == STAGE_ABORT
                        and later.payload.get("build_attempt_id") == attempt_id
                        and later.payload.get("reason") not in _SOURCE_NULL_ABORT_REASONS):
                    raise AttemptTopologyError(
                        "receiptless trigger attempt の abort reason が閉集合外"
                    )
                if later.stage in {
                    STAGE_BUILD_DONE, STAGE_VERIFY_DONE, STAGE_BENCH_DONE, STAGE_COMMIT,
                }:
                    raise AttemptTopologyError(
                        "receiptless trigger attempt に build/verify/bench/commit が続く"
                    )
        validated[attempt_id] = binding
    return validated


def _receipt_sha(payload: Dict, *, stage: str) -> str:
    value = payload.get("build_admission_receipt_sha256")
    if (type(value) is not str or len(value) != 64
            or any(ch not in "0123456789abcdef" for ch in value)):
        raise AttemptTopologyError(
            f"{stage}: build_admission_receipt_sha256 が exact lowercase SHA-256 でない"
        )
    return value


def validate_commit_contract_bindings(
        records: List[WalRecord], *, campaign_lock: object,
) -> None:
    """Validate lock-bound execution-contract identity on every COMMIT.

    The lock alone selects whether binding is required.  Legacy and guided
    locks without the wire key remain readable; a record cannot exempt itself
    by omitting the COMMIT field.
    """
    decoded = _decoded_campaign_lock_value(campaign_lock)
    identity = decoded.identity if decoded is not None else campaign_lock
    search_config = (
        identity.get("search_config") if type(identity) is dict else None
    )
    non_certifying = (
        type(decoded)
        is campaign_lock_codec.DecodedNonCertifyingCampaignLock
    )
    if non_certifying:
        expected = decoded.common_record["environment_contract_sha256"]
    elif decoded is not None and decoded.is_v2:
        if decoded.authority is None:  # codec contract 上は到達不能。防御的に閉じる。
            raise AttemptTopologyError("campaign-lock/v2 authority が欠落")
        expected = decoded.authority.environment_contract_sha256
    else:
        if (type(search_config) is not dict
                or _LEGACY_ENVIRONMENT_CONTRACT_SEARCH_KEY not in search_config):
            return
        expected = search_config.get(_LEGACY_ENVIRONMENT_CONTRACT_SEARCH_KEY)
    try:
        resolved = env_contract.resolve_by_contract_sha256(expected)
    except env_contract.EnvContractError as exc:
        raise AttemptTopologyError(
            "campaign.lock の environment contract を ever-active 契約へ解決できない"
        ) from exc
    for record in records:
        if record.stage != STAGE_COMMIT:
            continue
        if non_certifying:
            serialized = record.payload.get(RECEIPT_PAYLOAD_KEY)
            if type(serialized) is not dict:
                raise AttemptTopologyError(
                    "A-1 commit: 保存済み verifier receipt が欠落"
                )
            terminal_payload = dict(record.payload)
            terminal_payload.pop(RECEIPT_PAYLOAD_KEY, None)
            try:
                validate_serialized_receipt(
                    serialized,
                    sink_kind="campaign-wal",
                    lock_identity_sha256=campaign_lock_bytes_sha256(
                        decoded.original_text.encode("utf-8")
                    ),
                    variant=record.variant,
                    terminal_payload=terminal_payload,
                )
            except CommitReceiptError as exc:
                raise AttemptTopologyError(
                    "A-1 commit receipt が現在の campaign.lock SHA と不一致"
                ) from exc
        actual = record.payload.get(COMMIT_CONTRACT_SHA256_KEY)
        if (type(actual) is not str or len(actual) != 64
                or any(ch not in "0123456789abcdef" for ch in actual)):
            raise AttemptTopologyError(
                "commit: contract_sha256 が exact lowercase SHA-256 でない"
            )
        if actual != expected:
            raise AttemptTopologyError(
                "commit: contract_sha256 が campaign.lock と不一致"
            )
        if record.env_tag != resolved.contract.env_tag:
            raise AttemptTopologyError(
                "commit: env_tag が environment contract と不一致"
            )


def _validate_attempt_topology(
        records: List[WalRecord], *, admission_policy: BuildAdmissionPolicy,
        campaign_lock: object,
) -> Dict[str, Dict[str, BuildAttemptState]]:
    if type(admission_policy) is not BuildAdmissionPolicy:
        raise TypeError("admission_policy は BuildRunContext.policy の exact value が必要")
    return _validate_attempt_topology_body(
        records, campaign_lock=campaign_lock,
        validate_receipt=lambda receipt: validate_build_admission_receipt(
            receipt, expected_policy=admission_policy,
        ),
    )


def _validate_historical_attempt_topology(
        records: List[WalRecord], *, admission_policy: HistoricalBuildAdmissionPolicy,
        campaign_lock: object,
) -> Dict[str, Dict[str, BuildAttemptState]]:
    if type(admission_policy) is not HistoricalBuildAdmissionPolicy:
        raise TypeError("admission_policy requires exact HistoricalBuildAdmissionPolicy")
    return _validate_attempt_topology_body(
        records, campaign_lock=campaign_lock,
        validate_receipt=lambda receipt: validate_historical_build_admission_receipt(
            receipt, expected_policy=admission_policy,
        ),
    )


def _validate_attempt_topology_body(
        records: List[WalRecord], *, campaign_lock: object,
        validate_receipt: Callable[[object], Mapping[str, object]],
) -> Dict[str, Dict[str, BuildAttemptState]]:
    validate_knowledge_provenance_bindings(
        records, campaign_lock=campaign_lock,
    )
    validate_backoff_grammar_bindings(
        records, campaign_lock=campaign_lock,
    )
    validate_commit_contract_bindings(records, campaign_lock=campaign_lock)
    by_variant: Dict[str, Dict[str, BuildAttemptState]] = {}
    global_attempts: Dict[str, BuildAttemptState] = {}
    active: Dict[str, BuildAttemptState] = {}
    for index, record in enumerate(records):
        payload = record.payload
        if _is_trigger_orphan_tombstone_at(records, index):
            continue
        if record.stage == STAGE_BUILD_START:
            attempt_id = payload.get("build_attempt_id")
            if type(attempt_id) is not str or not attempt_id:
                raise AttemptTopologyError("build_start: build_attempt_id が欠落または不正")
            if attempt_id in global_attempts:
                raise AttemptTopologyError(
                    f"build_start: duplicate attempt id: {attempt_id}"
                )
            if record.variant in active:
                raise AttemptTopologyError(
                    f"build_start: variant に未終端 attempt がある: "
                    f"active={active[record.variant].attempt_id} next={attempt_id}"
                )
            receipt = payload.get("build_admission")
            receipt_sha = None
            if receipt is not None:
                try:
                    checked = validate_receipt(receipt)
                except BuildAdmissionError as exc:
                    raise AttemptTopologyError(
                        f"build_start: admission receipt canonicality/policy 不一致: {exc}"
                    ) from exc
                receipt_sha = _receipt_sha(payload, stage=record.stage)
                if checked["receipt_sha256"] != receipt_sha:
                    raise AttemptTopologyError(
                        "build_start: receipt body と伝播 SHA が不一致"
                    )
            elif "build_admission_receipt_sha256" in payload:
                raise AttemptTopologyError(
                    "build_start: receipt 無し attempt に receipt SHA がある"
                )
            attempt = BuildAttemptState(
                attempt_id=attempt_id,
                variant=record.variant,
                receipt_sha256=receipt_sha,
                stages_seen=[record.stage],
            )
            global_attempts[attempt_id] = attempt
            by_variant.setdefault(record.variant, {})[attempt_id] = attempt
            active[record.variant] = attempt
            continue

        if record.stage in {STAGE_BUILD_DONE, STAGE_COMMIT}:
            attempt_id = payload.get("build_attempt_id")
            attempt = global_attempts.get(attempt_id) if type(attempt_id) is str else None
            if attempt is None or attempt.variant != record.variant:
                raise AttemptTopologyError(
                    f"{record.stage}: matching build_start attempt がない"
                )
            if active.get(record.variant) is not attempt:
                raise AttemptTopologyError(
                    f"{record.stage}: attempt は active でない: {attempt_id}"
                )
            if attempt.receipt_sha256 is None:
                raise AttemptTopologyError(
                    f"{record.stage}: receiptless pre-build attempt は terminal build stage を持てない"
                )
            if _receipt_sha(payload, stage=record.stage) != attempt.receipt_sha256:
                raise AttemptTopologyError(
                    f"{record.stage}: 別 attempt の receipt SHA が流用された"
                )
            if record.stage == STAGE_BUILD_DONE:
                if attempt.build_done:
                    raise AttemptTopologyError("build_done: 同一 attempt で重複")
                attempt.build_done = True
            else:
                if not attempt.build_done:
                    raise AttemptTopologyError("commit: build_done より前または別 attempt")
                if attempt.committed:
                    raise AttemptTopologyError("commit: 同一 attempt で重複")
                attempt.committed = True
                active.pop(record.variant, None)
            attempt.stages_seen.append(record.stage)
            continue

        if record.stage in {STAGE_VERIFY_DONE, STAGE_BENCH_DONE}:
            attempt_id = payload.get("build_attempt_id")
            if attempt_id is None:
                continue
            if type(attempt_id) is not str or not attempt_id:
                raise AttemptTopologyError(
                    f"{record.stage}: build_attempt_id が欠落または不正"
                )
            attempt = global_attempts.get(attempt_id)
            if attempt is None or attempt.variant != record.variant:
                raise AttemptTopologyError(
                    f"{record.stage}: active attempt に対応する build_start がない"
                )
            current = active.get(record.variant)
            if current is not attempt:
                current_id = current.attempt_id if current is not None else None
                raise AttemptTopologyError(
                    f"{record.stage}: active attempt={current_id} と "
                    f"build_attempt_id={attempt_id} が不一致"
                )
            if not attempt.build_done:
                raise AttemptTopologyError(
                    f"{record.stage}: build_done より前の attempt に属する"
                )
            if "build_admission_receipt_sha256" in payload:
                receipt_sha = _receipt_sha(payload, stage=record.stage)
                if (attempt.receipt_sha256 is None
                        or receipt_sha != attempt.receipt_sha256):
                    raise AttemptTopologyError(
                        f"{record.stage}: 別 attempt の receipt SHA が流用された"
                    )
            if (record.stage == STAGE_BENCH_DONE
                    and STAGE_BENCH_DONE in attempt.stages_seen):
                raise AttemptTopologyError("bench_done: 同一 attempt で重複")
            # S2 may emit multiple verify passes; bench remains single-pass.
            attempt.stages_seen.append(record.stage)
            continue

        if record.stage == STAGE_ABORT:
            attempt_id = payload.get("build_attempt_id")
            if attempt_id is None:
                if record.variant in active:
                    raise AttemptTopologyError(
                        "abort: active attempt があるのに build_attempt_id が欠落"
                    )
                continue
            attempt = global_attempts.get(attempt_id) if type(attempt_id) is str else None
            if (attempt is None or attempt.variant != record.variant
                    or active.get(record.variant) is not attempt):
                raise AttemptTopologyError("abort: matching active attempt がない")
            if attempt.receipt_sha256 is None:
                if "build_admission_receipt_sha256" in payload:
                    raise AttemptTopologyError("abort: receiptless attempt に receipt SHA がある")
            elif _receipt_sha(payload, stage=record.stage) != attempt.receipt_sha256:
                raise AttemptTopologyError("abort: attempt receipt SHA が不一致")
            if payload.get("reason") in {
                INCOMPLETE_ATTEMPT_RECOVERY_REASON,
                _A1_BALANCED5_INTERRUPTED_ATTEMPT_INVALID_REASON,
            }:
                expected_keys = {"reason", "build_attempt_id"}
                if attempt.receipt_sha256 is not None:
                    expected_keys.add("build_admission_receipt_sha256")
                if set(payload) != expected_keys:
                    raise AttemptTopologyError(
                        "abort: interrupted-attempt recovery payload の "
                        "exact key 集合が不正"
                    )
            attempt.aborted = True
            attempt.stages_seen.append(record.stage)
            active.pop(record.variant, None)
    return by_variant


def _read_records_from_locked_fd(fd: int, size: int) -> List[WalRecord]:
    data = bytearray()
    offset = 0
    while offset < size:
        chunk = os.pread(fd, min(65536, size - offset), offset)
        if not chunk:
            raise OSError(errno.EIO, "unexpected EOF while scanning locked WAL")
        data.extend(chunk)
        offset += len(chunk)
    if data and data[-1:] != b"\n":
        raise WalFramingError(
            "WAL tail is not newline-terminated; explicit repair required"
        )
    if not data:
        return []
    return [
        _line_to_record(frame.decode("utf-8"))
        for frame in bytes(data[:-1]).split(b"\n")
    ]


def _recovery_context(records: List[WalRecord]) -> tuple[str, tuple[str, ...]]:
    for record in reversed(records):
        if not (_ATTEMPT_SCHEMA_KEYS & frozenset(record.payload)):
            continue
        attempt_id = record.payload.get("build_attempt_id")
        return (
            record.variant or "<unknown-variant>",
            (attempt_id if type(attempt_id) is str and attempt_id
             else "<unknown-attempt>",),
        )
    return "<unknown-variant>", ("<unknown-attempt>",)


def _active_attempt_candidates(
        records: List[WalRecord],
) -> Dict[str, list[tuple[str, int, WalRecord]]]:
    """Project only EOF-active IDs so multiple-active has a dedicated diagnosis."""
    active: Dict[str, list[tuple[str, int, WalRecord]]] = {}
    for index, record in enumerate(records):
        attempt_id = record.payload.get("build_attempt_id")
        if record.stage == STAGE_BUILD_START:
            if type(attempt_id) is str and attempt_id:
                active.setdefault(record.variant, []).append(
                    (attempt_id, index, record)
                )
            continue
        if record.stage not in {STAGE_COMMIT, STAGE_ABORT}:
            continue
        if type(attempt_id) is not str or not attempt_id:
            continue
        current = active.get(record.variant, [])
        active[record.variant] = [
            item for item in current if item[0] != attempt_id
        ]
    return {variant: items for variant, items in active.items() if items}


def _project_active_attempts(
        active_candidates: Dict[str, list[tuple[str, int, WalRecord]]],
) -> Dict[str, tuple[int, WalRecord, BuildAttemptState]]:
    """Project recovery inputs without performing topology validation."""
    projected: Dict[str, tuple[int, WalRecord, BuildAttemptState]] = {}
    for variant, candidates in active_candidates.items():
        if len(candidates) != 1:
            continue
        attempt_id, start_index, start = candidates[0]
        receipt_sha = start.payload.get("build_admission_receipt_sha256")
        projected[variant] = (
            start_index,
            start,
            BuildAttemptState(
                attempt_id=attempt_id,
                variant=variant,
                receipt_sha256=(receipt_sha if type(receipt_sha) is str else None),
                stages_seen=[STAGE_BUILD_START],
            ),
        )
    return projected


def _validate_recovery_suffix(
        recoveries: List[WalRecord],
        active_attempts: Dict[str, tuple[int, WalRecord, BuildAttemptState]],
        *, recovery_reason: str = INCOMPLETE_ATTEMPT_RECOVERY_REASON,
) -> None:
    """Validate only the new recovery suffix against the projected active starts."""
    if len(recoveries) != len(active_attempts):
        raise AttemptTopologyError("recovery suffix と active attempt の件数が不一致")
    seen: set[str] = set()
    for record in recoveries:
        projected = active_attempts.get(record.variant)
        if projected is None or record.variant in seen:
            raise AttemptTopologyError("recovery suffix の variant が active attempt と不一致")
        _start_index, start, attempt = projected
        expected_payload = {
            "reason": recovery_reason,
            "build_attempt_id": attempt.attempt_id,
        }
        if attempt.receipt_sha256 is not None:
            expected_payload["build_admission_receipt_sha256"] = attempt.receipt_sha256
        if (record.stage != STAGE_ABORT
                or record.env_tag != start.env_tag
                or record.payload != expected_payload):
            raise AttemptTopologyError(
                "recovery suffix が active attempt の exact terminal record でない"
            )
        seen.add(record.variant)


def _recovery_abort_record(
        start: WalRecord, attempt: BuildAttemptState, *, reason: str,
) -> WalRecord:
    payload = {
        "reason": reason,
        "build_attempt_id": attempt.attempt_id,
    }
    if attempt.receipt_sha256 is not None:
        payload["build_admission_receipt_sha256"] = attempt.receipt_sha256
    return WalRecord(
        variant=start.variant,
        stage=STAGE_ABORT,
        env_tag=start.env_tag,
        ts=time.time(),
        payload=payload,
    )


def _append_records_locked(
        layout: CampaignLayout, fd: int, records: List[WalRecord],
) -> None:
    if any(record.stage != STAGE_ABORT for record in records):
        raise InterruptedAttemptRecoveryError(
            condition="recovery-stage-not-abort",
            variant=next(
                record.variant for record in records
                if record.stage != STAGE_ABORT
            ),
            attempt_ids=("internal-recovery-suffix",),
            detail="_append_records_locked accepts STAGE_ABORT only",
        )
    encoded = b"".join(
        (_record_to_line(record) + "\n").encode("utf-8")
        for record in records
    )
    for frame in encoded.splitlines(keepends=True):
        parse_line(frame.decode("utf-8"))
    total = len(encoded)
    written = 0
    while written < total:
        try:
            count = os.write(fd, encoded[written:])
        except OSError as exc:
            raise _append_error(layout, total, written, "write", exc) from exc
        if count <= 0:
            exc = OSError(errno.EIO, "os.write made no progress")
            raise _append_error(layout, total, written, "write", exc) from exc
        written += count
    try:
        os.fsync(fd)
        dfd = os.open(
            layout.runs_dir,
            os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC,
        )
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except OSError as exc:
        raise _append_error(layout, total, written, "fsync", exc) from exc


def _recover_interrupted_attempts(
        layout: CampaignLayout, *, admission_policy: BuildAdmissionPolicy,
        allow_a1_non_certifying: bool = False,
        terminal_invalid: bool = False,
) -> List[WalRecord]:
    """Atomically terminate only the exact fail-open crash window.

    The existing WAL is scanned and validated, then the prospective suffix is
    validated, while one exclusive lock is held.  Any guard failure happens
    before the first write.  A WAL with no attempt-schema key is a byte-stable
    no-op.
    """
    if type(admission_policy) is not BuildAdmissionPolicy:
        raise TypeError("admission_policy は BuildRunContext.policy の exact value が必要")
    if type(terminal_invalid) is not bool:
        raise TypeError("terminal_invalid は exact bool が必要")
    getattr(layout, "_admit_materialization", lambda: None)()
    flags = os.O_RDWR | os.O_APPEND | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        fd = os.open(layout.wal_file, flags)
    except FileNotFoundError:
        return []
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise OSError(errno.EINVAL, "WAL is not a regular file")
        records = _read_records_from_locked_fd(fd, info.st_size)
        campaign_lock = _campaign_lock_value(
            layout,
            allow_a1_non_certifying=allow_a1_non_certifying,
        )
        if terminal_invalid:
            if (
                not allow_a1_non_certifying
                or not _has_exact_a1_balanced5_marker(campaign_lock)
            ):
                raise AttemptTopologyError(
                    "terminal invalid recovery は A-1 balanced5 marker 専用"
                )
        identity = _campaign_lock_identity(campaign_lock)
        search_config = (
            identity.get("search_config") if type(identity) is dict else None
        )
        if (type(search_config) is not dict
                or search_config.get("build_admission")
                != admission_policy.as_preimage()):
            variant, attempt_ids = _recovery_context(records)
            raise InterruptedAttemptRecoveryError(
                condition="admission-policy-lock-mismatch",
                variant=variant,
                attempt_ids=attempt_ids,
                detail=("campaign.lock search_config.build_admission must "
                        "match the current admission policy"),
            )
        try:
            validate_commit_contract_bindings(
                records, campaign_lock=campaign_lock,
            )
        except AttemptTopologyError as exc:
            variant, attempt_ids = _recovery_context(records)
            raise InterruptedAttemptRecoveryError(
                condition="existing-contract-binding-violation",
                variant=variant,
                attempt_ids=attempt_ids,
                detail=str(exc),
            ) from exc
        if not any(
                _ATTEMPT_SCHEMA_KEYS & frozenset(record.payload)
                for record in records):
            return []

        active_candidates = _active_attempt_candidates(records)
        for variant, candidates in active_candidates.items():
            if len(candidates) > 1:
                raise InterruptedAttemptRecoveryError(
                    condition="multiple-active-attempts",
                    variant=variant,
                    attempt_ids=tuple(item[0] for item in candidates),
                    detail="one variant has multiple EOF-active attempts",
                )

        active_attempts = _project_active_attempts(active_candidates)

        # D193's recovery gate is deliberately independent from the strict
        # attempt topology validator below.  In particular, legacy signal
        # records may have no build_attempt_id at all.  Preserve the first
        # post-start stage diagnosis using stage kind only.
        try:
            validate_trigger_bindings(records, campaign_lock=campaign_lock)
        except AttemptTopologyError as exc:
            variant, attempt_ids = _recovery_context(records)
            raise InterruptedAttemptRecoveryError(
                condition="existing-topology-violation",
                variant=variant,
                attempt_ids=attempt_ids,
                detail=str(exc),
            ) from exc
        for variant, (start_index, _start, attempt) in active_attempts.items():
            later_attempt_record = next((
                later for later in records[start_index + 1:]
                if (later.variant == variant
                    and later.stage in {
                        STAGE_BUILD_DONE, STAGE_VERIFY_DONE, STAGE_BENCH_DONE,
                    })
            ), None)
            if later_attempt_record is not None:
                raise InterruptedAttemptRecoveryError(
                    condition=(
                        "attempt-record-after-start"
                        if later_attempt_record.stage == STAGE_BUILD_DONE
                        else "signal-after-start"
                    ),
                    variant=variant,
                    attempt_ids=(attempt.attempt_id,),
                    detail=("build_done, verify_done, or bench_done follows "
                            "build_start"),
                )

        try:
            _validate_attempt_topology(
                records, admission_policy=admission_policy,
                campaign_lock=campaign_lock,
            )
        except AttemptTopologyError as exc:
            variant, attempt_ids = _recovery_context(records)
            raise InterruptedAttemptRecoveryError(
                condition="existing-topology-violation",
                variant=variant,
                attempt_ids=attempt_ids,
                detail=str(exc),
            ) from exc

        recoveries: List[WalRecord] = []
        recovery_reason = (
            _A1_BALANCED5_INTERRUPTED_ATTEMPT_INVALID_REASON
            if terminal_invalid else INCOMPLETE_ATTEMPT_RECOVERY_REASON
        )
        trigger_machine = is_trigger_machine_campaign_lock(campaign_lock)
        for variant, (_start_index, start, attempt) in active_attempts.items():
            if (trigger_machine
                    or TRIGGER_BINDING_COMMITMENT_KEY in start.payload):
                raise InterruptedAttemptRecoveryError(
                    condition="trigger-campaign",
                    variant=variant,
                    attempt_ids=(attempt.attempt_id,),
                    detail="trigger attempts require an unrevised proof chain",
                )
            recovery_count = sum(
                record.variant == variant
                and record.stage == STAGE_ABORT
                and record.payload.get("reason")
                == recovery_reason
                for record in records
            )
            if recovery_count >= INCOMPLETE_ATTEMPT_RECOVERY_LIMIT:
                raise InterruptedAttemptRecoveryError(
                    condition="recovery-exhausted",
                    variant=variant,
                    attempt_ids=(attempt.attempt_id,),
                    detail=("recovery count reached limit "
                            f"{INCOMPLETE_ATTEMPT_RECOVERY_LIMIT}"),
                )
            recoveries.append(
                _recovery_abort_record(start, attempt, reason=recovery_reason)
            )

        if not recoveries:
            return []
        prospective = records + recoveries
        try:
            validate_trigger_bindings(prospective, campaign_lock=campaign_lock)
            _validate_recovery_suffix(
                recoveries, active_attempts, recovery_reason=recovery_reason,
            )
        except AttemptTopologyError as exc:
            last = recoveries[-1]
            raise InterruptedAttemptRecoveryError(
                condition="prospective-topology-violation",
                variant=last.variant,
                attempt_ids=(last.payload["build_attempt_id"],),
                detail=str(exc),
            ) from exc
        _append_records_locked(layout, fd, recoveries)
        return recoveries
    finally:
        os.close(fd)


def recover_interrupted_attempts(
        layout: CampaignLayout, *, admission_policy: BuildAdmissionPolicy,
) -> List[WalRecord]:
    """通常 v1/v2 lock の interrupted attempt recovery。"""
    return _recover_interrupted_attempts(
        layout, admission_policy=admission_policy,
    )


def recover_interrupted_attempts_a1_non_certifying(
        layout: CampaignLayout, *, admission_policy: BuildAdmissionPolicy,
) -> List[WalRecord]:
    """旧 A-1 配置専用の retryable interrupted attempt recovery。"""
    decoded = _campaign_lock_value(layout, allow_a1_non_certifying=True)
    if not _has_exact_a1_non_certifying_marker(decoded):
        raise AttemptTopologyError("A-1 non-certifying recovery marker が不正")
    if _has_exact_a1_balanced5_marker(decoded):
        raise AttemptTopologyError(
            "A-1 balanced5 marker は terminal invalid recovery が必要"
        )
    return _recover_interrupted_attempts(
        layout,
        admission_policy=admission_policy,
        allow_a1_non_certifying=True,
    )


def recover_interrupted_attempts_a1_balanced5_terminal_invalid(
        layout: CampaignLayout, *, admission_policy: BuildAdmissionPolicy,
) -> List[WalRecord]:
    """新 A-1 配置の interrupted attempt を terminal invalid に閉じる。"""
    return _recover_interrupted_attempts(
        layout,
        admission_policy=admission_policy,
        allow_a1_non_certifying=True,
        terminal_invalid=True,
    )


def replay_admitted_records(records: List[WalRecord]) -> Dict[str, EvalState]:
    """Project an already-read WAL snapshot without touching the live layout.

    The legacy variant-wide fields intentionally retain replay's historical
    last-record behavior.  The committed fields are populated only from the
    final commit's attempt ID and records preceding that commit, so an older
    attempt cannot enter the committed projection merely by appearing later
    in a variant's WAL history.
    """
    states: Dict[str, EvalState] = {}
    for index, r in enumerate(records):
        if _is_trigger_orphan_tombstone_at(records, index):
            continue
        st = states.get(r.variant)
        if st is None:
            st = EvalState(variant=r.variant)
            states[r.variant] = st
        st.stages_seen.append(r.stage)
        st.env_tag = r.env_tag
        st.last = r
        if r.stage == STAGE_COMMIT:
            st.committed = True
            st.last_terminal = r
        elif r.stage == STAGE_ABORT:
            st.aborted = True
            st.last_terminal = r

    for variant, state in states.items():
        commit_index: Optional[int] = None
        committed_attempt_id: Optional[str] = None
        for index in range(len(records) - 1, -1, -1):
            record = records[index]
            if (_is_trigger_orphan_tombstone_at(records, index)
                    or record.variant != variant
                    or record.stage != STAGE_COMMIT):
                continue
            candidate = record.payload.get("build_attempt_id")
            if type(candidate) is str and candidate:
                commit_index = index
                committed_attempt_id = candidate
            break
        if commit_index is None or committed_attempt_id is None:
            continue

        state.committed_attempt_id = committed_attempt_id
        for index, record in enumerate(records[:commit_index + 1]):
            if (_is_trigger_orphan_tombstone_at(records, index)
                    or record.variant != variant
                    or record.payload.get("build_attempt_id")
                    != committed_attempt_id):
                continue
            if record.stage == STAGE_BUILD_START:
                state.committed_build_start = record
            elif record.stage == STAGE_VERIFY_DONE:
                state.committed_verify.append(record)
            elif record.stage == STAGE_BENCH_DONE:
                state.committed_bench = record
    return states


def _replay(
        layout: CampaignLayout, *,
        admission_policy: Optional[BuildAdmissionPolicy] = None,
        allow_a1_non_certifying: bool = False,
) -> Dict[str, EvalState]:
    """WAL をリプレイし、new-schema lock では attempt topology も検証する。"""
    # schema classification must complete before the first WAL read.
    campaign_lock = _campaign_lock_value(
        layout,
        allow_a1_non_certifying=allow_a1_non_certifying,
    )
    if allow_a1_non_certifying and not _has_exact_a1_non_certifying_marker(
            campaign_lock):
        raise AttemptTopologyError("A-1 dedicated replay の exact marker が不正")
    records = read_records(layout)
    validate_commit_contract_bindings(records, campaign_lock=campaign_lock)
    validate_trigger_bindings(records, campaign_lock=campaign_lock)
    if admission_policy is None:
        identity = _campaign_lock_identity(campaign_lock)
        search = identity.get("search_config") if type(identity) is dict else None
        declared_policy = (
            search.get("build_admission") if type(search) is dict else None
        )
        if declared_policy is not None:
            current_policy = resolve_current_build_admission_policy()
            if declared_policy != current_policy.as_preimage():
                raise AttemptTopologyError(
                    "campaign.lock の build admission_policy が現行 policy と不一致"
                )
            admission_policy = current_policy
    attempts = (
        _validate_attempt_topology(
            records, admission_policy=admission_policy,
            campaign_lock=campaign_lock,
        )
        if admission_policy is not None else {}
    )
    orphan = _tail_trigger_orphan(records)
    if orphan is not None:
        payload = {
            "build_attempt_id": orphan.payload["build_attempt_id"],
            "reason": _TRIGGER_ORPHAN_RECOVERY_REASON,
        }
        if allow_a1_non_certifying:
            append_a1_non_certifying(
                layout,
                WalRecord(
                    variant=orphan.variant,
                    stage=STAGE_ABORT,
                    env_tag=orphan.env_tag,
                    ts=time.time(),
                    payload=payload,
                ),
            )
        else:
            log(layout, orphan.variant, STAGE_ABORT, orphan.env_tag, payload)
        records = read_records(layout)
        validate_trigger_bindings(records, campaign_lock=campaign_lock)
        attempts = (
            _validate_attempt_topology(
                records, admission_policy=admission_policy,
                campaign_lock=campaign_lock,
            )
            if admission_policy is not None else {}
        )
    states = replay_admitted_records(records)
    for variant, variant_attempts in attempts.items():
        states.setdefault(variant, EvalState(variant=variant)).attempts = variant_attempts
    return states


def replay(
        layout: CampaignLayout, *,
        admission_policy: Optional[BuildAdmissionPolicy] = None,
) -> Dict[str, EvalState]:
    """通常 v1/v2 replay。非認証 schema は WAL read 前に拒否する。"""
    return _replay(layout, admission_policy=admission_policy)


def replay_a1_non_certifying(
        layout: CampaignLayout, *,
        admission_policy: Optional[BuildAdmissionPolicy] = None,
) -> Dict[str, EvalState]:
    """A-1 exact marker の non-certifying lock 専用 replay。"""
    return _replay(
        layout,
        admission_policy=admission_policy,
        allow_a1_non_certifying=True,
    )


def records_by_stage(layout: CampaignLayout, variant: str) -> Dict[str, Dict]:
    """variant の stage→payload (最後勝ち)。判定は宣言でなく WAL レコードで行う。

    p3_kickoff.py / p3_s4_red.py / p3_s4_loop.py が各々独立に持っていた同一実装を
    統合 (D36 決定4-2)。**注意 (敵対レビュー 2026-07-09 で確認):** STAGE_VERIFY_DONE
    は S2 有効時 (evaluate() の extra_correctness、search_config['verify']=='legacy+s2')
    に variant ごと legacy→S2 の順で複数回書かれる。本関数は stage 単位の最後勝ちの
    ため、この場合は最後のパス (S2) の payload だけが残り、先行パスの verdict/commits/
    aborts は見えなくなる。全パスを見る・スケールを揃えて比較する必要がある consumer
    (例 critic.digest.load_verify_abort_signals) は wal.read_records() を直接使い、
    workload タグ (payload["workload"]["tag"]) で読み分けること。"""
    records = read_records(layout)
    campaign_lock = _campaign_lock_value(layout)
    validate_commit_contract_bindings(records, campaign_lock=campaign_lock)
    validate_trigger_bindings(records, campaign_lock=campaign_lock)
    out: Dict[str, Dict] = {}
    for index, r in enumerate(records):
        if (r.variant == variant
                and r.stage != trigger_gate_binding.WAL_RECORD_STAGE
                and not _is_trigger_orphan_tombstone_at(records, index)):
            payload = dict(r.payload)
            payload.pop(RECEIPT_PAYLOAD_KEY, None)
            out[r.stage] = payload
    return out


def terminal_variants(states: Dict[str, EvalState]) -> set:
    """評価が終わっている (commit=採用 / abort=不採用) variant 集合 = スキップ対象。"""
    return {v for v, st in states.items() if st.terminal}


def resumable_variants(states: Dict[str, EvalState]) -> set:
    """未終端 = リカバリで破棄して再評価すべき variant (in-flight クラッシュ)。"""
    return {v for v, st in states.items() if st.resumable}


# ---- campaign.lock (同一性の正準 pre-image) ----

def write_lock(layout: CampaignLayout, preimage: str) -> None:
    getattr(layout, "_admit_materialization", lambda: None)()
    os.makedirs(layout.root, exist_ok=True)
    # 初回のみ書く (既存があれば上書きしない = identity は不変)。
    if not os.path.exists(layout.lock_file):
        with open(layout.lock_file, "w", encoding="utf-8") as f:
            f.write(preimage)


def read_lock(layout: CampaignLayout) -> Optional[str]:
    if not os.path.exists(layout.lock_file):
        return None
    with open(layout.lock_file, "r", encoding="utf-8") as f:
        return f.read()


# ---- 原子的 one-shot lock / WAL 存在判定 (R6 resume 拒否の強化) ----

def acquire_lock_atomic(layout: CampaignLayout, preimage: str) -> bool:
    """`O_CREAT|O_EXCL` で campaign.lock を原子的に獲得する。既存なら False。

    write_lock (exists 確認後の非原子書き込み) の resume-safe 版。並行起動では一方だけが
    True を得る。WAL 空確認から最初の campaign-start append までを覆う排他区間の起点。
    True 時は preimage を書き込み、ファイル本体と親ディレクトリを fsync して存在を
    耐久化する (作成直後の crash でも lock が残る)。
    """
    getattr(layout, "_admit_materialization", lambda: None)()
    os.makedirs(layout.root, exist_ok=True)
    try:
        fd = os.open(layout.lock_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        return False
    try:
        os.write(fd, preimage.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    dfd = os.open(layout.root, os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)
    return True


def wal_bytes_present(layout: CampaignLayout) -> bool:
    """WAL ファイルに byte が存在するか (parse 可否は問わない)。

    read_records は末尾切れの 1 行を捨てるため、campaign-start 1 行だけの途中切断 WAL
    では [] を返しうる。resume 拒否は「parse 可能 record の有無」でなく「byte の存在」で
    判定する必要がある (truncated/汚染 WAL 迂回の閉鎖、fail-closed)。
    """
    try:
        path_info = os.lstat(layout.wal_file)
    except FileNotFoundError:
        return False
    if not stat.S_ISREG(path_info.st_mode):
        raise OSError(
            errno.EINVAL, "WAL is a symlink or non-regular file",
            os.fspath(layout.wal_file),
        )
    try:
        fd = os.open(
            layout.wal_file,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
        )
    except FileNotFoundError:
        # lstat 後に消えた場合は「byte 無し」と同じ。その他の OSError は伝播する。
        return False
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise OSError(
                errno.EINVAL, "WAL is not a regular file",
                os.fspath(layout.wal_file),
            )
        return info.st_size > 0
    finally:
        os.close(fd)
