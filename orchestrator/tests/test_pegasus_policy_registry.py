# -*- coding: utf-8 -*-
"""Pegasus policy inventory gate と direct consumer の best-effort tripwire。"""
from __future__ import annotations

import ast
import json
import re
import shlex
import stat
import subprocess
import sys
from functools import cache
from pathlib import Path, PurePosixPath

import pytest


_REPO = Path(__file__).resolve().parents[2]
_POLICY_DIR = _REPO / "tools/pegasus/policies"
_REGISTRY_RELATIVE = PurePosixPath("tools/pegasus/policies/registry_v1.json")
_REGISTRY = _REPO / _REGISTRY_RELATIVE
_LEGACY_POLICIES = {
    "orchestrator/qualification/t126_reservation_policy_v1.json",
    "tools/pegasus/policy.json",
}
_MOVED_KEYS = {
    "smoke_walltime",
    "smoke_walltime_s",
    "certify_walltime",
    "certify_walltime_s",
    "finalize_reserve_s",
    "floor_walltime",
    "floor_walltime_s",
}
_HEREDOC = re.compile(
    r"(?P<opener>^[^\n]*<<(?:'PY'|\"PY\"|PY)\s*$)\n(?P<body>.*?)^PY\s*$",
    re.MULTILINE | re.DOTALL,
)
_SHELL_ASSIGNMENT = re.compile(
    r"(?m)^[ \t]*([A-Z_][A-Z0-9_]*)="
    r"(?:\"([^\"]*)\"|'([^']*)'|([^\s#]+))\s*$"
)
_SHELL_VARIABLE = re.compile(r"^\$(?:\{)?([A-Z_][A-Z0-9_]*)(?:\})?$")


@cache
def _tracked_paths() -> frozenset[PurePosixPath]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=_REPO,
        capture_output=True,
        check=True,
    )
    return frozenset(
        PurePosixPath(raw.decode("utf-8"))
        for raw in result.stdout.split(b"\0")
        if raw
    )


def _surface_findings(path: Path, *, label: str) -> list[str]:
    """Reject symlink components and paths resolving outside the repository."""
    findings: list[str] = []
    try:
        relative = path.relative_to(_REPO)
    except ValueError:
        return [f"{label} is not lexically inside the repository: {path}"]

    current = _REPO
    for part in relative.parts:
        current /= part
        try:
            info = current.lstat()
        except OSError as exc:
            findings.append(f"{label} path component cannot be lstat'ed: {current}: {exc}")
            break
        if stat.S_ISLNK(info.st_mode):
            findings.append(f"{label} path component is a symlink: {current}")

    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(_REPO.resolve(strict=True))
    except (OSError, ValueError) as exc:
        findings.append(f"{label} does not strictly resolve inside the repository: {path}: {exc}")
    return findings


def _target_binds_name(target: ast.AST | None, name: str) -> bool:
    if isinstance(target, ast.Name):
        return target.id == name
    if isinstance(target, (ast.Tuple, ast.List)):
        return any(_target_binds_name(item, name) for item in target.elts)
    return False


def _rebinds_shared_handle(item: ast.withitem, handle: str) -> bool:
    """Return whether a with-item replaces, rather than preserves, a handle."""
    if not _target_binds_name(item.optional_vars, handle):
        return False
    return not (
        isinstance(item.optional_vars, ast.Name)
        and item.optional_vars.id == handle
        and isinstance(item.context_expr, ast.Name)
        and item.context_expr.id == handle
    )


def _shared_handle_call_ids(statements: list[ast.stmt], handle: str) -> set[int]:
    """Track calls while nested ``with`` bindings retain handle provenance."""
    calls: set[int] = set()

    class HandleVisitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
            if any(
                isinstance(argument, ast.Name) and argument.id == handle
                for argument in node.args
            ):
                calls.add(id(node))
            self.generic_visit(node)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
            return

        def visit_With(self, node: ast.With) -> None:  # noqa: N802
            for item in node.items:
                self.visit(item.context_expr)
            if any(_rebinds_shared_handle(item, handle) for item in node.items):
                return
            for statement in node.body:
                self.visit(statement)

        visit_AsyncFunctionDef = visit_FunctionDef
        visit_Lambda = visit_FunctionDef
        visit_ClassDef = visit_FunctionDef
        visit_AsyncWith = visit_With

    visitor = HandleVisitor()
    for statement in statements:
        if isinstance(statement, (ast.With, ast.AsyncWith)) and any(
            _rebinds_shared_handle(item, handle) for item in statement.items
        ):
            for item in statement.items:
                visitor.visit(item.context_expr)
            break
        visitor.visit(statement)
    return calls


def _local_nodes(scope: ast.AST) -> list[ast.AST]:
    """scope 内だけを列挙し、nested scope の同名変数を混ぜない。"""
    body = getattr(scope, "body", ())
    roots = list(body) if isinstance(body, list) else [body]
    nodes: list[ast.AST] = []
    stack = roots[:]
    while stack:
        node = stack.pop()
        nodes.append(node)
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda),
        ):
            continue
        for child in ast.iter_child_nodes(node):
            if isinstance(
                child,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda),
            ):
                continue
            stack.append(child)
    return nodes


def _scopes(tree: ast.Module) -> list[ast.AST]:
    return [tree, *[
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda))
    ]]


def _mentions_shared_path(expr: ast.AST, shared_argv: set[int]) -> bool:
    for node in ast.walk(expr):
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Attribute)
            and isinstance(node.value.value, ast.Name)
            and node.value.value.id == "sys"
            and node.value.attr == "argv"
            and isinstance(node.slice, ast.Constant)
            and node.slice.value in shared_argv
        ):
            return True
        if (
            not shared_argv
            and isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and "tools/pegasus/policy.json" in node.value
        ):
            return True
    return False


def _is_shared_load(
    expr: ast.AST,
    shared_argv: set[int],
    shared_handle_loads: set[int] | None = None,
) -> bool:
    if not isinstance(expr, ast.Call):
        return False
    function = expr.func
    name = (
        function.id if isinstance(function, ast.Name)
        else function.attr if isinstance(function, ast.Attribute)
        else ""
    )
    if name not in {"load", "loads", "_load_json", "load_source_json"}:
        return False
    if id(expr) in (shared_handle_loads or set()):
        return True
    return any(
        _mentions_shared_path(argument, shared_argv)
        for argument in (*expr.args, *[kw.value for kw in expr.keywords])
    )


def _literal_keys(expr: ast.AST, loop_keys: dict[str, set[str]]) -> set[str]:
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return {expr.value}
    if isinstance(expr, ast.Name):
        return loop_keys.get(expr.id, set())
    if isinstance(expr, (ast.Tuple, ast.List, ast.Set)):
        return set().union(*(_literal_keys(item, loop_keys) for item in expr.elts))
    return set()


def _moved_reads(
    source: str,
    *,
    shared_argv: set[int],
    line_offset: int = 0,
) -> list[tuple[int, str]]:
    tree = ast.parse(source)
    findings: list[tuple[int, str]] = []
    for scope in _scopes(tree):
        nodes = _local_nodes(scope)
        roots: set[str] = set()
        shared_handle_loads: set[int] = set()
        loop_keys: dict[str, set[str]] = {}
        for node in nodes:
            if isinstance(node, ast.For) and isinstance(node.target, ast.Name):
                loop_keys[node.target.id] = _literal_keys(node.iter, {})
            if isinstance(node, (ast.With, ast.AsyncWith)):
                for item in node.items:
                    if (
                        isinstance(item.optional_vars, ast.Name)
                        and _mentions_shared_path(item.context_expr, shared_argv)
                    ):
                        shared_handle_loads.update(_shared_handle_call_ids(
                            node.body, item.optional_vars.id,
                        ))
        changed = True
        while changed:
            changed = False
            for node in nodes:
                if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                    continue
                value = node.value
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                root_value = _is_shared_load(
                    value, shared_argv, shared_handle_loads,
                ) or (
                    isinstance(value, ast.Name) and value.id in roots
                )
                if not root_value:
                    continue
                for target in targets:
                    if isinstance(target, ast.Name) and target.id not in roots:
                        roots.add(target.id)
                        changed = True
        for node in nodes:
            base: ast.AST | None = None
            keys: set[str] = set()
            if isinstance(node, ast.Subscript):
                base = node.value
                keys = _literal_keys(node.slice, loop_keys)
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {"get", "pop", "setdefault"}
                and node.args
            ):
                base = node.func.value
                keys = _literal_keys(node.args[0], loop_keys)
            if base is None or not (keys & _MOVED_KEYS):
                continue
            if (
                isinstance(base, ast.Name) and base.id in roots
            ) or _is_shared_load(base, shared_argv, shared_handle_loads):
                for key in sorted(keys & _MOVED_KEYS):
                    findings.append((node.lineno + line_offset, key))
    return sorted(set(findings))


def _shell_shared_vars(source: str) -> set[str]:
    shared: set[str] = set()
    for match in _SHELL_ASSIGNMENT.finditer(source):
        variable = match.group(1)
        value = next(group for group in match.groups()[1:] if group is not None)
        if value.endswith("/policy.json") and "/policies/" not in value:
            shared.add(variable)
    return shared


def _shell_shared_argv(opener: str, shared_vars: set[str]) -> set[int]:
    match = re.search(r"(?:^|\s)-\s+(?P<args>.*?)<<", opener)
    if match is None:
        return set()
    indexes: set[int] = set()
    for index, token in enumerate(shlex.split(match.group("args")), start=1):
        if token.startswith((">", "<")):
            continue
        variable = _SHELL_VARIABLE.fullmatch(token)
        if variable and variable.group(1) in shared_vars:
            indexes.add(index)
    return indexes


def _source_moved_reads(relative: PurePosixPath) -> list[tuple[int, str]]:
    """Find direct literal moved-key reads; this is deliberately not exhaustive."""
    source = (_REPO / relative).read_text(encoding="utf-8")
    if relative.suffix == ".py":
        return _moved_reads(source, shared_argv=set())
    findings: list[tuple[int, str]] = []
    shared_vars = _shell_shared_vars(source)
    for match in _HEREDOC.finditer(source):
        shared_argv = _shell_shared_argv(match.group("opener"), shared_vars)
        if not shared_argv:
            continue
        offset = source.count("\n", 0, match.start("body"))
        findings.extend(_moved_reads(
            match.group("body"), shared_argv=shared_argv, line_offset=offset,
        ))
    return sorted(set(findings))


def _tracked_live_sources(
    tracked_paths: frozenset[PurePosixPath],
) -> list[PurePosixPath]:
    return sorted(
        path for path in tracked_paths
        if path.suffix in {".py", ".sh"} and "tests" not in path.parts
    )


def test_pegasus_policy_registry_is_complete_and_tracked() -> None:
    findings: list[str] = []
    findings.extend(_surface_findings(_POLICY_DIR, label="policy directory"))
    findings.extend(_surface_findings(_REGISTRY, label="registry"))
    try:
        directory_stat = _POLICY_DIR.lstat()
        registry_stat = _REGISTRY.lstat()
    except OSError as exc:
        pytest.fail(f"policy inventory surface cannot be lstat'ed: {exc}")
    if not stat.S_ISDIR(directory_stat.st_mode):
        findings.append(f"policy directory is not a directory: {_POLICY_DIR}")
    if not stat.S_ISREG(registry_stat.st_mode):
        findings.append(f"registry is not a regular file: {_REGISTRY}")
    if findings:
        pytest.fail("\n".join(findings))

    tracked_paths = _tracked_paths()
    registry = json.loads(_REGISTRY.read_text(encoding="utf-8"))
    if set(registry) != {"schema_version", "policy_paths"}:
        findings.append(f"registry top-level keys: {sorted(registry)}")
    if registry.get("schema_version") != "pegasus-policy-registry/v1":
        findings.append(f"registry schema_version: {registry.get('schema_version')!r}")
    policy_paths = registry.get("policy_paths")
    if (
        type(policy_paths) is not list
        or not policy_paths
        or any(type(path) is not str for path in policy_paths)
    ):
        pytest.fail(f"registry policy_paths must be a non-empty string list: {policy_paths!r}")
    if policy_paths != sorted(set(policy_paths)):
        findings.append("registry policy_paths must be sorted and unique")

    registered = set(policy_paths)
    for relative in policy_paths:
        parsed = PurePosixPath(relative)
        if (
            parsed.is_absolute()
            or relative != parsed.as_posix()
            or any(part in {"", ".", ".."} for part in parsed.parts)
        ):
            findings.append(f"registry path is not canonical repo-relative: {relative!r}")
            continue
        absolute = _REPO / parsed
        findings.extend(_surface_findings(absolute, label=f"registry entry {relative}"))
        try:
            entry_stat = absolute.lstat()
        except OSError:
            findings.append(f"registry entry does not exist: {relative}")
        else:
            if stat.S_ISLNK(entry_stat.st_mode):
                findings.append(f"registry entry is a symlink: {relative}")
            elif not stat.S_ISREG(entry_stat.st_mode):
                findings.append(f"registry entry is not a regular file: {relative}")
        if parsed not in tracked_paths:
            findings.append(f"registry entry is not tracked: {relative}")

    discovered: set[str] = set()
    for entry in _POLICY_DIR.iterdir():
        if entry == _REGISTRY:
            continue
        entry_stat = entry.lstat()
        if stat.S_ISREG(entry_stat.st_mode):
            discovered.add(entry.relative_to(_REPO).as_posix())
        else:
            findings.append(
                "policy directory must be flat and contain only regular policy files: "
                f"{entry.relative_to(_REPO).as_posix()}"
            )
    expected = discovered | _LEGACY_POLICIES
    if registered != expected:
        findings.append(
            "registry/directory closed set mismatch: "
            f"missing={sorted(expected - registered)}, extra={sorted(registered - expected)}"
        )
    if _REGISTRY_RELATIVE not in tracked_paths:
        findings.append(f"registry itself is not tracked: {_REGISTRY_RELATIVE}")

    assert not findings, "\n".join(findings)


def test_direct_shared_policy_reads_of_moved_keys_are_a_best_effort_tripwire() -> None:
    """Tripwire direct literal Python reads, not every possible consumer shape.

    This intentionally is not a completeness proof. Variable-bound keys, string
    concatenation, jq variable expansion, and tracked suffixless executables are
    outside this scanner's detection envelope.
    """
    tracked_paths = _tracked_paths()

    positive_control = _moved_reads(
        "import json, sys\np = json.load(open(sys.argv[1]))\n"
        "print(p['certify_walltime_s'])\n",
        shared_argv={1},
    )
    assert positive_control == [(3, "certify_walltime_s")], positive_control
    nested_control = _moved_reads(
        "import json, sys\np = json.load(open(sys.argv[1]))['silo_ladder_rung1']\n"
        "print(p['finalize_reserve_s'])\n",
        shared_argv={1},
    )
    assert nested_control == [], nested_control
    task_file_control = _moved_reads(
        "import json, sys\n"
        "with open(sys.argv[1]) as handle:\n    shared = json.load(handle)\n"
        "with open(sys.argv[2]) as handle:\n    task = json.load(handle)\n"
        "print(task['certify_walltime_s'])\n",
        shared_argv={1},
    )
    assert task_file_control == [], task_file_control
    shadowed_handle_control = _moved_reads(
        "import json, sys\n"
        "with open(sys.argv[1]) as handle:\n"
        "    shared = json.load(handle)\n"
        "    with open(sys.argv[2]) as handle:\n"
        "        task = json.load(handle)\n"
        "        print(task['certify_walltime_s'])\n",
        shared_argv={1},
    )
    assert shadowed_handle_control == [], shadowed_handle_control
    rebound_shared_handle_control = _moved_reads(
        "import json, sys\n"
        "with open(sys.argv[1]) as handle:\n"
        "    with handle as handle:\n"
        "        policy = json.load(handle)\n"
        "        print(policy['certify_walltime_s'])\n",
        shared_argv={1},
    )
    assert rebound_shared_handle_control == [
        (5, "certify_walltime_s"),
    ], rebound_shared_handle_control

    consumers = {
        f"{relative}:{line}:{key}"
        for relative in _tracked_live_sources(tracked_paths)
        for line, key in _source_moved_reads(relative)
    }
    assert not consumers, (
        "moved keys still read from tools/pegasus/policy.json: "
        + ", ".join(sorted(consumers))
    )


def _run() -> int:
    return int(pytest.main(["-q", str(Path(__file__).resolve())]))


if __name__ == "__main__":
    raise SystemExit(_run())
