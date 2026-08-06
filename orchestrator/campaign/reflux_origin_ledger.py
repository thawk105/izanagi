# -*- coding: utf-8 -*-
"""D153 W1〜W5 ledger 側契約に適合する P4 batch-freeze prototype。

これは P4 の充足でも、producer / driver / formal consumer への結線でもない。
ledger が束縛する evidence は digest claim であり、referent の実在・完全性・policy 適合は
formal consumer の義務である。`sealed_queries` は evidence を伴う sealed member row 数で、
物理 query 数の証明ではない。producer が receipt 後に実 query を実行する順序もここでは
観測できない。W4 が固定するのは terminal member row 数であり、JSON byte 長は
受容残余として固定しない。

Git commit 済み
authority は人間レビューを経た単一版の信頼入力として扱うが、in-process の private
関数呼出しは capability 境界ではない。また、別 clone、Git checkout の rollback、同一
UID による authority と runtime の協調再構築は検出しない。mutable runtime head は Git
commit せず、clone の common-dir に置く。

公開 API は固定 production path だけを使う。test seam は private で temp Git repository
全体を差し替えるだけであり、authority / ledger / lock の個別 path は注入できない。

seal 要求は結果 plaintext の開示点である。seal event の fsync 後・head commit 前に
crash すると、開示済みだが未 commit の event bytes が raw storage 観測者に残りうる。
commitment salt は producer が CSPRNG で生成する契約であり、この leaf が強制するのは
salt の形式・長さと同一 origin 内での一意性だけである。
"""
from __future__ import annotations

import base64
import binascii
import fcntl
import hashlib
import json
import os
import re
import stat
import subprocess
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Iterator, Mapping, Sequence

__all__ = [
    "MANIFEST_SCHEMA_ID",
    "AUTHORITY_SCHEMA_ID",
    "AUTHORITY_RELATIVE_PATH",
    "EvidenceReference",
    "EvidenceDigest",
    "QueryFloorConstraint",
    "BudgetPolicy",
    "AuthorityManifest",
    "CommittedBatchMember",
    "PreparedBatchMember",
    "OpenedBatchMember",
    "SealedBatchMember",
    "BatchReserved",
    "BatchReservationAbandoned",
    "BatchCommitted",
    "BatchResultsPrepared",
    "BatchSealed",
    "OriginSealed",
    "OriginSnapshot",
    "SealedBatch",
    "EventReceipt",
    "canonical_manifest_bytes",
    "derive_origin_id",
    "derive_cell_key",
    "read_origin",
    "commit_event",
    "read_sealed_batch",
    "RefluxOriginLedgerError",
]

MANIFEST_SCHEMA_ID = "izanagi-reflux-origin-manifest/v2"
AUTHORITY_SCHEMA_ID = "izanagi-reflux-origin-authority/v2"
AUTHORITY_RELATIVE_PATH = "orchestrator/campaign/reflux_origin_authority_v2.json"
_EVENT_SCHEMA_ID = "izanagi-reflux-origin-event/v2"
_HEAD_SCHEMA_ID = "izanagi-reflux-origin-runtime-head/v2"
_FLOOR_FORMULA_ID = "q-lower-bound/base+perRound*R+Emin/v1"
_TRIGGER_GATE_IR_SCHEMA = "izanagi-trigger-gate-ir/v1"
_KNOWN_IR_SCHEMAS = frozenset({_TRIGGER_GATE_IR_SCHEMA})
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_OID_RE = re.compile(r"[0-9a-f]{40}\Z")
_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_MAX_INTEGER = (1 << 63) - 1
_MAX_RECORD_BYTES = 1 << 20
_MAX_LEDGER_BYTES = 64 << 20
_MAX_AUTHORITY_BYTES = 8 << 20
_GIT_TIMEOUT_SECONDS = 30
_DOMAIN_MANIFEST = b"izanagi-reflux-origin-manifest/v2\0"
_DOMAIN_CELL = b"izanagi-reflux-origin-cell/v1\0"
_DOMAIN_STATE = b"izanagi-reflux-origin-state/v2\0"
_DOMAIN_MEMBER = b"izanagi-reflux-origin-batch-member/v1\0"
_DOMAIN_RESULT_EVIDENCE = b"izanagi-reflux-origin-result-evidence/v1\0"
_NULL_SHA256 = "0" * 64
_MISSING = object()

# Literal ceiling is independently pinned at max/max+1 by V21.  Admission still
# serializes every relevant real frame before allocating authority-sized tuples.
_MAX_BATCH_MEMBER_ROW_COUNT = 2248
_JSON_SHA_MEMBER_BYTES = 67
_MAX_CLASS_CARDINALITY = (_MAX_RECORD_BYTES - 1) // _JSON_SHA_MEMBER_BYTES


class RefluxOriginLedgerError(RuntimeError):
    """Authority, ledger, CAS, or state-machine validation failed closed."""


class _LockReentryError(RefluxOriginLedgerError):
    pass


def _fail(reason: str) -> None:
    raise RefluxOriginLedgerError(reason) from None


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_json(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError):
        _fail("value is not canonical JSON")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    _fail("non-finite JSON number")


def _strict_json(raw: bytes, *, label: str) -> Any:
    try:
        text = raw.decode("utf-8", errors="strict")
        return json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except RefluxOriginLedgerError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError):
        _fail(f"invalid {label} JSON")


def _exact_object(value: object, keys: frozenset[str], *, label: str) -> dict[str, Any]:
    if type(value) is not dict or frozenset(value) != keys:
        _fail(f"invalid {label} keys")
    return value


def _string(value: object, *, label: str, token: bool = False) -> str:
    if type(value) is not str or not value or (token and _TOKEN_RE.fullmatch(value) is None):
        _fail(f"invalid {label}")
    return value


def _sha(value: object, *, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        _fail(f"invalid {label}")
    return value


def _oid(value: object, *, label: str) -> str:
    if type(value) is not str or _OID_RE.fullmatch(value) is None:
        _fail(f"invalid {label}")
    return value


def _integer(value: object, *, label: str, minimum: int = 0) -> int:
    if type(value) is not int or not minimum <= value <= _MAX_INTEGER:
        _fail(f"invalid {label}")
    return value


def _relative_path(value: object, *, label: str) -> str:
    value = _string(value, label=label)
    path = PurePosixPath(value)
    if path.is_absolute() or value != path.as_posix() or ".." in path.parts or "." in path.parts:
        _fail(f"invalid {label}")
    return value


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    path: str
    sha256: str


@dataclass(frozen=True, slots=True)
class EvidenceDigest:
    """A claimed content digest; this ledger deliberately does not dereference it."""

    sha256: str


@dataclass(frozen=True, slots=True)
class QueryFloorConstraint:
    formula_id: str
    base_queries: int
    queries_per_round: int
    rounds: int
    evidence_min: int

    @property
    def required_queries(self) -> int:
        value = self.base_queries + self.queries_per_round * self.rounds + self.evidence_min
        if value > _MAX_INTEGER:
            _fail("query floor arithmetic overflow")
        return value


@dataclass(frozen=True, slots=True)
class BudgetPolicy:
    imax: int
    qmax: int
    kmax: int
    batch_member_row_count_min: int
    batch_distinct_candidate_count_min: int
    query_floor_constraints: tuple[QueryFloorConstraint, ...]


@dataclass(frozen=True, slots=True)
class AuthorityManifest:
    authority_series_id: str
    spec_content_sha256: str
    ccbench_commit_oid: str
    axis_semantics_sha256: str
    workload: Mapping[str, object]
    verifier_policy_sha256: str
    environment_contract_sha256: str
    candidate_ir: Mapping[str, object]
    role_bundle_sha256: str
    recipient_projection_schema_sha256: str
    budget_policy: BudgetPolicy
    stock_certification_ref: EvidenceReference
    structural_zero_evidence_ref: EvidenceReference


_MANIFEST_KEYS = frozenset({
    "authority_series_id", "spec_content_sha256", "ccbench_commit_oid",
    "axis_semantics_sha256", "workload", "verifier_policy_sha256",
    "environment_contract_sha256", "candidate_ir", "role_bundle_sha256",
    "recipient_projection_schema_sha256", "budget_policy",
    "stock_certification_ref", "structural_zero_evidence_ref",
})
_WORKLOAD_KEYS = frozenset({"descriptor_sha256", "records", "threads"})
_CANDIDATE_IR_KEYS = frozenset({"schema_ref", "canonical_emitter_sha256"})
_BUDGET_KEYS = frozenset({
    "imax", "qmax", "kmax", "batch_member_row_count_min",
    "batch_distinct_candidate_count_min", "query_floor_constraints",
})
_FLOOR_KEYS = frozenset({
    "formula_id", "base_queries", "queries_per_round", "rounds", "evidence_min",
})
_EVIDENCE_KEYS = frozenset({"path", "sha256"})


def _evidence_from_object(value: object, *, label: str) -> EvidenceReference:
    obj = _exact_object(value, _EVIDENCE_KEYS, label=label)
    return EvidenceReference(
        path=_relative_path(obj["path"], label=f"{label}.path"),
        sha256=_sha(obj["sha256"], label=f"{label}.sha256"),
    )


def _evidence_object(value: EvidenceReference, *, label: str) -> dict[str, object]:
    if type(value) is not EvidenceReference:
        _fail(f"invalid {label}")
    return {
        "path": _relative_path(value.path, label=f"{label}.path"),
        "sha256": _sha(value.sha256, label=f"{label}.sha256"),
    }


def _floor_from_object(
    value: object,
    *,
    member_row_min: int,
    qmax: int,
) -> QueryFloorConstraint:
    obj = _exact_object(value, _FLOOR_KEYS, label="query floor")
    floor = QueryFloorConstraint(
        formula_id=_string(obj["formula_id"], label="floor formula_id"),
        base_queries=_integer(obj["base_queries"], label="floor base_queries"),
        queries_per_round=_integer(
            obj["queries_per_round"], label="floor queries_per_round", minimum=1
        ),
        rounds=_integer(obj["rounds"], label="floor rounds", minimum=1),
        evidence_min=_integer(obj["evidence_min"], label="floor evidence_min"),
    )
    if floor.formula_id != _FLOOR_FORMULA_ID:
        _fail("unknown query floor formula")
    required = floor.required_queries
    if required < max(2, member_row_min) or required > qmax:
        _fail("query floor is outside authority budget")
    return floor


def _budget_from_object(value: object) -> BudgetPolicy:
    obj = _exact_object(value, _BUDGET_KEYS, label="budget policy")
    imax = _integer(obj["imax"], label="Imax", minimum=1)
    qmax = _integer(obj["qmax"], label="Qmax", minimum=1)
    kmax = _integer(obj["kmax"], label="Kmax")
    member_row_min = _integer(
        obj["batch_member_row_count_min"],
        label="batch member row minimum",
        minimum=2,
    )
    candidate_min = _integer(
        obj["batch_distinct_candidate_count_min"],
        label="batch distinct candidate minimum",
        minimum=1,
    )
    if candidate_min > member_row_min:
        _fail("batch distinct candidate minimum exceeds member row minimum")
    if member_row_min > _MAX_BATCH_MEMBER_ROW_COUNT:
        _fail("batch minimum exceeds codec feasibility")
    raw_floors = obj["query_floor_constraints"]
    if type(raw_floors) is not list or not raw_floors:
        _fail("query floor constraints must be non-empty")
    floors = tuple(
        _floor_from_object(item, member_row_min=member_row_min, qmax=qmax)
        for item in raw_floors
    )
    canonical_order = tuple(
        sorted(
            floors,
            key=lambda item: (
                item.formula_id,
                item.base_queries,
                item.queries_per_round,
                item.rounds,
                item.evidence_min,
            ),
        )
    )
    if floors != canonical_order:
        _fail("query floor constraints are not canonical")
    if len(set(floors)) != len(floors):
        _fail("duplicate query floor constraint")
    policy = BudgetPolicy(
        imax,
        qmax,
        kmax,
        member_row_min,
        candidate_min,
        floors,
    )
    _check_budget_codec_feasibility(policy)
    return policy


def _budget_object(value: BudgetPolicy) -> dict[str, object]:
    if type(value) is not BudgetPolicy:
        _fail("invalid budget policy")
    raw = {
        "imax": value.imax,
        "qmax": value.qmax,
        "kmax": value.kmax,
        "batch_member_row_count_min": value.batch_member_row_count_min,
        "batch_distinct_candidate_count_min": (
            value.batch_distinct_candidate_count_min
        ),
        "query_floor_constraints": [
            {
                "formula_id": item.formula_id,
                "base_queries": item.base_queries,
                "queries_per_round": item.queries_per_round,
                "rounds": item.rounds,
                "evidence_min": item.evidence_min,
            }
            for item in value.query_floor_constraints
        ],
    }
    _budget_from_object(raw)
    return raw


def _manifest_from_object(value: object) -> AuthorityManifest:
    obj = _exact_object(value, _MANIFEST_KEYS, label="authority manifest")
    workload = _exact_object(obj["workload"], _WORKLOAD_KEYS, label="workload")
    workload_value = MappingProxyType({
        "descriptor_sha256": _sha(
            workload["descriptor_sha256"], label="workload descriptor"
        ),
        "records": _integer(workload["records"], label="workload records", minimum=1),
        "threads": _integer(workload["threads"], label="workload threads", minimum=1),
    })
    candidate = _exact_object(obj["candidate_ir"], _CANDIDATE_IR_KEYS, label="candidate IR")
    schema_ref = _string(candidate["schema_ref"], label="candidate IR schema")
    if schema_ref not in _KNOWN_IR_SCHEMAS:
        _fail("unknown candidate IR schema")
    candidate_value = MappingProxyType({
        "schema_ref": schema_ref,
        "canonical_emitter_sha256": _sha(
            candidate["canonical_emitter_sha256"], label="canonical emitter"
        ),
    })
    return AuthorityManifest(
        authority_series_id=_string(
            obj["authority_series_id"], label="authority series", token=True
        ),
        spec_content_sha256=_sha(obj["spec_content_sha256"], label="spec content"),
        ccbench_commit_oid=_oid(obj["ccbench_commit_oid"], label="CCBench commit OID"),
        axis_semantics_sha256=_sha(obj["axis_semantics_sha256"], label="axis semantics"),
        workload=workload_value,
        verifier_policy_sha256=_sha(
            obj["verifier_policy_sha256"], label="verifier policy"
        ),
        environment_contract_sha256=_sha(
            obj["environment_contract_sha256"], label="environment contract"
        ),
        candidate_ir=candidate_value,
        role_bundle_sha256=_sha(obj["role_bundle_sha256"], label="role bundle"),
        recipient_projection_schema_sha256=_sha(
            obj["recipient_projection_schema_sha256"], label="projection schema"
        ),
        budget_policy=_budget_from_object(obj["budget_policy"]),
        stock_certification_ref=_evidence_from_object(
            obj["stock_certification_ref"], label="stock certification ref"
        ),
        structural_zero_evidence_ref=_evidence_from_object(
            obj["structural_zero_evidence_ref"], label="structural zero ref"
        ),
    )


def _manifest_object(manifest: AuthorityManifest) -> dict[str, object]:
    if type(manifest) is not AuthorityManifest:
        _fail("invalid authority manifest")
    workload = dict(manifest.workload) if type(manifest.workload) in (dict, MappingProxyType) else None
    candidate = dict(manifest.candidate_ir) if type(manifest.candidate_ir) in (dict, MappingProxyType) else None
    raw: dict[str, object] = {
        "authority_series_id": manifest.authority_series_id,
        "spec_content_sha256": manifest.spec_content_sha256,
        "ccbench_commit_oid": manifest.ccbench_commit_oid,
        "axis_semantics_sha256": manifest.axis_semantics_sha256,
        "workload": workload,
        "verifier_policy_sha256": manifest.verifier_policy_sha256,
        "environment_contract_sha256": manifest.environment_contract_sha256,
        "candidate_ir": candidate,
        "role_bundle_sha256": manifest.role_bundle_sha256,
        "recipient_projection_schema_sha256": manifest.recipient_projection_schema_sha256,
        "budget_policy": _budget_object(manifest.budget_policy),
        "stock_certification_ref": _evidence_object(
            manifest.stock_certification_ref, label="stock certification ref"
        ),
        "structural_zero_evidence_ref": _evidence_object(
            manifest.structural_zero_evidence_ref, label="structural zero ref"
        ),
    }
    validated = _manifest_from_object(raw)
    return {
        **raw,
        "workload": dict(validated.workload),
        "candidate_ir": dict(validated.candidate_ir),
    }


def canonical_manifest_bytes(manifest: AuthorityManifest) -> bytes:
    """Return the canonical manifest JSON bytes, without a trailing LF."""
    return _canonical_json(_manifest_object(manifest))


def derive_origin_id(manifest: AuthorityManifest) -> str:
    return _sha256(_DOMAIN_MANIFEST + canonical_manifest_bytes(manifest))


def derive_cell_key(manifest: AuthorityManifest) -> str:
    obj = _manifest_object(manifest)
    cell = [
        obj["workload"]["descriptor_sha256"],
        obj["axis_semantics_sha256"],
        obj["verifier_policy_sha256"],
        obj["environment_contract_sha256"],
    ]
    return _sha256(_DOMAIN_CELL + _canonical_json(cell))


@dataclass(frozen=True, slots=True)
class CommittedBatchMember:
    query_ordinal: int
    candidate_commitment: str


@dataclass(frozen=True, slots=True)
class PreparedBatchMember:
    query_ordinal: int
    candidate_commitment: str
    result_evidence_commitment: str
    constraint_commitment: str


@dataclass(frozen=True, slots=True)
class OpenedBatchMember:
    query_ordinal: int
    replicate_ordinal: int
    candidate_salt: str
    candidate_bytes: bytes
    result_evidence_salt: str
    outcome: str
    evidence_digest: EvidenceDigest | None
    constraint_salt: str
    constraint_sha256: str | None


@dataclass(frozen=True, slots=True)
class SealedBatchMember:
    query_ordinal: int
    replicate_ordinal: int
    candidate_bytes: bytes
    outcome: str
    evidence_digest: EvidenceDigest | None
    constraint_sha256: str | None


@dataclass(frozen=True, slots=True)
class BatchReserved:
    batch_id: str
    iteration_index: int
    member_row_count: int
    query_ordinal_start: int


@dataclass(frozen=True, slots=True)
class BatchReservationAbandoned:
    batch_id: str


@dataclass(frozen=True, slots=True)
class BatchCommitted:
    batch_id: str
    iteration_index: int
    members: tuple[CommittedBatchMember, ...]


@dataclass(frozen=True, slots=True)
class BatchResultsPrepared:
    batch_id: str
    members: tuple[PreparedBatchMember, ...]


@dataclass(frozen=True, slots=True)
class BatchSealed:
    batch_id: str
    members: tuple[OpenedBatchMember, ...]


@dataclass(frozen=True, slots=True)
class OriginSealed:
    aborted: bool
    constraint_class_sha256s: tuple[str, ...]
    batch_count: int
    tombstone_count: int
    sealed_queries: int
    tombstoned_queries: int
    forfeited_iterations: int
    forfeited_queries: int
    """Reserved member rows, not a count of physical provider queries."""


OriginEvent = (
    BatchReserved
    | BatchReservationAbandoned
    | BatchCommitted
    | BatchResultsPrepared
    | BatchSealed
    | OriginSealed
)


@dataclass(frozen=True, slots=True)
class OriginSnapshot:
    origin_id: str
    state_commitment: str
    phase: str
    iterations_used: int
    queries_used: int
    sealed_queries: int
    tombstoned_queries: int
    forfeited_iterations: int
    forfeited_queries: int
    """Reserved member rows, not a count of physical provider queries."""
    batch_count: int
    tombstone_count: int
    terminal_status: str | None
    constraint_class_sha256s: tuple[str, ...]
    origin_distinct_candidate_count: int
    reserved_batch_id: str | None
    reserved_iteration_index: int | None
    reserved_member_row_count: int | None
    reserved_query_ordinal_start: int | None


@dataclass(frozen=True, slots=True)
class SealedBatch:
    origin_id: str
    batch_id: str
    member_row_count: int
    distinct_candidate_count: int
    sealed_distinct_candidate_count: int
    members: tuple[SealedBatchMember, ...]


@dataclass(frozen=True, slots=True)
class EventReceipt:
    origin_id: str
    operation_id: str
    event_index: int
    event_sha256: str
    resulting_state_commitment: str
    current_state_commitment: str
    replayed: bool


def _tuple_of(value: object, *, label: str, member: Any) -> tuple[Any, ...]:
    if type(value) is not tuple:
        _fail(f"invalid {label}")
    result = []
    for item in value:
        result.append(member(item))
    return tuple(result)


def _commitment(value: object, *, label: str) -> str:
    return _sha(value, label=label)


def _salt(value: object, *, label: str) -> str:
    value = _string(value, label=label)
    if len(value) != 32 or any(ch not in "0123456789abcdef" for ch in value):
        _fail(f"invalid {label}")
    if not any(ch != "0" for ch in value):
        _fail(f"invalid {label}: all-zero salt")
    return value


def _salted_commitment(salt_hex: str, value: bytes) -> str:
    try:
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        _fail("invalid commitment salt")
    return _sha256(salt + value)


def _evidence_digest(value: object, *, label: str) -> EvidenceDigest:
    if type(value) is not EvidenceDigest:
        _fail(f"invalid {label}")
    return EvidenceDigest(_sha(value.sha256, label=f"{label}.sha256"))


def _member_preimage(
    candidate_bytes: bytes,
    query_ordinal: int,
    replicate_ordinal: int,
) -> bytes:
    if type(candidate_bytes) is not bytes:
        _fail("invalid candidate opening bytes")
    return _DOMAIN_MEMBER + _canonical_json({
        "candidate_wire_b64": base64.b64encode(candidate_bytes).decode("ascii"),
        "query_ordinal": _integer(query_ordinal, label="query ordinal"),
        "replicate_ordinal": _integer(replicate_ordinal, label="replicate ordinal"),
    })


def _result_evidence_preimage(
    outcome: object,
    evidence_digest: object,
) -> bytes:
    outcome = _string(outcome, label="outcome")
    if outcome not in ("accepted", "rejected", "tombstoned"):
        _fail("invalid sealed outcome")
    if evidence_digest is None:
        evidence_sha: str | None = None
    else:
        evidence_sha = _evidence_digest(
            evidence_digest, label="evidence digest"
        ).sha256
    if outcome == "tombstoned":
        if evidence_sha is not None:
            _fail("tombstoned result has evidence")
    elif evidence_sha is None:
        _fail(f"{outcome} result lacks evidence")
    return _DOMAIN_RESULT_EVIDENCE + _canonical_json({
        "evidence_sha256": evidence_sha,
        "outcome": outcome,
    })


def _validate_result_matrix(
    *,
    outcome: object,
    evidence_digest: object,
    constraint_sha256: object,
) -> tuple[str, EvidenceDigest | None, str | None]:
    preimage = _result_evidence_preimage(outcome, evidence_digest)
    del preimage
    normalized_outcome = str(outcome)
    normalized_evidence = (
        None
        if evidence_digest is None
        else _evidence_digest(evidence_digest, label="evidence digest")
    )
    if normalized_outcome == "rejected":
        constraint = _sha(constraint_sha256, label="constraint digest")
    else:
        if constraint_sha256 is not None:
            _fail(f"{normalized_outcome} result has a constraint digest")
        constraint = None
    return normalized_outcome, normalized_evidence, constraint


def _committed_member_object(member: object) -> dict[str, object]:
    if type(member) is not CommittedBatchMember:
        _fail("invalid committed member")
    return {
        "candidate_commitment": _commitment(
            member.candidate_commitment, label="candidate commitment"
        ),
        "query_ordinal": _integer(member.query_ordinal, label="query ordinal"),
    }


def _prepared_member_object(member: object) -> dict[str, object]:
    if type(member) is not PreparedBatchMember:
        _fail("invalid prepared member")
    return {
        "candidate_commitment": _commitment(
            member.candidate_commitment, label="candidate commitment"
        ),
        "constraint_commitment": _commitment(
            member.constraint_commitment, label="constraint commitment"
        ),
        "query_ordinal": _integer(member.query_ordinal, label="query ordinal"),
        "result_evidence_commitment": _commitment(
            member.result_evidence_commitment,
            label="result evidence commitment",
        ),
    }


def _opened_member_object(member: object) -> dict[str, object]:
    if type(member) is not OpenedBatchMember:
        _fail("invalid opened member")
    outcome, evidence, constraint = _validate_result_matrix(
        outcome=member.outcome,
        evidence_digest=member.evidence_digest,
        constraint_sha256=member.constraint_sha256,
    )
    return {
        "candidate_salt": _salt(member.candidate_salt, label="candidate salt"),
        "candidate_wire_b64": base64.b64encode(member.candidate_bytes).decode("ascii")
        if type(member.candidate_bytes) is bytes
        else _fail("invalid candidate opening bytes"),
        "constraint_salt": _salt(member.constraint_salt, label="constraint salt"),
        "constraint_sha256": constraint,
        "evidence_sha256": None if evidence is None else evidence.sha256,
        "outcome": outcome,
        "query_ordinal": _integer(member.query_ordinal, label="query ordinal"),
        "replicate_ordinal": _integer(
            member.replicate_ordinal, label="replicate ordinal"
        ),
        "result_evidence_salt": _salt(
            member.result_evidence_salt, label="result evidence salt"
        ),
    }


def _event_payload(event: OriginEvent) -> tuple[str, dict[str, object]]:
    if type(event) is BatchReserved:
        return "batch-reserved", {
            "batch_id": _string(event.batch_id, label="batch ID", token=True),
            "iteration_index": _integer(
                event.iteration_index, label="iteration index"
            ),
            "member_row_count": _integer(
                event.member_row_count, label="member row count"
            ),
            "query_ordinal_start": _integer(
                event.query_ordinal_start, label="query ordinal start"
            ),
        }
    if type(event) is BatchReservationAbandoned:
        return "batch-reservation-abandoned", {
            "batch_id": _string(event.batch_id, label="batch ID", token=True),
        }
    if type(event) is BatchCommitted:
        batch_id = _string(event.batch_id, label="batch ID", token=True)
        iteration = _integer(event.iteration_index, label="iteration index")
        members = _tuple_of(
            event.members,
            label="committed members",
            member=_committed_member_object,
        )
        return "batch-committed", {
            "batch_id": batch_id,
            "iteration_index": iteration,
            "member_row_count": len(members),
            "members": list(members),
        }
    if type(event) is BatchResultsPrepared:
        members = _tuple_of(
            event.members,
            label="prepared members",
            member=_prepared_member_object,
        )
        return "batch-results-prepared", {
            "batch_id": _string(event.batch_id, label="batch ID", token=True),
            "members": list(members),
        }
    if type(event) is BatchSealed:
        members = _tuple_of(
            event.members,
            label="opened members",
            member=_opened_member_object,
        )
        return "batch-sealed", {
            "batch_id": _string(event.batch_id, label="batch ID", token=True),
            "member_row_count": len(members),
            "distinct_candidate_count": len({
                member["candidate_wire_b64"] for member in members
            }),
            "sealed_distinct_candidate_count": len({
                member["candidate_wire_b64"]
                for member in members
                if member["outcome"] != "tombstoned"
            }),
            "members": list(members),
        }
    if type(event) is OriginSealed:
        if type(event.aborted) is not bool:
            _fail("invalid origin seal kind")
        constraint_class = _tuple_of(
            event.constraint_class_sha256s,
            label="constraint class",
            member=lambda item: _sha(item, label="constraint class digest"),
        )
        return "origin-sealed", {
            "seal_kind": "aborted" if event.aborted else "certifiable",
            "constraint_class_sha256s": list(constraint_class),
            "batch_count": _integer(event.batch_count, label="seal batch count"),
            "tombstone_count": _integer(
                event.tombstone_count, label="seal tombstone count"
            ),
            "sealed_queries": _integer(
                event.sealed_queries, label="seal sealed queries"
            ),
            "tombstoned_queries": _integer(
                event.tombstoned_queries, label="seal tombstoned queries"
            ),
            "forfeited_iterations": _integer(
                event.forfeited_iterations, label="seal forfeited iterations"
            ),
            "forfeited_queries": _integer(
                event.forfeited_queries, label="seal forfeited queries"
            ),
        }
    _fail("unsupported origin event")


def _event_from_payload(event_type: object, payload: object) -> OriginEvent | None:
    event_type = _string(event_type, label="event type")
    if event_type == "origin-opened":
        _exact_object(
            payload,
            frozenset({"authority_blob_sha256", "cell_key"}),
            label="origin opened payload",
        )
        return None
    if event_type == "batch-reserved":
        obj = _exact_object(
            payload,
            frozenset({
                "batch_id", "iteration_index", "member_row_count",
                "query_ordinal_start",
            }),
            label="batch reserved payload",
        )
        return BatchReserved(
            batch_id=_string(obj["batch_id"], label="batch ID", token=True),
            iteration_index=_integer(
                obj["iteration_index"], label="iteration index"
            ),
            member_row_count=_integer(
                obj["member_row_count"], label="member row count"
            ),
            query_ordinal_start=_integer(
                obj["query_ordinal_start"], label="query ordinal start"
            ),
        )
    if event_type == "batch-reservation-abandoned":
        obj = _exact_object(
            payload,
            frozenset({"batch_id"}),
            label="batch reservation abandoned payload",
        )
        return BatchReservationAbandoned(
            batch_id=_string(obj["batch_id"], label="batch ID", token=True),
        )
    if event_type == "batch-committed":
        obj = _exact_object(
            payload,
            frozenset({
                "batch_id", "iteration_index", "member_row_count", "members",
            }),
            label="batch committed payload",
        )
        raw = obj["members"]
        if type(raw) is not list:
            _fail("invalid committed members")
        values = []
        for item in raw:
            member = _exact_object(
                item,
                frozenset({"candidate_commitment", "query_ordinal"}),
                label="committed member",
            )
            values.append(CommittedBatchMember(
                query_ordinal=_integer(
                    member["query_ordinal"], label="query ordinal"
                ),
                candidate_commitment=_sha(
                    member["candidate_commitment"], label="candidate commitment"
                ),
            ))
        if (
            _integer(obj["member_row_count"], label="member row count")
            != len(values)
        ):
            _fail("committed member row count mismatch")
        return BatchCommitted(
            _string(obj["batch_id"], label="batch ID", token=True),
            _integer(obj["iteration_index"], label="iteration index"),
            tuple(values),
        )
    if event_type == "batch-results-prepared":
        obj = _exact_object(
            payload,
            frozenset({"batch_id", "members"}),
            label="results prepared payload",
        )
        raw = obj["members"]
        if type(raw) is not list:
            _fail("invalid prepared members")
        members = []
        for item in raw:
            member = _exact_object(
                item,
                frozenset({
                    "candidate_commitment", "constraint_commitment",
                    "query_ordinal", "result_evidence_commitment",
                }),
                label="prepared member",
            )
            members.append(PreparedBatchMember(
                query_ordinal=_integer(
                    member["query_ordinal"], label="query ordinal"
                ),
                candidate_commitment=_sha(
                    member["candidate_commitment"], label="candidate commitment"
                ),
                result_evidence_commitment=_sha(
                    member["result_evidence_commitment"],
                    label="result evidence commitment",
                ),
                constraint_commitment=_sha(
                    member["constraint_commitment"],
                    label="constraint commitment",
                ),
            ))
        return BatchResultsPrepared(
            _string(obj["batch_id"], label="batch ID", token=True),
            tuple(members),
        )
    if event_type == "batch-sealed":
        obj = _exact_object(
            payload,
            frozenset({
                "batch_id", "member_row_count", "distinct_candidate_count",
                "sealed_distinct_candidate_count", "members",
            }),
            label="batch sealed payload",
        )
        raw = obj["members"]
        if type(raw) is not list:
            _fail("invalid opened members")
        members = []
        for item in raw:
            member = _exact_object(
                item,
                frozenset({
                    "candidate_salt", "candidate_wire_b64", "constraint_salt",
                    "constraint_sha256", "evidence_sha256", "outcome",
                    "query_ordinal", "replicate_ordinal", "result_evidence_salt",
                }),
                label="opened member",
            )
            wire_b64 = _string(
                member["candidate_wire_b64"], label="candidate wire base64"
            )
            try:
                candidate = base64.b64decode(wire_b64, validate=True)
            except (ValueError, binascii.Error):
                _fail("invalid candidate base64")
            if base64.b64encode(candidate).decode("ascii") != wire_b64:
                _fail("non-canonical candidate base64")
            evidence = (
                None
                if member["evidence_sha256"] is None
                else EvidenceDigest(
                    _sha(member["evidence_sha256"], label="evidence digest")
                )
            )
            outcome, evidence, constraint = _validate_result_matrix(
                outcome=member["outcome"],
                evidence_digest=evidence,
                constraint_sha256=member["constraint_sha256"],
            )
            members.append(OpenedBatchMember(
                query_ordinal=_integer(
                    member["query_ordinal"], label="query ordinal"
                ),
                replicate_ordinal=_integer(
                    member["replicate_ordinal"], label="replicate ordinal"
                ),
                candidate_salt=_salt(
                    member["candidate_salt"], label="candidate salt"
                ),
                candidate_bytes=candidate,
                result_evidence_salt=_salt(
                    member["result_evidence_salt"],
                    label="result evidence salt",
                ),
                outcome=outcome,
                evidence_digest=evidence,
                constraint_salt=_salt(
                    member["constraint_salt"], label="constraint salt"
                ),
                constraint_sha256=constraint,
            ))
        member_row_count = _integer(
            obj["member_row_count"], label="sealed member row count"
        )
        distinct_candidate_count = _integer(
            obj["distinct_candidate_count"],
            label="sealed batch distinct candidate count",
        )
        sealed_distinct_candidate_count = _integer(
            obj["sealed_distinct_candidate_count"],
            label="sealed batch executed distinct candidate count",
        )
        if member_row_count != len(members):
            _fail("sealed member row count mismatch")
        if distinct_candidate_count != len({
            member.candidate_bytes for member in members
        }):
            _fail("sealed batch distinct candidate count mismatch")
        if sealed_distinct_candidate_count != len({
            member.candidate_bytes
            for member in members
            if member.outcome != "tombstoned"
        }):
            _fail("sealed batch executed distinct candidate count mismatch")
        return BatchSealed(
            _string(obj["batch_id"], label="batch ID", token=True),
            tuple(members),
        )
    if event_type == "origin-sealed":
        obj = _exact_object(
            payload,
            frozenset({
                "seal_kind", "constraint_class_sha256s", "batch_count",
                "tombstone_count", "sealed_queries", "tombstoned_queries",
                "forfeited_iterations", "forfeited_queries",
            }),
            label="origin seal payload",
        )
        kind = _string(obj["seal_kind"], label="seal kind")
        if kind not in ("aborted", "certifiable"):
            _fail("invalid seal kind")
        raw_class = obj["constraint_class_sha256s"]
        if type(raw_class) is not list:
            _fail("invalid constraint class")
        return OriginSealed(
            aborted=kind == "aborted",
            constraint_class_sha256s=tuple(
                _sha(item, label="constraint class digest") for item in raw_class
            ),
            batch_count=_integer(obj["batch_count"], label="batch count"),
            tombstone_count=_integer(obj["tombstone_count"], label="tombstone count"),
            sealed_queries=_integer(obj["sealed_queries"], label="sealed queries"),
            tombstoned_queries=_integer(
                obj["tombstoned_queries"], label="tombstoned queries"
            ),
            forfeited_iterations=_integer(
                obj["forfeited_iterations"], label="forfeited iterations"
            ),
            forfeited_queries=_integer(
                obj["forfeited_queries"], label="forfeited queries"
            ),
        )
    _fail("unknown event type")


@dataclass(slots=True)
class _SemanticState:
    phase: str = "EMPTY"
    iterations_used: int = 0
    queries_used: int = 0
    sealed_queries: int = 0
    tombstoned_queries: int = 0
    forfeited_iterations: int = 0
    forfeited_queries: int = 0
    """Reserved member rows, not a count of physical provider queries."""
    batch_count: int = 0
    tombstone_count: int = 0
    open_batch: dict[str, object] | None = None
    sealed_batches: dict[str, SealedBatch] | None = None
    seen_batches: set[str] | None = None
    rejected_constraints: set[str] | None = None
    seen_salts: set[str] | None = None
    replicate_counts: dict[bytes, int] | None = None
    terminal_status: str | None = None
    constraint_class: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.sealed_batches is None:
            self.sealed_batches = {}
        if self.seen_batches is None:
            self.seen_batches = set()
        if self.rejected_constraints is None:
            self.rejected_constraints = set()
        if self.seen_salts is None:
            self.seen_salts = set()
        if self.replicate_counts is None:
            self.replicate_counts = {}

    @property
    def sealed_member_row_count(self) -> int:
        return sum(
            batch.member_row_count for batch in self.sealed_batches.values()
        )

    @property
    def origin_distinct_candidate_count(self) -> int:
        return len(self.replicate_counts)

    @property
    def origin_sealed_distinct_candidate_count(self) -> int:
        return len({
            member.candidate_bytes
            for batch in self.sealed_batches.values()
            for member in batch.members
            if member.outcome != "tombstoned"
        })


def _semantic_object(state: _SemanticState) -> dict[str, object]:
    open_batch: object = None
    if state.open_batch is not None:
        raw_members = state.open_batch["members"]
        open_batch = {
            "batch_id": state.open_batch["batch_id"],
            "iteration_index": state.open_batch["iteration_index"],
            "member_row_count": state.open_batch["member_row_count"],
            "query_ordinal_start": state.open_batch["query_ordinal_start"],
            "members": None if raw_members is None else [
                _committed_member_object(item)
                if type(item) is CommittedBatchMember
                else _prepared_member_object(item)
                for item in raw_members
            ],
        }
    return {
        "phase": state.phase,
        "iterations_used": state.iterations_used,
        "queries_used": state.queries_used,
        "sealed_queries": state.sealed_queries,
        "tombstoned_queries": state.tombstoned_queries,
        "forfeited_iterations": state.forfeited_iterations,
        "forfeited_queries": state.forfeited_queries,
        "sealed_member_row_count": state.sealed_member_row_count,
        "origin_distinct_candidate_count": state.origin_distinct_candidate_count,
        "origin_sealed_distinct_candidate_count": (
            state.origin_sealed_distinct_candidate_count
        ),
        "batch_count": state.batch_count,
        "tombstone_count": state.tombstone_count,
        "open_batch": open_batch,
        "sealed_batch_ids": sorted(state.sealed_batches),
        "seen_batch_ids": sorted(state.seen_batches),
        "rejected_constraints": sorted(state.rejected_constraints),
        "seen_salts": sorted(state.seen_salts),
        "terminal_status": state.terminal_status,
        "constraint_class": list(state.constraint_class),
    }


def _semantic_sha(state: _SemanticState) -> str:
    return _sha256(_canonical_json(_semantic_object(state)))


def _preseal_semantic_sha(state: _SemanticState) -> str:
    """Commit prospective structure without result/class plaintext or salts."""
    projected = _semantic_object(state)
    projected.pop("rejected_constraints")
    projected.pop("constraint_class")
    projected.pop("seen_salts")
    projected.pop("sealed_queries")
    projected.pop("tombstoned_queries")
    projected.pop("tombstone_count")
    projected.pop("sealed_member_row_count")
    projected.pop("origin_distinct_candidate_count")
    projected.pop("origin_sealed_distinct_candidate_count")
    return _sha256(_canonical_json(projected))


def _assert_query_partition(state: _SemanticState) -> None:
    open_phases = {"BATCH_RESERVED", "BATCH_COMMITTED", "RESULTS_PREPARED"}
    if (state.open_batch is None) != (state.phase not in open_phases):
        _fail("origin open batch shape mismatch")
    pending = 0
    if state.open_batch is not None:
        member_row_count = _integer(
            state.open_batch["member_row_count"],
            label="open batch member row count",
        )
        members = state.open_batch["members"]
        if state.phase == "BATCH_RESERVED":
            if members is not None:
                _fail("reserved batch unexpectedly has committed members")
            pending = member_row_count
        else:
            if type(members) is not tuple or len(members) != member_row_count:
                _fail("open batch member row count mismatch")
            expected_type = (
                CommittedBatchMember
                if state.phase == "BATCH_COMMITTED"
                else PreparedBatchMember
            )
            if any(type(member) is not expected_type for member in members):
                _fail("open batch member type mismatch")
            pending = member_row_count
    if state.queries_used != (
        state.sealed_queries
        + state.tombstoned_queries
        + state.forfeited_queries
        + pending
    ):
        _fail("origin query partition mismatch")


def _assert_iteration_partition(state: _SemanticState) -> None:
    reserved = 1 if state.phase == "BATCH_RESERVED" else 0
    if state.iterations_used != (
        state.batch_count + state.forfeited_iterations + reserved
    ):
        _fail("origin iteration partition mismatch")


def _assert_partitions(state: _SemanticState) -> None:
    _assert_query_partition(state)
    _assert_iteration_partition(state)


def _validate_candidate_wire(schema_ref: str, raw: bytes) -> None:
    if schema_ref != _TRIGGER_GATE_IR_SCHEMA:
        _fail("unknown candidate IR schema")
    # Δ1 の seal 時 wire 正準性検証だけが reflux_ir を import する。
    from . import reflux_ir

    try:
        wire = raw.decode("ascii", errors="strict")
        decoded = reflux_ir.parse_wire(wire)
        canonical = reflux_ir.encode_wire(decoded)
    except (UnicodeDecodeError, reflux_ir.RefluxIRError):
        _fail("invalid candidate IR wire")
    if canonical.encode("ascii") != raw:
        _fail("non-canonical candidate IR wire")


def _apply_event(
    state: _SemanticState,
    event: OriginEvent | None,
    *,
    manifest: AuthorityManifest,
    origin_id: str,
) -> None:
    if event is None:
        if state.phase != "EMPTY":
            _fail("duplicate origin genesis")
        state.phase = "IDLE"
        _assert_partitions(state)
        return
    budget = manifest.budget_policy
    if type(event) is BatchReserved:
        if state.phase != "IDLE":
            _fail("batch reservation is not allowed in current phase")
        batch_id = _string(event.batch_id, label="batch ID", token=True)
        iteration_index = _integer(
            event.iteration_index, label="iteration index"
        )
        member_row_count = _integer(
            event.member_row_count, label="member row count"
        )
        query_ordinal_start = _integer(
            event.query_ordinal_start, label="query ordinal start"
        )
        if batch_id in state.seen_batches:
            _fail("batch ID was reused")
        if iteration_index != state.iterations_used:
            _fail("iteration index is not contiguous")
        if query_ordinal_start != state.queries_used:
            _fail("query ordinal start is not contiguous")
        if member_row_count > _MAX_BATCH_MEMBER_ROW_COUNT:
            _fail("batch member row count exceeds codec feasibility")
        if member_row_count < budget.batch_member_row_count_min:
            _fail("reservation member row count is below batch minimum")
        if state.iterations_used + 1 > budget.imax:
            _fail("Imax exceeded")
        if state.queries_used + member_row_count > budget.qmax:
            _fail("Qmax exceeded")
        state.iterations_used += 1
        state.queries_used += member_row_count
        state.seen_batches.add(batch_id)
        state.open_batch = {
            "batch_id": batch_id,
            "iteration_index": iteration_index,
            "member_row_count": member_row_count,
            "query_ordinal_start": query_ordinal_start,
            "members": None,
        }
        state.phase = "BATCH_RESERVED"
        _assert_partitions(state)
        return
    if type(event) is BatchReservationAbandoned:
        if state.phase != "BATCH_RESERVED" or state.open_batch is None:
            _fail("batch reservation abandon is not allowed in current phase")
        batch_id = _string(event.batch_id, label="batch ID", token=True)
        if batch_id != state.open_batch["batch_id"]:
            _fail("abandoned batch does not match reservation")
        state.forfeited_iterations += 1
        state.forfeited_queries += int(state.open_batch["member_row_count"])
        state.open_batch = None
        state.phase = "IDLE"
        _assert_partitions(state)
        return
    if type(event) is BatchCommitted:
        if state.phase != "BATCH_RESERVED" or state.open_batch is None:
            _fail("batch commit is not allowed in current phase")
        reservation = state.open_batch
        batch_id = _string(event.batch_id, label="batch ID", token=True)
        iteration_index = _integer(
            event.iteration_index, label="iteration index"
        )
        if type(event.members) is not tuple:
            _fail("invalid committed members")
        member_row_count = len(event.members)
        if member_row_count > _MAX_BATCH_MEMBER_ROW_COUNT:
            _fail("batch member row count exceeds codec feasibility")
        members = tuple(
            CommittedBatchMember(
                query_ordinal=_integer(
                    member.query_ordinal, label="query ordinal"
                ),
                candidate_commitment=_sha(
                    member.candidate_commitment, label="candidate commitment"
                ),
            )
            if type(member) is CommittedBatchMember
            else _fail("invalid committed member")
            for member in event.members
        )
        if len({item.candidate_commitment for item in members}) != member_row_count:
            _fail("invalid batch candidate commitments")
        expected_queries = tuple(range(
            int(reservation["query_ordinal_start"]),
            int(reservation["query_ordinal_start"]) + member_row_count,
        ))
        if tuple(item.query_ordinal for item in members) != expected_queries:
            _fail("committed query ordinals do not match reservation")
        if (
            batch_id != reservation["batch_id"]
            or iteration_index != reservation["iteration_index"]
            or member_row_count != reservation["member_row_count"]
        ):
            _fail("committed batch does not match reservation")
        state.batch_count += 1
        state.open_batch["members"] = members
        state.phase = "BATCH_COMMITTED"
        _assert_partitions(state)
        return
    if type(event) is BatchResultsPrepared:
        if state.phase != "BATCH_COMMITTED" or state.open_batch is None:
            _fail("results preparation is not allowed in current phase")
        committed_members = state.open_batch["members"]
        member_row_count = len(committed_members)
        batch_id = _string(event.batch_id, label="batch ID", token=True)
        if type(event.members) is not tuple:
            _fail("invalid prepared members")
        prepared_members = tuple(
            PreparedBatchMember(
                query_ordinal=_integer(
                    member.query_ordinal, label="query ordinal"
                ),
                candidate_commitment=_sha(
                    member.candidate_commitment, label="candidate commitment"
                ),
                result_evidence_commitment=_sha(
                    member.result_evidence_commitment,
                    label="result evidence commitment",
                ),
                constraint_commitment=_sha(
                    member.constraint_commitment,
                    label="constraint commitment",
                ),
            )
            if type(member) is PreparedBatchMember
            else _fail("invalid prepared member")
            for member in event.members
        )
        prepared_identity = tuple(
            (item.query_ordinal, item.candidate_commitment)
            for item in prepared_members
        )
        committed_identity = tuple(
            (item.query_ordinal, item.candidate_commitment)
            for item in committed_members
        )
        if (
            batch_id != state.open_batch["batch_id"]
            or prepared_identity != committed_identity
        ):
            _fail("prepared results do not match committed batch")
        if len(prepared_members) != member_row_count:
            _fail("partial prepared result set")
        state.open_batch["members"] = prepared_members
        state.phase = "RESULTS_PREPARED"
        _assert_partitions(state)
        return
    if type(event) is BatchSealed:
        if state.phase != "RESULTS_PREPARED" or state.open_batch is None:
            _fail("batch seal is not allowed in current phase")
        batch = state.open_batch
        prepared_members = batch["members"]
        member_row_count = len(prepared_members)
        batch_id = _string(event.batch_id, label="batch ID", token=True)
        if type(event.members) is not tuple:
            _fail("invalid opened members")
        if (
            batch_id != batch["batch_id"]
            or len(event.members) != member_row_count
        ):
            _fail("partial or wrong batch opening")
        normalized: list[OpenedBatchMember] = []
        salts: list[str] = []
        for raw_member in event.members:
            if type(raw_member) is not OpenedBatchMember:
                _fail("invalid opened member")
            salts.extend((
                _salt(raw_member.candidate_salt, label="candidate salt"),
                _salt(
                    raw_member.result_evidence_salt,
                    label="result evidence salt",
                ),
                _salt(raw_member.constraint_salt, label="constraint salt"),
            ))
        if len(set(salts)) != len(salts) or any(
            salt in state.seen_salts for salt in salts
        ):
            _fail("commitment salt was reused within origin")
        tombstone_seen = False
        next_replicates = dict(state.replicate_counts)
        for prepared, member in zip(prepared_members, event.members, strict=True):
            if type(member) is not OpenedBatchMember:
                _fail("invalid opened member")
            query = _integer(member.query_ordinal, label="query ordinal")
            replicate = _integer(
                member.replicate_ordinal, label="replicate ordinal"
            )
            candidate_salt = _salt(member.candidate_salt, label="candidate salt")
            result_salt = _salt(
                member.result_evidence_salt, label="result evidence salt"
            )
            constraint_salt = _salt(
                member.constraint_salt, label="constraint salt"
            )
            if type(member.candidate_bytes) is not bytes:
                _fail("invalid candidate opening bytes")
            raw = member.candidate_bytes
            _validate_candidate_wire(str(manifest.candidate_ir["schema_ref"]), raw)
            outcome, evidence, constraint = _validate_result_matrix(
                outcome=member.outcome,
                evidence_digest=member.evidence_digest,
                constraint_sha256=member.constraint_sha256,
            )
            if outcome == "tombstoned":
                tombstone_seen = True
            elif tombstone_seen:
                _fail("tombstoned members are not a terminal suffix")
            expected_replicate = next_replicates.get(raw, 0)
            if replicate != expected_replicate:
                _fail("replicate ordinal is not origin-canonical")
            next_replicates[raw] = expected_replicate + 1
            if query != prepared.query_ordinal:
                _fail("opened member query ordinal mismatch")
            candidate_commitment = _salted_commitment(
                candidate_salt, _member_preimage(raw, query, replicate)
            )
            result_commitment = _salted_commitment(
                result_salt, _result_evidence_preimage(outcome, evidence)
            )
            constraint_commitment = _salted_commitment(
                constraint_salt,
                b"" if constraint is None else constraint.encode("ascii"),
            )
            if (
                candidate_commitment != prepared.candidate_commitment
                or result_commitment != prepared.result_evidence_commitment
                or constraint_commitment != prepared.constraint_commitment
            ):
                _fail("salted commitment opening mismatch")
            normalized.append(OpenedBatchMember(
                query_ordinal=query,
                replicate_ordinal=replicate,
                candidate_salt=candidate_salt,
                candidate_bytes=raw,
                result_evidence_salt=result_salt,
                outcome=outcome,
                evidence_digest=evidence,
                constraint_salt=constraint_salt,
                constraint_sha256=constraint,
            ))
        member_row_count = len(normalized)
        distinct_candidate_count = len({
            member.candidate_bytes for member in normalized
        })
        sealed_distinct_candidate_count = len({
            member.candidate_bytes
            for member in normalized
            if member.outcome != "tombstoned"
        })
        sealed_members = []
        sealed_count = tombstoned_count = 0
        for member in normalized:
            if member.outcome == "rejected":
                assert member.constraint_sha256 is not None
                state.rejected_constraints.add(member.constraint_sha256)
            if member.outcome == "tombstoned":
                tombstoned_count += 1
            else:
                sealed_count += 1
            sealed_members.append(SealedBatchMember(
                query_ordinal=member.query_ordinal,
                replicate_ordinal=member.replicate_ordinal,
                candidate_bytes=member.candidate_bytes,
                outcome=member.outcome,
                evidence_digest=member.evidence_digest,
                constraint_sha256=member.constraint_sha256,
            ))
        sealed = SealedBatch(
            origin_id=origin_id,
            batch_id=batch_id,
            member_row_count=member_row_count,
            distinct_candidate_count=distinct_candidate_count,
            sealed_distinct_candidate_count=sealed_distinct_candidate_count,
            members=tuple(sealed_members),
        )
        if batch_id in state.sealed_batches:
            _fail("duplicate sealed batch")
        state.sealed_batches[batch_id] = sealed
        state.seen_salts.update(salts)
        state.replicate_counts = next_replicates
        state.sealed_queries += sealed_count
        state.tombstoned_queries += tombstoned_count
        if tombstoned_count:
            state.tombstone_count += 1
        state.open_batch = None
        state.phase = "IDLE"
        _assert_partitions(state)
        return
    if type(event) is OriginSealed:
        if state.phase != "IDLE":
            _fail("origin seal is not allowed in current phase")
        if (
            event.batch_count != state.batch_count
            or event.tombstone_count != state.tombstone_count
            or event.sealed_queries != state.sealed_queries
            or event.tombstoned_queries != state.tombstoned_queries
            or event.forfeited_iterations != state.forfeited_iterations
            or event.forfeited_queries != state.forfeited_queries
        ):
            _fail("origin seal counters mismatch")
        _assert_partitions(state)
        supplied = event.constraint_class_sha256s
        if tuple(sorted(set(supplied))) != supplied:
            _fail("constraint class is not sorted and distinct")
        if event.aborted:
            if supplied:
                _fail("aborted origin seal must publish an empty class")
            state.terminal_status = "aborted"
        else:
            if any(
                state.sealed_queries < floor.required_queries
                for floor in budget.query_floor_constraints
            ):
                _fail("query floor is not satisfied")
            if any(
                0 < batch.sealed_distinct_candidate_count
                < budget.batch_distinct_candidate_count_min
                for batch in state.sealed_batches.values()
            ):
                _fail("sealed batch distinct candidate count is below minimum")
            exact_class = tuple(sorted(state.rejected_constraints))
            if supplied != exact_class:
                _fail("certifiable class is not the exact rejected set")
            if len(exact_class) > budget.kmax:
                _fail("Kmax exceeded")
            state.terminal_status = "certifiable"
        state.constraint_class = supplied
        state.phase = "ORIGIN_SEALED"
        _assert_partitions(state)
        return
    _fail("unsupported semantic event")


@dataclass(frozen=True, slots=True)
class _AuthorityEntry:
    origin_id: str
    cell_key: str
    manifest: AuthorityManifest


@dataclass(frozen=True, slots=True)
class _Authority:
    blob_sha256: str
    entries: Mapping[str, _AuthorityEntry]


@dataclass(frozen=True, slots=True)
class _Store:
    repo_root: Path
    common_dir: Path
    runtime_root: Path
    authority_path: Path
    committed_ref: str
    fixture: bool

    @property
    def lock_path(self) -> Path:
        return self.runtime_root / "authority.lock"

    @property
    def head_path(self) -> Path:
        return self.runtime_root / "runtime-head.jsonl"

    def origin_path(self, origin_id: str) -> Path:
        return self.runtime_root / "origins" / origin_id / "events.jsonl"


_AUTHORITY_KEYS = frozenset({"authority_schema", "origins"})
_AUTHORITY_ENTRY_KEYS = frozenset({"cell_key", "manifest", "origin_id"})
_GIT_HARDENING = (
    "-c", "core.hooksPath=/dev/null",
    "-c", "core.fsmonitor=false",
    "-c", "core.useBuiltinFSMonitor=false",
    "-c", "maintenance.auto=false",
    "-c", "gc.auto=0",
)


def _git_env() -> dict[str, str]:
    result = {
        key: os.environ[key]
        for key in ("PATH", "LANG", "LC_ALL", "TZ")
        if key in os.environ
    }
    result.update({
        "LC_ALL": "C",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_PROTOCOL_FROM_USER": "0",
        "GIT_NO_REPLACE_OBJECTS": "1",
    })
    return result


def _git(repo: Path, arguments: Sequence[str]) -> bytes:
    if isinstance(arguments, (str, bytes)) or not all(type(item) is str for item in arguments):
        _fail("invalid Git arguments")
    try:
        completed = subprocess.run(
            ["git", *_GIT_HARDENING, *arguments],
            cwd=os.fspath(repo),
            env=_git_env(),
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        _fail("Git observation failed")
    if completed.returncode != 0:
        _fail("Git observation failed")
    return completed.stdout


def _git_text(repo: Path, arguments: Sequence[str]) -> str:
    try:
        return _git(repo, arguments).decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError:
        _fail("non-UTF-8 Git output")


def _store_for_repo(repo: Path, *, committed_ref: str, fixture: bool) -> _Store:
    repo = repo.resolve(strict=True)
    top = Path(_git_text(repo, ("rev-parse", "--path-format=absolute", "--show-toplevel")))
    if top.resolve(strict=True) != repo:
        _fail("repository root mismatch")
    common_raw = _git_text(repo, ("rev-parse", "--path-format=absolute", "--git-common-dir"))
    common = Path(common_raw).resolve(strict=True)
    authority = repo / AUTHORITY_RELATIVE_PATH
    runtime = common / "izanagi" / "reflux-origin-ledger" / "v2"
    return _Store(repo, common, runtime, authority, committed_ref, fixture)


def _production_store() -> _Store:
    module_path = Path(__file__).resolve(strict=True)
    repo = module_path.parents[2]
    store = _store_for_repo(repo, committed_ref="HEAD", fixture=False)
    expected = store.repo_root / "orchestrator" / "campaign" / "reflux_origin_ledger.py"
    if module_path != expected.resolve(strict=True):
        _fail("module path is outside the repository root")
    return store


def _safe_existing_regular(path: Path, *, label: str) -> os.stat_result:
    try:
        info = path.lstat()
    except OSError:
        _fail(f"required {label} is absent")
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        _fail(f"{label} is not a regular file")
    return info


def _check_no_symlink_ancestors(root: Path, path: Path) -> None:
    try:
        relative = path.relative_to(root)
    except ValueError:
        _fail("path escapes fixed root")
    try:
        root_info = root.lstat()
    except OSError:
        _fail("fixed root inspection failed")
    if stat.S_ISLNK(root_info.st_mode) or not stat.S_ISDIR(root_info.st_mode):
        _fail("fixed root is not a real directory")
    cursor = root
    for part in relative.parts[:-1]:
        cursor = cursor / part
        try:
            info = cursor.lstat()
        except FileNotFoundError:
            continue
        except OSError:
            _fail("path ancestor inspection failed")
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            _fail("path ancestor is not a real directory")


def _read_regular(path: Path, *, root: Path, maximum: int, label: str) -> bytes:
    _check_no_symlink_ancestors(root, path)
    flags = (
        os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        fd = os.open(path, flags)
    except OSError:
        _fail(f"cannot open {label}")
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
            _fail(f"invalid {label} size or type")
        chunks = []
        remaining = maximum + 1
        while remaining:
            part = os.read(fd, min(65536, remaining))
            if not part:
                break
            chunks.append(part)
            remaining -= len(part)
        raw = b"".join(chunks)
        if len(raw) > maximum:
            _fail(f"oversize {label}")
        after = path.stat(follow_symlinks=False)
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            _fail(f"{label} inode changed")
        return raw
    finally:
        os.close(fd)


def _authority_from_bytes(live: bytes) -> _Authority:
    if len(live) > _MAX_AUTHORITY_BYTES:
        _fail("oversize authority")
    if not live.endswith(b"\n") or live.endswith(b"\n\n"):
        _fail("authority must have one trailing LF")
    document = _strict_json(live[:-1], label="authority")
    obj = _exact_object(document, _AUTHORITY_KEYS, label="authority")
    if obj["authority_schema"] != AUTHORITY_SCHEMA_ID:
        _fail("unsupported authority version")
    origins = obj["origins"]
    if type(origins) is not list:
        _fail("invalid authority origins")
    entries: dict[str, _AuthorityEntry] = {}
    raw_cells: set[tuple[str, str, str, str]] = set()
    cell_digests: dict[str, tuple[str, str, str, str]] = {}
    previous_origin = ""
    aggregate_head_transaction_bytes = 0
    for raw_entry in origins:
        entry = _exact_object(raw_entry, _AUTHORITY_ENTRY_KEYS, label="authority entry")
        manifest = _manifest_from_object(entry["manifest"])
        origin_id = _sha(entry["origin_id"], label="authority origin ID")
        cell_key = _sha(entry["cell_key"], label="authority cell key")
        if origin_id != derive_origin_id(manifest) or cell_key != derive_cell_key(manifest):
            _fail("authority derived identity mismatch")
        if origin_id <= previous_origin:
            _fail("authority origins are not strictly sorted")
        previous_origin = origin_id
        cell = (
            str(manifest.workload["descriptor_sha256"]),
            manifest.axis_semantics_sha256,
            manifest.verifier_policy_sha256,
            manifest.environment_contract_sha256,
        )
        if cell in raw_cells:
            _fail("duplicate authority cell")
        raw_cells.add(cell)
        observed = cell_digests.setdefault(cell_key, cell)
        if observed != cell:
            _fail("authority cell digest collision")
        if origin_id in entries:
            _fail("duplicate authority origin")
        entries[origin_id] = _AuthorityEntry(origin_id, cell_key, manifest)
        _, head_transaction_bytes = _check_budget_codec_feasibility(
            manifest.budget_policy
        )
        aggregate_head_transaction_bytes += head_transaction_bytes
    try:
        aggregate_head_bytes = (
            len(_feasibility_head_genesis_frame(len(entries)))
            + aggregate_head_transaction_bytes
        )
    except RefluxOriginLedgerError:
        _fail("authority shared runtime head exceeds codec feasibility")
    if aggregate_head_bytes > _MAX_LEDGER_BYTES:
        _fail("authority shared runtime head exceeds ledger codec feasibility")
    canonical = _canonical_json({
        "authority_schema": AUTHORITY_SCHEMA_ID,
        "origins": [
            {
                "cell_key": item.cell_key,
                "manifest": _manifest_object(item.manifest),
                "origin_id": item.origin_id,
            }
            for item in entries.values()
        ],
    }) + b"\n"
    if live != canonical:
        _fail("authority bytes are not canonical")
    return _Authority(_sha256(live), MappingProxyType(entries))


def _load_authority(store: _Store) -> _Authority:
    ref = _string(store.committed_ref, label="committed ref")
    oid_raw = _git_text(store.repo_root, ("rev-parse", "--verify", f"{ref}^{{commit}}"))
    oid = _oid(oid_raw, label="resolved HEAD OID")
    committed = _git(
        store.repo_root,
        ("cat-file", "blob", f"{oid}:{AUTHORITY_RELATIVE_PATH}"),
    )
    if len(committed) > _MAX_AUTHORITY_BYTES:
        _fail("oversize committed authority")
    live = _read_regular(
        store.authority_path,
        root=store.repo_root,
        maximum=_MAX_AUTHORITY_BYTES,
        label="authority",
    )
    if live != committed:
        _fail("live authority differs from committed bytes")
    return _authority_from_bytes(live)


_path_mutex_guard = threading.Lock()
_path_mutexes: dict[str, threading.Lock] = {}
_held_paths = threading.local()
_poison_guard = threading.Lock()
_poisoned_store_roots: set[str] = set()


def _mutex_for(path: Path) -> threading.Lock:
    key = os.fspath(path)
    with _path_mutex_guard:
        return _path_mutexes.setdefault(key, threading.Lock())


def _poison_store(store: _Store) -> None:
    with _poison_guard:
        _poisoned_store_roots.add(os.fspath(store.runtime_root))


def _assert_store_healthy(store: _Store) -> None:
    with _poison_guard:
        if os.fspath(store.runtime_root) in _poisoned_store_roots:
            _fail("origin ledger store is poisoned after durability failure")


def _mkdir_fixed(path: Path, *, root: Path) -> None:
    try:
        relative = path.relative_to(root)
    except ValueError:
        _fail("runtime directory escapes common dir")
    try:
        root_info = root.lstat()
    except OSError:
        _fail("runtime root inspection failed")
    if stat.S_ISLNK(root_info.st_mode) or not stat.S_ISDIR(root_info.st_mode):
        _fail("runtime root is not a real directory")
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        try:
            os.mkdir(cursor, 0o700)
        except FileExistsError:
            info = cursor.lstat()
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                _fail("runtime ancestor is not a real directory")
        except OSError:
            _fail("cannot create runtime directory")


@contextmanager
def _locked(store: _Store, *, create: bool = False) -> Iterator[_Authority]:
    if create:
        _mkdir_fixed(store.runtime_root, root=store.common_dir)
    held = getattr(_held_paths, "value", set())
    key = os.fspath(store.lock_path)
    if key in held:
        raise _LockReentryError("origin ledger lock reentry") from None
    mutex = _mutex_for(store.lock_path)
    mutex.acquire()
    fd = -1
    try:
        held = set(held)
        held.add(key)
        _held_paths.value = held
        _assert_store_healthy(store)
        _check_no_symlink_ancestors(store.common_dir, store.lock_path)
        flags = os.O_RDWR | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        if create:
            flags |= os.O_CREAT
        for _ in range(4):
            try:
                fd = os.open(store.lock_path, flags, 0o600)
            except OSError:
                _fail("cannot open authority lock")
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                os.close(fd)
                fd = -1
                _fail("authority lock is not regular")
            _fault_point(store, "lock:before-flock")
            fcntl.flock(fd, fcntl.LOCK_EX)
            _fault_point(store, "lock:flocked")
            try:
                live = store.lock_path.stat(follow_symlinks=False)
            except OSError:
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
                fd = -1
                continue
            if (info.st_dev, info.st_ino) == (live.st_dev, live.st_ino):
                break
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
            fd = -1
        else:
            _fail("authority lock inode is unstable")
        yield _load_authority(store)
    finally:
        if fd >= 0:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)
        current = set(getattr(_held_paths, "value", set()))
        current.discard(key)
        _held_paths.value = current
        mutex.release()


def _write_all(fd: int, raw: bytes) -> None:
    view = memoryview(raw)
    while view:
        count = os.write(fd, view)
        if count <= 0:
            _fail("short append write")
        view = view[count:]


_FAULT_HOOK: Any = None


def _fault_point(store: _Store, label: str) -> None:
    if not store.fixture:
        return
    hook = _FAULT_HOOK
    if hook is not None:
        hook(label)


def _append(store: _Store, path: Path, raw: bytes, *, root: Path, label: str) -> None:
    if not raw.endswith(b"\n") or len(raw) > _MAX_RECORD_BYTES:
        _fail("invalid append frame")
    _check_no_symlink_ancestors(root, path)
    flags = (
        os.O_WRONLY | os.O_APPEND | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        fd = os.open(path, flags)
    except OSError:
        _fail(f"cannot open {label}")
    try:
        info = os.fstat(fd)
        live = path.stat(follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode) or (info.st_dev, info.st_ino) != (live.st_dev, live.st_ino):
            _fail(f"invalid {label} inode")
        try:
            _write_all(fd, raw)
            _fault_point(store, f"{label}:written")
        except OSError:
            _fail(f"{label} append or fsync failed")
        try:
            os.fsync(fd)
            _fault_point(store, f"{label}:fsynced")
        except OSError:
            _poison_store(store)
            _fail(f"{label} append or fsync failed")
    finally:
        os.close(fd)


def _truncate(store: _Store, path: Path, length: int, *, root: Path, label: str) -> None:
    _check_no_symlink_ancestors(root, path)
    flags = os.O_WRONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError:
        _fail(f"cannot repair {label}")
    try:
        info = os.fstat(fd)
        live = path.stat(follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode) or (info.st_dev, info.st_ino) != (live.st_dev, live.st_ino):
            _fail(f"invalid {label} repair inode")
        try:
            os.ftruncate(fd, length)
            os.fsync(fd)
        except OSError:
            _poison_store(store)
            _fail(f"{label} truncate or fsync failed")
    finally:
        os.close(fd)


def _fsync_existing(store: _Store, path: Path, *, root: Path, label: str) -> None:
    _check_no_symlink_ancestors(root, path)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError:
        _fail(f"cannot open {label} for durability retry")
    try:
        info = os.fstat(fd)
        live = path.stat(follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode) or (info.st_dev, info.st_ino) != (live.st_dev, live.st_ino):
            _fail(f"invalid {label} durability inode")
        try:
            os.fsync(fd)
        except OSError:
            _poison_store(store)
            _fail(f"{label} durability retry failed")
    finally:
        os.close(fd)


@dataclass(frozen=True, slots=True)
class _Jsonl:
    records: tuple[dict[str, Any], ...]
    frames: tuple[bytes, ...]
    complete_length: int
    total_length: int
    tail: bytes


def _read_jsonl(path: Path, *, root: Path, label: str) -> _Jsonl:
    raw = _read_regular(path, root=root, maximum=_MAX_LEDGER_BYTES, label=label)
    if not raw:
        _fail(f"zero-byte {label}")
    pieces = raw.splitlines(keepends=True)
    frames: list[bytes] = []
    tail = b""
    if pieces and not pieces[-1].endswith(b"\n"):
        tail = pieces.pop()
    records: list[dict[str, Any]] = []
    for frame in pieces:
        if len(frame) > _MAX_RECORD_BYTES or not frame.endswith(b"\n"):
            _fail(f"invalid {label} record framing")
        value = _strict_json(frame[:-1], label=label)
        if type(value) is not dict or _canonical_json(value) + b"\n" != frame:
            _fail(f"non-canonical {label} record")
        records.append(value)
        frames.append(frame)
    if len(tail) > _MAX_RECORD_BYTES:
        _fail(f"oversize partial {label} tail")
    if tail:
        try:
            tail.decode("ascii", errors="strict")
        except UnicodeDecodeError:
            _fail(f"non-ASCII partial {label} tail")
        try:
            complete_tail = _strict_json(tail, label=label)
        except RefluxOriginLedgerError:
            complete_tail = _MISSING
        if complete_tail is not _MISSING and _canonical_json(complete_tail) == tail:
            _fail(f"complete {label} record lacks LF")
    complete = sum(map(len, frames))
    return _Jsonl(tuple(records), tuple(frames), complete, len(raw), tail)


def _record_frame(value: Mapping[str, object]) -> bytes:
    raw = _canonical_json(dict(value)) + b"\n"
    if len(raw) > _MAX_RECORD_BYTES:
        _fail("record exceeds maximum size")
    return raw


def _feasibility_event_frame(event: OriginEvent) -> bytes:
    event_type, payload = _event_payload(event)
    return _record_frame(_event_record(
        origin_id="f" * 64,
        operation_id="x" * 128,
        event_index=_MAX_INTEGER,
        previous_event_sha256="e" * 64,
        event_type=event_type,
        payload=payload,
    ))


def _dummy_hashes(count: int, *, offset: int = 0) -> tuple[str, ...]:
    return tuple(f"{offset + index + 1:064x}" for index in range(count))


def _feasibility_batch_frames(
    member_row_count: int,
    *,
    tombstoned: bool,
) -> tuple[bytes, bytes, bytes, bytes]:
    hashes = _dummy_hashes(member_row_count)
    committed = tuple(
        CommittedBatchMember(_MAX_INTEGER, digest) for digest in hashes
    )
    prepared = tuple(
        PreparedBatchMember(_MAX_INTEGER, digest, digest, digest)
        for digest in hashes
    )
    opened = []
    for index, digest in enumerate(hashes):
        salt_base = index * 3 + 1
        opened.append(OpenedBatchMember(
            query_ordinal=_MAX_INTEGER,
            replicate_ordinal=_MAX_INTEGER,
            candidate_salt=f"{salt_base:032x}"[-32:],
            candidate_bytes=f"{index % 32:05b}".encode("ascii"),
            result_evidence_salt=f"{salt_base + 1:032x}"[-32:],
            outcome="tombstoned" if tombstoned else "rejected",
            evidence_digest=None if tombstoned else EvidenceDigest(digest),
            constraint_salt=f"{salt_base + 2:032x}"[-32:],
            constraint_sha256=None if tombstoned else digest,
        ))
    return (
        _feasibility_event_frame(BatchReserved(
            "x" * 128, _MAX_INTEGER, member_row_count, _MAX_INTEGER
        )),
        _feasibility_event_frame(BatchCommitted(
            "x" * 128, _MAX_INTEGER, committed
        )),
        _feasibility_event_frame(BatchResultsPrepared(
            "x" * 128, prepared
        )),
        _feasibility_event_frame(BatchSealed(
            "x" * 128, tuple(opened)
        )),
    )


def _feasibility_abandoned_frames(
    member_row_count: int,
) -> tuple[bytes, bytes]:
    return (
        _feasibility_event_frame(BatchReserved(
            "x" * 128, _MAX_INTEGER, member_row_count, _MAX_INTEGER
        )),
        _feasibility_event_frame(BatchReservationAbandoned("x" * 128)),
    )


def _affine_batch_bytes(
    *,
    batches: int,
    members: int,
    tombstoned: bool,
) -> int:
    one = _feasibility_batch_frames(1, tombstoned=tombstoned)
    two = _feasibility_batch_frames(2, tombstoned=tombstoned)
    base = sum(map(len, one))
    increment = sum(map(len, two)) - base
    # Reservation, commit, and seal carry member row count.  The seal also
    # carries two distinct-candidate counts with an upper bound of 32.  Frames
    # for one and two rows have one-digit counts, so reserve every remaining
    # decimal expansion per batch.
    count_digit_reserve = (
        3 * (len(str(_MAX_BATCH_MEMBER_ROW_COUNT)) - 1)
        + 2 * (len(str(32)) - 1)
    )
    return (
        batches * base
        + (members - batches) * increment
        + batches * count_digit_reserve
    )


def _feasibility_head_genesis_frame(origin_count: int) -> bytes:
    return _record_frame(_head_record(
        record_index=0,
        previous_record_sha256=_NULL_SHA256,
        record_type="runtime-opened",
        payload={
            "authority_blob_sha256": "a" * 64,
            "origin_heads": [
                {
                    "origin_id": "f" * 64,
                    "event_index": 0,
                    "event_sha256": "b" * 64,
                }
                for _ in range(origin_count)
            ],
        },
    ))


def _check_budget_codec_feasibility(policy: BudgetPolicy) -> tuple[int, int]:
    """Separate per-batch frame feasibility from origin-total capacity."""
    member_row_min = policy.batch_member_row_count_min
    candidate_min = policy.batch_distinct_candidate_count_min
    effective_row_min = max(member_row_min, candidate_min)
    if member_row_min > _MAX_BATCH_MEMBER_ROW_COUNT:
        _fail("batch minimum exceeds codec feasibility")
    try:
        _feasibility_batch_frames(effective_row_min, tombstoned=False)
        _feasibility_batch_frames(effective_row_min, tombstoned=True)
        _feasibility_abandoned_frames(effective_row_min)
    except RefluxOriginLedgerError:
        _fail("batch minimum exceeds codec feasibility")
    if policy.qmax > policy.imax * _MAX_BATCH_MEMBER_ROW_COUNT:
        _fail("Qmax cannot be partitioned into feasible batches")
    maximum_floor = max(
        floor.required_queries for floor in policy.query_floor_constraints
    )
    minimum_floor_batches = (
        maximum_floor + _MAX_BATCH_MEMBER_ROW_COUNT - 1
    ) // _MAX_BATCH_MEMBER_ROW_COUNT
    maximum_budget_batches = min(
        policy.imax, policy.qmax // effective_row_min
    )
    if minimum_floor_batches > maximum_budget_batches:
        _fail("query floor cannot be partitioned into feasible batches")
    if policy.kmax > _MAX_CLASS_CARDINALITY:
        _fail("Kmax exceeds codec feasibility")
    try:
        class_frame = _feasibility_event_frame(OriginSealed(
            False,
            _dummy_hashes(policy.kmax),
            _MAX_INTEGER,
            _MAX_INTEGER,
            _MAX_INTEGER,
            _MAX_INTEGER,
            _MAX_INTEGER,
            _MAX_INTEGER,
        ))
    except RefluxOriginLedgerError:
        _fail("Kmax exceeds codec feasibility")
    head_prepared = _record_frame(_head_record(
        record_index=_MAX_INTEGER,
        previous_record_sha256="e" * 64,
        record_type="head-prepared",
        payload={
            "base_state_commitment": "a" * 64,
            "request_sha256": "b" * 64,
            "origin_id": "f" * 64,
            "operation_id": "x" * 128,
            "old_event_index": _MAX_INTEGER,
            "old_event_sha256": "c" * 64,
            "old_event_byte_length": _MAX_LEDGER_BYTES,
            "next_event_binding_sha256": "d" * 64,
            "prospective_public_state_sha256": "e" * 64,
        },
    ))
    head_committed = _record_frame(_head_record(
        record_index=_MAX_INTEGER,
        previous_record_sha256="e" * 64,
        record_type="head-committed",
        payload={
            "prepared_record_sha256": "a" * 64,
            "origin_id": "f" * 64,
            "operation_id": "x" * 128,
            "event_index": _MAX_INTEGER,
            "event_sha256": "b" * 64,
        },
    ))
    origin_genesis = _record_frame(_event_record(
        origin_id="f" * 64,
        operation_id="origin-opened:" + "f" * 64,
        event_index=0,
        previous_event_sha256=_NULL_SHA256,
        event_type="origin-opened",
        payload={
            "authority_blob_sha256": "a" * 64,
            "cell_key": "b" * 64,
        },
    ))
    head_genesis = _feasibility_head_genesis_frame(1)
    batch_count = min(policy.imax, policy.qmax // effective_row_min)
    normal_bytes = _affine_batch_bytes(
        batches=batch_count,
        members=policy.qmax,
        tombstoned=False,
    )
    tombstone_bytes = _affine_batch_bytes(
        batches=batch_count,
        members=policy.qmax,
        tombstoned=True,
    )
    origin_bytes = len(origin_genesis) + max(normal_bytes, tombstone_bytes) + len(class_frame)
    head_transaction_bytes = (
        (batch_count * 4 + 1) * (len(head_prepared) + len(head_committed))
    )
    head_bytes = len(head_genesis) + head_transaction_bytes
    if origin_bytes > _MAX_LEDGER_BYTES or head_bytes > _MAX_LEDGER_BYTES:
        _fail("authority budget exceeds ledger codec feasibility")
    return origin_bytes, head_transaction_bytes


def _event_record(
    *,
    origin_id: str,
    operation_id: str,
    event_index: int,
    previous_event_sha256: str,
    event_type: str,
    payload: Mapping[str, object],
) -> dict[str, object]:
    core: dict[str, object] = {
        "schema_version": _EVENT_SCHEMA_ID,
        "event_index": event_index,
        "previous_event_sha256": previous_event_sha256,
        "origin_id": origin_id,
        "operation_id": operation_id,
        "event_type": event_type,
        "payload": dict(payload),
    }
    core["event_sha256"] = _sha256(_canonical_json(core))
    return core


def _head_record(
    *,
    record_index: int,
    previous_record_sha256: str,
    record_type: str,
    payload: Mapping[str, object],
) -> dict[str, object]:
    core: dict[str, object] = {
        "schema_version": _HEAD_SCHEMA_ID,
        "record_index": record_index,
        "previous_record_sha256": previous_record_sha256,
        "record_type": record_type,
        "payload": dict(payload),
    }
    core["record_sha256"] = _sha256(_canonical_json(core))
    return core


def _validate_hash_record(
    record: dict[str, Any],
    *,
    keys: frozenset[str],
    hash_key: str,
    label: str,
) -> None:
    _exact_object(record, keys, label=label)
    observed = _sha(record[hash_key], label=f"{label} digest")
    core = {key: value for key, value in record.items() if key != hash_key}
    if observed != _sha256(_canonical_json(core)):
        _fail(f"{label} digest mismatch")


_EVENT_RECORD_KEYS = frozenset({
    "schema_version", "event_index", "previous_event_sha256", "origin_id",
    "operation_id", "event_type", "payload", "event_sha256",
})
_HEAD_RECORD_KEYS = frozenset({
    "schema_version", "record_index", "previous_record_sha256", "record_type",
    "payload", "record_sha256",
})


@dataclass(frozen=True, slots=True)
class _ParsedEvent:
    record: dict[str, Any]
    event: OriginEvent | None
    frame: bytes


def _parse_event_records(
    data: _Jsonl,
    *,
    entry: _AuthorityEntry,
    authority_sha: str,
) -> tuple[_ParsedEvent, ...]:
    parsed: list[_ParsedEvent] = []
    previous = _NULL_SHA256
    state = _SemanticState()
    for expected_index, (record, frame) in enumerate(zip(data.records, data.frames, strict=True)):
        _validate_hash_record(
            record,
            keys=_EVENT_RECORD_KEYS,
            hash_key="event_sha256",
            label="origin event",
        )
        if (
            record["schema_version"] != _EVENT_SCHEMA_ID
            or _integer(record["event_index"], label="event index") != expected_index
            or _sha(record["previous_event_sha256"], label="previous event") != previous
            or _sha(record["origin_id"], label="event origin") != entry.origin_id
        ):
            _fail("origin event chain mismatch")
        operation = _string(record["operation_id"], label="operation ID", token=True)
        event = _event_from_payload(record["event_type"], record["payload"])
        if expected_index == 0:
            if operation != f"origin-opened:{entry.origin_id}" or event is not None:
                _fail("invalid origin genesis")
            payload = _exact_object(
                record["payload"],
                frozenset({"authority_blob_sha256", "cell_key"}),
                label="origin genesis",
            )
            if (
                _sha(payload["authority_blob_sha256"], label="genesis authority")
                != authority_sha
                or _sha(payload["cell_key"], label="genesis cell") != entry.cell_key
            ):
                _fail("origin genesis authority mismatch")
        else:
            canonical_type, canonical_payload = _event_payload(event)
            if canonical_type != record["event_type"] or canonical_payload != record["payload"]:
                _fail("non-canonical event payload")
        _apply_event(state, event, manifest=entry.manifest, origin_id=entry.origin_id)
        previous = record["event_sha256"]
        parsed.append(_ParsedEvent(record, event, frame))
    return tuple(parsed)


def _head_prefix_length(data: _Jsonl, count: int) -> int:
    return sum(len(frame) for frame in data.frames[:count])


def _state_commitment(
    *,
    authority_sha: str,
    head_record: Mapping[str, object],
    head_byte_length: int,
    head_tail: bytes,
    transaction_phase: str,
    prepared_record_sha256: str | None,
    prepared_request_sha256: str | None,
    committed_heads: Mapping[str, tuple[int, str]],
    origin_states: Mapping[str, _SemanticState],
) -> str:
    origins = []
    for origin_id in sorted(committed_heads):
        event_index, event_sha = committed_heads[origin_id]
        origins.append([
            origin_id,
            event_index,
            event_sha,
            _semantic_sha(origin_states[origin_id]),
        ])
    preimage = {
        "authority_blob_sha256": authority_sha,
        "runtime_head_record_index": head_record["record_index"],
        "runtime_head_record_sha256": head_record["record_sha256"],
        "head_file_byte_length": head_byte_length,
        "head_partial_tail_sha256": _sha256(head_tail) if head_tail else None,
        "transaction_phase": transaction_phase,
        "prepared_record_sha256": prepared_record_sha256,
        "prepared_request_sha256": prepared_request_sha256,
        "origins": origins,
    }
    return _sha256(_DOMAIN_STATE + _canonical_json(preimage))


def _replay_state_prefix(
    *,
    authority: _Authority,
    parsed_events: Mapping[str, tuple[_ParsedEvent, ...]],
    committed_heads: Mapping[str, tuple[int, str]],
) -> dict[str, _SemanticState]:
    states: dict[str, _SemanticState] = {}
    for origin_id, entry in authority.entries.items():
        limit, expected_sha = committed_heads[origin_id]
        events = parsed_events[origin_id]
        if limit < 0 or limit >= len(events) or events[limit].record["event_sha256"] != expected_sha:
            _fail("committed head points outside origin ledger")
        state = _SemanticState()
        for item in events[:limit + 1]:
            _apply_event(state, item.event, manifest=entry.manifest, origin_id=origin_id)
        states[origin_id] = state
    return states


@dataclass(frozen=True, slots=True)
class _CommittedOperation:
    origin_id: str
    operation_id: str
    base_state_commitment: str
    request_sha256: str
    event_sha256: str
    event_index: int
    prepared_record_sha256: str
    committed_record_position: int


@dataclass(frozen=True, slots=True)
class _Replay:
    head_data: _Jsonl
    parsed_events: Mapping[str, tuple[_ParsedEvent, ...]]
    committed_heads: Mapping[str, tuple[int, str]]
    states: Mapping[str, _SemanticState]
    operations: Mapping[str, _CommittedOperation]
    operation_ids: frozenset[str]
    prepared: dict[str, Any] | None
    current_state_commitment: str
    resulting_commitments: Mapping[str, str]


def _validate_head_record(record: dict[str, Any], *, index: int, previous: str) -> None:
    _validate_hash_record(
        record,
        keys=_HEAD_RECORD_KEYS,
        hash_key="record_sha256",
        label="runtime head record",
    )
    if (
        record["schema_version"] != _HEAD_SCHEMA_ID
        or _integer(record["record_index"], label="head record index") != index
        or _sha(record["previous_record_sha256"], label="previous head record") != previous
    ):
        _fail("runtime head chain mismatch")


def _replay_once(store: _Store, authority: _Authority) -> _Replay:
    head = _read_jsonl(store.head_path, root=store.runtime_root, label="runtime head")
    if not head.records:
        _fail("runtime head lacks genesis")
    previous = _NULL_SHA256
    for index, record in enumerate(head.records):
        _validate_head_record(record, index=index, previous=previous)
        previous = record["record_sha256"]
    opened = head.records[0]
    if opened["record_type"] != "runtime-opened":
        _fail("runtime head lacks opening record")
    opened_payload = _exact_object(
        opened["payload"],
        frozenset({"authority_blob_sha256", "origin_heads"}),
        label="runtime opened payload",
    )
    if _sha(opened_payload["authority_blob_sha256"], label="runtime authority") != authority.blob_sha256:
        _fail("authority version mismatch")
    raw_heads = opened_payload["origin_heads"]
    if type(raw_heads) is not list or len(raw_heads) != len(authority.entries):
        _fail("runtime genesis origin set mismatch")
    committed_heads: dict[str, tuple[int, str]] = {}
    parsed_events: dict[str, tuple[_ParsedEvent, ...]] = {}
    for expected_origin, raw_head in zip(sorted(authority.entries), raw_heads, strict=True):
        obj = _exact_object(
            raw_head,
            frozenset({"origin_id", "event_index", "event_sha256"}),
            label="genesis origin head",
        )
        origin_id = _sha(obj["origin_id"], label="genesis origin ID")
        if origin_id != expected_origin or _integer(obj["event_index"], label="genesis event index") != 0:
            _fail("runtime genesis origin order mismatch")
        event_sha = _sha(obj["event_sha256"], label="genesis event digest")
        committed_heads[origin_id] = (0, event_sha)
    for origin_id, entry in authority.entries.items():
        data = _read_jsonl(
            store.origin_path(origin_id),
            root=store.runtime_root,
            label=f"origin ledger {origin_id}",
        )
        # Parse and validate only complete frames here.  A caller that mutates
        # state truncates any incomplete tail after this prefix has validated.
        complete_data = data
        parsed_events[origin_id] = _parse_event_records(
            complete_data,
            entry=entry,
            authority_sha=authority.blob_sha256,
        )
        if not parsed_events[origin_id]:
            _fail("origin ledger lacks genesis")
        if parsed_events[origin_id][0].record["event_sha256"] != committed_heads[origin_id][1]:
            _fail("runtime genesis event mismatch")
    operations: dict[str, _CommittedOperation] = {}
    operation_ids: set[str] = set()
    for origin_id, events in parsed_events.items():
        genesis = events[0].record
        genesis_operation = str(genesis["operation_id"])
        if genesis_operation in operation_ids:
            _fail("committed operation ID was reused")
        operation_ids.add(genesis_operation)
    prepared: dict[str, Any] | None = None
    prepared_position = -1
    position = 1
    while position < len(head.records):
        record = head.records[position]
        if record["record_type"] != "head-prepared" or prepared is not None:
            _fail("runtime head expected one prepared record")
        payload = _exact_object(
            record["payload"],
            frozenset({
                "base_state_commitment", "request_sha256", "origin_id", "operation_id",
                "old_event_index", "old_event_sha256", "old_event_byte_length",
                "next_event_binding_sha256", "prospective_public_state_sha256",
            }),
            label="head prepared payload",
        )
        origin_id = _sha(payload["origin_id"], label="prepared origin")
        if origin_id not in authority.entries:
            _fail("prepared unknown origin")
        old_index, old_sha = committed_heads[origin_id]
        parsed_for_origin = parsed_events[origin_id]
        if (
            _integer(payload["old_event_index"], label="old event index") != old_index
            or _sha(payload["old_event_sha256"], label="old event digest") != old_sha
            or _integer(payload["old_event_byte_length"], label="old event byte length")
            != sum(len(item.frame) for item in parsed_for_origin[:old_index + 1])
        ):
            _fail("prepared base event head mismatch")
        operation_id = _string(payload["operation_id"], label="operation ID", token=True)
        if operation_id in operation_ids:
            _fail("committed operation ID was reused")
        prepared = record
        prepared_position = position
        position += 1
        if position >= len(head.records):
            break
        committed = head.records[position]
        if committed["record_type"] != "head-committed":
            _fail("prepared record is followed by a non-commit")
        commit_payload = _exact_object(
            committed["payload"],
            frozenset({
                "prepared_record_sha256", "origin_id", "operation_id",
                "event_index", "event_sha256",
            }),
            label="head committed payload",
        )
        event_index = _integer(commit_payload["event_index"], label="committed event index")
        event_sha = _sha(commit_payload["event_sha256"], label="committed event digest")
        if event_index >= len(parsed_for_origin):
            _fail("committed head points outside origin ledger")
        if (
            _sha(commit_payload["prepared_record_sha256"], label="prepared record digest")
            != prepared["record_sha256"]
            or _sha(commit_payload["origin_id"], label="committed origin") != origin_id
            or _string(commit_payload["operation_id"], label="operation ID", token=True)
            != operation_id
            or event_index != old_index + 1
            or parsed_for_origin[event_index].record["event_sha256"] != event_sha
            or parsed_for_origin[event_index].record["operation_id"] != operation_id
        ):
            _fail("head commit does not match prepared event")
        actual_event = parsed_for_origin[event_index]
        actual_type = actual_event.record["event_type"]
        actual_payload = actual_event.record["payload"]
        before_states = _replay_state_prefix(
            authority=authority,
            parsed_events=parsed_events,
            committed_heads=committed_heads,
        )
        calculated_request = _request_sha256(
            base_state_commitment=payload["base_state_commitment"],
            origin_id=origin_id,
            operation_id=operation_id,
            event_type=actual_type,
            payload=actual_payload,
            state=before_states[origin_id],
        )
        calculated_binding = _prepared_event_binding_sha256(
            record=actual_event.record,
            event_type=actual_type,
            payload=actual_payload,
            state=before_states[origin_id],
        )
        calculated_base = _state_commitment(
            authority_sha=authority.blob_sha256,
            head_record=head.records[prepared_position - 1],
            head_byte_length=_head_prefix_length(head, prepared_position),
            head_tail=b"",
            transaction_phase="clean",
            prepared_record_sha256=None,
            prepared_request_sha256=None,
            committed_heads=committed_heads,
            origin_states=before_states,
        )
        _apply_event(
            before_states[origin_id],
            actual_event.event,
            manifest=authority.entries[origin_id].manifest,
            origin_id=origin_id,
        )
        if (
            _sha(payload["base_state_commitment"], label="prepared base")
            != calculated_base
            or _sha(payload["request_sha256"], label="prepared request")
            != calculated_request
            or _sha(payload["next_event_binding_sha256"], label="next event binding")
            != calculated_binding
            or _sha(
                payload["prospective_public_state_sha256"],
                label="prospective public state",
            )
            != _preseal_semantic_sha(before_states[origin_id])
        ):
            _fail("prepared request or semantic state mismatch")
        committed_heads[origin_id] = (event_index, event_sha)
        operation = _CommittedOperation(
            origin_id=origin_id,
            operation_id=operation_id,
            base_state_commitment=_sha(
                payload["base_state_commitment"], label="base state commitment"
            ),
            request_sha256=_sha(payload["request_sha256"], label="request digest"),
            event_sha256=event_sha,
            event_index=event_index,
            prepared_record_sha256=prepared["record_sha256"],
            committed_record_position=position,
        )
        operations[operation_id] = operation
        operation_ids.add(operation_id)
        prepared = None
        prepared_position = -1
        position += 1
    states = _replay_state_prefix(
        authority=authority,
        parsed_events=parsed_events,
        committed_heads=committed_heads,
    )
    # Only a durable prepared transaction may have one physical event past a committed head.
    for origin_id, events in parsed_events.items():
        committed_index = committed_heads[origin_id][0]
        extra_count = len(events) - committed_index - 1
        if extra_count:
            if (
                extra_count != 1
                or prepared is None
                or prepared["payload"]["origin_id"] != origin_id
                or _prepared_event_binding_sha256(
                    record=events[-1].record,
                    event_type=str(events[-1].record["event_type"]),
                    payload=events[-1].record["payload"],
                    state=states[origin_id],
                ) != prepared["payload"]["next_event_binding_sha256"]
            ):
                _fail("origin ledger contains an uncommitted event")
    if prepared is not None:
        prepared_payload = prepared["payload"]
        phase = "prepared"
        prepared_sha = prepared["record_sha256"]
        prepared_request = _sha(prepared_payload["request_sha256"], label="prepared request")
    else:
        phase = "clean"
        prepared_sha = None
        prepared_request = None
    current = _state_commitment(
        authority_sha=authority.blob_sha256,
        head_record=head.records[-1],
        head_byte_length=head.total_length,
        head_tail=head.tail,
        transaction_phase=phase,
        prepared_record_sha256=prepared_sha,
        prepared_request_sha256=prepared_request,
        committed_heads=committed_heads,
        origin_states=states,
    )
    resulting: dict[str, str] = {}
    # Rebuild each historic clean prefix; no production helper supplies test goldens.
    historic_heads: dict[str, tuple[int, str]] = {
        origin_id: (0, parsed_events[origin_id][0].record["event_sha256"])
        for origin_id in authority.entries
    }
    for index, record in enumerate(head.records[1:], start=1):
        if record["record_type"] == "head-prepared":
            continue
        payload = record["payload"]
        origin_id = payload["origin_id"]
        historic_heads[origin_id] = (payload["event_index"], payload["event_sha256"])
        historic_states = _replay_state_prefix(
            authority=authority,
            parsed_events=parsed_events,
            committed_heads=historic_heads,
        )
        operation_id = payload["operation_id"]
        resulting[operation_id] = _state_commitment(
            authority_sha=authority.blob_sha256,
            head_record=record,
            head_byte_length=_head_prefix_length(head, index + 1),
            head_tail=b"",
            transaction_phase="clean",
            prepared_record_sha256=None,
            prepared_request_sha256=None,
            committed_heads=historic_heads,
            origin_states=historic_states,
        )
    return _Replay(
        head,
        MappingProxyType(parsed_events),
        MappingProxyType(committed_heads),
        MappingProxyType(states),
        MappingProxyType(operations),
        frozenset(operation_ids),
        prepared,
        current,
        MappingProxyType(resulting),
    )


def _create_file(store: _Store, path: Path, raw: bytes, *, root: Path, label: str) -> None:
    _check_no_symlink_ancestors(root, path)
    flags = (
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        fd = os.open(path, flags, 0o600)
    except OSError:
        _fail(f"cannot create {label}")
    try:
        _write_all(fd, raw)
        try:
            os.fsync(fd)
        except OSError:
            _poison_store(store)
            _fail(f"{label} fsync failed")
    finally:
        os.close(fd)
    try:
        directory_fd = os.open(
            path.parent,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0),
        )
    except OSError:
        _fail(f"cannot open {label} parent")
    try:
        try:
            os.fsync(directory_fd)
        except OSError:
            _poison_store(store)
            _fail(f"{label} parent fsync failed")
    finally:
        os.close(directory_fd)


def _initialize_locked(store: _Store, authority: _Authority) -> None:
    if not store.fixture:
        _fail("production runtime initialization is forbidden")
    if store.head_path.exists():
        _fail("fixture runtime is already initialized")
    _mkdir_fixed(store.runtime_root / "origins", root=store.common_dir)
    genesis_heads = []
    for origin_id in sorted(authority.entries):
        entry = authority.entries[origin_id]
        origin_dir = store.origin_path(origin_id).parent
        _mkdir_fixed(origin_dir, root=store.common_dir)
        genesis = _event_record(
            origin_id=origin_id,
            operation_id=f"origin-opened:{origin_id}",
            event_index=0,
            previous_event_sha256=_NULL_SHA256,
            event_type="origin-opened",
            payload={
                "authority_blob_sha256": authority.blob_sha256,
                "cell_key": entry.cell_key,
            },
        )
        _create_file(
            store,
            store.origin_path(origin_id),
            _record_frame(genesis),
            root=store.runtime_root,
            label="origin genesis",
        )
        genesis_heads.append({
            "origin_id": origin_id,
            "event_index": 0,
            "event_sha256": genesis["event_sha256"],
        })
    opened = _head_record(
        record_index=0,
        previous_record_sha256=_NULL_SHA256,
        record_type="runtime-opened",
        payload={
            "authority_blob_sha256": authority.blob_sha256,
            "origin_heads": genesis_heads,
        },
    )
    _create_file(
        store,
        store.head_path,
        _record_frame(opened),
        root=store.runtime_root,
        label="runtime head genesis",
    )


def _fixture_store_for_test(
    temp_git_repo: os.PathLike[str] | str,
    committed_ref: str = "HEAD",
    *,
    initialize: bool = True,
) -> _Store:
    """Private seam: substitute only a complete temporary Git repository."""
    store = _store_for_repo(Path(temp_git_repo), committed_ref=committed_ref, fixture=True)
    with _locked(store, create=True) as authority:
        if initialize:
            if store.head_path.exists():
                _replay(store, authority)
            else:
                _initialize_locked(store, authority)
        elif store.head_path.exists():
            _replay(store, authority)
    return store


def _request_sha256(
    *,
    base_state_commitment: str,
    origin_id: str,
    operation_id: str,
    event_type: str,
    payload: Mapping[str, object],
    state: _SemanticState,
) -> str:
    projected_payload = _prepared_payload_projection(event_type, payload, state=state)
    return _sha256(_canonical_json({
        "base_state_commitment": base_state_commitment,
        "origin_id": origin_id,
        "operation_id": operation_id,
        "event_type": event_type,
        "payload": projected_payload,
    }))


def _prepared_payload_projection(
    event_type: str,
    payload: Mapping[str, object],
    *,
    state: _SemanticState,
) -> dict[str, object]:
    """Return the only payload bytes allowed in a durable pre-event record."""
    if event_type == "batch-sealed":
        batch = state.open_batch
        if state.phase != "RESULTS_PREPARED" or batch is None:
            _fail("batch seal projection requires prepared results")
        return {
            "batch_id": payload["batch_id"],
            "members": [
                _prepared_member_object(member) for member in batch["members"]
            ],
        }
    if event_type == "origin-sealed":
        return {
            "seal_kind": payload["seal_kind"],
            "batch_count": payload["batch_count"],
            "tombstone_count": payload["tombstone_count"],
            "sealed_queries": payload["sealed_queries"],
            "tombstoned_queries": payload["tombstoned_queries"],
            "forfeited_iterations": payload["forfeited_iterations"],
            "forfeited_queries": payload["forfeited_queries"],
        }
    return dict(payload)


def _prepared_event_binding_sha256(
    *,
    record: Mapping[str, object],
    event_type: str,
    payload: Mapping[str, object],
    state: _SemanticState,
) -> str:
    projected = {
        "schema_version": record["schema_version"],
        "event_index": record["event_index"],
        "previous_event_sha256": record["previous_event_sha256"],
        "origin_id": record["origin_id"],
        "operation_id": record["operation_id"],
        "event_type": event_type,
        "payload": _prepared_payload_projection(event_type, payload, state=state),
    }
    return _sha256(_canonical_json(projected))


def _build_event_for_current_head(
    *,
    replay: _Replay,
    origin_id: str,
    operation_id: str,
    event: OriginEvent,
) -> tuple[str, dict[str, object], dict[str, object], bytes, str]:
    event_type, payload = _event_payload(event)
    old_index, old_sha = replay.committed_heads[origin_id]
    record = _event_record(
        origin_id=origin_id,
        operation_id=operation_id,
        event_index=old_index + 1,
        previous_event_sha256=old_sha,
        event_type=event_type,
        payload=payload,
    )
    frame = _record_frame(record)
    return event_type, payload, record, frame, _sha256(frame)


def _prospective_semantic_sha(
    *,
    replay: _Replay,
    authority: _Authority,
    origin_id: str,
    event: OriginEvent,
) -> str:
    states = _replay_state_prefix(
        authority=authority,
        parsed_events=replay.parsed_events,
        committed_heads=replay.committed_heads,
    )
    state = states[origin_id]
    _apply_event(
        state,
        event,
        manifest=authority.entries[origin_id].manifest,
        origin_id=origin_id,
    )
    return _preseal_semantic_sha(state)


def _same_committed_request(
    operation: _CommittedOperation,
    *,
    replay: _Replay,
    origin_id: str,
    operation_id: str,
    expected_state_commitment: str,
    event: OriginEvent,
) -> bool:
    if (
        operation.origin_id != origin_id
        or operation.operation_id != operation_id
        or operation.base_state_commitment != expected_state_commitment
    ):
        return False
    parsed = replay.parsed_events[operation.origin_id][operation.event_index]
    event_type, payload = _event_payload(event)
    return (
        parsed.record["event_type"] == event_type
        and parsed.record["payload"] == payload
        and parsed.record["event_sha256"] == operation.event_sha256
    )


def _truncate_partial_tails(
    store: _Store,
    authority: _Authority,
    replay: _Replay,
) -> tuple[_Replay, bool]:
    """Discard every incomplete frame after its complete prefix validated."""
    changed = False
    if replay.head_data.tail:
        _truncate(
            store,
            store.head_path,
            replay.head_data.complete_length,
            root=store.runtime_root,
            label="runtime head partial tail",
        )
        changed = True
    for origin_id in authority.entries:
        path = store.origin_path(origin_id)
        data = _read_jsonl(path, root=store.runtime_root, label=f"origin ledger {origin_id}")
        if data.tail:
            _truncate(
                store,
                path,
                data.complete_length,
                root=store.runtime_root,
                label=f"origin ledger {origin_id} partial tail",
            )
            changed = True
    return (_replay_once(store, authority) if changed else replay), changed


def _replay(store: _Store, authority: _Authority) -> _Replay:
    """Validate complete prefixes, repair incomplete tails, then replay clean bytes."""
    replay = _replay_once(store, authority)
    replay, _ = _truncate_partial_tails(store, authority, replay)
    return replay


def _commit_locked(
    store: _Store,
    authority: _Authority,
    *,
    origin_id: str,
    operation_id: str,
    expected_state_commitment: str,
    event: OriginEvent,
) -> EventReceipt:
    origin_id = _sha(origin_id, label="origin ID")
    operation_id = _string(operation_id, label="operation ID", token=True)
    if operation_id.startswith("origin-opened:"):
        _fail("origin-opened operation prefix is reserved")
    expected_state_commitment = _sha(
        expected_state_commitment, label="expected state commitment"
    )
    if origin_id not in authority.entries:
        _fail("unknown authority origin")
    replay = _replay(store, authority)
    _fault_point(store, "commit:base-read")
    committed = replay.operations.get(operation_id)
    if committed is not None:
        if not _same_committed_request(
            committed,
            replay=replay,
            origin_id=origin_id,
            operation_id=operation_id,
            expected_state_commitment=expected_state_commitment,
            event=event,
        ):
            _fail("committed operation ID reuse mismatch")
        _fsync_existing(
            store,
            store.origin_path(origin_id),
            root=store.runtime_root,
            label="committed origin event",
        )
        _fsync_existing(
            store,
            store.head_path,
            root=store.runtime_root,
            label="committed runtime head",
        )
        return EventReceipt(
            origin_id=origin_id,
            operation_id=operation_id,
            event_index=committed.event_index,
            event_sha256=committed.event_sha256,
            resulting_state_commitment=replay.resulting_commitments[operation_id],
            current_state_commitment=replay.current_state_commitment,
            replayed=True,
        )

    if replay.prepared is None:
        if expected_state_commitment != replay.current_state_commitment:
            _fail("state commitment CAS mismatch")
        event_type, payload, event_record, event_frame, _ = (
            _build_event_for_current_head(
                replay=replay,
                origin_id=origin_id,
                operation_id=operation_id,
                event=event,
            )
        )
        request_sha = _request_sha256(
            base_state_commitment=expected_state_commitment,
            origin_id=origin_id,
            operation_id=operation_id,
            event_type=event_type,
            payload=payload,
            state=replay.states[origin_id],
        )
        event_binding = _prepared_event_binding_sha256(
            record=event_record,
            event_type=event_type,
            payload=payload,
            state=replay.states[origin_id],
        )
        prospective = _prospective_semantic_sha(
            replay=replay,
            authority=authority,
            origin_id=origin_id,
            event=event,
        )
        old_index, old_sha = replay.committed_heads[origin_id]
        prepared_record = _head_record(
            record_index=len(replay.head_data.records),
            previous_record_sha256=replay.head_data.records[-1]["record_sha256"],
            record_type="head-prepared",
            payload={
                "base_state_commitment": expected_state_commitment,
                "request_sha256": request_sha,
                "origin_id": origin_id,
                "operation_id": operation_id,
                "old_event_index": old_index,
                "old_event_sha256": old_sha,
                "old_event_byte_length": sum(
                    len(item.frame) for item in replay.parsed_events[origin_id][:old_index + 1]
                ),
                "next_event_binding_sha256": event_binding,
                "prospective_public_state_sha256": prospective,
            },
        )
        _append(
            store,
            store.head_path,
            _record_frame(prepared_record),
            root=store.runtime_root,
            label="head-prepared",
        )
        replay = _replay(store, authority)

    prepared = replay.prepared
    assert prepared is not None
    prepared_payload = prepared["payload"]
    if prepared_payload["operation_id"] != operation_id or prepared_payload["origin_id"] != origin_id:
        _fail("another operation is durably prepared")
    if expected_state_commitment != prepared_payload["base_state_commitment"]:
        _fail("prepared operation base mismatch")
    event_type, payload, event_record, event_frame, _ = _build_event_for_current_head(
        replay=replay,
        origin_id=origin_id,
        operation_id=operation_id,
        event=event,
    )
    request_sha = _request_sha256(
        base_state_commitment=expected_state_commitment,
        origin_id=origin_id,
        operation_id=operation_id,
        event_type=event_type,
        payload=payload,
        state=replay.states[origin_id],
    )
    event_binding = _prepared_event_binding_sha256(
        record=event_record,
        event_type=event_type,
        payload=payload,
        state=replay.states[origin_id],
    )
    prospective = _prospective_semantic_sha(
        replay=replay,
        authority=authority,
        origin_id=origin_id,
        event=event,
    )
    if (
        request_sha != prepared_payload["request_sha256"]
        or event_binding != prepared_payload["next_event_binding_sha256"]
        or prospective != prepared_payload["prospective_public_state_sha256"]
    ):
        _fail("prepared operation request mismatch")

    event_path = store.origin_path(origin_id)
    event_data = _read_jsonl(
        event_path,
        root=store.runtime_root,
        label=f"origin ledger {origin_id}",
    )
    old_length = prepared_payload["old_event_byte_length"]
    if event_data.tail:
        _fail("origin partial tail survived repair")
    if event_data.complete_length == old_length:
        _append(
            store,
            event_path,
            event_frame,
            root=store.runtime_root,
            label="origin-event",
        )
    elif (
        event_data.complete_length == old_length + len(event_frame)
        and event_data.frames[-1] == event_frame
    ):
        _fsync_existing(
            store,
            event_path,
            root=store.runtime_root,
            label="origin event",
        )
    else:
        _fail("origin event bytes do not match prepared request")

    event_index = int(event_record["event_index"])
    commit_record = _head_record(
        record_index=int(prepared["record_index"]) + 1,
        previous_record_sha256=prepared["record_sha256"],
        record_type="head-committed",
        payload={
            "prepared_record_sha256": prepared["record_sha256"],
            "origin_id": origin_id,
            "operation_id": operation_id,
            "event_index": event_index,
            "event_sha256": event_record["event_sha256"],
        },
    )
    commit_frame = _record_frame(commit_record)
    head_data = _read_jsonl(store.head_path, root=store.runtime_root, label="runtime head")
    if head_data.tail:
        _fail("runtime head partial tail survived repair")
    if head_data.records[-1]["record_sha256"] == prepared["record_sha256"]:
        _append(
            store,
            store.head_path,
            commit_frame,
            root=store.runtime_root,
            label="head-committed",
        )
    elif head_data.frames[-1] == commit_frame:
        _fsync_existing(
            store,
            store.head_path,
            root=store.runtime_root,
            label="runtime head commit",
        )
    else:
        _fail("runtime head commit mismatch")
    final = _replay(store, authority)
    completed = final.operations.get(operation_id)
    if completed is None:
        _fail("operation did not become committed")
    return EventReceipt(
        origin_id=origin_id,
        operation_id=operation_id,
        event_index=completed.event_index,
        event_sha256=completed.event_sha256,
        resulting_state_commitment=final.resulting_commitments[operation_id],
        current_state_commitment=final.current_state_commitment,
        replayed=False,
    )


def _read_origin_locked(
    store: _Store,
    authority: _Authority,
    origin_id: str,
) -> OriginSnapshot:
    origin_id = _sha(origin_id, label="origin ID")
    if origin_id not in authority.entries:
        _fail("unknown authority origin")
    replay = _replay(store, authority)
    state = replay.states[origin_id]
    reserved_batch_id: str | None = None
    reserved_iteration_index: int | None = None
    reserved_member_row_count: int | None = None
    reserved_query_ordinal_start: int | None = None
    if state.phase == "BATCH_RESERVED":
        if state.open_batch is None:
            _fail("reserved origin lacks reservation binding")
        reserved_batch_id = str(state.open_batch["batch_id"])
        reserved_iteration_index = int(state.open_batch["iteration_index"])
        reserved_member_row_count = int(state.open_batch["member_row_count"])
        reserved_query_ordinal_start = int(
            state.open_batch["query_ordinal_start"]
        )
    return OriginSnapshot(
        origin_id=origin_id,
        state_commitment=replay.current_state_commitment,
        phase=state.phase,
        iterations_used=state.iterations_used,
        queries_used=state.queries_used,
        sealed_queries=state.sealed_queries,
        tombstoned_queries=state.tombstoned_queries,
        forfeited_iterations=state.forfeited_iterations,
        forfeited_queries=state.forfeited_queries,
        batch_count=state.batch_count,
        tombstone_count=state.tombstone_count,
        terminal_status=state.terminal_status,
        constraint_class_sha256s=state.constraint_class,
        origin_distinct_candidate_count=state.origin_distinct_candidate_count,
        reserved_batch_id=reserved_batch_id,
        reserved_iteration_index=reserved_iteration_index,
        reserved_member_row_count=reserved_member_row_count,
        reserved_query_ordinal_start=reserved_query_ordinal_start,
    )


def _read_sealed_batch_locked(
    store: _Store,
    authority: _Authority,
    origin_id: str,
    batch_id: str,
) -> SealedBatch:
    origin_id = _sha(origin_id, label="origin ID")
    batch_id = _string(batch_id, label="batch ID", token=True)
    if origin_id not in authority.entries:
        _fail("unknown authority origin")
    replay = _replay(store, authority)
    batch = replay.states[origin_id].sealed_batches.get(batch_id)
    if batch is None:
        _fail("batch is not sealed")
    return batch


def read_origin(origin_id: str) -> OriginSnapshot:
    """Read the committed snapshot under the same global flock as writers."""
    store = _production_store()
    with _locked(store) as authority:
        return _read_origin_locked(store, authority, origin_id)


def commit_event(
    origin_id: str,
    *,
    operation_id: str,
    expected_state_commitment: str,
    event: OriginEvent,
) -> EventReceipt:
    """Commit one public event by CAS on the global authority state."""
    store = _production_store()
    with _locked(store) as authority:
        return _commit_locked(
            store,
            authority,
            origin_id=origin_id,
            operation_id=operation_id,
            expected_state_commitment=expected_state_commitment,
            event=event,
        )


def read_sealed_batch(origin_id: str, batch_id: str) -> SealedBatch:
    """Return revealed results only after a committed batch seal."""
    store = _production_store()
    with _locked(store) as authority:
        return _read_sealed_batch_locked(store, authority, origin_id, batch_id)
