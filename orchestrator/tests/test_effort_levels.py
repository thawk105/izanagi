# -*- coding: utf-8 -*-
"""reasoning / effort の repo policy tests (pytest / plain Python 両対応)。"""
from __future__ import annotations

import ast
import importlib.util
import sys
import traceback
from pathlib import Path


_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_EFFORT_LEVELS_PATH = _ROOT / "tools" / "dev_waves" / "effort_levels.py"
_MODULE_SPEC = importlib.util.spec_from_file_location(
    "_izanagi_effort_levels", _EFFORT_LEVELS_PATH
)
assert _MODULE_SPEC and _MODULE_SPEC.loader
effort_levels = importlib.util.module_from_spec(_MODULE_SPEC)
_MODULE_SPEC.loader.exec_module(effort_levels)

from orchestrator.codex_roles import launcher, spec  # noqa: E402


def test_launcher_reasoning_policy_is_subset_of_repo_policy() -> None:
    assert set(launcher.SAFE_ADAPTER_CODEX_REASONING_EFFORTS) <= set(
        effort_levels.CODEX_REASONING_EFFORTS
    )


def test_role_manifest_reasoning_policy_is_subset_of_repo_policy() -> None:
    assert set(spec.ROLE_MANIFEST_CODEX_REASONING_EFFORTS) <= set(
        effort_levels.CODEX_REASONING_EFFORTS
    )


def test_effort_vocabularies_are_exact_and_ordered() -> None:
    expected = ("low", "medium", "high", "xhigh", "max")
    assert effort_levels.CLAUDE_EFFORTS == expected
    assert effort_levels.CODEX_REASONING_EFFORTS == expected + ("ultra",)


def test_normal_import_matches_direct_load() -> None:
    from tools.dev_waves.effort_levels import (
        CLAUDE_EFFORTS,
        CODEX_REASONING_EFFORTS,
    )

    assert CLAUDE_EFFORTS == effort_levels.CLAUDE_EFFORTS
    assert CODEX_REASONING_EFFORTS == effort_levels.CODEX_REASONING_EFFORTS


def test_effort_levels_does_not_import_orchestrator() -> None:
    tree = ast.parse(_EFFORT_LEVELS_PATH.read_text(encoding="utf-8"))
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.append(node.module)
            else:
                imported_modules.extend(alias.name for alias in node.names)
    assert not any(
        name == "orchestrator" or name.startswith("orchestrator.")
        for name in imported_modules
    ), imported_modules


def _run() -> int:
    fns = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    passed = failed = errors = 0
    for fn in fns:
        try:
            fn()
            passed += 1
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {fn.__name__}: {exc}")
        except Exception:
            errors += 1
            print(f"ERROR {fn.__name__}:")
            traceback.print_exc()
    print(f"\n{passed} passed, {failed} failed, {errors} errors (of {len(fns)})")
    return 0 if failed == 0 and errors == 0 else 1


if __name__ == "__main__":
    sys.exit(_run())
