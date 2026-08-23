"""D282 payload と source-pinned D574 JSON projections の strict parser。"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
import json
import os
from pathlib import PurePosixPath
import re
from types import MappingProxyType

from .blobref import BlobRef, InvalidBlobRefError, read_pinned_blob


DECISION_KIND = "t139-preregistration-approval-supersession/v1"
D282_DECISIONS_REF = BlobRef(
    path="docs/decisions.md",
    commit="39d760985a5e37d20464c394760bf65596156566",
    sha256="ec588bb6b8149b1d35e62246045771a4b9769a5a2b2de3160575bb1a6cec79cf",
)
T139_APPROVAL_MANIFEST_REF = BlobRef(
    path="orchestrator/preregistration/t139-approval-manifest-v1.json",
    commit="dcc76fe0bb2a7963610b964fba8eecd7b3d17496",
    sha256="ceb75fdd5f0716af1aaeb9d71986860dcf0978f5484225d239346fbafa2ce61c",
)
T139_VECTOR_APPROVAL_REF = BlobRef(
    path="orchestrator/preregistration/t139-vector-approval-v1.json",
    commit="dcc76fe0bb2a7963610b964fba8eecd7b3d17496",
    sha256="e32acd6b00bfa17b59b48e61ffb362959b6e68da62827501a5bb55955aa60967",
)

APPROVED_BLOB_ROLES = frozenset(
    {
        "addendum_a",
        "derivation_map",
        "erratum_t139_core_s15_exactkey_v1",
        "record_items",
        "receipt_schema",
        "erratum_t139_core_s7_stresscheck_v1",
    }
)
APPROVED_ERRATUM_ORDER = (
    "t139-core-s15-exactkey-v1",
    "t139-core-s7-stresscheck-v1",
)

_TOP_LEVEL_KEYS = frozenset(
    {
        "decision_kind",
        "forward_supersedes",
        "preserved",
        "target_core",
        "approved_blobs",
        "erratum_application_order",
        "composed_sha256",
        "not_approved_as_record_items_root",
        "operational_boundary",
        "alpha_reservation",
    }
)
_TRIPLET_KEYS = frozenset({"path", "commit", "sha256"})
_EXCLUDED_ROOT_KEYS = frozenset({"path", "sha256", "note"})
_ALPHA_KEYS = frozenset(
    {
        "ledger_path",
        "family_root",
        "ordinal",
        "entry_canonical_bytes",
        "reservation_entry_sha256",
        "ledger_blob_sha256",
        "entry_serialization",
        "ledger_introduction",
        "reservation_commit",
    }
)
_COMMIT_RE = re.compile(r"[0-9a-f]{40}\Z")
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_D282_HEADING_RE = re.compile(r"## D282(?:\..*)?\Z")
_LEVEL_TWO_HEADING_RE = re.compile(r" {0,3}## ([^#].*)\Z")
_FENCE_RE = re.compile(r"^( {0,3})(`{3,})(.*)$")
_TOP_ASSIGNMENT_RE = re.compile(r"([a-z0-9_]+)\s*=\s*(.*)\Z")
_TOP_BLOCK_RE = re.compile(r"([a-z0-9_]+):\Z")


class ApprovalPayloadRejectionReason(str, Enum):
    """Machine-readable identity of the guard that rejected a payload."""

    INVALID_STRUCTURE = "invalid_structure"
    NON_UTF8_DOCUMENT = "non_utf8_document"
    D282_HEADING_COUNT = "d282_heading_count"
    FENCE_STRUCTURE = "fence_structure"
    TARGET_FENCE_COUNT = "target_fence_count"
    TARGET_FENCE_SECTION = "target_fence_section"
    TOP_LEVEL_UNKNOWN_KEY = "top_level_unknown_key"
    TOP_LEVEL_DUPLICATE_KEY = "top_level_duplicate_key"
    TOP_LEVEL_EXACT_KEYS = "top_level_exact_keys"
    ERRATUM_APPLICATION_ORDER = "erratum_application_order"
    EXCLUDED_ROOT_EXACT_KEYS = "excluded_root_exact_keys"
    ALPHA_RESERVATION_EXACT_KEYS = "alpha_reservation_exact_keys"
    ALPHA_RESERVATION_COMMIT = "alpha_reservation_commit"
    APPROVED_BLOB_ROLE_COUNT = "approved_blob_role_count"
    APPROVED_BLOB_ROLE_SET = "approved_blob_role_set"
    APPROVED_BLOB_DUPLICATE_ROLE = "approved_blob_duplicate_role"


class ApprovalPayloadError(Exception):
    """D282 の承認 payload を一意かつ厳密に解釈できない。"""

    def __init__(
        self,
        message: str,
        *,
        reason: ApprovalPayloadRejectionReason = (
            ApprovalPayloadRejectionReason.INVALID_STRUCTURE
        ),
    ) -> None:
        super().__init__(message)
        self.reason = reason


class ApprovalPayloadDecodeError(ApprovalPayloadError):
    """固定 blob が UTF-8 ではない。"""


class ApprovalPayloadStructureError(ApprovalPayloadError):
    """Markdown または payload の exact grammar が不正である。"""


class ApprovalProjectionError(ValueError):
    """D574 projection JSON の exact grammar が不正である。"""

    def __init__(self, message: str, *, reason_code: str = "invalid_structure") -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.code = reason_code


@dataclass(frozen=True)
class ExcludedRecordItemsRoot:
    """F_r 以後に record_items role として承認されない旧 root。"""

    path: str
    sha256: str
    note: str


@dataclass(frozen=True)
class AlphaReservationDescriptor:
    """D282 の literal descriptor。台帳の存在や履歴を証明しない。"""

    ledger_path: str
    family_root: str
    ordinal: int
    entry_canonical_bytes: bytes
    reservation_entry_sha256: str
    ledger_blob_sha256: str
    entry_serialization: str
    ledger_introduction: str
    reservation_commit: str


@dataclass(frozen=True)
class ApprovalPayload:
    decision_kind: str
    forward_supersedes: tuple[str, ...]
    preserved: tuple[str, ...]
    target_core: BlobRef
    approved_blobs: Mapping[str, BlobRef]
    erratum_application_order: tuple[str, ...]
    composed_sha256: str
    not_approved_as_record_items_root: ExcludedRecordItemsRoot
    operational_boundary: str
    alpha_reservation: AlphaReservationDescriptor


@dataclass(frozen=True, slots=True)
class _VectorApprovalProjection:
    predecessor: BlobRef
    base_approval_fold_commit: str
    approval_fold_commit: str
    canonical_authority: BlobRef
    vector_index: BlobRef


@dataclass(frozen=True, slots=True)
class _ApprovalManifestProjection:
    predecessor: BlobRef
    base_approval_fold_commit: str
    approval_fold_commit: str
    canonical_authority: BlobRef
    vector_index: BlobRef


@dataclass(frozen=True)
class _OpenFence:
    delimiter_length: int
    info: str
    in_d282: bool
    content: list[str]


def load_approval_payload(
    repository_root: str | os.PathLike[str],
) -> ApprovalPayload:
    """固定 F_r の ``docs/decisions.md`` だけから D282 payload を読む。"""

    return _parse_approval_payload(read_pinned_blob(repository_root, D282_DECISIONS_REF))


def load_effective_approval_projections(
    repository_root: str | os.PathLike[str],
) -> tuple[_ApprovalManifestProjection, _VectorApprovalProjection]:
    """Source-pinned D574 manifest/payload projection だけを historical blob から読む。"""

    return _load_effective_approval_projections_from_refs(
        repository_root,
        manifest_ref=T139_APPROVAL_MANIFEST_REF,
        projection_ref=T139_VECTOR_APPROVAL_REF,
    )


def _load_effective_approval_projections_from_refs(
    repository_root: str | os.PathLike[str],
    *,
    manifest_ref: BlobRef,
    projection_ref: BlobRef,
) -> tuple[_ApprovalManifestProjection, _VectorApprovalProjection]:
    """Explicit refs を使う private test seam。production wrapper は固定 refs のみ渡す。"""

    if type(manifest_ref) is not BlobRef or type(projection_ref) is not BlobRef:
        raise ApprovalProjectionError("projection refs は BlobRef でなければならない")
    manifest = _parse_approval_manifest_projection(
        read_pinned_blob(repository_root, manifest_ref)
    )
    projection = _parse_vector_approval_projection(
        read_pinned_blob(repository_root, projection_ref)
    )
    return manifest, projection


def _strict_json_object(document: bytes, label: str) -> dict[str, object]:
    if type(document) is not bytes:
        raise ApprovalProjectionError(f"{label} は bytes でなければならない")

    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in items:
            if key in result:
                raise ApprovalProjectionError(
                    f"{label} に重複 key がある: {key}", reason_code="duplicate_key"
                )
            result[key] = value
        return result

    def reject_constant(value: str) -> object:
        raise ApprovalProjectionError(
            f"{label} に非有限値がある: {value}", reason_code="non_finite"
        )

    try:
        value = json.loads(
            document.decode("utf-8", errors="strict"),
            object_pairs_hook=pairs,
            parse_constant=reject_constant,
        )
    except ApprovalProjectionError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise ApprovalProjectionError(f"{label} は strict UTF-8 JSON でない") from exc
    if type(value) is not dict:
        raise ApprovalProjectionError(f"{label} root は object でなければならない")
    return value


def _projection_fields(
    value: object, expected: frozenset[str], label: str
) -> dict[str, object]:
    if type(value) is not dict:
        raise ApprovalProjectionError(f"{label} は object でなければならない")
    actual = set(value)
    if actual != expected:
        raise ApprovalProjectionError(
            f"{label} key 集合が不一致: missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}",
            reason_code="exact_keys",
        )
    return value


def _projection_literal(value: object, expected: str, label: str) -> None:
    if type(value) is not str or value != expected:
        raise ApprovalProjectionError(f"{label} が固定値と一致しない")


def _projection_blob_ref(value: object, label: str) -> BlobRef:
    fields = _projection_fields(value, _TRIPLET_KEYS, label)
    try:
        return BlobRef(
            path=fields["path"], commit=fields["commit"], sha256=fields["sha256"]
        )
    except (InvalidBlobRefError, TypeError) as exc:
        raise ApprovalProjectionError(f"{label} の BlobRef が不正である") from exc


def _projection_commit(value: object, label: str) -> str:
    if type(value) is not str or _COMMIT_RE.fullmatch(value) is None:
        raise ApprovalProjectionError(f"{label} が 40 桁 lowercase hex でない")
    return value


def _parse_vector_approval_projection(document: bytes) -> _VectorApprovalProjection:
    raw = _projection_fields(
        _strict_json_object(document, "vector approval projection"),
        frozenset(
            {
                "schema_version", "decision_kind", "forward_supersedes",
                "base_approval_fold_commit", "approval_fold_commit",
                "canonical_authority", "conformance_vector_index",
            }
        ),
        "vector approval projection",
    )
    _projection_literal(raw["schema_version"], "t139-vector-approval/v1", "schema_version")
    _projection_literal(raw["decision_kind"], "t139-vector-approval/v1", "decision_kind")
    predecessor = _projection_fields(
        raw["forward_supersedes"], frozenset({"decision_kind", "approval"}),
        "forward_supersedes",
    )
    _projection_literal(predecessor["decision_kind"], DECISION_KIND, "predecessor kind")
    vector = _projection_fields(
        raw["conformance_vector_index"], frozenset({"approval"}),
        "conformance_vector_index",
    )
    return _VectorApprovalProjection(
        predecessor=_projection_blob_ref(predecessor["approval"], "predecessor approval"),
        base_approval_fold_commit=_projection_commit(
            raw["base_approval_fold_commit"], "base approval fold"
        ),
        approval_fold_commit=_projection_commit(raw["approval_fold_commit"], "approval fold"),
        canonical_authority=_projection_blob_ref(raw["canonical_authority"], "authority"),
        vector_index=_projection_blob_ref(vector["approval"], "vector index"),
    )


def _parse_approval_manifest_projection(document: bytes) -> _ApprovalManifestProjection:
    raw = _projection_fields(
        _strict_json_object(document, "approval manifest projection"),
        frozenset(
            {
                "schema_version", "base_approval_fold_commit", "approval_fold_commit",
                "canonical_authority", "namespaces",
            }
        ),
        "approval manifest projection",
    )
    _projection_literal(raw["schema_version"], "t139-approval-manifest/v1", "schema_version")
    namespaces = _projection_fields(
        raw["namespaces"],
        frozenset({"preregistration_approval", "conformance_vectors"}),
        "namespaces",
    )
    prereg = _projection_fields(
        namespaces["preregistration_approval"], frozenset({"namespace_projection"}),
        "preregistration namespace",
    )
    vectors = _projection_fields(
        namespaces["conformance_vectors"], frozenset({"namespace_projection"}),
        "vector namespace",
    )
    return _ApprovalManifestProjection(
        predecessor=_projection_blob_ref(prereg["namespace_projection"], "predecessor approval"),
        base_approval_fold_commit=_projection_commit(
            raw["base_approval_fold_commit"], "base approval fold"
        ),
        approval_fold_commit=_projection_commit(raw["approval_fold_commit"], "approval fold"),
        canonical_authority=_projection_blob_ref(raw["canonical_authority"], "authority"),
        vector_index=_projection_blob_ref(vectors["namespace_projection"], "vector index"),
    )


def _parse_approval_payload(document: bytes) -> ApprovalPayload:
    """テスト可能な bytes parser。Git や worktree file へアクセスしない。"""

    if not isinstance(document, bytes):
        raise ApprovalPayloadStructureError("document は bytes でなければならない")
    try:
        text = document.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ApprovalPayloadDecodeError(
            "docs/decisions.md が UTF-8 ではない",
            reason=ApprovalPayloadRejectionReason.NON_UTF8_DOCUMENT,
        ) from exc

    payload_text = _extract_d282_fence(text)
    return _parse_payload_text(payload_text)


def _extract_d282_fence(document: str) -> str:
    headings = 0
    current_section_is_d282 = False
    open_fence: _OpenFence | None = None
    candidates: list[tuple[bool, str]] = []

    for line_number, line in enumerate(document.splitlines(), start=1):
        fence_match = _FENCE_RE.fullmatch(line)
        if open_fence is not None:
            if fence_match is not None:
                delimiter = fence_match.group(2)
                suffix = fence_match.group(3)
                if suffix.strip() or len(delimiter) != open_fence.delimiter_length:
                    raise ApprovalPayloadStructureError(
                        f"fence の入れ子または delimiter 長不整合: line {line_number}",
                        reason=ApprovalPayloadRejectionReason.FENCE_STRUCTURE,
                    )
                content = open_fence.content
                if (
                    open_fence.info == "text"
                    and content
                    and content[0] == f"decision_kind = {DECISION_KIND}"
                ):
                    candidates.append((open_fence.in_d282, "\n".join(content)))
                open_fence = None
                continue
            open_fence.content.append(line)
            continue

        if fence_match is not None:
            info = fence_match.group(3).strip()
            if "`" in info:
                raise ApprovalPayloadStructureError(
                    f"fence info に backtick がある: line {line_number}"
                )
            open_fence = _OpenFence(
                delimiter_length=len(fence_match.group(2)),
                info=info,
                in_d282=current_section_is_d282,
                content=[],
            )
            continue

        if _D282_HEADING_RE.fullmatch(line):
            headings += 1
            current_section_is_d282 = True
            continue
        if _LEVEL_TWO_HEADING_RE.fullmatch(line):
            current_section_is_d282 = False

    if open_fence is not None:
        raise ApprovalPayloadStructureError("閉じていない backtick fence がある")
    if headings != 1:
        raise ApprovalPayloadStructureError(
            f"見出し ## D282 は exact 1 件でなければならない: {headings} 件",
            reason=ApprovalPayloadRejectionReason.D282_HEADING_COUNT,
        )
    if len(candidates) != 1:
        raise ApprovalPayloadStructureError(
            "対象 decision_kind の text fence は exact 1 件でなければならない: "
            f"{len(candidates)} 件",
            reason=ApprovalPayloadRejectionReason.TARGET_FENCE_COUNT,
        )
    in_d282, payload = candidates[0]
    if not in_d282:
        raise ApprovalPayloadStructureError(
            "対象 fence が D282 節に属していない",
            reason=ApprovalPayloadRejectionReason.TARGET_FENCE_SECTION,
        )
    return payload


def _parse_payload_text(payload: str) -> ApprovalPayload:
    if "\t" in payload:
        raise ApprovalPayloadStructureError("payload に tab は使えない")
    lines = payload.split("\n")
    raw: dict[str, object] = {}
    index = 0

    while index < len(lines):
        if not lines[index]:
            index += 1
            continue
        line = lines[index]
        if line.startswith(" "):
            raise ApprovalPayloadStructureError(
                f"top-level でない孤立行がある: {line!r}"
            )

        block_match = _TOP_BLOCK_RE.fullmatch(line)
        assignment_match = _TOP_ASSIGNMENT_RE.fullmatch(line)
        if block_match is not None:
            key = block_match.group(1)
            _claim_key(raw, key)
            index += 1
            block: list[str] = []
            while index < len(lines) and (not lines[index] or lines[index].startswith(" ")):
                block.append(lines[index])
                index += 1
            while block and not block[-1]:
                block.pop()
            if not block:
                raise ApprovalPayloadStructureError(f"{key} block が空である")
            raw[key] = block
            continue

        if assignment_match is None:
            raise ApprovalPayloadStructureError(f"不正な top-level 行: {line!r}")
        key, value = assignment_match.groups()
        _claim_key(raw, key)
        if key == "operational_boundary" and value != '"""':
            raise ApprovalPayloadStructureError(
                "operational_boundary は triple-quoted 値でなければならない"
            )
        if value == '"""':
            index += 1
            multiline: list[str] = []
            while index < len(lines) and lines[index] != '"""':
                multiline.append(lines[index])
                index += 1
            if index == len(lines):
                raise ApprovalPayloadStructureError(f"{key} の triple quote が閉じていない")
            raw[key] = "\n".join(multiline)
            index += 1
        else:
            if not value:
                raise ApprovalPayloadStructureError(f"{key} の値が空である")
            raw[key] = value
            index += 1

    _require_exact_keys(
        raw,
        _TOP_LEVEL_KEYS,
        "top-level",
        reason=ApprovalPayloadRejectionReason.TOP_LEVEL_EXACT_KEYS,
    )
    if raw["decision_kind"] != DECISION_KIND:
        raise ApprovalPayloadStructureError("decision_kind が承認値と一致しない")

    forward = _parse_literal_list(raw["forward_supersedes"], "forward_supersedes", 2)
    preserved = _parse_literal_list(raw["preserved"], "preserved", 3)
    target_core = _make_blob_ref(
        _parse_fields(raw["target_core"], 2, _TRIPLET_KEYS, "target_core"),
        "target_core",
    )
    approved = _parse_approved_blobs(raw["approved_blobs"])
    order = _parse_bracket_list(raw["erratum_application_order"])
    if order != APPROVED_ERRATUM_ORDER:
        raise ApprovalPayloadStructureError(
            "erratum_application_order が承認順序と一致しない",
            reason=ApprovalPayloadRejectionReason.ERRATUM_APPLICATION_ORDER,
        )
    composed_sha256 = _require_hex(raw["composed_sha256"], _SHA256_RE, "composed_sha256")

    excluded_fields = _parse_fields(
        raw["not_approved_as_record_items_root"],
        2,
        _EXCLUDED_ROOT_KEYS,
        "not_approved_as_record_items_root",
        exact_keys_reason=ApprovalPayloadRejectionReason.EXCLUDED_ROOT_EXACT_KEYS,
    )
    excluded = ExcludedRecordItemsRoot(
        path=_require_repo_relative_path(excluded_fields["path"], "excluded root path"),
        sha256=_require_hex(excluded_fields["sha256"], _SHA256_RE, "excluded root sha256"),
        note=_require_nonempty(excluded_fields["note"], "excluded root note"),
    )

    operational_boundary = _require_nonempty(raw["operational_boundary"], "operational_boundary")
    alpha = _make_alpha_descriptor(
        _parse_fields(
            raw["alpha_reservation"],
            2,
            _ALPHA_KEYS,
            "alpha_reservation",
            exact_keys_reason=(
                ApprovalPayloadRejectionReason.ALPHA_RESERVATION_EXACT_KEYS
            ),
        )
    )
    return ApprovalPayload(
        decision_kind=DECISION_KIND,
        forward_supersedes=forward,
        preserved=preserved,
        target_core=target_core,
        approved_blobs=MappingProxyType(approved),
        erratum_application_order=order,
        composed_sha256=composed_sha256,
        not_approved_as_record_items_root=excluded,
        operational_boundary=operational_boundary,
        alpha_reservation=alpha,
    )


def _claim_key(raw: dict[str, object], key: str) -> None:
    if key not in _TOP_LEVEL_KEYS:
        raise ApprovalPayloadStructureError(
            f"未知 top-level key: {key}",
            reason=ApprovalPayloadRejectionReason.TOP_LEVEL_UNKNOWN_KEY,
        )
    if key in raw:
        raise ApprovalPayloadStructureError(
            f"重複 top-level key: {key}",
            reason=ApprovalPayloadRejectionReason.TOP_LEVEL_DUPLICATE_KEY,
        )


def _require_exact_keys(
    values: Mapping[str, object],
    expected: frozenset[str],
    label: str,
    *,
    reason: ApprovalPayloadRejectionReason = (
        ApprovalPayloadRejectionReason.INVALID_STRUCTURE
    ),
) -> None:
    actual = set(values)
    if actual != expected:
        raise ApprovalPayloadStructureError(
            f"{label} key 集合が不一致: missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}",
            reason=reason,
        )


def _parse_literal_list(value: object, label: str, expected_count: int) -> tuple[str, ...]:
    block = _require_block(value, label)
    entries: list[str] = []
    for line in block:
        if not re.fullmatch(r"  \S.*", line):
            raise ApprovalPayloadStructureError(f"{label} の indentation が不正である")
        entries.append(line[2:])
    if len(entries) != expected_count or len(set(entries)) != expected_count:
        raise ApprovalPayloadStructureError(f"{label} の項目数または一意性が不正である")
    return tuple(entries)


def _parse_fields(
    value: object,
    indent: int,
    expected: frozenset[str],
    label: str,
    *,
    exact_keys_reason: ApprovalPayloadRejectionReason = (
        ApprovalPayloadRejectionReason.INVALID_STRUCTURE
    ),
) -> dict[str, str]:
    block = _require_block(value, label)
    assignment = re.compile(rf" {{{indent}}}([a-z0-9_]+)\s*=\s*(.*)\Z")
    fields: dict[str, list[str]] = {}
    current: str | None = None
    for line in block:
        match = assignment.fullmatch(line)
        if match is not None:
            key, first = match.groups()
            if key in fields:
                raise ApprovalPayloadStructureError(f"{label} の key が重複: {key}")
            fields[key] = [first]
            current = key
            continue
        leading = len(line) - len(line.lstrip(" "))
        if current is None or leading <= indent or not line.strip():
            raise ApprovalPayloadStructureError(f"{label} の field 行が不正: {line!r}")
        fields[current].append(line.strip())
    _require_exact_keys(fields, expected, label, reason=exact_keys_reason)
    joined = {key: "\n".join(parts) for key, parts in fields.items()}
    for key, item in joined.items():
        _require_nonempty(item, f"{label}.{key}")
    return joined


def _parse_approved_blobs(value: object) -> dict[str, BlobRef]:
    block = _require_block(value, "approved_blobs")
    approved: dict[str, BlobRef] = {}
    index = 0
    while index < len(block):
        role_match = re.fullmatch(r"  ([a-z0-9_]+)", block[index])
        if role_match is None:
            raise ApprovalPayloadStructureError(
                f"approved_blobs の role 行が不正: {block[index]!r}"
            )
        role = role_match.group(1)
        if role in approved:
            raise ApprovalPayloadStructureError(
                f"approved_blobs の role が重複: {role}",
                reason=ApprovalPayloadRejectionReason.APPROVED_BLOB_DUPLICATE_ROLE,
            )
        index += 1
        role_lines: list[str] = []
        while index < len(block) and not re.fullmatch(r"  [a-z0-9_]+", block[index]):
            role_lines.append(block[index])
            index += 1
        fields = _parse_fields(role_lines, 4, _TRIPLET_KEYS, f"approved_blobs.{role}")
        approved[role] = _make_blob_ref(fields, f"approved_blobs.{role}")

    if len(approved) != 6:
        raise ApprovalPayloadStructureError(
            f"approved_blobs は exact 6 role でなければならない: {len(approved)} 件",
            reason=ApprovalPayloadRejectionReason.APPROVED_BLOB_ROLE_COUNT,
        )
    roles = set(approved)
    if roles != APPROVED_BLOB_ROLES:
        raise ApprovalPayloadStructureError(
            "approved_blobs role 集合が不一致: "
            f"missing={sorted(APPROVED_BLOB_ROLES - roles)}, "
            f"unknown={sorted(roles - APPROVED_BLOB_ROLES)}",
            reason=ApprovalPayloadRejectionReason.APPROVED_BLOB_ROLE_SET,
        )
    return approved


def _make_blob_ref(fields: Mapping[str, str], label: str) -> BlobRef:
    try:
        return BlobRef(
            path=fields["path"],
            commit=_require_hex(fields["commit"], _COMMIT_RE, f"{label}.commit"),
            sha256=_require_hex(fields["sha256"], _SHA256_RE, f"{label}.sha256"),
        )
    except InvalidBlobRefError as exc:
        raise ApprovalPayloadStructureError(f"{label} の三つ組が不正である") from exc


def _make_alpha_descriptor(fields: Mapping[str, str]) -> AlphaReservationDescriptor:
    ordinal_text = fields["ordinal"]
    if re.fullmatch(r"[1-9][0-9]*", ordinal_text) is None:
        raise ApprovalPayloadStructureError("alpha_reservation.ordinal が正整数でない")
    canonical_text = fields["entry_canonical_bytes"]
    if "\n" in canonical_text:
        raise ApprovalPayloadStructureError("entry_canonical_bytes は単一行でなければならない")
    reservation_commit = fields["reservation_commit"]
    if not reservation_commit.startswith("pin しない。"):
        raise ApprovalPayloadStructureError(
            "reservation_commit は pin しない descriptor でなければならない",
            reason=ApprovalPayloadRejectionReason.ALPHA_RESERVATION_COMMIT,
        )
    return AlphaReservationDescriptor(
        ledger_path=_require_repo_relative_path(fields["ledger_path"], "alpha ledger_path"),
        family_root=_require_hex(fields["family_root"], _COMMIT_RE, "alpha family_root"),
        ordinal=int(ordinal_text),
        entry_canonical_bytes=canonical_text.encode("utf-8"),
        reservation_entry_sha256=_require_hex(
            fields["reservation_entry_sha256"], _SHA256_RE, "reservation_entry_sha256"
        ),
        ledger_blob_sha256=_require_hex(
            fields["ledger_blob_sha256"], _SHA256_RE, "ledger_blob_sha256"
        ),
        entry_serialization=_require_nonempty(
            fields["entry_serialization"], "entry_serialization"
        ),
        ledger_introduction=_require_nonempty(
            fields["ledger_introduction"], "ledger_introduction"
        ),
        reservation_commit=reservation_commit,
    )


def _parse_bracket_list(value: object) -> tuple[str, ...]:
    text = _require_nonempty(value, "erratum_application_order")
    if not text.startswith("[") or not text.endswith("]"):
        raise ApprovalPayloadStructureError("erratum_application_order の list 形式が不正")
    body = text[1:-1]
    if not body:
        return ()
    items = tuple(item.strip() for item in body.split(","))
    if any(not item for item in items):
        raise ApprovalPayloadStructureError("erratum_application_order に空要素がある")
    return items


def _require_block(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(line, str) for line in value):
        raise ApprovalPayloadStructureError(f"{label} は block でなければならない")
    return value


def _require_hex(value: object, pattern: re.Pattern[str], label: str) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise ApprovalPayloadStructureError(f"{label} の hex 桁数または文字種が不正である")
    return value


def _require_nonempty(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ApprovalPayloadStructureError(f"{label} が空または文字列でない")
    return value


def _require_repo_relative_path(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ApprovalPayloadStructureError(f"{label} が repo 相対 path でない")
    if "\\" in value or "\n" in value or "\r" in value:
        raise ApprovalPayloadStructureError(f"{label} が canonical POSIX path でない")
    path = PurePosixPath(value)
    if path.is_absolute() or value != path.as_posix():
        raise ApprovalPayloadStructureError(f"{label} が canonical POSIX path でない")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ApprovalPayloadStructureError(f"{label} に禁止 path 要素がある")
    return value
