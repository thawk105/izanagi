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
from typing import Mapping, Sequence
import xml.etree.ElementTree as ET


_REJECTION_PREFIX = "acceptance duration ledger input rejected:"
_SCHEMA_VERSION = 1
_MINIMUM_POSITIVE_SECONDS = Decimal("0.001")
_ADD_ONLY_FROZEN_SUITE_PREFIXES = (
    "orchestrator/tests/test_critic.py::",
    "orchestrator/tests/test_p3_exploration_namespace.py::",
    "orchestrator/tests/test_p3_s4_loop_sort.py::",
    "orchestrator/tests/test_real_repo_serialization.py::",
    "orchestrator/tests/test_s1_direct_comparison.py::",
    "orchestrator/tests/test_s8b_materialization.py::",
    "orchestrator/tests/test_s8b_sort_swo_receipt.py::",
    "orchestrator/tests/test_sort_swo_oracle.py::",
)
_ADD_ONLY_FROZEN_REMOVED_NODEIDS = frozenset(
    {
        "orchestrator/tests/test_critic.py::test_current_loader_rejects_non_exact_oracle_contract_ids[sort-swo-v3-corpus1-protocol2-checker2-grammar1-x2b6d45baab3f921208db25299b8622592c484dfb28bebeb8d2cf976fe38474f9-c436a66d9d5d5-tud88f98bc1991-f7ad0ac262561-a215b718a5bfe-suffix]",
        "orchestrator/tests/test_critic.py::test_current_loader_rejects_non_exact_oracle_contract_ids[sort-swo-v4-corpus1-protocol2-checker2-grammar1-x2b6d45baab3f921208db25299b8622592c484dfb28bebeb8d2cf976fe38474f9-c436a66d9d5d5-tud88f98bc1991-f7ad0ac262561-a215b718a5bfe]",
        r"orchestrator/tests/test_critic.py::test_sort_swo_non_axiom_kinds_have_dedicated_fixed_rendering[mutation-\u5168 field snapshot \u304c\u5909\u5316]",
        r"orchestrator/tests/test_critic.py::test_sort_swo_non_axiom_kinds_have_dedicated_fixed_rendering[protocol-\u56fa\u5b9a\u9577 protocol \u306e\u7570\u5e38]",
        "orchestrator/tests/test_sort_swo_oracle.py::test_real_patchharness_checkout_and_resolver_use_explicit_binding",
    }
)
_ADD_ONLY_FROZEN_WRITER_BASE_KEY = (
    "orchestrator/tests/test_sort_swo_oracle.py::"
    "test_real_patchharness_checkout_and_resolver_use_explicit_binding"
)


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
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--add-only",
        action="store_true",
        help=(
            "既存 duration entry を byte exact に保ち、未登録かつ凍結対象外の "
            "nodeid だけを追加する"
        ),
    )
    mode.add_argument(
        "--refresh",
        action="store_true",
        help=(
            "既存の凍結 entry を値ごと保持し、非凍結部分を JUnit から再生成する "
            "(failed/error を除外した後に凍結 suite を除外する)"
        ),
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


def _existing_ledger(path: Path) -> tuple[bytes, dict[str, float]]:
    try:
        existing = path.read_bytes()
        document = json.loads(existing.decode("ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise LedgerInputError(f"{path}: cannot read existing ledger: {exc}") from exc
    if not isinstance(document, dict) or set(document) != {
        "duration_seconds_by_nodeid",
        "nodeid_count",
        "schema_version",
        "unit",
    }:
        raise LedgerInputError(f"{path}: existing ledger has invalid top-level schema")
    if document["schema_version"] != _SCHEMA_VERSION:
        raise LedgerInputError(f"{path}: existing ledger has invalid schema_version")
    if document["unit"] != "seconds":
        raise LedgerInputError(f"{path}: existing ledger has invalid unit")
    durations = document["duration_seconds_by_nodeid"]
    count = document["nodeid_count"]
    if not isinstance(durations, dict) or not all(
        isinstance(nodeid, str)
        and isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
        for nodeid, value in durations.items()
    ):
        raise LedgerInputError(f"{path}: existing ledger has invalid durations")
    if isinstance(count, bool) or not isinstance(count, int) or count != len(durations):
        raise LedgerInputError(f"{path}: existing ledger has invalid nodeid_count")
    return existing, durations


def _add_only_bytes(
    existing: bytes,
    existing_durations: Mapping[str, float],
    additions: Mapping[str, float],
) -> bytes:
    """Insert additions without altering any existing duration-entry bytes."""

    if not additions:
        return existing
    old_count = len(existing_durations)
    new_count = old_count + len(additions)
    count_field = f'  "nodeid_count": {old_count},'.encode("ascii")
    if existing.count(count_field) != 1:
        raise LedgerInputError("existing ledger has non-canonical nodeid_count framing")

    nonempty_open = b'  "duration_seconds_by_nodeid": {\n'
    empty_mapping = b'  "duration_seconds_by_nodeid": {},\n'
    rendered_entries = [
        (
            "    "
            + json.dumps(nodeid, ensure_ascii=True)
            + ": "
            + json.dumps(value, allow_nan=False)
        ).encode("ascii")
        for nodeid, value in sorted(additions.items())
    ]
    if existing_durations:
        if existing.count(nonempty_open) != 1:
            raise LedgerInputError(
                "existing ledger has non-canonical duration mapping framing"
            )
        insertion = b"".join(entry + b",\n" for entry in rendered_entries)
        rendered = existing.replace(
            nonempty_open,
            nonempty_open + insertion,
            1,
        )
    else:
        if existing.count(empty_mapping) != 1:
            raise LedgerInputError(
                "existing ledger has non-canonical empty duration mapping framing"
            )
        mapping = nonempty_open + b",\n".join(rendered_entries) + b"\n  },\n"
        rendered = existing.replace(empty_mapping, mapping, 1)
    return rendered.replace(
        count_field,
        f'  "nodeid_count": {new_count},'.encode("ascii"),
        1,
    )


def _add_only_result(
    generated: bytes,
    existing: bytes,
    existing_durations: Mapping[str, float],
) -> tuple[bytes, set[str], dict[str, int]]:
    generated_durations = json.loads(generated.decode("ascii"))[
        "duration_seconds_by_nodeid"
    ]
    additions: dict[str, float] = {}
    counts = {
        "skipped_existing": 0,
        "excluded_frozen_removed": 0,
        "excluded_writer_base_key": 0,
        "excluded_frozen_suite": 0,
    }
    for nodeid, duration in generated_durations.items():
        if nodeid in existing_durations:
            counts["skipped_existing"] += 1
        elif nodeid == _ADD_ONLY_FROZEN_WRITER_BASE_KEY:
            counts["excluded_writer_base_key"] += 1
        elif nodeid in _ADD_ONLY_FROZEN_REMOVED_NODEIDS:
            counts["excluded_frozen_removed"] += 1
        elif nodeid.startswith(_ADD_ONLY_FROZEN_SUITE_PREFIXES):
            counts["excluded_frozen_suite"] += 1
        else:
            additions[nodeid] = duration
    rendered = _add_only_bytes(existing, existing_durations, additions)
    counts["added"] = len(additions)
    return rendered, set(existing_durations) | set(additions), counts


def _refresh_result(
    generated: bytes,
    existing_durations: Mapping[str, float],
) -> tuple[bytes, set[str], dict[str, int]]:
    """Preserve frozen values and replace all other entries from validated JUnit.

    Failed/error cases have already been excluded by _ledger_bytes, so they
    are not counted again as frozen-suite exclusions. Frozen values are not
    requantized; their JSON spelling is canonicalized with the whole payload.
    """
    generated_durations = json.loads(generated.decode("ascii"))[
        "duration_seconds_by_nodeid"
    ]
    frozen = {
        nodeid: duration
        for nodeid, duration in existing_durations.items()
        if nodeid.startswith(_ADD_ONLY_FROZEN_SUITE_PREFIXES)
    }
    old_nonfrozen = set(existing_durations) - frozen.keys()
    new_nonfrozen = {
        nodeid: duration
        for nodeid, duration in generated_durations.items()
        if not nodeid.startswith(_ADD_ONLY_FROZEN_SUITE_PREFIXES)
    }
    durations = {**frozen, **new_nonfrozen}
    counts = {
        "preserved_frozen": len(frozen),
        "replaced": len(old_nonfrozen & new_nonfrozen.keys()),
        "added": len(new_nonfrozen.keys() - old_nonfrozen),
        "removed": len(old_nonfrozen - new_nonfrozen.keys()),
        "excluded_frozen_suite": len(generated_durations) - len(new_nonfrozen),
    }
    payload = {
        "schema_version": _SCHEMA_VERSION,
        "unit": "seconds",
        "nodeid_count": len(durations),
        "duration_seconds_by_nodeid": durations,
    }
    rendered = json.dumps(
        payload, ensure_ascii=True, indent=2, sort_keys=True, allow_nan=False,
    )
    return (rendered + "\n").encode("ascii"), set(durations), counts


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
        add_only_counts = None
        refresh_counts = None
        if args.add_only:
            existing, existing_durations = _existing_ledger(output)
            rendered, ledger_nodeids, add_only_counts = _add_only_result(
                rendered,
                existing,
                existing_durations,
            )
        elif args.refresh:
            _, existing_durations = _existing_ledger(output)
            rendered, ledger_nodeids, refresh_counts = _refresh_result(
                rendered, existing_durations,
            )
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
        if add_only_counts is not None:
            excluded_total = excluded + sum(
                add_only_counts[key]
                for key in (
                    "excluded_frozen_removed",
                    "excluded_writer_base_key",
                    "excluded_frozen_suite",
                )
            )
            print("mode=add-only")
            print(f"added={add_only_counts['added']}")
            print(f"skipped_existing={add_only_counts['skipped_existing']}")
            print(
                "excluded_frozen_removed="
                f"{add_only_counts['excluded_frozen_removed']}"
            )
            print(
                "excluded_writer_base_key="
                f"{add_only_counts['excluded_writer_base_key']}"
            )
            print(
                "excluded_frozen_suite="
                f"{add_only_counts['excluded_frozen_suite']}"
            )
            print(f"excluded_total={excluded_total}")
        if refresh_counts is not None:
            print("mode=refresh")
            for key, count in refresh_counts.items():
                print(f"{key}={count}")
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
