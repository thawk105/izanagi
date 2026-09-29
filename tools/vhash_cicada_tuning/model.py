"""Pure diagnostic Cicada experiment model.

The control is the canonical CC/data-path equivalent of the CMake defaults
in Options.cmake: BACK_OFF=1, REUSE_VERSION=1, WRITE_LATEST_ONLY=0,
INLINE_VERSION_OPT_CICADA=0. Default promotion=1 is redundant when OPT=0;
its printed value differs, so binding uses canonical promotion=0.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from orchestrator.campaign.genome import CICADA_SPACE
from orchestrator.holdout_observation import normalized_direct_gflags

THREADS = 48
SKEW = "0.9"
RMW = 0
EXTIME = 3
CLOCKS_PER_US = 2100
L3_BYTES_EXPECTED = 110_100_480
CONTROL = {"BACK_OFF": 1, "INLINE_VERSION_OPT": 0,
           "INLINE_VERSION_PROMOTION": 0, "REUSE_VERSION": 1,
           "WRITE_LATEST_ONLY": 0}
AXES = tuple(sorted(CONTROL))


@dataclass(frozen=True)
class Workload:
    name: str
    rratio: int
    max_ope: int
    wait: bool = False


WORKLOADS = {
    "W1": Workload("W1", 5, 10),
    "W2": Workload("W2", 50, 10),
    "W3": Workload("W3", 95, 10),
    "W4": Workload("W4", 95, 100),
    "W5": Workload("W5", 50, 10, True),
}


def genomes() -> list[dict[str, int]]:
    result = [dict(g.flags) for g in CICADA_SPACE.enumerate()]
    if len(result) != 24 or CONTROL not in result:
        raise RuntimeError("CICADA_SPACE changed; review experiment")
    return result


def validate_genome(flags: Mapping[str, int]) -> None:
    if dict(flags) not in genomes():
        raise ValueError("genome is outside canonical CICADA_SPACE")


def canonical(flags: Mapping[str, int]) -> str:
    validate_genome(flags)
    return ",".join(f"{axis}={flags[axis]}" for axis in AXES)


def parse_canonical(value: str) -> dict[str, int]:
    try:
        fields = dict(part.split("=", 1) for part in value.split(","))
        result = {axis: int(fields[axis]) for axis in AXES}
    except (ValueError, KeyError) as exc:
        raise ValueError("invalid canonical genome") from exc
    if canonical(result) != value:
        raise ValueError("noncanonical genome spelling")
    return result


def reject_holdout_ratio(rratio: int) -> None:
    if rratio in (20, 80):
        raise ValueError("holdout read ratio")


def runtime_argv(workload: Workload, records: int, gc: int, *, threads: int = THREADS) -> list[str]:
    reject_holdout_ratio(workload.rratio)
    if workload.name not in WORKLOADS or workload != WORKLOADS[workload.name]:
        raise ValueError("unknown or altered workload")
    if records <= 0 or gc <= 0 or threads <= 0:
        raise ValueError("records, gc, threads must be positive")
    argv = [f"-thread_num={threads}", f"-ycsb_tuple_num={records}",
            f"-ycsb_zipf_skew={SKEW}", f"-ycsb_rratio={workload.rratio}",
            f"-ycsb_rmw={RMW}", f"-ycsb_max_ope={workload.max_ope}",
            f"-gc_inter_us={gc}", f"-extime={EXTIME}",
            f"-clocks_per_us={CLOCKS_PER_US}"]
    effective = normalized_direct_gflags(argv)
    return argv
