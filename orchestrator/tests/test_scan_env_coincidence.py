"""Tests for the literal environment-coincidence scanner."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.scan_env_coincidence import (  # noqa: E402
    SCHEMA,
    ScanError,
    main,
    scan_file,
    scan_root,
)


def _write_source(root: Path, name: str, source: str) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return path


def _projection(rows: list[dict[str, object]]) -> list[tuple[object, ...]]:
    return [
        (
            row["scan_index"],
            row["file"],
            row["line"],
            row["argument_line"],
            row["kind"],
            row["bound"],
            row["predicate"],
        )
        for row in rows
    ]


def test_p1_matches_exact_calls_and_keeps_same_line_occurrences(
    tmp_path: Path,
) -> None:
    """Kill: in visit_Call remove positional wait or generic timeout, or deduplicate by line."""
    source = (
        "thread.join(1); event.wait(2.5); arbitrary(timeout=3); other.sleep(4)\n"
    )
    path = _write_source(tmp_path, "fixture.py", source)

    rows = scan_file(path, "fixture.py", "P1")

    assert _projection(rows) == [
        (0, "fixture.py", 1, 1, "join(positional)", 1, "P1"),
        (1, "fixture.py", 1, 1, "wait(positional)", 2.5, "P1"),
        (2, "fixture.py", 1, 1, "timeout=", 3, "P1"),
    ]


def test_p2_is_strict_extension_and_preserves_origin_predicate(
    tmp_path: Path,
) -> None:
    """Kill: in visit_Call reject join only under P2, or omit or relabel a P2 keyword."""
    source = (
        "configure(timeout=1, deadline_s=2, termination_grace_s=3)\n"
        "thread.join(4)\n"
    )
    path = _write_source(tmp_path, "fixture.py", source)

    p1_rows = scan_file(path, "fixture.py", "P1")
    p2_rows = scan_file(path, "fixture.py", "P2")

    assert _projection(p1_rows) == [
        (0, "fixture.py", 1, 1, "timeout=", 1, "P1"),
        (1, "fixture.py", 2, 2, "join(positional)", 4, "P1"),
    ]
    assert _projection(p2_rows) == [
        (0, "fixture.py", 1, 1, "timeout=", 1, "P1"),
        (1, "fixture.py", 1, 1, "deadline_s=", 2, "P2"),
        (2, "fixture.py", 1, 1, "termination_grace_s=", 3, "P2"),
        (3, "fixture.py", 2, 2, "join(positional)", 4, "P1"),
    ]


def test_multiline_uses_call_line_and_nested_calls_stay_distinct(
    tmp_path: Path,
) -> None:
    """Kill: in _append use argument.lineno, or in visit_Call omit generic_visit."""
    source = (
        "runner(\n"
        "    timeout=6,\n"
        ")\n"
        "outer(inner.wait(4), timeout=5)\n"
    )
    path = _write_source(tmp_path, "fixture.py", source)

    rows = scan_file(path, "fixture.py", "P2")

    assert _projection(rows) == [
        (0, "fixture.py", 1, 2, "timeout=", 6, "P1"),
        (1, "fixture.py", 4, 4, "timeout=", 5, "P1"),
        (2, "fixture.py", 4, 4, "wait(positional)", 4, "P1"),
    ]


def test_bool_literals_are_not_numeric_bounds(tmp_path: Path) -> None:
    """Kill: in _numeric_literal replace exact types with isinstance against int and float."""
    source = (
        "target.join(True); target.wait(False); "
        "run(timeout=True, deadline_s=False, termination_grace_s=True); "
        "sentinel.wait(7)\n"
    )
    path = _write_source(tmp_path, "fixture.py", source)

    rows = scan_file(path, "fixture.py", "P2")

    assert _projection(rows) == [
        (0, "fixture.py", 1, 1, "wait(positional)", 7, "P1"),
    ]


_BLIND_SPOT_CASES = (
    (
        "symbolic-constant",
        "LIMIT = 120\nrun(timeout=LIMIT)\nthread.join(LIMIT)\nsentinel.wait(7)\n",
        4,
    ),
    (
        "execution-order",
        "assert callbacks.index('first') < callbacks.index('second')\n"
        "assert callbacks == ['first', 'second']\nsentinel.wait(7)\n",
        3,
    ),
    (
        "identifier-reuse",
        "assert fd == 7\nassert inode != 4\nassert pid == 3\nsentinel.wait(7)\n",
        4,
    ),
    (
        "ambient-state",
        "assert len(os.listdir('/proc/self/fd')) == 3\n"
        "assert len(os.listdir('/tmp')) < 20\nsentinel.wait(7)\n",
        3,
    ),
    (
        "alias-binding",
        "LIMIT = 1\nthread.join(LIMIT)\nrun(**{'timeout': 1})\n"
        "getattr(thread, 'join')(1)\nsentinel.wait(7)\n",
        5,
    ),
)


@pytest.mark.parametrize(
    ("case_name", "source", "sentinel_line"),
    _BLIND_SPOT_CASES,
    ids=[case[0] for case in _BLIND_SPOT_CASES],
)
def test_documented_blind_spots_are_p2_scope_freeze_guards(
    tmp_path: Path,
    case_name: str,
    source: str,
    sentinel_line: int,
) -> None:
    """P2 scope-freeze soundness guard, not a detection guard.

    Kill: add _MatchVisitor handling that emits a row for this excluded AST form.
    """
    path = _write_source(tmp_path, f"{case_name}.py", source)

    rows = scan_file(path, f"{case_name}.py", "P2")

    assert _projection(rows) == [
        (
            0,
            f"{case_name}.py",
            sentinel_line,
            sentinel_line,
            "wait(positional)",
            7,
            "P1",
        ),
    ]


def test_test_module_is_scanner_pure() -> None:
    """Kill: in visit_Call drop the join/wait name guard so sys.path.insert becomes a row."""
    assert scan_file(Path(__file__), Path(__file__).name, "P2") == []


def test_main_emits_deterministic_document_for_direct_python_children(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Kill: in scan_root deduplicate by (file, line), use rglob, or stop sorting."""
    _write_source(tmp_path, "b.py", "beta.wait(3)\n")
    _write_source(tmp_path, "a.py", "alpha(timeout=2, deadline_s=4)\n")
    _write_source(tmp_path, "nested/c.py", "hidden.join(4)\n")

    status = main(["--root", str(tmp_path), "--predicate", "P2"])
    captured = capsys.readouterr()

    assert status == 0
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "schema": SCHEMA,
        "root": tmp_path.as_posix(),
        "predicate": "P2",
        "source_file_count": 2,
        "matched_file_count": 2,
        "row_count": 3,
        "rows": [
            {
                "scan_index": 0,
                "file": "a.py",
                "line": 1,
                "column": 0,
                "argument_line": 1,
                "kind": "timeout=",
                "bound": 2,
                "predicate": "P1",
            },
            {
                "scan_index": 1,
                "file": "a.py",
                "line": 1,
                "column": 0,
                "argument_line": 1,
                "kind": "deadline_s=",
                "bound": 4,
                "predicate": "P2",
            },
            {
                "scan_index": 2,
                "file": "b.py",
                "line": 1,
                "column": 0,
                "argument_line": 1,
                "kind": "wait(positional)",
                "bound": 3,
                "predicate": "P1",
            },
        ],
    }


def test_parse_failure_rejects_partial_root_result(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Kill: in scan_file catch SyntaxError and return empty rows for the broken file."""
    _write_source(tmp_path, "a_valid.py", "sentinel.wait(7)\n")
    broken_path = _write_source(tmp_path, "b_broken.py", "def broken(:\n")

    with pytest.raises(ScanError, match="b_broken[.]py"):
        scan_root(tmp_path, "P2")

    status = main(["--root", str(tmp_path), "--predicate", "P2"])
    captured = capsys.readouterr()
    assert status != 0
    assert captured.out == ""
    assert broken_path.name in captured.err


def _run() -> int:
    return int(pytest.main([__file__, "-q"]))


if __name__ == "__main__":
    sys.exit(_run())
