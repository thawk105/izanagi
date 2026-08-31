#!/usr/bin/env python3
"""Source-separated replay verifier for balanced A-1 sizing.

This is a second source implementation of the registered rules.  It is not an
independent statistical oracle and makes no such claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import re
import stat
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Callable

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "paper-story-a1-balanced-sizing-certificate/v1"
RECEIPT_SCHEMA = "paper-story-a1-balanced-sizing-replay-receipt/v1"
PILOT_SCHEMA = "paper-story-a1-balanced-sizing-pilot/v1"
PILOT_STUDY_ID = "paper-story-a1-20260901-balanced5-pilot-v1"
CANONICAL_JSON = "utf8-sort-keys-compact-no-nonfinite-final-lf/v1"
SEED_GRAMMAR = "paper-story-a1-balanced-sizing-seed/v1"
ROOT_SEED_PREIMAGE = (
    "paper-story-a1-balanced-sizing-root-seed/v1|20260901|"
    "paired-mean-block-sigma"
)
ROOT_SEED_DIGEST = "e72bc005d156caea2c89085c563c72fa04bbeb4afd98160fca968da9a7f6b3b3"
if hashlib.sha256(ROOT_SEED_PREIMAGE.encode("ascii")).hexdigest() != ROOT_SEED_DIGEST:
    raise RuntimeError("registered replay seed preimage and digest differ")

RNG_ALGORITHM = "numpy-pcg64-normal-chisquare-sufficient-statistics/v1"
T_QUANTILE_ALGORITHM = "regularized-beta-bisection/v1"
CHI_SQUARE_QUANTILE_ALGORITHM = "regularized-gamma-bisection/v1"
EXACT_BOUND_ALGORITHM = "one-sided-exact-clopper-pearson-lower/v1"
GENERATOR_SOURCE = REPO_ROOT / "tools/size_paper_story_a1_balanced.py"
VERIFIER_SOURCE = REPO_ROOT / "tools/verify_paper_story_a1_balanced_sizing.py"

WORKLOADS = ("write-heavy", "balanced", "read-heavy")
ARMS = {
    "write-heavy": {"variant": "fixed10", "baseline": "no-backoff"},
    "balanced": {"variant": "fixed5", "baseline": "no-backoff"},
    "read-heavy": {"variant": "fixed2", "baseline": "no-backoff"},
}
CASES = (
    ("zero", Fraction(0), "bounded-within-floor", None),
    ("positive-two-floor", Fraction(3, 50), "resolved-beyond-floor", "improvement"),
    ("negative-two-floor", Fraction(-3, 50), "resolved-beyond-floor", "regression"),
)
FLOOR = Fraction(3, 100)
FAMILY_ALPHA = Fraction(1, 20)
ARM_FAILURE = Fraction(1, 120)
REQUIRED = Fraction(4, 5)
ALPHA_C = Fraction(1, 20)
PAIR_COUNT, PAIR_DF = 60, 59
BLOCK_SIZE, BLOCK_COUNT, BLOCK_DF = 5, 12, 11
STEP, EFFECTIVE_MIN = 10, 30
_SEED_RE = re.compile(r"[0-9a-f]{64}\Z")
_ROW_KEYS = {
    "arm", "block", "block_position", "ended_at_ns", "group",
    "pair_index", "started_at_ns", "tps",
}


class VerificationError(RuntimeError):
    """Replay or binding verification failed."""


@dataclass(frozen=True)
class VerificationConfig:
    root_seed: str
    search_trials: int
    certification_trials: int
    n_min: int
    n_max: int

    def validate(self) -> None:
        if not _SEED_RE.fullmatch(self.root_seed) or self.root_seed != ROOT_SEED_DIGEST:
            raise VerificationError("root seed differs")
        for label, value in (
            ("search trials", self.search_trials),
            ("certification trials", self.certification_trials),
            ("n-min", self.n_min),
            ("n-max", self.n_max),
        ):
            if type(value) is not int:
                raise VerificationError(f"{label} must be an integer")
        if not 1 <= self.search_trials <= 1_000_000 or not 1 <= self.certification_trials <= 1_000_000:
            raise VerificationError("simulation trial count differs")
        if not 28 <= self.n_min <= self.n_max <= 4096 or self.n_max < EFFECTIVE_MIN:
            raise VerificationError("candidate range differs")


def _frac(value: Fraction) -> dict[str, int]:
    return {"denominator": value.denominator, "numerator": value.numerator}


def _dec(value: float) -> str:
    if not math.isfinite(value):
        raise VerificationError("non-finite replay decimal")
    return format(value, ".17g")


def condition_alpha(attempt: int) -> Fraction:
    if type(attempt) is not int or attempt < 1:
        raise VerificationError("certification attempt differs")
    return Fraction(1, 60 * attempt * (attempt + 1))


def grid(n_min: int, n_max: int) -> tuple[int, ...]:
    first = max(EFFECTIVE_MIN, ((n_min + STEP - 1) // STEP) * STEP)
    return tuple(range(first, n_max + 1, STEP))


def _reject_constant(value: str) -> None:
    raise VerificationError(f"non-finite JSON constant: {value}")


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise VerificationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _parse(raw: bytes, label: str) -> dict[str, object]:
    try:
        value = json.loads(raw.decode("utf-8"), parse_constant=_reject_constant, object_pairs_hook=_unique)
    except (UnicodeError, json.JSONDecodeError, VerificationError) as exc:
        raise VerificationError(f"{label} is not strict UTF-8 JSON: {exc}") from exc
    if type(value) is not dict:
        raise VerificationError(f"{label} top level differs")
    return value


def _read(path: Path, label: str) -> bytes:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise VerificationError("O_NOFOLLOW is required")
    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | nofollow)
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise VerificationError(f"{label} must be a regular non-symlink file")
        pieces: list[bytes] = []
        while True:
            piece = os.read(descriptor, 1024 * 1024)
            if not piece:
                return b"".join(pieces)
            pieces.append(piece)
    except OSError as exc:
        raise VerificationError(f"cannot read {label}: {path}: {exc}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def canonical_bytes(value: dict[str, object]) -> bytes:
    try:
        return (json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise VerificationError(f"document is not canonical-JSON serializable: {exc}") from exc


def load_certificate(path: Path) -> tuple[dict[str, object], bytes]:
    raw = _read(path, "certificate")
    value = _parse(raw, "certificate")
    if value.get("schema_version") != SCHEMA:
        raise VerificationError("certificate schema differs")
    if canonical_bytes(value) != raw:
        raise VerificationError("certificate is not canonical JSON")
    return value, raw


def _positive(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise VerificationError(f"{label} is not an uncoerced number")
    try:
        clean = float(value)
    except (OverflowError, ValueError) as exc:
        raise VerificationError(f"{label} is not finite positive") from exc
    if not math.isfinite(clean) or clean <= 0:
        raise VerificationError(f"{label} is not finite positive")
    return clean


def _integer(value: object, label: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise VerificationError(f"{label} integer differs")
    return value


def _sd(values: list[float]) -> float:
    try:
        mean = math.fsum(values) / len(values)
        answer = math.sqrt(
            math.fsum((value - mean) ** 2 for value in values)
            / (len(values) - 1)
        )
    except (OverflowError, ValueError) as exc:
        raise VerificationError("pilot SD is not finite") from exc
    if not math.isfinite(answer):
        raise VerificationError("pilot SD is not finite")
    return answer


def _gamma_p(a: float, x: float) -> float:
    if x == 0.0:
        return 0.0
    tiny = 1e-300
    if x < a + 1.0:
        ap = a
        term = total = 1.0 / a
        for _ in range(1000):
            ap += 1.0
            term *= x / ap
            total += term
            if abs(term) <= abs(total) * 3e-15:
                return total * math.exp(-x + a * math.log(x) - math.lgamma(a))
        raise VerificationError("gamma series replay did not converge")
    b = x + 1.0 - a
    c = 1.0 / tiny
    d = 1.0 / b
    result = d
    for index in range(1, 1001):
        numerator = -index * (index - a)
        b += 2.0
        d = numerator * d + b
        d = tiny if abs(d) < tiny else d
        c = b + numerator / c
        c = tiny if abs(c) < tiny else c
        d = 1.0 / d
        change = d * c
        result *= change
        if abs(change - 1.0) <= 3e-15:
            return 1.0 - math.exp(-x + a * math.log(x) - math.lgamma(a)) * result
    raise VerificationError("gamma fraction replay did not converge")


def _chi_quantile(probability: Fraction, df: int) -> float:
    target = float(probability)
    lo, hi = 0.0, float(df)
    while _gamma_p(df / 2.0, hi / 2.0) < target:
        hi *= 2.0
    for _ in range(100):
        mid = (lo + hi) / 2.0
        if _gamma_p(df / 2.0, mid / 2.0) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def _sigma_factor(df: int) -> float:
    return math.sqrt(df / _chi_quantile(ALPHA_C, df))


def _beta_fraction(a: float, b: float, x: float) -> float:
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    tiny = 1e-300
    c = 1.0
    d = 1.0 - qab * x / qap
    d = 1.0 / (tiny if abs(d) < tiny else d)
    answer = d
    for index in range(1, 501):
        twice = 2 * index
        aa = index * (b - index) * x / ((qam + twice) * (a + twice))
        d = 1.0 + aa * d
        d = tiny if abs(d) < tiny else d
        c = 1.0 + aa / c
        c = tiny if abs(c) < tiny else c
        d = 1.0 / d
        answer *= d * c
        aa = -(a + index) * (qab + index) * x / ((a + twice) * (qap + twice))
        d = 1.0 + aa * d
        d = tiny if abs(d) < tiny else d
        c = 1.0 + aa / c
        c = tiny if abs(c) < tiny else c
        d = 1.0 / d
        change = d * c
        answer *= change
        if abs(change - 1.0) <= 3e-14:
            return answer
    raise VerificationError("beta fraction replay did not converge")


def _beta_cdf(x: float, a: float, b: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _beta_fraction(a, b, x) / a
    return 1.0 - front * _beta_fraction(b, a, 1.0 - x) / b


def _t_quantile(probability: Fraction, df: int) -> float:
    target = float(probability)
    lo, hi = 0.0, 1.0

    def cdf(value: float) -> float:
        return 1.0 - 0.5 * _beta_cdf(df / (df + value * value), df / 2.0, 0.5)

    while cdf(hi) < target:
        hi *= 2.0
    for _ in range(100):
        mid = (lo + hi) / 2.0
        if cdf(mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def _exact_lower(success: int, trials: int, alpha: Fraction) -> float:
    if success == 0:
        return 0.0
    lo, hi, target = 0.0, 1.0, float(alpha)
    for _ in range(100):
        mid = (lo + hi) / 2.0
        if _beta_cdf(mid, float(success), float(trials - success + 1)) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def replay_pilot(path: Path) -> dict[str, object]:
    raw = _read(path, "pilot input")
    document = _parse(raw, "pilot input")
    if set(document) != {"final_estimate_eligible", "schema_version", "study_id", "workloads"}:
        raise VerificationError("pilot top-level keys differ")
    if document["schema_version"] != PILOT_SCHEMA or document["study_id"] != PILOT_STUDY_ID:
        raise VerificationError("pilot identity differs")
    if document["final_estimate_eligible"] is not False:
        raise VerificationError("pilot final eligibility differs")
    workloads = document["workloads"]
    if type(workloads) is not list or len(workloads) != 3:
        raise VerificationError("pilot workload count differs")
    planning: list[dict[str, object]] = []
    for workload_index, name in enumerate(WORKLOADS):
        item = workloads[workload_index]
        if type(item) is not dict or set(item) != {"observations", "workload"} or item.get("workload") != name:
            raise VerificationError(f"pilot workload shape differs: {name}")
        rows = item["observations"]
        if type(rows) is not list or len(rows) != 120:
            raise VerificationError(f"pilot row count differs: {name}")
        arms = ARMS[name]
        arm_set = {arms["variant"], arms["baseline"]}
        pairs: dict[int, dict[str, tuple[float, int, int]]] = {}
        intervals: list[tuple[int, int]] = []
        for row_index, row in enumerate(rows):
            label = f"pilot {name} row {row_index}"
            if type(row) is not dict or set(row) != _ROW_KEYS:
                raise VerificationError(f"{label} keys differ")
            arm = row["arm"]
            if type(arm) is not str or arm not in arm_set:
                raise VerificationError(f"{label} arm differs")
            pair = _integer(row["pair_index"], f"{label} pair", 0, 59)
            group = _integer(row["group"], f"{label} group", 0, 5)
            block = _integer(row["block"], f"{label} block", 0, 11)
            position = _integer(row["block_position"], f"{label} position", 0, 4)
            if (group, block, position) != (pair // 10, pair // 5, pair % 5):
                raise VerificationError(f"{label} schedule differs")
            tps = _positive(row["tps"], f"{label} tps")
            start = _integer(row["started_at_ns"], f"{label} start", 1, 2**63 - 1)
            end = _integer(row["ended_at_ns"], f"{label} end", 1, 2**63 - 1)
            if end <= start:
                raise VerificationError(f"{label} time differs")
            record = pairs.setdefault(pair, {})
            if arm in record:
                raise VerificationError(f"duplicate pilot arm: {name}/{pair}")
            record[arm] = (tps, start, end)
            intervals.append((start, end))
        if sorted(intervals) != intervals or any(a[1] > b[0] for a, b in zip(intervals, intervals[1:])):
            raise VerificationError(f"pilot chronology differs: {name}")
        differences: list[float] = []
        baselines: list[float] = []
        block_orders: list[str] = []
        for pair in range(60):
            record = pairs.get(pair)
            if record is None or set(record) != arm_set:
                raise VerificationError(f"pilot pair arms differ: {name}/{pair}")
            difference = record[arms["variant"]][0] - record[arms["baseline"]][0]
            if not math.isfinite(difference):
                raise VerificationError(f"pilot paired difference is not finite: {name}/{pair}")
            differences.append(difference)
            baselines.append(record[arms["baseline"]][0])
        for block in range(12):
            indexes = range(block * 5, block * 5 + 5)
            variants = [pairs[index][arms["variant"]] for index in indexes]
            baselines_in_block = [pairs[index][arms["baseline"]] for index in indexes]
            if max(row[2] for row in variants) <= min(row[1] for row in baselines_in_block):
                block_orders.append("variant-first")
            elif max(row[2] for row in baselines_in_block) <= min(row[1] for row in variants):
                block_orders.append("baseline-first")
            else:
                raise VerificationError(f"pilot block order differs: {name}/{block}")
        if block_orders.count("variant-first") != 6 or block_orders.count("baseline-first") != 6:
            raise VerificationError(f"pilot lead counts differ: {name}")
        if any(set(block_orders[group * 2 : group * 2 + 2]) != {"variant-first", "baseline-first"} for group in range(6)):
            raise VerificationError(f"pilot group balance differs: {name}")
        block_means = [math.fsum(differences[start : start + 5]) / 5 for start in range(0, 60, 5)]
        pair_sd, block_sd = _sd(differences), _sd(block_means)
        pair_factor, block_factor = _sigma_factor(59), _sigma_factor(11)
        sigma_pair = pair_factor * pair_sd
        sigma_block = math.sqrt(5) * block_factor * block_sd
        try:
            baseline_mean = math.fsum(baselines) / 60
        except OverflowError as exc:
            raise VerificationError(f"pilot baseline mean is not finite: {name}") from exc
        if not math.isfinite(baseline_mean) or baseline_mean <= 0.0:
            raise VerificationError(f"pilot baseline mean is not finite positive: {name}")
        planning.append(
            {
                "baseline_mean_tps": _dec(baseline_mean),
                "block_count": 12,
                "block_lead_counts": {"baseline-first": 6, "variant-first": 6},
                "block_mean_sd_tps": _dec(block_sd),
                "block_size": 5,
                "chi_square_factors": {"block_df_11": _dec(block_factor), "pair_df_59": _dec(pair_factor)},
                "pair_count": 60,
                "pair_sd_tps": _dec(pair_sd),
                "planned_sigma_tps": _dec(max(sigma_pair, sigma_block)),
                "sigma_block_tps": _dec(sigma_block),
                "sigma_pair_tps": _dec(sigma_pair),
                "workload": name,
            }
        )
    return {
        "final_estimate_eligible": False,
        "path": path.as_posix(),
        "planning": planning,
        "schema_version": PILOT_SCHEMA,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "study_id": PILOT_STUDY_ID,
    }


def seed_record(
    root: str, phase: str, workload: str, condition: str, n: int,
    trials: int, attempt: int | None = None,
) -> dict[str, str]:
    if root != ROOT_SEED_DIGEST:
        raise VerificationError("replay root seed differs")
    preimage = (
        f"{SEED_GRAMMAR}|root={root}|phase={phase}|workload={workload}"
        f"|condition={condition}|n={n}|trials={trials}"
    )
    if phase == "certification":
        preimage += f"|attempt={attempt}"
    return {"digest": hashlib.sha256(preimage.encode("ascii")).hexdigest(), "preimage": preimage}


def _outcomes(means: np.ndarray, widths: np.ndarray, boundary: float, classification: str, direction: str | None) -> dict[str, object]:
    invalid = ~np.isfinite(means) | ~np.isfinite(widths) | (widths < 0)
    low, high = means - widths, means + widths
    valid = ~invalid
    improvement = valid & (low > boundary)
    regression = valid & (high < -boundary)
    bounded = valid & ~improvement & ~regression & (low >= -boundary) & (high <= boundary)
    unresolved = valid & ~improvement & ~regression & ~bounded
    counts: dict[str, object] = {
        "bounded-within-floor": int(np.count_nonzero(bounded)),
        "invalid": int(np.count_nonzero(invalid)),
        "resolved-beyond-floor": {
            "improvement": int(np.count_nonzero(improvement)),
            "regression": int(np.count_nonzero(regression)),
        },
        "unresolved": int(np.count_nonzero(unresolved)),
    }
    if classification == "bounded-within-floor":
        success = counts["bounded-within-floor"]
    else:
        success = counts["resolved-beyond-floor"][direction]  # type: ignore[index]
    return {"invalid": counts["invalid"], "outcomes": counts, "success": success}


def replay_condition(
    config: VerificationConfig, phase: str, workload: str, condition: str,
    delta: Fraction, classification: str, direction: str | None, n: int,
    trials: int, sigma_text: str, baseline_text: str, t_value: float,
    attempt: int | None = None,
) -> dict[str, object]:
    seed = seed_record(config.root_seed, phase, workload, condition, n, trials, attempt)
    rng = np.random.Generator(np.random.PCG64(int(seed["digest"], 16)))
    sigma, baseline = float(sigma_text), float(baseline_text)
    means = baseline * float(delta) + sigma * rng.standard_normal(trials) / math.sqrt(n)
    sample_sds = sigma * np.sqrt(rng.chisquare(n - 1, size=trials) / (n - 1))
    counts = _outcomes(means, t_value * sample_sds / math.sqrt(n), float(FLOOR) * baseline, classification, direction)
    return {
        "condition": condition,
        "invalid": counts["invalid"],
        "outcomes": counts["outcomes"],
        "seed": seed,
        "success": counts["success"],
        "trials": trials,
    }


ReplayFunction = Callable[..., dict[str, object]]


def recompute_workload(
    name: str, sigma_text: str, baseline_text: str, config: VerificationConfig,
    replay: ReplayFunction = replay_condition,
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    selected = None
    attempts = 0
    t_probability = Fraction(1) - ARM_FAILURE / 2
    for order_index, n in enumerate(grid(config.n_min, config.n_max)):
        t_value = _t_quantile(t_probability, n - 1)
        search = [
            replay(config, "search", name, case, delta, classification, direction, n, config.search_trials, sigma_text, baseline_text, t_value)
            for case, delta, classification, direction in CASES
        ]
        search_passes = all(int(item["success"]) * REQUIRED.denominator >= config.search_trials * REQUIRED.numerator for item in search)
        certification = None
        if search_passes:
            attempts += 1
            alpha = condition_alpha(attempts)
            conditions = []
            for case, delta, classification, direction in CASES:
                result = replay(config, "certification", name, case, delta, classification, direction, n, config.certification_trials, sigma_text, baseline_text, t_value, attempts)
                bound = _exact_lower(int(result["success"]), config.certification_trials, alpha)
                result.update({"alpha": _frac(alpha), "lower_bound": _dec(bound), "passes": bound >= float(REQUIRED)})
                conditions.append(result)
            certification = {
                "attempt": attempts,
                "condition_alpha": _frac(alpha),
                "conditions": conditions,
                "passes": all(bool(item["passes"]) for item in conditions),
            }
        row = {
            "certification": certification,
            "df": n - 1,
            "n": n,
            "order_index": order_index,
            "search": {"conditions": search, "passes": search_passes},
            "t_critical": _dec(t_value),
        }
        rows.append(row)
        if certification is not None and certification["passes"] is True:
            selected = {
                "certification_attempt": attempts,
                "df": n - 1,
                "n": n,
                "order_index": order_index,
                "t_critical": _dec(t_value),
            }
            break
    spent = sum((len(CASES) * condition_alpha(j) for j in range(1, attempts + 1)), Fraction())
    return {
        "baseline_mean_tps": baseline_text,
        "candidates": rows,
        "certification_alpha_spending": {
            "attempt_count": attempts,
            "condition_count": 3,
            "family_alpha_cap": _frac(FAMILY_ALPHA),
            "spent": _frac(spent),
            "within_cap": True,
        },
        "planned_sigma_tps": sigma_text,
        "selected": selected,
        "status": "selected" if selected is not None else "no-passing-n",
        "workload": name,
    }


def runtime_contract() -> dict[str, object]:
    return {
        "numpy": {"version": np.__version__},
        "python": {"implementation": platform.python_implementation(), "version": platform.python_version()},
    }


def _sigma_policy() -> dict[str, object]:
    return {
        "alpha_c": _frac(ALPHA_C),
        "block": {
            "chi_square_coefficient_applied": True,
            "d1296_explicitly_specified_block_coefficient": False,
            "df": 11,
            "formula": "sqrt(5) * c(one-sided, alpha_c, df=11) * sd(12 five-pair block means)",
            "reason": "conservative-choice-because-coefficient-increases-sigma-and-repetitions",
        },
        "chi_square_quantile_algorithm": CHI_SQUARE_QUANTILE_ALGORITHM,
        "coefficient": "sqrt(df / chi-square-quantile(alpha_c, df))",
        "pair": {"df": 59, "formula": "c(one-sided, alpha_c, df=59) * sd(60 paired differences)"},
        "planned": {"formula": "max(sigma_pair, sigma_block)"},
        "sidedness": "one-sided-upper-confidence-bound-for-sigma",
    }


def expected_certificate(pilot_path: Path, config: VerificationConfig) -> dict[str, object]:
    config.validate()
    pilot = replay_pilot(pilot_path)
    planning = {str(item["workload"]): item for item in pilot["planning"]}  # type: ignore[index]
    workloads = [
        recompute_workload(name, str(planning[name]["planned_sigma_tps"]), str(planning[name]["baseline_mean_tps"]), config)
        for name in WORKLOADS
    ]
    return {
        "canonical_json": CANONICAL_JSON,
        "inputs": {"pilot": pilot},
        "model": {
            "baseline_floor_scale": "pilot-baseline-mean-tps-held-fixed-within-each-operating-condition",
            "confidence_interval": "paired-mean-plus-or-minus-student-t-critical-times-sample-sd-over-sqrt-n",
            "estimand": "arithmetic-mean-of-paired-variant-minus-baseline-tps-differences",
            "normal_model": "paired-difference-normal-sufficient-statistics",
            "paired_difference_variance": "Var(variant)+Var(baseline)-2*Cov(variant,baseline)",
            "pilot_dependence_capture": "max-of-pair-sd-and-scaled-five-pair-block-mean-sd",
            "rng_algorithm": RNG_ALGORITHM,
            "t_quantile_algorithm": T_QUANTILE_ALGORITHM,
        },
        "policy": {
            "arm_failure_target": _frac(ARM_FAILURE),
            "candidate_grid": {
                "effective_minimum": 30,
                "maximum": config.n_max,
                "registered_minimum": config.n_min,
                "step": 10,
                "values": list(grid(config.n_min, config.n_max)),
            },
            "certification": {
                "alpha_accounting": "exact-rational-three-conditions-all-attempts-per-workload",
                "all_attempts_per_condition_alpha": _frac(Fraction(1, 60)),
                "all_attempts_total_alpha": _frac(FAMILY_ALPHA),
                "condition_alpha_at_attempt_j": "1/(60*j*(j+1))",
                "condition_count": 3,
                "exact_bound_algorithm": EXACT_BOUND_ALGORITHM,
                "failure_action": "continue-to-next-search-passing-realizable-n",
                "family_alpha": _frac(FAMILY_ALPHA),
                "trials": config.certification_trials,
            },
            "classification_operators": {
                "bounded-within-floor": {
                    "lower": {"endpoint": "difference-lower", "operator": ">=", "threshold": "-floor-boundary"},
                    "upper": {"endpoint": "difference-upper", "operator": "<=", "threshold": "+floor-boundary"},
                },
                "fallback": "unresolved",
                "resolved-beyond-floor": {
                    "improvement": {"endpoint": "difference-lower", "operator": ">", "threshold": "+floor-boundary"},
                    "regression": {"endpoint": "difference-upper", "operator": "<", "threshold": "-floor-boundary"},
                },
            },
            "conditions": [
                {
                    "delta_from_baseline_mean": _frac(delta),
                    "name": name,
                    "success": {"classification": classification, "direction": direction},
                }
                for name, delta, classification, direction in CASES
            ],
            "floor": _frac(FLOOR),
            "pilot_observation_rule": "values-determine-registered-summary-statistics-not-formulas-grid-or-success-rule",
            "required_probability": _frac(REQUIRED),
            "root_seed": {"algorithm": "sha256", "digest": ROOT_SEED_DIGEST, "encoding": "ascii", "preimage": ROOT_SEED_PREIMAGE},
            "search": {"method": "ascending-realizable-n-until-first-certification-pass", "pass_operator": ">=", "trials": config.search_trials},
            "seed_grammar": SEED_GRAMMAR,
            "selected_rule": "first-n-with-all-certification-lower-bounds-at-least-required-probability",
            "sigma_derivation": _sigma_policy(),
            "target_arm_mapping": [
                {"baseline": ARMS[name]["baseline"], "variant": ARMS[name]["variant"], "workload": name}
                for name in WORKLOADS
            ],
        },
        "replay_claim": "source-separated-replay-of-the-same-rules-not-an-independent-oracle",
        "runtime": runtime_contract(),
        "schema_version": SCHEMA,
        "status": "selected" if all(item["selected"] is not None for item in workloads) else "no-passing-n",
        "workloads": workloads,
    }


def _difference(expected: object, observed: object, path: str = "$") -> str | None:
    if type(expected) is not type(observed):
        return f"{path}: type differs"
    if type(expected) is dict:
        if set(expected) != set(observed):
            return f"{path}: keys differ"
        for key in sorted(expected):
            found = _difference(expected[key], observed[key], f"{path}.{key}")
            if found:
                return found
        return None
    if type(expected) is list:
        if len(expected) != len(observed):
            return f"{path}: length differs"
        for index, (left, right) in enumerate(zip(expected, observed)):
            found = _difference(left, right, f"{path}[{index}]")
            if found:
                return found
        return None
    return None if expected == observed else f"{path}: value differs"


def verify_certificate(certificate_path: Path, pilot_path: Path, config: VerificationConfig) -> str:
    observed, raw = load_certificate(certificate_path)
    if observed.get("runtime") != runtime_contract():
        raise VerificationError("certificate runtime differs")
    expected = expected_certificate(pilot_path, config)
    difference = _difference(expected, observed)
    if difference:
        raise VerificationError(f"certificate does not match source-separated replay: {difference}")
    return hashlib.sha256(raw).hexdigest()


def _source_record(path: Path) -> dict[str, str]:
    return {"path": path.relative_to(REPO_ROOT).as_posix(), "sha256": hashlib.sha256(_read(path, "source")).hexdigest()}


def build_replay_receipt(
    certificate_path: Path, pilot_path: Path, certificate_digest: str,
    config: VerificationConfig,
) -> dict[str, object]:
    pilot_raw = _read(pilot_path, "pilot input")
    return {
        "certificate": {"path": certificate_path.as_posix(), "sha256": certificate_digest},
        "pilot": {"path": pilot_path.as_posix(), "sha256": hashlib.sha256(pilot_raw).hexdigest()},
        "replay_claim": "source-separated-replay-of-the-same-rules-not-an-independent-oracle",
        "runtime": runtime_contract(),
        "schema_version": RECEIPT_SCHEMA,
        "sources": {"generator": _source_record(GENERATOR_SOURCE), "verifier": _source_record(VERIFIER_SOURCE)},
        "verification": {
            "candidate_grid": list(grid(config.n_min, config.n_max)),
            "certification_trials": config.certification_trials,
            "root_seed": config.root_seed,
            "search_trials": config.search_trials,
            "status": "verified",
        },
    }


def load_replay_receipt(path: Path) -> tuple[dict[str, object], bytes]:
    raw = _read(path, "replay receipt")
    value = _parse(raw, "replay receipt")
    if value.get("schema_version") != RECEIPT_SCHEMA:
        raise VerificationError("replay receipt schema differs")
    if canonical_bytes(value) != raw:
        raise VerificationError("replay receipt is not canonical JSON")
    return value, raw


def verify_replay_receipt(
    receipt_path: Path,
    certificate_path: Path,
    pilot_path: Path,
    config: VerificationConfig,
) -> str:
    observed, raw = load_replay_receipt(receipt_path)
    certificate_digest = verify_certificate(certificate_path, pilot_path, config)
    expected = build_replay_receipt(
        certificate_path, pilot_path, certificate_digest, config
    )
    difference = _difference(expected, observed)
    if difference:
        raise VerificationError(f"replay receipt binding differs: {difference}")
    return hashlib.sha256(raw).hexdigest()


def write_new_receipt(path: Path, raw: bytes) -> None:
    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC, 0o644)
        view = memoryview(raw)
        while view:
            count = os.write(descriptor, view)
            if count <= 0:
                raise VerificationError("receipt write made no progress")
            view = view[count:]
        os.fsync(descriptor)
    except OSError as exc:
        raise VerificationError(f"cannot exclusively create replay receipt: {path}: {exc}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _positive_arg(text: str) -> int:
    try:
        value = int(text, 10)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a base-10 integer") from exc
    if value < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--certificate", required=True, type=Path)
    parser.add_argument("--pilot", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--root-seed", required=True)
    parser.add_argument("--search-trials", required=True, type=_positive_arg)
    parser.add_argument("--certification-trials", required=True, type=_positive_arg)
    parser.add_argument("--n-min", required=True, type=_positive_arg)
    parser.add_argument("--n-max", required=True, type=_positive_arg)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    config = VerificationConfig(args.root_seed, args.search_trials, args.certification_trials, args.n_min, args.n_max)
    try:
        digest = verify_certificate(args.certificate, args.pilot, config)
        receipt = build_replay_receipt(args.certificate, args.pilot, digest, config)
        raw = canonical_bytes(receipt)
        receipt_digest = hashlib.sha256(raw).hexdigest()
        print(
            f"source-separated replay verified {args.certificate} sha256={digest} "
            f"receipt={args.receipt} receipt_sha256={receipt_digest}",
            flush=True,
        )
        write_new_receipt(args.receipt, raw)
    except VerificationError as exc:
        print(f"verification failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
