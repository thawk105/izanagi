# -*- coding: utf-8 -*-
"""[T-452] effective-clock policy authority and CLI surface tests."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest


ORCHESTRATOR = Path(__file__).resolve().parent.parent
if str(ORCHESTRATOR.parent) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR.parent))

from orchestrator.calibrator import cli  # noqa: E402
from orchestrator.calibrator import effective_clock_policy  # noqa: E402


def test_effective_clock_policy_is_single_literal_authority():
    path = ORCHESTRATOR / "calibrator/effective_clock_policy.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assignments = [node for node in ast.walk(tree) if isinstance(node, ast.AnnAssign)]
    assert len(assignments) == 1
    assignment = assignments[0]
    assert isinstance(assignment.target, ast.Name)
    assert assignment.target.id == "EFFECTIVE_CLOCK_TOLERANCE_PCT"
    assert ast.unparse(assignment.annotation) == "Final[float]"
    assert isinstance(assignment.value, ast.Constant)
    assert type(assignment.value.value) is float
    assert assignment.value.value == 2.0
    assert effective_clock_policy.EFFECTIVE_CLOCK_TOLERANCE_PCT == 2.0
    assert not any(isinstance(node, (ast.Dict, ast.FunctionDef, ast.AsyncFunctionDef))
                   for node in ast.walk(tree))
    assert "environ" not in source and "getenv" not in source


def test_certify_parser_option_surface_is_exact():
    parser = cli.build_parser()
    option_strings = {
        option
        for action in parser._actions
        for option in action.option_strings
    }
    destinations = {action.dest for action in parser._actions}
    assert "--effective-clock-tolerance-pct" not in option_strings
    assert "--clock-window" not in option_strings
    assert "effective_clock_tolerance_pct" not in destinations


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
