"""D291 が固定した公表 blob 承認 payload の resolver。

この module が解決するのは blob role の承認記録だけであり、pilot / 本走の
投入権限ではない。trust root は caller が選ぶ値ではなく、D291 の fold commit
``D291_FOLD_COMMIT`` に固定する。
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Final, Literal

from orchestrator.preregistration.blobref import BlobRef, read_pinned_blob


D291_FOLD_COMMIT: Final[str] = "b13b7ea840ad51199f40b3a534c9d1cdb422af2e"
D291_DECISIONS_SHA256: Final[str] = (
    "3d2cd5dc6cf63c5928a3ec64a91ae3b3c530dafc83d83d52a038a2eb5cf0c2b8"
)
D291_DECISIONS_REF: Final[BlobRef] = BlobRef(
    path="docs/decisions.md",
    commit=D291_FOLD_COMMIT,
    sha256=D291_DECISIONS_SHA256,
)

ApprovedRoleName = Literal["publication_core", "source_addendum_b"]

_TOP_LEVEL_KEYS: Final[tuple[str, ...]] = (
    "decision_kind",
    "prior_exact_byte_authority",
    "procedural_history",
    "source_core",
    "source_study_inputs",
    "document_relations",
    "approved_blobs",
    "approved_values_for_future_addendum_p",
    "historical_candidates_rejected_for_role",
    "exact_closure",
    "operational_state_on_fold",
    "authority_field_note",
    "role_coupling",
    "operational_boundary",
)
_APPROVED_ROLE_ORDER: Final[tuple[ApprovedRoleName, ...]] = (
    "publication_core",
    "source_addendum_b",
)
_APPROVED_ROLE_SET: Final[frozenset[str]] = frozenset(_APPROVED_ROLE_ORDER)
_DOCUMENT_RELATION_ROLES: Final[frozenset[str]] = frozenset(
    {
        "source_addendum_b",
        "publication_core",
        "future_publication_addendum_p",
    }
)

_APPROVED_REFS: Final[dict[ApprovedRoleName, BlobRef]] = {
    "publication_core": BlobRef(
        path="output/insights/2026-08-11_t139-pubcore-stage2/publication-core-v2.md",
        commit="66934dda7f28893110a64a2011e213c2bda5e821",
        sha256="ad326dae70584d86470ff861e9bfd517b4f5b8406247f8047ae6cdb3ddabef67",
    ),
    "source_addendum_b": BlobRef(
        path="output/insights/2026-08-11_t139-pubcore-stage2/addendum-b-v2.md",
        commit="25a66d2042a4fff1021e033c23fc2b814a735de9",
        sha256="ad12b60d29bb94ff67c3302b0779cb4765cd1c77768149d7cf6587698febb048",
    ),
}
_HISTORICAL_REJECTED_REFS: Final[dict[ApprovedRoleName, BlobRef]] = {
    "publication_core": BlobRef(
        path="output/insights/2026-08-10_t139-publication-core/publication-core.md",
        commit="db5e8dfce0449a6df5cb2e1ed494eff406600187",
        sha256="9b7bc1932dd76e0e72f5cd98f9de2e01a62c4a065e8ac0e0eb6a59e5a3f66a64",
    ),
    "source_addendum_b": BlobRef(
        path="output/insights/2026-08-09_t139-addendum-b/addendum-b.md",
        commit="8e9a5b4dddfb85f7d31f671090cd24a7a4192e42",
        sha256="5071acbd9db18f022cb9603acef3a8cd3394ed17de80cc794468c1b1f5baa384",
    ),
}

_PROJECTION_PAIRS: Final[tuple[tuple[str, str], ...]] = (
    ("p01.candidate_cap", "p01.candidate_cap"),
    ("p01.admissible_ordinals", "p01.admissible_ordinals"),
    ("p02.familywise_alpha", "p02.familywise_alpha"),
    ("p02.spending_domain", "p02.spending.domain"),
    ("p02.alpha_pub_k", "p02.spending.alpha_pub_k"),
    ("p02.current_k", "p02.current_study.k"),
    ("p02.alpha_pub", "p02.current_study.alpha_pub"),
    ("p02.unspent_tail_reclaim", "p02.unspent_tail.reclaim"),
    ("p02.unspent_tail_redistribute", "p02.unspent_tail.redistribute"),
)
_EXPECTED_VALUES: Final[dict[str, object]] = {
    "p01.candidate_cap": Decimal("1"),
    "p01.admissible_ordinals": frozenset({1}),
    "p02.familywise_alpha": Decimal("0.05"),
    "p02.spending_domain": "k = 1, 2, 3, …",
    "p02.alpha_pub_k": "0.05 / (k * (k + 1))",
    "p02.current_k": Decimal("1"),
    "p02.alpha_pub": Decimal("0.025"),
    "p02.unspent_tail_reclaim": False,
    "p02.unspent_tail_redistribute": False,
}
_NUMERIC_VALUE_KEYS: Final[frozenset[str]] = frozenset(
    {
        "p01.candidate_cap",
        "p02.familywise_alpha",
        "p02.current_k",
        "p02.alpha_pub",
    }
)
_CANONICAL_STRING_KEYS: Final[frozenset[str]] = frozenset(
    {"p02.spending_domain", "p02.alpha_pub_k"}
)
_BOOLEAN_VALUE_KEYS: Final[frozenset[str]] = frozenset(
    {"p02.unspent_tail_reclaim", "p02.unspent_tail_redistribute"}
)

# D291 の canonical payload から固定した節 digest。値節と relation 節は、D291 が
# 明示的に許す比較単位だけを正規化した後の digest を別途照合する。
_EXACT_SECTION_SHA256: Final[dict[str, str]] = {
    "decision_kind": "e69a72ef12a72c7fa4e58234248b494d7ae726baefe8c151ab4dd7dcf4ccb20c",
    "prior_exact_byte_authority": (
        "44b4190d186dcdaf5d38dc281e3b7864177811ac19538c090e83dfc2aae65547"
    ),
    "procedural_history": "804788e5d58db76c8cdd3aca820a3eaa062b871a3a2bf27c567e61d7f1572670",
    "source_core": "5f029dea8de5788c228f8e17ed722ebc13efa9efef11b2a7905583b54e80e873",
    "source_study_inputs": "21b03446a4b2c95dbd32513e5e242ac22cc2d04bf31c140168f55b9184db31e7",
    "approved_blobs": "446a957126259e854fad0c0348f6a7f35318b51b5efd65216c25d58b2429acb4",
    "historical_candidates_rejected_for_role": (
        "d60971bf2894b94c8bdaae3ed602bb967ac07848bc28fc04299da6913c869386"
    ),
    "exact_closure": "9f148ca1b9924ed9165391326b83d0de3d2c1d576d80a8fb696e4416526291c4",
    "operational_state_on_fold": (
        "c4a5fba8bb030a873d7b80c1d58ed09f0299b5dc1487f524153b50f241a9c560"
    ),
    "authority_field_note": "5703fe93e494ded2bdcb05ca6302af0814619ad944f4417e66a9ed374433224f",
    "role_coupling": "f55fe69a263a99c962c163ef006307f4fa8f0a2787dfa96496b9842b4d0f09cd",
    "operational_boundary": "ca6af1e2285908386ccacafa64a4175eef5bd47899f2a6defc1b0cb3ae991b07",
}
_DOCUMENT_RELATIONS_NORMALIZED_SHA256: Final[str] = (
    "10950721281b83d52b6301e6199858d890f292e8c059c075090508fa9d12ddc2"
)
_APPROVED_VALUES_NORMALIZED_SHA256: Final[str] = (
    "cf8a147031e16cd1561e1e40d7cae2468f884b73a8c8a6f3db810b87a5bd9646"
)

_TOP_LEVEL_RE = re.compile(r"^([a-z][a-z0-9_]*)\s*(?::|=)")
_FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
_ASSIGNMENT_RE = re.compile(r"^(\s+)([a-z][a-z0-9_]*)\s*=\s*(.*?)\s*$")


class D291ApprovalError(Exception):
    """D291 payload の検査または role 解決に失敗した。"""


class D291PayloadError(D291ApprovalError):
    """D291 payload が canonical exact grammar と一致しない。"""


class D291ResolutionError(D291ApprovalError):
    """candidate role 集合または三つ組が D291 の承認集合と一致しない。"""


@dataclass(frozen=True, slots=True)
class _D291ApprovalPayload:
    """全 exact-closure 検査を通過した D291 payload。"""

    decision_kind: str
    approved_blobs: tuple[tuple[ApprovedRoleName, BlobRef], ...]
    document_relation_roles: frozenset[str]
    approved_values: tuple[tuple[str, object], ...]
    value_projection: tuple[tuple[str, str], ...]
    historical_candidates_rejected_for_role: tuple[
        tuple[ApprovedRoleName, BlobRef], ...
    ]
    pilot_submission: Literal["forbidden"]
    main_submission: Literal["forbidden"]


@dataclass(frozen=True, slots=True)
class _D291RoleResolution:
    """D291 が記録する一 role の承認状態（投入権限ではない）。"""

    role_name: ApprovedRoleName
    ref: BlobRef
    approval_status: Literal["approved_by_canonical_decision"]
    trust_root_commit: str
    submission_authority: Literal["not_granted"]
    document_envelope_authority: Literal["none"]


def _outside_fences(lines: list[str]) -> tuple[bool, ...]:
    visible: list[bool] = []
    fence_character: str | None = None
    fence_width = 0
    for line in lines:
        if fence_character is not None:
            closing = re.fullmatch(
                rf" {{0,3}}{re.escape(fence_character)}{{{fence_width},}}[ \t]*",
                line,
            )
            visible.append(False)
            if closing is not None:
                fence_character = None
                fence_width = 0
            continue
        opening = _FENCE_OPEN_RE.fullmatch(line)
        if opening is not None:
            marker, info = opening.groups()
            if marker[0] == "`" and "`" in info:
                visible.append(True)
                continue
            fence_character = marker[0]
            fence_width = len(marker)
            visible.append(False)
            continue
        visible.append(True)
    return tuple(visible)


def _extract_d291_fenced_payload(decisions_blob: bytes) -> list[str]:
    try:
        text = decisions_blob.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise D291PayloadError("docs/decisions.md が UTF-8 でない") from exc
    lines = text.splitlines()
    visible = _outside_fences(lines)
    starts = [
        index
        for index, line in enumerate(lines)
        if visible[index] and line.startswith("## D291.")
    ]
    if len(starts) != 1:
        raise D291PayloadError("## D291 heading が一意に存在しない")
    start = starts[0]
    # A6: D292 という名前を仮定せず、次の可視 H2 または EOF で閉じる。
    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if visible[index] and lines[index].startswith("## ")
        ),
        len(lines),
    )
    section = lines[start:end]
    openings = [index for index, line in enumerate(section) if line == "```text"]
    closings = [index for index, line in enumerate(section) if line == "```"]
    if len(openings) != 1 or len(closings) != 1 or closings[0] <= openings[0]:
        raise D291PayloadError("D291 の ```text fenced payload が一意でない")
    if any(
        _FENCE_OPEN_RE.fullmatch(line) is not None
        for index, line in enumerate(section)
        if index not in {openings[0], closings[0]}
    ):
        raise D291PayloadError("D291 節に余剰 fenced block がある")
    return section[openings[0] + 1 : closings[0]]


def _split_top_level_sections(payload_lines: list[str]) -> dict[str, str]:
    starts: list[tuple[int, str]] = []
    for index, line in enumerate(payload_lines):
        match = _TOP_LEVEL_RE.match(line)
        if match is not None:
            starts.append((index, match.group(1)))
    actual = tuple(key for _, key in starts)
    if actual != _TOP_LEVEL_KEYS:
        duplicates = sorted({key for key in actual if actual.count(key) > 1})
        missing = sorted(set(_TOP_LEVEL_KEYS) - set(actual))
        extra = sorted(set(actual) - set(_TOP_LEVEL_KEYS))
        raise D291PayloadError(
            "top-level key 列が exact 14 keys と不一致: "
            f"missing={missing}, extra={extra}, duplicates={duplicates}, actual={actual}"
        )
    if starts[0][0] != 0:
        raise D291PayloadError("先頭 top-level key より前に payload text がある")
    sections: dict[str, str] = {}
    for position, (index, key) in enumerate(starts):
        next_index = starts[position + 1][0] if position + 1 < len(starts) else len(payload_lines)
        sections[key] = "\n".join(payload_lines[index:next_index])
    return sections


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalize_document_relations(section: str) -> str:
    roles = frozenset(
        match.group(1)
        for line in section.splitlines()
        if (match := re.fullmatch(r"  ([a-z][a-z0-9_]*):", line)) is not None
    )
    if roles != _DOCUMENT_RELATION_ROLES:
        raise D291PayloadError(
            f"document_relations role 集合が不一致: actual={sorted(roles)}"
        )
    normalized: list[str] = []
    for line in section.splitlines():
        match = _ASSIGNMENT_RE.fullmatch(line)
        if match is None:
            normalized.append(line)
            continue
        indent, key, value = match.groups()
        if key == "commit" and value.startswith("symbolic:"):
            expected = (
                "symbolic:F_p   (本 decision の fold commit を指す記号。"
                "hex40 の literal ではない)"
            )
            if value != expected:
                raise D291PayloadError("required_core_ref.commit の symbolic ref が不正")
        normalized.append(f"{indent}{key} = {value}")
    result = "\n".join(normalized)
    if _sha256_text(result) != _DOCUMENT_RELATIONS_NORMALIZED_SHA256:
        raise D291PayloadError("document_relations 節全体が D291 と exact 一致しない")
    return result


def _parse_decimal(value: object, label: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise D291PayloadError(f"{label} は 10 進数でなければならない")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise D291PayloadError(f"{label} は 10 進数でなければならない") from exc
    if not parsed.is_finite():
        raise D291PayloadError(f"{label} は有限 10 進数でなければならない")
    return parsed


def _parse_ordinals(value: object, label: str) -> frozenset[int]:
    if isinstance(value, str):
        match = re.fullmatch(r"\[\s*([0-9]+(?:\s*,\s*[0-9]+)*)?\s*\]", value)
        if match is None:
            raise D291PayloadError(f"{label} は整数 list でなければならない")
        items: object = [] if not match.group(1) else match.group(1).split(",")
    else:
        items = value
    if not isinstance(items, (list, tuple, set, frozenset)):
        raise D291PayloadError(f"{label} は整数集合でなければならない")
    result: set[int] = set()
    for item in items:
        if isinstance(item, bool):
            raise D291PayloadError(f"{label} は整数集合でなければならない")
        try:
            integer = int(str(item).strip())
        except (TypeError, ValueError) as exc:
            raise D291PayloadError(f"{label} は整数集合でなければならない") from exc
        if str(integer) != str(item).strip():
            raise D291PayloadError(f"{label} は canonical 整数集合でなければならない")
        result.add(integer)
    return frozenset(result)


def _collapse_whitespace(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise D291PayloadError(f"{label} は文字列でなければならない")
    return " ".join(value.split())


def _normalize_typed_value(key: str, value: object) -> object:
    if key in _NUMERIC_VALUE_KEYS:
        return _parse_decimal(value, key)
    if key == "p01.admissible_ordinals":
        return _parse_ordinals(value, key)
    if key in _CANONICAL_STRING_KEYS:
        return _collapse_whitespace(value, key)
    if key in _BOOLEAN_VALUE_KEYS:
        if isinstance(value, bool):
            return value
        if value == "true":
            return True
        if value == "false":
            return False
        raise D291PayloadError(f"{key} は true / false でなければならない")
    raise D291PayloadError(f"未知の approved value key: {key}")


def _canonical_value_text(key: str, value: object) -> str:
    normalized = _normalize_typed_value(key, value)
    if isinstance(normalized, Decimal):
        return format(normalized.normalize(), "f")
    if isinstance(normalized, frozenset):
        return "[" + ",".join(str(item) for item in sorted(normalized)) + "]"
    if isinstance(normalized, bool):
        return "true" if normalized else "false"
    return str(normalized)


def _normalize_approved_values(section: str) -> dict[str, object]:
    normalized_lines: list[str] = []
    parsed: dict[str, object] = {}
    block: str | None = None
    expected_fields = {
        "p01": frozenset({"candidate_cap", "admissible_ordinals"}),
        "p02": frozenset(
            {
                "familywise_alpha",
                "spending_domain",
                "alpha_pub_k",
                "current_k",
                "alpha_pub",
                "unspent_tail_reclaim",
                "unspent_tail_redistribute",
            }
        ),
    }
    seen_fields: dict[str, set[str]] = {"p01": set(), "p02": set()}
    for line in section.splitlines():
        block_match = re.fullmatch(r"  (p01|p02):", line)
        if block_match is not None:
            block = block_match.group(1)
            normalized_lines.append(line)
            continue
        if re.match(r"^  \S", line) is not None:
            block = None
        match = _ASSIGNMENT_RE.fullmatch(line)
        if match is None or len(match.group(1)) != 4 or block not in expected_fields:
            normalized_lines.append(line)
            continue
        indent, field, raw_value = match.groups()
        if field not in expected_fields[block]:
            normalized_lines.append(line)
            continue
        if field in seen_fields[block]:
            raise D291PayloadError(f"approved value field が重複: {block}.{field}")
        seen_fields[block].add(field)
        key = f"{block}.{field}"
        value = _normalize_typed_value(key, raw_value)
        parsed[key] = value
        normalized_lines.append(f"{indent}{field} = {_canonical_value_text(key, raw_value)}")
    for name, expected in expected_fields.items():
        if seen_fields[name] != expected:
            raise D291PayloadError(
                f"{name} value key 集合が不一致: actual={sorted(seen_fields[name])}"
            )
    if parsed != _EXPECTED_VALUES:
        raise D291PayloadError("approved_values_for_future_addendum_p の値が不一致")
    normalized_section = "\n".join(normalized_lines)
    if _sha256_text(normalized_section) != _APPROVED_VALUES_NORMALIZED_SHA256:
        raise D291PayloadError(
            "approved_values_for_future_addendum_p の写像または閉包が不一致"
        )
    return parsed


def _require_exact_sections(sections: Mapping[str, str]) -> None:
    for key, expected_digest in _EXACT_SECTION_SHA256.items():
        if _sha256_text(sections[key]) != expected_digest:
            raise D291PayloadError(f"{key} 節が D291 と exact 一致しない")


def _parse_d291_payload(decisions_blob: bytes) -> _D291ApprovalPayload:
    """任意 bytes から D291 fenced payload を検査する private test seam。"""

    if not isinstance(decisions_blob, bytes):
        raise TypeError("decisions_blob は bytes でなければならない")
    sections = _split_top_level_sections(_extract_d291_fenced_payload(decisions_blob))
    _require_exact_sections(sections)
    _normalize_document_relations(sections["document_relations"])
    approved_values = _normalize_approved_values(
        sections["approved_values_for_future_addendum_p"]
    )
    return _D291ApprovalPayload(
        decision_kind="t139-publication-core-approval/v1",
        approved_blobs=tuple((role, _APPROVED_REFS[role]) for role in _APPROVED_ROLE_ORDER),
        document_relation_roles=_DOCUMENT_RELATION_ROLES,
        approved_values=tuple((key, approved_values[key]) for key, _ in _PROJECTION_PAIRS),
        value_projection=_PROJECTION_PAIRS,
        historical_candidates_rejected_for_role=tuple(
            (role, _HISTORICAL_REJECTED_REFS[role]) for role in _APPROVED_ROLE_ORDER
        ),
        pilot_submission="forbidden",
        main_submission="forbidden",
    )


def load_d291_payload(repository_root: str | Path) -> _D291ApprovalPayload:
    """固定 ``F_p`` の D291 payload 全体を hash 検証して load する。"""

    decisions_blob = read_pinned_blob(repository_root, D291_DECISIONS_REF)
    return _parse_d291_payload(decisions_blob)


def require_d291_projection_exact(
    repository_root: str | Path,
    projection: Mapping[str, object],
) -> None:
    """実 ``F_p`` と追補 P 側の 9 値 projection の exact 一致を課す。

    検査済み payload を caller から受け取らない。権威となる値と写像は毎回、固定
    commit の ``docs/decisions.md`` bytes から再導出する。
    """

    payload = load_d291_payload(repository_root)
    if not isinstance(projection, Mapping):
        raise TypeError("projection は mapping でなければならない")
    if not all(isinstance(key, str) for key in projection):
        raise D291ResolutionError("value_projection key は文字列でなければならない")
    expected_keys = frozenset(right for _, right in payload.value_projection)
    actual_keys = frozenset(projection)
    if actual_keys != expected_keys:
        raise D291ResolutionError(
            "value_projection key 集合が不一致: "
            f"missing={sorted(expected_keys - actual_keys)}, "
            f"extra={sorted(actual_keys - expected_keys)}"
        )
    approved_values = dict(payload.approved_values)
    for left, right in payload.value_projection:
        actual = _normalize_typed_value(left, projection[right])
        if actual != approved_values[left]:
            raise D291ResolutionError(f"value_projection の値が不一致: {right}")


def _require_authority_none_envelope(blob: bytes, role: str) -> None:
    try:
        lines = blob.decode("utf-8", errors="strict").splitlines()
    except UnicodeDecodeError as exc:
        raise D291ResolutionError(f"{role} の文書 envelope が UTF-8 でない") from exc
    openings = [index for index, line in enumerate(lines) if line == "```text"]
    if not openings:
        raise D291ResolutionError(f"{role} に text envelope が存在しない")
    opening = openings[0]
    closing = next(
        (index for index in range(opening + 1, len(lines)) if lines[index] == "```"),
        None,
    )
    if closing is None:
        raise D291ResolutionError(f"{role} の text envelope が閉じていない")
    authority_lines = [
        line for line in lines[opening + 1 : closing] if line.startswith("authority:")
    ]
    if authority_lines != ["authority: none"]:
        raise D291ResolutionError(f"{role} の document envelope authority が none でない")


def _resolve_d291_approvals(
    repository_root: str | Path,
    *,
    candidates: Mapping[str, BlobRef] | None = None,
) -> dict[ApprovedRoleName, _D291RoleResolution]:
    """全 role 集合と全三つ組を一括検査して D291 の承認状態を返す。

    単一 role だけを解決する入口は設けない。``candidates`` を省略した場合も、D291
    が固定する 2 role の blob bytes を両方とも Git object database から再検査する。
    """

    payload = load_d291_payload(repository_root)
    expected = dict(payload.approved_blobs)
    selected: Mapping[str, BlobRef] = expected if candidates is None else candidates
    if not isinstance(selected, Mapping):
        raise TypeError("candidates は mapping でなければならない")
    if not all(isinstance(role, str) for role in selected):
        raise D291ResolutionError("approved_blobs role は文字列でなければならない")
    actual_roles = frozenset(selected)
    if actual_roles != _APPROVED_ROLE_SET:
        raise D291ResolutionError(
            "approved_blobs role 集合が不一致: "
            f"missing={sorted(_APPROVED_ROLE_SET - actual_roles)}, "
            f"extra={sorted(actual_roles - _APPROVED_ROLE_SET)}"
        )
    for role in _APPROVED_ROLE_ORDER:
        candidate = selected[role]
        if not isinstance(candidate, BlobRef) or candidate != expected[role]:
            raise D291ResolutionError(f"{role} の (path, commit, sha256) が不一致")
    resolutions: dict[ApprovedRoleName, _D291RoleResolution] = {}
    for role in _APPROVED_ROLE_ORDER:
        ref = expected[role]
        blob = read_pinned_blob(repository_root, ref)
        _require_authority_none_envelope(blob, role)
        resolutions[role] = _D291RoleResolution(
            role_name=role,
            ref=ref,
            approval_status="approved_by_canonical_decision",
            trust_root_commit=D291_FOLD_COMMIT,
            submission_authority="not_granted",
            document_envelope_authority="none",
        )
    return resolutions


def resolve_d291_approvals(
    repository_root: str | Path,
) -> dict[ApprovedRoleName, _D291RoleResolution]:
    """実 ``F_p`` が固定する exact 2 role を一括解決する公開 API。

    candidate mapping は caller から受け取らない。負例で閉包を検査する seam は
    private ``_resolve_d291_approvals`` に限定する。
    """

    return _resolve_d291_approvals(repository_root)
