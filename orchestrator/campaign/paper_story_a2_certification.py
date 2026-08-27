#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paper-story A-2 exact-workload certification protocol.

The module deliberately keeps the experiment values in the adjacent versioned
policy.  Code here validates bindings, collects one create-only outer attempt,
publishes a bounded tracked result, and exposes the exact qsub primitive used by
the login-side fan-out submitter.
"""
from __future__ import annotations

import argparse
import base64
import ctypes
import errno
import hashlib
import json
import math
import os
import re
import shlex
import shutil
import socket
import stat
import statistics
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterable, Mapping, Optional, Sequence

from ..scheduler_nqsv import (
    QSTAT_REQUEST_ID_RE,
    target_bound_qstat_state_result,
)
from . import buildcache
from .pipeline import PerfConfig


POLICY_SCHEMA = "paper-story-a2-certification-policy/v2"
RAW_RESULT_SCHEMA = "paper-story-a2-cell-result/v2"
CERTIFICATION_SCHEMA = "paper-story-a2-certification-result/v3"
SUBMISSION_SCHEMA = "paper-story-a2-submission-receipt/v4"
COMPLETION_SCHEMA = "paper-story-a2-completion-receipt/v3"
ACQUISITION_SCHEMA = "paper-story-a2-acquisition-receipt/v3"
TRACE0_SCHEMA = "paper-story-a2-trace0-evidence/v2"
RAW_MANIFEST_SCHEMA = "paper-story-a2-raw-manifest/v3"
COMPUTE_RESULT_SCHEMA = "paper-story-a2-compute-result/v2"
RESERVATION_RESULT_SCHEMA = "paper-story-a2-reservation-result/v1"
COMPLETE_MARKER_SCHEMA = "paper-story-a2-materialization-complete/v1"
POLICY_PATH = Path(__file__).with_suffix(".v2.json")
VERIFY_MODE = "legacy+performance"
PERFORMANCE_TAG = "performance"
LEGACY_TAG = "legacy"
COMPILE_OUT_SCOPE = (
    "source-routed evidence; artifact hashes are not standalone compile-out proof"
)

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_COMMIT_RE = re.compile(r"[0-9a-f]{7,64}")
_ATTEMPT_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}")
_REQUEST_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]*")
_QSUB_REQUEST_RE = re.compile(r"Request[ \t]+(\S+)[ \t]+submitted")
_COMPUTE_HOST_RE = re.compile(r"bnode[0-9]+(?:[.].*)?")
_NQSV_REQUEST_RE = re.compile(r"(?m)^[ \t]*Request ID:[ \t]*(\S+)[ \t]*$")
_NQSV_GROUP_RE = re.compile(r"(?m)^[ \t]*Group Name:[ \t]*(\S+)[ \t]*$")
_NQSV_STARTED_RE = re.compile(r"(?m)^[ \t]*Started Request Time:[ \t]*\S.*$")
_NQSV_ENDED_RE = re.compile(r"(?m)^[ \t]*Ended Request Time:[ \t]*\S.*$")
_NQSV_ELAPSE_RE = re.compile(r"(?m)^[ \t]*Elapse:[ \t]*\S.*$")
_NQSV_ENDED_REQUEST_TIME_RE = re.compile(
    r"(?im)^[ \t]*Ended[ \t]+Request[ \t]+Time[ \t]*=[ \t]*(.*?)"
    r"[ \t]*$"
)
_NQSV_DISAPPEARED_RE = re.compile(
    r"[ \t]*Batch[ \t]+Request:[ \t]+(\S+)[ \t]+does[ \t]+not[ \t]+"
    r"exist[ \t]+on[ \t]+nqsv\.[ \t]*(?:\r?\n)?"
)
_UTC_OBSERVATION_RE = re.compile(
    r"[0-9]{4}-(?:0[1-9]|1[0-2])-"
    r"(?:0[1-9]|[12][0-9]|3[01])T"
    r"(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]Z"
)
_TERMINAL_STATE_RE = re.compile(
    r"(?im)^[ \t]*(?:Request[ \t]+State|State)[ \t]*=[ \t]*EXT[ \t]*$"
    r"|^[ \t]*Current[ \t]+State[ \t]*=[ \t]*"
    r"(?:completed|finished|ended|exited|terminated|exiting|post-running)[ \t]*$"
)
_TOP_LEVEL_KEYS = {
    "schema_version", "study", "historical_reference",
    "durable_measurement_base", "tracked_destination", "performance_common",
    "legacy_correctness", "workloads", "controlled_define_base", "cells",
    "trace0_cmake_argv", "certification_composition", "scheduler",
}
_CERTIFICATION_COMPOSITION = {
    "campaign_unit": (
        "one independently environment-contracted campaign per workload"),
    "outer_certification": "logical conjunction in policy workload order",
}
_PERFORMANCE_KEYS = {
    "records", "threads", "skew", "rmw", "max_ope", "extime", "reps",
    "base", "wal", "ccbench_protocol",
}
_WORKLOAD_KEYS = {"id", "label", "rratio", "adopted_backoff_us"}
_CELL_KEYS = {"id", "workload", "role", "genome"}
_GENOME_KEYS = {"BACK_OFF", "BACKOFF_FIXED"}
_TRACE0_CMAKE_ARGV_KEYS = {"configure", "build"}
_TRACE0_CONFIGURE_ARGV_KEYS = {
    "source_option", "build_directory_option", "fixed_arguments",
    "toolchain_arguments", "dependency_prefix_argument",
    "controlled_define_argument",
}
_TRACE0_TOOLCHAIN_ARGUMENT_KEYS = {"role", "prefix"}
_TRACE0_BUILD_ARGV_KEYS = {
    "subcommand", "target_option", "target_prefix", "target_suffix",
    "jobs_option",
}
_CONTROLLED_BASE_KEYS = {
    "CCBENCH_NO_WAIT_LOCKING_IN_VALIDATION",
    "CCBENCH_NO_WAIT_OF_TICTOC",
    "CCBENCH_WAL",
    "CCBENCH_BACKOFF_NOINLINE",
    "CCBENCH_TRACE",
}
_PERF_WORKLOAD_KEYS = {
    "ycsb_zipf_skew", "ycsb_rratio", "ycsb_rmw", "ycsb_max_ope",
}
_QSUB_ENV_KEYS = {
    "IZANAGI_A2_ATTEMPT_ROOT",
    "IZANAGI_A2_WORKLOAD",
    "IZANAGI_A2_EXPECTED_HEAD",
    "IZANAGI_A2_CURRENT_PIN",
    "IZANAGI_A2_CCBENCH_ROOT",
    "IZANAGI_A2_REPO_ROOT",
    "IZANAGI_A2_DEPENDENCY_PREFIX_SOURCE",
}
_RESERVATION_ENV_KEYS = {
    "IZANAGI_RESERVATION_JOB_ID",
    "IZANAGI_RESERVATION_REQUESTED_S",
    "IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH",
    "IZANAGI_RESERVATION_DEADLINE_EPOCH",
    "IZANAGI_RESERVATION_HOST",
    "IZANAGI_RESERVATION_BOOT_ID",
    "IZANAGI_RESERVATION_SCRIPT_SHA256",
    "IZANAGI_RESERVATION_NONCE",
}
_RESULT_LIMIT = 2 * 1024 * 1024
_QSUB_JOB_NAME = "paper-a2-cert"
_SUBMISSION_VISIBLE_STATES = frozenset({"QUE", "RUN"})
_COLLECT_TEST_TOKEN = object()


class CertificationError(RuntimeError):
    """Evidence is incomplete or inconsistent and cannot certify A-2."""


@dataclass(frozen=True)
class CellSpec:
    cell_id: str
    workload_id: str
    workload_label: str
    role: str
    genome: Mapping[str, int]
    perf: Mapping[str, Any]


@dataclass(frozen=True)
class Policy:
    path: Path
    document: Mapping[str, Any]
    raw_bytes: bytes
    bytes_sha256: str
    protocol_sha256: str
    cells: tuple[CellSpec, ...]

    @property
    def study(self) -> str:
        return str(self.document["study"])

    @property
    def durable_base(self) -> Path:
        return Path(str(self.document["durable_measurement_base"]))

    @property
    def tracked_destination(self) -> Path:
        return Path(str(self.document["tracked_destination"])
                    )

    def cell(self, cell_id: str) -> CellSpec:
        matches = [cell for cell in self.cells if cell.cell_id == cell_id]
        if len(matches) != 1:
            raise CertificationError(f"unknown cell: {cell_id!r}")
        return matches[0]


def _canonical_json(value: object) -> bytes:
    try:
        text = json.dumps(
            value, ensure_ascii=True, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise CertificationError("value is not finite canonical JSON") from exc
    return (text + "\n").encode("utf-8")


def _reject_json_constant(value: str) -> None:
    raise CertificationError(f"non-finite JSON constant is not allowed: {value}")


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise CertificationError(f"duplicate JSON key is not allowed: {key!r}")
        value[key] = item
    return value


def _loads_json(raw: bytes, label: str) -> Any:
    try:
        return json.loads(
            raw.decode("utf-8"),
            parse_constant=_reject_json_constant,
            object_pairs_hook=_reject_duplicate_json_keys,
        )
    except CertificationError:
        raise
    except (UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise CertificationError(f"cannot parse JSON for {label}: {exc}") from exc


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
    except OSError as exc:
        raise CertificationError(f"cannot hash file: {path}: {exc}") from exc
    return digest.hexdigest()


def _exact_keys(value: object, expected: set[str], label: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        raise CertificationError(f"{label} must be an exact JSON object")
    if set(value) != expected:
        raise CertificationError(
            f"{label} keys mismatch: missing={sorted(expected - set(value))}, "
            f"extra={sorted(set(value) - expected)}"
        )
    return value


def _positive_int(value: object, label: str) -> int:
    if type(value) is not int or value <= 0:
        raise CertificationError(f"{label} must be a positive exact integer")
    return value


def _protocol_preimage(document: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        "schema_version": document["schema_version"],
        "study": document["study"],
        "performance_common": document["performance_common"],
        "legacy_correctness": document["legacy_correctness"],
        "workloads": document["workloads"],
        "controlled_define_base": document["controlled_define_base"],
        "cells": document["cells"],
        "trace0_cmake_argv": document["trace0_cmake_argv"],
        "certification_composition": document["certification_composition"],
    }


def load_policy(path: Path | str = POLICY_PATH) -> Policy:
    policy_path = Path(path)
    if policy_path.is_symlink() or not policy_path.is_file():
        raise CertificationError(f"policy is not a regular file: {policy_path}")
    try:
        raw = policy_path.read_bytes()
        document = _loads_json(raw, "policy")
    except (OSError, CertificationError) as exc:
        raise CertificationError(f"cannot read policy: {policy_path}: {exc}") from exc
    document = _exact_keys(document, _TOP_LEVEL_KEYS, "policy")
    if document["schema_version"] != POLICY_SCHEMA:
        raise CertificationError("unsupported policy schema")
    if document["certification_composition"] != _CERTIFICATION_COMPOSITION:
        raise CertificationError(
            "certification composition is not the workload conjunction")
    if type(document["study"]) is not str or not document["study"]:
        raise CertificationError("policy study must be nonempty")
    historical = _exact_keys(
        document["historical_reference"], {"ccbench_commit", "role"},
        "historical_reference",
    )
    if (type(historical["ccbench_commit"]) is not str
            or _COMMIT_RE.fullmatch(historical["ccbench_commit"]) is None):
        raise CertificationError("historical campaign reference is malformed")
    if "never a current comparison value" not in historical["role"]:
        raise CertificationError("historical pin role is not reference-only")
    durable = Path(str(document["durable_measurement_base"]))
    if not durable.is_absolute():
        raise CertificationError("durable measurement base must be absolute")
    if os.path.normpath(str(durable)) != str(durable):
        raise CertificationError("durable measurement base must be a lexical canonical path")
    tracked = Path(str(document["tracked_destination"]))
    if tracked.is_absolute() or ".." in tracked.parts:
        raise CertificationError("tracked destination must be a bounded relative path")
    scheduler = _exact_keys(
        document["scheduler"], {"project", "queue", "nodes", "walltime", "job_body"},
        "scheduler",
    )
    if (not all(type(scheduler[key]) is str and scheduler[key]
                for key in ("project", "queue", "walltime", "job_body"))
            or type(scheduler["nodes"]) is not int or scheduler["nodes"] <= 0
            or re.fullmatch(r"[0-9]{2}:[0-9]{2}:[0-9]{2}",
                            scheduler["walltime"]) is None):
        raise CertificationError("scheduler policy is malformed")
    job_body = Path(scheduler["job_body"])
    if job_body.is_absolute() or ".." in job_body.parts:
        raise CertificationError("scheduler job body must be a bounded relative path")

    common = _exact_keys(
        document["performance_common"], _PERFORMANCE_KEYS,
        "performance_common",
    )
    for key in ("records", "threads", "extime", "reps"):
        _positive_int(common[key], f"performance_common.{key}")
    if (common["wal"] != 0 or common["base"] != "L-W0"):
        raise CertificationError("policy must use L-W0 with WAL disabled")
    if common["ccbench_protocol"] != "silo":
        raise CertificationError(
            "performance_common.ccbench_protocol must be exact lowercase silo")
    for key in ("skew", "rmw", "max_ope"):
        if type(common[key]) is not str or not common[key]:
            raise CertificationError(f"performance_common.{key} must be a string")
    legacy = document["legacy_correctness"]
    if type(legacy) is not dict or set(legacy) != {
        "ycsb_tuple_num", "thread_num", "ycsb_zipf_skew", "ycsb_rratio",
        "ycsb_rmw", "ycsb_max_ope", "extime",
    } or not all(type(value) is str and value for value in legacy.values()):
        raise CertificationError("legacy correctness flags are not exact")

    controlled = _exact_keys(
        document["controlled_define_base"], _CONTROLLED_BASE_KEYS,
        "controlled_define_base",
    )
    if not all(type(value) is str for value in controlled.values()):
        raise CertificationError("controlled define values must be strings")
    if (controlled["CCBENCH_WAL"] != str(common["wal"])
            or controlled["CCBENCH_TRACE"] != "0"):
        raise CertificationError("performance build must be WAL=0 and TRACE=0")

    cmake_argv = _exact_keys(
        document["trace0_cmake_argv"], _TRACE0_CMAKE_ARGV_KEYS,
        "trace0_cmake_argv",
    )
    configure_argv = _exact_keys(
        cmake_argv["configure"], _TRACE0_CONFIGURE_ARGV_KEYS,
        "trace0_cmake_argv.configure",
    )
    configure_scalar_keys = {
        "source_option", "build_directory_option",
        "dependency_prefix_argument", "controlled_define_argument",
    }
    if (not all(type(configure_argv[key]) is str and configure_argv[key]
                and not any(character.isspace()
                            for character in configure_argv[key])
                for key in configure_scalar_keys)
            or len({configure_argv[key] for key in configure_scalar_keys})
            != len(configure_scalar_keys)):
        raise CertificationError("trace0 configure scalar grammar is malformed")
    fixed_arguments = configure_argv["fixed_arguments"]
    if (type(fixed_arguments) is not list or not fixed_arguments
            or not all(type(token) is str and token
                       and not any(character.isspace() for character in token)
                       for token in fixed_arguments)
            or len(set(fixed_arguments)) != len(fixed_arguments)):
        raise CertificationError("trace0 configure fixed arguments are malformed")
    toolchain_arguments = configure_argv["toolchain_arguments"]
    if type(toolchain_arguments) is not list or len(toolchain_arguments) != 2:
        raise CertificationError("trace0 configure toolchain grammar is malformed")
    toolchain_roles: list[str] = []
    for index, raw_argument in enumerate(toolchain_arguments):
        argument = _exact_keys(
            raw_argument, _TRACE0_TOOLCHAIN_ARGUMENT_KEYS,
            f"trace0_cmake_argv.configure.toolchain_arguments[{index}]",
        )
        if (type(argument["role"]) is not str or not argument["role"]
                or type(argument["prefix"]) is not str or not argument["prefix"]
                or any(character.isspace() for character in argument["prefix"])):
            raise CertificationError(
                "trace0 configure toolchain argument is malformed")
        toolchain_roles.append(argument["role"])
    if set(toolchain_roles) != {"cc", "cxx"} or len(set(toolchain_roles)) != 2:
        raise CertificationError("trace0 configure toolchain roles are not exact")
    build_argv = _exact_keys(
        cmake_argv["build"], _TRACE0_BUILD_ARGV_KEYS,
        "trace0_cmake_argv.build",
    )
    if (not all(type(value) is str and value
                and not any(character.isspace() for character in value)
                for value in build_argv.values())
            or len({build_argv["subcommand"], build_argv["target_option"],
                    build_argv["jobs_option"]}) != 3):
        raise CertificationError("trace0 build grammar is malformed")

    workloads_raw = document["workloads"]
    if type(workloads_raw) is not list or len(workloads_raw) != 2:
        raise CertificationError("policy must define exactly two workloads")
    workloads: dict[str, Mapping[str, Any]] = {}
    for index, raw_workload in enumerate(workloads_raw):
        workload = _exact_keys(raw_workload, _WORKLOAD_KEYS, f"workloads[{index}]")
        workload_id = workload["id"]
        if (type(workload_id) is not str or not workload_id
                or workload_id in workloads):
            raise CertificationError("workload IDs must be unique nonempty strings")
        if (type(workload["label"]) is not str or not workload["label"]
                or type(workload["rratio"]) is not str
                or type(workload["adopted_backoff_us"]) is not int
                or workload["adopted_backoff_us"] <= 0):
            raise CertificationError("workload identity is malformed")
        workloads[workload_id] = workload

    cells_raw = document["cells"]
    if type(cells_raw) is not list or len(cells_raw) != 4:
        raise CertificationError("policy must define exactly four cells")
    cells: list[CellSpec] = []
    seen_cells: set[str] = set()
    role_pairs: dict[str, set[str]] = {key: set() for key in workloads}
    for index, raw_cell in enumerate(cells_raw):
        cell = _exact_keys(raw_cell, _CELL_KEYS, f"cells[{index}]")
        genome = _exact_keys(cell["genome"], _GENOME_KEYS, f"cells[{index}].genome")
        cell_id = cell["id"]
        workload_id = cell["workload"]
        role = cell["role"]
        if type(cell_id) is not str or not cell_id or cell_id in seen_cells:
            raise CertificationError("cell IDs must be unique nonempty strings")
        if workload_id not in workloads or role not in {"stock", "adopted"}:
            raise CertificationError("cell workload or role is invalid")
        if role in role_pairs[workload_id]:
            raise CertificationError("each workload needs one stock and one adopted cell")
        if not all(type(value) is int for value in genome.values()):
            raise CertificationError("genome values must be exact integers")
        if role == "stock":
            if genome != {"BACK_OFF": 0, "BACKOFF_FIXED": -1}:
                raise CertificationError("stock cell is not exact no-backoff")
        elif genome != {
            "BACK_OFF": 1,
            "BACKOFF_FIXED": workloads[workload_id]["adopted_backoff_us"],
        }:
            raise CertificationError("adopted cell does not match workload policy")
        perf = {
            "records": common["records"],
            "threads": common["threads"],
            "workload": {
                "ycsb_zipf_skew": common["skew"],
                "ycsb_rratio": workloads[workload_id]["rratio"],
                "ycsb_rmw": common["rmw"],
                "ycsb_max_ope": common["max_ope"],
            },
            "extime": common["extime"],
            "reps": common["reps"],
        }
        cells.append(CellSpec(
            cell_id=cell_id,
            workload_id=workload_id,
            workload_label=str(workloads[workload_id]["label"]),
            role=role,
            genome=dict(genome),
            perf=perf,
        ))
        seen_cells.add(cell_id)
        role_pairs[workload_id].add(role)
    if any(roles != {"stock", "adopted"} for roles in role_pairs.values()):
        raise CertificationError("policy is not the exact two-by-two protocol")

    return Policy(
        path=policy_path.resolve(),
        document=document,
        raw_bytes=raw,
        bytes_sha256=_sha256_bytes(raw),
        protocol_sha256=_sha256_bytes(_canonical_json(_protocol_preimage(document))),
        cells=tuple(cells),
    )


def perf_config_for_cell(policy: Policy, cell_id: str) -> PerfConfig:
    perf = policy.cell(cell_id).perf
    return PerfConfig(
        records=perf["records"], threads=perf["threads"],
        workload=dict(perf["workload"]), extime=perf["extime"],
        reps=perf["reps"],
    )


def _genome_for_cell(policy: Policy, cell: CellSpec):
    from .model import Genome

    flags = {
        key.removeprefix("CCBENCH_"): int(value)
        for key, value in policy.document["controlled_define_base"].items()
        if key != "CCBENCH_TRACE"
    }
    flags.update(cell.genome)
    return Genome(
        protocol=policy.document["performance_common"]["ccbench_protocol"],
        flags=flags,
    )


def campaign_preimage(policy: Policy, workload_id: str, attempt_id: str,
                      current_pin: str) -> dict[str, Any]:
    cells = [cell for cell in policy.cells if cell.workload_id == workload_id]
    if len(cells) != 2:
        raise CertificationError(f"workload is not an exact pair: {workload_id}")
    if _ATTEMPT_RE.fullmatch(attempt_id) is None:
        raise CertificationError("attempt ID is not a canonical leaf")
    if type(current_pin) is not str or _COMMIT_RE.fullmatch(current_pin) is None:
        raise CertificationError("current pin is required")
    return {
        "study": policy.study,
        "protocol_schema": POLICY_SCHEMA,
        "protocol_sha256": policy.protocol_sha256,
        "attempt_id": attempt_id,
        "current_pin": current_pin,
        "historical_pin_role": "reference-only",
        "verify": VERIFY_MODE,
        "reps": cells[0].perf["reps"],
        "aggregate": "median",
        "effect": "adopted_median / stock_median - 1",
        "screening": False,
        "workload": dict(cells[0].perf),
        "ordered_cells": [cell.cell_id for cell in cells],
        "ordered_genomes": [dict(cell.genome) for cell in cells],
    }


def validate_campaign_binding(policy: Policy, workload_id: str, attempt_id: str,
                              current_pin: str, observed_preimage: object,
                              perf: PerfConfig) -> None:
    expected = campaign_preimage(policy, workload_id, attempt_id, current_pin)
    if observed_preimage != expected:
        raise CertificationError("campaign preimage does not match protocol")
    expected_perf = expected["workload"]
    actual_perf = {
        "records": perf.records,
        "threads": perf.threads,
        "workload": dict(perf.workload),
        "extime": perf.extime,
        "reps": perf.reps,
    }
    if actual_perf != expected_perf:
        raise CertificationError("PerfConfig does not match campaign preimage")


def _lexical_absolute_path(path: Path | str, label: str) -> Path:
    try:
        value = os.fspath(path)
    except TypeError as exc:
        raise CertificationError(f"{label} must be path-like") from exc
    if type(value) is not str or not value or not os.path.isabs(value):
        raise CertificationError(f"{label} must be an absolute lexical path")
    if os.path.normpath(value) != value:
        raise CertificationError(f"{label} is not lexically canonical")
    return Path(value)


def _reject_symlink_components(path: Path | str, label: str, *,
                               allow_missing: bool = False) -> None:
    candidate = _lexical_absolute_path(path, label)
    current = Path(candidate.anchor)
    for part in candidate.parts[1:]:
        current = current / part
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            if allow_missing:
                return
            raise CertificationError(f"{label} component is missing: {current}") from None
        except OSError as exc:
            raise CertificationError(f"cannot inspect {label} component: {current}") from exc
        if stat.S_ISLNK(info.st_mode):
            raise CertificationError(f"{label} component must not be a symlink: {current}")
        if current != candidate and not stat.S_ISDIR(info.st_mode):
            raise CertificationError(f"{label} ancestor is not a directory: {current}")


def validate_attempt_root(policy: Policy, attempt_root: Path | str,
                          *, must_exist: bool = True) -> tuple[str, Path]:
    raw = _lexical_absolute_path(attempt_root, "attempt root")
    base = _lexical_absolute_path(policy.durable_base, "durable measurement base")
    if raw.parent != base:
        raise CertificationError("attempt root is outside the pinned durable base")
    if _ATTEMPT_RE.fullmatch(raw.name) is None:
        raise CertificationError("attempt root is not a canonical child")
    _reject_symlink_components(base, "durable measurement base",
                               allow_missing=not must_exist)
    _reject_symlink_components(raw, "attempt root", allow_missing=not must_exist)
    if must_exist and not raw.is_dir():
        raise CertificationError("attempt root must be an existing real directory")
    return raw.name, raw


def create_attempt_root(policy: Policy, attempt_id: str) -> Path:
    if _ATTEMPT_RE.fullmatch(attempt_id) is None:
        raise CertificationError("attempt ID is not a canonical leaf")
    base = _lexical_absolute_path(policy.durable_base, "durable measurement base")
    _reject_symlink_components(base, "durable measurement base", allow_missing=True)
    base.mkdir(parents=True, exist_ok=True)
    _reject_symlink_components(base, "durable measurement base")
    root = base / attempt_id
    root.mkdir(mode=0o700, exist_ok=False)
    _reject_symlink_components(root, "attempt root")
    _fsync_dir(base)
    validate_attempt_root(policy, root)
    return root


def workload_ids(policy: Policy) -> tuple[str, ...]:
    """Return the exact policy order used by every fan-out/fan-in contract."""
    return tuple(str(workload["id"]) for workload in policy.document["workloads"])


def workload_job_root(policy: Policy, attempt_root: Path,
                      workload_id: str) -> Path:
    if workload_id not in workload_ids(policy):
        raise CertificationError(f"unknown workload: {workload_id!r}")
    return attempt_root / "jobs" / workload_id


def raw_result_claim_path(policy: Policy, workload_id: str,
                          attempt_root: Path, campaign_id: str) -> Path:
    from . import env_contract
    from .layout import env_scope_dir

    output_root = workload_job_root(policy, attempt_root, workload_id)
    contract = env_contract.lookup("pegasus")
    return (Path(env_scope_dir(contract.env_tag, str(output_root)))
            / "claims" / f"{campaign_id}.claim")


def preregister_attempt(policy: Policy, attempt_id: str,
                        current_pin: str) -> Path:
    """Create the outer attempt and its pre-run identity, never resume it."""
    if type(current_pin) is not str or _COMMIT_RE.fullmatch(current_pin) is None:
        raise CertificationError("current pin is required")
    root = create_attempt_root(policy, attempt_id)
    (root / "receipts").mkdir(mode=0o700)
    jobs_root = root / "jobs"
    jobs_root.mkdir(mode=0o700)
    for workload_id in workload_ids(policy):
        job_root = workload_job_root(policy, root, workload_id)
        job_root.mkdir(mode=0o700)
        for child in ("campaigns", "cache", "scheduler"):
            (job_root / child).mkdir(mode=0o700)
    write_json_x(root / "preregistration.json", {
        "schema_version": "paper-story-a2-preregistration/v1",
        "study": policy.study,
        "protocol_sha256": policy.protocol_sha256,
        "policy_sha256": policy.bytes_sha256,
        "attempt_id": attempt_id,
        "attempt_root": str(root),
        "current_pin": current_pin,
        "automatic_retry": False,
    })
    _fsync_dir(root / "receipts")
    for workload_id in workload_ids(policy):
        job_root = workload_job_root(policy, root, workload_id)
        for child in ("campaigns", "cache", "scheduler"):
            _fsync_dir(job_root / child)
        _fsync_dir(job_root)
    _fsync_dir(jobs_root)
    _fsync_dir(root)
    return root


def _read_json(path: Path, *, limit: int = _RESULT_LIMIT) -> tuple[dict[str, Any], bytes]:
    if path.is_symlink() or not path.is_file():
        raise CertificationError(f"required JSON is not a regular file: {path}")
    try:
        size = path.stat().st_size
        if size <= 0 or size > limit:
            raise CertificationError(f"JSON size is outside bound: {path}: {size}")
        raw = path.read_bytes()
        if len(raw) != size:
            raise CertificationError(f"JSON changed while being read: {path}")
        value = _loads_json(raw, str(path))
    except CertificationError:
        raise
    except OSError as exc:
        raise CertificationError(f"cannot read JSON: {path}: {exc}") from exc
    if type(value) is not dict:
        raise CertificationError(f"JSON root is not an object: {path}")
    return value, raw


def _write_bytes_x(path: Path, payload: bytes, *, mode: int = 0o600) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def write_json_x(path: Path, payload: Mapping[str, Any]) -> None:
    _write_bytes_x(path, _canonical_json(payload))


def _fsync_dir(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _canonical_child(path_value: object, parent: Path, label: str) -> Path:
    if type(path_value) is not str:
        raise CertificationError(f"{label} path must be a string")
    path = _lexical_absolute_path(path_value, f"{label} path")
    _reject_symlink_components(path, label)
    if not path.is_file():
        raise CertificationError(f"{label} is not a regular file")
    try:
        path.relative_to(parent)
    except ValueError as exc:
        raise CertificationError(f"{label} is outside attempt root") from exc
    return path


def _canonical_future_child(path_value: object, parent: Path, label: str) -> Path:
    if type(path_value) is not str:
        raise CertificationError(f"{label} path must be a string")
    path = _lexical_absolute_path(path_value, f"{label} path")
    try:
        relative = path.relative_to(parent)
    except ValueError as exc:
        raise CertificationError(f"{label} is outside attempt root") from exc
    if not relative.parts:
        raise CertificationError(f"{label} must be an attempt child")
    _reject_symlink_components(path.parent, f"{label} parent")
    if path.is_symlink():
        raise CertificationError(f"{label} must not be a symlink")
    return path


def _require_sha(value: object, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise CertificationError(f"{label} is not a full lowercase sha256")
    return value


def _option_value(argv: Sequence[str], option: str) -> str:
    positions = [index for index, token in enumerate(argv) if token == option]
    if len(positions) != 1 or positions[0] + 1 >= len(argv):
        raise CertificationError(f"qsub argv needs exactly one {option}")
    return argv[positions[0] + 1]


def _normalize_request_id(value: object) -> str:
    if type(value) is not str:
        raise CertificationError("request ID must be a string")
    normalized = value.strip().rstrip(".")
    if normalized.startswith("0:"):
        normalized = normalized[2:]
    if not normalized or _REQUEST_RE.fullmatch(normalized) is None:
        raise CertificationError("request ID is invalid")
    return normalized


def _validate_group_coordinates(policy: Policy,
                                bindings: Sequence[Mapping[str, Any]]) -> None:
    expected_workloads = workload_ids(policy)
    # The production receipt validators have already enforced workload order and
    # canonical per-workload log paths before constructing these bindings.  Keep
    # those two checks here as redundant defence for direct/helper callers, not
    # as independent production barriers.  Request-ID distinctness remains an
    # independent cross-job barrier at this layer.
    if [binding.get("workload") for binding in bindings] != list(expected_workloads):
        raise CertificationError("group workload order differs from policy")
    request_ids = [
        _normalize_request_id(binding.get("request_id")) for binding in bindings]
    if len(set(request_ids)) != len(request_ids):
        raise CertificationError("group request IDs must be distinct")
    stdout_paths = [binding.get("scheduler_stdout_path") for binding in bindings]
    stderr_paths = [binding.get("scheduler_stderr_path") for binding in bindings]
    if (any(not isinstance(path, Path) for path in stdout_paths + stderr_paths)
            or len(set(stdout_paths)) != len(stdout_paths)
            or len(set(stderr_paths)) != len(stderr_paths)
            or set(stdout_paths) & set(stderr_paths)):
        raise CertificationError("group scheduler log paths must be distinct")


def _validate_submission_receipt(policy: Policy, payload: Mapping[str, Any],
                                 attempt_id: str, attempt_root: Path,
                                 current_pin: str) -> dict[str, Any]:
    required = {
        "schema_version", "route", "study", "protocol_sha256", "attempt_id",
        "attempt_root", "source_commit", "current_pin", "submit_host",
        "submission_cwd", "job_body_sha256", "jobs",
    }
    if type(payload) is not dict or set(payload) != required:
        raise CertificationError(
            "submission receipt is missing required or has extra evidence fields")
    if (payload["schema_version"] != SUBMISSION_SCHEMA
            or payload["route"] != "direct-qsub"
            or payload["study"] != policy.study
            or payload["protocol_sha256"] != policy.protocol_sha256
            or payload["attempt_id"] != attempt_id
            or _lexical_absolute_path(
                payload["attempt_root"], "submission attempt root") != attempt_root
            or payload["current_pin"] != current_pin):
        raise CertificationError("submission receipt identity mismatch")
    if type(payload["submit_host"]) is not str or not payload["submit_host"]:
        raise CertificationError("submission host is missing")
    if (type(payload["source_commit"]) is not str
            or _COMMIT_RE.fullmatch(payload["source_commit"]) is None):
        raise CertificationError("submission source commit is missing")
    scheduler = policy.document["scheduler"]
    submission_cwd = _lexical_absolute_path(
        payload["submission_cwd"], "submission cwd")
    job_body = submission_cwd.joinpath(*Path(scheduler["job_body"]).parts)
    _reject_symlink_components(job_body, "job body")
    if not job_body.is_file():
        raise CertificationError("canonical job body is not a regular file")
    if (_require_sha(payload["job_body_sha256"], "job_body_sha256")
            != _sha256_file(job_body)):
        raise CertificationError("job body bytes differ from submission receipt")

    jobs = payload["jobs"]
    expected_workloads = workload_ids(policy)
    if type(jobs) is not list or len(jobs) != len(expected_workloads):
        raise CertificationError("submission must contain the exact two-job group")
    bindings: list[dict[str, Any]] = []
    for workload_id, job in zip(expected_workloads, jobs):
        job_required = {
            "workload", "qsub_argv", "qsub_stdout", "qsub_stderr",
            "qsub_returncode", "request_id", "qstat_visibility",
            "qsub_environment",
        }
        if type(job) is not dict or set(job) != job_required:
            raise CertificationError("submission job entry is not exact")
        if job["workload"] != workload_id:
            raise CertificationError("submission workload order differs from policy")
        if job["qsub_returncode"] != 0 or job["qsub_stderr"] != "":
            raise CertificationError("qsub execution did not complete cleanly")
        request_id = _normalize_request_id(job["request_id"])
        qsub_stdout = job["qsub_stdout"]
        stdout_ids = (
            [_normalize_request_id(value)
             for value in _QSUB_REQUEST_RE.findall(qsub_stdout)]
            if type(qsub_stdout) is str else []
        )
        if type(qsub_stdout) is not str or (
                stdout_ids != [request_id]
                and _normalize_request_id(qsub_stdout) != request_id):
            raise CertificationError("qsub stdout is not bound to request ID")
        argv = job["qsub_argv"]
        if (type(argv) is not list or not argv
                or not all(type(item) is str for item in argv)):
            raise CertificationError("canonical qsub argv is missing")
        if (len(argv) != 18
                or argv[0:2] != ["qsub", "-A"]
                or argv[2] != scheduler["project"]
                or argv[3:5] != ["-q", scheduler["queue"]]
                or argv[5:7] != ["-b", str(scheduler["nodes"])]
                or argv[7:9] != ["-l", f"elapstim_req={scheduler['walltime']}"]
                or argv[9:11] != ["-N", _QSUB_JOB_NAME]
                or argv[11] != "-v" or argv[13] != "-o" or argv[15] != "-e"):
            raise CertificationError("qsub argv does not match scheduler policy")
        variable_arg = _option_value(argv, "-v")
        variables: dict[str, str] = {}
        for item in variable_arg.split(","):
            key, separator, value = item.partition("=")
            if not separator or not key or key in variables:
                raise CertificationError("qsub -v mapping is malformed or duplicated")
            variables[key] = value
        if (set(variables) != _QSUB_ENV_KEYS
                or variables.get("IZANAGI_A2_ATTEMPT_ROOT") != str(attempt_root)
                or variables.get("IZANAGI_A2_WORKLOAD") != workload_id
                or variables.get("IZANAGI_A2_EXPECTED_HEAD") != payload["source_commit"]
                or variables.get("IZANAGI_A2_CURRENT_PIN") != current_pin
                or variables.get("IZANAGI_A2_REPO_ROOT") != str(submission_cwd)
                or not all(variables.get(name) for name in _QSUB_ENV_KEYS)):
            raise CertificationError("qsub -v is not bound to workload and current pin")
        if job["qsub_environment"] != variables:
            raise CertificationError("qsub environment differs from the exact -v mapping")
        if argv[-1] != str(job_body):
            raise CertificationError("qsub argv does not use the exact canonical job body")
        job_root = workload_job_root(policy, attempt_root, workload_id)
        stdout_arg = _canonical_future_child(
            _option_value(argv, "-o"), attempt_root, "scheduler stdout")
        stderr_arg = _canonical_future_child(
            _option_value(argv, "-e"), attempt_root, "scheduler stderr")
        if (stdout_arg != job_root / "scheduler" / "job.stdout"
                or stderr_arg != job_root / "scheduler" / "job.stderr"):
            raise CertificationError("scheduler log path is not workload-canonical")

        visibility = job["qstat_visibility"]
        visibility_stdout = (
            visibility.get("stdout") if type(visibility) is dict else None)
        if (type(visibility) is not dict or set(visibility) != {
                "observed", "observed_at_utc", "request_id", "argv", "returncode",
                "state", "stdout", "stderr"}
                or visibility.get("observed") is not True
                or type(visibility.get("observed_at_utc")) is not str
                or _UTC_OBSERVATION_RE.fullmatch(
                    visibility.get("observed_at_utc", "")) is None
                or _normalize_request_id(visibility.get("request_id")) != request_id
                or visibility.get("argv") != ["qstat", "-f", request_id]
                or visibility.get("returncode") != 0
                or visibility.get("stderr") != ""
                or type(visibility_stdout) is not str):
            raise CertificationError("qstat visibility evidence is incomplete")
        if _NQSV_DISAPPEARED_RE.search(visibility_stdout) is not None:
            raise CertificationError(
                "qstat visibility contains a disappeared request signature")
        ended_matches = list(
            _NQSV_ENDED_REQUEST_TIME_RE.finditer(visibility_stdout))
        if not ended_matches:
            raise CertificationError(
                "qstat visibility ended request time is missing")
        if len(ended_matches) != 1:
            raise CertificationError(
                "qstat visibility ended request time is duplicated")
        if ended_matches[0].group(1).strip() != "(none)":
            raise CertificationError(
                "qstat visibility ended request time is not (none)")
        request_matches = list(QSTAT_REQUEST_ID_RE.finditer(visibility_stdout))
        if (len(request_matches) == 1
                and ended_matches[0].start() < request_matches[0].end()):
            raise CertificationError(
                "qstat visibility ended request time precedes request ID")
        if _TERMINAL_STATE_RE.search(visibility_stdout) is not None:
            raise CertificationError("qstat visibility contains a terminal state")
        parsed_state = target_bound_qstat_state_result(
            visibility_stdout, request_id)
        parse_errors = {
            "request-id-count": "qstat visibility request ID count is not one",
            "request-id-mismatch": "qstat visibility request ID differs from submission",
            "state-before-target-request-id": (
                "qstat visibility has state before the target request ID"),
            "state-field-duplicated": "qstat visibility state field is duplicated",
            "state-fields-conflict": "qstat visibility state fields conflict",
            "state-field-missing": "qstat visibility state field is missing",
            "state-vocabulary-unknown": "qstat visibility state vocabulary is unknown",
            "noncanonical-state-whitespace": (
                "qstat visibility state whitespace is noncanonical"),
            "invalid-target-request-id": "qstat visibility target request ID is invalid",
            "invalid-observed-request-id": (
                "qstat visibility observed request ID is invalid"),
        }
        if parsed_state.state is None:
            raise CertificationError(parse_errors.get(
                parsed_state.reason, "qstat visibility is not target-bound"))
        if parsed_state.state not in _SUBMISSION_VISIBLE_STATES:
            raise CertificationError(
                "qstat visibility state is outside the submission acceptance set")
        if visibility.get("state") not in _SUBMISSION_VISIBLE_STATES:
            raise CertificationError(
                "qstat visibility receipt state is outside the submission acceptance set")
        if visibility.get("state") != parsed_state.state:
            raise CertificationError(
                "qstat visibility receipt state differs from canonical stdout state")
        bindings.append({
            "workload": workload_id,
            "request_id": request_id,
            "scheduler_stdout_path": stdout_arg,
            "scheduler_stderr_path": stderr_arg,
        })
    _validate_group_coordinates(policy, bindings)
    return {
        "jobs": bindings,
        "request_ids": {
            binding["workload"]: binding["request_id"] for binding in bindings},
        "source_commit": payload["source_commit"],
        "job_body_sha256": payload["job_body_sha256"],
    }


def _validate_completion_job(policy: Policy, payload: Mapping[str, Any],
                             attempt_id: str, attempt_root: Path,
                             current_pin: str, workload_id: str,
                             request_id: str,
                             submission: Mapping[str, Any],
                             job_body_sha256: str) -> dict[str, Any]:
    required = {
        "workload", "request_id",
        "terminal_observation", "compute_result", "compute_result_sha256",
        "reservation_result", "reservation_result_sha256",
        "driver_rc", "scheduler_stdout", "scheduler_stderr",
    }
    if type(payload) is not dict or set(payload) != required:
        raise CertificationError("completion job does not have exact evidence fields")
    if (payload["workload"] != workload_id
            or _normalize_request_id(payload["request_id"]) != request_id
            or type(payload["driver_rc"]) is not int):
        raise CertificationError("completion job identity mismatch")
    terminal = payload["terminal_observation"]
    terminal_keys = {
        "observed", "request_id", "argv", "returncode", "state", "stdout",
        "stderr", "reason",
    }
    if (type(terminal) is not dict or set(terminal) != terminal_keys
            or terminal.get("observed") is not True
            or _normalize_request_id(terminal.get("request_id")) != request_id
            or terminal.get("argv") != ["qstat", "-f", request_id]
            or terminal.get("returncode") != 0
            or terminal.get("stderr") != ""
            or terminal.get("state") != "END"
            or type(terminal.get("stdout")) is not str):
        raise CertificationError("scheduler terminal observation is incomplete")
    if terminal["reason"] == "scheduler-end-state":
        terminal_ids = [
            _normalize_request_id(value)
            for value in _NQSV_REQUEST_RE.findall(terminal["stdout"])
        ]
        if terminal_ids != [request_id] or _TERMINAL_STATE_RE.search(
                terminal["stdout"]) is None:
            raise CertificationError("visible scheduler terminal state is not request-bound")
    elif terminal["reason"] == "request-disappeared-after-visibility":
        disappeared = _NQSV_DISAPPEARED_RE.fullmatch(terminal["stdout"])
        if (disappeared is None
                or _normalize_request_id(disappeared.group(1)) != request_id):
            raise CertificationError(
                "disappeared request terminal is not the exact NQSV signature")
    else:
        raise CertificationError("scheduler terminal reason is not canonical")

    scheduler = policy.document["scheduler"]
    log_records: dict[str, dict[str, Any]] = {}
    log_bytes: dict[str, bytes] = {}
    for label, expected_path in (
        ("scheduler_stdout", submission["scheduler_stdout_path"]),
        ("scheduler_stderr", submission["scheduler_stderr_path"]),
    ):
        record = payload[label]
        if type(record) is not dict or set(record) != {"path", "size", "sha256"}:
            raise CertificationError(f"{label} record is incomplete")
        path = _canonical_child(record["path"], attempt_root, label)
        if path != expected_path:
            raise CertificationError(f"{label} path differs from qsub argv")
        try:
            observed_bytes = path.read_bytes()
        except OSError as exc:
            raise CertificationError(f"cannot read {label}") from exc
        if (type(record["size"]) is not int
                or record["size"] != len(observed_bytes)):
            raise CertificationError(f"{label} size mismatch")
        if (_require_sha(record["sha256"], f"{label}.sha256")
                != _sha256_bytes(observed_bytes)):
            raise CertificationError(f"{label} sha256 mismatch")
        log_records[label] = dict(record)
        log_bytes[label] = observed_bytes
    try:
        accounting_text = log_bytes["scheduler_stderr"].decode("utf-8")
    except UnicodeError as exc:
        raise CertificationError("cannot read NQSV accounting log") from exc
    accounting_ids = [
        _normalize_request_id(value)
        for value in _NQSV_REQUEST_RE.findall(accounting_text)
    ]
    if (accounting_ids != [request_id]
            or _NQSV_GROUP_RE.findall(accounting_text) != [scheduler["project"]]
            or _NQSV_STARTED_RE.search(accounting_text) is None
            or _NQSV_ENDED_RE.search(accounting_text) is None
            or _NQSV_ELAPSE_RE.search(accounting_text) is None):
        raise CertificationError("NQSV accounting is not request-bound")

    compute_path = _canonical_child(
        payload["compute_result"], attempt_root, "compute result")
    job_root = workload_job_root(policy, attempt_root, workload_id)
    if compute_path != job_root / "compute-result.json":
        raise CertificationError("compute result path is not canonical")
    compute, compute_bytes = _read_json(compute_path)
    if (_require_sha(payload["compute_result_sha256"], "compute_result_sha256")
            != _sha256_bytes(compute_bytes)):
        raise CertificationError("compute result hash mismatch")
    if (set(compute) != {
            "schema_version", "workload", "driver_rc", "pbs_jobid", "current_pin"}
            or compute.get("schema_version") != COMPUTE_RESULT_SCHEMA
            or compute.get("workload") != workload_id
            or type(compute.get("driver_rc")) is not int
            or compute["driver_rc"] != payload["driver_rc"]
            or _normalize_request_id(compute.get("pbs_jobid")) != request_id
            or compute.get("current_pin") != current_pin):
        raise CertificationError("compute result identity differs from completion")

    reservation_path = _canonical_child(
        payload["reservation_result"], attempt_root, "reservation result")
    if reservation_path != job_root / "reservation.json":
        raise CertificationError("reservation result path is not canonical")
    reservation_result, reservation_bytes = _read_json(reservation_path)
    if (_require_sha(
            payload["reservation_result_sha256"], "reservation_result_sha256")
            != _sha256_bytes(reservation_bytes)):
        raise CertificationError("reservation result hash mismatch")
    if set(reservation_result) != {
            "schema_version", "environment", "allocation_qstat_stdout",
            "allocation_qstat_stderr"} or (
            reservation_result.get("schema_version") != RESERVATION_RESULT_SCHEMA):
        raise CertificationError("reservation result schema is not exact")
    reservation_environment = reservation_result.get("environment")
    if (type(reservation_environment) is not dict
            or set(reservation_environment) != _RESERVATION_ENV_KEYS
            or not all(type(value) is str and value
                       for value in reservation_environment.values())):
        raise CertificationError("reservation result environment is not exact")
    from . import reservation
    try:
        reservation_binding = reservation.read_binding(reservation_environment)
    except reservation.ReservationError as exc:
        raise CertificationError("reservation result binding is invalid") from exc
    hours, minutes, seconds = (
        int(piece) for piece in policy.document["scheduler"]["walltime"].split(":"))
    if (reservation_binding.requested_s != hours * 3600 + minutes * 60 + seconds
            or _normalize_request_id(reservation_binding.job_id) != request_id
            or reservation_binding.script_sha256 != job_body_sha256):
        raise CertificationError("reservation result differs from scheduler submission")
    allocation_names = {
        "allocation_qstat_stdout": "allocation-qstat.stdout",
        "allocation_qstat_stderr": "allocation-qstat.stderr",
    }
    for label, filename in allocation_names.items():
        record = reservation_result[label]
        if type(record) is not dict or set(record) != {"path", "size", "sha256"}:
            raise CertificationError(f"{label} record is incomplete")
        path = _canonical_child(record["path"], attempt_root, label)
        expected_path = job_root / "scheduler" / filename
        if path != expected_path:
            raise CertificationError(f"{label} path is not canonical")
        try:
            observed_bytes = path.read_bytes()
        except OSError as exc:
            raise CertificationError(f"cannot read {label}") from exc
        if (type(record["size"]) is not int or record["size"] != len(observed_bytes)
                or _require_sha(record["sha256"], f"{label}.sha256")
                != _sha256_bytes(observed_bytes)):
            raise CertificationError(f"{label} bytes differ from reservation result")

    return {
        "workload": workload_id,
        "request_id": request_id,
        "driver_rc": payload["driver_rc"],
        "compute_result": compute,
        "reservation_result": reservation_result,
        "reservation_binding": reservation_binding,
        **log_records,
    }


def _validate_completion_receipt(policy: Policy, payload: Mapping[str, Any],
                                 attempt_id: str, attempt_root: Path,
                                 current_pin: str,
                                 submission: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "schema_version", "study", "protocol_sha256", "attempt_id",
        "attempt_root", "source_commit", "current_pin", "jobs",
        "raw_result_manifest", "raw_result_manifest_sha256",
    }
    if type(payload) is not dict or set(payload) != required:
        raise CertificationError("completion receipt does not have exact evidence fields")
    if (payload["schema_version"] != COMPLETION_SCHEMA
            or payload["study"] != policy.study
            or payload["protocol_sha256"] != policy.protocol_sha256
            or payload["attempt_id"] != attempt_id
            or _lexical_absolute_path(
                payload["attempt_root"], "completion attempt root") != attempt_root
            or payload["source_commit"] != submission["source_commit"]
            or payload["current_pin"] != current_pin):
        raise CertificationError("completion receipt identity mismatch")
    jobs = payload["jobs"]
    submission_jobs = submission["jobs"]
    expected_workloads = workload_ids(policy)
    if (type(jobs) is not list or len(jobs) != len(expected_workloads)
            or len(submission_jobs) != len(expected_workloads)):
        raise CertificationError("completion must contain the exact two-job group")
    job_bindings = [
        _validate_completion_job(
            policy, job, attempt_id, attempt_root, current_pin,
            workload_id, submission_job["request_id"], submission_job,
            submission["job_body_sha256"],
        )
        for workload_id, job, submission_job in zip(
            expected_workloads, jobs, submission_jobs)
    ]
    manifest_bundle = None
    manifest_reason = "driver-nonzero"
    all_drivers_succeeded = all(
        binding["driver_rc"] == 0 for binding in job_bindings)
    if all_drivers_succeeded:
        try:
            if (payload["raw_result_manifest"] is None
                    or payload["raw_result_manifest_sha256"] is None):
                raise CertificationError("verified raw manifest is missing")
            manifest_path = _canonical_child(
                payload["raw_result_manifest"], attempt_root,
                "raw result manifest")
            manifest_sha = _require_sha(
                payload["raw_result_manifest_sha256"],
                "raw_result_manifest_sha256")
            manifest_bundle = _load_raw_manifest_bundle(
                policy, manifest_path, manifest_sha, attempt_id=attempt_id,
                attempt_root=attempt_root, current_pin=current_pin,
                job_bindings=job_bindings,
            )
            manifest_reason = None
        except (CertificationError, OSError, ValueError, TypeError,
                KeyError, IndexError) as exc:
            manifest_reason = str(exc)
    elif (payload["raw_result_manifest"] is not None
          or payload["raw_result_manifest_sha256"] is not None):
        raise CertificationError(
            "failed group completion must not claim a raw manifest")
    return {
        "jobs": job_bindings,
        "driver_rcs": {
            binding["workload"]: binding["driver_rc"]
            for binding in job_bindings},
        "raw_manifest_valid": manifest_bundle is not None,
        "raw_manifest_reason": manifest_reason,
        "raw_manifest_bundle": manifest_bundle,
    }


def validate_acquisition_bundle(policy: Policy, acquisition_path: Path | str,
                                *, current_pin: str) -> dict[str, Any]:
    acquisition_file = _lexical_absolute_path(
        acquisition_path, "acquisition receipt")
    acquisition, acquisition_bytes = _read_json(acquisition_file)
    required = {
        "schema_version", "route", "study", "protocol_sha256", "attempt_id",
        "attempt_root", "source_commit", "current_pin", "request_ids",
        "submission_receipt",
        "submission_receipt_sha256", "completion_receipt",
        "completion_receipt_sha256",
    }
    if set(acquisition) != required:
        raise CertificationError("acquisition receipt is a hand-written subset")
    attempt_id = acquisition["attempt_id"]
    attempt_name, attempt_root = validate_attempt_root(
        policy, acquisition["attempt_root"])
    if (acquisition["schema_version"] != ACQUISITION_SCHEMA
            or acquisition["route"] != "direct-qsub"
            or acquisition["study"] != policy.study
            or acquisition["protocol_sha256"] != policy.protocol_sha256
            or attempt_id != attempt_name
            or acquisition["current_pin"] != current_pin):
        raise CertificationError("acquisition receipt identity mismatch")
    try:
        acquisition_file.relative_to(attempt_root)
    except ValueError as exc:
        raise CertificationError("acquisition receipt is not durable with attempt") from exc
    submission_path = _canonical_child(
        acquisition["submission_receipt"], attempt_root, "submission receipt")
    completion_path = _canonical_child(
        acquisition["completion_receipt"], attempt_root, "completion receipt")
    submission_sha = _require_sha(
        acquisition["submission_receipt_sha256"], "submission receipt sha256")
    completion_sha = _require_sha(
        acquisition["completion_receipt_sha256"], "completion receipt sha256")
    submission, submission_bytes = _read_json(submission_path)
    completion, completion_bytes = _read_json(completion_path)
    if (_sha256_bytes(submission_bytes) != submission_sha
            or _sha256_bytes(completion_bytes) != completion_sha):
        raise CertificationError("receipt bytes do not match acquisition receipt")
    submission_binding = _validate_submission_receipt(
        policy, submission, attempt_id, attempt_root, current_pin)
    if (type(acquisition["request_ids"]) is not dict
            or list(acquisition["request_ids"]) != list(workload_ids(policy))
            or acquisition["request_ids"] != submission_binding["request_ids"]):
        raise CertificationError("acquisition and submission request IDs differ")
    if acquisition["source_commit"] != submission_binding["source_commit"]:
        raise CertificationError("acquisition and submission source commits differ")
    completion_binding = _validate_completion_receipt(
        policy, completion, attempt_id, attempt_root, current_pin,
        submission_binding,
    )
    manifest_bundle = completion_binding["raw_manifest_bundle"]
    return {
        "attempt_id": attempt_id,
        "attempt_root": str(attempt_root),
        "request_ids": submission_binding["request_ids"],
        "source_commit": submission_binding["source_commit"],
        "acquisition": acquisition,
        "acquisition_bytes": acquisition_bytes,
        "submission": submission,
        "submission_bytes": submission_bytes,
        "completion": completion,
        "completion_bytes": completion_bytes,
        "driver_rcs": completion_binding["driver_rcs"],
        "raw_manifest_valid": completion_binding["raw_manifest_valid"],
        "raw_manifest_reason": completion_binding["raw_manifest_reason"],
        "raw_manifest_bytes": (
            manifest_bundle["manifest_bytes"] if manifest_bundle else None),
        "raw_results": (
            manifest_bundle["raw_results"] if manifest_bundle else None),
        "raw_files": manifest_bundle["files"] if manifest_bundle else None,
        "reservation_results": {
            binding["workload"]: binding["reservation_result"]
            for binding in completion_binding["jobs"]},
    }


def record_submission_receipt(policy: Policy, attempt_root: Path | str,
                              current_pin: str,
                              payload: Mapping[str, Any]) -> Path:
    attempt_id, root = validate_attempt_root(policy, attempt_root)
    observed_host = socket.gethostname()
    if (str(payload.get("submit_host", "")).split(".", 1)[0]
            != observed_host.split(".", 1)[0]):
        raise CertificationError("submission host differs from recorder host")
    _validate_submission_receipt(policy, payload, attempt_id, root, current_pin)
    path = root / "receipts" / "submission.json"
    write_json_x(path, payload)
    _fsync_dir(path.parent)
    return path


def record_scheduler_request_id(policy: Policy, attempt_root: Path | str,
                                workload_id: str, request_id: str) -> Path:
    """Durably retain a diagnostic request ID without making it a receipt."""
    _, root = validate_attempt_root(policy, attempt_root)
    normalized = _normalize_request_id(request_id)
    scheduler_root = workload_job_root(
        policy, root, workload_id) / "scheduler"
    _reject_symlink_components(scheduler_root, "scheduler request directory")
    if not scheduler_root.is_dir():
        raise CertificationError("scheduler request directory is unavailable")
    path = scheduler_root / "request-id"
    _write_bytes_x(path, (normalized + "\n").encode("ascii"))
    _fsync_dir(scheduler_root)
    return path


def durabilize_scheduler_qsub_diagnostics(
        policy: Policy, attempt_root: Path | str, workload_id: str,
) -> tuple[Path, Path]:
    """Fsync pre-opened qsub diagnostics without making them receipts."""
    _, root = validate_attempt_root(policy, attempt_root)
    scheduler_root = workload_job_root(
        policy, root, workload_id) / "scheduler"
    _reject_symlink_components(scheduler_root, "qsub diagnostics directory")
    if not scheduler_root.is_dir():
        raise CertificationError("qsub diagnostics directory is unavailable")
    paths = tuple(
        scheduler_root / filename for filename in ("qsub.stdout", "qsub.stderr"))
    for path in paths:
        _reject_symlink_components(path, "qsub diagnostic")
        if not path.is_file():
            raise CertificationError("qsub diagnostic is not a regular file")
        descriptor = os.open(
            path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    _fsync_dir(scheduler_root)
    return paths


def record_completion_receipt(policy: Policy, attempt_root: Path | str,
                              current_pin: str,
                              payload: Mapping[str, Any]) -> Path:
    attempt_id, root = validate_attempt_root(policy, attempt_root)
    submission_path = root / "receipts" / "submission.json"
    submission, _ = _read_json(submission_path)
    binding = _validate_submission_receipt(
        policy, submission, attempt_id, root, current_pin)
    _validate_completion_receipt(
        policy, payload, attempt_id, root, current_pin, binding,
    )
    path = root / "receipts" / "completion.json"
    write_json_x(path, payload)
    _fsync_dir(path.parent)
    return path


def record_acquisition_receipt(policy: Policy, attempt_root: Path | str,
                               current_pin: str) -> Path:
    attempt_id, root = validate_attempt_root(policy, attempt_root)
    submission_path = root / "receipts" / "submission.json"
    completion_path = root / "receipts" / "completion.json"
    submission, _ = _read_json(submission_path)
    completion, _ = _read_json(completion_path)
    binding = _validate_submission_receipt(
        policy, submission, attempt_id, root, current_pin)
    _validate_completion_receipt(
        policy, completion, attempt_id, root, current_pin, binding)
    payload = {
        "schema_version": ACQUISITION_SCHEMA,
        "route": "direct-qsub",
        "study": policy.study,
        "protocol_sha256": policy.protocol_sha256,
        "attempt_id": attempt_id,
        "attempt_root": str(root),
        "source_commit": submission.get("source_commit"),
        "current_pin": current_pin,
        "request_ids": binding["request_ids"],
        "submission_receipt": str(submission_path),
        "submission_receipt_sha256": _sha256_file(submission_path),
        "completion_receipt": str(completion_path),
        "completion_receipt_sha256": _sha256_file(completion_path),
    }
    path = root / "receipts" / "acquisition.json"
    write_json_x(path, payload)
    _fsync_dir(path.parent)
    return path


def exact_qsub(argv: Sequence[str], *, runner=subprocess.run) -> object:
    """Run only an exact, non-empty qsub argv."""
    if (type(argv) not in {list, tuple} or not argv or argv[0] != "qsub"
            or not all(type(token) is str and token for token in argv)):
        raise CertificationError("ratified qsub argv is not exact")
    return runner(list(argv), check=False)


def _file_record(path: Path, attempt_root: Path) -> dict[str, Any]:
    path = _canonical_child(str(path), attempt_root, "group evidence file")
    payload = path.read_bytes()
    return {
        "path": str(path),
        "size": len(payload),
        "sha256": _sha256_bytes(payload),
    }


def finish_group(policy: Policy, attempt_root: Path | str, current_pin: str,
                 *, qstat_runner=subprocess.run) -> tuple[Path, Path]:
    """Create the exact completion/acquisition pair from terminal job evidence."""
    attempt_id, root = validate_attempt_root(policy, attempt_root)
    submission_payload, _ = _read_json(root / "receipts" / "submission.json")
    submission = _validate_submission_receipt(
        policy, submission_payload, attempt_id, root, current_pin)
    jobs: list[dict[str, Any]] = []
    for workload_id, submitted in zip(workload_ids(policy), submission["jobs"]):
        request_id = submitted["request_id"]
        command = ["qstat", "-f", request_id]
        observed = qstat_runner(
            command, check=False, capture_output=True, text=True)
        stdout = observed.stdout or ""
        stderr = observed.stderr or ""
        if observed.returncode != 0 or stderr:
            raise CertificationError(
                f"terminal qstat failed for {workload_id}: rc={observed.returncode}")
        terminal_ids = [
            _normalize_request_id(value)
            for value in _NQSV_REQUEST_RE.findall(stdout)]
        if (terminal_ids == [request_id]
                and _TERMINAL_STATE_RE.search(stdout) is not None):
            reason = "scheduler-end-state"
        else:
            disappeared = _NQSV_DISAPPEARED_RE.fullmatch(stdout)
            if (disappeared is None
                    or _normalize_request_id(disappeared.group(1)) != request_id):
                raise CertificationError(
                    f"request is not terminal for {workload_id}")
            reason = "request-disappeared-after-visibility"
        job_root = workload_job_root(policy, root, workload_id)
        compute_path = job_root / "compute-result.json"
        reservation_path = job_root / "reservation.json"
        compute, _ = _read_json(compute_path)
        driver_status = compute.get("driver_rc")
        if type(driver_status) is not int:
            raise CertificationError("compute result driver_rc is missing")
        jobs.append({
            "workload": workload_id,
            "request_id": request_id,
            "terminal_observation": {
                "observed": True,
                "request_id": request_id,
                "argv": command,
                "returncode": int(observed.returncode),
                "state": "END",
                "stdout": stdout,
                "stderr": stderr,
                "reason": reason,
            },
            "compute_result": str(compute_path),
            "compute_result_sha256": _sha256_file(compute_path),
            "reservation_result": str(reservation_path),
            "reservation_result_sha256": _sha256_file(reservation_path),
            "driver_rc": driver_status,
            "scheduler_stdout": _file_record(
                job_root / "scheduler" / "job.stdout", root),
            "scheduler_stderr": _file_record(
                job_root / "scheduler" / "job.stderr", root),
        })
    validated_jobs = [
        _validate_completion_job(
            policy, job, attempt_id, root, current_pin,
            workload_id, submitted["request_id"], submitted,
            submission["job_body_sha256"],
        )
        for workload_id, job, submitted in zip(
            workload_ids(policy), jobs, submission["jobs"])
    ]
    all_succeeded = all(
        binding["driver_rc"] == 0 for binding in validated_jobs)
    manifest_path = None
    manifest_sha = None
    if all_succeeded:
        manifest_path = finalize_raw_manifest(policy, root, current_pin)
        manifest_sha = _sha256_file(manifest_path)
    completion = {
        "schema_version": COMPLETION_SCHEMA,
        "study": policy.study,
        "protocol_sha256": policy.protocol_sha256,
        "attempt_id": attempt_id,
        "attempt_root": str(root),
        "source_commit": submission["source_commit"],
        "current_pin": current_pin,
        "jobs": jobs,
        "raw_result_manifest": (
            str(manifest_path) if manifest_path is not None else None),
        "raw_result_manifest_sha256": manifest_sha,
    }
    completion_path = record_completion_receipt(
        policy, root, current_pin, completion)
    acquisition_path = record_acquisition_receipt(policy, root, current_pin)
    return completion_path, acquisition_path


def _cmake_directory(argv: Sequence[str], option: str) -> Path:
    values: list[str] = []
    for index, token in enumerate(argv):
        if token == option:
            if index + 1 >= len(argv):
                raise CertificationError(f"{option} has no directory")
            values.append(argv[index + 1])
        elif token.startswith(option) and token != option:
            values.append(token[len(option):])
    if len(values) != 1 or not values[0]:
        raise CertificationError(f"{option} must bind exactly one directory")
    return Path(values[0]).resolve()


def expected_controlled_defines(policy: Policy, cell_id: str) -> dict[str, str]:
    cell = policy.cell(cell_id)
    expected = dict(policy.document["controlled_define_base"])
    expected.update({
        "CCBENCH_BACK_OFF": str(cell.genome["BACK_OFF"]),
        "CCBENCH_BACKOFF_FIXED": str(cell.genome["BACKOFF_FIXED"]),
    })
    return expected


def _argv_controlled_defines(argv: Sequence[str],
                             define_argument: str) -> dict[str, str]:
    values: dict[str, str] = {}
    controlled_prefix = define_argument + "CCBENCH_"
    for token in argv:
        if token == define_argument:
            raise CertificationError("separated -D configure form is not canonical")
        if not token.startswith(controlled_prefix):
            continue
        key, separator, value = token[len(define_argument):].partition("=")
        if not separator or key in values:
            raise CertificationError("controlled define argv is malformed or duplicated")
        values[key] = value
    return values


def _run_workload_flags(argv: Sequence[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for token in argv[1:]:
        if not token.startswith("-"):
            continue
        key, separator, value = token[1:].partition("=")
        if not separator:
            continue
        if key in values:
            raise CertificationError("run argv contains a duplicated flag")
        values[key] = value
    return values


def _exact_trace0_configure_argv(
        policy: Policy, cell_id: str, argv: Sequence[str], build_dir: Path,
        toolchain: Mapping[str, Any],
) -> None:
    roles = {"cc", "cxx", "cmake"}
    entry_keys = {"requested", "realpath", "version_first_line"}
    if (type(toolchain) is not dict or set(toolchain) != roles
            or any(type(toolchain[role]) is not dict
                   or set(toolchain[role]) != entry_keys
                   or not all(type(value) is str and value
                              for value in toolchain[role].values())
                   for role in roles)):
        raise CertificationError("toolchain observation is not the v2 producer shape")
    if len(argv) < 10:
        raise CertificationError("configure argv is shorter than the v2 grammar")
    grammar = policy.document["trace0_cmake_argv"]["configure"]
    source_positions = [
        index for index, token in enumerate(argv)
        if token == grammar["source_option"]
    ]
    if len(source_positions) != 1 or source_positions[0] + 1 >= len(argv):
        raise CertificationError("configure argv needs one CCBench source root")
    source_root = _lexical_absolute_path(
        argv[source_positions[0] + 1], "CCBench source root")
    fixed = [
        toolchain["cmake"]["realpath"], grammar["source_option"],
        str(source_root), grammar["build_directory_option"], str(build_dir),
        *grammar["fixed_arguments"],
        *[
            argument["prefix"] + toolchain[argument["role"]]["realpath"]
            for argument in grammar["toolchain_arguments"]
        ],
    ]
    expected_defines = expected_controlled_defines(policy, cell_id)
    define_argument = grammar["controlled_define_argument"]
    ordered_define_tokens = [
        f"{define_argument}{key}={expected_defines[key]}"
        for key in sorted(expected_defines)
        if key != "CCBENCH_TRACE"
    ] + [
        f"{define_argument}CCBENCH_TRACE={expected_defines['CCBENCH_TRACE']}"
    ]
    tail = list(argv[len(fixed):])
    dependency_prefix = grammar["dependency_prefix_argument"]
    prefix = [token for token in tail if token.startswith(dependency_prefix)]
    if len(prefix) != 1 or not prefix[0].partition("=")[2]:
        raise CertificationError("configure argv needs one dependency prefix")
    expected = fixed + prefix + ordered_define_tokens
    if list(argv) != expected:
        raise CertificationError("configure argv does not match the closed v2 grammar")
    if _argv_controlled_defines(argv, define_argument) != expected_defines:
        raise CertificationError("configure argv controlled define map is not exact")


def _exact_trace0_build_argv(policy: Policy, argv: Sequence[str],
                             build_dir: Path,
                             toolchain: Mapping[str, Any]) -> None:
    grammar = policy.document["trace0_cmake_argv"]["build"]
    target = (
        grammar["target_prefix"]
        + policy.document["performance_common"]["ccbench_protocol"]
        + grammar["target_suffix"]
    )
    fixed = [
        toolchain["cmake"]["realpath"], grammar["subcommand"], str(build_dir),
        grammar["target_option"], target, grammar["jobs_option"],
    ]
    if (len(argv) != len(fixed) + 1
            or list(argv[:-1]) != fixed
            or not argv[-1].isdigit() or int(argv[-1]) <= 0):
        raise CertificationError("build argv does not match the closed v2 grammar")


def _exact_trace0_run_argv(policy: Policy, cell: CellSpec,
                           argv: Sequence[str], perf_binary: Path,
                           *, use_perf: bool) -> None:
    from ..calibrator.runner import PERF_EVENTS
    from . import env_contract

    contract = env_contract.lookup("pegasus")
    prefix = list(contract.numactl)
    if use_perf:
        prefix += ["perf", "stat", "-e", ",".join(PERF_EVENTS), "--"]
    expected_flags = [
        f"-thread_num={cell.perf['threads']}",
        f"-ycsb_tuple_num={cell.perf['records']}",
        f"-extime={cell.perf['extime']}",
        f"-clocks_per_us={contract.clocks_per_us}",
    ] + [
        f"-{key}={value}" for key, value in cell.perf["workload"].items()
    ]
    _require_run_binary_at_position(argv, len(prefix), perf_binary)
    expected = prefix + [str(perf_binary)] + expected_flags
    if list(argv) != expected:
        raise CertificationError("run argv does not match the closed producer grammar")
    if _run_workload_flags([str(perf_binary)] + expected_flags) != {
            token[1:].partition("=")[0]: token.partition("=")[2]
            for token in expected_flags}:
        raise CertificationError("run argv workload flags are not exact")


def _require_run_binary_at_position(
        argv: Sequence[str], binary_index: int, perf_binary: Path) -> None:
    if (type(binary_index) is not int or binary_index < 0
            or len(argv) <= binary_index
            or argv[binary_index] != str(perf_binary)):
        raise CertificationError(
            "run argv[0] after the canonical wrapper is not the binary")


def validate_trace0_evidence(policy: Policy, cell_id: str, attempt_id: str,
                             current_pin: str, evidence: object) -> dict[str, Any]:
    if type(evidence) is not dict:
        raise CertificationError("trace0 evidence must be an object")
    required = {
        "schema_version", "cell_id", "attempt_id", "current_pin",
        "source_commit", "controlled_defines", "configure_argv", "build_argv",
        "build_dir", "run_argv", "perf_binary", "perf_bin_sha256",
        "build_done", "toolchain", "use_perf", "compile_out_evidence_scope",
    }
    if set(evidence) != required:
        raise CertificationError("trace0 evidence is incomplete")
    if (evidence["schema_version"] != TRACE0_SCHEMA
            or evidence["cell_id"] != cell_id
            or evidence["attempt_id"] != attempt_id
            or evidence["current_pin"] != current_pin
            or evidence["source_commit"] != current_pin
            or evidence["compile_out_evidence_scope"] != COMPILE_OUT_SCOPE):
        raise CertificationError("trace0 evidence identity mismatch")
    expected = expected_controlled_defines(policy, cell_id)
    if evidence["controlled_defines"] != expected:
        raise CertificationError("controlled CCBENCH define map is not exact")
    configure = evidence["configure_argv"]
    build = evidence["build_argv"]
    run = evidence["run_argv"]
    if not all(type(argv) is list and argv and all(type(x) is str for x in argv)
               for argv in (configure, build, run)):
        raise CertificationError("trace0 argv evidence is malformed")
    if type(evidence["use_perf"]) is not bool:
        raise CertificationError("trace0 use_perf observation is not exact bool")
    build_dir = _lexical_absolute_path(evidence["build_dir"], "build directory")
    _reject_symlink_components(build_dir, "build directory")
    if not build_dir.is_dir():
        raise CertificationError("build directory is not a real directory")
    cmake_argv = policy.document["trace0_cmake_argv"]
    if (_cmake_directory(
            configure, cmake_argv["configure"]["build_directory_option"])
            != build_dir
            or _cmake_directory(build, cmake_argv["build"]["subcommand"])
            != build_dir):
        raise CertificationError("configure and build directories are not identical")
    _exact_trace0_configure_argv(
        policy, cell_id, configure, build_dir, evidence["toolchain"])
    _exact_trace0_build_argv(policy, build, build_dir, evidence["toolchain"])
    perf_binary = _lexical_absolute_path(
        evidence["perf_binary"], "performance binary")
    _reject_symlink_components(perf_binary, "performance binary")
    if not perf_binary.is_file():
        raise CertificationError("performance binary is not a regular file")
    expected_executable = (
        build_dir / "cc" / policy.document["performance_common"]["ccbench_protocol"]
        / f"ycsb_{policy.document['performance_common']['ccbench_protocol']}.exe")
    if perf_binary != expected_executable:
        raise CertificationError("performance binary is not the build canonical executable")
    cell = policy.cell(cell_id)
    _exact_trace0_run_argv(
        policy, cell, run, perf_binary, use_perf=evidence["use_perf"])
    actual_sha = _sha256_file(perf_binary)
    if _require_sha(evidence["perf_bin_sha256"], "perf_bin_sha256") != actual_sha:
        raise CertificationError("perf_bin_sha256 does not match binary bytes")
    build_done = evidence["build_done"]
    if (type(build_done) is not dict or set(build_done) != {
            "source_commit", "trace_bin_sha256", "perf_bin_sha256", "toolchain"}
            or build_done.get("source_commit") != current_pin
            or build_done.get("perf_bin_sha256") != actual_sha
            or build_done.get("toolchain") != evidence["toolchain"]
            or _SHA256_RE.fullmatch(str(build_done.get("trace_bin_sha256", ""))) is None
            or build_done.get("trace_bin_sha256") == actual_sha):
        raise CertificationError("trace/performance build_done binding is incomplete")
    return dict(evidence)


def validate_build_evidence(current_pin: str, evidence: object) -> dict[str, Any]:
    if type(evidence) is not dict:
        raise CertificationError("trace/performance build evidence is missing")
    required = {
        "source_commit", "trace_enabled_build", "performance_trace_disabled_build",
        "trace_bin_sha256", "perf_bin_sha256", "toolchain",
        "compile_out_evidence_scope",
    }
    if (set(evidence) != required
            or evidence["source_commit"] != current_pin
            or evidence["trace_enabled_build"] is not True
            or evidence["performance_trace_disabled_build"] is not True
            or evidence["compile_out_evidence_scope"] != COMPILE_OUT_SCOPE):
        raise CertificationError("trace/performance build evidence identity mismatch")
    trace_sha = _require_sha(evidence["trace_bin_sha256"], "trace_bin_sha256")
    perf_sha = _require_sha(evidence["perf_bin_sha256"], "perf_bin_sha256")
    if trace_sha == perf_sha:
        raise CertificationError("trace and performance builds are not separate")
    return dict(evidence)


def _expected_verify_flags(policy: Policy, cell: CellSpec, tag: str) -> dict[str, str]:
    if tag == LEGACY_TAG:
        return dict(policy.document["legacy_correctness"])
    perf = cell.perf
    return {
        "ycsb_tuple_num": str(perf["records"]),
        "thread_num": str(perf["threads"]),
        **dict(perf["workload"]),
        "extime": str(perf["extime"]),
    }


def _classify_verify_repetition(tag: str, raw: object,
                                build_attempt_id: str) -> str:
    if type(raw) is not dict:
        return "indeterminate"
    if (raw.get("tag") != tag or raw.get("trace_enabled") is not True
            or raw.get("build_attempt_id") != build_attempt_id):
        return "indeterminate"
    status = raw.get("status")
    if status == "pass":
        witness = raw.get("commit_witness")
        if (raw.get("certified") is True and raw.get("integrity") == "ok"
                and type(witness) is dict
                and type(witness.get("commit_counts")) is int
                and witness["commit_counts"] > 0
                and witness.get("batch_commit_counts") == 0
                and _SHA256_RE.fullmatch(str(raw.get("trace_binary_sha256", "")))):
            return "pass"
        return "indeterminate"
    if status == "anomaly":
        if (raw.get("certified") is False
                and raw.get("verdict") == "non-serializable"
                and type(raw.get("anomalies")) is list
                and len(raw["anomalies"]) > 0):
            return "anomaly"
        return "indeterminate"
    return "indeterminate"


def _classify_verify(tag: str, raw: object, build_attempt_id: str,
                     expected_reps: int) -> tuple[str, int]:
    if (type(raw) is not list or not raw or len(raw) > expected_reps
            or expected_reps <= 0):
        return "indeterminate", 0
    statuses = [
        _classify_verify_repetition(tag, repetition, build_attempt_id)
        for repetition in raw
    ]
    if "anomaly" in statuses:
        return "anomaly", len(statuses)
    if len(statuses) == expected_reps and all(
            status == "pass" for status in statuses):
        return "pass", len(statuses)
    return "indeterminate", len(statuses)


def _classify_performance(policy: Policy, cell: CellSpec, raw: object,
                          build_attempt_id: str,
                          expected_binary_sha256: str) -> tuple[str, Optional[float]]:
    if type(raw) is not dict:
        return "performance-indeterminate", None
    if (raw.get("trace_enabled") is not False
            or raw.get("build_attempt_id") != build_attempt_id
            or raw.get("workload") != dict(cell.perf)
            or raw.get("perf_bin_sha256") != expected_binary_sha256
            or raw.get("status") != "complete"
            or raw.get("unstable") is not False
            or raw.get("rep_notes") != []):
        return "performance-indeterminate", None
    samples = raw.get("samples_tps")
    if (type(samples) is not list or len(samples) != cell.perf["reps"]
            or not all(type(value) in {int, float} and math.isfinite(value)
                       and value > 0 for value in samples)):
        return "performance-indeterminate", None
    median = float(statistics.median(samples))
    if not math.isfinite(median):
        return "performance-indeterminate", None
    return "complete", median


def collect_results(policy: Policy, raw_results: Iterable[Mapping[str, Any]],
                    *, attempt_id: str, current_pin: str,
                    request_ids: Mapping[str, str],
                    frozen_files: Optional[Mapping[str, bytes]] = None,
                    attempt_root: Optional[Path] = None,
                    _test_token: object = None) -> dict[str, Any]:
    if type(request_ids) is not dict or list(request_ids) != list(workload_ids(policy)):
        raise CertificationError("request ID mapping is not in exact policy order")
    normalized_request_ids = {
        workload_id: _normalize_request_id(request_ids[workload_id])
        for workload_id in workload_ids(policy)}
    if len(set(normalized_request_ids.values())) != len(normalized_request_ids):
        raise CertificationError("certification request IDs must be distinct")
    raw_list = list(raw_results)
    if len(raw_list) != len(policy.cells):
        raise CertificationError("raw result count does not match exact four-cell protocol")
    indexed: dict[str, Mapping[str, Any]] = {}
    for raw in raw_list:
        required_raw = {
            "schema_version", "protocol_sha256", "attempt_id", "current_pin",
            "cell_id", "genome", "campaign_preimage", "campaign_evidence",
            "variant", "build_attempt_id", "build_evidence", "correctness",
            "performance", "trace0_evidence", "terminal", "abort",
        }
        if (type(raw) is not dict or not required_raw.issubset(raw)
                or raw.get("schema_version") != RAW_RESULT_SCHEMA):
            raise CertificationError("raw cell result schema mismatch")
        cell_id = raw.get("cell_id")
        if cell_id in indexed:
            raise CertificationError("duplicate cell result")
        if (cell_id not in {cell.cell_id for cell in policy.cells}
                or raw.get("attempt_id") != attempt_id
                or raw.get("current_pin") != current_pin
                or raw.get("protocol_sha256") != policy.protocol_sha256):
            raise CertificationError("extra or cross-attempt cell result")
        indexed[cell_id] = raw
    if set(indexed) != {cell.cell_id for cell in policy.cells}:
        raise CertificationError("cell result set is incomplete")

    cells: list[dict[str, Any]] = []
    any_anomaly = False
    any_indeterminate = False
    any_performance_indeterminate = False
    medians: dict[tuple[str, str], float] = {}
    for cell in policy.cells:
        raw = indexed[cell.cell_id]
        expected_preimage = campaign_preimage(
            policy, cell.workload_id, attempt_id, current_pin)
        observed_preimage = raw.get("campaign_preimage")
        from . import ident
        if (type(observed_preimage) is not dict
                or set(observed_preimage) != (
                    set(expected_preimage) | {ident.ADMISSION_POLICY_SEARCH_KEY})
                or any(observed_preimage.get(key) != value
                       for key, value in expected_preimage.items())):
            raise CertificationError("campaign preimage and protocol differ")
        perf = perf_config_for_cell(policy, cell.cell_id)
        validate_campaign_binding(
            policy, cell.workload_id, attempt_id, current_pin,
            expected_preimage, perf,
        )
        if _test_token is not _COLLECT_TEST_TOKEN:
            campaign_evidence = raw.get("campaign_evidence")
            if type(campaign_evidence) is not dict or set(campaign_evidence) != {
                    "campaign_id", "lock_path", "lock_sha256", "wal_path",
                    "wal_sha256", "claim_path", "claim_sha256"}:
                raise CertificationError("campaign lock/WAL evidence is incomplete")
            layout_root = str(Path(campaign_evidence["lock_path"]).parent)
            reconstructed = _raw_cell_from_wal(
                policy, cell, result=SimpleNamespace(variant=raw.get("variant")),
                layout_root=layout_root, attempt_id=attempt_id,
                current_pin=current_pin, frozen_files=frozen_files,
                attempt_root=attempt_root,
            )
            authority_keys = {
                "schema_version", "protocol_sha256", "attempt_id", "current_pin",
                "cell_id", "genome", "campaign_preimage", "campaign_evidence",
                "variant", "build_attempt_id", "build_evidence", "correctness",
                "performance", "trace0_evidence", "terminal", "abort",
            }
            if any(raw.get(key) != reconstructed.get(key) for key in authority_keys):
                raise CertificationError("raw cell differs from canonical campaign WAL")
        if raw.get("genome") != dict(cell.genome):
            raise CertificationError("cell genome and protocol differ")
        build_attempt_id = raw.get("build_attempt_id")
        if type(build_attempt_id) is not str or not build_attempt_id:
            raise CertificationError("build attempt identity is missing")
        build_evidence = validate_build_evidence(
            current_pin, raw.get("build_evidence"))
        correctness = raw.get("correctness")
        if type(correctness) is not dict:
            legacy_status = performance_status = "indeterminate"
            legacy_reps = performance_reps = 0
        else:
            legacy_status, legacy_reps = _classify_verify(
                LEGACY_TAG, correctness.get(LEGACY_TAG), build_attempt_id, 1,
            )
            performance_status, performance_reps = _classify_verify(
                PERFORMANCE_TAG, correctness.get(PERFORMANCE_TAG),
                build_attempt_id, cell.perf["reps"],
            )
        if "anomaly" in {legacy_status, performance_status}:
            correctness_status = "non-serializable"
            disposition = "reject"
            any_anomaly = True
        elif legacy_status == performance_status == "pass":
            correctness_status = "certified"
            disposition = "pass"
        else:
            correctness_status = "indeterminate"
            disposition = "indeterminate"
            any_indeterminate = True
        trace0_raw = raw.get("trace0_evidence")
        if correctness_status == "non-serializable" and trace0_raw is None:
            trace0 = None
            perf_status, median = "performance-indeterminate", None
        else:
            trace0 = validate_trace0_evidence(
                policy, cell.cell_id, attempt_id, current_pin, trace0_raw)
            if (trace0["perf_bin_sha256"] != build_evidence["perf_bin_sha256"]
                    or trace0["build_done"]["trace_bin_sha256"]
                    != build_evidence["trace_bin_sha256"]):
                raise CertificationError("trace0 evidence and build evidence differ")
            perf_status, median = _classify_performance(
                policy, cell, raw.get("performance"), build_attempt_id,
                trace0["perf_bin_sha256"],
            )
        if perf_status != "complete":
            any_performance_indeterminate = True
        elif correctness_status == "certified" and median is not None:
            medians[(cell.workload_id, cell.role)] = median
        cells.append({
            "cell_id": cell.cell_id,
            "workload": cell.workload_id,
            "role": cell.role,
            "genome": dict(cell.genome),
            "build_attempt_id": build_attempt_id,
            "correctness": {
                "legacy": legacy_status,
                "performance": performance_status,
                "legacy_repetitions_observed": legacy_reps,
                "performance_repetitions_observed": performance_reps,
                "workload_argv_observation": "not-independently-recorded-by-existing-pipeline",
                "status": correctness_status,
                "disposition": disposition,
            },
            "performance": {"status": perf_status, "median_tps": median},
            "trace_bin_sha256": (
                trace0["build_done"]["trace_bin_sha256"] if trace0
                else build_evidence["trace_bin_sha256"]),
            "perf_bin_sha256": (
                trace0["perf_bin_sha256"] if trace0
                else build_evidence["perf_bin_sha256"]),
        })

    effects: dict[str, float] = {}
    for workload_id in {cell.workload_id for cell in policy.cells}:
        stock = medians.get((workload_id, "stock"))
        adopted = medians.get((workload_id, "adopted"))
        if stock is not None and adopted is not None:
            effect = adopted / stock - 1.0
            if math.isfinite(effect):
                effects[workload_id] = effect
            else:
                any_performance_indeterminate = True
    if any_anomaly:
        status = "reject"
    elif any_indeterminate:
        status = "indeterminate"
    elif any_performance_indeterminate:
        status = "performance-indeterminate"
    elif len(effects) != len(policy.document["workloads"]):
        status = "performance-indeterminate"
    elif all(effect > 0 for effect in effects.values()):
        status = "observed-positive"
    else:
        status = "reject"
    return {
        "schema_version": CERTIFICATION_SCHEMA,
        "study": policy.study,
        "protocol_schema": POLICY_SCHEMA,
        "protocol_sha256": policy.protocol_sha256,
        "policy_sha256": policy.bytes_sha256,
        "policy_bytes_base64": base64.b64encode(policy.raw_bytes).decode("ascii"),
        "attempt_id": attempt_id,
        "request_ids": normalized_request_ids,
        "current_pin": current_pin,
        "historical_context": {
            "ccbench_commit": policy.document["historical_reference"]["ccbench_commit"],
            "comparison_input": False,
        },
        "cells": cells,
        "effects": effects,
        "status": status,
        "a4_noise_floor_status": "open",
        "legacy_role": "historically inherited companion",
        "smallest_observed_sufficient_in_this_two_point_protocol": None,
        "global_minimality_established": False,
        "compile_out_evidence_scope": COMPILE_OUT_SCOPE,
        "independent_observation_limits": {
            "correctness_run_argv": "not-recorded-by-existing-pipeline",
            "correctness_workload_binding": (
                "campaign-lock-and-pipeline-constructor; not an independent argv observation"
            ),
        },
    }


def driver_rc(report: Mapping[str, Any]) -> int:
    status = report.get("status")
    if status in {"observed-positive", "reject"}:
        return 0
    if status in {"indeterminate", "performance-indeterminate"}:
        return 2
    raise CertificationError("unknown report status")


def _raw_verify_record(policy: Policy, cell: CellSpec, tag: str,
                       payload: Optional[Mapping[str, Any]],
                       abort_payload: Optional[Mapping[str, Any]],
                       build_attempt_id: str,
                       trace_bin_sha256: Optional[str]) -> dict[str, Any]:
    base = {
        "tag": tag,
        "trace_enabled": True,
        "build_attempt_id": build_attempt_id,
        "trace_binary_sha256": trace_bin_sha256,
    }
    if payload is None:
        return {**base, "status": "indeterminate", "certified": False,
                "reason": (abort_payload or {}).get("reason", "verify-missing")}
    verdict = payload.get("verdict")
    if payload.get("certified") is True:
        return {
            **base,
            "status": "pass",
            "certified": True,
            "integrity": "ok",
            "verdict": verdict,
            "commit_witness": payload.get("commit_witness"),
        }
    verify = (abort_payload or {}).get("verify")
    anomalies = verify.get("anomalies") if type(verify) is dict else None
    if verdict == "non-serializable" and type(anomalies) is list and anomalies:
        return {
            **base,
            "status": "anomaly",
            "certified": False,
            "verdict": verdict,
            "anomalies": anomalies,
        }
    return {
        **base,
        "status": "indeterminate",
        "certified": False,
        "verdict": verdict,
        "reason": (abort_payload or {}).get("reason", "verifier-integrity"),
    }


def _event_payload(records: Sequence[object], stage: str,
                   build_attempt_id: str) -> Optional[Mapping[str, Any]]:
    matches = [record.payload for record in records
               if record.stage == stage
               and record.payload.get("build_attempt_id") == build_attempt_id]
    if len(matches) > 1:
        raise CertificationError(f"duplicate {stage} event in fresh attempt")
    return matches[0] if matches else None


def _campaign_config_binding(
        policy: Policy, workload_id: str, attempt_id: str, current_pin: str,
        observed_preimage: object) -> tuple[str, str]:
    """Reconstruct the bound campaign identity and its full protocol digest."""
    from . import ident
    from .model import CampaignConfig

    expected = campaign_preimage(policy, workload_id, attempt_id, current_pin)
    if (type(observed_preimage) is not dict
            or set(observed_preimage)
            != set(expected) | {ident.ADMISSION_POLICY_SEARCH_KEY}
            or any(observed_preimage.get(key) != value
                   for key, value in expected.items())):
        raise CertificationError("campaign preimage and protocol differ")
    cfg = CampaignConfig(
        spec_slug=f"paper-story-a2-{workload_id}",
        search_tag=f"{policy.study}-{workload_id}",
        spec_content=_canonical_json(expected).decode("ascii"),
        ccbench_commit=current_pin,
        search_config=dict(observed_preimage),
        trial=attempt_id,
    )
    return (
        str(ident.campaign_id(cfg)),
        hashlib.sha256(
            ident.canonical_preimage(cfg).encode("utf-8")
        ).hexdigest(),
    )


def _campaign_observation(
        policy: Policy, cell: CellSpec, layout_root: str, attempt_id: str,
        current_pin: str, *, lock_bytes: Optional[bytes] = None,
        wal_bytes: Optional[bytes] = None,
        claim_bytes: Optional[bytes] = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    from . import campaign_lock as campaign_lock_codec
    from . import ident
    from .layout import CampaignLayout

    layout_path = _lexical_absolute_path(layout_root, "campaign layout root")
    expected_campaign_parent = workload_job_root(
        policy, policy.durable_base / attempt_id, cell.workload_id) / "campaigns"
    if layout_path.parent != expected_campaign_parent:
        raise CertificationError("campaign layout is not the canonical attempt child")
    layout = CampaignLayout(str(layout_path))
    lock_path = _canonical_child(layout.lock_file, policy.durable_base / attempt_id,
                                 "campaign lock")
    wal_path = _canonical_child(layout.wal_file, policy.durable_base / attempt_id,
                                "campaign WAL")
    try:
        observed_lock_bytes = lock_path.read_bytes() if lock_bytes is None else lock_bytes
        observed_wal_bytes = wal_path.read_bytes() if wal_bytes is None else wal_bytes
        decoded = campaign_lock_codec.decode_campaign_lock_bytes(observed_lock_bytes)
    except (OSError, campaign_lock_codec.CampaignLockCodecError) as exc:
        raise CertificationError("campaign lock cannot be decoded") from exc
    if not decoded.is_v2:
        raise CertificationError("official A-2 campaign requires a v2 campaign lock")
    identity = decoded.identity
    expected = campaign_preimage(policy, cell.workload_id, attempt_id, current_pin)
    observed = identity.get("search_config")
    expected_search_tag = f"{policy.study}-{cell.workload_id}"
    if (type(observed) is not dict
            or set(observed) != set(expected) | {ident.ADMISSION_POLICY_SEARCH_KEY}
            or any(observed.get(key) != value for key, value in expected.items())
            or identity.get("spec_content") != _canonical_json(expected).decode("ascii")
            or identity.get("ccbench_commit") != current_pin
            or identity.get("search_tag") != expected_search_tag
            or identity.get("trial") != attempt_id):
        raise CertificationError("campaign lock identity does not match A-2 protocol")
    campaign_id, expected_protocol_digest = _campaign_config_binding(
        policy, cell.workload_id, attempt_id, current_pin, observed)
    if campaign_id != layout_path.name:
        raise CertificationError("campaign layout name differs from lock identity")
    claim_path = raw_result_claim_path(
        policy, cell.workload_id, policy.durable_base / attempt_id,
        layout_path.name)
    claim_path = _canonical_child(
        str(claim_path), policy.durable_base / attempt_id, "campaign claim")
    observed_claim_bytes = (
        claim_path.read_bytes() if claim_bytes is None else claim_bytes)
    claim = _decode_campaign_claim(observed_claim_bytes, "campaign claim")
    if claim["protocol_digest"] != expected_protocol_digest:
        raise CertificationError(
            "campaign claim protocol digest differs from campaign config")
    evidence = {
        "campaign_id": layout_path.name,
        "lock_path": str(lock_path),
        "lock_sha256": _sha256_bytes(observed_lock_bytes),
        "wal_path": str(wal_path),
        "wal_sha256": _sha256_bytes(observed_wal_bytes),
        "claim_path": str(claim_path),
        "claim_sha256": _sha256_bytes(observed_claim_bytes),
    }
    return dict(observed), evidence


def _observed_perf_workload(run_argv: Sequence[str], binary_index: int,
                            reps: int) -> dict[str, Any]:
    flags = _run_workload_flags(run_argv[binary_index:])
    required = {
        "thread_num", "ycsb_tuple_num", "extime", "clocks_per_us",
        *_PERF_WORKLOAD_KEYS,
    }
    if set(flags) != required:
        raise CertificationError("observed run command flags are not closed")
    try:
        return {
            "records": int(flags["ycsb_tuple_num"]),
            "threads": int(flags["thread_num"]),
            "workload": {key: flags[key] for key in _PERF_WORKLOAD_KEYS},
            "extime": int(flags["extime"]),
            "reps": reps,
        }
    except (TypeError, ValueError) as exc:
        raise CertificationError("observed run command numeric flags are malformed") from exc


def _raw_cell_from_wal(policy: Policy, cell: CellSpec, *, result: object,
                       layout_root: str, attempt_id: str,
                       current_pin: str,
                       frozen_files: Optional[Mapping[str, bytes]] = None,
                       attempt_root: Optional[Path] = None) -> dict[str, Any]:
    from .layout import CampaignLayout
    from .model import (STAGE_ABORT, STAGE_BENCH_DONE, STAGE_BUILD_DONE,
                        STAGE_BUILD_START, STAGE_COMMIT, STAGE_VERIFY_DONE)
    from .pipeline import variant_id
    from . import wal

    lock_bytes = wal_bytes = claim_bytes = None
    if frozen_files is not None:
        if attempt_root is None:
            raise CertificationError("frozen campaign bytes need an attempt root")
        layout = CampaignLayout(layout_root)
        try:
            lock_rel = Path(layout.lock_file).relative_to(attempt_root).as_posix()
            wal_rel = Path(layout.wal_file).relative_to(attempt_root).as_posix()
            claim_rel = Path(
                raw_result_claim_path(policy, cell.workload_id, attempt_root,
                                      Path(layout_root).name)
            ).relative_to(attempt_root).as_posix()
            lock_bytes = frozen_files[lock_rel]
            wal_bytes = frozen_files[wal_rel]
            claim_bytes = frozen_files[claim_rel]
        except (KeyError, ValueError) as exc:
            raise CertificationError("frozen campaign lock/WAL bytes are missing") from exc
    observed_preimage, campaign_evidence = _campaign_observation(
        policy, cell, layout_root, attempt_id, current_pin,
        lock_bytes=lock_bytes, wal_bytes=wal_bytes, claim_bytes=claim_bytes)
    if wal_bytes is None:
        all_records = wal.read_records(CampaignLayout(layout_root))
    else:
        if wal_bytes and not wal_bytes.endswith(b"\n"):
            raise CertificationError("frozen campaign WAL is not newline terminated")
        try:
            all_records = [
                wal.parse_line(frame.decode("utf-8"))
                for frame in wal_bytes.splitlines(keepends=True)
            ]
        except (UnicodeError, ValueError) as exc:
            raise CertificationError("frozen campaign WAL cannot be parsed") from exc
    expected_genome = _genome_for_cell(policy, cell)
    expected_variant = variant_id(expected_genome)
    if result.variant != expected_variant:
        raise CertificationError("WAL variant is not the canonical cell variant")
    records = [record for record in all_records if record.variant == result.variant]
    starts = [record for record in records if record.stage == STAGE_BUILD_START]
    if len(starts) != 1:
        raise CertificationError("fresh cell does not have one build attempt")
    build_attempt_id = starts[0].payload.get("build_attempt_id")
    if type(build_attempt_id) is not str or not build_attempt_id:
        raise CertificationError("WAL build attempt identity is missing")
    if starts[0].payload.get("genome") != expected_genome.canonical():
        raise CertificationError("WAL build start genome does not match cell policy")
    allowed_stages = {
        STAGE_BUILD_START, STAGE_BUILD_DONE, STAGE_VERIFY_DONE,
        STAGE_BENCH_DONE, STAGE_COMMIT, STAGE_ABORT,
    }
    if (any(record.stage not in allowed_stages for record in records)
            or any(record.stage != STAGE_BUILD_START
                   and record.payload.get("build_attempt_id") != build_attempt_id
                   for record in records)):
        raise CertificationError("WAL cell attempt contains an unknown or cross-attempt event")
    build_done = _event_payload(records, STAGE_BUILD_DONE, build_attempt_id)
    bench_done = _event_payload(records, STAGE_BENCH_DONE, build_attempt_id)
    commit = _event_payload(records, STAGE_COMMIT, build_attempt_id)
    abort = _event_payload(records, STAGE_ABORT, build_attempt_id)
    if (commit is None) == (abort is None):
        raise CertificationError("WAL cell attempt must have exactly one terminal event")
    stage_order = [record.stage for record in records]
    start_index = stage_order.index(STAGE_BUILD_START)
    build_index = (
        stage_order.index(STAGE_BUILD_DONE) if build_done is not None else None)
    terminal_stage = STAGE_COMMIT if commit is not None else STAGE_ABORT
    terminal_index = stage_order.index(terminal_stage)
    if start_index != 0 or terminal_index != len(stage_order) - 1:
        raise CertificationError("WAL cell attempt does not have canonical boundaries")
    if commit is not None and (build_index is None or bench_done is None):
        raise CertificationError("committed WAL cell lacks build or bench evidence")
    if build_index is not None:
        middle = stage_order[build_index + 1:terminal_index]
        if build_index <= start_index or any(
                stage not in {STAGE_VERIFY_DONE, STAGE_BENCH_DONE}
                for stage in middle):
            raise CertificationError("WAL cell stage order is not canonical")
        bench_positions = [
            index for index, stage in enumerate(stage_order)
            if stage == STAGE_BENCH_DONE]
        verify_positions = [
            index for index, stage in enumerate(stage_order)
            if stage == STAGE_VERIFY_DONE]
        if bench_positions and verify_positions and max(verify_positions) > min(bench_positions):
            raise CertificationError("WAL verify evidence appears after benchmark evidence")
    verify_payloads = [record.payload for record in records
                       if record.stage == STAGE_VERIFY_DONE
                       and record.payload.get("build_attempt_id") == build_attempt_id]
    by_tag: dict[str, list[Mapping[str, Any]]] = {}
    for payload in verify_payloads:
        workload = payload.get("workload")
        tag = workload.get("tag") if type(workload) is dict else None
        if tag not in {LEGACY_TAG, PERFORMANCE_TAG}:
            raise CertificationError("WAL verify tag is missing or unknown")
        by_tag.setdefault(tag, []).append(payload)

    trace_sha = build_done.get("trace_bin_sha256") if build_done else None
    correctness = {
        LEGACY_TAG: [
            _raw_verify_record(
                policy, cell, LEGACY_TAG, payload, abort,
                build_attempt_id, trace_sha,
            ) for payload in by_tag.get(LEGACY_TAG, [])
        ],
        PERFORMANCE_TAG: [
            _raw_verify_record(
                policy, cell, PERFORMANCE_TAG, payload, abort,
                build_attempt_id, trace_sha,
            ) for payload in by_tag.get(PERFORMANCE_TAG, [])
        ],
    }
    trace0: Optional[dict[str, Any]] = None
    performance: dict[str, Any] = {
        "status": "indeterminate",
        "trace_enabled": False,
        "build_attempt_id": build_attempt_id,
        "workload": None,
        "reason": (abort or {}).get("reason", "performance-missing"),
    }
    if build_done is not None and bench_done is not None:
        configure = build_done.get("perf_configure_cmd")
        build = build_done.get("perf_build_cmd")
        run = bench_done.get("run_cmd")
        if type(configure) is str:
            configure = shlex.split(configure)
        elif type(configure) is tuple:
            configure = list(configure)
        if type(build) is str:
            build = shlex.split(build)
        elif type(build) is tuple:
            build = list(build)
        if type(run) is str:
            run = shlex.split(run)
        elif type(run) is tuple:
            run = list(run)
        if (type(configure) is list and type(build) is list
                and type(run) is list and run):
            build_directory_option = policy.document[
                "trace0_cmake_argv"]["configure"]["build_directory_option"]
            build_dir = _cmake_directory(configure, build_directory_option)
            try:
                separator_index = run.index("--")
            except ValueError:
                separator_index = -1
            use_perf = separator_index >= 0
            if use_perf:
                binary_index = separator_index + 1
            else:
                from . import env_contract
                binary_index = len(env_contract.lookup("pegasus").numactl)
            if binary_index >= len(run):
                raise CertificationError("run command has no CCBench argv after wrapper")
            perf_binary = _lexical_absolute_path(
                run[binary_index], "observed performance binary")
            samples = bench_done.get("tps")
            observed_workload = _observed_perf_workload(
                run, binary_index,
                len(samples) if type(samples) is list else 0,
            )
            trace0 = {
                "schema_version": TRACE0_SCHEMA,
                "cell_id": cell.cell_id,
                "attempt_id": attempt_id,
                "current_pin": current_pin,
                "source_commit": current_pin,
                "controlled_defines": expected_controlled_defines(
                    policy, cell.cell_id),
                "configure_argv": list(configure),
                "build_argv": list(build),
                "build_dir": str(build_dir),
                "run_argv": list(run),
                "perf_binary": str(perf_binary),
                "perf_bin_sha256": build_done.get("perf_bin_sha256"),
                "toolchain": build_done.get("toolchain"),
                "use_perf": use_perf,
                "build_done": {
                    "source_commit": current_pin,
                    "trace_bin_sha256": build_done.get("trace_bin_sha256"),
                    "perf_bin_sha256": build_done.get("perf_bin_sha256"),
                    "toolchain": build_done.get("toolchain"),
                },
                "compile_out_evidence_scope": COMPILE_OUT_SCOPE,
            }
            performance = {
                "status": "complete" if commit is not None else "indeterminate",
                "trace_enabled": False,
                "build_attempt_id": build_attempt_id,
                "workload": observed_workload,
                "perf_bin_sha256": build_done.get("perf_bin_sha256"),
                "samples_tps": samples,
                "unstable": bench_done.get("unstable"),
                "rep_notes": bench_done.get("rep_notes"),
            }
    return {
        "schema_version": RAW_RESULT_SCHEMA,
        "protocol_sha256": policy.protocol_sha256,
        "attempt_id": attempt_id,
        "current_pin": current_pin,
        "cell_id": cell.cell_id,
        "genome": dict(cell.genome),
        "campaign_preimage": observed_preimage,
        "campaign_evidence": campaign_evidence,
        "variant": result.variant,
        "build_attempt_id": build_attempt_id,
        "build_evidence": ({
            "source_commit": current_pin,
            "trace_enabled_build": True,
            "performance_trace_disabled_build": True,
            "trace_bin_sha256": build_done.get("trace_bin_sha256"),
            "perf_bin_sha256": build_done.get("perf_bin_sha256"),
            "toolchain": build_done.get("toolchain"),
            "compile_out_evidence_scope": COMPILE_OUT_SCOPE,
        } if build_done is not None else None),
        "correctness": correctness,
        "performance": performance,
        "trace0_evidence": trace0,
        "terminal": "commit" if commit is not None else "abort",
        "abort": dict(abort) if abort is not None else None,
    }


def run_workload(policy: Policy, *, workload_id: str, attempt_root: Path | str,
                 raw_root: Path | str, current_pin: str,
                 dependency_prefix: Path | str, ccbench_dir: Path | str,
                 log=print) -> object:
    """Run one ordered stock/adopted workload pair through run_campaign()."""
    from . import env_contract
    from .build_admission import GeneratorId, build_run_context
    from .layout import (DurableRootPolicy, env_scope_dir,
                         resolve_campaign_output_root)
    from .loop import run_campaign
    from .model import CampaignConfig

    attempt_name, attempt = validate_attempt_root(policy, attempt_root)
    if attempt_name != attempt.name:
        raise CertificationError("attempt identity mismatch")
    raw = Path(raw_root).resolve(strict=True)
    job_root = workload_job_root(policy, attempt, workload_id)
    if raw != job_root / "raw" or raw.is_symlink() or not raw.is_dir():
        raise CertificationError("raw root is not the exact workload job child")
    dependency = Path(dependency_prefix).resolve(strict=True)
    if dependency.is_symlink() or not dependency.is_dir():
        raise CertificationError("dependency prefix is unavailable")
    source_root = Path(ccbench_dir).resolve(strict=True)
    if source_root.is_symlink() or not source_root.is_dir():
        raise CertificationError("CCBench source root is unavailable")
    observed_pin = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=source_root, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    dirty_source = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=source_root, check=True, capture_output=True, text=True,
    ).stdout
    if observed_pin != current_pin or dirty_source:
        raise CertificationError("CCBench current pin or clean-tree binding failed")
    cells = [cell for cell in policy.cells if cell.workload_id == workload_id]
    if len(cells) != 2 or [cell.role for cell in cells] != ["stock", "adopted"]:
        raise CertificationError("workload execution is not stock then adopted")
    for cell in cells:
        if (raw / f"{cell.cell_id}.json").exists():
            raise CertificationError("outer attempt is create-only; retry is disabled")

    preimage = campaign_preimage(policy, workload_id, attempt_name, current_pin)
    perf = perf_config_for_cell(policy, cells[0].cell_id)
    validate_campaign_binding(
        policy, workload_id, attempt_name, current_pin, preimage, perf)
    genomes = [_genome_for_cell(policy, cell) for cell in cells]
    cfg = CampaignConfig(
        spec_slug=f"paper-story-a2-{workload_id}",
        search_tag=f"{policy.study}-{workload_id}",
        spec_content=_canonical_json(preimage).decode("ascii"),
        ccbench_commit=current_pin,
        search_config=preimage,
        trial=attempt_name,
    )
    contract = env_contract.lookup("pegasus")
    authorization = env_contract.authorize("pegasus")
    output_root = job_root
    cache_root = job_root / "cache"
    if (output_root.is_symlink() or not output_root.is_dir()
            or (job_root / "campaigns").is_symlink()
            or not (job_root / "campaigns").is_dir()
            or cache_root.is_symlink() or not cache_root.is_dir()):
        raise CertificationError("workload campaign or cache root is unavailable")
    resolved_output = resolve_campaign_output_root("official", str(output_root))
    claim_root = Path(env_scope_dir(contract.env_tag, resolved_output)) / "claims"
    claim_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    durable_policy = DurableRootPolicy(
        approved_roots=(policy.durable_base,),
        forbidden_roots=(Path("/tmp"), Path("/scr")),
    )
    resolved_cc, resolved_cxx = buildcache.compilers_for_current_site()
    expected_toolchain_manifest = buildcache.observed_toolchain_manifest(
        resolved_cc, resolved_cxx,
    )
    summary = run_campaign(
        cfg, genomes, perf, contract.env_tag, contract.clocks_per_us,
        numactl=contract.numactl, do_bench=True, output_root=str(output_root),
        log=log, ccbench_dir=str(source_root), env_contract=contract,
        dependency_prefix=str(dependency),
        authorization_contract=authorization,
        cache_root=str(cache_root),
        build_context=build_run_context(generator_id=GeneratorId.BACKOFF_REPRO),
        declared_use_class="official",
        expected_toolchain_manifest=expected_toolchain_manifest,
        durable_root_policy=durable_policy,
    )
    if len(summary.results) != len(cells) or summary.skipped != 0:
        raise CertificationError("fresh workload did not evaluate exactly two cells")
    raw_payloads = []
    for cell, result in zip(cells, summary.results):
        payload = _raw_cell_from_wal(
            policy, cell, result=result, layout_root=summary.layout_root,
            attempt_id=attempt_name, current_pin=current_pin,
        )
        write_json_x(raw / f"{cell.cell_id}.json", payload)
        raw_payloads.append(payload)
    _fsync_dir(raw)
    for payload in raw_payloads:
        if payload["terminal"] != "abort":
            continue
        statuses = {
            repetition.get("status")
            for tag in (LEGACY_TAG, PERFORMANCE_TAG)
            for repetition in payload["correctness"][tag]
        }
        if "anomaly" not in statuses:
            raise CertificationError(
                "workload evidence, infrastructure, or performance is incomplete")
    return summary


_CAMPAIGN_CLAIM_KEYS = {
    "campaign_identity", "protocol_digest", "job_id", "host", "boot_id",
    "pid", "proc_starttime", "created_utc",
}


def _decode_campaign_claim(raw: bytes, label: str) -> dict[str, Any]:
    claim = _loads_json(raw, label)
    if type(claim) is not dict or set(claim) != _CAMPAIGN_CLAIM_KEYS:
        raise CertificationError("campaign claim schema is not exact")
    if (not all(type(claim[key]) is str and claim[key]
                for key in ("campaign_identity", "job_id", "host", "boot_id",
                            "created_utc"))
            or _SHA256_RE.fullmatch(str(claim["protocol_digest"])) is None
            or any(type(claim[key]) is not int or claim[key] <= 0
                   for key in ("pid", "proc_starttime"))):
        raise CertificationError("campaign claim identity is malformed")
    return claim


def _validate_claim_reservation_binding(
        claim: Mapping[str, Any], *, campaign_id: str, request_id: str,
        reservation_binding: object, expected_protocol_digest: str) -> None:
    if claim.get("protocol_digest") != expected_protocol_digest:
        raise CertificationError(
            "campaign claim protocol digest differs from campaign config")
    if (_normalize_request_id(claim.get("job_id")) != request_id
            or _normalize_request_id(getattr(reservation_binding, "job_id", None))
            != request_id
            or claim.get("host") != getattr(reservation_binding, "host", None)
            or claim.get("boot_id") != getattr(reservation_binding, "boot_id", None)
            or claim.get("campaign_identity") != campaign_id):
        raise CertificationError(
            "campaign claim differs from submission or reservation")


def load_raw_results(policy: Policy, attempt_root: Path) -> list[dict[str, Any]]:
    """Open the exact cells after closing each job-local raw namespace."""
    results: list[dict[str, Any]] = []
    for workload_id in workload_ids(policy):
        raw_root = workload_job_root(policy, attempt_root, workload_id) / "raw"
        expected_names = {
            f"{cell.cell_id}.json" for cell in policy.cells
            if cell.workload_id == workload_id
        }
        if raw_root.is_symlink() or not raw_root.is_dir():
            raise CertificationError(
                "job-local raw directory inventory is not closed")
        try:
            entries = list(os.scandir(raw_root))
        except OSError as exc:
            raise CertificationError(
                "job-local raw directory cannot be inspected") from exc
        if ({entry.name for entry in entries} != expected_names
                or any(entry.is_symlink()
                       or not entry.is_file(follow_symlinks=False)
                       for entry in entries)):
            raise CertificationError(
                "job-local raw directory inventory is not closed")
        for cell in policy.cells:
            if cell.workload_id == workload_id:
                results.append(_read_json(raw_root / f"{cell.cell_id}.json")[0])
    by_cell = {str(raw.get("cell_id")): raw for raw in results}
    if set(by_cell) != {cell.cell_id for cell in policy.cells}:
        raise CertificationError("job-local raw cell inventory is not exact")
    results = [by_cell[cell.cell_id] for cell in policy.cells]
    return results


def finalize_raw_manifest(policy: Policy, attempt_root: Path | str,
                          current_pin: str) -> Path:
    attempt_id, root = validate_attempt_root(policy, attempt_root)
    # Loading closes each independently owned job-local raw directory, without
    # enumerating the shared jobs/ parent, then opens the four policy paths.
    # The manifest freezes those bytes and both lock/WAL/claim triples.
    raw_results = load_raw_results(policy, root)
    files = {
        f"jobs/{cell.workload_id}/raw/{cell.cell_id}.json": _sha256_file(
            workload_job_root(policy, root, cell.workload_id)
            / "raw" / f"{cell.cell_id}.json")
        for cell in policy.cells
    }
    campaign_paths: set[str] = set()
    submission_payload, _ = _read_json(root / "receipts" / "submission.json")
    submission = _validate_submission_receipt(
        policy, submission_payload, attempt_id, root, current_pin)
    claims: dict[str, dict[str, Any]] = {}
    from . import reservation
    for workload_id, submission_job in zip(
            workload_ids(policy), submission["jobs"]):
        workload_raw = [
            raw for cell, raw in zip(policy.cells, raw_results)
            if cell.workload_id == workload_id
        ]
        if len(workload_raw) != 2:
            raise CertificationError("raw workload is not an exact cell pair")
        evidences = [raw.get("campaign_evidence") for raw in workload_raw]
        evidence_keys = {
            "campaign_id", "lock_path", "lock_sha256", "wal_path",
            "wal_sha256", "claim_path", "claim_sha256",
        }
        if (any(type(evidence) is not dict or set(evidence) != evidence_keys
                for evidence in evidences)
                or evidences[0] != evidences[1]):
            raise CertificationError("raw campaign evidence is incomplete or split")
        evidence = evidences[0]
        config_bindings = {
            _campaign_config_binding(
                policy, workload_id, attempt_id, current_pin,
                raw.get("campaign_preimage"))
            for raw in workload_raw
        }
        if len(config_bindings) != 1:
            raise CertificationError("raw campaign config binding is split")
        expected_campaign_id, expected_protocol_digest = config_bindings.pop()
        if expected_campaign_id != evidence["campaign_id"]:
            raise CertificationError("raw campaign config identity differs")
        for kind in ("lock", "wal", "claim"):
            path = _canonical_child(
                evidence[f"{kind}_path"], root, f"campaign {kind}")
            relative = path.relative_to(root).as_posix()
            expected_sha = _require_sha(
                evidence[f"{kind}_sha256"], f"campaign {kind} sha256")
            if _sha256_file(path) != expected_sha:
                raise CertificationError(f"campaign {kind} changed before manifest")
            previous = files.setdefault(relative, expected_sha)
            if previous != expected_sha:
                raise CertificationError(f"campaign {kind} hash is inconsistent")
            campaign_paths.add(relative)
        claim_path = _canonical_child(
            evidence["claim_path"], root, "campaign claim")
        claim_bytes = claim_path.read_bytes()
        claim = _decode_campaign_claim(claim_bytes, "campaign claim")
        reservation_path = workload_job_root(
            policy, root, workload_id) / "reservation.json"
        reservation_result, reservation_bytes = _read_json(reservation_path)
        environment = reservation_result.get("environment")
        try:
            binding = reservation.read_binding(environment)
        except (reservation.ReservationError, TypeError) as exc:
            raise CertificationError("reservation result binding is invalid") from exc
        _validate_claim_reservation_binding(
            claim, campaign_id=evidence["campaign_id"],
            request_id=submission_job["request_id"],
            reservation_binding=binding,
            expected_protocol_digest=expected_protocol_digest)
        claims[workload_id] = {
            "campaign_id": evidence["campaign_id"],
            "claim_path": claim_path.relative_to(root).as_posix(),
            "claim_sha256": _sha256_bytes(claim_bytes),
            "claim": claim,
            "reservation_result": reservation_path.relative_to(root).as_posix(),
            "reservation_result_sha256": _sha256_bytes(reservation_bytes),
        }
    if len(campaign_paths) != 6:
        raise CertificationError(
            "raw results do not bind exactly two campaign lock/WAL/claim triples")
    manifest = {
        "schema_version": RAW_MANIFEST_SCHEMA,
        "study": policy.study,
        "protocol_sha256": policy.protocol_sha256,
        "attempt_id": attempt_id,
        "current_pin": current_pin,
        "campaign_claims": claims,
        "files": files,
    }
    path = root / "raw-manifest.json"
    write_json_x(path, manifest)
    _fsync_dir(root)
    return path


def _load_raw_manifest_bundle(
        policy: Policy, manifest_path: Path, manifest_sha256: str, *,
        attempt_id: str, attempt_root: Path, current_pin: str,
        job_bindings: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    # This scans only independently owned jobs/<workload>/raw directories; the
    # shared jobs/ parent remains unenumerated.
    live_raw_results = load_raw_results(policy, attempt_root)
    manifest, manifest_bytes = _read_json(manifest_path)
    if _sha256_bytes(manifest_bytes) != manifest_sha256:
        raise CertificationError("completion raw manifest hash mismatch")
    if (set(manifest) != {
            "schema_version", "study", "protocol_sha256", "attempt_id",
            "current_pin", "campaign_claims", "files"}
            or manifest.get("schema_version") != RAW_MANIFEST_SCHEMA
            or manifest.get("study") != policy.study
            or manifest.get("protocol_sha256") != policy.protocol_sha256
            or manifest.get("attempt_id") != attempt_id
            or manifest.get("current_pin") != current_pin
            or type(manifest.get("campaign_claims")) is not dict
            or type(manifest.get("files")) is not dict):
        raise CertificationError("completion raw manifest identity mismatch")
    files = manifest["files"]
    raw_names = {
        f"jobs/{cell.workload_id}/raw/{cell.cell_id}.json"
        for cell in policy.cells}
    if (not raw_names.issubset(files)
            or len(files) != len(raw_names) + 6
            or any(type(name) is not str
                   or type(digest) is not str
                   or _SHA256_RE.fullmatch(digest) is None
                   for name, digest in files.items())):
        raise CertificationError("raw manifest file inventory is not closed")
    frozen_files: dict[str, bytes] = {}
    for relative, digest in files.items():
        relative_path = Path(relative)
        if (relative_path.is_absolute() or ".." in relative_path.parts
                or relative_path.as_posix() != relative):
            raise CertificationError("raw manifest path is not a canonical relative path")
        path = _canonical_child(str(attempt_root / relative_path), attempt_root,
                                "raw manifest member")
        try:
            payload = path.read_bytes()
        except OSError as exc:
            raise CertificationError("cannot freeze raw manifest member bytes") from exc
        if not payload or len(payload) > 16 * 1024 * 1024:
            raise CertificationError("raw manifest member is outside the size bound")
        if _sha256_bytes(payload) != digest:
            raise CertificationError("raw manifest member hash mismatch")
        frozen_files[relative] = payload
    raw_results: list[dict[str, Any]] = []
    campaign_members: set[str] = set()
    for cell in policy.cells:
        relative = f"jobs/{cell.workload_id}/raw/{cell.cell_id}.json"
        value = _loads_json(frozen_files[relative], relative)
        if type(value) is not dict:
            raise CertificationError("raw manifest cell member is not an object")
        evidence = value.get("campaign_evidence")
        if type(evidence) is not dict:
            raise CertificationError("raw cell campaign evidence is missing")
        for kind in ("lock", "wal", "claim"):
            path = _lexical_absolute_path(
                evidence.get(f"{kind}_path"), f"campaign {kind}")
            try:
                member = path.relative_to(attempt_root).as_posix()
            except ValueError as exc:
                raise CertificationError("campaign evidence is outside attempt") from exc
            if (member not in frozen_files
                    or evidence.get(f"{kind}_sha256") != files[member]):
                raise CertificationError("campaign evidence is not manifest-bound")
            campaign_members.add(member)
        raw_results.append(value)
    if [raw.get("cell_id") for raw in live_raw_results] != [
            raw.get("cell_id") for raw in raw_results]:
        raise CertificationError("live and frozen raw cell order differs")
    if campaign_members != set(files) - raw_names:
        raise CertificationError(
            "campaign lock/WAL/claim manifest members are not exact")
    claims = manifest["campaign_claims"]
    expected_workloads = workload_ids(policy)
    if (set(claims) != set(expected_workloads)
            or list(claims) != list(expected_workloads)):
        raise CertificationError("campaign claim workload mapping is not exact")
    binding_by_workload = {
        str(binding["workload"]): binding for binding in job_bindings}
    if (set(binding_by_workload) != set(expected_workloads)
            or [binding.get("workload") for binding in job_bindings]
            != list(expected_workloads)):
        raise CertificationError("completion job binding workload mapping is not exact")
    for workload_id in expected_workloads:
        claim_entry = claims[workload_id]
        if type(claim_entry) is not dict or set(claim_entry) != {
                "campaign_id", "claim_path", "claim_sha256", "claim",
                "reservation_result", "reservation_result_sha256"}:
            raise CertificationError("campaign claim manifest entry is not exact")
        claim_relative = claim_entry["claim_path"]
        if (type(claim_relative) is not str
                or claim_relative not in frozen_files
                or _require_sha(claim_entry["claim_sha256"], "claim sha256")
                != files[claim_relative]):
            raise CertificationError("campaign claim is not file-manifest-bound")
        claim = _decode_campaign_claim(
            frozen_files[claim_relative], "manifest campaign claim")
        if claim != claim_entry["claim"]:
            raise CertificationError("embedded campaign claim differs from frozen bytes")
        binding = binding_by_workload[workload_id]
        reservation_binding = binding["reservation_binding"]
        workload_raw = [
            raw for raw in raw_results
            if policy.cell(raw["cell_id"]).workload_id == workload_id
        ]
        config_bindings = {
            _campaign_config_binding(
                policy, workload_id, attempt_id, current_pin,
                raw.get("campaign_preimage"))
            for raw in workload_raw
        }
        if len(workload_raw) != 2 or len(config_bindings) != 1:
            raise CertificationError("manifest campaign config binding is split")
        expected_campaign_id, expected_protocol_digest = config_bindings.pop()
        if expected_campaign_id != claim_entry["campaign_id"]:
            raise CertificationError("manifest campaign config identity differs")
        reservation_relative = claim_entry["reservation_result"]
        expected_reservation = (
            workload_job_root(policy, attempt_root, workload_id)
            / "reservation.json")
        if (reservation_relative
                != expected_reservation.relative_to(attempt_root).as_posix()
                or _require_sha(
                    claim_entry["reservation_result_sha256"],
                    "reservation result sha256")
                != _sha256_file(expected_reservation)
                ):
            raise CertificationError(
                "campaign claim differs from completion reservation binding")
        _validate_claim_reservation_binding(
            claim, campaign_id=claim_entry["campaign_id"],
            request_id=binding["request_id"],
            reservation_binding=reservation_binding,
            expected_protocol_digest=expected_protocol_digest)
        workload_evidence = [
            raw["campaign_evidence"] for raw in raw_results
            if policy.cell(raw["cell_id"]).workload_id == workload_id
        ]
        if (len(workload_evidence) != 2
                or any(evidence["campaign_id"] != claim_entry["campaign_id"]
                       or Path(evidence["claim_path"]).relative_to(
                           attempt_root).as_posix() != claim_relative
                       or evidence["claim_sha256"] != claim_entry["claim_sha256"]
                       for evidence in workload_evidence)):
            raise CertificationError("raw campaign evidence differs from campaign claim")
    return {
        "manifest_bytes": manifest_bytes,
        "files": frozen_files,
        "raw_results": raw_results,
    }


def _rename_noreplace(source: Path, destination: Path) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise CertificationError("renameat2(RENAME_NOREPLACE) is unavailable")
    renameat2.argtypes = [ctypes.c_int, ctypes.c_char_p,
                          ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    renameat2.restype = ctypes.c_int
    at_fdcwd = -100
    rename_noreplace = 1
    rc = renameat2(
        at_fdcwd, os.fsencode(source), at_fdcwd, os.fsencode(destination),
        rename_noreplace,
    )
    if rc != 0:
        error_number = ctypes.get_errno()
        if error_number == errno.EEXIST:
            raise FileExistsError(destination)
        raise OSError(error_number, os.strerror(error_number), str(destination))


_CERTIFICATION_RESULT_COMMON_KEYS = {
    "schema_version", "study", "protocol_schema", "protocol_sha256",
    "policy_sha256", "policy_bytes_base64", "attempt_id", "request_ids",
    "current_pin", "source_commit", "cells", "effects", "status",
    "a4_noise_floor_status", "legacy_role",
    "smallest_observed_sufficient_in_this_two_point_protocol",
    "global_minimality_established", "compile_out_evidence_scope",
    "independent_observation_limits",
}
_CERTIFICATION_RESULT_STATUSES = {
    "observed-positive", "reject", "indeterminate", "performance-indeterminate",
}


def _validate_certification_result(
        policy: Policy, report: Mapping[str, Any],
        evidence: Mapping[str, Any]) -> None:
    """Validate the two exact v3 result shapes before creating a stage."""
    analysis_keys = _CERTIFICATION_RESULT_COMMON_KEYS | {"historical_context"}
    indeterminate_keys = _CERTIFICATION_RESULT_COMMON_KEYS | {"reason"}
    if type(report) is not dict or frozenset(report) not in {
            frozenset(analysis_keys), frozenset(indeterminate_keys)}:
        raise CertificationError(
            "certification result is missing required or has extra fields")
    acquisition = evidence.get("acquisition")
    expected_policy_bytes = base64.b64encode(policy.raw_bytes).decode("ascii")
    if (type(acquisition) is not dict
            or report["schema_version"] != CERTIFICATION_SCHEMA
            or report["study"] != policy.study
            or report["protocol_schema"] != POLICY_SCHEMA
            or report["protocol_sha256"] != policy.protocol_sha256
            or report["policy_sha256"] != policy.bytes_sha256
            or report["policy_bytes_base64"] != expected_policy_bytes
            or report["attempt_id"] != evidence.get("attempt_id")
            or report["current_pin"] != acquisition.get("current_pin")
            or report["source_commit"] != evidence.get("source_commit")
            or acquisition.get("protocol_sha256") != policy.protocol_sha256):
        raise CertificationError(
            "certification result and terminal evidence identity differ")
    request_ids = report["request_ids"]
    expected_workloads = workload_ids(policy)
    if (type(request_ids) is not dict
            or list(request_ids) != list(expected_workloads)
            or request_ids != evidence.get("request_ids")):
        raise CertificationError(
            "certification result request IDs differ from policy or evidence")
    normalized_request_ids = [
        _normalize_request_id(request_ids[workload_id])
        for workload_id in expected_workloads
    ]
    if (normalized_request_ids != list(request_ids.values())
            or len(set(normalized_request_ids)) != len(normalized_request_ids)):
        raise CertificationError(
            "certification result request IDs are not canonical and distinct")
    if (type(report["cells"]) is not list
            or type(report["effects"]) is not dict
            or type(report["status"]) is not str
            or report["status"] not in _CERTIFICATION_RESULT_STATUSES
            or report["a4_noise_floor_status"] != "open"
            or report["legacy_role"] != "historically inherited companion"
            or report[
                "smallest_observed_sufficient_in_this_two_point_protocol"] is not None
            or report["global_minimality_established"] is not False
            or report["compile_out_evidence_scope"] != COMPILE_OUT_SCOPE
            or type(report["independent_observation_limits"]) is not dict):
        raise CertificationError("certification result required fields are malformed")
    if "historical_context" in report:
        historical = report["historical_context"]
        if (type(historical) is not dict
                or set(historical) != {"ccbench_commit", "comparison_input"}
                or historical["ccbench_commit"]
                != policy.document["historical_reference"]["ccbench_commit"]
                or historical["comparison_input"] is not False):
            raise CertificationError(
                "certification result historical context is malformed")
    elif (report["status"] != "indeterminate"
          or type(report["reason"]) is not str or not report["reason"]
          or report["cells"] != [] or report["effects"] != {}):
        raise CertificationError(
            "indeterminate certification result fields are malformed")


def materialize(policy: Policy, report: Mapping[str, Any], evidence: Mapping[str, Any],
                *, repo_root: Path | str) -> Path:
    _validate_certification_result(policy, report, evidence)
    root = Path(repo_root).resolve(strict=True)
    destination = (root / policy.tracked_destination).resolve()
    expected = root.joinpath(*policy.tracked_destination.parts)
    if destination != expected or destination.exists() or destination.is_symlink():
        raise CertificationError("tracked destination is not a fresh exact leaf")
    parent = destination.parent
    parent.mkdir(parents=True, exist_ok=True)
    stage = parent / f".{destination.name}.stage-{os.getpid()}-{os.urandom(8).hex()}"
    stage.mkdir(mode=0o700, exist_ok=False)
    published = False
    try:
        encoded_policy = base64.b64encode(policy.raw_bytes).decode("ascii")
        certification_bytes = _canonical_json({
            **report,
            "policy_sha256": policy.bytes_sha256,
            "policy_bytes_base64": encoded_policy,
        })
        _write_bytes_x(stage / "certification.json", certification_bytes)
        _write_bytes_x(stage / "acquisition-receipt.json",
                       evidence["acquisition_bytes"])
        _write_bytes_x(stage / "submission-receipt.json",
                       evidence["submission_bytes"])
        _write_bytes_x(stage / "completion-receipt.json",
                       evidence["completion_bytes"])
        if evidence.get("raw_manifest_bytes") is not None:
            _write_bytes_x(stage / "raw-manifest.json",
                           evidence["raw_manifest_bytes"])
        manifest = {
            "schema_version": "paper-story-a2-artifact-manifest/v1",
            "attempt_id": report["attempt_id"],
            "protocol_sha256": policy.protocol_sha256,
            "files": {
                "certification.json": _sha256_bytes(certification_bytes),
                "acquisition-receipt.json": _sha256_bytes(evidence["acquisition_bytes"]),
                "submission-receipt.json": _sha256_bytes(evidence["submission_bytes"]),
                "completion-receipt.json": _sha256_bytes(evidence["completion_bytes"]),
            },
        }
        if evidence.get("raw_manifest_bytes") is not None:
            manifest["files"]["raw-manifest.json"] = _sha256_bytes(
                evidence["raw_manifest_bytes"])
        manifest_bytes = _canonical_json(manifest)
        _write_bytes_x(stage / "artifact-manifest.json", manifest_bytes)
        marker = {
            "schema_version": COMPLETE_MARKER_SCHEMA,
            "attempt_id": report["attempt_id"],
            "protocol_sha256": policy.protocol_sha256,
            "certification_sha256": _sha256_bytes(certification_bytes),
            "manifest_sha256": _sha256_bytes(manifest_bytes),
        }
        _write_bytes_x(stage / "COMPLETE.json", _canonical_json(marker))
        _fsync_dir(stage)
        _rename_noreplace(stage, destination)
        published = True
        _fsync_dir(parent)
        return destination
    finally:
        if not published and stage.exists():
            shutil.rmtree(stage)


def compute_preflight(policy: Policy, *, workload_id: str,
                      attempt_root: Path | str,
                      raw_root: Path | str, expected_head: str,
                      repo_root: Path | str, dependency_prefix: Path | str,
                      environ: Optional[Mapping[str, str]] = None,
                      hostname: Optional[str] = None) -> Path:
    environment = dict(os.environ if environ is None else environ)
    host = socket.gethostname() if hostname is None else hostname
    if _COMPUTE_HOST_RE.fullmatch(host) is None:
        raise CertificationError("job body is compute-only")
    for name in ("PBS_JOBID", "PBS_NODEFILE", "PBS_O_WORKDIR"):
        if not environment.get(name):
            raise CertificationError(f"missing PBS environment: {name}")
    reservation_values = {
        key: value for key, value in environment.items()
        if key.startswith("IZANAGI_RESERVATION_") and value
    }
    if set(reservation_values) != _RESERVATION_ENV_KEYS:
        raise CertificationError("reservation binding is incomplete")
    from . import reservation
    try:
        binding = reservation.read_binding(environment)
        if binding.host.split(".", 1)[0] != host.split(".", 1)[0]:
            raise CertificationError("reservation host differs from compute host")
        hours, minutes, seconds = (
            int(piece) for piece in policy.document["scheduler"]["walltime"].split(":")
        )
        requested_s = hours * 3600 + minutes * 60 + seconds
        if binding.requested_s != requested_s:
            raise CertificationError("reservation duration differs from scheduler policy")
        reservation.check_reservation(
            binding, required_s=1, safety_margin_s=0, environ=environment)
    except (reservation.ReservationError, TypeError, ValueError) as exc:
        if isinstance(exc, CertificationError):
            raise
        raise CertificationError(f"reservation binding is invalid: {exc}") from exc
    root = Path(repo_root).resolve(strict=True)
    job_body = root.joinpath(*Path(policy.document["scheduler"]["job_body"]).parts)
    if (_sha256_file(job_body) != binding.script_sha256
            or job_body.is_symlink() or not job_body.is_file()):
        raise CertificationError("reservation script hash is not the canonical job body")
    observed_head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    if observed_head != expected_head:
        raise CertificationError("worktree HEAD does not match expected HEAD")
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"], cwd=root,
        check=True, capture_output=True, text=True,
    ).stdout
    if dirty:
        raise CertificationError("worktree is not clean")
    _, attempt = validate_attempt_root(policy, attempt_root)
    job_root = workload_job_root(policy, attempt, workload_id)
    if job_root.is_symlink() or not job_root.is_dir():
        raise CertificationError("workload job root is unavailable")
    expected_raw = job_root / "raw"
    requested_raw = Path(raw_root).resolve(strict=False)
    if requested_raw != expected_raw or requested_raw.exists() or requested_raw.is_symlink():
        raise CertificationError("raw root is not the fresh exact attempt child")
    dependency = Path(dependency_prefix).resolve(strict=True)
    if dependency.is_symlink() or not dependency.is_dir():
        raise CertificationError("dependency staging prefix is unavailable")
    try:
        requested_raw.mkdir(mode=0o700, exist_ok=False)
    except FileExistsError as exc:
        raise CertificationError("raw root lost the create-only race") from exc
    _fsync_dir(job_root)
    return requested_raw


def _indeterminate_report(policy: Policy, evidence: Mapping[str, Any], *,
                          attempt_id: str, current_pin: str,
                          reason: str) -> dict[str, Any]:
    return {
        "schema_version": CERTIFICATION_SCHEMA,
        "study": policy.study,
        "protocol_schema": POLICY_SCHEMA,
        "protocol_sha256": policy.protocol_sha256,
        "policy_sha256": policy.bytes_sha256,
        "policy_bytes_base64": base64.b64encode(policy.raw_bytes).decode("ascii"),
        "attempt_id": attempt_id,
        "request_ids": evidence["request_ids"],
        "current_pin": current_pin,
        "source_commit": evidence["source_commit"],
        "cells": [],
        "effects": {},
        "status": "indeterminate",
        "reason": reason,
        "a4_noise_floor_status": "open",
        "legacy_role": "historically inherited companion",
        "smallest_observed_sufficient_in_this_two_point_protocol": None,
        "global_minimality_established": False,
        "compile_out_evidence_scope": COMPILE_OUT_SCOPE,
        "independent_observation_limits": {
            "correctness_run_argv": "not-recorded-by-existing-pipeline",
            "correctness_workload_binding": (
                "campaign-lock-and-pipeline-constructor; not an independent argv observation"
            ),
        },
    }


def _collect_command(args: argparse.Namespace) -> int:
    policy = load_policy()
    evidence = validate_acquisition_bundle(
        policy, args.acquisition_receipt, current_pin=args.current_pin)
    attempt_id, attempt_root = validate_attempt_root(policy, args.attempt_root)
    if (attempt_id != evidence["attempt_id"]
            or str(attempt_root) != evidence["attempt_root"]):
        raise CertificationError("collector attempt differs from receipt attempt")
    failed_drivers = {
        workload: rc for workload, rc in evidence["driver_rcs"].items()
        if rc != 0}
    if failed_drivers:
        report = _indeterminate_report(
            policy, evidence, attempt_id=attempt_id, current_pin=args.current_pin,
            reason=f"compute driver exited nonzero: {failed_drivers}",
        )
    elif not evidence["raw_manifest_valid"]:
        report = _indeterminate_report(
            policy, evidence, attempt_id=attempt_id, current_pin=args.current_pin,
            reason=("verified raw manifest unavailable: "
                    + str(evidence["raw_manifest_reason"])),
        )
    else:
        try:
            report = collect_results(
                policy, evidence["raw_results"],
                attempt_id=attempt_id, current_pin=args.current_pin,
                request_ids=evidence["request_ids"],
                frozen_files=evidence["raw_files"], attempt_root=attempt_root,
            )
        except (CertificationError, OSError, ValueError, TypeError,
                KeyError, IndexError) as exc:
            report = _indeterminate_report(
                policy, evidence, attempt_id=attempt_id,
                current_pin=args.current_pin, reason=str(exc),
            )
        else:
            report["source_commit"] = evidence["source_commit"]
    destination = materialize(policy, report, evidence, repo_root=args.repo_root)
    print(destination)
    return driver_rc(report)


def _preflight_command(args: argparse.Namespace) -> int:
    policy = load_policy()
    raw = compute_preflight(
        policy, workload_id=args.workload, attempt_root=args.attempt_root,
        raw_root=args.raw_root,
        expected_head=args.expected_head, repo_root=args.repo_root,
        dependency_prefix=args.dependency_prefix,
    )
    print(raw)
    return 0


def _run_workload_command(args: argparse.Namespace) -> int:
    policy = load_policy()
    summary = run_workload(
        policy, workload_id=args.workload, attempt_root=args.attempt_root,
        raw_root=args.raw_root, current_pin=args.current_pin,
        dependency_prefix=args.dependency_prefix, ccbench_dir=args.ccbench_dir,
    )
    # A workload-level abort is scientific/evidence data.  The final collector
    # determines whether the outer attempt is determinate after all four cells.
    print(json.dumps({
        "campaign_id": summary.campaign_id,
        "committed": summary.committed,
        "aborted": summary.aborted,
    }, ensure_ascii=True, sort_keys=True))
    return 0


def _preregister_command(args: argparse.Namespace) -> int:
    policy = load_policy()
    print(preregister_attempt(policy, args.attempt_id, args.current_pin))
    return 0


def _record_request_id_command(args: argparse.Namespace) -> int:
    policy = load_policy()
    print(record_scheduler_request_id(
        policy, args.attempt_root, args.workload, args.request_id))
    return 0


def _durabilize_qsub_diagnostics_command(args: argparse.Namespace) -> int:
    policy = load_policy()
    durabilize_scheduler_qsub_diagnostics(
        policy, args.attempt_root, args.workload)
    return 0


def _finalize_raw_command(args: argparse.Namespace) -> int:
    policy = load_policy()
    print(finalize_raw_manifest(policy, args.attempt_root, args.current_pin))
    return 0


def _exact_qsub_command(args: argparse.Namespace) -> int:
    argv = list(args.qsub_argv)
    if argv and argv[0] == "--":
        argv = argv[1:]
    completed = exact_qsub(argv)
    return int(completed.returncode)


def _finish_group_command(args: argparse.Namespace) -> int:
    policy = load_policy()
    completion, acquisition = finish_group(
        policy, args.attempt_root, args.current_pin)
    print(completion)
    print(acquisition)
    return 0


def _record_receipt_command(args: argparse.Namespace) -> int:
    policy = load_policy()
    if args.receipt_kind == "acquisition":
        path = record_acquisition_receipt(
            policy, args.attempt_root, args.current_pin)
    else:
        payload, _ = _read_json(Path(args.payload).resolve(strict=True))
        recorder = (
            record_submission_receipt
            if args.receipt_kind == "submission"
            else record_completion_receipt
        )
        path = recorder(policy, args.attempt_root, args.current_pin, payload)
    print(path)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    exact_submit = sub.add_parser("exact-qsub")
    exact_submit.add_argument("qsub_argv", nargs=argparse.REMAINDER)
    exact_submit.set_defaults(handler=_exact_qsub_command)
    preflight = sub.add_parser("compute-preflight")
    preflight.add_argument("--workload", required=True)
    preflight.add_argument("--attempt-root", required=True)
    preflight.add_argument("--raw-root", required=True)
    preflight.add_argument("--expected-head", required=True)
    preflight.add_argument("--repo-root", required=True)
    preflight.add_argument("--dependency-prefix", required=True)
    preflight.set_defaults(handler=_preflight_command)
    preregister = sub.add_parser("preregister")
    preregister.add_argument("--attempt-id", required=True)
    preregister.add_argument("--current-pin", required=True)
    preregister.set_defaults(handler=_preregister_command)
    request_id = sub.add_parser("record-request-id")
    request_id.add_argument("--attempt-root", required=True)
    request_id.add_argument("--workload", required=True)
    request_id.add_argument("--request-id", required=True)
    request_id.set_defaults(handler=_record_request_id_command)
    diagnostics = sub.add_parser("durabilize-qsub-diagnostics")
    diagnostics.add_argument("--attempt-root", required=True)
    diagnostics.add_argument("--workload", required=True)
    diagnostics.set_defaults(handler=_durabilize_qsub_diagnostics_command)
    run = sub.add_parser("run-workload")
    run.add_argument("--workload", required=True)
    run.add_argument("--attempt-root", required=True)
    run.add_argument("--raw-root", required=True)
    run.add_argument("--current-pin", required=True)
    run.add_argument("--dependency-prefix", required=True)
    run.add_argument("--ccbench-dir", required=True)
    run.set_defaults(handler=_run_workload_command)
    finalize = sub.add_parser("finalize-raw")
    finalize.add_argument("--attempt-root", required=True)
    finalize.add_argument("--current-pin", required=True)
    finalize.set_defaults(handler=_finalize_raw_command)
    finish = sub.add_parser("finish-group")
    finish.add_argument("--attempt-root", required=True)
    finish.add_argument("--current-pin", required=True)
    finish.set_defaults(handler=_finish_group_command)
    for receipt_kind in ("submission", "completion"):
        record = sub.add_parser("record-" + receipt_kind)
        record.add_argument("--attempt-root", required=True)
        record.add_argument("--current-pin", required=True)
        record.add_argument("--payload", required=True)
        record.set_defaults(
            handler=_record_receipt_command, receipt_kind=receipt_kind)
    acquisition = sub.add_parser("record-acquisition")
    acquisition.add_argument("--attempt-root", required=True)
    acquisition.add_argument("--current-pin", required=True)
    acquisition.set_defaults(
        handler=_record_receipt_command, receipt_kind="acquisition")
    collect = sub.add_parser("collect")
    collect.add_argument("--attempt-root", required=True)
    collect.add_argument("--current-pin", required=True)
    collect.add_argument("--acquisition-receipt", required=True)
    collect.add_argument("--repo-root", required=True)
    collect.set_defaults(handler=_collect_command)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except (CertificationError, FileExistsError, OSError,
            subprocess.SubprocessError) as exc:
        print(f"paper-story A-2 indeterminate: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
