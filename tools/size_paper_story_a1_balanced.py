#!/usr/bin/env python3
"""Generate the preregistered sizing certificate for balanced A-1 pairs.

The pilot contributes measured scale only.  Every formula, probability,
candidate, seed domain, and stopping rule below is frozen before pilot data is
read.  The Monte Carlo model uses the sufficient statistics of a Normal sample
mean and sample variance, so it does not allocate a ``trials by n`` array.
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


SCHEMA = "paper-story-a1-balanced-sizing-certificate/v1"
PILOT_SCHEMA = "paper-story-a1-balanced-sizing-pilot/v1"
PILOT_STUDY_ID = "paper-story-a1-20260901-balanced5-pilot-v1"
CANONICAL_JSON = "utf8-sort-keys-compact-no-nonfinite-final-lf/v1"
SEED_GRAMMAR = "paper-story-a1-balanced-sizing-seed/v1"
ROOT_SEED_PREIMAGE = (
    "paper-story-a1-balanced-sizing-root-seed/v1|20260901|"
    "paired-mean-block-sigma"
)
ROOT_SEED_ALGORITHM = "sha256"
ROOT_SEED_ENCODING = "ascii"
ROOT_SEED_DIGEST = "e72bc005d156caea2c89085c563c72fa04bbeb4afd98160fca968da9a7f6b3b3"
if hashlib.sha256(ROOT_SEED_PREIMAGE.encode("ascii")).hexdigest() != ROOT_SEED_DIGEST:
    raise RuntimeError("registered root seed preimage and digest differ")

RNG_ALGORITHM = "numpy-pcg64-normal-chisquare-sufficient-statistics/v1"
T_QUANTILE_ALGORITHM = "regularized-beta-bisection/v1"
CHI_SQUARE_QUANTILE_ALGORITHM = "regularized-gamma-bisection/v1"
EXACT_BOUND_ALGORITHM = "one-sided-exact-clopper-pearson-lower/v1"

WORKLOADS = ("write-heavy", "balanced", "read-heavy")
TARGET_ARM_MAPPING = {
    "write-heavy": {"variant": "fixed10", "baseline": "no-backoff"},
    "balanced": {"variant": "fixed5", "baseline": "no-backoff"},
    "read-heavy": {"variant": "fixed2", "baseline": "no-backoff"},
}
CONDITIONS = (
    ("zero", Fraction(0, 1), "bounded-within-floor", None),
    ("positive-two-floor", Fraction(3, 50), "resolved-beyond-floor", "improvement"),
    ("negative-two-floor", Fraction(-3, 50), "resolved-beyond-floor", "regression"),
)
FLOOR = Fraction(3, 100)
FAMILY_ALPHA = Fraction(1, 20)
ARM_FAILURE = Fraction(1, 120)
REQUIRED_PROBABILITY = Fraction(4, 5)
ALPHA_C = Fraction(1, 20)
PAIR_COUNT = 60
PAIR_DF = 59
BLOCK_SIZE = 5
BLOCK_COUNT = 12
BLOCK_DF = 11
CANDIDATE_STEP = 10
REGISTERED_N_MIN = 28
EFFECTIVE_N_MIN = 30

_ROOT_SEED_RE = re.compile(r"[0-9a-f]{64}\Z")
_ROW_KEYS = frozenset(
    {
        "arm",
        "block",
        "block_position",
        "ended_at_ns",
        "group",
        "pair_index",
        "started_at_ns",
        "tps",
    }
)


class SizingError(RuntimeError):
    """The sizing contract or an input is invalid."""


@dataclass(frozen=True)
class SizingConfig:
    root_seed: str
    search_trials: int
    certification_trials: int
    n_min: int
    n_max: int

    def validate(self) -> None:
        if not _ROOT_SEED_RE.fullmatch(self.root_seed):
            raise SizingError("root seed must be exactly 64 lowercase hex characters")
        if self.root_seed != ROOT_SEED_DIGEST:
            raise SizingError("root seed differs from the registered digest")
        for label, value in (
            ("search trials", self.search_trials),
            ("certification trials", self.certification_trials),
            ("n-min", self.n_min),
            ("n-max", self.n_max),
        ):
            if type(value) is not int:
                raise SizingError(f"{label} must be an integer")
        if not 1 <= self.search_trials <= 1_000_000:
            raise SizingError("search trials must be in 1..1000000")
        if not 1 <= self.certification_trials <= 1_000_000:
            raise SizingError("certification trials must be in 1..1000000")
        if not REGISTERED_N_MIN <= self.n_min <= self.n_max <= 4096:
            raise SizingError("candidate range must satisfy 28 <= n-min <= n-max <= 4096")
        if self.n_max < EFFECTIVE_N_MIN:
            raise SizingError("candidate range contains no realizable multiple of ten")


def _fraction(value: Fraction) -> dict[str, int]:
    return {"denominator": value.denominator, "numerator": value.numerator}


def _decimal(value: float) -> str:
    if not math.isfinite(value):
        raise SizingError("attempted to serialize a non-finite decimal")
    return format(value, ".17g")


def certification_condition_alpha(attempt: int) -> Fraction:
    if type(attempt) is not int or attempt < 1:
        raise SizingError("certification attempt must be a positive integer")
    return Fraction(1, 60 * attempt * (attempt + 1))


def candidate_grid(n_min: int, n_max: int) -> tuple[int, ...]:
    if type(n_min) is not int or type(n_max) is not int:
        raise SizingError("candidate bounds must be integers")
    first = max(EFFECTIVE_N_MIN, ((n_min + CANDIDATE_STEP - 1) // CANDIDATE_STEP) * CANDIDATE_STEP)
    return tuple(range(first, n_max + 1, CANDIDATE_STEP))


def _alpha_spending_summary(attempt_count: int) -> dict[str, object]:
    spent = sum(
        (len(CONDITIONS) * certification_condition_alpha(j) for j in range(1, attempt_count + 1)),
        Fraction(0, 1),
    )
    if spent > FAMILY_ALPHA:
        raise SizingError("certification alpha spending exceeds family alpha")
    return {
        "attempt_count": attempt_count,
        "condition_count": len(CONDITIONS),
        "family_alpha_cap": _fraction(FAMILY_ALPHA),
        "spent": _fraction(spent),
        "within_cap": True,
    }


def _reject_constant(value: str) -> None:
    raise SizingError(f"non-finite JSON constant is prohibited: {value}")


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SizingError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _strict_json(raw: bytes, label: str) -> dict[str, object]:
    try:
        value = json.loads(
            raw.decode("utf-8"),
            parse_constant=_reject_constant,
            object_pairs_hook=_no_duplicate_keys,
        )
    except (UnicodeError, json.JSONDecodeError, SizingError) as exc:
        raise SizingError(f"{label} is not strict UTF-8 JSON: {exc}") from exc
    if type(value) is not dict:
        raise SizingError(f"{label} top level must be an object")
    return value


def _read_regular(path: Path, label: str) -> bytes:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise SizingError("O_NOFOLLOW is required")
    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | nofollow)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise SizingError(f"{label} must be a regular non-symlink file")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)
    except OSError as exc:
        raise SizingError(f"cannot read {label}: {path}: {exc}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _finite_positive(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SizingError(f"{label} must be an uncoerced numeric value")
    try:
        clean = float(value)
    except (OverflowError, ValueError) as exc:
        raise SizingError(f"{label} must be finite positive") from exc
    if not math.isfinite(clean) or clean <= 0.0:
        raise SizingError(f"{label} must be finite positive")
    return clean


def _exact_int(value: object, label: str, lower: int, upper: int) -> int:
    if type(value) is not int or not lower <= value <= upper:
        raise SizingError(f"{label} must be an exact integer in {lower}..{upper}")
    return value


def _sample_sd(values: list[float]) -> float:
    if len(values) < 2:
        raise SizingError("sample SD requires at least two values")
    try:
        mean = math.fsum(values) / len(values)
        variance = math.fsum((value - mean) ** 2 for value in values) / (len(values) - 1)
        result = math.sqrt(variance)
    except (OverflowError, ValueError) as exc:
        raise SizingError("sample SD is not finite") from exc
    if not math.isfinite(result):
        raise SizingError("sample SD is not finite")
    return result


def _regularized_gamma_p(shape: float, x: float) -> float:
    if shape <= 0.0 or x < 0.0:
        raise SizingError("regularized gamma arguments are invalid")
    if x == 0.0:
        return 0.0
    tiny = 1e-300
    if x < shape + 1.0:
        term = 1.0 / shape
        total = term
        ap = shape
        for _ in range(1, 1001):
            ap += 1.0
            term *= x / ap
            total += term
            if abs(term) <= abs(total) * 3e-15:
                return total * math.exp(-x + shape * math.log(x) - math.lgamma(shape))
        raise SizingError("regularized gamma series did not converge")
    b = x + 1.0 - shape
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for index in range(1, 1001):
        an = -index * (index - shape)
        b += 2.0
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        step = d * c
        h *= step
        if abs(step - 1.0) <= 3e-15:
            q = math.exp(-x + shape * math.log(x) - math.lgamma(shape)) * h
            return 1.0 - q
    raise SizingError("regularized gamma continued fraction did not converge")


def chi_square_quantile(probability: Fraction, df: int) -> float:
    if not Fraction(0, 1) < probability < Fraction(1, 1) or type(df) is not int or df < 1:
        raise SizingError("chi-square quantile arguments are invalid")
    target = float(probability)
    low = 0.0
    high = float(df)
    while _regularized_gamma_p(df / 2.0, high / 2.0) < target:
        high *= 2.0
    for _ in range(100):
        middle = (low + high) / 2.0
        if _regularized_gamma_p(df / 2.0, middle / 2.0) < target:
            low = middle
        else:
            high = middle
    return (low + high) / 2.0


def chi_square_upper_sd_factor(alpha: Fraction, df: int) -> float:
    return math.sqrt(df / chi_square_quantile(alpha, df))


def _beta_continued_fraction(a: float, b: float, x: float) -> float:
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    tiny = 1e-300
    c = 1.0
    d = 1.0 - qab * x / qap
    d = 1.0 / (tiny if abs(d) < tiny else d)
    result = d
    for iteration in range(1, 501):
        twice = 2 * iteration
        aa = iteration * (b - iteration) * x / ((qam + twice) * (a + twice))
        d = 1.0 + aa * d
        d = tiny if abs(d) < tiny else d
        c = 1.0 + aa / c
        c = tiny if abs(c) < tiny else c
        d = 1.0 / d
        result *= d * c
        aa = -(a + iteration) * (qab + iteration) * x / ((a + twice) * (qap + twice))
        d = 1.0 + aa * d
        d = tiny if abs(d) < tiny else d
        c = 1.0 + aa / c
        c = tiny if abs(c) < tiny else c
        d = 1.0 / d
        step = d * c
        result *= step
        if abs(step - 1.0) <= 3e-14:
            return result
    raise SizingError("incomplete beta continued fraction did not converge")


def _regularized_beta(x: float, a: float, b: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    factor = math.exp(
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + a * math.log(x) + b * math.log1p(-x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return factor * _beta_continued_fraction(a, b, x) / a
    return 1.0 - factor * _beta_continued_fraction(b, a, 1.0 - x) / b


def student_t_quantile(probability: Fraction, df: int) -> float:
    if not Fraction(1, 2) < probability < Fraction(1, 1) or type(df) is not int or df < 1:
        raise SizingError("Student t quantile arguments are invalid")
    target = float(probability)
    low, high = 0.0, 1.0

    def cdf(value: float) -> float:
        x = df / (df + value * value)
        return 1.0 - 0.5 * _regularized_beta(x, df / 2.0, 0.5)

    while cdf(high) < target:
        high *= 2.0
    for _ in range(100):
        middle = (low + high) / 2.0
        if cdf(middle) < target:
            low = middle
        else:
            high = middle
    return (low + high) / 2.0


def clopper_pearson_lower(success: int, trials: int, alpha: Fraction) -> float:
    if type(success) is not int or type(trials) is not int or not 0 <= success <= trials or trials < 1:
        raise SizingError("binomial counts are invalid")
    if not Fraction(0, 1) < alpha < Fraction(1, 1):
        raise SizingError("binomial alpha is invalid")
    if success == 0:
        return 0.0
    target = float(alpha)
    low, high = 0.0, 1.0
    for _ in range(100):
        middle = (low + high) / 2.0
        if _regularized_beta(middle, float(success), float(trials - success + 1)) < target:
            low = middle
        else:
            high = middle
    return (low + high) / 2.0


def _sigma_policy() -> dict[str, object]:
    return {
        "alpha_c": _fraction(ALPHA_C),
        "block": {
            "chi_square_coefficient_applied": True,
            "d1296_explicitly_specified_block_coefficient": False,
            "df": BLOCK_DF,
            "formula": "sqrt(5) * c(one-sided, alpha_c, df=11) * sd(12 five-pair block means)",
            "reason": "conservative-choice-because-coefficient-increases-sigma-and-repetitions",
        },
        "chi_square_quantile_algorithm": CHI_SQUARE_QUANTILE_ALGORITHM,
        "coefficient": "sqrt(df / chi-square-quantile(alpha_c, df))",
        "pair": {
            "df": PAIR_DF,
            "formula": "c(one-sided, alpha_c, df=59) * sd(60 paired differences)",
        },
        "planned": {"formula": "max(sigma_pair, sigma_block)"},
        "sidedness": "one-sided-upper-confidence-bound-for-sigma",
    }


def derive_pilot(path: Path) -> dict[str, object]:
    raw = _read_regular(path, "pilot input")
    digest = hashlib.sha256(raw).hexdigest()
    document = _strict_json(raw, "pilot input")
    if set(document) != {"final_estimate_eligible", "schema_version", "study_id", "workloads"}:
        raise SizingError("pilot top-level keys differ")
    if document["schema_version"] != PILOT_SCHEMA:
        raise SizingError("pilot schema differs")
    if document["study_id"] != PILOT_STUDY_ID:
        raise SizingError("pilot study ID differs")
    if document["final_estimate_eligible"] is not False:
        raise SizingError("pilot must be ineligible for the final estimate")
    workloads = document["workloads"]
    if type(workloads) is not list or len(workloads) != len(WORKLOADS):
        raise SizingError("pilot workloads must contain exactly three entries")
    planning: list[dict[str, object]] = []
    for workload_index, name in enumerate(WORKLOADS):
        item = workloads[workload_index]
        if type(item) is not dict or set(item) != {"observations", "workload"} or item.get("workload") != name:
            raise SizingError(f"pilot workload order or shape differs at {name}")
        rows = item["observations"]
        if type(rows) is not list or len(rows) != 2 * PAIR_COUNT:
            raise SizingError(f"pilot observation count differs for {name}")
        mapping = TARGET_ARM_MAPPING[name]
        allowed_arms = {mapping["variant"], mapping["baseline"]}
        by_pair: dict[int, dict[str, tuple[float, int, int]]] = {}
        intervals: list[tuple[int, int]] = []
        for row_index, row in enumerate(rows):
            label = f"pilot {name} observation {row_index}"
            if type(row) is not dict or set(row) != _ROW_KEYS:
                raise SizingError(f"{label} keys differ")
            arm = row["arm"]
            if type(arm) is not str or arm not in allowed_arms:
                raise SizingError(f"{label} arm differs")
            pair = _exact_int(row["pair_index"], f"{label} pair_index", 0, PAIR_COUNT - 1)
            group = _exact_int(row["group"], f"{label} group", 0, PAIR_COUNT // 10 - 1)
            block = _exact_int(row["block"], f"{label} block", 0, BLOCK_COUNT - 1)
            position = _exact_int(row["block_position"], f"{label} block_position", 0, BLOCK_SIZE - 1)
            if group != pair // 10 or block != pair // BLOCK_SIZE or position != pair % BLOCK_SIZE:
                raise SizingError(f"{label} schedule coordinates differ")
            tps = _finite_positive(row["tps"], f"{label} tps")
            start = _exact_int(row["started_at_ns"], f"{label} started_at_ns", 1, 2**63 - 1)
            end = _exact_int(row["ended_at_ns"], f"{label} ended_at_ns", 1, 2**63 - 1)
            if end <= start:
                raise SizingError(f"{label} timestamp interval is not positive")
            pair_rows = by_pair.setdefault(pair, {})
            if arm in pair_rows:
                raise SizingError(f"duplicate pilot arm at {name} pair {pair}")
            pair_rows[arm] = (tps, start, end)
            intervals.append((start, end))
        if sorted(intervals) != intervals or any(left[1] > right[0] for left, right in zip(intervals, intervals[1:])):
            raise SizingError(f"pilot observations are not chronological non-overlapping rows: {name}")
        differences: list[float] = []
        baselines: list[float] = []
        order_by_block: list[str] = []
        for pair in range(PAIR_COUNT):
            pair_rows = by_pair.get(pair)
            if pair_rows is None or set(pair_rows) != allowed_arms:
                raise SizingError(f"pilot pair arm set differs: {name}/{pair}")
            variant = pair_rows[mapping["variant"]]
            baseline = pair_rows[mapping["baseline"]]
            difference = variant[0] - baseline[0]
            if not math.isfinite(difference):
                raise SizingError(f"pilot paired difference is not finite: {name}/{pair}")
            differences.append(difference)
            baselines.append(baseline[0])
        for block in range(BLOCK_COUNT):
            first_pair = block * BLOCK_SIZE
            variant_rows = [by_pair[index][mapping["variant"]] for index in range(first_pair, first_pair + BLOCK_SIZE)]
            baseline_rows = [by_pair[index][mapping["baseline"]] for index in range(first_pair, first_pair + BLOCK_SIZE)]
            if max(row[2] for row in variant_rows) <= min(row[1] for row in baseline_rows):
                order_by_block.append("variant-first")
            elif max(row[2] for row in baseline_rows) <= min(row[1] for row in variant_rows):
                order_by_block.append("baseline-first")
            else:
                raise SizingError(f"pilot five-pair arm block order differs: {name}/{block}")
        if order_by_block.count("variant-first") != 6 or order_by_block.count("baseline-first") != 6:
            raise SizingError(f"pilot block lead balance differs: {name}")
        for group in range(PAIR_COUNT // 10):
            if set(order_by_block[group * 2 : group * 2 + 2]) != {"variant-first", "baseline-first"}:
                raise SizingError(f"pilot group order balance differs: {name}/{group}")
        block_means = [
            math.fsum(differences[start : start + BLOCK_SIZE]) / BLOCK_SIZE
            for start in range(0, PAIR_COUNT, BLOCK_SIZE)
        ]
        pair_sd = _sample_sd(differences)
        block_mean_sd = _sample_sd(block_means)
        pair_factor = chi_square_upper_sd_factor(ALPHA_C, PAIR_DF)
        block_factor = chi_square_upper_sd_factor(ALPHA_C, BLOCK_DF)
        sigma_pair = pair_factor * pair_sd
        sigma_block = math.sqrt(BLOCK_SIZE) * block_factor * block_mean_sd
        planned_sigma = max(sigma_pair, sigma_block)
        try:
            baseline_mean = math.fsum(baselines) / PAIR_COUNT
        except OverflowError as exc:
            raise SizingError(f"pilot baseline mean is not finite: {name}") from exc
        if not math.isfinite(baseline_mean) or baseline_mean <= 0.0:
            raise SizingError(f"pilot baseline mean is not finite positive: {name}")
        planning.append(
            {
                "baseline_mean_tps": _decimal(baseline_mean),
                "block_count": BLOCK_COUNT,
                "block_lead_counts": {"baseline-first": 6, "variant-first": 6},
                "block_mean_sd_tps": _decimal(block_mean_sd),
                "block_size": BLOCK_SIZE,
                "chi_square_factors": {
                    "block_df_11": _decimal(block_factor),
                    "pair_df_59": _decimal(pair_factor),
                },
                "pair_count": PAIR_COUNT,
                "pair_sd_tps": _decimal(pair_sd),
                "planned_sigma_tps": _decimal(planned_sigma),
                "sigma_block_tps": _decimal(sigma_block),
                "sigma_pair_tps": _decimal(sigma_pair),
                "workload": name,
            }
        )
    return {
        "final_estimate_eligible": False,
        "path": path.as_posix(),
        "planning": planning,
        "schema_version": PILOT_SCHEMA,
        "sha256": digest,
        "study_id": PILOT_STUDY_ID,
    }


def child_seed(
    root_seed: str,
    phase: str,
    workload: str,
    condition: str,
    n: int,
    trials: int,
    certification_attempt: int | None = None,
) -> dict[str, str]:
    if root_seed != ROOT_SEED_DIGEST or not _ROOT_SEED_RE.fullmatch(root_seed):
        raise SizingError("root seed differs")
    if phase not in {"search", "certification"}:
        raise SizingError("seed phase differs")
    if phase == "search" and certification_attempt is not None:
        raise SizingError("search seed carries a certification attempt")
    if phase == "certification" and (type(certification_attempt) is not int or certification_attempt < 1):
        raise SizingError("certification seed lacks a positive attempt")
    preimage = (
        f"{SEED_GRAMMAR}|root={root_seed}|phase={phase}|workload={workload}"
        f"|condition={condition}|n={n}|trials={trials}"
    )
    if phase == "certification":
        preimage += f"|attempt={certification_attempt}"
    return {"digest": hashlib.sha256(preimage.encode("ascii")).hexdigest(), "preimage": preimage}


def _count_outcomes(
    means: np.ndarray,
    half_widths: np.ndarray,
    boundary: float,
    classification: str,
    direction: str | None,
) -> dict[str, object]:
    invalid = ~np.isfinite(means) | ~np.isfinite(half_widths) | (half_widths < 0.0)
    low = means - half_widths
    high = means + half_widths
    valid = ~invalid
    improvement = valid & (low > boundary)
    regression = valid & (high < -boundary)
    bounded = valid & ~improvement & ~regression & (low >= -boundary) & (high <= boundary)
    unresolved = valid & ~improvement & ~regression & ~bounded
    outcomes: dict[str, object] = {
        "bounded-within-floor": int(np.count_nonzero(bounded)),
        "invalid": int(np.count_nonzero(invalid)),
        "resolved-beyond-floor": {
            "improvement": int(np.count_nonzero(improvement)),
            "regression": int(np.count_nonzero(regression)),
        },
        "unresolved": int(np.count_nonzero(unresolved)),
    }
    if classification == "bounded-within-floor" and direction is None:
        success = outcomes["bounded-within-floor"]
    elif classification == "resolved-beyond-floor" and direction in {"improvement", "regression"}:
        success = outcomes["resolved-beyond-floor"][direction]  # type: ignore[index]
    else:
        raise SizingError("condition success classification differs")
    return {"invalid": outcomes["invalid"], "outcomes": outcomes, "success": success}


def simulate_condition(
    *,
    config: SizingConfig,
    phase: str,
    workload: str,
    condition: str,
    delta: Fraction,
    success_classification: str,
    success_direction: str | None,
    n: int,
    trials: int,
    planned_sigma_tps: str,
    baseline_mean_tps: str,
    t_critical: float,
    certification_attempt: int | None = None,
) -> dict[str, object]:
    seed = child_seed(config.root_seed, phase, workload, condition, n, trials, certification_attempt)
    rng = np.random.Generator(np.random.PCG64(int(seed["digest"], 16)))
    sigma = float(planned_sigma_tps)
    baseline = float(baseline_mean_tps)
    means = baseline * float(delta) + sigma * rng.standard_normal(trials) / math.sqrt(n)
    sample_sds = sigma * np.sqrt(rng.chisquare(n - 1, size=trials) / (n - 1))
    half_widths = t_critical * sample_sds / math.sqrt(n)
    counts = _count_outcomes(means, half_widths, float(FLOOR) * baseline, success_classification, success_direction)
    return {
        "condition": condition,
        "invalid": counts["invalid"],
        "outcomes": counts["outcomes"],
        "seed": seed,
        "success": counts["success"],
        "trials": trials,
    }


SimulationFunction = Callable[..., dict[str, object]]


def size_workload(
    *,
    workload: str,
    planned_sigma_tps: str,
    baseline_mean_tps: str,
    config: SizingConfig,
    simulate: SimulationFunction = simulate_condition,
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    selected: dict[str, object] | None = None
    certification_attempt = 0
    t_probability = Fraction(1, 1) - ARM_FAILURE / 2
    for order_index, n in enumerate(candidate_grid(config.n_min, config.n_max)):
        t_critical = student_t_quantile(t_probability, n - 1)
        search_conditions = [
            simulate(
                config=config,
                phase="search",
                workload=workload,
                condition=name,
                delta=delta,
                success_classification=classification,
                success_direction=direction,
                n=n,
                trials=config.search_trials,
                planned_sigma_tps=planned_sigma_tps,
                baseline_mean_tps=baseline_mean_tps,
                t_critical=t_critical,
            )
            for name, delta, classification, direction in CONDITIONS
        ]
        search_passes = all(
            int(item["success"]) * REQUIRED_PROBABILITY.denominator
            >= config.search_trials * REQUIRED_PROBABILITY.numerator
            for item in search_conditions
        )
        certification: dict[str, object] | None = None
        if search_passes:
            certification_attempt += 1
            alpha = certification_condition_alpha(certification_attempt)
            certified = []
            for name, delta, classification, direction in CONDITIONS:
                result = simulate(
                    config=config,
                    phase="certification",
                    workload=workload,
                    condition=name,
                    delta=delta,
                    success_classification=classification,
                    success_direction=direction,
                    n=n,
                    trials=config.certification_trials,
                    planned_sigma_tps=planned_sigma_tps,
                    baseline_mean_tps=baseline_mean_tps,
                    t_critical=t_critical,
                    certification_attempt=certification_attempt,
                )
                bound = clopper_pearson_lower(int(result["success"]), config.certification_trials, alpha)
                result.update(
                    {
                        "alpha": _fraction(alpha),
                        "lower_bound": _decimal(bound),
                        "passes": bound >= float(REQUIRED_PROBABILITY),
                    }
                )
                certified.append(result)
            certification = {
                "attempt": certification_attempt,
                "condition_alpha": _fraction(alpha),
                "conditions": certified,
                "passes": all(bool(item["passes"]) for item in certified),
            }
        row = {
            "certification": certification,
            "df": n - 1,
            "n": n,
            "order_index": order_index,
            "search": {"conditions": search_conditions, "passes": search_passes},
            "t_critical": _decimal(t_critical),
        }
        rows.append(row)
        if certification is not None and certification["passes"] is True:
            selected = {
                "certification_attempt": certification_attempt,
                "df": n - 1,
                "n": n,
                "order_index": order_index,
                "t_critical": _decimal(t_critical),
            }
            break
    return {
        "baseline_mean_tps": baseline_mean_tps,
        "candidates": rows,
        "certification_alpha_spending": _alpha_spending_summary(certification_attempt),
        "planned_sigma_tps": planned_sigma_tps,
        "selected": selected,
        "status": "selected" if selected is not None else "no-passing-n",
        "workload": workload,
    }


def runtime_contract() -> dict[str, object]:
    return {
        "numpy": {"version": np.__version__},
        "python": {"implementation": platform.python_implementation(), "version": platform.python_version()},
    }


def _root_seed_policy() -> dict[str, str]:
    return {
        "algorithm": ROOT_SEED_ALGORITHM,
        "digest": ROOT_SEED_DIGEST,
        "encoding": ROOT_SEED_ENCODING,
        "preimage": ROOT_SEED_PREIMAGE,
    }


def build_certificate(pilot_path: Path, config: SizingConfig) -> dict[str, object]:
    config.validate()
    pilot = derive_pilot(pilot_path)
    planning = {str(item["workload"]): item for item in pilot["planning"]}  # type: ignore[index]
    workloads = [
        size_workload(
            workload=name,
            planned_sigma_tps=str(planning[name]["planned_sigma_tps"]),
            baseline_mean_tps=str(planning[name]["baseline_mean_tps"]),
            config=config,
        )
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
            "arm_failure_target": _fraction(ARM_FAILURE),
            "candidate_grid": {
                "effective_minimum": EFFECTIVE_N_MIN,
                "maximum": config.n_max,
                "registered_minimum": config.n_min,
                "step": CANDIDATE_STEP,
                "values": list(candidate_grid(config.n_min, config.n_max)),
            },
            "certification": {
                "alpha_accounting": "exact-rational-three-conditions-all-attempts-per-workload",
                "all_attempts_per_condition_alpha": _fraction(Fraction(1, 60)),
                "all_attempts_total_alpha": _fraction(FAMILY_ALPHA),
                "condition_alpha_at_attempt_j": "1/(60*j*(j+1))",
                "condition_count": len(CONDITIONS),
                "exact_bound_algorithm": EXACT_BOUND_ALGORITHM,
                "failure_action": "continue-to-next-search-passing-realizable-n",
                "family_alpha": _fraction(FAMILY_ALPHA),
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
                    "delta_from_baseline_mean": _fraction(delta),
                    "name": name,
                    "success": {"classification": classification, "direction": direction},
                }
                for name, delta, classification, direction in CONDITIONS
            ],
            "floor": _fraction(FLOOR),
            "pilot_observation_rule": "values-determine-registered-summary-statistics-not-formulas-grid-or-success-rule",
            "required_probability": _fraction(REQUIRED_PROBABILITY),
            "root_seed": _root_seed_policy(),
            "search": {
                "method": "ascending-realizable-n-until-first-certification-pass",
                "pass_operator": ">=",
                "trials": config.search_trials,
            },
            "seed_grammar": SEED_GRAMMAR,
            "selected_rule": "first-n-with-all-certification-lower-bounds-at-least-required-probability",
            "sigma_derivation": _sigma_policy(),
            "target_arm_mapping": [
                {"baseline": TARGET_ARM_MAPPING[name]["baseline"], "variant": TARGET_ARM_MAPPING[name]["variant"], "workload": name}
                for name in WORKLOADS
            ],
        },
        "replay_claim": "source-separated-replay-of-the-same-rules-not-an-independent-oracle",
        "runtime": runtime_contract(),
        "schema_version": SCHEMA,
        "status": "selected" if all(item["selected"] is not None for item in workloads) else "no-passing-n",
        "workloads": workloads,
    }


def canonical_json_bytes(document: dict[str, object]) -> bytes:
    try:
        return (json.dumps(document, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise SizingError(f"certificate is not canonical-JSON serializable: {exc}") from exc


def write_new_file(path: Path, raw: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC
    descriptor: int | None = None
    try:
        descriptor = os.open(path, flags, 0o644)
        view = memoryview(raw)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise SizingError("certificate write made no progress")
            view = view[written:]
        os.fsync(descriptor)
    except OSError as exc:
        raise SizingError(f"cannot exclusively create certificate: {path}: {exc}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _positive_int(text: str) -> int:
    try:
        value = int(text, 10)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a base-10 integer") from exc
    if value < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--root-seed", required=True)
    parser.add_argument("--search-trials", required=True, type=_positive_int)
    parser.add_argument("--certification-trials", required=True, type=_positive_int)
    parser.add_argument("--n-min", required=True, type=_positive_int)
    parser.add_argument("--n-max", required=True, type=_positive_int)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    config = SizingConfig(args.root_seed, args.search_trials, args.certification_trials, args.n_min, args.n_max)
    try:
        document = build_certificate(args.pilot, config)
        raw = canonical_json_bytes(document)
        write_new_file(args.output, raw)
    except SizingError as exc:
        print(f"sizing failed: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {args.output} sha256={hashlib.sha256(raw).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
