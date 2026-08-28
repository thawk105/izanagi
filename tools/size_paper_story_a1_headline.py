#!/usr/bin/env python3
"""Generate the preregistered sizing certificate for the A-1 headline study.

The simulation jointly generates each arm's minimum and the two order
statistics needed by its exact population-median interval.  It never
materializes an ``(trials, n)`` Normal sample array.  Search and every
alpha-spending certification attempt use separately derived PCG64 streams.
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
PILOT_RELATIVE_PATH = Path(
    "output/insights/2026-08-24_paper-story-a1-paired/result.json"
)
PILOT_SHA256 = "13dabf6b148a3e5f02564e369c0a3244dd968682e110575bebc7f6bbb3662f8a"
STUDY_GENERATION = "paper-story-a1-headline-estimand-20260828-v2"
SCHEMA = "paper-story-a1-headline-sizing-certificate/v2"
CANONICAL_JSON = "utf8-sort-keys-compact-no-nonfinite-final-lf/v1"
SEED_GRAMMAR = "paper-story-a1-headline-sizing-seed/v2"
ROOT_SEED_PREIMAGE = (
    "paper-story-a1-headline-sizing-root-seed/v2|20260828|"
    "certification-alpha-spending"
)
ROOT_SEED_ALGORITHM = "sha256"
ROOT_SEED_ENCODING = "ascii"
ROOT_SEED_DIGEST = "531e720c249e561c768471ffbab1d63885a25a08868128bb5c3212843992bc16"
if (
    hashlib.sha256(ROOT_SEED_PREIMAGE.encode(ROOT_SEED_ENCODING)).hexdigest()
    != ROOT_SEED_DIGEST
):
    raise RuntimeError("registered root seed preimage and digest differ")
ORDER_ALGORITHM = "joint-uniform-minimum-and-interval-order-statistics-beta-conditional/v2"
NORMAL_INVERSE_ALGORITHM = "acklam-inverse-normal-cdf/v1"
RNG_ALGORITHM = "numpy-pcg64-generator-beta/v1"

WORKLOADS = ("write-heavy", "balanced", "read-heavy")
PILOT_SOURCE_ARMS = ("adaptive", "static10")
TARGET_ARM_MAPPING = {
    "write-heavy": {"baseline": "no-backoff", "variant": "fixed10"},
    "balanced": {"baseline": "no-backoff", "variant": "fixed5"},
    "read-heavy": {"baseline": "no-backoff", "variant": "fixed2"},
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
INFLATION = "2.372356"

# These decimal strings are the brief values.  They are still rederived from
# the bound pilot bytes on every generation and verification run.
PILOT_ARM_CVS = {
    "write-heavy": {
        "adaptive": "0.014909916574805745",
        "static10": "0.02074902601444439",
    },
    "balanced": {
        "adaptive": "0.033436696688397764",
        "static10": "0.026948333458687707",
    },
    "read-heavy": {
        "adaptive": "0.006150361983522758",
        "static10": "0.0054824266163625126",
    },
}
PLANNED_CVS = {
    "write-heavy": "0.049224076359523236",
    "balanced": "0.07932374800890056",
    "read-heavy": "0.014590848153782116",
}

_ROOT_SEED_RE = re.compile(r"[0-9a-f]{64}\Z")


class SizingError(RuntimeError):
    """The sizing contract or one of its bound inputs is invalid."""


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
            raise SizingError(
                "root seed must equal the registered SHA-256 digest "
                f"{ROOT_SEED_DIGEST}"
            )
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
        if not 28 <= self.n_min <= self.n_max <= 4096:
            raise SizingError("candidate range must satisfy 28 <= n-min <= n-max <= 4096")


def _fraction(value: Fraction) -> dict[str, int]:
    return {"denominator": value.denominator, "numerator": value.numerator}


def certification_condition_alpha(attempt: int) -> Fraction:
    """Return the registered exact per-condition alpha for attempt ``j``."""
    if type(attempt) is not int or attempt < 1:
        raise SizingError("certification attempt must be a positive integer")
    return Fraction(1, 60 * attempt * (attempt + 1))


def _alpha_spending_summary(attempt_count: int) -> dict[str, object]:
    if type(attempt_count) is not int or attempt_count < 0:
        raise SizingError("certification attempt count must be a nonnegative integer")
    spent = sum(
        (
            len(CONDITIONS) * certification_condition_alpha(attempt)
            for attempt in range(1, attempt_count + 1)
        ),
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


def _decimal(value: float) -> str:
    if not math.isfinite(value):
        raise SizingError("attempted to serialize a non-finite decimal")
    return format(value, ".17g")


def _reject_constant(value: str) -> None:
    raise SizingError(f"non-finite JSON constant is prohibited: {value}")


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SizingError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _strict_json_bytes(raw: bytes, label: str) -> dict[str, object]:
    try:
        text = raw.decode("utf-8")
        value = json.loads(
            text,
            parse_constant=_reject_constant,
            object_pairs_hook=_no_duplicate_keys,
        )
    except (UnicodeError, json.JSONDecodeError, SizingError) as exc:
        raise SizingError(f"{label} is not strict UTF-8 JSON: {exc}") from exc
    if type(value) is not dict:
        raise SizingError(f"{label} top level must be an object")
    return value


def _regular_file_bytes(path: Path, label: str) -> bytes:
    """Read a regular file through one O_NOFOLLOW descriptor."""
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise SizingError("O_NOFOLLOW is required for bound file reads")
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


def _reject_symlink_components(path: Path, label: str) -> None:
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    try:
        for component in absolute.parts[1:]:
            current /= component
            if stat.S_ISLNK(current.lstat().st_mode):
                raise SizingError(f"{label} path components must not be symlinks")
    except OSError as exc:
        raise SizingError(f"cannot inspect {label} path component: {current}: {exc}") from exc


def require_canonical_pilot(path: Path) -> Path:
    expected = Path(os.path.abspath(REPO_ROOT / PILOT_RELATIVE_PATH))
    supplied = Path(os.path.abspath(path))
    if supplied != expected:
        raise SizingError(f"pilot input must be {PILOT_RELATIVE_PATH.as_posix()}")
    return expected


def _canonical_pilot_bytes(path: Path) -> bytes:
    """Read the canonical pilot below one held repository-root descriptor."""
    require_canonical_pilot(path)
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory is None:
        raise SizingError(
            "O_NOFOLLOW and O_DIRECTORY are required for canonical pilot reads"
        )
    components = PILOT_RELATIVE_PATH.parts
    if (
        PILOT_RELATIVE_PATH.is_absolute()
        or not components
        or any(component in {"", ".", ".."} for component in components)
    ):
        raise SizingError("canonical pilot path components are invalid")

    directory_descriptor: int | None = None
    leaf_descriptor: int | None = None
    directory_flags = os.O_RDONLY | os.O_CLOEXEC | nofollow | directory
    try:
        directory_descriptor = os.open(REPO_ROOT, directory_flags)
        for component in components[:-1]:
            next_descriptor = os.open(
                component,
                directory_flags,
                dir_fd=directory_descriptor,
            )
            os.close(directory_descriptor)
            directory_descriptor = next_descriptor
        leaf_descriptor = os.open(
            components[-1],
            os.O_RDONLY | os.O_CLOEXEC | nofollow,
            dir_fd=directory_descriptor,
        )
        metadata = os.fstat(leaf_descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise SizingError("pilot input must be a regular non-symlink file")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(leaf_descriptor, 1024 * 1024)
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)
    except OSError as exc:
        raise SizingError(f"cannot read canonical pilot input: {exc}") from exc
    finally:
        if leaf_descriptor is not None:
            os.close(leaf_descriptor)
        if directory_descriptor is not None:
            os.close(directory_descriptor)


def runtime_contract() -> dict[str, object]:
    return {
        "numpy": {"version": np.__version__},
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
        },
    }


def derive_pilot(path: Path, *, require_canonical: bool = False) -> dict[str, object]:
    if require_canonical:
        raw = _canonical_pilot_bytes(path)
    else:
        raw = _regular_file_bytes(path, "pilot input")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != PILOT_SHA256:
        raise SizingError(f"pilot SHA-256 differs: {digest}")
    document = _strict_json_bytes(raw, "pilot input")
    workloads = document.get("workloads")
    if type(workloads) is not list or len(workloads) != len(WORKLOADS):
        raise SizingError("pilot workloads must contain the exact three workloads")

    by_name: dict[str, dict[str, object]] = {}
    for item in workloads:
        if type(item) is not dict or type(item.get("workload")) is not str:
            raise SizingError("pilot workload entry is malformed")
        name = item["workload"]
        if name in by_name:
            raise SizingError(f"duplicate pilot workload: {name}")
        by_name[name] = item
    if tuple(by_name) != WORKLOADS:
        raise SizingError("pilot workload order or names differ")

    planning: list[dict[str, object]] = []
    for workload_name in WORKLOADS:
        workload = by_name[workload_name]
        if workload.get("valid") is not True:
            raise SizingError(f"pilot workload is not valid: {workload_name}")
        arms = workload.get("arms")
        if type(arms) is not dict or set(arms) != set(PILOT_SOURCE_ARMS):
            raise SizingError(f"pilot arm set differs: {workload_name}")
        arm_rows: list[dict[str, object]] = []
        values_by_arm: dict[str, float] = {}
        for arm_name in PILOT_SOURCE_ARMS:
            arm = arms[arm_name]
            if type(arm) is not dict or arm.get("name") != arm_name:
                raise SizingError(f"pilot arm name differs: {workload_name}/{arm_name}")
            raw_tps = arm.get("raw_tps")
            if type(raw_tps) is not list or len(raw_tps) != 5:
                raise SizingError(f"pilot TPS count differs: {workload_name}/{arm_name}")
            samples: list[float] = []
            for value in raw_tps:
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise SizingError(f"pilot TPS is not numeric: {workload_name}/{arm_name}")
                clean = float(value)
                if not math.isfinite(clean) or clean <= 0.0:
                    raise SizingError(f"pilot TPS is not finite positive: {workload_name}/{arm_name}")
                samples.append(clean)
            mean = math.fsum(samples) / len(samples)
            variance = math.fsum((value - mean) ** 2 for value in samples) / (
                len(samples) - 1
            )
            cv = math.sqrt(variance) / mean
            cv_text = _decimal(cv)
            if cv_text != PILOT_ARM_CVS[workload_name][arm_name]:
                raise SizingError(
                    f"pilot CV differs for {workload_name}/{arm_name}: {cv_text}"
                )
            values_by_arm[arm_name] = cv
            arm_rows.append(
                {"arm": arm_name, "cv": cv_text, "sample_count": len(samples)}
            )
        max_arm = max(PILOT_SOURCE_ARMS, key=lambda name: values_by_arm[name])
        max_cv = values_by_arm[max_arm]
        planned_cv = _decimal(max_cv * float(INFLATION))
        if planned_cv != PLANNED_CVS[workload_name]:
            raise SizingError(f"planned CV differs for {workload_name}: {planned_cv}")
        planning.append(
            {
                "arm_cvs": arm_rows,
                "inflation": INFLATION,
                "max_arm": max_arm,
                "max_cv": _decimal(max_cv),
                "planned_cv": planned_cv,
                "workload": workload_name,
            }
        )
    return {
        "ddof": 1,
        "path": PILOT_RELATIVE_PATH.as_posix(),
        "planning": planning,
        "proxy": {
            "conditional_on_transferred_two-arm_variability": True,
            "target_arms_measured": False,
            "upper_bound_guarantee": False,
        },
        "sha256": digest,
        "source_arms": list(PILOT_SOURCE_ARMS),
    }


def median_order_interval(n: int) -> tuple[int, int, Fraction]:
    """Return the narrowest equal-tail interval meeting 119/120 coverage."""
    if type(n) is not int or n < 1:
        raise SizingError("order-statistic sample size must be positive integer")
    denominator = 1 << n
    tail = 0
    term = 1
    best: tuple[int, int, Fraction] | None = None
    for lower in range(1, (n + 1) // 2 + 1):
        tail += term
        coverage = Fraction(denominator - 2 * tail, denominator)
        if coverage < 1 - ARM_FAILURE:
            break
        best = (lower, n - lower + 1, coverage)
        term = term * (n - lower + 1) // lower
    if best is None:
        raise SizingError(f"n={n} cannot meet the arm median coverage target")
    return best


# Peter J. Acklam's inverse-normal rational approximation.  Coefficients,
# breakpoints, and the absence of an implementation-dependent refinement step
# are part of NORMAL_INVERSE_ALGORITHM.
_A = (
    -3.969683028665376e01,
    2.209460984245205e02,
    -2.759285104469687e02,
    1.383577518672690e02,
    -3.066479806614716e01,
    2.506628277459239e00,
)
_B = (
    -5.447609879822406e01,
    1.615858368580409e02,
    -1.556989798598866e02,
    6.680131188771972e01,
    -1.328068155288572e01,
)
_C = (
    -7.784894002430293e-03,
    -3.223964580411365e-01,
    -2.400758277161838e00,
    -2.549732539343734e00,
    4.374664141464968e00,
    2.938163982698783e00,
)
_D = (
    7.784695709041462e-03,
    3.224671290700398e-01,
    2.445134137142996e00,
    3.754408661907416e00,
)


def inverse_normal_cdf(probabilities: np.ndarray) -> np.ndarray:
    values = np.asarray(probabilities, dtype=np.float64)
    if values.ndim != 1 or np.any(values <= 0.0) or np.any(values >= 1.0):
        raise SizingError("inverse Normal probabilities must be a one-dimensional open-unit array")
    result = np.empty_like(values)
    low = values < 0.02425
    high = values > 0.97575
    middle = ~(low | high)
    if np.any(low):
        q = np.sqrt(-2.0 * np.log(values[low]))
        numerator = (((((_C[0] * q + _C[1]) * q + _C[2]) * q + _C[3]) * q + _C[4]) * q + _C[5])
        denominator = ((((_D[0] * q + _D[1]) * q + _D[2]) * q + _D[3]) * q + 1.0)
        result[low] = numerator / denominator
    if np.any(high):
        q = np.sqrt(-2.0 * np.log1p(-values[high]))
        numerator = (((((_C[0] * q + _C[1]) * q + _C[2]) * q + _C[3]) * q + _C[4]) * q + _C[5])
        denominator = ((((_D[0] * q + _D[1]) * q + _D[2]) * q + _D[3]) * q + 1.0)
        result[high] = -(numerator / denominator)
    if np.any(middle):
        q = values[middle] - 0.5
        r = q * q
        numerator = (((((_A[0] * r + _A[1]) * r + _A[2]) * r + _A[3]) * r + _A[4]) * r + _A[5]) * q
        denominator = (((((_B[0] * r + _B[1]) * r + _B[2]) * r + _B[3]) * r + _B[4]) * r + 1.0)
        result[middle] = numerator / denominator
    return result


def child_seed(
    root_seed: str,
    phase: str,
    workload: str,
    condition: str,
    n: int,
    trials: int,
    certification_attempt: int | None = None,
) -> dict[str, str]:
    if not _ROOT_SEED_RE.fullmatch(root_seed):
        raise SizingError("root seed grammar differs")
    if root_seed != ROOT_SEED_DIGEST:
        raise SizingError("root seed differs from the registered digest")
    if phase not in {"search", "certification"}:
        raise SizingError("seed phase is not registered")
    if phase == "search" and certification_attempt is not None:
        raise SizingError("search seed must not carry a certification attempt")
    if phase == "certification" and (
        type(certification_attempt) is not int or certification_attempt < 1
    ):
        raise SizingError("certification seed requires a positive attempt")
    if workload not in WORKLOADS or condition not in {item[0] for item in CONDITIONS}:
        raise SizingError("seed workload or condition is not registered")
    if type(n) is not int or type(trials) is not int or n < 1 or trials < 1:
        raise SizingError("seed integer field is invalid")
    preimage = (
        f"{SEED_GRAMMAR}|root={root_seed}|phase={phase}|workload={workload}"
        f"|condition={condition}|n={n}|trials={trials}"
    )
    if phase == "certification":
        preimage += f"|attempt={certification_attempt}"
    digest = hashlib.sha256(preimage.encode("ascii")).hexdigest()
    return {"digest": digest, "preimage": preimage}


def _joint_normal_minimum_and_interval(
    rng: np.random.Generator,
    *,
    n: int,
    lower_index: int,
    trials: int,
    median: float,
    cv: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    upper_index = n - lower_index + 1
    minimum_u = rng.beta(1, n, size=trials)
    lower_conditional = rng.beta(
        lower_index - 1, n + 1 - lower_index, size=trials
    )
    lower_u = minimum_u + (1.0 - minimum_u) * lower_conditional
    upper_conditional = rng.beta(
        upper_index - lower_index, n + 1 - upper_index, size=trials
    )
    upper_u = lower_u + (1.0 - lower_u) * upper_conditional
    open_low = np.nextafter(0.0, 1.0)
    open_high = np.nextafter(1.0, 0.0)
    np.clip(minimum_u, open_low, open_high, out=minimum_u)
    np.clip(lower_u, open_low, open_high, out=lower_u)
    np.clip(upper_u, open_low, open_high, out=upper_u)
    sigma = median * cv
    return (
        median + sigma * inverse_normal_cdf(minimum_u),
        median + sigma * inverse_normal_cdf(lower_u),
        median + sigma * inverse_normal_cdf(upper_u),
    )


def count_outcomes(
    baseline_minimum: np.ndarray,
    baseline_low: np.ndarray,
    baseline_high: np.ndarray,
    variant_minimum: np.ndarray,
    variant_low: np.ndarray,
    variant_high: np.ndarray,
    success_classification: str,
    success_direction: str | None,
) -> dict[str, object]:
    arrays = [
        np.asarray(value, dtype=np.float64)
        for value in (
            baseline_minimum,
            baseline_low,
            baseline_high,
            variant_minimum,
            variant_low,
            variant_high,
        )
    ]
    if any(value.ndim != 1 for value in arrays) or len({len(value) for value in arrays}) != 1:
        raise SizingError("order-statistic arrays must be one-dimensional and equal length")
    b_minimum, b_low, b_high, v_minimum, v_low, v_high = arrays
    invalid = (
        ~np.isfinite(b_minimum)
        | ~np.isfinite(b_low)
        | ~np.isfinite(b_high)
        | ~np.isfinite(v_minimum)
        | ~np.isfinite(v_low)
        | ~np.isfinite(v_high)
        | (b_minimum <= 0.0)
        | (b_low <= 0.0)
        | (b_high <= 0.0)
        | (v_minimum <= 0.0)
        | (v_low <= 0.0)
        | (v_high <= 0.0)
        | (b_minimum > b_low)
        | (b_low > b_high)
        | (v_minimum > v_low)
        | (v_low > v_high)
    )
    ratio_low = np.full(len(b_low), np.nan, dtype=np.float64)
    ratio_high = np.full(len(b_low), np.nan, dtype=np.float64)
    valid = ~invalid
    np.divide(v_low, b_high, out=ratio_low, where=valid)
    np.divide(v_high, b_low, out=ratio_high, where=valid)
    invalid |= ~np.isfinite(ratio_low) | ~np.isfinite(ratio_high)
    valid = ~invalid
    improvement = valid & (ratio_low > 1.0 + float(FLOOR))
    regression = valid & (ratio_high < 1.0 - float(FLOOR))
    bounded = (
        valid
        & ~improvement
        & ~regression
        & (ratio_low >= 1.0 - float(FLOOR))
        & (ratio_high <= 1.0 + float(FLOOR))
    )
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
    if success_classification == "bounded-within-floor" and success_direction is None:
        success = outcomes["bounded-within-floor"]
    elif (
        success_classification == "resolved-beyond-floor"
        and success_direction in {"improvement", "regression"}
    ):
        resolved = outcomes["resolved-beyond-floor"]
        assert type(resolved) is dict
        success = resolved[success_direction]
    else:
        raise SizingError("condition success outcome is invalid")
    return {
        "invalid": outcomes["invalid"],
        "outcomes": outcomes,
        "success": success,
    }


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
    planned_cv: str,
    lower_index: int,
    certification_attempt: int | None = None,
) -> dict[str, object]:
    seed = child_seed(
        config.root_seed,
        phase,
        workload,
        condition,
        n,
        trials,
        certification_attempt,
    )
    rng = np.random.Generator(np.random.PCG64(int(seed["digest"], 16)))
    baseline_minimum, baseline_low, baseline_high = _joint_normal_minimum_and_interval(
        rng,
        n=n,
        lower_index=lower_index,
        trials=trials,
        median=1.0,
        cv=float(planned_cv),
    )
    variant_median = 1.0 + float(delta)
    variant_minimum, variant_low, variant_high = _joint_normal_minimum_and_interval(
        rng,
        n=n,
        lower_index=lower_index,
        trials=trials,
        median=variant_median,
        cv=float(planned_cv),
    )
    counts = count_outcomes(
        baseline_minimum,
        baseline_low,
        baseline_high,
        variant_minimum,
        variant_low,
        variant_high,
        success_classification,
        success_direction,
    )
    return {
        "condition": condition,
        "invalid": counts["invalid"],
        "outcomes": counts["outcomes"],
        "seed": seed,
        "success": counts["success"],
        "trials": trials,
    }


def _beta_continued_fraction(a: float, b: float, x: float) -> float:
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    tiny = 1e-300
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    result = d
    for iteration in range(1, 401):
        twice = 2 * iteration
        aa = iteration * (b - iteration) * x / ((qam + twice) * (a + twice))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        result *= d * c
        aa = -(
            (a + iteration)
            * (qab + iteration)
            * x
            / ((a + twice) * (qap + twice))
        )
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        step = d * c
        result *= step
        if abs(step - 1.0) <= 3e-14:
            return result
    raise SizingError("incomplete beta continued fraction did not converge")


def _regularized_beta(x: float, a: int, b: int) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    log_factor = (
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log1p(-x)
    )
    factor = math.exp(log_factor)
    if x < (a + 1.0) / (a + b + 2.0):
        return factor * _beta_continued_fraction(float(a), float(b), x) / a
    return 1.0 - factor * _beta_continued_fraction(float(b), float(a), 1.0 - x) / b


def clopper_pearson_lower(success: int, trials: int, alpha: Fraction) -> float:
    if type(success) is not int or type(trials) is not int or not 0 <= success <= trials:
        raise SizingError("binomial counts are invalid")
    if trials < 1 or alpha <= 0 or alpha >= 1:
        raise SizingError("binomial trial count or alpha is invalid")
    if success == 0:
        return 0.0
    target = float(alpha)
    low = 0.0
    high = 1.0
    for _ in range(80):
        middle = (low + high) / 2.0
        if _regularized_beta(middle, success, trials - success + 1) < target:
            low = middle
        else:
            high = middle
    return (low + high) / 2.0


SimulationFunction = Callable[..., dict[str, object]]


def size_workload(
    *,
    workload: str,
    planned_cv: str,
    config: SizingConfig,
    simulate: SimulationFunction = simulate_condition,
) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    selected: dict[str, object] | None = None
    certification_attempt = 0
    for n in range(config.n_min, config.n_max + 1):
        lower_index, upper_index, coverage = median_order_interval(n)
        search_conditions = [
            simulate(
                config=config,
                phase="search",
                workload=workload,
                condition=name,
                delta=delta,
                success_classification=success_classification,
                success_direction=success_direction,
                n=n,
                trials=config.search_trials,
                planned_cv=planned_cv,
                lower_index=lower_index,
            )
            for name, delta, success_classification, success_direction in CONDITIONS
        ]
        search_passes = all(
            int(item["success"]) * REQUIRED_PROBABILITY.denominator
            >= config.search_trials * REQUIRED_PROBABILITY.numerator
            for item in search_conditions
        )
        certification: dict[str, object] | None = None
        if search_passes:
            certification_attempt += 1
            condition_alpha = certification_condition_alpha(certification_attempt)
            certification_conditions = []
            for name, delta, success_classification, success_direction in CONDITIONS:
                result = simulate(
                    config=config,
                    phase="certification",
                    workload=workload,
                    condition=name,
                    delta=delta,
                    success_classification=success_classification,
                    success_direction=success_direction,
                    n=n,
                    trials=config.certification_trials,
                    planned_cv=planned_cv,
                    lower_index=lower_index,
                    certification_attempt=certification_attempt,
                )
                bound = clopper_pearson_lower(
                    int(result["success"]),
                    config.certification_trials,
                    condition_alpha,
                )
                result["alpha"] = _fraction(condition_alpha)
                result["lower_bound"] = _decimal(bound)
                result["passes"] = bound >= float(REQUIRED_PROBABILITY)
                certification_conditions.append(result)
            certification = {
                "attempt": certification_attempt,
                "condition_alpha": _fraction(condition_alpha),
                "conditions": certification_conditions,
                "passes": all(bool(item["passes"]) for item in certification_conditions),
            }
        row = {
            "certification": certification,
            "n": n,
            "order_interval": {
                "coverage": _fraction(coverage),
                "lower_index_1based": lower_index,
                "upper_index_1based": upper_index,
            },
            "search": {"conditions": search_conditions, "passes": search_passes},
        }
        rows.append(row)
        if certification is not None:
            if certification["passes"] is True:
                selected = {
                    "certification_attempt": certification_attempt,
                    "coverage": _fraction(coverage),
                    "lower_index_1based": lower_index,
                    "n": n,
                    "upper_index_1based": upper_index,
                }
                break
    return {
        "candidates": rows,
        "certification_alpha_spending": _alpha_spending_summary(
            certification_attempt
        ),
        "planned_cv": planned_cv,
        "selected": selected,
        "status": "selected" if selected is not None else "no-passing-n",
        "workload": workload,
    }


def _root_seed_policy() -> dict[str, str]:
    return {
        "algorithm": ROOT_SEED_ALGORITHM,
        "digest": ROOT_SEED_DIGEST,
        "encoding": ROOT_SEED_ENCODING,
        "preimage": ROOT_SEED_PREIMAGE,
    }


def _condition_policy() -> list[dict[str, object]]:
    return [
        {
            "delta": _fraction(delta),
            "name": name,
            "success": {
                "classification": classification,
                "direction": direction,
            },
        }
        for name, delta, classification, direction in CONDITIONS
    ]


def _classification_operators() -> dict[str, object]:
    lower_band = Fraction(1, 1) - FLOOR
    upper_band = Fraction(1, 1) + FLOOR
    return {
        "bounded-within-floor": {
            "lower": {
                "endpoint": "ratio-lower",
                "operator": ">=",
                "threshold": _fraction(lower_band),
            },
            "upper": {
                "endpoint": "ratio-upper",
                "operator": "<=",
                "threshold": _fraction(upper_band),
            },
        },
        "fallback": "unresolved",
        "resolved-beyond-floor": {
            "improvement": {
                "endpoint": "ratio-lower",
                "operator": ">",
                "threshold": _fraction(upper_band),
            },
            "regression": {
                "endpoint": "ratio-upper",
                "operator": "<",
                "threshold": _fraction(lower_band),
            },
        },
    }


def build_certificate(pilot_path: Path, config: SizingConfig) -> dict[str, object]:
    config.validate()
    pilot = derive_pilot(pilot_path, require_canonical=True)
    planning_by_workload = {
        str(item["workload"]): str(item["planned_cv"])
        for item in pilot["planning"]  # type: ignore[index]
    }
    workloads = [
        size_workload(
            workload=name,
            planned_cv=planning_by_workload[name],
            config=config,
        )
        for name in WORKLOADS
    ]
    status = "selected" if all(item["selected"] is not None for item in workloads) else "no-passing-n"
    return {
        "canonical_json": CANONICAL_JSON,
        "inputs": {"pilot": pilot},
        "model": {
            "arm_independence": "independent-normal-iid",
            "baseline_population_median": _fraction(Fraction(1, 1)),
            "conditions": [
                {
                    "delta": _fraction(delta),
                    "name": name,
                    "success": {
                        "classification": success_classification,
                        "direction": success_direction,
                    },
                    "variant_population_median": _fraction(Fraction(1, 1) + delta),
                }
                for name, delta, success_classification, success_direction in CONDITIONS
            ],
            "even_n_sample_median": "arithmetic-mean-of-order-n-over-2-and-n-over-2-plus-1",
            "equal_cv_within_workload": True,
            "estimand": "median-variant-over-median-baseline-minus-1",
            "joint_order_algorithm": ORDER_ALGORITHM,
            "normal_inverse_algorithm": NORMAL_INVERSE_ALGORITHM,
            "pilot_source_arms": list(PILOT_SOURCE_ARMS),
            "ratio_interval": "variant-lower-over-baseline-upper-to-variant-upper-over-baseline-lower",
            "rng_algorithm": RNG_ALGORITHM,
            "simulated_arm_roles": {
                "baseline": "target-baseline",
                "variant": "target-variant",
            },
        },
        "policy": {
            "arm_count": 6,
            "arm_failure_target": _fraction(ARM_FAILURE),
            "band": {
                "lower": _fraction(Fraction(1, 1) - FLOOR),
                "upper": _fraction(Fraction(1, 1) + FLOOR),
            },
            "certification": {
                "alpha_accounting": "exact-rational-three-conditions-all-attempts-per-workload",
                "all_attempts_per_condition_alpha": _fraction(Fraction(1, 60)),
                "all_attempts_total_alpha": _fraction(FAMILY_ALPHA),
                "condition_alpha_at_attempt_j": "1/(60*j*(j+1))",
                "condition_count": len(CONDITIONS),
                "failure_action": "continue-to-next-search-passing-n",
                "family_alpha": _fraction(FAMILY_ALPHA),
                "method": "one-sided-exact-clopper-pearson-lower",
                "trials": config.certification_trials,
            },
            "classification_operators": _classification_operators(),
            "conditions": _condition_policy(),
            "family_alpha": _fraction(FAMILY_ALPHA),
            "floor": _fraction(FLOOR),
            "interval_family": {
                "arm_count": 6,
                "arm_failure_target": _fraction(ARM_FAILURE),
                "family_alpha": _fraction(FAMILY_ALPHA),
                "median_interval": "exact-binomial-order-statistic-equal-tail",
                "ratio_mapping": "rectangle-opposite-arm-endpoints",
            },
            "invalid_rule": "invalid-is-failure-with-fixed-trial-denominator",
            "n_max": config.n_max,
            "n_min": config.n_min,
            "n_range": {"maximum": config.n_max, "minimum": config.n_min, "step": 1},
            "required_probability": _fraction(REQUIRED_PROBABILITY),
            "pilot_source_arms": list(PILOT_SOURCE_ARMS),
            "root_seed": _root_seed_policy(),
            "search": {
                "method": "ascending-every-n-until-first-certification-pass",
                "pass_operator": ">=",
                "trials": config.search_trials,
            },
            "seed_grammar": SEED_GRAMMAR,
            "selected_rule": "first-certification-pass-among-ascending-search-passing-candidates",
            "target_arm_mapping": [
                {
                    "baseline": TARGET_ARM_MAPPING[name]["baseline"],
                    "variant": TARGET_ARM_MAPPING[name]["variant"],
                    "workload": name,
                }
                for name in WORKLOADS
            ],
        },
        "runtime": runtime_contract(),
        "schema_version": SCHEMA,
        "study_generation": STUDY_GENERATION,
        "status": status,
        "workloads": workloads,
    }


def canonical_json_bytes(document: dict[str, object]) -> bytes:
    try:
        rendered = json.dumps(
            document,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise SizingError(f"certificate is not canonicalizable: {exc}") from exc
    return (rendered + "\n").encode("utf-8")


def write_new_file(path: Path, raw: bytes) -> None:
    if type(raw) is not bytes:
        raise SizingError("certificate payload must be bytes")
    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            descriptor = None
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise SizingError(f"output already exists and will not be overwritten: {path}") from exc
    except OSError as exc:
        raise SizingError(f"cannot create output: {path}: {exc}") from exc
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
    arguments = _parser().parse_args(argv)
    config = SizingConfig(
        root_seed=arguments.root_seed,
        search_trials=arguments.search_trials,
        certification_trials=arguments.certification_trials,
        n_min=arguments.n_min,
        n_max=arguments.n_max,
    )
    try:
        if os.path.lexists(arguments.output):
            raise SizingError(
                f"output already exists and will not be overwritten: {arguments.output}"
            )
        certificate = build_certificate(arguments.pilot, config)
        raw = canonical_json_bytes(certificate)
        write_new_file(arguments.output, raw)
    except SizingError as exc:
        print(f"sizing error: {exc}", file=sys.stderr)
        return 1
    digest = hashlib.sha256(raw).hexdigest()
    print(f"wrote {arguments.output} sha256={digest} status={certificate['status']}")
    return 0 if certificate["status"] == "selected" else 2


if __name__ == "__main__":
    raise SystemExit(main())
