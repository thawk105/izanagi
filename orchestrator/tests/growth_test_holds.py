"""Repository-growth-proportional test hold registry and inventory CLI."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
from dataclasses import asdict, dataclass
from functools import wraps
from types import MappingProxyType
from typing import Callable, Iterable, Literal, Mapping, MutableMapping


RELEASE_EXPLICIT_USER_COMMAND_ONLY = "explicit-user-command-only"
RUN_GROWTH_HELD_TESTS_ENV = "IZANAGI_RUN_GROWTH_HELD_TESTS"
RUN_GROWTH_HELD_TESTS_TOKEN = "explicit-user-command"
RULING_2026_08_12_BUNDLE_3 = "2026-08-12 rulings 第 3 束"

HOLD_AXES = frozenset({
    "commits",
    "tracked_files",
    "docs_bytes",
    "output_artifacts",
    "provenance-chain",
})
_HOLD_KEY_RE = re.compile(r"^[A-Za-z0-9_]+\.py::[A-Za-z0-9_]+$")


@dataclass(frozen=True, slots=True)
class GrowthTestHold:
    hold_axis: str
    ruling: str
    reason: str
    correctness_gate: bool
    release_condition: str
    measured_seconds: float | None
    collateral_note: str | None = None


def _hold(
    hold_axis: str,
    reason: str,
    *,
    collateral_note: str | None = None,
) -> GrowthTestHold:
    return GrowthTestHold(
        hold_axis=hold_axis,
        ruling=RULING_2026_08_12_BUNDLE_3,
        reason=reason,
        correctness_gate=True,
        release_condition=RELEASE_EXPLICIT_USER_COMMAND_ONLY,
        measured_seconds=None,
        collateral_note=collateral_note,
    )


_CLONE_REASON = (
    "Copies the real repository without hardlinks, so cost grows with commit history."
)
_ROLLOUT_REASON = (
    "Recursively enumerates the real Codex session corpus, so cost grows with output artifacts."
)

_HOLD_ROWS = (
    ("test_codex_reasoning_ab.py::test_m3_focus_artifact_directions", _hold("commits", _CLONE_REASON)),
    ("test_codex_reasoning_ab.py::test_verify_replays_complete_fake_codex_experiment", _hold("commits", _CLONE_REASON)),
    ("test_codex_reasoning_ab.py::test_m3_ignored_extra_and_missing", _hold("commits", _CLONE_REASON)),
    ("test_codex_reasoning_ab.py::test_m3_snapshot_mode_change", _hold("commits", _CLONE_REASON)),
    ("test_codex_reasoning_ab.py::test_cleaned_snapshot_records_absent_commit_graph_and_keeps_closure", _hold("commits", _CLONE_REASON)),
    ("test_codex_reasoning_ab.py::test_stale_commit_graph_referencing_pruned_commit_is_rejected_and_manifested", _hold("commits", _CLONE_REASON)),
    ("test_codex_reasoning_ab.py::test_agent_sandbox_binds_exclude_attempt_receipt_directory", _hold("commits", _CLONE_REASON)),
    ("test_codex_reasoning_ab.py::test_f3_4_prelaunch_exception_completes_pair_and_allows_next_generation", _hold("commits", _CLONE_REASON)),
    ("test_codex_reasoning_ab.py::test_m3_symbolic_head_is_required", _hold("commits", _CLONE_REASON)),
    ("test_codex_reasoning_ab.py::test_m1_snapshot_head_pin_is_independent", _hold("commits", _CLONE_REASON)),
    ("test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases", _hold("commits", _CLONE_REASON)),
    ("test_codex_reasoning_ab.py::test_attempt_four_is_rejected_before_launch", _hold("commits", _CLONE_REASON)),
    ("test_codex_reasoning_ab.py::test_pos_neg_submodule_initialization_state_mismatch_is_rejected", _hold("commits", _CLONE_REASON)),
    ("test_codex_reasoning_ab.py::test_parent_numstat_controls_remain_pinned", _hold("commits", _CLONE_REASON)),
    ("test_codex_reasoning_ab.py::test_m2_production_golden_requires_both_routes", _hold("output_artifacts", _ROLLOUT_REASON)),
    ("test_codex_reasoning_ab.py::test_prompt_replacement_count_zero_expected_and_excess", _hold("output_artifacts", _ROLLOUT_REASON)),
    (
        "test_s8b_oracle_driver.py::test_cli_subprocess_returns_rc_2_on_gate_refused",
        _hold("commits", "Runs the real repository freeze/history gate whose cost grows with commit history."),
    ),
    (
        "test_s8b_binding_driftguards.py::test_run_block_broken_binding_manifest_refuses_and_writes_nothing",
        _hold("commits", "Runs the real repository binding/history gate whose cost grows with commit history."),
    ),
    (
        "test_s8b_oracle_driver.py::test_real_freeze_gate_lists_floor_and_budget_null",
        _hold("commits", "Runs the real repository freeze/history gate whose cost grows with commit history."),
    ),
    (
        "test_s8b_repo_scan_invariant.py::test_real_repository_scan_matches_known_hits_and_has_positive_control",
        _hold("tracked_files", "Scans the real checkout, so cost grows with tracked files."),
    ),
    (
        "test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight",
        _hold(
            "tracked_files",
            "Scans the real checkout, so cost grows with tracked files.",
            collateral_note=(
                "Holding this node also removes fixed-size checks for the maximum "
                "package, MAX_CANDIDATES/MAX_QUERY_COUNT/MAX_SIGNAL_TOKENS, "
                "independent inspect/pickaxe evidence, and the 45/60-second "
                "preflight boundaries."
            ),
        ),
    ),
    (
        "test_s8b_holdout_freeze.py::test_verify_cli_accepts_active_t080_receipt_exact_match",
        _hold("tracked_files", "Searches the real repository, so cost grows with tracked files."),
    ),
    (
        "test_s8b_holdout_freeze.py::test_verify_direct_cli_accepts_active_t080_receipt_exact_match",
        _hold("tracked_files", "Searches the real repository, so cost grows with tracked files."),
    ),
    (
        "test_campaign_import_invariant.py::test_repository_scan_set_is_nonempty_and_contains_sentinels",
        _hold("tracked_files", "Parses the real operational source and documentation tree."),
    ),
    (
        "test_campaign_import_invariant.py::test_real_campaign_package_uses_relative_sibling_imports",
        _hold("tracked_files", "Parses the real operational source and documentation tree."),
    ),
    (
        "test_campaign_import_invariant.py::test_real_campaign_package_has_canonical_direct_bootstrap",
        _hold("tracked_files", "Parses the real operational source and documentation tree."),
    ),
    (
        "test_campaign_import_invariant.py::test_real_current_docs_have_no_legacy_module_command",
        _hold("tracked_files", "Parses the real operational source and documentation tree."),
    ),
    (
        "test_campaign_import_invariant.py::test_real_repository_legacy_namespace_matches_exception_ledger",
        _hold("tracked_files", "Parses the real operational source and documentation tree."),
    ),
    (
        "test_campaign_import_invariant.py::test_known_exception_ledger_is_unique_rationalized_and_commented",
        _hold(
            "tracked_files",
            "Consumes the session-scoped repository_scan fixture; holding only five "
            "consumers leaves the full source scan running while removing its "
            "detection power.",
        ),
    ),
    (
        "test_env_attestation.py::test_probe_output_v1_corpus_is_exact_and_replays_all_physical_copies",
        _hold(
            "output_artifacts",
            "Recursively reads the real Pegasus probe corpus.",
            collateral_note=(
                "Holding this node also removes fixed-size checks for corpus count "
                "48, disjoint success/failure sets, and the complete JSON-pair "
                "partition."
            ),
        ),
    ),
)


def _validate_hold_rows(
    rows: Iterable[tuple[str, GrowthTestHold]],
) -> Mapping[str, GrowthTestHold]:
    """Validate a complete registry snapshot and return an immutable mapping."""
    materialized = tuple(rows)
    if not materialized:
        raise ValueError("growth-test hold registry must not be empty")

    mapping = dict(materialized)
    if len(mapping) != len(materialized):
        raise ValueError(
            "growth-test hold registry contains duplicate keys or has a "
            "row/mapping cardinality mismatch"
        )

    for key, hold in materialized:
        if not isinstance(key, str) or _HOLD_KEY_RE.fullmatch(key) is None:
            raise ValueError(f"invalid growth-test hold key: {key!r}")
        if not isinstance(hold, GrowthTestHold):
            raise ValueError(f"invalid growth-test hold row for {key!r}")
        if hold.hold_axis not in HOLD_AXES:
            raise ValueError(f"invalid hold_axis for {key!r}: {hold.hold_axis!r}")
        if not isinstance(hold.ruling, str) or not hold.ruling.strip():
            raise ValueError(f"blank ruling for {key!r}")
        if not isinstance(hold.reason, str) or not hold.reason.strip():
            raise ValueError(f"blank reason for {key!r}")
        if not isinstance(hold.correctness_gate, bool):
            raise ValueError(f"correctness_gate must be bool for {key!r}")
        if hold.release_condition != RELEASE_EXPLICIT_USER_COMMAND_ONLY:
            raise ValueError(f"invalid release_condition for {key!r}")
        collateral_note = hold.collateral_note
        if collateral_note is not None and (
            not isinstance(collateral_note, str) or not collateral_note.strip()
        ):
            raise ValueError(f"invalid collateral_note for {key!r}")
        measured = hold.measured_seconds
        if measured is not None and (
            isinstance(measured, bool)
            or not isinstance(measured, (int, float))
            or not math.isfinite(measured)
            or measured < 0
        ):
            raise ValueError(f"invalid measured_seconds for {key!r}: {measured!r}")
    return MappingProxyType(mapping)


GROWTH_TEST_HOLDS = _validate_hold_rows(_HOLD_ROWS)


class GrowthTestHoldBypassRefused(RuntimeError):
    """A held test function was called without the explicit release token."""


PlainRunner = Literal["pytest-delegating", "manual", "none"]
_PLAIN_RUNNERS = frozenset({"pytest-delegating", "manual", "none"})
_ENFORCING_PYTEST_CONFIG_IDS: set[int] = set()


def mark_pytest_session_enforcing(config: object) -> None:
    """Record that ``config`` owns the canonical hold collection enforcement."""
    _ENFORCING_PYTEST_CONFIG_IDS.add(id(config))


def unmark_pytest_session_enforcing(config: object) -> None:
    """Drop the enforcement record for a completed pytest configuration."""
    _ENFORCING_PYTEST_CONFIG_IDS.discard(id(config))


def _refusal_message(node_id: str) -> str:
    payload = {
        "node_id": node_id,
        "release_env": RUN_GROWTH_HELD_TESTS_ENV,
        "release_token": RUN_GROWTH_HELD_TESTS_TOKEN,
    }
    return "IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1 " + json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def _wrap_held_function(function: Callable, node_id: str) -> Callable:
    @wraps(function)
    def wrapped(*args, **kwargs):
        if os.environ.get(RUN_GROWTH_HELD_TESTS_ENV) != RUN_GROWTH_HELD_TESTS_TOKEN:
            raise GrowthTestHoldBypassRefused(_refusal_message(node_id))
        return function(*args, **kwargs)

    return wrapped


def enforce_held_functions(
    namespace: MutableMapping[str, object],
    module_file: str | os.PathLike[str],
    *,
    plain_runner: PlainRunner,
) -> tuple[str, ...]:
    """Bind held call guards and reject imports outside an enforcing runner."""
    if plain_runner not in _PLAIN_RUNNERS:
        raise ValueError(f"invalid growth-test plain runner: {plain_runner!r}")
    filename = os.path.basename(os.fspath(module_file))
    held_nodes = sorted(
        node_id for node_id in GROWTH_TEST_HOLDS
        if node_id.split("::", 1)[0] == filename
    )
    if not held_nodes:
        raise ValueError(f"no growth-test holds registered for {filename!r}")

    function_names = tuple(node_id.split("::", 1)[1] for node_id in held_nodes)
    missing = tuple(name for name in function_names if name not in namespace)
    if missing:
        raise ValueError(
            f"growth-test held functions missing from {filename!r}: {missing!r}"
        )
    noncallable = tuple(
        name for name in function_names if not callable(namespace[name])
    )
    if noncallable:
        raise ValueError(
            f"growth-test held names are not callable in {filename!r}: {noncallable!r}"
        )

    for node_id, function_name in zip(held_nodes, function_names, strict=True):
        namespace[function_name] = _wrap_held_function(
            namespace[function_name],  # type: ignore[arg-type]
            node_id,
        )

    if _ENFORCING_PYTEST_CONFIG_IDS:
        return function_names
    if os.environ.get(RUN_GROWTH_HELD_TESTS_ENV) == RUN_GROWTH_HELD_TESTS_TOKEN:
        return function_names
    if (
        namespace.get("__name__") == "__main__"
        and plain_runner == "pytest-delegating"
    ):
        return function_names
    raise GrowthTestHoldBypassRefused(_refusal_message(f"{filename}::*"))


def growth_test_hold_key_digest(keys: Iterable[str]) -> str:
    payload = "\n".join(sorted(keys)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def growth_test_hold_inventory() -> dict[str, object]:
    """Return the deterministic, user-presentable exact hold inventory."""
    keys = sorted(GROWTH_TEST_HOLDS)
    return {
        "schema": "izanagi-growth-test-holds/v1",
        "count": len(keys),
        "key_sha256": growth_test_hold_key_digest(keys),
        "correctness_gate_keys": [
            key for key in keys if GROWTH_TEST_HOLDS[key].correctness_gate
        ],
        "holds": [
            {"node_id": key, **asdict(GROWTH_TEST_HOLDS[key])}
            for key in keys
        ],
    }


def main() -> int:
    print(json.dumps(growth_test_hold_inventory(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
