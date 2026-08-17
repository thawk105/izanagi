"""Repository-growth-proportional test hold registry and inventory CLI."""
from __future__ import annotations

import hashlib
import inspect
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


_SNAPSHOT_CORPUS_REASON = (
    "Constructs the shared real snapshot fixture by recursively enumerating "
    "the real Codex session corpus, so cost grows with output artifacts."
)
_ROLLOUT_REASON = (
    "Recursively enumerates the real Codex session corpus, so cost grows with output artifacts."
)
_KNOWN_AXES_ARTIFACT_REASON = (
    "Builds or verifies the real known-axes freeze by globbing and parsing "
    "campaign artifacts, so cost grows with output artifacts."
)
_MEASUREMENT_FIXTURE_REASON = (
    "Consumes the module-scoped real known-axes fixture, which globs and parses "
    "campaign artifacts, so cost grows with output artifacts."
)
_REAL_HISTORY_REASON = (
    "Runs real-repository receipt and active-generation history resolution "
    "over the reachable commit graph, so cost grows with commit history."
)
_REAL_REPO_CLONE_REASON = (
    "Clones the real repository without hardlinks, so cost grows with commit history."
)
_REPO_STATUS_REASON = (
    "Runs full real-repository git status snapshots before and after the action, "
    "so cost grows with tracked files."
)
_CHECK_DOCS_REASON = (
    "Runs the real tools/check_docs.py with no arguments across a variable "
    "input set: enumerated living docs, the rotating docs/archive worklog set, "
    "the handoff directory, and discovered skill, command, reference, and "
    "provenance files. Its cost therefore grows with docs bytes."
)
_CHECK_DOCS_LAND_COLLATERAL = (
    "Land's _validate_generated_docs calls the checker with "
    "--expect-active-transaction after a non-noop fold; a noop fold returns "
    "before the check. The wave checker requires check-docs to be specified "
    "exactly once, but executes it in an isolated checkout only for a completed, "
    "passive-green run; incomplete or passive-failing runs do not execute it. "
    "A no-argument tools/check_docs.py invocation remains mandatory for class "
    "2/3 completion; it is not required for other task classes."
)
_SHARED_FIXTURE_COLLATERAL = (
    "Holding this node also prevents the shared module fixture from starting, "
    "so its fixed checks for full SHA format, CURRENT_PIN prefix, an independent "
    "golden, and K.verify_document stop too."
)


def _fixture_collateral(detail: str) -> str:
    return f"{_SHARED_FIXTURE_COLLATERAL} {detail}"


def _node_collateral(detail: str) -> str:
    return f"Holding this node removes {detail}."


_HOLD_ROWS = (
    ("test_codex_reasoning_ab.py::test_m3_focus_artifact_directions", _hold("output_artifacts", _SNAPSHOT_CORPUS_REASON)),
    ("test_codex_reasoning_ab.py::test_verify_replays_complete_fake_codex_experiment", _hold("output_artifacts", _SNAPSHOT_CORPUS_REASON)),
    ("test_codex_reasoning_ab.py::test_m3_ignored_extra_and_missing", _hold("output_artifacts", _SNAPSHOT_CORPUS_REASON)),
    ("test_codex_reasoning_ab.py::test_m3_snapshot_mode_change", _hold("output_artifacts", _SNAPSHOT_CORPUS_REASON)),
    ("test_codex_reasoning_ab.py::test_cleaned_snapshot_records_absent_commit_graph_and_keeps_closure", _hold("output_artifacts", _SNAPSHOT_CORPUS_REASON)),
    ("test_codex_reasoning_ab.py::test_stale_commit_graph_referencing_pruned_commit_is_rejected_and_manifested", _hold("output_artifacts", _SNAPSHOT_CORPUS_REASON)),
    ("test_codex_reasoning_ab.py::test_agent_sandbox_binds_exclude_attempt_receipt_directory", _hold("output_artifacts", _SNAPSHOT_CORPUS_REASON)),
    ("test_codex_reasoning_ab.py::test_f3_4_prelaunch_exception_completes_pair_and_allows_next_generation", _hold("output_artifacts", _SNAPSHOT_CORPUS_REASON)),
    ("test_codex_reasoning_ab.py::test_m3_symbolic_head_is_required", _hold("output_artifacts", _SNAPSHOT_CORPUS_REASON)),
    ("test_codex_reasoning_ab.py::test_m1_snapshot_head_pin_is_independent", _hold("output_artifacts", _SNAPSHOT_CORPUS_REASON)),
    ("test_codex_reasoning_ab.py::test_forbidden_commits_are_unreachable_in_both_cases", _hold("output_artifacts", _SNAPSHOT_CORPUS_REASON)),
    ("test_codex_reasoning_ab.py::test_attempt_four_is_rejected_before_launch", _hold("output_artifacts", _SNAPSHOT_CORPUS_REASON)),
    ("test_codex_reasoning_ab.py::test_pos_neg_submodule_initialization_state_mismatch_is_rejected", _hold("output_artifacts", _SNAPSHOT_CORPUS_REASON)),
    ("test_codex_reasoning_ab.py::test_parent_numstat_controls_remain_pinned", _hold("output_artifacts", _SNAPSHOT_CORPUS_REASON)),
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
    (
        "test_s1_known_axes_freeze.py::test_build_document_is_self_consistent_and_detects_tamper",
        _hold(
            "output_artifacts",
            _KNOWN_AXES_ARTIFACT_REASON,
            collateral_note=_node_collateral(
                "its fixed self-consistency and single-field tamper rejection checks"
            ),
        ),
    ),
    (
        "test_s1_known_axes_freeze.py::test_generate_refuses_existing_freeze",
        _hold(
            "output_artifacts",
            _KNOWN_AXES_ARTIFACT_REASON,
            collateral_note=_node_collateral(
                "its fixed create-only refusal check"
            ),
        ),
    ),
    (
        "test_s1_known_axes_freeze.py::test_generate_selects_registered_expected_points",
        _hold(
            "output_artifacts",
            _KNOWN_AXES_ARTIFACT_REASON,
            collateral_note=_node_collateral(
                "its fixed golden checks for registered P2, backoff, and sort selections"
            ),
        ),
    ),
    (
        "test_s1_known_axes_freeze.py::test_s1b_pairing_rejects_mismatched_flags",
        _hold(
            "output_artifacts",
            _KNOWN_AXES_ARTIFACT_REASON,
            collateral_note=_node_collateral(
                "its fixed S-1b mismatched-flags rejection check"
            ),
        ),
    ),
    (
        "test_s1_known_axes_freeze.py::test_verify_rejects_foreign_ccbench_pin",
        _hold(
            "output_artifacts",
            _KNOWN_AXES_ARTIFACT_REASON,
            collateral_note=_node_collateral(
                "its fixed held/released ccbench-pin positive control"
            ),
        ),
    ),
    (
        "test_s1_known_axes_freeze.py::test_verify_rejects_generator_sha_tamper",
        _hold(
            "output_artifacts",
            _KNOWN_AXES_ARTIFACT_REASON,
            collateral_note=_node_collateral(
                "its fixed generator-hash tamper rejection check"
            ),
        ),
    ),
    (
        "test_s1_known_axes_freeze.py::test_verify_rejects_non_ancestor_head",
        _hold(
            "output_artifacts",
            _KNOWN_AXES_ARTIFACT_REASON,
            collateral_note=_node_collateral(
                "its fixed non-ancestor HEAD rejection check"
            ),
        ),
    ),
    (
        "test_s1_known_axes_freeze.py::test_verify_rejects_one_byte_freeze_tamper",
        _hold(
            "output_artifacts",
            _KNOWN_AXES_ARTIFACT_REASON,
            collateral_note=_node_collateral(
                "its fixed one-byte freeze tamper rejection check"
            ),
        ),
    ),
    (
        "test_s1_known_axes_freeze.py::test_verify_rejects_tampered_source_copy",
        _hold(
            "output_artifacts",
            _KNOWN_AXES_ARTIFACT_REASON,
            collateral_note=_node_collateral(
                "its fixed copied-source hash tamper rejection check"
            ),
        ),
    ),
    (
        "test_s1_measurement_freeze.py::test_build_document_rejects_tampered_known_axes_semantics",
        _hold(
            "output_artifacts",
            _MEASUREMENT_FIXTURE_REASON,
            collateral_note=_fixture_collateral(
                "The node's fixed known-axes semantic tamper rejection check stops too."
            ),
        ),
    ),
    (
        "test_s1_measurement_freeze.py::test_generate_builds_registered_cells_comparisons_and_schedule",
        _hold(
            "output_artifacts",
            _MEASUREMENT_FIXTURE_REASON,
            collateral_note=_fixture_collateral(
                "The node's fixed checks for 18 cells, 12 comparisons, schedule "
                "shape, seeds, and operating-point flags stop too."
            ),
        ),
    ),
    (
        "test_s1_measurement_freeze.py::test_generate_refuses_existing_freeze",
        _hold(
            "output_artifacts",
            _MEASUREMENT_FIXTURE_REASON,
            collateral_note=_fixture_collateral(
                "The node's fixed measurement create-only refusal check stops too."
            ),
        ),
    ),
    (
        "test_s1_measurement_freeze.py::test_receipt_exists_but_measurement_verify_stays_legacy_strict",
        _hold(
            "output_artifacts",
            _MEASUREMENT_FIXTURE_REASON,
            collateral_note=_fixture_collateral(
                "The node's fixed legacy-verifier isolation from the T-080 "
                "adapter stops too."
            ),
        ),
    ),
    (
        "test_s1_measurement_freeze.py::test_recorded_ccbench_pin_hold_and_release_positive_control",
        _hold(
            "output_artifacts",
            _MEASUREMENT_FIXTURE_REASON,
            collateral_note=_fixture_collateral(
                "The node's fixed recorded-pin hold and release positive control stops too."
            ),
        ),
    ),
    (
        "test_s1_measurement_freeze.py::test_s1b_pairing_rejects_mismatched_flags",
        _hold(
            "output_artifacts",
            _MEASUREMENT_FIXTURE_REASON,
            collateral_note=_fixture_collateral(
                "The node's fixed measurement S-1b mismatched-flags rejection check stops too."
            ),
        ),
    ),
    (
        "test_s1_measurement_freeze.py::test_schedule_is_balanced_and_reproducible",
        _hold(
            "output_artifacts",
            _MEASUREMENT_FIXTURE_REASON,
            collateral_note=_fixture_collateral(
                "The node's fixed schedule balance and reproducibility checks stop too."
            ),
        ),
    ),
    (
        "test_s1_measurement_freeze.py::test_verify_rejects_known_axes_material_tamper",
        _hold(
            "output_artifacts",
            _MEASUREMENT_FIXTURE_REASON,
            collateral_note=_fixture_collateral(
                "The node's fixed known-axes material-hash tamper rejection check stops too."
            ),
        ),
    ),
    (
        "test_s1_measurement_freeze.py::test_verify_rejects_one_byte_freeze_tamper",
        _hold(
            "output_artifacts",
            _MEASUREMENT_FIXTURE_REASON,
            collateral_note=_fixture_collateral(
                "The node's fixed one-byte measurement freeze tamper rejection check stops too."
            ),
        ),
    ),
    (
        "test_s1_measurement_freeze.py::test_verify_rejects_one_byte_workload_flag_tamper",
        _hold(
            "output_artifacts",
            _MEASUREMENT_FIXTURE_REASON,
            collateral_note=_fixture_collateral(
                "The node's fixed one-byte workload-flag tamper rejection check stops too."
            ),
        ),
    ),
    (
        "test_s1_measurement_freeze.py::test_verify_rejects_stats_implementation_tamper",
        _hold(
            "output_artifacts",
            _MEASUREMENT_FIXTURE_REASON,
            collateral_note=_fixture_collateral(
                "The node's fixed statistics-implementation hash tamper rejection check stops too."
            ),
        ),
    ),
    (
        "test_s8b_binding_driftguards.py::test_gate_check_broken_binding_manifest_stacks_manifest_verify_refusal",
        _hold(
            "commits",
            _REAL_HISTORY_REASON,
            collateral_note=(
                "Holding this node also removes the fixed-size binding-manifest "
                "schema refusal aggregation check."
            ),
        ),
    ),
    (
        "test_s8b_oracle_driver.py::test_active_resolution_and_manifest_structure_refusals_are_aggregated",
        _hold(
            "commits",
            _REAL_HISTORY_REASON,
            collateral_note=(
                "Holding this node also removes the fixed-size independent-refusal "
                "aggregation and zero-side-effect checks."
            ),
        ),
    ),
    (
        "test_s8b_oracle_driver.py::test_nonnull_floor_without_active_generation_is_refused",
        _hold(
            "commits",
            _REAL_HISTORY_REASON,
            collateral_note=(
                "Holding this node also removes the fixed-size no-active error "
                "translation, no-prepare, no-evaluate, and no-write checks."
            ),
        ),
    ),
    (
        "test_s8b_oracle_driver.py::test_run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing",
        _hold(
            "commits",
            _REAL_HISTORY_REASON,
            collateral_note=(
                "Holding this node also removes fixed-size refusal, no-prepare, "
                "no-evaluate, and zero-output checks."
            ),
        ),
    ),
    (
        "test_real_repo_serialization.py::test_protocol_builder_repo_tree_guard_is_wired_to_real_root",
        _hold(
            "tracked_files",
            _REPO_STATUS_REASON,
            collateral_note=(
                "Holding this node also removes fixed-size checks for exact ROOT "
                "wiring, single guard invocation, and builder/writer execution "
                "inside that guard."
            ),
        ),
    ),
    (
        "test_s8b_protocol_builder.py::test_build_and_write_leave_repo_tree_unchanged",
        _hold(
            "tracked_files",
            _REPO_STATUS_REASON,
            collateral_note=(
                "Holding this node also removes fixed-size top-level and nested "
                "writer checks and the frozen-output refusal check."
            ),
        ),
    ),
    (
        "test_check_docs.py::test_real_repo_clean",
        _hold(
            "docs_bytes",
            _CHECK_DOCS_REASON,
            collateral_note=(
                "Holding this node removes its fixed-size assertions that the real "
                "checker returns rc=0, reports no violations, and has zero Pegasus "
                f"admission drift findings. {_CHECK_DOCS_LAND_COLLATERAL}"
            ),
        ),
    ),
    (
        "test_check_docs.py::test_dev_wave_model_pins_accept_current_docs_contract",
        _hold(
            "docs_bytes",
            _CHECK_DOCS_REASON,
            collateral_note=(
                "Holding this node removes the fixed-size positive check that the "
                "current dev-wave model pins do not over-reject the real repository. "
                f"{_CHECK_DOCS_LAND_COLLATERAL}"
            ),
        ),
    ),
    (
        "test_check_docs.py::test_normative_exact_section_pins_accept_real_repo",
        _hold(
            "docs_bytes",
            _CHECK_DOCS_REASON,
            collateral_note=(
                "Holding this node removes the fixed-size positive check that "
                "normative section pins do not over-reject the real repository. "
                f"{_CHECK_DOCS_LAND_COLLATERAL}"
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
GuardMode = Literal["import-and-call", "call-only"]
_GUARD_MODES = frozenset({"import-and-call", "call-only"})
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


def _pytest_drives_current_import() -> bool:
    """Return whether the active import call stack belongs to pytest."""
    frame = inspect.currentframe()
    if frame is None:
        return True
    try:
        frame = frame.f_back
        while frame is not None:
            module_name = frame.f_globals.get("__name__")
            if isinstance(module_name, str) and (
                module_name == "_pytest" or module_name.startswith("_pytest.")
            ):
                return True
            frame = frame.f_back
        return False
    finally:
        del frame


def enforce_held_functions(
    namespace: MutableMapping[str, object],
    module_file: str | os.PathLike[str],
    *,
    plain_runner: PlainRunner,
    guard_mode: GuardMode = "import-and-call",
) -> tuple[str, ...]:
    """Bind held call guards and reject imports outside an enforcing runner."""
    if plain_runner not in _PLAIN_RUNNERS:
        raise ValueError(f"invalid growth-test plain runner: {plain_runner!r}")
    if guard_mode not in _GUARD_MODES:
        raise ValueError(f"invalid growth-test guard mode: {guard_mode!r}")
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
    if guard_mode == "call-only":
        if _pytest_drives_current_import():
            raise GrowthTestHoldBypassRefused(_refusal_message(f"{filename}::*"))
        if (
            namespace.get("__name__") == "__main__"
            and plain_runner != "pytest-delegating"
        ):
            raise GrowthTestHoldBypassRefused(_refusal_message(f"{filename}::*"))
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
