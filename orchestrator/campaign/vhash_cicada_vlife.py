#!/usr/bin/env python3
"""Cicada version lifetime diagnostics; throughput is diagnostic, not performance."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import time

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import condition_meaning_gate as condition
from . import s3_mocc_lock_coverage as compute
from . import s3_lock_coverage as locks
from . import site_policy
from .model import cmake_cache_variable_for_axis
from .materializer_admission import non_admissible_materializer
from .p2_2 import _assert_single_tenant
from .patchharness import applied, checkout

ROOT = Path(__file__).resolve().parents[2]
PIN = "68106660686232781bca3be792a750d3e19d7a8a"
PATCH = ROOT / "patches/instr-cicada-version-lifetime.patch"
DRIVER_ID = "orchestrator.campaign.vhash_cicada_vlife"
MATERIALIZER = DRIVER_ID + "._build_variant"
PREFIX = "IZANAGI_CICADA_VLIFE_JSON "
K = (1, 2, 3, 4, 8)
SITES = ("read_update", "read_ronly", "blind_write", "rmw_latest",
         "precheck", "install", "readcheck", "writecheck")
POSITION_ORIGIN = ["latest"] * 6 + ["scan_start"] * 2
TIME_BOUNDS = [1 << i for i in range(41)] + [18446744073709551615]
MACROS = ("IZANAGI_CICADA_VLIFE", "IZANAGI_CICADA_LONGTX")
CONDITIONS = {
    f"{w}-{l}-gc{gc}": dict(
        ycsb_rratio=50 if w == "A" else 95,
        ycsb_zipf_skew=0 if w == "A" else 0.9,
        thread_num=47 if l == "ops1000" else 48,
        batch_th_num=1 if l == "ops1000" else 0,
        batch_max_ope=1000,
        worker1_insert_delay_rphase_us={"none": 0, "wait1ms": 1000,
                                        "wait10ms": 10000, "ops1000": 0}[l],
        gc_inter_us=gc,
    )
    for w in ("A", "B")
    for l in ("none", "wait1ms", "wait10ms", "ops1000")
    for gc in (10, 1000, 100000)
}
OLD_CONDITIONS = frozenset(CONDITIONS)
TUNED_GENOME = {"BACK_OFF": 0, "INLINE_VERSION_OPT": 1,
                "INLINE_VERSION_PROMOTION": 0, "REUSE_VERSION": 1,
                "WRITE_LATEST_ONLY": 0}
DEFAULT_GENOME = {"BACK_OFF": 1, "INLINE_VERSION_OPT": 0,
                  "INLINE_VERSION_PROMOTION": 1, "REUSE_VERSION": 1,
                  "WRITE_LATEST_ONLY": 0}
BEST100_GENOME = {"BACK_OFF": 0, "INLINE_VERSION_OPT": 0,
                  "INLINE_VERSION_PROMOTION": 0, "REUSE_VERSION": 0,
                  "WRITE_LATEST_ONLY": 0}
ABORT_REASONS = ("early_wts", "early_rts", "precheck", "latest",
                 "read_match", "write_rts_deleted", "node_set", "scan_node_set", "other")
MEASURE_RECORDS = 1000000
for prefix, rates, delays, intervals, skew, genome in (
    ("R", (0, 25, 50, 75, 95), ("none", "wait1msU", "wait10msU", "wait10msR"),
     (10, 1000, 100000), 0.9, "default"),
    ("S", (0, 50, 95), ("none", "wait10msU"), (10, 100000), 0, "default"),
    ("T", (0, 50, 95), ("none", "wait10msU"), (10, 100000), 0.9, "tuned"),
):
    for rate in rates:
        for delay in delays:
            for gc in intervals:
                CONDITIONS[f"{prefix}{rate}-{delay}-gc{gc}"] = dict(
                    ycsb_rratio=50, ycsb_zipf_skew=skew, thread_num=48,
                    batch_th_num=0, batch_max_ope=1000,
                    worker1_insert_delay_rphase_us=(1000 if delay == "wait1msU"
                        else 10000 if delay.startswith("wait10ms") else 0),
                    gc_inter_us=gc, izanagi_ronly_pct=rate,
                    izanagi_long_kind=(2 if delay == "wait10msR" else
                                       1 if delay.endswith("U") else 0),
                    genome=genome)

# The two O blocks use the fixed GF(3) columns and permutations of the
# preregistered design. Keep row order stable: condition IDs bind to rows.
_O_FACTORS = ((.6, .9, .99), (5, 50, 95), (10000, 100000, 1000000),
              (10, 100, 1000), ("none", "batchU", "batchR"), (0, 50, 95),
              (4, 100, 1000), (12, 24, 48), (10, 1000, 100000))
_O_COLS = ((1,0,0),(0,1,0),(0,0,1),(1,1,0),(1,2,0),
           (1,0,1),(1,0,2),(0,1,1),(0,1,2))


def _w_condition(point: tuple, genome: str) -> dict:
    skew, rr, records, ops, kind, ro, val, threads, gc = point
    return dict(records=records, ycsb_max_ope=ops,
                thread_num=threads - (kind != "none"),
                batch_th_num=int(kind != "none"), batch_max_ope=1000,
                val_size=val, genome=genome, ycsb_rratio=rr,
                ycsb_zipf_skew=skew, gc_inter_us=gc,
                izanagi_ronly_pct=ro,
                izanagi_long_kind={"none": 0, "batchU": 1, "batchR": 2}[kind],
                worker1_insert_delay_rphase_us=0)


def _add_w(layer: str, row: int, point: tuple) -> None:
    for genome in ("default", "tuned" if point[3] == 10 else "best100"):
        CONDITIONS[f"W{layer}-{row:02d}-{genome}"] = _w_condition(point, genome)


for _row, _point in enumerate(((skew, rr, 1000000, 10, kind, 0, 4, 48, 100)
    for skew in (.5, .6, .7, .8, .9, .95, .97, .99)
    for rr in (5, 50, 95) for kind in ("none", "batchU", "batchR")), 1):
    _add_w("S", _row, _point)
for _block, _perm, _shift in (("O1", tuple(range(9)), (0,)*9),
                              ("O2", tuple((i+4)%9 for i in range(9)),
                               (1,2,1,2,1,2,1,2,1))):
    for _row, (_a, _b, _c) in enumerate(
        ((a,b,c) for a in range(3) for b in range(3) for c in range(3)), 1):
        _levels = [(_a*x + _b*y + _c*z) % 3 for x,y,z in _O_COLS]
        _point = tuple(_O_FACTORS[i][(_levels[_perm[i]] + _shift[i]) % 3]
                       for i in range(9))
        _add_w(_block, _row, _point)


def genome_args(genome: str) -> list[str]:
    if genome == "default":
        return []
    if genome not in ("tuned", "best100"):
        raise ValueError("unknown genome")
    return [f"-D{cmake_cache_variable_for_axis('cicada', axis)}={value}"
            for axis, value in (TUNED_GENOME if genome == "tuned" else BEST100_GENOME).items()]


def verify_genome_commands(path: Path, genome: str, val_size: int | None = None) -> dict:
    rows = json.loads(path.read_text())
    relevant = [row for row in rows if "/cc/cicada/" in str(row.get("file", ""))]
    if not relevant:
        raise ValueError("no Cicada compile commands")
    expected = {"tuned": TUNED_GENOME, "default": DEFAULT_GENOME,
                "best100": BEST100_GENOME}[genome]
    records = []
    for row in relevant:
        args = row.get("arguments") or shlex.split(row["command"])
        definitions = {}
        for arg in args:
            match = re.fullmatch(r"-D([A-Z_]+)=(\d+)", arg)
            if match:
                definitions[match.group(1)] = int(match.group(2))
        if any(definitions.get(axis) != value for axis, value in expected.items()):
            raise ValueError("Cicada compile definition differs from genome")
        if val_size is not None and definitions.get("VAL_SIZE") != val_size:
            raise ValueError("Cicada compile VAL_SIZE differs from build key")
        records.append({"file": row["file"], "definitions": {
            axis: definitions[axis] for axis in expected}})
    return {"genome": genome, "commands": records}


def select_conditions(value: str) -> tuple[str, ...]:
    ids = tuple(value.split(","))
    if not ids or any(not item or item.strip() != item for item in ids):
        raise ValueError("empty or malformed condition ID")
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate condition ID")
    unknown = set(ids) - set(CONDITIONS)
    if unknown:
        raise ValueError("unknown condition ID: " + ",".join(sorted(unknown)))
    return ids


def _nonnegative(value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("expected nonnegative integer")
    return value


def _vector(value: object, length: int) -> list[int]:
    if not isinstance(value, list) or len(value) != length:
        raise ValueError("vector length")
    return [_nonnegative(x) for x in value]


def parse_vlife_line(stdout: str) -> dict:
    lines = [line[len(PREFIX):] for line in stdout.splitlines()
             if line.startswith(PREFIX)]
    if len(lines) != 1:
        raise ValueError("missing or duplicate Cicada vlife JSON line")
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    payload = json.loads(lines[0], object_pairs_hook=unique_pairs)
    if not isinstance(payload, dict) or set(payload) not in ({
        "schema_version", "clocks_per_us", "bucket_bounds", "time_bucket_bounds",
        "position_origin", "sites", "build", "workers",
    }, {"schema_version", "clocks_per_us", "bucket_bounds", "time_bucket_bounds",
        "position_origin", "sites", "build", "workers", "hot_chains",
        "hot_scan_us"}):
        raise ValueError("schema fields")
    schema = _nonnegative(payload["schema_version"])
    if schema not in (1, 2, 3):
        raise ValueError("schema version")
    if (schema == 3) != ("hot_chains" in payload):
        raise ValueError("schema fields")
    if not _nonnegative(payload["clocks_per_us"]):
        raise ValueError("zero clock")
    if _vector(payload["bucket_bounds"], 18) != [
        0, 1, 2, 3, 4, 5, 6, 7, 8, 16, 32, 64, 128, 256, 512, 1024, 2048,
        18446744073709551615
    ]:
        raise ValueError("bucket bounds")
    if payload["sites"] != list(SITES):
        raise ValueError("site names")
    if _vector(payload["time_bucket_bounds"], 42) != TIME_BOUNDS:
        raise ValueError("time bucket bounds")
    if payload["position_origin"] != POSITION_ORIGIN:
        raise ValueError("position origin")
    build = payload["build"]
    build_fields = {"reuse_version", "inline_version_opt", "longtx"}
    if schema >= 2:
        build_fields |= {"izanagi_ronly_pct", "izanagi_long_kind"}
    if schema == 3:
        build_fields |= {"val_size", "sizeof_version", "sizeof_ycsb"}
    if not isinstance(build, dict) or set(build) != build_fields:
        raise ValueError("build fields")
    for field in ("reuse_version", "inline_version_opt", "longtx"):
        _nonnegative(build[field])
    if schema >= 2:
        if type(build["izanagi_ronly_pct"]) is not int or not -1 <= build["izanagi_ronly_pct"] <= 100:
            raise ValueError("read-only flag")
        if type(build["izanagi_long_kind"]) is not int or build["izanagi_long_kind"] not in (0, 1, 2):
            raise ValueError("long kind flag")
    if schema == 3:
        for field in ("val_size", "sizeof_version", "sizeof_ycsb"):
            if not _nonnegative(build[field]):
                raise ValueError("zero build size")
        chains = payload.get("hot_chains")
        if not isinstance(chains, list) or len(chains) != 8:
            raise ValueError("hot chain keys missing")
        for item in chains:
            if not isinstance(item, dict) or set(item) != {"key", "status", "length"}:
                raise ValueError("hot chain fields")
            if type(item["key"]) is not int or item["status"] not in ("ok", "missing", "error", "unavailable"):
                raise ValueError("hot chain status")
            if item["status"] == "ok":
                if not _nonnegative(item["length"]):
                    raise ValueError("zero hot chain length")
            elif item["length"] is not None:
                raise ValueError("unavailable hot chain length")
        if {item["key"] for item in chains} != set(range(8)):
            raise ValueError("hot chain keys duplicated or missing")
        _nonnegative(payload["hot_scan_us"])
    workers = payload["workers"]
    if not isinstance(workers, list) or not workers:
        raise ValueError("workers")
    scalars = {"readonly_attempt", "readonly_commit",
               "install", "detach", "gc_negative"}
    vectors = {"no_scan": 8, "deep": 5, "candidate": 5, "readonly_deep": 5,
               "deep_read_zero": 5, "candidate_read_zero": 5,
               "gc_boundary_us": 42, "gc_publish_us": 42,
               "age_create_us": 42, "age_overwrite_us": 42,
               "attempts": 2, "commits": 2, "aborts": 2,
               "operations": 2, "cycles": 2}
    if schema >= 2:
        scalars |= {"readonly_reads", "gc_boundary_sum_us", "gc_boundary_count",
                    "gc_publish_sum_us", "gc_publish_count", "gc_publish_negative",
                    "gc_boundary_overflow", "gc_publish_overflow",
                    "ro_snapshot_age_sum_us", "ro_snapshot_age_count",
                    "ro_snapshot_age_negative", "ro_snapshot_age_overflow", "gc_same",
                    "dc_cf_wait_sum_us", "dc_ro_gap_sum_us", "dc_leader_wait_sum_us",
                    "dc_interval_sum_us",
                    "dc_count", "dc_first", "dc_missing", "dc_generation",
                    "dc_negative", "dc_epoch_mismatch", "dc_late_epoch",
                    "dc_leader_count", "holder_count",
                    "holder_unresolved"}
        vectors.update(readonly_candidate=5, ro_snapshot_age_us=42,
                       dc_cf_kind_count=5, dc_cf_kind_sum_us=5, holder_units=5)
    if schema == 3:
        vectors["abort_reasons"] = 9 * 2
    for worker in workers:
        if not isinstance(worker, dict) or set(worker) != {
            "hops", "position", *scalars, *vectors
        }:
            raise ValueError("worker fields")
        for field in ("hops", "position"):
            if not isinstance(worker[field], list) or len(worker[field]) != len(SITES):
                raise ValueError("site vector")
            for row in worker[field]:
                _vector(row, 18)
        for field in scalars:
            _nonnegative(worker[field])
        for field, n in vectors.items():
            _vector(worker[field], n)
        if any(a > b for a, b in zip(worker["candidate"], worker["deep"])):
            raise ValueError("candidate exceeds deep")
        if any(a > b for a, b in zip(worker["deep_read_zero"], worker["deep"])):
            raise ValueError("zero-read exceeds deep")
        if any(a > b or a > c for a, b, c in zip(
            worker["candidate_read_zero"], worker["candidate"], worker["deep_read_zero"]
        )):
            raise ValueError("zero-read candidate exceeds denominator")
        if any(x > sum(worker["hops"][0]) for x in worker["deep"]):
            raise ValueError("deep exceeds update reads")
        if any(x > sum(worker["hops"][1]) for x in worker["readonly_deep"]):
            raise ValueError("read-only deep exceeds reads")
        if schema >= 2:
            if any(a > b for a, b in zip(worker["readonly_candidate"], worker["readonly_deep"])):
                raise ValueError("read-only candidate exceeds deep")
            if any(x > worker["readonly_reads"] for x in worker["readonly_deep"]):
                raise ValueError("read-only deep exceeds selected reads")
            for histogram, count in (("gc_boundary_us", "gc_boundary_count"),
                                     ("gc_publish_us", "gc_publish_count"),
                                     ("ro_snapshot_age_us", "ro_snapshot_age_count")):
                if sum(worker[histogram]) != worker[count]:
                    raise ValueError("histogram count mismatch")
            for total_field, count_field in (("gc_boundary_sum_us", "gc_boundary_count"),
                                             ("gc_publish_sum_us", "gc_publish_count"),
                                             ("ro_snapshot_age_sum_us", "ro_snapshot_age_count")):
                if worker[count_field] == 0 and worker[total_field] != 0:
                    raise ValueError("nonzero sum without observations")
            for histogram, total_field in (("gc_boundary_us", "gc_boundary_sum_us"),
                                           ("gc_publish_us", "gc_publish_sum_us"),
                                           ("ro_snapshot_age_us", "ro_snapshot_age_sum_us")):
                lower = sum(count * (0 if i == 0 else TIME_BOUNDS[i-1] + 1)
                            for i, count in enumerate(worker[histogram]))
                upper = sum(count * TIME_BOUNDS[i]
                            for i, count in enumerate(worker[histogram]))
                if not lower <= worker[total_field] <= upper:
                    raise ValueError("time histogram and exact sum disagree")
            if worker["dc_count"] == 0 and any(worker[field] for field in (
                "dc_cf_wait_sum_us", "dc_ro_gap_sum_us", "dc_leader_wait_sum_us",
                "dc_interval_sum_us")):
                raise ValueError("D-C sum without interval")
            if sum(worker["dc_cf_kind_count"]) != worker["dc_count"] or (
                sum(worker["dc_cf_kind_sum_us"]) != worker["dc_cf_wait_sum_us"]):
                raise ValueError("D-C kind sum mismatch")
            if sum(worker["holder_units"]) != 1000000 * worker["holder_count"]:
                raise ValueError("holder weight mismatch")
            if (worker["dc_cf_wait_sum_us"] + worker["dc_ro_gap_sum_us"] +
                worker["dc_leader_wait_sum_us"] != worker["dc_interval_sum_us"]):
                raise ValueError("D-C three terms do not restore interval")
            if worker["dc_count"] == worker["gc_publish_count"] and (
                worker["dc_interval_sum_us"] != worker["gc_publish_sum_us"]):
                raise ValueError("D-C valid intervals differ from all published intervals")
            if (worker["dc_cf_wait_sum_us"] + worker["dc_ro_gap_sum_us"] +
                worker["dc_leader_wait_sum_us"] > worker["gc_publish_sum_us"]):
                raise ValueError("D-C exceeds observed interval")
            publications = (worker["gc_boundary_count"] + worker["gc_negative"] +
                            worker["gc_boundary_overflow"])
            if worker["dc_first"] > 1 or worker["gc_same"] > publications:
                raise ValueError("publication count mismatch")
            if worker["dc_late_epoch"] > publications:
                raise ValueError("late epoch advances exceed publications")
            if worker["holder_count"] + worker["holder_unresolved"] > publications:
                raise ValueError("holder outcomes exceed publications")
            if (worker["dc_count"] + worker["dc_first"] + worker["dc_missing"] +
                worker["dc_generation"] + worker["dc_negative"] >
                publications):
                raise ValueError("D-C outcomes exceed publications")
        if schema == 3 and (sum(worker["abort_reasons"]) != sum(worker["aborts"])):
            raise ValueError("abort reason sum differs from aborts")
        if any(c + a > n for c, a, n in zip(
            worker["commits"], worker["aborts"], worker["attempts"]
        )):
            raise ValueError("transaction outcome exceeds attempts")
        if worker["readonly_commit"] > worker["readonly_attempt"]:
            raise ValueError("read-only commits exceed attempts")
    return payload


def summarize(payload: dict) -> dict:
    workers = payload["workers"]
    deep = [sum(w["deep"][i] for w in workers) for i in range(5)]
    candidate = [sum(w["candidate"][i] for w in workers) for i in range(5)]
    readonly = [sum(w["readonly_deep"][i] for w in workers) for i in range(5)]
    zero = [sum(w["deep_read_zero"][i] for w in workers) for i in range(5)]
    candidate_zero = [sum(w["candidate_read_zero"][i] for w in workers) for i in range(5)]
    result = {
        "deep": deep, "candidate": candidate, "readonly_deep": readonly,
        "deep_read_zero": zero, "candidate_read_zero": candidate_zero,
        "candidate_rate": [candidate[i]/deep[i] if deep[i] else None for i in range(5)],
        "logical_version_delta": sum(w["install"]-w["detach"] for w in workers),
        "readonly_attempts": sum(w["readonly_attempt"] for w in workers),
    }
    if payload["schema_version"] == 1:
        return result
    total = lambda field: sum(w[field] for w in workers)
    rate = lambda numerator, denominator: numerator / denominator if denominator else None
    readonly_reads = total("readonly_reads")
    ro_candidate = [sum(w["readonly_candidate"][i] for w in workers) for i in range(5)]
    holder_units = [sum(w["holder_units"][i] for w in workers) for i in range(5)]
    boundary_hist = [sum(w["gc_boundary_us"][i] for w in workers) for i in range(42)]
    boundary_total = sum(boundary_hist)
    boundary_p50 = None
    if boundary_total:
        cumulative = 0
        for i, count in enumerate(boundary_hist):
            cumulative += count
            if cumulative * 2 >= boundary_total:
                boundary_p50 = TIME_BOUNDS[i]
                break
    attempts = sum(sum(w["attempts"]) for w in workers)
    commits = sum(sum(w["commits"]) for w in workers)
    aborts = sum(sum(w["aborts"]) for w in workers)
    result.update(
        readonly_reads=readonly_reads,
        readonly_candidate=ro_candidate,
        readonly_deep_rate=[rate(value, readonly_reads) for value in readonly],
        readonly_share_of_deep=[rate(readonly[i], readonly[i] + deep[i]) for i in range(5)],
        readonly_candidate_rate=[rate(ro_candidate[i], readonly[i]) for i in range(5)],
        realized_readonly_attempt_rate=rate(total("readonly_attempt"), attempts),
        realized_readonly_commit_rate=rate(total("readonly_commit"), commits),
        commit_rate=rate(commits, attempts), abort_rate=rate(aborts, attempts),
        update_commits=commits-total("readonly_commit"),
        install=total("install"),
        gc_boundary_mean_us=rate(total("gc_boundary_sum_us"), total("gc_boundary_count")),
        gc_boundary_p50_bucket_us=boundary_p50,
        gc_publications=total("gc_boundary_count") + total("gc_negative") +
                        total("gc_boundary_overflow"),
        gc_publish_mean_us=rate(total("gc_publish_sum_us"), total("gc_publish_count")),
        ro_snapshot_age_mean_us=rate(total("ro_snapshot_age_sum_us"),
                                     total("ro_snapshot_age_count")),
        dc_cf_wait_mean_us=rate(total("dc_cf_wait_sum_us"), total("dc_count")),
        dc_ro_gap_mean_us=rate(total("dc_ro_gap_sum_us"), total("dc_count")),
        dc_leader_wait_mean_us=rate(total("dc_leader_wait_sum_us"), total("dc_count")),
        dc_epoch_mismatch=total("dc_epoch_mismatch"),
        dc_late_epoch=total("dc_late_epoch"),
        local_flag_opportunity=rate(total("dc_ro_gap_sum_us"), total("gc_publish_sum_us")),
        holder_fraction=[rate(value, 1000000 * total("holder_count")) for value in holder_units],
        holder_unresolved=total("holder_unresolved"),
        same_boundary_publications=total("gc_same"),
    )
    return result


def df_interaction(lag_r_long: float, lag_r_none: float,
                   lag_0_long: float, lag_0_none: float) -> float:
    """Condition total difference interaction, not a causal attribution."""
    return lag_r_long - lag_r_none - lag_0_long + lag_0_none


def depth_at_k(position: int, k: int) -> bool:
    if k not in K or position < 0:
        raise ValueError("position or K")
    return position >= k


def _checked(argv: list[str], *, cwd: Path | None = None, timeout: int = 900) -> subprocess.CompletedProcess:
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                            timeout=timeout, check=False)
    if result.returncode:
        error = RuntimeError(f"command failed rc={result.returncode}: {argv}: {result.stderr[-2000:]}")
        error.stderr = result.stderr
        raise error
    return result


def _gates(source: Path, macros: tuple[str, ...], args: list[str], cxx: str) -> list[dict]:
    records = []
    for macro in macros:
        captured = condition.capture_define_inputs(source, configure_args=tuple(args))
        request = condition.make_define_request(driver_id=DRIVER_ID, macro=macro,
                                                requested_value=1, default_value=0)
        with condition._configured_define_compile_commands(
            captured, request=request, cxx=cxx, cmake="cmake",
        ) as commands:
            supply = condition.evaluate_define_supply_effectuation(
                captured, request=request, cxx=cxx, cmake="cmake", configured_commands=commands)
            meaning = condition.evaluate_define_runtime_meaning(
                captured, request=request,
                declaration=condition.declare_define_runtime_meaning(request),
                cxx=cxx, cmake="cmake", configured_commands=commands)
        admission = condition.require_condition_gate_family(
            [supply], [meaning], use_class="raw-measurement")
        records.append({"macro": macro, "supply": json.loads(supply.canonical_json()),
                        "meaning": json.loads(meaning.canonical_json()),
                        "admission": json.loads(admission.canonical_json())})
        if not admission.admitted:
            raise RuntimeError(f"condition gate rejected {macro}: {records[-1]}")
    return records


def _build_variant(source: Path, build: Path, toolchain: dict, dependencies: dict,
                   macros: tuple[str, ...], genome: str = "default",
                   val_size: int | None = None) -> tuple[Path, dict]:
    started = time.monotonic()
    admission = non_admissible_materializer(MATERIALIZER)
    args = compute._common_configure_args(trace=0, toolchain=toolchain,
                                           dependencies=dependencies)
    args = [arg for arg in args if arg not in compute.STOCK_G.cmake_defines()]
    args += ["-DCMAKE_EXPORT_COMPILE_COMMANDS=ON"]
    args += genome_args(genome)
    if val_size is not None:
        args += [f"-DCCBENCH_VAL_SIZE={val_size}"]
    gates = _gates(source, macros, args, toolchain["cxx_path"]) if macros else []
    if macros:
        args += ["-DCMAKE_CXX_FLAGS=" + " ".join("-D" + m + "=1" for m in macros)]
    configure = ["cmake", "-S", str(source), "-B", str(build),
                 "-DCMAKE_CXX_COMPILER=" + toolchain["cxx_path"], *args]
    _checked(configure)
    genome_witness = verify_genome_commands(build / "compile_commands.json", genome, val_size)
    _checked(["cmake", "--build", str(build), "--target", "ycsb_cicada.exe"])
    binary = build / "cc/cicada/ycsb_cicada.exe"
    if not binary.is_file():
        raise RuntimeError("Cicada binary missing")
    return binary, {
        "admission": admission, "gates": gates, "configure": configure,
        "sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "macros": list(macros),
        "genome": genome_witness,
        **({"val_size": val_size} if val_size is not None else {}),
        "elapsed_s": time.monotonic() - started,
    }


def _validate_run_echo(parsed: dict, flags: dict, genome: str,
                       val_size: int | None) -> None:
    if len(parsed["workers"]) != flags["thread_num"] + flags["batch_th_num"]:
        raise ValueError("worker count differs from argv")
    if parsed["schema_version"] != (3 if val_size is not None else 2):
        raise ValueError("instrument schema differs from condition")
    if parsed["build"]["izanagi_ronly_pct"] != flags["izanagi_ronly_pct"] or (
        parsed["build"]["izanagi_long_kind"] != flags["izanagi_long_kind"]):
        raise ValueError("instrument flag echo differs from argv")
    if parsed["build"]["inline_version_opt"] != (1 if genome == "tuned" else 0):
        raise ValueError("instrument genome echo differs from build")
    if val_size is not None and parsed["build"]["val_size"] != val_size:
        raise ValueError("instrument VAL_SIZE echo differs from build key")
    if val_size is not None and parsed["build"]["reuse_version"] != (
        TUNED_GENOME if genome == "tuned" else BEST100_GENOME if genome == "best100"
        else DEFAULT_GENOME)["REUSE_VERSION"]:
        raise ValueError("instrument genome echo differs from build")


def _run(binary: Path, flags: dict, *, cwd: Path, instrumented: bool = True,
         genome: str = "default", val_size: int | None = None) -> dict:
    _assert_single_tenant()
    argv = [str(binary)] + [f"-{k}={v}" for k, v in flags.items()]
    started = time.monotonic()
    with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
        process = subprocess.Popen(argv, cwd=cwd, stdout=stdout_file, stderr=stderr_file)
        deadline = time.monotonic() + 180
        timed_out = False
        while True:
            pid, status, usage = os.wait4(process.pid, os.WNOHANG)
            if pid:
                break
            if time.monotonic() >= deadline:
                timed_out = True
                process.kill()
                _, status, usage = os.wait4(process.pid, 0)
                break
            time.sleep(.01)
        process.returncode = os.waitstatus_to_exitcode(status)
        stdout_file.seek(0)
        stderr_file.seek(0)
        stdout = stdout_file.read().decode("utf-8", errors="replace")
        stderr = stderr_file.read().decode("utf-8", errors="replace")
        maxrss_kb = usage.ru_maxrss
    if timed_out:
        return {"argv": argv, "rc": None, "timeout_s": 180,
                "wall_s": time.monotonic() - started,
                "stdout": stdout, "stderr": stderr, "maxrss_kb": maxrss_kb,
                **({"build_key": {"genome": genome, "val_size": val_size}}
                   if val_size is not None else {}),
                "vlife_json_line": None, "parsed": None,
                "parse_error": "timeout", "summary": None,
                "throughput_interpretation": "diagnostic, not performance"}
    parsed = None
    parse_error = None
    if process.returncode == 0 and instrumented:
        try:
            parsed = parse_vlife_line(stdout)
            _validate_run_echo(parsed, flags, genome, val_size)
        except ValueError as exc:
            parse_error = str(exc)
    summary = summarize(parsed) if parsed else None
    if summary:
        summary["logical_live_versions"] = flags["tuple_num"] + summary["logical_version_delta"]
        if parsed["schema_version"] >= 2:
            summary["update_commits_per_s"] = summary["update_commits"] / flags["extime"]
            summary["install_per_s"] = summary["install"] / flags["extime"]
    return {"argv": argv, "rc": process.returncode, "stdout": stdout,
            "wall_s": time.monotonic() - started,
            "stderr": stderr, "maxrss_kb": maxrss_kb, "vlife_json_line": next(
                (line for line in stdout.splitlines() if line.startswith(PREFIX)), None),
            **({"build_key": {"genome": genome, "val_size": val_size}}
               if val_size is not None else {}),
            "parsed": parsed, "parse_error": parse_error,
            "summary": summary,
            "throughput_interpretation": "diagnostic, not performance"}


def _flags(condition_id: str, records: int, clocks_per_us: int) -> dict:
    condition = CONDITIONS[condition_id]
    if condition_id.startswith("W"):
        records = condition["records"]
    return {"tuple_num": records, "ycsb_tuple_num": records,
            "thread_num": CONDITIONS[condition_id]["thread_num"],
            "batch_th_num": CONDITIONS[condition_id]["batch_th_num"],
            "batch_max_ope": condition["batch_max_ope"] if condition_id.startswith("W") else 1000,
            "max_ope": condition["ycsb_max_ope"] if condition_id.startswith("W") else 10,
            "ycsb_max_ope": condition["ycsb_max_ope"] if condition_id.startswith("W") else 10,
            "rratio": CONDITIONS[condition_id]["ycsb_rratio"],
            "ycsb_rratio": CONDITIONS[condition_id]["ycsb_rratio"],
            "zipf_skew": CONDITIONS[condition_id]["ycsb_zipf_skew"],
            "ycsb_zipf_skew": CONDITIONS[condition_id]["ycsb_zipf_skew"],
            "gc_inter_us": CONDITIONS[condition_id]["gc_inter_us"],
            "worker1_insert_delay_rphase_us":
                CONDITIONS[condition_id]["worker1_insert_delay_rphase_us"],
            "extime": 3, "clocks_per_us": clocks_per_us,
            "izanagi_ronly_pct": condition.get("izanagi_ronly_pct", -1),
            "izanagi_long_kind": condition.get("izanagi_long_kind", 0),
            **({"izanagi_vlife_schema": 3} if condition_id.startswith("W") else {})}


def _normalized_disassembly(binary: Path) -> str:
    output = _checked(["objdump", "-d", str(binary)]).stdout
    output = re.sub(r"(?m)^.*: +file format .*$", "", output)
    output = re.sub(r"(?m)^ *[0-9a-f]+:", "ADDR:", output)
    output = re.sub(r"(?m)^([0-9a-f]+) <", "ADDR <", output)
    return output


def _normalized_rodata(binary: Path) -> str:
    output = _checked(["objdump", "-s", "-j", ".rodata", str(binary)]).stdout
    output = re.sub(r"(?m)^.*: +file format .*$", "", output)
    return re.sub(r"(?m)^ *[0-9a-f]+ +", "ADDR ", output)


def _smoke_records(path: Path) -> int:
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict) or raw.get("command") != "smoke" or raw.get("schema_version") != 1:
        raise ValueError("smoke JSON required")
    if "error" in raw:
        raise ValueError("failed smoke JSON")
    if raw.get("ccbench_commit") != PIN or raw.get("patch_sha256") != hashlib.sha256(PATCH.read_bytes()).hexdigest():
        raise ValueError("smoke build identity mismatch")
    witness = raw.get("witness")
    if not isinstance(witness, dict) or any(
        witness.get(key) is not True for key in
        ("normalized_objdump_equal", "normalized_rodata_equal")
    ) or any(
        not isinstance(witness.get(side), dict) or
        witness[side].get("nm") is not True or
        not isinstance(witness[side].get("strings"), list) or
        any(type(item) is not str for item in witness[side]["strings"])
        for side in ("stock_absence", "default_absence")
    ) or witness["stock_absence"]["strings"] != witness["default_absence"]["strings"]:
        raise ValueError("smoke binary witness failed")
    for name, inline in (("short_run", 0), ("tuned_short_run", 1)):
        short = raw.get(name)
        if (not isinstance(short, dict) or type(short.get("rc")) is not int or
            short["rc"] != 0 or not isinstance(short.get("parsed"), dict) or
            short["parsed"].get("schema_version") != 2 or
            short["parsed"].get("build", {}).get("inline_version_opt") != inline):
            raise ValueError(f"{name} failed")
    budget = raw.get("time_budget")
    if (not isinstance(budget, dict) or type(budget.get("estimated_node_s")) not in (int, float)
        or not math.isfinite(budget["estimated_node_s"]) or
        budget["estimated_node_s"] >= 7200):
        raise ValueError("new smoke exceeds two node hours or lacks estimate")
    calibration = raw.get("calibration")
    if not isinstance(calibration, dict):
        raise ValueError("smoke calibration missing")
    l3_bytes = calibration.get("l3_bytes")
    if type(l3_bytes) not in (int, float) or not math.isfinite(l3_bytes) or l3_bytes <= 0:
        raise ValueError("invalid L3 size")
    probes = calibration.get("probes")
    if not isinstance(probes, dict) or set(probes) != {"1000000", "2000000", "4000000"}:
        raise ValueError("incomplete calibration probes")
    for probe in probes.values():
        if not isinstance(probe, dict) or type(probe.get("rc")) is not int or probe["rc"] != 0 or type(probe.get("maxrss_kb")) is not int or probe["maxrss_kb"] <= 0:
            raise ValueError("failed calibration probe")
    expected = MEASURE_RECORDS
    records = calibration.get("selected_records")
    if type(records) is not int or records != expected:
        raise ValueError("measure requires 1M records")
    if probes[str(MEASURE_RECORDS)]["maxrss_kb"] * 1024 < 4 * l3_bytes:
        raise ValueError("1M records do not meet four times L3")
    return records


def _absence(binary: Path) -> dict:
    outputs = {tool: _checked([tool, "-C", str(binary)] if tool == "nm"
                              else [tool, "-a", str(binary)]).stdout
               for tool in ("nm", "strings")}
    return {
        "nm": not re.search(r"izanagi|IZANAGI_", outputs["nm"]),
        "strings": sorted(set(re.findall(r"(?m)^.*(?:izanagi|IZANAGI_).*$",
                                         outputs["strings"]))),
    }


def _delay_compile(source: Path, build: Path) -> dict:
    commands = json.loads((build / "compile_commands.json").read_text())
    def target_output(row: dict) -> bool:
        args = row.get("arguments") or shlex.split(row["command"])
        outputs = [row.get("output", "")]
        outputs += [args[i + 1] for i, arg in enumerate(args[:-1]) if arg == "-o"]
        outputs += [arg[2:] for arg in args if arg.startswith("-o") and arg != "-o"]
        return any("ycsb_cicada" in str(output) for output in outputs)

    rows = [row for row in commands
            if str(row["file"]).endswith("/cc/cicada/transaction.cc")
            and target_output(row)]
    if len(rows) != 1:
        raise RuntimeError("Cicada transaction compile command not unique")
    row = rows[0]
    args = row.get("arguments") or shlex.split(row["command"])
    stripped = []
    skip = False
    for arg in args:
        if skip:
            skip = False
            continue
        if arg == "-o":
            skip = True
            continue
        if arg == "-c":
            continue
        if arg.startswith("-DWORKER1_INSERT_DELAY_RPHASE="):
            continue
        stripped.append(arg)
    stripped += ["-fsyntax-only", "-DWORKER1_INSERT_DELAY_RPHASE=1"]
    result = subprocess.run(stripped, cwd=row["directory"], capture_output=True,
                            text=True, timeout=180, check=False)
    return {"argv": stripped, "rc": result.returncode,
            "stdout": result.stdout, "stderr": result.stderr}


def _calibrate(stock_binary: Path, scratch: Path) -> dict:
    cpu = _checked(["lscpu", "-J"]).stdout
    rows = json.loads(cpu).get("lscpu", [])
    l3 = next((row["data"] for row in rows
               if row.get("field", "").strip(":") == "L3 cache"), None)
    result = {"lscpu_json": cpu, "l3": l3, "probes": {}}
    for records in (1000000, 2000000, 4000000):
        _assert_single_tenant()
        flags = _flags("A-none-gc10", records, locks.CLK)
        flags.pop("izanagi_ronly_pct")
        flags.pop("izanagi_long_kind")
        flags.update(rratio=100, ycsb_rratio=100, extime=1)
        argv = ["/usr/bin/time", "-f", "IZANAGI_MAXRSS_KB %M",
                str(stock_binary)] + [f"-{k}={v}" for k, v in flags.items()]
        run = subprocess.run(argv, cwd=scratch, capture_output=True, text=True,
                             timeout=180, check=False)
        match = re.search(r"IZANAGI_MAXRSS_KB (\d+)", run.stderr)
        result["probes"][str(records)] = {
            "argv": argv, "rc": run.returncode, "stdout": run.stdout,
            "stderr": run.stderr, "maxrss_kb": int(match.group(1)) if match else None,
        }
    if l3 is None:
        raise RuntimeError("lscpu did not report L3")
    match = re.match(r"([0-9.]+)\s*([KMG]i?B)", l3)
    if match is None:
        raise RuntimeError("unrecognized L3 size: " + l3)
    l3_bytes = float(match.group(1)) * {
        "KB": 1000, "MB": 1000000, "GB": 1000000000,
        "KiB": 1024, "MiB": 1024**2, "GiB": 1024**3,
    }[match.group(2)]
    result["l3_bytes"] = l3_bytes
    result["selected_records"] = MEASURE_RECORDS
    result["selection_reason"] = "D15 second baseline: fixed 1M; require maxrss >= 4x L3"
    return result


def _stage_error(exc: Exception) -> dict:
    stderr = getattr(exc, "stderr", "")
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    return {"error": type(exc).__name__ + ": " + str(exc),
            "stderr_tail": (stderr or "")[-2000:]}


def _smoke(scratch: Path, toolchain: dict, dependencies: dict,
           result: dict | None = None) -> dict:
    result = {} if result is None else result
    builds = result.setdefault("builds", {})
    binaries = {}

    def stage(key: str, action, *, container: dict = result, valid=None):
        try:
            value = action()
            if valid is not None and not valid(value):
                container[key] = {**value, **_stage_error(
                    RuntimeError(f"{key} did not succeed"))}
                container[key]["stderr_tail"] = str(value.get("stderr", ""))[-2000:]
                return None
            container[key] = value
            return value
        except Exception as exc:
            container[key] = _stage_error(exc)
            return None

    def build(name: str, macros: tuple[str, ...], genome: str = "default"):
        value = stage(name, lambda: _build_variant(
            source, scratch / f"{name}-build", toolchain, dependencies, macros, genome),
            container=builds)
        if value is not None:
            binaries[name], builds[name] = value

    def skipped(key: str, reason: str):
        result[key] = {"error": "DependencyError: " + reason, "stderr_tail": ""}

    with checkout(PIN, base_dir=str(ROOT / "external/ccbench")) as path:
        source = Path(path)
        build("stock", ())
        if "stock" in binaries:
            stage("delay_compile", lambda: _delay_compile(source, scratch / "stock-build"),
                  valid=lambda value: isinstance(value, dict)
                  and type(value.get("rc")) is int
                  and type(value.get("stdout")) is str
                  and type(value.get("stderr")) is str)
        else:
            skipped("delay_compile", "stock build failed")
        try:
            with applied(str(PATCH), PIN, str(source)):
                build("default", ())
                build("enabled", MACROS)
                build("tuned_enabled", MACROS, "tuned")
        except Exception as exc:
            for name in ("default", "enabled", "tuned_enabled"):
                builds.setdefault(name, _stage_error(exc))

    def witness():
        stock_text = _normalized_disassembly(binaries["stock"])
        default_text = _normalized_disassembly(binaries["default"])
        stock_rodata = _normalized_rodata(binaries["stock"])
        default_rodata = _normalized_rodata(binaries["default"])
        return {
            "normalized_objdump_equal": stock_text == default_text,
            "stock_objdump_sha256": hashlib.sha256(stock_text.encode()).hexdigest(),
            "default_objdump_sha256": hashlib.sha256(default_text.encode()).hexdigest(),
            "normalized_rodata_equal": stock_rodata == default_rodata,
            "stock_rodata_sha256": hashlib.sha256(stock_rodata.encode()).hexdigest(),
            "default_rodata_sha256": hashlib.sha256(default_rodata.encode()).hexdigest(),
            "stock_absence": _absence(binaries["stock"]),
            "default_absence": _absence(binaries["default"]),
        }

    if "stock" in binaries and "default" in binaries:
        stage("witness", witness, valid=lambda value:
              value["normalized_objdump_equal"] and value["normalized_rodata_equal"]
              and value["stock_absence"]["nm"]
              and value["default_absence"]["nm"]
              and value["stock_absence"]["strings"] ==
                  value["default_absence"]["strings"])
    else:
        skipped("witness", "stock or default build failed")
    if "stock" in binaries:
        stage("calibration", lambda: _calibrate(binaries["stock"], scratch),
              valid=lambda value: all(
                  probe["rc"] == 0 and probe["maxrss_kb"] is not None
                  for probe in value["probes"].values())
              and value["probes"][str(MEASURE_RECORDS)]["maxrss_kb"] * 1024
                  >= 4 * value["l3_bytes"])
    else:
        skipped("calibration", "stock build failed")
    if "enabled" in binaries and "error" not in result["calibration"]:
        def short_run():
            flags = _flags("A-none-gc10", MEASURE_RECORDS, locks.CLK)
            return _run(binaries["enabled"], flags, cwd=scratch)
        stage("short_run", short_run,
              valid=lambda value: value["rc"] == 0 and value["parsed"] is not None)
    else:
        skipped("short_run", "enabled build or calibration failed")
    if "tuned_enabled" in binaries and "error" not in result["calibration"]:
        def tuned_short_run():
            flags = _flags("T50-none-gc10", MEASURE_RECORDS, locks.CLK)
            return _run(binaries["tuned_enabled"], flags, cwd=scratch, genome="tuned")
        stage("tuned_short_run", tuned_short_run,
              valid=lambda value: value["rc"] == 0 and value["parsed"] is not None)
    else:
        skipped("tuned_short_run", "tuned build or calibration failed")
    if all(name in builds and "error" not in builds[name] for name in ("enabled", "tuned_enabled")) and all(
        name in result and "error" not in result[name] for name in ("short_run", "tuned_short_run")
    ):
        times = [builds[name].get("elapsed_s") for name in
                 ("stock", "default", "enabled", "tuned_enabled")]
        times += [result[name].get("wall_s") for name in ("short_run", "tuned_short_run")]
        preparation = result.get("dependency_preparation_s")
        if preparation is None:
            preparation = dependencies.get("elapsed_s")
        if all(type(x) in (int, float) and math.isfinite(x) and x > 0 for x in times):
            # Four jobs each build stock/default/enabled/tuned and prepare dependencies.
            if type(preparation) not in (int, float) or not math.isfinite(preparation) or preparation < 0:
                preparation = 0
            estimate = 258 * max(times[4:]) + 4 * (sum(times[:4]) + preparation)
            result["time_budget"] = {"estimated_node_s": estimate,
                                     "limit_node_s": 7200,
                                     "method": "258*max(3s run wall)+4*(all four build walls+dependency preparation)",
                                     "dependency_preparation_s": preparation}
        else:
            result["time_budget"] = _stage_error(ValueError("smoke timing missing"))
    else:
        skipped("time_budget", "instrumented build or short run failed")
    return result


def _smoke_success(body: dict) -> bool:
    return (all(name in body.get("builds", {}) and
                "error" not in body["builds"][name]
                for name in ("stock", "default", "enabled", "tuned_enabled"))
            and all(key in body and "error" not in body[key]
                    for key in ("delay_compile", "witness", "calibration", "short_run", "tuned_short_run", "time_budget"))
            and body["time_budget"]["estimated_node_s"] < 7200)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("smoke", "measure"))
    parser.add_argument("--third-party-cache", type=Path, required=True)
    parser.add_argument("--policy", type=Path,
                        default=ROOT / "tools/pegasus/mocc_trace_v1_policy.json")
    parser.add_argument("--conditions", default="A-none-gc10")
    parser.add_argument("--smoke-json", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "measure" and args.smoke_json is None:
        parser.error("measure requires --smoke-json")
    if args.out.exists():
        raise FileExistsError(args.out)
    result = {"schema_version": 1, "command": args.command,
              "ccbench_commit": PIN, "patch_sha256": hashlib.sha256(PATCH.read_bytes()).hexdigest(),
              "throughput_interpretation": "diagnostic, not performance"}
    try:
        site = site_policy.current_site(require_evidence=True)
        result["site"] = site
        if site_policy.refuses_heavy_work(site):
            print(site_policy.heavy_work_refusal(site, "Cicada lifetime diagnostics"), file=sys.stderr)
            return 2
        ids = select_conditions(args.conditions)
        records = _smoke_records(args.smoke_json) if args.command == "measure" else None
        _assert_single_tenant()
        policy = compute._load_policy(args.policy.resolve(strict=True))
        toolchain = compute._resolve_toolchain(policy)
        result["toolchain"] = toolchain
        with tempfile.TemporaryDirectory(prefix="cicada-vlife-") as td:
            scratch = Path(td)
            preparation_started = time.monotonic()
            dependencies = compute._prepare_dependencies(
                ROOT, policy, args.third_party_cache.resolve(strict=True), scratch, toolchain)
            if args.command == "smoke":
                result["dependency_preparation_s"] = time.monotonic() - preparation_started
                _smoke(scratch, toolchain, dependencies, result)
            else:
                with checkout(PIN, base_dir=str(ROOT / "external/ccbench")) as stock_path:
                    # Stock build prepares Masstree artifacts used by the enabled build.
                    _, dependency_stock_build = _build_variant(
                        Path(stock_path), scratch / "dependency-stock-build",
                        toolchain, dependencies, ())
                with checkout(PIN, base_dir=str(ROOT / "external/ccbench")) as path:
                    source = Path(path)
                    with applied(str(PATCH), PIN, str(source)):
                        builds = {}
                        runs = {}
                        keys = {(CONDITIONS[id_].get("genome", "default"),
                                 CONDITIONS[id_].get("val_size")) for id_ in ids}
                        for genome, val_size in sorted(keys, key=lambda key: (key[0], key[1] or 0)):
                            build_name = genome if val_size is None else f"{genome}-v{val_size}"
                            if val_size is None:
                                binary, builds[build_name] = _build_variant(
                                    source, scratch / f"build-{genome}", toolchain,
                                    dependencies, MACROS, genome)
                            else:
                                binary, builds[build_name] = _build_variant(
                                    source, scratch / f"build-{build_name}", toolchain,
                                    dependencies, MACROS, genome, val_size=val_size)
                            for id_ in ids:
                                if ((CONDITIONS[id_].get("genome", "default"),
                                     CONDITIONS[id_].get("val_size")) == (genome, val_size)):
                                    runs[id_] = [
                                        _run(binary, _flags(id_, records, locks.CLK), cwd=scratch,
                                             genome=genome, **({"val_size": val_size} if val_size is not None else {}))
                                        for _ in range(2 if val_size is not None else 3)]
                result.update({"dependency_stock_build": dependency_stock_build,
                               "builds": builds, "runs": runs,
                               "conditions": {id_: CONDITIONS[id_] for id_ in ids},
                               "records": records})
    except Exception as exc:
        result.update(_stage_error(exc))
    if args.command == "smoke" and "error" not in result and not _smoke_success(result):
        result["error"] = "RuntimeError: smoke stage failed"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    if args.command == "smoke":
        good = "error" not in result and _smoke_success(result)
    else:
        good = "error" not in result and all(
            run["rc"] == 0 and run["parsed"] is not None
            for reps in result["runs"].values() for run in reps)
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
