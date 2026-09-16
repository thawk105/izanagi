# -*- coding: utf-8 -*-
"""S-1a 9 対図の provenance、独立再計算、production artist を検査する。

期待値計算は生成器を import せず、admission 済み物理 WAL から session と標本を
独立に再構成する。生成器の import は末尾の描画 spy/bbox test にだけ局所化する。
自走 harness を持つため pytest と直接実行の両方で同じ test_ 関数を走らせる。
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import io
import json
import math
import os
import shlex
import statistics
import sys
import tempfile
from collections.abc import Mapping, Sequence
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestrator.campaign import wal  # noqa: E402
from orchestrator.campaign.artifact_admission import (  # noqa: E402
    CampaignReadPurpose,
    CampaignVerifierEpochRejected,
    require_admitted_campaign,
)


SCHEMA = "izanagi-s1-9pair-figure-provenance/v1"
PROVENANCE_REL = Path(
    "docs/paper-story/figures/fig4_s1a_9pair_direct_comparison.provenance.json")
OUT_PREFIX_REL = Path(
    "docs/paper-story/figures/fig4_s1a_9pair_direct_comparison")
README_REL = Path("docs/paper-story/figures/README.md")
GENERATOR_REL = Path("tools/plotting/plot_s1_9pair.py")
FIG4_GENERATION_TIME_GENERATOR_SHA256 = (
    "4a76d59c854cf8021a711cb27ebeb7aad599c4dda448dd9ee6f15c80ab7d772c"
)
ADMISSION_VALIDATOR_REL = Path("orchestrator/campaign/artifact_admission.py")
REPORT_REL = Path("output/reports/s1_direct_comparison/report.json")
FREEZE_REL = Path("output/s1-freeze/measurement_freeze.json")
FROZEN_TEST_REL = Path("orchestrator/tests/test_frozen_artifacts.py")
WORKLOADS = ("write-heavy", "balanced", "read-heavy")
CONFIGURATIONS = (
    "system_gate", "ident_all", "p2_2_flag_opt", "backoff_fixed_best",
    "sort_best", "stock_common",
)
PLOT_CONFIGURATIONS = (
    "system_gate", "p2_2_flag_opt", "backoff_fixed_best", "sort_best",
)
AXES = ("p2_2_flag_opt", "backoff_fixed_best", "sort_best")
ROLES = ("develop", "floor", "block1", "block2")
PERFORMANCE_ROLES = ("floor", "block1", "block2")
COUNTS = {"develop": 18, "floor": 144, "block1": 72, "block2": 72}
CAMPAIGNS = {
    "develop": "s1-direct-develop-direct-comparison-d0f495bf",
    "floor": "s1-direct-floor-direct-comparison-b82b9229",
    "block1": "s1-direct-block1-direct-comparison-74ff9ba2",
    "block2": "s1-direct-block2-direct-comparison-9645b16a",
}
READ_RATIOS = {"write-heavy": 5, "balanced": 50, "read-heavy": 95}
T_DF7 = 2.365
REPORT_FREEZE_SHA = "5c719c076e17f385a781933c081bf02abcd85b9edb01ad8c50a37740c134a191"
CURRENT_E0_EPOCH = {
    "campaign_verifier_epoch": "E0",
    "state": "E0",
    "reason_code": "v1-authority-absent",
    "identity_scope": (
        "enforcement source closure (curated exact 63 path; source-import 推移閉包ではない; "
        "発見集合は収載 tuple を起点に静的 import と package 初期化を辿った集合であり、"
        "2026-09-16 (a1b40608c) の実測では 162 module、うち収載 63)"
    ),
    "excluded_scope": (
        "同実測の発見集合の未収載 99 module、同発見集合に入らない module、"
        "orchestrator/verifier/__main__.py、orchestrator/verifier/cli.py、"
        "package 外の orchestrator/verify.py、および収載 path の source bytes を除く "
        "data/schema、生成物、subprocess、外部 command/Git、toolchain、binary、動的 "
        "import を含む非 import 委譲は本 map の外であり、完全性を主張しない"
    ),
}
FROZEN_E0_EPOCH = {
    "campaign_verifier_epoch": "E0",
    "state": "E0",
    "reason_code": "v1-authority-absent",
    "identity_scope": (
        "enforcement source closure (exact 27 path; witness gate、S8C 判定器、"
        "批准比較、receipt 発行・検証面を含む)"
    ),
    "excluded_scope": (
        "verifier package のうち orchestrator/verifier/__main__.py と "
        "orchestrator/verifier/cli.py、および package 外の orchestrator/verify.py の "
        "implementation bytes は束縛しない"
    ),
}
ADMISSION_VALIDATOR_IDENTITY = "orchestrator.campaign.artifact_admission"
FROZEN_ADMISSION_VALIDATOR_SHA256 = (
    "ad5ccf08fac75d4f8f61fa00de11be9378d67131315a9cdb0a22a796be280f1e"
)
EXPECTED_TOP_KEYS = {
    "schema", "generated_utc", "generator", "generator_source", "outputs",
    "inputs", "facts", "reproduction", "caption",
}
FORBIDDEN_ARTIST_TEXT = {
    "system_gate", "p2_2_flag_opt", "backoff_fixed_best", "sort_best",
    "ident_all", "stock_common",
}


EXPECTED_SELF_TEST_NAMES = frozenset({
    "test_p1_independent_real_wal_projection_matches_frozen_report",
    "test_p2_certified_acceptance_rejects_historical_e0_campaign",
    "test_p3_real_provenance_closes_bytes_admission_caption_and_freeze_chain",
    "test_p4_frozen_manifest_remains_23_and_excludes_new_figure",
    "test_p5_test_module_does_not_import_generator_for_expected_values",
    "test_p6_production_ignores_unknown_build_fields_as_data",
    "test_p7_production_load_campaign_pins_admission_calls_and_receipts",
    "test_p8_production_caption_matches_independent_parent_text",
    "test_p9_production_provenance_keeps_historical_marker_for_every_campaign",
    "test_n1_rejects_relative_median_value_drift",
    "test_n2_rejects_real_effect_sign_flip",
    "test_n3_production_strict_floor_rejects_exact_boundary",
    "test_n4_production_collection_retains_unstable_eighth_sample",
    "test_n5_output_validator_rejects_byte_change",
    "test_n6_rejects_claim_and_family_p_drift",
    "test_n7_rejects_24th_frozen_manifest_entry",
    "test_n8_rejects_slash_colon_mixture_and_multiple_separators",
    "test_n9_rejects_any_failed_hard_gate",
    "test_n10_production_stops_judgment_gate_disagreement_and_marker_uses_report",
    "test_n11_spy_pins_artist_values_and_bbox_before_save",
    "test_n12_collects_all_artist_and_legend_text",
    "test_n13_bbox_checker_rejects_overlapping_non_tick_text",
    "test_n14_bbox_checker_pins_ticks_marker_reference_clearance_and_agg",
    "test_n15_self_run_harness_rejects_invalid_test_sets_before_execution",
    "test_n16_bbox_checker_rejects_legacy_bottom_legend_overlap",
    "test_n17_bbox_checker_rejects_missing_bottom_legend",
    "test_n18_bbox_checker_rejects_bottom_legend_excluded_from_tight_bbox",
})


class ProvenanceError(AssertionError):
    """図 provenance と独立な bytes/意味期待値が一致しない。"""


def _reject(message: str) -> None:
    raise ProvenanceError(message)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _strict_json(path: Path) -> dict:
    def reject_constant(value: str) -> None:
        raise ValueError(value)

    def no_duplicates(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError(f"duplicate key {key}")
            out[key] = value
        return out

    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), parse_constant=reject_constant,
            object_pairs_hook=no_duplicates,
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        _reject(f"strict JSON read failed: {path}: {exc}")
    if type(value) is not dict:
        _reject(f"JSON top-level is not object: {path}")
    return value


def _resolve(relative: object) -> Path:
    if type(relative) is not str or not relative or Path(relative).is_absolute():
        _reject(f"path must be repo-relative: {relative!r}")
    resolved = (ROOT / relative).resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError:
        _reject(f"path leaves repo: {relative}")
    return resolved


def _number(value: object, label: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _reject(f"{label} is not numeric")
    clean = float(value)
    if not math.isfinite(clean) or (positive and clean <= 0):
        _reject(f"{label} is not finite positive")
    return clean


def _close(left: object, right: object, label: str, tolerance: float = 1e-12) -> None:
    if not math.isclose(_number(left, label), _number(right, label),
                        rel_tol=0.0, abs_tol=tolerance):
        _reject(f"{label} mismatch: {left!r} != {right!r}")


def _normalize_wal_cell(value: object) -> str:
    if type(value) is not str or value.count("/") != 1 or ":" in value:
        _reject(f"invalid WAL cell separator: {value!r}")
    workload, configuration = value.split("/", 1)
    if workload not in WORKLOADS or configuration not in CONFIGURATIONS:
        _reject(f"unknown WAL cell: {value!r}")
    return f"{workload}:{configuration}"


def _event(record: object, name: str) -> bool:
    return (
        getattr(record, "stage", None) == "s1-session"
        and isinstance(getattr(record, "payload", None), Mapping)
        and record.payload.get("event") == name
    )


def _segments(records: Sequence[object]) -> list[list[object]]:
    segments = []
    current = None
    for record in records:
        if _event(record, "session-start"):
            if current is not None:
                segments.append(current)
            current = [record]
        elif current is not None:
            current.append(record)
    if current is not None:
        segments.append(current)
    return segments


def _one(segment: Sequence[object], predicate, label: str) -> object:
    found = [record for record in segment if predicate(record)]
    if len(found) != 1:
        _reject(f"{label} count differs: {len(found)}")
    return found[0]


def _safe_conditions(command: object, workload: str) -> dict:
    """run_cmd は実行せず whitelist argument だけを独立に分割する。"""
    if type(command) is not str:
        _reject("run_cmd is not string")
    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        raise ProvenanceError("run_cmd split failed") from exc
    events = "LLC-load-misses,LLC-loads,instructions,cycles"
    if (len(tokens) < 8 or Path(tokens[0]).name != "numactl"
            or tokens[1] != "--interleave=all" or Path(tokens[2]).name != "perf"
            or tokens[3:7] != ["stat", "-e", events, "--"]):
        _reject("run_cmd prefix differs")
    converters = {
        "thread_num": int, "ycsb_tuple_num": int, "extime": int,
        "clocks_per_us": int, "ycsb_zipf_skew": float, "ycsb_rratio": int,
        "ycsb_rmw": int,
    }
    observed = {}
    for token in tokens[8:]:
        if not token.startswith("-") or "=" not in token:
            continue
        key, raw = token[1:].split("=", 1)
        if key not in converters:  # unknown string fields remain ignored data
            continue
        if key in observed:
            _reject(f"duplicated condition: {key}")
        observed[key] = converters[key](raw)
    expected = {
        "thread_num": 48, "ycsb_tuple_num": 1_000_000, "extime": 3,
        "clocks_per_us": 1800, "ycsb_zipf_skew": 0.9,
        "ycsb_rratio": READ_RATIOS[workload], "ycsb_rmw": 0,
    }
    if observed != expected:
        _reject(f"measurement conditions differ: {observed}")
    return observed


def _independent_projection(role: str, records: Sequence[object]) -> tuple[list[dict], dict[int, dict]]:
    evidence = []
    benches = {}
    for segment in _segments(records):
        start_record = segment[0]
        start = start_record.payload
        if not isinstance(start, Mapping) or start.get("campaign_role") != role:
            _reject(f"session role differs: {role}")
        index = start.get("schedule_index")
        variant = start.get("variant")
        if isinstance(index, bool) or not isinstance(index, int) or type(variant) is not str:
            _reject("session identity invalid")
        cell = _normalize_wal_cell(start.get("cell_id"))
        result = _one(segment, lambda record: _event(record, "session-result"),
                      "session-result")
        if (result.payload.get("status") != "success"
                or result.payload.get("reason") != "certified"
                or result.payload.get("variant") != variant
                or result.payload.get("schedule_index") != index
                or _normalize_wal_cell(result.payload.get("cell_id")) != cell):
            _reject("session result differs")
        build = _one(segment, lambda record: record.stage == "build_start"
                     and record.variant == variant, "build_start")
        commit = _one(segment, lambda record: record.stage == "commit"
                      and record.variant == variant, "commit")
        if not isinstance(build.payload, Mapping) or not isinstance(commit.payload, Mapping):
            _reject("admission Mapping payload contract differs")
        verify = commit.payload.get("verify_configs")
        unstable = commit.payload.get("unstable", False)
        if not isinstance(verify, (tuple, list)) or type(unstable) is not bool:
            _reject("commit projection shape differs")
        fitness = commit.payload.get("fitness_tps")
        if role == "develop":
            if fitness is not None:
                _reject("develop fitness is present")
            clean_fitness = None
        else:
            clean_fitness = _number(fitness, "fitness", positive=True)
            bench = _one(segment, lambda record: record.stage == "bench_done"
                         and record.variant == variant, "bench_done")
            tps = bench.payload.get("tps")
            if not isinstance(tps, (tuple, list)) or len(tps) != 5:
                _reject("bench repetition count differs")
            clean_tps = [_number(value, "tps", positive=True) for value in tps]
            median = statistics.median(clean_tps)
            _close(median, bench.payload.get("median_tps"), "bench median")
            _close(median, clean_fitness, "commit median")
            workload = cell.split(":", 1)[0]
            conditions = _safe_conditions(bench.payload.get("run_cmd"), workload)
            benches[index] = {"tps": clean_tps, "conditions": conditions}
        evidence.append({
            "role": role, "schedule_index": index, "cell_id": cell,
            "variant_id": variant, "src_token": build.payload.get("src_token"),
            "fitness_tps": clean_fitness, "verify_configs": list(verify),
            "unstable": unstable,
        })
    evidence.sort(key=lambda row: row["schedule_index"])
    if len(evidence) != COUNTS[role]:
        _reject(f"projected sample count differs: {role}")
    return evidence, benches


def _real_inputs() -> tuple[dict, dict, dict[str, dict]]:
    report = _strict_json(ROOT / REPORT_REL)
    freeze = _strict_json(ROOT / FREEZE_REL)
    campaigns = {}
    accepted = report["hard_gates"]["certified"]["accepted_evidence"]
    for role, campaign_id in CAMPAIGNS.items():
        directory = ROOT / "output" / "campaigns" / campaign_id
        view = require_admitted_campaign(
            directory, purpose=CampaignReadPurpose.HISTORICAL_RAW)
        expected_wal = directory / "runs" / "wal.jsonl"
        expected_lock = directory / "campaign.lock"
        if (Path(view.wal_file).resolve() != expected_wal.resolve()
                or Path(view.lock_file).resolve() != expected_lock.resolve()
                or Path(view.layout.root).resolve().name != campaign_id):
            _reject(f"exact role/path binding differs: {role}")
        for _ in wal.iter_lines(str(expected_wal)):
            pass
        evidence, benches = _independent_projection(role, view.records)
        expected = sorted((dict(row) for row in accepted[role]),
                          key=lambda row: row["schedule_index"])
        if evidence != expected:
            _reject(f"WAL/report accepted evidence differs: {role}")
        epoch = {
            "campaign_verifier_epoch": view.campaign_verifier_epoch.campaign_verifier_epoch,
            "state": view.campaign_verifier_epoch.state,
            "reason_code": view.campaign_verifier_epoch.reason_code,
            "identity_scope": view.campaign_verifier_epoch.identity_scope,
            "excluded_scope": view.campaign_verifier_epoch.excluded_scope,
        }
        if (view.read_purpose is not CampaignReadPurpose.HISTORICAL_RAW
                or epoch != CURRENT_E0_EPOCH):
            _reject(f"HISTORICAL_RAW E0 differs: {role}")
        campaigns[role] = {
            "dir": directory, "wal": expected_wal, "lock": expected_lock,
            "evidence": evidence, "benches": benches,
            "receipt": view.decision.as_receipt(),
        }
    return report, freeze, campaigns


def _group(campaigns: Mapping[str, Mapping]) -> dict[str, dict[str, list[dict]]]:
    grouped = {role: {} for role in ROLES}
    for role in ROLES:
        for row in campaigns[role]["evidence"]:
            grouped[role].setdefault(row["cell_id"], []).append(row)
    return grouped


def _cell(grouped: Mapping, cell_id: str) -> dict:
    blocks = {}
    for role in ("block1", "block2"):
        rows = grouped[role].get(cell_id, [])
        if len(rows) != 4:
            _reject(f"cell block n differs: {role}:{cell_id}")
        blocks[role] = [_number(row["fitness_tps"], "cell tps", positive=True)
                        for row in rows]
    values = blocks["block1"] + blocks["block2"]
    mean = statistics.fmean(values)
    half = T_DF7 * statistics.stdev(values) / math.sqrt(8)
    return {
        "samples_tps": values, "block_samples_tps": blocks, "n": 8,
        "mean_tps": mean, "median_tps": statistics.median(values),
        "ci95_mean_half_tps": half,
        "ci95_mean_low_tps": mean - half,
        "ci95_mean_high_tps": mean + half,
        "unstable_count": sum(
            row["unstable"] for role in ("block1", "block2")
            for row in grouped[role][cell_id]),
    }


def _cv(values: Sequence[float]) -> float:
    if len(values) != 8:
        _reject("floor n differs")
    return statistics.stdev(values) / statistics.fmean(values)


def _sign(value: float) -> int:
    return 1 if value > 0 else (-1 if value < 0 else 0)


def _independent_expectations(report: Mapping, campaigns: Mapping[str, Mapping]) -> dict:
    grouped = _group(campaigns)
    cells = {
        f"{workload}:{configuration}": _cell(grouped, f"{workload}:{configuration}")
        for workload in WORKLOADS for configuration in PLOT_CONFIGURATIONS
    }
    report_by_id = {row["comparison_id"]: row for row in report["comparisons"]}
    comparisons = []
    for workload in WORKLOADS:
        for axis in AXES:
            comparison_id = f"S-1a:{workload}:{axis}"
            row = report_by_id[comparison_id]
            left_id = f"{workload}:system_gate"
            right_id = f"{workload}:{axis}"
            left, right = cells[left_id], cells[right_id]
            relative = (left["median_tps"] - right["median_tps"]) / right["median_tps"]
            floor_left = [_number(value["fitness_tps"], "floor left", positive=True)
                          for value in grouped["floor"][left_id]]
            floor_right = [_number(value["fitness_tps"], "floor right", positive=True)
                           for value in grouped["floor"][right_id]]
            floor_cmp = max(_cv(floor_left), _cv(floor_right), 0.03)
            gate1 = relative > floor_cmp
            pooled = _sign(left["median_tps"] - right["median_tps"])
            block_signs = [
                _sign(statistics.median(left["block_samples_tps"][role])
                      - statistics.median(right["block_samples_tps"][role]))
                for role in ("block1", "block2")
            ]
            gate2 = pooled != 0 and block_signs == [pooled, pooled]
            comparisons.append({
                "comparison_id": comparison_id, "workload": workload,
                "left_cell": left_id, "right_cell": right_id,
                "left_median_tps": left["median_tps"],
                "right_median_tps": right["median_tps"],
                "relative_median_difference": relative,
                "relative_median_difference_percent": relative * 100,
                "floor_cmp": floor_cmp,
                "gate1_recomputed_for_consistency": gate1,
                "gate2_recomputed_for_consistency": gate2,
                "judgment": row["judgment"], "p_perm": row["p_perm"],
                "p_star": row["p_star"],
            })
    context = {}
    for workload in WORKLOADS:
        stock = _cell(grouped, f"{workload}:stock_common")
        sort = cells[f"{workload}:sort_best"]
        system = cells[f"{workload}:system_gate"]
        context[workload] = {
            "median_tps": stock["median_tps"],
            "sort_best_relative_to_stock": (
                sort["median_tps"] - stock["median_tps"]) / stock["median_tps"],
            "system_gate_relative_to_stock": (
                system["median_tps"] - stock["median_tps"]) / stock["median_tps"],
        }
    return {"cells": cells, "comparisons": comparisons, "context": context}


def _validate_comparison(observed: Mapping, expected: Mapping) -> None:
    for key in (
        "left_median_tps", "right_median_tps", "relative_median_difference",
        "relative_median_difference_percent", "floor_cmp",
    ):
        _close(observed.get(key), expected[key], f"comparison {key}")
    for key in (
        "comparison_id", "workload", "left_cell", "right_cell",
        "gate1_recomputed_for_consistency", "gate2_recomputed_for_consistency",
        "judgment", "p_perm", "p_star",
    ):
        if observed.get(key) != expected[key]:
            _reject(f"comparison {key} mismatch")


def _validate_cell(observed: Mapping, expected: Mapping) -> None:
    if observed.get("n") != 8 or len(observed.get("samples_tps", ())) != 8:
        _reject("cell n mismatch")
    if observed.get("samples_tps") != expected["samples_tps"]:
        _reject("cell accepted samples mismatch")
    for key in (
        "mean_tps", "median_tps", "ci95_mean_half_tps",
        "ci95_mean_low_tps", "ci95_mean_high_tps",
    ):
        _close(observed.get(key), expected[key], f"cell {key}", 1e-9)
    if observed.get("unstable_count") != expected["unstable_count"]:
        _reject("cell unstable count mismatch")


def _validate_claim(claim: Mapping, report: Mapping, expected: Mapping) -> None:
    family = report["families"]["s1a"]
    passed = sum(row["judgment"] == "成立" for row in expected["comparisons"])
    expected_claim = {
        "claim_id": "S-1a", "judgment": family["judgment"],
        "p_family": family["p_family"], "pair_count": 9,
        "passed_pair_count": passed, "failed_pair_count": 9 - passed,
        "conjunction_required": True,
    }
    if dict(claim) != expected_claim:
        _reject("claim mismatch")


def _caption_percent(value: object) -> str:
    return f"{_number(value, 'caption percent'):+.1f}".replace("-", "−")


def _expected_caption(report: Mapping, expected: Mapping) -> str:
    """親確定正文を generator と独立に、WAL 再計算値と frozen golden で構成する。"""
    family = report["families"]["s1a"]
    if family.get("judgment") != "不成立" or family.get("p_family") != 1.0:
        _reject("frozen S-1a caption golden differs")
    by_axis = {
        axis: [
            row["relative_median_difference_percent"]
            for row in expected["comparisons"]
            if row["right_cell"].endswith(f":{axis}")
        ]
        for axis in AXES
    }
    passed = sum(row["judgment"] == "成立" for row in expected["comparisons"])
    failed = sum(row["judgment"] == "不成立" for row in expected["comparisons"])
    if (passed, failed) != (3, 6):
        _reject("frozen caption pair-count golden differs")
    if sum(cell["unstable_count"] for cell in expected["cells"].values()) != 0:
        _reject("frozen caption unstable golden differs")
    flags = by_axis["p2_2_flag_opt"]
    backoff = by_axis["backoff_fixed_best"]
    ordering = by_axis["sort_best"]
    return (
        "図4. 縮小主張 S' の性能次元 (S-1a) — 既知軸最良に対する直接比較 9 対 (失敗報告)。"
        "上段は、abort 要因別に backoff の発火可否を切り替える合成軸 (trigger gating) と、既知軸の"
        "最良 3 種 — コンパイル時フラグ最適化、静的 backoff の最良値、書込ロック順の並べ替え — との"
        "相対中央値差である。各点は 100 × (合成軸側の中央値 − 相手側の中央値) / 相手側の中央値 で、"
        "各セル 8 標本から再計算した。灰色の実線は差 0、赤の破線は厳密に超える必要がある判定境界"
        " +3% (between-run floor = 走行間の再現ばらつきの下限) で、薄赤の領域は境界を超えない範囲である。"
        "S-1a の成立条件は 9 対すべてが境界を超えることである。コンパイル時フラグ最適化との 3 対は"
        f" {_caption_percent(flags[0])}%〜{_caption_percent(flags[-1])}%、静的 backoff 最良値との 3 対は"
        f" {_caption_percent(backoff[0])}%〜{_caption_percent(backoff[-1])}% で境界を超えず、書込ロック順"
        f"並べ替えとの 3 対だけが {_caption_percent(ordering[0])}%〜{_caption_percent(ordering[-1])}% で超えた。"
        f"9 対中 {failed} 対が満たされず、{passed} 対が満たしたため、"
        f"S-1a は不成立である (family p = {family['p_family']:.1f})。"
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


def _validate_caption(caption: object, report: Mapping, expected: Mapping) -> None:
    if type(caption) is not str:
        _reject("caption is not text")
    wanted = _expected_caption(report, expected)
    if caption != wanted:
        _reject("caption正文 differs from independently constructed parent text")


def _manifest_literal() -> dict:
    tree = ast.parse((ROOT / FROZEN_TEST_REL).read_text(encoding="utf-8"))
    for node in tree.body:
        if (isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "FROZEN_MANIFEST"
                        for target in node.targets)):
            value = ast.literal_eval(node.value)
            if type(value) is dict:
                return value
    _reject("FROZEN_MANIFEST literal not found")


def _validate_manifest(manifest: Mapping) -> None:
    if len(manifest) != 23:
        _reject("FROZEN_MANIFEST count is not 23")
    if any("fig4_s1a_9pair_direct_comparison" in key for key in manifest):
        _reject("new figure entered FROZEN_MANIFEST")


def _validate_frozen_report_gates(report: Mapping) -> None:
    hard = report.get("hard_gates")
    if not isinstance(hard, Mapping) or set(hard) != {
        "freeze", "schedule", "certified", "sample_counts", "budget",
    }:
        _reject("five hard gate exact set differs")
    for name in ("freeze", "sample_counts", "budget"):
        gate = hard[name]
        if gate.get("status") != "pass" or gate.get("reasons") != []:
            _reject(f"hard gate is not clean pass: {name}")
    schedule = hard["schedule"]
    if not isinstance(schedule, Mapping) or set(schedule) != set(ROLES):
        _reject("schedule role exact set differs")
    for role in ROLES:
        if (schedule[role].get("status") != "pass"
                or schedule[role].get("reasons") != []):
            _reject(f"schedule hard gate is not clean pass: {role}")
    certified = hard["certified"]
    if certified.get("status") != "pass" or certified.get("issues") != []:
        _reject("certified hard gate is not clean pass")
    comparisons = report.get("comparisons")
    if (not isinstance(comparisons, list) or len(comparisons) != 12
            or any(row.get("reasons") != [] for row in comparisons)):
        _reject("comparison exact count/reasons differ")
    if set(report.get("families", {})) != {"s1a", "s1b"}:
        _reject("family exact set differs")


def _validate_output_digest(path: Path, recorded_sha256: object, label: str) -> None:
    """着地成果物 validator と負例が共有する bytes 境界。"""
    if not path.is_file() or recorded_sha256 != _sha256(path):
        _reject(f"output SHA256 mismatch: {label}")


def _frozen_admission_receipt(current: Mapping) -> dict:
    """Pin the generation-time validator while checking the live one separately."""
    live_validator = {
        "identity": ADMISSION_VALIDATOR_IDENTITY,
        "sha256": _sha256(ROOT / ADMISSION_VALIDATOR_REL),
    }
    if current.get("validator") != live_validator:
        _reject("live admission validator bytes differ")
    return {
        **current,
        "validator": {
            "identity": ADMISSION_VALIDATOR_IDENTITY,
            "sha256": FROZEN_ADMISSION_VALIDATOR_SHA256,
        },
    }


def validate_real_provenance(provenance: Mapping) -> None:
    if set(provenance) != EXPECTED_TOP_KEYS or provenance.get("schema") != SCHEMA:
        _reject("provenance top-level/schema differs")
    if provenance.get("generator") != GENERATOR_REL.name:
        _reject("generator name differs")
    source = provenance.get("generator_source")
    if (not isinstance(source, Mapping) or source.get("path") != GENERATOR_REL.as_posix()
            or source.get("sha256") != FIG4_GENERATION_TIME_GENERATOR_SHA256):
        _reject("generator source bytes differ")
    outputs = provenance.get("outputs")
    expected_output_paths = [
        f"{OUT_PREFIX_REL}.png",
        f"{OUT_PREFIX_REL}.pdf",
    ]
    if not isinstance(outputs, list) or [row.get("path") for row in outputs] != expected_output_paths:
        _reject("output exact path/order differs")
    for row in outputs:
        path = _resolve(row.get("path"))
        _validate_output_digest(path, row.get("sha256"), str(row.get("path")))

    report, freeze, campaigns = _real_inputs()
    frozen_manifest = _manifest_literal()
    current_freeze_sha = frozen_manifest.get(FREEZE_REL.as_posix())
    if _sha256(ROOT / FREEZE_REL) != current_freeze_sha:
        _reject("current freeze hash drift")
    _validate_frozen_report_gates(report)

    inputs = provenance.get("inputs")
    if not isinstance(inputs, list) or len(inputs) != 6:
        _reject("input count differs")
    report_input, freeze_input, *campaign_inputs = inputs
    if report_input != {
        "kind": "report", "path": REPORT_REL.as_posix(),
        "sha256": _sha256(ROOT / REPORT_REL),
        "generated_at_head": report["generated_at_head"],
    }:
        _reject("report input differs")
    if freeze_input != {
        "kind": "current_measurement_freeze", "path": FREEZE_REL.as_posix(),
        "sha256": current_freeze_sha,
    }:
        _reject("freeze input differs")
    by_role = {row.get("role"): row for row in campaign_inputs}
    if set(by_role) != set(ROLES):
        _reject("campaign input roles differ")
    campaign_keys = {
        "kind", "role", "campaign", "dir", "wal", "wal_sha256", "lock",
        "lock_sha256", "read_purpose", "campaign_verifier_epoch",
        "admission_decision",
    }
    for role in ROLES:
        row = by_role[role]
        campaign = campaigns[role]
        directory_rel = campaign["dir"].relative_to(ROOT).as_posix()
        if set(row) != campaign_keys or row.get("kind") != "campaign":
            _reject(f"campaign input exact shape differs: {role}")
        expected = {
            "role": role, "campaign": CAMPAIGNS[role], "dir": directory_rel,
            "wal": campaign["wal"].relative_to(ROOT).as_posix(),
            "wal_sha256": _sha256(campaign["wal"]),
            "lock": campaign["lock"].relative_to(ROOT).as_posix(),
            "lock_sha256": _sha256(campaign["lock"]),
            "read_purpose": "HISTORICAL_RAW",
            # The landed provenance is a frozen generation-time receipt.  Keep
            # its historical scope exact while independently checking the live
            # admitted view against CURRENT_E0_EPOCH above.
            "campaign_verifier_epoch": FROZEN_E0_EPOCH,
            "admission_decision": _frozen_admission_receipt(campaign["receipt"]),
        }
        for key, value in expected.items():
            if row.get(key) != value:
                _reject(f"campaign input {key} differs: {role}")

    expected = _independent_expectations(report, campaigns)
    facts = provenance.get("facts")
    if not isinstance(facts, Mapping):
        _reject("facts missing")
    _validate_claim(facts.get("claim", {}), report, expected)
    observed_cells = facts.get("cells")
    if not isinstance(observed_cells, Mapping) or set(observed_cells) != set(expected["cells"]):
        _reject("plotted cell exact set differs")
    for cell_id, cell in expected["cells"].items():
        _validate_cell(observed_cells[cell_id], cell)
    observed_comparisons = facts.get("comparisons")
    if not isinstance(observed_comparisons, list) or len(observed_comparisons) != 9:
        _reject("plotted comparison count differs")
    for observed, wanted in zip(observed_comparisons, expected["comparisons"]):
        _validate_comparison(observed, wanted)
    context = facts.get("context_cells")
    if not isinstance(context, Mapping) or set(context) != set(WORKLOADS):
        _reject("context cell workload set differs")
    for workload in WORKLOADS:
        row = context[workload]
        if row.get("registered_comparison") is not False:
            _reject("context cell became registered comparison")
        for key, value in expected["context"][workload].items():
            _close(row.get(key), value, f"context {workload}.{key}")
        freeze_note = freeze["cells"][f"{workload}:sort_best"]["variant"].get("note")
        if row.get("sort_selection_history") != freeze_note:
            _reject(f"context sort selection history differs: {workload}")
    proof = facts.get("freeze_proof")
    if (not isinstance(proof, Mapping)
            or proof.get("report_freeze_ref", {}).get("sha256") != REPORT_FREEZE_SHA
            or proof.get("current_freeze_sha256") != current_freeze_sha
            or proof.get("freeze_ref_matches_current") is not False
            or proof.get("changed_json_pointers") != [
                "/frozen_at_head",
                "/implementation_hashes/known_axes_freeze/sha256",
                "/cells/read-heavy:sort_best/variant/sources[0]/sha256",
            ]):
        _reject("freeze proof chain differs")
    contract = facts.get("plot_contract")
    if (contract.get("xlim_percent") != [-105.0, 105.0]
            or contract.get("strict_floor_line_percent") != 3.0
            or contract.get("workload_order") != list(WORKLOADS)
            or contract.get("axis_order") != list(AXES)
            or contract.get("stock_common_drawn") is not False):
        _reject("plot contract differs")
    _validate_caption(provenance.get("caption"), report, expected)
    readme = (ROOT / README_REL).read_text(encoding="utf-8")
    if provenance["caption"] not in readme:
        _reject("caption正文 is absent from figures README")
    _validate_manifest(_manifest_literal())


def _expect_rejected(callback, reason: str) -> None:
    try:
        callback()
    except ProvenanceError as exc:
        if reason not in str(exc):
            raise AssertionError(f"wrong rejection reason: {exc}") from exc
        return
    raise AssertionError("negative control was accepted")


def _positive_pair() -> tuple[dict, dict]:
    target = [120, 121, 119, 120, 122, 121, 123, 122]
    control = [100, 101, 99, 100, 102, 101, 103, 102]
    relative = (statistics.median(target) - statistics.median(control)) / statistics.median(control)
    expected = {
        "comparison_id": "fixture", "workload": "balanced",
        "left_cell": "balanced:system_gate", "right_cell": "balanced:p2_2_flag_opt",
        "left_median_tps": statistics.median(target),
        "right_median_tps": statistics.median(control),
        "relative_median_difference": relative,
        "relative_median_difference_percent": relative * 100,
        "floor_cmp": 0.03, "gate1_recomputed_for_consistency": True,
        "gate2_recomputed_for_consistency": True, "judgment": "成立",
        "p_perm": 0.00020408163265306123, "p_star": 0.00020408163265306123,
    }
    return dict(expected), expected


def test_p1_independent_real_wal_projection_matches_frozen_report():
    """実 WAL/report 境界を検査する。固定 Cartesian 件数は変異証拠に数えない。"""
    report, _freeze, campaigns = _real_inputs()
    _validate_frozen_report_gates(report)
    expected = _independent_expectations(report, campaigns)
    if sum(row["judgment"] == "成立" for row in expected["comparisons"]) != 3:
        raise AssertionError("independent pass count differs")
    if sum(row["judgment"] == "不成立" for row in expected["comparisons"]) != 6:
        raise AssertionError("independent fail count differs")
    if any(cell["unstable_count"] for cell in expected["cells"].values()):
        raise AssertionError("independent unstable count differs")


def test_p2_certified_acceptance_rejects_historical_e0_campaign():
    directory = ROOT / "output" / "campaigns" / CAMPAIGNS["block1"]
    try:
        require_admitted_campaign(
            directory, purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE)
    except CampaignVerifierEpochRejected as exc:
        if exc.epoch_state != "E0" or exc.reason_code != "v1-authority-absent":
            raise AssertionError("wrong E0 rejection diagnostic") from exc
        return
    raise AssertionError("CERTIFIED_ACCEPTANCE accepted E0 campaign")


def test_p3_real_provenance_closes_bytes_admission_caption_and_freeze_chain():
    if not (ROOT / PROVENANCE_REL).is_file():
        raise AssertionError(
            "new provenance is absent (parent figure generation/docs landing pending)")
    provenance = _strict_json(ROOT / PROVENANCE_REL)
    validate_real_provenance(provenance)
    mutated = json.loads(json.dumps(provenance))
    digest = mutated["generator_source"]["sha256"]
    mutated["generator_source"]["sha256"] = (
        ("0" if digest[0] != "0" else "1") + digest[1:]
    )
    _expect_rejected(
        lambda: validate_real_provenance(mutated),
        "generator source bytes differ",
    )


def test_p4_frozen_manifest_remains_23_and_excludes_new_figure():
    _validate_manifest(_manifest_literal())


def test_p5_test_module_does_not_import_generator_for_expected_values():
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    forbidden = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name for alias in node.names]
            if any("plot_s1_9pair" in name for name in names):
                forbidden.append((node.lineno, names))
    if forbidden:
        raise AssertionError(f"generator was imported by expected-value code: {forbidden}")
    callers = set()
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if any(
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Name)
            and child.func.id == "_load_generator_for_production_tests"
            for child in ast.walk(node)
        ):
            callers.add(node.name)
    expected_callers = {
        "test_p6_production_ignores_unknown_build_fields_as_data",
        "test_p7_production_load_campaign_pins_admission_calls_and_receipts",
        "test_p8_production_caption_matches_independent_parent_text",
        "test_p9_production_provenance_keeps_historical_marker_for_every_campaign",
        "test_n3_production_strict_floor_rejects_exact_boundary",
        "test_n4_production_collection_retains_unstable_eighth_sample",
        "test_n10_production_stops_judgment_gate_disagreement_and_marker_uses_report",
        "test_n11_spy_pins_artist_values_and_bbox_before_save",
        "test_n12_collects_all_artist_and_legend_text",
        "test_n13_bbox_checker_rejects_overlapping_non_tick_text",
        "test_n14_bbox_checker_pins_ticks_marker_reference_clearance_and_agg",
        "test_n16_bbox_checker_rejects_legacy_bottom_legend_overlap",
        "test_n17_bbox_checker_rejects_missing_bottom_legend",
        "test_n18_bbox_checker_rejects_bottom_legend_excluded_from_tight_bbox",
    }
    if callers != expected_callers:
        raise AssertionError(f"generator drawing-spy call scope differs: {callers}")
    generator_tree = ast.parse((ROOT / GENERATOR_REL).read_text(encoding="utf-8"))
    dangerous = []
    for node in ast.walk(generator_tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if any(alias.name == "subprocess" for alias in node.names):
                dangerous.append((node.lineno, "subprocess"))
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in {"eval", "exec"}):
            dangerous.append((node.lineno, node.func.id))
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "os" and node.func.attr in {"system", "popen"}):
            dangerous.append((node.lineno, f"os.{node.func.attr}"))
    if dangerous:
        raise AssertionError(f"generator contains command execution surface: {dangerous}")


def test_p6_production_ignores_unknown_build_fields_as_data():
    generator = _load_generator_for_production_tests()
    generator._trace_disabled({
        "perf_configure_cmd": "cmake -DCCBENCH_TRACE=0 -DCMAKE_BUILD_TYPE=Release ..",
        "unknown_false_trace": "-DCCBENCH_TRACE=1",
        "unknown_malformed_quote": "' this is unbalanced and must remain data",
    })
    command = (
        "numactl --interleave=all perf stat -e "
        "LLC-load-misses,LLC-loads,instructions,cycles -- /tmp/never-executed "
        "-thread_num=48 -ycsb_tuple_num=1000000 -extime=3 "
        "-clocks_per_us=1800 -ycsb_zipf_skew=0.9 -ycsb_rratio=5 "
        "-ycsb_rmw=0 -prompt=ignore-this-unknown-string"
    )
    observed = generator._parse_run_command(command, "write-heavy")
    if set(observed) != {
        "thread_num", "ycsb_tuple_num", "extime", "clocks_per_us",
        "ycsb_zipf_skew", "ycsb_rratio", "ycsb_rmw", "numactl_args",
        "perf_events",
    }:
        raise AssertionError(f"unknown command field entered projection: {observed}")


def test_p7_production_load_campaign_pins_admission_calls_and_receipts():
    generator = _load_generator_for_production_tests()
    original = generator.require_admitted_campaign
    calls = []
    returned_receipts = {}

    class ExactReceiptDecision:
        def __init__(self, receipt):
            self.receipt = receipt

        def as_receipt(self):
            return self.receipt

    def spy(directory, *, purpose):
        view = original(directory, purpose=purpose)
        role = next(
            key for key, campaign_id in CAMPAIGNS.items()
            if Path(directory).resolve().name == campaign_id
        )
        receipt = view.decision.as_receipt()
        returned_receipts[role] = receipt
        calls.append((role, Path(directory).resolve(), purpose))
        return SimpleNamespace(
            wal_file=view.wal_file,
            lock_file=view.lock_file,
            layout=view.layout,
            records=view.records,
            campaign_verifier_epoch=view.campaign_verifier_epoch,
            read_purpose=view.read_purpose,
            verifier_assessment_basis=view.verifier_assessment_basis,
            decision=ExactReceiptDecision(receipt),
        )

    generator.require_admitted_campaign = spy
    try:
        loaded = {
            role: generator.load_campaign(
                role, ROOT / "output" / "campaigns" / CAMPAIGNS[role]
            )
            for role in ROLES
        }
    finally:
        generator.require_admitted_campaign = original

    if [role for role, _directory, _purpose in calls] != list(ROLES):
        raise AssertionError(f"production admission call order/count differs: {calls}")
    for role, directory, purpose in calls:
        expected_dir = (ROOT / "output" / "campaigns" / CAMPAIGNS[role]).resolve()
        if directory != expected_dir:
            raise AssertionError(f"production admission directory differs: {role}")
        if purpose is not CampaignReadPurpose.HISTORICAL_RAW:
            raise AssertionError(f"production admission purpose differs: {role}")
        if loaded[role]["admission_decision"] is not returned_receipts[role]:
            raise AssertionError(f"production receipt lost admission return identity: {role}")
        if loaded[role]["campaign_verifier_epoch"].get(
                "verifier_assessment_basis"
        ) != "recorded-at-original-verifier-epoch":
            raise AssertionError(
                f"historical verifier assessment marker missing: {role}"
            )


def test_p8_production_caption_matches_independent_parent_text():
    generator = _load_generator_for_production_tests()
    report, _freeze, campaigns = _real_inputs()
    expected = _independent_expectations(report, campaigns)
    passed = sum(row["judgment"] == "成立" for row in expected["comparisons"])
    claim = {
        "claim_id": "S-1a",
        "judgment": report["families"]["s1a"]["judgment"],
        "p_family": report["families"]["s1a"]["p_family"],
        "pair_count": len(expected["comparisons"]),
        "passed_pair_count": passed,
        "failed_pair_count": len(expected["comparisons"]) - passed,
        "conjunction_required": True,
    }
    unstable = sum(cell["unstable_count"] for cell in expected["cells"].values())
    observed = generator._caption(expected["comparisons"], claim, unstable)
    wanted = _expected_caption(report, expected)
    if observed != wanted:
        raise AssertionError("production caption differs from independent parent text")


def test_p9_production_provenance_keeps_historical_marker_for_every_campaign():
    generator = _load_generator_for_production_tests()
    campaigns = {
        role: generator.load_campaign(
            role, ROOT / "output" / "campaigns" / CAMPAIGNS[role]
        )
        for role in ROLES
    }
    report = _strict_json(ROOT / REPORT_REL)
    data = {
        "report_path": REPORT_REL.as_posix(),
        "report_sha256": _sha256(ROOT / REPORT_REL),
        "report": report,
        "campaigns": campaigns,
        "facts": {
            "freeze_proof": {
                "current_freeze_sha256": _sha256(ROOT / FREEZE_REL),
            },
        },
        "caption": "fixture caption",
    }
    with tempfile.TemporaryDirectory(
        prefix=".s1-current-provenance-", dir=ROOT,
    ) as temp:
        prefix = Path(temp) / "figure"
        Path(f"{prefix}.png").write_bytes(b"fixture-png")
        Path(f"{prefix}.pdf").write_bytes(b"fixture-pdf")
        provenance = generator.build_provenance(
            data, prefix, ["python3", GENERATOR_REL.as_posix()],
        )

    if provenance["generator_source"] != {
        "path": GENERATOR_REL.as_posix(),
        "sha256": _sha256(ROOT / GENERATOR_REL),
    }:
        raise AssertionError("new provenance did not record current generator SHA")
    campaign_inputs = [
        row for row in provenance["inputs"] if row.get("kind") == "campaign"
    ]
    if [row.get("role") for row in campaign_inputs] != list(ROLES):
        raise AssertionError("final provenance campaign order/set differs")
    for row in campaign_inputs:
        if row["campaign_verifier_epoch"].get(
            "verifier_assessment_basis"
        ) != "recorded-at-original-verifier-epoch":
            raise AssertionError(
                f"final provenance historical marker missing: {row.get('role')}"
            )


def test_n1_rejects_relative_median_value_drift():
    observed, expected = _positive_pair()
    observed["relative_median_difference"] = 0.21
    _expect_rejected(lambda: _validate_comparison(observed, expected),
                     "relative_median_difference mismatch")


def test_n2_rejects_real_effect_sign_flip():
    observed, expected = _positive_pair()
    observed["relative_median_difference_percent"] *= -1
    _expect_rejected(lambda: _validate_comparison(observed, expected),
                     "relative_median_difference_percent mismatch")


def test_n3_production_strict_floor_rejects_exact_boundary():
    generator = _load_generator_for_production_tests()
    if generator._strict_gate1(0.03, 0.03) is not False:
        raise AssertionError("production strict gate accepted exact floor boundary")
    if generator._strict_gate1(math.nextafter(0.03, math.inf), 0.03) is not True:
        raise AssertionError("production strict gate rejected value above floor boundary")


def test_n4_production_collection_retains_unstable_eighth_sample():
    generator = _load_generator_for_production_tests()
    cell_id = "balanced:system_gate"
    campaigns = {role: {"evidence": []} for role in ROLES}
    rows = [
        {
            "cell_id": cell_id,
            "fitness_tps": float(index + 1),
            "unstable": index == 7,
            "schedule_index": index,
        }
        for index in range(8)
    ]
    campaigns["block1"]["evidence"] = rows[:4]
    campaigns["block2"]["evidence"] = rows[4:]
    grouped = generator._group_samples(campaigns)
    retained = grouped["block1"][cell_id] + grouped["block2"][cell_id]
    if len(retained) != 8 or retained[-1]["unstable"] is not True:
        raise AssertionError(f"production sample collector filtered accepted row: {retained}")
    cell = generator._cell_stats(grouped, cell_id)
    if cell["n"] != 8 or cell["unstable_count"] != 1:
        raise AssertionError(f"production cell stats lost unstable sample: {cell}")


def test_n5_output_validator_rejects_byte_change():
    with tempfile.TemporaryDirectory(prefix="s1-prov-byte-") as temp:
        path = Path(temp) / "figure.png"
        path.write_bytes(b"png")
        recorded = _sha256(path)
        path.write_bytes(b"png!")
        _expect_rejected(lambda: _validate_output_digest(path, recorded, "fixture"),
                         "output SHA256 mismatch")


def test_n6_rejects_claim_and_family_p_drift():
    report = {"families": {"s1a": {"judgment": "不成立", "p_family": 1.0}}}
    expected = {"comparisons": [
        {"judgment": "成立"} for _ in range(3)
    ] + [{"judgment": "不成立"} for _ in range(6)]}
    claim = {
        "claim_id": "S-1a", "judgment": "成立", "p_family": 0.0002040816,
        "pair_count": 9, "passed_pair_count": 3, "failed_pair_count": 6,
        "conjunction_required": True,
    }
    _expect_rejected(lambda: _validate_claim(claim, report, expected), "claim mismatch")


def test_n7_rejects_24th_frozen_manifest_entry():
    manifest = {f"output/frozen-{index}": "0" * 64 for index in range(23)}
    manifest[str(PROVENANCE_REL)] = "1" * 64
    _expect_rejected(lambda: _validate_manifest(manifest),
                     "FROZEN_MANIFEST count is not 23")


def test_n8_rejects_slash_colon_mixture_and_multiple_separators():
    for value in (
        "write-heavy/system_gate/extra", "write-heavy/system_gate:extra",
        "write-heavy:system_gate", "write-heavy//system_gate",
    ):
        _expect_rejected(lambda value=value: _normalize_wal_cell(value),
                         "invalid WAL cell separator")


def test_n9_rejects_any_failed_hard_gate():
    report = _strict_json(ROOT / REPORT_REL)
    _validate_frozen_report_gates(report)
    for name in ("freeze", "certified", "sample_counts", "budget"):
        mutated = json.loads(json.dumps(report))
        mutated["hard_gates"][name]["status"] = "fail"
        _expect_rejected(lambda mutated=mutated: _validate_frozen_report_gates(mutated),
                         "hard gate is not clean pass")
    mutated = json.loads(json.dumps(report))
    mutated["hard_gates"]["schedule"]["block1"]["status"] = "fail"
    _expect_rejected(lambda: _validate_frozen_report_gates(mutated),
                     "schedule hard gate is not clean pass")


def _load_generator_for_production_tests():
    """Production control 専用 loader。loader 可用性自体は変異の証拠に数えない。"""
    spec = importlib.util.spec_from_file_location(
        "_s1_9pair_generator_production_test", ROOT / GENERATOR_REL)
    if spec is None or spec.loader is None:
        raise AssertionError("auxiliary production-test loader is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _SpyText:
    def __init__(self, text):
        self.text = text
        self.gid = None

    def set_gid(self, value):
        self.gid = value


class _SpyAxis:
    def __init__(self):
        self.calls = []
        self.texts = []

    def _record(self, name, *args, **kwargs):
        self.calls.append((name, args, kwargs))
        return None

    def axvline(self, *args, **kwargs): return self._record("axvline", *args, **kwargs)
    def axvspan(self, *args, **kwargs): return self._record("axvspan", *args, **kwargs)
    def scatter(self, *args, **kwargs): return self._record("scatter", *args, **kwargs)
    def errorbar(self, *args, **kwargs): return self._record("errorbar", *args, **kwargs)
    def hlines(self, *args, **kwargs): return self._record("hlines", *args, **kwargs)
    def text(self, *args, **kwargs):
        value = _SpyText(args[2])
        self.texts.append(value)
        self._record("text", *args, **kwargs)
        return value
    def annotate(self, *args, **kwargs):
        value = _SpyText(args[0])
        self.texts.append(value)
        self._record("annotate", *args, **kwargs)
        return value
    def set_yticks(self, *args, **kwargs): return self._record("set_yticks", *args, **kwargs)
    def set_xticks(self, *args, **kwargs): return self._record("set_xticks", *args, **kwargs)
    def set_xlabel(self, *args, **kwargs): return self._record("set_xlabel", *args, **kwargs)
    def set_ylabel(self, *args, **kwargs): return self._record("set_ylabel", *args, **kwargs)
    def set_title(self, *args, **kwargs): return self._record("set_title", *args, **kwargs)
    def set_xlim(self, *args, **kwargs): return self._record("set_xlim", *args, **kwargs)
    def set_ylim(self, *args, **kwargs): return self._record("set_ylim", *args, **kwargs)
    def margins(self, *args, **kwargs): return self._record("margins", *args, **kwargs)
    def legend(self, *args, **kwargs):
        self._record("legend", *args, **kwargs)
        return SimpleNamespace(set_in_layout=lambda _value: None)

    def get_legend_handles_labels(self):
        handles = []
        labels = []
        for _name, _args, kwargs in self.calls:
            if type(kwargs.get("label")) is str:
                handles.append(object())
                labels.append(kwargs["label"])
        return handles, labels


class _SpyFigure:
    def __init__(self):
        self.calls = []
        self.texts = []
        self.transFigure = object()

    def text(self, *args, **kwargs):
        self.calls.append(("text", args, kwargs))
        self.texts.append(args[2])
        return _SpyText(args[2])

    def suptitle(self, *args, **kwargs):
        self.calls.append(("suptitle", args, kwargs))
        self.texts.append(args[0])

    def legend(self, *args, **kwargs):
        self.calls.append(("legend", args, kwargs))
        return SimpleNamespace(set_in_layout=lambda _value: None)

    def tight_layout(self, *args, **kwargs):
        self.calls.append(("tight_layout", args, kwargs))


def _spy_data() -> dict:
    comparisons = []
    cells = {}
    values = {
        "write-heavy": (-9.3448, -35.9897, 55.5031),
        "balanced": (-37.3765, -44.6037, 83.5081),
        "read-heavy": (-55.1167, -51.8903, 98.4334),
    }
    for workload in WORKLOADS:
        for axis, percent in zip(AXES, values[workload]):
            judgment = "成立" if axis == "sort_best" else "不成立"
            if workload == "write-heavy" and axis == "sort_best":
                # recomputed gate=True / frozen judgment=不成立の authority control。
                judgment = "不成立"
            recomputed_gate = percent > 3.0
            comparisons.append({
                "workload": workload, "right_cell": f"{workload}:{axis}",
                "relative_median_difference_percent": percent,
                "gate1_recomputed_for_consistency": recomputed_gate,
                "gate2_recomputed_for_consistency": True,
                "judgment": judgment,
            })
        for index, configuration in enumerate(PLOT_CONFIGURATIONS):
            samples1 = [1_000_000 + index * 100_000 + step * 1000 for step in range(4)]
            samples2 = [1_005_000 + index * 100_000 + step * 1000 for step in range(4)]
            all_values = samples1 + samples2
            mean = statistics.fmean(all_values)
            cells[f"{workload}:{configuration}"] = {
                "block_samples_tps": {"block1": samples1, "block2": samples2},
                "median_tps": statistics.median(all_values), "mean_tps": mean,
                "ci95_mean_half_tps": T_DF7 * statistics.stdev(all_values) / math.sqrt(8),
            }
    return {"facts": {
        "comparisons": comparisons, "cells": cells,
        "claim": {"judgment": "不成立", "failed_pair_count": 6,
                  "passed_pair_count": 3,
                  "pair_count": 9, "p_family": 1.0},
    }}


def test_n10_production_stops_judgment_gate_disagreement_and_marker_uses_report():
    generator = _load_generator_for_production_tests()
    try:
        generator._validate_report_judgment("fixture", "不成立", True, True)
    except generator.FigureDataError as exc:
        if "frozen judgment differs from recomputed gates" not in str(exc):
            raise AssertionError(f"wrong judgment/gate rejection: {exc}") from exc
    else:
        raise AssertionError("production accepted frozen judgment/recomputed gate disagreement")

    fig = _SpyFigure()
    axes = [[_SpyAxis() for _ in range(3)] for _ in range(2)]
    data = _spy_data()
    generator.draw_figure_artists(fig, axes, data)
    real_scatter = [
        call for call in axes[0][0].calls
        if call[0] == "scatter" and call[1] and call[1][0]
    ]
    fixture = next(
        row for row in data["facts"]["comparisons"]
        if row["workload"] == "write-heavy"
        and row["gate1_recomputed_for_consistency"] is True
        and row["judgment"] == "不成立"
    )
    fixture_index = [
        row for row in data["facts"]["comparisons"]
        if row["workload"] == "write-heavy"
    ].index(fixture)
    if fixture["gate1_recomputed_for_consistency"] is not True:
        raise AssertionError("authority fixture does not disagree")
    if fixture["judgment"] != "不成立" or real_scatter[fixture_index][2].get("marker") != "x":
        raise AssertionError("production marker did not use frozen report judgment")

    established_data = _spy_data()
    established_data["facts"]["claim"].update({
        "judgment": "成立", "passed_pair_count": 9,
        "failed_pair_count": 0, "p_family": 0.25,
    })
    established_fig = _SpyFigure()
    established_axes = [[_SpyAxis() for _ in range(3)] for _ in range(2)]
    generator.draw_figure_artists(established_fig, established_axes, established_data)
    legend_labels = [
        call[2].get("label")
        for call in established_axes[0][0].calls
        if call[0] == "scatter" and type(call[2].get("label")) is str
    ]
    if not any("(0/9)" in label for label in legend_labels):
        raise AssertionError(f"failed legend count did not follow claim: {legend_labels}")
    if not any("(9/9; S-1a remains established)" in label for label in legend_labels):
        raise AssertionError(f"passed legend count did not follow claim: {legend_labels}")
    if not any(
        "S-1a ESTABLISHED — 0 of 9 pairs fail — family p=0.2" in value
        for value in established_fig.texts
    ):
        raise AssertionError(f"family banner did not follow claim: {established_fig.texts}")

    bad_data = _spy_data()
    bad_data["facts"]["claim"]["judgment"] = "未知"
    try:
        generator.draw_figure_artists(
            _SpyFigure(), [[_SpyAxis() for _ in range(3)] for _ in range(2)], bad_data)
    except generator.FigureDataError as exc:
        if "unknown family judgment" not in str(exc):
            raise AssertionError(f"wrong unknown-family rejection: {exc}") from exc
    else:
        raise AssertionError("unknown family judgment reached artists")


def test_n11_spy_pins_artist_values_and_bbox_before_save():
    generator = _load_generator_for_production_tests()
    fig = _SpyFigure()
    axes = [[_SpyAxis() for _ in range(3)] for _ in range(2)]
    order = []

    def factory(): return fig, axes
    def checker(_fig, _axes): order.append("bbox")
    def saver(_fig, path): order.append(path.suffix)

    generator.make_figure(
        _spy_data(), ROOT / "docs/paper-story/figures/fig4_s1a_9pair_direct_comparison",
        figure_factory=factory, layout_checker=checker, save_callback=saver)
    if order != ["bbox", ".png", ".pdf"]:
        raise AssertionError(f"bbox/save order differs: {order}")
    bottom_legends = [call for call in fig.calls if call[0] == "legend"]
    if (len(bottom_legends) != 1
            or bottom_legends[0][2].get("loc") != "lower center"
            or bottom_legends[0][2].get("bbox_to_anchor") != (0.5, 0.025)
            or bottom_legends[0][2].get("bbox_transform") is not fig.transFigure):
        raise AssertionError(
            f"bottom legend is not pinned to the figure footer: {bottom_legends}"
        )
    for column in range(3):
        lines = [call[1][0] for call in axes[0][column].calls if call[0] == "axvline"]
        if lines != [0.0, 3.0]:
            raise AssertionError(f"top reference line arguments differ: {lines}")
        real_scatter = [call for call in axes[0][column].calls
                        if call[0] == "scatter" and call[1] and call[1][0]]
        expected_values = [
            row["relative_median_difference_percent"]
            for row in _spy_data()["facts"]["comparisons"]
            if row["workload"] == WORKLOADS[column]
        ]
        observed_values = [call[1][0][0] for call in real_scatter]
        if observed_values != expected_values:
            raise AssertionError(f"top scatter arguments differ: {observed_values}")
        areas = [call[2].get("s") for call in real_scatter]
        if areas != [44.0, 44.0, 44.0]:
            raise AssertionError(f"top marker areas differ: {areas}")
        markers = [call[2].get("marker") for call in real_scatter]
        selected = [
            row for row in _spy_data()["facts"]["comparisons"]
            if row["workload"] == WORKLOADS[column]
        ]
        expected_markers = ["o" if row["judgment"] == "成立" else "x" for row in selected]
        if markers != expected_markers:
            raise AssertionError(f"top marker judgments differ: {markers}")
        tick_calls = [call for call in axes[0][column].calls if call[0] == "set_xticks"]
        if len(tick_calls) != 1 or 3.0 in tick_calls[0][1][0]:
            raise AssertionError(f"strict floor leaked into major ticks: {tick_calls}")
        annotations = [call for call in axes[0][column].calls if call[0] == "annotate"]
        if len(annotations) != 3:
            raise AssertionError(f"data-label annotation count differs: {annotations}")
        for call, row in zip(annotations, selected):
            percent = row["relative_median_difference_percent"]
            xytext = call[2].get("xytext")
            if call[2].get("textcoords") != "offset points":
                raise AssertionError(f"data label is not renderer-offset: {call}")
            if not xytext or (xytext[0] < 0) != (percent < 0):
                raise AssertionError(f"data label is not outward: {call}")
        panel_text = [
            call[1][2] if call[0] == "text" else call[1][0]
            for call in axes[0][column].calls
            if call[0] in {"text", "annotate"}
        ]
        if "strict floor: > +3%" not in panel_text or "does not clear gate" not in panel_text:
            raise AssertionError(f"top gate text differs: {panel_text}")
        errorbars = [call for call in axes[1][column].calls if call[0] == "errorbar"]
        if len(errorbars) != 5:  # four cells + empty legend artist
            raise AssertionError(f"bottom errorbar count differs: {len(errorbars)}")
    if not any("S-1a NOT ESTABLISHED — 6 of 9 pairs fail — family p=1.0" in text
               for text in fig.texts):
        raise AssertionError(f"banner text differs: {fig.texts}")


def test_n12_collects_all_artist_and_legend_text():
    generator = _load_generator_for_production_tests()
    fig = _SpyFigure()
    axes = [[_SpyAxis() for _ in range(3)] for _ in range(2)]
    generator.draw_figure_artists(fig, axes, _spy_data())
    collected = list(fig.texts)
    for row in axes:
        for axis in row:
            collected.extend(item.text for item in axis.texts)
            for name, args, kwargs in axis.calls:
                if name in {"scatter", "errorbar"} and type(kwargs.get("label")) is str:
                    collected.append(kwargs["label"])
                if name in {"set_title", "set_xlabel", "set_ylabel"} and args:
                    collected.append(str(args[0]))
                if name in {"set_xticks", "set_yticks"} and len(args) > 1:
                    collected.append(str(args[1]))
    text = "\n".join(collected)
    leaked = sorted(value for value in FORBIDDEN_ARTIST_TEXT if value in text)
    if leaked:
        raise AssertionError(f"internal identifiers leaked into artist text: {leaked}")
    legend_labels = [
        value for value in collected
        if "criterion" in value or "samples" in value or "mean and" in value
    ]
    if not legend_labels or any("×" in value or "○" in value for value in legend_labels):
        raise AssertionError(f"legend labels contain duplicate marker glyphs: {legend_labels}")

    _mpl, plt = generator._load_plotting()
    real_fig, array = plt.subplots(2, 3, figsize=(12.0, 7.35), squeeze=False)
    real_axes = [[array[row, column] for column in range(3)] for row in range(2)]
    try:
        generator.draw_figure_artists(real_fig, real_axes, _spy_data())
        handle_and_legend_text = []
        for row in real_axes:
            for axis in row:
                for artist in axis.get_children():
                    label = artist.get_label() if hasattr(artist, "get_label") else None
                    if type(label) is str and label and not label.startswith("_"):
                        handle_and_legend_text.append(label)
                legend = axis.get_legend()
                if legend is not None:
                    handle_and_legend_text.extend(
                        item.get_text() for item in legend.get_texts()
                    )
        for legend in real_fig.legends:
            handle_and_legend_text.extend(
                item.get_text() for item in legend.get_texts()
            )
        handle_text = "\n".join(handle_and_legend_text)
        leaked = sorted(
            value for value in FORBIDDEN_ARTIST_TEXT if value in handle_text
        )
        if leaked:
            raise AssertionError(f"internal identifiers leaked into legend handles: {leaked}")
        if any("×" in value or "○" in value for value in handle_and_legend_text):
            raise AssertionError("legend handle/label duplicated marker glyph")
    finally:
        plt.close(real_fig)


def test_n13_bbox_checker_rejects_overlapping_non_tick_text():
    generator = _load_generator_for_production_tests()
    _mpl, plt = generator._load_plotting()
    fig, axis = plt.subplots(1, 1, figsize=(3, 2))
    axes = [[axis]]
    axis.text(0.5, 0.5, "first", transform=axis.transAxes)
    axis.text(0.5, 0.5, "second", transform=axis.transAxes)
    fig.tight_layout()
    try:
        generator.check_figure_layout(fig, axes)
    except generator.FigureLayoutError as exc:
        if "overlap" not in str(exc):
            raise AssertionError(f"wrong bbox rejection: {exc}") from exc
    else:
        raise AssertionError("overlapping annotations were accepted")
    finally:
        plt.close(fig)


def test_n14_bbox_checker_pins_ticks_marker_reference_clearance_and_agg():
    generator = _load_generator_for_production_tests()
    mpl, plt = generator._load_plotting()
    if str(mpl.get_backend()).lower() != "agg":
        raise AssertionError(f"generator backend is not Agg: {mpl.get_backend()}")

    def expect_layout_rejected(builder, reason):
        fig, axis = plt.subplots(1, 1, figsize=(3.0, 2.0))
        try:
            builder(fig, axis)
            fig.tight_layout()
            generator.check_figure_layout(fig, [[axis]])
        except generator.FigureLayoutError as exc:
            if reason not in str(exc):
                raise AssertionError(f"wrong layout rejection for {reason}: {exc}") from exc
        else:
            raise AssertionError(f"layout checker accepted {reason} control")
        finally:
            plt.close(fig)

    def overlap_ticks(_fig, axis):
        axis.set_xlim(-1.0, 1.0)
        axis.set_xticks([0.0, 0.001], ["zero", "near"])

    def overlap_marker(_fig, axis):
        axis.set_xlim(0.0, 1.0)
        axis.set_ylim(0.0, 1.0)
        axis.scatter([0.5], [0.5], s=44.0, gid="s1-data-marker")
        label = axis.annotate(
            "marker label", xy=(0.5, 0.5), xytext=(0.0, 0.0),
            textcoords="offset points", ha="left", va="center",
        )
        label.set_gid("s1-data-label")

    def approach_reference(_fig, axis):
        axis.set_xlim(0.0, 1.0)
        axis.set_ylim(0.0, 1.0)
        axis.axvline(0.25, gid="s1-reference-line")
        axis.scatter([0.20], [0.5], s=44.0, gid="s1-data-marker")
        label = axis.annotate(
            "line label", xy=(0.20, 0.5), xytext=(9.0, 0.0),
            textcoords="offset points", ha="left", va="center",
        )
        label.set_gid("s1-data-label")

    def overlap_legend_axis_label(_fig, axis):
        axis.set_xticks([])
        axis.set_yticks([])
        axis.scatter([], [], label="legend target")
        axis.legend(
            loc="lower center", bbox_to_anchor=(0.5, -0.05), borderaxespad=0,
        )
        axis.set_xlabel("axis label target", labelpad=0)

    def overlap_legend_title(_fig, axis):
        axis.set_xticks([])
        axis.set_yticks([])
        axis.scatter([], [], label="legend target")
        axis.legend(
            loc="upper center", bbox_to_anchor=(0.5, 1.04), borderaxespad=0,
        )
        axis.set_title("title target", pad=0)

    def overlap_legend_data_label(_fig, axis):
        axis.set_xlim(0.0, 1.0)
        axis.set_ylim(0.0, 1.0)
        axis.set_xticks([])
        axis.set_yticks([])
        axis.scatter([0.4], [0.5], s=44.0, gid="s1-data-marker")
        label = axis.annotate(
            "data target", xy=(0.4, 0.5), xytext=(14.0, 0.0),
            textcoords="offset points", ha="left", va="center",
        )
        label.set_gid("s1-data-label")
        axis.scatter([], [], label="legend target")
        axis.legend(
            loc="center", bbox_to_anchor=(0.62, 0.5), borderaxespad=0,
        )

    expect_layout_rejected(overlap_ticks, "x tick text overlap")
    expect_layout_rejected(overlap_marker, "data label/marker clearance")
    expect_layout_rejected(approach_reference, "data label/reference line clearance")
    expect_layout_rejected(overlap_legend_axis_label, "legend/text overlap")
    expect_layout_rejected(overlap_legend_title, "legend/text overlap")
    expect_layout_rejected(overlap_legend_data_label, "legend/text overlap")

    with mpl.rc_context():
        generator._style(mpl)
        if list(mpl.rcParams["font.family"]) != ["DejaVu Sans"]:
            raise AssertionError(f"generator font family differs: {mpl.rcParams['font.family']}")
        real_fig, array = plt.subplots(2, 3, figsize=(12.0, 7.35), squeeze=False)
        real_axes = [[array[row, column] for column in range(3)] for row in range(2)]
        try:
            generator.draw_figure_artists(real_fig, real_axes, _spy_data())
            real_fig.tight_layout(
                rect=generator.FIGURE_LAYOUT_RECT, h_pad=2.2, w_pad=1.2)
            generator.check_figure_layout(real_fig, real_axes)
        finally:
            plt.close(real_fig)


def test_n16_bbox_checker_rejects_legacy_bottom_legend_overlap():
    generator = _load_generator_for_production_tests()
    mpl, plt = generator._load_plotting()
    with mpl.rc_context():
        generator._style(mpl)
        fig, array = plt.subplots(2, 3, figsize=(12.0, 7.35), squeeze=False)
        axes = [[array[row, column] for column in range(3)] for row in range(2)]
        try:
            generator.draw_figure_artists(fig, axes, _spy_data())
            fig.legends[-1].remove()
            axes[1][0].legend(
                loc="lower left", bbox_to_anchor=(0.0, -0.45), fontsize=6.4,
                ncol=3,
            )
            # V5 の修正前と同じ axis-relative 凡例位置と下端 margin。
            fig.tight_layout(
                rect=(0.02, 0.08, 0.995, 0.90), h_pad=2.2, w_pad=1.2)
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
            legend_texts = axes[1][0].get_legend().get_texts()
            tick_texts = axes[1][0].get_xticklabels()
            overlaps = [
                (legend.get_text(), tick.get_text())
                for legend in legend_texts
                for tick in tick_texts
                if generator._bbox_intersection_area(
                    legend.get_window_extent(renderer),
                    tick.get_window_extent(renderer),
                ) > 1.0
            ]
            if not overlaps or not any(
                legend == "block1 samples" and tick == "compile-time flags"
                for legend, tick in overlaps
            ):
                raise AssertionError(
                    f"legacy V5 control did not reproduce the expected overlap: {overlaps}"
                )
            try:
                generator.check_figure_layout(fig, axes)
            except generator.FigureLayoutError as exc:
                if "legend/text overlap" not in str(exc):
                    raise AssertionError(
                        f"wrong legacy legend/tick rejection: {exc}"
                    ) from exc
            else:
                raise AssertionError("legacy bottom legend/tick overlap was accepted")
        finally:
            plt.close(fig)


def _production_layout_control(generator, mpl, plt):
    generator._style(mpl)
    fig, array = plt.subplots(2, 3, figsize=(12.0, 7.35), squeeze=False)
    axes = [[array[row, column] for column in range(3)] for row in range(2)]
    generator.draw_figure_artists(fig, axes, _spy_data())
    fig.tight_layout(
        rect=generator.FIGURE_LAYOUT_RECT, h_pad=2.2, w_pad=1.2)
    generator.check_figure_layout(fig, axes)
    return fig, axes


def test_n17_bbox_checker_rejects_missing_bottom_legend():
    generator = _load_generator_for_production_tests()
    mpl, plt = generator._load_plotting()
    with mpl.rc_context():
        fig, axes = _production_layout_control(generator, mpl, plt)
        try:
            fig.legends[-1].remove()
            try:
                generator.check_figure_layout(fig, axes)
            except generator.FigureLayoutError as exc:
                if "required artist text missing" not in str(exc):
                    raise AssertionError(
                        f"wrong missing-bottom-legend rejection: {exc}"
                    ) from exc
            else:
                raise AssertionError("missing bottom legend was accepted")
        finally:
            plt.close(fig)


def test_n18_bbox_checker_rejects_bottom_legend_excluded_from_tight_bbox():
    generator = _load_generator_for_production_tests()
    mpl, plt = generator._load_plotting()
    with mpl.rc_context():
        fig, axes = _production_layout_control(generator, mpl, plt)
        try:
            fig.legends[-1].set_in_layout(False)
            try:
                generator.check_figure_layout(fig, axes)
            except generator.FigureLayoutError as exc:
                if "required artist outside saved tight bbox" not in str(exc):
                    raise AssertionError(
                        f"wrong tight-bbox-exclusion rejection: {exc}"
                    ) from exc
            else:
                raise AssertionError("bottom legend excluded from tight bbox was accepted")
        finally:
            plt.close(fig)


def _validate_self_test_selection(tests: Sequence[object]) -> None:
    names = [getattr(test, "__name__", None) for test in tests]
    if any(type(name) is not str for name in names):
        raise ValueError("self-run test has no exact name")
    if len(names) != len(set(names)):
        raise ValueError("self-run test names are duplicated")
    observed = set(names)
    if observed != EXPECTED_SELF_TEST_NAMES:
        raise ValueError(
            "self-run exact test set differs: "
            f"missing={sorted(EXPECTED_SELF_TEST_NAMES - observed)!r} "
            f"extra={sorted(observed - EXPECTED_SELF_TEST_NAMES)!r}"
        )


def test_n15_self_run_harness_rejects_invalid_test_sets_before_execution():
    executed = []

    def named(name):
        def control():
            executed.append(name)
        control.__name__ = name
        return control

    exact = [named(name) for name in sorted(EXPECTED_SELF_TEST_NAMES)]
    _validate_self_test_selection(exact)
    extra = named("test_unregistered_extra")
    controls = (
        [],
        exact[:-1],
        exact + [extra],
        exact[:-1] + [exact[0], exact[0]],
    )
    for control in controls:
        with redirect_stdout(io.StringIO()):
            rc = _run(control)
        if rc != 1:
            raise AssertionError("self-run invalid selection did not return rc=1")
        if executed:
            raise AssertionError(f"self-run executed tests before set validation: {executed}")


def _run(tests: Sequence[object] | None = None) -> int:
    if tests is None:
        tests = [value for name, value in sorted(globals().items())
                 if name.startswith("test_") and callable(value)]
    else:
        tests = list(tests)
    try:
        _validate_self_test_selection(tests)
    except ValueError as exc:
        print(f"FAIL self-test selection: {exc}")
        return 1
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {test.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run())
