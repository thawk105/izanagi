#!/usr/bin/env python3
"""Bounded paired-block measurement runner for the T-1618 xdist replay."""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
import platform
import re
import signal
import statistics
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

from replay import (
    CALLERS,
    ReplayEngine,
    ReplayError,
    ReplayInput,
    _distribution,
    certify,
    load_replay_input,
    verify_xdist_sources,
)


sys.dont_write_bytecode = True

RESULT_SCHEMA = "t1618-xdist-controller-cost-result/v4"
INPUT_SCHEMA = "t1618-input-manifest/v2"
RECEIPT_SCHEMA = "t1618-success-receipt/v1"
SAMPLE_SCHEMA = "t1618-fresh-paired-block-sample/v2"
DRAFT_2020_12_SCHEMA_URI = "https://json-schema.org/draft/2020-12/schema"
RAW_RESULT_SCHEMA_PATH = Path(__file__).resolve().parent / "raw-result.schema.json"
SCENARIOS = ("protocol-only", "pass-event")
EXPECTED_OUTPUT_RELATIVE = Path("output/runs/t1618-xdist-controller-cost")
MIN_PAIRS_DEFAULT = 30
MAX_PAIRS_DEFAULT = 60
RELATIVE_HALF_WIDTH_DEFAULT = 0.20
MINIMUM_PRACTICAL_EFFECT_S_DEFAULT = 0.005
ABSOLUTE_NOISE_BOUND_S_DEFAULT = 0.010
PATH_A_DECISION_THRESHOLD_S = 0.500
FULL_DEADLINE_SECONDS = 10_500.0
FULL_WALL_LIMIT_SECONDS = 10_800.0
PILOT_ITEM_LIMIT = 256
PILOT_PAIRS = 2
PILOT_WORKERS = 4
SOURCE_FILES = (
    "prepare_inputs.py",
    "replay.py",
    "measure.py",
    "submit_t1618.py",
    "test_t1618_entrypoint.py",
    "promote_result.py",
    "raw-result.schema.json",
)


class MeasurementError(RuntimeError):
    """A measurement precondition, child block, or result contract failed closed."""


def _repo_root() -> Path:
    root = Path(__file__).resolve().parents[3]
    if not (root / "tools/run_tests.py").is_file():
        raise MeasurementError("repository root cannot be resolved")
    return root


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("ascii")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise MeasurementError(f"cannot hash {path}: {exc}") from exc
    return digest.hexdigest()


def _write_atomic(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MeasurementError(f"cannot read JSON object {path}: {exc}") from exc
    if type(value) is not dict:
        raise MeasurementError(f"JSON top level is not an object: {path}")
    return value


@lru_cache(maxsize=1)
def _raw_result_schema_validator() -> Any:
    schema = _read_json(RAW_RESULT_SCHEMA_PATH)
    if schema.get("$schema") != DRAFT_2020_12_SCHEMA_URI:
        raise MeasurementError("raw result schema is not Draft 2020-12")
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        # Pegasus currently provides jsonschema 3.2.0.  This schema uses only
        # keywords whose evaluation is identical in Draft 7 and Draft 2020-12;
        # $defs is reached through JSON Pointer references.  Keep the declared
        # dialect check above fail-closed and use the older engine only for this
        # compatible vocabulary until the cluster package exposes the named
        # Draft 2020-12 validator.
        from jsonschema import Draft7Validator as Draft202012Validator
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        raise MeasurementError(f"invalid Draft 2020-12 raw result schema: {exc}") from exc
    return Draft202012Validator(schema)


def validate_raw_result_schema(raw: Mapping[str, Any]) -> None:
    try:
        errors = sorted(
            _raw_result_schema_validator().iter_errors(raw),
            key=lambda error: [str(part) for part in error.absolute_path],
        )
    except MeasurementError:
        raise
    except Exception as exc:
        raise MeasurementError(f"Draft 2020-12 raw result validation failed: {exc}") from exc
    if errors:
        error = errors[0]
        path = "$" + "".join(
            f"[{part}]" if type(part) is int else f".{part}"
            for part in error.absolute_path
        )
        raise MeasurementError(
            f"Draft 2020-12 raw result schema mismatch at {path}: {error.message}"
        )


def load_manifest(path: Path) -> dict[str, Any]:
    manifest = _read_json(path)
    if manifest.get("schema_version") != INPUT_SCHEMA:
        raise MeasurementError("unknown input manifest schema")
    if manifest.get("snapshot_format") != "compact-deduplicated-json":
        raise MeasurementError("input manifest is not the compact durable snapshot")
    return manifest


def _finite_tree(value: Any, path: str = "$") -> None:
    if type(value) is float and not math.isfinite(value):
        raise MeasurementError(f"nonfinite result number at {path}")
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str:
                raise MeasurementError(f"non-string JSON key at {path}")
            _finite_tree(child, f"{path}.{key}")
    elif type(value) is list:
        for index, child in enumerate(value):
            _finite_tree(child, f"{path}[{index}]")


def _exact_keys(value: Any, keys: set[str], path: str) -> Mapping[str, Any]:
    if type(value) is not dict or set(value) != keys:
        actual = sorted(value) if type(value) is dict else type(value).__name__
        raise MeasurementError(f"exact object schema mismatch at {path}: {actual!r}")
    return value


def _thread_count() -> int | None:
    try:
        return len(list(Path("/proc/self/task").iterdir()))
    except OSError:
        return None


def _pin_one_core(requested_core: int) -> dict[str, Any]:
    if not hasattr(os, "sched_getaffinity") or not hasattr(os, "sched_setaffinity"):
        raise MeasurementError("single-core affinity is unavailable")
    before = sorted(os.sched_getaffinity(0))
    if requested_core not in before:
        if before == [requested_core]:
            return {"before": before, "selected": requested_core, "after": before}
        raise MeasurementError(f"requested core {requested_core} is outside affinity {before!r}")
    os.sched_setaffinity(0, {requested_core})
    after = sorted(os.sched_getaffinity(0))
    if after != [requested_core]:
        raise MeasurementError("single-core affinity did not take effect")
    return {"before": before, "selected": requested_core, "after": after}


def _pre_touch_memory_pressure(mebibytes: int = 128) -> bytearray:
    buffer = bytearray(mebibytes * 1024 * 1024)
    for offset in range(0, len(buffer), 4096):
        buffer[offset] = (offset // 4096) & 0xFF
    return buffer


def timed_sample(
    replay_input: ReplayInput,
    arm: Mapping[str, Any],
    *,
    core: int,
    pilot: bool,
) -> dict[str, Any]:
    engine = ReplayEngine(
        replay_input,
        scenario=arm["scenario"],
        index_mode=arm["index_mode"],
        pending_policy=arm["pending_policy"],
        real_callers=arm.get("real_callers", ()),
        identity_mode=arm.get("identity_mode", "first-worker-alias"),
        amplification_k=arm.get("amplification_k", 1),
        diagnostics=False,
    )
    engine.prepare()
    affinity = _pin_one_core(core)
    pressure = (
        _pre_touch_memory_pressure()
        if arm.get("pre_touch_memory_pressure", False)
        else None
    )
    gc.collect()
    gc_events: Counter[str] = Counter()

    def gc_callback(phase: str, _info: Mapping[str, Any]) -> None:
        gc_events[phase] += 1

    thread_before = _thread_count()
    gc.callbacks.append(gc_callback)
    process_start = time.process_time_ns()
    wall_start = time.perf_counter_ns()
    try:
        engine.run_timed()
    finally:
        wall_end = time.perf_counter_ns()
        process_end = time.process_time_ns()
        gc.callbacks.remove(gc_callback)
    replay = engine.finalize()
    thread_after = _thread_count()
    del pressure
    return {
        "schema_version": SAMPLE_SCHEMA,
        "population_id": replay_input.population_id,
        "controller_id": replay_input.controller_id,
        "pilot": pilot,
        "pid": os.getpid(),
        "scenario": arm["scenario"],
        "index_mode": arm["index_mode"],
        "pending_policy": arm["pending_policy"],
        "real_callers": list(arm.get("real_callers", ())),
        "identity_mode": arm.get("identity_mode", "first-worker-alias"),
        "amplification_k": arm.get("amplification_k", 1),
        "pre_touch_memory_pressure": arm.get("pre_touch_memory_pressure", False),
        "process_cpu_s": (process_end - process_start) / 1_000_000_000,
        "wall_s": (wall_end - wall_start) / 1_000_000_000,
        "list_index_slot_probes": replay["list_index_slot_probes"],
        "pending_calls": replay["pending_calls"],
        "gc_events": dict(sorted(gc_events.items())),
        "thread_count_before": thread_before,
        "thread_count_after": thread_after,
        "affinity": affinity,
        "clock": {
            "process_time": vars(time.get_clock_info("process_time")),
            "perf_counter": vars(time.get_clock_info("perf_counter")),
        },
    }


def _student_t_critical_975(df: int) -> float:
    if df <= 0:
        return math.inf
    z = 1.959963984540054
    inverse = 1.0 / df
    return (
        z
        + (z**3 + z) * inverse / 4
        + (5 * z**5 + 16 * z**3 + 3 * z) * inverse**2 / 96
        + (3 * z**7 + 19 * z**5 + 17 * z**3 - 15 * z) * inverse**3 / 384
    )


def _ci95(values: Sequence[float]) -> dict[str, Any]:
    if not values:
        raise MeasurementError("cannot form a confidence interval from no values")
    mean = statistics.fmean(values)
    if len(values) == 1:
        return {
            "n": 1, "mean_s": mean, "standard_deviation_s": None,
            "half_width_s": None, "low_s": None, "high_s": None,
            "relative_half_width": None,
        }
    deviation = statistics.stdev(values)
    half = _student_t_critical_975(len(values) - 1) * deviation / math.sqrt(len(values))
    return {
        "n": len(values), "mean_s": mean, "standard_deviation_s": deviation,
        "half_width_s": half, "low_s": mean - half, "high_s": mean + half,
        "relative_half_width": None if mean == 0 else abs(half / mean),
    }


def _block_payload(
    replay_input: ReplayInput,
    treatment: Mapping[str, Any],
    control: Mapping[str, Any],
    block_index: int,
    core: int,
    pilot: bool,
) -> dict[str, Any]:
    order = "ABBA" if block_index % 2 == 0 else "BAAB"
    started = time.perf_counter()
    samples = []
    for symbol in order:
        sample = timed_sample(
            replay_input,
            treatment if symbol == "A" else control,
            core=core,
            pilot=pilot,
        )
        samples.append({"arm": symbol, "sample": sample})
    treatment_values = [
        entry["sample"]["process_cpu_s"] for entry in samples if entry["arm"] == "A"
    ]
    control_values = [
        entry["sample"]["process_cpu_s"] for entry in samples if entry["arm"] == "B"
    ]
    return {
        "population_id": replay_input.population_id,
        "controller_id": replay_input.controller_id,
        "block": block_index,
        "order": order,
        "paired_difference_s": statistics.fmean(treatment_values)
        - statistics.fmean(control_values),
        "block_wall_s": time.perf_counter() - started,
        "samples": samples,
    }


class BlockRunner:
    """Fork one fresh process per paired block and checkpoint every block."""

    def __init__(
        self, attempt_dir: Path, deadline_at: float, *, max_workers: int, pilot: bool
    ) -> None:
        if not hasattr(os, "fork"):
            raise MeasurementError("paired-block freshness requires os.fork")
        self.attempt_dir = attempt_dir
        self.deadline_at = deadline_at
        self.pilot = pilot
        self.cores = sorted(os.sched_getaffinity(0))
        self.max_workers = min(max_workers, len(self.cores))
        if self.max_workers < 1:
            raise MeasurementError("no CPU is available to paired-block children")

    def run_blocks(
        self,
        replay_input: ReplayInput,
        treatment: Mapping[str, Any],
        control: Mapping[str, Any],
        label: str,
        indices: Sequence[int],
    ) -> list[dict[str, Any]]:
        safe_label = hashlib.sha256(label.encode("utf-8")).hexdigest()[:16]
        checkpoint_dir = self.attempt_dir / "checkpoints" / safe_label
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        pending = list(indices)
        active: dict[int, tuple[int, Path, int]] = {}
        results: dict[int, dict[str, Any]] = {}
        free_cores = self.cores[: self.max_workers]
        failures: list[str] = []
        while pending or active:
            if time.monotonic() >= self.deadline_at:
                raise MeasurementError("measurement hard deadline expired")
            while pending and free_cores:
                block_index = pending.pop(0)
                path = checkpoint_dir / f"block-{block_index:03d}.json"
                if path.exists():
                    raise MeasurementError(f"stale checkpoint already exists: {path}")
                core = free_cores.pop(0)
                pid = os.fork()
                if pid == 0:
                    try:
                        remaining = max(1, math.ceil(self.deadline_at - time.monotonic()))
                        signal.alarm(remaining)
                        payload = _block_payload(
                            replay_input, treatment, control, block_index, core, self.pilot
                        )
                        _finite_tree(payload)
                        _write_atomic(path, _canonical_json_bytes(payload))
                        os._exit(0)
                    except BaseException as exc:
                        try:
                            _write_atomic(
                                path.with_suffix(".error.json"),
                                _canonical_json_bytes(
                                    {"block": block_index, "error": f"{type(exc).__name__}: {exc}"}
                                ),
                            )
                        finally:
                            os._exit(2)
                active[pid] = (block_index, path, core)
            pid, wait_status = os.wait()
            if pid not in active:
                raise MeasurementError(f"reaped an unknown paired-block child: {pid}")
            block_index, path, core = active.pop(pid)
            free_cores.append(core)
            free_cores.sort()
            if not os.WIFEXITED(wait_status) or os.WEXITSTATUS(wait_status) != 0:
                failures.append(f"block {block_index} child status {wait_status}")
                continue
            result = _read_json(path)
            _validate_block(result, replay_input.population_id, replay_input.controller_id)
            results[block_index] = result
        if failures:
            raise MeasurementError("paired-block children failed: " + "; ".join(failures))
        return [results[index] for index in indices]


def _order_effect(blocks: Sequence[Mapping[str, Any]], noise_bound_s: float) -> dict[str, Any]:
    abba = [float(block["paired_difference_s"]) for block in blocks if block["order"] == "ABBA"]
    baab = [float(block["paired_difference_s"]) for block in blocks if block["order"] == "BAAB"]
    balanced = len(abba) == len(baab) and bool(abba)
    paired = [left - right for left, right in zip(abba, baab)]
    interval = _ci95(paired) if paired else None
    inside = bool(
        interval is not None and interval["low_s"] is not None
        and interval["high_s"] is not None
        and interval["low_s"] >= -noise_bound_s
        and interval["high_s"] <= noise_bound_s
    )
    return {
        "definition": "ABBA block difference minus BAAB block difference",
        "confidence_interval_95": interval,
        "absolute_noise_bound_s": noise_bound_s,
        "balanced": balanced,
        "gate": "passed" if balanced and inside else "failed",
    }


def _paired_measurement(
    runner: BlockRunner,
    replay_input: ReplayInput,
    treatment: Mapping[str, Any],
    control: Mapping[str, Any],
    *,
    min_pairs: int,
    max_pairs: int,
    relative_half_width: float,
    practical_effect_s: float,
    noise_bound_s: float,
    label: str,
    effect_definition: str,
) -> dict[str, Any]:
    if min_pairs < 2 or min_pairs % 2 or max_pairs < min_pairs or max_pairs % 2:
        raise MeasurementError("paired bounds require even values with minimum at least two")
    blocks = runner.run_blocks(replay_input, treatment, control, label, list(range(min_pairs)))
    if len(blocks) < max_pairs:
        interval = _ci95([float(block["paired_difference_s"]) for block in blocks])
        excludes_zero = interval["low_s"] > 0 or interval["high_s"] < 0
        precise = interval["relative_half_width"] is not None and interval["relative_half_width"] <= relative_half_width
        if not (excludes_zero and precise):
            blocks.extend(
                runner.run_blocks(
                    replay_input,
                    treatment,
                    control,
                    label,
                    list(range(len(blocks), max_pairs)),
                )
            )
    differences = [float(block["paired_difference_s"]) for block in blocks]
    interval = _ci95(differences)
    excludes_zero = interval["low_s"] > 0 or interval["high_s"] < 0
    precise = interval["relative_half_width"] is not None and interval["relative_half_width"] <= relative_half_width
    practical = abs(interval["mean_s"]) >= practical_effect_s
    if excludes_zero and precise and practical:
        status = "measured-practical-effect"
    elif excludes_zero and precise:
        status = "measured-below-practical-effect"
    else:
        status = "inconclusive-ci"
    order_effect = _order_effect(blocks, noise_bound_s)
    return {
        "label": label,
        "status": status,
        "effect_definition": effect_definition,
        "marginal_replay_cpu_saving_vs_o1_control_s": interval["mean_s"],
        "confidence_interval_95": interval,
        "minimum_practical_effect_s": practical_effect_s,
        "relative_half_width_threshold": relative_half_width,
        "independent_fresh_process_pairs": len(blocks),
        "sample_count": len(blocks) * 4,
        "abba_baab_balanced": order_effect["balanced"],
        "order_effect": order_effect,
        "blocks": blocks,
    }


def _negative_control(
    runner: BlockRunner,
    replay_input: ReplayInput,
    control: Mapping[str, Any],
    *,
    pairs: int,
    practical_effect_s: float,
    noise_bound_s: float,
    label: str,
) -> dict[str, Any]:
    result = _paired_measurement(
        runner, replay_input, control, control,
        min_pairs=pairs, max_pairs=pairs, relative_half_width=1.0,
        practical_effect_s=practical_effect_s, noise_bound_s=noise_bound_s,
        label=label, effect_definition="identical O(1) control CPU difference",
    )
    interval = result["confidence_interval_95"]
    inside = (
        interval["low_s"] is not None and interval["high_s"] is not None
        and interval["low_s"] >= -noise_bound_s
        and interval["high_s"] <= noise_bound_s
    )
    result["absolute_noise_bound_s"] = noise_bound_s
    result["negative_control_ci_gate"] = "passed" if inside else "failed"
    result["negative_control_order_gate"] = result["order_effect"]["gate"]
    return result


def _measurement_passed(value: Mapping[str, Any], minimum_pairs: int, pilot: bool) -> bool:
    return bool(
        not pilot and str(value.get("status", "")).startswith("measured-")
        and value.get("independent_fresh_process_pairs", 0) >= minimum_pairs
        and value.get("abba_baab_balanced") is True
        and value.get("order_effect", {}).get("gate") == "passed"
    )


def _path_a_adoption_gate_results(
    primary: Mapping[str, Any],
    negative: Mapping[str, Any],
    *,
    minimum_pairs: int,
    pilot: bool,
) -> dict[str, bool]:
    return {
        "primary_measurement_status": str(primary.get("status", "")).startswith(
            "measured-"
        ),
        "primary_minimum_pairs": (
            primary.get("independent_fresh_process_pairs", 0) >= minimum_pairs
        ),
        "primary_abba_baab_balanced": primary.get("abba_baab_balanced") is True,
        "primary_order_effect": primary.get("order_effect", {}).get("gate")
        == "passed",
        "negative_control_ci": negative.get("negative_control_ci_gate") == "passed",
        "negative_control_order": negative.get("negative_control_order_gate")
        == "passed",
        "non_pilot": not pilot,
    }


def _common_arm(scenario: str) -> dict[str, Any]:
    return {
        "scenario": scenario, "index_mode": "o1", "pending_policy": "all-oracle",
        "real_callers": (), "identity_mode": "first-worker-alias",
        "amplification_k": 1, "pre_touch_memory_pressure": False,
    }


def _path_a(
    runner: BlockRunner,
    replay_input: ReplayInput,
    *,
    min_pairs: int,
    max_pairs: int,
    relative_half_width: float,
    practical_effect_s: float,
    noise_bound_s: float,
    diagnostic_pairs: int,
    pilot: bool,
) -> dict[str, Any]:
    control = _common_arm("protocol-only")
    treatment = {**control, "index_mode": "real"}
    primary = _paired_measurement(
        runner, replay_input, treatment, control,
        min_pairs=min_pairs, max_pairs=max_pairs,
        relative_half_width=relative_half_width,
        practical_effect_s=practical_effect_s, noise_bound_s=noise_bound_s,
        label=f"{replay_input.controller_id}:path-a-primary",
        effect_definition="whole replay list.index CPU minus O(1) index control CPU",
    )
    negative = _negative_control(
        runner, replay_input, control, pairs=min_pairs,
        practical_effect_s=practical_effect_s, noise_bound_s=noise_bound_s,
        label=f"{replay_input.controller_id}:path-a-negative",
    )
    pressure = _paired_measurement(
        runner, replay_input,
        {**treatment, "pre_touch_memory_pressure": True},
        {**control, "pre_touch_memory_pressure": True},
        min_pairs=diagnostic_pairs, max_pairs=diagnostic_pairs,
        relative_half_width=1.0, practical_effect_s=practical_effect_s,
        noise_bound_s=noise_bound_s,
        label=f"{replay_input.controller_id}:path-a-pre-touch-pressure",
        effect_definition="unadoptable pre-touch memory-pressure diagnostic",
    )
    adoption_gate_results = _path_a_adoption_gate_results(
        primary,
        negative,
        minimum_pairs=min_pairs,
        pilot=pilot,
    )
    adopted = all(adoption_gate_results.values())
    return {
        "adopted": adopted,
        "adoption_gate_results": adoption_gate_results,
        "hot_replay": True,
        "list_index_slot_probes": len(replay_input.collection) * (len(replay_input.collection) + 1) // 2,
        "marginal_replay_cpu_saving_vs_o1_control_s": primary["marginal_replay_cpu_saving_vs_o1_control_s"],
        "primary_first_worker_identity_alias": primary,
        "negative_control": negative,
        "pre_touch_memory_pressure_diagnostic": {
            "diagnostic_only": True,
            "measurement": pressure,
        },
        "all_worker_clone_certification": "passed-before-performance",
        "actual_controller_cpu_seconds_claimed": False,
    }


def _regression_linearity(
    measurements: Mapping[int, Mapping[str, Any]], *, minimum_pairs: int, pilot: bool
) -> dict[str, Any]:
    common_n = min(len(value["blocks"]) for value in measurements.values())
    slopes = []
    relative_residuals = []
    for block_index in range(common_n):
        xs = [1.0, 2.0, 4.0, 8.0]
        ys = [float(measurements[k]["blocks"][block_index]["paired_difference_s"]) for k in (1, 2, 4, 8)]
        xmean = statistics.fmean(xs)
        ymean = statistics.fmean(ys)
        denominator = sum((x - xmean) ** 2 for x in xs)
        slope = sum((x - xmean) * (y - ymean) for x, y in zip(xs, ys)) / denominator
        intercept = ymean - slope * xmean
        residuals = [y - (intercept + slope * x) for x, y in zip(xs, ys)]
        scale = max(max(abs(value) for value in ys), 1e-12)
        slopes.append(slope)
        relative_residuals.append(max(abs(value) for value in residuals) / scale)
    slope_ci = _ci95(slopes)
    slope_excludes_zero = bool(
        slope_ci["low_s"] is not None and slope_ci["high_s"] is not None
        and (slope_ci["low_s"] > 0 or slope_ci["high_s"] < 0)
    )
    residual_gate = max(relative_residuals, default=math.inf) <= 0.10
    k_gates = all(_measurement_passed(measurements[k], minimum_pairs, pilot) for k in (1, 2, 4, 8))
    passed = bool(not pilot and common_n >= minimum_pairs and slope_excludes_zero and residual_gate and k_gates)
    result = {
        "status": "passed" if passed else "failed",
        "model": "block-level D(K)=alpha+beta*K",
        "k_measurements": {str(k): measurements[k] for k in (1, 2, 4, 8)},
        "block_slope_confidence_interval_95": slope_ci,
        "block_slope_count": common_n,
        "maximum_block_relative_residual": max(relative_residuals, default=None),
        "relative_residual_threshold": 0.10,
        "slope_ci_excludes_zero": slope_excludes_zero,
        "all_k_measurement_gates_passed": k_gates,
        "k1_cost_equivalence_claimed": False,
    }
    if passed:
        result["beta_hot_repetition_s"] = slope_ci["mean_s"]
    return result


def _path_b(
    runner: BlockRunner,
    replay_input: ReplayInput,
    certification: Mapping[str, Any],
    scenario: str,
    *,
    min_pairs: int,
    max_pairs: int,
    relative_half_width: float,
    practical_effect_s: float,
    noise_bound_s: float,
    pilot: bool,
) -> dict[str, Any]:
    occupancy = certification["occupancy_gate"]
    control = _common_arm(scenario)
    all_real = {**control, "pending_policy": "all-real"}
    total = _paired_measurement(
        runner, replay_input, all_real, control,
        min_pairs=min_pairs, max_pairs=max_pairs,
        relative_half_width=relative_half_width,
        practical_effect_s=practical_effect_s, noise_bound_s=noise_bound_s,
        label=f"{replay_input.controller_id}:{scenario}:path-b-total",
        effect_definition="whole replay all-real pending CPU minus all-oracle control CPU",
    )
    marginals: dict[str, Any] = {}
    for caller in CALLERS:
        marginals[caller] = _paired_measurement(
            runner, replay_input,
            {**control, "pending_policy": "mixed", "real_callers": (caller,)}, control,
            min_pairs=min_pairs, max_pairs=max_pairs,
            relative_half_width=relative_half_width,
            practical_effect_s=practical_effect_s, noise_bound_s=noise_bound_s,
            label=f"{replay_input.controller_id}:{scenario}:path-b:{caller}",
            effect_definition=f"whole replay {caller} real CPU minus all-oracle control CPU",
        )
    negative = _negative_control(
        runner, replay_input, control, pairs=min_pairs,
        practical_effect_s=practical_effect_s, noise_bound_s=noise_bound_s,
        label=f"{replay_input.controller_id}:{scenario}:path-b-negative",
    )
    k_measurements: dict[int, Any] = {}
    for k in (1, 2, 4, 8):
        k_measurements[k] = _paired_measurement(
            runner, replay_input,
            {**all_real, "amplification_k": k}, {**control, "amplification_k": k},
            min_pairs=min_pairs, max_pairs=max_pairs,
            relative_half_width=relative_half_width,
            practical_effect_s=practical_effect_s, noise_bound_s=noise_bound_s,
            label=f"{replay_input.controller_id}:{scenario}:path-b-k{k}",
            effect_definition=f"whole replay amplified K={k} real CPU minus oracle control CPU",
        )
    linearity = _regression_linearity(k_measurements, minimum_pairs=min_pairs, pilot=pilot)
    total_value = float(total["marginal_replay_cpu_saving_vs_o1_control_s"])
    marginal_sum = sum(float(value["marginal_replay_cpu_saving_vs_o1_control_s"]) for value in marginals.values())
    negative_ok = negative["negative_control_ci_gate"] == "passed" and negative["negative_control_order_gate"] == "passed"
    adoption_gate_results = {
        "occupancy_exact_match": occupancy["adopt_path_b"] is True,
        "total_measurement": _measurement_passed(total, min_pairs, False),
        "all_caller_measurements": all(
            _measurement_passed(value, min_pairs, False)
            for value in marginals.values()
        ),
        "negative_control": negative_ok,
        "non_pilot": not pilot,
    }
    adopted = all(adoption_gate_results.values())
    real_trace = certification["real"]
    return {
        "adopted": adopted,
        "performance_values_emitted": True,
        "adoption_gate_results": adoption_gate_results,
        "hot_replay": True,
        "scenario": scenario,
        "total_all_real_minus_all_oracle": total,
        "by_caller_conditional_marginals": marginals,
        "interaction_residual_s": total_value - marginal_sum,
        "caller_values_are_additive_breakdown": False,
        "negative_control": negative,
        "amplification_linearity": linearity,
        "caller_counts": real_trace["pending_calls"],
        "scope_visits": real_trace["pending_scope_visits"],
        "item_visits": real_trace["pending_item_visits"],
        "tests_finished": real_trace["tests_finished"],
        "worker_workload_distribution": real_trace["worker_workload_distribution"],
        "occupancy_gate": occupancy,
        "actual_controller_cpu_seconds_claimed": False,
    }


def _pilot_input(value: ReplayInput) -> ReplayInput:
    collection = value.collection[:PILOT_ITEM_LIMIT]
    return ReplayInput(
        population_id=value.population_id,
        controller_id=value.controller_id,
        collection=collection,
        duration_by_nodeid={nodeid: value.duration_by_nodeid[nodeid] for nodeid in collection},
        group_by_nodeid={nodeid: value.group_by_nodeid[nodeid] for nodeid in collection},
        worker_count=min(value.worker_count, 8),
        expected_worker_occupancy=None,
        expected_group_to_workers=None,
    )


def _controller_inputs(manifest_path: Path, manifest: Mapping[str, Any], pilot: bool) -> list[ReplayInput]:
    controller_ids = [controller["id"] for population in manifest["populations"] for controller in population["controllers"]]
    if len(controller_ids) != 4 or len(controller_ids) != len(set(controller_ids)):
        raise MeasurementError("input manifest does not contain four unique controllers")
    values = [load_replay_input(manifest_path, controller_id) for controller_id in controller_ids]
    return [_pilot_input(value) for value in values] if pilot else values


def _certify_all(
    inputs: Sequence[ReplayInput], pilot: bool
) -> tuple[dict[tuple[str, str], dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    started = time.perf_counter()
    certifications: dict[tuple[str, str], dict[str, Any]] = {}
    trace_records: list[dict[str, Any]] = []
    summary = []
    for replay_input in inputs:
        for scenario in SCENARIOS:
            certified = certify(replay_input, scenario)
            occupancy = certified["occupancy_gate"]
            certifications[(replay_input.controller_id, scenario)] = certified
            real = certified["real"]
            for record in real["events"] + real["pending_trace"]:
                if record.get("population_id") != replay_input.population_id:
                    raise MeasurementError("certification trace population id mismatch")
                trace_records.append({"population_id": replay_input.population_id, "controller_id": replay_input.controller_id, "scenario": scenario, **record})
            summary.append({
                "population_id": replay_input.population_id,
                "controller_id": replay_input.controller_id,
                "scenario": scenario,
                "status": certified["status"],
                "all_pending_values_equal": certified["all_pending_values_equal"],
                "behavior_transcript_equal": certified["behavior_transcript_equal"],
                "all_worker_clone_control": certified["all_worker_clone_control"],
                "pending_call_count": certified["pending_call_count"],
                "occupancy_gate": occupancy,
            })
    occupancy_status_counts = Counter(
        entry["occupancy_gate"]["status"] for entry in summary
    )
    return certifications, trace_records, {
        "status": "correctness-passed-before-performance",
        "all_controller_scenario_count": len(summary),
        "observed_wall_s": time.perf_counter() - started,
        "occupancy_adoption_summary": {
            "passed_count": occupancy_status_counts["passed"],
            "failed_count": occupancy_status_counts["failed"],
            "not_applicable_count": occupancy_status_counts["not-applicable"],
            "all_applicable_passed": occupancy_status_counts["failed"] == 0,
        },
        "results": summary,
    }


def _parse_proc_stat(stat: str) -> dict[str, Any]:
    """Parse the stable fields of one Linux /proc/<pid>/stat record."""
    comm_start = stat.find("(")
    comm_end = stat.rfind(")")
    if comm_start <= 0 or comm_end <= comm_start:
        raise ValueError("stat comm delimiters are missing or reversed")
    pid_text = stat[:comm_start].strip()
    if not pid_text.isascii() or not pid_text.isdecimal():
        raise ValueError("stat pid is not an ASCII decimal integer")
    fields_after_comm = stat[comm_end + 1:].split()
    if len(fields_after_comm) < 13:
        raise ValueError("stat record ends before stime")
    if len(fields_after_comm[0]) != 1 or not fields_after_comm[0].isalpha():
        raise ValueError("stat process state is not one letter")
    try:
        pid = int(pid_text)
        ppid = int(fields_after_comm[1])
        utime_ticks = int(fields_after_comm[11])
        stime_ticks = int(fields_after_comm[12])
    except ValueError as exc:
        raise ValueError("stat numeric field is malformed") from exc
    if pid <= 0 or ppid < 0 or utime_ticks < 0 or stime_ticks < 0:
        raise ValueError("stat numeric field is outside its valid range")
    return {
        "pid": pid,
        "comm": stat[comm_start + 1:comm_end],
        "ppid": ppid,
        "utime_ticks": utime_ticks,
        "stime_ticks": stime_ticks,
    }


def _parse_proc_real_uid(status: str) -> int:
    uid_lines = [line for line in status.splitlines() if line.startswith("Uid:")]
    if len(uid_lines) != 1:
        raise ValueError("status does not contain exactly one Uid record")
    label, separator, payload = uid_lines[0].partition(":")
    fields = payload.split()
    if label != "Uid" or separator != ":" or len(fields) != 4:
        raise ValueError("status Uid record has the wrong shape")
    if any(not field.isascii() or not field.isdecimal() for field in fields):
        raise ValueError("status Uid record contains a non-decimal value")
    return int(fields[0])


def _append_process_snapshot_record(
    processes: list[dict[str, Any]],
    *,
    status: str,
    stat: str,
    uid: int,
    expected_pid: int,
) -> bool:
    """Append an owned process, returning True when a malformed record was skipped."""
    try:
        real_uid = _parse_proc_real_uid(status)
        if real_uid != uid:
            return False
        process = _parse_proc_stat(stat)
        if process["pid"] != expected_pid:
            raise ValueError("stat pid differs from its proc directory")
    except ValueError:
        return True
    processes.append(process)
    return False


def _process_snapshot() -> dict[str, Any]:
    uid = os.getuid()
    processes: list[dict[str, Any]] = []
    skipped_pids = 0
    try:
        entries = list(Path("/proc").iterdir())
    except OSError:
        return {"status": "unavailable", "processes": [], "skipped_pids": 0}
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            status = (entry / "status").read_text(encoding="ascii")
            stat = (entry / "stat").read_text(encoding="ascii")
        except (OSError, UnicodeError):
            skipped_pids += 1
            continue
        skipped_pids += int(_append_process_snapshot_record(
            processes,
            status=status,
            stat=stat,
            uid=uid,
            expected_pid=int(entry.name),
        ))
    return {
        "status": "sampled",
        "processes": sorted(processes, key=lambda item: item["pid"]),
        "skipped_pids": skipped_pids,
    }


def _proc_stat_parser_regression() -> dict[str, Any]:
    zero_fields = " ".join(["0"] * 9)
    valid_cases = [
        (
            f"101 (worker) R 7 {zero_fields} 11 13\n",
            {"pid": 101, "comm": "worker", "ppid": 7, "utime_ticks": 11, "stime_ticks": 13},
        ),
        (
            f"202 (tmux: (server) helper) S 1 {zero_fields} 120 34\n",
            {
                "pid": 202,
                "comm": "tmux: (server) helper",
                "ppid": 1,
                "utime_ticks": 120,
                "stime_ticks": 34,
            },
        ),
    ]
    for stat, expected in valid_cases:
        if _parse_proc_stat(stat) != expected:
            raise MeasurementError("synthetic proc stat valid-case regression failed")
    invalid_cases = [
        "303 missing-delimiters S 1 2 3",
        "bad (worker) S 1 2 3 4 5 6 7 8 9 10 11 12",
        "304 (worker) S invalid 0 0 0 0 0 0 0 0 0 1 2",
        "305 (worker) S 1 2",
    ]
    for stat in invalid_cases:
        try:
            _parse_proc_stat(stat)
        except ValueError:
            continue
        raise MeasurementError("synthetic proc stat invalid-case regression failed")
    processes: list[dict[str, Any]] = []
    skipped_pids = 0
    status = f"Name:\tfixture\nUid:\t{os.getuid()} {os.getuid()} {os.getuid()} {os.getuid()}\n"
    skipped_pids += int(_append_process_snapshot_record(
        processes,
        status=status,
        stat=valid_cases[1][0],
        uid=os.getuid(),
        expected_pid=202,
    ))
    skipped_pids += int(_append_process_snapshot_record(
        processes,
        status=status,
        stat=invalid_cases[2],
        uid=os.getuid(),
        expected_pid=304,
    ))
    if processes != [valid_cases[1][1]] or skipped_pids != 1:
        raise MeasurementError("malformed proc stat snapshot skip regression failed")
    return {
        "status": "passed",
        "valid_cases": len(valid_cases),
        "invalid_cases": len(invalid_cases),
        "snapshot_processes": len(processes),
        "skipped_pids": skipped_pids,
    }


def _timer_probe(read_count: int = 10_000) -> dict[str, Any]:
    readings = [time.process_time_ns() for _ in range(read_count)]
    deltas = [right - left for left, right in zip(readings, readings[1:])]
    positive = sorted(delta for delta in deltas if delta > 0)
    ordered = sorted(deltas)
    return {
        "read_count": read_count,
        "zero_rate": sum(delta == 0 for delta in deltas) / len(deltas),
        "minimum_positive_delta_ns": min(positive) if positive else None,
        "median_delta_ns": statistics.median(deltas),
        "p99_delta_ns": ordered[max(0, math.ceil(len(deltas) * 0.99) - 1)],
        "clock_info": vars(time.get_clock_info("process_time")),
    }


def _pythonpath_observation() -> dict[str, str | None]:
    if "PYTHONPATH" not in os.environ:
        return {"state": "absent", "value": None}
    value = os.environ["PYTHONPATH"]
    return {"state": "empty" if value == "" else "set", "value": value}


def _environment(pilot: bool) -> dict[str, Any]:
    try:
        import pytest
        import xdist
    except Exception as exc:
        raise MeasurementError(f"cannot resolve pytest/xdist environment: {exc}") from exc
    return {
        "hostname": platform.node(),
        "pbs_jobid": os.environ.get("PBS_JOBID") if not pilot else "pilot-local",
        "python": sys.version,
        "python_executable": sys.executable,
        "pythonpath": _pythonpath_observation(),
        "pytest": pytest.__version__,
        "xdist_version": xdist.__version__,
        "xdist_path": str(Path(xdist.__file__).resolve()),
        "kernel": platform.release(),
        "machine": platform.machine(),
        "affinity_cpus": sorted(os.sched_getaffinity(0)),
        "thread_count": _thread_count(),
    }


def _require_full_environment(environment: Mapping[str, Any]) -> None:
    hostname = environment.get("hostname")
    if type(hostname) is not str or not hostname.split(".", 1)[0].startswith("bnode"):
        raise MeasurementError("full measurement is allowed only on a Pegasus compute node")
    if not environment.get("pbs_jobid"):
        raise MeasurementError("full measurement requires PBS_JOBID")


def _source_hashes() -> dict[str, str]:
    here = Path(__file__).resolve().parent
    return {name: _sha256_path(here / name) for name in SOURCE_FILES}


def _planned_sample_count(controller_count: int, min_pairs: int, max_pairs: int, diagnostic_pairs: int) -> int:
    path_a_blocks = controller_count * (max_pairs + min_pairs + diagnostic_pairs)
    path_b_blocks = controller_count * len(SCENARIOS) * (10 * max_pairs + min_pairs)
    return 4 * (path_a_blocks + path_b_blocks)


def _calibration(runner: BlockRunner, inputs: Sequence[ReplayInput]) -> dict[str, Any]:
    started = time.perf_counter()
    blocks = []
    for replay_input in inputs:
        control = _common_arm("protocol-only")
        blocks.extend(runner.run_blocks(
            replay_input, {**control, "index_mode": "real"}, control,
            f"{replay_input.controller_id}:calibration-a", [0],
        ))
        blocks.extend(runner.run_blocks(
            replay_input,
            {**_common_arm("pass-event"), "pending_policy": "all-real", "amplification_k": 8},
            {**_common_arm("pass-event"), "amplification_k": 8},
            f"{replay_input.controller_id}:calibration-b-k8", [0],
        ))
    sample_walls = [entry["sample"]["wall_s"] for block in blocks for entry in block["samples"]]
    block_walls = [float(block["block_wall_s"]) for block in blocks]
    return {
        "sample_unit": "one timed replay inside a fresh paired-block process",
        "measured_sample_count": len(sample_walls),
        "measured_sample_cost_s": max(sample_walls),
        "median_sample_cost_s": statistics.median(sample_walls),
        "maximum_paired_block_wall_s": max(block_walls),
        "observed_wall_s": time.perf_counter() - started,
    }


def _aggregate_ci(values: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    cis = [value["confidence_interval_95"] for value in values]
    return {
        "mean_s": sum(float(ci["mean_s"]) for ci in cis),
        "low_s": sum(float(ci["low_s"]) for ci in cis),
        "high_s": sum(float(ci["high_s"]) for ci in cis),
        "method": "conservative sum of shard CI endpoints",
    }


def _aggregate_k2(results: Sequence[Mapping[str, Any]], pilot: bool) -> dict[str, Any]:
    shards = [result for result in results if result["population_id"] == "canonical-acceptance-15103-k2"]
    if len(shards) != 2:
        raise MeasurementError("K=2 aggregate requires exactly two controller results")
    path_a_values = [result["path_a"] for result in shards]
    path_a_adopted = bool(not pilot and all(value["adopted"] for value in path_a_values))
    path_a: dict[str, Any] = {
        "status": "adopted" if path_a_adopted else "blocked-not-all-shards-adopted",
        "all_shards_adopted": path_a_adopted,
    }
    if path_a_adopted:
        leaves = [value["primary_first_worker_identity_alias"] for value in path_a_values]
        estimates = [float(value["marginal_replay_cpu_saving_vs_o1_control_s"]) for value in leaves]
        path_a.update({
            "shard_marginal_replay_cpu_saving_vs_o1_control_s": estimates,
            "sum_shard_marginal_replay_cpu_saving_vs_o1_control_s": sum(estimates),
            "max_shard_marginal_replay_cpu_saving_vs_o1_control_s": max(estimates),
            "aggregate_confidence_interval_95": _aggregate_ci(leaves),
        })
    path_b: dict[str, Any] = {}
    for scenario in SCENARIOS:
        entries = [result["path_b"][scenario] for result in shards]
        adopted = bool(not pilot and all(entry["adopted"] for entry in entries))
        aggregate: dict[str, Any] = {
            "status": "adopted" if adopted else "blocked-not-all-shards-adopted",
            "all_shards_adopted": adopted,
        }
        if adopted:
            leaves = [entry["total_all_real_minus_all_oracle"] for entry in entries]
            estimates = [float(value["marginal_replay_cpu_saving_vs_o1_control_s"]) for value in leaves]
            aggregate.update({
                "shard_marginal_replay_cpu_saving_vs_o1_control_s": estimates,
                "sum_shard_marginal_replay_cpu_saving_vs_o1_control_s": sum(estimates),
                "max_shard_marginal_replay_cpu_saving_vs_o1_control_s": max(estimates),
                "aggregate_confidence_interval_95": _aggregate_ci(leaves),
            })
        path_b[scenario] = aggregate
    return {
        "population_id": "canonical-acceptance-15103-k2",
        "effective_worker_count_per_shard": 48,
        "path_a": path_a,
        "path_b": path_b,
    }


def _decision_rule(k2: Mapping[str, Any]) -> dict[str, Any]:
    path_a = k2["path_a"]
    selected = "inconclusive"
    if path_a["status"] == "adopted":
        interval = path_a["aggregate_confidence_interval_95"]
        if interval["high_s"] < PATH_A_DECISION_THRESHOLD_S:
            selected = "investigate-model-error-and-other-controller-paths"
        elif interval["low_s"] > PATH_A_DECISION_THRESHOLD_S:
            selected = "prototype-o1-index-and-run-causal-k2-wall-ab"
    return {
        "metric": "K=2 sum shard path-A marginal replay CPU saving",
        "threshold_s": PATH_A_DECISION_THRESHOLD_S,
        "rule": "CI high below threshold selects model/path investigation; CI low above threshold selects O(1) causal AB; overlap or non-adoption is inconclusive",
        "selected_next_experiment": selected,
        "wall_improvement_claimed": False,
        "d747_claim_closed": False,
    }


def _top_level_status(
    *, pilot: bool, isolation_status: Any, authoritative: Any
) -> str:
    if pilot:
        return "pilot-valid-not-adoptable"
    if isolation_status == "isolation-unverified" and authoritative is False:
        return "reference-only-isolation-unverified"
    raise MeasurementError("no top-level status is defined for this evidence envelope")


def resolve_attempt_dir(attempt_id: str) -> Path:
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}", attempt_id) is None:
        raise MeasurementError(f"invalid attempt id: {attempt_id!r}")
    base = (_repo_root() / EXPECTED_OUTPUT_RELATIVE).resolve()
    path = (base / attempt_id).resolve()
    if path.parent != base:
        raise MeasurementError("attempt directory escaped the owned runtime root")
    return path


def _attempt_dir(attempt_id: str) -> Path:
    path = resolve_attempt_dir(attempt_id)
    path.mkdir(parents=True, exist_ok=True)
    for filename in ("raw-result.json", "success-receipt.json"):
        if (path / filename).exists():
            raise MeasurementError(f"attempt already contains terminal artifact: {path / filename}")
    return path


def measure_all(
    manifest_path: Path,
    attempt_id: str,
    *,
    pilot: bool,
    min_pairs: int,
    max_pairs: int,
    relative_half_width: float,
    practical_effect_s: float,
    noise_bound_s: float,
    diagnostic_pairs: int,
    deadline_seconds: float,
    max_workers: int,
) -> dict[str, Any]:
    started = time.perf_counter()
    manifest_path = manifest_path.resolve()
    manifest = load_manifest(manifest_path)
    xdist_verification = verify_xdist_sources(manifest)
    environment = _environment(pilot)
    if not pilot:
        _require_full_environment(environment)
        if min_pairs < MIN_PAIRS_DEFAULT:
            raise MeasurementError("full measurement cannot reduce the 30-pair minimum")
    attempt_dir = _attempt_dir(attempt_id)
    deadline_at = time.monotonic() + deadline_seconds
    runner = BlockRunner(attempt_dir, deadline_at, max_workers=max_workers, pilot=pilot)
    replay_inputs = _controller_inputs(manifest_path, manifest, pilot)
    _proc_stat_parser_regression()
    isolation_pre = _process_snapshot()
    timer = _timer_probe()
    certifications, trace_records, certification_summary = _certify_all(replay_inputs, pilot)
    calibration = _calibration(runner, replay_inputs)
    planned_samples = _planned_sample_count(len(replay_inputs), min_pairs, max_pairs, diagnostic_pairs)
    effective_parallelism = min(runner.max_workers, min_pairs)
    estimated_wall_s = (
        calibration["measured_sample_cost_s"] * planned_samples / effective_parallelism * 1.50
        + certification_summary["observed_wall_s"] * 1.50
        + calibration["observed_wall_s"]
    )
    if not pilot and estimated_wall_s >= FULL_WALL_LIMIT_SECONDS:
        raise MeasurementError(f"measured cost model exceeds three hours: {estimated_wall_s:.3f}s")
    controller_results = []
    for replay_input in replay_inputs:
        path_a = _path_a(
            runner, replay_input, min_pairs=min_pairs, max_pairs=max_pairs,
            relative_half_width=relative_half_width, practical_effect_s=practical_effect_s,
            noise_bound_s=noise_bound_s, diagnostic_pairs=diagnostic_pairs, pilot=pilot,
        )
        path_b = {
            scenario: _path_b(
                runner, replay_input, certifications[(replay_input.controller_id, scenario)], scenario,
                min_pairs=min_pairs, max_pairs=max_pairs,
                relative_half_width=relative_half_width, practical_effect_s=practical_effect_s,
                noise_bound_s=noise_bound_s, pilot=pilot,
            )
            for scenario in SCENARIOS
        }
        controller_results.append({
            "population_id": replay_input.population_id,
            "controller_id": replay_input.controller_id,
            "n": len(replay_input.collection),
            "worker_count": replay_input.worker_count,
            "pilot": pilot,
            "hot_replay": True,
            "isolation_status": "isolation-unverified",
            "authoritative": False,
            "path_a": path_a,
            "path_b": path_b,
        })
    isolation_post = _process_snapshot()
    trace_path = attempt_dir / "certification-trace.jsonl"
    trace_payload = b"".join(_canonical_json_bytes(record) for record in trace_records)
    _write_atomic(trace_path, trace_payload)
    k2_aggregate = _aggregate_k2(controller_results, pilot)
    source_hashes = _source_hashes()
    observed_wall_s = time.perf_counter() - started
    actual_samples = sum(_count_controller_samples(result) for result in controller_results)
    isolation_status = "isolation-unverified"
    authoritative = False
    raw = {
        "schema_version": RESULT_SCHEMA,
        "status": _top_level_status(
            pilot=pilot,
            isolation_status=isolation_status,
            authoritative=authoritative,
        ),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "pilot": pilot,
        "performance_values_emitted": True,
        "pilot_notice": "Pilot values are structural health-check data and must not be used as performance evidence." if pilot else None,
        "attempt": {
            "attempt_id": attempt_id,
            "pbs_job_id": environment["pbs_jobid"],
            "run_directory": str(attempt_dir),
            "success_receipt_path": str(attempt_dir / "success-receipt.json"),
        },
        "estimated_wall_s": estimated_wall_s,
        "observed_wall_s": observed_wall_s,
        "cost_model": {
            **calibration,
            "planned_maximum_sample_count": planned_samples,
            "observed_measurement_sample_count": actual_samples,
            "effective_parallelism": effective_parallelism,
            "safety_factor": 1.50,
            "estimate_formula": "measured maximum replay sample wall * planned sample count / effective parallelism * safety factor + certification and calibration",
            "three_hour_limit_s": FULL_WALL_LIMIT_SECONDS,
        },
        "certification": certification_summary,
        "population_results": controller_results,
        "k2_aggregate": k2_aggregate,
        "isolation_status": isolation_status,
        "authoritative": authoritative,
        "hot_replay": True,
        "inputs": {
            "manifest_path": str(manifest_path),
            "manifest_sha256": _sha256_path(manifest_path),
            "manifest_schema": manifest["schema_version"],
            "population_ids": manifest["population_ids"],
            "xdist_import_verification": xdist_verification,
            "source_sha256": source_hashes,
        },
        "timing": {
            "timer_probe": timer,
            "minimum_pairs": min_pairs,
            "maximum_pairs": max_pairs,
            "relative_half_width_threshold": relative_half_width,
            "minimum_practical_effect_s": practical_effect_s,
            "absolute_noise_bound_s": noise_bound_s,
            "fresh_process_unit": "paired-block",
            "controller_thread_single_core_pinned": True,
            "worker_collection_decode_clone_and_control_prepared_before_clock": True,
            "transcript_generated_only_by_certification": True,
        },
        "environment": environment,
        "isolation_evidence": {
            "pre": isolation_pre,
            "post": isolation_post,
            "sampling": "whole-run pre/post snapshots only",
            "exclusive_placement_proven": False,
            "reason": "scheduler/cgroup exclusive placement is not established by this harness",
        },
        "artifacts": {
            "certification_trace_path": str(trace_path),
            "certification_trace_sha256": _sha256_bytes(trace_payload),
            "certification_trace_records": len(trace_records),
            "checkpoint_root": str(attempt_dir / "checkpoints"),
        },
        "diagnostics": {
            "single_run_hybrid_residual_s": 61.3,
            "residual_role": "historical diagnostic reference only; not an occupancy denominator",
            "cold_lookup_claimed": False,
            "pre_touch_memory_pressure_diagnostic_only": True,
        },
        "decision_rule": _decision_rule(k2_aggregate),
        "limitations": [
            "whole-replay differences are marginal savings versus controls, not gross function CPU",
            "compressed replay is hot-cache and does not recover the historical DSession event trace",
            "protocol-only and pass-event range the unpreserved event stream and workerfinish tie order",
            "isolation is unverified without scheduler or cgroup exclusivity evidence",
            "K=1 groupmap order and K=2 historical reorder provenance are not closed",
            "the 61.3 second single-run hybrid residual is not a physical cost bucket",
        ],
    }
    _finite_tree(raw)
    validate_raw_result_schema(raw)
    validate_raw_result(raw, manifest, trace_path=trace_path)
    raw_path = attempt_dir / "raw-result.json"
    raw_payload = _canonical_json_bytes(raw)
    _write_atomic(raw_path, raw_payload)
    _write_atomic(attempt_dir / "isolation-pre.json", _canonical_json_bytes(isolation_pre))
    _write_atomic(attempt_dir / "isolation-post.json", _canonical_json_bytes(isolation_post))
    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "status": "success",
        "attempt_id": attempt_id,
        "pbs_job_id": environment["pbs_jobid"],
        "pilot": pilot,
        "raw_result_path": str(raw_path),
        "raw_result_sha256": _sha256_bytes(raw_payload),
        "manifest_sha256": raw["inputs"]["manifest_sha256"],
        "source_sha256": source_hashes,
    }
    _write_atomic(attempt_dir / "success-receipt.json", _canonical_json_bytes(receipt))
    return raw


def _count_measurement_samples(value: Mapping[str, Any]) -> int:
    return int(value["sample_count"])


def _count_controller_samples(result: Mapping[str, Any]) -> int:
    path_a = result["path_a"]
    count = _count_measurement_samples(path_a["primary_first_worker_identity_alias"])
    count += _count_measurement_samples(path_a["negative_control"])
    count += _count_measurement_samples(path_a["pre_touch_memory_pressure_diagnostic"]["measurement"])
    for scenario in SCENARIOS:
        path_b = result["path_b"][scenario]
        count += _count_measurement_samples(path_b["total_all_real_minus_all_oracle"])
        count += sum(_count_measurement_samples(value) for value in path_b["by_caller_conditional_marginals"].values())
        count += _count_measurement_samples(path_b["negative_control"])
        count += sum(_count_measurement_samples(value) for value in path_b["amplification_linearity"]["k_measurements"].values())
    return count


def _validate_ci(value: Any, path: str) -> None:
    obj = _exact_keys(value, {
        "n", "mean_s", "standard_deviation_s", "half_width_s",
        "low_s", "high_s", "relative_half_width",
    }, path)
    if type(obj["n"]) is not int or obj["n"] < 1:
        raise MeasurementError(f"invalid CI count at {path}")


def _validate_sample(value: Any, population_id: str, controller_id: str, path: str) -> None:
    obj = _exact_keys(value, {
        "schema_version", "population_id", "controller_id", "pilot", "pid",
        "scenario", "index_mode", "pending_policy", "real_callers", "identity_mode",
        "amplification_k", "pre_touch_memory_pressure", "process_cpu_s", "wall_s",
        "list_index_slot_probes", "pending_calls", "gc_events", "thread_count_before",
        "thread_count_after", "affinity", "clock",
    }, path)
    if obj["schema_version"] != SAMPLE_SCHEMA or obj["population_id"] != population_id or obj["controller_id"] != controller_id:
        raise MeasurementError(f"sample population/controller/schema mismatch at {path}")
    _exact_keys(obj["affinity"], {"before", "selected", "after"}, path + ".affinity")
    clock = _exact_keys(obj["clock"], {"process_time", "perf_counter"}, path + ".clock")
    for name in ("process_time", "perf_counter"):
        _exact_keys(clock[name], {"implementation", "monotonic", "adjustable", "resolution"}, f"{path}.clock.{name}")


def _validate_block(value: Any, population_id: str, controller_id: str) -> None:
    obj = _exact_keys(value, {
        "population_id", "controller_id", "block", "order",
        "paired_difference_s", "block_wall_s", "samples",
    }, "block")
    if obj["population_id"] != population_id or obj["controller_id"] != controller_id:
        raise MeasurementError("paired block population/controller mismatch")
    if obj["order"] not in {"ABBA", "BAAB"} or type(obj["samples"]) is not list or len(obj["samples"]) != 4:
        raise MeasurementError("paired block order or sample count mismatch")
    for index, entry in enumerate(obj["samples"]):
        item = _exact_keys(entry, {"arm", "sample"}, f"block.samples[{index}]")
        if item["arm"] != obj["order"][index]:
            raise MeasurementError("paired block arm order mismatch")
        _validate_sample(item["sample"], population_id, controller_id, f"block.samples[{index}].sample")


def _validate_measurement(
    value: Any, population_id: str, controller_id: str, path: str, *, negative: bool = False
) -> None:
    keys = {
        "label", "status", "effect_definition", "marginal_replay_cpu_saving_vs_o1_control_s",
        "confidence_interval_95", "minimum_practical_effect_s", "relative_half_width_threshold",
        "independent_fresh_process_pairs", "sample_count", "abba_baab_balanced",
        "order_effect", "blocks",
    }
    if negative:
        keys |= {"absolute_noise_bound_s", "negative_control_ci_gate", "negative_control_order_gate"}
    obj = _exact_keys(value, keys, path)
    _validate_ci(obj["confidence_interval_95"], path + ".confidence_interval_95")
    order = _exact_keys(obj["order_effect"], {
        "definition", "confidence_interval_95", "absolute_noise_bound_s", "balanced", "gate",
    }, path + ".order_effect")
    if order["confidence_interval_95"] is not None:
        _validate_ci(order["confidence_interval_95"], path + ".order_effect.confidence_interval_95")
    if type(obj["blocks"]) is not list or obj["sample_count"] != len(obj["blocks"]) * 4:
        raise MeasurementError(f"measurement block/sample count mismatch at {path}")
    for block in obj["blocks"]:
        _validate_block(block, population_id, controller_id)


def _controller_map(manifest: Mapping[str, Any]) -> dict[str, tuple[str, int]]:
    return {
        controller["id"]: (population["id"], int(controller["selected_n"]))
        for population in manifest["populations"] for controller in population["controllers"]
    }


def _validate_counter(value: Any, allowed: set[str], path: str) -> None:
    if type(value) is not dict or not set(value) <= allowed:
        raise MeasurementError(f"counter key set mismatch at {path}")
    if any(type(item) is not int or item < 0 for item in value.values()):
        raise MeasurementError(f"counter value mismatch at {path}")


def _validate_distribution(value: Any, path: str) -> None:
    _exact_keys(value, {"min", "median", "max"}, path)


def _validate_occupancy(value: Any, path: str) -> None:
    if type(value) is not dict:
        raise MeasurementError(f"occupancy gate is not an object at {path}")
    if value.get("status") == "not-applicable":
        _exact_keys(value, {"status", "adopt_path_b"}, path)
        return
    obj = _exact_keys(value, {
        "status", "adopt_path_b", "sorted_item_count_vector_match",
        "expected_sorted_item_count_vector", "observed_sorted_item_count_vector",
        "missing_item_counts", "unexpected_item_counts", "expected_item_distribution",
        "observed_item_distribution", "group_to_workers_match",
        "expected_group_to_workers", "observed_group_to_workers",
    }, path)
    for name in (
        "expected_sorted_item_count_vector", "observed_sorted_item_count_vector",
        "missing_item_counts", "unexpected_item_counts",
    ):
        vector = obj[name]
        if (
            type(vector) is not list
            or any(type(item) is not int or item < 0 for item in vector)
            or vector != sorted(vector)
        ):
            raise MeasurementError(f"occupancy item-count vector mismatch at {path}.{name}")
    expected_items = obj["expected_sorted_item_count_vector"]
    observed_items = obj["observed_sorted_item_count_vector"]
    vector_match = expected_items == observed_items
    missing = sorted((Counter(expected_items) - Counter(observed_items)).elements())
    unexpected = sorted((Counter(observed_items) - Counter(expected_items)).elements())
    if obj["missing_item_counts"] != missing or obj["unexpected_item_counts"] != unexpected:
        raise MeasurementError(f"occupancy multiset difference mismatch at {path}")
    _validate_distribution(obj["expected_item_distribution"], path + ".expected_item_distribution")
    _validate_distribution(obj["observed_item_distribution"], path + ".observed_item_distribution")
    if (
        obj["expected_item_distribution"] != _distribution(expected_items)
        or obj["observed_item_distribution"] != _distribution(observed_items)
    ):
        raise MeasurementError(f"occupancy item distribution mismatch at {path}")
    for name in ("expected_group_to_workers", "observed_group_to_workers"):
        groups = obj[name]
        if type(groups) is not dict or any(
            type(group) is not str
            or type(workers) is not list
            or any(type(worker) is not str for worker in workers)
            for group, workers in groups.items()
        ):
            raise MeasurementError(f"group-to-workers shape mismatch at {path}.{name}")
    group_match = obj["expected_group_to_workers"] == obj["observed_group_to_workers"]
    adopt_path_b = vector_match and group_match
    if (
        obj["sorted_item_count_vector_match"] is not vector_match
        or obj["group_to_workers_match"] is not group_match
        or obj["adopt_path_b"] is not adopt_path_b
        or obj["status"] != ("passed" if adopt_path_b else "failed")
    ):
        raise MeasurementError(f"occupancy exact-match decision mismatch at {path}")


def _validate_tests_finished(value: Any, path: str) -> None:
    _exact_keys(value, {
        "property_evaluations", "collection_early_returns", "workqueue_early_returns",
        "workers_scanned_by_event", "pending_short_circuits", "full_worker_scans",
    }, path)


def _validate_process_snapshot(value: Any, path: str) -> None:
    obj = _exact_keys(value, {"status", "processes", "skipped_pids"}, path)
    if type(obj["processes"]) is not list:
        raise MeasurementError(f"process snapshot list mismatch at {path}")
    if type(obj["skipped_pids"]) is not int or obj["skipped_pids"] < 0:
        raise MeasurementError(f"process snapshot skipped PID count mismatch at {path}")
    for process in obj["processes"]:
        _exact_keys(
            process,
            {"pid", "comm", "ppid", "utime_ticks", "stime_ticks"},
            path + ".processes[]",
        )


def validate_raw_result(
    raw: Mapping[str, Any], manifest: Mapping[str, Any], *, trace_path: Path | None = None
) -> None:
    _finite_tree(raw)
    top = _exact_keys(raw, {
        "schema_version", "status", "generated_at_utc", "pilot", "performance_values_emitted",
        "pilot_notice", "attempt", "estimated_wall_s", "observed_wall_s", "cost_model",
        "certification", "population_results", "k2_aggregate", "isolation_status", "authoritative",
        "hot_replay", "inputs", "timing", "environment", "isolation_evidence", "artifacts",
        "diagnostics", "decision_rule", "limitations",
    }, "$")
    if top["schema_version"] != RESULT_SCHEMA:
        raise MeasurementError("raw result schema version mismatch")
    pilot = top["pilot"] is True
    if top["performance_values_emitted"] is not True:
        raise MeasurementError("raw result did not mark its performance values as emitted")
    expected_status = _top_level_status(
        pilot=pilot,
        isolation_status=top["isolation_status"],
        authoritative=top["authoritative"],
    )
    if top["status"] != expected_status:
        raise MeasurementError("top-level status does not match the evidence envelope")
    _exact_keys(top["attempt"], {"attempt_id", "pbs_job_id", "run_directory", "success_receipt_path"}, "$.attempt")
    attempt_dir = resolve_attempt_dir(top["attempt"]["attempt_id"])
    if Path(top["attempt"]["run_directory"]).resolve() != attempt_dir:
        raise MeasurementError("raw attempt directory mismatch")
    if Path(top["attempt"]["success_receipt_path"]).resolve() != attempt_dir / "success-receipt.json":
        raise MeasurementError("raw success receipt path mismatch")
    cost = _exact_keys(top["cost_model"], {
        "sample_unit", "measured_sample_count", "measured_sample_cost_s",
        "median_sample_cost_s", "maximum_paired_block_wall_s", "observed_wall_s",
        "planned_maximum_sample_count", "observed_measurement_sample_count",
        "effective_parallelism", "safety_factor", "estimate_formula", "three_hour_limit_s",
    }, "$.cost_model")
    if top["estimated_wall_s"] <= 0 or top["observed_wall_s"] <= 0 or cost["measured_sample_cost_s"] <= 0:
        raise MeasurementError("raw wall/cost values must be positive")
    inputs = _exact_keys(top["inputs"], {
        "manifest_path", "manifest_sha256", "manifest_schema", "population_ids",
        "xdist_import_verification", "source_sha256",
    }, "$.inputs")
    if inputs["manifest_schema"] != INPUT_SCHEMA or inputs["population_ids"] != manifest["population_ids"]:
        raise MeasurementError("raw input population/schema mismatch")
    if set(inputs["source_sha256"]) != set(SOURCE_FILES):
        raise MeasurementError("raw source hash set mismatch")
    verification = _exact_keys(
        inputs["xdist_import_verification"],
        {"status", "version", "sources", "shadow_check"},
        "$.inputs.xdist_import_verification",
    )
    expected_xdist_sources = manifest.get("xdist", {}).get("sources", {})
    if (
        verification["status"] != "passed"
        or verification["version"] != manifest.get("xdist", {}).get("version")
        or set(verification["sources"])
        != {"xdist", "loadscope", "loadgroup", "dsession"}
        or verification["sources"] != expected_xdist_sources
    ):
        raise MeasurementError("xdist import verification mismatch")
    for name, source in verification["sources"].items():
        _exact_keys(source, {"path", "sha256"}, f"$.inputs.xdist_import_verification.sources.{name}")
    shadow = _exact_keys(verification["shadow_check"], {
        "status", "pinned_package_path", "pinned_sys_path_entry",
        "pinned_sys_path_index", "preceding_entries_checked",
    }, "$.inputs.xdist_import_verification.shadow_check")
    if (
        shadow["status"] != "passed"
        or shadow["pinned_package_path"] != manifest.get("xdist", {}).get("source_root")
        or type(shadow["pinned_sys_path_index"]) is not int
        or shadow["pinned_sys_path_index"] < 0
        or shadow["preceding_entries_checked"] != shadow["pinned_sys_path_index"]
    ):
        raise MeasurementError("xdist shadow verification mismatch")
    timing = _exact_keys(top["timing"], {
        "timer_probe", "minimum_pairs", "maximum_pairs", "relative_half_width_threshold",
        "minimum_practical_effect_s", "absolute_noise_bound_s", "fresh_process_unit",
        "controller_thread_single_core_pinned",
        "worker_collection_decode_clone_and_control_prepared_before_clock",
        "transcript_generated_only_by_certification",
    }, "$.timing")
    timer_probe = _exact_keys(timing["timer_probe"], {
        "read_count", "zero_rate", "minimum_positive_delta_ns", "median_delta_ns",
        "p99_delta_ns", "clock_info",
    }, "$.timing.timer_probe")
    _exact_keys(
        timer_probe["clock_info"],
        {"implementation", "monotonic", "adjustable", "resolution"},
        "$.timing.timer_probe.clock_info",
    )
    _exact_keys(top["environment"], {
        "hostname", "pbs_jobid", "python", "python_executable", "pythonpath", "pytest",
        "xdist_version", "xdist_path", "kernel", "machine", "affinity_cpus", "thread_count",
    }, "$.environment")
    pythonpath = _exact_keys(
        top["environment"]["pythonpath"], {"state", "value"},
        "$.environment.pythonpath",
    )
    if (
        (pythonpath["state"] == "absent" and pythonpath["value"] is not None)
        or (pythonpath["state"] == "empty" and pythonpath["value"] != "")
        or (
            pythonpath["state"] == "set"
            and (type(pythonpath["value"]) is not str or pythonpath["value"] == "")
        )
        or pythonpath["state"] not in {"absent", "empty", "set"}
    ):
        raise MeasurementError("raw PYTHONPATH observation mismatch")
    isolation = _exact_keys(top["isolation_evidence"], {
        "pre", "post", "sampling", "exclusive_placement_proven", "reason",
    }, "$.isolation_evidence")
    _validate_process_snapshot(isolation["pre"], "$.isolation_evidence.pre")
    _validate_process_snapshot(isolation["post"], "$.isolation_evidence.post")
    _exact_keys(top["diagnostics"], {
        "single_run_hybrid_residual_s", "residual_role", "cold_lookup_claimed",
        "pre_touch_memory_pressure_diagnostic_only",
    }, "$.diagnostics")
    _exact_keys(top["decision_rule"], {
        "metric", "threshold_s", "rule", "selected_next_experiment",
        "wall_improvement_claimed", "d747_claim_closed",
    }, "$.decision_rule")
    if type(top["limitations"]) is not list or any(type(item) is not str for item in top["limitations"]):
        raise MeasurementError("limitations shape mismatch")
    controller_map = _controller_map(manifest)
    results = top["population_results"]
    if type(results) is not list or {value.get("controller_id") for value in results} != set(controller_map):
        raise MeasurementError("raw controller set mismatch")
    for result in results:
        obj = _exact_keys(result, {
            "population_id", "controller_id", "n", "worker_count", "pilot", "hot_replay",
            "isolation_status", "authoritative", "path_a", "path_b",
        }, "$.population_results[]")
        expected_population, expected_n = controller_map[obj["controller_id"]]
        if obj["population_id"] != expected_population or obj["pilot"] is not pilot:
            raise MeasurementError("controller population/pilot mismatch")
        if (not pilot and obj["n"] != expected_n) or (pilot and not 1 <= obj["n"] <= expected_n):
            raise MeasurementError("controller population size mismatch")
        path_a = _exact_keys(obj["path_a"], {
            "adopted", "adoption_gate_results", "hot_replay", "list_index_slot_probes",
            "marginal_replay_cpu_saving_vs_o1_control_s", "primary_first_worker_identity_alias",
            "negative_control", "pre_touch_memory_pressure_diagnostic",
            "all_worker_clone_certification", "actual_controller_cpu_seconds_claimed",
        }, "$.population_results[].path_a")
        _validate_measurement(path_a["primary_first_worker_identity_alias"], expected_population, obj["controller_id"], "path_a.primary")
        _validate_measurement(path_a["negative_control"], expected_population, obj["controller_id"], "path_a.negative", negative=True)
        diagnostic = _exact_keys(path_a["pre_touch_memory_pressure_diagnostic"], {"diagnostic_only", "measurement"}, "path_a.pre_touch")
        if diagnostic["diagnostic_only"] is not True:
            raise MeasurementError("pre-touch value is not marked diagnostic-only")
        _validate_measurement(diagnostic["measurement"], expected_population, obj["controller_id"], "path_a.pre_touch.measurement")
        path_a_gates = _exact_keys(path_a["adoption_gate_results"], {
            "primary_measurement_status", "primary_minimum_pairs",
            "primary_abba_baab_balanced", "primary_order_effect",
            "negative_control_ci", "negative_control_order", "non_pilot",
        }, "path_a.adoption_gate_results")
        expected_path_a_gates = _path_a_adoption_gate_results(
            path_a["primary_first_worker_identity_alias"],
            path_a["negative_control"],
            minimum_pairs=timing["minimum_pairs"],
            pilot=pilot,
        )
        if dict(path_a_gates) != expected_path_a_gates:
            raise MeasurementError("path A adoption gate result mismatch")
        path_a_adopted = all(path_a_gates.values())
        if path_a["adopted"] is not path_a_adopted:
            raise MeasurementError("path A adoption decision mismatch")
        if (
            path_a["marginal_replay_cpu_saving_vs_o1_control_s"]
            != path_a["primary_first_worker_identity_alias"][
                "marginal_replay_cpu_saving_vs_o1_control_s"
            ]
            or path_a["list_index_slot_probes"] != obj["n"] * (obj["n"] + 1) // 2
        ):
            raise MeasurementError("path A primary value or slot-probe total mismatch")
        path_b = obj["path_b"]
        if type(path_b) is not dict or set(path_b) != set(SCENARIOS):
            raise MeasurementError("path B scenario set mismatch")
        for scenario, entry in path_b.items():
            b = _exact_keys(entry, {
                "adopted", "performance_values_emitted",
                "adoption_gate_results", "hot_replay", "scenario",
                "total_all_real_minus_all_oracle", "by_caller_conditional_marginals",
                "interaction_residual_s", "caller_values_are_additive_breakdown", "negative_control",
                "amplification_linearity", "caller_counts", "scope_visits", "item_visits",
                "tests_finished", "worker_workload_distribution", "occupancy_gate",
                "actual_controller_cpu_seconds_claimed",
            }, f"path_b.{scenario}")
            if b["scenario"] != scenario or set(b["by_caller_conditional_marginals"]) != set(CALLERS):
                raise MeasurementError("path B scenario/caller set mismatch")
            _validate_counter(b["caller_counts"], set(CALLERS), f"path_b.{scenario}.caller_counts")
            _validate_counter(b["scope_visits"], set(CALLERS), f"path_b.{scenario}.scope_visits")
            _validate_counter(b["item_visits"], set(CALLERS), f"path_b.{scenario}.item_visits")
            _validate_tests_finished(b["tests_finished"], f"path_b.{scenario}.tests_finished")
            distribution = _exact_keys(
                b["worker_workload_distribution"], {"scopes", "items"},
                f"path_b.{scenario}.worker_workload_distribution",
            )
            _validate_distribution(distribution["scopes"], f"path_b.{scenario}.worker_workload_distribution.scopes")
            _validate_distribution(distribution["items"], f"path_b.{scenario}.worker_workload_distribution.items")
            _validate_occupancy(b["occupancy_gate"], f"path_b.{scenario}.occupancy_gate")
            _validate_measurement(b["total_all_real_minus_all_oracle"], expected_population, obj["controller_id"], f"path_b.{scenario}.total")
            for caller, measurement in b["by_caller_conditional_marginals"].items():
                _validate_measurement(measurement, expected_population, obj["controller_id"], f"path_b.{scenario}.{caller}")
            _validate_measurement(b["negative_control"], expected_population, obj["controller_id"], f"path_b.{scenario}.negative", negative=True)
            linearity = b["amplification_linearity"]
            expected_keys = {
                "status", "model", "k_measurements", "block_slope_confidence_interval_95",
                "block_slope_count", "maximum_block_relative_residual", "relative_residual_threshold",
                "slope_ci_excludes_zero", "all_k_measurement_gates_passed", "k1_cost_equivalence_claimed",
            }
            if linearity.get("status") == "passed":
                expected_keys.add("beta_hot_repetition_s")
            _exact_keys(linearity, expected_keys, f"path_b.{scenario}.linearity")
            if set(linearity["k_measurements"]) != {"1", "2", "4", "8"}:
                raise MeasurementError("K measurement set mismatch")
            _validate_ci(linearity["block_slope_confidence_interval_95"], f"path_b.{scenario}.slope_ci")
            for k, measurement in linearity["k_measurements"].items():
                _validate_measurement(measurement, expected_population, obj["controller_id"], f"path_b.{scenario}.k{k}")
            adoption_gates = _exact_keys(b["adoption_gate_results"], {
                "occupancy_exact_match", "total_measurement", "all_caller_measurements",
                "negative_control", "non_pilot",
            }, f"path_b.{scenario}.adoption_gate_results")
            expected_adoption_gates = {
                "occupancy_exact_match": b["occupancy_gate"]["adopt_path_b"] is True,
                "total_measurement": _measurement_passed(
                    b["total_all_real_minus_all_oracle"], timing["minimum_pairs"], False
                ),
                "all_caller_measurements": all(
                    _measurement_passed(value, timing["minimum_pairs"], False)
                    for value in b["by_caller_conditional_marginals"].values()
                ),
                "negative_control": (
                    b["negative_control"]["negative_control_ci_gate"] == "passed"
                    and b["negative_control"]["negative_control_order_gate"] == "passed"
                ),
                "non_pilot": not pilot,
            }
            if dict(adoption_gates) != expected_adoption_gates:
                raise MeasurementError(f"path B adoption gate result mismatch at {scenario}")
            adopted = all(adoption_gates.values())
            if (
                b["adopted"] is not adopted
                or b["performance_values_emitted"] is not True
            ):
                raise MeasurementError(f"path B adoption decision mismatch at {scenario}")
        if pilot and (path_a["adopted"] is not False or any(entry["adopted"] is not False for entry in path_b.values())):
            raise MeasurementError("pilot leaf was marked adopted")
    certification = _exact_keys(top["certification"], {
        "status", "all_controller_scenario_count", "observed_wall_s",
        "occupancy_adoption_summary", "results",
    }, "$.certification")
    if certification["status"] != "correctness-passed-before-performance" or certification["all_controller_scenario_count"] != 8:
        raise MeasurementError("global certification summary mismatch")
    occupancy_summary = _exact_keys(certification["occupancy_adoption_summary"], {
        "passed_count", "failed_count", "not_applicable_count", "all_applicable_passed",
    }, "$.certification.occupancy_adoption_summary")
    observed_occupancy_counts: Counter[str] = Counter()
    for entry in certification["results"]:
        c = _exact_keys(entry, {
            "population_id", "controller_id", "scenario", "status", "all_pending_values_equal",
            "behavior_transcript_equal", "all_worker_clone_control", "pending_call_count", "occupancy_gate",
        }, "$.certification.results[]")
        if controller_map[c["controller_id"]][0] != c["population_id"]:
            raise MeasurementError("certification population mismatch")
        if c["status"] != "correctness-passed":
            raise MeasurementError("correctness certification status mismatch")
        _validate_occupancy(c["occupancy_gate"], "$.certification.results[].occupancy_gate")
        observed_occupancy_counts[c["occupancy_gate"]["status"]] += 1
    expected_occupancy_summary = {
        "passed_count": observed_occupancy_counts["passed"],
        "failed_count": observed_occupancy_counts["failed"],
        "not_applicable_count": observed_occupancy_counts["not-applicable"],
        "all_applicable_passed": observed_occupancy_counts["failed"] == 0,
    }
    if dict(occupancy_summary) != expected_occupancy_summary:
        raise MeasurementError("certification occupancy adoption summary mismatch")
    k2 = top["k2_aggregate"]
    _exact_keys(k2, {"population_id", "effective_worker_count_per_shard", "path_a", "path_b"}, "$.k2_aggregate")
    k2_path_b = _exact_keys(
        k2["path_b"], set(SCENARIOS), "$.k2_aggregate.path_b"
    )
    for aggregate in [k2["path_a"], *k2_path_b.values()]:
        required = {"status", "all_shards_adopted"}
        if aggregate["status"] == "adopted":
            required |= {
                "shard_marginal_replay_cpu_saving_vs_o1_control_s",
                "sum_shard_marginal_replay_cpu_saving_vs_o1_control_s",
                "max_shard_marginal_replay_cpu_saving_vs_o1_control_s",
                "aggregate_confidence_interval_95",
            }
        _exact_keys(aggregate, required, "$.k2_aggregate.aggregate")
        if aggregate["status"] == "adopted":
            _exact_keys(
                aggregate["aggregate_confidence_interval_95"],
                {"mean_s", "low_s", "high_s", "method"},
                "$.k2_aggregate.aggregate.aggregate_confidence_interval_95",
            )
    if pilot and any(aggregate["status"] == "adopted" for aggregate in [k2["path_a"], *k2["path_b"].values()]):
        raise MeasurementError("pilot aggregate was marked adopted")
    expected_k2 = _aggregate_k2(results, pilot)
    if k2 != expected_k2:
        raise MeasurementError("K=2 aggregate does not exactly match its shard leaves")
    expected_decision = _decision_rule(expected_k2)
    if top["decision_rule"] != expected_decision:
        raise MeasurementError("decision rule does not exactly match the K=2 aggregate")
    artifacts = _exact_keys(top["artifacts"], {
        "certification_trace_path", "certification_trace_sha256",
        "certification_trace_records", "checkpoint_root",
    }, "$.artifacts")
    actual_trace = trace_path or Path(artifacts["certification_trace_path"]).resolve()
    if actual_trace != Path(artifacts["certification_trace_path"]).resolve():
        raise MeasurementError("certification trace path mismatch")
    try:
        trace_payload = actual_trace.read_bytes()
    except OSError as exc:
        raise MeasurementError(f"cannot read certification trace: {exc}") from exc
    if _sha256_bytes(trace_payload) != artifacts["certification_trace_sha256"]:
        raise MeasurementError("certification trace digest mismatch")
    lines = trace_payload.splitlines()
    if len(lines) != artifacts["certification_trace_records"]:
        raise MeasurementError("certification trace record count mismatch")
    for index, line in enumerate(lines):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise MeasurementError(f"invalid trace JSON at line {index + 1}") from exc
        controller_id = record.get("controller_id")
        if controller_id not in controller_map or record.get("population_id") != controller_map[controller_id][0]:
            raise MeasurementError("trace population/controller mismatch")
        if record.get("type") == "event":
            _exact_keys(record, {
                "type", "population_id", "controller_id", "scenario", "event_seq", "event",
                "worker", "virtual_time_s", "tests_finished", "tests_finished_workers_scanned",
                "workqueue_units", "active_workers",
            }, "trace.event")
        elif record.get("type") == "pending_of":
            _exact_keys(record, {
                "type", "population_id", "controller_id", "scenario", "event_seq", "caller",
                "workload_scopes", "workload_items", "pending", "real", "oracle",
            }, "trace.pending_of")
        else:
            raise MeasurementError("unknown certification trace record type")


def validate_receipt(receipt: Mapping[str, Any], raw: Mapping[str, Any], raw_payload: bytes) -> None:
    obj = _exact_keys(receipt, {
        "schema_version", "status", "attempt_id", "pbs_job_id", "pilot",
        "raw_result_path", "raw_result_sha256", "manifest_sha256", "source_sha256",
    }, "receipt")
    if obj["schema_version"] != RECEIPT_SCHEMA or obj["status"] != "success":
        raise MeasurementError("success receipt status/schema mismatch")
    if (
        obj["attempt_id"] != raw["attempt"]["attempt_id"]
        or obj["pbs_job_id"] != raw["attempt"]["pbs_job_id"]
        or obj["pilot"] is not raw["pilot"]
        or obj["raw_result_sha256"] != _sha256_bytes(raw_payload)
        or obj["manifest_sha256"] != raw["inputs"]["manifest_sha256"]
        or obj["source_sha256"] != raw["inputs"]["source_sha256"]
    ):
        raise MeasurementError("success receipt is not bound to this raw result attempt")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--measure", action="store_true")
    mode.add_argument("--pilot", action="store_true")
    mode.add_argument("--self-test-proc-stat", action="store_true")
    parser.add_argument("--manifest", type=Path, default=Path(__file__).resolve().parent / "input-manifest.json")
    parser.add_argument("--attempt-id")
    parser.add_argument("--min-pairs", type=int, default=MIN_PAIRS_DEFAULT)
    parser.add_argument("--max-pairs", type=int, default=MAX_PAIRS_DEFAULT)
    parser.add_argument("--relative-half-width", type=float, default=RELATIVE_HALF_WIDTH_DEFAULT)
    parser.add_argument("--minimum-practical-effect-s", type=float, default=MINIMUM_PRACTICAL_EFFECT_S_DEFAULT)
    parser.add_argument("--absolute-noise-bound-s", type=float, default=ABSOLUTE_NOISE_BOUND_S_DEFAULT)
    parser.add_argument("--diagnostic-pairs", type=int, default=2)
    parser.add_argument("--deadline-seconds", type=float)
    parser.add_argument("--max-workers", type=int)
    args = parser.parse_args(argv)
    if args.self_test_proc_stat:
        try:
            print(json.dumps(_proc_stat_parser_regression(), ensure_ascii=True, sort_keys=True))
        except MeasurementError as exc:
            print(f"proc stat parser regression failed: {exc}", file=sys.stderr)
            return 2
        return 0
    pilot = bool(args.pilot)
    attempt_id = args.attempt_id
    if attempt_id is None and pilot:
        attempt_id = f"pilot-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{os.getpid()}"
    if attempt_id is None:
        parser.error("full measurement requires --attempt-id")
    min_pairs = PILOT_PAIRS if pilot else args.min_pairs
    max_pairs = PILOT_PAIRS if pilot else args.max_pairs
    diagnostic_pairs = PILOT_PAIRS if pilot else args.diagnostic_pairs
    deadline = args.deadline_seconds or (600.0 if pilot else FULL_DEADLINE_SECONDS)
    max_workers = args.max_workers or (PILOT_WORKERS if pilot else 48)
    try:
        raw = measure_all(
            args.manifest, attempt_id, pilot=pilot, min_pairs=min_pairs, max_pairs=max_pairs,
            relative_half_width=args.relative_half_width,
            practical_effect_s=args.minimum_practical_effect_s,
            noise_bound_s=args.absolute_noise_bound_s,
            diagnostic_pairs=diagnostic_pairs, deadline_seconds=deadline, max_workers=max_workers,
        )
        print(json.dumps({
            "schema_version": raw["schema_version"], "status": raw["status"],
            "pilot": raw["pilot"], "attempt_id": raw["attempt"]["attempt_id"],
            "raw_result": str(Path(raw["attempt"]["run_directory"]) / "raw-result.json"),
            "estimated_wall_s": raw["estimated_wall_s"], "observed_wall_s": raw["observed_wall_s"],
        }, ensure_ascii=True, sort_keys=True))
    except (MeasurementError, ReplayError) as exc:
        print(f"measurement failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
