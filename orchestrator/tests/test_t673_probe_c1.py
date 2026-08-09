# -*- coding: utf-8 -*-
"""T-673 C1: 遷移 gate の direct iterator を pin する AST 検査。

この検査が閉じるのは、対象 loop の直接 slice と、loop 前の Subscript を
使う再束縛・削除である。helper 呼出しや islice、alias の内部、callback の弱化、
caller 側の別量化は閉じない。また変数 rename や無害な iterator wrapper も拒否する。
"""
from __future__ import annotations

import ast

import pytest

from test_env_contract_activation import REPO_ROOT


def _is_name(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


def _is_predicate_loop_target(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Tuple)
        and len(node.elts) == 2
        and _is_name(node.elts[0], "predecessor")
        and _is_name(node.elts[1], "successor")
    )


def _target_binds_name(node: ast.AST, name: str) -> bool:
    if _is_name(node, name):
        return True
    if isinstance(node, (ast.Tuple, ast.List)):
        return any(_target_binds_name(element, name) for element in node.elts)
    return False


def _subscript_root_name(node: ast.AST) -> str | None:
    while isinstance(node, ast.Subscript):
        node = node.value
    if isinstance(node, ast.Name):
        return node.id
    return None


def _preloop_slice_rebindings_or_deletes(
    function: ast.FunctionDef,
    *,
    name: str,
    loop_lineno: int,
) -> list[str]:
    offenders: list[str] = []
    for node in ast.walk(function):
        if getattr(node, "lineno", loop_lineno) >= loop_lineno:
            continue
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, (ast.AnnAssign, ast.NamedExpr, ast.AugAssign)):
            targets = [node.target]
            value = node.value
        else:
            targets = []
            value = None
        if targets and value is not None:
            binds_name = any(_target_binds_name(target, name) for target in targets)
            mutates_slice = any(
                isinstance(target, ast.Subscript)
                and _subscript_root_name(target) == name
                for target in targets
            )
            contains_subscript = any(
                isinstance(descendant, ast.Subscript)
                for descendant in ast.walk(value)
            )
            if (binds_name and contains_subscript) or mutates_slice:
                offenders.append(type(node).__name__)
        if isinstance(node, ast.Delete) and any(
            _is_name(target, name)
            or (
                isinstance(target, ast.Subscript)
                and _subscript_root_name(target) == name
            )
            for target in node.targets
        ):
            offenders.append("Delete")
    return offenders


def test_activation_transition_quantifier_loops_are_direct_and_unsliced():
    path = REPO_ROOT / "orchestrator/campaign/env_contract_activation.py"
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    matches = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name == "_validate_activation_transition"
    ]
    assert len(matches) == 1, (
        "_validate_activation_transition FunctionDef must be exactly one; "
        f"observed={len(matches)}"
    )
    function = matches[0]

    loops = [node for node in ast.walk(function) if isinstance(node, ast.For)]
    assert len(loops) == 2, (
        "transition quantifier loops must be exactly two; "
        f"observed={len(loops)}"
    )
    generation_loops = [
        loop for loop in loops if _is_name(loop.target, "successor")
    ]
    predicate_loops = [
        loop for loop in loops if _is_predicate_loop_target(loop.target)
    ]
    assert len(generation_loops) == 1, (
        "successor_rows quantifier loop must be exactly one; "
        f"observed={len(generation_loops)}"
    )
    assert len(predicate_loops) == 1, (
        "changed quantifier loop must be exactly one; "
        f"observed={len(predicate_loops)}"
    )

    generation_loop = generation_loops[0]
    predicate_loop = predicate_loops[0]
    assert type(generation_loop.iter) is ast.Name
    assert generation_loop.iter.id == "successor_rows"
    assert type(predicate_loop.iter) is ast.Name
    assert predicate_loop.iter.id == "changed"

    assert _preloop_slice_rebindings_or_deletes(
        function,
        name="successor_rows",
        loop_lineno=generation_loop.lineno,
    ) == []
    assert _preloop_slice_rebindings_or_deletes(
        function,
        name="changed",
        loop_lineno=predicate_loop.lineno,
    ) == []


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
