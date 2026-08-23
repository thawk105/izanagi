# -*- coding: utf-8 -*-
"""依存物不在と条件付き未実走の skip 分類がドリフトしないことを検査する。"""
from __future__ import annotations

import ast
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from skiputil import CONDITIONAL_UNRUN, Skip, skip_conditional_unrun  # noqa: E402


_CONDITIONAL_NODES = {
    "test_campaign.py": (
        "test_source_digest_parse_options_defaults",
        "test_source_digest_fixed_variant_distinct",
        "test_source_digest_failsclosed_on_missing_define",
    ),
    "test_hooks.py": ("test_real_submodule_payload_edit",),
}
_CONDITIONAL_NODEIDS = tuple(
    f"orchestrator/tests/{filename}::{function}"
    for filename, functions in _CONDITIONAL_NODES.items()
    for function in functions
)


def _function_node(filename: str, function_name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    tree = ast.parse((HERE / filename).read_text(encoding="utf-8"), filename=filename)
    matches = [node for node in tree.body
               if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
               and node.name == function_name]
    assert len(matches) == 1, f"対象 node が一意でない: {filename}::{function_name}"
    return matches[0]


def _calls_in_function(filename: str, function_name: str) -> set[str]:
    function = _function_node(filename, function_name)
    return {
        node.func.id
        for node in ast.walk(function)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }


def _call_leaf_names_for_real_silo_meta(function: ast.AST) -> set[str]:
    return {
        node.func.id if isinstance(node.func, ast.Name) else node.func.attr
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Name, ast.Attribute))
    }


def test_conditional_unrun_nodes_use_classified_helper():
    for filename, functions in _CONDITIONAL_NODES.items():
        for function_name in functions:
            calls = _calls_in_function(filename, function_name)
            assert "skip_conditional_unrun" in calls, (
                f"条件付き未実走 helper の結線が無い: {filename}::{function_name}"
            )


def test_dependency_absence_skip_stays_unclassified():
    calls = _calls_in_function("test_campaign.py", "test_source_digest_stock_roundtrip")
    assert "skip" in calls, "依存物不在の正例が素の skip を呼んでいない"
    assert "skip_conditional_unrun" not in calls, (
        "条件付き未実走の分類を依存物不在 skip へ広げている"
    )


def test_conditional_unrun_reason_has_classification_reason_and_pointer():
    saved = os.environ.pop("PYTEST_CURRENT_TEST", None)
    try:
        try:
            skip_conditional_unrun("X")
            assert False, "skip_conditional_unrun は Skip を送出すべき"
        except Skip as exc:
            reason = str(exc)
    finally:
        if saved is not None:
            os.environ["PYTEST_CURRENT_TEST"] = saved

    assert reason.startswith(CONDITIONAL_UNRUN)
    assert "X" in reason
    assert "orchestrator/tests/README.md" in reason


def test_readme_conditional_unrun_census_names_all_nodes():
    source = (HERE / "README.md").read_text(encoding="utf-8")
    heading = re.search(r"^(#{1,6})[^\n]*条件付き未実走[^\n]*$", source, re.MULTILINE)
    assert heading, "README.md に『条件付き未実走』を含む見出しの節が無い"
    level = len(heading.group(1))
    following = source[heading.end():]
    next_heading = re.search(rf"^#{{1,{level}}}\s", following, re.MULTILINE)
    section = following[:next_heading.start()] if next_heading else following
    for nodeid in _CONDITIONAL_NODEIDS:
        assert nodeid in section, f"条件付き未実走の節に nodeid が無い: {nodeid}"


def test_real_silo_node_always_verifies_tracked_fixture_without_skip():
    function = _function_node("test_verifier.py", "test_real_silo_serializable")
    calls = _call_leaf_names_for_real_silo_meta(function)
    assert calls.isdisjoint({"skip", "skip_conditional_unrun"}), (
        "tracked 実 Silo fixture の node が skip helper を呼んでいる"
    )
    assert not any(isinstance(node, ast.Return) for node in ast.walk(function)), (
        "tracked 実 Silo fixture の検査を return で迂回している"
    )

    mandatory_calls = []
    for statement in function.body:
        if not isinstance(statement, ast.Assign) or not isinstance(statement.value, ast.Call):
            continue
        call = statement.value
        if not isinstance(call.func, ast.Name) or call.func.id != "_assert_certified_serializable":
            continue
        if call.args and isinstance(call.args[0], ast.Name):
            mandatory_calls.append(call)
    assert len(mandatory_calls) == 1, (
        "tracked fixture の無条件な certified/serializable 検証呼び出しが一意でない"
    )
    call = mandatory_calls[0]
    assert call.args[0].id == "REAL_SILO_FIXTURE"
    expected_commits = [
        keyword.value for keyword in call.keywords
        if keyword.arg == "expected_commits"
    ]
    assert len(expected_commits) == 1
    assert ast.literal_eval(expected_commits[0]) == 1345


def _run() -> int:
    passed = failed = skipped = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"PASS {name}")
            passed += 1
        except Skip as exc:
            print(f"SKIP {name}: {exc}")
            skipped += 1
        except AssertionError as exc:
            print(f"FAIL {name}: {exc}")
            failed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR {name}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
