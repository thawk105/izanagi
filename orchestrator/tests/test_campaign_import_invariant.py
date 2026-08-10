# -*- coding: utf-8 -*-
"""campaign import 形を tracked + untracked の実 repository へ束縛する。"""
from __future__ import annotations

import ast
import io
import re
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path

import pytest

ORCHESTRATOR = Path(__file__).resolve().parents[1]
REPOSITORY = ORCHESTRATOR.parent
sys.path.insert(0, str(REPOSITORY))

from orchestrator.tests import repo_tree_util  # noqa: E402


LEGACY_RULE = "legacy-campaign-namespace"
PATH_RULE = "campaign-orchestrator-sys-path"
BOOTSTRAP_RULE = "campaign-direct-bootstrap"
DOCS_RULE = "legacy-campaign-doc-command"
RELATIVE_RULE = "campaign-absolute-sibling-import"

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
_RATIONALE_RE = re.compile(r"(?:D|F|T)-?\d+")


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
        line=4594,
        rule=LEGACY_RULE,
        matched_text=_legacy_module("lock"),
        rationale="T-720: campaign.lock という file 名を含む拒否文言の検査",
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


def _violation(path: str, line: int, rule: str, matched_text: str) -> Violation:
    return Violation(path=path, line=line, rule=rule, matched_text=matched_text)


def _static_string(node: ast.AST, names: dict[str, str]) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
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


def _static_names(tree: ast.AST) -> dict[str, str]:
    names: dict[str, str] = {}
    assignments = [node for node in ast.walk(tree) if isinstance(node, (ast.Assign, ast.AnnAssign))]
    # source 順の通常代入と 1 段の forward reference を覆い、巨大 source でも線形に保つ。
    for _ in range(2):
        changed = False
        for assignment in assignments:
            value_node = assignment.value
            if value_node is None:
                continue
            value = _static_string(value_node, names)
            if value is None:
                continue
            targets = assignment.targets if isinstance(assignment, ast.Assign) else [assignment.target]
            for target in targets:
                if isinstance(target, ast.Name) and names.get(target.id) != value:
                    names[target.id] = value
                    changed = True
        if not changed:
            break
    return names


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


def scan_legacy_namespace(
    path: str,
    source: str,
    *,
    tree: ast.AST | None = None,
) -> tuple[Violation, ...]:
    """R-A: module path literal と import 文から legacy namespace を検出する。"""
    found: set[Violation] = set()
    suffix = Path(path).suffix

    if suffix == ".sh":
        for line, module in _textual_legacy_hits(source):
            if not source.splitlines()[line - 1].lstrip().startswith("#"):
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

    names = _static_names(tree)
    for node in ast.walk(tree):
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
        if isinstance(node, (ast.Constant, ast.JoinedStr, ast.BinOp)):
            value = _static_string(node, names)
            if value is None:
                continue
            if (
                "." in value
                and not (
                    value == _legacy_module("lock")
                    or value.startswith(_legacy_module("lock") + ".")
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


def _path_expression_kind(node: ast.AST, kinds: dict[str, str]) -> str | None:
    if isinstance(node, ast.Name):
        return kinds.get(node.id)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        parts = Path(node.value).parts
        return "orchestrator" if parts and parts[-1] == "orchestrator" else None
    if isinstance(node, ast.Call) and node.args:
        return _path_expression_kind(node.args[0], kinds)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        right = _static_string(node.right, {})
        if right == "orchestrator":
            return "orchestrator"
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "parents"
        and isinstance(node.slice, ast.Constant)
        and node.slice.value == 1
    ):
        return "orchestrator"
    if isinstance(node, ast.Attribute) and node.attr == "parent":
        parent = node.value
        if isinstance(parent, ast.Attribute) and parent.attr == "parent":
            return "orchestrator"
    return None


def _path_kinds(tree: ast.AST) -> dict[str, str]:
    kinds: dict[str, str] = {}
    assignments = [node for node in ast.walk(tree) if isinstance(node, (ast.Assign, ast.AnnAssign))]
    for _ in range(2):
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


def _has_relative_import(tree: ast.AST) -> bool:
    return any(isinstance(node, ast.ImportFrom) and node.level > 0 for node in ast.walk(tree))


def scan_campaign_shape(
    path: str,
    source: str,
    *,
    tree: ast.AST | None = None,
) -> tuple[Violation, ...]:
    """R-B: campaign package の sys.path と direct CLI bootstrap を検査する。"""
    tree = ast.parse(source, filename=path) if tree is None else tree
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
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Subscript) and _is_sys_path(target.value) for target in targets):
                values = [node.value] if node.value is not None else []
        for value in values:
            candidates = value.elts if isinstance(value, (ast.List, ast.Tuple)) else [value]
            if any(_path_expression_kind(item, kinds) == "orchestrator" for item in candidates):
                matched = ast.get_source_segment(source, node) or "sys.path mutation"
                found.add(_violation(path, node.lineno, PATH_RULE, matched))

    if _has_main_guard(tree) and _has_relative_import(tree) and source.count(DIRECT_BOOTSTRAP) != 1:
        found.add(_violation(path, 1, BOOTSTRAP_RULE, "direct CLI bootstrap count != 1"))
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
    """列挙 1 回・各 file 読取 1 回で実 repository の全規則を評価する。"""
    relative_paths = repo_tree_util.list_tracked_and_untracked_files(root)
    operational = {
        path.as_posix()
        for path in relative_paths
        if not _excluded(path) and path.suffix in {".py", ".sh"}
    }
    docs = {
        path.as_posix()
        for path in relative_paths
        if not _excluded(path) and _is_current_doc(path)
    }
    selected = operational | docs
    sources = {
        path: (root / path).read_bytes().decode("utf-8", "surrogateescape")
        for path in selected
    }

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


@pytest.fixture(scope="module")
def repository_scan() -> RepositoryScan:
    return scan_repository(REPOSITORY)


def test_repository_scan_set_is_nonempty_and_contains_sentinels(repository_scan: RepositoryScan):
    assert repository_scan.operational_paths, "operational source の走査数が 0"
    assert SENTINELS <= repository_scan.operational_paths


def test_real_repository_legacy_namespace_matches_exception_ledger(repository_scan: RepositoryScan):
    legacy = tuple(item for item in repository_scan.violations if item.rule == LEGACY_RULE)
    _assert_ledger_matches(legacy, KNOWN_EXCEPTIONS)


def test_real_campaign_package_has_canonical_direct_bootstrap(repository_scan: RepositoryScan):
    violations = tuple(
        item for item in repository_scan.violations if item.rule in {PATH_RULE, BOOTSTRAP_RULE}
    )
    assert not violations, violations


def test_real_current_docs_have_no_legacy_module_command(repository_scan: RepositoryScan):
    violations = tuple(item for item in repository_scan.violations if item.rule == DOCS_RULE)
    assert not violations, violations


def test_real_campaign_package_uses_relative_sibling_imports(repository_scan: RepositoryScan):
    violations = tuple(item for item in repository_scan.violations if item.rule == RELATIVE_RULE)
    assert not violations, violations


def test_known_exception_ledger_is_unique_rationalized_and_commented(repository_scan: RepositoryScan):
    keys = [item.key() for item in KNOWN_EXCEPTIONS]
    assert len(keys) == len(set(keys))
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
    ],
    ids=[
        "plain-from-import",
        "arbitrary-callable",
        "shell-heredoc",
        "subprocess-module-argv",
    ],
)
def test_r_a_positive_controls(case: str, source: str, module: str):
    suffix = ".sh" if case == "shell-heredoc" else ".py"
    violations = scan_legacy_namespace(f"synthetic/control{suffix}", source)
    assert any(item.matched_text == module for item in violations)


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

    path = "orchestrator/campaign/control.py"
    assert {item.rule for item in scan_campaign_shape(path, missing_bootstrap)} == {BOOTSTRAP_RULE}
    assert {item.rule for item in scan_campaign_shape(path, malformed_bootstrap)} == {BOOTSTRAP_RULE}
    assert {item.rule for item in scan_campaign_shape(path, wrong_path)} == {
        PATH_RULE,
        BOOTSTRAP_RULE,
    }
    assert scan_campaign_shape(path, no_relative_import) == ()


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
    assert scan_campaign_shape("orchestrator/campaign/control.py", direct_source) == ()
    assert scan_current_doc("docs/control.md", "python3 -m orchestrator.campaign.ident\n") == ()
    assert scan_campaign_relative_imports("orchestrator/campaign/control.py", relative_source) == ()


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
