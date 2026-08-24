#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paper-story A-2 exact-workload certification protocol.

The module deliberately keeps the experiment values in the adjacent versioned
policy.  Code here validates bindings, collects one create-only outer attempt,
and publishes a bounded tracked result.  It does not submit PBS jobs.
"""
from __future__ import annotations

import argparse
import ctypes
import errno
import hashlib
import json
import os
import re
import shlex
import shutil
import socket
import statistics
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence

from .pipeline import PerfConfig


POLICY_SCHEMA = "paper-story-a2-certification-policy/v1"
RAW_RESULT_SCHEMA = "paper-story-a2-cell-result/v1"
CERTIFICATION_SCHEMA = "paper-story-a2-certification-result/v1"
SUBMISSION_SCHEMA = "paper-story-a2-submission-receipt/v1"
COMPLETION_SCHEMA = "paper-story-a2-completion-receipt/v1"
ACQUISITION_SCHEMA = "paper-story-a2-acquisition-receipt/v1"
TRACE0_SCHEMA = "paper-story-a2-trace0-evidence/v1"
RAW_MANIFEST_SCHEMA = "paper-story-a2-raw-manifest/v1"
COMPLETE_MARKER_SCHEMA = "paper-story-a2-materialization-complete/v1"
POLICY_PATH = Path(__file__).with_suffix(".v1.json")
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
_TERMINAL_STATE_RE = re.compile(
    r"(?im)^[ \t]*(?:Request[ \t]+State|State)[ \t]*=[ \t]*EXT[ \t]*$"
    r"|^[ \t]*Current[ \t]+State[ \t]*=[ \t]*"
    r"(?:completed|finished|ended|exited|terminated|exiting|post-running)[ \t]*$"
)
_TOP_LEVEL_KEYS = {
    "schema_version", "study", "historical_reference",
    "durable_measurement_base", "tracked_destination", "performance_common",
    "legacy_correctness", "workloads", "controlled_define_base", "cells",
    "scheduler",
}
_PERFORMANCE_KEYS = {
    "records", "threads", "skew", "rmw", "max_ope", "extime", "reps",
    "base", "wal", "ccbench_protocol",
}
_WORKLOAD_KEYS = {"id", "label", "rratio", "adopted_backoff_us"}
_CELL_KEYS = {"id", "workload", "role", "genome"}
_GENOME_KEYS = {"BACK_OFF", "BACKOFF_FIXED"}
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
_RESULT_LIMIT = 2 * 1024 * 1024


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
    bytes_sha256: str
    protocol_sha256: str
    cells: tuple[CellSpec, ...]

    @property
    def study(self) -> str:
        return str(self.document["study"])

    @property
    def durable_base(self) -> Path:
        return Path(str(self.document["durable_measurement_base"])).resolve()

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
    return (json.dumps(value, ensure_ascii=True, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


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
    }


def load_policy(path: Path | str = POLICY_PATH) -> Policy:
    policy_path = Path(path)
    if policy_path.is_symlink() or not policy_path.is_file():
        raise CertificationError(f"policy is not a regular file: {policy_path}")
    try:
        raw = policy_path.read_bytes()
        document = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CertificationError(f"cannot read policy: {policy_path}: {exc}") from exc
    document = _exact_keys(document, _TOP_LEVEL_KEYS, "policy")
    if document["schema_version"] != POLICY_SCHEMA:
        raise CertificationError("unsupported policy schema")
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
    tracked = Path(str(document["tracked_destination"]))
    if tracked.is_absolute() or ".." in tracked.parts:
        raise CertificationError("tracked destination must be a bounded relative path")

    common = _exact_keys(
        document["performance_common"], _PERFORMANCE_KEYS,
        "performance_common",
    )
    for key in ("records", "threads", "extime", "reps"):
        _positive_int(common[key], f"performance_common.{key}")
    if (common["wal"] != 0 or common["base"] != "L-W0"
            or type(common["ccbench_protocol"]) is not str
            or not common["ccbench_protocol"]):
        raise CertificationError("policy must use L-W0 with WAL disabled")
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


def validate_attempt_root(policy: Policy, attempt_root: Path | str,
                          *, must_exist: bool = True) -> tuple[str, Path]:
    raw = Path(attempt_root)
    if not raw.is_absolute():
        raise CertificationError("attempt root must be absolute")
    if raw.is_symlink():
        raise CertificationError("attempt root must not be a symlink")
    resolved = raw.resolve(strict=must_exist)
    if resolved.parent != policy.durable_base:
        raise CertificationError("attempt root is outside the pinned durable base")
    if _ATTEMPT_RE.fullmatch(resolved.name) is None:
        raise CertificationError("attempt root is not a canonical child")
    if must_exist and not resolved.is_dir():
        raise CertificationError("attempt root must be an existing real directory")
    return resolved.name, resolved


def create_attempt_root(policy: Policy, attempt_id: str) -> Path:
    if _ATTEMPT_RE.fullmatch(attempt_id) is None:
        raise CertificationError("attempt ID is not a canonical leaf")
    policy.durable_base.mkdir(parents=True, exist_ok=True)
    base = policy.durable_base.resolve(strict=True)
    root = base / attempt_id
    root.mkdir(mode=0o700, exist_ok=False)
    _fsync_dir(base)
    validate_attempt_root(policy, root)
    return root


def preregister_attempt(policy: Policy, attempt_id: str,
                        current_pin: str) -> Path:
    """Create the outer attempt and its pre-run identity, never resume it."""
    if type(current_pin) is not str or _COMMIT_RE.fullmatch(current_pin) is None:
        raise CertificationError("current pin is required")
    root = create_attempt_root(policy, attempt_id)
    (root / "receipts").mkdir(mode=0o700)
    (root / "scheduler").mkdir(mode=0o700)
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
    _fsync_dir(root / "scheduler")
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
        value = json.loads(raw.decode("utf-8"))
    except CertificationError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
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
    path = Path(path_value)
    if not path.is_absolute():
        raise CertificationError(f"{label} path must be absolute")
    if path.is_symlink() or not path.is_file():
        raise CertificationError(f"{label} is not a regular file")
    resolved = path.resolve(strict=True)
    try:
        resolved.relative_to(parent)
    except ValueError as exc:
        raise CertificationError(f"{label} is outside attempt root") from exc
    return resolved


def _require_sha(value: object, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise CertificationError(f"{label} is not a full lowercase sha256")
    return value


def _option_value(argv: Sequence[str], option: str) -> str:
    positions = [index for index, token in enumerate(argv) if token == option]
    if len(positions) != 1 or positions[0] + 1 >= len(argv):
        raise CertificationError(f"qsub argv needs exactly one {option}")
    return argv[positions[0] + 1]


def _validate_submission_receipt(policy: Policy, payload: Mapping[str, Any],
                                 attempt_id: str, attempt_root: Path,
                                 current_pin: str) -> dict[str, Any]:
    required = {
        "schema_version", "route", "study", "protocol_sha256", "attempt_id",
        "attempt_root", "source_commit", "current_pin", "submit_host", "qsub_argv",
        "qsub_stdout", "request_id", "qstat_visibility", "scheduler_stdout",
        "scheduler_stderr",
    }
    if not required.issubset(payload):
        raise CertificationError("submission receipt is missing required evidence")
    if (payload["schema_version"] != SUBMISSION_SCHEMA
            or payload["route"] != "direct-qsub"
            or payload["study"] != policy.study
            or payload["protocol_sha256"] != policy.protocol_sha256
            or payload["attempt_id"] != attempt_id
            or Path(str(payload["attempt_root"])).resolve() != attempt_root
            or payload["current_pin"] != current_pin):
        raise CertificationError("submission receipt identity mismatch")
    if type(payload["submit_host"]) is not str or not payload["submit_host"]:
        raise CertificationError("submission host is missing")
    if (type(payload["source_commit"]) is not str
            or _COMMIT_RE.fullmatch(payload["source_commit"]) is None):
        raise CertificationError("submission source commit is missing")
    request_id = payload["request_id"]
    if type(request_id) is not str or _REQUEST_RE.fullmatch(request_id) is None:
        raise CertificationError("submission request ID is invalid")
    qsub_stdout = payload["qsub_stdout"]
    if type(qsub_stdout) is not str or (
            _QSUB_REQUEST_RE.findall(qsub_stdout) != [request_id]
            and qsub_stdout.strip().rstrip(".") != request_id.rstrip(".")):
        raise CertificationError("qsub stdout is not bound to request ID")
    argv = payload["qsub_argv"]
    if type(argv) is not list or not argv or not all(type(item) is str for item in argv):
        raise CertificationError("canonical qsub argv is missing")
    scheduler = policy.document["scheduler"]
    if (len(argv) != 18
            or argv[0:2] != ["qsub", "-A"]
            or argv[2] != scheduler["project"]
            or argv[3:5] != ["-q", scheduler["queue"]]
            or argv[5:7] != ["-b", "1"]
            or argv[7:9] != ["-l", f"elapstim_req={scheduler['walltime']}"]
            or argv[9] != "-N" or not argv[10]
            or argv[11] != "-v" or argv[13] != "-o" or argv[15] != "-e"):
        raise CertificationError("qsub argv does not match scheduler policy")
    variable_arg = _option_value(argv, "-v")
    stdout_arg = Path(_option_value(argv, "-o")).resolve()
    stderr_arg = Path(_option_value(argv, "-e")).resolve()
    variables: dict[str, str] = {}
    for item in variable_arg.split(","):
        key, separator, value = item.partition("=")
        if not separator or not key or key in variables:
            raise CertificationError("qsub -v mapping is malformed or duplicated")
        variables[key] = value
    if (variables.get("IZANAGI_A2_ATTEMPT_ROOT") != str(attempt_root)
            or variables.get("IZANAGI_A2_EXPECTED_HEAD") != payload["source_commit"]
            or variables.get("IZANAGI_A2_CURRENT_PIN") != current_pin
            or not all(variables.get(name) for name in (
                "IZANAGI_A2_CCBENCH_ROOT", "IZANAGI_A2_REPO_ROOT",
                "IZANAGI_A2_DEPENDENCY_PREFIX_SOURCE",
                "IZANAGI_RESERVATION_JOB_ID", "IZANAGI_RESERVATION_HOST",
                "IZANAGI_RESERVATION_DEADLINE",
            ))):
        raise CertificationError("qsub -v is not bound to attempt and current pin")
    if (argv[-1] != scheduler["job_body"]
            and not argv[-1].endswith("/" + scheduler["job_body"])):
        raise CertificationError("qsub argv does not end in the policy job body")

    visibility = payload["qstat_visibility"]
    if (type(visibility) is not dict
            or visibility.get("observed") is not True
            or visibility.get("request_id") != request_id
            or visibility.get("argv") != ["qstat", "-f", request_id]
            or visibility.get("returncode") != 0
            or type(visibility.get("stdout")) is not str
            or _NQSV_REQUEST_RE.findall(visibility["stdout"]) != [request_id]):
        raise CertificationError("qstat visibility evidence is incomplete")

    logs: dict[str, Any] = {}
    for label, option_path in (
        ("scheduler_stdout", stdout_arg), ("scheduler_stderr", stderr_arg),
    ):
        record = payload[label]
        if type(record) is not dict or set(record) != {"path", "size", "sha256"}:
            raise CertificationError(f"{label} record is incomplete")
        path = _canonical_child(record["path"], attempt_root, label)
        if path != option_path:
            raise CertificationError(f"{label} path differs from qsub argv")
        if type(record["size"]) is not int or record["size"] != path.stat().st_size:
            raise CertificationError(f"{label} size mismatch")
        expected_sha = _require_sha(record["sha256"], f"{label}.sha256")
        if _sha256_file(path) != expected_sha:
            raise CertificationError(f"{label} sha256 mismatch")
        logs[label] = dict(record)
        if label == "scheduler_stderr":
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise CertificationError("cannot read NQSV accounting log") from exc
            if (_NQSV_REQUEST_RE.findall(text) != [request_id]
                    or _NQSV_GROUP_RE.findall(text) != [scheduler["project"]]
                    or _NQSV_STARTED_RE.search(text) is None
                    or _NQSV_ENDED_RE.search(text) is None
                    or _NQSV_ELAPSE_RE.search(text) is None):
                raise CertificationError("NQSV accounting is not request-bound")
    return {
        "request_id": request_id,
        "source_commit": payload["source_commit"],
        **logs,
    }


def _validate_completion_receipt(policy: Policy, payload: Mapping[str, Any],
                                 attempt_id: str, attempt_root: Path,
                                 current_pin: str, request_id: str,
                                 submission: Mapping[str, Any]) -> None:
    required = {
        "schema_version", "study", "protocol_sha256", "attempt_id",
        "attempt_root", "source_commit", "current_pin", "request_id",
        "terminal_observation",
        "driver_rc", "raw_result_manifest", "raw_result_manifest_sha256",
        "scheduler_stdout_sha256", "scheduler_stderr_sha256",
    }
    if not required.issubset(payload):
        raise CertificationError("completion receipt is missing required evidence")
    if (payload["schema_version"] != COMPLETION_SCHEMA
            or payload["study"] != policy.study
            or payload["protocol_sha256"] != policy.protocol_sha256
            or payload["attempt_id"] != attempt_id
            or Path(str(payload["attempt_root"])).resolve() != attempt_root
            or payload["source_commit"] != submission["source_commit"]
            or payload["current_pin"] != current_pin
            or payload["request_id"] != request_id
            or type(payload["driver_rc"]) is not int):
        raise CertificationError("completion receipt identity mismatch")
    terminal = payload["terminal_observation"]
    if (type(terminal) is not dict
            or terminal.get("observed") is not True
            or terminal.get("request_id") != request_id
            or terminal.get("argv") != ["qstat", "-f", request_id]
            or terminal.get("returncode") != 0
            or terminal.get("state") != "END"
            or type(terminal.get("stdout")) is not str
            or _NQSV_REQUEST_RE.findall(terminal["stdout"]) != [request_id]):
        raise CertificationError("scheduler terminal observation is incomplete")
    if _TERMINAL_STATE_RE.search(terminal["stdout"]) is None:
        raise CertificationError("scheduler terminal stdout is not terminal")
    if payload["driver_rc"] == 0:
        manifest_path = _canonical_child(
            payload["raw_result_manifest"], attempt_root, "raw result manifest")
        manifest_sha = _require_sha(
            payload["raw_result_manifest_sha256"], "raw_result_manifest_sha256")
        if _sha256_file(manifest_path) != manifest_sha:
            raise CertificationError("completion raw manifest hash mismatch")
        manifest, _ = _read_json(manifest_path)
        expected_files = {
            f"raw/{cell.cell_id}.json": _sha256_file(
                attempt_root / "raw" / f"{cell.cell_id}.json")
            for cell in policy.cells
        }
        if (manifest.get("schema_version") != RAW_MANIFEST_SCHEMA
                or manifest.get("study") != policy.study
                or manifest.get("protocol_sha256") != policy.protocol_sha256
                or manifest.get("attempt_id") != attempt_id
                or manifest.get("current_pin") != current_pin
                or manifest.get("files") != expected_files):
            raise CertificationError("completion raw manifest identity mismatch")
    elif (payload["raw_result_manifest"] is not None
          or payload["raw_result_manifest_sha256"] is not None):
        raise CertificationError("failed driver completion must not claim a raw manifest")
    if (payload["scheduler_stdout_sha256"]
            != submission["scheduler_stdout"]["sha256"]
            or payload["scheduler_stderr_sha256"]
            != submission["scheduler_stderr"]["sha256"]):
        raise CertificationError("completion scheduler logs are not cross-bound")


def validate_acquisition_bundle(policy: Policy, acquisition_path: Path | str,
                                *, current_pin: str) -> dict[str, Any]:
    acquisition_file = Path(acquisition_path).resolve(strict=True)
    acquisition, acquisition_bytes = _read_json(acquisition_file)
    required = {
        "schema_version", "route", "study", "protocol_sha256", "attempt_id",
        "attempt_root", "source_commit", "current_pin", "request_id",
        "submission_receipt",
        "submission_receipt_sha256", "completion_receipt",
        "completion_receipt_sha256",
    }
    if not required.issubset(acquisition):
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
    if (_sha256_file(submission_path) != submission_sha
            or _sha256_file(completion_path) != completion_sha):
        raise CertificationError("receipt bytes do not match acquisition receipt")
    submission, submission_bytes = _read_json(submission_path)
    completion, completion_bytes = _read_json(completion_path)
    submission_binding = _validate_submission_receipt(
        policy, submission, attempt_id, attempt_root, current_pin)
    if acquisition["request_id"] != submission_binding["request_id"]:
        raise CertificationError("acquisition and submission request IDs differ")
    if acquisition["source_commit"] != submission_binding["source_commit"]:
        raise CertificationError("acquisition and submission source commits differ")
    _validate_completion_receipt(
        policy, completion, attempt_id, attempt_root, current_pin,
        submission_binding["request_id"], submission_binding,
    )
    raw_manifest_bytes = None
    if completion["driver_rc"] == 0:
        _, raw_manifest_bytes = _read_json(
            Path(completion["raw_result_manifest"]).resolve(strict=True))
    return {
        "attempt_id": attempt_id,
        "attempt_root": str(attempt_root),
        "request_id": submission_binding["request_id"],
        "source_commit": submission_binding["source_commit"],
        "acquisition": acquisition,
        "acquisition_bytes": acquisition_bytes,
        "submission": submission,
        "submission_bytes": submission_bytes,
        "completion": completion,
        "completion_bytes": completion_bytes,
        "raw_manifest_bytes": raw_manifest_bytes,
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


def record_completion_receipt(policy: Policy, attempt_root: Path | str,
                              current_pin: str,
                              payload: Mapping[str, Any]) -> Path:
    attempt_id, root = validate_attempt_root(policy, attempt_root)
    submission_path = root / "receipts" / "submission.json"
    submission, _ = _read_json(submission_path)
    binding = _validate_submission_receipt(
        policy, submission, attempt_id, root, current_pin)
    _validate_completion_receipt(
        policy, payload, attempt_id, root, current_pin,
        binding["request_id"], binding,
    )
    path = root / "receipts" / "completion.json"
    write_json_x(path, payload)
    _fsync_dir(path.parent)
    return path


def record_acquisition_receipt(policy: Policy, attempt_root: Path | str,
                               current_pin: str, request_id: str) -> Path:
    attempt_id, root = validate_attempt_root(policy, attempt_root)
    submission_path = root / "receipts" / "submission.json"
    completion_path = root / "receipts" / "completion.json"
    submission, _ = _read_json(submission_path)
    completion, _ = _read_json(completion_path)
    binding = _validate_submission_receipt(
        policy, submission, attempt_id, root, current_pin)
    if request_id != binding["request_id"]:
        raise CertificationError("acquisition request ID differs from submission")
    _validate_completion_receipt(
        policy, completion, attempt_id, root, current_pin, request_id, binding)
    payload = {
        "schema_version": ACQUISITION_SCHEMA,
        "route": "direct-qsub",
        "study": policy.study,
        "protocol_sha256": policy.protocol_sha256,
        "attempt_id": attempt_id,
        "attempt_root": str(root),
        "source_commit": submission.get("source_commit"),
        "current_pin": current_pin,
        "request_id": request_id,
        "submission_receipt": str(submission_path),
        "submission_receipt_sha256": _sha256_file(submission_path),
        "completion_receipt": str(completion_path),
        "completion_receipt_sha256": _sha256_file(completion_path),
    }
    path = root / "receipts" / "acquisition.json"
    write_json_x(path, payload)
    _fsync_dir(path.parent)
    return path


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


def _argv_controlled_defines(argv: Sequence[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for token in argv:
        if not token.startswith("-DCCBENCH_"):
            continue
        key, separator, value = token[2:].partition("=")
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
    controlled = {
        key: value for key, value in values.items()
        if key.startswith("ycsb_") or key in {"thread_num", "extime"}
    }
    return controlled


def validate_trace0_evidence(policy: Policy, cell_id: str, attempt_id: str,
                             current_pin: str, evidence: object) -> dict[str, Any]:
    if type(evidence) is not dict:
        raise CertificationError("trace0 evidence must be an object")
    required = {
        "schema_version", "cell_id", "attempt_id", "current_pin",
        "source_commit", "controlled_defines", "configure_argv", "build_argv",
        "build_dir", "run_argv", "perf_binary", "perf_bin_sha256",
        "build_done", "compile_out_evidence_scope",
    }
    if not required.issubset(evidence):
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
    if _argv_controlled_defines(configure) != expected:
        raise CertificationError("configure argv controlled define map is not exact")
    build_dir = Path(str(evidence["build_dir"])).resolve(strict=True)
    if (_cmake_directory(configure, "-B") != build_dir
            or _cmake_directory(build, "--build") != build_dir):
        raise CertificationError("configure and build directories are not identical")
    perf_binary = Path(str(evidence["perf_binary"])).resolve(strict=True)
    if perf_binary.is_symlink() or not perf_binary.is_file():
        raise CertificationError("performance binary is not a regular file")
    expected_executable = (
        build_dir / f"ycsb_{policy.document['performance_common']['ccbench_protocol']}.exe")
    if perf_binary != expected_executable:
        raise CertificationError("performance binary is not the build canonical executable")
    if Path(run[0]).resolve(strict=True) != perf_binary:
        raise CertificationError("run argv[0] is not the canonical performance binary")
    cell = policy.cell(cell_id)
    if _run_workload_flags(run) != _expected_verify_flags(
            policy, cell, PERFORMANCE_TAG):
        raise CertificationError("trace0 run workload is not exact performance workload")
    actual_sha = _sha256_file(perf_binary)
    if _require_sha(evidence["perf_bin_sha256"], "perf_bin_sha256") != actual_sha:
        raise CertificationError("perf_bin_sha256 does not match binary bytes")
    build_done = evidence["build_done"]
    if (type(build_done) is not dict
            or build_done.get("source_commit") != current_pin
            or build_done.get("perf_bin_sha256") != actual_sha
            or _SHA256_RE.fullmatch(str(build_done.get("trace_bin_sha256", ""))) is None
            or build_done.get("trace_bin_sha256") == actual_sha):
        raise CertificationError("trace/performance build_done binding is incomplete")
    return dict(evidence)


def validate_build_evidence(current_pin: str, evidence: object) -> dict[str, Any]:
    if type(evidence) is not dict:
        raise CertificationError("trace/performance build evidence is missing")
    required = {
        "source_commit", "trace_enabled_build", "performance_trace_disabled_build",
        "trace_bin_sha256", "perf_bin_sha256", "compile_out_evidence_scope",
    }
    if (not required.issubset(evidence)
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


def _classify_verify(policy: Policy, cell: CellSpec, tag: str, raw: object,
                     build_attempt_id: str) -> str:
    if type(raw) is not dict:
        return "indeterminate"
    if (raw.get("tag") != tag or raw.get("trace_enabled") is not True
            or raw.get("build_attempt_id") != build_attempt_id
            or raw.get("workload_flags") != _expected_verify_flags(policy, cell, tag)):
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
            or not all(type(value) in {int, float} and value > 0 for value in samples)):
        return "performance-indeterminate", None
    return "complete", float(statistics.median(samples))


def collect_results(policy: Policy, raw_results: Iterable[Mapping[str, Any]],
                    *, attempt_id: str, current_pin: str,
                    request_id: str) -> dict[str, Any]:
    raw_list = list(raw_results)
    if len(raw_list) != len(policy.cells):
        raise CertificationError("raw result count does not match exact four-cell protocol")
    indexed: dict[str, Mapping[str, Any]] = {}
    for raw in raw_list:
        if type(raw) is not dict or raw.get("schema_version") != RAW_RESULT_SCHEMA:
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
        if raw.get("campaign_preimage") != expected_preimage:
            raise CertificationError("campaign preimage and protocol differ")
        perf = perf_config_for_cell(policy, cell.cell_id)
        validate_campaign_binding(
            policy, cell.workload_id, attempt_id, current_pin,
            raw["campaign_preimage"], perf,
        )
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
        else:
            legacy_status = _classify_verify(
                policy, cell, LEGACY_TAG, correctness.get(LEGACY_TAG),
                build_attempt_id,
            )
            performance_status = _classify_verify(
                policy, cell, PERFORMANCE_TAG,
                correctness.get(PERFORMANCE_TAG), build_attempt_id,
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
            effects[workload_id] = adopted / stock - 1.0
    if any_indeterminate:
        status = "indeterminate"
    elif any_anomaly:
        status = "reject"
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
        "attempt_id": attempt_id,
        "request_id": request_id,
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
        "smallest_observed_sufficient_in_this_two_point_protocol": (
            (policy.document["legacy_correctness"]["ycsb_tuple_num"] + "/"
             + policy.document["legacy_correctness"]["thread_num"])
            if all(cell["correctness"]["status"] == "certified"
                   for cell in cells) else None
        ),
        "global_minimality_established": False,
        "compile_out_evidence_scope": COMPILE_OUT_SCOPE,
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
        "workload_flags": _expected_verify_flags(policy, cell, tag),
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


def _raw_cell_from_wal(policy: Policy, cell: CellSpec, *, result: object,
                       layout_root: str, attempt_id: str,
                       current_pin: str) -> dict[str, Any]:
    from .layout import CampaignLayout
    from .model import (STAGE_ABORT, STAGE_BENCH_DONE, STAGE_BUILD_DONE,
                        STAGE_BUILD_START, STAGE_COMMIT, STAGE_VERIFY_DONE)
    from . import wal

    records = [record for record in wal.read_records(CampaignLayout(layout_root))
               if record.variant == result.variant]
    starts = [record for record in records if record.stage == STAGE_BUILD_START]
    if len(starts) != 1:
        raise CertificationError("fresh cell does not have one build attempt")
    build_attempt_id = starts[0].payload.get("build_attempt_id")
    if type(build_attempt_id) is not str or not build_attempt_id:
        raise CertificationError("WAL build attempt identity is missing")
    build_done = _event_payload(records, STAGE_BUILD_DONE, build_attempt_id)
    bench_done = _event_payload(records, STAGE_BENCH_DONE, build_attempt_id)
    commit = _event_payload(records, STAGE_COMMIT, build_attempt_id)
    abort = _event_payload(records, STAGE_ABORT, build_attempt_id)
    verify_payloads = [record.payload for record in records
                       if record.stage == STAGE_VERIFY_DONE
                       and record.payload.get("build_attempt_id") == build_attempt_id]
    by_tag: dict[str, Mapping[str, Any]] = {}
    for payload in verify_payloads:
        workload = payload.get("workload")
        tag = workload.get("tag") if type(workload) is dict else None
        if type(tag) is not str or tag in by_tag:
            raise CertificationError("WAL verify tag is missing or duplicated")
        by_tag[tag] = payload

    trace_sha = build_done.get("trace_bin_sha256") if build_done else None
    correctness = {
        LEGACY_TAG: _raw_verify_record(
            policy, cell, LEGACY_TAG, by_tag.get(LEGACY_TAG), abort,
            build_attempt_id, trace_sha,
        ),
        PERFORMANCE_TAG: _raw_verify_record(
            policy, cell, PERFORMANCE_TAG, by_tag.get(PERFORMANCE_TAG), abort,
            build_attempt_id, trace_sha,
        ),
    }
    trace0: Optional[dict[str, Any]] = None
    performance: dict[str, Any] = {
        "status": "indeterminate",
        "trace_enabled": False,
        "build_attempt_id": build_attempt_id,
        "workload": dict(cell.perf),
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
        if type(run) is tuple:
            run = list(run)
        if (type(configure) is list and type(build) is list
                and type(run) is list and run):
            build_dir = _cmake_directory(configure, "-B")
            perf_binary = Path(run[0]).resolve(strict=True)
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
                "build_done": {
                    "source_commit": current_pin,
                    "trace_bin_sha256": build_done.get("trace_bin_sha256"),
                    "perf_bin_sha256": build_done.get("perf_bin_sha256"),
                },
                "compile_out_evidence_scope": COMPILE_OUT_SCOPE,
            }
            performance = {
                "status": "complete" if commit is not None else "indeterminate",
                "trace_enabled": False,
                "build_attempt_id": build_attempt_id,
                "workload": dict(cell.perf),
                "perf_bin_sha256": build_done.get("perf_bin_sha256"),
                "samples_tps": bench_done.get("tps"),
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
        "campaign_preimage": campaign_preimage(
            policy, cell.workload_id, attempt_id, current_pin),
        "build_attempt_id": build_attempt_id,
        "build_evidence": ({
            "source_commit": current_pin,
            "trace_enabled_build": True,
            "performance_trace_disabled_build": True,
            "trace_bin_sha256": build_done.get("trace_bin_sha256"),
            "perf_bin_sha256": build_done.get("perf_bin_sha256"),
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
    from .model import CampaignConfig, Genome

    attempt_name, attempt = validate_attempt_root(policy, attempt_root)
    if attempt_name != attempt.name:
        raise CertificationError("attempt identity mismatch")
    raw = Path(raw_root).resolve(strict=True)
    if raw != attempt / "raw" or raw.is_symlink() or not raw.is_dir():
        raise CertificationError("raw root is not the exact attempt child")
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
    common = policy.document["performance_common"]
    genomes = []
    for cell in cells:
        flags = {
            key.removeprefix("CCBENCH_"): int(value)
            for key, value in policy.document["controlled_define_base"].items()
            if key != "CCBENCH_TRACE"
        }
        flags.update(cell.genome)
        genomes.append(Genome(
            protocol=common["ccbench_protocol"], flags=flags,
        ))
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
    output_root = attempt / "campaigns"
    output_root.mkdir(mode=0o700, exist_ok=True)
    resolved_output = resolve_campaign_output_root("official", str(output_root))
    claim_root = Path(env_scope_dir(contract.env_tag, resolved_output)) / "claims"
    claim_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    durable_policy = DurableRootPolicy(
        approved_roots=(policy.durable_base,),
        forbidden_roots=(Path("/tmp"), Path("/scr")),
    )
    summary = run_campaign(
        cfg, genomes, perf, contract.env_tag, contract.clocks_per_us,
        numactl=contract.numactl, do_bench=True, output_root=str(output_root),
        log=log, ccbench_dir=str(source_root), env_contract=contract,
        dependency_prefix=str(dependency),
        authorization_contract=authorization,
        build_context=build_run_context(generator_id=GeneratorId.BACKOFF_REPRO),
        declared_use_class="official",
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
            payload["correctness"][tag].get("status")
            for tag in (LEGACY_TAG, PERFORMANCE_TAG)
        }
        if "anomaly" not in statuses:
            raise CertificationError(
                "workload evidence, infrastructure, or performance is incomplete")
    return summary


def load_raw_results(policy: Policy, attempt_root: Path) -> list[dict[str, Any]]:
    raw_root = attempt_root / "raw"
    if raw_root.is_symlink() or not raw_root.is_dir():
        raise CertificationError("raw result root is missing")
    expected = {f"{cell.cell_id}.json" for cell in policy.cells}
    observed = {path.name for path in raw_root.iterdir() if path.is_file()}
    if observed != expected:
        raise CertificationError("raw root has missing or extra cell files")
    return [_read_json(raw_root / f"{cell.cell_id}.json")[0]
            for cell in policy.cells]


def finalize_raw_manifest(policy: Policy, attempt_root: Path | str,
                          current_pin: str) -> Path:
    attempt_id, root = validate_attempt_root(policy, attempt_root)
    # Loading first applies the exact missing/extra file predicate.  The raw
    # payloads are collected later; this manifest only freezes their bytes.
    load_raw_results(policy, root)
    raw_root = root / "raw"
    files = {
        f"raw/{cell.cell_id}.json": _sha256_file(
            raw_root / f"{cell.cell_id}.json")
        for cell in policy.cells
    }
    manifest = {
        "schema_version": RAW_MANIFEST_SCHEMA,
        "study": policy.study,
        "protocol_sha256": policy.protocol_sha256,
        "attempt_id": attempt_id,
        "current_pin": current_pin,
        "files": files,
    }
    path = root / "raw-manifest.json"
    write_json_x(path, manifest)
    _fsync_dir(root)
    return path


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


def materialize(policy: Policy, report: Mapping[str, Any], evidence: Mapping[str, Any],
                *, repo_root: Path | str) -> Path:
    if (report.get("attempt_id") != evidence.get("attempt_id")
            or report.get("request_id") not in {None, evidence.get("request_id")}
            or report.get("protocol_sha256") != policy.protocol_sha256
            or evidence.get("acquisition", {}).get("protocol_sha256")
            != policy.protocol_sha256):
        raise CertificationError("materializer report and terminal evidence differ")
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
        certification_bytes = _canonical_json(report)
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


def compute_preflight(policy: Policy, *, attempt_root: Path | str,
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
    if len(reservation_values) < 3:
        raise CertificationError("reservation binding is incomplete")
    root = Path(repo_root).resolve(strict=True)
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
    expected_raw = attempt / "raw"
    requested_raw = Path(raw_root).resolve(strict=False)
    if requested_raw != expected_raw or requested_raw.exists() or requested_raw.is_symlink():
        raise CertificationError("raw root is not the fresh exact attempt child")
    dependency = Path(dependency_prefix).resolve(strict=True)
    if dependency.is_symlink() or not dependency.is_dir():
        raise CertificationError("dependency staging prefix is unavailable")
    requested_raw.mkdir(mode=0o700, exist_ok=False)
    _fsync_dir(attempt)
    return requested_raw


def _collect_command(args: argparse.Namespace) -> int:
    policy = load_policy(args.policy)
    evidence = validate_acquisition_bundle(
        policy, args.acquisition_receipt, current_pin=args.current_pin)
    attempt_id, attempt_root = validate_attempt_root(policy, args.attempt_root)
    if (attempt_id != evidence["attempt_id"]
            or str(attempt_root) != evidence["attempt_root"]):
        raise CertificationError("collector attempt differs from receipt attempt")
    try:
        report = collect_results(
            policy, load_raw_results(policy, attempt_root),
            attempt_id=attempt_id, current_pin=args.current_pin,
            request_id=evidence["request_id"],
        )
    except CertificationError as exc:
        report = {
            "schema_version": CERTIFICATION_SCHEMA,
            "study": policy.study,
            "protocol_schema": POLICY_SCHEMA,
            "protocol_sha256": policy.protocol_sha256,
            "policy_sha256": policy.bytes_sha256,
            "attempt_id": attempt_id,
            "request_id": evidence["request_id"],
            "current_pin": args.current_pin,
            "source_commit": evidence["source_commit"],
            "cells": [],
            "effects": {},
            "status": "indeterminate",
            "reason": str(exc),
            "a4_noise_floor_status": "open",
            "legacy_role": "historically inherited companion",
            "smallest_observed_sufficient_in_this_two_point_protocol": None,
            "global_minimality_established": False,
            "compile_out_evidence_scope": COMPILE_OUT_SCOPE,
        }
    else:
        report["source_commit"] = evidence["source_commit"]
    destination = materialize(policy, report, evidence, repo_root=args.repo_root)
    print(destination)
    return driver_rc(report)


def _preflight_command(args: argparse.Namespace) -> int:
    policy = load_policy(args.policy)
    raw = compute_preflight(
        policy, attempt_root=args.attempt_root, raw_root=args.raw_root,
        expected_head=args.expected_head, repo_root=args.repo_root,
        dependency_prefix=args.dependency_prefix,
    )
    print(raw)
    return 0


def _run_workload_command(args: argparse.Namespace) -> int:
    policy = load_policy(args.policy)
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
    policy = load_policy(args.policy)
    print(preregister_attempt(policy, args.attempt_id, args.current_pin))
    return 0


def _finalize_raw_command(args: argparse.Namespace) -> int:
    policy = load_policy(args.policy)
    print(finalize_raw_manifest(policy, args.attempt_root, args.current_pin))
    return 0


def _record_receipt_command(args: argparse.Namespace) -> int:
    policy = load_policy(args.policy)
    if args.receipt_kind == "acquisition":
        path = record_acquisition_receipt(
            policy, args.attempt_root, args.current_pin, args.request_id)
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
    parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    sub = parser.add_subparsers(dest="command", required=True)
    preflight = sub.add_parser("compute-preflight")
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
    acquisition.add_argument("--request-id", required=True)
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
