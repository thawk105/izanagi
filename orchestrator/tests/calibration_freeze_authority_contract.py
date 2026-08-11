# -*- coding: utf-8 -*-
"""Calibration/freeze authority fixture manifest の fail-closed 契約検査。"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


FIXTURE_ROOT: Path = (
    Path(__file__).resolve().parent / "fixtures" / "calibration_freeze_authority"
)
DESIGN_DOC: Path = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "calibration-freeze-authority-bundle-design.md"
)

__all__ = (
    "FIXTURE_ROOT",
    "DESIGN_DOC",
    "ContractError",
    "extract_design_row_ids",
    "load_manifest",
    "load_ruling_profile",
    "load_fixture_cases",
    "validate_repository",
    "require_stage0_complete",
)


class ContractError(ValueError):
    """Authority fixture 契約が閉じていないときの fail-closed 例外。"""


_MANIFEST_SCHEMA = "calibration-freeze-authority-fixture-manifest/v1"
_PROFILE_SCHEMA = "calibration-freeze-authority-ruling-profile/v1"
_CASE_SCHEMA = "calibration-freeze-authority-invariant-fixture/v1"
_DESIGN_SOURCE_PATH = "docs/calibration-freeze-authority-bundle-design.md"
_DESIGN_ROW_PATTERN = r"^CFAB-(?:7\.2-0[1-3]|11\.1-0[1-6]|11\.2-01)$"

_IDENTIFIER_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_ROW_ID_RE = re.compile(r"^CFAB-(?:7\.2|11\.[12])-[0-9]{2}$")
_DESIGN_TABLE_ROW_RE = re.compile(
    r"^\|\s*`(CFAB-(?:7\.2|11\.1)-[0-9]{2})`\s*\|", re.MULTILINE
)
_DESIGN_DECLARED_ROW_RE = re.compile(
    r"^row ID\s*=\s*`(CFAB-11\.2-[0-9]{2})`[.。]$", re.MULTILINE
)
_RULING_TABLE_ROW_RE = re.compile(
    r"^\|\s*`((?:CFAB|FREEZE)-[^`]+)`\s*\|[^|]*\|\s*(.*?)\s*\|\s*$",
    re.MULTILINE,
)
_SELECTION_LITERAL_RE = re.compile(r"`([^`]+)`")
_UPPER_REVOCATION_TABLE_MARKER = (
    "**失効 record R** — `revocations/<bundle_digest>.json`、"
    "束当たり 0/1 件、top-level exact 7 key。"
)
_UPPER_REVOCATION_TABLE_HEADER = "| key | 型・制約 |\n|---|---|\n"
_UPPER_REVOCATION_TABLE_ROW_RE = re.compile(
    r"^\|\s*`([a-z][a-z0-9_]*)`\s*\|\s*(.*?)\s*\|$"
)
_STAGE6_TABLE_ROW_RE = re.compile(
    r"^\|\s*6\s*\|\s*発効 X\s*\|\s*(.*?)\s*\|\s*$",
    re.MULTILINE,
)
_STAGE6_STRUCTURAL_MARKER = "**構造部分 (段 0 で固定):** "
_STAGE6_POLICY_MARKER = "**policy 依存部分:** "
_STAGE6_STRUCTURAL_CLAUSE_RE = re.compile(
    r"\((i|ii|iii|iv|v)\) (.+?。)"
    r"(?= \((?:i|ii|iii|iv|v)\)| 以上 5 条件)"
)
_FENCE_OPEN_RE = re.compile(
    r"^[ \t]{0,3}(?P<marker>`{3,}|~{3,})(?P<info>.*)$"
)
_STAGE6_POLICY_RE = re.compile(
    r"^段 5 の S / B 裁定後まで `(?P<gate_id>CFAB-[A-Z0-9-]+)` "
    r"\(owner = `(?P<owner>[a-z0-9-]+)`, "
    r"status = `(?P<status>[a-z-]+)`\) として残し、"
    r"段 6 の完了には構造部分と policy 依存部分の双方を要求する。"
    r"段 5 の除外は段 6 へ及ばない$"
)
_STAGE_SCOPE_DECLARATION_RE = re.compile(
    r"^\*\*この fixture 閉包が対象とする段は、段 ([0-9]+)〜([0-9]+) と"
    r"段 ([0-9]+)〜([0-9]+) である",
    re.MULTILINE,
)
_ENTRYPOINT_RE = re.compile(
    r"^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*:[A-Za-z_]\w*$"
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PLACEHOLDER_RE = re.compile(r"TODO|FIXME|\.\.\.", re.IGNORECASE)

_PROFILE_IDS = (
    "CFAB-Q1-PLACEMENT",
    "CFAB-Q2-ACTOR",
    "CFAB-Q2-MEANING",
    "CFAB-Q3-LOCKSTEP",
    "CFAB-Q3-ROLLBACK",
    "CFAB-Q3-REVOCATION",
    "CFAB-Q3-XF-POSITION",
    "CFAB-Q4-HEAD-MODE",
    "CFAB-S-SEAL",
    "CFAB-S-GUARANTEE",
    "CFAB-B-SIDE-EFFECT",
    "FREEZE-U-A1",
)
_SELECTION_ENUMS = {
    "CFAB-Q1-PLACEMENT": frozenset({"outside-authority-directory"}),
    "CFAB-Q2-ACTOR": frozenset({"human-approval-and-activation"}),
    "CFAB-Q2-MEANING": frozenset({"digest-plus-inspection-receipt"}),
    "CFAB-Q3-LOCKSTEP": frozenset({"both-components-change"}),
    "CFAB-Q3-ROLLBACK": frozenset({"forward-compensating-generation"}),
    "CFAB-Q3-REVOCATION": frozenset({"no-lower-fallback-fail-closed"}),
    "CFAB-Q3-XF-POSITION": frozenset({"after-upper-activation"}),
    "CFAB-Q4-HEAD-MODE": frozenset({"literal-pinned"}),
    "CFAB-S-SEAL": frozenset({"S1", "S2"}),
    "CFAB-S-GUARANTEE": frozenset({"G-a", "G-b", "G-c"}),
    "FREEZE-U-A1": frozenset({"activation-window"}),
}

_EXPECTED_RULING_STATES: Mapping[str, tuple[str, str | None]] = MappingProxyType({
    "CFAB-Q3-ROLLBACK": ("resolved", "forward-compensating-generation"),
    "CFAB-Q3-REVOCATION": ("resolved", "no-lower-fallback-fail-closed"),
    "CFAB-Q3-XF-POSITION": ("resolved", "after-upper-activation"),
    "CFAB-S-SEAL": ("unresolved", None),
    "CFAB-S-GUARANTEE": ("unresolved", None),
    "CFAB-B-SIDE-EFFECT": ("unresolved", None),
    "FREEZE-U-A1": ("resolved", "activation-window"),
})

_UPPER_REVOCATION_SCHEMA = (
    (
        "schema_version",
        "逐語 `calibration-freeze-authority-revocation/v1`",
    ),
    (
        "bundle_digest",
        "64 lower-hex。file 名の stem と一致し、§7.3 の再計算値と一致",
    ),
    (
        "approval_raw_sha256",
        "64 lower-hex。対象束の A の raw bytes の sha256 および "
        "`approvals/<raw sha256>.json` の file 名 stem と一致",
    ),
    ("revoked_by", "NFC、trim 済み、1〜128 code point"),
    ("revoked_at", "exact int の UTC 秒。`bool` を int として受理しない"),
    ("scope", "逐語 `bundle-only`"),
    ("reason", "非空 string"),
)
_EXPECTED_STAGE6_STRUCTURAL_PREDICATES = (
    "X は `active/<raw sha256>.json` に置く top-level exact 5 key "
    "(`schema_version` / `authority_bundle_generation` / "
    "`parent_active_pointer_raw_sha256` / `bundle_digest` / "
    "`approval_raw_sha256`) の record で、file 名の stem は X の raw bytes の "
    "sha256 と一致する。",
    "`parent_active_pointer_raw_sha256` は genesis のときだけ `null`、"
    "それ以外は**その時点の live tip X** の raw sha256 と一致する "
    "(祖先の非 tip X を parent にした列を拒否する)。",
    "`authority_bundle_generation` は A の同 field と一致し、非 genesis では "
    "parent X の値より真に大きい (§5.1 の世代単調増加)。",
    "`bundle_digest` は A の `bundle_digest` と一致し、§7.3 の再計算値と一致する。",
    "`approval_raw_sha256` は A の raw bytes の sha256 と "
    "`approvals/<raw sha256>.json` の file 名 stem の双方に一致し、参照先 A は"
    "下位 family 検証器と §5.1 の topology 検査を通った承認済み A に限る。",
)
_EXPECTED_STAGE6_STRUCTURAL_CONTROL = (
    "以上 5 条件をすべて満たす陽性 control を少なくとも 1 件受理し、"
    "各条件を 1 つだけ破る 5 個の陰性変異をそれぞれ対応する理由で拒否する。"
)
_EXPECTED_STAGE6_EXECUTION_BOUNDARY = (
    "**本行が固定するのは predicate であって実行ではない** — "
    "実 entrypoint と fixture の対応付けは "
    "`CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT` の手番であり、"
    "それが `pending` である限り段 0 は完了しない。"
)

# These literals were calculated once from the checked-in case-file bytes.  They
# are deliberately independent of manifest.v1.json so that changing a case and
# refreshing the manifest cannot move the fixture pin.
_EXPECTED_RAW_SHA256_BY_FIXTURE: Mapping[str, str] = MappingProxyType({
    "activation-head-consistency":
        "88366e954ff42f772116e9708247747132a9c8ee6ec1720ada89dfba071e59c5",
    "approved-freeze-reference":
        "63b27b6a1baad78daffaa81d8d9e0d89471477745288e3f8fcc4924952e4a740",
    "bundle-identity-propagation":
        "67600f26c1f604add2abce21171ad24ff0e87b9409c97b3d3f37806b5ea0ce5c",
    "candidate-type-preservation":
        "8530e43e975b15de2bde8dff2436c376e77a8d7a2b48fbe9c78fed90211369e1",
    "environment-floor-contract-consistency":
        "041ddc01676a9c5cf20fa6586d9d02e56394593e2a81f240249b05f2c231f6e1",
    "floor-seal-consistency":
        "db154c0e98d5686d9f724345f2f7eef240e60efe6f2d9386a3bc6d5adf90ff44",
    "freeze-history-immutability":
        "170268fb92660769fc7b4b628bd727ab49c12532e336238133eebf97f86b67c4",
    "orphan-generation-no-authority":
        "e0166f918a5302871071e84a5f38443771d849d311933e78b0798e1cb16357d4",
    "post-cutoff-bundle-identity":
        "be7219a39230586bf0cde4347ba024ab746c48740eb83e2d247b50fd99a2508d",
    "unapproved-generation-no-authority":
        "92b70ce5cd7bff0678b3a6b24bc3d5950a134108f7616cd4b37b8b0eec6a1d73",
})
_EXPECTED_FIXTURE_ENTRIES_SHA256 = (
    "a8bf16889b3b83a6c22506fd2069fad16ea20b08195597ac361b905f2476a91b"
)
_EXPECTED_ROW_IDS_SHA256 = (
    "facd79bcbd94c1783df767bede2a727df5db6e758bba79833deb5478d76eabfe"
)
_EXPECTED_REQUIRED_GATES = frozenset({
    ("CFAB-Q3-REVOCATION", "user", "resolved"),
    ("CFAB-Q3-ROLLBACK", "user", "resolved"),
    ("CFAB-Q3-XF-POSITION", "user", "resolved"),
    ("CFAB-R1-REVOCATION-RECORD", "user", "resolved"),
    ("CFAB-R2-STAGE0-COMPLETION", "user", "resolved"),
    ("CFAB-R3-STAGE6-PREDICATE", "user", "resolved"),
    ("CFAB-R4-CANCELLATION-RECORD", "user", "unresolved"),
    ("CFAB-S8-S10-CONTRADICTION", "user", "resolved"),
    ("CFAB-STAGE6-POLICY-PREDICATE", "user", "unresolved"),
    (
        "CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT",
        "stage1-and-later",
        "pending",
    ),
    ("FREEZE-AX-TOPOLOGY", "lower-impl-wave", "nonconforming"),
    ("FREEZE-CONFORMANCE-LITERAL", "lower-wa-wave", "unresolved"),
    ("FREEZE-U-A1", "user", "resolved"),
})
_EXPECTED_REQUIRED_GATES_ENTRIES_SHA256 = (
    "167d5c2e9fc365fc7945ddad7549b147be3f288e26a1182bd410712eb81cffd2"
)


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("value is not canonical JSON") from exc


def _sha256_canonical(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _reject_constant(token: str) -> None:
    raise ContractError(f"non-finite JSON constant is forbidden: {token}")


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate JSON key is forbidden: {key}")
        result[key] = value
    return result


def _load_canonical_record(path: Path, *, label: str) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ContractError(f"{label} cannot be read: {path}") from exc
    try:
        text = raw.decode("ascii", "strict")
        value = json.loads(
            text,
            parse_constant=_reject_constant,
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except ContractError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ContractError(f"{label} is not strict ASCII JSON") from exc
    if type(value) is not dict:
        raise ContractError(f"{label} top-level must be an object")
    if raw != _canonical_bytes(value) + b"\n":
        raise ContractError(f"{label} raw bytes are not canonical JSON plus one LF")
    _reject_placeholders(value, label=label)
    return value


def _reject_placeholders(value: Any, *, label: str) -> None:
    if type(value) is str and _PLACEHOLDER_RE.search(value):
        raise ContractError(f"{label} contains a placeholder string")
    if type(value) is dict:
        for key, item in value.items():
            _reject_placeholders(key, label=label)
            _reject_placeholders(item, label=label)
    elif type(value) is list:
        for item in value:
            _reject_placeholders(item, label=label)


def _expect_exact_keys(value: Any, expected: frozenset[str], *, label: str) -> None:
    if type(value) is not dict:
        raise ContractError(f"{label} must be an object")
    actual = frozenset(value)
    if actual != expected:
        raise ContractError(
            f"{label} keys must be exact; differing keys={sorted(actual ^ expected)}"
        )


def _expect_list(value: Any, *, label: str) -> list[Any]:
    if type(value) is not list:
        raise ContractError(f"{label} must be an array")
    return value


def _expect_int(value: Any, *, label: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ContractError(f"{label} must be an integer >= {minimum}; bool is forbidden")
    return value


def _expect_nonempty_string(value: Any, *, label: str) -> str:
    if type(value) is not str or not value or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value


def _expect_identifier(value: Any, *, label: str) -> str:
    text = _expect_nonempty_string(value, label=label)
    if _IDENTIFIER_RE.fullmatch(text) is None:
        raise ContractError(f"{label} is not a canonical identifier: {text!r}")
    return text


def _expect_row_id(value: Any, *, label: str) -> str:
    text = _expect_nonempty_string(value, label=label)
    if _ROW_ID_RE.fullmatch(text) is None:
        raise ContractError(f"{label} is not a CFAB design row ID: {text!r}")
    return text


def _expect_sha256(value: Any, *, label: str) -> str:
    text = _expect_nonempty_string(value, label=label)
    if _SHA256_RE.fullmatch(text) is None:
        raise ContractError(f"{label} must be a lowercase SHA-256 hex digest")
    return text


def _read_design(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ContractError(f"design document cannot be read: {path}") from exc
    if "<!--" in text or "-->" in text:
        raise ContractError("design document must not contain HTML comments")
    visible_lines: list[str] = []
    invalid_backtick_info_lines: list[int] = []
    fence: tuple[str, int] | None = None
    for lineno, line in enumerate(text.splitlines(keepends=True), 1):
        fence_line = line.rstrip("\r\n")
        if fence is not None:
            marker_char, marker_len = fence
            stripped = fence_line.lstrip(" \t")
            indent = len(fence_line) - len(stripped)
            if indent <= 3 and re.fullmatch(
                rf"{re.escape(marker_char)}{{{marker_len},}}[ \t]*", stripped
            ):
                fence = None
            continue
        fence_match = _FENCE_OPEN_RE.fullmatch(fence_line)
        if fence_match is not None:
            marker = fence_match.group("marker")
            info = fence_match.group("info")
            if marker[0] == "`" and "`" in info:
                invalid_backtick_info_lines.append(lineno)
                visible_lines.append(line)
                continue
            fence = (marker[0], len(marker))
            continue
        visible_lines.append(line)
    if invalid_backtick_info_lines:
        raise ContractError(
            "design document has an invalid backtick fence info string: "
            f"lines={invalid_backtick_info_lines}"
        )
    if fence is not None:
        raise ContractError("design document has an unclosed fenced code block")
    return "".join(visible_lines)


def _extract_design_row_ids(path: Path) -> tuple[str, ...]:
    text = _read_design(path)
    row_ids = _DESIGN_TABLE_ROW_RE.findall(text) + _DESIGN_DECLARED_ROW_RE.findall(text)
    duplicates = sorted({row_id for row_id in row_ids if row_ids.count(row_id) > 1})
    if duplicates:
        raise ContractError(f"design document has duplicate row IDs: {duplicates}")
    return tuple(sorted(row_ids))


def extract_design_row_ids() -> tuple[str, ...]:
    """設計正本の §7.2 / §11 row ID を昇順・重複なしで返す。"""

    return _extract_design_row_ids(DESIGN_DOC)


def _extract_ruling_ids(path: Path) -> tuple[str, ...]:
    text = _read_design(path)
    start_marker = "### 8.1 裁定 profile の exact schema"
    start = text.find(start_marker)
    if start < 0 or text.find(start_marker, start + 1) >= 0:
        raise ContractError("design §8.1 heading is missing or duplicated")
    end = text.find("\n---", start)
    if end < 0:
        raise ContractError("design §8.1 terminator is missing")
    ids = tuple(
        re.findall(r"^\|\s*`((?:CFAB|FREEZE)-[^`]+)`\s*\|", text[start:end], re.MULTILINE)
    )
    if len(ids) != len(set(ids)):
        raise ContractError("design §8.1 has duplicate ruling IDs")
    if ids != _PROFILE_IDS:
        raise ContractError(
            f"design §8.1 ruling IDs drifted: expected={_PROFILE_IDS!r}, actual={ids!r}"
        )
    return ids


def _extract_design_selection_enums(path: Path) -> dict[str, frozenset[str]]:
    text = _read_design(path)
    start_marker = "### 8.1 裁定 profile の exact schema"
    start = text.find(start_marker)
    if start < 0 or text.find(start_marker, start + 1) >= 0:
        raise ContractError("design §8.1 heading is missing or duplicated")
    end = text.find("\n---", start)
    if end < 0:
        raise ContractError("design §8.1 terminator is missing")
    rows = _RULING_TABLE_ROW_RE.findall(text[start:end])
    ids = tuple(ruling_id for ruling_id, _selection_cell in rows)
    if ids != _PROFILE_IDS:
        raise ContractError(
            "design §8.1 selection rows drifted: "
            f"expected={_PROFILE_IDS!r}, actual={ids!r}"
        )
    return {
        ruling_id: frozenset(_SELECTION_LITERAL_RE.findall(selection_cell))
        for ruling_id, selection_cell in rows
        if _SELECTION_LITERAL_RE.search(selection_cell) is not None
    }


def _extract_design_revocation_schema(path: Path) -> tuple[tuple[str, str], ...]:
    text = _read_design(path)
    start_marker = "### 7.5 上位層の namespace と record schema"
    start = text.find(start_marker)
    if start < 0 or text.find(start_marker, start + 1) >= 0:
        raise ContractError("design §7.5 heading is missing or duplicated")
    end = text.find("\n---", start)
    if end < 0:
        raise ContractError("design §7.5 terminator is missing")
    section = text[start:end]
    table_prefix = (
        _UPPER_REVOCATION_TABLE_MARKER
        + "\n\n"
        + _UPPER_REVOCATION_TABLE_HEADER
    )
    table_start = section.find(table_prefix)
    if table_start < 0 or section.find(table_prefix, table_start + 1) >= 0:
        raise ContractError("design §7.5 revocation table is missing or duplicated")
    body_start = table_start + len(table_prefix)
    body_end = section.find("\n\n", body_start)
    if body_end < 0:
        raise ContractError("design §7.5 revocation table terminator is missing")
    body_lines = section[body_start:body_end].splitlines()
    rows: list[tuple[str, str]] = []
    for line in body_lines:
        match = _UPPER_REVOCATION_TABLE_ROW_RE.fullmatch(line)
        if match is None:
            raise ContractError("design §7.5 revocation table has a malformed row")
        rows.append((match.group(1), match.group(2)))
    if not rows:
        raise ContractError("design §7.5 revocation table is empty")
    keys = [key for key, _constraint in rows]
    if len(keys) != len(set(keys)):
        raise ContractError("design §7.5 revocation table has duplicate keys")
    return tuple(rows)


def _extract_stage6_contract(
    path: Path,
) -> tuple[tuple[str, ...], str, str, tuple[str, str, str]]:
    text = _read_design(path)
    start_marker = "## 10. 段階分割と完了判定"
    start = text.find(start_marker)
    if start < 0 or text.find(start_marker, start + 1) >= 0:
        raise ContractError("design §10 heading is missing or duplicated")
    end = text.find("\n## ", start + len(start_marker))
    if end < 0:
        raise ContractError("design §10 terminator is missing")
    matches = _STAGE6_TABLE_ROW_RE.findall(text[start:end])
    if len(matches) != 1:
        raise ContractError("design §10 stage 6 row is missing or duplicated")

    row = matches[0]
    prefix = "**段 5 の後にしか置けない。** " + _STAGE6_STRUCTURAL_MARKER
    if not row.startswith(prefix):
        raise ContractError("design §10 stage 6 structural marker drifted")
    body = row[len(prefix):]
    policy_parts = body.split(" " + _STAGE6_POLICY_MARKER)
    if len(policy_parts) != 2:
        raise ContractError("design §10 stage 6 policy marker is missing or duplicated")
    structural_text, policy_text = policy_parts

    clause_matches = tuple(_STAGE6_STRUCTURAL_CLAUSE_RE.finditer(structural_text))
    labels = tuple(match.group(1) for match in clause_matches)
    if labels != ("i", "ii", "iii", "iv", "v"):
        raise ContractError("design §10 stage 6 predicate labels drifted")
    clauses_text = " ".join(
        f"({match.group(1)}) {match.group(2)}" for match in clause_matches
    )
    if not structural_text.startswith(clauses_text + " "):
        raise ContractError("design §10 stage 6 predicate ordering drifted")
    remainder = structural_text[len(clauses_text) + 1:]
    boundary_marker = "**本行が固定するのは predicate であって実行ではない**"
    boundary_parts = remainder.split(" " + boundary_marker)
    if len(boundary_parts) != 2:
        raise ContractError(
            "design §10 stage 6 execution boundary is missing or duplicated"
        )
    control, boundary_tail = boundary_parts
    execution_boundary = boundary_marker + boundary_tail

    policy_match = _STAGE6_POLICY_RE.fullmatch(policy_text)
    if policy_match is None:
        raise ContractError("design §10 stage 6 policy contract drifted")
    return (
        tuple(match.group(2) for match in clause_matches),
        control,
        execution_boundary,
        (
            policy_match.group("gate_id"),
            policy_match.group("owner"),
            policy_match.group("status"),
        ),
    )


def _fixture_assignment_gate_id_from_design(path: Path) -> str:
    text = _read_design(path)
    start_marker = "## 10. 段階分割と完了判定"
    start = text.find(start_marker)
    if start < 0 or text.find(start_marker, start + 1) >= 0:
        raise ContractError("design §10 heading is missing or duplicated")
    end = text.find("\n## ", start + len(start_marker))
    if end < 0:
        raise ContractError("design §10 terminator is missing")
    matches = _STAGE_SCOPE_DECLARATION_RE.findall(text[start:end])
    if len(matches) != 1:
        raise ContractError("design §10 stage-scope declaration is missing or duplicated")
    first_start, first_end, second_start, second_end = matches[0]
    return (
        f"CFAB-STAGES{first_start}-{first_end}-AND{second_start}-{second_end}"
        "-FIXTURE-ASSIGNMENT"
    )


def _validate_manifest(document: dict[str, Any]) -> None:
    _expect_exact_keys(
        document,
        frozenset(
            {
                "schema_version",
                "status",
                "design_source",
                "fixtures",
                "row_coverage",
                "required_gates",
            }
        ),
        label="manifest",
    )
    if document["schema_version"] != _MANIFEST_SCHEMA:
        raise ContractError("manifest schema_version is unsupported")
    if type(document["status"]) is not str or document["status"] not in {
        "complete",
        "incomplete",
    }:
        raise ContractError("manifest status must be complete or incomplete")

    design_source = document["design_source"]
    _expect_exact_keys(
        design_source, frozenset({"path", "row_id_pattern"}), label="design_source"
    )
    if design_source["path"] != _DESIGN_SOURCE_PATH:
        raise ContractError("design_source.path does not name the design authority")
    if design_source["row_id_pattern"] != _DESIGN_ROW_PATTERN:
        raise ContractError("design_source.row_id_pattern drifted")

    fixtures = document["fixtures"]
    _expect_exact_keys(
        fixtures, frozenset({"count", "entries", "entries_sha256"}), label="fixtures"
    )
    entries = _expect_list(fixtures["entries"], label="fixtures.entries")
    count = _expect_int(fixtures["count"], label="fixtures.count")
    if count != len(entries):
        raise ContractError("fixtures.count does not match the fixture entry count")
    fixture_ids: list[str] = []
    paths: list[str] = []
    for index, entry in enumerate(entries):
        label = f"fixtures.entries[{index}]"
        _expect_exact_keys(
            entry, frozenset({"fixture_id", "path", "raw_sha256"}), label=label
        )
        fixture_id = _expect_identifier(entry["fixture_id"], label=f"{label}.fixture_id")
        expected_path = f"cases/{fixture_id}.json"
        if entry["path"] != expected_path:
            raise ContractError(f"{label}.path must be {expected_path!r}")
        _expect_sha256(entry["raw_sha256"], label=f"{label}.raw_sha256")
        fixture_ids.append(fixture_id)
        paths.append(entry["path"])
    if len(fixture_ids) != len(set(fixture_ids)):
        raise ContractError("fixtures.entries has duplicate fixture_id values")
    if len(paths) != len(set(paths)):
        raise ContractError("fixtures.entries has duplicate paths")
    expected_entries_sha = _sha256_canonical(entries)
    actual_entries_sha = _expect_sha256(
        fixtures["entries_sha256"], label="fixtures.entries_sha256"
    )
    if actual_entries_sha != expected_entries_sha:
        raise ContractError("fixtures.entries_sha256 does not match canonical entries bytes")

    coverage = document["row_coverage"]
    _expect_exact_keys(
        coverage,
        frozenset(
            {
                "entries",
                "entries_sha256",
                "pending_count",
                "row_count",
                "row_ids_sha256",
            }
        ),
        label="row_coverage",
    )
    coverage_entries = _expect_list(coverage["entries"], label="row_coverage.entries")
    for index, entry in enumerate(coverage_entries):
        label = f"row_coverage.entries[{index}]"
        _expect_exact_keys(entry, frozenset({"fixture_id", "row_id"}), label=label)
        binding = _expect_nonempty_string(entry["fixture_id"], label=f"{label}.fixture_id")
        if binding.startswith("unresolved:"):
            raise ContractError("unresolved: binding is forbidden in row_coverage")
        _expect_identifier(binding, label=f"{label}.fixture_id")
        _expect_row_id(entry["row_id"], label=f"{label}.row_id")
    _expect_int(coverage["pending_count"], label="row_coverage.pending_count")
    _expect_int(coverage["row_count"], label="row_coverage.row_count")
    expected_coverage_sha = _sha256_canonical(coverage_entries)
    actual_coverage_sha = _expect_sha256(
        coverage["entries_sha256"], label="row_coverage.entries_sha256"
    )
    if actual_coverage_sha != expected_coverage_sha:
        raise ContractError(
            "row_coverage.entries_sha256 does not match canonical entries bytes"
        )
    _expect_sha256(coverage["row_ids_sha256"], label="row_coverage.row_ids_sha256")

    gates = document["required_gates"]
    _expect_exact_keys(
        gates, frozenset({"count", "entries", "entries_sha256"}), label="required_gates"
    )
    gate_entries = _expect_list(gates["entries"], label="required_gates.entries")
    gate_count = _expect_int(gates["count"], label="required_gates.count")
    if gate_count != len(gate_entries):
        raise ContractError("required_gates.count does not match its entry count")
    gate_ids: list[str] = []
    for index, entry in enumerate(gate_entries):
        label = f"required_gates.entries[{index}]"
        _expect_exact_keys(
            entry, frozenset({"gate_id", "owner", "status"}), label=label
        )
        gate_ids.append(_expect_nonempty_string(entry["gate_id"], label=f"{label}.gate_id"))
        _expect_nonempty_string(entry["owner"], label=f"{label}.owner")
        if type(entry["status"]) is not str or entry["status"] not in {
            "resolved",
            "unresolved",
            "pending",
            "nonconforming",
        }:
            raise ContractError(f"{label}.status is outside the required gate enum")
    if len(gate_ids) != len(set(gate_ids)):
        raise ContractError("required_gates.entries has duplicate gate_id values")
    actual_required_gates = frozenset(
        (entry["gate_id"], entry["owner"], entry["status"])
        for entry in gate_entries
    )
    if actual_required_gates != _EXPECTED_REQUIRED_GATES:
        raise ContractError(
            "required_gates entries do not exactly match the required "
            "gate_id/owner/initial-status set"
        )
    expected_gates_sha = _sha256_canonical(gate_entries)
    actual_gates_sha = _expect_sha256(
        gates["entries_sha256"], label="required_gates.entries_sha256"
    )
    if not (
        actual_gates_sha
        == expected_gates_sha
        == _EXPECTED_REQUIRED_GATES_ENTRIES_SHA256
    ):
        raise ContractError(
            "required_gates.entries_sha256 must match canonical entries bytes "
            "and the independent module pin"
        )


def _load_manifest(fixture_root: Path) -> Mapping[str, Any]:
    document = _load_canonical_record(
        fixture_root / "manifest.v1.json", label="fixture manifest"
    )
    _validate_manifest(document)
    return document


def load_manifest() -> Mapping[str, Any]:
    """既定 fixture manifest を strict schema と canonical bytes で読む。"""

    return _load_manifest(FIXTURE_ROOT)


def _validate_ruling_profile(document: dict[str, Any], *, design_doc: Path) -> None:
    _expect_exact_keys(
        document, frozenset({"schema_version", "rulings"}), label="ruling profile"
    )
    if document["schema_version"] != _PROFILE_SCHEMA:
        raise ContractError("ruling profile schema_version is unsupported")
    rulings = _expect_list(document["rulings"], label="ruling profile.rulings")
    design_ids = _extract_ruling_ids(design_doc)
    design_selection_enums = _extract_design_selection_enums(design_doc)
    if design_selection_enums != _SELECTION_ENUMS:
        raise ContractError(
            "design §8.1 selection column does not exactly match selection enums"
        )
    design_revocation_schema = _extract_design_revocation_schema(design_doc)
    if design_revocation_schema != _UPPER_REVOCATION_SCHEMA:
        raise ContractError(
            "design §7.5 revocation record schema does not exactly match validator schema"
        )
    actual_ids: list[str] = []
    by_id: dict[str, dict[str, Any]] = {}
    for index, ruling in enumerate(rulings):
        label = f"ruling profile.rulings[{index}]"
        _expect_exact_keys(
            ruling, frozenset({"ruling_id", "status", "selection"}), label=label
        )
        ruling_id = _expect_nonempty_string(ruling["ruling_id"], label=f"{label}.ruling_id")
        status = ruling["status"]
        if type(status) is not str or status not in {
            "resolved",
            "unresolved",
            "not-applicable",
        }:
            raise ContractError(f"{label}.status is outside the ruling status enum")
        selection = ruling["selection"]
        if status == "resolved":
            selection = _expect_nonempty_string(selection, label=f"{label}.selection")
            allowed = _SELECTION_ENUMS.get(ruling_id)
            if allowed is None:
                raise ContractError(
                    f"{label}.selection has no design-defined enum yet"
                )
            if selection not in allowed:
                raise ContractError(f"{label}.selection is outside its allowed enum")
        elif selection is not None:
            raise ContractError(f"{label}.selection must be null unless status is resolved")
        if status == "not-applicable" and ruling_id != "CFAB-S-GUARANTEE":
            raise ContractError(
                f"not-applicable is forbidden outside CFAB-S-GUARANTEE: {ruling_id}"
            )
        actual_ids.append(ruling_id)
        by_id[ruling_id] = ruling
    if tuple(actual_ids) != design_ids:
        raise ContractError(
            "ruling profile IDs/order do not exactly match design §8.1: "
            f"expected={design_ids!r}, actual={tuple(actual_ids)!r}"
        )
    if len(by_id) != len(actual_ids):
        raise ContractError("ruling profile has duplicate ruling IDs")

    seal = by_id["CFAB-S-SEAL"]
    guarantee = by_id["CFAB-S-GUARANTEE"]
    if seal["status"] == "resolved" and seal["selection"] == "S2":
        if guarantee["status"] != "not-applicable":
            raise ContractError(
                "CFAB-S-GUARANTEE must be not-applicable when CFAB-S-SEAL is S2"
            )
    elif guarantee["status"] == "not-applicable":
        raise ContractError(
            "CFAB-S-GUARANTEE is not-applicable only when CFAB-S-SEAL is resolved to S2"
        )
    if seal["status"] == "unresolved" and guarantee["status"] != "unresolved":
        raise ContractError(
            "CFAB-S-GUARANTEE must remain unresolved while CFAB-S-SEAL is unresolved"
        )
    actual_pinned_states = {
        ruling_id: (by_id[ruling_id]["status"], by_id[ruling_id]["selection"])
        for ruling_id in _EXPECTED_RULING_STATES
    }
    if actual_pinned_states != _EXPECTED_RULING_STATES:
        raise ContractError(
            "adjudicated and deferred ruling states do not match the independent pin"
        )


def _load_ruling_profile(fixture_root: Path, design_doc: Path) -> Mapping[str, Any]:
    document = _load_canonical_record(
        fixture_root / "ruling-profile.v1.json", label="ruling profile"
    )
    _validate_ruling_profile(document, design_doc=design_doc)
    return document


def _applicable_unresolved_count(profile: Mapping[str, Any]) -> int:
    rulings = profile["rulings"]
    seal = next(ruling for ruling in rulings if ruling["ruling_id"] == "CFAB-S-SEAL")
    guarantee_is_applicable = (
        seal["status"] == "resolved" and seal["selection"] == "S1"
    )
    return sum(
        ruling["status"] == "unresolved"
        and (
            ruling["ruling_id"] != "CFAB-S-GUARANTEE"
            or guarantee_is_applicable
        )
        for ruling in rulings
    )


def load_ruling_profile() -> Mapping[str, Any]:
    """既定裁定 profile を strict schema・ID 順・applicability つきで読む。"""

    return _load_ruling_profile(FIXTURE_ROOT, DESIGN_DOC)


def _validate_fixture_case(document: dict[str, Any], *, path: Path) -> None:
    _expect_exact_keys(
        document,
        frozenset(
            {
                "schema_version",
                "fixture_id",
                "design_row_id",
                "binding_state",
                "entrypoint",
                "positive_control",
                "negative_case",
                "pending_reason",
            }
        ),
        label=f"fixture case {path.name}",
    )
    if document["schema_version"] != _CASE_SCHEMA:
        raise ContractError(f"fixture case {path.name} schema_version is unsupported")
    fixture_id = _expect_identifier(
        document["fixture_id"], label=f"fixture case {path.name}.fixture_id"
    )
    if path.name != f"{fixture_id}.json":
        raise ContractError(
            f"case filename does not match fixture_id: {path.name!r} != {fixture_id!r}"
        )
    _expect_row_id(
        document["design_row_id"], label=f"fixture case {path.name}.design_row_id"
    )
    entrypoint = _expect_nonempty_string(
        document["entrypoint"], label=f"fixture case {path.name}.entrypoint"
    )
    if _ENTRYPOINT_RE.fullmatch(entrypoint) is None:
        raise ContractError(f"fixture case {path.name}.entrypoint is not module:function")
    state = document["binding_state"]
    if type(state) is not str or state not in {"executable", "pending"}:
        raise ContractError(f"fixture case {path.name}.binding_state is invalid")

    positive = document["positive_control"]
    negative = document["negative_case"]
    pending_reason = document["pending_reason"]
    if state == "executable":
        if positive is None or negative is None or pending_reason is not None:
            raise ContractError(
                f"fixture case {path.name} executable binding_state requires both controls "
                "and null pending_reason"
            )
        _expect_exact_keys(
            positive,
            frozenset({"builder", "case_id", "expected_decision"}),
            label=f"fixture case {path.name}.positive_control",
        )
        _expect_identifier(
            positive["builder"], label=f"fixture case {path.name}.positive_control.builder"
        )
        _expect_identifier(
            positive["case_id"], label=f"fixture case {path.name}.positive_control.case_id"
        )
        if positive["expected_decision"] != "accept":
            raise ContractError(
                f"fixture case {path.name}.positive_control must expect accept"
            )
        _expect_exact_keys(
            negative,
            frozenset({"builder", "case_id", "expected_decision", "single_mutation"}),
            label=f"fixture case {path.name}.negative_case",
        )
        _expect_identifier(
            negative["builder"], label=f"fixture case {path.name}.negative_case.builder"
        )
        _expect_identifier(
            negative["case_id"], label=f"fixture case {path.name}.negative_case.case_id"
        )
        if negative["expected_decision"] != "reject":
            raise ContractError(f"fixture case {path.name}.negative_case must expect reject")
        _expect_nonempty_string(
            negative["single_mutation"],
            label=f"fixture case {path.name}.negative_case.single_mutation",
        )
    else:
        if positive is not None or negative is not None or pending_reason is None:
            raise ContractError(
                f"fixture case {path.name} pending binding_state requires null controls "
                "and a pending_reason"
            )
        _expect_nonempty_string(
            pending_reason, label=f"fixture case {path.name}.pending_reason"
        )


def _load_fixture_cases(fixture_root: Path) -> tuple[Mapping[str, Any], ...]:
    cases_dir = fixture_root / "cases"
    try:
        paths = sorted(cases_dir.glob("*.json"))
    except OSError as exc:
        raise ContractError(f"fixture cases directory cannot be read: {cases_dir}") from exc
    documents: list[Mapping[str, Any]] = []
    fixture_ids: list[str] = []
    for path in paths:
        if not path.is_file():
            raise ContractError(f"fixture case path is not a regular file: {path}")
        document = _load_canonical_record(path, label=f"fixture case {path.name}")
        _validate_fixture_case(document, path=path)
        documents.append(document)
        fixture_ids.append(document["fixture_id"])
    if len(fixture_ids) != len(set(fixture_ids)):
        raise ContractError("case files have duplicate fixture_id values")
    return tuple(sorted(documents, key=lambda document: document["fixture_id"]))


def load_fixture_cases() -> tuple[Mapping[str, Any], ...]:
    """実在する全 case file を strict 検証し fixture_id 昇順で返す。"""

    return _load_fixture_cases(FIXTURE_ROOT)


def _validate_repository(fixture_root: Path, design_doc: Path) -> Mapping[str, Any]:
    manifest = _load_manifest(fixture_root)
    profile = _load_ruling_profile(fixture_root, design_doc)
    cases = _load_fixture_cases(fixture_root)
    design_row_ids = _extract_design_row_ids(design_doc)
    (
        stage6_predicates,
        stage6_control,
        stage6_execution_boundary,
        stage6_policy_gate,
    ) = _extract_stage6_contract(design_doc)
    if (
        stage6_predicates != _EXPECTED_STAGE6_STRUCTURAL_PREDICATES
        or stage6_control != _EXPECTED_STAGE6_STRUCTURAL_CONTROL
        or stage6_execution_boundary != _EXPECTED_STAGE6_EXECUTION_BOUNDARY
    ):
        raise ContractError("design §10 stage 6 structural predicates drifted")
    stage6_policy_gates = [
        (entry["gate_id"], entry["owner"], entry["status"])
        for entry in manifest["required_gates"]["entries"]
        if entry["gate_id"].startswith("CFAB-STAGE6-POLICY-")
    ]
    if stage6_policy_gates != [stage6_policy_gate]:
        raise ContractError(
            "design §10 stage 6 policy gate does not exactly match required_gates"
        )
    expected_assignment_gate_id = _fixture_assignment_gate_id_from_design(design_doc)
    assignment_gate_ids = [
        entry["gate_id"]
        for entry in manifest["required_gates"]["entries"]
        if entry["gate_id"].endswith("-FIXTURE-ASSIGNMENT")
    ]
    if assignment_gate_ids != [expected_assignment_gate_id]:
        raise ContractError(
            "design §10 stage scope does not exactly match the fixture assignment gate ID"
        )

    declared_entries = manifest["fixtures"]["entries"]
    declared_by_id = {entry["fixture_id"]: entry for entry in declared_entries}
    actual_by_id = {case["fixture_id"]: case for case in cases}
    declared_ids = set(declared_by_id)
    actual_ids = set(actual_by_id)
    if declared_ids != actual_ids:
        raise ContractError(
            "fixture entries do not exactly match case files: "
            f"missing case files={sorted(declared_ids - actual_ids)}, "
            f"orphan case files={sorted(actual_ids - declared_ids)}"
        )
    expected_ids = set(_EXPECTED_RAW_SHA256_BY_FIXTURE)
    if declared_ids != expected_ids:
        raise ContractError(
            "fixture IDs do not exactly match the independent raw SHA-256 pins: "
            f"missing pins={sorted(declared_ids - expected_ids)}, "
            f"unused pins={sorted(expected_ids - declared_ids)}"
        )

    for fixture_id, entry in declared_by_id.items():
        path = fixture_root / entry["path"]
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise ContractError(f"declared fixture case cannot be read: {path}") from exc
        actual_sha = hashlib.sha256(raw).hexdigest()
        expected_sha = _EXPECTED_RAW_SHA256_BY_FIXTURE[fixture_id]
        if entry["raw_sha256"] != actual_sha or actual_sha != expected_sha:
            raise ContractError(
                f"fixture raw SHA-256 mismatch for {fixture_id}: "
                f"manifest={entry['raw_sha256']}, actual={actual_sha}, "
                f"independent={expected_sha}"
            )
    if manifest["fixtures"]["entries_sha256"] != _EXPECTED_FIXTURE_ENTRIES_SHA256:
        raise ContractError("fixtures.entries_sha256 does not match its independent pin")

    coverage_entries = manifest["row_coverage"]["entries"]
    coverage_row_ids = [entry["row_id"] for entry in coverage_entries]
    coverage_fixture_ids = [entry["fixture_id"] for entry in coverage_entries]
    if len(coverage_row_ids) != len(set(coverage_row_ids)):
        raise ContractError("row_coverage must bind every design row exactly once")
    if set(coverage_row_ids) != set(design_row_ids):
        raise ContractError(
            "row_coverage does not exactly match design row IDs: "
            f"missing={sorted(set(design_row_ids) - set(coverage_row_ids))}, "
            f"extra={sorted(set(coverage_row_ids) - set(design_row_ids))}"
        )
    if len(coverage_fixture_ids) != len(set(coverage_fixture_ids)):
        raise ContractError("row_coverage must bind every fixture exactly once")
    if set(coverage_fixture_ids) != declared_ids:
        raise ContractError(
            "row_coverage fixture IDs do not exactly match fixture entries: "
            f"missing={sorted(declared_ids - set(coverage_fixture_ids))}, "
            f"extra={sorted(set(coverage_fixture_ids) - declared_ids)}"
        )
    coverage_by_fixture = {
        entry["fixture_id"]: entry["row_id"] for entry in coverage_entries
    }
    for fixture_id, case in actual_by_id.items():
        if coverage_by_fixture[fixture_id] != case["design_row_id"]:
            raise ContractError(
                f"case design_row_id disagrees with row_coverage for {fixture_id}"
            )

    row_coverage = manifest["row_coverage"]
    if row_coverage["row_count"] != len(design_row_ids):
        raise ContractError("row_coverage.row_count does not match design row count")
    expected_row_ids_sha = _sha256_canonical(list(design_row_ids))
    if row_coverage["row_ids_sha256"] != expected_row_ids_sha:
        raise ContractError(
            "row_coverage.row_ids_sha256 does not match extracted design row IDs"
        )
    if row_coverage["row_ids_sha256"] != _EXPECTED_ROW_IDS_SHA256:
        raise ContractError(
            "row_coverage.row_ids_sha256 does not match its independent pin"
        )

    pending_count = sum(case["binding_state"] == "pending" for case in cases)
    if row_coverage["pending_count"] != pending_count:
        raise ContractError(
            "row_coverage.pending_count does not match pending fixture cases: "
            f"manifest={row_coverage['pending_count']}, actual={pending_count}"
        )
    unresolved_count = _applicable_unresolved_count(profile)
    blocking_gate_statuses = {"unresolved", "pending", "nonconforming"}
    has_blocking_gate = any(
        entry["status"] in blocking_gate_statuses
        for entry in manifest["required_gates"]["entries"]
    )
    computed_status = (
        "incomplete"
        if pending_count > 0 or unresolved_count > 0 or has_blocking_gate
        else "complete"
    )
    if manifest["status"] != computed_status:
        raise ContractError(
            "manifest status disagrees with computed repository status: "
            f"manifest={manifest['status']}, computed={computed_status}"
        )

    return {
        "status": computed_status,
        "pending_count": pending_count,
        "unresolved_count": unresolved_count,
        "row_ids": design_row_ids,
        "executable_fixture_ids": tuple(
            sorted(
                case["fixture_id"]
                for case in cases
                if case["binding_state"] == "executable"
            )
        ),
    }


def validate_repository(
    fixture_root: Path = FIXTURE_ROOT,
    design_doc: Path = DESIGN_DOC,
) -> Mapping[str, Any]:
    """指定 repository の fixture 閉包を検査し、完了とは別の要約を返す。"""

    return _validate_repository(fixture_root, design_doc)


def require_stage0_complete(
    fixture_root: Path = FIXTURE_ROOT,
    design_doc: Path = DESIGN_DOC,
) -> Mapping[str, Any]:
    """段 0 の完了を要求し、blocker が一つでもあれば fail-closed にする。"""

    summary = validate_repository(fixture_root, design_doc)
    manifest = _load_manifest(fixture_root)
    blocking_gate_statuses = {"unresolved", "pending", "nonconforming"}
    blocking_gate_count = sum(
        entry["status"] in blocking_gate_statuses
        for entry in manifest["required_gates"]["entries"]
    )
    if (
        summary["status"] != "complete"
        or summary["pending_count"] != 0
        or summary["unresolved_count"] != 0
        or blocking_gate_count != 0
    ):
        raise ContractError(
            "stage 0 is incomplete: "
            f"status={summary['status']}, pending={summary['pending_count']}, "
            f"applicable_unresolved={summary['unresolved_count']}, "
            f"blocking_gates={blocking_gate_count}"
        )

    return summary
