from __future__ import annotations

import difflib
import importlib.util
import json
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
CHECKER = REPO / "tools" / "check_silo_validation_isolation.py"
CCBENCH = REPO / "external" / "ccbench"
OPTIONS = CCBENCH / "cmake" / "Options.cmake"
TRANSACTION = CCBENCH / "cc" / "silo" / "transaction.cc"
SILO_OP_ELEMENT = CCBENCH / "cc" / "silo" / "include" / "silo_op_element.hh"
TRANSACTION_HEADER = CCBENCH / "cc" / "silo" / "include" / "transaction.hh"
POSITIVE_PATCH = REPO / "patches" / "silo-backoff-fixed.patch"
NORW_PATCH = REPO / "patches" / "broken-silo-norw-validation.patch"
LOCKSKIP_PATCH = REPO / "patches" / "broken-silo-lockskip-validation.patch"
EARLY_UNLOCK_PATCH = REPO / "patches" / "broken-silo-early-unlock-validation.patch"
ROOT_EDIT_PATCHES = tuple(
    REPO / "patches" / name
    for name in (
        "broken-silo-permutation-erase.patch",
        "broken-silo-permutation-swap.patch",
        "broken-silo-write-intent-erase.patch",
        "broken-silo-write-intent-forge.patch",
        "broken-silo-write-intent-opswap.patch",
        "broken-silo-write-intent-ptrswap.patch",
        "broken-silo-sort-nonswo.patch",
    )
)

NO_INTERSECTION = "NO_STATIC_VALIDATION_CLOSURE_INTERSECTION"
INTERSECTION = "STATIC_VALIDATION_CLOSURE_INTERSECTION"

EXPECTED_CLAIM_BOUNDARY = {
    "analysis_kind": "raw-config-union-static-downward-call-closure",
    "closure_direction": "downward-callees-only",
    "thread_interleavings_proven": False,
    "validation_decision_sequence_proven": False,
    "abort_retry_lifecycle_proven": False,
    "commit_validation_result_consumption_covered": False,
    "write_phase_write_writeback_correctness_covered": False,
    "pure_timing_or_side_effect_freedom_proven": False,
    "other_protocols_covered": False,
    "other_groups_or_unexecuted_schedules_licensed": False,
    "runtime_anomaly_policy": (
        "REJECT_VARIANT_IMMEDIATELY_REGARDLESS_OF_THIS_RESULT"
    ),
    "runtime_anomaly_policy_enforced_by_this_checker": False,
    "external_runtime_anomaly_evidence_required": True,
    "implicit_constructor_destructor_edges_modeled": False,
    "error_policy": "ERROR_IS_NOT_NO_STATIC_VALIDATION_CLOSURE_INTERSECTION",
    "does_not_prove": [
        "thread_interleaving",
        "validation_decision_sequence",
        "abort_retry_lifecycle",
        "commit_validation_result_consumption",
        "write_phase_write_or_writeback_correctness",
        "pure_timing_or_side_effect_freedom",
        "serializability_or_dynamic_anomaly_absence",
        "implicit_constructor_or_destructor_call_edges",
        "other_protocol_correctness",
        "other_group_or_unexecuted_schedule_certification",
    ],
}


def _invoke(patch: Path) -> tuple[int, dict]:
    completed = subprocess.run(
        [sys.executable, str(CHECKER), str(patch)],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert completed.stderr == "", completed.stderr
    lines = completed.stdout.splitlines()
    assert len(lines) == 1, completed.stdout
    payload = json.loads(lines[0])
    assert payload["schema"] == "izanagi.silo-validation-isolation/v1"
    assert payload["owner_tus"] == ["cc/silo/transaction.cc"]
    return completed.returncode, payload


def _temporary_transaction_patch(directory: Path, name: str, updated: str) -> Path:
    original = TRANSACTION.read_text(encoding="utf-8")
    diff = list(difflib.unified_diff(
        original.splitlines(),
        updated.splitlines(),
        fromfile="a/cc/silo/transaction.cc",
        tofile="b/cc/silo/transaction.cc",
        lineterm="",
        # A deliberately broad context also proves that the checker maps the
        # iterator overload uniquely instead of trusting volatile hunk numbers.
        n=12,
    ))
    assert diff and diff[0] == "--- a/cc/silo/transaction.cc"
    patch = directory / name
    patch.write_text(
        "diff --git a/cc/silo/transaction.cc b/cc/silo/transaction.cc\n"
        + "\n".join(diff)
        + "\n",
        encoding="utf-8",
    )
    return patch


def _temporary_ccbench_patch(
    directory: Path, name: str, relative: str, original: str, updated: str,
) -> Path:
    diff = list(difflib.unified_diff(
        original.splitlines(keepends=True),
        updated.splitlines(keepends=True),
        fromfile=f"a/{relative}",
        tofile=f"b/{relative}",
        n=3,
    ))
    assert diff and diff[0] == f"--- a/{relative}\n"
    patch = directory / name
    patch.write_text(
        f"diff --git a/{relative} b/{relative}\n" + "".join(diff),
        encoding="utf-8",
    )
    return patch


def _decoy_patch(directory: Path) -> Path:
    original = TRANSACTION.read_text(encoding="utf-8")
    old = "while (expected.lock) { expected.obj_ = loadAcquire(tuple->tidword_.obj_); }"
    new = "if (expected.lock) { expected.obj_ = loadAcquire(tuple->tidword_.obj_); }"
    assert original.count(old) == 1
    return _temporary_transaction_patch(
        directory, "decoy-read-internal.patch", original.replace(old, new, 1)
    )


def _depth_two_patch(directory: Path) -> Path:
    original = TRANSACTION.read_text(encoding="utf-8")
    start_marker = (
        "void TxExecutor::unlockWriteSet(\n"
        "    std::vector<WriteElement<Tuple>>::iterator end) {"
    )
    end_marker = "\n}\n\nbool TxExecutor::validationPhase()"
    start = original.index(start_marker)
    end = original.index(end_marker, start)
    function = original[start:end]
    assert function.count("desired.lock = 0;") == 1
    updated_function = function.replace("desired.lock = 0;", "desired.lock = false;", 1)
    updated = original[:start] + updated_function + original[end:]
    return _temporary_transaction_patch(directory, "depth-two-unlock.patch", updated)


def _root_and_unconsumed_patch(directory: Path) -> Path:
    original = TRANSACTION.read_text(encoding="utf-8")
    extern_old = "extern void displayDB();"
    extern_new = "extern void displayDB_t2539_decoy();"
    root_start = original.index("bool TxExecutor::validationPhase()")
    root_end = original.index("\n}\n\nvoid TxExecutor::wal", root_start)
    root = original[root_start:root_end]
    assert root.count("  return true;") == 1
    updated_root = root.replace("  return true;", "  return (true);", 1)
    assert original.count(extern_old) == 1
    updated = (
        original[:root_start] + updated_root + original[root_end:]
    ).replace(extern_old, extern_new, 1)
    return _temporary_transaction_patch(
        directory, "root-and-unconsumed.patch", updated,
    )


def _get_tidword_patches(directory: Path) -> tuple[Path, Path, Path]:
    relative = "cc/silo/include/silo_op_element.hh"
    original = SILO_OP_ELEMENT.read_text(encoding="utf-8")
    old = "  Tidword get_tidword() { return tidword_; }\n"
    assert original.count(old) == 1
    default_arg = (
        "  Tidword get_tidword(int = 0) {\n"
        "    Tidword wrong = tidword_;\n"
        "    wrong.tid ^= 1;\n"
        "    return wrong;\n"
        "  }\n"
    )
    body_only = (
        "  Tidword get_tidword() { "
        "Tidword wrong = tidword_; wrong.tid ^= 1; return wrong; }\n"
    )
    required_arg = "  Tidword get_tidword(int selector) { return tidword_; }\n"
    return (
        _temporary_ccbench_patch(
            directory, "get-tidword-default-arg.patch", relative,
            original, original.replace(old, default_arg, 1),
        ),
        _temporary_ccbench_patch(
            directory, "get-tidword-body-only.patch", relative,
            original, original.replace(old, body_only, 1),
        ),
        _temporary_ccbench_patch(
            directory, "get-tidword-required-arg.patch", relative,
            original, original.replace(old, required_arg, 1),
        ),
    )


def _comment_directive_patch(directory: Path) -> Path:
    relative = "cc/silo/include/transaction.hh"
    original = TRANSACTION_HEADER.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    anchors = [index for index, line in enumerate(lines) if "bool validationPhase();" in line]
    assert len(anchors) == 1
    anchor = anchors[0]
    injected = "  /* doc:\n#if TRACE\n  */\n"
    updated = "".join(lines[:anchor]) + injected + "".join(lines[anchor:])
    return _temporary_ccbench_patch(
        directory, "comment-directive.patch", relative, original, updated,
    )


def _trace_default_patch(directory: Path) -> Path:
    relative = "cmake/Options.cmake"
    original = OPTIONS.read_text(encoding="utf-8")
    old = (
        'set(CCBENCH_TRACE         0 CACHE STRING '
        '"izanagi correctness trace (0=off, perf)")\n'
    )
    new = (
        'set(CCBENCH_TRACE         1 CACHE STRING '
        '"izanagi correctness trace (0=off, perf)")\n'
    )
    assert original.count(old) == 1
    return _temporary_ccbench_patch(
        directory, "trace-default.patch", relative,
        original, original.replace(old, new, 1),
    )


def _closure_map(payload: dict) -> dict[str, dict]:
    return {item["symbol"]: item for item in payload["closure"]}


def test_cli_reports_no_intersection_for_registered_backoff_patch() -> None:
    rc, payload = _invoke(POSITIVE_PATCH)
    assert rc == 0
    assert payload["verdict"] == NO_INTERSECTION
    assert payload["intersections"] == []
    assert payload["unconsumed_edits"] == []
    assert len(payload["classified_edits"]) == 6
    assert {item["edit_id"] for item in payload["classified_edits"]} == {
        "E0001", "E0002", "E0003", "E0004", "E0005", "E0006",
    }
    classified_targets = {
        target
        for edit in payload["classified_edits"]
        for target in edit["targets"]
    }
    assert "Backoff::backoff/1" in classified_targets
    assert {item["macro"] for item in payload["cmake_macros"]} == {
        "BACKOFF_FIXED", "BACKOFF_NOINLINE",
    }
    assert all(not item["closure_references"] for item in payload["cmake_macros"])


def test_cli_reports_root_intersection_for_guarded_norw_patch() -> None:
    rc, payload = _invoke(NORW_PATCH)
    assert rc == 1
    assert payload["verdict"] == INTERSECTION
    assert payload["unconsumed_edits"] == []
    assert payload["intersections"]
    assert {item["symbol"] for item in payload["intersections"]} == {
        "TxExecutor::validationPhase/0"
    }
    assert {item["depth"] for item in payload["intersections"]} == {0}


def test_cli_reports_depth_one_intersection_for_guarded_lockskip_patch() -> None:
    rc, payload = _invoke(LOCKSKIP_PATCH)
    assert rc == 1
    assert payload["verdict"] == INTERSECTION
    assert payload["unconsumed_edits"] == []
    assert {item["symbol"] for item in payload["intersections"]} == {
        "TxExecutor::lockWriteSet/0"
    }
    assert {item["depth"] for item in payload["intersections"]} == {1}


def test_known_root_edits_win_over_incomplete_closure_expansion() -> None:
    for patch in ROOT_EDIT_PATCHES:
        rc, payload = _invoke(patch)
        assert rc == 1, patch.name
        assert payload["verdict"] == INTERSECTION, patch.name
        assert payload["closure_expansion_errors"], patch.name
        closure = set(_closure_map(payload))
        function_intersections = [
            item for item in payload["intersections"]
            if item["kind"] == "function-region"
        ]
        assert function_intersections, patch.name
        assert all(item["symbol"] in closure for item in function_intersections)
        assert "TxExecutor::validationPhase/0" in {
            item["symbol"] for item in function_intersections
        }, patch.name


def test_known_root_edit_wins_over_unconsumed_edit() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        patch = _root_and_unconsumed_patch(Path(temporary))
        rc, payload = _invoke(patch)
    assert rc == 1
    assert payload["verdict"] == INTERSECTION
    assert payload["unconsumed_edits"]
    assert "error" not in payload
    assert "TxExecutor::validationPhase/0" in {
        item["symbol"] for item in payload["intersections"]
    }


def test_default_argument_callee_edit_is_not_reported_as_no_intersection() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        default_patch, control_patch, mismatch_patch = _get_tidword_patches(
            Path(temporary),
        )
        default_rc, default_payload = _invoke(default_patch)
        control_rc, control_payload = _invoke(control_patch)
        mismatch_rc, mismatch_payload = _invoke(mismatch_patch)
    assert default_rc == 1
    assert default_payload["verdict"] == INTERSECTION
    assert {
        (item["kind"], item["symbol"], item["depth"])
        for item in default_payload["intersections"]
    } == {("function-region", "ReadElement::get_tidword/1", 1)}
    assert control_rc == 1
    assert control_payload["verdict"] == INTERSECTION
    assert {
        (item["symbol"], item["depth"])
        for item in control_payload["intersections"]
        if item["kind"] == "function-region"
    } == {("ReadElement::get_tidword/0", 1)}
    assert mismatch_rc == 2
    assert mismatch_payload["verdict"] == "ERROR"
    assert mismatch_payload["error"]["code"] == "INCOMPLETE_CLOSURE_EXPANSION"
    assert {
        item["code"] for item in mismatch_payload["closure_expansion_errors"]
    } == {"FIRST_PARTY_ARITY_MISMATCH"}


def test_cmake_trace_default_reports_macro_closure_intersections() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        patch = _trace_default_patch(Path(temporary))
        rc, payload = _invoke(patch)
    assert rc == 1
    assert payload["verdict"] == INTERSECTION
    assert len(payload["cmake_macros"]) == 1
    trace = payload["cmake_macros"][0]
    assert trace["macro"] == "TRACE"
    assert trace["change_kinds"] == ["cache-default"]
    expected = {
        ("TxExecutor::validationPhase/0", 0),
        ("TxExecutor::lockWriteSet/0", 1),
        ("TxExecutor::unlockWriteSet/0", 1),
        ("TxExecutor::unlockWriteSet/1", 2),
    }
    assert len(trace["closure_references"]) == 4
    assert {
        (item["symbol"], item["depth"])
        for item in trace["closure_references"]
    } == expected
    assert len(payload["intersections"]) == 4
    assert {
        (item["kind"], item["macro"], item["symbol"], item["depth"])
        for item in payload["intersections"]
    } == {
        ("macro-reference", "TRACE", symbol, depth)
        for symbol, depth in expected
    }


def test_comment_directive_text_does_not_create_macro_intersection() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        patch = _comment_directive_patch(Path(temporary))
        rc, payload = _invoke(patch)
    assert rc == 2
    assert payload["verdict"] == "ERROR"
    assert payload["error"]["code"] == "UNCONSUMED_EDITS"
    assert payload["intersections"] == []
    assert payload["conditional_macros"] == []
    assert payload["classified_edits"] == []
    assert len(payload["unconsumed_edits"]) == 1


def test_cli_reports_no_intersection_for_same_file_unreachable_decoy() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        patch = _decoy_patch(Path(temporary))
        rc, payload = _invoke(patch)
    assert rc == 0
    assert payload["verdict"] == NO_INTERSECTION
    assert payload["intersections"] == []
    assert payload["unconsumed_edits"] == []
    assert {
        target
        for edit in payload["classified_edits"]
        for target in edit["targets"]
    } == {"TxExecutor::read_internal/3"}


def test_cli_reports_depth_two_intersection_for_iterator_unlock() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        patch = _depth_two_patch(Path(temporary))
        rc, payload = _invoke(patch)
    assert rc == 1
    assert payload["verdict"] == INTERSECTION
    assert payload["unconsumed_edits"] == []
    assert {item["symbol"] for item in payload["intersections"]} == {
        "TxExecutor::unlockWriteSet/1"
    }
    assert {item["depth"] for item in payload["intersections"]} == {2}


def test_real_raw_closure_contains_root_helpers_and_implicit_comparators() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        _, payload = _invoke(_decoy_patch(Path(temporary)))
    closure = _closure_map(payload)
    assert closure["TxExecutor::validationPhase/0"]["depth"] == 0
    assert closure["TxExecutor::lockWriteSet/0"]["depth"] == 1
    assert closure["TxExecutor::unlockWriteSet/1"]["depth"] == 2
    assert closure["WriteElement::operator</1"]["depth"] == 1
    assert closure["WriteElement::operator</1"]["edge_kind"] == "implicit-comparator"
    assert closure["Tidword::operator</1"]["depth"] == 1
    assert closure["Tidword::operator</1"]["edge_kind"] == "implicit-comparator"


def test_real_raw_closure_excludes_callers_postvalidation_and_abort_path() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        _, payload = _invoke(_decoy_patch(Path(temporary)))
    symbols = set(_closure_map(payload))
    assert {
        "TxExecutor::commit/0",
        "TxExecutor::writePhase/0",
        "TxExecutor::abort/0",
        "Backoff::backoff/1",
        "leaderBackoffWork/2",
        "TxExecutor::read_internal/3",
    }.isdisjoint(symbols)


def test_cli_missing_patch_is_error_not_no_intersection() -> None:
    missing = REPO / "patches" / "does-not-exist-t2539.patch"
    rc, payload = _invoke(missing)
    assert rc == 2
    assert payload["verdict"] == "ERROR"
    assert payload["error"]["code"] == "PATCH_UNREADABLE"


def test_cli_unmappable_hunk_is_error_not_no_intersection() -> None:
    patch_text = """diff --git a/cc/silo/transaction.cc b/cc/silo/transaction.cc
--- a/cc/silo/transaction.cc
+++ b/cc/silo/transaction.cc
@@ -1,1 +1,1 @@
-this line is not in the source
+nor is this replacement
"""
    with tempfile.TemporaryDirectory() as temporary:
        patch = Path(temporary) / "unmappable.patch"
        patch.write_text(patch_text, encoding="utf-8")
        rc, payload = _invoke(patch)
    assert rc == 2
    assert payload["verdict"] == "ERROR"
    assert payload["error"]["code"] == "UNMAPPABLE_HUNK"


def test_cli_unconsumed_edit_is_reported_and_errors() -> None:
    original = TRANSACTION.read_text(encoding="utf-8")
    old = "extern void displayDB();"
    new = "extern void displayDB_t2539_decoy();"
    assert original.count(old) == 1
    with tempfile.TemporaryDirectory() as temporary:
        patch = _temporary_transaction_patch(
            Path(temporary), "unconsumed-file-scope.patch",
            original.replace(old, new, 1),
        )
        rc, payload = _invoke(patch)
    assert rc == 2
    assert payload["verdict"] == "ERROR"
    assert payload["error"]["code"] == "UNCONSUMED_EDITS"
    assert payload["unconsumed_edits"]
    assert {
        item["edit_id"] for item in payload["classified_edits"]
    }.isdisjoint(item["edit_id"] for item in payload["unconsumed_edits"])


def _load_checker_module():
    spec = importlib.util.spec_from_file_location(
        "t2539_check_silo_validation_isolation", CHECKER
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_missing_repo_root_is_error_not_empty_closure() -> None:
    checker = _load_checker_module()
    with tempfile.TemporaryDirectory() as temporary:
        payload = checker.analyze(Path(temporary) / "absent-root", POSITIVE_PATCH)
    assert payload["verdict"] == "ERROR"
    assert payload["closure"] == []
    assert payload["error"]["code"] == "CCBENCH_ROOT_UNINITIALIZED"


def test_early_unlock_is_outside_closure_and_claims_no_correctness() -> None:
    rc, payload = _invoke(EARLY_UNLOCK_PATCH)
    assert rc == 0
    assert payload["verdict"] == NO_INTERSECTION
    assert payload["intersections"] == []
    assert payload["unconsumed_edits"] == []
    assert {
        target
        for edit in payload["classified_edits"]
        for target in edit["targets"]
    } == {"TxExecutor::writePhase/0"}
    boundary = payload["claim_boundary"]
    assert boundary["write_phase_write_writeback_correctness_covered"] is False
    assert "serializability_or_dynamic_anomaly_absence" in boundary["does_not_prove"]


def test_claim_boundary_records_every_required_non_guarantee() -> None:
    _, payload = _invoke(POSITIVE_PATCH)
    boundary = payload["claim_boundary"]
    assert set(boundary) == {
        "analysis_kind",
        "closure_direction",
        "thread_interleavings_proven",
        "validation_decision_sequence_proven",
        "abort_retry_lifecycle_proven",
        "commit_validation_result_consumption_covered",
        "write_phase_write_writeback_correctness_covered",
        "pure_timing_or_side_effect_freedom_proven",
        "other_protocols_covered",
        "other_groups_or_unexecuted_schedules_licensed",
        "runtime_anomaly_policy",
        "runtime_anomaly_policy_enforced_by_this_checker",
        "external_runtime_anomaly_evidence_required",
        "implicit_constructor_destructor_edges_modeled",
        "error_policy",
        "does_not_prove",
    }
    assert boundary == EXPECTED_CLAIM_BOUNDARY


def test_claim_boundary_requires_external_runtime_anomaly_evidence() -> None:
    _, payload = _invoke(POSITIVE_PATCH)
    boundary = payload["claim_boundary"]
    assert boundary["runtime_anomaly_policy_enforced_by_this_checker"] is False
    assert boundary["external_runtime_anomaly_evidence_required"] is True


def test_claim_boundary_records_unmodeled_implicit_lifetime_edges() -> None:
    _, payload = _invoke(POSITIVE_PATCH)
    boundary = payload["claim_boundary"]
    assert boundary["implicit_constructor_destructor_edges_modeled"] is False
    assert "implicit_constructor_or_destructor_call_edges" in boundary["does_not_prove"]


TESTS = (
    test_cli_reports_no_intersection_for_registered_backoff_patch,
    test_cli_reports_root_intersection_for_guarded_norw_patch,
    test_cli_reports_depth_one_intersection_for_guarded_lockskip_patch,
    test_known_root_edits_win_over_incomplete_closure_expansion,
    test_known_root_edit_wins_over_unconsumed_edit,
    test_default_argument_callee_edit_is_not_reported_as_no_intersection,
    test_cmake_trace_default_reports_macro_closure_intersections,
    test_comment_directive_text_does_not_create_macro_intersection,
    test_cli_reports_no_intersection_for_same_file_unreachable_decoy,
    test_cli_reports_depth_two_intersection_for_iterator_unlock,
    test_real_raw_closure_contains_root_helpers_and_implicit_comparators,
    test_real_raw_closure_excludes_callers_postvalidation_and_abort_path,
    test_cli_missing_patch_is_error_not_no_intersection,
    test_cli_unmappable_hunk_is_error_not_no_intersection,
    test_cli_unconsumed_edit_is_reported_and_errors,
    test_missing_repo_root_is_error_not_empty_closure,
    test_early_unlock_is_outside_closure_and_claims_no_correctness,
    test_claim_boundary_records_every_required_non_guarantee,
    test_claim_boundary_requires_external_runtime_anomaly_evidence,
    test_claim_boundary_records_unmodeled_implicit_lifetime_edges,
)


def _run() -> int:
    if not TESTS:
        print("ERROR: zero tests registered", file=sys.stderr)
        return 1
    failures = 0
    for test in TESTS:
        try:
            test()
        except Exception:
            failures += 1
            print(f"FAIL {test.__name__}", file=sys.stderr)
            traceback.print_exc()
        else:
            print(f"ok {test.__name__}")
    print(f"ran {len(TESTS)} tests; failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run())
