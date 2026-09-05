#!/usr/bin/env python3
"""Read-only retrospective analysis for T-2098 acceptance sessions.

The input tree is inventoried with directory listing, stat, and read-only opens.
Only accounting stderr, confirm JSON, and receipt.json files are opened for content.
All calculations that claim a duration stay within the login-node clock or the
scheduler clock. Cross-clock head and tail values are emitted only as raw values
that include clock offset.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import stat
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


ORACLE_SESSION = "00e791819b6e2fd7908f1c2261f35e0a"
NS_PER_SECOND = 1_000_000_000
ORACLE_EXPECTED_NS = {
    "s_ns": 457 * NS_PER_SECOND,
    "jmax_ns": 442 * NS_PER_SECOND,
    "env_ns": 443 * NS_PER_SECOND,
    "skew_ns": 1 * NS_PER_SECOND,
    "rpair_ns": 15 * NS_PER_SECOND,
    "rout_ns": 14 * NS_PER_SECOND,
    "head_offset_including_ns": 0,
    "tail_offset_including_ns": 14 * NS_PER_SECOND,
}
D1320_TARGET = {
    "inventory_sessions": 568,
    "missing_dispatch_intents": 1,
    "missing_confirm_or_handled": 18,
    "included_sessions": 549,
    "median_s": 338,
}
MONTHS = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}
WEEKDAYS = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}
ACCOUNTING_TIME_RE = re.compile(
    r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+"
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+"
    r"([ 0-9][0-9]?)\s+([0-9]{2}):([0-9]{2}):([0-9]{2})\s+([0-9]{4})$"
)
SHARD_DIR_RE = re.compile(r"^shard-([0-9]+)$")
MARKER_RE = re.compile(r"^shard-([0-9]+)\.(intent|confirm|handled)\.json$")
PATH_COMPONENT_SYMLINK = "path_component_symlink"


class AnalysisError(Exception):
    """A user-facing input or output contract error."""


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--scheduler-timezone", required=True)
    cohort = parser.add_mutually_exclusive_group(required=True)
    cohort.add_argument(
        "--d1320-cutoff",
        type=parse_iso_date,
        metavar="YYYY-MM-DD",
        help="evaluate one inclusive max-handled calendar-date cutoff",
    )
    cohort.add_argument(
        "--d1320-cutoff-scan",
        action="store_true",
        help="scan every observed max-handled calendar date",
    )
    return parser.parse_args(argv)


def parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected YYYY-MM-DD") from exc


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_paths(root_arg: Path, output_arg: Path) -> tuple[Path, Path]:
    try:
        root = root_arg.resolve(strict=True)
    except OSError as exc:
        raise AnalysisError(f"input root cannot be resolved: {exc}") from exc
    try:
        root_stat = root.stat()
    except OSError as exc:
        raise AnalysisError(f"input root cannot be stated: {exc}") from exc
    if not stat.S_ISDIR(root_stat.st_mode):
        raise AnalysisError("input root is not a directory")

    try:
        output = output_arg.resolve(strict=False)
    except OSError as exc:
        raise AnalysisError(f"output directory cannot be resolved: {exc}") from exc
    if output == root or root in output.parents:
        raise AnalysisError("output directory must not be inside the input root")
    try:
        output.mkdir(parents=True, exist_ok=True)
        output_stat = output.stat()
    except OSError as exc:
        raise AnalysisError(f"output directory cannot be created or stated: {exc}") from exc
    if not stat.S_ISDIR(output_stat.st_mode):
        raise AnalysisError("output path is not a directory")
    return root, output


def symlink_component(root: Path, path: Path) -> Optional[Path]:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return path
    current = root
    for component in relative.parts:
        current = current / component
        try:
            value = current.lstat()
        except FileNotFoundError:
            return None
        except OSError:
            return None
        if stat.S_ISLNK(value.st_mode):
            return current
    return None


def inspect_path(root: Path, path: Path) -> dict[str, Any]:
    unsafe_component = symlink_component(root, path)
    if unsafe_component is not None:
        return {
            "status": PATH_COMPONENT_SYMLINK,
            "mtime_ns": None,
            "size": None,
            "error": f"symlink path component: {unsafe_component}",
        }
    try:
        value = path.stat(follow_symlinks=False)
    except FileNotFoundError:
        return {"status": "missing", "mtime_ns": None, "size": None}
    except OSError as exc:
        return {
            "status": "stat_error",
            "mtime_ns": None,
            "size": None,
            "error": f"{type(exc).__name__}: {exc}",
        }
    if stat.S_ISREG(value.st_mode):
        kind = "regular"
    elif stat.S_ISDIR(value.st_mode):
        kind = "directory"
    else:
        kind = "other"
    return {"status": kind, "mtime_ns": value.st_mtime_ns, "size": value.st_size}


def list_names(root: Path, path: Path) -> tuple[Optional[list[str]], Optional[str]]:
    unsafe_component = symlink_component(root, path)
    if unsafe_component is not None:
        return None, f"{PATH_COMPONENT_SYMLINK}: {unsafe_component}"
    try:
        with os.scandir(path) as entries:
            return [entry.name for entry in entries], None
    except OSError as exc:
        return None, f"{type(exc).__name__}: {exc}"


def read_regular_text(root: Path, path: Path) -> tuple[Optional[str], Optional[str]]:
    unsafe_component = symlink_component(root, path)
    if unsafe_component is not None:
        return None, f"{PATH_COMPONENT_SYMLINK}: {unsafe_component}"
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        return None, f"{type(exc).__name__}: {exc}"
    try:
        value = os.fstat(descriptor)
        if not stat.S_ISREG(value.st_mode):
            return None, "not a regular file"
        with os.fdopen(descriptor, "r", encoding="utf-8", errors="strict") as stream:
            descriptor = -1
            return stream.read(), None
    except (OSError, UnicodeError) as exc:
        return None, f"{type(exc).__name__}: {exc}"
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def parse_accounting_time(value: str, scheduler_tz: ZoneInfo) -> int:
    match = ACCOUNTING_TIME_RE.fullmatch(value.strip())
    if match is None:
        raise ValueError(f"invalid accounting timestamp: {value!r}")
    weekday, month_name, day_text, hour, minute, second, year = match.groups()
    parsed = datetime(
        int(year),
        MONTHS[month_name],
        int(day_text),
        int(hour),
        int(minute),
        int(second),
        tzinfo=scheduler_tz,
    )
    if parsed.weekday() != WEEKDAYS[weekday]:
        raise ValueError(f"weekday does not match date: {value!r}")
    return int(parsed.timestamp()) * NS_PER_SECOND


def one_field(text: str, label: str) -> tuple[Optional[str], Optional[str]]:
    pattern = re.compile(rf"^\s*{re.escape(label)}:\s*(.*?)\s*$", re.MULTILINE)
    values = pattern.findall(text)
    if not values:
        return None, None
    if len(values) != 1:
        return None, f"duplicate {label} fields"
    return values[0], None


def parse_elapse_seconds(value: str) -> int:
    compact = value.strip()
    plain = re.fullmatch(r"([0-9]+)S", compact)
    if plain:
        return int(plain.group(1))
    compound = re.fullmatch(
        r"(?:(?P<days>[0-9]+)D)?(?:(?P<hours>[0-9]+)H)?"
        r"(?:(?P<minutes>[0-9]+)M)?(?:(?P<seconds>[0-9]+)S)?",
        compact,
    )
    if compound is None or not any(compound.groupdict().values()):
        raise ValueError(f"invalid Elapse value: {value!r}")
    pieces = {name: int(raw or 0) for name, raw in compound.groupdict().items()}
    return (
        pieces["days"] * 86400
        + pieces["hours"] * 3600
        + pieces["minutes"] * 60
        + pieces["seconds"]
    )


def parse_accounting(text: str, scheduler_tz: ZoneInfo) -> dict[str, Any]:
    labels = {
        "request_name": "Request Name",
        "created_ns": "Created Request Time",
        "started_ns": "Started Request Time",
        "ended_ns": "Ended Request Time",
        "elapse_s": "Elapse",
    }
    raw: dict[str, Optional[str]] = {}
    errors: list[str] = []
    for key, label in labels.items():
        value, error = one_field(text, label)
        raw[key] = value
        if error:
            errors.append(error)
    if all(value is None for value in raw.values()):
        errors.append("no accounting summary fields")

    parsed: dict[str, Any] = {
        "request_name": raw["request_name"],
        "created_ns": None,
        "started_ns": None,
        "ended_ns": None,
        "elapse_s": None,
        "errors": errors,
    }
    for key in ("created_ns", "started_ns", "ended_ns"):
        if raw[key] is not None:
            try:
                parsed[key] = parse_accounting_time(raw[key] or "", scheduler_tz)
            except ValueError as exc:
                parsed["errors"].append(str(exc))
    if raw["elapse_s"] is not None:
        try:
            parsed["elapse_s"] = parse_elapse_seconds(raw["elapse_s"] or "")
        except ValueError as exc:
            parsed["errors"].append(str(exc))
    parsed["status"] = "ok" if not parsed["errors"] else "parse_error"
    return parsed


def finite_number(value: Any) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def parse_receipt(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text)
    except (json.JSONDecodeError, UnicodeError) as exc:
        return {"status": "parse_error", "error": f"{type(exc).__name__}: {exc}"}
    if not isinstance(payload, dict):
        return {"status": "parse_error", "error": "receipt root is not an object"}
    outcome = payload.get("outcome")
    if not isinstance(outcome, dict):
        outcome = {}
    result = payload.get("result")
    if not isinstance(result, dict):
        result = {}
    runner_binding = result.get("runner_binding")
    if not isinstance(runner_binding, dict):
        runner_binding = {}
    kind = outcome.get("kind")
    reason = outcome.get("reason")
    checkout = runner_binding.get("tested_main")
    return {
        "status": "ok",
        "queue_wait_s": finite_number(payload.get("queue_wait_s")),
        "outcome_kind": str(kind) if kind is not None else "",
        "outcome_reason": str(reason) if reason is not None else "",
        "checkout": str(checkout) if checkout is not None else "",
    }


def confirm_request_id(root: Path, path: Path) -> tuple[Optional[str], Optional[str]]:
    text, error = read_regular_text(root, path)
    if error:
        return None, error
    try:
        payload = json.loads(text or "")
    except (json.JSONDecodeError, UnicodeError) as exc:
        return None, f"{type(exc).__name__}: {exc}"
    if not isinstance(payload, dict):
        return None, "confirm root is not an object"
    value = payload.get("request_id")
    if not isinstance(value, str) or not value.strip():
        return None, "request_id is missing or not a non-empty string"
    return value.strip(), None


def request_id_variants(request_id: str) -> list[str]:
    without_leading_zero_prefix = request_id.removeprefix("0:")
    before_dot = without_leading_zero_prefix.split(".", 1)[0]
    return list(dict.fromkeys((before_dot, without_leading_zero_prefix, request_id)))


def accounting_candidates(
    root: Path,
    directory: Path,
    shard_index: int,
    request_id: Optional[str],
) -> tuple[list[Path], Optional[str], str]:
    first_stem = f"izdw-shard-{shard_index}.e"
    second_stem = "dispatch.sh.e"
    if request_id is not None:
        exact_paths = [
            directory / f"{stem}{identifier}"
            for identifier in request_id_variants(request_id)
            for stem in (first_stem, second_stem)
        ]
        selected: list[Path] = []
        for candidate in dict.fromkeys(exact_paths):
            info = inspect_path(root, candidate)
            if info["status"] == PATH_COMPONENT_SYMLINK:
                return [], info["error"], "request_id_exact"
            if info["status"] != "missing":
                selected.append(candidate)
        return sorted(selected, key=lambda item: item.name), None, "request_id_exact"

    names, error = list_names(root, directory)
    if names is None:
        return [], error, "prefix_fallback"
    selected = [
        directory / name
        for name in names
        if name.startswith(first_stem) or name.startswith(second_stem)
    ]
    return sorted(selected, key=lambda item: item.name), None, "prefix_fallback"


def infer_shard_ids(session_names: Iterable[str], marker_names: Iterable[str]) -> list[int]:
    observed: set[int] = set()
    for name in session_names:
        match = SHARD_DIR_RE.fullmatch(name)
        if match:
            observed.add(int(match.group(1)))
    for name in marker_names:
        match = MARKER_RE.fullmatch(name)
        if match:
            observed.add(int(match.group(1)))
    maximum = max(observed, default=1)
    maximum = max(1, maximum)
    return list(range(maximum + 1))


def add_flag(flags: list[str], value: str) -> None:
    if value not in flags:
        flags.append(value)


def inspect_marker(root: Path, path: Path) -> dict[str, Any]:
    value = inspect_path(root, path)
    if value["status"] == "regular":
        return value
    return value


def ns_to_iso(value: Optional[int], scheduler_tz: ZoneInfo) -> str:
    if value is None:
        return ""
    return datetime.fromtimestamp(value / NS_PER_SECOND, scheduler_tz).isoformat()


def analyze_shard(
    root: Path,
    session_id: str,
    session_path: Path,
    shard_index: int,
    scheduler_tz: ZoneInfo,
) -> dict[str, Any]:
    dispatch_intents = session_path / "dispatch-intents"
    confirm_path = dispatch_intents / f"shard-{shard_index}.confirm.json"
    confirm = inspect_marker(root, confirm_path)
    handled = inspect_marker(root, dispatch_intents / f"shard-{shard_index}.handled.json")
    shard_root = session_path / f"shard-{shard_index}"
    accounting_dir = shard_root / "dispatch" / f"shard-{shard_index}"
    request_id = None
    request_id_error = "confirm is not a regular file"
    if confirm["status"] == "regular":
        request_id, request_id_error = confirm_request_id(root, confirm_path)
    candidates, candidate_list_error, accounting_lookup_mode = accounting_candidates(
        root, accounting_dir, shard_index, request_id
    )
    path_component_symlink = any(
        value == PATH_COMPONENT_SYMLINK
        for value in (confirm["status"], handled["status"])
    ) or PATH_COMPONENT_SYMLINK in (candidate_list_error or "")
    accounting: dict[str, Any] = {
        "status": "missing" if not candidates else "ambiguous",
        "request_name": None,
        "created_ns": None,
        "started_ns": None,
        "ended_ns": None,
        "elapse_s": None,
        "errors": [],
    }
    accounting_path = ""
    if candidate_list_error:
        accounting["status"] = "list_error"
        accounting["errors"] = [candidate_list_error]
    elif len(candidates) == 1:
        accounting_path = str(candidates[0])
        candidate_info = inspect_path(root, candidates[0])
        if candidate_info["status"] == PATH_COMPONENT_SYMLINK:
            path_component_symlink = True
        if candidate_info["status"] != "regular":
            accounting["status"] = "parse_error"
            accounting["errors"] = [f"candidate is {candidate_info['status']}"]
        else:
            text, read_error = read_regular_text(root, candidates[0])
            if read_error:
                if PATH_COMPONENT_SYMLINK in read_error:
                    path_component_symlink = True
                accounting["status"] = "parse_error"
                accounting["errors"] = [read_error]
            else:
                accounting = parse_accounting(text or "", scheduler_tz)

    receipt_path = accounting_dir / "receipt.json"
    receipt_info = inspect_path(root, receipt_path)
    if receipt_info["status"] == PATH_COMPONENT_SYMLINK:
        path_component_symlink = True
    receipt: dict[str, Any] = {"status": receipt_info["status"]}
    if receipt_info["status"] == "regular":
        receipt_text, receipt_error = read_regular_text(root, receipt_path)
        if receipt_error:
            if PATH_COMPONENT_SYMLINK in receipt_error:
                path_component_symlink = True
            receipt = {"status": "parse_error", "error": receipt_error}
        else:
            receipt = parse_receipt(receipt_text or "")

    report = inspect_path(root, shard_root / "report.json")
    shard_junit = inspect_path(root, shard_root / "junit.xml")
    if report["status"] == PATH_COMPONENT_SYMLINK or shard_junit["status"] == PATH_COMPONENT_SYMLINK:
        path_component_symlink = True
    created_ns = accounting.get("created_ns")
    started_ns = accounting.get("started_ns")
    ended_ns = accounting.get("ended_ns")
    job_span_ns = None
    if created_ns is not None and ended_ns is not None:
        job_span_ns = ended_ns - created_ns
    scheduler_queue_ns = None
    if created_ns is not None and started_ns is not None:
        scheduler_queue_ns = started_ns - created_ns
    run_display_ns = None
    if started_ns is not None and ended_ns is not None:
        run_display_ns = ended_ns - started_ns
    queue_wait_diff_s = None
    if receipt.get("queue_wait_s") is not None and scheduler_queue_ns is not None:
        queue_wait_diff_s = receipt["queue_wait_s"] - scheduler_queue_ns / NS_PER_SECOND
    elapse_minus_display_s = None
    if accounting.get("elapse_s") is not None and run_display_ns is not None:
        elapse_minus_display_s = accounting["elapse_s"] - run_display_ns / NS_PER_SECOND

    return {
        "session_id": session_id,
        "shard_index": shard_index,
        "confirm_status": confirm["status"],
        "confirm_mtime_ns": confirm.get("mtime_ns"),
        "handled_status": handled["status"],
        "handled_mtime_ns": handled.get("mtime_ns"),
        "path_component_symlink": path_component_symlink,
        "request_id": request_id or "",
        "request_id_error": request_id_error or "",
        "accounting_lookup_mode": accounting_lookup_mode,
        "accounting_candidate_count": len(candidates),
        "accounting_candidate_list_error": candidate_list_error or "",
        "accounting_path": accounting_path,
        "accounting_status": accounting["status"],
        "accounting_errors": list(accounting.get("errors", [])),
        "request_name": accounting.get("request_name") or "",
        "created_ns": created_ns,
        "started_ns": started_ns,
        "ended_ns": ended_ns,
        "elapse_s": accounting.get("elapse_s"),
        "job_span_ns": job_span_ns,
        "scheduler_queue_ns": scheduler_queue_ns,
        "run_display_ns": run_display_ns,
        "receipt_status": receipt.get("status", "parse_error"),
        "receipt_queue_wait_s": receipt.get("queue_wait_s"),
        "outcome_kind": receipt.get("outcome_kind", ""),
        "outcome_reason": receipt.get("outcome_reason", ""),
        "checkout": receipt.get("checkout", ""),
        "queue_wait_minus_scheduler_queue_s": queue_wait_diff_s,
        "elapse_minus_ended_started_s": elapse_minus_display_s,
        "report_status": report["status"],
        "report_mtime_ns": report.get("mtime_ns"),
        "report_size": report.get("size"),
        "shard_junit_status": shard_junit["status"],
        "shard_junit_mtime_ns": shard_junit.get("mtime_ns"),
        "shard_junit_size": shard_junit.get("size"),
        "is_job_span_argmax": False,
        "is_handled_argmax": False,
    }


EXCLUSION_PRIORITY = [
    "unreadable_session_directory",
    "missing_dispatch_intents",
    "shard_count_invalid",
    "path_component_symlink",
    "marker_missing_or_invalid",
    "accounting_missing",
    "accounting_ambiguous",
    "accounting_unparseable",
    "missing_created",
    "missing_ended",
    "scheduler_order_invalid",
    "login_order_invalid",
]


def choose_exclusive(flags: list[str]) -> str:
    for reason in EXCLUSION_PRIORITY:
        if reason in flags:
            return reason
    return ""


def analyze_session(
    root: Path,
    session_id: str,
    session_path: Path,
    session_stat_status: str,
    session_mtime_ns: Optional[int],
    scheduler_tz: ZoneInfo,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    flags: list[str] = []
    if session_stat_status != "directory":
        add_flag(flags, "unreadable_session_directory")
        return (
            {
                "session_id": session_id,
                "k": None,
                "flags": flags,
                "primary_included": False,
                "primary_exclusion_reason": choose_exclusive(flags),
                "d1320_status": "unreadable",
                "d1320_cohort_date": "",
                "d1320_cohort_date_source": "unavailable",
                "login_collection_class": "indeterminate",
                "root_junit_status": "not_checked",
            },
            [],
        )

    session_names, session_list_error = list_names(root, session_path)
    if session_names is None:
        add_flag(flags, "unreadable_session_directory")
        return (
            {
                "session_id": session_id,
                "k": None,
                "flags": flags,
                "primary_included": False,
                "primary_exclusion_reason": choose_exclusive(flags),
                "d1320_status": "unreadable",
                "d1320_cohort_date": "",
                "d1320_cohort_date_source": "unavailable",
                "login_collection_class": "indeterminate",
                "root_junit_status": "not_checked",
                "session_list_error": session_list_error or "",
            },
            [],
        )

    dispatch_path = session_path / "dispatch-intents"
    dispatch_info = inspect_path(root, dispatch_path)
    marker_names: list[str] = []
    dispatch_list_error = ""
    if dispatch_info["status"] == "directory":
        listed, error = list_names(root, dispatch_path)
        if listed is None:
            dispatch_list_error = error or "unknown list error"
            if PATH_COMPONENT_SYMLINK in dispatch_list_error:
                add_flag(flags, "path_component_symlink")
            add_flag(flags, "marker_missing_or_invalid")
        else:
            marker_names = listed
    else:
        if dispatch_info["status"] == PATH_COMPONENT_SYMLINK:
            add_flag(flags, "path_component_symlink")
        add_flag(flags, "missing_dispatch_intents")

    shard_ids = infer_shard_ids(session_names, marker_names)
    if len(shard_ids) not in (2, 3):
        add_flag(flags, "shard_count_invalid")
    shards = [
        analyze_shard(root, session_id, session_path, index, scheduler_tz)
        for index in shard_ids
    ]

    for shard in shards:
        if shard["path_component_symlink"]:
            add_flag(flags, "path_component_symlink")
        if shard["confirm_status"] != "regular" or shard["handled_status"] != "regular":
            add_flag(flags, "marker_missing_or_invalid")
        status = shard["accounting_status"]
        if status in ("missing", "list_error"):
            add_flag(flags, "accounting_missing")
        elif status == "ambiguous":
            add_flag(flags, "accounting_ambiguous")
        elif status != "ok":
            add_flag(flags, "accounting_unparseable")
        if status == "ok" and shard["created_ns"] is None:
            add_flag(flags, "missing_created")
        if status == "ok" and shard["ended_ns"] is None:
            add_flag(flags, "missing_ended")
        if shard["created_ns"] is not None and shard["ended_ns"] is not None:
            if shard["created_ns"] > shard["ended_ns"]:
                add_flag(flags, "scheduler_order_invalid")

    confirm_values = [shard["confirm_mtime_ns"] for shard in shards]
    handled_values = [shard["handled_mtime_ns"] for shard in shards]
    markers_complete = all(
        shard["confirm_status"] == "regular" and shard["handled_status"] == "regular"
        for shard in shards
    )
    min_confirm_ns = min(confirm_values) if markers_complete else None
    max_handled_ns = max(handled_values) if markers_complete else None
    if min_confirm_ns is not None and max_handled_ns is not None and min_confirm_ns > max_handled_ns:
        add_flag(flags, "login_order_invalid")

    d1320_status = "complete"
    if dispatch_info["status"] != "directory":
        d1320_status = "missing_dispatch_intents"
    elif not markers_complete:
        d1320_status = "missing_confirm_or_handled"

    root_junit = inspect_path(root, session_path / "junit.xml")
    login_collection = inspect_path(root, session_path / "login-collection.log")
    if login_collection["status"] != "regular" or max_handled_ns is None:
        collection_class = "indeterminate"
    elif login_collection["mtime_ns"] <= max_handled_ns:
        collection_class = "off_path"
    else:
        collection_class = "on_path_candidate"

    checkout_values = sorted({shard["checkout"] for shard in shards if shard["checkout"]})
    if not checkout_values:
        checkout = "<missing>"
    elif len(checkout_values) == 1:
        checkout = checkout_values[0]
    else:
        checkout = "mixed:" + "|".join(checkout_values)
    outcome_values = sorted(
        {
            f"{shard['outcome_kind'] or '<missing-kind>'}/{shard['outcome_reason'] or '<missing-reason>'}"
            for shard in shards
        }
    )

    row: dict[str, Any] = {
        "session_id": session_id,
        "k": len(shard_ids),
        "flags": flags,
        "primary_included": not flags,
        "primary_exclusion_reason": choose_exclusive(flags),
        "d1320_status": d1320_status,
        "dispatch_intents_status": dispatch_info["status"],
        "dispatch_list_error": dispatch_list_error,
        "min_confirm_ns": min_confirm_ns,
        "max_handled_ns": max_handled_ns,
        "login_collection_status": login_collection["status"],
        "login_collection_mtime_ns": login_collection.get("mtime_ns"),
        "login_collection_size": login_collection.get("size"),
        "login_collection_class": collection_class,
        "root_junit_status": root_junit["status"],
        "root_junit_mtime_ns": root_junit.get("mtime_ns"),
        "root_junit_size": root_junit.get("size"),
        "checkout": checkout,
        "outcomes": "|".join(outcome_values),
        "report_available_shards": sum(shard["report_status"] == "regular" for shard in shards),
        "shard_junit_available_shards": sum(shard["shard_junit_status"] == "regular" for shard in shards),
        "receipt_available_shards": sum(shard["receipt_status"] == "ok" for shard in shards),
    }

    if markers_complete:
        row["s_ns"] = max_handled_ns - min_confirm_ns
        row["s_pair_max_ns"] = max(
            shard["handled_mtime_ns"] - shard["confirm_mtime_ns"] for shard in shards
        )
        row["month"] = datetime.fromtimestamp(
            max_handled_ns / NS_PER_SECOND, scheduler_tz
        ).strftime("%Y-%m")
        row["max_handled_date"] = datetime.fromtimestamp(
            max_handled_ns / NS_PER_SECOND, scheduler_tz
        ).date().isoformat()
        row["d1320_cohort_date"] = row["max_handled_date"]
        row["d1320_cohort_date_source"] = "max_j_H_j"
    else:
        row["s_ns"] = None
        row["s_pair_max_ns"] = None
        row["month"] = "<indeterminate>"
        row["max_handled_date"] = ""
        available_handled = [
            shard["handled_mtime_ns"]
            for shard in shards
            if shard["handled_status"] == "regular"
        ]
        available_confirm = [
            shard["confirm_mtime_ns"]
            for shard in shards
            if shard["confirm_status"] == "regular"
        ]
        if available_handled:
            cohort_anchor_ns = max(available_handled)
            cohort_source = "max_available_H_j"
        elif available_confirm:
            cohort_anchor_ns = max(available_confirm)
            cohort_source = "max_available_F_j"
        else:
            cohort_anchor_ns = session_mtime_ns
            cohort_source = "session_directory_mtime_fallback"
        if cohort_anchor_ns is None:
            fallback_date = ""
            fallback_source = "unavailable"
        else:
            fallback_date = datetime.fromtimestamp(
                cohort_anchor_ns / NS_PER_SECOND, scheduler_tz
            ).date().isoformat()
            fallback_source = cohort_source
        row["d1320_cohort_date"] = ""
        row["d1320_cohort_date_source"] = "unavailable"
        row["d1320_fallback_cohort_date"] = fallback_date
        row["d1320_fallback_cohort_date_source"] = fallback_source

    if markers_complete:
        row["d1320_fallback_cohort_date"] = row["d1320_cohort_date"]
        row["d1320_fallback_cohort_date_source"] = row["d1320_cohort_date_source"]

    if row["primary_included"]:
        job_spans = [shard["job_span_ns"] for shard in shards]
        created = [shard["created_ns"] for shard in shards]
        ended = [shard["ended_ns"] for shard in shards]
        jmax_ns = max(job_spans)
        env_ns = max(ended) - min(created)
        skew_ns = env_ns - jmax_ns
        rout_ns = row["s_ns"] - env_ns
        rpair_ns = row["s_ns"] - jmax_ns
        head_ns = min(created) - row["min_confirm_ns"]
        tail_ns = row["max_handled_ns"] - max(ended)
        row.update(
            {
                "jmax_ns": jmax_ns,
                "env_ns": env_ns,
                "skew_ns": skew_ns,
                "rout_ns": rout_ns,
                "rpair_ns": rpair_ns,
                "head_offset_including_ns": head_ns,
                "tail_offset_including_ns": tail_ns,
                "identity_rpair_diff_ns": rpair_ns - (rout_ns + skew_ns),
                "identity_rout_raw_diff_ns": rout_ns - (head_ns + tail_ns),
            }
        )
        job_argmax = {shard["shard_index"] for shard in shards if shard["job_span_ns"] == jmax_ns}
        handled_argmax = {
            shard["shard_index"]
            for shard in shards
            if shard["handled_mtime_ns"] == row["max_handled_ns"]
        }
        row["job_argmax_shards"] = ",".join(str(value) for value in sorted(job_argmax))
        row["handled_argmax_shards"] = ",".join(str(value) for value in sorted(handled_argmax))
        row["job_argmax_tie"] = len(job_argmax) > 1
        row["handled_argmax_tie"] = len(handled_argmax) > 1
        row["argmax_any_overlap"] = bool(job_argmax & handled_argmax)
        row["argmax_exact_set_match"] = job_argmax == handled_argmax
        for shard in shards:
            shard["is_job_span_argmax"] = shard["shard_index"] in job_argmax
            shard["is_handled_argmax"] = shard["shard_index"] in handled_argmax
    else:
        for key in (
            "jmax_ns",
            "env_ns",
            "skew_ns",
            "rout_ns",
            "rpair_ns",
            "head_offset_including_ns",
            "tail_offset_including_ns",
            "identity_rpair_diff_ns",
            "identity_rout_raw_diff_ns",
        ):
            row[key] = None
        row["job_argmax_shards"] = ""
        row["handled_argmax_shards"] = ""
        row["job_argmax_tie"] = False
        row["handled_argmax_tie"] = False
        row["argmax_any_overlap"] = False
        row["argmax_exact_set_match"] = False
    return row, shards


def nearest_rank(values: Iterable[float], probability: float) -> Optional[float]:
    ordered = sorted(values)
    if not ordered:
        return None
    rank = max(1, math.ceil(probability * len(ordered)))
    return ordered[rank - 1]


def distribution_seconds(values: Iterable[float]) -> dict[str, Any]:
    ordered = sorted(value for value in values if math.isfinite(value))
    if not ordered:
        return {"n": 0, "unit": "seconds"}
    return {
        "n": len(ordered),
        "unit": "seconds",
        "min": ordered[0],
        "p25": nearest_rank(ordered, 0.25),
        "median": nearest_rank(ordered, 0.50),
        "p75": nearest_rank(ordered, 0.75),
        "p90": nearest_rank(ordered, 0.90),
        "max": ordered[-1],
    }


def distribution_ns(values: Iterable[int]) -> dict[str, Any]:
    return distribution_seconds(value / NS_PER_SECOND for value in values)


SESSION_METRICS = (
    "s_ns",
    "jmax_ns",
    "env_ns",
    "skew_ns",
    "rout_ns",
    "rpair_ns",
    "head_offset_including_ns",
    "tail_offset_including_ns",
)


def session_distribution(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        key.removesuffix("_ns"): distribution_ns(
            row[key] for row in rows if row.get(key) is not None
        )
        for key in SESSION_METRICS
    }


def strata_by(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(key, "<missing>"))].append(row)
    return {
        name: {"sessions": len(group), "distributions": session_distribution(group)}
        for name, group in sorted(groups.items())
    }


def checkout_strata(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["checkout"] for row in rows)
    actual_checkouts = {
        name: count
        for name, count in counts.items()
        if name != "<missing>" and not name.startswith("mixed:")
    }
    top = [
        name
        for name, _ in sorted(actual_checkouts.items(), key=lambda item: (-item[1], item[0]))[:10]
    ]
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["checkout"] == "<missing>":
            label = "<missing>"
        elif row["checkout"].startswith("mixed:"):
            label = "<mixed>"
        else:
            label = row["checkout"] if row["checkout"] in top else "<other>"
        groups[label].append(row)
    return {
        "top_10_checkout_values": top,
        "groups": {
            name: {"sessions": len(group), "distributions": session_distribution(group)}
            for name, group in sorted(groups.items())
        },
    }


def outcome_strata(shards: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for shard in shards:
        if shard["receipt_status"] != "ok":
            label = f"<receipt-{shard['receipt_status']}>"
        else:
            label = f"{shard['outcome_kind'] or '<missing-kind>'}/{shard['outcome_reason'] or '<missing-reason>'}"
        groups[label].append(shard)
    result: dict[str, Any] = {}
    for label, group in sorted(groups.items()):
        result[label] = {
            "shards": len(group),
            "sessions": len({shard["session_id"] for shard in group}),
            "job_created_to_ended": distribution_ns(
                shard["job_span_ns"] for shard in group if shard["job_span_ns"] is not None
            ),
            "receipt_queue_wait": distribution_seconds(
                shard["receipt_queue_wait_s"]
                for shard in group
                if shard["receipt_queue_wait_s"] is not None
            ),
        }
    return result


def d1320_result_for_cutoff(
    rows: list[dict[str, Any]], cutoff: date, cohort_date_key: str, retain_unassignable: bool
) -> dict[str, Any]:
    selected: list[dict[str, Any]] = []
    for row in rows:
        cohort_date = row.get(cohort_date_key)
        if not cohort_date and retain_unassignable:
            selected.append(row)
        elif cohort_date and date.fromisoformat(cohort_date) <= cutoff:
            selected.append(row)
    included = [row for row in selected if row["d1320_status"] == "complete"]
    envelope_median_ns = nearest_rank([row["s_ns"] for row in included], 0.50)
    paired_median_ns = nearest_rank([row["s_pair_max_ns"] for row in included], 0.50)
    return {
        "cutoff": cutoff.isoformat(),
        "inventory_sessions": len(selected),
        "missing_dispatch_intents": sum(
            row["d1320_status"] == "missing_dispatch_intents" for row in selected
        ),
        "missing_confirm_or_handled": sum(
            row["d1320_status"] in ("missing_confirm_or_handled", "unreadable") for row in selected
        ),
        "included_sessions": len(included),
        "median_max_h_minus_min_f_s": (
            envelope_median_ns / NS_PER_SECOND if envelope_median_ns is not None else None
        ),
        "median_max_h_minus_matching_f_s": (
            paired_median_ns / NS_PER_SECOND if paired_median_ns is not None else None
        ),
    }


def d1320_variant(
    rows: list[dict[str, Any]],
    explicit_cutoff: Optional[date],
    scan: bool,
    cohort_date_key: str,
    cohort_source_key: str,
    retain_unassignable: bool,
    membership_rule: str,
) -> dict[str, Any]:
    observed_dates = sorted(
        {
            date.fromisoformat(row[cohort_date_key])
            for row in rows
            if row.get(cohort_date_key)
        }
    )
    cutoffs = observed_dates if scan else [explicit_cutoff]
    evaluations = [
        d1320_result_for_cutoff(rows, cutoff, cohort_date_key, retain_unassignable)
        for cutoff in cutoffs
        if cutoff is not None
    ]

    matches = []
    for evaluation in evaluations:
        counts_match = all(
            evaluation[key] == D1320_TARGET[key]
            for key in (
                "inventory_sessions",
                "missing_dispatch_intents",
                "missing_confirm_or_handled",
                "included_sessions",
            )
        )
        median_match = (
            evaluation["median_max_h_minus_min_f_s"] == D1320_TARGET["median_s"]
            or evaluation["median_max_h_minus_matching_f_s"] == D1320_TARGET["median_s"]
        )
        if counts_match and median_match:
            matches.append(evaluation)

    identified = "not_identified"
    if matches:
        first = matches[0]
        envelope_matches = first["median_max_h_minus_min_f_s"] == D1320_TARGET["median_s"]
        matching_pair_matches = (
            first["median_max_h_minus_matching_f_s"] == D1320_TARGET["median_s"]
        )
        if envelope_matches and not matching_pair_matches:
            identified = "max_j_H_j_minus_min_j_F_j"
        elif matching_pair_matches and not envelope_matches:
            identified = "max_j_of_H_j_minus_F_j"
        elif envelope_matches and matching_pair_matches:
            identified = "not_identified_both_formulas_match"
    return {
        "status": "pass" if matches else "fail",
        "reproduced": bool(matches),
        "matching_cutoffs": [item["cutoff"] for item in matches],
        "formula_identification": identified,
        "matching_evaluations": matches,
        "evaluations": evaluations,
        "cutoff_membership_rule": membership_rule,
        "cutoff_anchor_sources": dict(
            sorted(Counter(row.get(cohort_source_key, "unavailable") for row in rows).items())
        ),
    }


def d1320_check(
    rows: list[dict[str, Any]], explicit_cutoff: Optional[date], scan: bool
) -> dict[str, Any]:
    with_fallback = d1320_variant(
        rows,
        explicit_cutoff,
        scan,
        "d1320_fallback_cohort_date",
        "d1320_fallback_cohort_date_source",
        True,
        (
            "Complete-marker sessions use max_j H_j as the inclusive local calendar-date cutoff anchor. "
            "For a session where max_j H_j is undefined, this variant falls back to max available H_j, "
            "then max available F_j, then session directory mtime. A session still lacking an anchor is "
            "retained in every cutoff and reported as unassignable."
        ),
    )
    without_fallback = d1320_variant(
        rows,
        explicit_cutoff,
        scan,
        "d1320_cohort_date",
        "d1320_cohort_date_source",
        False,
        (
            "Only complete regular-file marker sessions use max_j H_j as the inclusive local calendar-date "
            "cutoff anchor. Sessions without that anchor are omitted from cohort counts; no fallback is used."
        ),
    )
    return {
        "kind": "falsifiable",
        "target": D1320_TARGET,
        "with_fallback": with_fallback,
        "without_fallback": without_fallback,
    }


def oracle_check(rows: list[dict[str, Any]]) -> dict[str, Any]:
    row = next((item for item in rows if item["session_id"] == ORACLE_SESSION), None)
    actual: dict[str, Any] = {}
    mismatches: dict[str, Any] = {}
    if row is None:
        mismatches["session"] = {"expected": "present", "actual": "missing"}
    elif not row["primary_included"]:
        mismatches["primary_included"] = {
            "expected": True,
            "actual": False,
            "exclusion": row["primary_exclusion_reason"],
            "all_flags": row["flags"],
        }
    else:
        for key, expected in ORACLE_EXPECTED_NS.items():
            actual[key] = row.get(key)
            if actual[key] != expected:
                mismatches[key] = {"expected_ns": expected, "actual_ns": actual[key]}
    return {
        "name": "oracle_session_exact_eight_values",
        "kind": "falsifiable",
        "status": "pass" if not mismatches else "fail",
        "session_id": ORACLE_SESSION,
        "expected_ns": ORACLE_EXPECTED_NS,
        "actual_ns": actual,
        "mismatches": mismatches,
    }


def exclusion_and_auxiliary_counters(
    rows: list[dict[str, Any]], shards: list[dict[str, Any]]
) -> tuple[dict[str, Any], dict[str, Any]]:
    multi = Counter(flag for row in rows for flag in row["flags"])
    exclusive = Counter(
        row["primary_exclusion_reason"] for row in rows if not row["primary_included"]
    )
    exclusion = {
        "unit": "sessions",
        "multiple_reason_counters": {name: multi.get(name, 0) for name in EXCLUSION_PRIORITY},
        "exclusive_reason_counters": {name: exclusive.get(name, 0) for name in EXCLUSION_PRIORITY},
        "condition_counters": {
            "shard_count_invalid_sessions": sum(
                "shard_count_invalid" in row["flags"] for row in rows
            ),
            "missing_confirm_sessions": sum(
                any(shard["confirm_status"] == "missing" for shard in shards if shard["session_id"] == row["session_id"])
                for row in rows
            ),
            "missing_handled_sessions": sum(
                any(shard["handled_status"] == "missing" for shard in shards if shard["session_id"] == row["session_id"])
                for row in rows
            ),
            "missing_created_sessions": sum(
                "missing_created" in row["flags"] for row in rows
            ),
            "missing_ended_sessions": sum("missing_ended" in row["flags"] for row in rows),
        },
    }
    shard_status_values = [
        shard[field]
        for shard in shards
        for field in (
            "confirm_status",
            "handled_status",
            "receipt_status",
            "report_status",
            "shard_junit_status",
        )
    ]
    session_status_values = [
        row[field]
        for row in rows
        for field in ("dispatch_intents_status", "login_collection_status", "root_junit_status")
        if field in row
    ]
    auxiliary = {
        "accounting_by_prefix_fallback": sum(
            shard["accounting_lookup_mode"] == "prefix_fallback" for shard in shards
        ),
        "path_component_symlink": sum(
            shard["path_component_symlink"] for shard in shards
        ),
        "missing_started_shards": sum(
            shard["accounting_status"] == "ok" and shard["started_ns"] is None for shard in shards
        ),
        "missing_receipt_shards": sum(shard["receipt_status"] == "missing" for shard in shards),
        "receipt_parse_failure_shards": sum(
            shard["receipt_status"] not in ("ok", "missing") for shard in shards
        ),
        "unavailable_receipt_shards": sum(shard["receipt_status"] != "ok" for shard in shards),
        "missing_request_name_shards": sum(
            shard["accounting_status"] == "ok" and not shard["request_name"] for shard in shards
        ),
        "missing_created_shards": sum(
            shard["accounting_status"] == "ok" and shard["created_ns"] is None for shard in shards
        ),
        "missing_ended_shards": sum(
            shard["accounting_status"] == "ok" and shard["ended_ns"] is None for shard in shards
        ),
        "missing_report_shards": sum(shard["report_status"] != "regular" for shard in shards),
        "missing_shard_junit_shards": sum(
            shard["shard_junit_status"] != "regular" for shard in shards
        ),
        "missing_root_junit_sessions": sum(row["root_junit_status"] != "regular" for row in rows),
        "missing_login_collection_sessions": sum(
            row["login_collection_status"] != "regular" for row in rows
        ),
        "negative_rout_sessions": sum(
            row.get("rout_ns") is not None and row["rout_ns"] < 0 for row in rows
        ),
        "negative_rpair_sessions": sum(
            row.get("rpair_ns") is not None and row["rpair_ns"] < 0 for row in rows
        ),
        "negative_head_offset_including_sessions": sum(
            row.get("head_offset_including_ns") is not None
            and row["head_offset_including_ns"] < 0
            for row in rows
        ),
        "file_stat_failure_paths": sum(value == "stat_error" for value in shard_status_values)
        + sum(value == "stat_error" for value in session_status_values)
        + sum(
            any("stat_error" in error for error in shard["accounting_errors"])
            for shard in shards
        ),
        "queue_wait_timeout_outcome_shards": sum(
            "queue-wait-timeout"
            in f"{shard['outcome_kind']}/{shard['outcome_reason']}".lower()
            for shard in shards
            if shard["receipt_status"] == "ok"
        ),
    }
    return exclusion, auxiliary


def build_summary(
    root: Path,
    output: Path,
    scheduler_timezone: str,
    started_at: str,
    ended_at: str,
    rows: list[dict[str, Any]],
    shards: list[dict[str, Any]],
    d1320: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    included = [row for row in rows if row["primary_included"]]
    excluded = [row for row in rows if not row["primary_included"]]
    exclusion, auxiliary = exclusion_and_auxiliary_counters(rows, shards)
    exclusive_total = sum(exclusion["exclusive_reason_counters"].values())
    duplicate_ids = sorted(
        session_id for session_id, count in Counter(row["session_id"] for row in rows).items() if count != 1
    )
    coverage_ok = len(rows) == len(included) + exclusive_total and not duplicate_ids

    identity_diffs = [
        row["identity_rpair_diff_ns"] for row in included if row["identity_rpair_diff_ns"] is not None
    ]
    raw_identity_diffs = [
        row["identity_rout_raw_diff_ns"]
        for row in included
        if row["identity_rout_raw_diff_ns"] is not None
    ]
    identity_ok = len(identity_diffs) == len(included) and all(value == 0 for value in identity_diffs)
    raw_identity_ok = len(raw_identity_diffs) == len(included) and all(
        value == 0 for value in raw_identity_diffs
    )

    nqsv_checked = [
        shard
        for shard in shards
        if shard["created_ns"] is not None
        and shard["started_ns"] is not None
        and shard["ended_ns"] is not None
    ]
    nqsv_violations = [
        f"{shard['session_id']}/shard-{shard['shard_index']}"
        for shard in nqsv_checked
        if not (shard["created_ns"] <= shard["started_ns"] <= shard["ended_ns"])
    ]

    queue_diffs = [
        shard["queue_wait_minus_scheduler_queue_s"]
        for shard in shards
        if shard["queue_wait_minus_scheduler_queue_s"] is not None
    ]
    elapse_diffs = [
        shard["elapse_minus_ended_started_s"]
        for shard in shards
        if shard["elapse_minus_ended_started_s"] is not None
    ]
    argmax_overlap = sum(row["argmax_any_overlap"] for row in included)
    argmax_exact = sum(row["argmax_exact_set_match"] for row in included)
    job_ties = sum(row["job_argmax_tie"] for row in included)
    handled_ties = sum(row["handled_argmax_tie"] for row in included)
    oracle = oracle_check(rows)
    oracle_shard_zero = next(
        (
            shard
            for shard in shards
            if shard["session_id"] == ORACLE_SESSION and shard["shard_index"] == 0
        ),
        None,
    )
    oracle_queue_example = {
        "session_id": ORACLE_SESSION,
        "shard_index": 0,
        "receipt_queue_wait_s": (
            oracle_shard_zero["receipt_queue_wait_s"] if oracle_shard_zero else None
        ),
        "scheduler_started_minus_created_s": (
            oracle_shard_zero["scheduler_queue_ns"] / NS_PER_SECOND
            if oracle_shard_zero and oracle_shard_zero["scheduler_queue_ns"] is not None
            else None
        ),
        "interpretation": "The expected approximate contrast is 5.34 seconds versus 208 seconds; they are different quantities.",
    }

    collection_all = Counter(row["login_collection_class"] for row in rows)
    collection_primary = Counter(row["login_collection_class"] for row in included)
    checkout_count = len({row["checkout"] for row in included})
    month_count = len({row["month"] for row in included})
    checks = [
        {
            "name": "rpair_equals_rout_plus_skew_at_ns_precision",
            "kind": "identity",
            "status": "pass" if identity_ok else "fail",
            "rows_checked": len(identity_diffs),
            "nonzero_difference_rows": sum(value != 0 for value in identity_diffs),
            "max_absolute_difference_ns": max((abs(value) for value in identity_diffs), default=0),
            "interpretation": "This is an algebraic identity, not validation of the estimand or data.",
        },
        {
            "name": "rout_equals_cross_clock_raw_head_plus_tail_at_ns_precision",
            "kind": "identity",
            "status": "pass" if raw_identity_ok else "fail",
            "rows_checked": len(raw_identity_diffs),
            "nonzero_difference_rows": sum(value != 0 for value in raw_identity_diffs),
            "interpretation": "This is also algebraic; head and tail individually include clock offset.",
        },
        {
            "name": "inventory_partition_and_one_session_row",
            "kind": "self_consistency",
            "status": "pass" if coverage_ok else "fail",
            "inventory_sessions": len(rows),
            "primary_included_sessions": len(included),
            "exclusive_excluded_sessions": exclusive_total,
            "duplicate_or_missing_session_ids": duplicate_ids,
        },
        {
            "name": "d1320_cohort_reproduction_with_fallback",
            "kind": "falsifiable",
            "status": d1320["with_fallback"]["status"],
            "reproduced": d1320["with_fallback"]["reproduced"],
            "matching_cutoffs": d1320["with_fallback"]["matching_cutoffs"],
            "formula_identification": d1320["with_fallback"]["formula_identification"],
        },
        {
            "name": "d1320_cohort_reproduction_without_fallback",
            "kind": "falsifiable",
            "status": d1320["without_fallback"]["status"],
            "reproduced": d1320["without_fallback"]["reproduced"],
            "matching_cutoffs": d1320["without_fallback"]["matching_cutoffs"],
            "formula_identification": d1320["without_fallback"]["formula_identification"],
        },
        {
            "name": "nqsv_created_started_ended_order",
            "kind": "self_consistency",
            "status": "pass" if not nqsv_violations else "fail",
            "shards_checked": len(nqsv_checked),
            "violation_count": len(nqsv_violations),
            "violations": nqsv_violations,
        },
        {
            "name": "receipt_queue_wait_minus_scheduler_started_minus_created",
            "kind": "diagnostic",
            "status": "reported",
            "difference": distribution_seconds(queue_diffs),
            "interpretation": (
                "No equality criterion applies: receipt queue_wait_s measures qsub return to first qstat RUN "
                "interpretation, while scheduler Started minus Created is a different quantity."
            ),
        },
        {
            "name": "job_span_argmax_vs_handled_mtime_argmax",
            "kind": "diagnostic",
            "status": "reported",
            "sessions": len(included),
            "any_overlap_count": argmax_overlap,
            "any_overlap_rate": argmax_overlap / len(included) if included else None,
            "exact_set_match_count": argmax_exact,
            "exact_set_match_rate": argmax_exact / len(included) if included else None,
            "job_span_tie_sessions": job_ties,
            "handled_mtime_tie_sessions": handled_ties,
        },
        {
            "name": "elapse_minus_ended_minus_started",
            "kind": "diagnostic",
            "status": "reported",
            "difference": distribution_seconds(elapse_diffs),
            "interpretation": "Elapse is not assumed equal to Ended Request Time minus Started Request Time.",
        },
        oracle,
    ]

    primary_distribution = session_distribution(included)
    pooled_job_span = distribution_ns(
        shard["job_span_ns"]
        for shard in shards
        if shard["primary_session_included"] and shard["job_span_ns"] is not None
    )
    median_s = primary_distribution["s"].get("median")
    median_jmax = primary_distribution["jmax"].get("median")
    median_rpair = primary_distribution["rpair"].get("median")
    median_pooled_job_span = pooled_job_span.get("median")
    median_s_minus_pooled = (
        median_s - median_pooled_job_span
        if median_s is not None and median_pooled_job_span is not None
        else None
    )
    median_s_minus_jmax = (
        median_s - median_jmax
        if median_s is not None and median_jmax is not None
        else None
    )

    summary: dict[str, Any] = {
        "schema_version": 1,
        "status": "ok",
        "inventory": {
            "root": str(root),
            "started_at_utc": started_at,
            "ended_at_utc": ended_at,
            "is_snapshot": False,
            "sessions": len(rows),
            "primary_included_sessions": len(included),
            "primary_excluded_sessions": len(excluded),
        },
        "output_directory": str(output),
        "scheduler_time": {
            "timezone": scheduler_timezone,
            "assumption": (
                "Timezone-less NQSV accounting timestamps are interpreted as Asia/Tokyo only when the "
                "requested scheduler timezone is Asia/Tokyo; the configured name is recorded here."
            ),
            "input_resolution_seconds": 1,
        },
        "quantiles": {
            "method": "nearest-rank",
            "definition": "For p in (0,1], select sorted value at one-based rank ceil(p*n).",
        },
        "estimands": {
            "S": "max_j H_j - min_j F_j; login-node marker clock",
            "Jmax": "max_j (E_j - C_j); scheduler clock",
            "Env": "max_j E_j - min_j C_j; scheduler clock",
            "Skew": "Env - Jmax; scheduler durations",
            "Rout": "S - Env; difference of durations",
            "Rpair": "S - Jmax; difference of durations",
            "head_offset_including": "min_j C_j - min_j F_j; raw cross-clock value including offset",
            "tail_offset_including": "max_j H_j - max_j E_j; raw cross-clock value including offset",
        },
        "primary_complete_case": {
            "distributions": primary_distribution,
            "pooled_shard_job_span": pooled_job_span,
            "median_differences_seconds": {
                "median_s_minus_median_pooled_shard_job_span": (
                    median_s_minus_pooled
                ),
                "median_s_minus_median_jmax": median_s_minus_jmax,
                "median_rpair": median_rpair,
                "median_s_minus_median_jmax_equals_median_rpair": (
                    median_s_minus_jmax == median_rpair
                    if median_s_minus_jmax is not None and median_rpair is not None
                    else None
                ),
            },
            "warning": (
                "This is a complete-case distribution. Long sessions can be preferentially absent when "
                "timeouts, qdel, shared deadlines, or late accounting leave required markers or C/E missing."
            ),
        },
        "exclusions": exclusion,
        "auxiliary_coverage_and_signs": auxiliary,
        "stratification": {
            "by_k": strata_by(included, "k"),
            "by_checkout_top_10_and_other": checkout_strata(included),
            "by_max_handled_month": strata_by(included, "month"),
            "shards_by_receipt_outcome_kind_reason": {
                "all_inventory_sessions": outcome_strata(shards),
                "primary_sessions": outcome_strata(
                    [shard for shard in shards if shard["primary_session_included"]]
                ),
                "excluded_sessions": outcome_strata(
                    [shard for shard in shards if not shard["primary_session_included"]]
                ),
            },
        },
        "login_collection_marker_comparison": {
            "all_inventory_sessions": {
                name: collection_all.get(name, 0)
                for name in ("off_path", "on_path_candidate", "indeterminate")
            },
            "primary_sessions": {
                name: collection_primary.get(name, 0)
                for name in ("off_path", "on_path_candidate", "indeterminate")
            },
            "definition": (
                "off_path means login-collection.log mtime <= max_j H_j; on_path_candidate means it is "
                "later; indeterminate means either marker is unavailable. Both compared markers are written "
                "on the login node."
            ),
            "limitation": (
                "The log mtime is a write after the collection subprocess returns, not the collection end "
                "event. Even an off_path classification does not imply that collection did not delay the "
                "parent: the parent starts reading worker results only after collection returns."
            ),
        },
        "diagnostics": {
            "receipt_queue_wait_minus_scheduler_queue": distribution_seconds(queue_diffs),
            "elapse_minus_scheduler_displayed_run": distribution_seconds(elapse_diffs),
            "oracle_queue_wait_example": oracle_queue_example,
        },
        "d1320_reproduction": d1320,
        "oracle": oracle,
        "independent_checks": checks,
        "interpretation_notes": [
            "The historic 338 second session median minus 263 second job median is an unpaired difference across different units and populations; it is not decomposed here.",
            (
                "Medians are not additive or subtractive term by term. In this primary complete case, "
                f"median(S) - median(Jmax) is {median_s_minus_jmax} seconds, while median(S - Jmax) "
                f"is {median_rpair} seconds. A difference of medians is not a per-session decomposition."
            ),
            "Rpair = Rout + Skew is checked at nanosecond precision on every primary row, but it is an algebraic identity and not validation.",
            "head_offset_including and tail_offset_including cross clocks, include offset, can be negative, and are not used for the primary conclusion.",
            "Ended to handled is not split into polling, artifact collection, or merge because saved observation points do not support that split.",
            (
                f"This inventory contains {len(rows)} sessions across {checkout_count} primary checkout "
                f"groups and {month_count} primary max-handled months. It is a mixed population, not one "
                "single acceptance profile."
            ),
            "The stated 743-session cohort spans multiple checkouts and multiple months, so it cannot be described as one acceptance profile; the same stratification rule is applied to this live inventory count.",
        ],
    }
    structural_success = identity_ok and raw_identity_ok and coverage_ok
    oracle_success = oracle["status"] == "pass"
    success = structural_success and oracle_success
    if not success:
        summary["status"] = "failed"
        summary["failure_reasons"] = []
        if not identity_ok or not raw_identity_ok:
            summary["failure_reasons"].append("identity check failed")
        if not coverage_ok:
            summary["failure_reasons"].append("inventory coverage check failed")
        if not oracle_success:
            summary["failure_reasons"].append("oracle exact match failed")
    return summary, success


SESSION_FIELDS = [
    "session_id",
    "k",
    "primary_included",
    "primary_exclusion_reason",
    "all_exclusion_reasons",
    "d1320_status",
    "d1320_cohort_date",
    "d1320_cohort_date_source",
    "d1320_fallback_cohort_date",
    "d1320_fallback_cohort_date_source",
    "dispatch_intents_status",
    "checkout",
    "outcomes",
    "month",
    "max_handled_date",
    "login_collection_class",
    "login_collection_status",
    "login_collection_mtime_ns",
    "login_collection_size",
    "root_junit_status",
    "root_junit_mtime_ns",
    "root_junit_size",
    "receipt_available_shards",
    "report_available_shards",
    "shard_junit_available_shards",
    "min_confirm_ns",
    "max_handled_ns",
    "s_ns",
    "s_pair_max_ns",
    "jmax_ns",
    "env_ns",
    "skew_ns",
    "rout_ns",
    "rpair_ns",
    "head_offset_including_ns",
    "tail_offset_including_ns",
    "identity_rpair_diff_ns",
    "identity_rout_raw_diff_ns",
    "job_argmax_shards",
    "handled_argmax_shards",
    "job_argmax_tie",
    "handled_argmax_tie",
    "argmax_any_overlap",
    "argmax_exact_set_match",
]


SHARD_FIELDS = [
    "session_id",
    "shard_index",
    "primary_session_included",
    "session_primary_exclusion_reason",
    "confirm_status",
    "confirm_mtime_ns",
    "handled_status",
    "handled_mtime_ns",
    "path_component_symlink",
    "request_id",
    "request_id_error",
    "accounting_lookup_mode",
    "accounting_candidate_count",
    "accounting_candidate_list_error",
    "accounting_path",
    "accounting_status",
    "accounting_errors",
    "request_name",
    "created_ns",
    "created_iso",
    "started_ns",
    "started_iso",
    "ended_ns",
    "ended_iso",
    "elapse_s",
    "job_span_ns",
    "scheduler_queue_ns",
    "run_display_ns",
    "receipt_status",
    "receipt_queue_wait_s",
    "outcome_kind",
    "outcome_reason",
    "checkout",
    "queue_wait_minus_scheduler_queue_s",
    "elapse_minus_ended_started_s",
    "report_status",
    "report_mtime_ns",
    "report_size",
    "shard_junit_status",
    "shard_junit_mtime_ns",
    "shard_junit_size",
    "is_job_span_argmax",
    "is_handled_argmax",
]


def exclusive_output_stream(path: Path, newline: Optional[str] = None) -> Any:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as exc:
        raise AnalysisError(f"cannot create output file {path}: {exc}") from exc
    try:
        return os.fdopen(descriptor, "w", encoding="utf-8", newline=newline)
    except (OSError, ValueError) as exc:
        os.close(descriptor)
        raise AnalysisError(f"cannot open output stream {path}: {exc}") from exc


def write_outputs(
    output: Path,
    rows: list[dict[str, Any]],
    shards: list[dict[str, Any]],
    summary: dict[str, Any],
    scheduler_tz: ZoneInfo,
) -> None:
    try:
        with exclusive_output_stream(output / "sessions.csv", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=SESSION_FIELDS, extrasaction="ignore", lineterminator="\n")
            writer.writeheader()
            for row in rows:
                rendered = dict(row)
                rendered["all_exclusion_reasons"] = ";".join(row["flags"])
                writer.writerow(rendered)
        with exclusive_output_stream(output / "shards.csv", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=SHARD_FIELDS, extrasaction="ignore", lineterminator="\n")
            writer.writeheader()
            for shard in shards:
                rendered = dict(shard)
                rendered["accounting_errors"] = ";".join(shard["accounting_errors"])
                rendered["created_iso"] = ns_to_iso(shard["created_ns"], scheduler_tz)
                rendered["started_iso"] = ns_to_iso(shard["started_ns"], scheduler_tz)
                rendered["ended_iso"] = ns_to_iso(shard["ended_ns"], scheduler_tz)
                writer.writerow(rendered)
        with exclusive_output_stream(output / "summary.json") as stream:
            json.dump(summary, stream, ensure_ascii=True, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
    except AnalysisError:
        raise
    except (OSError, TypeError, ValueError) as exc:
        raise AnalysisError(f"cannot write complete output set: {exc}") from exc


def inventory_root(root: Path) -> list[tuple[str, Path, str, Optional[int]]]:
    try:
        with os.scandir(root) as entries:
            raw_entries = list(entries)
    except OSError as exc:
        raise AnalysisError(f"cannot list input root: {exc}") from exc
    inventory: list[tuple[str, Path, str, Optional[int]]] = []
    for entry in raw_entries:
        try:
            value = entry.stat(follow_symlinks=False)
        except OSError:
            inventory.append((entry.name, root / entry.name, "stat_error", None))
            continue
        if stat.S_ISDIR(value.st_mode):
            inventory.append((entry.name, root / entry.name, "directory", value.st_mtime_ns))
    return sorted(inventory, key=lambda item: item[0])


def run(args: argparse.Namespace) -> int:
    root, output = validate_paths(args.root, args.output_dir)
    try:
        scheduler_tz = ZoneInfo(args.scheduler_timezone)
    except ZoneInfoNotFoundError as exc:
        raise AnalysisError(f"unknown scheduler timezone: {args.scheduler_timezone}") from exc
    if args.scheduler_timezone != "Asia/Tokyo":
        raise AnalysisError("this analysis contract requires --scheduler-timezone Asia/Tokyo")

    inventory_started = utc_now_iso()
    entries = inventory_root(root)
    rows: list[dict[str, Any]] = []
    shards: list[dict[str, Any]] = []
    for session_id, session_path, session_status, session_mtime_ns in entries:
        row, session_shards = analyze_session(
            root, session_id, session_path, session_status, session_mtime_ns, scheduler_tz
        )
        rows.append(row)
        for shard in session_shards:
            shard["primary_session_included"] = row["primary_included"]
            shard["session_primary_exclusion_reason"] = row["primary_exclusion_reason"]
        shards.extend(session_shards)
    inventory_ended = utc_now_iso()

    d1320 = d1320_check(rows, args.d1320_cutoff, args.d1320_cutoff_scan)
    summary, success = build_summary(
        root,
        output,
        args.scheduler_timezone,
        inventory_started,
        inventory_ended,
        rows,
        shards,
        d1320,
    )
    write_outputs(output, rows, shards, summary, scheduler_tz)

    oracle = summary["oracle"]
    print(
        f"T-2098 inventory: {len(rows)} sessions; "
        f"primary complete cases: {summary['inventory']['primary_included_sessions']}; "
        f"excluded: {summary['inventory']['primary_excluded_sessions']}."
    )
    print(
        f"Oracle {ORACLE_SESSION}: {oracle['status']} for all eight values. "
        f"D1320 cutoff reproduction with fallback: {d1320['with_fallback']['status']}; "
        f"without fallback: {d1320['without_fallback']['status']}."
    )
    print(f"Outputs: {output / 'sessions.csv'}, {output / 'shards.csv'}, {output / 'summary.json'}")
    return 0 if success else 3


def main() -> int:
    try:
        return run(parse_args())
    except AnalysisError as exc:
        print(f"T-2098 analysis failed: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("T-2098 analysis interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
