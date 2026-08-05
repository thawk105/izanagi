#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pegasus 上で /proc/cpuinfo の観測者効果を非認証実験する。

``--self-test`` は合成観測だけを使い、/proc と subprocess を一切参照しない。
通常実行は PBS wrapper が作成した no-clobber directory だけへ create-only で書く。
done-marker がない出力は、result/manifest の有無にかかわらず不採用である。
"""
from __future__ import annotations

import argparse
import errno
import hashlib
import json
import math
import os
import platform
import random
import re
import select
import signal
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence


SCHEMA_VERSION = "t419-probe-causality/v1"
EXPECTED_CPU_COUNT = 48
DEFAULT_SEED = 419
DEFAULT_READ_INTERVAL_MS = 50.0
DEFAULT_HARD_DEADLINE_SECONDS = 900.0
COOLDOWN_SECONDS = 1.0
BUSY_MIN_CPU_TICKS = 5
SHAM_MAX_CPU_TICKS = 1
COMPETITOR_MIN_TICKS = 3
COMPETITOR_MAX_TICKS_PER_SECOND = 25.0
"""走行 889279 の実測 65 subwindow で、非自活動の率は中央値 0.00 /
最大 11.86 tick/s。その活動は読み値を汚していない — A1 の control 観測
11,280 件のうち帯外は 1 件 (0.0089%) で、率 7.9 tick/s の subwindow が
4 つあっても control 帯外は増えなかった。一方 A2 が置く busy child は
1 コア占有で約 100 tick/s。25.0 は観測された背景最大 11.86 の約 2 倍、
1 コア占有の約 1/4 であり、背景ノイズと実負荷を分離する。
絶対下限 3 tick は据え置き。
"""
INCONCLUSIVE_PAIR_INVALID_MIN = 3
CHILD_TERM_TIMEOUT_SECONDS = 2.0
CHILD_KILL_TIMEOUT_SECONDS = 2.0
PINNED_HIT_RATE_MIN = 0.95
NONPINNED_OUT_OF_BAND_RATE_MAX = 0.05
POSITIVE_CONTRAST_CPU_MIN = 46
BASELINE_READS = 30
PIN_REPEATS = 5
MIGRATION_READS = 30
ALPHA_K = 5
ALPHA_QUIET_BLOCKS = 10
CORESIDENT_TARGETS = 8
CORESIDENT_REPEATS = 5
ALPHA_CONTENTION_BLOCKS = 3
RAW_CPUINFO_LIMIT = 3
ARM_ORDER = (
    "A0_quiet_baseline",
    "A1_pin_sweep",
    "A4_migration_description",
    "A3_alpha_quiet",
    "A2_coresident",
    "A3_alpha_contention",
)
EXPECTED_PRIMARY_READS = {
    "A0_quiet_baseline": BASELINE_READS,
    "A1_pin_sweep": EXPECTED_CPU_COUNT * PIN_REPEATS,
    "A4_migration_description": MIGRATION_READS,
    "A3_alpha_quiet": ALPHA_QUIET_BLOCKS * ALPHA_K,
    "A2_coresident": CORESIDENT_TARGETS * 2 * CORESIDENT_REPEATS,
    "A3_alpha_contention": ALPHA_CONTENTION_BLOCKS * ALPHA_K,
}
assert sum(EXPECTED_PRIMARY_READS.values()) == 445
PREREGISTERED_PRIMARY_READS = 445
_PBS_JOBID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9:._-]*")
_HEX64_RE = re.compile(r"[0-9a-f]{64}")
_HEAD_RE = re.compile(r"[0-9a-f]{40}")
DIAGNOSTIC_FIELD_STATUSES = ("value", "absent", "unreadable", "error")


def _error(exc: BaseException) -> dict[str, str]:
    return {"type": type(exc).__name__, "message": str(exc)}


def calibration_band(
    expected_samples: Sequence[float], tolerance_pct: float
) -> dict[str, float]:
    """凍結 expected sample から canonical inclusive band を作る純粋関数。"""
    if not expected_samples:
        raise ValueError("expected_samples must not be empty")
    samples = [float(value) for value in expected_samples]
    tolerance = float(tolerance_pct)
    if (
        any(not math.isfinite(value) or value <= 0.0 for value in samples)
        or not math.isfinite(tolerance)
        or tolerance < 0.0
    ):
        raise ValueError("calibration values must be finite and positive")
    nominal = float(statistics.median(samples))
    delta = abs(nominal) * tolerance / 100.0
    return {
        "expected_median_mhz": nominal,
        "tolerance_pct": tolerance,
        "lower_mhz": nominal - delta,
        "upper_mhz": nominal + delta,
    }


def _bounds(band: Mapping[str, float]) -> tuple[float, float]:
    lower = float(band["lower_mhz"])
    upper = float(band["upper_mhz"])
    if not math.isfinite(lower) or not math.isfinite(upper) or lower > upper:
        raise ValueError("invalid band")
    return lower, upper


def valid_band(band: Any) -> bool:
    """Canonical band の形・有限性・median±tolerance の数式的一致を検査する。"""
    if not isinstance(band, Mapping):
        return False
    try:
        lower, upper = _bounds(band)
        nominal = float(band["expected_median_mhz"])
        tolerance = float(band["tolerance_pct"])
    except (KeyError, TypeError, ValueError, OverflowError):
        return False
    expected_delta = nominal * tolerance / 100.0
    return (
        math.isfinite(nominal)
        and nominal > 0.0
        and math.isfinite(tolerance)
        and tolerance >= 0.0
        and lower == nominal - expected_delta
        and upper == nominal + expected_delta
    )


def canonical_pass(samples: Sequence[float], band: Mapping[str, float]) -> bool:
    """全要素が inclusive band 内なら真。空 vector は fail-closed。"""
    lower, upper = _bounds(band)
    values = [float(value) for value in samples]
    return bool(values) and all(
        math.isfinite(value) and lower <= value <= upper for value in values
    )


def exact_nominal_rate(samples: Sequence[float], nominal: float) -> float:
    """canonical 判定と分離した、較正 median への厳密一致率。"""
    values = [float(value) for value in samples]
    return (
        sum(value == float(nominal) for value in values) / len(values)
        if values
        else 0.0
    )


def _int_vector(vector: Mapping[Any, Any]) -> dict[int, float]:
    result: dict[int, float] = {}
    for cpu, value in vector.items():
        if type(cpu) is not int:
            raise ValueError(f"CPU key must be an exact int: {cpu!r}")
        if type(value) not in (int, float):
            raise ValueError(f"MHz value must be an exact int or float: {value!r}")
        cpu_id = cpu
        if cpu_id in result:
            raise ValueError(f"duplicate CPU after integer normalization: {cpu!r}")
        result[cpu_id] = float(value)
    return result


def out_of_band_cpu_ids(
    vector: Mapping[Any, Any], band: Mapping[str, float]
) -> set[int]:
    lower, upper = _bounds(band)
    return {
        cpu
        for cpu, value in _int_vector(vector).items()
        if not math.isfinite(value) or value < lower or value > upper
    }


def alpha_cumulative(
    vectors: Sequence[Mapping[Any, Any]], band: Mapping[str, float]
) -> list[dict[str, Any]]:
    """位置ごとの累積最小を k=1..K で評価する純粋関数。"""
    if not vectors:
        return []
    normalized = [_int_vector(vector) for vector in vectors]
    keys = set(normalized[0])
    if not keys or any(set(vector) != keys for vector in normalized[1:]):
        raise ValueError("alpha vectors must have one identical non-empty CPU key set")
    lower, upper = _bounds(band)
    cumulative: dict[int, float] = {}
    result = []
    for index, vector in enumerate(normalized, 1):
        cumulative = (
            dict(vector)
            if not cumulative
            else {cpu: min(cumulative[cpu], vector[cpu]) for cpu in sorted(keys)}
        )
        values = [cumulative[cpu] for cpu in sorted(keys)]
        result.append(
            {
                "k": index,
                "canonical_pass": canonical_pass(values, band),
                "below_band_count": sum(value < lower for value in values),
                "above_band_count": sum(value > upper for value in values),
                "cumulative_min_by_cpu": dict(cumulative),
            }
        )
    return result


def beta_pass(
    vector: Mapping[Any, Any], reader_cpu: int, band: Mapping[str, float]
) -> bool:
    """reader に対応する 1 要素だけを除外して canonical 述語を適用する。"""
    normalized = _int_vector(vector)
    if int(reader_cpu) not in normalized:
        return False
    return canonical_pass(
        [value for cpu, value in normalized.items() if cpu != int(reader_cpu)], band
    )


def gamma_pass(vector: Mapping[Any, Any], band: Mapping[str, float]) -> bool:
    """帯外を任意の 1 要素まで許容する counterfactual predicate。"""
    normalized = _int_vector(vector)
    return bool(normalized) and len(out_of_band_cpu_ids(normalized, band)) <= 1


def select_evenly_spaced(cpus: Sequence[int], count: int) -> list[int]:
    """sorted candidate から両端を含む等間隔 index を決定的に選ぶ。"""
    ordered = sorted(set(int(cpu) for cpu in cpus))
    if count <= 0 or len(ordered) < count:
        raise ValueError("not enough CPUs for evenly spaced selection")
    if count == 1:
        return [ordered[len(ordered) // 2]]
    indexes = [round(i * (len(ordered) - 1) / (count - 1)) for i in range(count)]
    selected = [ordered[index] for index in indexes]
    if len(set(selected)) != count:
        raise ValueError("even spacing produced duplicate indices")
    return selected


def _reading_values(reading: Mapping[str, Any]) -> dict[int, float]:
    vector = reading.get("mhz_by_cpu")
    if not isinstance(vector, Mapping):
        raise ValueError("reading lacks mhz_by_cpu mapping")
    return _int_vector(vector)


def _arm_reads(observations: Mapping[str, Any], name: str) -> list[Mapping[str, Any]]:
    arms = observations.get("arms")
    if not isinstance(arms, Mapping):
        return []
    arm = arms.get(name)
    if not isinstance(arm, Mapping) or not isinstance(arm.get("reads"), list):
        return []
    return arm["reads"]


def _group_readings(
    readings: Sequence[Mapping[str, Any]], size: int
) -> list[list[Mapping[str, Any]]]:
    if size <= 0 or len(readings) % size:
        return []
    return [list(readings[index : index + size]) for index in range(0, len(readings), size)]


def _recorded_blocks(arm: Mapping[str, Any]) -> list[list[Mapping[str, Any]]]:
    blocks = arm.get("blocks")
    if not isinstance(blocks, list):
        return []
    result = []
    for block in blocks:
        if isinstance(block, Mapping) and isinstance(block.get("reads"), list):
            result.append(block["reads"])
    return result


def _method_summary(outcomes: Sequence[bool], *, should_pass: bool) -> dict[str, Any]:
    passed = sum(bool(value) for value in outcomes)
    rejected = len(outcomes) - passed
    return {
        "evaluated": len(outcomes),
        "passed": passed,
        "rejected": rejected,
        "false_positive_overreject_count": rejected if should_pass else 0,
        "false_negative_missed_deviation_count": passed if not should_pass else 0,
    }


def alpha_with_rotation(
    a1_arm: Mapping[str, Any], band: Mapping[str, float]
) -> dict[str, Any]:
    """A1 の randomized pin 順を K target ごとに束ね、各 target の先頭 read を使う。"""
    pin_order = a1_arm.get("pin_order")
    by_pin = a1_arm.get("by_pin")
    if not isinstance(pin_order, list) or not isinstance(by_pin, list):
        raise ValueError("A1 pin_order/by_pin missing for alpha rotation")
    if len(pin_order) != len(by_pin):
        raise ValueError("A1 pin_order/by_pin length mismatch for alpha rotation")
    selected: list[tuple[int, Mapping[str, Any], int]] = []
    for target_index, (target, group) in enumerate(zip(pin_order, by_pin)):
        if not isinstance(group, Mapping) or int(group.get("pin_target", -1)) != int(target):
            raise ValueError("A1 by_pin order mismatch for alpha rotation")
        reads = group.get("reads")
        if not isinstance(reads, list) or not reads or not isinstance(reads[0], Mapping):
            raise ValueError("A1 by_pin primary read missing for alpha rotation")
        selected.append((int(target), reads[0], target_index * PIN_REPEATS))

    complete = len(selected) // ALPHA_K * ALPHA_K
    groups = []
    for start in range(0, complete, ALPHA_K):
        members = selected[start : start + ALPHA_K]
        analysis = alpha_cumulative(
            [_reading_values(reading) for _, reading, _ in members], band
        )
        groups.append(
            {
                "group": start // ALPHA_K,
                "positions": [
                    {
                        "position": position,
                        "pin_target": target,
                        "primary_read_index": flat_index,
                        "within_target_primary_read_index": 0,
                        "started_monotonic_ns": reading.get("started_monotonic_ns"),
                    }
                    for position, (target, reading, flat_index) in enumerate(members)
                ],
                "alpha": analysis,
            }
        )
    discarded = selected[complete:]
    return {
        "k": ALPHA_K,
        "primary_read_selector": "first_primary_read_per_pin_target",
        "group_count": len(groups),
        "discarded_pin_target_count": len(discarded),
        "discarded_pin_targets": [target for target, _, _ in discarded],
        "groups": groups,
    }


def evaluate_method_table(
    observations: Mapping[str, Any], band: Mapping[str, float]
) -> dict[str, Any]:
    """同じ raw vector に α/β/γ を当てる 2×3 counterfactual 表。"""
    arms = observations.get("arms") if isinstance(observations.get("arms"), Mapping) else {}
    a0 = _arm_reads(observations, "A0_quiet_baseline")
    a1 = arms.get("A1_pin_sweep", {}) if isinstance(arms, Mapping) else {}
    a3q = _arm_reads(observations, "A3_alpha_quiet")
    a2 = arms.get("A2_coresident", {}) if isinstance(arms, Mapping) else {}
    a3c = _arm_reads(observations, "A3_alpha_contention")

    quiet_alpha_blocks = _group_readings(a0, ALPHA_K)
    if isinstance(arms, Mapping) and isinstance(arms.get("A3_alpha_quiet"), Mapping):
        quiet_alpha_blocks.extend(_recorded_blocks(arms["A3_alpha_quiet"]))
    reject_alpha_blocks: list[list[Mapping[str, Any]]] = []
    sham_alpha_blocks: list[list[Mapping[str, Any]]] = []
    if isinstance(a2, Mapping):
        for pair in a2.get("pairs", []):
            if not isinstance(pair, Mapping):
                continue
            if pair.get("status") != "VALID":
                continue
            for condition in pair.get("conditions", []):
                if isinstance(condition, Mapping):
                    reads = condition.get("reads")
                    if isinstance(reads, list):
                        if condition.get("mode") == "busy":
                            reject_alpha_blocks.append(reads)
                        elif condition.get("mode") == "sham":
                            sham_alpha_blocks.append(reads)
    if isinstance(arms, Mapping) and isinstance(arms.get("A3_alpha_contention"), Mapping):
        reject_alpha_blocks.extend(_recorded_blocks(arms["A3_alpha_contention"]))

    quiet_alpha_blocks.extend(sham_alpha_blocks)
    quiet_reads = list(a0) + list(a3q)
    reject_reads = []
    if isinstance(a2, Mapping):
        for pair in a2.get("pairs", []):
            if isinstance(pair, Mapping):
                if pair.get("status") != "VALID":
                    continue
                for condition in pair.get("conditions", []):
                    if isinstance(condition, Mapping) and condition.get("mode") == "busy":
                        reject_reads.extend(condition.get("reads", []))
                    elif isinstance(condition, Mapping) and condition.get("mode") == "sham":
                        quiet_reads.extend(condition.get("reads", []))
    reject_reads.extend(a3c)

    def alpha_outcomes(
        blocks: Sequence[Sequence[Mapping[str, Any]]], stage: int
    ) -> list[bool]:
        outcomes = []
        for block in blocks:
            if len(block) < stage:
                continue
            analyzed = alpha_cumulative(
                [_reading_values(reading) for reading in block[:stage]], band
            )
            outcomes.append(bool(analyzed[-1]["canonical_pass"]))
        return outcomes

    alpha_without_rotation_stages: dict[str, Any] = {}
    for stage in range(1, ALPHA_K + 1):
        alpha_without_rotation_stages[str(stage)] = {
            "should_pass": _method_summary(
                alpha_outcomes(quiet_alpha_blocks, stage), should_pass=True
            ),
            "should_reject": _method_summary(
                alpha_outcomes(reject_alpha_blocks, stage), should_pass=False
            ),
        }

    rotation = alpha_with_rotation(a1, band) if isinstance(a1, Mapping) else {
        "k": ALPHA_K,
        "primary_read_selector": "first_primary_read_per_pin_target",
        "group_count": 0,
        "discarded_pin_target_count": 0,
        "discarded_pin_targets": [],
        "groups": [],
    }
    alpha_with_rotation_stages: dict[str, Any] = {}
    for stage in range(1, ALPHA_K + 1):
        outcomes = [
            bool(group["alpha"][stage - 1]["canonical_pass"])
            for group in rotation["groups"]
        ]
        alpha_with_rotation_stages[str(stage)] = {
            "should_pass": _method_summary(outcomes, should_pass=True),
            "should_reject": _method_summary([], should_pass=False),
        }

    beta_quiet = [
        beta_pass(_reading_values(reading), int(reading["reader_cpu_before"]), band)
        for reading in quiet_reads
    ]
    beta_reject = [
        beta_pass(_reading_values(reading), int(reading["reader_cpu_before"]), band)
        for reading in reject_reads
    ]
    gamma_quiet = [gamma_pass(_reading_values(reading), band) for reading in quiet_reads]
    gamma_reject = [gamma_pass(_reading_values(reading), band) for reading in reject_reads]
    rotating_alpha = {
        "stages": alpha_with_rotation_stages,
        "should_pass": alpha_with_rotation_stages[str(ALPHA_K)]["should_pass"],
        "should_reject": alpha_with_rotation_stages[str(ALPHA_K)]["should_reject"],
        "rotation": rotation,
    }
    return {
        "semantics": {
            "should_pass": "quiet A0/A3 and A2 sham; rejection is over-rejection",
            "should_reject": (
                "sustained non-self busy A2/A3+A2; pass is a false negative "
                "that misses an environment deviation"
            ),
        },
        "reported_method_columns": ["alpha", "beta", "gamma"],
        "alpha": rotating_alpha,
        "alpha_with_rotation": rotating_alpha,
        "alpha_without_rotation": {
            "reported_as_alpha": False,
            "stages": alpha_without_rotation_stages,
            "should_pass": alpha_without_rotation_stages[str(ALPHA_K)]["should_pass"],
            "should_reject": alpha_without_rotation_stages[str(ALPHA_K)]["should_reject"],
        },
        "beta": {
            "should_pass": _method_summary(beta_quiet, should_pass=True),
            "should_reject": _method_summary(beta_reject, should_pass=False),
        },
        "gamma": {
            "should_pass": _method_summary(gamma_quiet, should_pass=True),
            "should_reject": _method_summary(gamma_reject, should_pass=False),
        },
    }


def causal_metrics(
    observations: Mapping[str, Any], band: Mapping[str, float], cpus: Sequence[int]
) -> dict[str, Any]:
    """A1 個々の読みから事前登録済み 3 条件を計算する。"""
    reads = _arm_reads(observations, "A1_pin_sweep")
    arms = observations.get("arms")
    a1 = arms.get("A1_pin_sweep") if isinstance(arms, Mapping) else None
    isolation = a1.get("isolation") if isinstance(a1, Mapping) else None
    subwindows = isolation.get("subwindows") if isinstance(isolation, Mapping) else []
    incidental_by_subwindow: dict[str, set[int]] = {}
    if isinstance(subwindows, list):
        for subwindow in subwindows:
            if not isinstance(subwindow, Mapping):
                continue
            identifier = subwindow.get("subwindow_id")
            incidental = subwindow.get("incidental_nonself_cpus")
            if isinstance(identifier, str) and isinstance(incidental, list):
                incidental_by_subwindow[identifier] = {int(cpu) for cpu in incidental}
    pinned_hits = 0
    nonpinned_oob = 0
    nonpinned_total = 0
    by_cpu: dict[int, dict[str, list[bool]]] = {
        int(cpu): {"pinned": [], "control": []} for cpu in cpus
    }
    intersections: dict[int, dict[str, dict[str, int]]] = {
        int(cpu): {
            "pinned": {"incidental_read_count": 0, "intersection_count": 0},
            "control": {"incidental_read_count": 0, "intersection_count": 0},
        }
        for cpu in cpus
    }
    for reading in reads:
        vector = _reading_values(reading)
        target = int(reading["pin_target"])
        reader = int(reading["reader_cpu_before"])
        oob = out_of_band_cpu_ids(vector, band)
        pinned_hits += target in oob
        for cpu in cpus:
            cpu_id = int(cpu)
            population = "pinned" if cpu_id == target else "control"
            by_cpu[cpu_id][population].append(cpu_id in oob)
            identifier = reading.get("isolation_subwindow_id")
            incidental_cpus = incidental_by_subwindow.get(str(identifier), set())
            if cpu_id in incidental_cpus:
                intersections[cpu_id][population]["incidental_read_count"] += 1
                intersections[cpu_id][population]["intersection_count"] += cpu_id in oob
        excluded = {target, reader}
        for cpu in cpus:
            if int(cpu) in excluded:
                continue
            nonpinned_total += 1
            nonpinned_oob += int(cpu) in oob
    pinned_hit_rate = pinned_hits / len(reads) if reads else 0.0
    nonpinned_rate = nonpinned_oob / nonpinned_total if nonpinned_total else 1.0
    contrasts: dict[int, dict[str, float]] = {}
    intersection_metrics: dict[int, dict[str, dict[str, Any]]] = {}
    positive = 0
    for cpu in cpus:
        pinned_values = by_cpu[int(cpu)]["pinned"]
        control_values = by_cpu[int(cpu)]["control"]
        pinned_rate = sum(pinned_values) / len(pinned_values) if pinned_values else 0.0
        control_rate = sum(control_values) / len(control_values) if control_values else 0.0
        contrast = pinned_rate - control_rate
        positive += contrast > 0.0
        contrasts[int(cpu)] = {
            "pinned_out_of_band_rate": pinned_rate,
            "nonpinned_control_out_of_band_rate": control_rate,
            "contrast": contrast,
        }
        intersection_metrics[int(cpu)] = {}
        for population in ("pinned", "control"):
            counts = intersections[int(cpu)][population]
            denominator = counts["incidental_read_count"]
            intersection_metrics[int(cpu)][population] = {
                **counts,
                "intersection_rate": (
                    counts["intersection_count"] / denominator
                    if denominator
                    else None
                ),
            }
    non_signal_intersections = non_signal_rate_exceedance_intersections(
        observations, band
    )
    return {
        "pinned_hit_rate": pinned_hit_rate,
        "pinned_hit_rate_threshold": PINNED_HIT_RATE_MIN,
        "pinned_hit_rate_condition": pinned_hit_rate >= PINNED_HIT_RATE_MIN,
        "nonpinned_out_of_band_rate": nonpinned_rate,
        "nonpinned_out_of_band_rate_threshold": NONPINNED_OUT_OF_BAND_RATE_MAX,
        "nonpinned_out_of_band_rate_condition": (
            nonpinned_rate <= NONPINNED_OUT_OF_BAND_RATE_MAX
        ),
        "paired_contrast_by_cpu": contrasts,
        "positive_contrast_cpu_count": positive,
        "positive_contrast_cpu_threshold": POSITIVE_CONTRAST_CPU_MIN,
        "paired_contrast_condition": positive >= POSITIVE_CONTRAST_CPU_MIN,
        "incidental_out_of_band_intersection_by_cpu": intersection_metrics,
        "non_signal_rate_exceeded_cpus": sorted(
            {
                int(item["cpu"])
                for item in non_signal_intersections
            }
        ),
        "non_signal_rate_exceedance_control_out_of_band_intersections": (
            non_signal_intersections
        ),
    }


def non_signal_rate_exceedance_intersections(
    observations: Mapping[str, Any], band: Mapping[str, float]
) -> list[dict[str, Any]]:
    """非 signal CPU の率超過と、同じ窓の control 帯外読みを交差する。"""
    arms = observations.get("arms")
    if not isinstance(arms, Mapping):
        return []
    result: list[dict[str, Any]] = []
    for arm_name in ARM_ORDER:
        arm = arms.get(arm_name)
        isolation = arm.get("isolation") if isinstance(arm, Mapping) else None
        subwindows = (
            isolation.get("subwindows") if isinstance(isolation, Mapping) else []
        )
        if not isinstance(subwindows, list):
            continue
        reads_by_subwindow: dict[str, list[Mapping[str, Any]]] = {}
        for reading in _arm_reads(observations, arm_name):
            identifier = reading.get("isolation_subwindow_id")
            if isinstance(identifier, str):
                reads_by_subwindow.setdefault(identifier, []).append(reading)
        for subwindow in subwindows:
            if not isinstance(subwindow, Mapping):
                continue
            identifier = subwindow.get("subwindow_id")
            exceedances = subwindow.get("non_signal_rate_exceedances")
            if not isinstance(identifier, str) or not isinstance(exceedances, list):
                continue
            matching_reads = reads_by_subwindow.get(identifier, [])
            for exceedance in exceedances:
                if not isinstance(exceedance, Mapping):
                    continue
                cpu = int(exceedance["cpu"])
                control_read_count = 0
                control_out_of_band_read_count = 0
                for reading in matching_reads:
                    reader_cpus = {
                        int(reading["reader_cpu_before"]),
                        int(reading["reader_cpu_after"]),
                    }
                    pin_target = reading.get("pin_target")
                    if pin_target is not None:
                        reader_cpus.add(int(pin_target))
                    if cpu in reader_cpus:
                        continue
                    control_read_count += 1
                    control_out_of_band_read_count += cpu in out_of_band_cpu_ids(
                        _reading_values(reading), band
                    )
                result.append(
                    {
                        "arm": arm_name,
                        "subwindow_id": identifier,
                        **dict(exceedance),
                        "control_read_count": control_read_count,
                        "control_out_of_band_read_count": (
                            control_out_of_band_read_count
                        ),
                    }
                )
    return result


def coresident_metrics(
    observations: Mapping[str, Any], band: Mapping[str, float]
) -> list[dict[str, Any]]:
    """A2 の sham/busy 対について target indicator と MHz 差を要約する。"""
    arms = observations.get("arms")
    if not isinstance(arms, Mapping):
        return []
    arm = arms.get("A2_coresident")
    if not isinstance(arm, Mapping):
        return []
    result = []
    for pair in arm.get("pairs", []):
        if not isinstance(pair, Mapping):
            continue
        target = int(pair["target_cpu"])
        conditions = {
            condition.get("mode"): condition
            for condition in pair.get("conditions", [])
            if isinstance(condition, Mapping)
        }
        if not {"sham", "busy"} <= set(conditions):
            continue
        item: dict[str, Any] = {"target_cpu": target, "status": pair.get("status")}
        target_values: dict[str, list[float]] = {}
        for mode in ("sham", "busy"):
            values = [
                _reading_values(reading)[target]
                for reading in conditions[mode].get("reads", [])
            ]
            target_values[mode] = values
            item[mode] = {
                "read_count": len(values),
                "target_mean_mhz": statistics.fmean(values) if values else None,
                "target_out_of_band_rate": (
                    sum(not canonical_pass([value], band) for value in values) / len(values)
                    if values
                    else None
                ),
            }
        item["busy_minus_sham_target_mean_mhz"] = (
            statistics.fmean(target_values["busy"])
            - statistics.fmean(target_values["sham"])
            if target_values["busy"] and target_values["sham"]
            else None
        )
        result.append(item)
    return result


def intervention_evidence_reasons(
    mode: str, target_cpu: int, evidence: Any
) -> list[str]:
    """child の自己申告 status を使わず、保存証拠だけから介入成立を再計算する。"""
    reasons: list[str] = []
    if mode not in {"sham", "busy"}:
        return ["mode_invalid"]
    if not isinstance(evidence, Mapping):
        return ["child_evidence_missing"]
    required_ints = (
        "pid",
        "starttime",
        "start_utime",
        "start_stime",
        "end_utime",
        "end_stime",
        "end_starttime",
        "cpu_ticks_delta",
        "waited_pid",
    )
    for field in required_ints:
        if type(evidence.get(field)) is not int:
            reasons.append(f"{field}_missing_or_invalid")
    if evidence.get("requested_affinity") != [int(target_cpu)]:
        reasons.append("requested_affinity_mismatch")
    if evidence.get("observed_affinity") != [int(target_cpu)]:
        reasons.append("observed_affinity_mismatch")
    if evidence.get("live_after_barrier") is not True:
        reasons.append("not_live_after_barrier")
    if evidence.get("live_before_terminate") is not True:
        reasons.append("not_live_before_terminate")
    if evidence.get("terminate_sent") is not True:
        reasons.append("terminate_not_sent")
    if evidence.get("live_after_wait") is not False:
        reasons.append("live_after_wait")
    if type(evidence.get("pid")) is int and evidence.get("waited_pid") != evidence["pid"]:
        reasons.append("waited_pid_mismatch")
    if (
        type(evidence.get("starttime")) is int
        and type(evidence.get("end_starttime")) is int
        and evidence["starttime"] != evidence["end_starttime"]
    ):
        reasons.append("starttime_identity_mismatch")
    if (
        type(evidence.get("starttime")) is int
        and type(evidence.get("reap_starttime")) is int
        and evidence["starttime"] != evidence["reap_starttime"]
    ):
        reasons.append("reap_starttime_identity_mismatch")
    delta = evidence.get("cpu_ticks_delta")
    if type(delta) is int:
        if delta < 0:
            reasons.append("negative_cpu_tick_delta")
        tick_fields = (
            evidence.get("start_utime"),
            evidence.get("start_stime"),
            evidence.get("end_utime"),
            evidence.get("end_stime"),
        )
        if all(type(value) is int for value in tick_fields):
            arithmetic_delta = (
                int(evidence["end_utime"])
                + int(evidence["end_stime"])
                - int(evidence["start_utime"])
                - int(evidence["start_stime"])
            )
            if delta != arithmetic_delta:
                reasons.append("cpu_tick_delta_arithmetic_mismatch")
        if mode == "busy" and delta < BUSY_MIN_CPU_TICKS:
            reasons.append("busy_cpu_tick_delta_below_threshold")
        if mode == "sham" and delta > SHAM_MAX_CPU_TICKS:
            reasons.append("sham_cpu_tick_delta_above_threshold")
    return reasons


def intervention_status(mode: str, target_cpu: int, evidence: Any) -> str:
    return (
        "VALID"
        if not intervention_evidence_reasons(mode, target_cpu, evidence)
        else "INCONCLUSIVE"
    )


def _flatten_blocks(blocks: Sequence[Sequence[Mapping[str, Any]]]) -> list[Mapping[str, Any]]:
    return [reading for block in blocks for reading in block]


def _validate_block_population(
    reasons: list[str],
    *,
    arm_name: str,
    arm: Any,
    expected_blocks: int,
    expected_per_block: int,
) -> None:
    if not isinstance(arm, Mapping):
        return
    raw_blocks = arm.get("blocks")
    if not isinstance(raw_blocks, list) or len(raw_blocks) != expected_blocks:
        actual = len(raw_blocks) if isinstance(raw_blocks, list) else -1
        reasons.append(f"{arm_name}:block_count:{actual}!={expected_blocks}")
        return
    blocks: list[list[Mapping[str, Any]]] = []
    block_anchors: list[Mapping[str, Any]] = []
    for index, block in enumerate(raw_blocks):
        reads = block.get("reads") if isinstance(block, Mapping) else None
        if not isinstance(reads, list) or len(reads) != expected_per_block:
            actual = len(reads) if isinstance(reads, list) else -1
            reasons.append(
                f"{arm_name}:block_{index}_read_count:{actual}!={expected_per_block}"
            )
            continue
        blocks.append(reads)
        anchor = block.get("discarded_anchor") if isinstance(block, Mapping) else None
        if not isinstance(anchor, Mapping):
            reasons.append(f"{arm_name}:block_{index}_anchor_missing")
        else:
            block_anchors.append(anchor)
    flat = arm.get("reads")
    if len(blocks) == expected_blocks and (
        not isinstance(flat, list) or flat != _flatten_blocks(blocks)
    ):
        reasons.append(f"{arm_name}:flat_reads_block_mismatch")
    if len(block_anchors) == expected_blocks and arm.get("discarded_anchors") != block_anchors:
        reasons.append(f"{arm_name}:flat_anchors_block_mismatch")


def _execution_validity_reasons_impl(
    observations: Mapping[str, Any],
    calibration: Mapping[str, Any],
    environment: Mapping[str, Any],
) -> list[str]:
    """execution_validity の fail-closed 理由を決定的に列挙する。"""
    reasons: list[str] = []
    raw_cpus = environment.get("allocated_cpus", [])
    try:
        cpus = (
            [int(cpu) for cpu in raw_cpus]
            if isinstance(raw_cpus, (list, tuple))
            else []
        )
    except (TypeError, ValueError):
        cpus = []
    if len(cpus) != EXPECTED_CPU_COUNT or len(set(cpus)) != EXPECTED_CPU_COUNT:
        reasons.append("affinity_cpu_count_or_uniqueness_mismatch")
    if cpus != sorted(cpus):
        reasons.append("allocated_cpus_not_sorted")
    if not environment.get("pbs_jobid_present"):
        reasons.append("PBS_JOBID_missing")
    if not environment.get("compute_node_marker"):
        reasons.append("compute_node_marker_false")
    if environment.get("binding_verified") is not True:
        reasons.append("submission_binding_unverified")
    scheduler_binding = environment.get("scheduler_binding")
    if (
        isinstance(scheduler_binding, Mapping)
        and scheduler_binding.get("status") == "mismatch"
    ):
        reasons.append("scheduler_queue_or_project_mismatch")
    if calibration.get("pin_verified") is not True:
        reasons.append("calibration_pin_unverified")
    if not valid_band(calibration.get("band")):
        reasons.append("calibration_band_invalid")
    exceptions = observations.get("exceptions")
    if not isinstance(exceptions, list) or exceptions:
        reasons.append("experiment_exception_present")
    arms = observations.get("arms")
    if not isinstance(arms, Mapping):
        reasons.append("arms_missing")
        arms = {}
    expected_cpu_set = set(cpus)
    for name in ARM_ORDER:
        arm = arms.get(name)
        if not isinstance(arm, Mapping):
            reasons.append(f"{name}:missing")
            continue
        reads = arm.get("reads")
        if not isinstance(reads, list) or len(reads) != EXPECTED_PRIMARY_READS[name]:
            actual = len(reads) if isinstance(reads, list) else -1
            reasons.append(
                f"{name}:primary_read_count:{actual}!={EXPECTED_PRIMARY_READS[name]}"
            )
            reads = reads if isinstance(reads, list) else []
        all_reads = list(reads)
        anchors = arm.get("discarded_anchors", [])
        if isinstance(anchors, list):
            all_reads.extend(anchors)
            ready_ns = arm.get("instrumentation_ready_monotonic_ns")
            for index, anchor in enumerate(anchors):
                try:
                    if int(anchor["started_monotonic_ns"]) < int(ready_ns):
                        reasons.append(f"{name}:anchor_{index}:before_instrumentation")
                except (KeyError, TypeError, ValueError):
                    reasons.append(f"{name}:anchor_{index}:timing_unparseable")
        else:
            reasons.append(f"{name}:anchors_not_list")
        for index, reading in enumerate(all_reads):
            if not isinstance(reading, Mapping):
                reasons.append(f"{name}:read_{index}:not_mapping")
                continue
            try:
                vector = _reading_values(reading)
            except (TypeError, ValueError, KeyError):
                reasons.append(f"{name}:read_{index}:vector_unparseable")
                continue
            if reading.get("parsed_count") != EXPECTED_CPU_COUNT:
                reasons.append(f"{name}:read_{index}:parsed_count_mismatch")
            if set(vector) != expected_cpu_set:
                reasons.append(f"{name}:read_{index}:processor_ids_mismatch")
            if any(not math.isfinite(value) or value <= 0.0 for value in vector.values()):
                reasons.append(f"{name}:read_{index}:mhz_nonfinite_or_nonpositive")
            try:
                affinity = [int(cpu) for cpu in reading.get("affinity_before", [])]
                pin_target = reading.get("pin_target")
                expected_affinity = (
                    cpus if pin_target is None else [int(pin_target)]
                )
                if pin_target is not None and int(pin_target) not in expected_cpu_set:
                    reasons.append(f"{name}:read_{index}:pin_target_unallocated")
                if affinity != expected_affinity:
                    reasons.append(f"{name}:read_{index}:affinity_mismatch")
                if (
                    int(reading["reader_cpu_before"]) not in affinity
                    or int(reading["reader_cpu_after"]) not in affinity
                ):
                    reasons.append(f"{name}:read_{index}:reader_outside_affinity")
            except (TypeError, ValueError, KeyError):
                reasons.append(f"{name}:read_{index}:affinity_unparseable")
        diagnostics = arm.get("diagnostics")
        if (
            not isinstance(diagnostics, Mapping)
            or not isinstance(diagnostics.get("pre"), Mapping)
            or not isinstance(diagnostics.get("post"), Mapping)
            or diagnostics["pre"].get("complete") is not True
            or diagnostics["post"].get("complete") is not True
        ):
            reasons.append(f"{name}:diagnostic_snapshot_incomplete")
        isolation = arm.get("isolation")
        if not isinstance(isolation, Mapping):
            reasons.append(f"{name}:isolation_missing")
        else:
            if isolation.get("visibility_complete") is not True:
                reasons.append(f"{name}:process_visibility_incomplete")
            subwindows = isolation.get("subwindows")
            if not isinstance(subwindows, list) or not subwindows:
                reasons.append(f"{name}:isolation_subwindows_missing")
            attribution = isolation.get("isolation_attribution")
            if attribution == "COMPETITOR":
                reasons.append(f"{name}:competing_process_detected")
            elif attribution not in {"CLEAN", "ATTRIBUTION_UNRESOLVED"}:
                reasons.append(f"{name}:isolation_attribution_invalid")
            if isolation.get("errors"):
                reasons.append(f"{name}:isolation_accounting_error")

    expected_anchor_counts = {
        "A0_quiet_baseline": BASELINE_READS // ALPHA_K,
        "A1_pin_sweep": EXPECTED_CPU_COUNT,
        "A4_migration_description": 1,
        "A3_alpha_quiet": ALPHA_QUIET_BLOCKS,
        "A3_alpha_contention": ALPHA_CONTENTION_BLOCKS,
    }
    for name, expected_count in expected_anchor_counts.items():
        arm = arms.get(name) if isinstance(arms, Mapping) else None
        anchors = arm.get("discarded_anchors") if isinstance(arm, Mapping) else None
        if not isinstance(anchors, list) or len(anchors) != expected_count:
            actual = len(anchors) if isinstance(anchors, list) else -1
            reasons.append(f"{name}:anchor_count:{actual}!={expected_count}")

    a1 = arms.get("A1_pin_sweep") if isinstance(arms, Mapping) else None
    if isinstance(a1, Mapping):
        pin_order = a1.get("pin_order")
        if (
            not isinstance(pin_order, list)
            or len(pin_order) != EXPECTED_CPU_COUNT
            or set(pin_order) != expected_cpu_set
        ):
            reasons.append("A1_pin_sweep:pin_order_not_allocated_permutation")
        try:
            seed = environment["seed"]
            if type(seed) is not int:
                raise TypeError("seed must be int")
            expected_pin_order = list(cpus)
            random.Random(seed).shuffle(expected_pin_order)
        except (KeyError, TypeError, ValueError):
            expected_pin_order = []
            reasons.append("A1_pin_sweep:seed_invalid")
        if pin_order != expected_pin_order:
            reasons.append("A1_pin_sweep:pin_order_seed_mismatch")
        flat_targets: list[int] = []
        for reading in a1.get("reads", []):
            try:
                flat_targets.append(int(reading["pin_target"]))
            except (KeyError, TypeError, ValueError):
                flat_targets.append(-1)
        expected_flat_targets = [
            cpu for cpu in expected_pin_order for _ in range(PIN_REPEATS)
        ]
        if flat_targets != expected_flat_targets:
            reasons.append("A1_pin_sweep:flat_read_order_mismatch")
        by_pin = a1.get("by_pin")
        if not isinstance(by_pin, list) or len(by_pin) != EXPECTED_CPU_COUNT:
            reasons.append("A1_pin_sweep:by_pin_population_invalid")
        else:
            try:
                by_pin_targets = [int(group["pin_target"]) for group in by_pin]
                by_pin_reads = [reading for group in by_pin for reading in group["reads"]]
            except (KeyError, TypeError, ValueError):
                reasons.append("A1_pin_sweep:by_pin_unparseable")
            else:
                if by_pin_targets != expected_pin_order:
                    reasons.append("A1_pin_sweep:by_pin_order_mismatch")
                if by_pin_reads != a1.get("reads"):
                    reasons.append("A1_pin_sweep:by_pin_flat_reads_mismatch")
        primary_by_cpu = {cpu: 0 for cpu in cpus}
        for index, reading in enumerate(a1.get("reads", [])):
            try:
                target = int(reading["pin_target"])
                primary_by_cpu[target] += 1
                if (
                    target not in expected_cpu_set
                    or int(reading["reader_cpu_before"]) != target
                    or int(reading["reader_cpu_after"]) != target
                ):
                    reasons.append(f"A1_pin_sweep:read_{index}:pin_or_reader_mismatch")
            except (KeyError, TypeError, ValueError):
                reasons.append(f"A1_pin_sweep:read_{index}:placement_unparseable")
        if any(primary_by_cpu.get(cpu) != PIN_REPEATS for cpu in cpus):
            reasons.append("A1_pin_sweep:per_cpu_primary_count_mismatch")
        anchor_by_cpu = {cpu: 0 for cpu in cpus}
        anchors = a1.get("discarded_anchors")
        if isinstance(anchors, list):
            for index, reading in enumerate(anchors):
                try:
                    target = int(reading["pin_target"])
                    anchor_by_cpu[target] += 1
                    if (
                        target not in expected_cpu_set
                        or int(reading["reader_cpu_before"]) != target
                        or int(reading["reader_cpu_after"]) != target
                    ):
                        reasons.append(f"A1_pin_sweep:anchor_{index}:placement_mismatch")
                except (KeyError, TypeError, ValueError):
                    reasons.append(f"A1_pin_sweep:anchor_{index}:placement_unparseable")
        if any(anchor_by_cpu.get(cpu) != 1 for cpu in cpus):
            reasons.append("A1_pin_sweep:per_cpu_anchor_count_mismatch")

    _validate_block_population(
        reasons,
        arm_name="A0_quiet_baseline",
        arm=arms.get("A0_quiet_baseline") if isinstance(arms, Mapping) else None,
        expected_blocks=BASELINE_READS // ALPHA_K,
        expected_per_block=ALPHA_K,
    )
    _validate_block_population(
        reasons,
        arm_name="A3_alpha_quiet",
        arm=arms.get("A3_alpha_quiet") if isinstance(arms, Mapping) else None,
        expected_blocks=ALPHA_QUIET_BLOCKS,
        expected_per_block=ALPHA_K,
    )
    _validate_block_population(
        reasons,
        arm_name="A3_alpha_contention",
        arm=arms.get("A3_alpha_contention") if isinstance(arms, Mapping) else None,
        expected_blocks=ALPHA_CONTENTION_BLOCKS,
        expected_per_block=ALPHA_K,
    )

    a2 = arms.get("A2_coresident") if isinstance(arms, Mapping) else None
    a2_pairs = a2.get("pairs") if isinstance(a2, Mapping) else None
    if not isinstance(a2_pairs, list) or len(a2_pairs) != CORESIDENT_TARGETS:
        reasons.append("A2_coresident:pair_count_mismatch")
    else:
        nested_reads: list[Mapping[str, Any]] = []
        targets: list[int] = []
        inconclusive_pairs = 0
        for pair_index, pair in enumerate(a2_pairs):
            if not isinstance(pair, Mapping):
                reasons.append(f"A2_coresident:pair_{pair_index}:not_mapping")
                continue
            try:
                target = int(pair["target_cpu"])
                targets.append(target)
            except (KeyError, TypeError, ValueError):
                reasons.append(f"A2_coresident:pair_{pair_index}:target_invalid")
                continue
            conditions = pair.get("conditions")
            if not isinstance(conditions, list) or len(conditions) != 2:
                reasons.append(f"A2_coresident:pair_{pair_index}:condition_count_mismatch")
                continue
            modes = [
                condition.get("mode")
                for condition in conditions
                if isinstance(condition, Mapping)
            ]
            if len(modes) != 2 or set(modes) != {"busy", "sham"}:
                reasons.append(f"A2_coresident:pair_{pair_index}:condition_modes_mismatch")
            statuses = []
            for condition_index, condition in enumerate(conditions):
                if not isinstance(condition, Mapping):
                    reasons.append(
                        f"A2_coresident:pair_{pair_index}:condition_{condition_index}:not_mapping"
                    )
                    continue
                mode = condition.get("mode")
                reads = condition.get("reads")
                if not isinstance(reads, list) or len(reads) != CORESIDENT_REPEATS:
                    actual = len(reads) if isinstance(reads, list) else -1
                    reasons.append(
                        f"A2_coresident:pair_{pair_index}:{mode}_read_count:"
                        f"{actual}!={CORESIDENT_REPEATS}"
                    )
                else:
                    nested_reads.extend(reads)
                if not isinstance(condition.get("discarded_anchor"), Mapping):
                    reasons.append(
                        f"A2_coresident:pair_{pair_index}:{mode}_anchor_missing"
                    )
                else:
                    try:
                        anchor_ns = int(condition["discarded_anchor"]["started_monotonic_ns"])
                        barrier_ns = int(condition["child"]["barrier_monotonic_ns"])
                        if anchor_ns < barrier_ns:
                            reasons.append(
                                f"A2_coresident:pair_{pair_index}:{mode}_anchor_before_child"
                            )
                    except (KeyError, TypeError, ValueError):
                        reasons.append(
                            f"A2_coresident:pair_{pair_index}:{mode}_anchor_timing_unparseable"
                        )
                cooldown = condition.get("cooldown_after")
                if not isinstance(cooldown, Mapping):
                    reasons.append(
                        f"A2_coresident:pair_{pair_index}:{mode}_cooldown_missing"
                    )
                else:
                    try:
                        if float(cooldown["actual_seconds"]) < COOLDOWN_SECONDS:
                            reasons.append(
                                f"A2_coresident:pair_{pair_index}:{mode}_cooldown_short"
                            )
                    except (KeyError, TypeError, ValueError):
                        reasons.append(
                            f"A2_coresident:pair_{pair_index}:{mode}_cooldown_unparseable"
                        )
                evidence_reasons = intervention_evidence_reasons(
                    mode if isinstance(mode, str) else mode,
                    target,
                    condition.get("child"),
                )
                threshold_reasons = {
                    "busy_cpu_tick_delta_below_threshold",
                    "sham_cpu_tick_delta_above_threshold",
                }
                if any(reason not in threshold_reasons for reason in evidence_reasons):
                    reasons.append(
                        f"A2_coresident:pair_{pair_index}:{mode}_child_evidence_invalid"
                    )
                recomputed = "VALID" if not evidence_reasons else "INCONCLUSIVE"
                statuses.append(recomputed)
                if condition.get("status") != recomputed:
                    reasons.append(
                        f"A2_coresident:pair_{pair_index}:{mode}_status_evidence_mismatch"
                    )
            pair_recomputed = "VALID" if statuses == ["VALID", "VALID"] else "INCONCLUSIVE"
            if pair.get("status") != pair_recomputed:
                reasons.append(f"A2_coresident:pair_{pair_index}:status_evidence_mismatch")
            if pair_recomputed != "VALID":
                inconclusive_pairs += 1
        if len(set(targets)) != CORESIDENT_TARGETS or not set(targets) <= expected_cpu_set:
            reasons.append("A2_coresident:target_population_invalid")
        if isinstance(a2, Mapping) and a2.get("reads") != nested_reads:
            reasons.append("A2_coresident:flat_reads_condition_mismatch")
        if inconclusive_pairs >= INCONCLUSIVE_PAIR_INVALID_MIN:
            reasons.append(
                "A2_coresident:inconclusive_pair_count:"
                f"{inconclusive_pairs}>={INCONCLUSIVE_PAIR_INVALID_MIN}"
            )

    contention = arms.get("A3_alpha_contention") if isinstance(arms, Mapping) else None
    if not isinstance(contention, Mapping):
        reasons.append("A3_alpha_contention:intervention_inconclusive")
    else:
        try:
            busy_cpu = int(contention["busy_cpu"])
        except (KeyError, TypeError, ValueError):
            busy_cpu = -1
        recomputed = intervention_status("busy", busy_cpu, contention.get("child"))
        if contention.get("intervention_status") != recomputed:
            reasons.append("A3_alpha_contention:status_evidence_mismatch")
        if recomputed != "VALID":
            reasons.append("A3_alpha_contention:intervention_inconclusive")
        try:
            barrier_ns = int(contention["child"]["barrier_monotonic_ns"])
            if any(
                int(block["discarded_anchor"]["started_monotonic_ns"]) < barrier_ns
                for block in contention["blocks"]
            ):
                reasons.append("A3_alpha_contention:anchor_before_child")
        except (KeyError, TypeError, ValueError):
            reasons.append("A3_alpha_contention:anchor_timing_unparseable")

    crosscheck = observations.get("parser_crosscheck")
    files = crosscheck.get("files") if isinstance(crosscheck, Mapping) else None
    if (
        not isinstance(crosscheck, Mapping)
        or crosscheck.get("status") != "match"
        or not isinstance(files, list)
        or len(files) != RAW_CPUINFO_LIMIT
        or any(not isinstance(item, Mapping) or item.get("status") != "match" for item in files)
    ):
        reasons.append("parser_crosscheck_incomplete_or_mismatch")
    raw_count = observations.get("raw_cpuinfo_saved_count")
    if raw_count != RAW_CPUINFO_LIMIT:
        reasons.append(f"raw_cpuinfo_saved_count:{raw_count}!={RAW_CPUINFO_LIMIT}")
    return list(dict.fromkeys(reasons))


def execution_validity_reasons(
    observations: Any,
    calibration: Any,
    environment: Any,
) -> list[str]:
    """あらゆる入力を決定的な validity reason へ写す total 関数。"""
    if not isinstance(observations, Mapping):
        return ["observations_not_mapping"]
    if not isinstance(calibration, Mapping):
        return ["calibration_not_mapping"]
    if not isinstance(environment, Mapping):
        return ["environment_not_mapping"]
    try:
        arms = observations.get("arms")
        a2 = arms.get("A2_coresident") if isinstance(arms, Mapping) else None
        pairs = a2.get("pairs") if isinstance(a2, Mapping) else []
        if isinstance(pairs, list):
            for pair in pairs:
                conditions = pair.get("conditions") if isinstance(pair, Mapping) else []
                if isinstance(conditions, list) and any(
                    not isinstance(condition, Mapping)
                    or type(condition.get("mode")) is not str
                    or condition.get("mode") not in {"busy", "sham"}
                    for condition in conditions
                ):
                    return ["A2_coresident:condition_mode_invalid"]
    except Exception:
        return ["A2_coresident:condition_mode_invalid"]
    try:
        return _execution_validity_reasons_impl(
            observations, calibration, environment
        )
    except Exception as exc:
        return [f"validity_structure_invalid:{type(exc).__name__}"]


def evaluate(
    observations: Mapping[str, Any],
    calibration: Mapping[str, Any],
    environment: Mapping[str, Any],
) -> dict[str, Any]:
    """純粋な妥当性・因果判定。INVALID は常に NOT_EVALUATED。"""
    reasons = execution_validity_reasons(observations, calibration, environment)
    band = calibration.get("band")
    try:
        table = (
            evaluate_method_table(observations, band)
            if isinstance(band, Mapping)
            else None
        )
    except Exception as exc:
        table = {"analysis_error": _error(exc)}
        if "counterfactual_method_analysis_failed" not in reasons:
            reasons.append("counterfactual_method_analysis_failed")
    try:
        co_metrics = coresident_metrics(observations, band) if isinstance(band, Mapping) else []
    except Exception as exc:
        co_metrics = [{"analysis_error": _error(exc)}]
        if "coresident_analysis_failed" not in reasons:
            reasons.append("coresident_analysis_failed")
    if reasons:
        return {
            "execution_validity": "INVALID",
            "causal_verdict": "NOT_EVALUATED",
            "validity_reasons": reasons,
            "causal_metrics": None,
            "coresident_metrics": co_metrics,
            "method_table": table,
        }
    cpus = [int(cpu) for cpu in environment["allocated_cpus"]]
    try:
        metrics = causal_metrics(observations, band, cpus)  # type: ignore[arg-type]
    except Exception as exc:
        return {
            "execution_validity": "INVALID",
            "causal_verdict": "NOT_EVALUATED",
            "validity_reasons": ["causal_analysis_failed"],
            "causal_metrics": {"analysis_error": _error(exc)},
            "coresident_metrics": co_metrics,
            "method_table": table,
        }
    confirmed = all(
        metrics[name]
        for name in (
            "pinned_hit_rate_condition",
            "nonpinned_out_of_band_rate_condition",
            "paired_contrast_condition",
        )
    )
    return {
        "execution_validity": "VALID",
        "causal_verdict": "CONFIRMED" if confirmed else "REFUTED",
        "validity_reasons": [],
        "causal_metrics": metrics,
        "coresident_metrics": co_metrics,
        "method_table": table,
    }


def _synthetic_read(
    cpus: Sequence[int],
    vector: Mapping[int, float],
    *,
    pin_target: Optional[int] = None,
    reader_cpu: Optional[int] = None,
) -> dict[str, Any]:
    reader = int(cpus[0] if reader_cpu is None else reader_cpu)
    affinity = [int(pin_target)] if pin_target is not None else list(cpus)
    return {
        "reader_cpu_before": reader,
        "reader_cpu_after": reader,
        "affinity_before": affinity,
        "pin_target": pin_target,
        "started_monotonic_ns": 1,
        "finished_monotonic_ns": 2,
        "mhz_by_cpu": {int(cpu): float(vector[int(cpu)]) for cpu in cpus},
        "parsed_count": len(cpus),
    }


def _synthetic_child(mode: str, target_cpu: int, pid: int) -> dict[str, Any]:
    delta = BUSY_MIN_CPU_TICKS if mode == "busy" else 0
    start_utime = 10
    start_stime = 2
    end_utime = start_utime + delta
    end_stime = start_stime
    reap_utime = end_utime
    reap_stime = end_stime
    return {
        "pid": pid,
        "starttime": 1000 + pid,
        "barrier_monotonic_ns": 0,
        "requested_affinity": [target_cpu],
        "observed_affinity": [target_cpu],
        "fork_cpu_ticks_baseline": 0,
        "start_utime": start_utime,
        "start_stime": start_stime,
        "start_cpu_ticks": start_utime + start_stime,
        "end_utime": end_utime,
        "end_stime": end_stime,
        "end_cpu_ticks": end_utime + end_stime,
        "end_starttime": 1000 + pid,
        "reap_utime": reap_utime,
        "reap_stime": reap_stime,
        "reap_cpu_ticks": reap_utime + reap_stime,
        "reap_starttime": 1000 + pid,
        "lifetime_cpu_ticks": reap_utime + reap_stime,
        "cpu_ticks_delta": delta,
        "live_after_barrier": True,
        "live_before_terminate": True,
        "terminate_sent": True,
        "waited_pid": pid,
        "live_after_wait": False,
    }


def _synthetic_base() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    cpus = list(range(EXPECTED_CPU_COUNT))
    band = calibration_band([100.0] * EXPECTED_CPU_COUNT, 2.0)
    in_band = {cpu: 100.0 for cpu in cpus}
    arms: dict[str, Any] = {}

    def arm(reads: list[dict[str, Any]], **extra: Any) -> dict[str, Any]:
        return {
            "reads": reads,
            "discarded_anchors": [],
            "diagnostics": {"pre": {"complete": True}, "post": {"complete": True}},
            "isolation": {
                "visibility_complete": True,
                "competition_detected": False,
                "isolation_attribution": "CLEAN",
                "subwindows": [
                    {
                        "subwindow_id": "synthetic:clean",
                        "duration_s": 1.0,
                        "unexplained_ticks": 0,
                        "unexplained_ticks_per_second": 0.0,
                        "isolation_attribution": "CLEAN",
                        "residual_ticks_by_cpu": {},
                        "incidental_nonself_cpus": [],
                        "competitor_cpus": [],
                        "errors": [],
                    }
                ],
                "residual_total": 0,
                "self_unattributable_total": 0,
                "window_boundary_timestamps": {
                    "start_process_snapshot_monotonic_ns": 1,
                    "start_cpu_counter_monotonic_ns": 2,
                    "end_cpu_counter_monotonic_ns": 3,
                    "end_process_snapshot_monotonic_ns": 4,
                },
                "window_skew_by_boundary_ns": {"start": 1, "end": 1},
                "window_skew_ns": 2,
                "errors": [],
            },
            "instrumentation_ready_monotonic_ns": 0,
            **extra,
        }

    baseline_blocks = [
        {
            "block": block,
            "discarded_anchor": _synthetic_read(cpus, in_band, reader_cpu=0),
            "reads": [
                _synthetic_read(cpus, in_band, reader_cpu=0)
                for _ in range(ALPHA_K)
            ],
        }
        for block in range(BASELINE_READS // ALPHA_K)
    ]
    arms["A0_quiet_baseline"] = arm(
        [reading for block in baseline_blocks for reading in block["reads"]],
        blocks=baseline_blocks,
        discarded_anchors=[block["discarded_anchor"] for block in baseline_blocks],
    )
    pin_order = list(cpus)
    random.Random(DEFAULT_SEED).shuffle(pin_order)
    pin_reads = []
    by_pin = []
    for target in pin_order:
        vector = dict(in_band)
        vector[target] = 110.0
        group = [
            _synthetic_read(
                cpus, vector, pin_target=target, reader_cpu=target
            )
            for _ in range(PIN_REPEATS)
        ]
        pin_reads.extend(group)
        by_pin.append({"pin_target": target, "reads": group})
    arms["A1_pin_sweep"] = arm(
        pin_reads,
        discarded_anchors=[
            _synthetic_read(cpus, in_band, pin_target=target, reader_cpu=target)
            for target in pin_order
        ],
        pin_order=pin_order,
        by_pin=by_pin,
    )
    arms["A4_migration_description"] = arm(
        [_synthetic_read(cpus, in_band, reader_cpu=0) for _ in range(MIGRATION_READS)],
        discarded_anchors=[_synthetic_read(cpus, in_band, reader_cpu=0)],
        migration_conclusion="NOT_OBSERVED",
        migration_observed=False,
        affinity_not_singleton=False,
    )
    quiet_blocks = [
        {
            "block": block,
            "discarded_anchor": _synthetic_read(cpus, in_band, reader_cpu=0),
            "reads": [
                _synthetic_read(cpus, in_band, reader_cpu=0) for _ in range(ALPHA_K)
            ],
        }
        for block in range(ALPHA_QUIET_BLOCKS)
    ]
    arms["A3_alpha_quiet"] = arm(
        [reading for block in quiet_blocks for reading in block["reads"]],
        blocks=quiet_blocks,
        discarded_anchors=[block["discarded_anchor"] for block in quiet_blocks],
    )
    targets = select_evenly_spaced(cpus[1:], CORESIDENT_TARGETS)
    pairs = []
    a2_reads = []
    next_pid = 100
    for target in targets:
        conditions = []
        for mode in ("sham", "busy"):
            reads = [
                _synthetic_read(cpus, in_band, pin_target=0, reader_cpu=0)
                for _ in range(CORESIDENT_REPEATS)
            ]
            a2_reads.extend(reads)
            child = _synthetic_child(mode, target, next_pid)
            next_pid += 1
            conditions.append(
                {
                    "mode": mode,
                    "reads": reads,
                    "discarded_anchor": _synthetic_read(
                        cpus, in_band, pin_target=0, reader_cpu=0
                    ),
                    "child": child,
                    "status": "VALID",
                    "cooldown_after": {
                        "started_monotonic_ns": 1,
                        "finished_monotonic_ns": 1_000_000_001,
                        "requested_seconds": COOLDOWN_SECONDS,
                        "actual_seconds": COOLDOWN_SECONDS,
                    },
                }
            )
        pairs.append({"target_cpu": target, "status": "VALID", "conditions": conditions})
    arms["A2_coresident"] = arm(a2_reads, pairs=pairs)
    contention_blocks = [
        {
            "block": block,
            "discarded_anchor": _synthetic_read(cpus, in_band, reader_cpu=0),
            "reads": [
                _synthetic_read(cpus, in_band, reader_cpu=0) for _ in range(ALPHA_K)
            ],
        }
        for block in range(ALPHA_CONTENTION_BLOCKS)
    ]
    arms["A3_alpha_contention"] = arm(
        [reading for block in contention_blocks for reading in block["reads"]],
        blocks=contention_blocks,
        discarded_anchors=[block["discarded_anchor"] for block in contention_blocks],
        busy_cpu=targets[len(targets) // 2],
        child=_synthetic_child("busy", targets[len(targets) // 2], next_pid),
        intervention_status="VALID",
    )
    observations = {
        "arms": arms,
        "exceptions": [],
        "parser_crosscheck": {
            "status": "match",
            "files": [
                {"path": f"cpuinfo-raw-{index}.txt", "status": "match"}
                for index in range(1, RAW_CPUINFO_LIMIT + 1)
            ],
        },
        "raw_cpuinfo_saved_count": RAW_CPUINFO_LIMIT,
    }
    calibration = {"pin_verified": True, "band": band}
    environment = {
        "allocated_cpus": cpus,
        "pbs_jobid_present": True,
        "compute_node_marker": True,
        "binding_verified": True,
        "seed": DEFAULT_SEED,
        "scheduler_binding": {"status": "unavailable"},
    }
    return observations, calibration, environment


def synthetic_fixture(name: str) -> dict[str, Any]:
    """self-test と pytest が共有する名前付き合成 fixture を返す。"""
    if name == "in_band_non_nominal":
        band = calibration_band([100.0], 2.0)
        return {"band": band, "samples": [101.0]}
    if name == "alpha_converges":
        band = calibration_band([100.0, 100.0], 2.0)
        vectors = [
            {0: 110.0, 1: 100.0},
            {0: 100.0, 1: 110.0},
            {0: 100.0, 1: 100.0},
            {0: 100.0, 1: 100.0},
            {0: 100.0, 1: 100.0},
        ]
        return {"band": band, "vectors": vectors}
    observations, calibration, environment = _synthetic_base()
    def replace_a1_reads(reads: list[dict[str, Any]]) -> None:
        a1 = observations["arms"]["A1_pin_sweep"]
        a1["reads"] = reads
        a1["by_pin"] = [
            {
                "pin_target": target,
                "reads": reads[index * PIN_REPEATS : (index + 1) * PIN_REPEATS],
            }
            for index, target in enumerate(a1["pin_order"])
        ]

    if name == "no_effect":
        cpus = environment["allocated_cpus"]
        vector = {cpu: 100.0 for cpu in cpus}
        replace_a1_reads([
            _synthetic_read(cpus, vector, pin_target=target, reader_cpu=target)
            for target in observations["arms"]["A1_pin_sweep"]["pin_order"]
            for _ in range(PIN_REPEATS)
        ])
    elif name == "all_out_of_band":
        cpus = environment["allocated_cpus"]
        vector = {cpu: 110.0 for cpu in cpus}
        replace_a1_reads([
            _synthetic_read(cpus, vector, pin_target=target, reader_cpu=target)
            for target in observations["arms"]["A1_pin_sweep"]["pin_order"]
            for _ in range(PIN_REPEATS)
        ])
    elif name == "missing_reads":
        observations["arms"]["A0_quiet_baseline"]["reads"].pop()
    elif name == "primary_count_only":
        observations["arms"]["A4_migration_description"]["reads"].pop()
    elif name == "contention":
        observations["arms"]["A0_quiet_baseline"]["isolation"][
            "competition_detected"
        ] = True
        observations["arms"]["A0_quiet_baseline"]["isolation"][
            "isolation_attribution"
        ] = "COMPETITOR"
    elif name == "paired_contrast_only":
        cpus = environment["allocated_cpus"]
        control_counts = {cpu: 0 for cpu in cpus[:3]}
        reads = []
        for target in observations["arms"]["A1_pin_sweep"]["pin_order"]:
            for repeat in range(PIN_REPEATS):
                vector = {cpu: 100.0 for cpu in cpus}
                if target >= 3 or repeat == 0:
                    vector[target] = 110.0
                for weak_cpu in cpus[:3]:
                    if weak_cpu != target and control_counts[weak_cpu] < 47:
                        vector[weak_cpu] = 110.0
                        control_counts[weak_cpu] += 1
                reads.append(
                    _synthetic_read(
                        cpus, vector, pin_target=target, reader_cpu=target
                    )
                )
        replace_a1_reads(reads)
    elif name == "missing_cpu":
        cpus = environment["allocated_cpus"]
        missing = cpus[-1]
        replacement = cpus[-2]
        for reading in observations["arms"]["A1_pin_sweep"]["reads"]:
            if reading["pin_target"] == missing:
                reading["pin_target"] = replacement
                reading["affinity_before"] = [replacement]
                reading["reader_cpu_before"] = replacement
                reading["reader_cpu_after"] = replacement
    elif name == "child_evidence_missing":
        observations["arms"]["A2_coresident"]["pairs"][0]["conditions"][0][
            "child"
        ] = {}
    elif name == "child_status_mismatch":
        observations["arms"]["A2_coresident"]["pairs"][0]["conditions"][0][
            "status"
        ] = "INCONCLUSIVE"
    elif name == "exception_only":
        observations["exceptions"].append(
            {"stage": "synthetic", "type": "SyntheticException"}
        )
    elif name == "band_missing":
        calibration["band"] = None
    elif name == "parser_unavailable":
        observations["parser_crosscheck"] = {"status": "unavailable", "files": []}
    elif name == "population_missing":
        observations["arms"]["A2_coresident"]["pairs"] = []
    elif name in {"overreject", "confirmed"}:
        pass
    else:
        raise KeyError(name)
    return {
        "observations": observations,
        "calibration": calibration,
        "environment": environment,
    }


SYNTHETIC_FIXTURE_NAMES = (
    "no_effect",
    "all_out_of_band",
    "missing_reads",
    "primary_count_only",
    "in_band_non_nominal",
    "alpha_converges",
    "contention",
    "paired_contrast_only",
    "missing_cpu",
    "child_evidence_missing",
    "child_status_mismatch",
    "exception_only",
    "band_missing",
    "parser_unavailable",
    "population_missing",
    "overreject",
    "confirmed",
)


def run_self_test() -> int:
    """fixture 構築と INVALID implication の smoke。oracle は pytest 側が所有する。"""
    for name in SYNTHETIC_FIXTURE_NAMES:
        fixture = synthetic_fixture(name)
        if {"observations", "calibration", "environment"} <= set(fixture):
            verdict = evaluate(
                fixture["observations"], fixture["calibration"], fixture["environment"]
            )
            assert not (
                verdict["execution_validity"] == "INVALID"
                and verdict["causal_verdict"] != "NOT_EVALUATED"
            )
            print(
                f"PASS {name} {verdict['execution_validity']} "
                f"{verdict['causal_verdict']}"
            )
        else:
            print(f"PASS {name} constructed")
    return 0


def parse_cpuinfo_text(text: str) -> dict[int, float]:
    """processor block ごとの cpu MHz を strict に読む自前 parser。"""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("cpuinfo text is empty")
    blocks = [block for block in re.split(r"\n\s*\n", text.strip()) if block.strip()]
    result: dict[int, float] = {}
    for index, block in enumerate(blocks):
        fields: dict[str, str] = {}
        for line in block.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            if key in fields:
                raise ValueError(f"cpuinfo block {index} duplicates {key!r}")
            fields[key] = value.strip()
        if not fields.get("processor") or not fields.get("cpu MHz"):
            raise ValueError(f"cpuinfo block {index} lacks processor or cpu MHz")
        cpu = int(fields["processor"], 10)
        value = float(fields["cpu MHz"])
        if cpu < 0 or cpu in result or not math.isfinite(value) or value <= 0.0:
            raise ValueError(f"invalid cpuinfo block {index}")
        result[cpu] = value
    if not result:
        raise ValueError("cpuinfo has no processor blocks")
    return result


def _parse_proc_stat_line(text: str) -> dict[str, Any]:
    closing = text.rfind(")")
    if closing < 0:
        raise ValueError("/proc stat comm terminator missing")
    pid_text, comm = text[:closing].split("(", 1)
    fields = text[closing + 2 :].split()
    if len(fields) <= 36:
        raise ValueError("/proc stat has too few fields")
    return {
        "pid": int(pid_text.strip()),
        "comm": comm,
        "state": fields[0],
        "ppid": int(fields[1]),
        "utime": int(fields[11]),
        "stime": int(fields[12]),
        "starttime": int(fields[19]),
        "processor": int(fields[36]),
    }


def _self_processor() -> int:
    return int(
        _parse_proc_stat_line(
            Path("/proc/self/stat").read_text(encoding="utf-8")
        )["processor"]
    )


def collect_cpuinfo_read(
    *,
    pin_target: Optional[int],
    raw_cpuinfo: list[str],
    scheduled_start_ns: Optional[int] = None,
) -> dict[str, Any]:
    """単独 read/anchor。連続系列は ``_collect_series`` で parse を後置する。"""
    raw = _collect_raw_cpuinfo_read(
        pin_target=pin_target,
        scheduled_start_ns=scheduled_start_ns,
        read_interval_ns=None,
    )
    return _materialize_cpuinfo_read(raw, raw_cpuinfo)


def lateness_record(
    scheduled_start_ns: Optional[int], started_ns: int, read_interval_ms: float
) -> dict[str, Any]:
    """scheduled deadline と実 started の差を late threshold とともに返す。"""
    if scheduled_start_ns is None:
        return {"lateness_ns": None, "late": False}
    lateness_ns = int(started_ns) - int(scheduled_start_ns)
    threshold_ns = float(read_interval_ms) * 1_000_000.0 / 2.0
    return {
        "lateness_ns": lateness_ns,
        "late": lateness_ns > threshold_ns,
    }


def _collect_raw_cpuinfo_read(
    *,
    pin_target: Optional[int],
    scheduled_start_ns: Optional[int],
    read_interval_ns: Optional[int],
) -> dict[str, Any]:
    """critical window では stat/affinity、read、時刻だけを採る。"""
    reader_before = _self_processor()
    affinity_before = sorted(os.sched_getaffinity(0))
    started = time.monotonic_ns()
    text = Path("/proc/cpuinfo").read_text(encoding="utf-8")
    finished = time.monotonic_ns()
    reader_after = _self_processor()
    lateness = lateness_record(
        scheduled_start_ns,
        started,
        (read_interval_ns or 0) / 1_000_000.0,
    )
    return {
        "reader_cpu_before": reader_before,
        "reader_cpu_after": reader_after,
        "affinity_before": affinity_before,
        "pin_target": pin_target,
        "scheduled_start_monotonic_ns": scheduled_start_ns,
        "started_monotonic_ns": started,
        "finished_monotonic_ns": finished,
        "duration_ns": finished - started,
        **lateness,
        "_raw_cpuinfo_text": text,
    }


def _materialize_cpuinfo_read(
    raw: Mapping[str, Any], raw_cpuinfo: list[str]
) -> dict[str, Any]:
    text = raw.get("_raw_cpuinfo_text")
    if not isinstance(text, str):
        raise ValueError("raw cpuinfo text missing")
    vector = parse_cpuinfo_text(text)
    if len(raw_cpuinfo) < RAW_CPUINFO_LIMIT:
        raw_cpuinfo.append(text)
    return {
        key: value for key, value in raw.items() if key != "_raw_cpuinfo_text"
    } | {
        "mhz_by_cpu": vector,
        "parsed_count": len(vector),
    }


def _proc_cpu_counters(cpus: Sequence[int]) -> dict[int, list[int]]:
    wanted = set(int(cpu) for cpu in cpus)
    result: dict[int, list[int]] = {}
    text = Path("/proc/stat").read_text(encoding="utf-8")
    for line in text.splitlines():
        fields = line.split()
        if not fields or re.fullmatch(r"cpu[0-9]+", fields[0]) is None:
            continue
        cpu = int(fields[0][3:])
        if cpu in wanted:
            result[cpu] = [int(value) for value in fields[1:]]
    if set(result) != wanted:
        raise ValueError("/proc/stat does not cover allocated CPUs")
    return result


def _counter_delta(
    before: Mapping[int, Sequence[int]], after: Mapping[int, Sequence[int]]
) -> dict[int, list[int]]:
    result = {}
    for cpu in sorted(set(before) & set(after)):
        width = min(len(before[cpu]), len(after[cpu]))
        result[int(cpu)] = [
            int(after[cpu][index]) - int(before[cpu][index]) for index in range(width)
        ]
    return result


def _diagnostic_exception_status(exc: BaseException) -> str:
    if isinstance(exc, FileNotFoundError) or (
        isinstance(exc, OSError) and exc.errno == errno.ENOENT
    ):
        return "absent"
    if isinstance(exc, PermissionError) or (
        isinstance(exc, OSError) and exc.errno in {errno.EACCES, errno.EPERM}
    ):
        return "unreadable"
    return "error"


def diagnostic_status_summary(
    records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """診断 field の四値 status を集計し、error だけを incomplete とする。"""
    counts = {status: 0 for status in DIAGNOSTIC_FIELD_STATUSES}
    counts_by_field: dict[str, dict[str, int]] = {}
    normalized = []
    for source in records:
        record = dict(source)
        status = str(record.get("status", "error"))
        if status not in counts:
            status = "error"
            record["status"] = status
            record["error"] = {
                "type": "InvalidDiagnosticStatus",
                "message": str(source.get("status")),
            }
        field = str(record.get("field") or Path(str(record.get("path", "unknown"))).name)
        record["field"] = field
        counts[status] += 1
        field_counts = counts_by_field.setdefault(
            field, {item: 0 for item in DIAGNOSTIC_FIELD_STATUSES}
        )
        field_counts[status] += 1
        normalized.append(record)
    return {
        "field_statuses": normalized,
        "status_counts": counts,
        "status_counts_by_field": counts_by_field,
        "complete": counts["error"] == 0,
    }


def _read_path_record(path: Path, *, unit: Optional[str] = None) -> dict[str, Any]:
    base = {"path": str(path)}
    if unit is not None:
        base["unit"] = unit
    try:
        value = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        status = _diagnostic_exception_status(exc)
        if status == "absent":
            return {**base, "status": status, "errno": errno.ENOENT}
        if status == "unreadable":
            return {
                **base,
                "status": status,
                "errno": exc.errno if isinstance(exc, OSError) else None,
                "error": _error(exc),
            }
        return {
            **base,
            "status": status,
            "errno": exc.errno if isinstance(exc, OSError) else None,
            "error": _error(exc),
        }
    return {**base, "status": "value", "value": value}


def _interrupt_snapshot() -> dict[str, Any]:
    text = Path("/proc/interrupts").read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines:
        raise ValueError("/proc/interrupts is empty")
    cpu_columns = [int(token[3:]) for token in lines[0].split() if token.startswith("CPU")]
    rows = {}
    for line in lines[1:]:
        if ":" not in line:
            continue
        label, rest = line.split(":", 1)
        tokens = rest.split()
        counts = []
        for token in tokens[: len(cpu_columns)]:
            if token.isdigit():
                counts.append(int(token))
            else:
                break
        if len(counts) == len(cpu_columns):
            rows[label.strip()] = dict(zip(cpu_columns, counts))
    return {"cpu_columns": cpu_columns, "rows": rows}


def _sysfs_diagnostics(cpus: Sequence[int]) -> dict[str, Any]:
    cpu_root = Path("/sys/devices/system/cpu")
    cpuidle = {}
    thermal = {}
    records = []
    for cpu in cpus:
        idle_root = cpu_root / f"cpu{cpu}" / "cpuidle"
        states = []
        for state in sorted(idle_root.glob("state*")):
            states.append(
                {
                    "state": state.name,
                    "usage": _read_path_record(state / "usage", unit="count"),
                    "time": _read_path_record(state / "time", unit="microseconds"),
                }
            )
        cpuidle[int(cpu)] = {
            "path": str(idle_root),
            "status": "value" if idle_root.is_dir() else "absent",
            "states": states,
        }
        throttle = cpu_root / f"cpu{cpu}" / "thermal_throttle"
        thermal[int(cpu)] = {
            name: _read_path_record(throttle / name, unit="count")
            for name in ("core_throttle_count", "package_throttle_count")
        }
    policy_root = cpu_root / "cpufreq"
    policies = []
    fields = (
        "affected_cpus",
        "related_cpus",
        "scaling_driver",
        "scaling_governor",
        "scaling_min_freq",
        "scaling_max_freq",
        "scaling_cur_freq",
        "cpuinfo_min_freq",
        "cpuinfo_max_freq",
        "cpuinfo_cur_freq",
        "bios_limit",
    )
    for policy in sorted(policy_root.glob("policy*")):
        policies.append(
            {
                "policy": policy.name,
                "values": {
                    field: _read_path_record(
                        policy / field,
                        unit=("kHz" if field.endswith("_freq") else None),
                    )
                    for field in fields
                },
            }
        )
    records.extend(
        record
        for idle in cpuidle.values()
        for state in idle["states"]
        for record in (state["usage"], state["time"])
    )
    records.extend(
        {"path": idle["path"], "status": idle["status"]}
        for idle in cpuidle.values()
    )
    records.extend(record for values in thermal.values() for record in values.values())
    records.extend(
        record for policy in policies for record in policy["values"].values()
    )
    boost = _read_path_record(policy_root / "boost", unit="boolean")
    records.append(boost)
    field_records = [
        {**record, "field": Path(str(record["path"])).name}
        for record in records
    ]
    summary = diagnostic_status_summary(field_records)
    return {
        "cpuidle": cpuidle,
        "thermal_throttle": thermal,
        "cpufreq": {"boost": boost, "policies": policies},
        **summary,
        "errors": [
            record for record in summary["field_statuses"]
            if record.get("status") == "error"
        ],
    }


def diagnostic_snapshot(cpus: Sequence[int]) -> dict[str, Any]:
    """arm 境界だけで採る in-process diagnostics。"""
    field_statuses = []
    snapshot: dict[str, Any] = {"monotonic_ns": time.monotonic_ns()}
    try:
        snapshot["proc_stat"] = _proc_cpu_counters(cpus)
        field_statuses.append({"field": "proc_stat", "status": "value"})
    except Exception as exc:
        snapshot["proc_stat"] = None
        field_statuses.append(
            {
                "field": "proc_stat",
                "status": _diagnostic_exception_status(exc),
                "error": _error(exc),
            }
        )
    try:
        snapshot["interrupts"] = _interrupt_snapshot()
        field_statuses.append({"field": "interrupts", "status": "value"})
    except Exception as exc:
        snapshot["interrupts"] = None
        field_statuses.append(
            {
                "field": "interrupts",
                "status": _diagnostic_exception_status(exc),
                "error": _error(exc),
            }
        )
    try:
        sysfs = _sysfs_diagnostics(cpus)
        snapshot.update(sysfs)
        field_statuses.extend(sysfs["field_statuses"])
    except Exception as exc:
        snapshot.update({"cpuidle": None, "thermal_throttle": None, "cpufreq": None})
        field_statuses.append(
            {
                "field": "sysfs",
                "status": _diagnostic_exception_status(exc),
                "error": _error(exc),
            }
        )
    summary = diagnostic_status_summary(field_statuses)
    snapshot.update(summary)
    snapshot["errors"] = [
        record for record in summary["field_statuses"]
        if record.get("status") == "error"
    ]
    return snapshot


def diagnostic_delta(pre: Mapping[str, Any], post: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if isinstance(pre.get("proc_stat"), Mapping) and isinstance(post.get("proc_stat"), Mapping):
        result["proc_stat"] = _counter_delta(pre["proc_stat"], post["proc_stat"])
    else:
        result["proc_stat"] = None
    pre_interrupts = pre.get("interrupts")
    post_interrupts = post.get("interrupts")
    interrupt_delta = {}
    if isinstance(pre_interrupts, Mapping) and isinstance(post_interrupts, Mapping):
        pre_rows = pre_interrupts.get("rows", {})
        post_rows = post_interrupts.get("rows", {})
        if isinstance(pre_rows, Mapping) and isinstance(post_rows, Mapping):
            for label in sorted(set(pre_rows) & set(post_rows)):
                before = pre_rows[label]
                after = post_rows[label]
                if isinstance(before, Mapping) and isinstance(after, Mapping):
                    interrupt_delta[label] = {
                        int(cpu): int(after[cpu]) - int(before[cpu])
                        for cpu in set(before) & set(after)
                    }
    result["interrupts"] = interrupt_delta
    return result


def _proc_mount_visible() -> tuple[bool, list[str]]:
    errors = []
    try:
        mounts = Path("/proc/mounts").read_text(encoding="utf-8")
        proc_lines = [line for line in mounts.splitlines() if line.split()[1] == "/proc"]
        if len(proc_lines) != 1:
            errors.append("proc mount is not unique")
        else:
            options = proc_lines[0].split()[3].split(",")
            hidepid = [item for item in options if item.startswith("hidepid=")]
            if hidepid and hidepid != ["hidepid=0"]:
                errors.append(f"process visibility hidden: {hidepid}")
    except Exception as exc:
        errors.append(f"proc mount visibility error: {type(exc).__name__}: {exc}")
    try:
        if Path("/proc/2/comm").read_text(encoding="utf-8").strip() != "kthreadd":
            errors.append("host PID namespace marker is false")
    except Exception as exc:
        errors.append(f"PID namespace marker unreadable: {type(exc).__name__}: {exc}")
    return not errors, errors


def _process_snapshot() -> tuple[dict[int, dict[str, Any]], list[dict[str, Any]]]:
    processes: dict[int, dict[str, Any]] = {}
    errors = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        try:
            stat = _parse_proc_stat_line((entry / "stat").read_text(encoding="utf-8"))
            uid_line = next(
                line
                for line in (entry / "status").read_text(encoding="utf-8").splitlines()
                if line.startswith("Uid:")
            )
            uid = int(uid_line.split()[1])
            cgroup = (entry / "cgroup").read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            continue
        except (OSError, UnicodeError, ValueError, StopIteration) as exc:
            errors.append({"pid": pid, **_error(exc)})
            continue
        processes[pid] = {
            "utime": int(stat["utime"]),
            "stime": int(stat["stime"]),
            "ticks": int(stat["utime"]) + int(stat["stime"]),
            "starttime": int(stat["starttime"]),
            "ppid": int(stat["ppid"]),
            "public": {
                "pid": pid,
                "uid": uid,
                "comm": stat["comm"],
                "state": stat["state"],
                "processor": stat["processor"],
                "starttime": stat["starttime"],
                "cgroup": cgroup,
            },
        }
    return processes, errors


def _process_identity(record: Mapping[str, Any]) -> tuple[int, int]:
    public = record.get("public") if isinstance(record.get("public"), Mapping) else {}
    return int(public["pid"]), int(record["starttime"])


def _tree_identities(
    processes: Mapping[int, Mapping[str, Any]], root_identity: tuple[int, int]
) -> set[tuple[int, int]]:
    root_pid, root_starttime = root_identity
    root = processes.get(root_pid)
    if not isinstance(root, Mapping) or int(root.get("starttime", -1)) != root_starttime:
        return set()
    pids = {root_pid}
    changed = True
    while changed:
        changed = False
        for pid, record in processes.items():
            if int(record.get("ppid", -1)) in pids and int(pid) not in pids:
                pids.add(int(pid))
                changed = True
    return {_process_identity(processes[pid]) for pid in pids}


def _cpu_counter_components(values: Sequence[int]) -> dict[str, int]:
    """/proc/stat delta を process 帰属可能量と独立診断 field に分ける。"""
    if len(values) < 9:
        raise ValueError("per-CPU /proc/stat counter vector is too short")
    components = {
        "user": int(values[0]),
        "nice": int(values[1]),
        "system": int(values[2]),
        "idle": int(values[3]),
        "iowait": int(values[4]),
        "irq": int(values[5]),
        "softirq": int(values[6]),
        "steal": int(values[7]),
        "guest": int(values[8]),
        "guest_nice": int(values[9]) if len(values) > 9 else 0,
    }
    if any(value < 0 for value in components.values()):
        raise ValueError("per-CPU /proc/stat counter decreased")
    components["process_attributable"] = (
        components["user"]
        + components["nice"]
        + components["system"]
        + components["guest"]
    )
    return components


def analyze_isolation_subwindow(
    subwindow_id: str,
    before_cpu: Mapping[int, Sequence[int]],
    after_cpu: Mapping[int, Sequence[int]],
    before_self: Mapping[tuple[int, int], Mapping[str, Any]],
    after_self: Mapping[tuple[int, int], Mapping[str, Any]],
    allocated_cpus: Sequence[int],
    duration_s: float,
    migration_observed_identities: Sequence[tuple[int, int]] = (),
    signal_cpus: Optional[Sequence[int]] = None,
) -> dict[str, Any]:
    """実時間付き subwindow の unexplained 率を、CPU 横断相殺なしで判定する。"""
    cpus = sorted(set(int(cpu) for cpu in allocated_cpus))
    signal_cpu_set = (
        set(cpus)
        if signal_cpus is None
        else {int(cpu) for cpu in signal_cpus if int(cpu) in cpus}
    )
    errors: list[str] = []
    self_by_cpu = {cpu: 0 for cpu in cpus}
    self_unattributable_processes: list[dict[str, Any]] = []
    affinity_not_singleton_processes: list[dict[str, Any]] = []
    migration_observed_processes: list[dict[str, Any]] = []
    migration_identities = {
        (int(pid), int(starttime))
        for pid, starttime in migration_observed_identities
    }
    self_ticks_total = 0
    self_unattributable_total = 0
    for identity in sorted(set(before_self) | set(after_self)):
        before = before_self.get(identity)
        after = after_self.get(identity)
        if not isinstance(before, Mapping) or not isinstance(after, Mapping):
            errors.append(f"pid_{identity[0]}:self_boundary_lifetime_missing")
            continue
        try:
            before_start = int(before["starttime"])
            after_start = int(after["starttime"])
            before_cpu_id = int(before["processor"])
            after_cpu_id = int(after["processor"])
            delta = int(after["ticks"]) - int(before["ticks"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"pid_{identity[0]}:self_boundary_unparseable")
            continue
        if before_start != identity[1] or after_start != identity[1]:
            errors.append(f"pid_{identity[0]}:self_boundary_starttime_mismatch")
            continue
        if delta < 0:
            errors.append(f"pid_{identity[0]}:self_boundary_negative_tick_delta")
            continue
        self_ticks_total += delta
        before_affinity = before.get("affinity")
        after_affinity = after.get("affinity")
        try:
            before_affinity_ids = sorted(int(cpu) for cpu in before_affinity)
            after_affinity_ids = sorted(int(cpu) for cpu in after_affinity)
        except (TypeError, ValueError):
            before_affinity_ids = []
            after_affinity_ids = []
        stably_singleton = (
            len(before_affinity_ids) == 1
            and before_affinity_ids == after_affinity_ids
            and before_affinity_ids[0] in self_by_cpu
        )
        affinity_not_singleton = not stably_singleton
        migration_observed = (
            identity in migration_identities or before_cpu_id != after_cpu_id
        )
        pinned_cpu = (
            before_affinity_ids[0]
            if stably_singleton and not migration_observed
            else None
        )
        if pinned_cpu is not None:
            self_by_cpu[pinned_cpu] += delta
            continue
        self_unattributable_total += delta
        record = {
            "pid": identity[0],
            "starttime": identity[1],
            "before_cpu": before_cpu_id,
            "after_cpu": after_cpu_id,
            "before_affinity": before_affinity_ids,
            "after_affinity": after_affinity_ids,
            "cpu_ticks_delta": delta,
            "affinity_not_singleton": affinity_not_singleton,
            "migration_observed": migration_observed,
            "reasons": [
                reason
                for reason, present in (
                    ("affinity_not_singleton", affinity_not_singleton),
                    ("migration_observed", migration_observed),
                )
                if present
            ],
        }
        self_unattributable_processes.append(record)
        if affinity_not_singleton:
            affinity_not_singleton_processes.append(record)
        if migration_observed:
            migration_observed_processes.append(record)

    components_by_cpu: dict[int, dict[str, int]] = {}
    process_by_cpu: dict[int, int] = {}
    residual_by_cpu: dict[int, int] = {}
    try:
        counter_delta = _counter_delta(before_cpu, after_cpu)
    except (TypeError, ValueError) as exc:
        errors.append(f"subwindow_counter_delta_invalid:{type(exc).__name__}")
        counter_delta = {}
    for cpu in cpus:
        try:
            components = _cpu_counter_components(counter_delta[cpu])
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"cpu_{cpu}:subwindow_counter_invalid:{type(exc).__name__}")
            continue
        process_ticks = components["process_attributable"]
        components_by_cpu[cpu] = components
        process_by_cpu[cpu] = process_ticks
        residual_by_cpu[cpu] = max(0, process_ticks - self_by_cpu[cpu])

    residual_total = sum(residual_by_cpu.values())
    unexplained = max(0, residual_total - self_unattributable_total)
    try:
        actual_duration_s = float(duration_s)
    except (TypeError, ValueError, OverflowError):
        actual_duration_s = math.nan
    if not math.isfinite(actual_duration_s) or actual_duration_s <= 0.0:
        errors.append("subwindow_duration_invalid")
        unexplained_rate: Optional[float] = None
    else:
        unexplained_rate = unexplained / actual_duration_s
    rate_exceedances: list[dict[str, Any]] = []
    if unexplained >= COMPETITOR_MIN_TICKS and unexplained_rate is not None:
        for cpu, ticks in sorted(residual_by_cpu.items()):
            cpu_rate = ticks / actual_duration_s
            if (
                ticks >= COMPETITOR_MIN_TICKS
                and cpu_rate > COMPETITOR_MAX_TICKS_PER_SECOND
            ):
                rate_exceedances.append(
                    {
                        "cpu": cpu,
                        "unexplained_ticks": ticks,
                        "unexplained_ticks_per_second": cpu_rate,
                        "duration_s": actual_duration_s,
                    }
                )
    signal_rate_exceedances = [
        item for item in rate_exceedances if int(item["cpu"]) in signal_cpu_set
    ]
    non_signal_rate_exceedances = [
        item for item in rate_exceedances if int(item["cpu"]) not in signal_cpu_set
    ]
    competitor = bool(signal_rate_exceedances)
    migration_with_ticks = any(
        int(record["cpu_ticks_delta"]) > 0
        for record in migration_observed_processes
    )
    if competitor:
        attribution = "COMPETITOR"
    elif unexplained > 0 or migration_with_ticks:
        attribution = "ATTRIBUTION_UNRESOLVED"
    else:
        attribution = "CLEAN"
    residual_positive_cpus = sorted(
        cpu for cpu, ticks in residual_by_cpu.items() if ticks > 0
    )
    return {
        "subwindow_id": str(subwindow_id),
        "duration_s": actual_duration_s,
        "isolation_attribution": attribution,
        "affinity_not_singleton": bool(affinity_not_singleton_processes),
        "affinity_not_singleton_self_processes": affinity_not_singleton_processes,
        "migration_observed": bool(migration_observed_processes),
        "migration_observed_self_processes": migration_observed_processes,
        "migration_detected": bool(migration_observed_processes),
        # Compatibility-only detail; canonical reports use the two fields above.
        "migrated_self_processes": self_unattributable_processes,
        "self_ticks_total": self_ticks_total,
        "self_attributed_ticks_by_cpu": self_by_cpu,
        "self_unattributable_total": self_unattributable_total,
        "self_unattributable_processes": self_unattributable_processes,
        "process_attributable_ticks_by_cpu": process_by_cpu,
        "proc_stat_components_by_cpu": components_by_cpu,
        "residual_ticks_by_cpu": residual_by_cpu,
        "residual_total": residual_total,
        "residual_max_ticks": max(residual_by_cpu.values(), default=0),
        "unexplained_ticks": unexplained,
        "unexplained_ticks_per_second": unexplained_rate,
        "signal_cpus": sorted(signal_cpu_set),
        "signal_rate_exceeded_cpus": [
            int(item["cpu"]) for item in signal_rate_exceedances
        ],
        "non_signal_rate_exceeded_cpus": [
            int(item["cpu"]) for item in non_signal_rate_exceedances
        ],
        "non_signal_rate_exceedances": non_signal_rate_exceedances,
        "incidental_nonself_cpus": (
            residual_positive_cpus
            if attribution == "ATTRIBUTION_UNRESOLVED" and unexplained > 0
            else []
        ),
        "competitor_cpus": [
            int(item["cpu"]) for item in signal_rate_exceedances
        ],
        "errors": errors,
    }


def summarize_isolation_subwindows(
    subwindows: Sequence[Mapping[str, Any]], allocated_cpus: Sequence[int]
) -> dict[str, Any]:
    """subwindow 判定を arm 結果へ集約する。arm 合計 tick は判定に使わない。"""
    cpus = sorted(set(int(cpu) for cpu in allocated_cpus))
    maximum = {cpu: 0 for cpu in cpus}
    incidental_cpus: set[int] = set()
    competitor = False
    unresolved = False
    maximum_rate = 0.0
    affinity_not_singleton = False
    migration_observed = False
    errors: list[str] = []
    for index, subwindow in enumerate(subwindows):
        if not isinstance(subwindow, Mapping):
            errors.append(f"subwindow_{index}:not_mapping")
            continue
        for cpu, ticks in subwindow.get("residual_ticks_by_cpu", {}).items():
            cpu_id = int(cpu)
            if cpu_id in maximum:
                maximum[cpu_id] = max(maximum[cpu_id], int(ticks))
        incidental_cpus.update(int(cpu) for cpu in subwindow.get("incidental_nonself_cpus", []))
        attribution = subwindow.get("isolation_attribution")
        competitor = competitor or attribution == "COMPETITOR"
        unresolved = unresolved or attribution == "ATTRIBUTION_UNRESOLVED"
        affinity_not_singleton = (
            affinity_not_singleton
            or subwindow.get("affinity_not_singleton") is True
        )
        migration_observed = (
            migration_observed or subwindow.get("migration_observed") is True
        )
        rate = subwindow.get("unexplained_ticks_per_second")
        if isinstance(rate, (int, float)) and math.isfinite(float(rate)):
            maximum_rate = max(maximum_rate, float(rate))
        errors.extend(
            f"{subwindow.get('subwindow_id', index)}:{item}"
            for item in subwindow.get("errors", [])
        )
    return {
        "isolation_attribution": (
            "COMPETITOR"
            if competitor
            else "ATTRIBUTION_UNRESOLVED"
            if unresolved or not subwindows
            else "CLEAN"
        ),
        "subwindow_evidence_present": bool(subwindows),
        "max_residual_ticks_by_cpu": maximum,
        "max_per_cpu_per_subwindow_residual_ticks": max(maximum.values(), default=0),
        "max_unexplained_ticks_per_second": maximum_rate,
        "affinity_not_singleton": affinity_not_singleton,
        "migration_observed": migration_observed,
        "incidental_nonself_cpus": sorted(incidental_cpus),
        "errors": errors,
    }


def detect_isolation_competition(
    before_processes: Mapping[int, Mapping[str, Any]],
    after_processes: Mapping[int, Mapping[str, Any]],
    before_cpu: Mapping[int, Sequence[int]],
    after_cpu: Mapping[int, Sequence[int]],
    allocated_cpus: Sequence[int],
    allowed_identities: Sequence[tuple[int, int]],
    completed_children: Sequence[Mapping[str, Any]] = (),
    pinned_self_intervals: Sequence[Mapping[str, Any]] = (),
    pinned_identity_cpus: Sequence[tuple[int, int, int]] = (),
    subwindows: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """PID+starttime と CPU 別 residual から単独性を三値判定する。

    全 process snapshot は identity 証拠だけに使い、判定は実時間付き subwindow に限る。
    """
    cpus = set(int(cpu) for cpu in allocated_cpus)
    allowed = {(int(pid), int(start)) for pid, start in allowed_identities}
    nonself_activity: list[dict[str, Any]] = []
    nonself_migrations: list[dict[str, Any]] = []
    snapshot_identity_discontinuities: list[dict[str, Any]] = []
    nonself_by_cpu = {cpu: 0 for cpu in cpus}
    attributed_by_cpu = {cpu: 0 for cpu in cpus}
    attributed_by_identity: dict[tuple[int, int], int] = {}
    self_unattributable_total = 0
    errors: list[str] = []

    def add_nonself(
        record: Mapping[str, Any], delta: int, processors: set[int], *, force: bool = False
    ) -> None:
        if delta <= 0:
            return
        public = record.get("public")
        if not isinstance(public, Mapping):
            errors.append("nonself_process_public_record_missing")
            return
        if force:
            snapshot_identity_discontinuities.append(
                {
                    **dict(public),
                    "cpu_ticks_delta": delta,
                    "attributed_cpu": int(public["processor"]),
                    "observed_processors": sorted(processors),
                    "classification": "snapshot_identity_discontinuity",
                }
            )
            return
        after_cpu = int(public["processor"])
        in_scope = sorted(processors & cpus)
        if len(in_scope) > 1:
            nonself_migrations.append(
                {
                    **dict(public),
                    "cpu_ticks_delta": delta,
                    "attributed_cpu": None,
                    "observed_processors": in_scope,
                    "classification": "attribution_unresolved",
                }
            )
            return
        if after_cpu in cpus:
            target = after_cpu
        elif in_scope:
            target = in_scope[-1]
        else:
            return
        nonself_by_cpu[target] += delta
        nonself_activity.append(
            {
                **dict(public),
                "cpu_ticks_delta": delta,
                "attributed_cpu": target,
                "observed_processors": sorted(processors),
            }
        )

    def add_pinned(identity: tuple[int, int], target: int, delta: int, label: str) -> None:
        if identity not in allowed or target not in cpus or delta < 0:
            errors.append(f"{label}:identity_cpu_or_ticks_invalid")
            return
        attributed_by_cpu[target] += delta
        attributed_by_identity[identity] = attributed_by_identity.get(identity, 0) + delta

    for pid, starttime, target in pinned_identity_cpus:
        identity = (int(pid), int(starttime))
        before = before_processes.get(identity[0])
        after = after_processes.get(identity[0])
        if (
            not isinstance(before, Mapping)
            or not isinstance(after, Mapping)
            or _process_identity(before) != identity
            or _process_identity(after) != identity
        ):
            errors.append(f"pid_{identity[0]}:pinned_identity_lifetime_missing")
            continue
        add_pinned(
            identity,
            int(target),
            int(after["ticks"]) - int(before["ticks"]),
            f"pid_{identity[0]}",
        )

    for interval in pinned_self_intervals:
        try:
            identity = (int(interval["pid"]), int(interval["starttime"]))
            target = int(interval["target_cpu"])
            delta = int(interval["cpu_ticks_delta"])
        except (KeyError, TypeError, ValueError):
            errors.append("pinned_self_interval_unparseable")
            continue
        add_pinned(identity, target, delta, f"pid_{identity[0]}:pinned_interval")

    for child in completed_children:
        try:
            identity = (int(child["pid"]), int(child["starttime"]))
            target = int(child["requested_affinity"][0])
            delta = int(child["lifetime_cpu_ticks"])
            end_starttime = int(child["end_starttime"])
            reap_starttime = int(child["reap_starttime"])
        except (KeyError, TypeError, ValueError, IndexError):
            errors.append("completed_child_evidence_unparseable")
            continue
        if end_starttime != identity[1] or reap_starttime != identity[1]:
            errors.append(f"pid_{identity[0]}:completed_child_starttime_mismatch")
            continue
        add_pinned(identity, target, delta, f"pid_{identity[0]}:completed_child_lifetime")

    for pid in sorted(set(before_processes) | set(after_processes)):
        before = before_processes.get(pid)
        after = after_processes.get(pid)
        before_identity = _process_identity(before) if isinstance(before, Mapping) else None
        after_identity = _process_identity(after) if isinstance(after, Mapping) else None
        same_lifetime = before_identity is not None and before_identity == after_identity
        if same_lifetime:
            delta = int(after["ticks"]) - int(before["ticks"])  # type: ignore[index]
            processors = {
                int(before["public"]["processor"]),  # type: ignore[index]
                int(after["public"]["processor"]),  # type: ignore[index]
            }
            if delta < 0:
                errors.append(f"pid_{pid}:negative_tick_delta")
            elif before_identity in allowed:
                attributed = attributed_by_identity.get(before_identity, 0)
                if attributed > delta:
                    errors.append(f"pid_{pid}:attributed_ticks_exceed_process_delta")
                else:
                    self_unattributable_total += delta - attributed
            elif delta > 0 and processors & cpus:
                add_nonself(after, delta, processors)  # type: ignore[arg-type]
        elif isinstance(after, Mapping):
            processor = int(after["public"]["processor"])
            if after_identity not in allowed and int(after["ticks"]) > 0 and processor in cpus:
                add_nonself(after, int(after["ticks"]), {processor}, force=True)

    counter_delta = _counter_delta(before_cpu, after_cpu)
    components_by_cpu: dict[int, dict[str, int]] = {}
    process_by_cpu: dict[int, int] = {}
    residual_by_cpu: dict[int, int] = {}
    for cpu in sorted(cpus):
        try:
            components = _cpu_counter_components(counter_delta[cpu])
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"cpu_{cpu}:counter_invalid:{type(exc).__name__}")
            continue
        process_ticks = components["process_attributable"]
        components_by_cpu[cpu] = components
        process_by_cpu[cpu] = process_ticks
        residual_by_cpu[cpu] = max(0, process_ticks - attributed_by_cpu[cpu])
    residual_total = sum(residual_by_cpu.values())
    snapshot_nonself_processes = [
        {**item, "classification": "snapshot_identity_evidence"}
        for item in nonself_activity
    ]
    unknown_residual_by_cpu = {
        cpu: max(0, residual_by_cpu.get(cpu, 0) - nonself_by_cpu[cpu])
        for cpu in sorted(cpus)
    }
    unknown_residual_total = sum(unknown_residual_by_cpu.values())
    subwindow_summary = summarize_isolation_subwindows(subwindows, sorted(cpus))
    if subwindow_summary["isolation_attribution"] == "COMPETITOR":
        attribution = "COMPETITOR"
    elif subwindow_summary["isolation_attribution"] == "ATTRIBUTION_UNRESOLVED":
        attribution = "ATTRIBUTION_UNRESOLVED"
    else:
        attribution = "CLEAN"
    competitors = (
        snapshot_identity_discontinuities + snapshot_nonself_processes
        if attribution == "COMPETITOR"
        else []
    )
    return {
        "isolation_attribution": attribution,
        "competition_detected": attribution == "COMPETITOR",
        "competitors": competitors,
        "snapshot_nonself_processes": snapshot_nonself_processes,
        "snapshot_identity_discontinuities": snapshot_identity_discontinuities,
        "nonself_migration_unresolved_processes": nonself_migrations,
        "snapshot_nonself_ticks_by_cpu": {
            cpu: ticks for cpu, ticks in sorted(nonself_by_cpu.items()) if ticks > 0
        },
        "incidental_nonself_cpus": subwindow_summary["incidental_nonself_cpus"],
        "proc_stat_components_by_cpu": components_by_cpu,
        "process_attributable_ticks_by_cpu": process_by_cpu,
        "self_attributed_ticks_by_cpu": attributed_by_cpu,
        "residual_ticks_by_cpu": residual_by_cpu,
        "residual_total": residual_total,
        "self_unattributable_total": self_unattributable_total,
        "unknown_residual_ticks_by_cpu": unknown_residual_by_cpu,
        "unknown_residual_total": unknown_residual_total,
        "subwindows": [dict(item) for item in subwindows],
        "subwindow_evidence_present": subwindow_summary[
            "subwindow_evidence_present"
        ],
        "max_residual_ticks_by_cpu": subwindow_summary["max_residual_ticks_by_cpu"],
        "max_per_cpu_per_subwindow_residual_ticks": subwindow_summary[
            "max_per_cpu_per_subwindow_residual_ticks"
        ],
        "max_unexplained_ticks_per_second": subwindow_summary[
            "max_unexplained_ticks_per_second"
        ],
        "affinity_not_singleton": subwindow_summary["affinity_not_singleton"],
        "migration_observed": subwindow_summary["migration_observed"],
        # Compatibility diagnostic name; no CPU-crossing cancellation is performed.
        "unattributed_ticks_by_cpu": residual_by_cpu,
        "errors": errors + subwindow_summary["errors"],
    }


def _self_tree_stat_snapshot(
    identities: Sequence[tuple[int, int]],
) -> dict[tuple[int, int], dict[str, Any]]:
    """既知の自 tree PID の stat と affinity を subwindow 境界で採る。"""
    snapshot: dict[tuple[int, int], dict[str, Any]] = {}
    for pid, starttime in sorted((int(pid), int(start)) for pid, start in identities):
        stat = _child_stat(pid)
        if int(stat["starttime"]) != starttime:
            raise RuntimeError(f"self tree PID {pid} starttime changed")
        try:
            affinity: Optional[list[int]] = sorted(os.sched_getaffinity(pid))
        except (AttributeError, OSError):
            affinity = None
        snapshot[(pid, starttime)] = {"pid": pid, **stat, "affinity": affinity}
    return snapshot


class IsolationTracker:
    """arm 前後の全 process と、subwindow 境界の自 tree stat で単独性を判定する。

    self の process 窓は CPU counter 窓を包含し、隠れうる量の上界は skew 区間である。
    """

    def __init__(self, cpus: Sequence[int]) -> None:
        self.cpus = set(int(cpu) for cpu in cpus)
        self.active_children: dict[int, tuple[int, int]] = {}
        self.completed_children: list[dict[str, Any]] = []
        self.record: dict[str, Any] = {}
        self._before_processes: dict[int, dict[str, Any]] = {}
        self._before_cpu: dict[int, list[int]] = {}
        self._base_allowed: set[tuple[int, int]] = set()
        self._completed_identities: set[tuple[int, int]] = set()
        self._self_identity: tuple[int, int] = (os.getpid(), -1)
        self.pinned_self_intervals: list[dict[str, Any]] = []
        self.pinned_identity_cpus: list[tuple[int, int, int]] = []
        self._start_process_snapshot_ns: Optional[int] = None
        self._start_cpu_counter_ns: Optional[int] = None
        self.subwindows: list[dict[str, Any]] = []
        self._open_subwindow: Optional[dict[str, Any]] = None

    def allow_child(self, pid: int, evidence: Mapping[str, Any]) -> None:
        self.active_children[int(pid)] = (int(pid), int(evidence["starttime"]))

    def disallow_child(self, pid: int, evidence: Mapping[str, Any]) -> None:
        identity = self.active_children.pop(int(pid), None)
        if identity is not None:
            self._completed_identities.add(identity)
        self.completed_children.append(dict(evidence))

    def record_pinned_self_interval(
        self, target_cpu: int, start: Mapping[str, Any], end: Mapping[str, Any]
    ) -> None:
        """A1 reader の PID+starttime 束縛 tick を pin 先 CPU へ記録する。"""
        if int(start["starttime"]) != int(end["starttime"]):
            raise RuntimeError("self starttime changed during pinned interval")
        if int(start["starttime"]) != self._self_identity[1]:
            raise RuntimeError("pinned interval does not match tracked self identity")
        self.pinned_self_intervals.append(
            {
                "pid": self._self_identity[0],
                "starttime": self._self_identity[1],
                "target_cpu": int(target_cpu),
                "cpu_ticks_delta": int(end["ticks"]) - int(start["ticks"]),
            }
        )

    def start_subwindow(self, subwindow_id: str) -> None:
        """anchor の直前に CPU counter と自 tree stat の境界サンプルを採る。"""
        if self._open_subwindow is not None:
            raise RuntimeError("isolation subwindow already open")
        identities = self._base_allowed | set(self.active_children.values())
        self_snapshot = _self_tree_stat_snapshot(sorted(identities))
        self_snapshot_ns = time.monotonic_ns()
        cpu_snapshot = _proc_cpu_counters(sorted(self.cpus))
        cpu_snapshot_ns = time.monotonic_ns()
        self._open_subwindow = {
            "subwindow_id": str(subwindow_id),
            "identities": sorted(identities),
            "before_self": self_snapshot,
            "before_cpu": cpu_snapshot,
            "start_self_snapshot_monotonic_ns": self_snapshot_ns,
            "start_cpu_snapshot_monotonic_ns": cpu_snapshot_ns,
        }

    def finish_subwindow(
        self,
        subwindow_id: str,
        readings: Sequence[Mapping[str, Any]] = (),
        additional_signal_cpus: Sequence[int] = (),
    ) -> dict[str, Any]:
        """最後の primary read 後に境界サンプルを採り、subwindow を閉じる。"""
        opened = self._open_subwindow
        if opened is None or opened.get("subwindow_id") != str(subwindow_id):
            raise RuntimeError("isolation subwindow close mismatch")
        cpu_snapshot = _proc_cpu_counters(sorted(self.cpus))
        cpu_snapshot_ns = time.monotonic_ns()
        self_snapshot = _self_tree_stat_snapshot(opened["identities"])
        self_snapshot_ns = time.monotonic_ns()
        duration_ns = cpu_snapshot_ns - opened["start_cpu_snapshot_monotonic_ns"]
        observed_reader_cpus: list[int] = []
        signal_cpus = {int(cpu) for cpu in additional_signal_cpus}
        reader_transition = False
        reader_observation_errors = 0
        for reading in readings:
            try:
                before_reader = int(reading["reader_cpu_before"])
                after_reader = int(reading["reader_cpu_after"])
            except (KeyError, TypeError, ValueError):
                reader_observation_errors += 1
                continue
            observed_reader_cpus.extend((before_reader, after_reader))
            signal_cpus.update((before_reader, after_reader))
            pin_target = reading.get("pin_target")
            if pin_target is not None:
                try:
                    signal_cpus.add(int(pin_target))
                except (TypeError, ValueError):
                    reader_observation_errors += 1
            reader_transition = reader_transition or before_reader != after_reader
        reader_migration = reader_transition or len(set(observed_reader_cpus)) > 1
        analysis = analyze_isolation_subwindow(
            str(subwindow_id),
            opened["before_cpu"],
            cpu_snapshot,
            opened["before_self"],
            self_snapshot,
            sorted(self.cpus),
            duration_ns / 1e9,
            [self._self_identity] if reader_migration else [],
            sorted(signal_cpus),
        )
        analysis["duration_ns"] = duration_ns
        analysis["errors"].extend(
            "reader_cpu_observation_unparseable"
            for _ in range(reader_observation_errors)
        )
        analysis["observed_reader_cpus"] = sorted(set(observed_reader_cpus))
        analysis["observed_reader_migration"] = reader_migration
        analysis["boundary_timestamps"] = {
            "start_self_snapshot_monotonic_ns": opened[
                "start_self_snapshot_monotonic_ns"
            ],
            "start_cpu_snapshot_monotonic_ns": opened[
                "start_cpu_snapshot_monotonic_ns"
            ],
            "end_cpu_snapshot_monotonic_ns": cpu_snapshot_ns,
            "end_self_snapshot_monotonic_ns": self_snapshot_ns,
        }
        analysis["boundary_skew_ns"] = (
            opened["start_cpu_snapshot_monotonic_ns"]
            - opened["start_self_snapshot_monotonic_ns"]
            + self_snapshot_ns
            - cpu_snapshot_ns
        )
        self.subwindows.append(analysis)
        self._open_subwindow = None
        return analysis

    def start(self) -> None:
        visible, visibility_errors = _proc_mount_visible()
        processes, errors = _process_snapshot()
        process_snapshot_ns = time.monotonic_ns()
        cpu = _proc_cpu_counters(sorted(self.cpus))
        cpu_counter_ns = time.monotonic_ns()
        self_record = processes.get(os.getpid())
        if not isinstance(self_record, Mapping):
            errors.append({"pid": os.getpid(), "type": "SelfProcessMissing"})
            self_identity = (os.getpid(), -1)
        else:
            self_identity = _process_identity(self_record)
        self._self_identity = self_identity
        self._base_allowed = _tree_identities(processes, self_identity)
        try:
            affinity = sorted(os.sched_getaffinity(0))
        except (AttributeError, OSError):
            affinity = []
        if len(affinity) == 1:
            self.pinned_identity_cpus = [
                (self_identity[0], self_identity[1], affinity[0])
            ]
        self._before_processes = processes
        self._before_cpu = cpu
        self._start_process_snapshot_ns = process_snapshot_ns
        self._start_cpu_counter_ns = cpu_counter_ns
        self.record = {
            "process_information_trust": "untrusted data; argv and env are not recorded",
            "visibility_complete": visible and not errors,
            "visibility_errors": visibility_errors + errors,
            "boundary_processes": {
                "pre": [
                    item["public"]
                    for item in processes.values()
                    if int(item["public"]["processor"]) in self.cpus
                ]
            },
            "self_identity": list(self_identity),
        }

    def finish(self) -> dict[str, Any]:
        if self._open_subwindow is not None:
            raise RuntimeError("isolation subwindow left open")
        cpu = _proc_cpu_counters(sorted(self.cpus))
        cpu_counter_ns = time.monotonic_ns()
        processes, errors = _process_snapshot()
        process_snapshot_ns = time.monotonic_ns()
        if errors:
            self.record["visibility_complete"] = False
            self.record["visibility_errors"].extend(errors)
        self.record["boundary_processes"]["post"] = [
            item["public"]
            for item in processes.values()
            if int(item["public"]["processor"]) in self.cpus
        ]
        if self._start_process_snapshot_ns is None or self._start_cpu_counter_ns is None:
            raise RuntimeError("isolation tracker start timestamps are missing")
        start_skew_ns = self._start_cpu_counter_ns - self._start_process_snapshot_ns
        end_skew_ns = process_snapshot_ns - cpu_counter_ns
        if start_skew_ns < 0 or end_skew_ns < 0:
            raise RuntimeError("isolation window timestamps are not monotonic")
        self.record["window_boundary_timestamps"] = {
            "start_process_snapshot_monotonic_ns": self._start_process_snapshot_ns,
            "start_cpu_counter_monotonic_ns": self._start_cpu_counter_ns,
            "end_cpu_counter_monotonic_ns": cpu_counter_ns,
            "end_process_snapshot_monotonic_ns": process_snapshot_ns,
        }
        self.record["window_skew_by_boundary_ns"] = {
            "start": start_skew_ns,
            "end": end_skew_ns,
        }
        self.record["window_skew_ns"] = start_skew_ns + end_skew_ns
        allowed = (
            self._base_allowed
            | self._completed_identities
            | set(self.active_children.values())
        )
        analysis = detect_isolation_competition(
            self._before_processes,
            processes,
            self._before_cpu,
            cpu,
            sorted(self.cpus),
            sorted(allowed),
            self.completed_children,
            self.pinned_self_intervals,
            self.pinned_identity_cpus,
            self.subwindows,
        )
        self.record.update(analysis)
        return self.record


def isolation_allows_later_arms(isolation: Any) -> bool:
    """COMPETITOR だけが後続 arm を抑止し、UNRESOLVED は継続を許す。"""
    return (
        isinstance(isolation, Mapping)
        and isolation.get("isolation_attribution")
        in {"CLEAN", "ATTRIBUTION_UNRESOLVED"}
    )


def _collect_series(
    count: int,
    *,
    pin_target: Optional[int],
    interval_s: float,
    raw_cpuinfo: list[str],
    delay_before_first: bool = False,
    first_deadline_ns: Optional[int] = None,
    hard_deadline_ns: Optional[int] = None,
) -> list[dict[str, Any]]:
    interval_ns = int(interval_s * 1_000_000_000)
    if first_deadline_ns is None:
        first_deadline_ns = time.monotonic_ns() + (interval_ns if delay_before_first else 0)
    raw_reads = []
    for index in range(count):
        scheduled = first_deadline_ns + index * interval_ns
        if hard_deadline_ns is not None and scheduled >= hard_deadline_ns:
            raise TimeoutError("hard measurement deadline reached before scheduled read")
        remaining_ns = scheduled - time.monotonic_ns()
        if remaining_ns > 0:
            time.sleep(remaining_ns / 1_000_000_000)
        if hard_deadline_ns is not None and time.monotonic_ns() >= hard_deadline_ns:
            raise TimeoutError("hard measurement deadline reached")
        raw_reads.append(
            _collect_raw_cpuinfo_read(
                pin_target=pin_target,
                scheduled_start_ns=scheduled,
                read_interval_ns=interval_ns,
            )
        )
    return [_materialize_cpuinfo_read(raw, raw_cpuinfo) for raw in raw_reads]


def _child_stat(pid: int) -> dict[str, Any]:
    stat = _parse_proc_stat_line(Path(f"/proc/{pid}/stat").read_text(encoding="utf-8"))
    return {
        "utime": int(stat["utime"]),
        "stime": int(stat["stime"]),
        "ticks": int(stat["utime"]) + int(stat["stime"]),
        "starttime": int(stat["starttime"]),
        "state": stat["state"],
        "processor": stat["processor"],
    }


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class ChildRegistry:
    """全出口の finally から bounded 回収する outer-scope registry。"""

    def __init__(self) -> None:
        self.active: dict[int, dict[str, Any]] = {}
        self.cleanup_records: list[dict[str, Any]] = []

    def register(self, pid: int, evidence: dict[str, Any]) -> None:
        self.active[int(pid)] = evidence

    def completed(self, pid: int) -> None:
        self.active.pop(int(pid), None)

    def recover_all(self) -> list[dict[str, Any]]:
        for pid, evidence in list(self.active.items()):
            record = {"pid": pid, "reason": "outer_finally_recovery"}
            try:
                _stop_child(pid, evidence)
                record["evidence"] = dict(evidence)
            except Exception as exc:
                record["error"] = _error(exc)
            record["live_after_recovery"] = _pid_alive(pid)
            self.cleanup_records.append(record)
            self.active.pop(pid, None)
        return list(self.cleanup_records)


def _start_child(
    mode: str, cpu: int, registry: ChildRegistry
) -> tuple[int, dict[str, Any]]:
    if mode not in {"sham", "busy"}:
        raise ValueError(mode)
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        try:
            os.close(read_fd)
            os.sched_setaffinity(0, {int(cpu)})
            os.write(write_fd, b"R")
            os.close(write_fd)
            if mode == "sham":
                while True:
                    time.sleep(3600.0)
            value = 1
            while True:
                value = (value * 1103515245 + 12345) & 0x7FFFFFFF
        except BaseException:
            os._exit(111)
    os.close(write_fd)
    evidence: dict[str, Any] = {
        "pid": pid,
        "requested_affinity": [int(cpu)],
        # Linux task CPU counters begin at zero at fork; the absolute zombie
        # snapshot therefore covers fork through the instant before reap.
        "fork_cpu_ticks_baseline": 0,
    }
    registry.register(pid, evidence)
    ready, _, _ = select.select([read_fd], [], [], 5.0)
    payload = os.read(read_fd, 1) if ready else b""
    os.close(read_fd)
    if payload != b"R":
        _stop_child(pid, evidence)
        registry.completed(pid)
        raise RuntimeError(f"{mode} child failed readiness barrier")
    affinity = sorted(os.sched_getaffinity(pid))
    start = _child_stat(pid)
    evidence.update(
        {
            "starttime": start["starttime"],
            "observed_affinity": affinity,
            "start_utime": start["utime"],
            "start_stime": start["stime"],
            "start_cpu_ticks": start["ticks"],
            "start_state": start["state"],
            "start_processor": start["processor"],
            "live_after_barrier": _pid_alive(pid),
            "barrier_monotonic_ns": time.monotonic_ns(),
        }
    )
    return pid, evidence


def _bounded_waitid_no_reap(pid: int, timeout_s: float) -> bool:
    """終了を bounded wait し、zombie の /proc stat を読むまで reap しない。"""
    deadline = time.monotonic() + timeout_s
    while True:
        try:
            result = os.waitid(
                os.P_PID,
                pid,
                os.WEXITED | os.WNOHANG | os.WNOWAIT,
            )
        except ChildProcessError:
            return False
        if result is not None and result.si_pid == pid:
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.01)


def _stop_child(pid: int, evidence: dict[str, Any]) -> None:
    try:
        end = _child_stat(pid)
        start_ticks = evidence.get("start_cpu_ticks")
        evidence.update(
            {
                "end_cpu_ticks": end["ticks"],
                "end_utime": end["utime"],
                "end_stime": end["stime"],
                "end_starttime": end["starttime"],
                "cpu_ticks_delta": (
                    end["ticks"] - start_ticks if type(start_ticks) is int else None
                ),
                "end_state": end["state"],
                "end_processor": end["processor"],
                "live_before_terminate": end["state"] != "Z" and _pid_alive(pid),
            }
        )
    except Exception as exc:
        evidence.update(
            {
                "end_error": _error(exc),
                "end_utime": None,
                "end_stime": None,
                "end_cpu_ticks": None,
                "end_starttime": None,
                "cpu_ticks_delta": None,
                "live_before_terminate": False,
            }
        )
    try:
        os.kill(pid, signal.SIGTERM)
        evidence["terminate_sent"] = True
    except ProcessLookupError:
        evidence["terminate_sent"] = False
    exited = _bounded_waitid_no_reap(pid, CHILD_TERM_TIMEOUT_SECONDS)
    evidence["term_wait_timed_out"] = not exited
    if not exited:
        try:
            os.kill(pid, signal.SIGKILL)
            evidence["sigkill_sent"] = True
        except ProcessLookupError:
            evidence["sigkill_sent"] = False
        exited = _bounded_waitid_no_reap(pid, CHILD_KILL_TIMEOUT_SECONDS)
        evidence["kill_wait_timed_out"] = not exited
    waited_pid: Optional[int] = None
    status: Optional[int] = None
    if exited:
        try:
            reap = _child_stat(pid)
            baseline = evidence.get("fork_cpu_ticks_baseline")
            evidence.update(
                {
                    "reap_utime": reap["utime"],
                    "reap_stime": reap["stime"],
                    "reap_cpu_ticks": reap["ticks"],
                    "reap_starttime": reap["starttime"],
                    "reap_state": reap["state"],
                    "reap_processor": reap["processor"],
                    "lifetime_cpu_ticks": (
                        reap["ticks"] - baseline if type(baseline) is int else None
                    ),
                }
            )
        except Exception as exc:
            evidence.update(
                {
                    "reap_error": _error(exc),
                    "reap_utime": None,
                    "reap_stime": None,
                    "reap_cpu_ticks": None,
                    "reap_starttime": None,
                    "lifetime_cpu_ticks": None,
                }
            )
        try:
            waited_pid, status = os.waitpid(pid, 0)
        except ChildProcessError:
            waited_pid = pid
    evidence.update(
        {
            "waited_pid": waited_pid,
            "wait_status": status,
            "live_after_wait": _pid_alive(pid),
        }
    )


def _run_child_condition(
    mode: str,
    cpu: int,
    reader_cpu: int,
    *,
    count: int,
    interval_s: float,
    raw_cpuinfo: list[str],
    tracker: IsolationTracker,
    registry: ChildRegistry,
    hard_deadline_ns: Optional[int],
) -> dict[str, Any]:
    pid, evidence = _start_child(mode, cpu, registry)
    tracker.allow_child(pid, evidence)
    reads: list[dict[str, Any]] = []
    anchor: Optional[dict[str, Any]] = None
    subwindow_id = f"A2:target:{cpu}:mode:{mode}"
    try:
        tracker.start_subwindow(subwindow_id)
        try:
            anchor = collect_cpuinfo_read(pin_target=reader_cpu, raw_cpuinfo=raw_cpuinfo)
            reads = _collect_series(
                count,
                pin_target=reader_cpu,
                interval_s=interval_s,
                raw_cpuinfo=raw_cpuinfo,
                first_deadline_ns=anchor["started_monotonic_ns"] + int(interval_s * 1e9),
                hard_deadline_ns=hard_deadline_ns,
            )
        finally:
            tracker.finish_subwindow(
                subwindow_id, reads, additional_signal_cpus=[cpu]
            )
    finally:
        _stop_child(pid, evidence)
        registry.completed(pid)
        tracker.disallow_child(pid, evidence)
    for reading in reads:
        reading["isolation_subwindow_id"] = subwindow_id
    status = intervention_status(mode, cpu, evidence)
    return {
        "mode": mode,
        "reads": reads,
        "discarded_anchor": anchor,
        "child": evidence,
        "status": status,
    }


def _execute_arm(
    name: str,
    cpus: Sequence[int],
    primary_fn: Any,
    *,
    setup_fn: Optional[Any] = None,
) -> dict[str, Any]:
    arm_started_ns = time.monotonic_ns()
    pre = diagnostic_snapshot(cpus)
    tracker = IsolationTracker(cpus)
    tracker.start()
    instrumentation_ready_ns = time.monotonic_ns()
    discarded: list[dict[str, Any]] = []
    primary: dict[str, Any] = {}
    primary_error: Optional[dict[str, Any]] = None
    try:
        discarded = setup_fn() if setup_fn is not None else []
        primary = primary_fn(tracker)
    except Exception as exc:
        primary_error = _error(exc)
    try:
        isolation = tracker.finish()
    except Exception as exc:
        isolation = {
            **tracker.record,
            "visibility_complete": False,
            "competition_detected": True,
            "finish_error": _error(exc),
        }
    post = diagnostic_snapshot(cpus)
    primary_anchors = primary.pop("discarded_anchors", [])
    if isinstance(primary_anchors, list):
        discarded.extend(primary_anchors)
    arm = {
        "name": name,
        "discarded_anchors": discarded,
        "started_monotonic_ns": arm_started_ns,
        "finished_monotonic_ns": time.monotonic_ns(),
        "instrumentation_ready_monotonic_ns": instrumentation_ready_ns,
        "diagnostics": {
            "pre": pre,
            "post": post,
            "delta": diagnostic_delta(pre, post),
        },
        "isolation": isolation,
        **primary,
    }
    arm["duration_ns"] = arm["finished_monotonic_ns"] - arm_started_ns
    if primary_error is not None:
        arm["error"] = primary_error
    return arm


def _normalize_jobid(raw: str) -> str:
    if _PBS_JOBID_RE.fullmatch(raw) is None:
        raise ValueError("PBS_JOBID has unsafe characters")
    normalized = raw.replace(":", "_")
    if normalized in {".", ".."} or "/" in normalized:
        raise ValueError("normalized PBS_JOBID is unsafe")
    return normalized


def _parse_marker(path: Path, raw_jobid: str) -> dict[str, Any]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        fields = dict(line.split("=", 1) for line in lines if "=" in line)
    except Exception as exc:
        return {"valid": False, "error": _error(exc)}
    hostname = fields.get("hostname", "")
    valid = (
        fields.get("PBS_JOBID") == raw_jobid
        and fields.get("compute_node_marker") == "true"
        and re.fullmatch(r"bnode[0-9]+", hostname) is not None
    )
    return {"valid": valid, "fields": fields}


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _load_calibration(
    repo_root: Path, expected_submission_sha256: str
) -> dict[str, Any]:
    orchestrator = repo_root / "orchestrator"
    sys.path.insert(0, str(orchestrator))
    try:
        from campaign import env_contract

        contract = env_contract.lookup("pegasus")
    finally:
        if sys.path and sys.path[0] == str(orchestrator):
            sys.path.pop(0)
    relative = Path(contract.calibration_ref.path)
    if relative.is_absolute():
        raise ValueError("calibration path must be repository-relative")
    root = repo_root.resolve(strict=True)
    path = (root / relative).resolve(strict=True)
    path.relative_to(root)
    raw = path.read_bytes()
    actual = _sha256_bytes(raw)
    expected = contract.calibration_ref.sha256
    submission_expected = expected_submission_sha256.lower()
    if actual != expected or actual != submission_expected:
        return {
            "pin_verified": False,
            "path": str(relative),
            "expected_sha256": expected,
            "submission_expected_sha256": submission_expected,
            "actual_sha256": actual,
            "band": None,
        }
    parsed = json.loads(raw)
    clock = parsed["attestation_profile"]["effective_clock"]
    band = calibration_band(clock["samples_mhz"], clock["tolerance_pct"])
    return {
        "pin_verified": True,
        "path": str(relative),
        "expected_sha256": expected,
        "submission_expected_sha256": submission_expected,
        "actual_sha256": actual,
        "expected_samples_count": len(clock["samples_mhz"]),
        "band": band,
    }


def _git_provenance(repo_root: Path, output_dir: Path) -> dict[str, Any]:
    """probe 自身の output directory だけを除外した repository 状態を返す。"""
    head = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    ).stdout.strip()
    status = subprocess.run(
        [
            "git", "-C", str(repo_root), "status", "--porcelain=v1", "-z",
            "--untracked-files=all",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout
    output_relative = str(output_dir.relative_to(repo_root))
    dirty_entries = []
    for entry in status.split("\0"):
        if not entry:
            continue
        path = entry[3:] if len(entry) >= 4 else entry
        if path == output_relative or path.startswith(output_relative + "/"):
            continue
        dirty_entries.append(entry)
    return {
        "repo_commit": head,
        "repo_dirty": bool(dirty_entries),
        "repo_dirty_entries_excluding_probe_output": dirty_entries,
        "repo_dirty_excluded_path": output_relative,
    }


def _submission_binding(
    repo_root: Path,
    calibration: Mapping[str, Any],
    *,
    expect_head: str,
    expect_driver_sha256: str,
    expect_pbs_sha256: str,
    expect_env_attestation_sha256: str,
) -> dict[str, Any]:
    driver_path = Path(__file__).resolve(strict=True)
    pbs_path = repo_root / "tools/pegasus/probes/t419_probe_causality.pbs"
    calibration_relative = calibration.get("path")
    if not isinstance(calibration_relative, str):
        raise ValueError("calibration path unavailable for binding")
    calibration_path = repo_root / calibration_relative
    head = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    ).stdout.strip().lower()
    related = [
        str(driver_path.relative_to(repo_root)),
        str(pbs_path.relative_to(repo_root)),
        calibration_relative,
        "orchestrator/campaign/env_contract.py",
        "orchestrator/campaign/env_attestation.py",
    ]
    dirty = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain", "--", *related],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.splitlines()
    observed_driver = _sha256_path(driver_path)
    observed_pbs = _sha256_path(pbs_path)
    observed_env_attestation = _sha256_path(
        repo_root / "orchestrator/campaign/env_attestation.py"
    )
    matched = (
        head == expect_head.lower()
        and observed_driver == expect_driver_sha256.lower()
        and observed_pbs == expect_pbs_sha256.lower()
        and observed_env_attestation == expect_env_attestation_sha256.lower()
        and calibration.get("pin_verified") is True
        and not dirty
    )
    return {
        "attempted": True,
        "matched": matched,
        "expected_head": expect_head.lower(),
        "head": head,
        "expected_driver_sha256": expect_driver_sha256.lower(),
        "driver_sha256": observed_driver,
        "expected_pbs_sha256": expect_pbs_sha256.lower(),
        "pbs_sha256": observed_pbs,
        "expected_calibration_sha256": calibration.get(
            "submission_expected_sha256"
        ),
        "calibration_sha256": calibration.get("actual_sha256"),
        "expected_env_attestation_sha256": expect_env_attestation_sha256.lower(),
        "env_contract_sha256": _sha256_path(
            repo_root / "orchestrator/campaign/env_contract.py"
        ),
        "env_attestation_sha256": observed_env_attestation,
        "related_paths": related,
        "related_dirty_entries": dirty,
    }


def _qstat_record(raw_jobid: str) -> dict[str, Any]:
    normalized = raw_jobid[2:] if raw_jobid.startswith("0:") else raw_jobid
    try:
        completed = subprocess.run(
            ["qstat", "-f", normalized],
            capture_output=True,
            text=True,
            timeout=20,
        )
    except Exception as exc:
        return {
            "attempted": True,
            "untrusted_data": True,
            "jobid": normalized,
            "error": _error(exc),
        }
    return {
        "attempted": True,
        "untrusted_data": True,
        "jobid": normalized,
        "rc": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _scheduler_environment_binding(
    expected_queue: Optional[str], expected_project: Optional[str]
) -> dict[str, Any]:
    """scheduler 由来 env があれば submission queue/project と照合する。"""
    fields = {
        "queue": (expected_queue, ("PBS_QUEUE", "PBS_O_QUEUE")),
        "project": (
            expected_project,
            ("PBS_PROJECT", "PBS_ACCOUNT", "PBS_O_PROJECT", "PBS_O_ACCOUNT"),
        ),
    }
    records: dict[str, Any] = {}
    any_mismatch = False
    any_available = False
    for name, (expected, candidates) in fields.items():
        observed_source = next(
            (key for key in candidates if os.environ.get(key)), None
        )
        if observed_source is None:
            records[name] = {
                "status": "unavailable",
                "expected": expected,
                "candidate_env_keys": list(candidates),
            }
            continue
        any_available = True
        observed = os.environ[observed_source]
        matched = isinstance(expected, str) and bool(expected) and observed == expected
        any_mismatch = any_mismatch or not matched
        records[name] = {
            "status": "match" if matched else "mismatch",
            "expected": expected,
            "observed": observed,
            "source": observed_source,
        }
    return {
        "status": (
            "mismatch" if any_mismatch else "match" if any_available else "unavailable"
        ),
        **records,
    }


def _parser_crosscheck(repo_root: Path, raw_paths: Sequence[Path]) -> dict[str, Any]:
    if len(raw_paths) != RAW_CPUINFO_LIMIT:
        return {
            "status": "error",
            "error": {
                "type": "RawFileCountMismatch",
                "message": f"expected {RAW_CPUINFO_LIMIT}, got {len(raw_paths)}",
            },
            "files": [],
        }
    orchestrator = repo_root / "orchestrator"
    sys.path.insert(0, str(orchestrator))
    try:
        try:
            from campaign import env_attestation
        except Exception as exc:
            return {"status": "unavailable", "error": _error(exc)}
        results = []
        mismatch = False
        for path in raw_paths:
            text = path.read_text(encoding="utf-8")
            own = parse_cpuinfo_text(text)
            try:
                _, production = env_attestation._parse_cpuinfo(path)
            except Exception as exc:
                results.append({"path": path.name, "status": "error", "error": _error(exc)})
                mismatch = True
                continue
            matched = own == production
            mismatch = mismatch or not matched
            results.append(
                {
                    "path": path.name,
                    "status": "match" if matched else "mismatch",
                    "element_count": len(own),
                }
            )
        all_match = (
            len(results) == RAW_CPUINFO_LIMIT
            and all(item.get("status") == "match" for item in results)
        )
        return {
            "status": "match" if all_match and not mismatch else "mismatch",
            "files": results,
        }
    finally:
        if sys.path and sys.path[0] == str(orchestrator):
            sys.path.pop(0)


def _write_text_create_only(path: Path, text: str) -> None:
    with path.open("x", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())


def _encode(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _check_no_symlink_components(path: Path) -> None:
    if not path.is_absolute():
        raise ValueError("path must be absolute")
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        if current.is_symlink():
            raise ValueError(f"symlink path component: {current}")


def finalize_output(
    output_dir: Path,
    *,
    probe_rc: int,
    wrapper_started_at_utc: str,
    wrapper_finished_at_utc: str,
    pbs_jobid: str,
) -> int:
    """final binding を再照合し、manifest 成功後だけ result を atomic publish する。

    final mismatch は非零 rc を返し、wrapper は done-marker を発行してはならない。
    """
    pending = output_dir / ".result.pending.json"
    if (output_dir / "result.json").exists() or (output_dir / "manifest.json").exists():
        raise FileExistsError("result or manifest already exists")
    payload = json.loads(pending.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("pending result root must be an object")
    environment = payload.get("environment")
    if (
        not isinstance(environment, Mapping)
        or environment.get("marker", {}).get("fields", {}).get("PBS_JOBID")
        != pbs_jobid
    ):
        raise ValueError("pending result PBS_JOBID mismatch")
    wrapper = {
        "started_at_utc": wrapper_started_at_utc,
        "finished_at_utc": wrapper_finished_at_utc,
        "PBS_JOBID": pbs_jobid,
    }
    provenance = payload.get("provenance")
    if not isinstance(provenance, dict):
        raise TypeError("pending result provenance missing")
    driver_path = Path(__file__).resolve(strict=True)
    repo_root = driver_path.parents[3]
    pbs_path = repo_root / "tools/pegasus/probes/t419_probe_causality.pbs"
    submission = provenance.get("submission_binding")
    try:
        if not isinstance(submission, Mapping):
            raise TypeError("submission binding missing")
        calibration = _load_calibration(
            repo_root, str(submission["expected_calibration_sha256"])
        )
        final_binding = _submission_binding(
            repo_root,
            calibration,
            expect_head=str(submission["expected_head"]),
            expect_driver_sha256=str(submission["expected_driver_sha256"]),
            expect_pbs_sha256=str(submission["expected_pbs_sha256"]),
            expect_env_attestation_sha256=str(
                submission["expected_env_attestation_sha256"]
            ),
        )
    except Exception as exc:
        final_binding = {
            "attempted": False,
            "matched": False,
            "error": _error(exc),
        }
    provenance["finalization_binding"] = final_binding
    final_binding_matched = final_binding.get("matched") is True
    finalization_rc = 0 if final_binding_matched else 4
    wrapper_rc = int(probe_rc) if finalization_rc == 0 else finalization_rc
    if not final_binding_matched:
        payload["execution_validity"] = "INVALID"
        payload["causal_verdict"] = "NOT_EVALUATED"
        payload["causal_metrics"] = None
        reasons = payload.get("validity_reasons")
        payload["validity_reasons"] = (
            list(reasons) if isinstance(reasons, list) else []
        ) + ["finalization_submission_binding_mismatch"]
    provenance["wrapper"] = wrapper
    payload["wrapper"] = wrapper
    payload["probe_rc"] = int(probe_rc)
    payload["finalization_rc"] = finalization_rc
    result_text = _encode(payload)
    result_tmp = output_dir / f".result.json.tmp.{os.getpid()}"
    _write_text_create_only(result_tmp, result_text)

    files = {}
    for path in sorted(output_dir.rglob("*")):
        if path.name in {
            "manifest.json",
            "result.json",
            pending.name,
            result_tmp.name,
            "done-marker",
        }:
            continue
        if path.is_symlink():
            raise ValueError(f"symlink output entry: {path}")
        if not path.is_file():
            if path.is_dir():
                continue
            raise ValueError(f"unsupported output entry: {path}")
        files[str(path.relative_to(output_dir))] = {
            "sha256": _sha256_path(path),
            "bytes": path.stat().st_size,
        }
    result_raw = result_text.encode("utf-8")
    files["result.json"] = {
        "sha256": _sha256_bytes(result_raw),
        "bytes": len(result_raw),
    }
    wrapper_rc_raw = f"{wrapper_rc}\n".encode("utf-8")
    files["wrapper.rc"] = {
        "sha256": _sha256_bytes(wrapper_rc_raw),
        "bytes": len(wrapper_rc_raw),
        "published_after_manifest": True,
    }
    if finalization_rc == 0:
        done_raw = (
            f"probe_rc={int(probe_rc)}\nwrapper_rc={wrapper_rc}\n"
        ).encode("utf-8")
        files["done-marker"] = {
            "sha256": _sha256_bytes(done_raw),
            "bytes": len(done_raw),
            "published_after_manifest": True,
        }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "non_certifying": True,
        "counterfactual_only": True,
        "manifest_self_hash": "excluded (a manifest cannot contain its own stable hash)",
        "files": files,
        "wrapper": wrapper,
        "probe_rc": int(probe_rc),
        "finalization_rc": finalization_rc,
        "wrapper_rc": wrapper_rc,
        "preregistered_primary_reads": PREREGISTERED_PRIMARY_READS,
        "provenance": provenance,
    }
    _write_text_create_only(output_dir / "manifest.json", _encode(manifest))
    os.replace(result_tmp, output_dir / "result.json")
    pending.unlink()
    directory_fd = os.open(output_dir, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    return finalization_rc


def run_experiment(
    repo_root: Path,
    output_dir: Path,
    *,
    seed: int,
    read_interval_ms: float,
    hard_deadline_seconds: float,
    expect_head: str,
    expect_driver_sha256: str,
    expect_pbs_sha256: str,
    expect_calibration_sha256: str,
    expect_env_attestation_sha256: str,
) -> int:
    started_at = datetime.now(timezone.utc).isoformat()
    started_monotonic_ns = time.monotonic_ns()
    hard_deadline_ns = started_monotonic_ns + int(hard_deadline_seconds * 1e9)
    raw_jobid = os.environ.get("PBS_JOBID", "")
    normalized_jobid = _normalize_jobid(raw_jobid) if raw_jobid else "missing"
    output_dir = output_dir.absolute()
    repo_root = repo_root.resolve(strict=True)
    _check_no_symlink_components(output_dir)
    if not output_dir.is_dir():
        raise ValueError("output_dir must already exist")
    expected_dir = (
        repo_root
        / "output/env/pegasus/t419-probe-causality"
        / normalized_jobid
    )
    if output_dir != expected_dir:
        raise ValueError(f"output_dir mismatch: {output_dir} != {expected_dir}")
    marker = _parse_marker(output_dir / "marker", raw_jobid)
    allocated_cpus = sorted(os.sched_getaffinity(0))
    calibration: dict[str, Any]
    try:
        calibration = _load_calibration(repo_root, expect_calibration_sha256)
    except Exception as exc:
        calibration = {"pin_verified": False, "band": None, "error": _error(exc)}
    try:
        binding = _submission_binding(
            repo_root,
            calibration,
            expect_head=expect_head,
            expect_driver_sha256=expect_driver_sha256,
            expect_pbs_sha256=expect_pbs_sha256,
            expect_env_attestation_sha256=expect_env_attestation_sha256,
        )
    except Exception as exc:
        binding = {"attempted": False, "matched": False, "error": _error(exc)}
    queue = os.environ.get("T419_QUEUE")
    project = os.environ.get("T419_PROJECT")
    scheduler_binding = _scheduler_environment_binding(queue, project)
    environment = {
        "allocated_cpus": allocated_cpus,
        "pbs_jobid_present": bool(raw_jobid),
        "compute_node_marker": marker.get("valid") is True,
        "binding_verified": binding.get("matched") is True,
        "binding": binding,
        "marker": marker,
        "hostname": platform.node(),
        "queue": queue,
        "project": project,
        "seed": seed,
        "scheduler_binding": scheduler_binding,
    }
    observations: dict[str, Any] = {
        "arm_order": list(ARM_ORDER),
        "expected_primary_read_counts": dict(EXPECTED_PRIMARY_READS),
        "arms": {},
        "exceptions": [],
        "parser_crosscheck": {"status": "unavailable", "reason": "not attempted"},
        "raw_cpuinfo_saved_count": 0,
        "cooldowns": [],
        "arm_durations_ns": {},
        "hard_deadline_seconds": hard_deadline_seconds,
    }
    raw_cpuinfo: list[str] = []
    if calibration.get("pin_verified") is not True:
        observations["exceptions"].append(
            {
                "stage": "calibration",
                "type": "CalibrationBindingFailure",
                "detail": calibration.get("error"),
            }
        )
    rng = random.Random(seed)
    interval_s = read_interval_ms / 1000.0
    original_affinity = list(allocated_cpus)
    child_registry = ChildRegistry()

    preflight_ok = (
        len(allocated_cpus) == EXPECTED_CPU_COUNT
        and len(set(allocated_cpus)) == EXPECTED_CPU_COUNT
        and environment["pbs_jobid_present"]
        and environment["compute_node_marker"]
        and environment["binding_verified"]
        and calibration.get("pin_verified") is True
        and valid_band(calibration.get("band"))
        and bool(queue)
        and bool(project)
        and scheduler_binding.get("status") != "mismatch"
    )

    def check_deadline(stage: str) -> None:
        if time.monotonic_ns() >= hard_deadline_ns:
            raise TimeoutError(f"hard deadline exceeded at {stage}")

    def cooldown(label: str) -> dict[str, Any]:
        check_deadline(f"cooldown:{label}:start")
        start_ns = time.monotonic_ns()
        requested_end_ns = start_ns + int(COOLDOWN_SECONDS * 1e9)
        if requested_end_ns >= hard_deadline_ns:
            raise TimeoutError(f"hard deadline would expire during cooldown:{label}")
        time.sleep(COOLDOWN_SECONDS)
        record = {
            "label": label,
            "started_monotonic_ns": start_ns,
            "finished_monotonic_ns": time.monotonic_ns(),
            "requested_seconds": COOLDOWN_SECONDS,
        }
        record["actual_seconds"] = (
            record["finished_monotonic_ns"] - start_ns
        ) / 1e9
        observations["cooldowns"].append(record)
        return record

    def store_arm(name: str, arm: dict[str, Any]) -> None:
        observations["arms"][name] = arm
        observations["arm_durations_ns"][name] = arm.get("duration_ns")
        if "error" in arm:
            raise RuntimeError(f"{name} primary failed: {arm['error']}")
        isolation = arm.get("isolation")
        if not isinstance(isolation, Mapping):
            raise RuntimeError(f"{name} isolation evidence missing; later arms suppressed")
        if not isolation_allows_later_arms(isolation):
            if isolation.get("isolation_attribution") == "COMPETITOR":
                raise RuntimeError(
                    f"{name} isolation admission failed; later arms suppressed"
                )
            raise RuntimeError(f"{name} isolation attribution invalid; later arms suppressed")
        check_deadline(f"{name}:complete")

    def deadline_alarm(signum: int, frame: Any) -> None:
        del signum, frame
        raise TimeoutError("hard measurement deadline alarm fired")

    previous_alarm_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, deadline_alarm)
    signal.setitimer(signal.ITIMER_REAL, hard_deadline_seconds)

    try:
        if not preflight_ok:
            raise RuntimeError("experiment admission preflight failed")

        def baseline(tracker: IsolationTracker) -> dict[str, Any]:
            blocks = []
            reads = []
            anchors = []
            for block in range(BASELINE_READS // ALPHA_K):
                check_deadline(f"A0:block:{block}")
                subwindow_id = f"A0:block:{block}"
                tracker.start_subwindow(subwindow_id)
                measured: list[dict[str, Any]] = []
                try:
                    anchor = collect_cpuinfo_read(pin_target=None, raw_cpuinfo=raw_cpuinfo)
                    anchors.append(anchor)
                    measured = _collect_series(
                        ALPHA_K,
                        pin_target=None,
                        interval_s=interval_s,
                        raw_cpuinfo=raw_cpuinfo,
                        first_deadline_ns=anchor["started_monotonic_ns"] + int(interval_s * 1e9),
                        hard_deadline_ns=hard_deadline_ns,
                    )
                finally:
                    tracker.finish_subwindow(subwindow_id, measured)
                for reading in measured:
                    reading["isolation_subwindow_id"] = subwindow_id
                reads.extend(measured)
                blocks.append({"block": block, "discarded_anchor": anchor, "reads": measured})
            return {"reads": reads, "blocks": blocks, "discarded_anchors": anchors}

        store_arm("A0_quiet_baseline", _execute_arm(
            "A0_quiet_baseline",
            allocated_cpus,
            baseline,
        ))
        cooldown("after_A0")

        pin_order = list(allocated_cpus)
        rng.shuffle(pin_order)

        def pin_sweep(tracker: IsolationTracker) -> dict[str, Any]:
            reads = []
            anchors = []
            by_pin = []
            for cpu in pin_order:
                os.sched_setaffinity(0, {cpu})
                subwindow_id = f"A1:pin:{cpu}"
                tracker.start_subwindow(subwindow_id)
                interval_start = _child_stat(os.getpid())
                measured: list[dict[str, Any]] = []
                try:
                    anchor = collect_cpuinfo_read(pin_target=cpu, raw_cpuinfo=raw_cpuinfo)
                    anchors.append(anchor)
                    measured = _collect_series(
                        PIN_REPEATS,
                        pin_target=cpu,
                        interval_s=interval_s,
                        raw_cpuinfo=raw_cpuinfo,
                        first_deadline_ns=anchor["started_monotonic_ns"] + int(interval_s * 1e9),
                        hard_deadline_ns=hard_deadline_ns,
                    )
                    interval_end = _child_stat(os.getpid())
                    tracker.record_pinned_self_interval(cpu, interval_start, interval_end)
                finally:
                    tracker.finish_subwindow(subwindow_id, measured)
                for reading in measured:
                    reading["isolation_subwindow_id"] = subwindow_id
                reads.extend(measured)
                by_pin.append({"pin_target": cpu, "reads": measured})
            return {
                "reads": reads,
                "discarded_anchors": anchors,
                "pin_order": pin_order,
                "by_pin": by_pin,
            }

        store_arm("A1_pin_sweep", _execute_arm(
            "A1_pin_sweep", allocated_cpus, pin_sweep
        ))
        cooldown("after_A1")

        os.sched_setaffinity(0, set(original_affinity))
        def migration_description(tracker: IsolationTracker) -> dict[str, Any]:
            subwindow_id = "A4:migration_description"
            tracker.start_subwindow(subwindow_id)
            reads: list[dict[str, Any]] = []
            isolation_subwindow: Optional[dict[str, Any]] = None
            try:
                anchor = collect_cpuinfo_read(pin_target=None, raw_cpuinfo=raw_cpuinfo)
                reads = _collect_series(
                    MIGRATION_READS,
                    pin_target=None,
                    interval_s=interval_s,
                    raw_cpuinfo=raw_cpuinfo,
                    first_deadline_ns=(
                        anchor["started_monotonic_ns"] + int(interval_s * 1e9)
                    ),
                    hard_deadline_ns=hard_deadline_ns,
                )
            finally:
                isolation_subwindow = tracker.finish_subwindow(subwindow_id, reads)
            for reading in reads:
                reading["isolation_subwindow_id"] = subwindow_id
            return {
                "reads": reads,
                "discarded_anchors": [anchor],
                "migration_conclusion": (
                    "OBSERVED"
                    if isolation_subwindow.get("migration_observed") is True
                    else "NOT_OBSERVED"
                ),
                "migration_observed": isolation_subwindow.get(
                    "migration_observed"
                ),
                "affinity_not_singleton": isolation_subwindow.get(
                    "affinity_not_singleton"
                ),
                "used_for_causal_verdict": False,
            }

        store_arm("A4_migration_description", _execute_arm(
            "A4_migration_description",
            allocated_cpus,
            migration_description,
        ))
        cooldown("after_A4")

        def alpha_quiet(tracker: IsolationTracker) -> dict[str, Any]:
            blocks = []
            reads = []
            anchors = []
            for block in range(ALPHA_QUIET_BLOCKS):
                check_deadline(f"A3_quiet:block:{block}")
                subwindow_id = f"A3_quiet:block:{block}"
                tracker.start_subwindow(subwindow_id)
                measured: list[dict[str, Any]] = []
                try:
                    anchor = collect_cpuinfo_read(pin_target=None, raw_cpuinfo=raw_cpuinfo)
                    anchors.append(anchor)
                    measured = _collect_series(
                        ALPHA_K,
                        pin_target=None,
                        interval_s=interval_s,
                        raw_cpuinfo=raw_cpuinfo,
                        first_deadline_ns=anchor["started_monotonic_ns"] + int(interval_s * 1e9),
                        hard_deadline_ns=hard_deadline_ns,
                    )
                finally:
                    tracker.finish_subwindow(subwindow_id, measured)
                for reading in measured:
                    reading["isolation_subwindow_id"] = subwindow_id
                reads.extend(measured)
                blocks.append(
                    {
                        "block": block,
                        "discarded_anchor": anchor,
                        "reads": measured,
                        "alpha": alpha_cumulative(
                            [_reading_values(reading) for reading in measured],
                            calibration["band"],
                        ),
                    }
                )
            return {"reads": reads, "blocks": blocks, "discarded_anchors": anchors}

        store_arm("A3_alpha_quiet", _execute_arm(
            "A3_alpha_quiet", allocated_cpus, alpha_quiet
        ))
        cooldown("after_A3_quiet")

        reader_cpu = allocated_cpus[len(allocated_cpus) // 2]
        target_cpus = select_evenly_spaced(
            [cpu for cpu in allocated_cpus if cpu not in {0, reader_cpu}],
            CORESIDENT_TARGETS,
        )

        def pin_reader_setup() -> list[dict[str, Any]]:
            return []

        def coresident(tracker: IsolationTracker) -> dict[str, Any]:
            pairs = []
            reads = []
            for target in target_cpus:
                order = ["sham", "busy"]
                rng.shuffle(order)
                conditions = []
                for mode in order:
                    condition = _run_child_condition(
                        mode,
                        target,
                        reader_cpu,
                        count=CORESIDENT_REPEATS,
                        interval_s=interval_s,
                        raw_cpuinfo=raw_cpuinfo,
                        tracker=tracker,
                        registry=child_registry,
                        hard_deadline_ns=hard_deadline_ns,
                    )
                    conditions.append(condition)
                    reads.extend(condition["reads"])
                    condition["cooldown_after"] = cooldown(
                        f"A2_target_{target}_{mode}"
                    )
                busy = next(item for item in conditions if item["mode"] == "busy")
                sham = next(item for item in conditions if item["mode"] == "sham")
                status = (
                    "VALID"
                    if busy["status"] == "VALID" and sham["status"] == "VALID"
                    else "INCONCLUSIVE"
                )
                pairs.append(
                    {
                        "target_cpu": target,
                        "condition_order": order,
                        "status": status,
                        "conditions": conditions,
                    }
                )
            return {
                "reads": reads,
                "reader_cpu": reader_cpu,
                "target_cpus": target_cpus,
                "pairs": pairs,
            }

        os.sched_setaffinity(0, {reader_cpu})
        store_arm("A2_coresident", _execute_arm(
            "A2_coresident",
            allocated_cpus,
            coresident,
            setup_fn=pin_reader_setup,
        ))
        cooldown("after_A2")

        contention_cpu = target_cpus[len(target_cpus) // 2]

        def alpha_contention(tracker: IsolationTracker) -> dict[str, Any]:
            pid, child = _start_child("busy", contention_cpu, child_registry)
            tracker.allow_child(pid, child)
            reads = []
            blocks = []
            anchors = []
            try:
                for block in range(ALPHA_CONTENTION_BLOCKS):
                    check_deadline(f"A3_contention:block:{block}")
                    subwindow_id = f"A3_contention:block:{block}"
                    tracker.start_subwindow(subwindow_id)
                    measured: list[dict[str, Any]] = []
                    try:
                        anchor = collect_cpuinfo_read(pin_target=None, raw_cpuinfo=raw_cpuinfo)
                        anchors.append(anchor)
                        measured = _collect_series(
                            ALPHA_K,
                            pin_target=None,
                            interval_s=interval_s,
                            raw_cpuinfo=raw_cpuinfo,
                            first_deadline_ns=anchor["started_monotonic_ns"] + int(interval_s * 1e9),
                            hard_deadline_ns=hard_deadline_ns,
                        )
                    finally:
                        tracker.finish_subwindow(subwindow_id, measured)
                    for reading in measured:
                        reading["isolation_subwindow_id"] = subwindow_id
                    reads.extend(measured)
                    blocks.append(
                        {
                            "block": block,
                            "discarded_anchor": anchor,
                            "reads": measured,
                            "alpha": alpha_cumulative(
                                [_reading_values(reading) for reading in measured],
                                calibration["band"],
                            ),
                        }
                    )
            finally:
                _stop_child(pid, child)
                child_registry.completed(pid)
                tracker.disallow_child(pid, child)
            established = intervention_status("busy", contention_cpu, child)
            return {
                "reads": reads,
                "blocks": blocks,
                "discarded_anchors": anchors,
                "busy_cpu": contention_cpu,
                "child": child,
                "intervention_status": established,
            }

        os.sched_setaffinity(0, set(original_affinity))
        store_arm("A3_alpha_contention", _execute_arm(
            "A3_alpha_contention",
            allocated_cpus,
            alpha_contention,
        ))
    except Exception as exc:
        observations["exceptions"].append({"stage": "experiment", **_error(exc)})
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, previous_alarm_handler)
        cleanup_records = child_registry.recover_all()
        observations["child_cleanup"] = cleanup_records
        if any(record.get("live_after_recovery") is not False for record in cleanup_records):
            observations["exceptions"].append(
                {"stage": "child_cleanup", "type": "ChildStillAlive"}
            )
        try:
            if original_affinity:
                os.sched_setaffinity(0, set(original_affinity))
        except Exception as exc:
            observations["exceptions"].append(
                {"stage": "restore_affinity", **_error(exc)}
            )

    raw_paths = []
    for index, text in enumerate(raw_cpuinfo[:RAW_CPUINFO_LIMIT], 1):
        path = output_dir / f"cpuinfo-raw-{index}.txt"
        _write_text_create_only(path, text)
        raw_paths.append(path)
    observations["raw_cpuinfo_saved_count"] = len(raw_paths)
    if raw_paths:
        observations["parser_crosscheck"] = _parser_crosscheck(repo_root, raw_paths)
    observations["read_count_summary"] = {
        name: {
            "expected": EXPECTED_PRIMARY_READS[name],
            "actual": len(_arm_reads(observations, name)),
            "missing": EXPECTED_PRIMARY_READS[name] - len(_arm_reads(observations, name)),
        }
        for name in ARM_ORDER
    }

    verdict = evaluate(observations, calibration, environment)
    rc = 0 if verdict["execution_validity"] == "VALID" else 3
    finished_at = datetime.now(timezone.utc).isoformat()
    nominal = (
        calibration.get("band", {}).get("expected_median_mhz")
        if isinstance(calibration.get("band"), Mapping)
        else None
    )
    try:
        all_values = [
            value
            for name in ARM_ORDER
            for reading in _arm_reads(observations, name)
            for value in _reading_values(reading).values()
        ]
    except Exception as exc:
        all_values = []
        observations["exceptions"].append({"stage": "secondary_diagnostics", **_error(exc)})
    diagnostics = {
        "exact_nominal_rate": (
            exact_nominal_rate(all_values, nominal) if nominal is not None else None
        ),
        "sample_count": len(all_values),
    }
    payload = {
        "schema_version": SCHEMA_VERSION,
        "non_certifying": True,
        "counterfactual_only": True,
        "execution_validity": verdict["execution_validity"],
        "causal_verdict": verdict["causal_verdict"],
        "validity_reasons": verdict["validity_reasons"],
        "causal_metrics": verdict["causal_metrics"],
        "coresident_metrics": verdict["coresident_metrics"],
        "method_table": verdict["method_table"],
        "secondary_diagnostics": diagnostics,
        "environment": environment,
        "observations": observations,
        "calibration": calibration,
    }
    try:
        git = _git_provenance(repo_root, output_dir)
    except Exception as exc:
        git = {"error": _error(exc)}
        rc = 3
        payload["execution_validity"] = "INVALID"
        payload["causal_verdict"] = "NOT_EVALUATED"
        payload["causal_metrics"] = None
        payload["validity_reasons"] = list(payload["validity_reasons"]) + [
            "provenance_collection_failed"
        ]
    qstat = _qstat_record(raw_jobid) if raw_jobid else {"attempted": False}
    boot_cmdline = _read_path_record(Path("/proc/cmdline"))
    driver_finished_at = datetime.now(timezone.utc).isoformat()
    provenance = {
        **git,
        "driver_path": str(Path(__file__).resolve(strict=True).relative_to(repo_root)),
        "driver_sha256": _sha256_path(Path(__file__).resolve(strict=True)),
        "pbs_path": "tools/pegasus/probes/t419_probe_causality.pbs",
        "pbs_sha256": _sha256_path(
            repo_root / "tools/pegasus/probes/t419_probe_causality.pbs"
        ),
        "exact_argv": list(sys.argv),
        "seed": seed,
        "parameters": {
            "N": BASELINE_READS,
            "R": PIN_REPEATS,
            "K": ALPHA_K,
            "alpha_quiet_blocks": ALPHA_QUIET_BLOCKS,
            "alpha_contention_blocks": ALPHA_CONTENTION_BLOCKS,
            "coresident_targets": CORESIDENT_TARGETS,
            "coresident_repeats": CORESIDENT_REPEATS,
            "read_interval_ms": read_interval_ms,
            "cooldown_seconds": COOLDOWN_SECONDS,
            "busy_min_cpu_ticks": BUSY_MIN_CPU_TICKS,
            "sham_max_cpu_ticks": SHAM_MAX_CPU_TICKS,
            "inconclusive_pair_invalid_min": INCONCLUSIVE_PAIR_INVALID_MIN,
            "clock_ticks_per_second": os.sysconf("SC_CLK_TCK"),
            "causal_thresholds": {
                "pinned_hit_rate_min": PINNED_HIT_RATE_MIN,
                "nonpinned_out_of_band_rate_max": NONPINNED_OUT_OF_BAND_RATE_MAX,
                "positive_contrast_cpu_min": POSITIVE_CONTRAST_CPU_MIN,
            },
            "pin_order": observations.get("arms", {}).get("A1_pin_sweep", {}).get("pin_order"),
            "k_list": observations.get("arms", {}).get("A2_coresident", {}).get("target_cpus"),
        },
        "python": {
            "executable": sys.executable,
            "version": sys.version,
        },
        "uname": {
            "release": platform.uname().release,
            "version": platform.uname().version,
        },
        "boot_cmdline": boot_cmdline,
        "queue": queue,
        "project": project,
        "pbs_jobid_raw": raw_jobid,
        "pbs_jobid_normalized": normalized_jobid,
        "qstat": qstat,
        "started_at_utc": started_at,
        "experiment_finished_at_utc": finished_at,
        "finished_at_utc": driver_finished_at,
        "rc": rc,
        "hard_deadline_seconds": hard_deadline_seconds,
        "arm_durations_ns": observations["arm_durations_ns"],
        "preregistered_primary_reads": PREREGISTERED_PRIMARY_READS,
        "submission_binding": binding,
        "calibration": {
            "path": calibration.get("path"),
            "sha256": calibration.get("actual_sha256"),
            "expected_sha256": calibration.get("expected_sha256"),
            **(calibration.get("band") or {}),
        },
    }
    payload["provenance"] = provenance
    _write_text_create_only(output_dir / ".result.pending.json", _encode(payload))
    return rc


def _expected_sha256(value: str) -> str:
    lowered = value.lower()
    if _HEX64_RE.fullmatch(lowered) is None:
        raise argparse.ArgumentTypeError("must be exactly 64 hexadecimal characters")
    return lowered


def _expected_head(value: str) -> str:
    lowered = value.lower()
    if _HEAD_RE.fullmatch(lowered) is None:
        raise argparse.ArgumentTypeError("must be exactly 40 hexadecimal characters")
    return lowered


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--finalize-wrapper", action="store_true")
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--read-interval-ms", type=float, default=DEFAULT_READ_INTERVAL_MS
    )
    parser.add_argument(
        "--hard-deadline-seconds",
        type=float,
        default=DEFAULT_HARD_DEADLINE_SECONDS,
    )
    parser.add_argument("--expect-head", type=_expected_head)
    parser.add_argument("--expect-driver-sha256", type=_expected_sha256)
    parser.add_argument("--expect-pbs-sha256", type=_expected_sha256)
    parser.add_argument("--expect-calibration-sha256", type=_expected_sha256)
    parser.add_argument("--expect-env-attestation-sha256", type=_expected_sha256)
    parser.add_argument("--probe-rc", type=int)
    parser.add_argument("--wrapper-started-at-utc")
    parser.add_argument("--wrapper-finished-at-utc")
    parser.add_argument("--pbs-jobid")
    args = parser.parse_args(argv)
    if args.self_test:
        return run_self_test()
    if args.finalize_wrapper:
        required = (
            args.output_dir,
            args.probe_rc,
            args.wrapper_started_at_utc,
            args.wrapper_finished_at_utc,
            args.pbs_jobid,
        )
        if any(value is None for value in required):
            parser.error(
                "--finalize-wrapper requires --output-dir, --probe-rc, "
                "--wrapper-started-at-utc, --wrapper-finished-at-utc, and --pbs-jobid"
            )
        return finalize_output(
            args.output_dir,
            probe_rc=args.probe_rc,
            wrapper_started_at_utc=args.wrapper_started_at_utc,
            wrapper_finished_at_utc=args.wrapper_finished_at_utc,
            pbs_jobid=args.pbs_jobid,
        )
    if args.repo_root is None or args.output_dir is None:
        parser.error("--repo-root and --output-dir are required outside --self-test")
    if any(
        value is None
        for value in (
            args.expect_head,
            args.expect_driver_sha256,
            args.expect_pbs_sha256,
            args.expect_calibration_sha256,
            args.expect_env_attestation_sha256,
        )
    ):
        parser.error("all --expect-* binding arguments are required")
    if not math.isfinite(args.read_interval_ms) or args.read_interval_ms < 0.0:
        parser.error("--read-interval-ms must be finite and non-negative")
    if not math.isfinite(args.hard_deadline_seconds) or args.hard_deadline_seconds <= 0.0:
        parser.error("--hard-deadline-seconds must be finite and positive")
    return run_experiment(
        args.repo_root,
        args.output_dir,
        seed=args.seed,
        read_interval_ms=args.read_interval_ms,
        hard_deadline_seconds=args.hard_deadline_seconds,
        expect_head=args.expect_head,
        expect_driver_sha256=args.expect_driver_sha256,
        expect_pbs_sha256=args.expect_pbs_sha256,
        expect_calibration_sha256=args.expect_calibration_sha256,
        expect_env_attestation_sha256=args.expect_env_attestation_sha256,
    )


if __name__ == "__main__":
    raise SystemExit(main())
