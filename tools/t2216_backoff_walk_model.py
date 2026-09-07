#!/usr/bin/env python3
"""Event-driven walk model for the T-2216 Silo adaptive-backoff study.

The prediction path is calibrated only from static fixed-backoff cells.  The
adaptive measurements are read by the evaluation path after prediction, never
by the walk or its calibration.  The executable writes one JSON document and
does not run CCBench or submit work to Pegasus.

Usage:
    python3 tools/t2216_backoff_walk_model.py \
        MEASURED_JSON BACKOFF_COPY OUTPUT_JSON [--score-h2]

``--score-h2`` is intentionally opt-in.  It scores balanced/read-heavy as a
post-hoc, parameter-independent consistency check.  Some adaptive values were
exposed before scoring, so this is not a blinded or preregistered holdout.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import sys
import tempfile
from typing import Any, Mapping, Sequence

import numpy as np


SCHEMA = "izanagi-t2216-backoff-walk/v2"
SOURCE_PIN = "511c9538e4e8efa54b45cda62e72389ed3b706ec"
BACKOFF_COPY_SHA256 = "3e9f548507200532c79b14b94389abbfd4f87c7c03addde0099740f2df3d8cd7"
MEASURED_INPUT_SHA256 = "f46cebdd2691e3012c4632d3d6e82a050bb262aa43a0e8dd3aa6ffd66d604931"
NOT_CERTIFIED = (
    "trace-disabled performance measurements only; no serializability check "
    "was run; this analysis is not a basis for variant adoption"
)
PROTOCOL = "Silo"
THREADS = 48
RECORDS = 1_000_000
ZIPF_SKEW = 0.9
DURATION_US = 3_000_000.0
REPETITIONS = 8
_MAX_INTERNAL_REPETITIONS = 32
BASE_SEED = 221_620_260_902
UINT64_MASK = (1 << 64) - 1
STATIC_BACKOFFS = (0.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0)
TAIL_BACKOFFS = (150, 200, 300, 500, 750, 999)
TAIL_REPORT_SCHEMA = "t2266-backoff-static-tail-report/v1"
TAIL_RUN_KIND = "t2266-tail"
TAIL_REPETITIONS = 5
STAGE1_STEPS = (0.1, 0.25, 0.5, 1.0, 5.0, 100.0)
D1475_STEPS = (0.5, 1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0)
UPDATE_INTERVALS_US = (10, 40, 160, 640, 2560)
WORKLOADS = ("write-heavy", "balanced", "read-heavy")
RESIDENCE_THRESHOLDS_US = (
    0.0, 0.5, 1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0,
    150.0, 200.0, 300.0, 500.0, 750.0, 1000.0,
)
RESIDENCE_BIN_WIDTH_US = 0.5

# Frozen before any model main run.  Kendall distance is the number of
# discordant pairs, evaluated independently inside each measurement dataset.
STAGE1_MAX_KENDALL_DISTANCE = 2
D1475_MAX_KENDALL_DISTANCE = 3
B_MAX_MIN_RATIO_LIMIT = 1.5
D1475_VALLEY_TPS = 1_241_671.0
D1475_VALLEY_RELATIVE_TOLERANCE = 0.20
H1_STEP2_MIN_CAP_RATIO = 1.5
H1_STEP05_MAX_CAP_RATIO = 1.2
H1_RATIO_RELATIVE_TOLERANCE = 0.20


# Exact copy of the pinned C++ function.  It is data for the static fidelity
# test; the executable translation below intentionally preserves its ordering.
VERBATIM_UPDATE_BACKOFF = r'''  void update_backoff(const uint64_t committed_txs) {
    uint64_t now = rdtscp();
    uint64_t time_diff = now - last_time_;
    last_time_ = now;

    double new_backoff = Backoff_.load(std::memory_order_acquire);
    double backoff_diff = new_backoff - last_backoff_;

    uint64_t committed_diff = committed_txs - last_committed_txs_;
    double committed_tput = static_cast<double>(committed_diff) /
                            (static_cast<double>(time_diff) / clocks_per_us_) *
                            pow(10.0, 6);
    double committed_tput_diff = committed_tput - last_committed_tput_;

    last_committed_txs_ = committed_txs;
    last_committed_tput_ = committed_tput;
    last_backoff_ = new_backoff;
    /*
    cout << "=====" << endl;
    cout << "committed_tput_diff:\t" <<
    static_cast<int64_t>(committed_tput_diff) << endl; cout <<
    "last_backoff_:\t" << last_backoff_ << endl; cout << "backoff_diff:\t" <<
    backoff_diff << endl;
    */

    double gradient;
    if (backoff_diff != 0)
      gradient = committed_tput_diff / backoff_diff;
    else
      gradient = 0;

    if (gradient < 0)
      new_backoff -= kIncrBackoff;
    else if (gradient > 0)
      new_backoff += kIncrBackoff;
    else {
      if ((committed_txs & 1) == 0 ||
          new_backoff == kMaxBackoff) // 確率はおよそ 1/2, すなわちランダム．
        new_backoff -= kIncrBackoff;
      else if ((committed_txs & 1) == 1 || new_backoff == kMinBackoff)
        new_backoff += kIncrBackoff;
    }

    if (new_backoff < kMinBackoff)
      new_backoff = kMinBackoff;
    else if (new_backoff > kMaxBackoff)
      new_backoff = kMaxBackoff;
    Backoff_.store(new_backoff, std::memory_order_release);
  }'''


class ModelError(RuntimeError):
    """The input or frozen model contract is invalid."""


@dataclass(frozen=True)
class WalkState:
    backoff_us: float = 0.0
    last_committed_txs: int = 0
    last_committed_tput: float = 0.0
    last_backoff: int | float = 0
    committed_txs: int = 0


@dataclass(frozen=True)
class Transition:
    state: WalkState
    time_diff_us: float
    committed_diff: int
    committed_tput: float
    committed_tput_diff: float
    backoff_diff: float
    gradient: float
    branch: str


@dataclass(frozen=True)
class Calibration:
    workload: str
    backoffs_us: tuple[float, ...]
    throughput_tps: tuple[float, ...]
    abort_rate: tuple[float, ...]
    raw_cells: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class Scenario:
    name: str
    truncate_last_backoff: bool = True
    event_driven: bool = True
    count_law: str = "poisson"
    tail: str = "primary"
    interpolation: str = "linear"


EXACT = Scenario("M_exact")
NO_TRUNC = Scenario("M_no_trunc", truncate_last_backoff=False)
NO_P4 = Scenario("M_no_P4", event_driven=False)
NO_TRUNC_NO_P4 = Scenario(
    "M_no_trunc_no_P4", truncate_last_backoff=False,
    event_driven=False,
)
NO_COUNT_NOISE = Scenario(
    "M_no_count_noise", count_law="deterministic",
)
FLAT_TAIL = Scenario("M_flat_tail", tail="flat-tail")
LINEAR_ZERO = Scenario("M_linear_zero", tail="linear-zero")
LOG_INTERP = Scenario("M_log_interp", interpolation="log")
FANO2 = Scenario("M_fano2", count_law="fano2")
FANO4 = Scenario("M_fano4", count_law="fano4")


def _fail(message: str) -> None:
    raise ModelError(message)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ModelError(f"cannot hash {path}: {exc}") from exc
    return digest.hexdigest()


def strict_json(path: Path) -> dict[str, Any]:
    """Read a finite, duplicate-key-free JSON object."""

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
            path.read_text(encoding="utf-8"),
            parse_constant=reject_constant,
            object_pairs_hook=no_duplicates,
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise ModelError(f"strict JSON cannot be read: {path}: {exc}") from exc
    if type(value) is not dict:
        _fail("measured JSON top level must be an object")
    return value


def _finite(value: object, label: str, *, lower: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(f"{label} must be numeric")
    number = float(value)
    if not math.isfinite(number) or (lower is not None and number < lower):
        _fail(f"{label} must be finite and >= {lower}")
    return number


def _cells(document: Mapping[str, Any], section: str) -> Mapping[str, Any]:
    value = document.get(section)
    if type(value) is not dict:
        _fail(f"missing object section {section!r}")
    nested = value.get("cells")
    if nested is not None:
        if type(nested) is not dict:
            _fail(f"{section}.cells must be an object")
        return nested
    return value


def _raw_cell(cell: object, label: str) -> tuple[list[float], list[float], list[str]]:
    if type(cell) is not dict or type(cell.get("reps")) is not list:
        _fail(f"{label} must contain reps[]")
    throughputs: list[float] = []
    abort_rates: list[float] = []
    jobids: list[str] = []
    for index, rep in enumerate(cell["reps"]):
        if type(rep) is not dict or type(rep.get("throughputs")) is not list:
            _fail(f"{label}.reps[{index}] must contain throughputs[]")
        values = [
            _finite(value, f"{label}.throughputs", lower=0.0)
            for value in rep["throughputs"]
        ]
        if not values:
            _fail(f"{label}.reps[{index}].throughputs must not be empty")
        throughputs.extend(values)
        abort = _finite(rep.get("abort_rate"), f"{label}.abort_rate", lower=0.0)
        if abort > 1.0:
            _fail(f"{label}.abort_rate must be <= 1")
        abort_rates.append(abort)
        jobid = rep.get("pbs_jobid")
        if type(jobid) is not str or not jobid:
            _fail(f"{label}.pbs_jobid must be a non-empty string")
        jobids.append(jobid)
    return throughputs, abort_rates, jobids


def _tail_calibration_rows(
    document: Mapping[str, Any], workload: str,
) -> list[tuple[float, float, float, dict[str, Any]]]:
    """Validate one T-2266 report and return its six static mean rows."""
    required = {
        "schema_version": TAIL_REPORT_SCHEMA,
        "run_kind": TAIL_RUN_KIND,
        "status": "complete",
        "workload": workload,
        "source_measurement": "trace_disabled",
        "performance_certified": False,
    }
    for key, expected in required.items():
        if document.get(key) != expected or (
            key == "performance_certified"
            and document.get(key) is not False
        ):
            _fail(f"tail report {key} must equal {expected!r}")
    campaign_id = document.get("campaign_id")
    if type(campaign_id) is not str or not campaign_id:
        _fail("tail report campaign_id must be a non-empty string")
    realized = document.get("realized_us")
    if (
        type(realized) is not list
        or any(type(value) is not int for value in realized)
        or realized != list(TAIL_BACKOFFS)
    ):
        _fail(f"tail report realized_us must equal {list(TAIL_BACKOFFS)}")
    points = document.get("points")
    if type(points) is not list:
        _fail("tail report points must be a list")

    rows: list[tuple[float, float, float, dict[str, Any]]] = []
    for index, point in enumerate(points):
        if type(point) is not dict:
            _fail(f"tail report points[{index}] must be an object")
        kind = point.get("kind")
        if kind not in ("static", "none", "adaptive"):
            _fail(f"tail report points[{index}].kind is unsupported")
        if kind != "static":
            continue
        backoff = point.get("backoff_us")
        if type(backoff) is not int:
            _fail(f"tail report points[{index}].backoff_us must be an integer")
        throughputs = point.get("throughput_tps_reps")
        abort_rates = point.get("abort_rate_reps")
        for label, values in (
            ("throughput_tps_reps", throughputs),
            ("abort_rate_reps", abort_rates),
        ):
            if type(values) is not list or len(values) != TAIL_REPETITIONS:
                _fail(
                    f"tail report points[{index}].{label} must contain "
                    f"{TAIL_REPETITIONS} values"
                )
        throughput_values = [
            _finite(
                value,
                f"tail report points[{index}].throughput_tps_reps",
            )
            for value in throughputs
        ]
        if any(value <= 0.0 for value in throughput_values):
            _fail(f"tail report points[{index}] throughput must be > 0")
        abort_values = [
            _finite(
                value,
                f"tail report points[{index}].abort_rate_reps",
                lower=0.0,
            )
            for value in abort_rates
        ]
        if any(value > 1.0 for value in abort_values):
            _fail(f"tail report points[{index}] abort rate must be <= 1")
        throughput_mean = statistics.fmean(throughput_values)
        abort_mean = statistics.fmean(abort_values)
        rows.append((
            float(backoff), throughput_mean, abort_mean, {
                "cell": f"tail-{backoff}us",
                "backoff_us": backoff,
                "throughputs_tps": throughput_values,
                "abort_rates": abort_values,
                "pbs_jobids": [],
                "throughput_mean_tps": throughput_mean,
                "abort_rate_mean": abort_mean,
                "source": TAIL_RUN_KIND,
                "campaign_id": campaign_id,
            },
        ))
    if len(rows) != len(TAIL_BACKOFFS) or {
        int(row[0]) for row in rows
    } != set(TAIL_BACKOFFS):
        _fail("tail report static points must equal the six realized backoffs")
    return rows


def build_calibration(
    document: Mapping[str, Any], workload: str,
    tail: Mapping[str, Any] | None = None,
) -> Calibration:
    """Build one workload curve without touching any adaptive target section."""
    if workload not in WORKLOADS:
        _fail(f"unsupported workload: {workload!r}")
    cells = _cells(document, "static_fixed_backoff")
    names = (
        "zero-loop", "constant-mu2", "constant-mu5", "constant-mu10",
        "constant-mu25", "constant-mu50", "constant-mu100",
    )
    throughput_means: list[float] = []
    abort_means: list[float] = []
    raw_cells: list[dict[str, Any]] = []
    for backoff, name in zip(STATIC_BACKOFFS, names, strict=True):
        key = f"{workload}|{name}"
        cell = cells.get(key)
        throughputs, abort_rates, jobids = _raw_cell(cell, key)
        meta = cell.get("meta") if type(cell) is dict else None
        if type(meta) is not dict:
            _fail(f"{key}.meta must be an object")
        if meta.get("ccbench_head") != SOURCE_PIN:
            _fail(f"{key} source pin differs")
        if meta.get("workload") != workload or meta.get("cell") != name:
            _fail(f"{key} metadata differs")
        genome = meta.get("genome")
        if type(genome) is not str or "BACK_OFF=1" not in genome:
            _fail(f"{key} is not an active backoff cell")
        if name == "zero-loop" and "BACKOFF_FIXED=0" not in genome:
            _fail("T(0) must come from BACKOFF_FIXED=0,BACK_OFF=1 zero-loop")
        throughput_means.append(statistics.fmean(throughputs))
        abort_means.append(statistics.fmean(abort_rates))
        raw_cells.append({
            "cell": name,
            "backoff_us": backoff,
            "throughputs_tps": throughputs,
            "abort_rates": abort_rates,
            "pbs_jobids": jobids,
            "throughput_mean_tps": throughput_means[-1],
            "abort_rate_mean": abort_means[-1],
        })
    calibration = Calibration(
        workload=workload,
        backoffs_us=STATIC_BACKOFFS,
        throughput_tps=tuple(throughput_means),
        abort_rate=tuple(abort_means),
        raw_cells=tuple(raw_cells),
    )
    if tail is None:
        return calibration
    combined = [
        (backoff, throughput, abort, raw)
        for backoff, throughput, abort, raw in zip(
            calibration.backoffs_us, calibration.throughput_tps,
            calibration.abort_rate, calibration.raw_cells, strict=True,
        )
    ]
    combined.extend(_tail_calibration_rows(tail, workload))
    combined.sort(key=lambda row: row[0])
    return Calibration(
        workload=workload,
        backoffs_us=tuple(row[0] for row in combined),
        throughput_tps=tuple(row[1] for row in combined),
        abort_rate=tuple(row[2] for row in combined),
        raw_cells=tuple(row[3] for row in combined),
    )


def _curve_value(
    backoff_us: np.ndarray | float,
    xs: tuple[float, ...], ys: tuple[float, ...], *,
    tail: str, interpolation: str, lower: float, upper: float | None,
) -> np.ndarray:
    b = np.asarray(backoff_us, dtype=float)
    if np.any(~np.isfinite(b)) or np.any(b < xs[0]) or np.any(b > 1000.0):
        _fail("backoff evaluation is outside [0,1000]")
    x_array = np.asarray(xs, dtype=float)
    y_array = np.asarray(ys, dtype=float)
    if np.any(y_array <= 0.0):
        _fail("calibration curve values must be positive")
    if interpolation == "linear":
        result = np.interp(np.minimum(b, xs[-1]), x_array, y_array)
    elif interpolation == "log":
        result = np.exp(np.interp(
            np.minimum(b, xs[-1]), x_array, np.log(y_array),
        ))
    else:
        _fail(f"unknown interpolation: {interpolation}")
    beyond = b > xs[-1]
    if np.any(beyond):
        if tail == "primary":
            slope = (math.log(ys[-1]) - math.log(ys[-2])) / (xs[-1] - xs[-2])
            result = np.where(beyond, ys[-1] * np.exp(slope * (b - xs[-1])), result)
        elif tail == "flat-tail":
            result = np.where(beyond, ys[-1], result)
        elif tail == "linear-zero":
            slope = (ys[-1] - ys[-2]) / (xs[-1] - xs[-2])
            result = np.where(beyond, ys[-1] + slope * (b - xs[-1]), result)
        else:
            _fail(f"unknown tail: {tail}")
    result = np.maximum(result, lower)
    if upper is not None:
        result = np.minimum(result, upper)
    return result


def throughput_at(
    calibration: Calibration, backoff_us: np.ndarray | float,
    scenario: Scenario = EXACT,
) -> np.ndarray:
    return _curve_value(
        backoff_us, calibration.backoffs_us, calibration.throughput_tps,
        tail=scenario.tail, interpolation=scenario.interpolation,
        lower=0.0, upper=None,
    )


def abort_rate_at(
    calibration: Calibration, backoff_us: np.ndarray | float,
    scenario: Scenario = EXACT,
) -> np.ndarray:
    # P4 has no fitted coefficient: a(b) uses the same interpolation/tail rule
    # as T(b), applied to the measured static abort-rate curve.
    return _curve_value(
        backoff_us, calibration.backoffs_us, calibration.abort_rate,
        tail=scenario.tail, interpolation=scenario.interpolation,
        lower=0.0, upper=1.0,
    )


def leader_period_us(
    calibration: Calibration, backoff_us: np.ndarray | float,
    scenario: Scenario = EXACT,
) -> np.ndarray:
    throughput = throughput_at(calibration, backoff_us, scenario)
    abort = abort_rate_at(calibration, backoff_us, scenario)
    with np.errstate(divide="ignore", invalid="ignore"):
        period = THREADS * (1.0 - abort) / throughput * 1_000_000.0
    return np.where(throughput > 0.0, period, math.inf)


def effective_update_interval_us(
    calibration: Calibration, backoff_us: np.ndarray | float,
    nominal_update_us: np.ndarray | float, scenario: Scenario = EXACT,
) -> np.ndarray:
    """Return the first leader-attempt event at or after the nominal deadline."""
    nominal = np.asarray(nominal_update_us, dtype=float)
    if np.any(~np.isfinite(nominal)) or np.any(nominal <= 0.0):
        _fail("nominal update interval must be positive")
    b = np.asarray(backoff_us, dtype=float)
    nominal = np.broadcast_to(nominal, b.shape)
    if not scenario.event_driven:
        return nominal.copy()
    period = leader_period_us(calibration, b, scenario)
    with np.errstate(divide="ignore", invalid="ignore"):
        attempts = np.ceil(nominal / period)
    attempts = np.maximum(attempts, 1.0)
    return attempts * period


def advance_window(
    state: WalkState, *, committed_txs: int, time_diff_us: float,
    step_us: float, k_min_backoff: float = 0.0,
    k_max_backoff: float = 1000.0, truncate_last_backoff: bool = True,
) -> Transition:
    """Adapt one scalar fixture to the vector transition used by every run."""
    if not 0 <= committed_txs <= UINT64_MASK:
        _fail("committed_txs must be uint64")
    if not math.isfinite(time_diff_us) or time_diff_us <= 0.0:
        _fail("time_diff_us must be finite and positive")
    if not math.isfinite(step_us) or step_us <= 0.0:
        _fail("step_us must be finite and positive")
    if k_min_backoff != 0.0:
        _fail("the pinned source minimum backoff is 0")
    if not math.isfinite(k_max_backoff) or k_max_backoff <= k_min_backoff:
        _fail("k_max_backoff must be finite and greater than the minimum")

    backoff = np.asarray([state.backoff_us], dtype=float)
    last_committed = np.asarray([state.last_committed_txs], dtype=np.uint64)
    last_tput = np.asarray([state.last_committed_tput], dtype=float)
    last_backoff = np.asarray([state.last_backoff], dtype=float)
    committed = np.asarray([committed_txs], dtype=np.uint64)
    time_diff = np.asarray([time_diff_us], dtype=float)
    (
        next_backoff, next_last_committed, next_last_tput,
        next_last_backoff, gradient_values, branch_codes,
    ) = _advance_vector(
        backoff=backoff,
        last_committed=last_committed,
        last_tput=last_tput,
        last_backoff=last_backoff,
        committed=committed,
        time_diff=time_diff,
        step_us=step_us,
        ceiling_us=k_max_backoff,
        truncate=truncate_last_backoff,
    )

    backoff_diff = float(backoff[0] - last_backoff[0])
    committed_diff = (committed_txs - state.last_committed_txs) & UINT64_MASK
    committed_tput = float(committed_diff) / time_diff_us * 1_000_000.0
    committed_tput_diff = committed_tput - state.last_committed_tput
    branches = (
        "gradient_negative", "gradient_positive",
        "parity_decrease", "parity_increase",
    )
    return Transition(
        state=WalkState(
            backoff_us=float(next_backoff[0]),
            last_committed_txs=int(next_last_committed[0]),
            last_committed_tput=float(next_last_tput[0]),
            last_backoff=float(next_last_backoff[0]),
            committed_txs=committed_txs,
        ),
        time_diff_us=time_diff_us,
        committed_diff=committed_diff,
        committed_tput=committed_tput,
        committed_tput_diff=committed_tput_diff,
        backoff_diff=backoff_diff,
        gradient=float(gradient_values[0]),
        branch=branches[int(branch_codes[0])],
    )


def _sample_counts(
    rng: np.random.Generator, expected: np.ndarray, law: str,
    residual: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    expected = np.maximum(expected, 0.0)
    if law == "poisson":
        return rng.poisson(expected).astype(np.uint64), residual
    if law == "deterministic":
        value = expected + residual
        counts = np.floor(value).astype(np.uint64)
        return counts, value - counts.astype(float)
    if law in ("fano2", "fano4"):
        fano = 2.0 if law == "fano2" else 4.0
        result = np.zeros(expected.shape, dtype=np.uint64)
        positive = expected > 0.0
        shape = expected[positive] / (fano - 1.0)
        result[positive] = rng.negative_binomial(
            shape, 1.0 / fano,
        ).astype(np.uint64)
        return result, residual
    _fail(f"unknown count law: {law}")
    raise AssertionError("unreachable")


def _advance_vector(
    *, backoff: np.ndarray, last_committed: np.ndarray,
    last_tput: np.ndarray, last_backoff: np.ndarray,
    committed: np.ndarray, time_diff: np.ndarray,
    step_us: np.ndarray | float, ceiling_us: np.ndarray | float,
    truncate: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Vectorized repetition-axis translation of ``advance_window``."""
    new_backoff = backoff.copy()
    backoff_diff = new_backoff - last_backoff
    committed_diff = committed - last_committed  # np.uint64 wraps like C++.
    committed_tput = committed_diff.astype(float) / time_diff * 1_000_000.0
    committed_tput_diff = committed_tput - last_tput

    next_last_committed = committed.copy()
    next_last_tput = committed_tput.copy()
    next_last_backoff = (
        new_backoff.astype(np.uint64).astype(float)
        if truncate else new_backoff.copy()
    )

    gradient = np.zeros(new_backoff.shape, dtype=float)
    steps = np.broadcast_to(np.asarray(step_us, dtype=float), new_backoff.shape)
    ceilings = np.broadcast_to(
        np.asarray(ceiling_us, dtype=float), new_backoff.shape,
    )
    nonzero = backoff_diff != 0.0
    gradient[nonzero] = committed_tput_diff[nonzero] / backoff_diff[nonzero]
    negative = gradient < 0.0
    positive = gradient > 0.0
    zero = ~(negative | positive)
    new_backoff[negative] -= steps[negative]
    new_backoff[positive] += steps[positive]
    even_or_max = ((committed & np.uint64(1)) == 0) | (new_backoff == ceilings)
    parity_decrease = zero & even_or_max
    parity_increase = zero & ~even_or_max
    new_backoff[parity_decrease] -= steps[parity_decrease]
    new_backoff[parity_increase] += steps[parity_increase]
    new_backoff = np.where(new_backoff < 0.0, 0.0, new_backoff)
    new_backoff = np.where(new_backoff > ceilings, ceilings, new_backoff)
    branch_code = np.where(
        negative, 0, np.where(positive, 1, np.where(parity_decrease, 2, 3)),
    )
    return (
        new_backoff, next_last_committed, next_last_tput,
        next_last_backoff, gradient, branch_code,
    )


def _weighted_quantile_from_hist(
    counts: np.ndarray, coordinates: np.ndarray, quantile: float,
) -> float | None:
    total = float(np.sum(counts))
    if total <= 0.0:
        return None
    index = int(np.searchsorted(np.cumsum(counts), quantile * total, side="left"))
    return float(coordinates[min(index, len(coordinates) - 1)])


def _seed_for(
    workload: str, step_us: float, update_us: int, ceiling_us: float,
) -> tuple[np.random.Generator, list[int]]:
    """Return the condition-local stream shared by all counterfactuals."""
    spawn_key = [
        BASE_SEED,
        WORKLOADS.index(workload),
        int(round(step_us * 1000.0)),
        int(update_us),
        int(round(ceiling_us)),
    ]
    return np.random.default_rng(np.random.SeedSequence(spawn_key)), spawn_key


def _simulate_condition(
    calibration: Calibration, scenario: Scenario, *, step_us: float,
    update_us: int, ceiling_us: float = 1000.0,
    repetitions: int = REPETITIONS, duration_us: float = DURATION_US,
) -> dict[str, Any]:
    """Internal bounded simulator used by frozen APIs and small unit tests."""
    if (
        isinstance(repetitions, bool)
        or not 1 <= repetitions <= _MAX_INTERNAL_REPETITIONS
    ):
        _fail(f"repetitions must be in [1,{_MAX_INTERNAL_REPETITIONS}]")
    if not math.isfinite(duration_us) or duration_us <= 0.0:
        _fail("duration_us must be finite and positive")
    if ceiling_us not in (50.0, 1000.0):
        _fail("only the source and H1 ceilings (50,1000 us) are admissible")
    rng, spawn_key = _seed_for(
        calibration.workload, step_us, update_us, ceiling_us,
    )
    n = repetitions
    backoff = np.zeros(n, dtype=float)
    last_committed = np.zeros(n, dtype=np.uint64)
    last_tput = np.zeros(n, dtype=float)
    last_backoff = np.zeros(n, dtype=float)
    last_expected_tput = np.zeros(n, dtype=float)
    committed = np.zeros(n, dtype=np.uint64)
    total_commits = np.zeros(n, dtype=np.uint64)
    elapsed = np.zeros(n, dtype=float)
    residual = np.zeros(n, dtype=float)
    residence_gt100 = np.zeros(n, dtype=float)
    survivor_time = np.zeros((n, len(RESIDENCE_THRESHOLDS_US)), dtype=float)
    residence_coordinates = np.arange(
        0.0, ceiling_us + RESIDENCE_BIN_WIDTH_US, RESIDENCE_BIN_WIDTH_US,
    )
    residence_hist = np.zeros((n, len(residence_coordinates)), dtype=float)
    interval_edges = np.concatenate((
        np.asarray([0.0]),
        np.geomspace(1.0, duration_us, num=128),
    ))
    interval_hist = np.zeros((n, len(interval_edges) - 1), dtype=np.uint64)
    branch_counts = np.zeros((n, 4), dtype=np.uint64)
    sign_counts = np.zeros((n, 3), dtype=np.uint64)  # correct, incorrect, zero
    update_counts = np.zeros(n, dtype=np.uint64)

    while np.any(elapsed < duration_us):
        active = elapsed < duration_us
        indices = np.flatnonzero(active)
        current_backoff = backoff[indices]
        intervals = effective_update_interval_us(
            calibration, current_backoff, float(update_us), scenario,
        )
        remaining = duration_us - elapsed[indices]
        full_update = np.isfinite(intervals) & (intervals <= remaining)
        spans = np.where(full_update, intervals, remaining)
        expected_tput = throughput_at(calibration, current_backoff, scenario)
        expected_counts = expected_tput * spans / 1_000_000.0
        sampled, next_residual = _sample_counts(
            rng, expected_counts, scenario.count_law, residual[indices],
        )
        residual[indices] = next_residual
        total_commits[indices] += sampled
        committed[indices] += sampled

        residence_gt100[indices] += spans * (current_backoff > 100.0)
        survivor_time[indices] += spans[:, None] * (
            current_backoff[:, None] >= np.asarray(RESIDENCE_THRESHOLDS_US)[None, :]
        )
        residence_bins = np.minimum(
            np.floor(current_backoff / RESIDENCE_BIN_WIDTH_US).astype(int),
            len(residence_coordinates) - 1,
        )
        np.add.at(residence_hist, (indices, residence_bins), spans)
        elapsed[indices] += spans

        updating_local = np.flatnonzero(full_update)
        if updating_local.size == 0:
            continue
        updating = indices[updating_local]
        used_intervals = intervals[updating_local]
        interval_bins = np.searchsorted(
            interval_edges, used_intervals, side="right",
        ) - 1
        interval_bins = np.clip(interval_bins, 0, interval_hist.shape[1] - 1)
        np.add.at(interval_hist, (updating, interval_bins), 1)

        old_backoff_diff = backoff[updating] - last_backoff[updating]
        expected_diff = expected_tput[updating_local] - last_expected_tput[updating]
        expected_gradient = np.zeros(updating.size, dtype=float)
        nz = old_backoff_diff != 0.0
        expected_gradient[nz] = expected_diff[nz] / old_backoff_diff[nz]
        (
            next_backoff, next_last_committed, next_last_tput,
            next_last_backoff, observed_gradient, branch_code,
        ) = _advance_vector(
            backoff=backoff[updating],
            last_committed=last_committed[updating],
            last_tput=last_tput[updating],
            last_backoff=last_backoff[updating],
            committed=committed[updating],
            time_diff=used_intervals,
            step_us=step_us,
            ceiling_us=ceiling_us,
            truncate=scenario.truncate_last_backoff,
        )
        backoff[updating] = next_backoff
        last_committed[updating] = next_last_committed
        last_tput[updating] = next_last_tput
        last_backoff[updating] = next_last_backoff
        last_expected_tput[updating] = expected_tput[updating_local]
        update_counts[updating] += 1
        np.add.at(branch_counts, (updating, branch_code), 1)

        observed_sign = np.sign(observed_gradient)
        expected_sign = np.sign(expected_gradient)
        zero = observed_sign == 0.0
        correct = ~zero & (observed_sign == expected_sign)
        incorrect = ~zero & ~correct
        sign_counts[updating, 0] += correct.astype(np.uint64)
        sign_counts[updating, 1] += incorrect.astype(np.uint64)
        sign_counts[updating, 2] += zero.astype(np.uint64)

    repetitions_out: list[dict[str, Any]] = []
    for rep in range(n):
        update_count = int(update_counts[rep])
        denominator = float(update_count) if update_count else 1.0
        interval_coordinates = np.sqrt(interval_edges[:-1] * interval_edges[1:])
        interval_coordinates[0] = interval_edges[1] / 2.0
        repetitions_out.append({
            "rep_index": rep,
            "throughput_tps": float(total_commits[rep]) / duration_us * 1_000_000.0,
            "total_commits": int(total_commits[rep]),
            "p_backoff_gt_100": float(residence_gt100[rep] / duration_us),
            "backoff_quantiles_us": {
                f"p{int(q * 100):02d}": _weighted_quantile_from_hist(
                    residence_hist[rep], residence_coordinates, q,
                )
                for q in (0.50, 0.90, 0.99)
            },
            "effective_update_interval_quantiles_us": {
                f"p{int(q * 100):02d}": _weighted_quantile_from_hist(
                    interval_hist[rep], interval_coordinates, q,
                )
                for q in (0.50, 0.90, 0.99)
            },
            "residence_survivor": [
                float(value / duration_us) for value in survivor_time[rep]
            ],
            "branch_rates": {
                "gradient_negative": float(branch_counts[rep, 0] / denominator),
                "gradient_positive": float(branch_counts[rep, 1] / denominator),
                "parity_decrease": float(branch_counts[rep, 2] / denominator),
                "parity_increase": float(branch_counts[rep, 3] / denominator),
            },
            "gradient_sign_rates": {
                "correct": float(sign_counts[rep, 0] / denominator),
                "incorrect": float(sign_counts[rep, 1] / denominator),
                "zero": float(sign_counts[rep, 2] / denominator),
            },
            "update_count": update_count,
            "final_backoff_us": float(backoff[rep]),
            "final_backoff_hex": float(backoff[rep]).hex(),
        })
    return {
        "workload": calibration.workload,
        "scenario": scenario.name,
        "condition": {
            "step_us": step_us,
            "nominal_update_us": update_us,
            "ceiling_us": ceiling_us,
            "duration_us": duration_us,
        },
        "seed_sequence": spawn_key,
        "repetitions": repetitions_out,
        "residence_thresholds_us": list(RESIDENCE_THRESHOLDS_US),
        "effective_update_interval_histogram": {
            "edges_us": interval_edges.tolist(),
            "counts": np.sum(interval_hist, axis=0).astype(int).tolist(),
        },
    }


def _require_frozen_config(repetitions: int, duration_us: float) -> None:
    if repetitions != REPETITIONS:
        _fail(f"repetitions is frozen at {REPETITIONS}")
    if duration_us != DURATION_US:
        _fail(f"duration_us is frozen at {DURATION_US:g}")


def simulate_condition(
    calibration: Calibration, scenario: Scenario, *, step_us: float,
    update_us: int, ceiling_us: float = 1000.0,
    repetitions: int = REPETITIONS, duration_us: float = DURATION_US,
) -> dict[str, Any]:
    """Simulate one condition under the literal, frozen run configuration."""
    _require_frozen_config(repetitions, duration_us)
    return _simulate_condition(
        calibration, scenario, step_us=step_us, update_us=update_us,
        ceiling_us=ceiling_us, repetitions=REPETITIONS,
        duration_us=DURATION_US,
    )


def _simulate_condition_batch(
    calibration: Calibration, scenario: Scenario,
    conditions: Sequence[tuple[float, int, float]], *,
    repetitions: int = REPETITIONS, duration_us: float = DURATION_US,
) -> list[dict[str, Any]]:
    """Internal condition-local batch used by frozen APIs and unit tests."""
    if not conditions:
        return []
    canonical = tuple(
        (float(step), int(update), float(ceiling))
        for step, update, ceiling in conditions
    )
    if len(set(canonical)) != len(canonical):
        _fail("batched condition coordinates must be unique")
    if any(
        step <= 0.0 or update <= 0 or ceiling not in (50.0, 1000.0)
        for step, update, ceiling in canonical
    ):
        _fail("batched condition coordinate is outside the frozen contract")
    return [
        _simulate_condition(
            calibration, scenario, step_us=step, update_us=update,
            ceiling_us=ceiling, repetitions=repetitions,
            duration_us=duration_us,
        )
        for step, update, ceiling in canonical
    ]


def simulate_condition_batch(
    calibration: Calibration, scenario: Scenario,
    conditions: Sequence[tuple[float, int, float]], *,
    repetitions: int = REPETITIONS, duration_us: float = DURATION_US,
) -> list[dict[str, Any]]:
    """Simulate a condition list under the literal, frozen configuration."""
    _require_frozen_config(repetitions, duration_us)
    return _simulate_condition_batch(
        calibration, scenario, conditions, repetitions=REPETITIONS,
        duration_us=DURATION_US,
    )


def prediction_conditions() -> tuple[tuple[float, int, float], ...]:
    union10 = tuple(sorted(set(STAGE1_STEPS) | set(D1475_STEPS)))
    rows = [(step, 10, 1000.0) for step in union10]
    rows.extend((0.5, 10, 50.0) for _ in range(1))
    rows.extend((2.0, 10, 50.0) for _ in range(1))
    for update in UPDATE_INTERVALS_US[1:]:
        rows.extend((step, update, 1000.0) for step in STAGE1_STEPS)
    # The residence figure preregisters step 25 at the long interval too.
    rows.append((25.0, 2560, 1000.0))
    return tuple(rows)


def diagnostic_conditions() -> tuple[tuple[float, int, float], ...]:
    return (
        (0.5, 10, 1000.0), (1.0, 10, 1000.0),
        (5.0, 10, 1000.0), (25.0, 10, 1000.0),
        (0.5, 2560, 1000.0), (1.0, 2560, 1000.0),
        (5.0, 2560, 1000.0),
    )


def sensitivity_conditions() -> tuple[tuple[float, int, float], ...]:
    return tuple(
        [(step, 10, 1000.0) for step in sorted(set(STAGE1_STEPS) | set(D1475_STEPS))]
        + [(step, 2560, 1000.0) for step in (0.1, 0.25, 0.5, 1.0, 5.0)]
    )


def predict_all(
    calibrations: Mapping[str, Calibration], *,
    repetitions: int = REPETITIONS, duration_us: float = DURATION_US,
) -> list[dict[str, Any]]:
    """Predict from static calibrations; adaptive targets are not an argument."""
    _require_frozen_config(repetitions, duration_us)
    runs: list[dict[str, Any]] = []
    for workload in WORKLOADS:
        calibration = calibrations[workload]
        runs.extend(simulate_condition_batch(
            calibration, EXACT, prediction_conditions(),
            repetitions=repetitions, duration_us=duration_us,
        ))
    write = calibrations["write-heavy"]
    for scenario in (NO_TRUNC, NO_P4, NO_TRUNC_NO_P4, NO_COUNT_NOISE):
        runs.extend(simulate_condition_batch(
            write, scenario, diagnostic_conditions(),
            repetitions=repetitions, duration_us=duration_us,
        ))
    for scenario in (FLAT_TAIL, LINEAR_ZERO, LOG_INTERP, FANO2, FANO4):
        runs.extend(simulate_condition_batch(
            write, scenario, sensitivity_conditions(),
            repetitions=repetitions, duration_us=duration_us,
        ))
    return runs


def _run_mean_tps(run: Mapping[str, Any]) -> float:
    values = [float(rep["throughput_tps"]) for rep in run["repetitions"]]
    return statistics.fmean(values)


def _find_run(
    runs: Sequence[Mapping[str, Any]], workload: str, scenario: str,
    step_us: float, update_us: int, ceiling_us: float = 1000.0,
) -> Mapping[str, Any]:
    selected = [
        run for run in runs
        if run["workload"] == workload and run["scenario"] == scenario
        and run["condition"]["step_us"] == step_us
        and run["condition"]["nominal_update_us"] == update_us
        and run["condition"]["ceiling_us"] == ceiling_us
    ]
    if len(selected) != 1:
        _fail(
            "prediction lookup must be unique: "
            f"{workload}/{scenario}/{step_us}/{update_us}/{ceiling_us}"
        )
    return selected[0]


def _observed_series(
    document: Mapping[str, Any], *, dataset: str, workload: str,
    update_us: int, ceiling_us: float = 1000.0,
) -> dict[float, list[float]]:
    section = (
        "stage1_adaptive_step_x_interval"
        if dataset == "stage1" else "d1475_adaptive_step_grid"
    )
    cells = _cells(document, section)
    result: dict[float, list[float]] = {}
    for key, cell in cells.items():
        if not key.startswith(f"{workload}|") or type(cell) is not dict:
            continue
        meta = cell.get("meta")
        if type(meta) is not dict or meta.get("back_off") != 1:
            continue
        cell_ceiling = float(meta.get("ceiling_us", 1000.0))
        cell_update = int(meta.get("update_us", 10))
        if cell_ceiling != ceiling_us or cell_update != update_us:
            continue
        step = _finite(meta.get("step_us"), f"{key}.step_us", lower=0.0)
        throughputs, _abort, _jobs = _raw_cell(cell, key)
        if step in result:
            _fail(f"duplicate observed coordinate: {dataset}/{workload}/{step}")
        result[step] = throughputs
    return result


def kendall_distance(
    observed: Mapping[float, float], predicted: Mapping[float, float],
) -> int | None:
    """Return discordant-pair count, or None for key mismatch/ties."""
    if set(observed) != set(predicted) or len(observed) < 2:
        return None
    if len(set(observed.values())) != len(observed) or len(set(predicted.values())) != len(predicted):
        return None
    keys = sorted(observed)
    distance = 0
    for left_index, left in enumerate(keys):
        for right in keys[left_index + 1:]:
            observed_order = observed[left] < observed[right]
            predicted_order = predicted[left] < predicted[right]
            distance += observed_order != predicted_order
    return distance


def _unique_extreme(values: Mapping[float, float], *, maximum: bool) -> float | None:
    extreme = (max if maximum else min)(values.values())
    points = [key for key, value in values.items() if value == extreme]
    return points[0] if len(points) == 1 else None


def _rule_a(
    observed: Mapping[float, float], predicted: Mapping[float, float], *,
    dataset: str,
) -> dict[str, Any]:
    if dataset == "stage1":
        expected_steps = set(STAGE1_STEPS)
        limit = STAGE1_MAX_KENDALL_DISTANCE
    elif dataset == "d1475":
        expected_steps = set(D1475_STEPS)
        limit = D1475_MAX_KENDALL_DISTANCE
    else:
        _fail(f"unknown rank dataset: {dataset}")
    distance = kendall_distance(observed, predicted)
    maximum = _unique_extreme(predicted, maximum=True) if predicted else None
    minimum = _unique_extreme(predicted, maximum=False) if predicted else None
    complete = set(observed) == expected_steps and set(predicted) == expected_steps
    distance_ok = distance is not None and distance <= limit
    maximum_ok = maximum == 0.5
    minimum_ok = minimum is not None and 5.0 <= minimum <= 25.0
    return {
        "passed": complete and distance_ok and maximum_ok and minimum_ok,
        "complete_dataset": complete,
        "kendall_distance": distance,
        "kendall_distance_limit": limit,
        "maximum_step_us": maximum,
        "maximum_is_0.5": maximum_ok,
        "minimum_step_us": minimum,
        "minimum_is_5_to_25": minimum_ok,
        "observed_mean_tps": {str(k): observed[k] for k in sorted(observed)},
        "predicted_mean_tps": {str(k): predicted[k] for k in sorted(predicted)},
    }


def rule_a_stage1(
    observed: Mapping[float, float], predicted: Mapping[float, float],
) -> dict[str, Any]:
    return _rule_a(observed, predicted, dataset="stage1")


def rule_a_d1475(
    observed: Mapping[float, float], predicted: Mapping[float, float],
) -> dict[str, Any]:
    return _rule_a(observed, predicted, dataset="d1475")


def rule_b(predicted: Mapping[float, float]) -> dict[str, Any]:
    expected = {0.1, 0.25, 0.5, 1.0, 5.0}
    complete = set(predicted) == expected
    ratio = max(predicted.values()) / min(predicted.values()) if complete else None
    passed = complete and ratio is not None and ratio < B_MAX_MIN_RATIO_LIMIT
    return {
        "passed": passed,
        "ratio": ratio,
        "strict_limit": B_MAX_MIN_RATIO_LIMIT,
        "predicted_mean_tps": {str(k): predicted[k] for k in sorted(predicted)},
    }


def rule_c(predicted_step25_tps: float) -> dict[str, Any]:
    relative_error = abs(predicted_step25_tps - D1475_VALLEY_TPS) / D1475_VALLEY_TPS
    return {
        "passed": relative_error <= D1475_VALLEY_RELATIVE_TOLERANCE,
        "predicted_step25_tps": predicted_step25_tps,
        "observed_d1475_step25_tps": D1475_VALLEY_TPS,
        "relative_error": relative_error,
        "inclusive_relative_tolerance": D1475_VALLEY_RELATIVE_TOLERANCE,
    }


def rule_h1(
    predicted_ratios: Mapping[float, float],
    observed_ratios: Mapping[float, float],
) -> dict[str, Any]:
    complete = (
        set(predicted_ratios) == {0.5, 2.0}
        and set(observed_ratios) == {0.5, 2.0}
    )
    relative_errors = (
        {
            step: abs(predicted_ratios[step] - observed_ratios[step])
            / observed_ratios[step]
            for step in (0.5, 2.0)
        }
        if complete else {}
    )
    passed = (
        complete
        and predicted_ratios[2.0] >= H1_STEP2_MIN_CAP_RATIO
        and predicted_ratios[0.5] <= H1_STEP05_MAX_CAP_RATIO
        and all(
            value <= H1_RATIO_RELATIVE_TOLERANCE
            for value in relative_errors.values()
        )
    )
    return {
        "passed": passed,
        "predicted_cap50_over_cap1000": {
            str(k): predicted_ratios[k] for k in sorted(predicted_ratios)
        },
        "observed_cap50_over_cap1000": {
            str(k): observed_ratios[k] for k in sorted(observed_ratios)
        },
        "relative_error": {
            str(k): relative_errors[k] for k in sorted(relative_errors)
        },
        "inclusive_relative_tolerance": H1_RATIO_RELATIVE_TOLERANCE,
        "step2_inclusive_min": H1_STEP2_MIN_CAP_RATIO,
        "step0.5_inclusive_max": H1_STEP05_MAX_CAP_RATIO,
        "kind": "parameter-independent consistency check, not blinded calibration",
    }


def derive_status(shape_passed: bool) -> str | None:
    """Return the shape-only status reachable from this indirect study."""
    return "shape_match" if shape_passed else None


def _mean_observed(series: Mapping[float, Sequence[float]]) -> dict[float, float]:
    return {step: statistics.fmean(values) for step, values in series.items()}


def _predicted_map(
    runs: Sequence[Mapping[str, Any]], workload: str, steps: Sequence[float],
    update_us: int,
) -> dict[float, float]:
    return {
        step: _run_mean_tps(_find_run(
            runs, workload, EXACT.name, step, update_us, 1000.0,
        ))
        for step in steps
    }


def _score_workload_shape(
    document: Mapping[str, Any], runs: Sequence[Mapping[str, Any]], workload: str,
) -> dict[str, Any]:
    stage1_observed = _mean_observed(_observed_series(
        document, dataset="stage1", workload=workload, update_us=10,
    ))
    d1475_observed = _mean_observed(_observed_series(
        document, dataset="d1475", workload=workload, update_us=10,
    ))
    stage1_predicted = _predicted_map(runs, workload, STAGE1_STEPS, 10)
    d1475_predicted = _predicted_map(runs, workload, D1475_STEPS, 10)
    b_predicted = _predicted_map(runs, workload, (0.1, 0.25, 0.5, 1.0, 5.0), 2560)
    a_stage1 = rule_a_stage1(stage1_observed, stage1_predicted)
    a_d1475 = rule_a_d1475(d1475_observed, d1475_predicted)
    b = rule_b(b_predicted)
    # The 20% relative rule is workload-independent for H2; write-heavy also
    # records the pre-frozen literal observed value through rule_c().
    observed_valley = d1475_observed[25.0]
    predicted_valley = d1475_predicted[25.0]
    c = (
        rule_c(predicted_valley)
        if workload == "write-heavy"
        else {
            "passed": abs(predicted_valley - observed_valley) / observed_valley
            <= D1475_VALLEY_RELATIVE_TOLERANCE,
            "predicted_step25_tps": predicted_valley,
            "observed_step25_tps": observed_valley,
            "relative_error": abs(predicted_valley - observed_valley) / observed_valley,
            "inclusive_relative_tolerance": D1475_VALLEY_RELATIVE_TOLERANCE,
        }
    )
    return {
        "passed": all(item["passed"] for item in (a_stage1, a_d1475, b, c)),
        "A_stage1": a_stage1,
        "A_d1475": a_d1475,
        "B_flattening": b,
        "C_valley": c,
    }


def evaluate_predictions(
    document: Mapping[str, Any], runs: Sequence[Mapping[str, Any]], *,
    score_h2: bool = False,
) -> dict[str, Any]:
    write_shape = _score_workload_shape(document, runs, "write-heavy")
    h1_ratios = {
        step: _run_mean_tps(_find_run(
            runs, "write-heavy", EXACT.name, step, 10, 50.0,
        )) / _run_mean_tps(_find_run(
            runs, "write-heavy", EXACT.name, step, 10, 1000.0,
        ))
        for step in (0.5, 2.0)
    }
    h1_cap1000 = _mean_observed(_observed_series(
        document, dataset="d1475", workload="write-heavy", update_us=10,
        ceiling_us=1000.0,
    ))
    h1_cap50 = _mean_observed(_observed_series(
        document, dataset="d1475", workload="write-heavy", update_us=10,
        ceiling_us=50.0,
    ))
    h1_observed_ratios = {
        step: h1_cap50[step] / h1_cap1000[step] for step in (0.5, 2.0)
    }
    h1 = rule_h1(h1_ratios, h1_observed_ratios)
    h2: dict[str, Any] = {
        "scored": False,
        "kind": "post-hoc parameter-independent consistency check",
        "reason": (
            "balanced/read-heavy adaptive values are not scored by default; "
            "some were exposed before scoring, so H2 is not a blinded or "
            "preregistered holdout"
        ),
    }
    if score_h2:
        scores = {
            workload: _score_workload_shape(document, runs, workload)
            for workload in ("balanced", "read-heavy")
        }
        h2 = {
            "scored": True,
            "passed": all(item["passed"] for item in scores.values()),
            "workloads": scores,
            "kind": "post-hoc parameter-independent consistency check",
            "disclosure": (
                "predictions use static measurements only, but some adaptive "
                "values were exposed before scoring; this is not a blinded or "
                "preregistered holdout"
            ),
        }
    shape_passed = bool(write_shape["passed"])
    return {
        "status": derive_status(shape_passed),
        "shape": write_shape,
        "consistency_checks": {
            "H1_ceiling": h1,
            "H2_workloads": h2,
            "intermediate_predictions": {
                "passed": None,
                "kind": "reported prediction without direct observed counterpart",
                "reason": (
                    "Backoff trajectory, effective interval, and branch-rate "
                    "observations are unavailable in this wave"
                ),
            },
        },
    }


def _calibration_json(calibration: Calibration) -> dict[str, Any]:
    return {
        "workload": calibration.workload,
        "backoffs_us": list(calibration.backoffs_us),
        "throughput_tps": list(calibration.throughput_tps),
        "abort_rate": list(calibration.abort_rate),
        "leader_period_us_at_static_points": [
            float(value) for value in leader_period_us(
                calibration, np.asarray(calibration.backoffs_us), EXACT,
            )
        ],
        "raw_cells": list(calibration.raw_cells),
    }


def _evaluation_jobids(
    measured: Mapping[str, Any], *, score_h2: bool,
) -> list[str]:
    workloads = WORKLOADS if score_h2 else ("write-heavy",)
    jobs: set[str] = set()
    for section in (
        "stage1_adaptive_step_x_interval", "d1475_adaptive_step_grid",
    ):
        for key, cell in _cells(measured, section).items():
            if not any(key.startswith(f"{workload}|") for workload in workloads):
                continue
            if type(cell) is not dict or type(cell.get("reps")) is not list:
                _fail(f"{section}/{key} must contain reps[]")
            for rep in cell["reps"]:
                if type(rep) is not dict or type(rep.get("pbs_jobid")) is not str:
                    _fail(f"{section}/{key} repetition lacks pbs_jobid")
                jobs.add(rep["pbs_jobid"])
    return sorted(jobs)


def _load_tail_inputs(
    arguments: Sequence[str] | None,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    entries = tuple(arguments or ())
    if not entries:
        return {}, []
    paths: dict[str, Path] = {}
    for entry in entries:
        if type(entry) is not str or "=" not in entry:
            _fail("--tail-json must have the form WORKLOAD=PATH")
        workload, raw_path = entry.split("=", 1)
        if workload not in WORKLOADS:
            _fail(f"--tail-json workload is unsupported: {workload!r}")
        if workload in paths:
            _fail(f"--tail-json workload is duplicated: {workload!r}")
        if not raw_path:
            _fail("--tail-json path must not be empty")
        paths[workload] = Path(raw_path).resolve()
    if len(entries) != len(WORKLOADS) or set(paths) != set(WORKLOADS):
        _fail(
            "--tail-json requires all three workloads: "
            "write-heavy, balanced, and read-heavy"
        )

    documents: dict[str, dict[str, Any]] = {}
    provenance: list[dict[str, Any]] = []
    for workload in WORKLOADS:
        path = paths.get(workload)
        if path is None:
            continue
        tail = strict_json(path)
        _tail_calibration_rows(tail, workload)
        documents[workload] = tail
        provenance.append({
            "workload": workload,
            "path": str(path),
            "sha256": _sha256(path),
            "campaign_id": tail["campaign_id"],
            "backoffs_us": list(TAIL_BACKOFFS),
        })
    return documents, provenance


def build_document(
    measured_path: Path, backoff_copy: Path, *, score_h2: bool = False,
    repetitions: int = REPETITIONS, duration_us: float = DURATION_US,
    tail_json: Sequence[str] | None = None,
) -> dict[str, Any]:
    _require_frozen_config(repetitions, duration_us)
    measured_path = measured_path.resolve()
    backoff_copy = backoff_copy.resolve()
    if _sha256(backoff_copy) != BACKOFF_COPY_SHA256:
        _fail("backoff copy SHA256 differs from the pinned source copy")
    source_text = backoff_copy.read_text(encoding="utf-8")
    if VERBATIM_UPDATE_BACKOFF not in source_text:
        _fail("verbatim update_backoff copy differs")
    if _sha256(measured_path) != MEASURED_INPUT_SHA256:
        _fail("measured JSON SHA256 differs from the frozen input")
    measured = strict_json(measured_path)
    tail_documents, tail_provenance = _load_tail_inputs(tail_json)
    calibrations = {
        workload: build_calibration(
            measured, workload, tail_documents.get(workload),
        )
        for workload in WORKLOADS
    }
    runs = predict_all(
        calibrations, repetitions=repetitions, duration_us=duration_us,
    )
    evaluation = evaluate_predictions(measured, runs, score_h2=score_h2)
    static_jobs = sorted({
        jobid
        for calibration in calibrations.values()
        for cell in calibration.raw_cells
        for jobid in cell["pbs_jobids"]
    })
    return {
        "schema_version": SCHEMA,
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat().replace(
            "+00:00", "Z"
        ),
        "not_certified": NOT_CERTIFIED,
        "protocol": PROTOCOL,
        "configuration": {
            "threads": THREADS,
            "records": RECORDS,
            "zipf_skew": ZIPF_SKEW,
            "duration_us": duration_us,
            "repetitions": repetitions,
            "base_seed": BASE_SEED,
            "rng": "numpy.random.Generator(PCG64)",
            "condition_order": [list(row) for row in prediction_conditions()],
            "scenario_order": [
                scenario.name for scenario in (
                    EXACT, NO_TRUNC, NO_P4, NO_TRUNC_NO_P4,
                    NO_COUNT_NOISE, FLAT_TAIL, LINEAR_ZERO,
                    LOG_INTERP, FANO2, FANO4,
                )
            ],
            "fixed_rules": {
                "stage1_max_kendall_distance": STAGE1_MAX_KENDALL_DISTANCE,
                "d1475_max_kendall_distance": D1475_MAX_KENDALL_DISTANCE,
                "B_strict_ratio_limit": B_MAX_MIN_RATIO_LIMIT,
                "d1475_valley_tps": D1475_VALLEY_TPS,
                "valley_relative_tolerance": D1475_VALLEY_RELATIVE_TOLERANCE,
                "H1_step2_inclusive_min": H1_STEP2_MIN_CAP_RATIO,
                "H1_step0.5_inclusive_max": H1_STEP05_MAX_CAP_RATIO,
                "H1_ratio_relative_tolerance": H1_RATIO_RELATIVE_TOLERANCE,
            },
        },
        "provenance": {
            "measured_input": {
                "path": str(measured_path), "sha256": _sha256(measured_path),
            },
            "backoff_copy": {
                "path": str(backoff_copy), "sha256": _sha256(backoff_copy),
                "source_pin": SOURCE_PIN,
            },
            "generator": {
                "path": str(Path(__file__).resolve()),
                "sha256": _sha256(Path(__file__).resolve()),
            },
            "static_calibration_jobids": static_jobs,
            "tail_inputs": tail_provenance,
            "evaluation_jobids": _evaluation_jobids(
                measured, score_h2=score_h2,
            ),
            "numpy_version": np.__version__,
        },
        "calibrations": {
            workload: _calibration_json(calibration)
            for workload, calibration in calibrations.items()
        },
        "predictions": runs,
        "evaluation": evaluation,
    }


def _atomic_json(path: Path, document: Mapping[str, Any]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(document, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("measured_json", type=Path)
    parser.add_argument("backoff_copy", type=Path)
    parser.add_argument("output_json", type=Path)
    parser.add_argument(
        "--score-h2", action="store_true",
        help=(
            "score balanced/read-heavy as a post-hoc, parameter-independent "
            "consistency check"
        ),
    )
    parser.add_argument(
        "--tail-json", action="append", default=[], metavar="WORKLOAD=PATH",
        help="add all three T-2266 static-tail workload reports",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        document = build_document(
            args.measured_json, args.backoff_copy, score_h2=args.score_h2,
            tail_json=args.tail_json,
        )
        document["provenance"]["reproduction"] = {
            "argv": [
                "python3", str(Path(__file__).resolve()),
                str(args.measured_json.resolve()), str(args.backoff_copy.resolve()),
                str(args.output_json.resolve()),
                *(["--score-h2"] if args.score_h2 else []),
                *[
                    value
                    for entry in args.tail_json
                    for value in ("--tail-json", entry)
                ],
            ]
        }
        _atomic_json(args.output_json, document)
    except Exception as exc:  # noqa: BLE001 - fail-closed CLI boundary.
        print(f"[error] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {args.output_json.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
