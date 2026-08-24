# -*- coding: utf-8 -*-
"""依存物不在と条件付き未実走の skip 分類がドリフトしないことを検査する。"""
from __future__ import annotations

import ast
import os
import re
import sys
import types
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
_CONDITIONAL_PREPROCESS_NODES = {
    "test_campaign.py": (
        "test_source_digest_fixed_variant_distinct",
        "test_source_digest_failsclosed_on_missing_define",
    ),
}
_SELECTED_CXX_CONSUMERS = {
    ("test_campaign.py", "test_source_digest_stock_roundtrip"): {
        "source_digest.src_token": 1,
    },
    ("test_campaign.py", "test_source_digest_fixed_variant_distinct"): {
        "source_digest.src_token": 1,
        "buildcache.cache_key": 2,
    },
    ("test_campaign.py", "test_source_digest_failsclosed_on_missing_define"): {
        "source_digest._cpp_normalize": 2,
    },
    ("test_campaign.py", "test_source_digest_semantic_comment_vs_behavior"): {
        "source_digest._cpp_normalize": 3,
    },
    ("test_campaign.py", "test_source_digest_builtin_ifdef_not_aliased_to_stock"): {
        "source_digest.resolve": 2,
        "source_digest.compute": 1,
        "source_digest.baseline": 1,
        "buildcache.cache_key": 2,
    },
    ("test_campaign.py", "test_source_digest_include_change_rejected_by_resolve"): {
        "source_digest.resolve": 4,
        "source_digest.assert_includes_match_head": 1,
    },
    ("test_campaign.py", "test_trace_diff_of_diffs_predicate"): {
        "source_digest.assert_trace_diff_matches_head": 3,
    },
    ("test_campaign.py", "test_trace_diff_of_diffs_allows_stock_hook_catches_inner_edit"): {
        "source_digest.assert_trace_diff_matches_head": 3,
    },
    ("test_s1_direct_comparison.py",
     "test_real_source_digest_unifies_all_outer_whitespace_tokens"): {
        "S.source_digest.resolve": 2,
    },
}


def _function_node(filename: str, function_name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    tree = ast.parse((HERE / filename).read_text(encoding="utf-8"), filename=filename)
    matches = [node for node in tree.body
               if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
               and node.name == function_name]
    assert len(matches) == 1, f"対象 node が一意でない: {filename}::{function_name}"
    return matches[0]


class _ExecutionScopeNodes(ast.NodeVisitor):
    """Collect nodes executed by the target function without nested scopes."""

    def __init__(self):
        self.nodes = []

    def generic_visit(self, node):
        self.nodes.append(node)
        super().generic_visit(node)

    def visit_FunctionDef(self, node):
        return None

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_Lambda = visit_FunctionDef
    visit_ClassDef = visit_FunctionDef


def _nodes_in_execution_scope(function: ast.AST) -> list[ast.AST]:
    visitor = _ExecutionScopeNodes()
    for statement in function.body:
        visitor.visit(statement)
    return visitor.nodes


def _qualified_name(expression: ast.AST) -> str | None:
    parts = []
    while isinstance(expression, ast.Attribute):
        parts.append(expression.attr)
        expression = expression.value
    if not isinstance(expression, ast.Name):
        return None
    parts.append(expression.id)
    return ".".join(reversed(parts))


def _calls_in_execution_scope(function: ast.AST) -> list[ast.Call]:
    return [
        node for node in _nodes_in_execution_scope(function)
        if isinstance(node, ast.Call)
    ]


def _calls_in_function(filename: str, function_name: str) -> set[str]:
    function = _function_node(filename, function_name)
    return {
        name for node in _calls_in_execution_scope(function)
        if (name := _qualified_name(node.func)) is not None
    }


def _call_leaf_names_for_real_silo_meta(function: ast.AST) -> set[str]:
    return {
        name.rsplit(".", 1)[-1]
        for node in _calls_in_execution_scope(function)
        if (name := _qualified_name(node.func)) is not None
    }


def _calls_named(function: ast.AST, names: set[str]) -> list[ast.Call]:
    return [
        node for node in _calls_in_execution_scope(function)
        if _qualified_name(node.func) in names
    ]


def _selected_cxx_assignment(function: ast.AST) -> tuple[str, ast.Call]:
    matches = []
    for node in _nodes_in_execution_scope(function):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or not isinstance(node.value, ast.Call):
            continue
        if _qualified_name(node.value.func) == "_any_cxx":
            matches.append((target.id, node.value))
    assert len(matches) == 1, "対象 node は _any_cxx() の選択値を一度だけ束縛すべき"
    return matches[0]


def _cxx_argument(call: ast.Call) -> ast.AST | None:
    keywords = [keyword.value for keyword in call.keywords if keyword.arg == "cxx"]
    assert len(keywords) <= 1, "cxx keyword が重複している"
    if keywords:
        return keywords[0]
    return None


class _HelperSkip(Exception):
    pass


def _compiled_any_cxx(filename: str, which):
    function = _function_node(filename, "_any_cxx")

    def raise_skip(reason):
        raise _HelperSkip(reason)

    namespace = {
        "shutil": types.SimpleNamespace(which=which),
        "skip": raise_skip,
        "pytest": types.SimpleNamespace(skip=raise_skip),
    }
    module = ast.Module(body=[function], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), filename, "exec"), namespace)
    return namespace["_any_cxx"], function


def test_conditional_preprocess_nodes_classify_before_compiler_selection():
    for filename, functions in _CONDITIONAL_NODES.items():
        for function_name in functions:
            calls = _calls_in_function(filename, function_name)
            assert "skip_conditional_unrun" in calls, (
                f"条件付き未実走 helper の結線が無い: {filename}::{function_name}"
            )
    for filename, functions in _CONDITIONAL_PREPROCESS_NODES.items():
        for function_name in functions:
            function = _function_node(filename, function_name)
            selected_name, selection = _selected_cxx_assignment(function)
            assert selected_name == "cxx"
            conditional_calls = _calls_named(function, {"skip_conditional_unrun"})
            assert len(conditional_calls) == 1
            consumer_names = set(
                _SELECTED_CXX_CONSUMERS[(filename, function_name)]
            )
            consumers = _calls_named(function, consumer_names)
            assert consumers
            assert conditional_calls[0].lineno < selection.lineno, (
                "conditional skip より先に compiler を選んでいる: "
                f"{filename}::{function_name}"
            )
            assert selection.lineno < min(call.lineno for call in consumers), (
                "compiler 選択より先に preprocess consumer が走りうる: "
                f"{filename}::{function_name}"
            )


def test_site_compiler_helpers_choose_first_available_and_skip_only_when_empty():
    filenames = ("test_campaign.py", "test_s1_direct_comparison.py")
    cases = (
        ("g++-13", "g++-13", ["g++-13"]),
        ("g++-12", "g++-12", ["g++-13", "g++-12"]),
        ("g++", "g++", ["g++-13", "g++-12", "g++"]),
        (None, None, ["g++-13", "g++-12", "g++"]),
    )
    for filename in filenames:
        function = _function_node(filename, "_any_cxx")
        docstring = ast.get_docstring(function) or ""
        assert "compiler 版をまたぐ関係は保証しない" in docstring, filename
        for available, expected, expected_calls in cases:
            calls = []

            def which(candidate):
                calls.append(candidate)
                return (
                    f"/fixture/{candidate}"
                    if candidate == available else None
                )

            helper, _ = _compiled_any_cxx(filename, which)
            if expected is None:
                try:
                    helper()
                    assert False, f"全候補不在なら skip すべき: {filename}"
                except _HelperSkip as exc:
                    assert "全滅" in str(exc), filename
            else:
                assert helper() == expected, (filename, available)
            assert calls == expected_calls, (filename, available)


def test_selected_cxx_is_bound_to_every_target_consumer():
    matcher_fixture = ast.parse(
        "def target():\n"
        "    source_digest.resolve(genome, head, cxx=cxx)\n"
        "    other.resolve(genome, head, cxx=cxx)\n"
        "    def nested():\n"
        "        source_digest.resolve(genome, head, cxx=cxx)\n"
        "    decoy = lambda: source_digest.resolve(genome, head, cxx=cxx)\n"
    ).body[0]
    assert len(_calls_named(
        matcher_fixture, {"source_digest.resolve"},
    )) == 1

    assert len(_SELECTED_CXX_CONSUMERS) == 9
    for (filename, function_name), expected_counts in _SELECTED_CXX_CONSUMERS.items():
        function = _function_node(filename, function_name)
        selected_name, selection = _selected_cxx_assignment(function)
        consumer_names = set(expected_counts)
        consumers = _calls_named(function, consumer_names)
        actual_counts = {
            name: sum(
                _qualified_name(call.func) == name for call in consumers
            )
            for name in consumer_names
        }
        assert actual_counts == expected_counts, (
            f"compiler consumer census が変わった: {filename}::{function_name}: "
            f"{actual_counts!r} != {expected_counts!r}"
        )
        assert selection.lineno < min(call.lineno for call in consumers)
        for call in consumers:
            qualified = _qualified_name(call.func)
            bound = _cxx_argument(call)
            assert isinstance(bound, ast.Name) and bound.id == selected_name, (
                "選択 compiler が consumer の cxx 引数へ届いていない: "
                f"{filename}::{function_name}:{call.lineno} {qualified}"
            )
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
    contracts = (
        (
            "test_real_silo_serializable",
            "_assert_certified_serializable",
            "REAL_SILO_FIXTURE",
            "res",
            1345,
        ),
        (
            "test_silo_serial_1thread_fixture_contract",
            "verify_trace_dir",
            "SILO_SERIAL_1THREAD_FIXTURE",
            "res",
            200,
        ),
        (
            "test_broken_silo_norw_fixture_contract",
            "verify_trace_dir",
            "BROKEN_SILO_NORW_FIXTURE",
            "res",
            288,
        ),
    )
    for (
        function_name, verifier_name, fixture_name, result_name, commit_count,
    ) in contracts:
        function = _function_node("test_verifier.py", function_name)
        calls = _call_leaf_names_for_real_silo_meta(function)
        assert calls.isdisjoint({"skip", "skip_conditional_unrun"}), (
            f"tracked 実 Silo fixture の node が skip helper を呼んでいる: {function_name}"
        )
        assert not any(isinstance(node, ast.Return) for node in ast.walk(function)), (
            f"tracked 実 Silo fixture の検査を return で迂回している: {function_name}"
        )

        direct_assignments = [
            statement for statement in function.body
            if (
                isinstance(statement, ast.Assign)
                and isinstance(statement.value, ast.Call)
                and isinstance(statement.value.func, ast.Name)
                and statement.value.func.id == verifier_name
                and statement.value.args
                and isinstance(statement.value.args[0], ast.Name)
            )
        ]
        assert len(direct_assignments) == 1, (
            "node 直下の検証 assignment 全体が一意でない: "
            f"{function_name}::{verifier_name}"
        )
        assignment = direct_assignments[0]
        call = direct_assignments[0].value
        assert call.args and isinstance(call.args[0], ast.Name)
        assert call.args[0].id == fixture_name
        assert (
            len(assignment.targets) == 1
            and isinstance(assignment.targets[0], ast.Name)
            and assignment.targets[0].id == result_name
        ), (
            "検証結果が後続 golden の参照名へ直接束縛されていない: "
            f"{function_name}::{result_name}"
        )
        result_stores = [
            node for node in ast.walk(function)
            if (
                isinstance(node, ast.Name)
                and node.id == result_name
                and isinstance(node.ctx, ast.Store)
            )
        ]
        assert (
            len(result_stores) == 1
            and result_stores[0] is assignment.targets[0]
        ), (
            "検証結果の束縛名が同じ node 内で再束縛されている: "
            f"{function_name}::{result_name}"
        )
        following = function.body[function.body.index(assignment) + 1:]
        assert any(
            isinstance(node, ast.Name)
            and node.id == result_name
            and isinstance(node.ctx, ast.Load)
            for statement in following
            for node in ast.walk(statement)
        ), (
            "検証結果の束縛名を後続 golden が参照していない: "
            f"{function_name}::{result_name}"
        )
        expected_commits = [
            keyword.value for keyword in call.keywords
            if keyword.arg == "expected_commits"
        ]
        assert len(expected_commits) == 1
        assert ast.literal_eval(expected_commits[0]) == commit_count


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
