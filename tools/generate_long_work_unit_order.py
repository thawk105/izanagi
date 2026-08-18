#!/usr/bin/env python3
"""Generate a namespace-bearing long-work-unit declaration from JUnit XML.

The runtime never imports this module. It is a bounded maintenance tool: each
JUnit file must describe the same testcase collection, grouped testcase times
are summed per run, and the resulting units are sorted by mean duration.
"""

from __future__ import annotations

import argparse
import ast
import difflib
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from typing import Iterable


ScopeKey = tuple[str, str]


def _split_scope(nodeid: str) -> ScopeKey:
    if nodeid.rfind("@") > nodeid.rfind("]"):
        return "group", nodeid.split("@")[-1]
    return "nodeid", nodeid


def _normalize_path(value: str, repo_root: Path) -> str:
    candidate = Path(value.replace("\\", "/"))
    if candidate.is_absolute():
        try:
            candidate = candidate.resolve().relative_to(repo_root.resolve())
        except ValueError:
            candidate = Path(candidate.name)
    text = PurePosixPath(candidate.as_posix()).as_posix()
    while text.startswith("./"):
        text = text[2:]
    return text


def _path_from_classname(classname: str) -> str:
    text = classname.replace("\\", "/")
    if "/" not in text:
        text = text.replace(".", "/")
    if not text.endswith(".py"):
        text += ".py"
    return text


def _testcase_nodeid(testcase: ET.Element, repo_root: Path) -> str:
    attrs = testcase.attrib
    explicit = attrs.get("nodeid")
    if explicit:
        return explicit
    name = attrs.get("name")
    if not name:
        raise ValueError("JUnit testcase has no name")
    file_name = attrs.get("file")
    if file_name:
        path = _normalize_path(file_name, repo_root)
    else:
        classname = attrs.get("classname")
        if not classname:
            raise ValueError(
                "JUnit testcase needs either nodeid, file, or classname"
            )
        path = _path_from_classname(classname)
    return f"{path}::{name}"


def _testcase_time(testcase: ET.Element, source: Path) -> float:
    raw = testcase.attrib.get("time")
    if raw is None:
        raise ValueError(f"{source}: testcase has no time")
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{source}: invalid testcase time {raw!r}") from exc
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{source}: invalid testcase time {raw!r}")
    return value


def _read_run(path: Path, repo_root: Path) -> dict[str, float]:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        raise ValueError(f"cannot read JUnit XML {path}: {exc}") from exc

    testcase_times: dict[str, float] = {}
    unit_times: dict[ScopeKey, float] = {}
    for testcase in root.iter("testcase"):
        nodeid = _testcase_nodeid(testcase, repo_root)
        if nodeid in testcase_times:
            raise ValueError(f"{path}: duplicate testcase {nodeid!r}")
        duration = _testcase_time(testcase, path)
        testcase_times[nodeid] = duration
        unit = _split_scope(nodeid)
        unit_times[unit] = unit_times.get(unit, 0.0) + duration
    return {"\0".join(key): value for key, value in unit_times.items()} | {
        "__testcase__\0" + nodeid: duration
        for nodeid, duration in testcase_times.items()
    }


def _run_parts(run: dict[str, float]) -> tuple[dict[str, float], dict[str, float]]:
    units: dict[str, float] = {}
    testcases: dict[str, float] = {}
    for key, value in run.items():
        if key.startswith("__testcase__\0"):
            testcases[key[len("__testcase__\0"):]] = value
        else:
            units[key] = value
    return units, testcases


def generate_order(
    junit_paths: Iterable[Path],
    *,
    repo_root: Path,
    min_duration: float = 0.0,
    max_units: int | None = None,
) -> tuple[ScopeKey, ...]:
    """Return average-duration units in descending order."""
    paths = tuple(Path(path) for path in junit_paths)
    if not paths:
        raise ValueError("at least one JUnit XML is required")
    if min_duration < 0 or not math.isfinite(min_duration):
        raise ValueError("--min-duration must be a finite non-negative number")
    if max_units is not None and max_units <= 0:
        raise ValueError("--max-units must be positive")

    runs = [_read_run(path, repo_root) for path in paths]
    run_parts = [_run_parts(run) for run in runs]
    expected_testcases = set(run_parts[0][1])
    for path, (_, testcases) in zip(paths[1:], run_parts[1:]):
        if set(testcases) != expected_testcases:
            raise ValueError(f"{path}: testcase collection differs between JUnit runs")

    sums: dict[str, float] = {}
    for units, _ in run_parts:
        for key, value in units.items():
            sums[key] = sums.get(key, 0.0) + value
    averages = {
        key: value / len(run_parts)
        for key, value in sums.items()
    }
    ranked = []
    for encoded, average in averages.items():
        namespace, value = encoded.split("\0", 1)
        if average >= min_duration:
            ranked.append(((namespace, value), average))
    ranked.sort(key=lambda entry: (-entry[1], entry[0]))
    if max_units is not None:
        ranked = ranked[:max_units]
    return tuple(unit for unit, _ in ranked)


def format_declaration(order: Iterable[ScopeKey]) -> str:
    lines = ["LONG_WORK_UNIT_SCOPE_ORDER: tuple[tuple[str, str], ...] = ("]
    lines.extend(f"    ({namespace!r}, {key!r})," for namespace, key in order)
    lines.append(")")
    return "\n".join(lines) + "\n"


def _literal_declaration(path: Path) -> tuple[ScopeKey, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        else:
            continue
        if not any(
            isinstance(target, ast.Name)
            and target.id == "LONG_WORK_UNIT_SCOPE_ORDER"
            for target in targets
        ):
            continue
        literal = ast.literal_eval(value)
        return tuple((namespace, key) for namespace, key in literal)
    raise ValueError(f"{path}: LONG_WORK_UNIT_SCOPE_ORDER was not found")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--junit", action="append", type=Path, required=True,
        help="JUnit XML input; repeat for multiple runs",
    )
    parser.add_argument("--min-duration", type=float, default=0.0)
    parser.add_argument("--max-units", type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--check", action="store_true",
        help="compare the generated declaration with the existing conftest declaration",
    )
    parser.add_argument(
        "--existing", type=Path,
        help="declaration source for --check (default: orchestrator/tests/conftest.py)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    try:
        order = generate_order(
            args.junit,
            repo_root=repo_root,
            min_duration=args.min_duration,
            max_units=args.max_units,
        )
        rendered = format_declaration(order)
        if args.check:
            existing = args.existing or repo_root / "orchestrator/tests/conftest.py"
            actual = format_declaration(_literal_declaration(existing))
            if actual == rendered:
                print("LONG_WORK_UNIT_SCOPE_ORDER: match")
                return 0
            sys.stdout.writelines(
                difflib.unified_diff(
                    actual.splitlines(True),
                    rendered.splitlines(True),
                    fromfile=str(existing),
                    tofile="generated",
                )
            )
            return 1
        if args.output is None:
            sys.stdout.write(rendered)
        else:
            args.output.write_text(rendered, encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(f"generate_long_work_unit_order: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
