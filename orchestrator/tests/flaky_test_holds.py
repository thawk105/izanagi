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


_FLAKY_TEST_HOLD_ROWS = (
    (
        "orchestrator/tests/test_pegasus_dispatch_compute.py::"
        "test_control_lock_allows_peer_after_pending_hold_is_durably_released",
        FlakyTestHold(
            known_failure_node_ids=frozenset({
                "orchestrator/tests/test_pegasus_dispatch_compute.py::"
                "test_control_lock_allows_peer_after_pending_hold_is_durably_released",
            }),
            same_tree=True,
            green_observation=(
                "同一 tree の単独 node 実走が 1 passed / 13.56 秒で再現しなかった"
            ),
            green_collection_condition="single-node",
            green_run_count=1,
            red_observation=(
                "同一 tree の受入全走で 1 failed / 16384 passed / 60 skipped"
            ),
            red_collection_condition=ACCEPTANCE_COLLECTION,
            failure_signature="assert not first.is_alive() and not second.is_alive()",
            cause=(
                "受入全走の高並列下で thread の join が実時間上界を超える "
                "(F480 の族)"
            ),
            evidence_id="F480",
            reintroduction_task_id="{{T:flaky-thread-join-upper-bound}}",
        ),
    ),
    (
        "orchestrator/tests/test_s8b_oracle_driver.py::"
        "test_t080_stub_free_e2e_temp_roots_fail_closed_at_real_output_boundary",
        FlakyTestHold(
            known_failure_node_ids=frozenset({
                "orchestrator/tests/test_s8b_oracle_driver.py::"
                "test_t080_stub_free_e2e_temp_roots_fail_closed_at_real_output_boundary",
            }),
            same_tree=True,
            green_observation=(
                "親が同一 tree で単独 node を実走し 1 passed / 11.83 秒だった"
            ),
            green_collection_condition="single-node",
            green_run_count=1,
            red_observation=(
                "同一 tree の受入全走で 1 failed / 16558 passed / 60 skipped"
            ),
            red_collection_condition=ACCEPTANCE_COLLECTION,
            failure_signature=(
                "別 helper _t080_output_snapshot() が output/ 自身の mtime 変化"
            ),
            cause=(
                "受入全走の shard 経路が同じ作業木から 2 request を重ねて投入し、"
                "片方の output/runs/pytest-launcher-failures の mtime 変化をもう片方の "
                "output/ before/after snapshot 検査が拾う (F136 の族)"
            ),
            evidence_id="F136",
            reintroduction_task_id="{{T:t080-output-snapshot-shard-race}}",
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
