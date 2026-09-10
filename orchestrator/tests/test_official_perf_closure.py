"""Closure checks for official no-perf measurement authority.

The reviewed ledger is intentionally literal.  The assertions below derive the
other side from production ASTs (and from the existing certified-writer caller
inventory), so changing either a reviewed predicate or its caller set requires
an explicit review of this file.
"""

from __future__ import annotations

import ast
import collections
import sys
from dataclasses import dataclass
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[2]
_CAMPAIGN_TEST = _REPO_ROOT / "orchestrator/tests/test_campaign.py"
_T126_SCRIPT = _REPO_ROOT / "tools/pegasus/t126_qualification.sh"
_PRODUCTION_ROOTS = ("orchestrator", "tools")
_PRODUCTION_SUFFIXES = frozenset({".py", ".sh"})
_NON_PRODUCTION_PARTS = frozenset({
    "tests", "external", "output", "__pycache__",
})

_TRACKED_CALLS = frozenset({
    "build_perf_observation",
    "build_portable_run_cmd",
    "evaluate",
    "evaluate_fn",
    "load_measurement_manifest",
    "manifest_keys_for_mode",
    "perf_claim_allowed",
    "probe_perf_availability",
    "result_keys_for_mode",
    "use_perf_from_receipt",
    "validate_manifest_v3",
    "validate_perf_observation",
    "validate_perf_preflight_receipt",
    "write_measurement_manifest",
})
_PERF_DISCOVERY_CALLS = _TRACKED_CALLS - {"evaluate", "evaluate_fn"}
_REVIEWED_PERF_FILES = frozenset({
    "orchestrator/calibrator/perf_preflight.py",
    "orchestrator/calibrator/runner.py",
    "orchestrator/campaign/autonomous_trial_completeness.py",
    "orchestrator/campaign/b10_backoff_shape_sweep.py",
    # Invokes the certified campaign pipeline, which may launch perf after preflight.
    "orchestrator/campaign/backoff_extended_sweep.py",
    # Consumes producer-recorded perf observations for verdicts; it never launches perf.
    "orchestrator/campaign/backoff_extended_sweep_report.py",
    "orchestrator/campaign/floor_pair_driver.py",
    "orchestrator/campaign/layer3_report.py",
    "orchestrator/campaign/loop.py",
    # Parses producer-recorded perf-wrapped argv as exploratory trace evidence.
    "orchestrator/campaign/paper_story_a1_paired.py",
    # Parses producer-recorded perf-wrapped argv as evidence; it never launches perf.
    "orchestrator/campaign/paper_story_a2_certification.py",
    "orchestrator/campaign/pipeline.py",
    "orchestrator/campaign/profiler_directive.py",
    "orchestrator/campaign/s1_direct_comparison.py",
    # Derives perf from the receipt and checks capture kwargs; capture_measure_point owns launch.
    "orchestrator/campaign/s8b_floor_attempt_launcher.py",
    "orchestrator/campaign/s8b_floor_campaign.py",
    "orchestrator/campaign/s8b_floor_contract.py",
    "orchestrator/campaign/s8b_floor_stats.py",
    "orchestrator/campaign/s8b_holdout_freeze.py",
    "orchestrator/campaign/s8b_oracle_artifacts.py",
    "orchestrator/campaign/s8b_oracle_driver.py",
    "orchestrator/campaign/s8b_oracle_judge.py",
    "orchestrator/campaign/s8b_oracle_n_pilot.py",
    "orchestrator/campaign/s8b_oracle_report.py",
    "orchestrator/campaign/s8b_ratified_freeze.py",
    "orchestrator/campaign/s8b_verdict.py",
    "orchestrator/campaign/screening_driver.py",
    "orchestrator/campaign/silo_ladder_rung1.py",
    # Consumes producer-recorded trace-disabled performance-build evidence only.
    "orchestrator/campaign/t1998_stock_inline_pair.py",
    "orchestrator/holdout_observation.py",
    "orchestrator/qualification/artifacts.py",
    "orchestrator/qualification/contract.py",
    "orchestrator/qualification/submission.py",
    "orchestrator/qualification/t126_driver.py",
    "tools/pegasus/a5_second_boot_backoff_sweep.sh",
    "tools/pegasus/b10_backoff_shape_campaign.sh",
    "tools/pegasus/certify_calibration.sh",
    "tools/pegasus/floor_scoping.sh",
    "tools/pegasus/probes/t293_perf_site_probe.py",
    "tools/pegasus/probes/t316_sandbox_backend_probe.py",
    "tools/pegasus/submit_b10_backoff_shape.sh",
    "tools/pegasus/t126_qualification.sh",
    "tools/pegasus/t141_region_profile.sh",
    # Parses producer-recorded perf-wrapped argv as measurement evidence; it never launches perf.
    "tools/plotting/plot_s1_9pair.py",
})


@dataclass(frozen=True)
class _Predicate:
    surface: str
    path: str
    function: str
    call: str
    count: int = 1


# Ruling section 5, at production predicate granularity.  A repeated call in a
# function is represented by count, not hidden by a set.
_REVIEWED_PREDICATES = (
    _Predicate("shared", "orchestrator/calibrator/perf_preflight.py",
               "probe_perf_availability", "validate_perf_preflight_receipt"),
    _Predicate("shared", "orchestrator/calibrator/perf_preflight.py",
               "use_perf_from_receipt", "validate_perf_preflight_receipt"),
    _Predicate("shared", "orchestrator/calibrator/perf_preflight.py",
               "build_perf_observation", "validate_perf_preflight_receipt"),
    _Predicate("shared", "orchestrator/calibrator/perf_preflight.py",
               "build_perf_observation", "use_perf_from_receipt"),
    _Predicate("shared", "orchestrator/calibrator/perf_preflight.py",
               "build_perf_observation", "validate_perf_observation"),
    _Predicate("shared", "orchestrator/calibrator/perf_preflight.py",
               "validate_perf_observation", "validate_perf_preflight_receipt"),
    _Predicate("shared", "orchestrator/calibrator/perf_preflight.py",
               "validate_perf_observation", "use_perf_from_receipt"),
    _Predicate("shared", "orchestrator/calibrator/perf_preflight.py",
               "perf_claim_allowed", "validate_perf_observation"),

    _Predicate("R", "orchestrator/campaign/backoff_extended_sweep.py",
               "_materialize_preflight_stop", "validate_perf_preflight_receipt"),
    _Predicate("R", "orchestrator/campaign/loop.py",
               "_perform_perf_preflight", "validate_perf_preflight_receipt"),
    _Predicate("R", "orchestrator/campaign/loop.py",
               "_perform_perf_preflight", "use_perf_from_receipt"),
    _Predicate("R", "orchestrator/campaign/loop.py",
               "run_campaign", "evaluate"),
    _Predicate("P", "orchestrator/campaign/screening_driver.py",
               "evaluate_candidate", "probe_perf_availability"),
    _Predicate("P", "orchestrator/campaign/screening_driver.py",
               "evaluate_candidate", "use_perf_from_receipt"),
    _Predicate("P", "orchestrator/campaign/screening_driver.py",
               "evaluate_candidate", "evaluate"),
    _Predicate("P", "orchestrator/campaign/s1_direct_comparison.py",
               "run_role", "probe_perf_availability"),
    _Predicate("P", "orchestrator/campaign/s1_direct_comparison.py",
               "run_role", "use_perf_from_receipt"),
    _Predicate("P", "orchestrator/campaign/s1_direct_comparison.py",
               "run_role", "evaluate_fn"),
    _Predicate("P", "orchestrator/campaign/s1_direct_comparison.py",
               "run_role", "evaluate"),

    _Predicate("I", "orchestrator/campaign/s8b_oracle_driver.py",
               "run_block", "probe_perf_availability"),
    _Predicate("I", "orchestrator/campaign/s8b_oracle_driver.py",
               "run_block", "use_perf_from_receipt"),
    _Predicate("I", "orchestrator/campaign/s8b_oracle_driver.py",
               "run_block", "build_perf_observation"),
    _Predicate("I", "orchestrator/campaign/s8b_oracle_driver.py",
               "run_block", "write_measurement_manifest"),
    _Predicate("I", "orchestrator/campaign/s8b_oracle_driver.py",
               "run_block", "evaluate_fn"),
    _Predicate("I", "orchestrator/campaign/s8b_oracle_driver.py",
               "run_block", "evaluate"),
    _Predicate("T967", "orchestrator/campaign/s8b_oracle_artifacts.py",
               "_validate_measurement_manifest", "validate_perf_observation"),
    _Predicate("T967", "orchestrator/campaign/s8b_oracle_report.py",
               "_measurement_condition_for_campaign", "load_measurement_manifest", 2),
    _Predicate("T967", "orchestrator/campaign/s8b_oracle_report.py",
               "_assess_window", "perf_claim_allowed"),
    _Predicate("T967", "orchestrator/campaign/s8b_oracle_judge.py",
               "_measurement_conditions", "perf_claim_allowed"),
    _Predicate("T967", "orchestrator/campaign/s8b_oracle_judge.py",
               "_measurement_conditions", "validate_perf_observation"),
    _Predicate("T967", "orchestrator/campaign/s8b_verdict.py",
               "_combined_measurement_conditions", "perf_claim_allowed"),
    _Predicate("T967", "orchestrator/campaign/s8b_verdict.py",
               "_combined_measurement_conditions", "validate_perf_observation", 3),

    _Predicate("A", "orchestrator/campaign/s8b_floor_campaign.py",
               "_normalize_perf_preflight", "validate_perf_preflight_receipt"),
    _Predicate("A", "orchestrator/campaign/s8b_floor_campaign.py",
               "_normalize_perf_preflight", "use_perf_from_receipt"),
    _Predicate("A", "orchestrator/campaign/s8b_floor_campaign.py",
               "_project_probed_perf_preflight", "use_perf_from_receipt"),
    _Predicate("A", "orchestrator/campaign/s8b_floor_campaign.py",
               "_assert_perf_mode", "use_perf_from_receipt"),
    _Predicate("A", "orchestrator/campaign/s8b_floor_attempt_launcher.py",
               "_checked_reservation_policy", "use_perf_from_receipt"),
    _Predicate("J", "orchestrator/campaign/s8b_floor_campaign.py",
               "assemble_manifest", "build_perf_observation"),
    _Predicate("A", "orchestrator/campaign/s8b_floor_campaign.py",
               "_project_measure_run_cmd", "build_portable_run_cmd"),
    _Predicate("O", "orchestrator/campaign/s8b_floor_campaign.py",
               "assemble_result", "build_perf_observation"),
    _Predicate("A", "orchestrator/campaign/s8b_floor_campaign.py",
               "_load_resume_manifest", "validate_manifest_v3"),
    _Predicate("B", "orchestrator/campaign/s8b_floor_contract.py",
               "_official_perf_evidence_keys", "use_perf_from_receipt"),
    _Predicate("B", "orchestrator/campaign/s8b_floor_contract.py",
               "_validate_resume_diagnostic_events", "validate_perf_preflight_receipt", 2),
    _Predicate("B", "orchestrator/campaign/s8b_floor_contract.py",
               "validate_manifest_v3", "manifest_keys_for_mode"),
    _Predicate("B", "orchestrator/campaign/s8b_floor_contract.py",
               "validate_manifest_v3", "validate_perf_observation"),
    _Predicate("K", "orchestrator/campaign/s8b_floor_stats.py",
               "validate_floor_perf_evidence", "validate_perf_observation", 3),
    _Predicate("K", "orchestrator/campaign/s8b_floor_stats.py",
               "validate_floor_perf_evidence", "perf_claim_allowed"),
    _Predicate("K", "orchestrator/campaign/s8b_floor_stats.py",
               "verify_floor_artifact", "use_perf_from_receipt"),
    _Predicate("K", "orchestrator/campaign/s8b_floor_stats.py",
               "verify_floor_artifact", "result_keys_for_mode"),
    _Predicate("D", "orchestrator/campaign/s8b_holdout_freeze.py",
               "_validate_floor_inputs", "use_perf_from_receipt"),
    _Predicate("D", "orchestrator/campaign/s8b_holdout_freeze.py",
               "_validate_floor_inputs", "result_keys_for_mode"),
    _Predicate("D", "orchestrator/campaign/s8b_holdout_freeze.py",
               "_validate_floor_inputs", "validate_manifest_v3"),
    _Predicate("E", "orchestrator/campaign/s8b_ratified_freeze.py",
               "_validate_manifest", "use_perf_from_receipt"),
    _Predicate("E", "orchestrator/campaign/s8b_ratified_freeze.py",
               "_validate_manifest", "manifest_keys_for_mode"),
    _Predicate("E", "orchestrator/campaign/s8b_ratified_freeze.py",
               "_validate_manifest", "validate_manifest_v3"),
    _Predicate("E", "orchestrator/campaign/s8b_ratified_freeze.py",
               "_validate_result_top_level_keys", "use_perf_from_receipt"),
    _Predicate("E", "orchestrator/campaign/s8b_ratified_freeze.py",
               "_validate_journal", "validate_perf_preflight_receipt"),
    _Predicate("L", "orchestrator/campaign/s8b_ratified_freeze.py",
               "_validate_result_top_level_keys", "result_keys_for_mode"),
    _Predicate("L", "orchestrator/campaign/s8b_ratified_freeze.py",
               "_run_cmd_matches_portable_session", "build_portable_run_cmd"),

    _Predicate("C", "orchestrator/campaign/pipeline.py",
               "_run_bench", "build_perf_observation"),
    _Predicate("C", "orchestrator/campaign/pipeline.py",
               "_run_balanced_schedule", "build_perf_observation"),
    _Predicate("C", "orchestrator/campaign/pipeline.py",
               "evaluate", "validate_perf_preflight_receipt"),
    _Predicate("C", "orchestrator/campaign/pipeline.py",
               "evaluate", "use_perf_from_receipt"),
    _Predicate("S", "orchestrator/campaign/layer3_report.py",
               "_validate_schema", "validate_perf_observation"),
    _Predicate("H", "orchestrator/qualification/submission.py",
               "prepare_toolchain", "probe_perf_availability"),
    _Predicate("H", "orchestrator/qualification/submission.py",
               "prepare_toolchain", "use_perf_from_receipt"),
    _Predicate("M", "orchestrator/qualification/contract.py",
               "series_identity", "use_perf_from_receipt"),
    _Predicate("G", "orchestrator/qualification/t126_driver.py",
               "ForkedMemberRunner.__call__", "evaluate"),
    _Predicate("G", "orchestrator/qualification/t126_driver.py",
               "_verify_prologue_evidence", "validate_perf_observation"),
    _Predicate("G", "orchestrator/qualification/artifacts.py",
               "validate_member_evidence", "validate_perf_observation"),
    _Predicate("G", "orchestrator/qualification/artifacts.py",
               "validate_member_evidence", "perf_claim_allowed"),
)


@dataclass(frozen=True)
class _GuardSpec:
    surface: str
    path: str
    function: str
    terms: tuple[str, ...]
    conditions: tuple[str, ...]


# Calls alone are insufficient: deleting the condition around a still-live
# canonical call must also be visible.  These are normalized with ast.unparse,
# so whitespace and line movement do not cause drift.
_REVIEWED_GUARDS = (
    _GuardSpec(
        "shared", "orchestrator/calibrator/perf_preflight.py",
        "build_perf_observation", ("receipt", "use_perf", "leading_indicators"),
        (
            "receipt is None",
            "not isinstance(leading_indicators, Mapping)",
            "not use_perf",
        ),
    ),
    _GuardSpec(
        "shared", "orchestrator/calibrator/perf_preflight.py",
        "validate_perf_observation",
        ("use_perf", "claim_scope", "leading_indicators"),
        (
            "type(use_perf) is not bool",
            "use_perf is not derived_use_perf",
            "use_perf",
            "observation.get('claim_scope') != _CLAIM_SCOPE",
            "not isinstance(leading_indicators, Mapping)",
            "name not in leading_indicators",
            "leading_indicators[name] is not None",
            "not use_perf",
        ),
    ),
    _GuardSpec(
        "A", "orchestrator/campaign/s8b_floor_campaign.py", "_assert_perf_mode",
        ("use_perf",),
        ("mode != 'pilot' and receipt is not None and use_perf",),
    ),
    _GuardSpec(
        "A", "orchestrator/campaign/s8b_floor_attempt_launcher.py",
        "_checked_reservation_policy", ("expected_use_perf", "capture_use_perf"),
        (
            "reservation.mode == 'official' and "
            "reservation.perf_preflight_receipt is not None and "
            "expected_use_perf",
            "type(capture_use_perf) is not bool or "
            "capture_use_perf is not expected_use_perf",
        ),
    ),
    _GuardSpec(
        "B", "orchestrator/campaign/s8b_floor_contract.py",
        "_official_perf_evidence_keys", ("receipt", "use_perf"),
        ("receipt is not None and use_perf", "receipt is None"),
    ),
    _GuardSpec(
        "C", "orchestrator/campaign/pipeline.py", "evaluate",
        ("use_perf", "perf_preflight_receipt"),
        (
            "type(use_perf) is not bool",
            "perf_preflight_receipt is None",
            "not use_perf",
            "use_perf is not expected_use_perf",
        ),
    ),
    _GuardSpec(
        "D", "orchestrator/campaign/s8b_holdout_freeze.py",
        "_validate_floor_inputs",
        ("expected_use_perf", "result_perf_preflight", "perf_observation"),
        (
            "not expected_use_perf",
            "normalized_observation['preflight'] != result_perf_preflight",
            "result.get('perf_preflight') != manifest_document.get('perf_preflight') "
            "or result.get('perf_observation') != "
            "manifest_document.get('perf_observation')",
        ),
    ),
    _GuardSpec(
        "I", "orchestrator/campaign/s8b_oracle_driver.py", "run_block",
        ("use_perf",), ("not use_perf",),
    ),
    _GuardSpec(
        "J", "orchestrator/campaign/s8b_floor_campaign.py", "assemble_manifest",
        ("use_perf", "normalized_perf"),
        (
            "mode != 'pilot' and normalized_perf is not None and use_perf",
            "normalized_perf is not None",
            "mode != 'pilot' and (not use_perf)",
        ),
    ),
    _GuardSpec(
        "K", "orchestrator/campaign/s8b_floor_stats.py", "verify_floor_artifact",
        ("expected_use_perf", "derived_use_perf", "normalized_observation"),
        (
            "type(expected_use_perf) is not bool",
            "expected_use_perf is not derived_use_perf",
            "artifact.get('mode') == 'official' and (not derived_use_perf)",
            "normalized_observation['preflight'] != receipt",
        ),
    ),
    _GuardSpec(
        "L", "orchestrator/campaign/s8b_ratified_freeze.py",
        "_validate_result_top_level_keys",
        ("derived_use_perf", "expected_perf_preflight", "expected_perf_observation"),
        (
            "derived_use_perf is not expected_use_perf",
            "receipt != expected_perf_preflight",
            "observation != expected_perf_observation",
        ),
    ),
    _GuardSpec(
        "M", "orchestrator/qualification/contract.py", "series_identity",
        ("receipt", "use_perf"),
        (
            "receipt is not None and use_perf",
            "not use_perf",
            "use_perf",
        ),
    ),
    _GuardSpec(
        "O", "orchestrator/campaign/s8b_floor_campaign.py", "assemble_result",
        ("use_perf",), ("mode != 'pilot' and (not use_perf)",),
    ),
    _GuardSpec(
        "P", "orchestrator/campaign/screening_driver.py", "evaluate_candidate",
        ("use_perf",), ("not use_perf",),
    ),
    _GuardSpec(
        "P", "orchestrator/campaign/s1_direct_comparison.py", "run_role",
        ("use_perf",), ("not use_perf",),
    ),
    _GuardSpec(
        "G", "orchestrator/qualification/t126_driver.py",
        "_member_pipeline_perf_kwargs", ("perf_observation", "use_perf"),
        (
            "perf_observation is None",
            "perf_observation.get('use_perf') is not False",
        ),
    ),
    _GuardSpec(
        "G", "orchestrator/qualification/t126_driver.py",
        "_verify_prologue_evidence", ("perf_observation", "use_perf"),
        (
            "key_set not in (required, common_required | {'perf_observation'})",
            "observation['use_perf'] is not False",
        ),
    ),
    _GuardSpec(
        "H", "orchestrator/qualification/submission.py", "prepare_toolchain",
        ("use_perf",), ("use_perf", "not use_perf"),
    ),
    _GuardSpec(
        "T967", "orchestrator/campaign/s8b_oracle_artifacts.py",
        "_validate_measurement_manifest", ("use_perf",),
        ("observation['use_perf'] is not False",),
    ),
    _GuardSpec(
        "T967", "orchestrator/campaign/s8b_oracle_judge.py",
        "_measurement_conditions", ("use_perf",),
        ("canonical['use_perf'] is not False",),
    ),
    _GuardSpec(
        "T967", "orchestrator/campaign/s8b_verdict.py",
        "_combined_measurement_conditions", ("perf_preflight",),
        ("floor_observation.get('preflight') != floor_source.get('perf_preflight')",),
    ),
)

_ADDED_REVIEWED_GUARDS = (
    _GuardSpec(
        "T967", "orchestrator/campaign/s8b_oracle_report.py",
        "_assess_window", ("observation", "expected_perf_observation"),
        (
            "observation != expected_perf_observation",
            "observation is not None",
        ),
    ),
    _GuardSpec(
        "runner", "orchestrator/calibrator/runner.py", "_build_cmd",
        ("use_perf",), ("use_perf",),
    ),
    _GuardSpec(
        "runner", "orchestrator/calibrator/runner.py", "measure_point",
        ("use_perf",), ("not use_perf",),
    ),
)


class _CallScanner(ast.NodeVisitor):
    def __init__(self, rel_path: str):
        self.rel_path = rel_path
        self.scope: list[str] = []
        self.calls: collections.Counter[tuple[str, str, str]] = collections.Counter()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute):
            name = node.func.attr
        elif isinstance(node.func, ast.Name):
            name = node.func.id
        else:
            name = None
        if name in _TRACKED_CALLS:
            function = ".".join(self.scope) if self.scope else "<module>"
            self.calls[(self.rel_path, function, name)] += 1
        self.generic_visit(node)


def _scan_source(rel_path: str, source: str) -> collections.Counter:
    scanner = _CallScanner(rel_path)
    scanner.visit(ast.parse(source, filename=rel_path))
    return scanner.calls


def _is_perf_name(name: str) -> bool:
    lowered = name.lower()
    return (lowered in {"perf", "use_perf", "perf_preflight"}
            or lowered.startswith("perf_")
            or lowered.endswith("_perf")
            or "_perf_" in lowered)


def _python_has_perf_predicate(rel_path: str, source: str) -> bool:
    if ("perf" not in source.lower()
            and not any(call in source for call in _PERF_DISCOVERY_CALLS)):
        return False
    tree = ast.parse(source, filename=rel_path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
            elif isinstance(node.func, ast.Name):
                call_name = node.func.id
            else:
                call_name = None
            if call_name in _PERF_DISCOVERY_CALLS:
                return True
        if not isinstance(node, (ast.If, ast.IfExp, ast.While)):
            continue
        for term in ast.walk(node.test):
            if isinstance(term, ast.Name) and _is_perf_name(term.id):
                return True
            if isinstance(term, ast.Attribute) and _is_perf_name(term.attr):
                return True
    return False


def _shell_has_perf_predicate(source: str) -> bool:
    for raw_line in source.splitlines():
        line = raw_line.strip().lower()
        if "perf" not in line:
            continue
        if (line.startswith(("if ", "elif ", "while ", "case "))
                or "[[" in line or "&&" in line or "||" in line
                or "perf_preflight." in line):
            return True
    return False


def _production_perf_files(overrides: dict[str, str] | None = None) -> set[str]:
    overrides = overrides or {}
    paths = {
        path.relative_to(_REPO_ROOT).as_posix()
        for root in _PRODUCTION_ROOTS
        for path in (_REPO_ROOT / root).rglob("*")
        if path.is_file()
        and path.suffix in _PRODUCTION_SUFFIXES
        and not (_NON_PRODUCTION_PARTS & set(path.relative_to(_REPO_ROOT).parts))
    }
    paths.update(
        rel_path for rel_path in overrides
        if Path(rel_path).suffix in _PRODUCTION_SUFFIXES
        and not (_NON_PRODUCTION_PARTS & set(Path(rel_path).parts))
        and Path(rel_path).parts
        and Path(rel_path).parts[0] in _PRODUCTION_ROOTS
    )
    found = set()
    for rel_path in sorted(paths):
        source = overrides.get(rel_path)
        if source is None:
            source = (_REPO_ROOT / rel_path).read_text(encoding="utf-8")
        if rel_path.endswith(".py"):
            if _python_has_perf_predicate(rel_path, source):
                found.add(rel_path)
        elif _shell_has_perf_predicate(source):
            found.add(rel_path)
    return found


def _perf_file_drift(actual: set[str]) -> str:
    rows = [f"unreviewed: {path}" for path in sorted(actual - _REVIEWED_PERF_FILES)]
    rows.extend(
        f"missing: {path}" for path in sorted(_REVIEWED_PERF_FILES - actual)
    )
    return "\n".join(rows)


def _expected_predicates() -> collections.Counter:
    return collections.Counter({
        (item.path, item.function, item.call): item.count
        for item in _REVIEWED_PREDICATES
    })


def _production_predicates(
        overrides: dict[str, str] | None = None) -> collections.Counter:
    overrides = overrides or {}
    actual: collections.Counter = collections.Counter()
    for rel_path in sorted({item.path for item in _REVIEWED_PREDICATES}):
        source = overrides.get(rel_path)
        if source is None:
            source = (_REPO_ROOT / rel_path).read_text(encoding="utf-8")
        actual.update(_scan_source(rel_path, source))
    return actual


def _drift(actual: collections.Counter, expected: collections.Counter) -> str:
    added = actual - expected
    removed = expected - actual
    rows = []
    for label, difference in (("unreviewed", added), ("missing", removed)):
        rows.extend(
            f"{label}: {path}:{function}:{call} x{count}"
            for (path, function, call), count in sorted(difference.items())
        )
    return "\n".join(rows)


def _extract_existing_evaluate_inventory() -> collections.Counter:
    tree = ast.parse(_CAMPAIGN_TEST.read_text(encoding="utf-8"))
    target = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "test_certified_writer_authorization_caller_inventory_is_closed"
    )
    assignments = [
        node for node in ast.walk(target)
        if isinstance(node, ast.Assign)
        and any(isinstance(item, ast.Name) and item.id == "expected_inventory"
                for item in node.targets)
    ]
    assert len(assignments) == 1, "certified-writer expected_inventory must remain unique"
    constructor = assignments[0].value
    assert (isinstance(constructor, ast.Call) and constructor.args
            and isinstance(constructor.args[0], ast.Dict))
    inventory = collections.Counter(ast.literal_eval(constructor.args[0]))
    return collections.Counter({
        (path, target_name): count
        for (path, target_name), count in inventory.items()
        if target_name == "campaign.pipeline.evaluate"
    })


@dataclass(frozen=True)
class _BenchAuthority:
    caller_function: str
    evaluate_call: str
    canonical_calls: tuple[tuple[str, str], ...]
    supply_function: str
    authority_edges: tuple[tuple[str, str], ...] = ()


_BENCH_AUTHORITIES = {
    "orchestrator/campaign/loop.py": _BenchAuthority(
        "run_campaign", "evaluate",
        (("_perform_perf_preflight", "use_perf_from_receipt"),),
        "run_campaign", (("run_campaign", "_perform_perf_preflight"),),
    ),
    "orchestrator/campaign/screening_driver.py": _BenchAuthority(
        "evaluate_candidate", "evaluate",
        (("evaluate_candidate", "use_perf_from_receipt"),),
        "evaluate_candidate",
    ),
    "orchestrator/campaign/s1_direct_comparison.py": _BenchAuthority(
        "run_role", "evaluate_fn",
        (("run_role", "use_perf_from_receipt"),), "run_role",
    ),
    "orchestrator/campaign/s8b_oracle_driver.py": _BenchAuthority(
        "run_block", "evaluate_fn",
        (("run_block", "use_perf_from_receipt"),), "run_block",
    ),
    "orchestrator/qualification/t126_driver.py": _BenchAuthority(
        "ForkedMemberRunner.__call__", "evaluate",
        (("_verify_prologue_evidence", "validate_perf_observation"),),
        "_member_pipeline_perf_kwargs",
        (("ForkedMemberRunner.__call__", "_member_pipeline_perf_kwargs"),),
    ),
}


def _function_nodes(source: str) -> dict[str, ast.FunctionDef]:
    tree = ast.parse(source)
    found: dict[str, ast.FunctionDef] = {}

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.scope: list[str] = []

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self.scope.append(node.name)
            self.generic_visit(node)
            self.scope.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self.scope.append(node.name)
            found[".".join(self.scope)] = node
            self.generic_visit(node)
            self.scope.pop()

    Visitor().visit(tree)
    return found


def _call_names(node: ast.AST) -> collections.Counter[str]:
    names: collections.Counter[str] = collections.Counter()
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        if isinstance(child.func, ast.Attribute):
            names[child.func.attr] += 1
        elif isinstance(child.func, ast.Name):
            names[child.func.id] += 1
    return names


def _string_constants(node: ast.AST) -> set[str]:
    return {
        child.value for child in ast.walk(node)
        if isinstance(child, ast.Constant) and isinstance(child.value, str)
    }


def _expected_guards(
        specs: tuple[_GuardSpec, ...] = _REVIEWED_GUARDS,
) -> collections.Counter:
    expected: collections.Counter = collections.Counter()
    for spec in specs:
        expected.update(
            (spec.path, spec.function, condition)
            for condition in spec.conditions
        )
    return expected


def _production_guards(
        overrides: dict[str, str] | None = None, *,
        specs: tuple[_GuardSpec, ...] = _REVIEWED_GUARDS,
) -> collections.Counter:
    overrides = overrides or {}
    sources: dict[str, str] = {}
    functions_by_path: dict[str, dict[str, ast.FunctionDef]] = {}
    actual: collections.Counter = collections.Counter()
    for spec in specs:
        if spec.path not in sources:
            sources[spec.path] = overrides.get(
                spec.path,
                (_REPO_ROOT / spec.path).read_text(encoding="utf-8"),
            )
            functions_by_path[spec.path] = _function_nodes(sources[spec.path])
        function = functions_by_path[spec.path].get(spec.function)
        if function is None:
            actual[(spec.path, spec.function, "<function-missing>")] += 1
            continue
        for node in ast.walk(function):
            if not isinstance(node, ast.If):
                continue
            condition = ast.unparse(node.test)
            if any(term in condition for term in spec.terms):
                actual[(spec.path, spec.function, condition)] += 1
    return actual


def test_bench_callers_are_exact_and_own_canonical_preflight() -> None:
    authoritative = _extract_existing_evaluate_inventory()
    expected = collections.Counter({
        (path, "campaign.pipeline.evaluate"): 1
        for path in _BENCH_AUTHORITIES
    })
    assert authoritative == expected, (
        "test_campaign.py の exact evaluate inventory と authority 台帳が不一致\n"
        + _drift(
            collections.Counter({
                (path, "<caller>", target): count
                for (path, target), count in authoritative.items()
            }),
            collections.Counter({
                (path, "<caller>", target): count
                for (path, target), count in expected.items()
            }),
        )
    )

    failures = []
    for rel_path, authority in _BENCH_AUTHORITIES.items():
        functions = _function_nodes(
            (_REPO_ROOT / rel_path).read_text(encoding="utf-8")
        )
        caller = functions.get(authority.caller_function)
        if caller is None:
            failures.append(f"{rel_path}: caller {authority.caller_function} missing")
            continue
        evaluate_count = _call_names(caller)[authority.evaluate_call]
        if evaluate_count != 1:
            failures.append(
                f"{rel_path}:{authority.caller_function}: "
                f"{authority.evaluate_call} count={evaluate_count}, expected=1"
            )
        for function, call in authority.canonical_calls + authority.authority_edges:
            node = functions.get(function)
            count = 0 if node is None else _call_names(node)[call]
            if count != 1:
                failures.append(
                    f"{rel_path}:{function}: {call} count={count}, expected=1"
                )
        supply = functions.get(authority.supply_function)
        strings = set() if supply is None else _string_constants(supply)
        missing = {"use_perf", "perf_preflight_receipt"} - strings
        if missing:
            failures.append(
                f"{rel_path}:{authority.supply_function}: "
                f"evaluate authority pair missing {sorted(missing)}"
            )
    assert not failures, "\n".join(failures)


def test_balanced_schedule_uses_lock_free_blocks_under_one_outer_lock() -> None:
    """The balanced executor must not re-enter legacy `_run_bench`'s flock."""
    functions = _function_nodes(
        (_REPO_ROOT / "orchestrator/campaign/pipeline.py").read_text(
            encoding="utf-8"
        )
    )
    balanced = functions["_run_balanced_schedule"]
    calls = _call_names(balanced)
    assert calls["bench_lock"] == 1
    assert calls["measure_point"] == 1
    assert calls["_run_bench"] == 0
    assert calls["build_perf_observation"] == 1


def test_campaign_loop_has_distinct_legacy_and_balanced_split_calls() -> None:
    functions = _function_nodes(
        (_REPO_ROOT / "orchestrator/campaign/loop.py").read_text(encoding="utf-8")
    )
    calls = _call_names(functions["run_campaign"])
    assert calls["evaluate"] == 1
    assert calls["_prepare_evaluation"] == 1
    assert calls["_run_balanced_schedule"] == 1


def test_official_perf_surface_inventory_is_exact() -> None:
    reviewed_surfaces = {item.surface for item in _REVIEWED_PREDICATES}
    reviewed_surfaces.update(item.surface for item in _REVIEWED_GUARDS)
    reviewed_surfaces.update({"F", "N", "R"})
    assert reviewed_surfaces == {
        "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L",
        "M", "N", "O", "P", "R", "S", "T967", "shared",
    }

    expected = _expected_predicates()
    actual = _production_predicates()
    assert actual == expected, _drift(actual, expected)
    expected_guards = _expected_guards()
    actual_guards = _production_guards()
    assert actual_guards == expected_guards, _drift(
        actual_guards, expected_guards,
    )

    shell = _T126_SCRIPT.read_text(encoding="utf-8")
    shell_markers = {
        "perf_preflight.probe_perf_availability(": 1,
        "perf_preflight.use_perf_from_receipt(": 4,
        "perf_preflight.build_perf_observation(": 1,
        'if [[ -n "$PERF_REAL" ]]; then': 1,
        'if compute_use_perf and "perf" not in d["executables"]:': 1,
        'if compute_use_perf: actual["perf"]=perf': 1,
    }
    marker_drift = {
        marker: (shell.count(marker), count)
        for marker, count in shell_markers.items()
        if shell.count(marker) != count
    }
    assert not marker_drift, f"F/N shell predicate inventory drift: {marker_drift}"
    assert '[[ -n "$PERF_REAL" ]] ||' not in shell

    own_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    own_tests = {
        node.name for node in own_tree.body if isinstance(node, ast.FunctionDef)
    }
    assert "test_official_perf_surface_inventory_is_exact" in own_tests


def test_closure_inventory_mutations_are_not_tautologies() -> None:
    """Prove the derivation turns one deletion and two additions red."""
    expected = _expected_predicates()
    expected_guards = _expected_guards()
    rel_path = "orchestrator/campaign/s8b_floor_contract.py"
    source = (_REPO_ROOT / rel_path).read_text(encoding="utf-8")
    guard = "if receipt is not None and use_perf:"
    assert source.count(guard) == 1

    deleted = source.replace(guard, "if False:", 1)
    deleted_actual = _production_guards({rel_path: deleted})
    assert "missing:" in _drift(deleted_actual, expected_guards)

    insertion = "    if receipt is None:\n"
    assert source.count(insertion) == 1
    added_predicate = source.replace(
        insertion,
        "    if use_perf:\n        pass\n" + insertion,
        1,
    )
    added_actual = _production_guards({rel_path: added_predicate})
    assert "unreviewed:" in _drift(added_actual, expected_guards)

    caller_path = "orchestrator/campaign/screening_driver.py"
    caller_source = (_REPO_ROOT / caller_path).read_text(encoding="utf-8")
    added_caller = caller_source + "\nevaluate(None)\n"
    caller_actual = _production_predicates({caller_path: added_caller})
    assert "unreviewed:" in _drift(caller_actual, expected)

    authoritative = _extract_existing_evaluate_inventory()
    authoritative[("orchestrator/campaign/unreviewed.py",
                   "campaign.pipeline.evaluate")] = 1
    reviewed = collections.Counter({
        (path, "campaign.pipeline.evaluate"): 1
        for path in _BENCH_AUTHORITIES
    })
    assert authoritative != reviewed


def test_outer_perf_file_and_added_guard_inventory_is_exact() -> None:
    actual_perf_files = _production_perf_files()
    assert actual_perf_files == _REVIEWED_PERF_FILES, _perf_file_drift(
        actual_perf_files,
    )
    expected_guards = _expected_guards(_ADDED_REVIEWED_GUARDS)
    actual_guards = _production_guards(specs=_ADDED_REVIEWED_GUARDS)
    assert actual_guards == expected_guards, _drift(actual_guards, expected_guards)


def test_outer_perf_file_mutations_are_not_tautologies() -> None:
    """New production files and erased registered surfaces must turn red."""

    unreviewed_path = "orchestrator/campaign/unreviewed.py"
    with_unreviewed = _production_perf_files({
        unreviewed_path: "def added():\n    probe_perf_availability()\n",
    })
    assert f"unreviewed: {unreviewed_path}" in _perf_file_drift(with_unreviewed)

    runner_path = "orchestrator/calibrator/runner.py"
    without_runner = _production_perf_files({runner_path: ""})
    assert f"missing: {runner_path}" in _perf_file_drift(without_runner)

    pilot_path = "orchestrator/campaign/s8b_oracle_n_pilot.py"
    without_pilot = _production_perf_files({pilot_path: ""})
    assert f"missing: {pilot_path}" in _perf_file_drift(without_pilot)


def _run() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {test.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
