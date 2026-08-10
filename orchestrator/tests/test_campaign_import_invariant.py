# -*- coding: utf-8 -*-
"""campaign import 形を tracked + untracked の実 repository へ束縛する。

gitignore された未追跡 source は operational source 集合に含まれない既知の限界がある。
"""
from __future__ import annotations

import ast
import inspect
import io
import os
import re
import subprocess
import sys
import tempfile
import tokenize
from dataclasses import dataclass
from pathlib import Path

import pytest

ORCHESTRATOR = Path(__file__).resolve().parents[1]
REPOSITORY = ORCHESTRATOR.parent
sys.path.insert(0, str(REPOSITORY))

from orchestrator.tests import repo_tree_util  # noqa: E402
from skiputil import Skip  # noqa: E402


LEGACY_RULE = "legacy-campaign-namespace"
PATH_RULE = "campaign-orchestrator-sys-path"
BOOTSTRAP_RULE = "campaign-direct-bootstrap"
DOCS_RULE = "legacy-campaign-doc-command"
RELATIVE_RULE = "campaign-absolute-sibling-import"
KNOWN_RULES = frozenset(
    {LEGACY_RULE, PATH_RULE, BOOTSTRAP_RULE, DOCS_RULE, RELATIVE_RULE}
)

DIRECT_BOOTSTRAP = '''if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"'''

SENTINELS = frozenset(
    {
        "orchestrator/campaign/ident.py",
        "orchestrator/tests/conftest.py",
        "tools/pegasus/run_probe.py",
    }
)

_MODULE_PATH_RE = re.compile(r"campaign(?:\.[A-Za-z_]\w*)*\Z")
_IMPORT_LINE_RE = re.compile(
    r"(?m)^\s*(?:from\s+(campaign(?:\.[A-Za-z_]\w*)*)\s+import\b"
    r"|import\s+(campaign(?:\.[A-Za-z_]\w*)*))"
)
_MODULE_ARG_RE = re.compile(r"(?<![\w.])-m\s+(campaign\.[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\b")
_SHELL_MODULE_LITERAL_RE = re.compile(
    r"(?<![\w.])(campaign\.[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)(?![\w.])"
)
_RATIONALE_RE = re.compile(r"(?:D|F|T)-?\d+")
_LEXICAL_SCOPES = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)


@dataclass(frozen=True, order=True)
class Violation:
    path: str
    line: int
    rule: str
    matched_text: str


@dataclass(frozen=True)
class ImportException:
    path: str
    line: int
    rule: str
    matched_text: str
    rationale: str

    def key(self) -> tuple[str, int, str, str]:
        return (self.path, self.line, self.rule, self.matched_text)


@dataclass(frozen=True)
class RepositoryScan:
    operational_paths: frozenset[str]
    sources: dict[str, str]
    violations: tuple[Violation, ...]


def _legacy_module(suffix: str | None = None) -> str:
    root = "Campaign".lower()
    return root if suffix is None else f"{root}.{suffix}"


KNOWN_EXCEPTIONS: tuple[ImportException, ...] = (
    # 根拠: T-720 — campaign.lock は module でなく検査対象の file 名
    ImportException(
        path="orchestrator/tests/test_campaign.py",
        line=4596,
        rule=LEGACY_RULE,
        matched_text=_legacy_module("lock"),
        rationale="T-720: campaign.lock という file 名を含む拒否文言の検査",
    ),
    # 根拠: T-720 — 実 import topology を検査するための legacy alias
    ImportException(
        path="orchestrator/tests/test_campaign.py",
        line=6031,
        rule=LEGACY_RULE,
        matched_text=_legacy_module("layout"),
        rationale="T-720: 実 import topology を検査するための legacy alias",
    ),
    # 根拠: D149 決定 (5) — sink の mask 再検証を実 import topology で検査する
    ImportException(
        path="orchestrator/tests/test_reflux_ir.py",
        line=124,
        rule=LEGACY_RULE,
        matched_text=_legacy_module(),
        rationale="D149(5): 二重 namespace 下でも sink が peer 値を受理することの検査",
    ),
    # 根拠: D149 決定 (5) — sink の mask 再検証を実 import topology で検査する
    ImportException(
        path="orchestrator/tests/test_reflux_ir.py",
        line=125,
        rule=LEGACY_RULE,
        matched_text=_legacy_module(),
        rationale="D149(5): 二重 namespace 下でも sink が peer 値を受理することの検査",
    ),
    # 根拠: D149 決定 (5) — topology test 後の legacy module 清掃条件
    ImportException(
        path="orchestrator/tests/test_reflux_ir.py",
        line=284,
        rule=LEGACY_RULE,
        matched_text=_legacy_module(),
        rationale="D149(5): 二重 namespace topology test の module 清掃条件",
    ),
    # 根拠: T-720 R1 — provenance に記録する値であり import ではない
    ImportException(
        path="orchestrator/campaign/p3_s4_loop_trigger_gating.py",
        line=288,
        rule=LEGACY_RULE,
        matched_text=_legacy_module("axis_trigger_gating"),
        rationale="T-720 R1: 挙動保持対象の provenance 値であり import ではない",
    ),
    # 根拠: D149 決定 (5) — sink の mask 再検証が参照する peer literal
    ImportException(
        path="orchestrator/campaign/reflux_ir.py",
        line=82,
        rule=LEGACY_RULE,
        matched_text=_legacy_module("reflux_ir"),
        rationale="D149(5): sink の mask 再検証が参照する peer literal",
    ),
    # 根拠: T-720 — campaign.lock は module でなく検査対象の file 名
    ImportException(
        path="orchestrator/tests/test_s8b_oracle_driver.py",
        line=3454,
        rule=LEGACY_RULE,
        matched_text=_legacy_module("lock"),
        rationale="T-720: campaign.lock という file 名を含む拒否文言の検査",
    ),
    # 根拠: T-720 R5 — どこからも参照されない休眠歴史 artifact
    ImportException(
        path="output/insights/2026-07-29_t139-ladder-verbatim/t139_probe_correctness.py",
        line=20,
        rule=LEGACY_RULE,
        matched_text=_legacy_module(),
        rationale="T-720 R5: どこからも参照されない休眠歴史 artifact",
    ),
    # 根拠: T-720 R5 — どこからも参照されない休眠歴史 artifact
    ImportException(
        path="output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/smoke_driver.py",
        line=8,
        rule=LEGACY_RULE,
        matched_text=_legacy_module(),
        rationale="T-720 R5: どこからも参照されない休眠歴史 artifact",
    ),
    # 根拠: T-720 R5 — どこからも参照されない休眠歴史 artifact
    ImportException(
        path="output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/smoke_driver.py",
        line=9,
        rule=LEGACY_RULE,
        matched_text=_legacy_module(),
        rationale="T-720 R5: どこからも参照されない休眠歴史 artifact",
    ),
    # 根拠: T-720 R5 — どこからも参照されない休眠歴史 artifact
    ImportException(
        path="output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/smoke_driver.py",
        line=10,
        rule=LEGACY_RULE,
        matched_text=_legacy_module("build_admission"),
        rationale="T-720 R5: どこからも参照されない休眠歴史 artifact",
    ),
    # 根拠: T-720 R2 — --repo-root が指す別 checkout を読む契約上の絶対 import
    ImportException(
        path="orchestrator/campaign/certified_writer_preflight.py",
        line=160,
        rule=RELATIVE_RULE,
        matched_text="orchestrator.campaign.certified_writer_admission",
        rationale="T-720 R2: --repo-root が指す別 checkout を読むための絶対 import",
    ),
)

EXPECTED_EXCEPTION_COUNT = 13
MINIMUM_RULE_EXCEPTION_COUNTS = {
    LEGACY_RULE: 12,
    RELATIVE_RULE: 1,
}


def _violation(path: str, line: int, rule: str, matched_text: str) -> Violation:
    return Violation(path=path, line=line, rule=rule, matched_text=matched_text)


def _static_string(node: ast.AST, names: dict[str, str]) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "join"
        and len(node.args) == 1
        and not node.keywords
        and isinstance(node.args[0], (ast.List, ast.Tuple))
    ):
        separator = _static_string(node.func.value, names)
        items = [_static_string(item, names) for item in node.args[0].elts]
        if separator is not None and all(item is not None for item in items):
            return separator.join(item for item in items if item is not None)
    if isinstance(node, ast.Name):
        return names.get(node.id)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _static_string(node.left, names)
        right = _static_string(node.right, names)
        return None if left is None or right is None else left + right
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.FormattedValue):
                item = _static_string(value.value, names)
            else:
                item = _static_string(value, names)
            if item is None:
                return None
            parts.append(item)
        return "".join(parts)
    return None


def _static_name_contexts(tree: ast.AST) -> dict[int, dict[str, str]]:
    """各 lexical scope で一意に静的な名前だけを node ごとに返す。"""
    assert isinstance(tree, ast.Module)
    node_scopes: dict[int, ast.AST] = {}
    scope_parents: dict[int, ast.AST | None] = {id(tree): None}
    scopes: list[ast.AST] = [tree]

    def bind(node: ast.AST, scope: ast.AST) -> None:
        node_scopes[id(node)] = scope
        for child in ast.iter_child_nodes(node):
            child_scope = scope
            if isinstance(child, _LEXICAL_SCOPES):
                child_scope = child
                scope_parents[id(child)] = scope
                scopes.append(child)
            bind(child, child_scope)

    bind(tree, tree)
    assignments_by_scope: dict[int, dict[str, list[ast.AST]]] = {
        id(scope): {} for scope in scopes
    }
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)) or node.value is None:
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Name):
                assignments_by_scope[id(node_scopes[id(node)])].setdefault(
                    target.id, []
                ).append(node.value)

    names_by_scope: dict[int, dict[str, str]] = {}
    for scope in scopes:
        parent = scope_parents[id(scope)]
        assignments = assignments_by_scope[id(scope)]
        bound_names = set(assignments)
        names = (
            {
                name: value
                for name, value in names_by_scope[id(parent)].items()
                if name not in bound_names
            }
            if parent is not None
            else {}
        )
        unique_assignments = {
            name: values[0] for name, values in assignments.items() if len(values) == 1
        }
        # 一意な代入だけを fixed point で解決する。重複・動的代入は親名も shadow する。
        for _ in range(len(unique_assignments) + 1):
            changed = False
            for name, value_node in unique_assignments.items():
                value = _static_string(value_node, names)
                if value is not None and names.get(name) != value:
                    names[name] = value
                    changed = True
            if not changed:
                break
        names_by_scope[id(scope)] = names

    return {
        node_id: names_by_scope[id(scope)] for node_id, scope in node_scopes.items()
    }


def _is_non_module_legacy_literal(value: str) -> bool:
    """file/path 文脈として許容する legacy 風 literal の共通判定。"""
    return value == _legacy_module("lock") or value.startswith(
        _legacy_module("lock") + "."
    )


def _textual_legacy_hits(text: str, base_line: int = 1) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for match in _IMPORT_LINE_RE.finditer(text):
        module = match.group(1) or match.group(2)
        line = base_line + text.count("\n", 0, match.start())
        hits.append((line, module))
    for match in _MODULE_ARG_RE.finditer(text):
        line = base_line + text.count("\n", 0, match.start())
        hits.append((line, match.group(1)))
    return hits


def _shell_legacy_hits(text: str) -> list[tuple[int, str]]:
    """shell 全体から campaign module literal を拾う。"""
    def without_comment(line: str) -> str:
        ending = line[len(line.rstrip("\r\n")) :]
        body = line[: len(line) - len(ending)] if ending else line
        quote: str | None = None
        escaped = False
        for index, character in enumerate(body):
            if escaped:
                escaped = False
                continue
            if character == "\\" and quote != "'":
                escaped = True
                continue
            if character in {"'", '"'}:
                if quote is None:
                    quote = character
                elif quote == character:
                    quote = None
                continue
            if character == "#" and quote is None:
                return body[:index] + " " * (len(body) - index) + ending
        return line

    uncommented = "".join(without_comment(line) for line in text.splitlines(keepends=True))
    hits = set(_textual_legacy_hits(uncommented))
    for match in _SHELL_MODULE_LITERAL_RE.finditer(uncommented):
        module = match.group(1)
        if _is_non_module_legacy_literal(module):
            continue
        if match.start() > 0 and uncommented[match.start() - 1] in {"/", "$"}:
            continue
        line = 1 + uncommented.count("\n", 0, match.start())
        hits.add((line, module))
    return sorted(hits)


def scan_legacy_namespace(
    path: str,
    source: str,
    *,
    tree: ast.AST | None = None,
) -> tuple[Violation, ...]:
    """R-A: module path literal と import 文から legacy namespace を検出する。"""
    found: set[Violation] = set()
    suffix = Path(path).suffix

    if suffix in {".sh", ".bash"} or (not suffix and source.startswith("#!")):
        for line, module in _shell_legacy_hits(source):
            found.add(_violation(path, line, LEGACY_RULE, module))
        return tuple(sorted(found))

    if tree is None:
        try:
            tree = ast.parse(source, filename=path)
        except SyntaxError as exc:
            raise AssertionError(f"R-A scan 対象 Python を parse できない: {path}:{exc.lineno}: {exc.msg}") from exc

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _MODULE_PATH_RE.fullmatch(alias.name):
                    found.add(_violation(path, node.lineno, LEGACY_RULE, alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module is not None and _MODULE_PATH_RE.fullmatch(node.module):
                found.add(_violation(path, node.lineno, LEGACY_RULE, node.module))

    name_contexts = _static_name_contexts(tree)
    for node in ast.walk(tree):
        names = name_contexts[id(node)]
        if isinstance(node, ast.Subscript) and (
            isinstance(node.value, ast.Attribute)
            and node.value.attr == "modules"
            and isinstance(node.value.value, ast.Name)
            and node.value.value.id == "sys"
        ):
            value = _static_string(node.slice, names)
            if value is not None and _MODULE_PATH_RE.fullmatch(value):
                found.add(_violation(path, node.slice.lineno, LEGACY_RULE, value))
        elif isinstance(node, ast.Compare):
            expressions = [node.left, *node.comparators]
            comparison_mentions_module_name = any(
                isinstance(item, ast.Name) and item.id in {"name", "module", "module_name"}
                for item in expressions
            )
            for expression in expressions:
                value = _static_string(expression, names)
                if value is None or not _MODULE_PATH_RE.fullmatch(value):
                    continue
                if value == _legacy_module("lock"):
                    is_message_membership = (
                        any(isinstance(operator, (ast.In, ast.NotIn)) for operator in node.ops)
                        and any(
                            isinstance(item, ast.Call)
                            and isinstance(item.func, ast.Name)
                            and item.func.id == "str"
                            for item in expressions
                        )
                    )
                    if not is_message_membership:
                        continue
                if "." in value or comparison_mentions_module_name:
                    found.add(_violation(path, expression.lineno, LEGACY_RULE, value))

        # dotted literal は呼出形によらず module path と判定する。root 単体は
        # 通常の campaign label と衝突するため、上の利用文脈内だけを対象にする。
        if isinstance(node, (ast.Constant, ast.JoinedStr, ast.BinOp, ast.Call)):
            value = _static_string(node, names)
            if value is None:
                continue
            if (
                "." in value
                and not (
                    _is_non_module_legacy_literal(value)
                )
                and _MODULE_PATH_RE.fullmatch(value)
            ):
                found.add(_violation(path, node.lineno, LEGACY_RULE, value))
            for line, module in _textual_legacy_hits(value, node.lineno):
                found.add(_violation(path, line, LEGACY_RULE, module))
    return tuple(sorted(found))


def _is_sys_path(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "path"
        and isinstance(node.value, ast.Name)
        and node.value.id == "sys"
    )


def _is_site_addsitedir(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "addsitedir"
        and isinstance(node.value, ast.Name)
        and node.value.id == "site"
    )


def _is_pythonpath_target(node: ast.AST) -> bool:
    if not isinstance(node, ast.Subscript):
        return False
    container = node.value
    is_environ = (
        isinstance(container, ast.Attribute)
        and container.attr == "environ"
        and isinstance(container.value, ast.Name)
        and container.value.id == "os"
    ) or (isinstance(container, ast.Name) and container.id == "environ")
    return is_environ and _static_string(node.slice, {}) == "PYTHONPATH"


_SYMBOLIC_REPOSITORY = "/<repository>"
_SYMBOLIC_FILE = f"{_SYMBOLIC_REPOSITORY}/orchestrator/campaign/<file>"
_SYMBOLIC_ORCHESTRATOR = f"{_SYMBOLIC_REPOSITORY}/orchestrator"


def _is_os_path_call(node: ast.Call, name: str) -> bool:
    return (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == name
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr == "path"
        and isinstance(node.func.value.value, ast.Name)
        and node.func.value.value.id == "os"
    )


def _path_expression_kind(node: ast.AST, kinds: dict[str, str]) -> str | None:
    if isinstance(node, ast.Name):
        if node.id == "__file__":
            return _SYMBOLIC_FILE
        return kinds.get(node.id)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        parts = Path(node.value).parts
        return _SYMBOLIC_ORCHESTRATOR if parts and parts[-1] == "orchestrator" else None
    if isinstance(node, ast.Call):
        if _is_os_path_call(node, "dirname"):
            if len(node.args) != 1 or node.keywords:
                return None
            kind = _path_expression_kind(node.args[0], kinds)
            return os.path.dirname(kind) if kind is not None else None
        if _is_os_path_call(node, "join"):
            if not node.args or node.keywords:
                return None
            kind = _path_expression_kind(node.args[0], kinds)
            if kind is None:
                return None
            suffixes = [_static_string(argument, {}) for argument in node.args[1:]]
            if any(suffix is None for suffix in suffixes):
                return None
            return os.path.normpath(
                os.path.join(kind, *(suffix for suffix in suffixes if suffix is not None))
            )
        if _is_os_path_call(node, "abspath") or _is_os_path_call(node, "realpath"):
            if len(node.args) != 1 or node.keywords:
                return None
            return _path_expression_kind(node.args[0], kinds)
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in {"absolute", "resolve"}
            and not node.args
            and not node.keywords
        ):
            return _path_expression_kind(node.func.value, kinds)
        if len(node.args) == 1 and not node.keywords:
            return _path_expression_kind(node.args[0], kinds)
        return None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left = _path_expression_kind(node.left, kinds)
        right = _static_string(node.right, {})
        if left is not None and right is not None:
            return os.path.normpath(os.path.join(left, right))
        if right == "orchestrator":
            return _SYMBOLIC_ORCHESTRATOR
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "parents"
        and isinstance(node.slice, ast.Constant)
        and isinstance(node.slice.value, int)
        and node.slice.value >= 0
    ):
        kind = _path_expression_kind(node.value.value, kinds)
        if kind is None:
            return None
        for _ in range(node.slice.value + 1):
            kind = os.path.dirname(kind)
        return kind
    if isinstance(node, ast.Attribute) and node.attr == "parent":
        kind = _path_expression_kind(node.value, kinds)
        return os.path.dirname(kind) if kind is not None else None
    return None


def _path_kinds(tree: ast.AST) -> dict[str, str]:
    kinds: dict[str, str] = {}
    assignments = [node for node in ast.walk(tree) if isinstance(node, (ast.Assign, ast.AnnAssign))]
    for _ in range(len(assignments) + 1):
        changed = False
        for assignment in assignments:
            value_node = assignment.value
            if value_node is None:
                continue
            kind = _path_expression_kind(value_node, kinds)
            if kind is None:
                continue
            targets = assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
            for target in targets:
                if isinstance(target, ast.Name) and kinds.get(target.id) != kind:
                    kinds[target.id] = kind
                    changed = True
        if not changed:
            break
    return kinds


def _has_main_guard(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
            continue
        test = node.test
        operands = [test.left, *test.comparators]
        if any(isinstance(item, ast.Name) and item.id == "__name__" for item in operands) and any(
            isinstance(item, ast.Constant) and item.value == "__main__" for item in operands
        ):
            return True
    return False


def _is_type_checking_guard(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Name)
        and node.id == "TYPE_CHECKING"
    ) or (
        isinstance(node, ast.Attribute)
        and node.attr == "TYPE_CHECKING"
        and isinstance(node.value, ast.Name)
        and node.value.id == "typing"
    )


def _runtime_relative_imports(tree: ast.AST) -> tuple[ast.ImportFrom, ...]:
    """TYPE_CHECKING の真側を除く、実行されうる相対 import を返す。"""
    found: list[ast.ImportFrom] = []

    class Visitor(ast.NodeVisitor):
        def visit_If(self, node: ast.If) -> None:
            if _is_type_checking_guard(node.test):
                for statement in node.orelse:
                    self.visit(statement)
                return
            self.generic_visit(node)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            if node.level > 0:
                found.append(node)

    Visitor().visit(tree)
    return tuple(found)


def _has_relative_import(tree: ast.AST) -> bool:
    return bool(_runtime_relative_imports(tree))


def _direct_bootstrap_nodes(tree: ast.Module, source: str) -> list[ast.stmt]:
    """module 直下にある逐語 bootstrap の実文だけを返す。"""
    return [
        node
        for node in tree.body
        if ast.get_source_segment(source, node) == DIRECT_BOOTSTRAP
    ]


def scan_campaign_shape(
    path: str,
    source: str,
    *,
    tree: ast.AST | None = None,
) -> tuple[Violation, ...]:
    """R-B: campaign package の sys.path と direct CLI bootstrap を検査する。"""
    tree = ast.parse(source, filename=path) if tree is None else tree
    assert isinstance(tree, ast.Module)
    found: set[Violation] = set()
    kinds = _path_kinds(tree)
    for node in ast.walk(tree):
        values: list[ast.AST] = []
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and _is_sys_path(node.func.value)
            and node.func.attr in {"insert", "append", "extend"}
        ):
            values = node.args[1:] if node.func.attr == "insert" else node.args
        elif (
            isinstance(node, ast.Call)
            and _is_site_addsitedir(node.func)
        ):
            values = node.args
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(
                (
                    isinstance(target, ast.Subscript)
                    and _is_sys_path(target.value)
                )
                or _is_pythonpath_target(target)
                for target in targets
            ):
                values = [node.value] if node.value is not None else []
        for value in values:
            candidates = value.elts if isinstance(value, (ast.List, ast.Tuple)) else [value]
            if any(
                _path_expression_kind(item, kinds) == _SYMBOLIC_ORCHESTRATOR
                for item in candidates
            ):
                matched = ast.get_source_segment(source, node) or "sys.path mutation"
                found.add(_violation(path, node.lineno, PATH_RULE, matched))

    if _has_main_guard(tree) and _has_relative_import(tree):
        bootstrap_nodes = _direct_bootstrap_nodes(tree, source)
        relative_import_lines = [node.lineno for node in _runtime_relative_imports(tree)]
        valid_bootstrap = (
            len(bootstrap_nodes) == 1
            and source.count(DIRECT_BOOTSTRAP) == 1
            and bootstrap_nodes[0].lineno < min(relative_import_lines)
        )
        if not valid_bootstrap:
            found.add(
                _violation(
                    path,
                    1,
                    BOOTSTRAP_RULE,
                    "direct CLI bootstrap is not one top-level statement before relative imports",
                )
            )
    return tuple(sorted(found))


def scan_current_doc(path: str, source: str) -> tuple[Violation, ...]:
    """R-C: 現行運用 doc の legacy ``-m`` 起動形を検出する。"""
    return tuple(
        _violation(
            path,
            1 + source.count("\n", 0, match.start()),
            DOCS_RULE,
            match.group(1),
        )
        for match in _MODULE_ARG_RE.finditer(source)
    )


def scan_campaign_relative_imports(
    path: str,
    source: str,
    *,
    tree: ast.AST | None = None,
) -> tuple[Violation, ...]:
    """R-D: campaign package 内の canonical absolute sibling import を検出する。"""
    tree = ast.parse(source, filename=path) if tree is None else tree
    found: set[Violation] = set()
    canonical = "orchestrator.campaign"
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module is not None:
            modules = [node.module]
        else:
            continue
        for module in modules:
            if module == canonical or module.startswith(canonical + "."):
                found.add(_violation(path, node.lineno, RELATIVE_RULE, module))
    return tuple(sorted(found))


def _excluded(relative: Path) -> bool:
    parts = relative.parts
    if parts and parts[0] == "external":
        return True
    return any(parts[index : index + 2] == (".claude", "worktrees") for index in range(len(parts) - 1))


def _is_current_doc(relative: Path) -> bool:
    if len(relative.parts) < 2 or relative.parts[0] != "docs" or relative.suffix != ".md":
        return False
    if relative.parts[1] == "archive":
        return False
    return relative.name not in {"decisions.md", "failures.md", "worklog.md"}


def scan_repository(root: Path) -> RepositoryScan:
    """列挙 1 回・選択した各 file の全内容読取 1 回で全規則を評価する。

    gitignore された未追跡 source は ``list_tracked_and_untracked_files`` の契約上対象外。
    """
    relative_paths = repo_tree_util.list_tracked_and_untracked_files(root)
    operational = {
        path.as_posix()
        for path in relative_paths
        if not _excluded(path) and path.suffix in {".py", ".sh", ".bash"}
    }
    docs = {
        path.as_posix()
        for path in relative_paths
        if not _excluded(path) and _is_current_doc(path)
    }
    sources = {
        path: (root / path).read_bytes().decode("utf-8", "surrogateescape")
        for path in operational | docs
    }
    for relative in relative_paths:
        if _excluded(relative) or relative.suffix:
            continue
        absolute = root / relative
        if not absolute.is_file() or not os.access(absolute, os.X_OK):
            continue
        with absolute.open("rb") as candidate:
            if candidate.read(2) != b"#!":
                continue
        source = absolute.read_bytes().decode("utf-8", "surrogateescape")
        path = relative.as_posix()
        operational.add(path)
        sources[path] = source

    violations: list[Violation] = []
    for path in operational:
        source = sources[path]
        tree = ast.parse(source, filename=path) if path.endswith(".py") else None
        violations.extend(scan_legacy_namespace(path, source, tree=tree))
        if path.startswith("orchestrator/campaign/") and path.endswith(".py"):
            assert tree is not None
            violations.extend(scan_campaign_shape(path, source, tree=tree))
            violations.extend(scan_campaign_relative_imports(path, source, tree=tree))
    for path in docs:
        violations.extend(scan_current_doc(path, sources[path]))
    return RepositoryScan(
        operational_paths=frozenset(operational),
        sources=sources,
        violations=tuple(sorted(set(violations))),
    )


def _assert_ledger_matches(
    actual: tuple[Violation, ...],
    expected: tuple[ImportException, ...],
) -> None:
    actual_set = {(item.path, item.line, item.rule, item.matched_text) for item in actual}
    expected_set = {item.key() for item in expected}
    assert actual_set == expected_set, (
        f"unlisted={sorted(actual_set - expected_set)!r} "
        f"stale={sorted(expected_set - actual_set)!r}"
    )


def _assert_rule_ledger_matches(repository_scan: RepositoryScan, rule: str) -> None:
    actual = tuple(item for item in repository_scan.violations if item.rule == rule)
    expected = tuple(item for item in KNOWN_EXCEPTIONS if item.rule == rule)
    _assert_ledger_matches(actual, expected)


@pytest.fixture(scope="session")
def repository_scan() -> RepositoryScan:
    return scan_repository(REPOSITORY)


def test_repository_scan_set_is_nonempty_and_contains_sentinels(repository_scan: RepositoryScan):
    assert repository_scan.operational_paths, "operational source の走査数が 0"
    assert SENTINELS <= repository_scan.operational_paths
    assert any(path.endswith(".sh") for path in repository_scan.operational_paths)
    assert any(
        path.startswith("orchestrator/campaign/") and path.endswith(".py")
        for path in repository_scan.operational_paths
    )
    assert any(_is_current_doc(Path(path)) for path in repository_scan.sources)

    listed = repo_tree_util.list_tracked_and_untracked_files(REPOSITORY)
    extensionless_executables = {
        relative.as_posix()
        for relative in listed
        if (
            not _excluded(relative)
            and not relative.suffix
            and (REPOSITORY / relative).is_file()
            and os.access(REPOSITORY / relative, os.X_OK)
            and (REPOSITORY / relative).read_bytes().startswith(b"#!")
        )
    }
    if extensionless_executables:
        assert extensionless_executables <= repository_scan.operational_paths


def test_synthetic_repository_wires_every_rule_and_source_kind_end_to_end():
    files = {
        "src/legacy.py": f"import {_legacy_module('legacy_rule')}\n",
        "scripts/check.sh": (
            "python3 -c 'import importlib; "
            f'importlib.import_module("{_legacy_module("shell_rule")}")\'\n'
        ),
        "scripts/check.bash": f"python3 -m {_legacy_module('bash_rule')}\n",
        "scripts/check": (
            f"#!/bin/sh\npython3 -m {_legacy_module('executable_rule')}\n"
        ),
        "orchestrator/campaign/path_probe.py": (
            "from pathlib import Path\n"
            "import sys\n"
            "sys.path.insert(0, str(Path(__file__).resolve().parents[1]))\n"
        ),
        "orchestrator/campaign/bootstrap_probe.py": (
            "from . import ident\n"
            'if __name__ == "__main__":\n'
            "    raise SystemExit(0)\n"
        ),
        "orchestrator/campaign/relative_probe.py": (
            "from orchestrator.campaign import ident\n"
        ),
        "docs/guide.md": f"python3 -m {_legacy_module('docs_rule')}\n",
    }
    with tempfile.TemporaryDirectory(prefix="campaign-import-invariant-") as temporary:
        root = Path(temporary)
        for relative, source in files.items():
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source, encoding="utf-8")
        (root / "scripts/check").chmod(0o755)
        subprocess.run(
            ["git", "init", "-q"],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        subprocess.run(
            ["git", "add", "."],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

        actual = scan_repository(root)

    expected = (
        _violation("docs/guide.md", 1, DOCS_RULE, _legacy_module("docs_rule")),
        _violation(
            "orchestrator/campaign/bootstrap_probe.py",
            1,
            BOOTSTRAP_RULE,
            "direct CLI bootstrap is not one top-level statement before relative imports",
        ),
        _violation(
            "orchestrator/campaign/path_probe.py",
            3,
            PATH_RULE,
            "sys.path.insert(0, str(Path(__file__).resolve().parents[1]))",
        ),
        _violation(
            "orchestrator/campaign/relative_probe.py",
            1,
            RELATIVE_RULE,
            "orchestrator.campaign",
        ),
        _violation(
            "scripts/check", 2, LEGACY_RULE, _legacy_module("executable_rule")
        ),
        _violation("scripts/check.bash", 1, LEGACY_RULE, _legacy_module("bash_rule")),
        _violation("scripts/check.sh", 1, LEGACY_RULE, _legacy_module("shell_rule")),
        _violation("src/legacy.py", 1, LEGACY_RULE, _legacy_module("legacy_rule")),
    )
    assert actual.violations == tuple(sorted(expected))
    assert {
        "src/legacy.py",
        "scripts/check.sh",
        "scripts/check.bash",
        "scripts/check",
        "orchestrator/campaign/path_probe.py",
        "orchestrator/campaign/bootstrap_probe.py",
        "orchestrator/campaign/relative_probe.py",
    } <= actual.operational_paths
    assert "docs/guide.md" in actual.sources


def test_real_repository_legacy_namespace_matches_exception_ledger(repository_scan: RepositoryScan):
    _assert_rule_ledger_matches(repository_scan, LEGACY_RULE)


def test_real_campaign_package_has_canonical_direct_bootstrap(repository_scan: RepositoryScan):
    for rule in (PATH_RULE, BOOTSTRAP_RULE):
        _assert_rule_ledger_matches(repository_scan, rule)


def test_real_current_docs_have_no_legacy_module_command(repository_scan: RepositoryScan):
    _assert_rule_ledger_matches(repository_scan, DOCS_RULE)


def test_real_campaign_package_uses_relative_sibling_imports(repository_scan: RepositoryScan):
    _assert_rule_ledger_matches(repository_scan, RELATIVE_RULE)


def test_known_exception_ledger_is_unique_rationalized_and_commented(repository_scan: RepositoryScan):
    assert len(KNOWN_EXCEPTIONS) == EXPECTED_EXCEPTION_COUNT
    rule_counts = {
        rule: sum(item.rule == rule for item in KNOWN_EXCEPTIONS)
        for rule in KNOWN_RULES
    }
    for rule, minimum in MINIMUM_RULE_EXCEPTION_COUNTS.items():
        assert rule_counts[rule] >= minimum

    keys = [item.key() for item in KNOWN_EXCEPTIONS]
    assert len(keys) == len(set(keys))
    ledger_rules = {item.rule for item in KNOWN_EXCEPTIONS}
    unknown_rules = ledger_rules - KNOWN_RULES
    assert not unknown_rules, f"unknown ledger rules={sorted(unknown_rules)!r}"
    for item in KNOWN_EXCEPTIONS:
        assert item.rationale.strip()
        assert _RATIONALE_RE.search(item.rationale)

    source = repository_scan.sources["orchestrator/tests/test_campaign_import_invariant.py"]
    tree = ast.parse(source)
    ledger = next(
        node for node in tree.body
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "KNOWN_EXCEPTIONS" for target in node.targets)
        )
        or (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "KNOWN_EXCEPTIONS"
        )
    )
    entry_lines = {
        node.lineno
        for node in ast.walk(ledger)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "ImportException"
    }
    comments = {
        token.start[0]: token.string
        for token in tokenize.generate_tokens(io.StringIO(source).readline)
        if token.type == tokenize.COMMENT
    }
    assert all(comments.get(line - 1, "").lstrip().startswith("# 根拠:") for line in entry_lines)
    assert len(entry_lines) == len(KNOWN_EXCEPTIONS)


@pytest.mark.parametrize(
    ("case", "source", "module"),
    [
        (
            "plain-from-import",
            f"from {_legacy_module('env_contract')} import AuthorizedContract\n",
            _legacy_module("env_contract"),
        ),
        (
            "arbitrary-callable",
            f'importer("{_legacy_module("env_attestation")}")\n',
            _legacy_module("env_attestation"),
        ),
        (
            "shell-heredoc",
            "python3 - <<'PY'\n"
            f"from {_legacy_module('profiler_directive')} import x\n"
            "PY\n",
            _legacy_module("profiler_directive"),
        ),
        (
            "subprocess-module-argv",
            f'argv = ["python3", "-m", "{_legacy_module("p3_s4_loop")}"]\n',
            _legacy_module("p3_s4_loop"),
        ),
        (
            "shell-python-c",
            "python3 -c 'import importlib; importlib.import_module(\""
            f"{_legacy_module('env_attestation')}"
            "\")'\n",
            _legacy_module("env_attestation"),
        ),
        (
            "str-join",
            'import importlib\nimportlib.import_module(".".join(("'
            f"{_legacy_module()}"
            '", "env_contract")))\n',
            _legacy_module("env_contract"),
        ),
    ],
    ids=[
        "plain-from-import",
        "arbitrary-callable",
        "shell-heredoc",
        "subprocess-module-argv",
        "shell-python-c",
        "str-join",
    ],
)
def test_r_a_positive_controls(case: str, source: str, module: str):
    suffix = ".sh" if case in {"shell-heredoc", "shell-python-c"} else ".py"
    violations = scan_legacy_namespace(f"synthetic/control{suffix}", source)
    assert any(item.matched_text == module for item in violations)
    if case == "shell-python-c":
        assert any(
            item.matched_text == module
            for item in scan_legacy_namespace("synthetic/control.bash", source)
        )
        assert any(
            item.matched_text == module
            for item in scan_legacy_namespace("synthetic/control", "#!/bin/bash\n" + source)
        )


def test_r_b_positive_control_rejects_wrong_direct_bootstrap():
    missing_bootstrap = '''from . import ident
if __name__ == "__main__":
    raise SystemExit(0)
'''
    malformed_bootstrap = DIRECT_BOOTSTRAP.replace(
        "direct CLI execution", "direct execution"
    ) + '''

from . import ident

if __name__ == "__main__":
    raise SystemExit(0)
'''
    wrong_path = '''from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from . import ident
if __name__ == "__main__":
    raise SystemExit(0)
'''
    no_relative_import = '''if __name__ == "__main__":
    raise SystemExit(0)
'''
    fake_bootstrap = '''from . import ident
_FAKE = ''' + repr(DIRECT_BOOTSTRAP) + '''
if __name__ == "__main__":
    raise SystemExit(0)
'''
    late_bootstrap = '''from . import ident
''' + DIRECT_BOOTSTRAP + '''
if __name__ == "__main__":
    raise SystemExit(0)
'''
    addsitedir_path = '''from pathlib import Path
import site
site.addsitedir(str(Path(__file__).resolve().parents[1]))
'''
    pythonpath_assignment = '''from pathlib import Path
import os
os.environ["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
'''

    path = "orchestrator/campaign/control.py"
    assert {item.rule for item in scan_campaign_shape(path, missing_bootstrap)} == {BOOTSTRAP_RULE}
    assert {item.rule for item in scan_campaign_shape(path, malformed_bootstrap)} == {BOOTSTRAP_RULE}
    assert {item.rule for item in scan_campaign_shape(path, wrong_path)} == {
        PATH_RULE,
        BOOTSTRAP_RULE,
    }
    assert {item.rule for item in scan_campaign_shape(path, fake_bootstrap)} == {BOOTSTRAP_RULE}
    assert {item.rule for item in scan_campaign_shape(path, late_bootstrap)} == {BOOTSTRAP_RULE}
    assert {item.rule for item in scan_campaign_shape(path, addsitedir_path)} == {PATH_RULE}
    assert {item.rule for item in scan_campaign_shape(path, pythonpath_assignment)} == {PATH_RULE}
    assert scan_campaign_shape(path, no_relative_import) == ()


def test_r_b_os_path_and_pathlib_depth_controls():
    os_path_nested = '''import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
'''
    os_path_join = '''import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
'''
    pathlib_orchestrator = '''import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
'''
    pathlib_repository = '''import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
'''
    join_repository_to_orchestrator = '''import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), "orchestrator"))
'''
    join_orchestrator_to_repository = '''import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), ".."))
'''
    join_unresolved_suffix = '''import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), suffix))
'''

    source_file = REPOSITORY / "orchestrator/campaign/x.py"
    os_path_result = os.path.dirname(os.path.dirname(os.path.abspath(source_file)))
    assert Path(os_path_result) == REPOSITORY / "orchestrator"

    path = "orchestrator/campaign/x.py"
    for source in (os_path_nested, os_path_join, pathlib_orchestrator):
        violations = scan_campaign_shape(path, source)
        assert len(violations) == 1
        assert [item.rule for item in violations] == [PATH_RULE]
    assert scan_campaign_shape(path, pathlib_repository) == ()
    assert [
        item.rule
        for item in scan_campaign_shape(path, join_repository_to_orchestrator)
    ] == [PATH_RULE]
    assert scan_campaign_shape(path, join_orchestrator_to_repository) == ()
    assert scan_campaign_shape(path, join_unresolved_suffix) == ()


def test_r_c_positive_control_rejects_legacy_doc_command():
    source = f"python3 -m {_legacy_module('p3_s4_loop')} --help\n"
    violations = scan_current_doc("docs/control.md", source)
    assert [item.matched_text for item in violations] == [_legacy_module("p3_s4_loop")]


def test_r_d_positive_control_rejects_absolute_sibling_import():
    source = "from orchestrator.campaign.ident import CampaignIdent\n"
    violations = scan_campaign_relative_imports("orchestrator/campaign/control.py", source)
    assert [item.matched_text for item in violations] == ["orchestrator.campaign.ident"]


def test_canonical_negative_controls_have_no_violations():
    canonical_source = "from orchestrator.campaign import ident\n"
    relative_source = "from .ident import CampaignIdent\n"
    direct_source = DIRECT_BOOTSTRAP + '''

from .ident import CampaignIdent

if __name__ == "__main__":
    raise SystemExit(0)
'''
    assert scan_legacy_namespace("tools/control.py", canonical_source) == ()
    assert scan_legacy_namespace("tools/control.py", 'assert "campaign.lock と不一致" in message\n') == ()
    assert scan_legacy_namespace("tools/control.py", "from campaign_lock_test_support import build_v2_lock\n") == ()
    shell_non_modules = '''LOCK_PATH="$TMPDIR/campaign.lock"
echo ok  # campaign.layout is a historical name
echo /campaign.layout $campaign.layout
'''
    assert scan_legacy_namespace("tools/control.sh", shell_non_modules) == ()
    quoted_hash = (
        f'''python3 -c 'print("#"); import_module("{_legacy_module("env_contract")}")'\n'''
    )
    assert [
        item.matched_text
        for item in scan_legacy_namespace("tools/control.sh", quoted_hash)
    ] == [_legacy_module("env_contract")]
    assert scan_campaign_shape("orchestrator/campaign/control.py", direct_source) == ()
    assert scan_current_doc("docs/control.md", "python3 -m orchestrator.campaign.ident\n") == ()
    assert scan_campaign_relative_imports("orchestrator/campaign/control.py", relative_source) == ()


def test_static_join_does_not_use_ambiguous_or_cross_scope_names():
    unique = '''import importlib
root = "campaign"
importlib.import_module(".".join((root, "env_contract")))
'''
    reassigned = '''import importlib
import os
root = "campaign"
root = os.environ["RUNTIME_PACKAGE"]
importlib.import_module(".".join((root, "env_contract")))
'''
    cross_scope = '''import importlib
import os
root = "campaign"
def load():
    root = os.environ["RUNTIME_PACKAGE"]
    return importlib.import_module(".".join((root, "env_contract")))
'''
    assert [
        item.matched_text
        for item in scan_legacy_namespace("tools/unique.py", unique)
    ] == [_legacy_module("env_contract")]
    assert scan_legacy_namespace("tools/reassigned.py", reassigned) == ()
    assert scan_legacy_namespace("tools/cross_scope.py", cross_scope) == ()


def test_type_checking_relative_import_does_not_require_bootstrap():
    source = '''from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .model import CampaignConfig

if __name__ == "__main__":
    raise SystemExit(0)
'''
    assert scan_campaign_shape("orchestrator/campaign/type_only.py", source) == ()


def test_exception_ledger_comparison_rejects_stale_entry():
    stale = ImportException(
        path="synthetic.py",
        line=1,
        rule=LEGACY_RULE,
        matched_text=_legacy_module("stale"),
        rationale="T-720: stale control",
    )
    with pytest.raises(AssertionError, match="stale"):
        _assert_ledger_matches((), (stale,))


def test_exception_ledger_comparison_rejects_empty_ledger_with_real_violation():
    source = '''import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
'''
    actual = scan_campaign_shape("orchestrator/campaign/x.py", source)
    assert len(actual) == 1
    assert actual[0].rule == PATH_RULE
    with pytest.raises(AssertionError, match="unlisted"):
        _assert_ledger_matches(actual, ())


def _run() -> int:
    fns = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    scan_value: RepositoryScan | None = None
    scan_error: Exception | None = None
    try:
        scan_value = scan_repository(REPOSITORY)
    except Exception as exc:  # noqa: BLE001 - fixture failure is reported per consumer
        scan_error = exc

    passed = failed = skipped = 0
    for fn in fns:
        if fn is test_r_a_positive_controls:
            invocations = [
                (case, (case, source, module))
                for case, source, module in fn.pytestmark[0].args[1]
            ]
        elif "repository_scan" in inspect.signature(fn).parameters:
            invocations = [(fn.__name__, (scan_value,))]
        else:
            invocations = [(fn.__name__, ())]

        for label, args in invocations:
            try:
                if "repository_scan" in inspect.signature(fn).parameters and scan_error is not None:
                    raise scan_error
                fn(*args)
                print(f"PASS {fn.__name__}[{label}]")
                passed += 1
            except Skip as exc:
                print(f"SKIP {fn.__name__}[{label}]: {exc}")
                skipped += 1
            except AssertionError as exc:
                print(f"FAIL {fn.__name__}[{label}]: {exc}")
                failed += 1
            except Exception as exc:  # noqa: BLE001
                print(f"ERROR {fn.__name__}[{label}]: {type(exc).__name__}: {exc}")
                failed += 1
    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
