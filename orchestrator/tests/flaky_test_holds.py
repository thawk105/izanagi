"""Evidence-backed registry for tests excluded from the default acceptance run.

The registry is intentionally narrower than a pytest selector: its keys are
complete node IDs and collection code compares those keys literally.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType


ACCEPTANCE_COLLECTION = "acceptance-full-suite"
_NODE_ID_RE = re.compile(r"^[^\r\n]+\.py::[^\r\n]+$")
_EVIDENCE_ID_RE = re.compile(r"^F[0-9]+$")
_REINTRODUCTION_TASK_ID_RE = re.compile(
    r"^(?:[a-z0-9]+(?:-[a-z0-9]+)*|\{\{T:[a-z0-9]+(?:-[a-z0-9]+)*\}\})$"
)
_FAILURES_LEDGER = Path(__file__).resolve().parents[2] / "docs" / "failures.md"


@dataclass(frozen=True, slots=True)
class FlakyTestHold:
    """One explicitly registered, evidence-backed flaky node."""

    known_failure_node_ids: frozenset[str]
    same_tree: bool
    green_observation: str
    green_collection_condition: str
    green_run_count: int
    red_observation: str
    red_collection_condition: str
    failure_signature: str
    cause: str
    evidence_id: str
    reintroduction_task_id: str


def _nonblank(value: object, field: str, node_id: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"blank or non-string {field} for {node_id!r}")


def _read_failures_ledger() -> str:
    try:
        return _FAILURES_LEDGER.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValueError(
            f"canonical flaky-test evidence ledger cannot be read: {_FAILURES_LEDGER}"
        ) from exc


def _evidence_section(evidence_id: str) -> str | None:
    text = _read_failures_ledger()
    heading = re.search(
        rf"(?m)^###\s+{re.escape(evidence_id)}\b[^\n]*(?:\n|$)",
        text,
    )
    if heading is None:
        return None
    remainder = text[heading.end():]
    next_heading = re.search(r"(?m)^###\s+", remainder)
    if next_heading is None:
        return remainder
    return remainder[:next_heading.start()]


def _evidence_exists(evidence_id: str) -> bool:
    return _evidence_section(evidence_id) is not None


def _normalized_evidence_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("`", "")).strip()


def _test_function_name(node_id: str) -> str:
    return node_id.rsplit("::", 1)[1].split("[", 1)[0]


def _validate_flaky_test_hold_rows(
    rows: Iterable[tuple[str, FlakyTestHold]],
) -> Mapping[str, FlakyTestHold]:
    """Validate registry rows and return an immutable mapping.

    This validator is deliberately strict so an incomplete registration cannot
    silently turn a failing acceptance run green.
    """
    materialized = tuple(rows)
    try:
        mapping = dict(materialized)
    except (TypeError, ValueError) as exc:
        raise ValueError("flaky-test hold registry rows are not key/value pairs") from exc
    if len(mapping) != len(materialized):
        raise ValueError("flaky-test hold registry contains duplicate keys")

    for node_id, hold in materialized:
        if not isinstance(node_id, str) or _NODE_ID_RE.fullmatch(node_id) is None:
            raise ValueError(f"invalid flaky-test hold node ID: {node_id!r}")
        if not isinstance(hold, FlakyTestHold):
            raise ValueError(f"invalid flaky-test hold row for {node_id!r}")
        if not isinstance(hold.known_failure_node_ids, frozenset):
            raise ValueError(
                f"known_failure_node_ids must be frozenset for {node_id!r}"
            )
        if hold.known_failure_node_ids != frozenset({node_id}):
            raise ValueError(
                f"known_failure_node_ids must equal registry key for {node_id!r}"
            )
        if hold.same_tree is not True:
            raise ValueError(f"same_tree must be true for {node_id!r}")
        _nonblank(hold.green_observation, "green_observation", node_id)
        _nonblank(hold.red_observation, "red_observation", node_id)
        _nonblank(
            hold.green_collection_condition,
            "green_collection_condition",
            node_id,
        )
        _nonblank(
            hold.red_collection_condition,
            "red_collection_condition",
            node_id,
        )
        if ACCEPTANCE_COLLECTION not in (
            hold.green_collection_condition,
            hold.red_collection_condition,
        ):
            raise ValueError(
                f"an acceptance-full-suite observation is required for {node_id!r}"
            )
        if (
            isinstance(hold.green_run_count, bool)
            or not isinstance(hold.green_run_count, int)
            or hold.green_run_count < 1
        ):
            raise ValueError(f"green_run_count must be positive for {node_id!r}")
        _nonblank(hold.failure_signature, "failure_signature", node_id)
        _nonblank(hold.cause, "cause", node_id)
        if not isinstance(hold.evidence_id, str) or not _EVIDENCE_ID_RE.fullmatch(
            hold.evidence_id
        ):
            raise ValueError(f"invalid evidence_id for {node_id!r}")
        evidence_section = _evidence_section(hold.evidence_id)
        if evidence_section is None:
            raise ValueError(
                f"evidence_id {hold.evidence_id!r} is absent from docs/failures.md"
            )
        test_function = _test_function_name(node_id)
        normalized_section = _normalized_evidence_text(evidence_section)
        if test_function not in normalized_section:
            raise ValueError(
                f"evidence_id {hold.evidence_id!r} does not mention test function "
                f"{test_function!r} for {node_id!r}"
            )
        if _normalized_evidence_text(hold.failure_signature) not in normalized_section:
            raise ValueError(
                f"failure_signature for {node_id!r} is not present in evidence "
                f"section {hold.evidence_id!r}"
            )
        if not isinstance(hold.reintroduction_task_id, str) or not _REINTRODUCTION_TASK_ID_RE.fullmatch(
            hold.reintroduction_task_id
        ):
            raise ValueError(f"invalid reintroduction_task_id for {node_id!r}")
    return MappingProxyType(mapping)


def _hold_payload(hold: FlakyTestHold) -> dict[str, object]:
    return {
        "known_failure_node_ids": sorted(hold.known_failure_node_ids),
        "same_tree": hold.same_tree,
        "green_observation": hold.green_observation,
        "green_collection_condition": hold.green_collection_condition,
        "green_run_count": hold.green_run_count,
        "red_observation": hold.red_observation,
        "red_collection_condition": hold.red_collection_condition,
        "failure_signature": hold.failure_signature,
        "cause": hold.cause,
        "evidence_id": hold.evidence_id,
        "reintroduction_task_id": hold.reintroduction_task_id,
    }


def _registry_sha256(registry: Mapping[str, FlakyTestHold]) -> str:
    payload = [
        {"node_id": node_id, "hold": _hold_payload(registry[node_id])}
        for node_id in sorted(registry)
    ]
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(canonical).hexdigest()


_EXPLORATION_EXTERNAL_ROOT_NODE = (
    "orchestrator/tests/test_dev_wave_land.py::"
    "test_exploration_external_root_keeps_wave_clean"
)
_CHECK_RECEIPT_V1_EXPLICIT_SKIP_FALSE_NODE = (
    "orchestrator/tests/test_codex_worker_launch.py::"
    "test_check_receipt_reads_v1_field_sets_with_explicit_skip_diagnostics[False]"
)


_FLAKY_TEST_HOLD_ROWS = (
    (
        _EXPLORATION_EXTERNAL_ROOT_NODE,
        FlakyTestHold(
            known_failure_node_ids=frozenset({_EXPLORATION_EXTERNAL_ROOT_NODE}),
            same_tree=True,
            green_observation=(
                "同一 tree の 10 file 焦点走では当該 node が緑だった"
            ),
            green_collection_condition="focused-10-file",
            green_run_count=1,
            red_observation=(
                "同一 tip の受入全走と exact node 単独再走で同じ本文の赤を観測した"
            ),
            red_collection_condition=ACCEPTANCE_COLLECTION,
            failure_signature=(
                "Pegasus compute では receipt state 内で一意な required "
                "authorization_contract だけを受理する"
            ),
            cause=(
                "Pegasus compute の receipt state における required "
                "authorization_contract 一意性判定の site 依存フレーク"
            ),
            evidence_id="F57",
            reintroduction_task_id="t-1079",
        ),
    ),
    (
        _CHECK_RECEIPT_V1_EXPLICIT_SKIP_FALSE_NODE,
        FlakyTestHold(
            known_failure_node_ids=frozenset(
                {_CHECK_RECEIPT_V1_EXPLICIT_SKIP_FALSE_NODE}
            ),
            same_tree=True,
            green_observation=(
                "同一 tip の exact node 単独走は 1 passed in 5.60s で、"
                "直後の受入全走は 18499 passed / 62 skipped で緑だった"
            ),
            green_collection_condition=(
                "exact-node-single-run + acceptance-full-suite"
            ),
            green_run_count=2,
            red_observation=(
                "同一 tip の受入 attempt 1 で当該 exact node が唯一の赤だった"
            ),
            red_collection_condition=ACCEPTANCE_COLLECTION,
            failure_signature="subprocess 出力が空による JSONDecodeError",
            cause=(
                "launcher プロセス全体の実時間が admission 上限を超えると v1 "
                "判定表が拒否する経路を実測で再現した。当時の receipt と stderr は"
                "残っておらず、当該赤がこの経路だった直接証拠は無い"
            ),
            evidence_id="F273",
            reintroduction_task_id="t-2073",
        ),
    ),
)


FLAKY_TEST_HOLDS = _validate_flaky_test_hold_rows(_FLAKY_TEST_HOLD_ROWS)
FLAKY_TEST_HOLD_NODE_IDS = frozenset(FLAKY_TEST_HOLDS)
FLAKY_TEST_HOLDS_SHA256 = _registry_sha256(FLAKY_TEST_HOLDS)


def flaky_test_hold_registry_sha256(
    registry: Mapping[str, FlakyTestHold] | None = None,
) -> str:
    """Return the stable digest used by the end-of-run summary."""
    return _registry_sha256(FLAKY_TEST_HOLDS if registry is None else registry)


validate_flaky_test_hold_rows = _validate_flaky_test_hold_rows
