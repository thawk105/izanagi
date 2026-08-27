#!/usr/bin/env python3
"""Scan direct Python children for literal environment-coincidence bounds."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any, Sequence


SCHEMA = "izanagi-env-coincidence-scan/v1"
PREDICATES = ("P1", "P2")
_P1_KEYWORDS = frozenset({"timeout"})
_P2_KEYWORDS = frozenset({"deadline_s", "termination_grace_s"})
_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_ROOT = _REPO_ROOT / "orchestrator" / "tests"


class ScanError(RuntimeError):
    """Raised when a requested scan cannot be completed in full."""


@dataclass(frozen=True)
class _Match:
    line: int
    column: int
    argument_line: int
    kind: str
    bound: int | float
    predicate: str


def _numeric_literal(node: ast.AST) -> int | float | None:
    if not isinstance(node, ast.Constant):
        return None
    value = node.value
    if type(value) not in (int, float):
        return None
    return value


class _MatchVisitor(ast.NodeVisitor):
    def __init__(self, predicate: str) -> None:
        self._predicate = predicate
        self.matches: list[_Match] = []

    def _append(
        self,
        call: ast.Call,
        argument: ast.AST,
        kind: str,
        bound: int | float,
        predicate: str,
    ) -> None:
        self.matches.append(
            _Match(
                line=call.lineno,
                column=call.col_offset,
                argument_line=argument.lineno,
                kind=kind,
                bound=bound,
                predicate=predicate,
            )
        )

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in {"join", "wait"}
            and node.args
        ):
            bound = _numeric_literal(node.args[0])
            if bound is not None:
                self._append(
                    node,
                    node.args[0],
                    f"{node.func.attr}(positional)",
                    bound,
                    "P1",
                )

        for keyword in node.keywords:
            bound = _numeric_literal(keyword.value)
            if bound is None:
                continue
            if keyword.arg in _P1_KEYWORDS:
                self._append(node, keyword.value, "timeout=", bound, "P1")
            elif self._predicate == "P2" and keyword.arg in _P2_KEYWORDS:
                self._append(node, keyword.value, f"{keyword.arg}=", bound, "P2")

        self.generic_visit(node)


def _validate_predicate(predicate: str) -> None:
    if predicate not in PREDICATES:
        choices = ", ".join(PREDICATES)
        raise ScanError(f"unsupported predicate {predicate!r}; choose one of {choices}")


def scan_file(
    path: str | Path,
    relative_name: str | None = None,
    predicate: str = "P2",
) -> list[dict[str, Any]]:
    """Scan one UTF-8 Python file and return rows in AST traversal order."""

    _validate_predicate(predicate)
    source_path = Path(path)
    try:
        source = source_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ScanError(f"cannot read {source_path}: {exc}") from exc

    try:
        tree = ast.parse(source, filename=str(source_path))
    except SyntaxError as exc:
        location = f"{source_path}:{exc.lineno or 0}:{exc.offset or 0}"
        raise ScanError(f"cannot parse {location}: {exc.msg}") from exc

    visitor = _MatchVisitor(predicate)
    visitor.visit(tree)
    file_name = relative_name if relative_name is not None else source_path.name
    return [
        {
            "scan_index": index,
            "file": file_name,
            "line": match.line,
            "column": match.column,
            "argument_line": match.argument_line,
            "kind": match.kind,
            "bound": match.bound,
            "predicate": match.predicate,
        }
        for index, match in enumerate(visitor.matches)
    ]


def scan_root(root: str | Path, predicate: str = "P2") -> dict[str, Any]:
    """Scan only direct ``*.py`` children of root and build a v1 document."""

    _validate_predicate(predicate)
    root_path = Path(root)
    if not root_path.is_dir():
        raise ScanError(f"scan root is not a directory: {root_path}")

    source_paths = sorted(root_path.glob("*.py"), key=lambda path: path.name)
    rows: list[dict[str, Any]] = []
    matched_file_count = 0
    for source_path in source_paths:
        file_rows = scan_file(
            source_path,
            source_path.relative_to(root_path).as_posix(),
            predicate,
        )
        if file_rows:
            matched_file_count += 1
        for row in file_rows:
            row["scan_index"] = len(rows)
            rows.append(row)

    return {
        "schema": SCHEMA,
        "root": root_path.as_posix(),
        "predicate": predicate,
        "source_file_count": len(source_paths),
        "matched_file_count": matched_file_count,
        "row_count": len(rows),
        "rows": rows,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        help="directory whose direct *.py children are scanned",
    )
    parser.add_argument(
        "--predicate",
        choices=PREDICATES,
        default="P2",
        help="scan predicate (default: P2)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    root = args.root if args.root is not None else _DEFAULT_ROOT
    try:
        document = scan_root(root, args.predicate)
    except ScanError as exc:
        print(f"scan_env_coincidence: {exc}", file=sys.stderr)
        return 2

    if args.root is None:
        document["root"] = "orchestrator/tests"
    json.dump(document, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
