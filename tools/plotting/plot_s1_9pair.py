#!/usr/bin/env python3
"""S-1a の登録 9 対を、admission 済み WAL と凍結 report から描く。

標本、測定条件、相対中央値差は HISTORICAL_RAW view の WAL から再構成し、
凍結 report の accepted evidence と全行照合する。judgment と p 値は凍結
report だけを権威とし、WAL 側の gate 再計算は一致検査にしか使わない。

使い方:
    python3 tools/plotting/plot_s1_9pair.py OUT_PREFIX REPORT_JSON \
      --develop DEVELOP_CAMPAIGN_DIR --floor FLOOR_CAMPAIGN_DIR \
      --block1 BLOCK1_CAMPAIGN_DIR --block2 BLOCK2_CAMPAIGN_DIR

出力は OUT_PREFIX.{png,pdf,provenance.json}。作図は計測機の外で行う。
入力中の run_cmd/spec_content はデータであり、shell へ渡さない。
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import shlex
import statistics
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from orchestrator.campaign import wal  # noqa: E402
from orchestrator.campaign.artifact_admission import (  # noqa: E402
    CampaignReadPurpose,
    require_admitted_campaign,
)


SCHEMA = "izanagi-s1-9pair-figure-provenance/v1"
REPORT_REL = Path("output/reports/s1_direct_comparison/report.json")
FREEZE_REL = Path("output/s1-freeze/measurement_freeze.json")
GENERATOR_REL = Path("tools/plotting/plot_s1_9pair.py")
OUTPUT_BASENAME = "fig4_s1a_9pair_direct_comparison"

WORKLOADS = ("write-heavy", "balanced", "read-heavy")
CONFIGURATIONS = (
    "system_gate", "ident_all", "p2_2_flag_opt", "backoff_fixed_best",
    "sort_best", "stock_common",
)
PLOT_CONFIGURATIONS = (
    "system_gate", "p2_2_flag_opt", "backoff_fixed_best", "sort_best",
)
AXES = ("p2_2_flag_opt", "backoff_fixed_best", "sort_best")
DISPLAY_LABELS = {
    "system_gate": "trigger gating",
    "p2_2_flag_opt": "compile-time flags",
    "backoff_fixed_best": "static backoff",
    "sort_best": "lock ordering",
}
INTERNAL_TEXT_FORBIDDEN = frozenset({
    "system_gate", "p2_2_flag_opt", "backoff_fixed_best", "sort_best",
    "ident_all", "stock_common",
})
ROLES = ("develop", "floor", "block1", "block2")
PERFORMANCE_ROLES = ("floor", "block1", "block2")
EXPECTED_COUNTS = {"develop": 18, "floor": 144, "block1": 72, "block2": 72}
CANONICAL_CAMPAIGNS = {
    "develop": "s1-direct-develop-direct-comparison-d0f495bf",
    "floor": "s1-direct-floor-direct-comparison-b82b9229",
    "block1": "s1-direct-block1-direct-comparison-74ff9ba2",
    "block2": "s1-direct-block2-direct-comparison-9645b16a",
}
READ_RATIOS = {"write-heavy": 5, "balanced": 50, "read-heavy": 95}
EXPECTED_PERF_EVENTS = (
    "LLC-load-misses", "LLC-loads", "instructions", "cycles",
)
EXPECTED_REPORT_KEYS = frozenset({
    "freeze_ref", "hard_gates", "comparisons", "families", "effect_sizes",
    "budget", "generated_at_head",
})
EXPECTED_HARD_GATE_KEYS = frozenset({
    "freeze", "schedule", "certified", "sample_counts", "budget",
})
EXPECTED_COMPARISON_KEYS = frozenset({
    "comparison_id", "family", "workload", "left_cell", "right_cell",
    "alternative", "judgment", "reasons", "gates", "floor_cmp", "p_perm",
    "p_star", "reference_alpha", "reference_below_alpha", "unstable_counts",
    "block_effects", "retry_events",
})
EXPECTED_EVIDENCE_KEYS = frozenset({
    "role", "schedule_index", "cell_id", "variant_id", "src_token",
    "fitness_tps", "verify_configs", "unstable",
})
REPORT_FREEZE_SHA256 = (
    "5c719c076e17f385a781933c081bf02abcd85b9edb01ad8c50a37740c134a191"
)
FREEZE_EMISSION_COMMIT = "b4e5cb621e3f8f93de952e9400d4b8dcd34107e0"
FREEZE_CHANGED_POINTERS = (
    "/frozen_at_head",
    "/implementation_hashes/known_axes_freeze/sha256",
    "/cells/read-heavy:sort_best/variant/sources[0]/sha256",
)
T_975_DF7 = 2.365
TOP_MARKER_AREA_PT2 = 44.0
DATA_LABEL_OFFSET_PT = 9.0
DATA_LABEL_MARKER_CLEARANCE_PX = 3.0
DATA_LABEL_REFERENCE_CLEARANCE_PX = 4.0
BOTTOM_LEGEND_ANCHOR = (0.5, 0.025)
FIGURE_LAYOUT_RECT = (0.02, 0.12, 0.995, 0.90)
TOP_LEGEND_TEXTS = frozenset({
    "registered pair criterion not met (6/9)",
    "pair criterion met (3/9; S-1a remains not established)",
})
BOTTOM_LEGEND_TEXTS = frozenset({
    "block1 samples", "block2 samples", "mean and t 95% CI",
})
BANNER_TEXT = "S-1a NOT ESTABLISHED — 6 of 9 pairs fail — family p=1.0"
FIGURE_TITLE_TEXT = (
    "Silo, 48 threads, 1,000,000 records, 3 s, Zipf 0.9; "
    "bottom panels use independent y-scales"
)
TOP_AXIS_LABEL_TEXT = "relative median difference (%)"
BOTTOM_AXIS_LABEL_TEXT = "throughput (M tps)"
REQUIRED_ARTIST_TEXT_COUNTS = {
    **{value: 1 for value in TOP_LEGEND_TEXTS | BOTTOM_LEGEND_TEXTS},
    **{value: 1 for value in WORKLOADS},
    BANNER_TEXT: 1,
    FIGURE_TITLE_TEXT: 1,
    TOP_AXIS_LABEL_TEXT: len(WORKLOADS),
    BOTTOM_AXIS_LABEL_TEXT: len(WORKLOADS),
}
REQUIRED_ARTIST_TEXTS = frozenset(REQUIRED_ARTIST_TEXT_COUNTS)
PAIR_JUDGMENT_STYLE = {
    "不成立": ("x", "#9d2a2a"),
    "成立": ("o", "#496f8a"),
}
FAMILY_JUDGMENT_DISPLAY = {
    "不成立": "NOT ESTABLISHED",
    "成立": "ESTABLISHED",
}


class FigureDataError(RuntimeError):
    """入力、凍結判定、描画契約が一致せず図を生成できない。"""


class FigureLayoutError(FigureDataError):
    """保存前 bbox 検査で図の逸脱または重なりを検出した。"""


def _fail(message: str) -> None:
    raise FigureDataError(message)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise FigureDataError(f"file cannot be read: {path}") from exc
    return digest.hexdigest()


def _strict_json(path: Path) -> dict[str, Any]:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON constant: {value}")

    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), parse_constant=reject_constant,
            object_pairs_hook=no_duplicates,
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise FigureDataError(f"strict JSON cannot be read: {path}: {exc}") from exc
    if type(value) is not dict:
        _fail(f"JSON top level must be an object: {path}")
    return value


def _repo_path(value: os.PathLike[str] | str, *, must_exist: bool = True) -> Path:
    path = Path(value)
    resolved = path.resolve() if path.is_absolute() else (REPO_ROOT / path).resolve()
    try:
        resolved.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise FigureDataError(f"path leaves repository: {value}") from exc
    if must_exist and not resolved.exists():
        _fail(f"required path is absent: {resolved.relative_to(REPO_ROOT)}")
    return resolved


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError as exc:
        raise FigureDataError(f"path is not repository-relative: {path}") from exc


def _finite_number(value: object, label: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(f"{label} must be numeric")
    clean = float(value)
    if not math.isfinite(clean) or (positive and clean <= 0.0):
        _fail(f"{label} must be finite" + (" and positive" if positive else ""))
    return clean


def _same(left: object, right: object, label: str, *, tolerance: float = 1e-12) -> None:
    a = _finite_number(left, label)
    b = _finite_number(right, label)
    if not math.isclose(a, b, rel_tol=0.0, abs_tol=tolerance):
        _fail(f"{label} mismatch: {a!r} != {b!r}")


def _expected_comparison_ids() -> frozenset[str]:
    return frozenset(
        [f"S-1a:{workload}:{axis}" for workload in WORKLOADS for axis in AXES]
        + [f"S-1b:{workload}:gate_on_vs_gate_off" for workload in WORKLOADS]
    )


def _report_cell_id(value: object) -> str:
    if type(value) is not str or value.count(":") != 1 or "/" in value:
        _fail(f"report cell_id must contain exactly one colon: {value!r}")
    workload, configuration = value.split(":", 1)
    if workload not in WORKLOADS or configuration not in CONFIGURATIONS:
        _fail(f"unknown report cell_id: {value!r}")
    return value


def normalize_wal_cell_id(value: object) -> str:
    """WAL の exact workload/configuration を report の colon 表記へ変換する。"""
    if type(value) is not str or value.count("/") != 1 or ":" in value:
        _fail(f"WAL cell_id must contain exactly one slash and no colon: {value!r}")
    workload, configuration = value.split("/", 1)
    if workload not in WORKLOADS or configuration not in CONFIGURATIONS:
        _fail(f"unknown WAL cell_id: {value!r}")
    return f"{workload}:{configuration}"


def _validate_report(report: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    if set(report) != EXPECTED_REPORT_KEYS:
        _fail(f"report top-level exact keys differ: {sorted(set(report))}")
    hard = report.get("hard_gates")
    if not isinstance(hard, Mapping) or set(hard) != EXPECTED_HARD_GATE_KEYS:
        _fail("report hard_gates exact keys differ")
    for name in ("freeze", "sample_counts", "budget"):
        gate = hard.get(name)
        if not isinstance(gate, Mapping) or gate.get("status") != "pass":
            _fail(f"hard gate {name} is not pass")
        reason_key = "reasons"
        if gate.get(reason_key) != []:
            _fail(f"hard gate {name} has reasons")
    schedule = hard.get("schedule")
    if not isinstance(schedule, Mapping) or set(schedule) != set(ROLES):
        _fail("schedule role set differs")
    for role in ROLES:
        gate = schedule[role]
        if not isinstance(gate, Mapping) or gate.get("status") != "pass" or gate.get("reasons") != []:
            _fail(f"schedule hard gate is not clean pass: {role}")
    certified = hard.get("certified")
    if not isinstance(certified, Mapping) or certified.get("status") != "pass":
        _fail("certified hard gate is not pass")
    if certified.get("issues") != []:
        _fail("certified hard gate has issues")
    if certified.get("accepted_samples") != EXPECTED_COUNTS:
        _fail("certified accepted sample counts differ")
    if certified.get("rejected_or_unbound_commits") != {role: 0 for role in ROLES}:
        _fail("certified rejected/unbound counts differ")
    evidence = certified.get("accepted_evidence")
    if not isinstance(evidence, Mapping) or set(evidence) != set(ROLES):
        _fail("accepted_evidence roles differ")
    for role in ROLES:
        rows = evidence[role]
        if type(rows) is not list or len(rows) != EXPECTED_COUNTS[role]:
            _fail(f"accepted_evidence count differs: {role}")
        for row in rows:
            if type(row) is not dict or set(row) != EXPECTED_EVIDENCE_KEYS:
                _fail(f"accepted_evidence row shape differs: {role}")
            if row.get("role") != role:
                _fail(f"accepted_evidence role differs: {role}")
            _report_cell_id(row.get("cell_id"))

    comparisons = report.get("comparisons")
    if type(comparisons) is not list or len(comparisons) != 12:
        _fail("report must contain exactly 12 comparisons")
    by_id: dict[str, Mapping[str, Any]] = {}
    for row in comparisons:
        if type(row) is not dict or set(row) != EXPECTED_COMPARISON_KEYS:
            _fail("comparison exact keys differ")
        comparison_id = row.get("comparison_id")
        if type(comparison_id) is not str or comparison_id in by_id:
            _fail("comparison id is missing or duplicated")
        if row.get("reasons") != []:
            _fail(f"comparison has reasons: {comparison_id}")
        _report_cell_id(row.get("left_cell"))
        _report_cell_id(row.get("right_cell"))
        by_id[comparison_id] = row
    if set(by_id) != _expected_comparison_ids():
        _fail("exact comparison id set differs")
    families = report.get("families")
    if not isinstance(families, Mapping) or set(families) != {"s1a", "s1b"}:
        _fail("family exact set differs")
    for name, family in families.items():
        if not isinstance(family, Mapping) or family.get("reasons") != []:
            _fail(f"family is not a clean adjudication: {name}")
    s1a = families["s1a"]
    if (s1a.get("judgment") != "不成立" or s1a.get("p_family") != 1
            or set(s1a.get("comparison_ids", ()))
            != {value for value in by_id if value.startswith("S-1a:")}):
        _fail("S-1a frozen family adjudication differs")
    effect_sizes = report.get("effect_sizes")
    if not isinstance(effect_sizes, Mapping) or set(effect_sizes) != set(by_id):
        _fail("effect_sizes exact comparison set differs")
    freeze_ref = report.get("freeze_ref")
    if (not isinstance(freeze_ref, Mapping)
            or freeze_ref.get("sha256") != REPORT_FREEZE_SHA256):
        _fail("report freeze_ref differs from ruled historical reference")
    return by_id


def _event(record: object, name: str) -> bool:
    return (
        getattr(record, "stage", None) == "s1-session"
        and isinstance(getattr(record, "payload", None), Mapping)
        and record.payload.get("event") == name
    )


def _segments(records: Sequence[object]) -> list[list[object]]:
    result: list[list[object]] = []
    current: list[object] | None = None
    for record in records:
        if _event(record, "session-start"):
            if current is not None:
                result.append(current)
            current = [record]
        elif current is not None:
            current.append(record)
    if current is not None:
        result.append(current)
    return result


def _single(records: Sequence[object], predicate, label: str) -> object:
    selected = [record for record in records if predicate(record)]
    if len(selected) != 1:
        _fail(f"{label} must be unique: {len(selected)}")
    return selected[0]


def _parse_run_command(command: object, workload: str) -> dict[str, Any]:
    """命令列を実行せず、whitelist 測定条件だけを安全に照合する。"""
    if type(command) is not str:
        _fail("bench_done.run_cmd must be a string")
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError as exc:
        raise FigureDataError("run_cmd cannot be safely split") from exc
    if (len(tokens) < 8 or Path(tokens[0]).name != "numactl"
            or tokens[1] != "--interleave=all" or Path(tokens[2]).name != "perf"
            or tokens[3:5] != ["stat", "-e"]
            or tuple(tokens[5].split(",")) != EXPECTED_PERF_EVENTS
            or tokens[6] != "--"):
        _fail("run_cmd numactl/perf stat prefix differs")
    whitelisted = {
        "thread_num": int, "ycsb_tuple_num": int, "extime": int,
        "clocks_per_us": int, "ycsb_zipf_skew": float, "ycsb_rratio": int,
        "ycsb_rmw": int,
    }
    observed: dict[str, Any] = {}
    for token in tokens[8:]:
        if not token.startswith("-") or "=" not in token:
            continue
        key, raw = token[1:].split("=", 1)
        converter = whitelisted.get(key)
        if converter is None:  # 未知の文字列 field は命令として扱わず無視する。
            continue
        if key in observed:
            _fail(f"run_cmd condition is duplicated: {key}")
        try:
            observed[key] = converter(raw)
        except ValueError as exc:
            raise FigureDataError(f"run_cmd condition is invalid: {key}") from exc
    expected = {
        "thread_num": 48, "ycsb_tuple_num": 1_000_000, "extime": 3,
        "clocks_per_us": 1800, "ycsb_zipf_skew": 0.9,
        "ycsb_rratio": READ_RATIOS[workload], "ycsb_rmw": 0,
    }
    if observed != expected:
        _fail(f"run_cmd measurement conditions differ: {observed!r}")
    return {
        **observed,
        "numactl_args": ["--interleave=all"],
        "perf_events": list(EXPECTED_PERF_EVENTS),
    }


def _trace_disabled(payload: Mapping[str, Any]) -> None:
    """裁定済みの単一 field だけから compile-time trace 契約を読む。"""
    command = payload.get("perf_configure_cmd")
    if type(command) is not str:
        _fail("build_done perf_configure_cmd must be a string")
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError as exc:
        raise FigureDataError("perf_configure_cmd cannot be safely split") from exc
    matches = [
        token.split("=", 1)[1]
        for token in tokens
        if token.startswith("-DCCBENCH_TRACE=")
    ]
    if matches != ["0"]:
        _fail(f"build_done trace contract differs: {matches!r}")


def _project_segment(role: str, segment: Sequence[object]) -> tuple[dict, dict | None]:
    start_record = segment[0]
    start = start_record.payload
    if not isinstance(start, Mapping):
        _fail("session-start payload is not a Mapping")
    if start.get("campaign_role") != role:
        _fail(f"session role differs: {role}")
    schedule_index = start.get("schedule_index")
    if isinstance(schedule_index, bool) or not isinstance(schedule_index, int):
        _fail("schedule_index is not an integer")
    variant = start.get("variant")
    if type(variant) is not str or not variant or start_record.variant != variant:
        _fail("session-start variant differs")
    cell_id = normalize_wal_cell_id(start.get("cell_id"))
    result_record = _single(
        segment, lambda row: _event(row, "session-result"), "session-result")
    result = result_record.payload
    if (result.get("status") != "success" or result.get("reason") != "certified"
            or result.get("campaign_role") != role
            or result.get("schedule_index") != schedule_index
            or result.get("variant") != variant
            or normalize_wal_cell_id(result.get("cell_id")) != cell_id):
        _fail("session-result identity/status differs")
    build = _single(
        segment,
        lambda row: row.stage == "build_start" and row.variant == variant,
        "build_start",
    )
    build_done = _single(
        segment,
        lambda row: row.stage == "build_done" and row.variant == variant,
        "build_done",
    )
    commit = _single(
        segment, lambda row: row.stage == "commit" and row.variant == variant,
        "commit",
    )
    if not all(isinstance(row.payload, Mapping) for row in (build, build_done, commit)):
        _fail("immutable WAL payload is not a Mapping")
    _trace_disabled(build_done.payload)
    src_token = build.payload.get("src_token")
    verify = commit.payload.get("verify_configs")
    if type(src_token) is not str or not src_token:
        _fail("build_start src_token is missing")
    if not isinstance(verify, (list, tuple)) or not all(type(x) is str for x in verify):
        _fail("commit verify_configs is invalid")
    expected_verify = ("legacy", "s2") if role == "develop" else ("legacy",)
    if tuple(verify) != expected_verify:
        _fail(f"commit verify_configs differs: {role}")
    unstable = commit.payload.get("unstable", False)
    if type(unstable) is not bool:
        _fail("commit unstable is not bool")
    fitness = commit.payload.get("fitness_tps")
    bench_projection = None
    if role == "develop":
        if fitness is not None or any(row.stage == "bench_done" for row in segment):
            _fail("develop session unexpectedly has performance evidence")
        clean_fitness = None
    else:
        clean_fitness = _finite_number(fitness, "commit fitness_tps", positive=True)
        bench = _single(
            segment, lambda row: row.stage == "bench_done" and row.variant == variant,
            "bench_done",
        )
        if not isinstance(bench.payload, Mapping):
            _fail("bench payload is not a Mapping")
        repetitions = bench.payload.get("tps")
        if not isinstance(repetitions, (list, tuple)) or len(repetitions) != 5:
            _fail("bench tps must contain exactly five repetitions")
        clean_repetitions = [
            _finite_number(value, "bench tps", positive=True) for value in repetitions
        ]
        median = statistics.median(clean_repetitions)
        _same(bench.payload.get("median_tps"), median, "bench median_tps")
        _same(clean_fitness, median, "commit fitness_tps")
        if bench.payload.get("unstable", False) is not unstable:
            _fail("bench/commit unstable differs")
        workload = cell_id.split(":", 1)[0]
        conditions = _parse_run_command(bench.payload.get("run_cmd"), workload)
        bench_projection = {
            "tps": clean_repetitions,
            "median_tps": median,
            "conditions": conditions,
            "env": str(bench.env_tag),
        }
    evidence = {
        "role": role,
        "schedule_index": schedule_index,
        "cell_id": cell_id,
        "variant_id": variant,
        "src_token": src_token,
        "fitness_tps": clean_fitness,
        "verify_configs": list(verify),
        "unstable": unstable,
    }
    return evidence, bench_projection


def _epoch_projection(
        epoch: object, *, verifier_assessment_basis: str | None = None,
) -> dict[str, Any]:
    projection = {
        "campaign_verifier_epoch": epoch.campaign_verifier_epoch,
        "state": epoch.state,
        "reason_code": epoch.reason_code,
        "identity_scope": epoch.identity_scope,
        "excluded_scope": epoch.excluded_scope,
    }
    if verifier_assessment_basis is not None:
        projection["verifier_assessment_basis"] = verifier_assessment_basis
    return projection


def _campaign_lock_commit(path: Path) -> str:
    document = _strict_json(path)
    commit = document.get("ccbench_commit")
    if commit != "d706650":
        _fail(f"campaign ccbench_commit differs: {commit!r}")
    # spec_content and all other strings are intentionally ignored as data.
    return commit


def load_campaign(role: str, campaign_dir: os.PathLike[str] | str) -> dict[str, Any]:
    if role not in ROLES:
        _fail(f"unknown campaign role: {role}")
    directory = _repo_path(campaign_dir)
    if directory.name != CANONICAL_CAMPAIGNS[role]:
        _fail(f"canonical campaign differs for {role}: {directory.name}")
    expected_wal = directory / "runs" / "wal.jsonl"
    expected_lock = directory / "campaign.lock"
    view = require_admitted_campaign(
        directory, purpose=CampaignReadPurpose.HISTORICAL_RAW)
    wal_path = Path(view.wal_file).resolve()
    lock_path = Path(view.lock_file).resolve()
    if wal_path != expected_wal.resolve() or lock_path != expected_lock.resolve():
        _fail(f"admission layout differs for {role}")
    if Path(view.layout.root).resolve().name != directory.name:
        _fail(f"campaign id differs from basename: {role}")
    for _ in wal.iter_lines(str(wal_path)):
        pass
    rows: list[dict[str, Any]] = []
    benches: dict[int, dict[str, Any]] = {}
    for segment in _segments(view.records):
        evidence, bench = _project_segment(role, segment)
        index = evidence["schedule_index"]
        if index in {row["schedule_index"] for row in rows}:
            _fail(f"duplicate schedule index: {role}:{index}")
        rows.append(evidence)
        if bench is not None:
            benches[index] = bench
    rows.sort(key=lambda row: row["schedule_index"])
    if len(rows) != EXPECTED_COUNTS[role]:
        _fail(f"campaign projected sample count differs: {role}:{len(rows)}")
    epoch = _epoch_projection(
        view.campaign_verifier_epoch,
        verifier_assessment_basis=view.verifier_assessment_basis,
    )
    if (view.read_purpose is not CampaignReadPurpose.HISTORICAL_RAW
            or epoch["state"] != "E0"
            or epoch["reason_code"] != "v1-authority-absent"):
        _fail(f"historical E0 contract differs: {role}")
    receipt = view.decision.as_receipt()
    if receipt.get("campaign_id") != directory.name:
        _fail(f"admission receipt campaign differs: {role}")
    commit = _campaign_lock_commit(lock_path)
    return {
        "role": role,
        "campaign": directory.name,
        "dir": _rel(directory),
        "wal": _rel(wal_path),
        "wal_sha256": _sha256(wal_path),
        "lock": _rel(lock_path),
        "lock_sha256": _sha256(lock_path),
        "read_purpose": view.read_purpose.value,
        "campaign_verifier_epoch": epoch,
        "admission_decision": receipt,
        "ccbench_commit": commit,
        "evidence": rows,
        "benches": benches,
    }


def _evidence_sort(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return sorted((dict(row) for row in rows), key=lambda row: row["schedule_index"])


def _group_samples(campaigns: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, list[dict]]]:
    grouped: dict[str, dict[str, list[dict]]] = {role: {} for role in ROLES}
    for role, campaign in campaigns.items():
        for row in campaign["evidence"]:
            grouped[role].setdefault(row["cell_id"], []).append(dict(row))
    return grouped


def _strict_gate1(relative: object, floor_cmp: object) -> bool:
    """判定境界は等号を含めず、相対中央値差が floor を厳密に超える時だけ通す。"""
    clean_relative = _finite_number(relative, "relative median difference")
    clean_floor = _finite_number(floor_cmp, "floor_cmp", positive=True)
    return clean_relative > clean_floor


def _validate_report_judgment(
    comparison_id: str, judgment: object, gate1: bool, gate2: bool,
) -> None:
    """WAL 再計算 gate と凍結 report の判定が食い違えば描画前に停止する。"""
    if judgment not in PAIR_JUDGMENT_STYLE:
        _fail(f"unknown comparison judgment: {comparison_id}:{judgment!r}")
    expected = "成立" if gate1 and gate2 else "不成立"
    if judgment != expected:
        _fail(
            f"frozen judgment differs from recomputed gates: {comparison_id}:"
            f" report={judgment!r} recomputed={expected!r}"
        )


def _cv(values: Sequence[float]) -> float:
    if len(values) != 8:
        _fail(f"floor CV requires n=8, got {len(values)}")
    mean = statistics.fmean(values)
    if mean <= 0.0:
        _fail("floor CV mean must be positive")
    return statistics.stdev(values) / mean


def _sign(value: float) -> int:
    return 1 if value > 0 else (-1 if value < 0 else 0)


def _cell_stats(grouped: Mapping[str, Mapping[str, Sequence[Mapping[str, Any]]]], cell_id: str) -> dict:
    block_values: dict[str, list[float]] = {}
    unstable = 0
    for role in ("block1", "block2"):
        rows = grouped[role].get(cell_id, ())
        if len(rows) != 4:
            _fail(f"block cell must contain four samples: {role}:{cell_id}")
        block_values[role] = [
            _finite_number(row.get("fitness_tps"), f"{role}:{cell_id}", positive=True)
            for row in rows
        ]
        unstable += sum(row.get("unstable") is True for row in rows)
    values = block_values["block1"] + block_values["block2"]
    mean = statistics.fmean(values)
    stdev = statistics.stdev(values)
    half = T_975_DF7 * stdev / math.sqrt(len(values))
    return {
        "cell_id": cell_id,
        "n": 8,
        "samples_tps": values,
        "block_samples_tps": block_values,
        "mean_tps": mean,
        "median_tps": statistics.median(values),
        "ci95_mean_low_tps": mean - half,
        "ci95_mean_high_tps": mean + half,
        "ci95_mean_half_tps": half,
        "unstable_count": unstable,
    }


def _comparison_fact(
    comparison: Mapping[str, Any], grouped: Mapping[str, Mapping[str, Sequence[Mapping[str, Any]]]],
    cells: Mapping[str, Mapping[str, Any]], effects: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    comparison_id = comparison["comparison_id"]
    workload = comparison["workload"]
    left = _report_cell_id(comparison["left_cell"])
    right = _report_cell_id(comparison["right_cell"])
    if (comparison.get("family") != "S-1a" or comparison.get("alternative") != "greater"
            or left != f"{workload}:system_gate"
            or right != f"{workload}:{comparison_id.rsplit(':', 1)[-1]}"):
        _fail(f"S-1a comparison identity differs: {comparison_id}")
    target = cells[left]
    control = cells[right]
    relative = (target["median_tps"] - control["median_tps"]) / control["median_tps"]
    floor_left_values = [
        _finite_number(row.get("fitness_tps"), "floor left", positive=True)
        for row in grouped["floor"].get(left, ())
    ]
    floor_right_values = [
        _finite_number(row.get("fitness_tps"), "floor right", positive=True)
        for row in grouped["floor"].get(right, ())
    ]
    floor_left_cv = _cv(floor_left_values)
    floor_right_cv = _cv(floor_right_values)
    floor_cmp = max(floor_left_cv, floor_right_cv, 0.03)
    gate1 = _strict_gate1(relative, floor_cmp)
    pooled_sign = _sign(target["median_tps"] - control["median_tps"])
    block_signs = [
        _sign(statistics.median(target["block_samples_tps"][role])
              - statistics.median(control["block_samples_tps"][role]))
        for role in ("block1", "block2")
    ]
    gate2 = pooled_sign != 0 and block_signs == [pooled_sign, pooled_sign]
    gate_report = comparison.get("gates")
    if not isinstance(gate_report, Mapping):
        _fail(f"comparison gates missing: {comparison_id}")
    gate1_report = gate_report.get("gate1")
    gate2_report = gate_report.get("gate2")
    if not isinstance(gate1_report, Mapping) or not isinstance(gate2_report, Mapping):
        _fail(f"comparison gate shape differs: {comparison_id}")
    _same(relative, gate1_report.get("relative_median_difference"),
          f"relative median {comparison_id}")
    _same(relative, effects[comparison_id].get("relative_median_difference"),
          f"effect relative median {comparison_id}")
    _same(floor_cmp, comparison.get("floor_cmp"), f"floor_cmp {comparison_id}")
    _same(floor_left_cv, effects[comparison_id].get("floor_left_cv"),
          f"floor left CV {comparison_id}")
    _same(floor_right_cv, effects[comparison_id].get("floor_right_cv"),
          f"floor right CV {comparison_id}")
    if (gate1_report.get("passed") is not gate1
            or gate2_report.get("passed") is not gate2
            or gate2_report.get("pooled_direction_sign") != pooled_sign
            or gate2_report.get("block_direction_signs") != block_signs):
        _fail(f"recomputed gates differ from report: {comparison_id}")
    _validate_report_judgment(
        comparison_id, comparison.get("judgment"), gate1, gate2)
    return {
        "comparison_id": comparison_id,
        "workload": workload,
        "left_cell": left,
        "right_cell": right,
        "left_median_tps": target["median_tps"],
        "right_median_tps": control["median_tps"],
        "relative_median_difference": relative,
        "relative_median_difference_percent": relative * 100.0,
        "floor_cmp": floor_cmp,
        "gate1_recomputed_for_consistency": gate1,
        "gate2_recomputed_for_consistency": gate2,
        # 描画判定の唯一の出所は以下の凍結 report fields。
        "judgment": comparison["judgment"],
        "p_perm": comparison["p_perm"],
        "p_star": comparison["p_star"],
    }


def _validate_freeze(freeze: Mapping[str, Any], report: Mapping[str, Any]) -> None:
    cells = freeze.get("cells")
    if not isinstance(cells, Mapping) or set(cells) != {
        f"{workload}:{configuration}"
        for workload in WORKLOADS for configuration in CONFIGURATIONS
    }:
        _fail("current freeze exact 18-cell set differs")
    comparisons = freeze.get("comparisons")
    if type(comparisons) is not list or len(comparisons) != 12:
        _fail("current freeze exact comparison count differs")
    if {row.get("comparison_id") for row in comparisons if isinstance(row, Mapping)} != _expected_comparison_ids():
        _fail("current freeze comparison id set differs")
    expected_note = "stock_common は併記用の文脈セルであり、検定比較対には含めない。"
    if any(not isinstance(row, Mapping) or row.get("note") != expected_note for row in comparisons):
        _fail("current freeze comparison note differs")
    if freeze.get("operating_point") != {
        "RECORDS": 1_000_000, "THREADS": 48, "EXTIME": 3, "REPS": 5,
    }:
        _fail("current freeze operating point differs")
    if freeze.get("workload_flags") != {
        workload: {"ycsb_rratio": str(READ_RATIOS[workload])} for workload in WORKLOADS
    }:
        _fail("current freeze workload flags differ")
    report_ids = {row["comparison_id"] for row in report["comparisons"]}
    if report_ids != {row["comparison_id"] for row in comparisons}:
        _fail("current freeze/report comparison semantics differ")


def _display_percent(value: object) -> str:
    return f"{_finite_number(value, 'caption percent'):+.1f}".replace("-", "−")


def _caption(
    comparisons: Sequence[Mapping[str, Any]], claim: Mapping[str, Any],
    unstable_sample_count: int,
) -> str:
    """親確定 caption の正文を、report/WAL 由来の数値で組み立てる。"""
    by_axis = {
        axis: [row["relative_median_difference_percent"] for row in comparisons
               if row["right_cell"].endswith(f":{axis}")]
        for axis in AXES
    }
    flags = by_axis["p2_2_flag_opt"]
    backoff = by_axis["backoff_fixed_best"]
    ordering = by_axis["sort_best"]
    if not isinstance(unstable_sample_count, int) or unstable_sample_count < 0:
        _fail("caption unstable sample count is invalid")
    if claim.get("judgment") != "不成立":
        _fail(f"caption S-1a judgment differs: {claim.get('judgment')!r}")
    return (
        "図4. 縮小主張 S' の性能次元 (S-1a) — 既知軸最良に対する直接比較 9 対 (失敗報告)。"
        "上段は、abort 要因別に backoff の発火可否を切り替える合成軸 (trigger gating) と、既知軸の"
        "最良 3 種 — コンパイル時フラグ最適化、静的 backoff の最良値、書込ロック順の並べ替え — との"
        "相対中央値差である。各点は 100 × (合成軸側の中央値 − 相手側の中央値) / 相手側の中央値 で、"
        "各セル 8 標本から再計算した。灰色の実線は差 0、赤の破線は厳密に超える必要がある判定境界"
        " +3% (between-run floor = 走行間の再現ばらつきの下限) で、薄赤の領域は境界を超えない範囲である。"
        "S-1a の成立条件は 9 対すべてが境界を超えることである。コンパイル時フラグ最適化との 3 対は"
        f" {_display_percent(flags[0])}%〜{_display_percent(flags[-1])}%、静的 backoff 最良値との 3 対は"
        f" {_display_percent(backoff[0])}%〜{_display_percent(backoff[-1])}% で境界を超えず、書込ロック順"
        f"並べ替えとの 3 対だけが {_display_percent(ordering[0])}%〜{_display_percent(ordering[-1])}% で超えた。"
        f"9 対中 {claim['failed_pair_count']} 対が満たされず、{claim['passed_pair_count']} 対が満たしたため、"
        f"S-1a は不成立である (family p = {claim['p_family']:.1f})。"
        "下段は各セルの 8 標本を全数表示したもので、短い横線が中央値、菱形と誤差棒が標本平均と"
        " t 分布による 95% 信頼区間である。下段の平均の信頼区間は標本分布の記述用であり、上段の"
        "相対中央値差、判定境界、family 判定のいずれにも用いていない。下段の縦軸は workload ごとに"
        "独立なので、パネル間で点の高さや区間の幅を直接比べてはならない。"
        "各標本の値は同一セッション内 5 反復の中央値であり、M tps は毎秒 100 万トランザクションを表す。"
        "unstable と記録された標本は除外しない契約であり、本図の対象 12 セルには 1 件も無かった。"
        "測定条件は Silo、48 スレッド、レコード数 1,000,000、Zipf skew 0.9、read-modify-write 無効、"
        "実行時間 3 秒、`clocks_per_us` = 1,800 TSC tick/µs、トレース無効、`numactl --interleave=all`、"
        "環境タグ `linux-baremetal`、CCBench commit `d706650`。read 比率だけが workload ごとに異なる"
        " (write-heavy 5%、balanced 50%、read-heavy 95%)。"
        "測定は `perf stat` 下で最終レベルキャッシュの load misses / loads、instructions、cycles を"
        "収集しながら行われた記録であり、そのオーバーヘッドを含む。したがって本図の絶対スループットは"
        "論文の headline 値の出所ではなく、現行の同一 campaign 内対測定契約 (D496) を満たすとも"
        "主張しない。この限定は凍結済みの S-1a 判定を変更しない。"
        "生の追記専用ログ (write-ahead log; WAL) は admission を経た `HISTORICAL_RAW` として"
        " verifier epoch E0 で再読し、凍結報告が certified accepted evidence として受理した行と"
        "一致するものだけを描いた。判定と p 値は凍結報告から読んでおり、本図の生成器はそれを"
        "再計算していない。"
        "S-1b は既知軸最良との優劣を問う S-1a とは独立の主張であり、その成立は S-1a の不成立を救わない。"
    )


def build_figure_data(
    report_path: os.PathLike[str] | str,
    campaign_dirs: Mapping[str, os.PathLike[str] | str],
) -> dict[str, Any]:
    report_file = _repo_path(report_path)
    if _rel(report_file) != REPORT_REL.as_posix():
        _fail(f"canonical report path differs: {_rel(report_file)}")
    report = _strict_json(report_file)
    by_id = _validate_report(report)
    if set(campaign_dirs) != set(ROLES):
        _fail("campaign role arguments differ")
    campaigns = {role: load_campaign(role, campaign_dirs[role]) for role in ROLES}
    accepted = report["hard_gates"]["certified"]["accepted_evidence"]
    for role in ROLES:
        if _evidence_sort(accepted[role]) != campaigns[role]["evidence"]:
            _fail(f"physical WAL projection differs from accepted_evidence: {role}")
    grouped = _group_samples(campaigns)

    freeze_path = _repo_path(FREEZE_REL)
    freeze = _strict_json(freeze_path)
    _validate_freeze(freeze, report)
    current_freeze_sha = _sha256(freeze_path)
    if current_freeze_sha == REPORT_FREEZE_SHA256:
        _fail("ruled report/current freeze mismatch unexpectedly disappeared")

    cells = {
        f"{workload}:{configuration}": _cell_stats(
            grouped, f"{workload}:{configuration}")
        for workload in WORKLOADS for configuration in PLOT_CONFIGURATIONS
    }
    ordered_comparisons: list[dict[str, Any]] = []
    for workload in WORKLOADS:
        for axis in AXES:
            comparison = by_id[f"S-1a:{workload}:{axis}"]
            ordered_comparisons.append(_comparison_fact(
                comparison, grouped, cells, report["effect_sizes"]))
    passed = sum(row["judgment"] == "成立" for row in ordered_comparisons)
    failed = sum(row["judgment"] == "不成立" for row in ordered_comparisons)
    if (passed, failed) != (3, 6):
        _fail(f"frozen judgment counts differ: pass={passed} fail={failed}")
    family = report["families"]["s1a"]
    claim = {
        "claim_id": "S-1a",
        "judgment": family["judgment"],
        "p_family": family["p_family"],
        "pair_count": 9,
        "passed_pair_count": passed,
        "failed_pair_count": failed,
        "conjunction_required": True,
    }

    context_cells: dict[str, Any] = {}
    for workload in WORKLOADS:
        stock_id = f"{workload}:stock_common"
        stock = _cell_stats(grouped, stock_id)
        sort = cells[f"{workload}:sort_best"]
        system = cells[f"{workload}:system_gate"]
        note = freeze["cells"][f"{workload}:sort_best"]["variant"].get("note")
        context_cells[workload] = {
            "cell_id": stock_id,
            "registered_comparison": False,
            "n": stock["n"],
            "samples_tps": stock["samples_tps"],
            "median_tps": stock["median_tps"],
            "sort_best_relative_to_stock": (
                sort["median_tps"] - stock["median_tps"]) / stock["median_tps"],
            "system_gate_relative_to_stock": (
                system["median_tps"] - stock["median_tps"]) / stock["median_tps"],
            "sort_selection_history": note,
        }

    all_benches = [
        bench for role in PERFORMANCE_ROLES
        for bench in campaigns[role]["benches"].values()
    ]
    if len(all_benches) != 288:
        _fail(f"performance bench count differs: {len(all_benches)}")
    if {bench["env"] for bench in all_benches} != {"linux-baremetal"}:
        _fail("performance env differs")
    conditions = {
        json.dumps(bench["conditions"], sort_keys=True) for bench in all_benches
    }
    if len(conditions) != 3:
        _fail("measurement conditions must contain exactly three read ratios")
    unstable_total = sum(
        row["unstable"] for role in ("block1", "block2")
        for row in campaigns[role]["evidence"]
    )
    if unstable_total != 0:
        _fail("the ruled figure expects zero unstable block samples")

    caption = _caption(ordered_comparisons, claim, unstable_total)
    facts = {
        "claim": claim,
        "measurement_conditions": {
            "threads": 48, "records": 1_000_000, "duration_s": 3,
            "clocks_per_us": 1800, "zipf_skew": 0.9,
            "read_ratios_percent": READ_RATIOS, "read_modify_write": False,
            "env": "linux-baremetal", "ccbench_commit": "d706650",
            "CCBENCH_TRACE": 0, "numactl_args": ["--interleave=all"],
            "perf": "stat", "perf_events": list(EXPECTED_PERF_EVENTS),
            "repetitions_per_session": 5, "session_statistic": "median",
            "samples_per_cell": 8,
            "unstable_policy": "retain all accepted evidence; do not filter",
            "unstable_sample_count": unstable_total,
        },
        "cells": cells,
        "comparisons": ordered_comparisons,
        "context_cells": context_cells,
        "freeze_proof": {
            "report_freeze_ref": {
                "path": report["freeze_ref"]["path"],
                "sha256": report["freeze_ref"]["sha256"],
            },
            "current_freeze_path": FREEZE_REL.as_posix(),
            "current_freeze_sha256": current_freeze_sha,
            "freeze_ref_matches_current": False,
            "historical_emission_commit": FREEZE_EMISSION_COMMIT,
            "changed_json_pointers": list(FREEZE_CHANGED_POINTERS),
            "figure_semantics_equal": [
                "18 cell definitions", "12 comparison definitions and notes",
                "operating_point", "workload_flags",
            ],
        },
        "plot_contract": {
            "layout": "2 rows x 3 columns",
            "workload_order": list(WORKLOADS),
            "axis_order": list(AXES),
            "order_source": "frozen axis order and ascending read ratio; never effect size",
            "xlim_percent": [-105.0, 105.0],
            "zero_line_percent": 0.0,
            "strict_floor_line_percent": 3.0,
            "failure_region_percent": [-105.0, 3.0],
            "equal_marker_area": True,
            "random_jitter": False,
            "bottom_y_scales": "independent by workload",
            "bottom_tick_labels": [DISPLAY_LABELS[value] for value in PLOT_CONFIGURATIONS],
            "stock_common_drawn": False,
        },
        "figure_conventions_compliance": {
            "status": "partial",
            "reason": (
                "samples and aggregates are recomputed from WAL; frozen judgment and p-values "
                "are read from the hash-bound report"
            ),
        },
    }
    return {
        "report": report,
        "report_path": _rel(report_file),
        "report_sha256": _sha256(report_file),
        "campaigns": campaigns,
        "facts": facts,
        "caption": caption,
    }


def _load_plotting():
    import matplotlib as mpl
    mpl.use("Agg")
    import matplotlib.pyplot as plt
    return mpl, plt


def _style(mpl) -> None:
    mpl.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 200,
        "font.family": "DejaVu Sans", "font.size": 8.5,
        "axes.titlesize": 9, "axes.labelsize": 8,
        "xtick.labelsize": 7, "ytick.labelsize": 7,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.22, "grid.linewidth": 0.5,
        "legend.frameon": False,
    })


def _claim_display(claim: Mapping[str, Any]) -> dict[str, Any]:
    judgment = claim.get("judgment")
    if judgment not in FAMILY_JUDGMENT_DISPLAY:
        _fail(f"unknown family judgment: {judgment!r}")
    counts = {
        key: claim.get(key)
        for key in ("pair_count", "passed_pair_count", "failed_pair_count")
    }
    if (any(isinstance(value, bool) or not isinstance(value, int) or value < 0
            for value in counts.values())
            or counts["passed_pair_count"] + counts["failed_pair_count"]
            != counts["pair_count"]):
        _fail(f"claim pair counts differ: {counts!r}")
    return {
        **counts,
        "judgment_display": FAMILY_JUDGMENT_DISPLAY[judgment],
        "p_family": _finite_number(claim.get("p_family"), "family p"),
    }


def _draw_top_panel(
    axis, workload: str, comparisons: Sequence[Mapping[str, Any]],
    claim_display: Mapping[str, Any],
) -> None:
    failed_color = "#9d2a2a"
    passed_color = "#496f8a"
    axis.axvspan(-105.0, 3.0, color="#f6dede", alpha=0.48, zorder=0)
    axis.axvline(0.0, color="#777777", linewidth=0.8, linestyle="-", zorder=1,
                 gid="s1-reference-line")
    axis.axvline(3.0, color=failed_color, linewidth=1.0, linestyle="--", zorder=1,
                 gid="s1-reference-line")
    y_positions = [2, 1, 0]
    for y, comparison in zip(y_positions, comparisons):
        value = comparison["relative_median_difference_percent"]
        judgment = comparison.get("judgment")
        if judgment not in PAIR_JUDGMENT_STYLE:
            _fail(f"unknown comparison judgment for artist: {judgment!r}")
        marker, color = PAIR_JUDGMENT_STYLE[judgment]
        passed = judgment == "成立"
        kwargs = {
            "s": TOP_MARKER_AREA_PT2, "marker": marker, "color": color,
            "linewidths": 1.35, "zorder": 4, "gid": "s1-data-marker",
        }
        if passed:
            kwargs.update({"facecolors": "none", "edgecolors": color})
        axis.scatter([value], [y], **kwargs)
        if value < 0.0:
            label_offset = (-DATA_LABEL_OFFSET_PT, 0.0)
            label_kwargs = {"ha": "right", "va": "center", "rotation": 0.0}
        else:
            # +98.4% でも ±105% の対称軸内へ収めつつ、marker の右上へ外向きに離す。
            label_offset = (1.0, 8.0)
            label_kwargs = {
                "ha": "center", "va": "bottom", "rotation": 90.0,
                "rotation_mode": "default",
            }
        label = axis.annotate(
            f"{value:+.1f}%", xy=(value, y), xytext=label_offset,
            textcoords="offset points", **label_kwargs,
            color=color, fontsize=7.0, zorder=5, annotation_clip=True,
        )
        if hasattr(label, "set_gid"):
            label.set_gid("s1-data-label")
    axis.text(-101.0, 2.42, "does not clear gate", color=failed_color,
              ha="left", va="top", fontsize=6.5)
    axis.text(4.2, 2.42, "strict floor: > +3%", color=failed_color,
              ha="left", va="top", fontsize=6.5)
    axis.set_xlim(-105.0, 105.0)
    axis.set_ylim(-0.55, 2.55)
    axis.set_xticks([-100.0, -50.0, 0.0, 50.0, 100.0])
    axis.set_yticks(y_positions, [DISPLAY_LABELS[value] for value in AXES])
    axis.set_xlabel("relative median difference (%)")
    axis.set_title(workload)
    axis.scatter(
        [], [], s=TOP_MARKER_AREA_PT2, marker="x", color=failed_color,
        label=("registered pair criterion not met "
               f"({claim_display['failed_pair_count']}/{claim_display['pair_count']})"),
    )
    axis.scatter(
        [], [], s=TOP_MARKER_AREA_PT2, marker="o", facecolors="none",
        edgecolors=passed_color,
        label=("pair criterion met "
               f"({claim_display['passed_pair_count']}/{claim_display['pair_count']}; "
               f"S-1a remains {claim_display['judgment_display'].lower()})"),
    )


def _draw_bottom_panel(axis, workload: str, cells: Mapping[str, Mapping[str, Any]]) -> None:
    cell_ids = [f"{workload}:{configuration}" for configuration in PLOT_CONFIGURATIONS]
    colors = ["#666666"] * 4
    for x, (cell_id, color) in enumerate(zip(cell_ids, colors)):
        cell = cells[cell_id]
        block1 = [value / 1e6 for value in cell["block_samples_tps"]["block1"]]
        block2 = [value / 1e6 for value in cell["block_samples_tps"]["block2"]]
        axis.scatter([x - 0.12] * 4, block1, s=26.0, marker="o", color=color,
                     alpha=0.78, zorder=3)
        axis.scatter([x + 0.12] * 4, block2, s=26.0, marker="s", color=color,
                     alpha=0.78, zorder=3)
        median = cell["median_tps"] / 1e6
        mean = cell["mean_tps"] / 1e6
        half = cell["ci95_mean_half_tps"] / 1e6
        axis.hlines(median, x - 0.23, x + 0.23, color="#111111", linewidth=1.4,
                    zorder=4)
        axis.errorbar([x], [mean], yerr=[[half], [half]], fmt="D", color="#111111",
                      markerfacecolor="white", markersize=4.6, capsize=3,
                      linewidth=1.0, zorder=5)
    axis.set_xticks(range(4), [DISPLAY_LABELS[value] for value in PLOT_CONFIGURATIONS],
                    rotation=70, ha="right", rotation_mode="anchor")
    axis.set_ylabel("throughput (M tps)")
    axis.margins(y=0.16)
    axis.scatter([], [], s=26.0, marker="o", color="#666666", label="block1 samples")
    axis.scatter([], [], s=26.0, marker="s", color="#666666", label="block2 samples")
    axis.errorbar([], [], yerr=[], fmt="D", color="#111111", markerfacecolor="white",
                  label="mean and t 95% CI")


def draw_figure_artists(fig, axes, data: Mapping[str, Any]) -> None:
    comparisons = data["facts"]["comparisons"]
    cells = data["facts"]["cells"]
    claim = data["facts"]["claim"]
    claim_display = _claim_display(claim)
    for column, workload in enumerate(WORKLOADS):
        selected = [row for row in comparisons if row["workload"] == workload]
        _draw_top_panel(axes[0][column], workload, selected, claim_display)
        _draw_bottom_panel(axes[1][column], workload, cells)
    axes[0][0].legend(loc="lower left", bbox_to_anchor=(0.0, 1.10), fontsize=6.4)
    bottom_handles, bottom_labels = axes[1][0].get_legend_handles_labels()
    fig.legend(
        bottom_handles, bottom_labels,
        loc="lower center", bbox_to_anchor=BOTTOM_LEGEND_ANCHOR,
        bbox_transform=fig.transFigure, fontsize=6.4, ncol=3,
    )
    # 回転した x tick の下とは分離し、tight bbox に含まれる figure 下端の予約帯へ固定する。
    fig.text(
        0.5, 0.985,
        f"S-1a {claim_display['judgment_display']} — "
        f"{claim_display['failed_pair_count']} of "
        f"{claim_display['pair_count']} pairs fail — "
        f"family p={claim_display['p_family']:.1f}",
        ha="center", va="top", color="#8d1f1f", fontsize=10, fontweight="bold",
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "#fff7f7",
              "edgecolor": "#a53a3a", "linewidth": 0.9},
    )
    fig.suptitle(
        FIGURE_TITLE_TEXT,
        fontsize=8.2, y=0.947,
    )


def _bbox_intersection_area(left, right) -> float:
    x0 = max(left.x0, right.x0)
    y0 = max(left.y0, right.y0)
    x1 = min(left.x1, right.x1)
    y1 = min(left.y1, right.y1)
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def _bbox_contains(outer, inner, tolerance: float = 0.5) -> bool:
    return (
        inner.x0 >= outer.x0 - tolerance
        and inner.y0 >= outer.y0 - tolerance
        and inner.x1 <= outer.x1 + tolerance
        and inner.y1 <= outer.y1 + tolerance
    )


def _is_production_axes(axes) -> bool:
    return (
        len(axes) == 2
        and all(len(row) == len(WORKLOADS) for row in axes)
    )


def _check_required_artists(fig, axes, renderer, all_boxes) -> None:
    """必須 text の実在と、bbox_inches="tight" の実保存領域内包を検査する。"""
    from matplotlib import rcParams

    observed_counts = {
        value: sum(text.get_text() == value for text, _box in all_boxes)
        for value in REQUIRED_ARTIST_TEXTS
    }
    count_mismatches = {
        value: (REQUIRED_ARTIST_TEXT_COUNTS[value], observed_counts[value])
        for value in REQUIRED_ARTIST_TEXTS
        if observed_counts[value] != REQUIRED_ARTIST_TEXT_COUNTS[value]
    }
    if count_mismatches:
        raise FigureLayoutError(
            f"required artist text missing or duplicated: {count_mismatches!r}"
        )

    top_legend = axes[0][0].get_legend()
    top_labels = (
        frozenset(text.get_text() for text in top_legend.get_texts())
        if top_legend is not None else frozenset()
    )
    all_legend_labels = [
        frozenset(text.get_text() for text in legend.get_texts())
        for row in axes for axis in row
        for legend in [axis.get_legend()]
        if legend is not None
    ] + [
        frozenset(text.get_text() for text in legend.get_texts())
        for legend in fig.legends
    ]
    if top_labels != TOP_LEGEND_TEXTS:
        raise FigureLayoutError(f"top legend exact text set differs: {sorted(top_labels)!r}")
    if (len(all_legend_labels) != 2
            or all_legend_labels.count(TOP_LEGEND_TEXTS) != 1
            or all_legend_labels.count(BOTTOM_LEGEND_TEXTS) != 1):
        raise FigureLayoutError(
            f"legend exact text sets differ: {all_legend_labels!r}"
        )
    for column, workload in enumerate(WORKLOADS):
        if axes[0][column].get_title() != workload:
            raise FigureLayoutError(f"top panel title differs: {workload!r}")
        if axes[0][column].get_xlabel() != TOP_AXIS_LABEL_TEXT:
            raise FigureLayoutError(f"top panel x label differs: {workload!r}")
        if axes[1][column].get_ylabel() != BOTTOM_AXIS_LABEL_TEXT:
            raise FigureLayoutError(f"bottom panel y label differs: {workload!r}")

    tight_box_inches = fig.get_tightbbox(renderer)
    if tight_box_inches is None:
        raise FigureLayoutError("saved tight bbox is absent")
    pad_inches = rcParams["savefig.pad_inches"]
    if isinstance(pad_inches, bool) or not isinstance(pad_inches, (int, float)):
        raise FigureLayoutError(f"savefig tight padding is not numeric: {pad_inches!r}")
    saved_box = tight_box_inches.padded(float(pad_inches)).transformed(
        fig.dpi_scale_trans
    )
    for text, box in all_boxes:
        if text.get_text() in REQUIRED_ARTIST_TEXTS and not _bbox_contains(saved_box, box):
            raise FigureLayoutError(
                f"required artist outside saved tight bbox: {text.get_text()!r}"
            )


def check_figure_layout(fig, axes) -> None:
    """draw 後・保存前に overlap、逸脱、data label の pixel 余白を検査する。"""
    from matplotlib.text import Annotation, Text

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    figure_box = fig.bbox
    flat_axes = [axis for row in axes for axis in row]
    tick_text = {
        text for axis in flat_axes
        for text in [*axis.get_xticklabels(), *axis.get_yticklabels()]
    }
    legends = [
        legend for legend in [
            *(axis.get_legend() for axis in flat_axes),
            *fig.legends,
        ]
        if legend is not None
    ]
    legend_text = {
        text
        for legend in legends
        for text in [*legend.get_texts(), legend.get_title()]
        if text.get_visible() and text.get_text().strip()
    }
    axis_label_title_text = {
        text
        for axis in flat_axes
        for text in (
            axis.xaxis.label, axis.yaxis.label, axis.title,
            axis._left_title, axis._right_title,
        )
        if text.get_visible() and text.get_text().strip()
    }
    all_texts = [
        text for text in fig.findobj(Text)
        if text.get_visible() and text.get_text().strip()
    ]
    all_boxes = [(text, text.get_window_extent(renderer)) for text in all_texts]
    if _is_production_axes(axes):
        _check_required_artists(fig, axes, renderer, all_boxes)
    for text, box in all_boxes:
        if (box.x0 < figure_box.x0 - 0.5 or box.y0 < figure_box.y0 - 0.5
                or box.x1 > figure_box.x1 + 0.5 or box.y1 > figure_box.y1 + 0.5):
            raise FigureLayoutError(f"text leaves figure bbox: {text.get_text()!r}")
        if text.get_gid() == "s1-data-label":
            owner = text.axes
            if owner is None or not owner.bbox.contains(box.x0, box.y0) or not owner.bbox.contains(box.x1, box.y1):
                raise FigureLayoutError(f"data label leaves axes: {text.get_text()!r}")
        owner = text.axes
        if owner is not None:
            for other in flat_axes:
                if other is not owner and _bbox_intersection_area(box, other.bbox) > 0.5:
                    raise FigureLayoutError(
                        f"text enters neighboring panel: {text.get_text()!r}")

    for axis in flat_axes:
        for kind, labels in (
            ("x", axis.get_xticklabels()), ("y", axis.get_yticklabels()),
        ):
            tick_boxes = [
                (text, text.get_window_extent(renderer))
                for text in labels
                if text.get_visible() and text.get_text().strip()
            ]
            for index, (left_text, left_box) in enumerate(tick_boxes):
                for right_text, right_box in tick_boxes[index + 1:]:
                    if _bbox_intersection_area(left_box, right_box) > 1.0:
                        raise FigureLayoutError(
                            f"{kind} tick text overlap: {left_text.get_text()!r} / "
                            f"{right_text.get_text()!r}"
                        )

    for axis in flat_axes:
        labels = [
            (text, box) for text, box in all_boxes
            if text.axes is axis and text.get_gid() == "s1-data-label"
        ]
        markers: list[tuple[float, float, float]] = []
        for collection in axis.collections:
            if collection.get_gid() != "s1-data-marker":
                continue
            offsets = collection.get_offsets()
            pixels = collection.get_offset_transform().transform(offsets)
            sizes = collection.get_sizes()
            if len(pixels) != 1 or len(sizes) != 1:
                raise FigureLayoutError("data marker collection shape differs")
            markers.append((
                float(pixels[0][0]), float(pixels[0][1]),
                math.sqrt(float(sizes[0])) * fig.dpi / 72.0 / 2.0,
            ))
        if len(labels) != len(markers):
            raise FigureLayoutError(
                f"data label/marker count differs: {len(labels)} != {len(markers)}"
            )
        remaining = list(markers)
        for text, box in labels:
            if not isinstance(text, Annotation):
                raise FigureLayoutError("data label is not an axes Annotation")
            anchor_x, anchor_y = axis.transData.transform(text.xy)
            marker = min(
                remaining,
                key=lambda point: math.hypot(point[0] - anchor_x, point[1] - anchor_y),
            )
            remaining.remove(marker)
            marker_x, marker_y, marker_radius_px = marker
            if math.hypot(marker_x - anchor_x, marker_y - anchor_y) > 0.5:
                raise FigureLayoutError(
                    f"data label is detached from marker: {text.get_text()!r}"
                )
            horizontal_gap = max(box.x0 - marker_x, marker_x - box.x1, 0.0)
            vertical_gap = max(box.y0 - marker_y, marker_y - box.y1, 0.0)
            marker_gap = math.hypot(horizontal_gap, vertical_gap) - marker_radius_px
            if marker_gap < DATA_LABEL_MARKER_CLEARANCE_PX:
                raise FigureLayoutError(
                    f"data label/marker clearance too small: {text.get_text()!r}: "
                    f"{marker_gap:.2f}px"
                )
            for line in axis.lines:
                if line.get_gid() != "s1-reference-line":
                    continue
                x_values = line.get_xdata()
                if len(x_values) == 0:
                    continue
                line_x = axis.transData.transform((float(x_values[0]), 0.0))[0]
                line_gap = max(box.x0 - line_x, line_x - box.x1, 0.0)
                if line_gap < DATA_LABEL_REFERENCE_CLEARANCE_PX:
                    raise FigureLayoutError(
                        f"data label/reference line clearance too small: "
                        f"{text.get_text()!r}: {line_gap:.2f}px"
                    )
    box_by_text = dict(all_boxes)
    data_label_text = {
        text for text in box_by_text if text.get_gid() == "s1-data-label"
    }
    legend_overlap_targets = (
        tick_text | axis_label_title_text | data_label_text
    ) - legend_text
    for left_text in legend_text:
        left_box = box_by_text.get(left_text)
        if left_box is None:
            continue
        for right_text in legend_overlap_targets:
            right_box = box_by_text.get(right_text)
            if (right_box is not None
                    and _bbox_intersection_area(left_box, right_box) > 1.0):
                raise FigureLayoutError(
                    f"legend/text overlap: {left_text.get_text()!r} / "
                    f"{right_text.get_text()!r}"
                )
    boxes = [(text, box) for text, box in all_boxes if text not in tick_text]
    for index, (left_text, left_box) in enumerate(boxes):
        for right_text, right_box in boxes[index + 1:]:
            if _bbox_intersection_area(left_box, right_box) > 1.0:
                raise FigureLayoutError(
                    f"non-tick text overlap: {left_text.get_text()!r} / "
                    f"{right_text.get_text()!r}")


def _atomic_figure_pair(fig, out_prefix: Path) -> None:
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    temporary: list[tuple[Path, Path]] = []
    try:
        for suffix, fmt in ((".png", "png"), (".pdf", "pdf")):
            descriptor, raw = tempfile.mkstemp(
                prefix=f".{out_prefix.name}.", suffix=suffix, dir=out_prefix.parent)
            os.close(descriptor)
            temp_path = Path(raw)
            destination = Path(f"{out_prefix}{suffix}")
            temporary.append((temp_path, destination))
            fig.savefig(temp_path, format=fmt, bbox_inches="tight")
        for temp_path, destination in temporary:
            os.replace(temp_path, destination)
    finally:
        for temp_path, _destination in temporary:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass


def make_figure(
    data: Mapping[str, Any], out_prefix: os.PathLike[str] | str, *,
    figure_factory=None, layout_checker=None, save_callback=None,
):
    """production artist を描き、bbox 検査後にだけ PNG/PDF を保存する。"""
    mpl, plt = _load_plotting()
    with mpl.rc_context():
        _style(mpl)
        if figure_factory is None:
            fig, axes_array = plt.subplots(2, 3, figsize=(12.0, 7.35), squeeze=False)
            axes = [[axes_array[row, column] for column in range(3)] for row in range(2)]
        else:
            fig, axes = figure_factory()
        draw_figure_artists(fig, axes, data)
        fig.tight_layout(rect=FIGURE_LAYOUT_RECT, h_pad=2.2, w_pad=1.2)
        checker = layout_checker or check_figure_layout
        checker(fig, axes)  # 裁定: canvas.draw 後、保存前。
        prefix = _repo_path(out_prefix, must_exist=False)
        if prefix.name != OUTPUT_BASENAME:
            _fail(f"output prefix basename differs: {prefix.name}")
        if save_callback is None:
            _atomic_figure_pair(fig, prefix)
        else:
            save_callback(fig, Path(f"{prefix}.png"))
            save_callback(fig, Path(f"{prefix}.pdf"))
    return fig


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(raw, path)
    finally:
        try:
            os.unlink(raw)
        except FileNotFoundError:
            pass


def build_provenance(
    data: Mapping[str, Any], out_prefix: os.PathLike[str] | str,
    argv: Sequence[str],
) -> dict[str, Any]:
    prefix = _repo_path(out_prefix, must_exist=False)
    output_paths = [Path(f"{prefix}.png"), Path(f"{prefix}.pdf")]
    if not all(path.is_file() for path in output_paths):
        _fail("PNG/PDF must both exist before provenance is written")
    inputs: list[dict[str, Any]] = [{
        "kind": "report",
        "path": data["report_path"],
        "sha256": data["report_sha256"],
        "generated_at_head": data["report"]["generated_at_head"],
    }, {
        "kind": "current_measurement_freeze",
        "path": FREEZE_REL.as_posix(),
        "sha256": data["facts"]["freeze_proof"]["current_freeze_sha256"],
    }]
    for role in ROLES:
        campaign = data["campaigns"][role]
        inputs.append({key: campaign[key] for key in (
            "role", "campaign", "dir", "wal", "wal_sha256", "lock",
            "lock_sha256", "read_purpose", "campaign_verifier_epoch",
            "admission_decision",
        )} | {"kind": "campaign"})
    clean_argv = [str(value) for value in argv]
    return {
        "schema": SCHEMA,
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "generator": GENERATOR_REL.name,
        "generator_source": {
            "path": GENERATOR_REL.as_posix(),
            "sha256": _sha256(REPO_ROOT / GENERATOR_REL),
        },
        "outputs": [
            {"path": _rel(path), "sha256": _sha256(path)} for path in output_paths
        ],
        "inputs": inputs,
        "facts": data["facts"],
        "reproduction": {
            "cwd": "repository-root",
            "argv": clean_argv,
            "command": shlex.join(clean_argv),
        },
        "caption": data["caption"],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out_prefix")
    parser.add_argument("report_json")
    for role in ROLES:
        parser.add_argument(f"--{role}", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    canonical_argv = [
        "python3", GENERATOR_REL.as_posix(), args.out_prefix, args.report_json,
        "--develop", args.develop, "--floor", args.floor,
        "--block1", args.block1, "--block2", args.block2,
    ]
    try:
        data = build_figure_data(args.report_json, {
            role: getattr(args, role) for role in ROLES
        })
        fig = make_figure(data, args.out_prefix)
        provenance = build_provenance(data, args.out_prefix, canonical_argv)
        _atomic_json(Path(f"{_repo_path(args.out_prefix, must_exist=False)}.provenance.json"),
                     provenance)
        _mpl, plt = _load_plotting()
        plt.close(fig)
    except Exception as exc:  # noqa: BLE001 - CLI is fail-closed with rc=1.
        print(f"[error] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {args.out_prefix}.png / .pdf / .provenance.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
