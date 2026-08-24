"""Fold-gate node registry の drift contract と実 bytes positive control。"""
from __future__ import annotations

import ast
import inspect
import shutil
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from orchestrator.tests import fold_gate_nodes as REGISTRY
from orchestrator.tests import test_spool_fold as SPOOL_TESTS
from orchestrator.tests.fold_gate_nodes import (
    D781_EXCLUSION_REASON,
    FOLD_GATE_FAMILY_MINIMUMS,
    FOLD_GATE_NODE_REGISTRY,
    FOLD_GATE_NODE_REGISTRY_SHA256,
    FOLD_GATE_SELECTED_NODES,
    FOLD_GATE_UNCOVERED_FAMILY_ALLOWLIST,
    TARGET_FAMILIES,
    FoldGateNode,
    _validate_family_minimums,
    _validate_node_rows,
    _validate_uncovered_family_allowlist,
    fold_gate_family_population,
    fold_gate_family_shortfalls,
    fold_gate_node_registry_sha256,
)
from orchestrator.tests.growth_test_holds import GROWTH_TEST_HOLDS


SPOOL_TEST_PATH = ROOT / "orchestrator/tests/test_spool_fold.py"
_COPY_HELPER = "_copy_real_canonical_family"
_EXPECTED_NODE_COUNT = 5
_EXPECTED_REGISTRY_SHA256 = (
    "cf69d81c65cb79d415c590ce116f06742e18c9bf8a5996e21d21f8c97c434752"
)


class _CallGraphAnalysisError(ValueError):
    pass


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    return {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }


def _derived_real_canonical_reader_tests(source: str) -> frozenset[str]:
    """Local function/method call graph で copy helper へ到達する test を導出する。"""
    tree = ast.parse(source, filename="test_spool_fold.py")
    definitions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    local_classes: set[str] = set()
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if statement.name in definitions:
                raise _CallGraphAnalysisError(
                    f"duplicate top-level function: {statement.name}"
                )
            definitions[statement.name] = statement
        elif isinstance(statement, ast.ClassDef):
            if statement.name in local_classes:
                raise _CallGraphAnalysisError(
                    f"duplicate top-level class: {statement.name}"
                )
            local_classes.add(statement.name)
            for member in statement.body:
                if not isinstance(
                    member, (ast.FunctionDef, ast.AsyncFunctionDef)
                ):
                    continue
                qualified = f"{statement.name}.{member.name}"
                if qualified in definitions:
                    raise _CallGraphAnalysisError(
                        f"duplicate qualified method: {qualified}"
                    )
                definitions[qualified] = member
    if _COPY_HELPER not in definitions:
        raise _CallGraphAnalysisError(f"missing {_COPY_HELPER}")

    parents = _parent_map(tree)
    edges = {name: set() for name in definitions}
    dynamic_references: list[tuple[str, str, int]] = []
    dynamic_calls: list[tuple[str, int, str]] = []
    owner_by_node: dict[ast.AST, str] = {}
    for name, definition in definitions.items():
        for node in ast.walk(definition):
            owner_by_node.setdefault(node, name)

    for node in ast.walk(tree):
        owner = owner_by_node.get(node, "<module>")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                callee = node.func.id
                if callee in definitions:
                    if owner != "<module>":
                        edges[owner].add(callee)
                if callee in {"getattr", "eval", "exec"}:
                    dynamic_calls.append((owner, node.lineno, callee))
            elif isinstance(node.func, ast.Attribute):
                base = node.func.value
                qualified: str | None = None
                if isinstance(base, ast.Name) and base.id in local_classes:
                    qualified = f"{base.id}.{node.func.attr}"
                elif (
                    isinstance(base, ast.Name)
                    and base.id in {"self", "cls"}
                    and "." in owner
                ):
                    qualified = f"{owner.split('.', 1)[0]}.{node.func.attr}"
                if qualified is not None:
                    if qualified not in definitions:
                        dynamic_calls.append(
                            (owner, node.lineno, f"unresolved-attribute:{qualified}")
                        )
                    elif owner != "<module>":
                        edges[owner].add(qualified)
            elif isinstance(node.func, ast.Subscript):
                dynamic_calls.append((owner, node.lineno, "subscript-call"))
            elif isinstance(node.func, ast.Call):
                dynamic_calls.append((owner, node.lineno, "call-result"))
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Call):
            called = node.value.func
            if isinstance(called, ast.Name) and called.id in {"globals", "locals"}:
                dynamic_calls.append((owner, node.lineno, f"{called.id}-lookup"))
        if not isinstance(node, ast.Name) or not isinstance(node.ctx, ast.Load):
            if (
                isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Store)
                and node.id in definitions
            ):
                dynamic_references.append((owner, node.id, node.lineno))
            elif isinstance(node, ast.arg) and node.arg in definitions:
                dynamic_references.append((owner, node.arg, node.lineno))
            continue
        if node.id in definitions:
            parent = parents.get(node)
            if not (isinstance(parent, ast.Call) and parent.func is node):
                dynamic_references.append((owner, node.id, node.lineno))

    reaches_copy = {_COPY_HELPER}
    changed = True
    while changed:
        changed = False
        for caller, callees in edges.items():
            if caller not in reaches_copy and callees & reaches_copy:
                reaches_copy.add(caller)
                changed = True

    unresolved = [
        (owner, referenced, line)
        for owner, referenced, line in dynamic_references
        if referenced in reaches_copy
    ]
    if unresolved:
        raise _CallGraphAnalysisError(
            f"dynamic reference reaches {_COPY_HELPER}: {unresolved!r}"
        )
    if dynamic_calls:
        raise _CallGraphAnalysisError(
            f"dynamic call form is not statically traceable: {dynamic_calls!r}"
        )
    return frozenset(
        f"test_spool_fold.py::{name}"
        for name in reaches_copy
        if name.startswith("test_")
    )


def _call_name(node: ast.expr) -> str | None:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    parts.append(current.id)
    return ".".join(reversed(parts))


def _forbidden_launcher_calls(
    source: str,
    roots: frozenset[str],
    *,
    filename: str,
) -> tuple[tuple[str, int, str], ...]:
    """Execution roots から到達する pytest/acceptance 再起動だけを返す。"""
    tree = ast.parse(source, filename=filename)
    definitions = {
        statement.name: statement
        for statement in tree.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    edges = {name: set() for name in definitions}
    for owner, definition in definitions.items():
        for call in (
            node for node in ast.walk(definition) if isinstance(node, ast.Call)
        ):
            if isinstance(call.func, ast.Name) and call.func.id in definitions:
                edges[owner].add(call.func.id)
    reachable = set(roots & definitions.keys())
    changed = True
    while changed:
        changed = False
        for owner in tuple(reachable):
            added = edges[owner] - reachable
            if added:
                reachable.update(added)
                changed = True

    launch_calls = {
        "os.execl",
        "os.execle",
        "os.execlp",
        "os.execlpe",
        "os.execv",
        "os.execve",
        "os.execvp",
        "os.execvpe",
        "subprocess.call",
        "subprocess.check_call",
        "subprocess.check_output",
        "subprocess.Popen",
        "subprocess.run",
    }
    banned_payloads = (
        "tools/run_tests.py",
        "tools/acceptance_launcher.py",
        "tools/dev_wave_wait.py",
    )
    findings: list[tuple[str, int, str]] = []
    for owner in sorted(reachable):
        for call in (
            node
            for node in ast.walk(definitions[owner])
            if isinstance(node, ast.Call)
        ):
            called = _call_name(call.func)
            if called == "pytest.main":
                findings.append((owner, call.lineno, called))
                continue
            if called not in launch_calls:
                continue
            literals = tuple(
                child.value
                for child in ast.walk(call)
                if isinstance(child, ast.Constant)
                and isinstance(child.value, str)
            )
            if "pytest" in literals or any(
                banned in literal
                for banned in banned_payloads
                for literal in literals
            ):
                findings.append((owner, call.lineno, called))
    return tuple(findings)


def _row(**changes) -> FoldGateNode:
    return replace(
        FoldGateNode(
            target_family=("worklog",),
            reason="実 canonical の意味を検査する。",
        ),
        **changes,
    )


def _assert_uncovered_allowlist_exact(
    observed_uncovered: frozenset[str],
    allowlisted: frozenset[str],
) -> None:
    assert observed_uncovered - allowlisted == frozenset()
    assert allowlisted - observed_uncovered == frozenset()


def test_registry_count_digest_and_family_minimums_are_frozen() -> None:
    assert len(FOLD_GATE_NODE_REGISTRY) == _EXPECTED_NODE_COUNT
    assert FOLD_GATE_NODE_REGISTRY_SHA256 == _EXPECTED_REGISTRY_SHA256
    assert fold_gate_node_registry_sha256() == _EXPECTED_REGISTRY_SHA256
    assert tuple(FOLD_GATE_FAMILY_MINIMUMS) == TARGET_FAMILIES
    assert dict(FOLD_GATE_FAMILY_MINIMUMS) == {
        family: 1 for family in TARGET_FAMILIES
    }
    assert dict(FOLD_GATE_UNCOVERED_FAMILY_ALLOWLIST).keys() == {
        "decisions",
        "phase3",
        "rotation",
    }
    changed_allowlist = dict(FOLD_GATE_UNCOVERED_FAMILY_ALLOWLIST)
    changed_allowlist["decisions"] += " drift"
    assert fold_gate_node_registry_sha256(
        uncovered_allowlist=changed_allowlist
    ) != _EXPECTED_REGISTRY_SHA256


_REGISTRY_SCHEMA_NEGATIVE_CASES = (
    ("test_spool_fold.py:test_name", _row()),
    ("test_other.py::test_name", _row()),
    ("test_spool_fold.py::test_name", _row(target_family=())),
    (
        "test_spool_fold.py::test_name",
        _row(target_family=("worklog", "worklog")),
    ),
    (
        "test_spool_fold.py::test_name",
        _row(target_family=("unknown",)),
    ),
    ("test_spool_fold.py::test_name", _row(reason=" ")),
    ("test_spool_fold.py::test_name", _row(reason="一\n二\n三")),
    (
        "test_spool_fold.py::test_name",
        _row(exclusion_reason=D781_EXCLUSION_REASON),
    ),
)


@pytest.mark.parametrize(
    ("node_id", "row"),
    _REGISTRY_SCHEMA_NEGATIVE_CASES,
)
def test_registry_schema_negative_controls_are_rejected(node_id, row) -> None:
    with pytest.raises(ValueError):
        _validate_node_rows(((node_id, row),))


test_registry_schema_negative_controls_are_rejected._plain_cases = (
    _REGISTRY_SCHEMA_NEGATIVE_CASES
)


def test_registry_rejects_empty_duplicate_and_wrong_row_types() -> None:
    with pytest.raises(ValueError):
        _validate_node_rows(())
    row = ("test_spool_fold.py::test_name", _row())
    with pytest.raises(ValueError):
        _validate_node_rows((row, row))
    with pytest.raises(ValueError):
        _validate_node_rows(((row[0], object()),))


def test_family_minimum_schema_negative_controls_are_rejected() -> None:
    valid = {family: 1 for family in TARGET_FAMILIES}
    invalid_documents = (
        {},
        {**valid, "unknown": 1},
        {family: value for family, value in valid.items() if family != "rotation"},
        {**valid, "rotation": 0},
        {**valid, "rotation": True},
    )
    for document in invalid_documents:
        with pytest.raises(ValueError):
            _validate_family_minimums(document)


def test_uncovered_allowlist_schema_and_immutability_are_fail_closed() -> None:
    valid = dict(FOLD_GATE_UNCOVERED_FAMILY_ALLOWLIST)
    assert all(reason.strip() for reason in valid.values())
    with pytest.raises(TypeError):
        FOLD_GATE_UNCOVERED_FAMILY_ALLOWLIST["worklog"] = "forged"
    for document in (
        [],
        {"unknown": "理由"},
        {"decisions": " "},
        {"decisions": "一\n二\n三"},
    ):
        with pytest.raises(ValueError):
            _validate_uncovered_family_allowlist(document)


def test_growth_held_rows_require_exact_d781_exclusion(monkeypatch) -> None:
    node_id = "test_spool_fold.py::test_name"
    monkeypatch.setattr(REGISTRY, "GROWTH_TEST_HOLDS", {node_id: object()})
    with pytest.raises(ValueError, match="exact D781 exclusion"):
        _validate_node_rows(((node_id, _row()),))
    accepted = _validate_node_rows((
        (node_id, _row(exclusion_reason=D781_EXCLUSION_REASON)),
    ))
    assert accepted[node_id].exclusion_reason == D781_EXCLUSION_REASON


def test_ast_derived_reader_set_matches_registry_in_both_directions() -> None:
    derived = _derived_real_canonical_reader_tests(
        SPOOL_TEST_PATH.read_text(encoding="utf-8")
    )
    registered = frozenset(FOLD_GATE_NODE_REGISTRY)
    assert derived - registered == frozenset()
    assert registered - derived == frozenset()


def test_call_graph_follows_helpers_and_rejects_dynamic_target_routes() -> None:
    indirect = """
def _copy_real_canonical_family(path):
    return path
def helper(path):
    return _copy_real_canonical_family(path)
def test_reader(path):
    return helper(path)
"""
    assert _derived_real_canonical_reader_tests(indirect) == frozenset({
        "test_spool_fold.py::test_reader"
    })

    alias = indirect.replace(
        "return helper(path)",
        "reader = helper\n    return reader(path)",
    )
    with pytest.raises(_CallGraphAnalysisError, match="dynamic reference"):
        _derived_real_canonical_reader_tests(alias)

    dynamic = """
def _copy_real_canonical_family(path):
    return path
def test_reader(path):
    return getattr(object(), '_copy_real_canonical_family')(path)
"""
    with pytest.raises(_CallGraphAnalysisError, match="dynamic call form"):
        _derived_real_canonical_reader_tests(dynamic)

    staticmethod_route = """
def _copy_real_canonical_family(path):
    return path
class Helper:
    @staticmethod
    def copy(path):
        return _copy_real_canonical_family(path)
def test_reader(path):
    return Helper.copy(path)
"""
    assert _derived_real_canonical_reader_tests(
        staticmethod_route
    ) == frozenset({"test_spool_fold.py::test_reader"})

    unresolved_attribute = staticmethod_route.replace(
        "Helper.copy(path)", "Helper.unknown(path)"
    )
    with pytest.raises(
        _CallGraphAnalysisError,
        match="unresolved-attribute:Helper.unknown",
    ):
        _derived_real_canonical_reader_tests(unresolved_attribute)


def test_growth_hold_join_and_selected_registry_are_exact() -> None:
    held = frozenset(FOLD_GATE_NODE_REGISTRY) & frozenset(GROWTH_TEST_HOLDS)
    excluded = frozenset(
        node_id
        for node_id, row in FOLD_GATE_NODE_REGISTRY.items()
        if row.exclusion_reason is not None
    )
    assert excluded == held
    assert frozenset(FOLD_GATE_SELECTED_NODES) == (
        frozenset(FOLD_GATE_NODE_REGISTRY) - held
    )
    assert all(
        FOLD_GATE_NODE_REGISTRY[node_id].exclusion_reason
        == D781_EXCLUSION_REASON
        for node_id in held
    )


def test_family_population_and_shortfalls_are_fail_closed() -> None:
    population = dict(fold_gate_family_population())
    assert population == {
        "worklog": 2,
        "archive": 2,
        "decisions": 0,
        "failures": 3,
        "phase3": 0,
        "folded": 1,
        "rotation": 0,
    }
    assert dict(fold_gate_family_shortfalls(("worklog", "failures"))) == {}
    assert dict(
        fold_gate_family_shortfalls(("decisions", "phase3", "rotation"))
    ) == {
        "decisions": (1, 0),
        "phase3": (1, 0),
        "rotation": (1, 0),
    }
    for invalid in (("unknown",), ("worklog", "worklog")):
        with pytest.raises(ValueError):
            fold_gate_family_shortfalls(invalid)
    observed_uncovered = frozenset(
        family for family, count in population.items() if count == 0
    )
    allowlisted = frozenset(FOLD_GATE_UNCOVERED_FAMILY_ALLOWLIST)
    _assert_uncovered_allowlist_exact(observed_uncovered, allowlisted)


def test_uncovered_allowlist_rejects_reverse_only_drift() -> None:
    observed_uncovered = frozenset({"decisions", "phase3"})
    allowlisted = frozenset({"decisions", "phase3", "rotation"})
    assert observed_uncovered - allowlisted == frozenset()

    with pytest.raises(AssertionError):
        _assert_uncovered_allowlist_exact(observed_uncovered, allowlisted)


def test_registered_execution_graph_cannot_restart_pytest_or_acceptance() -> None:
    source = SPOOL_TEST_PATH.read_text(encoding="utf-8")
    roots = frozenset(
        nodeid.split("::", 1)[1] for nodeid in FOLD_GATE_SELECTED_NODES
    )
    assert _forbidden_launcher_calls(
        source,
        roots,
        filename="test_spool_fold.py",
    ) == ()

    conftest_path = ROOT / "orchestrator/tests/conftest.py"
    conftest_source = conftest_path.read_text(encoding="utf-8")
    conftest_tree = ast.parse(conftest_source, filename="conftest.py")
    selected_tree = ast.parse(source, filename="test_spool_fold.py")
    requested_fixtures = {
        argument.arg
        for statement in selected_tree.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
        and statement.name in roots
        for argument in (
            *statement.args.posonlyargs,
            *statement.args.args,
            *statement.args.kwonlyargs,
        )
    }
    conftest_roots = {
        statement.name
        for statement in conftest_tree.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
        and (
            statement.name.startswith("pytest_")
            or statement.name in requested_fixtures
            or any(
                isinstance(decorator, ast.Call)
                and _call_name(decorator.func) == "pytest.fixture"
                and any(
                    keyword.arg == "autouse"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is True
                    for keyword in decorator.keywords
                )
                for decorator in statement.decorator_list
            )
        )
    }
    assert _forbidden_launcher_calls(
        conftest_source,
        frozenset(conftest_roots),
        filename="conftest.py",
    ) == ()

    negative = """
import subprocess
def helper():
    subprocess.run(['python3', 'tools/run_tests.py'])
def test_registered():
    helper()
def test_unrelated():
    subprocess.run(['python3', '-m', 'pytest'])
"""
    assert _forbidden_launcher_calls(
        negative,
        frozenset({"test_registered"}),
        filename="negative.py",
    ) == (("helper", 4, "subprocess.run"),)


def _materialize_real_canonical_source(destination: Path) -> None:
    for source in SPOOL_TESTS._real_canonical_sources(ROOT):
        target = destination / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        assert target.read_bytes() == source.read_bytes()


def _mutate_latest_t139_bytes(worklog_path: Path) -> None:
    raw = worklog_path.read_bytes()
    text = raw.decode("utf-8", errors="strict")
    headings = list(SPOOL_TESTS.spool_fold.WORKLOG_ENTRY_RE.finditer(text))
    assert headings, "positive control の worklog に global entry がない"
    maximum = max(int(heading.group("ordinal")) for heading in headings)
    latest = [
        heading
        for heading in headings
        if int(heading.group("ordinal")) == maximum
    ]
    assert len(latest) == 1 and latest[0] is headings[-1], (
        "positive control の最新 entry が一意でない",
        maximum,
        len(latest),
    )
    entry_start = len(text[: latest[0].start()].encode("utf-8"))
    marker = b"- [T-139] "
    relative = raw[entry_start:].rfind(marker)
    assert relative >= 0, "positive control の最新 entry に T-139 marker がない"
    marker_offset = entry_start + relative
    digit_offset = marker_offset + marker.index(b"9")
    assert raw[digit_offset:digit_offset + 1] == b"9"
    mutated = raw[:digit_offset] + b"8" + raw[digit_offset + 1:]
    assert len(mutated) == len(raw)
    assert sum(before != after for before, after in zip(raw, mutated)) == 1
    worklog_path.write_bytes(mutated)


def test_real_node_rejects_one_byte_t139_mutation_and_accepts_clean_bytes(
    tmp_path: Path,
) -> None:
    clean_source = tmp_path / "clean-source"
    _materialize_real_canonical_source(clean_source)
    clean_run = tmp_path / "clean-run"
    clean_run.mkdir()
    SPOOL_TESTS.test_cli_base_digest_real_corpus_resolves_active_and_rejects_completed(
        clean_run,
        _checkout=clean_source,
    )

    mutated_source = tmp_path / "mutated-source"
    _materialize_real_canonical_source(mutated_source)
    _mutate_latest_t139_bytes(mutated_source / "docs/worklog.md")
    mutated_run = tmp_path / "mutated-run"
    mutated_run.mkdir()
    with pytest.raises(AssertionError):
        SPOOL_TESTS.test_cli_base_digest_real_corpus_resolves_active_and_rejects_completed(
            mutated_run,
            _checkout=mutated_source,
        )


def _run() -> int:
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    passed = failed = 0
    for test in tests:
        monkeypatch = None
        try:
            plain_cases = getattr(test, "_plain_cases", None)
            if plain_cases is not None:
                for case in plain_cases:
                    test(*case)
            else:
                parameters = inspect.signature(test).parameters
                if not parameters:
                    test()
                elif tuple(parameters) == ("monkeypatch",):
                    monkeypatch = pytest.MonkeyPatch()
                    test(monkeypatch)
                elif tuple(parameters) == ("tmp_path",):
                    with tempfile.TemporaryDirectory(
                        prefix="fold-gate-nodes-contract-"
                    ) as raw:
                        test(Path(raw))
                else:
                    raise AssertionError(
                        f"unsupported plain-runner parameters: {tuple(parameters)}"
                    )
            print(f"PASS {test.__name__}")
            passed += 1
        except AssertionError as exc:
            print(f"FAIL {test.__name__}: {exc}")
            failed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR {test.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
        finally:
            if monkeypatch is not None:
                monkeypatch.undo()
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
