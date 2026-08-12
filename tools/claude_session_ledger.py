#!/usr/bin/env python3
"""Claude session JSONL から read-only な観測台帳を作る。

``model_calls`` は usage を持つ assistant response を file provenance 内で
``requestId`` / ``message.id`` alias により dedupe した件数であり、tool 呼び出し数では
ない。空でない canonical な ``message.id`` が一致する assistant 応答は同一の model
call であることを同一性の公理とし、検証済みの cross-file replica も全体で 1 回だけ
数える。入力は ``cache_read_input_tokens + cache_creation_input_tokens + input_tokens`` の
生トークン交通量であり、費用・課金・利用枠を表さない。
"""
from __future__ import annotations

import sys

_ORIGINAL_DONT_WRITE_BYTECODE = sys.dont_write_bytecode
try:
    # script 経由の補助 import が source tree に bytecode を残すことも避ける。
    sys.dont_write_bytecode = True
    import argparse
    import hashlib
    import json
    import os
    import re
    import stat as stat_module
    import unicodedata
    import uuid as uuid_module
    from dataclasses import dataclass
    from datetime import datetime, timezone
    from pathlib import Path
    from typing import Any, Sequence
finally:
    sys.dont_write_bytecode = _ORIGINAL_DONT_WRITE_BYTECODE


DEFAULT_PROJECTS_ROOT = "~/.claude/projects"
DEFAULT_MAX_FILES = 25
MAX_MAX_FILES = 1_000
MAX_TOTAL_BYTES = 512 * 1024 * 1024
MAX_LINE_BYTES = 16 * 1024 * 1024
MAX_RECORDS = 1_000_000
MAX_REQUESTS = 250_000
MAX_TOOL_IDENTITIES = 500_000
MAX_DISCOVERY_ENTRIES = 100_000
MAX_ISSUE_DETAILS = 100
MAX_CANONICAL_MESSAGE_ID_LENGTH = 256
DEDUP_ALGORITHM_VERSION = "canonical_message_id_usage_dominance_v1"
_CANONICAL_MESSAGE_ID = re.compile(r"msg_[A-Za-z0-9]+\Z")

USAGE_FIELDS = (
    "cache_read_input_tokens",
    "cache_creation_input_tokens",
    "input_tokens",
    "output_tokens",
)
STRICT_ISSUES = frozenset(
    {
        "alias_conflict",
        "discovery_limit_exceeded",
        "event_timestamp_out_of_order",
        "incomplete_event_timestamps",
        "invalid_timestamp",
        "line_too_long",
        "malformed_json",
        "malformed_usage",
        "message_id_collision",
        "missing_cwd",
        "missing_project",
        "missing_request_key",
        "non_regular_file",
        "path_outside_root",
        "record_limit_exceeded",
        "request_id_collision",
        "request_limit_exceeded",
        "root_missing",
        "terminal_usage_missing",
        "tool_identity_limit_exceeded",
        "total_bytes_limit_exceeded",
        "unreadable_directory",
        "unreadable_file",
        "usage_final_below_prior_max",
    }
)
FATAL_ISSUES = frozenset(
    {
        "alias_conflict",
        "discovery_limit_exceeded",
        "line_too_long",
        "message_id_collision",
        "non_regular_file",
        "path_outside_root",
        "record_limit_exceeded",
        "request_id_collision",
        "request_limit_exceeded",
        "root_missing",
        "tool_identity_limit_exceeded",
        "total_bytes_limit_exceeded",
        "unreadable_directory",
    }
)


def _default_projects_root() -> Path:
    return Path(DEFAULT_PROJECTS_ROOT).expanduser()


def _max_files(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("正の整数を指定すること") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("正の整数を指定すること")
    if parsed > MAX_MAX_FILES:
        raise argparse.ArgumentTypeError(f"{MAX_MAX_FILES} 以下を指定すること")
    return parsed


def _absolute_path(value: str) -> str:
    path = Path(value)
    if not path.is_absolute():
        raise argparse.ArgumentTypeError("絶対 path を指定すること")
    return os.fspath(path)


def _parser(*, include_cwd_under: bool = False) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Claude session JSONL を決定的に集計する read-only 台帳"
    )
    parser.add_argument("--projects-root", type=Path, default=None)
    parser.add_argument(
        "--project",
        action="append",
        default=[],
        metavar="SLUG",
        help="projects root 直下の project slug (複数指定は OR)",
    )
    parser.add_argument(
        "--cwd-contains",
        action="append",
        default=[],
        metavar="SUBSTR",
        help="record.cwd の部分一致 filter (複数指定は OR)",
    )
    if include_cwd_under:
        parser.add_argument(
            "--cwd-under",
            type=_absolute_path,
            default=None,
            metavar="ABS_PATH",
            help="record.cwd の path 境界一致 filter",
        )
    parser.add_argument("--since", metavar="ISO8601")
    parser.add_argument("--until", metavar="ISO8601")
    parser.add_argument("--max-files", type=_max_files, default=DEFAULT_MAX_FILES, metavar="N")
    parser.add_argument("--include-sidechains", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--strict", action="store_true")
    return parser


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _normalized_timestamp(
    value: str | None, parser: argparse.ArgumentParser
) -> tuple[datetime | None, str | None]:
    if value is None:
        return None, None
    parsed = _parse_timestamp(value)
    if parsed is None:
        parser.error(f"ISO8601 timestamp が不正: {value!r}")
    return parsed, parsed.isoformat()


def _new_metrics() -> dict[str, int]:
    return {
        "model_calls": 0,
        "tool_calls": 0,
        "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0,
        "input_tokens": 0,
        "raw_input_tokens": 0,
        "output_tokens": 0,
        "event_timestamp_model_calls": 0,
        "mtime_fallback_model_calls": 0,
        "synthetic_zero_usage_excluded": 0,
        "compaction_boundaries": 0,
    }


def _issue(issues: dict[str, list[str]], category: str, detail: str) -> None:
    bucket = issues.setdefault(category, [])
    if len(bucket) < MAX_ISSUE_DETAILS:
        bucket.append(detail)
    elif len(bucket) == MAX_ISSUE_DETAILS:
        bucket.append(f"<additional {category} details omitted>")


def _project_roots(
    projects_root: Path,
    project_filters: list[str],
    issues: dict[str, list[str]],
) -> list[Path]:
    if not project_filters:
        return [projects_root]
    roots: list[Path] = []
    for slug in sorted(set(project_filters)):
        if not slug or Path(slug).name != slug or slug in {".", ".."}:
            _issue(issues, "missing_project", f"invalid project slug: {slug!r}")
            continue
        candidate = projects_root / slug
        if not candidate.is_dir():
            _issue(issues, "missing_project", os.fspath(candidate))
            continue
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(projects_root)
        except ValueError:
            _issue(issues, "path_outside_root", f"{candidate} -> {resolved}")
            continue
        except OSError as exc:
            _issue(issues, "unreadable_directory", f"{candidate}: {type(exc).__name__}")
            continue
        if candidate.is_symlink():
            _issue(issues, "non_regular_file", os.fspath(candidate))
            continue
        roots.append(resolved)
    return roots


def _is_sidechain(path: Path, projects_root: Path) -> bool:
    try:
        relative = path.relative_to(projects_root)
    except ValueError:
        return False
    return "subagents" in relative.parts[:-1]


def _select_balanced_paths(
    root_candidates: list[Path], sidechain_candidates: list[Path], max_files: int
) -> tuple[list[Path], dict[str, Any], bool]:
    base_root = (max_files + 1) // 2
    base_sidechain = max_files // 2
    selected_root = min(base_root, len(root_candidates))
    selected_sidechain = min(base_sidechain, len(sidechain_candidates))
    remaining = max_files - selected_root - selected_sidechain

    # 予約枠が余った場合だけ、root→sidechain の round-robin で再配分する。
    while remaining:
        progressed = False
        if selected_root < len(root_candidates):
            selected_root += 1
            remaining -= 1
            progressed = True
        if remaining and selected_sidechain < len(sidechain_candidates):
            selected_sidechain += 1
            remaining -= 1
            progressed = True
        if not progressed:
            break

    selected = root_candidates[:selected_root] + sidechain_candidates[:selected_sidechain]
    selected.sort(key=os.fspath)
    allocation = {
        "policy": "balanced_root_sidechain_with_unused_quota_reassigned",
        "root_base_quota": base_root,
        "sidechain_base_quota": base_sidechain,
        "root_selected": selected_root,
        "sidechain_selected": selected_sidechain,
    }
    limit_reached = len(root_candidates) + len(sidechain_candidates) > len(selected)
    return selected, allocation, limit_reached


def _discover_paths(
    roots: list[Path],
    max_files: int,
    *,
    projects_root: Path,
    issues: dict[str, list[str]],
    counters: dict[str, Any],
) -> tuple[list[Path], dict[str, Any], bool]:
    root_candidates: list[Path] = []
    sidechain_candidates: list[Path] = []
    discovery_entries = 0
    stopped = False

    def onerror(exc: OSError) -> None:
        nonlocal stopped
        location = getattr(exc, "filename", None) or "<unknown directory>"
        _issue(issues, "unreadable_directory", f"{location}: {type(exc).__name__}")
        counters["directories_unreadable"] += 1
        stopped = True

    for root in sorted(set(roots), key=os.fspath):
        for current, directories, filenames in os.walk(
            root, followlinks=False, onerror=onerror
        ):
            directories.sort()
            for filename in sorted(filenames):
                discovery_entries += 1
                if discovery_entries > MAX_DISCOVERY_ENTRIES:
                    _issue(
                        issues,
                        "discovery_limit_exceeded",
                        f"entries > {MAX_DISCOVERY_ENTRIES}",
                    )
                    stopped = True
                    break
                if not filename.endswith(".jsonl"):
                    continue
                path = Path(current) / filename
                try:
                    resolved = path.resolve(strict=True)
                except OSError as exc:
                    _issue(issues, "unreadable_file", f"{path}: {type(exc).__name__}")
                    counters["files_unreadable"] += 1
                    continue
                try:
                    resolved.relative_to(projects_root)
                except ValueError:
                    _issue(issues, "path_outside_root", f"{path} -> {resolved}")
                    counters["paths_rejected"] += 1
                    continue
                try:
                    mode = path.lstat().st_mode
                except OSError as exc:
                    _issue(issues, "unreadable_file", f"{path}: {type(exc).__name__}")
                    counters["files_unreadable"] += 1
                    continue
                if not stat_module.S_ISREG(mode):
                    _issue(issues, "non_regular_file", os.fspath(path))
                    counters["paths_rejected"] += 1
                    continue
                bucket = (
                    sidechain_candidates
                    if _is_sidechain(resolved, projects_root)
                    else root_candidates
                )
                if len(bucket) <= max_files:
                    bucket.append(resolved)
                if len(root_candidates) > max_files and len(sidechain_candidates) > max_files:
                    stopped = True
                    break
            if stopped:
                break
        if stopped:
            break

    counters["discovery_entries"] = discovery_entries
    return _select_balanced_paths(root_candidates, sidechain_candidates, max_files)


def _usage(value: Any, *, location: str) -> tuple[dict[str, int] | None, list[str]]:
    if not isinstance(value, dict):
        return None, [f"{location}: usage is not an object"]
    result: dict[str, int] = {}
    errors: list[str] = []
    for field in USAGE_FIELDS:
        field_value = value.get(field)
        if isinstance(field_value, bool) or not isinstance(field_value, int):
            errors.append(f"{location}: {field} is not an int")
        elif field_value < 0:
            errors.append(f"{location}: {field} is negative")
        else:
            result[field] = field_value
    if errors:
        return None, errors
    return result, []


def _is_compaction(record: dict[str, Any]) -> bool:
    record_type = record.get("type")
    subtype = record.get("subtype")
    return bool(
        record_type == "compact_boundary"
        or record_type == "summary"
        or (record_type == "system" and subtype == "compact_boundary")
    )


def _record_meta(
    record: dict[str, Any],
    *,
    resolved_path: str,
    mtime: datetime,
    sidechain: bool,
    sequence: int,
    issues: dict[str, list[str]],
    location: str,
) -> dict[str, Any]:
    raw_timestamp = record.get("timestamp")
    event_timestamp = _parse_timestamp(raw_timestamp)
    invalid_timestamp = raw_timestamp not in (None, "") and event_timestamp is None
    if invalid_timestamp:
        _issue(issues, "invalid_timestamp", location)
    cwd = record.get("cwd")
    if not isinstance(cwd, str):
        cwd = ""
    return {
        "event_timestamp": event_timestamp,
        "invalid_timestamp": invalid_timestamp,
        "mtime": mtime,
        "cwd": cwd,
        "sidechain": sidechain,
        "path": resolved_path,
        "sequence": sequence,
    }


def _new_request(path: str, sidechain: bool) -> dict[str, Any]:
    return {
        "path": path,
        "sidechain": sidechain,
        "last_stream_meta": None,
        "last_stream_timestamp": None,
        "terminal_rank": None,
        "terminal_meta": None,
        "terminal_has_usage": False,
        "terminal_usage": None,
        "terminal_model": "",
        "usage_seen": 0,
        "usage_maxima": None,
        "timestamped_records": 0,
        "untimestamped_records": 0,
        "request_ids": set(),
        "message_ids": set(),
        "tools": set(),
        "member_anomaly": False,
        "assistant_records": 0,
        "clone_evidence": [],
        "clone_evidence_complete": True,
        "record_uuid_digests": {},
    }


def _is_canonical_message_id(value: str) -> bool:
    return bool(
        value
        and value.isascii()
        and len(value) <= MAX_CANONICAL_MESSAGE_ID_LENGTH
        and _CANONICAL_MESSAGE_ID.fullmatch(value)
    )


def _normalized_json_digest(value: Any) -> str | None:
    """JSON 値の全 string を NFC 化した canonical digest を返す。"""

    def normalize(item: Any) -> Any:
        if isinstance(item, str):
            return unicodedata.normalize("NFC", item)
        if isinstance(item, list):
            return [normalize(child) for child in item]
        if isinstance(item, dict):
            normalized = {}
            for key, child in item.items():
                normalized_key = normalize(key)
                if normalized_key in normalized:
                    raise ValueError("NFC-normalized object keys collide")
                normalized[normalized_key] = normalize(child)
            return normalized
        return item

    try:
        encoded = json.dumps(
            normalize(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError):
        return None
    return hashlib.sha256(encoded).hexdigest()


def _is_canonical_record_uuid(value: Any) -> bool:
    if not isinstance(value, str) or not value or not value.isascii():
        return False
    try:
        return str(uuid_module.UUID(value)) == value
    except (ValueError, AttributeError):
        return False


def _request_identity(
    record: dict[str, Any],
    message: dict[str, Any],
    *,
    path: str,
    sidechain: bool,
    location: str,
    state: dict[str, Any],
    issues: dict[str, list[str]],
) -> tuple[str, int] | None:
    request_id = record.get("requestId")
    if not isinstance(request_id, str) or not request_id:
        request_id = None
    message_id = message.get("id")
    if not isinstance(message_id, str) or not message_id:
        message_id = None
    if request_id is None and message_id is None:
        return None

    alias_keys: list[tuple[str, str, str]] = []
    if request_id is not None:
        alias_keys.append((path, "requestId", request_id))
    if message_id is not None:
        alias_keys.append((path, "message.id", message_id))
    mapped = {state["aliases"][key] for key in alias_keys if key in state["aliases"]}
    if len(mapped) > 1:
        detail = f"{location}: requestId/message.id map to distinct responses"
        _issue(issues, "alias_conflict", detail)
        state["identity_conflicts"].update(mapped)
        return None
    if mapped:
        canonical = next(iter(mapped))
    else:
        if len(state["requests"]) >= MAX_REQUESTS:
            _issue(
                issues,
                "request_limit_exceeded",
                f"requests >= {MAX_REQUESTS}",
            )
            state["resource_stop"] = True
            return None
        state["next_request"] += 1
        canonical = (path, state["next_request"])
        state["requests"][canonical] = _new_request(path, sidechain)

    request = state["requests"][canonical]
    proposed = (
        ("request_ids", request_id),
        ("message_ids", message_id),
    )
    for field, value in proposed:
        if value is None:
            continue
        known = request[field]
        if known and value not in known:
            _issue(
                issues,
                "alias_conflict",
                f"{location}: one response has multiple {field}",
            )
            state["identity_conflicts"].add(canonical)
            return None
    for alias_key in alias_keys:
        existing = state["aliases"].get(alias_key)
        if existing is not None and existing != canonical:
            _issue(issues, "alias_conflict", location)
            state["identity_conflicts"].update({existing, canonical})
            return None
        state["aliases"][alias_key] = canonical
        _, kind, value = alias_key
        state["raw_aliases"].setdefault((kind, value), set()).add(canonical)
    if request_id is not None:
        request["request_ids"].add(request_id)
    if message_id is not None:
        request["message_ids"].add(message_id)
    return canonical


def _selected(
    meta: dict[str, Any] | None,
    *,
    cwd_filters: list[str],
    cwd_under: str | None,
    since: datetime | None,
    until: datetime | None,
) -> bool:
    if meta is None:
        return False
    cwd = meta["cwd"]
    if cwd_filters and not any(needle in cwd for needle in cwd_filters):
        return False
    if cwd_under is not None and not (
        cwd == cwd_under or cwd.startswith(cwd_under + "/")
    ):
        return False
    effective = meta["event_timestamp"] or meta["mtime"]
    if since is not None and effective < since:
        return False
    if until is not None and effective >= until:
        return False
    return True


def _stream_file(
    path: Path,
    *,
    projects_root: Path,
    state: dict[str, Any],
    issues: dict[str, list[str]],
    counters: dict[str, Any],
    report: dict[str, Any],
    cwd_filters: list[str],
    cwd_under: str | None,
    since: datetime | None,
    until: datetime | None,
    sequence: int,
) -> tuple[int, bool]:
    sidechain = _is_sidechain(path, projects_root)
    resolved_path = os.fspath(path)
    try:
        current_resolved = path.resolve(strict=True)
        current_resolved.relative_to(projects_root)
        file_stat = path.lstat()
        if current_resolved != path or not stat_module.S_ISREG(file_stat.st_mode):
            _issue(issues, "non_regular_file", resolved_path)
            return sequence, False
        mtime = datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc)
        stream = path.open("rb")
    except ValueError:
        _issue(issues, "path_outside_root", resolved_path)
        return sequence, False
    except OSError as exc:
        _issue(issues, "unreadable_file", f"{resolved_path}: {type(exc).__name__}")
        counters["files_unreadable"] += 1
        return sequence, False

    malformed_file = False
    resource_stop = False
    with stream:
        line_number = 0
        while True:
            line = stream.readline(MAX_LINE_BYTES + 1)
            if not line:
                break
            line_number += 1
            counters["bytes_read"] += len(line)
            if counters["bytes_read"] > MAX_TOTAL_BYTES:
                _issue(
                    issues,
                    "total_bytes_limit_exceeded",
                    f"bytes read > {MAX_TOTAL_BYTES}",
                )
                resource_stop = True
                break
            if len(line) > MAX_LINE_BYTES:
                _issue(issues, "line_too_long", f"{resolved_path}:{line_number}")
                resource_stop = True
                break
            if counters["records_seen"] >= MAX_RECORDS:
                _issue(
                    issues,
                    "record_limit_exceeded",
                    f"records >= {MAX_RECORDS}",
                )
                resource_stop = True
                break
            counters["records_seen"] += 1
            location = f"{resolved_path}:{line_number}"
            try:
                record = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                _issue(issues, "malformed_json", location)
                counters["malformed_json_lines"] += 1
                malformed_file = True
                continue
            if not isinstance(record, dict):
                _issue(issues, "malformed_json", location)
                counters["malformed_json_lines"] += 1
                malformed_file = True
                continue
            sequence += 1
            meta = _record_meta(
                record,
                resolved_path=resolved_path,
                mtime=mtime,
                sidechain=sidechain,
                sequence=sequence,
                issues=issues,
                location=location,
            )
            if _is_compaction(record) and _selected(
                meta,
                cwd_filters=cwd_filters,
                cwd_under=cwd_under,
                since=since,
                until=until,
            ):
                report["sidechains" if sidechain else "root"]["compaction_boundaries"] += 1

            if record.get("type") != "assistant":
                continue
            message = record.get("message")
            if not isinstance(message, dict):
                message = {}
            content = message.get("content")
            tool_blocks = [
                (index, block)
                for index, block in enumerate(content if isinstance(content, list) else [])
                if isinstance(block, dict) and block.get("type") == "tool_use"
            ]
            has_usage = "usage" in message and message.get("usage") is not None
            canonical = _request_identity(
                record,
                message,
                path=resolved_path,
                sidechain=sidechain,
                location=location,
                state=state,
                issues=issues,
            )
            if canonical is None:
                if has_usage or tool_blocks:
                    request_id = record.get("requestId")
                    message_id = message.get("id")
                    if not request_id and not message_id:
                        _issue(issues, "missing_request_key", location)
                        counters["missing_request_key_records"] += 1
                if state["resource_stop"]:
                    resource_stop = True
                    break
                continue

            request = state["requests"][canonical]
            request["assistant_records"] += 1
            record_uuid = record.get("uuid")
            content_digest = _normalized_json_digest(content)
            usage_digest = _normalized_json_digest(message.get("usage"))
            model_for_evidence = message.get("model")
            if not isinstance(model_for_evidence, str):
                model_for_evidence = ""
            if (
                _is_canonical_record_uuid(record_uuid)
                and content_digest is not None
                and usage_digest is not None
            ):
                evidence = (
                    record_uuid,
                    content_digest,
                    usage_digest,
                    model_for_evidence,
                )
                request["clone_evidence"].append(evidence)
                request["record_uuid_digests"].setdefault(record_uuid, set()).add(
                    content_digest
                )
            else:
                request["clone_evidence_complete"] = False
            if meta["invalid_timestamp"]:
                request["member_anomaly"] = True
            previous_meta = request["last_stream_meta"]
            if not meta["cwd"] and previous_meta is not None:
                meta["cwd"] = previous_meta["cwd"]
            event_timestamp = meta["event_timestamp"]
            if event_timestamp is None:
                request["untimestamped_records"] += 1
            else:
                request["timestamped_records"] += 1
                previous_timestamp = request["last_stream_timestamp"]
                if previous_timestamp is not None and event_timestamp < previous_timestamp:
                    _issue(
                        issues,
                        "event_timestamp_out_of_order",
                        f"{resolved_path}:{line_number}",
                    )
                    request["member_anomaly"] = True
                request["last_stream_timestamp"] = event_timestamp
            request["last_stream_meta"] = meta

            rank = (
                1 if event_timestamp is not None else 0,
                event_timestamp or mtime,
                sequence,
            )
            terminal = request["terminal_rank"] is None or rank > request["terminal_rank"]
            if terminal:
                request["terminal_rank"] = rank
                request["terminal_meta"] = meta
                request["terminal_has_usage"] = has_usage
                request["terminal_usage"] = None
                request["terminal_model"] = ""

            for block_index, block in tool_blocks:
                tool_id = block.get("id")
                if isinstance(tool_id, str) and tool_id:
                    tool_key = ("id", tool_id)
                else:
                    tool_key = ("position", resolved_path, line_number, block_index)
                if tool_key not in request["tools"]:
                    if state["tool_identities"] >= MAX_TOOL_IDENTITIES:
                        _issue(
                            issues,
                            "tool_identity_limit_exceeded",
                            f"tool identities >= {MAX_TOOL_IDENTITIES}",
                        )
                        state["resource_stop"] = True
                        resource_stop = True
                        break
                    request["tools"].add(tool_key)
                    state["tool_identities"] += 1
            if resource_stop:
                break
            if not has_usage:
                continue

            request["usage_seen"] += 1
            parsed_usage, usage_errors = _usage(message.get("usage"), location=location)
            if parsed_usage is not None:
                maxima = request["usage_maxima"]
                if maxima is None:
                    request["usage_maxima"] = dict(parsed_usage)
                else:
                    for field in USAGE_FIELDS:
                        maxima[field] = max(maxima[field], parsed_usage[field])
            if usage_errors:
                counters["malformed_usage_records"] += 1
                request["member_anomaly"] = True
            for detail in usage_errors:
                _issue(issues, "malformed_usage", detail)
            if terminal:
                request["terminal_usage"] = parsed_usage
                model = message.get("model")
                if isinstance(model, str) and model:
                    request["terminal_model"] = model

    if malformed_file:
        counters["files_with_malformed_json"] += 1
    return sequence, resource_stop


def _member_local_validation(
    state: dict[str, Any],
    issues: dict[str, list[str]],
    *,
    cwd_filters: list[str],
    cwd_under: str | None,
    since: datetime | None,
    until: datetime | None,
) -> tuple[set[tuple[str, int]], set[tuple[str, int]]]:
    """相 1: replica 解決前に member 固有の anomaly をすべて確定する。"""
    anomalous = set(state["identity_conflicts"])
    aggregation_excluded = set(state["identity_conflicts"])
    cross_file_message_members: set[tuple[str, int]] = set()
    for (kind, _), raw_group in state["raw_aliases"].items():
        if kind == "message.id" and len({canonical[0] for canonical in raw_group}) > 1:
            cross_file_message_members.update(raw_group)
    for canonical in sorted(state["requests"]):
        if canonical in state["identity_conflicts"]:
            continue
        request = state["requests"][canonical]
        if request["member_anomaly"]:
            anomalous.add(canonical)
        request_key = f"{canonical[0]}#{canonical[1]}"
        if request["timestamped_records"] and request["untimestamped_records"]:
            _issue(issues, "incomplete_event_timestamps", request_key)
            anomalous.add(canonical)
            aggregation_excluded.add(canonical)
        if request["usage_seen"] and not request["terminal_has_usage"]:
            _issue(issues, "terminal_usage_missing", request_key)
            anomalous.add(canonical)
            aggregation_excluded.add(canonical)
        meta = request["terminal_meta"]
        if (
            (cwd_filters or cwd_under is not None)
            and meta is not None
            and not meta["cwd"]
        ):
            _issue(issues, "missing_cwd", request_key)
            anomalous.add(canonical)
            aggregation_excluded.add(canonical)
        usage = request["terminal_usage"]
        maxima = request["usage_maxima"]
        if usage is not None and maxima is not None:
            lower = [field for field in USAGE_FIELDS if usage[field] < maxima[field]]
            if lower:
                anomalous.add(canonical)
                if canonical in cross_file_message_members or _selected(
                    meta,
                    cwd_filters=cwd_filters,
                    cwd_under=cwd_under,
                    since=since,
                    until=until,
                ):
                    _issue(
                        issues,
                        "usage_final_below_prior_max",
                        f"{request_key}: {', '.join(lower)}",
                    )
    return anomalous, aggregation_excluded


def _dominates(left: dict[str, int], right: dict[str, int]) -> bool:
    return all(left[field] >= right[field] for field in USAGE_FIELDS)


def _replica_preference(
    canonical: tuple[str, int], state: dict[str, Any]
) -> tuple[bool, str, int]:
    request = state["requests"][canonical]
    return request["sidechain"], canonical[0], canonical[1]


def _resolve_cross_file_replicas(
    state: dict[str, Any],
    issues: dict[str, list[str]],
    *,
    member_anomalies: set[tuple[str, int]],
    cwd_filters: list[str],
    cwd_under: str | None,
    since: datetime | None,
    until: datetime | None,
) -> None:
    """final representative map と final invalid set は相 3 まで書かない。"""
    canonicals = set(state["requests"])
    planned_representatives = {canonical: canonical for canonical in canonicals}
    planned_invalid = set(state["identity_conflicts"])
    planned_sidechain = {
        canonical: state["requests"][canonical]["sidechain"]
        for canonical in canonicals
    }
    parent = {canonical: canonical for canonical in canonicals}

    def find(canonical: tuple[str, int]) -> tuple[str, int]:
        while parent[canonical] != canonical:
            parent[canonical] = parent[parent[canonical]]
            canonical = parent[canonical]
        return canonical

    def union(group: tuple[tuple[str, int], ...]) -> None:
        root = find(group[0])
        for canonical in group[1:]:
            other = find(canonical)
            if other != root:
                parent[other] = root

    def selector_verdicts(group: tuple[tuple[str, int], ...]) -> set[bool]:
        return {
            _selected(
                state["requests"][canonical]["terminal_meta"],
                cwd_filters=cwd_filters,
                cwd_under=cwd_under,
                since=since,
                until=until,
            )
            for canonical in group
        }

    def candidates_for(
        group: tuple[tuple[str, int], ...]
    ) -> list[tuple[str, int]]:
        candidates: list[tuple[str, int]] = []
        for candidate in group:
            candidate_request = state["requests"][candidate]
            candidate_usage = candidate_request["terminal_usage"]
            if candidate_usage is None:
                continue
            dominates_group = True
            for other in group:
                other_request = state["requests"][other]
                other_usage = other_request["terminal_usage"]
                if (
                    other_usage is None
                    or not _dominates(candidate_usage, other_usage)
                    or not other_request["tools"].issubset(
                        candidate_request["tools"]
                    )
                ):
                    dominates_group = False
                    break
            if dominates_group:
                candidates.append(candidate)
        return candidates

    def common_structure_is_valid(group: tuple[tuple[str, int], ...]) -> bool:
        requests = [state["requests"][canonical] for canonical in group]
        models = {request["terminal_model"] for request in requests}
        return bool(
            all(
                request["terminal_has_usage"]
                and request["terminal_usage"] is not None
                for request in requests
            )
            and len(models) == 1
            and not any(canonical in member_anomalies for canonical in group)
            and len(selector_verdicts(group)) == 1
            and candidates_for(group)
        )

    # 相 2a: canonical message.id を共有する replica edge を検証する。
    for (kind, value), raw_group in sorted(state["raw_aliases"].items()):
        if kind != "message.id":
            continue
        group = tuple(sorted(raw_group))
        provenances = {canonical[0] for canonical in group}
        if len(provenances) <= 1:
            continue
        requests = [state["requests"][canonical] for canonical in group]
        request_id_sets = {frozenset(request["request_ids"]) for request in requests}
        structurally_valid = bool(
            _is_canonical_message_id(value)
            and all(request["message_ids"] == {value} for request in requests)
            and len(request_id_sets) == 1
            and common_structure_is_valid(group)
        )
        if not structurally_valid:
            _issue(
                issues,
                "message_id_collision",
                f"{value}: {', '.join(sorted(provenances))}",
            )
            planned_invalid.update(group)
            continue
        union(group)

    # 相 2b: shared alias がなくても完全一致する record clone を検証する。
    uuid_members: dict[str, set[tuple[str, int]]] = {}
    clone_groups: dict[tuple[tuple[str, str, str, str], ...], set[tuple[str, int]]] = {}
    for canonical in sorted(canonicals):
        request = state["requests"][canonical]
        for record_uuid in request["record_uuid_digests"]:
            uuid_members.setdefault(record_uuid, set()).add(canonical)
        if (
            request["clone_evidence_complete"]
            and request["clone_evidence"]
            and len(request["clone_evidence"]) == request["assistant_records"]
        ):
            key = tuple(request["clone_evidence"])
            clone_groups.setdefault(key, set()).add(canonical)

    for record_uuid, raw_group in sorted(uuid_members.items()):
        group = tuple(sorted(raw_group))
        if len({canonical[0] for canonical in group}) <= 1:
            continue
        evidence_sets = {
            tuple(state["requests"][canonical]["clone_evidence"])
            if state["requests"][canonical]["clone_evidence_complete"]
            else ()
            for canonical in group
        }
        if len(evidence_sets) != 1 or not next(iter(evidence_sets)):
            _issue(
                issues,
                "message_id_collision",
                f"record uuid {record_uuid}: "
                f"{', '.join(sorted(canonical[0] for canonical in group))}",
            )
            planned_invalid.update(group)

    for evidence, raw_group in sorted(clone_groups.items()):
        group = tuple(sorted(raw_group))
        provenances = {canonical[0] for canonical in group}
        if len(provenances) <= 1:
            continue
        requests = [state["requests"][canonical] for canonical in group]
        message_ids = set().union(*(request["message_ids"] for request in requests))
        request_ids = set().union(*(request["request_ids"] for request in requests))
        structurally_valid = bool(
            len(message_ids) <= 1
            and len(request_ids) <= 1
            and all(_is_canonical_message_id(value) for value in message_ids)
            and common_structure_is_valid(group)
        )
        if not structurally_valid:
            _issue(
                issues,
                "message_id_collision",
                f"record clone {evidence[0][0]}: {', '.join(sorted(provenances))}",
            )
            planned_invalid.update(group)
            continue
        union(group)

    # 検証済み edge の connected component ごとに代表を一度だけ計画する。
    component_groups: dict[tuple[str, int], set[tuple[str, int]]] = {}
    for canonical in sorted(canonicals):
        component_groups.setdefault(find(canonical), set()).add(canonical)
    components = {canonical: {canonical} for canonical in canonicals}
    for raw_group in component_groups.values():
        if len(raw_group) <= 1:
            continue
        group = tuple(sorted(raw_group))
        candidates = candidates_for(group) if common_structure_is_valid(group) else []
        if not candidates:
            _issue(
                issues,
                "message_id_collision",
                "replica component: "
                + ", ".join(sorted(canonical[0] for canonical in group)),
            )
            planned_invalid.update(group)
            continue
        representative = min(
            candidates, key=lambda canonical: _replica_preference(canonical, state)
        )
        components[representative] = set(group)
        planned_sidechain[representative] = all(
            state["requests"][canonical]["sidechain"] for canonical in group
        )
        for canonical in group:
            planned_representatives[canonical] = representative

    # 相 2c: message representative へ写像した後の requestId 再利用を検証する。
    for (kind, value), raw_group in sorted(state["raw_aliases"].items()):
        if kind != "requestId":
            continue
        group = tuple(sorted(raw_group))
        provenances = {canonical[0] for canonical in group}
        if len(provenances) <= 1:
            continue
        if all(canonical in planned_invalid for canonical in group):
            continue
        mapped = {planned_representatives[canonical] for canonical in group}
        if len(mapped) <= 1:
            continue
        _issue(
            issues,
            "request_id_collision",
            f"{value}: {', '.join(sorted(provenances))}",
        )
        for representative in mapped:
            planned_invalid.update(components[representative])

    # 相 3: 全群の検証後に初めて representative map と invalid 集合を書く。
    for component in components.values():
        if component.intersection(planned_invalid):
            planned_invalid.update(component)
    state["representatives"] = planned_representatives
    state["representative_sidechain"] = planned_sidechain
    state["invalid_requests"] = planned_invalid


def _add_request(
    metrics: dict[str, int],
    request: dict[str, Any],
) -> None:
    metrics["tool_calls"] += len(request["tools"])
    usage = request["terminal_usage"]
    if usage is None:
        return
    if request["terminal_model"] == "<synthetic>" and all(
        usage[field] == 0 for field in USAGE_FIELDS
    ):
        metrics["synthetic_zero_usage_excluded"] += 1
        return
    metrics["model_calls"] += 1
    for field in USAGE_FIELDS:
        metrics[field] += usage[field]
    metrics["raw_input_tokens"] += (
        usage["cache_read_input_tokens"]
        + usage["cache_creation_input_tokens"]
        + usage["input_tokens"]
    )
    usage_meta = request["terminal_meta"]
    if usage_meta["event_timestamp"] is None:
        metrics["mtime_fallback_model_calls"] += 1
    else:
        metrics["event_timestamp_model_calls"] += 1


def _combined(root: dict[str, int], sidechains: dict[str, int]) -> dict[str, int]:
    return {key: root[key] + sidechains[key] for key in root}


def _render(report: dict[str, Any]) -> str:
    population = report["population"]
    window = population["time_window"]
    allocation = population["file_allocation"]
    lines = [
        "Claude session ledger (read-only)",
        "母集団:",
        f"  projects root: {population['projects_root']}",
        f"  project filter (OR): {population['project_filters'] or ['<all>']}",
        f"  cwd filter (OR): {population['cwd_contains_filters'] or ['<all>']}",
        f"  時間窓: [{window['since_inclusive'] or '-'}, {window['until_exclusive'] or '-'})",
        "  時間判定: record の event timestamp を優先し、全欠損 request だけ file mtime へ退避",
        f"  走査 file: {population['files_scanned']} / 上限 {population['max_files']}"
        f" (打切り={'yes' if population['limit_reached'] else 'no'})",
        "  file 配分 (root/sidechain): "
        f"{allocation['root_selected']}/{allocation['sidechain_selected']} "
        f"(基準枠 {allocation['root_base_quota']}/{allocation['sidechain_base_quota']}; "
        "未使用枠は再配分)",
        f"  読取 bytes: {population['bytes_read']} / 上限 {population['hard_limits']['total_bytes']}",
        f"  読めなかった file: {population['files_unreadable']}",
        f"  読めなかった directory: {population['directories_unreadable']}",
        f"  壊れた JSONL file/行: {population['files_with_malformed_json']}/"
        f"{population['malformed_json_lines']}",
    ]
    for label, key in (("root", "root"), ("sidechain", "sidechains")):
        metrics = report[key]
        lines.extend(
            [
                f"{label}:",
                f"  model call (応答数): {metrics['model_calls']}",
                f"  tool 呼び出し数: {metrics['tool_calls']}",
                f"  生入力トークン: {metrics['raw_input_tokens']}",
                f"    cache read 入力トークン: {metrics['cache_read_input_tokens']}",
                f"    cache creation 入力トークン: {metrics['cache_creation_input_tokens']}",
                f"    通常入力トークン (input_tokens): {metrics['input_tokens']}",
                f"  出力トークン: {metrics['output_tokens']}",
                f"  時間判定 (event timestamp/mtime): "
                f"{metrics['event_timestamp_model_calls']}/"
                f"{metrics['mtime_fallback_model_calls']}",
                f"  除外した synthetic 全ゼロ応答: "
                f"{metrics['synthetic_zero_usage_excluded']}",
                f"  compaction 境界: {metrics['compaction_boundaries']}",
            ]
        )
    if "combined" in report:
        metrics = report["combined"]
        lines.extend(
            [
                "root + sidechain (明示合算):",
                f"  model call (応答数): {metrics['model_calls']}",
                f"  tool 呼び出し数: {metrics['tool_calls']}",
                f"  生入力トークン: {metrics['raw_input_tokens']}",
                f"  出力トークン: {metrics['output_tokens']}",
            ]
        )
    lines.append("context 曲線: compaction 境界を跨ぐ単調曲線は算出しない")
    for category, details in report["issues"].items():
        for detail in details:
            lines.append(f"ISSUE\t{category}\t{detail}")
    return "\n".join(lines) + "\n"


def _empty_report(
    *,
    projects_root: Path,
    project_filters: list[str],
    cwd_filters: list[str],
    since_text: str | None,
    until_text: str | None,
    max_files: int,
) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "population": {
            "projects_root": os.fspath(projects_root),
            "project_filters": sorted(set(project_filters)),
            "cwd_contains_filters": sorted(set(cwd_filters)),
            "request_identity": (
                "resolved_file_provenance_aliases_with_verified_cross_file_"
                "canonical_message.id_replicas"
            ),
            "dedup_algorithm_version": DEDUP_ALGORITHM_VERSION,
            "dedup_comparison_compatibility": (
                "incomparable_with_reports_without_dedup_algorithm_version"
            ),
            "time_window": {
                "since_inclusive": since_text,
                "until_exclusive": until_text,
                "basis": "event_timestamp_then_file_mtime",
            },
            "max_files": max_files,
            "limit_reached": False,
            "file_allocation": {
                "policy": "balanced_root_sidechain_with_unused_quota_reassigned",
                "root_base_quota": (max_files + 1) // 2,
                "sidechain_base_quota": max_files // 2,
                "root_selected": 0,
                "sidechain_selected": 0,
            },
            "files_scanned": 0,
            "root_files_scanned": 0,
            "sidechain_files_scanned": 0,
            "files_unreadable": 0,
            "directories_unreadable": 0,
            "paths_rejected": 0,
            "discovery_entries": 0,
            "bytes_read": 0,
            "records_seen": 0,
            "files_with_malformed_json": 0,
            "malformed_json_lines": 0,
            "malformed_usage_records": 0,
            "missing_request_key_records": 0,
            "hard_limits": {
                "max_files": MAX_MAX_FILES,
                "total_bytes": MAX_TOTAL_BYTES,
                "line_bytes": MAX_LINE_BYTES,
                "records": MAX_RECORDS,
                "requests": MAX_REQUESTS,
                "tool_identities": MAX_TOOL_IDENTITIES,
                "discovery_entries": MAX_DISCOVERY_ENTRIES,
                "issue_details_per_category": MAX_ISSUE_DETAILS,
            },
        },
        "root": _new_metrics(),
        "sidechains": _new_metrics(),
        "issues": {},
    }


def _exit_code(report: dict[str, Any], *, strict: bool) -> int:
    issues = report["issues"]
    if any(issues.get(category) for category in FATAL_ISSUES):
        return 2
    if strict and any(issues.get(category) for category in STRICT_ISSUES):
        return 2
    return 0


@dataclass(frozen=True)
class CollectionResult:
    report: dict[str, Any]
    exit_code: int
    as_json: bool
    strict: bool


def collect_report(argv: Sequence[str] | None = None) -> CollectionResult:
    """CLI と同じ selector で schema v2 report を収集する公開 API。"""
    parser = _parser(include_cwd_under=True)
    args = parser.parse_args(argv)
    since, since_text = _normalized_timestamp(args.since, parser)
    until, until_text = _normalized_timestamp(args.until, parser)
    if since is not None and until is not None and since > until:
        parser.error("--since は --until 以下であること")

    projects_root = (args.projects_root or _default_projects_root()).resolve()
    report = _empty_report(
        projects_root=projects_root,
        project_filters=args.project,
        cwd_filters=args.cwd_contains,
        since_text=since_text,
        until_text=until_text,
        max_files=args.max_files,
    )
    population = report["population"]
    issues: dict[str, list[str]] = report["issues"]
    state: dict[str, Any] = {
        "requests": {},
        "aliases": {},
        "raw_aliases": {},
        "identity_conflicts": set(),
        "next_request": 0,
        "tool_identities": 0,
        "resource_stop": False,
    }
    if not projects_root.is_dir():
        _issue(issues, "root_missing", os.fspath(projects_root))
    else:
        roots = _project_roots(projects_root, args.project, issues)
        paths, allocation, limit_reached = _discover_paths(
            roots,
            args.max_files,
            projects_root=projects_root,
            issues=issues,
            counters=population,
        )
        population["file_allocation"] = allocation
        population["limit_reached"] = limit_reached
        sequence = 0
        admitted_bytes = 0
        for path in paths:
            try:
                file_size = path.stat().st_size
            except OSError as exc:
                _issue(issues, "unreadable_file", f"{path}: {type(exc).__name__}")
                population["files_unreadable"] += 1
                continue
            if admitted_bytes + file_size > MAX_TOTAL_BYTES:
                _issue(
                    issues,
                    "total_bytes_limit_exceeded",
                    f"selected bytes > {MAX_TOTAL_BYTES}",
                )
                break
            admitted_bytes += file_size
            sidechain = _is_sidechain(path, projects_root)
            population["files_scanned"] += 1
            population[
                "sidechain_files_scanned" if sidechain else "root_files_scanned"
            ] += 1
            sequence, resource_stop = _stream_file(
                path,
                projects_root=projects_root,
                state=state,
                issues=issues,
                counters=population,
                report=report,
                cwd_filters=args.cwd_contains,
                cwd_under=args.cwd_under,
                since=since,
                until=until,
                sequence=sequence,
            )
            if resource_stop:
                break

        member_anomalies, aggregation_excluded = _member_local_validation(
            state,
            issues,
            cwd_filters=args.cwd_contains,
            cwd_under=args.cwd_under,
            since=since,
            until=until,
        )
        _resolve_cross_file_replicas(
            state,
            issues,
            member_anomalies=member_anomalies,
            cwd_filters=args.cwd_contains,
            cwd_under=args.cwd_under,
            since=since,
            until=until,
        )
        for canonical in sorted(state["requests"]):
            representative = state["representatives"][canonical]
            if canonical != representative:
                continue
            if canonical in state["invalid_requests"] or canonical in aggregation_excluded:
                continue
            request = state["requests"][canonical]
            request_key = f"{canonical[0]}#{canonical[1]}"
            meta = request["terminal_meta"]
            if not _selected(
                meta,
                cwd_filters=args.cwd_contains,
                cwd_under=args.cwd_under,
                since=since,
                until=until,
            ):
                continue
            metrics = report[
                "sidechains"
                if state["representative_sidechain"][canonical]
                else "root"
            ]
            _add_request(metrics, request)

    report["issues"] = {
        key: sorted(set(value)) for key, value in sorted(issues.items())
    }
    if args.include_sidechains:
        report["combined"] = _combined(report["root"], report["sidechains"])
    rc = _exit_code(report, strict=args.strict)
    return CollectionResult(
        report=report,
        exit_code=rc,
        as_json=args.as_json,
        strict=args.strict,
    )


def main(argv: Sequence[str] | None = None) -> int:
    result = collect_report(argv)
    if result.as_json:
        sys.stdout.write(
            json.dumps(
                result.report,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        )
    else:
        sys.stdout.write(_render(result.report))

    if result.exit_code:
        for category in sorted(result.report["issues"]):
            if category in FATAL_ISSUES or (
                result.strict and category in STRICT_ISSUES
            ):
                prefix = "strict" if result.strict else "fatal"
                for detail in result.report["issues"][category]:
                    print(f"{prefix}: {category}: {detail}", file=sys.stderr)
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
