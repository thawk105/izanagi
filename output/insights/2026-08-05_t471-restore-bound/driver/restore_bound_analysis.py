"""T-471 の復元時間 evidence を扱う純関数。"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any


_PROFILE_FIELDS = (
    "n",
    "B_original_total",
    "B_mutated_total",
    "target_existence_states",
    "P",
    "E_by_parent",
    "E_total",
    "cache_temperature_label",
)


def _is_exact_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _nearest_rank(sorted_values: Sequence[int], percentile: float) -> int:
    rank = math.ceil(percentile * len(sorted_values))
    return sorted_values[rank - 1]


def summarize_elapsed_ns(samples: Sequence[int]) -> dict[str, int | float | str]:
    """正の整数 nanoseconds を raw max を失わず要約する。"""

    if isinstance(samples, (str, bytes)) or not isinstance(samples, Sequence):
        raise TypeError("samples は sequence でなければならない")
    values = list(samples)
    if not values:
        raise ValueError("samples は空であってはならない")
    for index, value in enumerate(values):
        if not _is_exact_int(value) or value <= 0:
            raise ValueError(f"samples[{index}] は正の exact int でなければならない")
    ordered = sorted(values)
    return {
        "count": len(values),
        "min_ns": ordered[0],
        "max_ns": max(values),
        "mean_ns": math.fsum(values) / len(values),
        "p50_ns": _nearest_rank(ordered, 0.50),
        "p90_ns": _nearest_rank(ordered, 0.90),
        "p99_ns": _nearest_rank(ordered, 0.99),
        "quantile_method": "nearest-rank",
    }


def _profile_type_reasons(value: Mapping[str, Any], label: str) -> list[str]:
    reasons: list[str] = []
    actual_fields = set(value)
    expected_fields = set(_PROFILE_FIELDS)
    if actual_fields != expected_fields:
        reasons.append(
            f"{label}.fields mismatch: missing={sorted(expected_fields - actual_fields)}, "
            f"unknown={sorted(actual_fields - expected_fields)}"
        )
        return reasons

    for field in ("n", "B_original_total", "B_mutated_total", "P", "E_total"):
        number = value[field]
        minimum = 0 if field == "E_total" else 1
        if not _is_exact_int(number) or number < minimum:
            reasons.append(f"{label}.{field} must be an exact int >= {minimum}")

    states = value["target_existence_states"]
    if not isinstance(states, list) or any(
        not isinstance(item, str) or not item for item in states
    ):
        reasons.append(f"{label}.target_existence_states must be a non-empty string list")
    elif _is_exact_int(value["n"]) and len(states) != value["n"]:
        reasons.append(f"{label}.target_existence_states length must equal n")

    entries = value["E_by_parent"]
    if not isinstance(entries, list) or any(
        not _is_exact_int(item) or item < 0 for item in entries
    ):
        reasons.append(f"{label}.E_by_parent must be a non-negative exact-int list")
    else:
        if _is_exact_int(value["P"]) and len(entries) != value["P"]:
            reasons.append(f"{label}.E_by_parent length must equal P")
        if _is_exact_int(value["E_total"]) and sum(entries) != value["E_total"]:
            reasons.append(f"{label}.E_total must equal sum(E_by_parent)")

    temperature = value["cache_temperature_label"]
    if not isinstance(temperature, str) or not temperature:
        reasons.append(f"{label}.cache_temperature_label must be a non-empty string")
    return reasons


def validate_arm_profile(
    profile: Mapping[str, Any], observed: Mapping[str, Any]
) -> dict[str, bool | list[str]]:
    """事前登録 profile と実観測を exact 比較し、不一致理由を返す。"""

    reasons: list[str] = []
    if not isinstance(profile, Mapping):
        reasons.append("profile must be a mapping")
    if not isinstance(observed, Mapping):
        reasons.append("observed must be a mapping")
    if reasons:
        return {"valid": False, "reasons": reasons}

    reasons.extend(_profile_type_reasons(profile, "profile"))
    reasons.extend(_profile_type_reasons(observed, "observed"))
    if not reasons:
        for field in _PROFILE_FIELDS:
            if observed[field] != profile[field]:
                reasons.append(
                    f"{field} mismatch: expected={profile[field]!r}, observed={observed[field]!r}"
                )
    return {"valid": not reasons, "reasons": reasons}


def attempt_validity(trials: Sequence[Mapping[str, Any]]) -> dict[str, bool | list[str]]:
    """失敗または sequence 欠落が 1 件でもある attempt を fail-closed にする。"""

    if isinstance(trials, (str, bytes)) or not isinstance(trials, Sequence):
        return {"valid": False, "reasons": ["trials must be a sequence"]}
    records = list(trials)
    if not records:
        return {"valid": False, "reasons": ["trials must not be empty"]}

    reasons: list[str] = []
    sequences: list[int] = []
    for index, trial in enumerate(records):
        if not isinstance(trial, Mapping):
            reasons.append(f"trials[{index}] must be a mapping")
            continue
        if trial.get("success") is not True:
            reasons.append(f"trials[{index}] did not succeed")
        elif not _is_exact_int(trial.get("restore_call_count")) or trial.get(
            "restore_call_count"
        ) != 1:
            reasons.append(f"trials[{index}].restore_call_count must be exact int 1")
        sequence = trial.get("sequence")
        if not _is_exact_int(sequence) or sequence < 0:
            reasons.append(f"trials[{index}].sequence must be a non-negative exact int")
        else:
            sequences.append(sequence)

    if len(sequences) == len(records) and sorted(sequences) != list(range(len(records))):
        reasons.append("trial sequences must be unique and contiguous from zero")
    return {"valid": not reasons, "reasons": reasons}


def planning_allowance_ns(observed_max_ns: int) -> int:
    """観測 max に設計用余裕を足す。この参考値は時間の上限ではない。"""

    if not _is_exact_int(observed_max_ns) or observed_max_ns <= 0:
        raise ValueError("observed_max_ns は正の exact int でなければならない")
    margin_ns = max((observed_max_ns + 1) // 2, 1_000_000_000)
    planning_reference_ns_not_upper_bound = observed_max_ns + margin_ns
    return planning_reference_ns_not_upper_bound
