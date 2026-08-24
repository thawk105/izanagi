"""Fold 後 canonical の意味検査 node registry。"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Literal, Mapping

from orchestrator.tests.growth_test_holds import GROWTH_TEST_HOLDS


TargetFamily = Literal[
    "worklog",
    "archive",
    "decisions",
    "failures",
    "phase3",
    "folded",
    "rotation",
]
TARGET_FAMILIES = (
    "worklog",
    "archive",
    "decisions",
    "failures",
    "phase3",
    "folded",
    "rotation",
)
_TARGET_FAMILY_SET = frozenset(TARGET_FAMILIES)
_NODE_ID_RE = re.compile(r"^[A-Za-z0-9_]+\.py::[A-Za-z0-9_]+$")
D781_EXCLUSION_REASON = (
    "D781: correctness gate 付き growth hold の復帰は専用 wave の仕事であり、"
    "fold gate は opt-in token を立てないため対象外。"
)


@dataclass(frozen=True, slots=True)
class FoldGateNode:
    target_family: tuple[TargetFamily, ...]
    reason: str
    exclusion_reason: str | None = None


_NODE_ROWS = (
    (
        "test_spool_fold.py::test_failure_supersede_real_f1_boundary_without_blank_line_is_byte_exact",
        FoldGateNode(
            ("failures",),
            "実 failures canonical の F1/F2 境界へ supersede を exact splice し、"
            "既存 bytes と entry topology を検査する。",
        ),
    ),
    (
        "test_spool_fold.py::test_failure_supersede_real_f196_f197_boundary_is_byte_exact",
        FoldGateNode(
            ("failures",),
            "実 failures canonical の F196/F197 境界へ supersede を exact splice し、"
            "空行境界を含む既存 bytes を検査する。",
        ),
    ),
    (
        "test_spool_fold.py::test_failure_supersede_real_final_entry_eof_is_byte_exact",
        FoldGateNode(
            ("failures",),
            "実 failures canonical の最終 entry へ supersede を追記し、"
            "EOF 境界と既存 bytes を検査する。",
        ),
    ),
    (
        "test_spool_fold.py::test_cli_base_digest_real_corpus_resolves_active_and_rejects_completed",
        FoldGateNode(
            ("worklog", "archive"),
            "実 worklog と archive の carry 鎖から active 本文 digest を解決し、"
            "active と completed の意味を CLI で検査する。",
        ),
    ),
    (
        "test_spool_fold.py::test_n37_real_repo_canonical_family_requires_archive_active_history",
        FoldGateNode(
            ("worklog", "archive", "folded"),
            "実 worklog/archive の active-history 解決を必須にし、実 FOLDED receipt を読んだ"
            "計画が worklog と FOLDED を更新対象にすることを検査する。",
        ),
    ),
)


def _validate_node_rows(
    rows: Iterable[tuple[str, FoldGateNode]],
) -> Mapping[str, FoldGateNode]:
    """完全な registry snapshot を検証し、immutable mapping を返す。"""
    materialized = tuple(rows)
    if not materialized:
        raise ValueError("fold-gate node registry must not be empty")

    mapping = dict(materialized)
    if len(mapping) != len(materialized):
        raise ValueError(
            "fold-gate node registry contains duplicate keys or has a "
            "row/mapping cardinality mismatch"
        )

    for node_id, row in materialized:
        if not isinstance(node_id, str) or _NODE_ID_RE.fullmatch(node_id) is None:
            raise ValueError(f"invalid fold-gate node ID: {node_id!r}")
        if not node_id.startswith("test_spool_fold.py::"):
            raise ValueError(f"fold-gate node is outside test_spool_fold.py: {node_id!r}")
        if not isinstance(row, FoldGateNode):
            raise ValueError(f"invalid fold-gate node row for {node_id!r}")
        families = row.target_family
        if (
            type(families) is not tuple
            or not families
            or len(families) != len(set(families))
            or any(type(family) is not str or family not in _TARGET_FAMILY_SET for family in families)
        ):
            raise ValueError(f"invalid target_family for {node_id!r}: {families!r}")
        if not isinstance(row.reason, str) or not row.reason.strip():
            raise ValueError(f"blank reason for {node_id!r}")
        if "\r" in row.reason or len(row.reason.splitlines()) not in {1, 2}:
            raise ValueError(f"reason must be one or two LF lines for {node_id!r}")
        excluded = row.exclusion_reason
        if excluded is not None and (
            not isinstance(excluded, str) or not excluded.strip()
        ):
            raise ValueError(f"invalid exclusion_reason for {node_id!r}")
        held = node_id in GROWTH_TEST_HOLDS
        if held and excluded != D781_EXCLUSION_REASON:
            raise ValueError(f"growth-held node lacks the exact D781 exclusion: {node_id!r}")
        if not held and excluded is not None:
            raise ValueError(f"non-held node has an exclusion reason: {node_id!r}")
    return MappingProxyType(mapping)


FOLD_GATE_NODE_REGISTRY = _validate_node_rows(_NODE_ROWS)
FOLD_GATE_SELECTED_NODES = MappingProxyType({
    node_id: row
    for node_id, row in FOLD_GATE_NODE_REGISTRY.items()
    if row.exclusion_reason is None
})


def _validate_uncovered_family_allowlist(
    reasons: Mapping[str, str],
) -> Mapping[str, str]:
    if type(reasons) is not dict:
        raise ValueError("fold-gate uncovered allowlist must be an exact dict")
    for family, reason in reasons.items():
        if type(family) is not str or family not in _TARGET_FAMILY_SET:
            raise ValueError(
                f"invalid fold-gate uncovered family: {family!r}"
            )
        if (
            type(reason) is not str
            or not reason.strip()
            or "\r" in reason
            or len(reason.splitlines()) not in {1, 2}
        ):
            raise ValueError(
                f"invalid fold-gate uncovered reason: {family!r}"
            )
    return MappingProxyType(dict(reasons))


FOLD_GATE_UNCOVERED_FAMILY_ALLOWLIST = _validate_uncovered_family_allowlist({
    "decisions": (
        "実 decisions canonical を読む既存 pytest に、fold 後の採番と本文を"
        "意味検査する node がまだ無い。"
    ),
    "phase3": (
        "実 phase3 canonical を読む既存 pytest に、fold 後の見送り更新を"
        "意味検査する node がまだ無い。"
    ),
    "rotation": (
        "実 rotation archive と索引を同時に読む既存 pytest に、fold 後 bytes を"
        "意味検査する node がまだ無い。"
    ),
})


def fold_gate_node_registry_sha256(
    rows: Mapping[str, FoldGateNode] = FOLD_GATE_NODE_REGISTRY,
    uncovered_allowlist: Mapping[
        str, str
    ] = FOLD_GATE_UNCOVERED_FAMILY_ALLOWLIST,
) -> str:
    payload = {
        "nodes": [
            {
                "exclusion_reason": row.exclusion_reason,
                "node_id": node_id,
                "reason": row.reason,
                "target_family": list(row.target_family),
            }
            for node_id, row in sorted(rows.items())
        ],
        "uncovered_family_allowlist": dict(
            sorted(uncovered_allowlist.items())
        ),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


FOLD_GATE_NODE_REGISTRY_SHA256 = "cf69d81c65cb79d415c590ce116f06742e18c9bf8a5996e21d21f8c97c434752"
if fold_gate_node_registry_sha256() != FOLD_GATE_NODE_REGISTRY_SHA256:
    raise ValueError(
        "fold-gate node registry digest drift: "
        f"observed={fold_gate_node_registry_sha256()}"
    )


def _validate_family_minimums(
    minimums: Mapping[str, int],
) -> Mapping[str, int]:
    if type(minimums) is not dict or frozenset(minimums) != _TARGET_FAMILY_SET:
        raise ValueError("fold-gate family minimum key set is not exact")
    if any(type(value) is not int or value < 1 for value in minimums.values()):
        raise ValueError("fold-gate family minimum must be a positive int")
    return MappingProxyType(dict(minimums))


FOLD_GATE_FAMILY_MINIMUMS = _validate_family_minimums({
    family: 1 for family in TARGET_FAMILIES
})


def fold_gate_family_population() -> Mapping[str, int]:
    counts = {family: 0 for family in TARGET_FAMILIES}
    for row in FOLD_GATE_SELECTED_NODES.values():
        for family in row.target_family:
            counts[family] += 1
    return MappingProxyType(counts)


def fold_gate_family_shortfalls(
    target_families: Iterable[str],
) -> Mapping[str, tuple[int, int]]:
    """対象 family の ``minimum -> observed`` 不足だけを返す。"""
    materialized = tuple(target_families)
    if (
        len(materialized) != len(set(materialized))
        or any(type(family) is not str or family not in _TARGET_FAMILY_SET for family in materialized)
    ):
        raise ValueError("invalid or duplicate fold-gate target family")
    population = fold_gate_family_population()
    return MappingProxyType({
        family: (FOLD_GATE_FAMILY_MINIMUMS[family], population[family])
        for family in materialized
        if population[family] < FOLD_GATE_FAMILY_MINIMUMS[family]
    })
