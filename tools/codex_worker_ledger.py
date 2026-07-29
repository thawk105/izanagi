#!/usr/bin/env python3
"""Codex rollout JSONL から read-only な worker 資源台帳を作る。

``model_calls`` は ``info`` が JSON object の ``token_count`` event 数であり、
推論上の turn 数を推測した値ではない。``turn_contexts`` は ``turn_context`` 行数で
ある。この二つを分離して、rollout が直接持つ観測値だけを公開する。
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


_TOOLS_DIR = Path(__file__).resolve().parent
_VALIDATOR_PATH = _TOOLS_DIR / "check_codex_output.py"
_VALIDATOR_SPEC = importlib.util.spec_from_file_location(
    "codex_output_validator_for_ledger", _VALIDATOR_PATH
)
if _VALIDATOR_SPEC is None or _VALIDATOR_SPEC.loader is None:
    raise ImportError(f"validator を import できない: {_VALIDATOR_PATH}")
_VALIDATOR = importlib.util.module_from_spec(_VALIDATOR_SPEC)
_ORIGINAL_DONT_WRITE_BYTECODE = sys.dont_write_bytecode
try:
    # read-only CLI 自身の import が tools/__pycache__ を生成するのも禁止する。
    sys.dont_write_bytecode = True
    _VALIDATOR_SPEC.loader.exec_module(_VALIDATOR)
finally:
    sys.dont_write_bytecode = _ORIGINAL_DONT_WRITE_BYTECODE

STAGES = ("plan", "consult", "author", "review", "fix", "focus")
STAGE_VALUES = STAGES + ("unclassified",)

# stage は prompt 中の役割語ではなく段番号で決める。role=author は権限 role 名に
# すぎないため、author は段5だけ、段6の実装作業は役割語にかかわらず fix とする。
# focus は段6の focused reviewer、review は段6の非 focused reviewer に限定する。
STAGE_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"段6(?:の)?\s*(?:fix(?:2)?\s*後の\s+)?read-only\s+focused\s+"
            r"(?:adversarial\s+)?reviewer",
            re.IGNORECASE,
        ),
        "focus",
    ),
    (
        re.compile(
            r"段6(?:の)?\s*(?:(?:Codex\s+)?fix\s+worker|"
            r"fix2\s+implementation\s+author)",
            re.IGNORECASE,
        ),
        "fix",
    ),
    (
        re.compile(r"段2(?:の)?\s*read-only\s+Codex\s+planner", re.IGNORECASE),
        "plan",
    ),
    (
        re.compile(
            r"段3(?:の)?\s*read-only\s+adversarial\s+consultant",
            re.IGNORECASE,
        ),
        "consult",
    ),
    (
        re.compile(
            r"段5(?:の)?\s*Codex\s+implementation\s+worker"
            r"\s*\(\s*`?role=author`?\s*\)",
            re.IGNORECASE,
        ),
        "author",
    ),
    (
        re.compile(
            r"段6(?:の)?\s*read-only\s+(?:adversarial\s+)?reviewer",
            re.IGNORECASE,
        ),
        "review",
    ),
)

# turn_aborted は task_complete の有無にかかわらず最も具体的な終了事実なので、
# incomplete より優先する。
OUTCOME_PRECEDENCE = ("aborted_turn", "incomplete", "fragment", "completed")

WORKLOG_BUCKETS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("planner", ("plan",)),
    ("consult", ("consult",)),
    ("author・fix", ("author", "fix")),
    ("review", ("review", "focus")),
)

_WORKLOG_EFFORT_RE = re.compile(
    r"エージェント工数\s*:\s*Codex\s*"
    r"(?P<total>[0-9０-９,，]+)\s*job\s*"
    r"\(\s*planner\s*(?P<planner>[0-9０-９,，]+)\s*/\s*"
    r"consult\s*(?P<consult>[0-9０-９,，]+)\s*/\s*"
    r"author・fix\s*(?P<author_fix>[0-9０-９,，]+)\s*/\s*"
    r"review\s*(?P<review>[0-9０-９,，]+)\s*\)"
)


def _default_sessions_root() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "sessions"
    return Path("~/.codex/sessions").expanduser()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Codex rollout JSONL を決定的に集計する read-only 台帳"
    )
    parser.add_argument(
        "--sessions-root",
        type=Path,
        default=None,
        help="rollout-*.jsonl を再帰探索する root",
    )
    parser.add_argument(
        "--cwd-contains",
        action="append",
        default=[],
        metavar="SUBSTR",
        help="session_meta.cwd の部分一致 filter (複数指定は OR)",
    )
    parser.add_argument(
        "--stage-map",
        metavar="JSON",
        help='session override JSON: {"<session_id>": "<stage>"}',
    )
    parser.add_argument("--worklog", type=Path)
    parser.add_argument("--worklog-entry", metavar="SUBSTR")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--strict", action="store_true")
    return parser


_REQUIRED_USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "total_tokens",
)
_USAGE_FIELDS = _REQUIRED_USAGE_FIELDS[:-1] + (
    "reasoning_output_tokens",
    "total_tokens",
)


def _validated_usage(
    usage: Any, *, location: str
) -> tuple[dict[str, int] | None, list[str]]:
    if not isinstance(usage, dict):
        return None, [f"{location} is not an object"]
    errors: list[str] = []
    result: dict[str, int] = {}
    for field in _REQUIRED_USAGE_FIELDS:
        value = usage.get(field)
        # bool は int の subclass だが token count としては schema 違反である。
        if isinstance(value, bool) or not isinstance(value, int):
            errors.append(f"{location}.{field} is not an int")
        elif value < 0:
            errors.append(f"{location}.{field} is negative")
        else:
            result[field] = value
    reasoning = usage.get("reasoning_output_tokens", 0)
    if isinstance(reasoning, bool) or not isinstance(reasoning, int):
        errors.append(
            f"{location}.reasoning_output_tokens is not an int"
        )
    else:
        result["reasoning_output_tokens"] = reasoning
    if errors:
        return None, errors
    return result, []


def _billable(usage: dict[str, int]) -> int:
    return (
        usage["input_tokens"]
        - usage["cached_input_tokens"]
        + usage["output_tokens"]
    )


def _new_record(path: Path) -> dict[str, Any]:
    return {
        "path": os.fspath(path.resolve()),
        "session_id": None,
        "timestamp": "",
        "cwd": "",
        "session_meta_count": 0,
        "session_meta_has_cwd": False,
        "session_meta_cwds": [],
        "session_meta_ids": [],
        "model": "",
        "reasoning": "",
        "prompt": "",
        "model_calls": 0,
        "turn_contexts": 0,
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
        "cli_reported": 0,
        "per_turn_sum": 0,
        "cumulative_minus_per_turn": 0,
        "total_tokens_raw": 0,
        "task_complete": False,
        "context_compacted": 0,
        "thread_rolled_back": 0,
        "turn_aborted": 0,
        "last_agent_message": None,
        "saw_user_message": False,
    }


def _stream_rollout(path: Path) -> tuple[dict[str, Any], dict[str, list[str]]]:
    record = _new_record(path)
    issues: dict[str, list[str]] = {}
    first_turn_context: tuple[str, str] | None = None
    previous_cumulative_total: int | None = None
    with path.open("rb") as stream:
        for line_number, line in enumerate(stream, 1):
            line_location = f"{record['path']}:{line_number}"
            try:
                item = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                issues.setdefault("malformed_json", []).append(line_location)
                continue
            if not isinstance(item, dict):
                issues.setdefault("malformed_json", []).append(line_location)
                continue
            item_type = item.get("type")
            payload = item.get("payload")
            if not isinstance(payload, dict):
                payload = {}
            if item_type == "session_meta":
                record["session_meta_count"] += 1
                if record["session_meta_count"] == 2:
                    issues.setdefault("multiple_session_meta", []).append(
                        record["path"]
                    )
                session_id = payload.get("session_id")
                if isinstance(session_id, str) and session_id:
                    normalized_id = session_id.lower()
                    record["session_meta_ids"].append(normalized_id)
                    if record["session_id"] is None:
                        record["session_id"] = normalized_id
                        record["timestamp"] = str(
                            payload.get("timestamp", "")
                        )
                cwd = payload.get("cwd")
                if isinstance(cwd, str) and cwd:
                    record["session_meta_cwds"].append(cwd)
                    if not record["cwd"]:
                        record["cwd"] = cwd
                    record["session_meta_has_cwd"] = True
                continue
            if item_type == "turn_context":
                record["turn_contexts"] += 1
                model = str(payload.get("model", item.get("model", "")))
                reasoning = str(
                    payload.get("effort", item.get("effort", ""))
                )
                context = (model, reasoning)
                if first_turn_context is None:
                    first_turn_context = context
                    record["model"] = model
                    record["reasoning"] = reasoning
                elif context != first_turn_context:
                    issues.setdefault(
                        "inconsistent_turn_context", []
                    ).append(
                        f"{line_location}: "
                        f"{context!r} != {first_turn_context!r}"
                    )
                continue
            if item_type != "event_msg":
                continue
            event_type = payload.get("type")
            if event_type == "user_message" and not record["saw_user_message"]:
                record["prompt"] = str(payload.get("message", ""))
                record["saw_user_message"] = True
            elif event_type == "agent_message":
                record["last_agent_message"] = str(payload.get("message", ""))
            elif event_type == "task_complete":
                record["task_complete"] = True
            elif event_type == "context_compacted":
                record["context_compacted"] += 1
            elif event_type == "thread_rolled_back":
                record["thread_rolled_back"] += 1
            elif event_type == "turn_aborted":
                record["turn_aborted"] += 1
            elif event_type == "token_count":
                info = payload.get("info")
                if not isinstance(info, dict):
                    continue
                record["model_calls"] += 1
                total_usage, total_errors = _validated_usage(
                    info.get("total_token_usage"),
                    location=f"{line_location} total_token_usage",
                )
                last_usage, last_errors = _validated_usage(
                    info.get("last_token_usage"),
                    location=f"{line_location} last_token_usage",
                )
                if total_errors or last_errors:
                    issues.setdefault("malformed_usage", []).extend(
                        total_errors + last_errors
                    )
                if total_usage is not None:
                    cumulative_total = total_usage["total_tokens"]
                    if (
                        previous_cumulative_total is not None
                        and cumulative_total < previous_cumulative_total
                    ):
                        issues.setdefault(
                            "non_monotonic_cumulative", []
                        ).append(
                            f"{line_location}: {cumulative_total} < "
                            f"{previous_cumulative_total}"
                        )
                    previous_cumulative_total = cumulative_total
                    for field in _USAGE_FIELDS[:-1]:
                        record[field] = total_usage[field]
                    record["cli_reported"] = _billable(total_usage)
                    record["total_tokens_raw"] = cumulative_total
                if last_usage is not None:
                    record["per_turn_sum"] += _billable(last_usage)
    record["cumulative_minus_per_turn"] = (
        record["cli_reported"] - record["per_turn_sum"]
    )
    return record, issues


def _stage_prefix(prompt: str) -> str:
    # dev-wave の role 宣言は先頭行に置かれる。先頭 400 文字では同じ段落内の
    # 引用 role まで拾いうるため、先頭の非空行だけを分類面にする。
    return next((line for line in prompt.splitlines() if line.strip()), "")


def _classify_stage(prompt: str) -> tuple[str, tuple[str, ...]]:
    prefix = _stage_prefix(prompt)
    matches = tuple(
        sorted({stage for pattern, stage in STAGE_RULES if pattern.search(prefix)})
    )
    if len(matches) == 1:
        return matches[0], matches
    return "unclassified", matches


def _validator_accepts(message: str | None) -> bool:
    """既存 validator の既定 regular-file 受理集合と同値な本文判定。"""
    if message is None:
        return False
    raw = message.encode("utf-8")
    if (
        len(raw) < _VALIDATOR._DEFAULT_MIN_BYTES
        or len(raw) > _VALIDATOR._MAX_READ_BYTES
    ):
        return False
    body = _VALIDATOR._without_fenced_code(message)
    heading = re.compile(_VALIDATOR._DEFAULT_HEADING, re.MULTILINE)
    return heading.search(body) is not None


def _classify_outcome(record: dict[str, Any]) -> str:
    if record["turn_aborted"]:
        return "aborted_turn"
    if not record["task_complete"]:
        return "incomplete"
    if not _validator_accepts(record["last_agent_message"]):
        return "fragment"
    return "completed"


def _timestamp_key(record: dict[str, Any]) -> tuple[int, str, str]:
    value = record["timestamp"]
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        normalized = parsed.astimezone(timezone.utc).isoformat()
        return (0, normalized, str(record["session_id"]))
    except (ValueError, AttributeError):
        return (1, str(value), str(record["session_id"]))


def _normalized_prompt_hash(prompt: str) -> str:
    normalized = " ".join(prompt.strip().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _assign_retries(records: list[dict[str, Any]]) -> None:
    by_wave_and_hash: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for record in records:
        digest = _normalized_prompt_hash(record["prompt"])
        record["prompt_hash"] = digest
        by_wave_and_hash.setdefault((record["cwd"], digest), []).append(record)
    repeated = [
        (min(_timestamp_key(item) for item in group), key, group)
        for key, group in by_wave_and_hash.items()
        if len(group) > 1
    ]
    repeated.sort(key=lambda item: (item[0], item[1]))
    for group_number, (_, _key, group) in enumerate(repeated, 1):
        for retry_index, record in enumerate(sorted(group, key=_timestamp_key), 1):
            record["retry_group"] = group_number
            record["retry_index"] = retry_index
    for record in records:
        record.setdefault("retry_group", None)
        record.setdefault("retry_index", 0)


def _parse_stage_map(parser: argparse.ArgumentParser, raw: str | None) -> dict[str, str]:
    if raw is None:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        parser.error(f"--stage-map JSON が不正: {exc}")
    if not isinstance(parsed, dict):
        parser.error("--stage-map は JSON object であること")
    result: dict[str, str] = {}
    for session_id, stage in parsed.items():
        if not isinstance(session_id, str) or not isinstance(stage, str):
            parser.error("--stage-map の key/value は文字列であること")
        if stage not in STAGE_VALUES:
            parser.error(
                f"--stage-map の stage が不正: {stage!r} "
                f"(allowed: {', '.join(STAGE_VALUES)})"
            )
        normalized_id = session_id.lower()
        if normalized_id in result and result[normalized_id] != stage:
            parser.error(
                "--stage-map に case 正規化後の同一 session_id が"
                "異なる stage で重複している"
            )
        result[normalized_id] = stage
    return result


def _number(value: str) -> int:
    normalized = unicodedata.normalize("NFKC", value).replace(",", "")
    return int(normalized)


def _worklog_expectation(
    path: Path, entry_substring: str
) -> tuple[dict[str, int] | None, list[str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return None, [f"worklog を読めない: {os.fspath(path)} ({exc})"]
    lines = text.splitlines()
    visible_lines: list[str | None] = []
    fence_marker: str | None = None
    fence_width = 0
    fence_open = re.compile(r"^[ \t]*(`{3,}|~{3,})")
    for line in lines:
        stripped = line.rstrip()
        if fence_marker is None:
            opening = fence_open.match(stripped)
            if opening:
                marker = opening.group(1)
                fence_marker = marker[0]
                fence_width = len(marker)
                visible_lines.append(None)
            else:
                visible_lines.append(line)
            continue
        if re.fullmatch(
            rf"[ \t]*{re.escape(fence_marker)}{{{fence_width},}}[ \t]*",
            stripped,
        ):
            fence_marker = None
            fence_width = 0
        visible_lines.append(None)

    heading_re = re.compile(r"^(#{1,6})\s+(.*)$")
    matches: list[tuple[int, int]] = []
    for index, line in enumerate(visible_lines):
        if line is None:
            continue
        heading = heading_re.match(line)
        if heading and entry_substring in heading.group(2):
            matches.append((index, len(heading.group(1))))
    if len(matches) != 1:
        return None, [
            "worklog entry が"
            + ("見つからない" if not matches else f"一意でない ({len(matches)} 件)")
            + f": {entry_substring!r}"
        ]
    start, level = matches[0]
    end = len(lines)
    for index in range(start + 1, len(lines)):
        line = visible_lines[index]
        heading = heading_re.match(line) if line is not None else None
        if heading and len(heading.group(1)) <= level:
            end = index
            break
    effort_matches = [
        match
        for line in visible_lines[start + 1 : end]
        if line is not None and (match := _WORKLOG_EFFORT_RE.search(line))
    ]
    if len(effort_matches) != 1:
        return None, [
            "worklog のエージェント工数行が"
            + (
                "見つからない"
                if not effort_matches
                else f"一意でない ({len(effort_matches)} 件)"
            )
        ]
    match = effort_matches[0]
    return {
        "total": _number(match.group("total")),
        "planner": _number(match.group("planner")),
        "consult": _number(match.group("consult")),
        "author・fix": _number(match.group("author_fix")),
        "review": _number(match.group("review")),
    }, []


def _compare_worklog(
    records: list[dict[str, Any]], expected: dict[str, int]
) -> list[str]:
    actual = {"total": len(records)}
    for bucket, stages in WORKLOG_BUCKETS:
        actual[bucket] = sum(record["stage"] in stages for record in records)
    mismatches: list[str] = []
    for bucket in ("total", "planner", "consult", "author・fix", "review"):
        if expected[bucket] != actual[bucket]:
            mismatches.append(
                f"worklog mismatch {bucket}: expected {expected[bucket]}, "
                f"actual {actual[bucket]}"
            )
    return mismatches


def _totals(records: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "sessions": len(records),
        "model_calls": sum(record["model_calls"] for record in records),
        "turn_contexts": sum(record["turn_contexts"] for record in records),
        "input_tokens": sum(record["input_tokens"] for record in records),
        "cached_input_tokens": sum(
            record["cached_input_tokens"] for record in records
        ),
        "output_tokens": sum(record["output_tokens"] for record in records),
        "reasoning_output_tokens": sum(
            record["reasoning_output_tokens"] for record in records
        ),
        "cli_reported": sum(record["cli_reported"] for record in records),
        "per_turn_sum": sum(record["per_turn_sum"] for record in records),
        "cumulative_minus_per_turn": sum(
            record["cumulative_minus_per_turn"] for record in records
        ),
        "context_compacted": sum(
            record["context_compacted"] for record in records
        ),
        "thread_rolled_back": sum(
            record["thread_rolled_back"] for record in records
        ),
        "turn_aborted": sum(record["turn_aborted"] for record in records),
    }


def _public_record(record: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "timestamp",
        "session_id",
        "stage",
        "outcome",
        "exit_code",
        "model",
        "reasoning",
        "model_calls",
        "turn_contexts",
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
        "cli_reported",
        "per_turn_sum",
        "cumulative_minus_per_turn",
        "total_tokens_raw",
        "context_compacted",
        "thread_rolled_back",
        "turn_aborted",
        "retry_group",
        "retry_index",
        "prompt_hash",
        "cwd",
        "path",
    )
    return {key: record[key] for key in keys}


def _render_table(
    records: list[dict[str, Any]], totals: dict[str, int], issues: dict[str, list[str]]
) -> str:
    columns = (
        "timestamp",
        "session_id",
        "stage",
        "outcome",
        "exit_code",
        "model",
        "reasoning",
        "model_calls",
        "turn_contexts",
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
        "cli_reported",
        "per_turn_sum",
        "cumulative_minus_per_turn",
        "total_tokens_raw",
        "context_compacted",
        "thread_rolled_back",
        "turn_aborted",
        "retry_group",
        "retry_index",
        "path",
    )
    lines = ["\t".join(columns)]
    for record in records:
        values = []
        for column in columns:
            value = record[column]
            values.append("-" if value is None else str(value))
        lines.append("\t".join(values))
    lines.append(
        "TOTAL\t"
        + "\t".join(f"{key}={totals[key]}" for key in totals)
    )
    for category in sorted(issues):
        for detail in sorted(issues[category]):
            lines.append(f"ISSUE\t{category}\t{detail}")
    return "\n".join(lines) + "\n"


def _strict_messages(issues: dict[str, list[str]]) -> list[str]:
    labels = {
        "unclassified": "unclassified stage",
        "ambiguous_stage": "ambiguous stage",
        "malformed_json": "malformed JSON lines",
        "malformed_usage": "malformed usage",
        "inconsistent_turn_context": "inconsistent turn_context",
        "non_monotonic_cumulative": "non-monotonic cumulative usage",
        "missing_session_meta": "missing session_meta files",
        "missing_session_cwd": "missing session_meta.cwd",
        "multiple_session_meta": "multiple session_meta rows",
        "duplicate_session_id": "duplicate session_id",
        "no_selected_sessions": "no selected sessions",
        "worklog": "worklog reconciliation",
        "unknown_stage_map_session": "stage-map unknown session_id",
    }
    messages: list[str] = []
    for category in (
        "unclassified",
        "ambiguous_stage",
        "malformed_json",
        "malformed_usage",
        "inconsistent_turn_context",
        "non_monotonic_cumulative",
        "missing_session_meta",
        "missing_session_cwd",
        "multiple_session_meta",
        "duplicate_session_id",
        "no_selected_sessions",
        "worklog",
        "unknown_stage_map_session",
    ):
        details = issues.get(category, [])
        if details:
            messages.append(
                f"strict: {labels[category]}: " + "; ".join(sorted(details))
            )
    return messages


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if (args.worklog is None) != (args.worklog_entry is None):
        parser.error("--worklog と --worklog-entry は同時に指定すること")
    stage_map = _parse_stage_map(parser, args.stage_map)
    sessions_root = (args.sessions_root or _default_sessions_root()).resolve()
    if not sessions_root.exists() or not sessions_root.is_dir():
        print(
            f"error: sessions root が存在する directory ではない: "
            f"{os.fspath(sessions_root)}",
            file=sys.stderr,
        )
        return 2

    issues: dict[str, list[str]] = {}
    records: list[dict[str, Any]] = []
    scanned: list[tuple[dict[str, Any], dict[str, list[str]]]] = []
    known_ids_all: set[str] = set()
    paths = sorted(
        (path.resolve() for path in sessions_root.rglob("rollout-*.jsonl")),
        key=os.fspath,
    )
    for path in paths:
        record, file_issues = _stream_rollout(path)
        scanned.append((record, file_issues))
        known_ids_all.update(record["session_meta_ids"])

    for record, file_issues in scanned:
        has_session_meta = bool(record["session_meta_ids"])
        has_cwd = record["session_meta_has_cwd"]
        if args.cwd_contains:
            matching_cwds = [
                cwd
                for cwd in record["session_meta_cwds"]
                if any(needle in cwd for needle in args.cwd_contains)
            ]
            if not matching_cwds:
                # 全 session_meta を走査し終えてから file 単位で選ぶ。cwd を
                # 一つも解読できない file は filter 時には帰属不能として選外に
                # 置き、その壊れ行で無関係な wave を汚さない。filter 無しなら
                # 従来どおり malformed/missing meta を fail-closed で報告する。
                continue
            # 複数 meta の先頭が選外でも、選択対象 meta の cwd を record の
            # file-level 帰属として使い、同じ file の issue を見落とさない。
            record["cwd"] = matching_cwds[0]
        for category, details in file_issues.items():
            issues.setdefault(category, []).extend(details)
        if not has_session_meta:
            issues.setdefault("missing_session_meta", []).append(record["path"])
            continue
        if not has_cwd:
            issues.setdefault("missing_session_cwd", []).append(record["path"])
            # filter 指定時は選択可否を決められないため record 自体は集計しない。
            if args.cwd_contains:
                continue
        records.append(record)

    records.sort(key=_timestamp_key)
    session_paths: dict[str, list[str]] = {}
    for record in records:
        session_paths.setdefault(record["session_id"], []).append(record["path"])
    for session_id, paths in sorted(session_paths.items()):
        if len(paths) > 1:
            issues.setdefault("duplicate_session_id", []).append(
                f"{session_id}: {', '.join(sorted(paths))}"
            )

    for session_id in sorted(set(stage_map) - known_ids_all):
        issues.setdefault("unknown_stage_map_session", []).append(session_id)
    for record in records:
        if record["session_id"] in stage_map:
            record["stage"] = stage_map[record["session_id"]]
            stage_matches: tuple[str, ...] = ()
        else:
            record["stage"], stage_matches = _classify_stage(record["prompt"])
        record["outcome"] = _classify_outcome(record)
        record["exit_code"] = "unknown"
        if len(stage_matches) > 1:
            issues.setdefault("ambiguous_stage", []).append(
                f"{record['session_id']}: {', '.join(stage_matches)}"
            )
        elif record["stage"] == "unclassified":
            issues.setdefault("unclassified", []).append(record["session_id"])

    _assign_retries(records)
    if not records:
        issues.setdefault("no_selected_sessions", []).append(
            "rollout selection is empty"
        )
    if args.worklog is not None:
        expectation, worklog_errors = _worklog_expectation(
            args.worklog, args.worklog_entry
        )
        if worklog_errors:
            issues.setdefault("worklog", []).extend(worklog_errors)
        elif expectation is not None:
            mismatches = _compare_worklog(records, expectation)
            if mismatches:
                issues.setdefault("worklog", []).extend(mismatches)

    totals = _totals(records)
    if args.as_json:
        output = {
            "sessions": [_public_record(record) for record in records],
            "totals": totals,
            "issues": {key: sorted(value) for key, value in sorted(issues.items())},
        }
        sys.stdout.write(
            json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
        )
    else:
        sys.stdout.write(_render_table(records, totals, issues))

    strict_messages = _strict_messages(issues)
    if args.strict and strict_messages:
        for message in strict_messages:
            print(message, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
