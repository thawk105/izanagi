#!/usr/bin/env python3
"""Detect unguarded Python subprocesses in ``orchestrator/`` and ``tools/``.

The checker only inspects direct calls to ``subprocess.run``, ``Popen``,
``call``, ``check_call``, and ``check_output`` with an explicit ``env=``
keyword.  P1 is deliberately limited to list/tuple argv values whose
``argv[0]`` is ``sys.executable``, ``"python"``, ``"python3"``, or a
``.py`` string literal.  P2 is a shallow guard check: it understands direct
dict literals, ``dict(...)`` literals, ``-B``, literals in the enclosing
function, and one same-file assignment hop to a locally defined function.
Dynamic argv, imported environment builders, and deeper data-flow are not
analysed.

The following paths are intentionally out of scope and are not detected:
``shell=True`` with a string argv; ``os.system``/``os.popen``/
``multiprocessing``; startup performed inside pytest-xdist workers; env
builders reached through imports; and function resolution beyond one hop.
These are future scope-expansion candidates and are not implemented here.

Return codes are 0 for no violations, 1 for violations, and 2 when the
repository cannot be fully classified (for example, a read or parse error).
Indeterminate results take precedence over violations.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Sequence


CLEAN_RC = 0
VIOLATION_RC = 1
INDETERMINATE_RC = 2
TARGET_CALLEES = frozenset(
    {"run", "Popen", "call", "check_call", "check_output"}
)
GUARD_NAME = "PYTHONDONTWRITEBYTECODE"


@dataclass(frozen=True)
class Violation:
    path: Path
    lineno: int
    col_offset: int
    callee: str


@dataclass(frozen=True)
class ParseIssue:
    path: Path | None
    error: str


@dataclass(frozen=True)
class ScanReport:
    violations: tuple[Violation, ...]
    issues: tuple[ParseIssue, ...]


def iter_python_files(repo: Path) -> Iterator[Path]:
    """Yield sorted-scope Python files, excluding every ``__pycache__`` path."""

    for directory_name in ("orchestrator", "tools"):
        directory = repo / directory_name
        if not directory.is_dir():
            continue
        for path in directory.rglob("*.py"):
            if "__pycache__" in path.parts or not path.is_file():
                continue
            yield path


def _literal_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _direct_subprocess_callee(node: ast.Call) -> str | None:
    function = node.func
    if not isinstance(function, ast.Attribute):
        return None
    if not isinstance(function.value, ast.Name) or function.value.id != "subprocess":
        return None
    if function.attr not in TARGET_CALLEES:
        return None
    return function.attr


def _is_sys_executable(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "sys"
        and node.attr == "executable"
    )


def _is_python_argv(node: ast.Call) -> bool:
    if not node.args or not isinstance(node.args[0], (ast.List, ast.Tuple)):
        return False
    argv = node.args[0].elts
    if not argv:
        return False
    argv0 = argv[0]
    literal = _literal_string(argv0)
    if _is_sys_executable(argv0):
        return True
    if literal in {"python", "python3"}:
        return True
    return literal is not None and literal.endswith(".py")


def _dict_literal_has_guard(node: ast.AST) -> bool:
    if not isinstance(node, ast.Dict):
        return False
    return any(_literal_string(key) == GUARD_NAME for key in node.keys)


def _mapping_has_guard(node: ast.AST) -> bool:
    if _dict_literal_has_guard(node):
        return True
    if not isinstance(node, ast.Call):
        return False
    if not isinstance(node.func, ast.Name) or node.func.id != "dict":
        return False
    if any(keyword.arg == GUARD_NAME for keyword in node.keywords):
        return True
    if any(_dict_literal_has_guard(argument) for argument in node.args):
        return True
    return any(
        keyword.arg is None and _dict_literal_has_guard(keyword.value)
        for keyword in node.keywords
    )


class _ScopeGuardVisitor(ast.NodeVisitor):
    """Find literals in one function without entering nested scopes."""

    def __init__(self, root: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.root = root
        self.found = False

    def visit_Constant(self, node: ast.Constant) -> None:
        if node.value == GUARD_NAME:
            self.found = True

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node is self.root:
            self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        if node is self.root:
            self.generic_visit(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        return

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        return


def _scope_has_guard(
    scope: ast.FunctionDef | ast.AsyncFunctionDef | None,
) -> bool:
    if scope is None:
        return False
    visitor = _ScopeGuardVisitor(scope)
    visitor.visit(scope)
    return visitor.found


@dataclass(frozen=True)
class _Assignment:
    name: str
    value: ast.AST
    lineno: int
    col_offset: int
    scope: ast.FunctionDef | ast.AsyncFunctionDef | None


class _FileIndex(ast.NodeVisitor):
    """Index same-file function definitions and simple local assignments."""

    def __init__(self) -> None:
        self.function_definitions: dict[
            str, list[ast.FunctionDef | ast.AsyncFunctionDef]
        ] = {}
        self.assignments: list[_Assignment] = []
        self._function_stack: list[ast.FunctionDef | ast.AsyncFunctionDef] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_definitions.setdefault(node.name, []).append(node)
        self._function_stack.append(node)
        self.generic_visit(node)
        self._function_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.function_definitions.setdefault(node.name, []).append(node)
        self._function_stack.append(node)
        self.generic_visit(node)
        self._function_stack.pop()

    def visit_Assign(self, node: ast.Assign) -> None:
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            self.assignments.append(
                _Assignment(
                    name=node.targets[0].id,
                    value=node.value,
                    lineno=node.lineno,
                    col_offset=node.col_offset,
                    scope=(self._function_stack[-1] if self._function_stack else None),
                )
            )
        self.generic_visit(node)


def _position(node: ast.AST) -> tuple[int, int]:
    return (getattr(node, "lineno", -1), getattr(node, "col_offset", -1))


def _nearest_assignment(
    name: str,
    call: ast.Call,
    scope: ast.FunctionDef | ast.AsyncFunctionDef | None,
    assignments: Sequence[_Assignment],
) -> _Assignment | None:
    call_position = _position(call)
    candidates = [
        assignment
        for assignment in assignments
        if assignment.name == name
        and assignment.scope is scope
        and (assignment.lineno, assignment.col_offset) <= call_position
    ]
    if not candidates and scope is not None:
        candidates = [
            assignment
            for assignment in assignments
            if assignment.name == name
            and assignment.scope is None
            and (assignment.lineno, assignment.col_offset) <= call_position
        ]
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item.lineno, item.col_offset))


def _one_hop_guard(
    name: str,
    call: ast.Call,
    scope: ast.FunctionDef | ast.AsyncFunctionDef | None,
    index: _FileIndex,
) -> bool:
    assignment = _nearest_assignment(name, call, scope, index.assignments)
    if assignment is None or not isinstance(assignment.value, ast.Call):
        return False
    if not isinstance(assignment.value.func, ast.Name):
        return False
    definitions = index.function_definitions.get(assignment.value.func.id, ())
    if not definitions:
        return False
    definition = max(definitions, key=_position)
    return _scope_has_guard(definition)


def _argv_has_bytecode_flag(call: ast.Call) -> bool:
    if not call.args or not isinstance(call.args[0], (ast.List, ast.Tuple)):
        return False
    return any(_literal_string(element) == "-B" for element in call.args[0].elts)


def _env_has_guard(
    call: ast.Call,
    env_value: ast.AST,
    scope: ast.FunctionDef | ast.AsyncFunctionDef | None,
    index: _FileIndex,
) -> bool:
    if _argv_has_bytecode_flag(call) or _mapping_has_guard(env_value):
        return True
    if not isinstance(env_value, ast.Name):
        return False
    if _scope_has_guard(scope):
        return True
    return _one_hop_guard(env_value.id, call, scope, index)


class _CallVisitor(ast.NodeVisitor):
    def __init__(self, index: _FileIndex, path: Path) -> None:
        self.index = index
        self.path = path
        self.violations: list[Violation] = []
        self._function_stack: list[ast.FunctionDef | ast.AsyncFunctionDef] = []

    @property
    def _current_function(
        self,
    ) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
        return self._function_stack[-1] if self._function_stack else None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._function_stack.append(node)
        self.generic_visit(node)
        self._function_stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._function_stack.append(node)
        self.generic_visit(node)
        self._function_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        callee = _direct_subprocess_callee(node)
        if callee is not None and _is_python_argv(node):
            env_keyword = next(
                (keyword for keyword in node.keywords if keyword.arg == "env"),
                None,
            )
            if env_keyword is not None and not _env_has_guard(
                node,
                env_keyword.value,
                self._current_function,
                self.index,
            ):
                self.violations.append(
                    Violation(
                        path=self.path,
                        lineno=node.lineno,
                        col_offset=node.col_offset,
                        callee=callee,
                    )
                )
        self.generic_visit(node)


def _scan_file(path: Path) -> tuple[tuple[Violation, ...], tuple[ParseIssue, ...]]:
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return (), (ParseIssue(path=path, error=f"read-error: {exc}"),)
    try:
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, UnicodeError) as exc:
        return (), (ParseIssue(path=path, error=f"parse-error: {exc}"),)

    index = _FileIndex()
    index.visit(tree)
    visitor = _CallVisitor(index, path)
    visitor.visit(tree)
    return tuple(visitor.violations), ()


def scan_repository(repo: Path) -> ScanReport:
    repo = Path(repo).resolve(strict=False)
    issues: list[ParseIssue] = []
    violations: list[Violation] = []
    try:
        if not repo.is_dir():
            raise NotADirectoryError(repo)
        directories = [repo / name for name in ("orchestrator", "tools")]
        for directory in directories:
            if not directory.is_dir():
                issues.append(
                    ParseIssue(path=directory, error="missing-scope-directory")
                )
        files = sorted(
            iter_python_files(repo),
            key=lambda path: path.relative_to(repo).as_posix(),
        )
    except (OSError, RuntimeError, ValueError) as exc:
        issues.append(ParseIssue(path=repo, error=f"scan-error: {exc}"))
        files = ()

    for path in files:
        file_violations, file_issues = _scan_file(path)
        violations.extend(file_violations)
        issues.extend(file_issues)
    violations.sort(
        key=lambda item: (
            item.path.relative_to(repo).as_posix(),
            item.lineno,
            item.col_offset,
            item.callee,
        )
    )
    issues.sort(key=lambda item: str(item.path))
    return ScanReport(tuple(violations), tuple(issues))


def _display_path(repo: Path, path: Path | None) -> str:
    if path is None:
        return "<repository>"
    try:
        return path.relative_to(repo).as_posix()
    except ValueError:
        return path.as_posix()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="env= Python subprocess の bytecode guard を検査する。"
    )
    parser.add_argument("--repo", required=True, help="repository root")
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve(strict=False)
    report = scan_repository(repo)
    for violation in report.violations:
        print(
            f"{_display_path(repo, violation.path)}:"
            f"{violation.lineno}:{violation.col_offset + 1}:{violation.callee}"
        )
    for issue in report.issues:
        print(
            f"{_display_path(repo, issue.path)}:{issue.error}",
            file=sys.stderr,
        )
    if report.issues:
        return INDETERMINATE_RC
    return VIOLATION_RC if report.violations else CLEAN_RC


if __name__ == "__main__":
    sys.exit(main())
