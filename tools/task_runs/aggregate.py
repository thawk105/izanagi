# -*- coding: utf-8 -*-
"""task-run/v1 の決定的な集計と create-only Markdown report publish。"""
from __future__ import annotations

import argparse
import ctypes
import errno
import fcntl
import hashlib
import json
import math
import os
import stat
import sys
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from . import LedgerError, ValidatedRun
from .ledger import FINAL_MARKER_NAME, _locked_root_snapshot
from .schema import MEASUREMENT_POLICY, SAFE_SLUG_RE, SCHEMA_VERSION


REPORT_MAX_BYTES = 1024 * 1024
TOKEN_FIELDS = ("input_tokens", "output_tokens", "cached_tokens", "total_tokens")
TEST_COUNT_FIELDS = ("collected", "passed", "failed", "skipped")
STAGE_ID_EVENTS = frozenset({"agent_run", "test_run", "finding_summary", "rework"})
SOURCE_FIELDS = ("timestamp", "duration", "metrics", "tokens")

# V18: 適用集合・分子・分母を実装上も固定する。値は report の式節へ逐語で出す。
RATE_DEFINITIONS: Mapping[str, tuple[str, str, str]] = {
    "task_end_missing": (
        "validated runs in one task_kind layer",
        "runs without task_end in that layer",
        "validated runs in that layer",
    ),
    "lead_unclassified": (
        "completed runs with positive lead and consistent decomposition",
        "lead_time_s - recorded_stage_time_s - wait_time_s",
        "lead_time_s",
    ),
    "stage_id_missing": (
        "agent_run/test_run/finding_summary/rework events in one run",
        "applicable events whose stage_id is null",
        "applicable events",
    ),
    "test_count_missing": (
        "four count fields on test_run events in one run",
        "null count fields",
        "test_run events * 4 fields",
    ),
    "token_field_missing": (
        "four token fields on agent_run events in one run",
        "null token fields",
        "agent_run events * 4 fields",
    ),
    "trigger_unspecified": (
        "test_run events in one run",
        "test_run events with trigger=unspecified",
        "test_run events",
    ),
    "source_not_exposed": (
        "measurement_source fields except not-applicable in one run",
        "applicable source fields equal to not-exposed",
        "applicable measurement_source fields",
    ),
    "finding_effective": (
        "real and refuted findings",
        "real findings",
        "real findings + refuted findings",
    ),
    "recording_overhead_coverage": (
        "recorded events",
        "events containing recording_duration_s",
        "recorded events",
    ),
    "stage_ratio": (
        "stage_end events grouped by stage",
        "recorded duration for one stage",
        "recorded duration for all stages in the run",
    ),
    "test_time_ratio": (
        "test_run events in a run",
        "sum of test_run.duration_s",
        "recorded duration for all stages in the run",
    ),
}


class ReportError(LedgerError):
    """report の cohort 確定、render、publish を完遂できない。"""


def _ratio(numerator: float | int, denominator: float | int) -> float | None:
    try:
        left = float(numerator)
        right = float(denominator)
    except (OverflowError, ValueError) as exc:
        raise ReportError("aggregate ratio input cannot be represented as finite") from exc
    if not math.isfinite(left) or not math.isfinite(right):
        raise ReportError("aggregate ratio input is non-finite")
    if right == 0:
        return None
    result = left / right
    if not math.isfinite(result):
        raise ReportError("aggregate ratio is non-finite")
    return result


def _finite_sum(values: Iterable[float | int], *, label: str) -> float:
    try:
        result = math.fsum(float(value) for value in values)
    except (OverflowError, ValueError) as exc:
        raise ReportError(f"{label} cannot be represented as finite") from exc
    if not math.isfinite(result):
        raise ReportError(f"{label} is non-finite")
    return result


def _finite_integer_sum(values: Iterable[int], *, label: str) -> int:
    result = sum(values)
    try:
        finite = math.isfinite(float(result))
    except OverflowError as exc:
        raise ReportError(f"{label} cannot be represented as finite") from exc
    if not finite:
        raise ReportError(f"{label} is non-finite")
    return result


def _timestamp(value: object) -> datetime:
    if not isinstance(value, str):
        raise ReportError("validated timestamp が string でない")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError as exc:  # validate_run 後の防御
        raise ReportError(f"validated timestamp を再解釈できない: {value!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ReportError("validated timestamp に timezone がない")
    return parsed


def _sum_duration(events: Iterable[Mapping[str, object]]) -> float:
    return round(_finite_sum((float(event["duration_s"]) for event in events), label="duration sum"), 3)


def _test_cycles(events: Sequence[Mapping[str, object]]) -> Mapping[str, object]:
    """rc=1 のみ red。digest が片端で欠測なら suite_id のみで対応する。"""

    opens: dict[str, list[str | None]] = defaultdict(list)
    cycles = 0
    missing_digest_cycles = 0
    outcomes = Counter[str]()

    def compatible(left: str | None, right: str | None) -> bool:
        return left is None or right is None or left == right

    for event in events:
        if event["event"] != "test_run":
            continue
        suite = str(event["suite_id"])
        digest = event["collected_node_digest"]
        digest = None if digest is None else str(digest)
        rc = int(event["exit_status"])
        if rc == 1:
            outcomes["red"] += 1
            matches = [
                index for index, opened in enumerate(opens[suite])
                if compatible(opened, digest)
            ]
            if not matches:
                opens[suite].append(digest)
            elif digest is None:
                # 欠測 red を観測した open state は、以後 suite_id のみで対応付ける。
                opens[suite][matches[0]] = None
        elif rc == 0:
            outcomes["green"] += 1
            candidates = [
                (index, opened) for index, opened in enumerate(opens[suite])
                if compatible(opened, digest)
            ]
            if candidates:
                # exact digest を優先し、次に欠測、最後に安定した挿入順。
                index, opened = min(
                    candidates,
                    key=lambda item: (item[1] != digest, item[1] is not None, item[0]),
                )
                del opens[suite][index]
                cycles += 1
                if opened is None or digest is None:
                    missing_digest_cycles += 1
        else:
            outcomes["infra"] += 1
    return {
        "red_to_green_cycles": cycles,
        "open_red": sum(len(values) for values in opens.values()),
        "green_runs": outcomes["green"],
        "red_runs": outcomes["red"],
        "infra_runs": outcomes["infra"],
        "digest_missing_pairings": missing_digest_cycles,
    }


def _source_missing(events: Sequence[Mapping[str, object]]) -> Mapping[str, object]:
    numerator = 0
    denominator = 0
    by_field: dict[str, Mapping[str, object]] = {}
    for field in SOURCE_FIELDS:
        field_num = 0
        field_den = 0
        for event in events:
            source = event["measurement_source"]
            assert isinstance(source, Mapping)
            value = source[field]
            if value == "not-applicable":
                continue
            field_den += 1
            if value == "not-exposed":
                field_num += 1
        numerator += field_num
        denominator += field_den
        by_field[field] = {
            "numerator": field_num,
            "denominator": field_den,
            "rate": _ratio(field_num, field_den),
        }
    return {
        "numerator": numerator,
        "denominator": denominator,
        "rate": _ratio(numerator, denominator),
        "by_field": by_field,
    }


def aggregate_run(run: ValidatedRun) -> dict[str, object]:
    """1 run の観測値を集計する。入力は E1 が完全検査した view に限定する。"""

    task = run.task
    events = run.events
    started_at = _timestamp(task["started_at"])
    task_end = next((event for event in events if event["event"] == "task_end"), None)
    lead_time_s = None
    outcome = None
    if task_end is not None:
        lead_time_s = round((_timestamp(task_end["timestamp"]) - started_at).total_seconds(), 3)
        outcome = str(task_end["outcome"])

    stage_events = [event for event in events if event["event"] == "stage_end"]
    stage_by_kind: dict[str, float] = {}
    for stage in sorted({str(event["stage"]) for event in stage_events}):
        stage_by_kind[stage] = _sum_duration(
            event for event in stage_events if event["stage"] == stage
        )
    recorded_stage_time_s = round(_finite_sum(stage_by_kind.values(), label="stage sum"), 3)
    waits = [event for event in events if event["event"] == "wait"]
    wait_time_s = _sum_duration(waits)
    unclassified_time_s = None
    time_inconsistent = False
    unclassified_rate = None
    if lead_time_s is not None:
        unclassified_time_s = round(lead_time_s - recorded_stage_time_s - wait_time_s, 3)
        time_inconsistent = unclassified_time_s < 0
        if not time_inconsistent:
            unclassified_rate = _ratio(unclassified_time_s, lead_time_s)

    test_events = [event for event in events if event["event"] == "test_run"]
    test_duration_s = _sum_duration(test_events)
    stage_ratios = {
        stage: _ratio(duration, recorded_stage_time_s)
        for stage, duration in stage_by_kind.items()
    }
    test_time_ratio = _ratio(test_duration_s, recorded_stage_time_s)
    cycles = _test_cycles(events)

    test_count_nulls = sum(
        event[field] is None for event in test_events for field in TEST_COUNT_FIELDS
    )
    test_count_denominator = len(test_events) * len(TEST_COUNT_FIELDS)
    stage_applicable = [event for event in events if event["event"] in STAGE_ID_EVENTS]
    stage_id_nulls = sum(event["stage_id"] is None for event in stage_applicable)
    unspecified = sum(event["trigger"] == "unspecified" for event in test_events)
    digest_missing = sum(event["collected_node_digest"] is None for event in test_events)

    reworks = [event for event in events if event["event"] == "rework"]
    rework_causes = Counter(str(event["cause"]) for event in reworks)
    agents = [event for event in events if event["event"] == "agent_run"]
    agent_statuses = Counter(str(event["status"]) for event in agents)
    token_nulls = sum(
        event["tokens"][field] is None  # type: ignore[index]
        for event in agents for field in TOKEN_FIELDS
    )
    token_denominator = len(agents) * len(TOKEN_FIELDS)

    findings = {name: 0 for name in ("real", "refuted", "unresolved")}
    for event in events:
        if event["event"] == "finding_summary":
            for name in findings:
                findings[name] += int(event[name])
    finding_denominator = findings["real"] + findings["refuted"]

    commits = [event for event in events if event["event"] == "commit"]
    overhead_values = [
        float(event["recording_duration_s"])
        for event in events if "recording_duration_s" in event
    ]
    last_timestamp = str(events[-1]["timestamp"]) if events else str(task["started_at"])
    lower_bound_s = round((_timestamp(last_timestamp) - started_at).total_seconds(), 3)

    return {
        "task_run_id": str(task["task_run_id"]),
        "task_kind": str(task["task_kind"]),
        "task_class": int(task["task_class"]),
        "started_at": str(task["started_at"]),
        "last_event_at": last_timestamp,
        "is_finished": task_end is not None,
        "outcome": outcome,
        "lead_time_s": lead_time_s,
        "right_censored_lower_bound_s": None if task_end is not None else lower_bound_s,
        "recorded_stage_time_s": recorded_stage_time_s,
        # v1 の旧 consumer 互換名。意味は recorded stage duration の累積で wall-time ではない。
        "active_time_s": recorded_stage_time_s,
        "stage_time_s": stage_by_kind,
        "stage_ratios": stage_ratios,
        "wait_time_s": wait_time_s,
        "unclassified_time_s": unclassified_time_s,
        "unclassified_rate": unclassified_rate,
        "time_inconsistency": time_inconsistent,
        "test_run_count": len(test_events),
        "full_suite_count": sum(event["suite_kind"] == "full" for event in test_events),
        "test_duration_s": test_duration_s,
        "test_time_ratio": test_time_ratio,
        "test_outcomes": cycles,
        "trigger_counts": dict(sorted(Counter(str(event["trigger"]) for event in test_events).items())),
        "collected_digest_missing_count": digest_missing,
        "rework_count": len(reworks),
        "rework_duration_s": _sum_duration(reworks),
        "rework_causes": dict(sorted(rework_causes.items())),
        "agent_run_count": len(agents),
        "agent_duration_s": _sum_duration(agents),
        "agent_statuses": dict(sorted(agent_statuses.items())),
        "findings": findings,
        "finding_effective_rate": _ratio(findings["real"], finding_denominator),
        "commit_count": len(commits),
        "commits": tuple((str(event["commit_sha"]), str(event["relation"])) for event in commits),
        "operation_count": len(events),
        "recording_overhead_s": round(_finite_sum(overhead_values, label="recording overhead sum"), 3),
        "recording_overhead_observed": len(overhead_values),
        "missingness": {
            "stage_id": {
                "numerator": stage_id_nulls,
                "denominator": len(stage_applicable),
                "rate": _ratio(stage_id_nulls, len(stage_applicable)),
            },
            "test_count_fields": {
                "numerator": test_count_nulls,
                "denominator": test_count_denominator,
                "rate": _ratio(test_count_nulls, test_count_denominator),
            },
            "token_fields": {
                "numerator": token_nulls,
                "denominator": token_denominator,
                "rate": _ratio(token_nulls, token_denominator),
            },
            "trigger_unspecified": {
                "numerator": unspecified,
                "denominator": len(test_events),
                "rate": _ratio(unspecified, len(test_events)),
            },
            "measurement_source_not_exposed": _source_missing(events),
            "recording_overhead_coverage": {
                "numerator": len(overhead_values),
                "denominator": len(events),
                "rate": _ratio(len(overhead_values), len(events)),
            },
        },
        "_agent_events": tuple(agents),
    }


def _token_cohorts(
    runs: Sequence[Mapping[str, object]],
) -> tuple[Mapping[str, object], ...]:
    groups: dict[tuple[str, str, str], list[Mapping[str, object]]] = defaultdict(list)
    for run in runs:
        for event in run["_agent_events"]:  # type: ignore[union-attr]
            groups[(str(run["task_kind"]), str(event["product"]), str(event["model"]))].append(event)
    result: list[Mapping[str, object]] = []
    for (task_kind, product, model), events in sorted(groups.items()):
        fields: dict[str, Mapping[str, object]] = {}
        for field in TOKEN_FIELDS:
            observed = [
                int(event["tokens"][field])  # type: ignore[index]
                for event in events if event["tokens"][field] is not None  # type: ignore[index]
            ]
            fields[field] = {
                "sum": _finite_integer_sum(observed, label="token sum") if observed else None,
                "observed": len(observed),
                "denominator": len(events),
                "coverage": _ratio(len(observed), len(events)),
            }
        result.append({
            "task_kind": task_kind,
            "product": product,
            "model": model,
            "agent_runs": len(events),
            "fields": fields,
        })
    return tuple(result)


def aggregate_runs(validated_runs: Sequence[ValidatedRun]) -> dict[str, object]:
    """task_kind 層を越えず cohort 集計し、打切りを比較母集団から除外する。"""

    runs = [aggregate_run(run) for run in validated_runs]
    runs.sort(key=lambda item: str(item["task_run_id"]))
    by_kind: list[Mapping[str, object]] = []
    kinds = sorted({str(run["task_kind"]) for run in runs})
    for kind in kinds:
        layer = [run for run in runs if run["task_kind"] == kind]
        completed = [run for run in layer if run["is_finished"]]
        end_missing = len(layer) - len(completed)
        summary: dict[str, object] = {
            "task_kind": kind,
            "run_count": len(layer),
            "completed_count": len(completed),
            "right_censored_count": end_missing,
            "task_end_missing": {
                "numerator": end_missing,
                "denominator": len(layer),
                "rate": _ratio(end_missing, len(layer)),
            },
            "comparison": None,
        }
        if len(completed) >= 2:
            ranked = sorted(completed, key=lambda item: (float(item["lead_time_s"]), str(item["task_run_id"])))
            summary["comparison"] = {
                "mean_lead_time_s": round(
                    _finite_sum(
                        (float(run["lead_time_s"]) for run in completed), label="lead sum",
                    ) / len(completed), 3
                ),
                "lead_time_rank": tuple(str(run["task_run_id"]) for run in ranked),
            }
        by_kind.append(summary)
    token_cohorts = _token_cohorts(runs)
    for run in runs:
        run.pop("_agent_events", None)
    return {
        "runs": tuple(runs),
        "task_kind_layers": tuple(by_kind),
        "token_cohorts": token_cohorts,
    }


def _fmt(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ReportError("report output contains non-finite number")
        return f"{value:.6f}".rstrip("0").rstrip(".")
    return str(value)


def _rate_cell(value: Mapping[str, object]) -> str:
    return f"{_fmt(value['rate'])} ({value['numerator']}/{value['denominator']})"


def _compact_counts(value: Mapping[str, object]) -> str:
    return ", ".join(f"{key}={value[key]}" for key in sorted(value)) or "none"


def _manifest(run: ValidatedRun) -> Mapping[str, object]:
    return {
        "task_run_id": str(run.task["task_run_id"]),
        "final_seq": run.final_seq,
        "task_sha256": run.task_bytes_sha256,
        "events_sha256": run.events_bytes_sha256,
    }


def _managed_series_health(root: Path) -> Mapping[str, object] | None:
    """Read full-series health only for automatic generation roots.

    A report remains scoped to its target root.  The optional projection makes
    a damaged sibling generation visible without changing checkout-local
    manual report behavior.
    """

    from . import generation

    if not generation.is_managed_generation_root(root):
        return None
    try:
        series = generation.validate_series(root)
    except Exception:
        return {
            "scope": "managed-series",
            "status": "invalid",
            "reasons": ("series-reader-error",),
        }
    reasons = tuple(series.invalid_codes)
    if series.is_empty:
        reasons = ("empty-series",)
    elif series.is_valid is not True and not reasons:
        reasons = ("series-invalid",)
    return {
        "scope": "managed-series",
        "status": "valid" if series.is_valid is True else "invalid",
        "reasons": reasons,
    }


def render_report(
    validated_runs: Sequence[ValidatedRun],
    *,
    manifests: Sequence[Mapping[str, object]] | None = None,
    damaged: Sequence[tuple[str, str]] = (),
    diagnostic: bool = False,
    report_time: str | None = None,
    series_health: Mapping[str, object] | None = None,
) -> bytes:
    """検査済み cohort を deterministic Markdown bytes にする。"""

    if damaged and not diagnostic:
        raise ReportError("damaged run があるため通常 report を生成しない")
    if report_time is not None:
        _timestamp(report_time)
    data = aggregate_runs(validated_runs)
    runs = data["runs"]
    manifests = tuple(manifests) if manifests is not None else tuple(_manifest(run) for run in validated_runs)
    cohort_times = [str(run.task["started_at"]) for run in validated_runs]
    cohort_times.extend(str(event["timestamp"]) for run in validated_runs for event in run.events)
    as_of = report_time if report_time is not None else (
        max(cohort_times, key=_timestamp) if cohort_times else "no-healthy-run"
    )
    published_damage_reasons = {
        "invalid-run", "run-io-error", "unexpected-validation-error",
    }
    published_run_count = len(validated_runs) + sum(
        reason in published_damage_reasons for _name, reason in damaged
    )
    max_task_runs = int(MEASUREMENT_POLICY["max_task_runs"])
    cap_excess = max(0, published_run_count - max_task_runs)

    lines = [
        "# 不完全 — task-run 診断 report" if diagnostic and damaged else "# task-run 観測 report",
        "",
        "> 主張範囲: 記録された event のみ。pytest/check は wrapper 実測、その他は手動記録。",
        "> 時間値は非排他的な観測値であり、wall-time の排他的分解ではない。欠測率は台帳内で観測可能な下限。",
        "",
        f"- cohort_as_of: `{as_of}`",
        f"- healthy_runs: {len(validated_runs)}",
        f"- published_runs: {published_run_count}",
        f"- pilot_max_task_runs: {max_task_runs}",
        f"- cap_exceeded: {'yes' if cap_excess else 'no'}",
        f"- cap_excess: {cap_excess}",
        f"- diagnostic: {'yes' if diagnostic else 'no'}",
        "",
    ]
    if series_health is not None:
        status = str(series_health["status"])
        reasons = tuple(str(reason) for reason in series_health.get("reasons", ()))
        reason_text = ", ".join(reasons) if reasons else "none"
        lines.extend([
            f"- series全体の健全性: {status} ({reason_text})",
            "- 個別root reportの範囲: 対象generation rootのみ。series全体の状態は別掲。",
            "",
        ])
    if damaged:
        lines.extend(["## Damaged entries", "", "| entry | reason |", "|---|---|"])
        for name, reason in sorted(damaged):
            lines.append(f"| `{name}` | {reason.replace('|', '&#124;')} |")
        lines.append("")

    if series_health is not None:
        status = str(series_health["status"])
        reasons = tuple(str(reason) for reason in series_health.get("reasons", ()))
        lines.extend([
            "## Series health manifest",
            "",
            "| scope | status | reasons |",
            "|---|---|---|",
            f"| {series_health.get('scope', 'managed-series')} | `{status}` | "
            f"{', '.join(reasons) if reasons else 'none'} |",
            "",
        ])

    lines.extend([
        "## Input binding", "",
        "| task_run_id | final_seq | task.json SHA-256 | events.jsonl SHA-256 |",
        "|---|---:|---|---|",
    ])
    for item in sorted(manifests, key=lambda value: str(value["task_run_id"])):
        lines.append(
            f"| `{item['task_run_id']}` | {item['final_seq']} | `{item['task_sha256']}` | `{item['events_sha256']}` |"
        )
    lines.extend([
        "",
        "## Completed observations", "",
        "| task_kind | task_run_id | outcome | lead_s | stage_s | wait_s | unclassified_s | unclassified_rate | inconsistency | tests_s | test/stage ratio | operations | recording_overhead_s |",
        "|---|---|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|",
    ])
    completed = [run for run in runs if run["is_finished"]]  # type: ignore[index]
    for run in completed:
        lines.append(
            "| {task_kind} | `{task_run_id}` | {outcome} | {lead_time_s} | "
            "{recorded_stage_time_s} | {wait_time_s} | {unclassified_time_s} | "
            "{unclassified_rate} | {time_inconsistency} | {test_duration_s} | {test_time_ratio} | "
            "{operation_count} | {recording_overhead_s} |".format(
                **{key: _fmt(value) for key, value in run.items()}
            )
        )
    lines.extend([
        "",
        "Recorded stage durations and ratios:",
        "",
        "| task_kind | task_run_id | stage | recorded_duration_s | stage_ratio |",
        "|---|---|---|---:|---:|",
    ])
    for run in runs:  # type: ignore[assignment]
        for stage, duration in run["stage_time_s"].items():
            lines.append(
                f"| {run['task_kind']} | `{run['task_run_id']}` | {stage} | {_fmt(duration)} | "
                f"{_fmt(run['stage_ratios'][stage])} |"
            )
    lines.extend([
        "",
        "## Right-censored observations", "",
        "| task_kind | task_run_id | started_at | last_event_at | observed_lower_bound_s | operations |",
        "|---|---|---|---|---:|---:|",
    ])
    for run in runs:  # type: ignore[assignment]
        if run["is_finished"]:
            continue
        lines.append(
            f"| {run['task_kind']} | `{run['task_run_id']}` | `{run['started_at']}` | "
            f"`{run['last_event_at']}` | {_fmt(run['right_censored_lower_bound_s'])} | {run['operation_count']} |"
        )

    lines.extend([
        "",
        "## Test and rework observations", "",
        "| task_kind | task_run_id | test_runs | full | green | red | infra | cycles | open_red | digest_missing_pairings | triggers | reworks | rework_s | rework_causes |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---|",
    ])
    for run in runs:  # type: ignore[assignment]
        outcome = run["test_outcomes"]
        lines.append(
            f"| {run['task_kind']} | `{run['task_run_id']}` | {run['test_run_count']} | {run['full_suite_count']} | "
            f"{outcome['green_runs']} | {outcome['red_runs']} | {outcome['infra_runs']} | "
            f"{outcome['red_to_green_cycles']} | {outcome['open_red']} | {outcome['digest_missing_pairings']} | "
            f"{_compact_counts(run['trigger_counts'])} | {run['rework_count']} | {_fmt(run['rework_duration_s'])} | "
            f"{_compact_counts(run['rework_causes'])} |"
        )
    if any(run["collected_digest_missing_count"] for run in runs):  # type: ignore[index]
        lines.extend(["", "Digest 欠測時の red/green 対応付けは suite_id のみに基づく。"])

    lines.extend([
        "",
        "## Agent, finding, and commit observations", "",
        "| task_kind | task_run_id | agents | agent_s | agent_statuses | real | refuted | unresolved | finding_rate | commits |",
        "|---|---|---:|---:|---|---:|---:|---:|---:|---:|",
    ])
    for run in runs:  # type: ignore[assignment]
        findings = run["findings"]
        lines.append(
            f"| {run['task_kind']} | `{run['task_run_id']}` | {run['agent_run_count']} | {_fmt(run['agent_duration_s'])} | "
            f"{_compact_counts(run['agent_statuses'])} | {findings['real']} | {findings['refuted']} | {findings['unresolved']} | "
            f"{_fmt(run['finding_effective_rate'])} | {run['commit_count']} |"
        )
    lines.extend(["", "Commit associations:", ""])
    for run in runs:  # type: ignore[assignment]
        associations = ", ".join(f"`{sha}` ({relation})" for sha, relation in run["commits"])
        lines.append(f"- `{run['task_run_id']}`: {associations or 'none'}")

    lines.extend([
        "",
        "## Token cohorts", "",
        "Token values are combined only inside each task_kind/product/model cohort; null stays unobserved.",
        "",
        "| task_kind | product | model | field | observed/agent_runs | coverage | observed_sum |",
        "|---|---|---|---|---:|---:|---:|",
    ])
    for cohort in data["token_cohorts"]:  # type: ignore[assignment]
        for field in TOKEN_FIELDS:
            values = cohort["fields"][field]
            lines.append(
                f"| {cohort['task_kind']} | {cohort['product']} | {cohort['model']} | {field} | "
                f"{values['observed']}/{values['denominator']} | {_fmt(values['coverage'])} | {_fmt(values['sum'])} |"
            )

    lines.extend([
        "",
        "## Missingness by run", "",
        "| task_kind | task_run_id | stage_id null | test counts null | token fields null | unspecified trigger | source not-exposed | overhead coverage |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ])
    for run in runs:  # type: ignore[assignment]
        missing = run["missingness"]
        lines.append(
            f"| {run['task_kind']} | `{run['task_run_id']}` | {_rate_cell(missing['stage_id'])} | "
            f"{_rate_cell(missing['test_count_fields'])} | {_rate_cell(missing['token_fields'])} | "
            f"{_rate_cell(missing['trigger_unspecified'])} | "
            f"{_rate_cell(missing['measurement_source_not_exposed'])} | "
            f"{_rate_cell(missing['recording_overhead_coverage'])} |"
        )

    lines.extend([
        "",
        "## task_kind layers", "",
        "A comparison is emitted only for a layer containing at least two completed runs. Right-censored runs are excluded.",
        "",
        "| task_kind | runs | completed | right_censored | task_end_missing | comparison |",
        "|---|---:|---:|---:|---:|---|",
    ])
    for layer in data["task_kind_layers"]:  # type: ignore[assignment]
        comparison = layer["comparison"]
        if comparison is None:
            comparison_text = "not emitted"
        else:
            ranks = " → ".join(f"`{value}`" for value in comparison["lead_time_rank"])
            comparison_text = f"mean_lead_s={_fmt(comparison['mean_lead_time_s'])}; rank={ranks}"
        lines.append(
            f"| {layer['task_kind']} | {layer['run_count']} | {layer['completed_count']} | "
            f"{layer['right_censored_count']} | {_rate_cell(layer['task_end_missing'])} | {comparison_text} |"
        )

    lines.extend([
        "",
        "## Measurement source exposure by run", "",
        "`not-applicable` fields are excluded from each denominator.",
        "",
        "| task_kind | task_run_id | source field | not-exposed rate |",
        "|---|---|---|---:|",
    ])
    for run in runs:  # type: ignore[assignment]
        by_field = run["missingness"]["measurement_source_not_exposed"]["by_field"]
        for field in SOURCE_FIELDS:
            lines.append(
                f"| {run['task_kind']} | `{run['task_run_id']}` | {field} | "
                f"{_rate_cell(by_field[field])} |"
            )

    lines.extend(["", "## Fixed rate definitions", "", "| metric | applicable set | numerator | denominator |", "|---|---|---|---|"])
    for name, (applicable, numerator, denominator) in RATE_DEFINITIONS.items():
        lines.append(f"| `{name}` | {applicable} | {numerator} | {denominator} |")
    lines.append("")
    payload = ("\n".join(lines)).encode("utf-8")
    if len(payload) > REPORT_MAX_BYTES:
        raise ReportError(f"report size 上限超過 ({len(payload)} > {REPORT_MAX_BYTES})")
    return payload


def _open_root_lock(root: Path) -> int:
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    flags = os.O_RDONLY | nofollow | getattr(os, "O_DIRECTORY", 0)
    try:
        fd = os.open(root, flags)
    except OSError as exc:
        raise ReportError(f"root lock を開けない: {root}: {exc}") from exc
    if not stat.S_ISDIR(os.fstat(fd).st_mode):
        os.close(fd)
        raise ReportError("root lock target が directory でない")
    return fd


def _rename_noreplace(source: Path, destination: Path) -> None:
    """Linux renameat2(RENAME_NOREPLACE)。非対応環境は atomic link で fail-closed。"""

    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is not None:
        renameat2.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        renameat2.restype = ctypes.c_int
        result = renameat2(
            -100, os.fsencode(source), -100, os.fsencode(destination), 1  # AT_FDCWD, RENAME_NOREPLACE
        )
        if result == 0:
            return
        error = ctypes.get_errno()
        unsupported = {errno.ENOSYS, errno.EINVAL, getattr(errno, "EOPNOTSUPP", errno.EINVAL)}
        if error not in unsupported:
            raise OSError(error, os.strerror(error), destination)
    os.link(source, destination)
    os.unlink(source)


_DAMAGE_REASON_CODES = frozenset({
    "invalid-run", "run-io-error", "unexpected-validation-error",
    "incomplete-start", "unknown-root-entry",
})


def _safe_entry_label(name: str) -> str:
    if SAFE_SLUG_RE.fullmatch(name) is not None:
        return name
    return f"sha256-{hashlib.sha256(name.encode('utf-8', errors='strict')).hexdigest()[:12]}"


def _create_final_marker(root_fd: int, destination: Path, report_payload: bytes) -> None:
    marker = {
        "schema_version": SCHEMA_VERSION,
        "final_report": _safe_entry_label(destination.name),
        "report_sha256": hashlib.sha256(report_payload).hexdigest(),
    }
    raw = (json.dumps(marker, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise ReportError("O_NOFOLLOW が利用できないため final marker を作れない")
    try:
        fd = os.open(
            FINAL_MARKER_NAME,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | nofollow,
            0o600,
            dir_fd=root_fd,
        )
    except OSError as exc:
        raise ReportError(f"final marker を create-only 生成できない: {exc}") from exc
    try:
        view = memoryview(raw)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError(errno.EIO, "final marker write が進行しない")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)


def publish_report(
    root: Path,
    destination: Path,
    *,
    diagnostic: bool = False,
    report_time: str | None = None,
    final: bool = False,
) -> Path:
    """root/event locks 下で cohort と digest を確定し create-only publish する。"""

    root = Path(root)
    destination = Path(destination)
    try:
        if root.is_symlink():
            raise ReportError("root symlink は禁止")
        root_resolved = root.resolve(strict=True)
    except OSError as exc:
        raise ReportError(f"root が存在しない/解決できない: {root}: {exc}") from exc
    reports = root_resolved / "reports"
    if destination.parent.resolve(strict=False) != reports or destination.name in {"", ".", ".."}:
        raise ReportError("destination は root/reports/ 直下でなければならない")
    series_health = _managed_series_health(root_resolved)
    root_fd = _open_root_lock(root_resolved)
    temp_path: Path | None = None
    try:
        fcntl.flock(root_fd, fcntl.LOCK_EX)
        if final:
            try:
                os.stat(FINAL_MARKER_NAME, dir_fd=root_fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise ReportError("pilot は既に final marker で凍結済み")
        with _locked_root_snapshot(root_resolved, root_fd=root_fd) as (root_report, validated):
            problems: list[tuple[str, str]] = [
                (_safe_entry_label(item.path.name), item.reason) for item in root_report.damaged
            ]
            problems.extend(
                (_safe_entry_label(path.name), "incomplete-start")
                for path in root_report.incomplete
            )
            problems.extend(
                (_safe_entry_label(path.name), "unknown-root-entry")
                for path in root_report.unknown
            )
            if any(reason not in _DAMAGE_REASON_CODES for _name, reason in problems):
                raise ReportError("internal damage reason code is not closed")
            if problems and not diagnostic:
                raise ReportError("damaged/incomplete/unknown entry があるため report を生成しない")
            manifests = tuple(_manifest(run) for run in validated)
            payload = render_report(
                validated,
                manifests=manifests,
                damaged=problems,
                diagnostic=diagnostic,
                report_time=report_time,
                series_health=series_health,
            )
        reports.mkdir(mode=0o700, exist_ok=True)
        if reports.is_symlink() or not reports.is_dir():
            raise ReportError("reports path は symlink でない directory が必要")
        if destination.exists() or destination.is_symlink():
            raise ReportError(f"report は既に存在するため上書きしない: {destination.name}")
        fd, temp_name = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=reports)
        temp_path = Path(temp_name)
        try:
            view = memoryview(payload)
            while view:
                written = os.write(fd, view)
                if written <= 0:
                    raise OSError(errno.EIO, "report write が進行しない")
                view = view[written:]
            os.fsync(fd)
        finally:
            os.close(fd)
        if destination.exists() or destination.is_symlink():
            raise ReportError(f"report publish 直前に既存化したため上書きしない: {destination.name}")
        _rename_noreplace(temp_path, destination)
        temp_path = None
        reports_fd = _open_root_lock(reports)
        try:
            os.fsync(reports_fd)
        finally:
            os.close(reports_fd)
        if final:
            _create_final_marker(root_fd, destination, payload)
        os.fsync(root_fd)
        return destination
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            raise ReportError(f"report は既に存在するため上書きしない: {destination.name}") from exc
        raise ReportError(f"report publish I/O failure: {exc}") from exc
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass
        try:
            fcntl.flock(root_fd, fcntl.LOCK_UN)
        finally:
            os.close(root_fd)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="task-run/v1 observation report")
    parser.add_argument("root", type=Path, nargs="?")
    parser.add_argument("destination", type=Path, nargs="?")
    parser.add_argument("--root", dest="root_option", type=Path)
    parser.add_argument("--output", dest="output_option", type=Path)
    parser.add_argument("--diagnostic", action="store_true")
    parser.add_argument("--final", action="store_true", help="publish 後に pilot を create-only marker で凍結")
    parser.add_argument("--report-time", help="report 本文へ入れる決定的な caller-supplied timestamp")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.root is not None and args.root_option is not None:
        parser.error("root は positional と --root のどちらか一方だけ指定する")
    if args.destination is not None and args.output_option is not None:
        parser.error("destination は positional と --output のどちらか一方だけ指定する")
    root = args.root_option if args.root_option is not None else args.root
    destination = args.output_option if args.output_option is not None else args.destination
    if root is None or destination is None:
        parser.error("root と destination/--output は必須")
    try:
        path = publish_report(
            root,
            destination,
            diagnostic=args.diagnostic,
            report_time=args.report_time,
            final=args.final,
        )
    except LedgerError as exc:
        print(f"task_run_report: {exc}", file=sys.stderr)
        return 1
    print(path)
    return 0


__all__ = [
    "RATE_DEFINITIONS",
    "REPORT_MAX_BYTES",
    "ReportError",
    "aggregate_run",
    "aggregate_runs",
    "render_report",
    "publish_report",
    "main",
]
