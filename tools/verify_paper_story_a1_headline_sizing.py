#!/usr/bin/env python3
"""Source-separated replay verifier for an A-1 headline sizing certificate."""
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
RECEIPT_SCHEMA = "paper-story-a1-headline-sizing-replay-receipt/v1"
GENERATOR_SOURCE_PATH = REPO_ROOT / "tools/size_paper_story_a1_headline.py"
VERIFIER_SOURCE_PATH = REPO_ROOT / "tools/verify_paper_story_a1_headline_sizing.py"
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
REQUIRED = Fraction(4, 5)
INFLATION = "2.372356"
EXPECTED_CVS = {
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
EXPECTED_PLANNED = {
    "write-heavy": "0.049224076359523236",
    "balanced": "0.07932374800890056",
    "read-heavy": "0.014590848153782116",
}
_ROOT_SEED_RE = re.compile(r"[0-9a-f]{64}\Z")


class VerificationError(RuntimeError):
    """The certificate or a source-separated replay value is invalid."""


@dataclass(frozen=True)
class VerificationConfig:
    root_seed: str
    search_trials: int
    certification_trials: int
    n_min: int
    n_max: int

    def validate(self) -> None:
        if not _ROOT_SEED_RE.fullmatch(self.root_seed):
            raise VerificationError("root seed grammar differs")
        if self.root_seed != ROOT_SEED_DIGEST:
            raise VerificationError("root seed differs from the registered digest")
        values = (
            self.search_trials,
            self.certification_trials,
            self.n_min,
            self.n_max,
        )
        if any(type(value) is not int for value in values):
            raise VerificationError("verification policy values must be integers")
        if not 1 <= self.search_trials <= 1_000_000:
            raise VerificationError("search trials outside 1..1000000")
        if not 1 <= self.certification_trials <= 1_000_000:
            raise VerificationError("certification trials outside 1..1000000")
        if not 28 <= self.n_min <= self.n_max <= 4096:
            raise VerificationError("candidate range outside 28..4096")


def _frac(value: Fraction) -> dict[str, int]:
    return {"denominator": value.denominator, "numerator": value.numerator}


def condition_alpha(attempt: int) -> Fraction:
    if type(attempt) is not int or attempt < 1:
        raise VerificationError("certification attempt must be a positive integer")
    return Fraction(1, 60 * attempt * (attempt + 1))


def _fraction_record(value: object, path: str) -> Fraction:
    if type(value) is not dict or set(value) != {"denominator", "numerator"}:
        raise VerificationError(f"{path} is not an exact rational record")
    denominator = value["denominator"]
    numerator = value["numerator"]
    if type(denominator) is not int or type(numerator) is not int or denominator < 1:
        raise VerificationError(f"{path} has invalid exact rational integers")
    result = Fraction(numerator, denominator)
    if value != _frac(result):
        raise VerificationError(f"{path} is not reduced canonical rational form")
    return result


def _dec(value: float) -> str:
    if not math.isfinite(value):
        raise VerificationError("non-finite recomputed value")
    return format(value, ".17g")


def _reject_constant(value: str) -> None:
    raise VerificationError(f"non-finite JSON constant: {value}")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise VerificationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _parse(raw: bytes, label: str) -> dict[str, object]:
    try:
        parsed = json.loads(
            raw.decode("utf-8"),
            parse_constant=_reject_constant,
            object_pairs_hook=_unique_object,
        )
    except (UnicodeError, json.JSONDecodeError, VerificationError) as exc:
        raise VerificationError(f"{label} is not strict UTF-8 JSON: {exc}") from exc
    if type(parsed) is not dict:
        raise VerificationError(f"{label} top level is not an object")
    return parsed


def _read_regular(path: Path, label: str) -> bytes:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise VerificationError("O_NOFOLLOW is required for bound file reads")
    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | nofollow)
        mode = os.fstat(descriptor).st_mode
        if not stat.S_ISREG(mode):
            raise VerificationError(f"{label} is not a regular non-symlink file")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)
    except OSError as exc:
        raise VerificationError(f"cannot read {label}: {path}: {exc}") from exc
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
                raise VerificationError(f"{label} path components must not be symlinks")
    except OSError as exc:
        raise VerificationError(
            f"cannot inspect {label} path component: {current}: {exc}"
        ) from exc


def runtime_contract() -> dict[str, object]:
    return {
        "numpy": {"version": np.__version__},
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
        },
    }


def verify_runtime_contract(certificate: dict[str, object]) -> None:
    observed = certificate.get("runtime")
    expected = runtime_contract()
    if observed != expected:
        raise VerificationError("certificate runtime differs from this replay runtime")


def canonical_bytes(value: dict[str, object]) -> bytes:
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise VerificationError(f"JSON value is not canonicalizable: {exc}") from exc
    return (text + "\n").encode("utf-8")


def load_certificate(path: Path) -> tuple[dict[str, object], bytes]:
    raw = _read_regular(path, "certificate")
    value = _parse(raw, "certificate")
    if canonical_bytes(value) != raw:
        raise VerificationError("certificate bytes are not canonical JSON")
    if value.get("schema_version") != SCHEMA:
        raise VerificationError("certificate schema differs")
    return value, raw


def _receipt_path(path: Path) -> str:
    absolute = Path(os.path.abspath(path))
    try:
        return absolute.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return absolute.as_posix()


def _source_receipt(path: Path, label: str) -> dict[str, str]:
    raw = _read_regular(path, f"{label} source")
    return {
        "path": _receipt_path(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def build_replay_receipt(
    certificate_path: Path,
    certificate_sha256: str,
    config: VerificationConfig,
) -> dict[str, object]:
    """Build the stable receipt for one successful source-separated replay."""
    config.validate()
    if not _ROOT_SEED_RE.fullmatch(certificate_sha256):
        raise VerificationError("verified certificate SHA-256 grammar differs")
    return {
        "canonical_json": CANONICAL_JSON,
        "certificate": {
            "path": _receipt_path(certificate_path),
            "sha256": certificate_sha256,
        },
        "pilot": {
            "path": PILOT_RELATIVE_PATH.as_posix(),
            "sha256": PILOT_SHA256,
        },
        "policy": {
            "certification_trials": config.certification_trials,
            "n_range": {
                "maximum": config.n_max,
                "minimum": config.n_min,
                "step": 1,
            },
            "root_seed": _root_seed_policy(),
            "search_trials": config.search_trials,
        },
        "runtime": runtime_contract(),
        "schema_version": RECEIPT_SCHEMA,
        "sources": {
            "generator": _source_receipt(
                GENERATOR_SOURCE_PATH,
                "generator",
            ),
            "verifier": _source_receipt(
                VERIFIER_SOURCE_PATH,
                "verifier",
            ),
        },
        "verification": {
            "return_code": 0,
            "status": "verified",
        },
    }


def load_replay_receipt(path: Path) -> tuple[dict[str, object], bytes]:
    raw = _read_regular(path, "replay receipt")
    value = _parse(raw, "replay receipt")
    if canonical_bytes(value) != raw:
        raise VerificationError("replay receipt bytes are not canonical JSON")
    if value.get("schema_version") != RECEIPT_SCHEMA:
        raise VerificationError("replay receipt schema differs")
    return value, raw


def write_new_receipt(path: Path, raw: bytes) -> None:
    if type(raw) is not bytes:
        raise VerificationError("replay receipt payload must be bytes")
    descriptor: int | None = None
    try:
        descriptor = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC,
            0o644,
        )
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            descriptor = None
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise VerificationError(
            f"replay receipt already exists and will not be overwritten: {path}"
        ) from exc
    except OSError as exc:
        raise VerificationError(f"cannot create replay receipt: {path}: {exc}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def require_pilot(path: Path) -> Path:
    expected = Path(os.path.abspath(REPO_ROOT / PILOT_RELATIVE_PATH))
    supplied = Path(os.path.abspath(path))
    if supplied != expected:
        raise VerificationError(f"pilot path must be {PILOT_RELATIVE_PATH.as_posix()}")
    return expected


def _read_canonical_pilot(path: Path) -> bytes:
    """Open every pilot component relative to its already-open parent."""
    require_pilot(path)
    nofollow_flag = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    if nofollow_flag is None or directory_flag is None:
        raise VerificationError(
            "canonical pilot replay requires O_NOFOLLOW and O_DIRECTORY"
        )
    names = tuple(PILOT_RELATIVE_PATH.parts)
    if (
        PILOT_RELATIVE_PATH.is_absolute()
        or len(names) == 0
        or any(name in {"", ".", ".."} for name in names)
    ):
        raise VerificationError("canonical pilot relative path is invalid")

    open_directories: list[int] = []
    pilot_descriptor: int | None = None
    flags = os.O_RDONLY | os.O_CLOEXEC | nofollow_flag | directory_flag
    try:
        open_directories.append(os.open(REPO_ROOT, flags))
        for name in names[:-1]:
            child = os.open(name, flags, dir_fd=open_directories[-1])
            open_directories.append(child)
        pilot_descriptor = os.open(
            names[-1],
            os.O_RDONLY | os.O_CLOEXEC | nofollow_flag,
            dir_fd=open_directories[-1],
        )
        if not stat.S_ISREG(os.fstat(pilot_descriptor).st_mode):
            raise VerificationError("pilot is not a regular non-symlink file")
        payload = bytearray()
        while True:
            block = os.read(pilot_descriptor, 1024 * 1024)
            if not block:
                return bytes(payload)
            payload.extend(block)
    except OSError as exc:
        raise VerificationError(f"cannot read canonical pilot: {exc}") from exc
    finally:
        if pilot_descriptor is not None:
            os.close(pilot_descriptor)
        for descriptor in reversed(open_directories):
            os.close(descriptor)


def rederive_pilot(path: Path) -> dict[str, object]:
    raw = _read_canonical_pilot(path)
    digest = hashlib.sha256(raw).hexdigest()
    if digest != PILOT_SHA256:
        raise VerificationError(f"pilot SHA-256 differs: {digest}")
    source = _parse(raw, "pilot")
    workload_values = source.get("workloads")
    if type(workload_values) is not list or len(workload_values) != 3:
        raise VerificationError("pilot workload count differs")
    if [item.get("workload") if type(item) is dict else None for item in workload_values] != list(WORKLOADS):
        raise VerificationError("pilot workload names or order differ")
    planning: list[dict[str, object]] = []
    for workload_name, workload in zip(WORKLOADS, workload_values):
        assert type(workload) is dict
        if workload.get("valid") is not True:
            raise VerificationError(f"pilot workload invalid: {workload_name}")
        arms = workload.get("arms")
        if type(arms) is not dict or set(arms) != set(PILOT_SOURCE_ARMS):
            raise VerificationError(f"pilot arms differ: {workload_name}")
        arm_rows = []
        cv_values: dict[str, float] = {}
        for arm_name in PILOT_SOURCE_ARMS:
            arm = arms[arm_name]
            if type(arm) is not dict or arm.get("name") != arm_name:
                raise VerificationError(f"pilot arm name differs: {workload_name}/{arm_name}")
            samples = arm.get("raw_tps")
            if type(samples) is not list or len(samples) != 5:
                raise VerificationError(f"pilot sample count differs: {workload_name}/{arm_name}")
            cleaned: list[float] = []
            for sample in samples:
                if isinstance(sample, bool) or not isinstance(sample, (int, float)):
                    raise VerificationError("pilot TPS is not numeric")
                number = float(sample)
                if not math.isfinite(number) or number <= 0.0:
                    raise VerificationError("pilot TPS is not finite positive")
                cleaned.append(number)
            mean = math.fsum(cleaned) / 5
            sample_variance = math.fsum((number - mean) ** 2 for number in cleaned) / 4
            cv = math.sqrt(sample_variance) / mean
            cv_text = _dec(cv)
            if cv_text != EXPECTED_CVS[workload_name][arm_name]:
                raise VerificationError(f"pilot CV differs: {workload_name}/{arm_name}")
            cv_values[arm_name] = cv
            arm_rows.append({"arm": arm_name, "cv": cv_text, "sample_count": 5})
        max_arm = max(PILOT_SOURCE_ARMS, key=cv_values.__getitem__)
        planned = _dec(cv_values[max_arm] * float(INFLATION))
        if planned != EXPECTED_PLANNED[workload_name]:
            raise VerificationError(f"planned CV differs: {workload_name}")
        planning.append(
            {
                "arm_cvs": arm_rows,
                "inflation": INFLATION,
                "max_arm": max_arm,
                "max_cv": _dec(cv_values[max_arm]),
                "planned_cv": planned,
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


def order_interval(n: int) -> tuple[int, int, Fraction]:
    denominator = 1 << n
    tail = 0
    binomial_term = 1
    selected = None
    for index in range(1, (n + 1) // 2 + 1):
        tail += binomial_term
        coverage = Fraction(denominator - 2 * tail, denominator)
        if coverage < Fraction(119, 120):
            break
        selected = (index, n - index + 1, coverage)
        binomial_term = binomial_term * (n - index + 1) // index
    if selected is None:
        raise VerificationError(f"no exact arm interval at n={n}")
    return selected


_A = (-39.69683028665376, 220.9460984245205, -275.9285104469687, 138.3577518672690, -30.66479806614716, 2.506628277459239)
_B = (-54.47609879822406, 161.5858368580409, -155.6989798598866, 66.80131188771972, -13.28068155288572)
_C = (-0.007784894002430293, -0.3223964580411365, -2.400758277161838, -2.549732539343734, 4.374664141464968, 2.938163982698783)
_D = (0.007784695709041462, 0.3224671290700398, 2.445134137142996, 3.754408661907416)


def inverse_normal(probabilities: np.ndarray) -> np.ndarray:
    p = np.asarray(probabilities, dtype=np.float64)
    if p.ndim != 1 or np.any(p <= 0.0) or np.any(p >= 1.0):
        raise VerificationError("joint order probabilities outside the open unit interval")
    answer = np.empty_like(p)
    lo = p < 0.02425
    hi = p > 0.97575
    center = ~(lo | hi)
    for mask, reflected in ((lo, False), (hi, True)):
        if np.any(mask):
            q = np.sqrt(-2.0 * (np.log1p(-p[mask]) if reflected else np.log(p[mask])))
            top = (((((_C[0] * q + _C[1]) * q + _C[2]) * q + _C[3]) * q + _C[4]) * q + _C[5])
            bottom = ((((_D[0] * q + _D[1]) * q + _D[2]) * q + _D[3]) * q + 1.0)
            answer[mask] = -top / bottom if reflected else top / bottom
    if np.any(center):
        q = p[center] - 0.5
        r = q * q
        top = (((((_A[0] * r + _A[1]) * r + _A[2]) * r + _A[3]) * r + _A[4]) * r + _A[5]) * q
        bottom = (((((_B[0] * r + _B[1]) * r + _B[2]) * r + _B[3]) * r + _B[4]) * r + 1.0)
        answer[center] = top / bottom
    return answer


def seed_record(
    config: VerificationConfig,
    phase: str,
    workload: str,
    condition: str,
    n: int,
    trials: int,
    certification_attempt: int | None = None,
) -> dict[str, str]:
    if config.root_seed != ROOT_SEED_DIGEST:
        raise VerificationError("root seed differs from the registered digest")
    if phase == "search" and certification_attempt is not None:
        raise VerificationError("search seed must not carry a certification attempt")
    if phase == "certification" and (
        type(certification_attempt) is not int or certification_attempt < 1
    ):
        raise VerificationError("certification seed requires a positive attempt")
    preimage = (
        f"{SEED_GRAMMAR}|root={config.root_seed}|phase={phase}|workload={workload}"
        f"|condition={condition}|n={n}|trials={trials}"
    )
    if phase == "certification":
        preimage += f"|attempt={certification_attempt}"
    return {
        "digest": hashlib.sha256(preimage.encode("ascii")).hexdigest(),
        "preimage": preimage,
    }


def joint_minimum_and_interval(
    rng: np.random.Generator,
    n: int,
    lower_index: int,
    trials: int,
    median: float,
    cv: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    upper_index = n - lower_index + 1
    minimum_probability = rng.beta(1, n, size=trials)
    lower_gap = rng.beta(lower_index - 1, n + 1 - lower_index, size=trials)
    lower_probability = minimum_probability + (1.0 - minimum_probability) * lower_gap
    gap_probability = rng.beta(upper_index - lower_index, n + 1 - upper_index, size=trials)
    upper_probability = lower_probability + (1.0 - lower_probability) * gap_probability
    minimum = np.nextafter(0.0, 1.0)
    maximum = np.nextafter(1.0, 0.0)
    minimum_probability = np.clip(minimum_probability, minimum, maximum)
    lower_probability = np.clip(lower_probability, minimum, maximum)
    upper_probability = np.clip(upper_probability, minimum, maximum)
    standard_deviation = median * cv
    return (
        median + standard_deviation * inverse_normal(minimum_probability),
        median + standard_deviation * inverse_normal(lower_probability),
        median + standard_deviation * inverse_normal(upper_probability),
    )


def replay_count(
    baseline: tuple[np.ndarray, np.ndarray, np.ndarray],
    variant: tuple[np.ndarray, np.ndarray, np.ndarray],
    expected_classification: str,
    expected_direction: str | None,
) -> dict[str, object]:
    b_minimum, b0, b1 = baseline
    v_minimum, v0, v1 = variant
    invalid = (
        ~np.isfinite(b_minimum) | ~np.isfinite(b0) | ~np.isfinite(b1)
        | ~np.isfinite(v_minimum) | ~np.isfinite(v0) | ~np.isfinite(v1)
        | (b_minimum <= 0.0) | (b0 <= 0.0) | (b1 <= 0.0)
        | (v_minimum <= 0.0) | (v0 <= 0.0) | (v1 <= 0.0)
        | (b_minimum > b0) | (b0 > b1)
        | (v_minimum > v0) | (v0 > v1)
    )
    low_ratio = np.full(len(b0), np.nan)
    high_ratio = np.full(len(b0), np.nan)
    np.divide(v0, b1, out=low_ratio, where=~invalid)
    np.divide(v1, b0, out=high_ratio, where=~invalid)
    invalid |= ~np.isfinite(low_ratio) | ~np.isfinite(high_ratio)
    usable = ~invalid
    improvement = usable & (low_ratio > 1.03)
    regression = usable & (high_ratio < 0.97)
    bounded = usable & ~improvement & ~regression & (low_ratio >= 0.97) & (high_ratio <= 1.03)
    unresolved = usable & ~improvement & ~regression & ~bounded
    counts: dict[str, object] = {
        "bounded-within-floor": int(np.count_nonzero(bounded)),
        "invalid": int(np.count_nonzero(invalid)),
        "resolved-beyond-floor": {
            "improvement": int(np.count_nonzero(improvement)),
            "regression": int(np.count_nonzero(regression)),
        },
        "unresolved": int(np.count_nonzero(unresolved)),
    }
    if expected_classification == "bounded-within-floor" and expected_direction is None:
        success = counts["bounded-within-floor"]
    elif (
        expected_classification == "resolved-beyond-floor"
        and expected_direction in {"improvement", "regression"}
    ):
        resolved = counts["resolved-beyond-floor"]
        assert type(resolved) is dict
        success = resolved[expected_direction]
    else:
        raise VerificationError("condition success outcome differs")
    return {"invalid": counts["invalid"], "outcomes": counts, "success": success}


def simulate(
    config: VerificationConfig,
    phase: str,
    workload: str,
    condition: str,
    delta: Fraction,
    expected_classification: str,
    expected_direction: str | None,
    n: int,
    trials: int,
    planned_cv: str,
    lower_index: int,
    certification_attempt: int | None = None,
) -> dict[str, object]:
    seed = seed_record(
        config,
        phase,
        workload,
        condition,
        n,
        trials,
        certification_attempt,
    )
    random = np.random.Generator(np.random.PCG64(int(seed["digest"], 16)))
    baseline = joint_minimum_and_interval(
        random, n, lower_index, trials, 1.0, float(planned_cv)
    )
    variant = joint_minimum_and_interval(
        random, n, lower_index, trials, 1.0 + float(delta), float(planned_cv)
    )
    counts = replay_count(
        baseline, variant, expected_classification, expected_direction
    )
    return {
        "condition": condition,
        "invalid": counts["invalid"],
        "outcomes": counts["outcomes"],
        "seed": seed,
        "success": counts["success"],
        "trials": trials,
    }


def _continued_beta(a: float, b: float, x: float) -> float:
    total = a + b
    c = 1.0
    d = 1.0 - total * x / (a + 1.0)
    tiny = 1e-300
    d = 1.0 / (tiny if abs(d) < tiny else d)
    accumulated = d
    for iteration in range(1, 401):
        even = 2 * iteration
        coefficient = iteration * (b - iteration) * x / ((a - 1.0 + even) * (a + even))
        d = 1.0 + coefficient * d
        c = 1.0 + coefficient / c
        d = 1.0 / (tiny if abs(d) < tiny else d)
        c = tiny if abs(c) < tiny else c
        accumulated *= d * c
        coefficient = -((a + iteration) * (total + iteration) * x / ((a + even) * (a + 1.0 + even)))
        d = 1.0 + coefficient * d
        c = 1.0 + coefficient / c
        d = 1.0 / (tiny if abs(d) < tiny else d)
        c = tiny if abs(c) < tiny else c
        change = d * c
        accumulated *= change
        if abs(change - 1.0) <= 3e-14:
            return accumulated
    raise VerificationError("beta continued fraction failed")


def _beta_cdf(x: float, a: int, b: int) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    multiplier = math.exp(
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + a * math.log(x) + b * math.log1p(-x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return multiplier * _continued_beta(float(a), float(b), x) / a
    return 1.0 - multiplier * _continued_beta(float(b), float(a), 1.0 - x) / b


def exact_lower(success: int, trials: int, alpha: Fraction) -> float:
    if type(success) is not int or type(trials) is not int or not 0 <= success <= trials:
        raise VerificationError("binomial counts are invalid")
    if trials < 1 or alpha <= 0 or alpha >= 1:
        raise VerificationError("binomial trial count or alpha is invalid")
    if success == 0:
        return 0.0
    low, high = 0.0, 1.0
    target = float(alpha)
    for _ in range(80):
        midpoint = (low + high) / 2.0
        if _beta_cdf(midpoint, success, trials - success + 1) < target:
            low = midpoint
        else:
            high = midpoint
    return (low + high) / 2.0


ReplayFunction = Callable[..., dict[str, object]]


def recompute_workload(
    name: str,
    planned_cv: str,
    config: VerificationConfig,
    replay: ReplayFunction = simulate,
) -> dict[str, object]:
    candidates = []
    selected = None
    certification_attempt = 0
    for n in range(config.n_min, config.n_max + 1):
        lower, upper, coverage = order_interval(n)
        searched = [
            replay(
                config, "search", name, condition, delta,
                classification, direction, n, config.search_trials,
                planned_cv, lower,
            )
            for condition, delta, classification, direction in CONDITIONS
        ]
        search_pass = all(
            int(result["success"]) * 5 >= config.search_trials * 4
            for result in searched
        )
        certified = None
        if search_pass:
            certification_attempt += 1
            alpha = condition_alpha(certification_attempt)
            results = []
            for condition, delta, classification, direction in CONDITIONS:
                result = replay(
                    config, "certification", name, condition, delta,
                    classification, direction,
                    n, config.certification_trials, planned_cv, lower,
                    certification_attempt,
                )
                bound = exact_lower(
                    int(result["success"]), config.certification_trials, alpha
                )
                result["alpha"] = _frac(alpha)
                result["lower_bound"] = _dec(bound)
                result["passes"] = bound >= 0.8
                results.append(result)
            certified = {
                "attempt": certification_attempt,
                "condition_alpha": _frac(alpha),
                "conditions": results,
                "passes": all(bool(result["passes"]) for result in results),
            }
        candidates.append(
            {
                "certification": certified,
                "n": n,
                "order_interval": {
                    "coverage": _frac(coverage),
                    "lower_index_1based": lower,
                    "upper_index_1based": upper,
                },
                "search": {"conditions": searched, "passes": search_pass},
            }
        )
        if certified is not None:
            if certified["passes"] is True:
                selected = {
                    "certification_attempt": certification_attempt,
                    "coverage": _frac(coverage),
                    "lower_index_1based": lower,
                    "n": n,
                    "upper_index_1based": upper,
                }
                break
    spent = sum(
        (
            len(CONDITIONS) * condition_alpha(attempt)
            for attempt in range(1, certification_attempt + 1)
        ),
        Fraction(0, 1),
    )
    if spent > FAMILY_ALPHA:
        raise VerificationError("recomputed certification alpha exceeds family alpha")
    return {
        "candidates": candidates,
        "certification_alpha_spending": {
            "attempt_count": certification_attempt,
            "condition_count": len(CONDITIONS),
            "family_alpha_cap": _frac(FAMILY_ALPHA),
            "spent": _frac(spent),
            "within_cap": True,
        },
        "planned_cv": planned_cv,
        "selected": selected,
        "status": "selected" if selected is not None else "no-passing-n",
        "workload": name,
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
            "delta": _frac(delta),
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
                "threshold": _frac(lower_band),
            },
            "upper": {
                "endpoint": "ratio-upper",
                "operator": "<=",
                "threshold": _frac(upper_band),
            },
        },
        "fallback": "unresolved",
        "resolved-beyond-floor": {
            "improvement": {
                "endpoint": "ratio-lower",
                "operator": ">",
                "threshold": _frac(upper_band),
            },
            "regression": {
                "endpoint": "ratio-upper",
                "operator": "<",
                "threshold": _frac(lower_band),
            },
        },
    }


def expected_certificate(pilot_path: Path, config: VerificationConfig) -> dict[str, object]:
    config.validate()
    pilot = rederive_pilot(pilot_path)
    planning = {
        str(item["workload"]): str(item["planned_cv"])
        for item in pilot["planning"]  # type: ignore[index]
    }
    workloads = [recompute_workload(name, planning[name], config) for name in WORKLOADS]
    return {
        "canonical_json": CANONICAL_JSON,
        "inputs": {"pilot": pilot},
        "model": {
            "arm_independence": "independent-normal-iid",
            "baseline_population_median": _frac(Fraction(1, 1)),
            "conditions": [
                {
                    "delta": _frac(delta),
                    "name": name,
                    "success": {
                        "classification": classification,
                        "direction": direction,
                    },
                    "variant_population_median": _frac(Fraction(1, 1) + delta),
                }
                for name, delta, classification, direction in CONDITIONS
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
            "arm_failure_target": _frac(ARM_FAILURE),
            "band": {
                "lower": _frac(Fraction(1, 1) - FLOOR),
                "upper": _frac(Fraction(1, 1) + FLOOR),
            },
            "certification": {
                "alpha_accounting": "exact-rational-three-conditions-all-attempts-per-workload",
                "all_attempts_per_condition_alpha": _frac(Fraction(1, 60)),
                "all_attempts_total_alpha": _frac(FAMILY_ALPHA),
                "condition_alpha_at_attempt_j": "1/(60*j*(j+1))",
                "condition_count": len(CONDITIONS),
                "failure_action": "continue-to-next-search-passing-n",
                "family_alpha": _frac(FAMILY_ALPHA),
                "method": "one-sided-exact-clopper-pearson-lower",
                "trials": config.certification_trials,
            },
            "classification_operators": _classification_operators(),
            "conditions": _condition_policy(),
            "family_alpha": _frac(FAMILY_ALPHA),
            "floor": _frac(FLOOR),
            "interval_family": {
                "arm_count": 6,
                "arm_failure_target": _frac(ARM_FAILURE),
                "family_alpha": _frac(FAMILY_ALPHA),
                "median_interval": "exact-binomial-order-statistic-equal-tail",
                "ratio_mapping": "rectangle-opposite-arm-endpoints",
            },
            "invalid_rule": "invalid-is-failure-with-fixed-trial-denominator",
            "n_max": config.n_max,
            "n_min": config.n_min,
            "n_range": {"maximum": config.n_max, "minimum": config.n_min, "step": 1},
            "required_probability": _frac(REQUIRED),
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
        "status": "selected" if all(item["selected"] is not None for item in workloads) else "no-passing-n",
        "workloads": workloads,
    }


def verify_exact_alpha_spending(certificate: dict[str, object]) -> None:
    """Check every stored attempt and condition using exact ``Fraction`` sums."""
    policy = certificate.get("policy")
    if type(policy) is not dict:
        raise VerificationError("certificate policy is missing")
    certification_policy = policy.get("certification")
    if type(certification_policy) is not dict:
        raise VerificationError("certificate certification policy is missing")
    if certification_policy.get("condition_alpha_at_attempt_j") != "1/(60*j*(j+1))":
        raise VerificationError("certification alpha-spending rule differs")
    all_attempts_per_condition = _fraction_record(
        certification_policy.get("all_attempts_per_condition_alpha"),
        "$.policy.certification.all_attempts_per_condition_alpha",
    )
    all_attempts_total = _fraction_record(
        certification_policy.get("all_attempts_total_alpha"),
        "$.policy.certification.all_attempts_total_alpha",
    )
    if all_attempts_per_condition != Fraction(1, 60):
        raise VerificationError("all-attempt per-condition alpha differs")
    if len(CONDITIONS) * all_attempts_per_condition != all_attempts_total:
        raise VerificationError("all-attempt three-condition alpha sum differs")
    if all_attempts_total != FAMILY_ALPHA:
        raise VerificationError("all-attempt total alpha differs from family alpha")
    if _fraction_record(
        certification_policy.get("family_alpha"),
        "$.policy.certification.family_alpha",
    ) != FAMILY_ALPHA:
        raise VerificationError("certification family alpha differs")

    workloads = certificate.get("workloads")
    if type(workloads) is not list or len(workloads) != len(WORKLOADS):
        raise VerificationError("certificate workload count differs")
    for workload_index, workload in enumerate(workloads):
        base = f"$.workloads[{workload_index}]"
        if type(workload) is not dict:
            raise VerificationError(f"{base} is not an object")
        candidates = workload.get("candidates")
        if type(candidates) is not list:
            raise VerificationError(f"{base}.candidates is not a list")
        attempt_count = 0
        spent = Fraction(0, 1)
        first_passing_attempt: int | None = None
        for row_index, row in enumerate(candidates):
            row_path = f"{base}.candidates[{row_index}]"
            if first_passing_attempt is not None:
                raise VerificationError(
                    "candidate rows continue after the first certification pass"
                )
            if type(row) is not dict:
                raise VerificationError(f"{row_path} is not an object")
            certification = row.get("certification")
            if certification is None:
                continue
            if type(certification) is not dict:
                raise VerificationError(f"{row_path}.certification is malformed")
            attempt_count += 1
            if certification.get("attempt") != attempt_count:
                raise VerificationError("certification attempts are not consecutive")
            expected_alpha = condition_alpha(attempt_count)
            if _fraction_record(
                certification.get("condition_alpha"),
                f"{row_path}.certification.condition_alpha",
            ) != expected_alpha:
                raise VerificationError("certification condition alpha differs")
            conditions = certification.get("conditions")
            if type(conditions) is not list or len(conditions) != len(CONDITIONS):
                raise VerificationError("certification condition count differs")
            for condition_index, condition in enumerate(conditions):
                if type(condition) is not dict:
                    raise VerificationError("certification condition is malformed")
                observed_alpha = _fraction_record(
                    condition.get("alpha"),
                    f"{row_path}.certification.conditions[{condition_index}].alpha",
                )
                if observed_alpha != expected_alpha:
                    raise VerificationError("per-condition certification alpha differs")
                spent += observed_alpha
            if spent > FAMILY_ALPHA:
                raise VerificationError("certification alpha spending exceeds family alpha")
            if certification.get("passes") is True:
                if first_passing_attempt is not None:
                    raise VerificationError("certification continues after the first pass")
                first_passing_attempt = attempt_count

        summary = workload.get("certification_alpha_spending")
        if type(summary) is not dict:
            raise VerificationError(f"{base}.certification_alpha_spending is missing")
        expected_summary = {
            "attempt_count": attempt_count,
            "condition_count": len(CONDITIONS),
            "family_alpha_cap": _frac(FAMILY_ALPHA),
            "spent": _frac(spent),
            "within_cap": True,
        }
        if summary != expected_summary:
            raise VerificationError("certification alpha-spending summary differs")
        selected = workload.get("selected")
        if first_passing_attempt is None:
            if selected is not None:
                raise VerificationError("workload is selected without a certification pass")
        elif (
            type(selected) is not dict
            or selected.get("certification_attempt") != first_passing_attempt
        ):
            raise VerificationError("selected workload is not the first certification pass")


def _first_difference(expected: object, observed: object, path: str = "$") -> str | None:
    if type(expected) is not type(observed):
        return f"{path}: type {type(observed).__name__} != {type(expected).__name__}"
    if type(expected) is dict:
        expected_dict = expected
        observed_dict = observed
        if set(expected_dict) != set(observed_dict):
            return f"{path}: keys differ"
        for key in sorted(expected_dict):
            difference = _first_difference(expected_dict[key], observed_dict[key], f"{path}.{key}")
            if difference is not None:
                return difference
        return None
    if type(expected) is list:
        if len(expected) != len(observed):
            return f"{path}: list length {len(observed)} != {len(expected)}"
        for index, (left, right) in enumerate(zip(expected, observed)):
            difference = _first_difference(left, right, f"{path}[{index}]")
            if difference is not None:
                return difference
        return None
    if expected != observed:
        return f"{path}: value differs"
    return None


def verify_certificate(
    certificate_path: Path,
    pilot_path: Path,
    config: VerificationConfig,
) -> str:
    observed, raw = load_certificate(certificate_path)
    verify_runtime_contract(observed)
    verify_exact_alpha_spending(observed)
    expected = expected_certificate(pilot_path, config)
    difference = _first_difference(expected, observed)
    if difference is not None:
        raise VerificationError(
            f"certificate does not match source-separated replay: {difference}"
        )
    return hashlib.sha256(raw).hexdigest()


def verify_replay_receipt(
    receipt_path: Path,
    certificate_path: Path,
    pilot_path: Path,
    config: VerificationConfig,
) -> str:
    observed, raw = load_replay_receipt(receipt_path)
    certificate_digest = verify_certificate(certificate_path, pilot_path, config)
    expected = build_replay_receipt(certificate_path, certificate_digest, config)
    difference = _first_difference(expected, observed)
    if difference is not None:
        raise VerificationError(f"replay receipt binding differs: {difference}")
    return hashlib.sha256(raw).hexdigest()


def _positive(text: str) -> int:
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
    parser.add_argument("--search-trials", required=True, type=_positive)
    parser.add_argument("--certification-trials", required=True, type=_positive)
    parser.add_argument("--n-min", required=True, type=_positive)
    parser.add_argument("--n-max", required=True, type=_positive)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    config = VerificationConfig(
        root_seed=args.root_seed,
        search_trials=args.search_trials,
        certification_trials=args.certification_trials,
        n_min=args.n_min,
        n_max=args.n_max,
    )
    try:
        digest = verify_certificate(args.certificate, args.pilot, config)
        receipt = build_replay_receipt(args.certificate, digest, config)
        receipt_raw = canonical_bytes(receipt)
        write_new_receipt(args.receipt, receipt_raw)
    except VerificationError as exc:
        print(f"verification failed: {exc}", file=sys.stderr)
        return 1
    receipt_digest = hashlib.sha256(receipt_raw).hexdigest()
    print(
        f"source-separated replay verified {args.certificate} sha256={digest} "
        f"receipt={args.receipt} receipt_sha256={receipt_digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
