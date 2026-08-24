#!/usr/bin/env python3
"""Build the acceptance-test duration ledger from one or more JUnit files."""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
import math
import os
from pathlib import Path
import sys
import tempfile
from typing import Sequence
import xml.etree.ElementTree as ET


_REJECTION_PREFIX = "acceptance duration ledger input rejected:"
_SCHEMA_VERSION = 1
_MINIMUM_POSITIVE_SECONDS = Decimal("0.001")


class LedgerInputError(ValueError):
    """A JUnit, join, or coverage input cannot safely produce a ledger."""


def _strip_group_suffix(nodeid: str) -> str:
    at = nodeid.rfind("@")
    if at > nodeid.rfind("]"):
        return nodeid[:at]
    return nodeid


def _parser() -> argparse.ArgumentParser:
    repo = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="受入 JUnit XML から canonical な所要時間台帳を生成する",
    )
    parser.add_argument("JUNIT", nargs="+", type=Path, help="統合する JUnit XML")
    parser.add_argument(
        "--repo",
        type=Path,
        default=repo,
        help=f"join 対象の repository root (default: {repo})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "出力先 (default: "
            "<repo>/orchestrator/tests/acceptance_duration_ledger.json)"
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="生成 bytes と既存台帳の一致だけを検査し、書き込まない",
    )
    parser.add_argument(
        "--coverage-against",
        type=Path,
        metavar="FILE",
        help="pytest --collect-only -q 出力または改行区切り nodeid 一覧",
    )
    return parser


def _duration(raw: str | None, *, source: Path, ordinal: int) -> Decimal:
    if raw is None:
        raise LedgerInputError(f"{source}: testcase {ordinal} has no time")
    try:
        value = Decimal(raw)
    except InvalidOperation as exc:
        raise LedgerInputError(
            f"{source}: testcase {ordinal} has invalid time {raw!r}"
        ) from exc
    if not value.is_finite() or value < 0:
        raise LedgerInputError(
            f"{source}: testcase {ordinal} has non-finite or negative time {raw!r}"
        )
    return value


def _quantize_seconds(value: Decimal) -> float:
    """Round to two significant decimal digits, clamping positive values to 1 ms.

    ROUND_HALF_UP is explicit so the ledger does not depend on binary-float
    rounding.  The consumer uses only rank, so two significant digits keep git
    diffs small without changing the scheduling signal.
    """

    if value.is_zero():
        return 0.0
    try:
        quantum = Decimal(1).scaleb(value.adjusted() - 1)
        rounded = value.quantize(quantum, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise LedgerInputError(f"duration cannot be quantized: {value}") from exc
    if rounded < _MINIMUM_POSITIVE_SECONDS:
        rounded = _MINIMUM_POSITIVE_SECONDS
    result = float(rounded)
    if not math.isfinite(result):
        raise LedgerInputError(f"duration is too large to encode: {value}")
    return result


def _validate_suites(root: ET.Element, source: Path) -> None:
    suites = list(root.iter("testsuite"))
    if not suites:
        raise LedgerInputError(f"{source}: no testsuite element")
    counted_elements = [root, *suites] if root.tag == "testsuites" else suites
    for suite in counted_elements:
        for field in ("failures", "errors"):
            raw = suite.get(field)
            if raw is None:
                if suite is root and root.tag == "testsuites":
                    continue
                raise LedgerInputError(f"{source}: testsuite has no {field} count")
            try:
                count = int(raw)
            except ValueError as exc:
                raise LedgerInputError(
                    f"{source}: testsuite has invalid {field} count {raw!r}"
                ) from exc
            if count < 0:
                raise LedgerInputError(
                    f"{source}: testsuite has negative {field} count {count}"
                )


def _module_join(repo: Path, classname: str, name: str) -> str:
    parts = classname.split(".")
    if not parts or any(not part.isidentifier() for part in parts):
        raise LedgerInputError(f"invalid classname {classname!r}")

    candidates: list[tuple[int, Path]] = []
    for length in range(1, len(parts) + 1):
        candidate = repo.joinpath(*parts[: length - 1], parts[length - 1] + ".py")
        try:
            resolved = candidate.resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        try:
            relative = resolved.relative_to(repo)
        except ValueError as exc:
            raise LedgerInputError(
                f"classname {classname!r} resolves outside the repository"
            ) from exc
        if resolved.is_file():
            candidates.append((length, relative))

    if not candidates:
        raise LedgerInputError(f"classname {classname!r} has no Python module")
    if len(candidates) != 1:
        raise LedgerInputError(f"classname {classname!r} has an ambiguous module")
    module_length, module_path = candidates[0]

    name = _strip_group_suffix(name)
    if not name:
        raise LedgerInputError(f"classname {classname!r} has an empty test name")
    scopes = [module_path.as_posix(), *parts[module_length:], name]
    return "::".join(scopes)


def _read_junit(
    path: Path,
    repo: Path,
) -> list[tuple[str | None, Decimal | None, bool]]:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        raise LedgerInputError(f"{path}: cannot parse XML: {exc}") from exc
    if root.tag not in {"testsuite", "testsuites"}:
        raise LedgerInputError(f"{path}: root must be testsuite or testsuites")
    _validate_suites(root, path)

    rows: list[tuple[str | None, Decimal | None, bool]] = []
    for ordinal, testcase in enumerate(root.iter("testcase"), start=1):
        classname = testcase.get("classname")
        name = testcase.get("name")
        excluded = any(child.tag in {"failure", "error"} for child in testcase)
        if excluded:
            nodeid = None
            if classname and name:
                try:
                    nodeid = _module_join(repo, classname, name)
                except LedgerInputError:
                    pass
            rows.append((nodeid, None, True))
            continue
        if classname is None or not classname:
            raise LedgerInputError(f"{path}: testcase {ordinal} has no classname")
        if name is None or not name:
            raise LedgerInputError(f"{path}: testcase {ordinal} has no name")
        duration = _duration(testcase.get("time"), source=path, ordinal=ordinal)
        try:
            nodeid = _module_join(repo, classname, name)
        except LedgerInputError as exc:
            raise LedgerInputError(f"{path}: testcase {ordinal}: {exc}") from exc
        rows.append((nodeid, duration, False))
    return rows


def _ledger_bytes(
    junit_paths: Sequence[Path],
    repo: Path,
) -> tuple[bytes, set[str], int]:
    durations: dict[str, float] = {}
    seen_nodeids: set[str] = set()
    excluded = 0
    testcase_count = 0
    for path in junit_paths:
        rows = _read_junit(path, repo)
        testcase_count += len(rows)
        for nodeid, duration, row_excluded in rows:
            if nodeid is not None:
                if nodeid in seen_nodeids:
                    raise LedgerInputError(f"duplicate nodeid {nodeid!r}")
                seen_nodeids.add(nodeid)
            if row_excluded:
                excluded += 1
                continue
            if nodeid is None or duration is None:
                raise LedgerInputError(
                    "usable testcase has no canonical nodeid or duration"
                )
            durations[nodeid] = _quantize_seconds(duration)
    if not durations:
        if testcase_count == 0:
            raise LedgerInputError("JUnit input contains no testcases")
        raise LedgerInputError(
            "JUnit input contains no usable testcases after excluding "
            f"{excluded} failed/error testcases"
        )
    payload = {
        "schema_version": _SCHEMA_VERSION,
        "unit": "seconds",
        "nodeid_count": len(durations),
        "duration_seconds_by_nodeid": durations,
    }
    try:
        rendered = json.dumps(
            payload,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise LedgerInputError(f"cannot encode ledger: {exc}") from exc
    return (rendered + "\n").encode("ascii"), set(durations), excluded


def _coverage_nodeids(path: Path, repo: Path) -> set[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise LedgerInputError(f"{path}: cannot read coverage collection: {exc}") from exc
    nodeids: set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if "::" not in line:
            continue
        path_text, scopes = line.split("::", 1)
        if Path(path_text).suffix != ".py":
            continue
        candidate = Path(path_text)
        if not candidate.is_absolute():
            candidate = repo / candidate
        try:
            resolved = candidate.resolve(strict=True)
            relative = resolved.relative_to(repo)
        except (OSError, RuntimeError, ValueError) as exc:
            raise LedgerInputError(
                f"{path}: coverage nodeid path is not a repository Python file: "
                f"{path_text!r}"
            ) from exc
        if not resolved.is_file():
            raise LedgerInputError(
                f"{path}: coverage nodeid path is not a repository Python file: "
                f"{path_text!r}"
            )
        nodeid = _strip_group_suffix(f"{relative.as_posix()}::{scopes}")
        if nodeid.endswith("::"):
            raise LedgerInputError(f"{path}: coverage nodeid has an empty test name")
        nodeids.add(nodeid)
    if not nodeids:
        raise LedgerInputError(f"{path}: coverage collection contains no nodeids")
    return nodeids


def _coverage_line(ledger_nodeids: set[str], collection: set[str]) -> str:
    covered = len(ledger_nodeids & collection)
    total = len(collection)
    return f"covered={covered} total={total} ratio={covered / total:.3f}"


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        os.fchmod(fd, 0o644)
        handle = os.fdopen(fd, "wb")
        fd = -1
        with handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if fd >= 0:
            os.close(fd)
        if temporary_path.exists():
            temporary_path.unlink()


def _check(path: Path, expected: bytes) -> bool:
    try:
        return path.read_bytes() == expected
    except OSError:
        return False


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        repo = args.repo.resolve(strict=True)
        if not repo.is_dir():
            raise LedgerInputError(f"repository is not a directory: {repo}")
        output = args.output or (
            repo / "orchestrator" / "tests" / "acceptance_duration_ledger.json"
        )
        rendered, ledger_nodeids, excluded = _ledger_bytes(args.JUNIT, repo)
        coverage = None
        if args.coverage_against is not None:
            coverage = _coverage_line(
                ledger_nodeids,
                _coverage_nodeids(args.coverage_against, repo),
            )
        if args.check:
            if not _check(output, rendered):
                print(f"acceptance duration ledger differs: {output}", file=sys.stderr)
                result = 1
            else:
                result = 0
        else:
            _atomic_write(output, rendered)
            result = 0
        print(f"excluded_failure_or_error={excluded}")
        if coverage is not None:
            print(coverage)
        return result
    except LedgerInputError as exc:
        print(f"{_REJECTION_PREFIX} {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"acceptance duration ledger operation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
