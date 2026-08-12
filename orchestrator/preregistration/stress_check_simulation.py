"""Deterministic T-139 a12 empirical stress simulation.

This module is not an admission gate. It does not resolve preregistration,
submit a pilot, approve a run, or verify a receipt. A successful result is
limited to the pinned empirical stress model and does not complete the core
weak-null calibration obligation.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import platform
import socket
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np


__all__ = (
    "SimulationResult",
    "run_smoke",
    "run_stress_check",
)

INPUT_RELATIVE_PATH = Path(
    "output/env/pegasus/t139-positive-control-probe/"
    "0_892042.nqsv/throughput.tsv"
)
INPUT_SHA256 = "755cfa7ea7c22ac763f404769103fd2ff0c49763c79369ac826db6a32b71c4f2"
SEED = "01dad84c523b0a476655b91979c91d7174e40bb5a27757ada312abf2fe158ed2"
SEED_DERIVATION_PREIMAGE = (
    "t139-mainrun-a12-v1|"
    "ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9"
)
FULL_REPETITIONS = 1_000_000
ALPHA_1 = 0.025
DELTA_MC = 0.001
CELL_COUNT = 60
J_VALUES = tuple(range(4, 14))
WORKLOADS = ("W1", "W2")
COMPONENTS = ("N", "H", "G")
ARM_MAPPING = {"S": "stock", "D_g": "mode1", "X": "modeX"}
ALGORITHM_VERSION = "t139-a12-v1"
BETA_CF_MAX_ITERATIONS = 10_000
_BETA_EPSILON = 4.0 * sys.float_info.epsilon
_HASH_DESCRIPTION = "Recomputation aid only; not an acceptance condition."


@dataclass(frozen=True)
class SimulationResult:
    """In-memory result and the canonical transcript path."""

    verdict: str | None
    run_status: str
    authoritative: bool
    transcript: Mapping[str, Any]
    output_path: Path


class _PreconditionFailure(Exception):
    pass


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("ascii")


def _write_canonical_json(path: Path, value: Any) -> None:
    data = _canonical_bytes(value)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite transcript: {path}")
    temp = path.with_name(f".{path.name}.tmp-{os.getpid()}-{time.time_ns()}")
    try:
        with temp.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temp, path)
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass


def _load_support(repo_root: Path) -> tuple[dict[str, dict[str, np.ndarray]], dict[str, Any]]:
    path = Path(repo_root) / INPUT_RELATIVE_PATH
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise _PreconditionFailure(f"input_missing_or_unreadable:{exc.__class__.__name__}") from exc
    digest = hashlib.sha256(raw).hexdigest()
    if digest != INPUT_SHA256:
        raise _PreconditionFailure("input_digest_mismatch")
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise _PreconditionFailure("input_not_ascii") from exc
    rows = list(csv.DictReader(io.StringIO(text), delimiter="\t"))
    expected_header = ["workload", "arm", "rep", "throughput_tps"]
    if not rows or list(rows[0]) != expected_header or len(rows) != 30:
        raise _PreconditionFailure("input_shape_mismatch")
    values: dict[tuple[str, int, str], int] = {}
    try:
        for row in rows:
            workload = row["workload"]
            arm = row["arm"]
            rep = int(row["rep"])
            throughput = int(row["throughput_tps"])
            key = (workload, rep, arm)
            if key in values:
                raise _PreconditionFailure("input_duplicate_row")
            values[key] = throughput
    except (KeyError, TypeError, ValueError) as exc:
        raise _PreconditionFailure("input_parse_failure") from exc
    expected = {
        (workload, rep, arm)
        for workload in WORKLOADS
        for rep in range(1, 6)
        for arm in ARM_MAPPING.values()
    }
    if set(values) != expected:
        raise _PreconditionFailure("input_key_mismatch")

    support: dict[str, dict[str, np.ndarray]] = {}
    for workload in WORKLOADS:
        raw_components: dict[str, list[int]] = {name: [] for name in COMPONENTS}
        for rep in range(1, 6):
            stock = values[(workload, rep, "stock")]
            mode1 = values[(workload, rep, "mode1")]
            modex = values[(workload, rep, "modeX")]
            raw_components["N"].append(5 * (modex - mode1))
            raw_components["H"].append(4 * stock - 5 * mode1)
            raw_components["G"].append(5 * (stock - modex))
        support[workload] = {}
        for component, raw_values in raw_components.items():
            total = sum(raw_values)
            numerators = np.asarray(
                [5 * item - total for item in raw_values], dtype=np.int64
            )
            if int(numerators.sum()) != 0 or numerators.shape != (5,):
                raise _PreconditionFailure("residual_support_failure")
            support[workload][component] = numerators
    metadata = {
        "path": INPUT_RELATIVE_PATH.as_posix(),
        "sha256": digest,
        "byte_count": len(raw),
        "line_count": len(text.splitlines()),
        "data_row_count": len(rows),
    }
    return support, metadata


def _prng_prefix(J: int, workload: str, component: str) -> hashlib._Hash:
    if J not in J_VALUES or workload not in WORKLOADS or component not in COMPONENTS:
        raise ValueError("invalid cell key")
    domain = f"|t139-a12-v1|{J}|{workload}|{component}".encode("ascii")
    return hashlib.sha256(SEED.encode("ascii") + domain)


def _prng_bytes(J: int, workload: str, component: str, count: int) -> bytes:
    if count < 0:
        raise ValueError("count must be nonnegative")
    prefix = _prng_prefix(J, workload, component)
    blocks = bytearray()
    counter = 0
    while len(blocks) < count:
        if counter > (1 << 64) - 1:
            raise OverflowError("PRNG counter exhausted")
        state = prefix.copy()
        state.update(counter.to_bytes(8, "big"))
        blocks.extend(state.digest())
        counter += 1
    return bytes(blocks[:count])


def _accept_raw_bytes(raw: bytes | bytearray | np.ndarray) -> np.ndarray:
    if isinstance(raw, np.ndarray):
        values = np.asarray(raw, dtype=np.uint8)
    else:
        values = np.frombuffer(raw, dtype=np.uint8)
    accepted = values[values != 255]
    return np.remainder(accepted, 5).astype(np.uint8, copy=False)


class _IndexStream:
    def __init__(self, J: int, workload: str, component: str) -> None:
        self._prefix = _prng_prefix(J, workload, component)
        self._generated_blocks = 0
        self._pending = b""
        self.raw_bytes_consumed = 0
        self.rejected_bytes = 0
        self.accepted_count = 0
        self._accepted_hash = hashlib.sha256()

    def _generate(self, minimum_raw: int) -> None:
        block_count = max(1, math.ceil(minimum_raw / 32))
        new = bytearray()
        for _ in range(block_count):
            if self._generated_blocks > (1 << 64) - 1:
                raise OverflowError("PRNG counter exhausted")
            state = self._prefix.copy()
            state.update(self._generated_blocks.to_bytes(8, "big"))
            new.extend(state.digest())
            self._generated_blocks += 1
        self._pending += bytes(new)

    def take(self, count: int) -> np.ndarray:
        if count < 0:
            raise ValueError("count must be nonnegative")
        if count == 0:
            return np.empty(0, dtype=np.uint8)
        while True:
            values = np.frombuffer(self._pending, dtype=np.uint8)
            accepted_positions = np.flatnonzero(values != 255)
            if accepted_positions.size >= count:
                stop = int(accepted_positions[count - 1]) + 1
                consumed = values[:stop]
                accepted = np.remainder(consumed[consumed != 255], 5).astype(
                    np.uint8, copy=False
                )
                self.rejected_bytes += int(np.count_nonzero(consumed == 255))
                self.raw_bytes_consumed += stop
                self._pending = self._pending[stop:]
                self.accepted_count += count
                self._accepted_hash.update(accepted.tobytes())
                return accepted
            needed = count - int(accepted_positions.size)
            self._generate(max(32, math.ceil(needed * 256 / 255)))

    @property
    def accepted_sha256(self) -> str:
        return self._accepted_hash.hexdigest()

    @property
    def final_counter(self) -> int:
        return self.raw_bytes_consumed // 32

    @property
    def final_byte_offset(self) -> int:
        return self.raw_bytes_consumed % 32


def _beta_continued_fraction(a: float, b: float, x: float) -> tuple[float, int]:
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    tiny = sys.float_info.min / _BETA_EPSILON
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    result = d
    for iteration in range(1, BETA_CF_MAX_ITERATIONS + 1):
        m2 = 2 * iteration
        aa = iteration * (b - iteration) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        result *= d * c
        aa = -(a + iteration) * (qab + iteration) * x / (
            (a + m2) * (qap + m2)
        )
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        result *= delta
        if abs(delta - 1.0) <= _BETA_EPSILON:
            return result, iteration
    raise ArithmeticError("incomplete beta continued fraction did not converge")


def _regularized_beta_details(a: float, b: float, x: float) -> tuple[float, int]:
    if not (a > 0.0 and b > 0.0 and 0.0 <= x <= 1.0):
        raise ValueError("invalid regularized beta arguments")
    if x == 0.0:
        return 0.0, 0
    if x == 1.0:
        return 1.0, 0
    log_front = (
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log1p(-x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        fraction, iterations = _beta_continued_fraction(a, b, x)
        value = math.exp(log_front) * fraction / a
    else:
        fraction, iterations = _beta_continued_fraction(b, a, 1.0 - x)
        value = 1.0 - math.exp(log_front) * fraction / b
    if not math.isfinite(value):
        raise ArithmeticError("non-finite regularized beta result")
    return min(1.0, max(0.0, value)), iterations


def _regularized_beta(a: float, b: float, x: float) -> float:
    return _regularized_beta_details(a, b, x)[0]


def _q_tail_details(J: int, q: float) -> tuple[float, int]:
    if J not in J_VALUES:
        raise ValueError("q requires 4 <= J <= 13")
    if q < 0.0:
        raise ValueError("q must be nonnegative")
    f_survival = (1.0 + q * q / (J - 1)) ** (-(J - 2) / 2.0)
    if q == 0.0:
        t_survival = 0.5
        iterations = 0
    else:
        nu = J - 1
        z = nu / (nu + q * q)
        beta_value, iterations = _regularized_beta_details(nu / 2.0, 0.5, z)
        t_survival = 0.5 * beta_value
    return f_survival + t_survival, iterations


def _q_tail(J: int, q: float) -> float:
    return _q_tail_details(J, q)[0]


def _q_details(J: int) -> dict[str, Any]:
    if J not in J_VALUES:
        raise ValueError("q requires 4 <= J <= 13")
    beta_iterations_max = 0

    def evaluate(q: float) -> float:
        nonlocal beta_iterations_max
        value, iterations = _q_tail_details(J, q)
        beta_iterations_max = max(beta_iterations_max, iterations)
        return value

    root_low = 0.0
    root_high = 1.0
    while evaluate(root_high) > ALPHA_1:
        root_low = root_high
        root_high *= 2.0
    while (root_high - root_low) / root_high > 1e-13:
        middle = (root_low + root_high) / 2.0
        if evaluate(middle) <= ALPHA_1:
            root_high = middle
        else:
            root_low = middle

    low = 0
    high = 1_000_000_000
    while evaluate(high / 1_000_000_000) > ALPHA_1:
        low = high
        high *= 2
    while low + 1 < high:
        middle = (low + high) // 2
        if evaluate(middle / 1_000_000_000) <= ALPHA_1:
            high = middle
        else:
            low = middle
    q = high / 1_000_000_000
    previous = (high - 1) / 1_000_000_000
    tail = evaluate(q)
    previous_tail = evaluate(previous)
    if not (tail <= ALPHA_1 < previous_tail):
        raise ArithmeticError("q nanogrid boundary was not established")
    return {
        "J": J,
        "q": q,
        "q_nano": high,
        "unrounded_root_bracket": [root_low, root_high],
        "root_relative_bracket_width": (root_high - root_low) / root_high,
        "tail": tail,
        "previous_grid_tail": previous_tail,
        "beta_iterations_max": beta_iterations_max,
    }


def _q_value(J: int) -> float:
    return float(_q_details(J)["q"])


def _clopper_pearson_upper_details(x: int, B: int) -> tuple[float, int]:
    if isinstance(x, bool) or isinstance(B, bool) or not isinstance(x, int) or not isinstance(B, int):
        raise TypeError("x and B must be integers")
    if B <= 0 or not 0 <= x <= B:
        raise ValueError("require B > 0 and 0 <= x <= B")
    gamma = DELTA_MC / CELL_COUNT
    if x == B:
        return 1.0, 0
    if x == 0:
        return -math.expm1(math.log(gamma) / B), 0
    low = 0.0
    high = 1.0
    max_iterations = 0
    for _ in range(80):
        middle = (low + high) / 2.0
        complement, iterations = _regularized_beta_details(
            float(B - x), float(x + 1), 1.0 - middle
        )
        max_iterations = max(max_iterations, iterations)
        if complement > gamma:
            low = middle
        else:
            high = middle
        if math.nextafter(low, math.inf) >= high:
            break
    return high, max_iterations


def _clopper_pearson_upper(x: int, B: int) -> float:
    return _clopper_pearson_upper_details(x, B)[0]


def _false_pass_from_cluster_sums(
    cluster_sums: np.ndarray | Sequence[Sequence[float]],
    q: float,
    *,
    ddof: int = 1,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    values = np.asarray(cluster_sums, dtype=np.float64)
    if values.ndim == 1:
        values = values.reshape(1, -1)
    if values.ndim != 2 or values.shape[1] < 2:
        raise ValueError("cluster_sums must have shape (datasets, J) with J >= 2")
    means = values.mean(axis=1)
    variances = values.var(axis=1, ddof=ddof)
    lower = means - q * np.sqrt(variances / values.shape[1])
    return lower > 0.0, means, variances


def _simulate_cell(
    support_values: np.ndarray,
    J: int,
    workload: str,
    component: str,
    B: int,
    chunk_datasets: int,
    q: float,
) -> dict[str, Any]:
    if B <= 0 or chunk_datasets <= 0:
        raise ValueError("B and chunk_datasets must be positive")
    support = np.asarray(support_values, dtype=np.int64)
    if support.shape != (5,):
        raise ValueError("support must contain exactly five workload-specific points")
    stream = _IndexStream(J, workload, component)
    false_passes = 0
    completed = 0
    while completed < B:
        count = min(chunk_datasets, B - completed)
        indices = stream.take(count * J * 6).reshape(count, J, 6)
        cluster_sums = support[indices].sum(axis=2, dtype=np.int64)
        flags, _, _ = _false_pass_from_cluster_sums(cluster_sums, q)
        false_passes += int(np.count_nonzero(flags))
        completed += count
    return {
        "J": J,
        "workload": workload,
        "component": component,
        "x": false_passes,
        "completed_datasets": completed,
        "accepted_draws": stream.accepted_count,
        "rejected_bytes": stream.rejected_bytes,
        "final_counter": stream.final_counter,
        "final_byte_offset": stream.final_byte_offset,
        "stream_sha256": {
            "value": stream.accepted_sha256,
            "description": _HASH_DESCRIPTION,
        },
    }


def _simulate_cell_task(arguments: tuple[Any, ...]) -> dict[str, Any]:
    return _simulate_cell(*arguments)


def _cell_keys() -> tuple[tuple[int, str, str], ...]:
    return tuple(
        (J, workload, component)
        for J in J_VALUES
        for workload in WORKLOADS
        for component in COMPONENTS
    )


def _aggregate_cells(
    worker_results: Sequence[Mapping[str, Any]],
    B: int,
    *,
    upper_bound_fn: Callable[[int, int], float] | None = None,
) -> tuple[str, list[dict[str, Any]], int]:
    if B <= 0:
        raise ValueError("B must be positive")
    expected = set(_cell_keys())
    received: dict[tuple[int, str, str], Mapping[str, Any]] = {}
    for result in worker_results:
        key = (result.get("J"), result.get("workload"), result.get("component"))
        if key in received:
            raise ValueError("duplicate cell result")
        received[key] = result
    if set(received) != expected:
        raise ValueError("cell results are not the exact 60-cell Cartesian product")
    cells: list[dict[str, Any]] = []
    all_pass = True
    max_iterations = 0
    for J, workload, component in _cell_keys():
        result = received[(J, workload, component)]
        x = result.get("x")
        if isinstance(x, bool) or not isinstance(x, int) or not 0 <= x <= B:
            raise ValueError("invalid false-pass count")
        if result.get("completed_datasets") != B:
            raise ValueError("cell did not complete all datasets")
        if result.get("accepted_draws") != 6 * J * B:
            raise ValueError("cell did not consume all accepted draws")
        if upper_bound_fn is None:
            upper, iterations = _clopper_pearson_upper_details(x, B)
        else:
            upper = float(upper_bound_fn(x, B))
            iterations = 0
        cell_pass = upper <= ALPHA_1
        all_pass = all_pass and cell_pass
        max_iterations = max(max_iterations, iterations)
        copied = dict(result)
        copied["U"] = upper
        copied["cell_pass"] = cell_pass
        copied["beta_iterations_max"] = iterations
        cells.append(copied)
    return ("pass" if all_pass else "design_not_feasible"), cells, max_iterations


def _auto_workers() -> int:
    try:
        available = len(os.sched_getaffinity(0))
    except AttributeError:
        available = os.cpu_count() or 1
    return max(1, min(CELL_COUNT, available))


def _run_cells(
    support: Mapping[str, Mapping[str, np.ndarray]],
    B: int,
    workers: int | None,
    chunk_datasets: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    worker_count = _auto_workers() if workers is None else workers
    if isinstance(worker_count, bool) or not isinstance(worker_count, int) or worker_count <= 0:
        raise ValueError("workers must be a positive integer or None")
    q_details = [_q_details(J) for J in J_VALUES]
    q_by_J = {item["J"]: item["q"] for item in q_details}
    tasks = [
        (
            support[workload][component],
            J,
            workload,
            component,
            B,
            chunk_datasets,
            q_by_J[J],
        )
        for J, workload, component in sorted(_cell_keys(), reverse=True)
    ]
    if worker_count == 1:
        results = [_simulate_cell_task(task) for task in tasks]
    else:
        results = []
        with ProcessPoolExecutor(max_workers=min(worker_count, CELL_COUNT)) as executor:
            futures = [executor.submit(_simulate_cell_task, task) for task in tasks]
            for future in as_completed(futures):
                results.append(future.result())
    return results, q_details, worker_count


def _base_transcript(mode: str, authoritative: bool, B: int, chunk: int) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "algorithm_version": ALGORITHM_VERSION,
        "mode": mode,
        "authoritative": authoritative,
        "claim_scope": {
            "value": "a11_empirical_stress_model_only",
            "core_weak_null_calibration_complete": False,
            "pilot_ready": False,
            "remaining_unmet_pilot_prerequisites": [1, 4, 5, 6, 7, 8, 9],
        },
        "source_commit": {"value": None, "description": _HASH_DESCRIPTION},
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "hostname": socket.gethostname(),
            "scheduler_job_id": os.environ.get("PBS_JOBID"),
            "chunk_datasets": chunk,
        },
        "constants": {
            "seed": SEED,
            "seed_derivation_preimage": SEED_DERIVATION_PREIMAGE,
            "B": B,
            "J": list(J_VALUES),
            "workloads": list(WORKLOADS),
            "components": list(COMPONENTS),
            "alpha_1": {"numerator": 1, "denominator": 40},
            "delta_MC": {"numerator": 1, "denominator": 1000},
            "kappa": {"numerator": 1, "denominator": 5},
            "arm_mapping": ARM_MAPPING,
        },
        "prng": {
            "grammar_version": ALGORITHM_VERSION,
            "seed_encoding": "64 lowercase hexadecimal ASCII bytes",
            "counter_start": 0,
            "counter_encoding": "uint64 big endian",
            "digest_byte_order": "raw bytes 0 through 31",
            "rejected_byte": 255,
            "draw_order": ["dataset", "cluster", "block_position_0_through_5"],
            "B_in_domain": False,
            "grammar_sensitivity": (
                "The adjudicated alternative rejection grammars did not change the "
                "conclusion in the independent full runs."
            ),
        },
        "field_descriptions": {
            "source_commit": _HASH_DESCRIPTION,
            "stream_sha256": _HASH_DESCRIPTION,
            "result_sha256": _HASH_DESCRIPTION,
        },
    }


def _precondition_result(
    *,
    mode: str,
    authoritative: bool,
    B: int,
    chunk_datasets: int,
    output_path: Path,
    reason: str,
) -> SimulationResult:
    transcript = _base_transcript(mode, authoritative, B, chunk_datasets)
    transcript.update(
        {
            "run_status": "precondition_failed",
            "verdict": "design_not_feasible",
            "reason_codes": [reason],
            "cells": [],
            "completed_cell_count": 0,
        }
    )
    deterministic = {
        "run_status": transcript["run_status"],
        "verdict": transcript["verdict"],
        "reason_codes": transcript["reason_codes"],
        "cells": [],
    }
    transcript["result_sha256"] = {
        "value": hashlib.sha256(_canonical_bytes(deterministic)).hexdigest(),
        "description": _HASH_DESCRIPTION,
    }
    _write_canonical_json(output_path, transcript)
    return SimulationResult(
        verdict="design_not_feasible",
        run_status="precondition_failed",
        authoritative=authoritative,
        transcript=transcript,
        output_path=Path(output_path),
    )


def _run(
    *,
    repo_root: Path,
    output_path: Path,
    mode: str,
    authoritative: bool,
    B: int,
    workers: int | None,
    chunk_datasets: int,
) -> SimulationResult:
    output_path = Path(output_path)
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite transcript: {output_path}")
    started = time.monotonic()
    try:
        support, input_metadata = _load_support(Path(repo_root))
    except _PreconditionFailure as exc:
        return _precondition_result(
            mode=mode,
            authoritative=authoritative,
            B=B,
            chunk_datasets=chunk_datasets,
            output_path=output_path,
            reason=str(exc),
        )
    raw_results, q_details, worker_count = _run_cells(
        support, B, workers, chunk_datasets
    )
    aggregate_verdict, cells, cp_iterations = _aggregate_cells(raw_results, B)
    elapsed = time.monotonic() - started
    verdict: str | None = aggregate_verdict if authoritative else None
    transcript = _base_transcript(mode, authoritative, B, chunk_datasets)
    transcript["runtime"].update(
        {"workers": worker_count, "elapsed_seconds": elapsed}
    )
    transcript.update(
        {
            "run_status": "completed",
            "verdict": verdict,
            "reason_codes": [],
            "input": input_metadata,
            "residual_support": {
                workload: {
                    component: {
                        "numerators": support[workload][component].tolist(),
                        "denominator": 25,
                    }
                    for component in COMPONENTS
                }
                for workload in WORKLOADS
            },
            "q": q_details,
            "beta_cf_max_iterations": {
                "q": max(item["beta_iterations_max"] for item in q_details),
                "clopper_pearson": cp_iterations,
                "configured_limit": BETA_CF_MAX_ITERATIONS,
            },
            "cells": cells,
            "completed_cell_count": len(cells),
            "exact_cartesian_product": len(cells) == CELL_COUNT,
            "smoke_aggregate_would_pass": (
                aggregate_verdict == "pass" if not authoritative else None
            ),
        }
    )
    deterministic = {
        "algorithm_version": ALGORITHM_VERSION,
        "mode": mode,
        "authoritative": authoritative,
        "input": input_metadata,
        "constants": transcript["constants"],
        "q": q_details,
        "cells": cells,
        "verdict": verdict,
    }
    transcript["result_sha256"] = {
        "value": hashlib.sha256(_canonical_bytes(deterministic)).hexdigest(),
        "description": _HASH_DESCRIPTION,
    }
    _write_canonical_json(output_path, transcript)
    return SimulationResult(
        verdict=verdict,
        run_status="completed",
        authoritative=authoritative,
        transcript=transcript,
        output_path=output_path,
    )


def run_stress_check(
    *,
    repo_root: Path,
    output_path: Path,
    workers: int | None = None,
    chunk_datasets: int = 32_768,
) -> SimulationResult:
    """Run the pinned authoritative B=1,000,000 simulation."""

    return _run(
        repo_root=repo_root,
        output_path=output_path,
        mode="full",
        authoritative=True,
        B=FULL_REPETITIONS,
        workers=workers,
        chunk_datasets=chunk_datasets,
    )


def run_smoke(
    *,
    repo_root: Path,
    output_path: Path,
    repetitions: int = 10_000,
    workers: int | None = None,
    chunk_datasets: int = 32_768,
) -> SimulationResult:
    """Run all 60 cells on a non-authoritative prefix of every full stream."""

    if isinstance(repetitions, bool) or not isinstance(repetitions, int) or repetitions <= 0:
        raise ValueError("repetitions must be a positive integer")
    return _run(
        repo_root=repo_root,
        output_path=output_path,
        mode="smoke",
        authoritative=False,
        B=repetitions,
        workers=workers,
        chunk_datasets=chunk_datasets,
    )
