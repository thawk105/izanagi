#!/usr/bin/env python3
"""Measure Cicada adaptive-backoff constants on a Pegasus compute node.

This is a performance-only probe. It builds trace-disabled binaries, never
uses perf, and does not make a correctness or certification claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import resource
import statistics
import subprocess
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from orchestrator.calibrator.runner import measure_point  # noqa: E402
from orchestrator.campaign import buildcache, env_contract, site_policy, source_digest  # noqa: E402
from orchestrator.campaign.build_admission import (  # noqa: E402
    GeneratorId,
    attest_generator_output,
    build_run_context,
    derive_build_admission,
)
from orchestrator.campaign.model import Genome  # noqa: E402
from orchestrator.campaign.p2_2 import RECORDS, _assert_single_tenant  # noqa: E402
from orchestrator.campaign.patchharness import applied, assert_pinned_clean  # noqa: E402
from orchestrator.campaign.pin import CURRENT_PIN  # noqa: E402

SCHEMA_VERSION = "izanagi-cicada-adaptive-3const-probe/v1"
NOT_CERTIFIED = (
    "trace-disabled performance runs only; no serializability check was run"
)
PIN_FULL = "511c9538e4e8efa54b45cda62e72389ed3b706ec"
PATCH = ROOT / "patches" / "cicada-adaptive-params.patch"

CONTRACT = env_contract.lookup("pegasus")
ENV_TAG = CONTRACT.env_tag
CLOCKS_PER_US = CONTRACT.clocks_per_us
NUMA = list(CONTRACT.numactl)

LOGICAL_CORES = 48
DEFAULT_THREADS = (48,)
DEFAULT_WORKLOADS = ("write-heavy", "balanced", "read-heavy")
EXTIME = 3
RUN_TIMEOUT_S = 180.0

STOCK_STEP_US = 100.0
STOCK_INCR_MILLI = 100_000
STOCK_MAX_US = 1_000
STOCK_UPDATE_US = 10

BASE = {
    "NO_WAIT_LOCKING_IN_VALIDATION": 1,
    "NO_WAIT_OF_TICTOC": 0,
    "WAL": 0,
}

WORKLOADS = {
    "write-heavy": {
        "ycsb_zipf_skew": "0.9",
        "ycsb_rratio": "5",
        "ycsb_rmw": "0",
        "ycsb_max_ope": "10",
    },
    "balanced": {
        "ycsb_zipf_skew": "0.9",
        "ycsb_rratio": "50",
        "ycsb_rmw": "0",
        "ycsb_max_ope": "10",
    },
    "read-heavy": {
        "ycsb_zipf_skew": "0.9",
        "ycsb_rratio": "95",
        "ycsb_rmw": "0",
        "ycsb_max_ope": "10",
    },
}

_LABEL_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_INTEGER_RE = re.compile(r"[0-9]+")


@dataclass(frozen=True)
class Cell:
    """One runtime grid cell, normalized to an exact 1/1000 us build value."""

    label: str
    back_off: int
    step_us: float
    ceiling_us: int
    update_us: int

    @property
    def incr_milli(self) -> int:
        return int(Decimal(str(self.step_us)) * 1000)

    @property
    def is_stock_control(self) -> bool:
        return is_stock_control(self)


def is_stock_control(cell: Cell) -> bool:
    """Return true only for exact stock adaptive settings."""
    return (
        cell.back_off == 1
        and cell.step_us == STOCK_STEP_US
        and cell.ceiling_us == STOCK_MAX_US
        and cell.update_us == STOCK_UPDATE_US
    )


def _parse_positive_integer(text: str, field: str) -> int:
    if _INTEGER_RE.fullmatch(text) is None:
        raise ValueError(f"{field} must be a positive integer: {text!r}")
    value = int(text)
    if value <= 0:
        raise ValueError(f"{field} must be positive: {value}")
    return value


def _parse_step_us(text: str) -> tuple[float, int]:
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"step_us is not a decimal: {text!r}") from exc
    if not value.is_finite() or value <= 0:
        raise ValueError(f"step_us must be finite and positive: {text!r}")
    milli = value * 1000
    integral = milli.to_integral_value()
    if milli != integral:
        raise ValueError(
            f"step_us cannot be represented exactly in 1/1000 us: {text!r}"
        )
    return float(value), int(integral)


def parse_cells(text: str) -> tuple[Cell, ...]:
    """Parse ``label:back_off:step_us:ceiling_us:update_us`` cells."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("cells must not be empty")
    cells: list[Cell] = []
    labels: set[str] = set()
    for index, raw_cell in enumerate(text.split(",")):
        fields = [field.strip() for field in raw_cell.split(":")]
        if len(fields) != 5 or any(not field for field in fields):
            raise ValueError(
                f"cell {index} must have five nonempty colon-separated fields: "
                f"{raw_cell!r}"
            )
        label, back_off_text, step_text, ceiling_text, update_text = fields
        if _LABEL_RE.fullmatch(label) is None:
            raise ValueError(f"cell label is unsafe: {label!r}")
        if label in labels:
            raise ValueError(f"duplicate cell label: {label!r}")
        if back_off_text not in {"0", "1"}:
            raise ValueError(f"back_off must be 0 or 1: {back_off_text!r}")
        step_us, incr_milli = _parse_step_us(step_text)
        ceiling_us = _parse_positive_integer(ceiling_text, "ceiling_us")
        update_us = _parse_positive_integer(update_text, "update_us")
        cell = Cell(label, int(back_off_text), step_us, ceiling_us, update_us)
        if cell.incr_milli != incr_milli:
            raise ValueError(f"step_us normalization changed value: {step_text!r}")
        cells.append(cell)
        labels.add(label)
    if not cells:
        raise ValueError("cells must not be empty")
    return tuple(cells)


_parse_cells = parse_cells


def _validate_grid_contract(cells: tuple[Cell, ...]) -> None:
    disabled = [cell for cell in cells if cell.back_off == 0]
    if len(disabled) != 1 or disabled[0] != Cell(
        "none", 0, STOCK_STEP_US, STOCK_MAX_US, STOCK_UPDATE_US
    ):
        raise ValueError(
            "grid must contain exactly none:0:100:1000:10 as its disabled cell"
        )
    if sum(cell.is_stock_control for cell in cells) != 1:
        raise ValueError("grid must contain exactly one stock adaptive control")
    configurations = {
        (cell.back_off, cell.incr_milli, cell.ceiling_us, cell.update_us)
        for cell in cells
    }
    if len(configurations) != len(cells):
        raise ValueError("grid contains duplicate build configurations")


def _parse_threads(text: str) -> tuple[int, ...]:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("threads must not be empty")
    values = []
    for token in text.split(","):
        token = token.strip()
        if _INTEGER_RE.fullmatch(token) is None:
            raise ValueError(f"thread count must be an integer: {token!r}")
        value = int(token)
        if value <= 0 or value > LOGICAL_CORES:
            raise ValueError(f"thread count is outside 1..{LOGICAL_CORES}: {value}")
        values.append(value)
    if len(set(values)) != len(values):
        raise ValueError(f"thread list contains duplicates: {text!r}")
    return tuple(values)


def _parse_workloads(text: str) -> tuple[str, ...]:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("workloads must not be empty")
    values = tuple(token.strip() for token in text.split(","))
    if any(not token for token in values):
        raise ValueError(f"workload list contains an empty item: {text!r}")
    unknown = [token for token in values if token not in WORKLOADS]
    if unknown:
        raise ValueError(f"unknown workloads: {unknown}")
    if len(set(values)) != len(values):
        raise ValueError(f"workload list contains duplicates: {text!r}")
    return values


def _nonnegative_int(text: str) -> int:
    value = int(text)
    if value < 0:
        raise argparse.ArgumentTypeError("must be nonnegative")
    return value


def _positive_int(text: str) -> int:
    value = int(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return value


def _ccbench_head(submodule: Path) -> str:
    head = subprocess.run(
        ["git", "-C", str(submodule), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if CURRENT_PIN != PIN_FULL[: len(CURRENT_PIN)] or head != PIN_FULL:
        raise RuntimeError(
            f"ccbench HEAD {head!r} does not match required pin {PIN_FULL!r}"
        )
    return head


@contextmanager
def isolated_checkout(submodule: Path, pin_commit: str):
    """Create a node-local ``--shared`` clone under ``$TMPDIR``."""
    tmpdir = os.environ.get("TMPDIR")
    if not tmpdir:
        raise RuntimeError("TMPDIR is required for the node-local checkout")
    path = Path(tmpdir) / "ccbench-src"
    if path.exists():
        raise FileExistsError(f"isolated checkout already exists: {path}")
    subprocess.run(
        ["git", "clone", "--shared", "--no-checkout", str(submodule), str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "-C", str(path), "checkout", "--detach", pin_commit],
        check=True,
        capture_output=True,
        text=True,
    )
    assert_pinned_clean(str(path), pin_commit)
    try:
        yield str(path)
    finally:
        assert_pinned_clean(str(path), pin_commit)


def genome_for(cell: Cell) -> Genome:
    return Genome(
        "silo",
        {
            **BASE,
            "BACK_OFF": cell.back_off,
            "BACKOFF_INCR_MILLI": cell.incr_milli,
            "BACKOFF_MAX_US": cell.ceiling_us,
            "BACKOFF_UPDATE_US": cell.update_us,
        },
    )


def _cpu_seconds() -> float:
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime


def _validate_output_path(out: Path) -> None:
    if out.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {out}")


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cells", required=True)
    parser.add_argument(
        "--workloads", default=",".join(DEFAULT_WORKLOADS)
    )
    parser.add_argument(
        "--threads", default=",".join(str(value) for value in DEFAULT_THREADS)
    )
    parser.add_argument("--rep-index", type=_nonnegative_int, default=0)
    parser.add_argument("--reps-per-job", type=_positive_int, default=1)
    parser.add_argument("--stage", type=int, choices=(1, 2, 3), default=1)
    parser.add_argument("--extime", type=_positive_int, default=EXTIME)
    parser.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _argument_parser().parse_args(argv)
    cells = parse_cells(args.cells)
    _validate_grid_contract(cells)
    workloads = _parse_workloads(args.workloads)
    threads_axis = _parse_threads(args.threads)
    out = Path(args.out)
    _validate_output_path(out)
    if not PATCH.is_file():
        raise FileNotFoundError(f"patch is missing: {PATCH}")

    site = site_policy.current_site()
    if site_policy.refuses_heavy_work(site):
        raise RuntimeError(
            site_policy.heavy_work_refusal(site, "T-2187 adaptive constant probe")
        )
    _assert_single_tenant()

    started_utc = datetime.now(timezone.utc).isoformat()
    wall_started = time.monotonic()
    cpu_started = _cpu_seconds()

    submodule = ROOT / "external" / "ccbench"
    head = _ccbench_head(submodule)
    assert_pinned_clean(str(submodule), CURRENT_PIN)
    cc, cxx = buildcache.compilers_for_current_site()
    cache_root = Path(os.environ["TMPDIR"]) / "build-variants"
    cache_root.mkdir(mode=0o700)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "kind": "performance-only-probe",
        "not_certified": NOT_CERTIFIED,
        "stage": args.stage,
        "grid_spec": args.cells,
        "env_tag": ENV_TAG,
        "site": "pegasus",
        "host": os.uname().nodename,
        "pbs_jobid": os.environ.get("PBS_JOBID"),
        "rep_index": args.rep_index,
        "records": RECORDS,
        "extime_s": args.extime,
        "reps_per_job": args.reps_per_job,
        "clocks_per_us": CLOCKS_PER_US,
        "numactl": NUMA,
        "use_perf": False,
        "ccbench_commit": CURRENT_PIN,
        "ccbench_head": head,
        "cc": cc,
        "cxx": cxx,
        "patch_sha256": hashlib.sha256(PATCH.read_bytes()).hexdigest(),
        "stock": {
            "step_us": STOCK_STEP_US,
            "ceiling_us": STOCK_MAX_US,
            "update_us": STOCK_UPDATE_US,
        },
        "started_utc": started_utc,
        "cells": [],
    }

    with isolated_checkout(submodule, CURRENT_PIN) as work_root:
        with applied(str(PATCH), CURRENT_PIN, work_root):
            build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
            built = []
            for cell in cells:
                genome = genome_for(cell)
                evidence = source_digest.resolve_evidence(
                    genome,
                    CURRENT_PIN,
                    cxx=cxx,
                    ccbench_dir=work_root,
                )
                receipt = attest_generator_output(
                    build_context,
                    evidence,
                    generator_input_sha256=hashlib.sha256(
                        f"{SCHEMA_VERSION}|{evidence.genome_sha256}".encode("utf-8")
                    ).hexdigest(),
                )
                admission = derive_build_admission(
                    build_context, evidence, generator_receipt=receipt
                )
                build_started = time.monotonic()
                build = buildcache.build(
                    genome,
                    ccbench_commit=CURRENT_PIN,
                    trace=False,
                    cc=cc,
                    cxx=cxx,
                    admission=admission,
                    build_context=build_context,
                    source_evidence=evidence,
                    cache_root=str(cache_root),
                    ccbench_dir=work_root,
                )
                built.append((cell, genome, build))
                print(
                    f"[build] {cell.label} sha={build.bin_sha256[:16]} "
                    f"cached={build.cached} "
                    f"{time.monotonic() - build_started:.1f}s",
                    flush=True,
                )

            binary_shas = {
                cell.label: build.bin_sha256 for cell, _genome, build in built
            }
            if len(set(binary_shas.values())) != len(binary_shas):
                raise RuntimeError(
                    "cells produced duplicate binaries; a build define may be inert: "
                    f"{binary_shas}"
                )

            for workload_id in workloads:
                workload = WORKLOADS[workload_id]
                for threads in threads_axis:
                    for cell, genome, build in built:
                        measure_started = time.monotonic()
                        point = measure_point(
                            build.binary,
                            records=RECORDS,
                            threads=threads,
                            clocks_per_us=CLOCKS_PER_US,
                            extime=args.extime,
                            reps=args.reps_per_job,
                            workload=workload,
                            numactl=NUMA,
                            timeout_s=RUN_TIMEOUT_S,
                            use_perf=False,
                        )
                        throughputs = list(point.throughputs)
                        median_tps = (
                            statistics.median(throughputs) if throughputs else None
                        )
                        payload["cells"].append(
                            {
                                "cell": cell.label,
                                "workload": workload_id,
                                "workload_flags": dict(workload),
                                "threads": threads,
                                "back_off": cell.back_off,
                                "step_us": cell.step_us,
                                "ceiling_us": cell.ceiling_us,
                                "update_us": cell.update_us,
                                "is_stock_control": cell.is_stock_control,
                                "genome": genome.canonical(),
                                "binary_sha256": build.bin_sha256,
                                "throughputs": throughputs,
                                "median_tps": median_tps,
                                "abort_rate": point.abort_rate,
                                "latency_ns": point.latency_ns,
                                "run_cmd": point.run_cmd,
                                "measured_utc": datetime.now(timezone.utc).isoformat(),
                            }
                        )
                        shown = (
                            "none" if median_tps is None else f"{median_tps:,.0f}"
                        )
                        print(
                            f"[run] workload={workload_id} t={threads:2d} "
                            f"cell={cell.label} median={shown} tps "
                            f"({time.monotonic() - measure_started:.1f}s)",
                            flush=True,
                        )

    wall_seconds = time.monotonic() - wall_started
    cpu_seconds = _cpu_seconds() - cpu_started
    payload["finished_utc"] = datetime.now(timezone.utc).isoformat()
    payload["wall_seconds"] = wall_seconds
    payload["cpu_seconds"] = cpu_seconds
    payload["cpu_over_elapsed"] = cpu_seconds / wall_seconds

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(
        f"[done] {out} wall={wall_seconds:.1f}s cpu={cpu_seconds:.1f}s "
        f"cpu/wall={payload['cpu_over_elapsed']:.2f}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
