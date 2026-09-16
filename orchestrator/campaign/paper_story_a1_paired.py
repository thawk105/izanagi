# -*- coding: utf-8 -*-
"""D95 paper-story A-1 exploratory two-arm measurement and materializer.

The measurement path deliberately reuses ``loop.run_campaign``.  Legacy v2
retains the producer's default remeasurement, while v3 is fail-closed onto the
registered one-round balanced executor.  Invalid campaigns remain first-class
raw results and are never silently replaced or promoted.
"""
from __future__ import annotations

import argparse
import ctypes
from contextlib import nullcontext
import errno
import hashlib
import hmac
import json
import math
import os
import re
import secrets
import shutil
import shlex
import socket
import stat
import statistics
import struct
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal, Mapping, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from ..calibrator import runner as calibrator_runner  # noqa: E402
from ..scheduler_nqsv import (  # noqa: E402
    QSTAT_REQUEST_ID_RE as _QSTAT_REQUEST_ID_RE,
    target_bound_qstat_state_result,
)
from . import (  # noqa: E402
    buildcache,
    campaign_lock as campaign_lock_codec,
    condition_meaning_gate,
    ident,
    p2_2,
    patchharness,
    paper_story_a1_source as a1_source,
    pin,
    site_policy,
    trial_registry,
    wal,
)
from .build_admission import (  # noqa: E402
    GeneratorId,
    attest_generator_output,
    build_run_context,
)
from .durable_root import DurableRootPolicy  # noqa: E402
from .layout import CampaignLayout, exploration_campaign_layout  # noqa: E402
from . import loop as campaign_loop  # noqa: E402
from .loop import run_campaign  # noqa: E402
from .model import (  # noqa: E402
    CampaignConfig,
    Genome,
    STAGE_ABORT,
    STAGE_BENCH_DONE,
    STAGE_BUILD_DONE,
    STAGE_BUILD_START,
    STAGE_COMMIT,
    STAGE_VERIFY_DONE,
)
from .pipeline import BalancedScheduleConfig, PerfConfig  # noqa: E402
from .p2_2 import _assert_single_tenant  # noqa: E402
from .reservation import (  # noqa: E402
    ReservationBinding,
    ReservationError,
    read_binding,
)


POLICY_SCHEMA_V2 = "paper-story-a1-paired-policy/v2"
POLICY_SCHEMA_V3 = "paper-story-a1-paired-policy/v3"
POLICY_PATH = Path(__file__).with_name("paper_story_a1_paired.v2.json")
V3_PILOT_POLICY_PATH = Path(__file__).with_name(
    "paper_story_a1_paired.v3-pilot.json"
)
V3_SIZED_POLICY_PATH = Path(__file__).with_name(
    "paper_story_a1_paired.v3-sized.json"
)
DECLARED_USE_CLASS = "exploration"
STUDY_ID = "paper-story-a1-20260826-sized-v1"
V3_PILOT_STUDY_ID = "paper-story-a1-20260901-balanced5-pilot-v1"
V3_SIZED_STUDY_ID = "paper-story-a1-20260901-balanced5-sized-v1"
RESULT_SCHEMA = "paper-story-a1-paired-result/v3"
RECEIPT_SCHEMA = "paper-story-a1-paired-receipt/v3"
JOB_TERMINAL_SCHEMA = "paper-story-a1-paired-job-terminal/v3"
SUBMISSION_SCHEMA = "paper-story-a1-paired-submission/v1"
SUBMISSION_INTENT_SCHEMA = "paper-story-a1-paired-submission-intent/v1"
ACQUISITION_SCHEMA = SUBMISSION_SCHEMA
COMPLETION_SCHEMA = "paper-story-a1-paired-scheduler-completion/v2"
V3_GROUP_SUBMISSION_SCHEMA = "paper-story-a1-paired-group-submission/v1"
V3_GROUP_SUBMISSION_FAILURE_SCHEMA = (
    "paper-story-a1-paired-group-submission-failure/v1"
)
V3_GROUP_INTENT_SCHEMA = "paper-story-a1-paired-group-intent/v1"
V3_WORKLOAD_SHARD_SCHEMA = "paper-story-a1-paired-workload-shard/v1"
V3_WORKLOAD_RECEIPT_SCHEMA = "paper-story-a1-paired-workload-receipt/v1"
V3_JOB_TERMINAL_SCHEMA = "paper-story-a1-paired-workload-job-terminal/v1"
V3_GROUP_TERMINAL_SCHEMA = "paper-story-a1-paired-group-terminal/v1"
V3_GROUP_COMPLETION_SCHEMA = "paper-story-a1-paired-group-completion/v1"
V3_READY_SCHEMA = "paper-story-a1-paired-workload-ready/v1"
V3_BENCH_GO_SCHEMA = "paper-story-a1-paired-bench-go/v1"
V3_BENCH_START_SCHEMA = "paper-story-a1-paired-bench-start/v1"
_SUBMISSION_RECEIPT_KEYS = frozenset({
    "schema_version", "route", "study_id", "source_commit", "attempt_root",
    "request_id", "submission_receipt_path", "completion_receipt_path",
    "qsub_argv", "qsub_options", "submit_observation",
})
NON_CERTIFYING_OBSERVATION_SCHEMA = (
    "paper-story-a1-non-certifying-observation/v1"
)
NON_CERTIFYING_OBSERVATION_FILENAME = "non-certifying-observation.json"
_NON_CERTIFYING_RESULT_KEYS = frozenset({
    "schema_version", "study_id", "formal", "promotion_prohibited",
    "authority", "pairing_design", "policy_sha256", "source_binding",
    "reservation_binding", "pbs_evidence_scope", "workload_reps",
    "all_workloads_terminal", "complete", "measurement_error", "workloads",
    "limitations",
})
_V3_NON_CERTIFYING_RESULT_KEYS = (
    _NON_CERTIFYING_RESULT_KEYS - {"reservation_binding"}
) | {"job_executions"}
_NON_CERTIFYING_RECEIPT_KEYS = frozenset({
    "schema_version", "study_id", "formal", "promotion_prohibited", "route",
    "pbs_jobid", "host", "recorded_epoch", "policy", "source_binding",
    "submission_receipt", "scheduler_completion_receipt", "roots", "result",
    "calibration_sha256",
})
_V3_NON_CERTIFYING_RECEIPT_KEYS = (
    _NON_CERTIFYING_RECEIPT_KEYS
    - {"pbs_jobid", "host", "calibration_sha256"}
) | {"job_executions"}
PAIRING_DESIGN = "arm-grouped-positional-v1"
V3_PAIRING_DESIGN = "balanced-a5b5-b5a5-v1"
ARM_ORDER = ("adaptive", "static10")
WORKLOAD_ORDER = ("write-heavy", "balanced", "read-heavy")
EXPECTED_VERIFY_CONFIGS = ("legacy",)
PIPELINE_RELATIVE_PATH = "orchestrator/campaign/pipeline.py"
DRIVER_RELATIVE_PATH = "orchestrator/campaign/paper_story_a1_paired.py"
POLICY_RELATIVE_PATH = "orchestrator/campaign/paper_story_a1_paired.v2.json"
V3_PILOT_POLICY_RELATIVE_PATH = (
    "orchestrator/campaign/paper_story_a1_paired.v3-pilot.json"
)
V3_SIZED_POLICY_RELATIVE_PATH = (
    "orchestrator/campaign/paper_story_a1_paired.v3-sized.json"
)
JOB_RELATIVE_PATH = "tools/pegasus/paper_story_a1_paired.sh"
PREREGISTRATION_RELATIVE_PATH = (
    "output/insights/2026-08-26_paper-story-a1-sized-preregistration/README.md"
)
SOURCE_RELATIVE_PATHS = (
    DRIVER_RELATIVE_PATH,
    POLICY_RELATIVE_PATH,
    PIPELINE_RELATIVE_PATH,
    JOB_RELATIVE_PATH,
)
NON_CERTIFYING_SOURCE_RELATIVE_PATHS = SOURCE_RELATIVE_PATHS + (
    "orchestrator/campaign/campaign_lock.py",
    "orchestrator/campaign/ident.py",
    "orchestrator/campaign/wal.py",
    "orchestrator/campaign/loop.py",
    "orchestrator/campaign/trial_registry.py",
)
V3_SOURCE_RELATIVE_PATHS = SOURCE_RELATIVE_PATHS + (
    "orchestrator/calibrator/runner.py",
)
V3_NON_CERTIFYING_SOURCE_RELATIVE_PATHS = (
    NON_CERTIFYING_SOURCE_RELATIVE_PATHS
    + ("orchestrator/calibrator/runner.py",)
)
BALANCED_SCHEDULE_RECEIPT_NAME = "balanced-schedule-receipt.json"
BALANCED_SIZING_CERTIFICATE_SCHEMA = (
    "paper-story-a1-balanced-sizing-certificate/v1"
)
BALANCED_SIZING_PILOT_SCHEMA = "paper-story-a1-balanced-sizing-pilot/v1"
BALANCED_SIZING_PILOT_FILENAME = "sizing-pilot.json"
MATERIALIZATION_RELATIVE_PATH = Path(
    "output/insights/2026-08-26_paper-story-a1-sized"
)
COMPLETION_MARKER = ".complete.json"
POLICY_SHA256 = "83b9c1a1ca4cce1e6394ce3338b491b14663427259eb3e129560fe5b50b99b5b"
V3_PILOT_POLICY_SHA256 = (
    "ed1c942f9d4bc24ab1bc6106caea672262c8634d32b022eca75b125811f7b825"
)
V3_SIZED_POLICY_SHA256 = (
    "a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a"
)
CANONICAL_CCBENCH_OID = "511c9538e4e8efa54b45cda62e72389ed3b706ec"
PREREGISTRATION_SHA256 = (
    "c85279e997c7483060f3282836aa4800f473b95fe5f0fc1807431f06a0817fea"
)
V3_PILOT_PREREGISTRATION_RELATIVE_PATH: str | None = (
    "output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md"
)
V3_PILOT_PREREGISTRATION_SHA256: str | None = (
    "8f8d2ad338a7a3193aaee8433c1495cef06b9520425251dd8bef89584ca626fc"
)
V3_SIZED_PREREGISTRATION_RELATIVE_PATH: str | None = (
    "output/insights/2026-09-13/"
    "paper-story-a1-balanced5-sized-preregistration/README.md"
)
V3_SIZED_PREREGISTRATION_SHA256: str | None = (
    "6047eff005fbd94bad8df0313124bd4ca037dedf0f2e3db05224d04ad34fd3c2"
)
# Frozen preregistration §§5.4–5.5; D1452 consumer registration values.
V3_SIZED_CERTIFICATE_REGISTERED_PARAMETERS = (
    ("search", "trials", 20000),
    ("certification", "trials", 100000),
    ("candidate_grid", "registered_minimum", 28),
    ("candidate_grid", "maximum", 4096),
    (
        "root_seed", "digest",
        "e72bc005d156caea2c89085c563c72fa04bbeb4afd98160fca968da9a7f6b3b3",
    ),
)
WORKLOAD_DESIGNS = {
    "write-heavy": {
        "reps": 72,
        "df": 71,
        "k": 1.993943,
        "planned_sigma_tps": 103551.0849,
    },
    "balanced": {
        "reps": 205,
        "df": 204,
        "k": 1.971661,
        "planned_sigma_tps": 156906.1857,
    },
    "read-heavy": {
        "reps": 28,
        "df": 27,
        "k": 2.051831,
        "planned_sigma_tps": 60384.6868,
    },
}
CLASSIFICATION_RULES = [
    {
        "priority": 1,
        "predicate": "abs(mean) - h > B",
        "classification": "resolved-above-floor",
    },
    {
        "priority": 2,
        "predicate": "abs(mean) + h <= B",
        "classification": "bounded-below-floor",
    },
    {
        "priority": 3,
        "predicate": "otherwise",
        "classification": "unresolved",
    },
]
RERUN_REASONS = [
    "build-failure-before-bench",
    "verify-failure-before-bench",
    "competing-tenant-detected-before-bench",
    "scheduler-or-infrastructure-failure-before-bench",
]
V3_INVALID_RULES = [
    "campaign workload arm set is not exactly its registered variant and baseline",
    "an arm has anything other than exactly one build attempt",
    "both arms are not built and verified before the first bench block",
    "a verify_done is not certified true or its workload tag differs",
    "a competing-tenant probe is missing, raises, or detects a tenant before any five-rep arm block",
    "settle is missing, fails, or occurs other than once at workload schedule start",
    "bench throughput has no point",
    "bench aggregate CV is undefined",
    "bench aggregate CV is not computed from every rep of its arm",
    "bench rounds is not exactly integer one",
    "bench unstable is not exactly false",
    "a block has anything other than five positive finite throughput points",
    "schedule receipt is missing or differs from the frozen seed derivation and physical order",
    "a workload is interrupted, one-sided committed, or lacks both arm completion records",
    "trace0 source-routed evidence is incomplete or inconsistent",
    "CCBench HEAD differs from canonical pin or CCBench tracked files are dirty at a required boundary",
]
V3_CCBENCH_BOUNDARIES = [
    "login-submit-before-intent-and-qsub",
    "compute-job-body-preflight",
    "driver-measurement-start",
    "before-each-trace-and-perf-build",
    "artifact-consumer-arm-validation-and-materializer-raw-recollection",
]
PREREGISTERED_LIMITATIONS = (
    "- **arm を別々の時間帯で測る交絡は反復数では消えない。** 1 arm の block は 205 rep で約 615 秒に\n"
    "  なり、pilot の 15 秒から 40 倍以上に伸びる。同じ番号の「対」の時間隔もそれだけ開く (luna-8)。\n"
    "- 位置対応差の SD が表すのは**この 1 走で便宜的に同番号を引いた差の散らばり**であって、\n"
    "  母平均の不確かさではない (sol-12)。\n"
    "- したがって出す区間は**事前登録した記述的な区間**であり、公式の信頼区間ではない。因果・母集団・\n"
    "  再現性・公式有意差は主張しない (sol-14)。\n"
    "- 計画 sigma は 5 点から作った上側限界であり、正規性・定常性・150 点との同分布性は検査できない。\n"
    "  3 workload を同時に 95% とも扱えない (Bonferroni では 85%) (sol-4)。\n"
    "- 観測窓が 40 倍になるため、CV が 5% を越えて `rounds != 1` になる確率は pilot から予測できない\n"
    "  (sol-18)。\n"
    "- `rep_notes` 非空は n に対して急速に壊れる。1 rep あたり 0.1% でも balanced 1 workload で\n"
    "  約 33.5%。これは感度分析であって p の推定ではない (sol-15, sol-17)。\n"
)
CONTROLLED_CCBENCH_DEFINES = frozenset({
    "BACK_OFF",
    "BACKOFF_FIXED",
    "NO_WAIT_LOCKING_IN_VALIDATION",
    "NO_WAIT_OF_TICTOC",
    "TRACE",
    "WAL",
})
_FULL_OID = re.compile(r"[0-9a-f]{40}")
_FULL_SHA256 = re.compile(r"[0-9a-f]{64}")
_PBS_JOBID = re.compile(r"(?:0:)?[A-Za-z0-9][A-Za-z0-9._-]*")
_NORMALIZED_REQUEST_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_REQUEST_RE = re.compile(r"Request\s+(\S+)\s+submitted")
_QSTAT_STATE_RE = re.compile(
    r"(?im)^\s*(?:job_state|State)\s*[:=]\s*([A-Za-z]+)\s*$"
)
_QSTAT_EXIT_STATUS_RE = re.compile(
    r"(?im)^\s*(?:exit_status|Exit Status)\s*[:=]\s*(-?\d+)\s*$"
)
_PBS_QUEUE = "gen_S"
_NQSV_EXECUTION_QUEUE_CANDIDATE_RE = re.compile(
    r"(?m)^[ \t]*Queue[ \t]*=[ \t]*\S(?:[^\r\n]*\S)?[ \t]+"
    r"\(Execution[ \t]+Queue\)[ \t]*$"
)
_NQSV_EXECUTION_QUEUE_RE = re.compile(
    r"(?m)^[ \t]*Queue[ \t]*=[ \t]*([A-Za-z0-9._-]+)@nqsv[ \t]+"
    r"\(Execution[ \t]+Queue\)[ \t]*$"
)
_NQSV_DISAPPEARED_RE = re.compile(
    r"[ \t]*Batch[ \t]+Request:[ \t]+(\S+)[ \t]+does[ \t]+not[ \t]+"
    r"exist[ \t]+on[ \t]+nqsv\.[ \t]*(?:\r?\n)?"
)
_NQSV_SUBMISSION_VISIBLE_STATES = frozenset({"QUE", "RUN"})
NQSV_QSTAT_STATES = frozenset({
    "ARR",
    "WAI",
    "QUE",
    "PRR",
    "RUN",
    "POR",
    "EXT",
    "HLD",
    "HOL",
    "SUS",
    "MIG",
    "STG",
})
NQSV_QSTAT_TERMINAL_STATES = frozenset({"C", "F", "EXT"})
_PBS_OBSERVATION_KEYS = frozenset({
    "pbs_jobid",
    "pbs_o_host",
    "pbs_o_workdir",
})
RESERVATION_BINDING_KEYS = (
    "job_id",
    "requested_s",
    "scheduler_started_epoch",
    "deadline_epoch",
    "host",
    "boot_id",
    "script_sha256",
    "nonce",
)
V3_ACCOUNTING_KEYS = frozenset({
    "method",
    "started_epoch_s",
    "ended_epoch_s",
    "started_monotonic_s",
    "ended_monotonic_s",
    "elapsed_s",
    "shell_user_s",
    "shell_system_s",
    "reaped_descendants_user_s",
    "reaped_descendants_system_s",
    "cpu_total_s",
    "times_baseline_raw",
    "times_final_raw",
    "unreaped_descendants",
})
PBS_EVIDENCE_SCOPE = {
    "job_environment_fields": (
        "PBS_JOBID",
        "PBS_O_HOST",
        "PBS_O_WORKDIR",
    ),
    "omitted_job_observations": (
        "PBS_O_QUEUE (not exported by this NQSV site)",
        "stdout/stderr FD targets (not the qsub -o/-e delivery files on NQSV)",
    ),
    "queue_binding": "submission qstat_visibility only",
    "delivery_log_binding": (
        "scheduler completion receipt path/bytes SHA-256 plus job-terminal SHA-256"
    ),
}
MATERIALIZATION_EVIDENCE_SCHEMA = (
    "paper-story-a1-paired-materialization-evidence/v2"
)
MATERIALIZATION_PUBLISH_SCHEMA = (
    "paper-story-a1-paired-materialization-publish/v1"
)
PUBLISH_RENAME_NOREPLACE = "renameat2-rename-noreplace"
PUBLISH_EINVAL_FALLBACK = "a1-exclusive-claim-check-then-renameat2"
_RENAME_DEFAULT = 0
_RENAME_NOREPLACE = 1
_AT_FDCWD = -100
SCHEDULER_COMPLETION_INTERPRETATION = {
    "terminal_forms": {
        "scheduler-end-state": (
            "qstat still exposes terminal state and scheduler exit status"
        ),
        "request-disappeared-after-visibility": (
            "submission qstat_visibility proves the request was visible before a "
            "later successful qstat observation no longer exposes it; scheduler "
            "state and exit status are explicitly unobserved"
        ),
    },
    "job_outcome": (
        "driver_rc=0, shell_rc=0, and job terminal status=finished establish job "
        "success even when a disappeared request has no observable scheduler exit status"
    ),
}
_OBSERVATION_TAG_DOMAIN = b"izanagi-a1-observation-identity-tag/v1\0"
_NON_CERTIFYING_VIEW_TOKEN = object()


class PaperStoryError(RuntimeError):
    """The A-1 preregistered contract is not satisfied."""


class _PublishedReceiptCleanupError(PaperStoryError):
    """Receipt publication succeeded, but owned staging cleanup failed."""


@dataclass(frozen=True, slots=True)
class NonCertifyingObservationView:
    """A-1専用consumerが再検証後にだけ発行する局所view。"""

    sidecar_path: Path
    common_record: Mapping[str, object]
    campaigns: tuple[Mapping[str, object], ...]
    result: Mapping[str, object]
    receipt: Mapping[str, object]
    _token: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self._token is not _NON_CERTIFYING_VIEW_TOKEN:
            raise TypeError(
                "NonCertifyingObservationView は A-1専用consumerだけが発行できる"
            )


def _freeze_json(value: object) -> object:
    if type(value) is dict:
        return MappingProxyType({
            key: _freeze_json(item) for key, item in value.items()
        })
    if type(value) is list:
        return tuple(_freeze_json(item) for item in value)
    return value


def _reject_duplicate_keys(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise PaperStoryError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def _reject_constant(value: str):
    raise PaperStoryError(f"non-finite JSON constant: {value}")


def _read_json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as stream:
            value = json.load(
                stream,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=_reject_constant,
            )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise PaperStoryError(f"JSON read failed: {path}: {exc}") from exc
    if type(value) is not dict:
        raise PaperStoryError(f"JSON root is not an object: {path}")
    return value


def _decode_json_bytes(raw: bytes, label: str) -> dict:
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise PaperStoryError(f"JSON bytes decode failed: {label}: {exc}") from exc
    if type(value) is not dict:
        raise PaperStoryError(f"JSON bytes root is not an object: {label}")
    return value


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _normalize_request_id(value: str) -> str:
    """Match dispatch_compute's request-ID normalization exactly."""
    if type(value) is not str:
        raise PaperStoryError("request ID is not a string")
    normalized = value.strip().rstrip(".")
    if normalized.startswith("0:"):
        normalized = normalized[2:]
    if not normalized:
        raise PaperStoryError("request ID is empty")
    return normalized


def _validated_request_id(value: str, label: str) -> str:
    normalized = _normalize_request_id(value)
    if _NORMALIZED_REQUEST_ID.fullmatch(normalized) is None:
        raise PaperStoryError(f"{label} is unsafe")
    return normalized


def _parse_request_id(stdout: str) -> str:
    """Match dispatch_compute's NQSV-first, single-token-fallback parser."""
    if type(stdout) is not str:
        raise PaperStoryError("qsub stdout is not a string")
    match = _REQUEST_RE.search(stdout)
    if match is not None:
        return match.group(1).rstrip(".")
    tokens = stdout.split()
    if len(tokens) == 1:
        return tokens[0].rstrip(".")
    raise PaperStoryError("qsub stdout does not contain one request ID")


def _qstat_mentions_request(stdout: str, request_id: str) -> bool:
    """Match dispatch_compute's structured request-ID visibility check."""
    expected = _validated_request_id(request_id, "qstat request ID")
    for observed in _QSTAT_REQUEST_ID_RE.findall(stdout):
        try:
            if _validated_request_id(observed, "observed qstat request ID") == expected:
                return True
        except PaperStoryError:
            continue
    return False


def _is_target_nqsv_disappearance(stdout: str, request_id: str) -> bool:
    """Require the one-line NQSV disappearance signature for the target."""
    if type(stdout) is not str:
        return False
    disappeared = _NQSV_DISAPPEARED_RE.fullmatch(stdout)
    if disappeared is None:
        return False
    try:
        return _validated_request_id(
            disappeared.group(1), "disappeared qstat request ID",
        ) == _validated_request_id(request_id, "completion request ID")
    except PaperStoryError:
        return False


def _parse_qstat_terminal(stdout: str) -> tuple[str, str, int]:
    """Parse the request ID, state, and exit status from terminal qstat output."""
    if type(stdout) is not str:
        raise PaperStoryError("qstat stdout is not a string")
    request_matches = _QSTAT_REQUEST_ID_RE.findall(stdout)
    state_matches = _QSTAT_STATE_RE.findall(stdout)
    exit_matches = _QSTAT_EXIT_STATUS_RE.findall(stdout)
    if (
        len(request_matches) != 1
        or len(state_matches) != 1
        or len(exit_matches) != 1
    ):
        raise PaperStoryError("visible scheduler request is not terminal")
    return (
        _validated_request_id(request_matches[0], "observed qstat request ID"),
        state_matches[0],
        int(exit_matches[0]),
    )


def _validate_reservation_binding_document(value: object) -> dict[str, object]:
    if type(value) is not dict or set(value) != set(RESERVATION_BINDING_KEYS):
        raise PaperStoryError("reservation binding shape differs")
    try:
        binding = ReservationBinding(**value)
    except (ReservationError, TypeError) as exc:
        raise PaperStoryError(f"reservation binding is invalid: {exc}") from exc
    if _PBS_JOBID.fullmatch(binding.job_id) is None:
        raise PaperStoryError("reservation job ID is unsafe")
    return {
        field: getattr(binding, field)
        for field in RESERVATION_BINDING_KEYS
    }


def _validate_v3_accounting(value: object) -> dict[str, object]:
    """Validate one shell/reaped-descendant accounting window."""
    if type(value) is not dict or set(value) != V3_ACCOUNTING_KEYS:
        raise PaperStoryError("job accounting shape differs")
    if value.get("method") != "bash-times-delta-reaped-descendants/v1":
        raise PaperStoryError("job accounting method differs")
    numeric = (
        "started_epoch_s",
        "ended_epoch_s",
        "started_monotonic_s",
        "ended_monotonic_s",
        "elapsed_s",
        "shell_user_s",
        "shell_system_s",
        "reaped_descendants_user_s",
        "reaped_descendants_system_s",
        "cpu_total_s",
    )
    if any(not _finite_number(value.get(key)) for key in numeric):
        raise PaperStoryError("job accounting contains a non-finite value")
    if any(float(value[key]) < 0.0 for key in numeric):
        raise PaperStoryError("job accounting contains a negative value")
    if (
        float(value["ended_epoch_s"]) < float(value["started_epoch_s"])
        or float(value["ended_monotonic_s"])
        < float(value["started_monotonic_s"])
        or not math.isclose(
            float(value["elapsed_s"]),
            float(value["ended_monotonic_s"])
            - float(value["started_monotonic_s"]),
            rel_tol=0.0,
            abs_tol=1e-6,
        )
    ):
        raise PaperStoryError("job accounting elapsed window differs")
    components = sum(float(value[key]) for key in (
        "shell_user_s",
        "shell_system_s",
        "reaped_descendants_user_s",
        "reaped_descendants_system_s",
    ))
    if not math.isclose(
        float(value["cpu_total_s"]), components, rel_tol=0.0, abs_tol=1e-6,
    ):
        raise PaperStoryError("job accounting CPU total differs")
    if (
        type(value.get("times_baseline_raw")) is not str
        or not value["times_baseline_raw"]
        or type(value.get("times_final_raw")) is not str
        or not value["times_final_raw"]
    ):
        raise PaperStoryError("job accounting times snapshots are missing")
    duration_pattern = re.compile(r"([0-9]+)m([0-9]+(?:\.[0-9]+)?)s")

    def parse_snapshot(raw: str) -> list[float]:
        matches = duration_pattern.findall(raw)
        if len(matches) != 4:
            raise PaperStoryError("job accounting times snapshot shape differs")
        return [
            float(minutes) * 60.0 + float(seconds)
            for minutes, seconds in matches
        ]

    baseline = parse_snapshot(value["times_baseline_raw"])
    final = parse_snapshot(value["times_final_raw"])
    deltas = [end - start for start, end in zip(baseline, final)]
    recorded = [
        float(value[key]) for key in (
            "shell_user_s", "shell_system_s", "reaped_descendants_user_s",
            "reaped_descendants_system_s",
        )
    ]
    if any(delta < -1e-9 for delta in deltas) or any(
        not math.isclose(delta, observed, rel_tol=0.0, abs_tol=1e-6)
        for delta, observed in zip(deltas, recorded)
    ):
        raise PaperStoryError("job accounting is not the baseline times delta")
    if value.get("unreaped_descendants") != []:
        raise PaperStoryError("job accounting has unreaped descendants")
    return dict(value)


def _validate_v3_job_executions(
    value: object,
    *,
    attempt: Path | None = None,
) -> list[dict[str, object]]:
    """Bind the exact workload triple to distinct normalized scheduler jobs."""
    if type(value) is not list or len(value) != len(WORKLOAD_ORDER):
        raise PaperStoryError("job executions are not the exact workload triple")
    validated: list[dict[str, object]] = []
    normalized_request_ids: list[str] = []
    for ordinal, (raw, workload) in enumerate(zip(value, WORKLOAD_ORDER)):
        if type(raw) is not dict or set(raw) != {
            "workload", "ordinal", "request_id", "reservation_binding",
            "accounting",
        }:
            raise PaperStoryError("job execution shape differs")
        if raw.get("workload") != workload or raw.get("ordinal") != ordinal:
            raise PaperStoryError("job execution workload ordinal differs")
        request_id = _validated_request_id(
            raw.get("request_id"), f"{workload} request ID",
        )
        reservation = _validate_reservation_binding_document(
            raw.get("reservation_binding")
        )
        if _validated_request_id(
            reservation["job_id"], f"{workload} reservation job ID",
        ) != request_id:
            raise PaperStoryError("job execution reservation request ID differs")
        if attempt is not None and reservation["nonce"] != (
            f"{attempt.name}.{workload}"
        ):
            raise PaperStoryError("job execution reservation nonce differs")
        accounting = _validate_v3_accounting(raw.get("accounting"))
        normalized_request_ids.append(request_id)
        validated.append({
            "workload": workload,
            "ordinal": ordinal,
            "request_id": raw["request_id"],
            "reservation_binding": reservation,
            "accounting": accounting,
        })
    # MF1: uniqueness is deliberately checked only after NQSV normalization.
    if len(set(normalized_request_ids)) != len(WORKLOAD_ORDER):
        raise PaperStoryError("normalized request IDs are not a unique triple")
    return validated


def _reservation_binding_from_environment(
    environ: Mapping[str, str],
) -> dict[str, object]:
    try:
        binding = read_binding(environ)
    except ReservationError as exc:
        raise PaperStoryError(f"reservation environment is invalid: {exc}") from exc
    return _validate_reservation_binding_document({
        field: getattr(binding, field)
        for field in RESERVATION_BINDING_KEYS
    })


def _read_bytes_once(path: Path, *, missing_ok: bool = False) -> bytes | None:
    """Read one regular-file snapshot without following a final symlink."""
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except FileNotFoundError:
        if missing_ok:
            return None
        raise PaperStoryError(f"required snapshot file is missing: {path}") from None
    except OSError as exc:
        raise PaperStoryError(f"snapshot open failed: {path}: {exc}") from exc
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise PaperStoryError(f"snapshot source is not a regular file: {path}")
        remaining = before.st_size
        blocks = []
        while remaining:
            block = os.read(fd, min(1024 * 1024, remaining))
            if not block:
                raise PaperStoryError(f"snapshot source shortened while reading: {path}")
            blocks.append(block)
            remaining -= len(block)
        after = os.fstat(fd)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise PaperStoryError(f"snapshot source changed while reading: {path}")
        return b"".join(blocks)
    finally:
        os.close(fd)


def _exclusive_write_bytes(path: Path, raw: bytes) -> tuple[int, int]:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags, 0o600)
    except OSError as exc:
        raise PaperStoryError(f"create-only write refused: {path}: {exc}") from exc
    try:
        created = os.fstat(fd)
        view = memoryview(raw)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
    return created.st_dev, created.st_ino


def _exclusive_write(path: Path, value: object) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags, 0o600)
    except OSError as exc:
        raise PaperStoryError(f"create-only write refused: {path}: {exc}") from exc
    try:
        raw = _canonical_json_bytes(value)
        with os.fdopen(fd, "wb") as stream:
            fd = -1
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        if fd >= 0:
            os.close(fd)


def _receipt_staging_path(
    path: Path,
    *,
    receipt_kind: Literal["submission", "completion"],
) -> Path:
    """Derive a kind-separated PID staging basename within the final-name budget."""
    marker = receipt_kind[0]
    suffix = f".{marker}-{os.getpid():x}"
    basename_budget = len(os.fsencode(path.name))
    stem_budget = basename_budget - len(os.fsencode(f".{suffix}"))
    stem = path.name
    while stem and len(os.fsencode(stem)) > stem_budget:
        stem = stem[:-1]
    if not stem:
        raise PaperStoryError("receipt basename cannot fit staging name")
    return path.parent / f".{stem}{suffix}"


def _remove_receipt_staging(
    staging: Path,
    identity: tuple[int, int],
    *,
    destination: Path,
    published: bool,
) -> None:
    if published:
        try:
            destination_info = destination.lstat()
        except FileNotFoundError:
            raise PaperStoryError(
                "published receipt destination is missing during staging cleanup"
            ) from None
        except OSError as exc:
            raise PaperStoryError(
                f"published receipt destination cleanup stat failed: {exc}"
            ) from exc
        if (
            not stat.S_ISREG(destination_info.st_mode)
            or (destination_info.st_dev, destination_info.st_ino) != identity
        ):
            raise PaperStoryError(
                "published receipt destination identity differs during staging cleanup"
            )
    try:
        info = staging.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise PaperStoryError(
            f"receipt staging cleanup stat failed: {exc}"
        ) from exc
    if (
        not stat.S_ISREG(info.st_mode)
        or (info.st_dev, info.st_ino) != identity
    ):
        raise PaperStoryError("receipt staging cleanup identity differs")
    try:
        os.unlink(staging)
        _fsync_directory(staging.parent)
    except OSError as exc:
        raise PaperStoryError(
            f"receipt staging cleanup failed: {exc}"
        ) from exc


def _publish_receipt(
    path: Path,
    value: object,
    *,
    receipt_kind: Literal["submission", "completion"],
) -> None:
    raw = _canonical_json_bytes(value)
    staging = _receipt_staging_path(path, receipt_kind=receipt_kind)
    staging_identity = _exclusive_write_bytes(staging, raw)
    published = False
    try:
        try:
            os.link(staging, path, follow_symlinks=False)
        except FileExistsError as exc:
            raise PaperStoryError(
                f"no-replace {receipt_kind} receipt publish failed: {exc.strerror}"
            ) from exc
        except OSError as exc:
            raise PaperStoryError(
                f"no-replace {receipt_kind} receipt publish failed: {exc.strerror}"
            ) from exc
        published = True
        _fsync_directory(path.parent)
    finally:
        try:
            _remove_receipt_staging(
                staging,
                staging_identity,
                destination=path,
                published=published,
            )
        except PaperStoryError as exc:
            if published:
                raise _PublishedReceiptCleanupError(
                    f"receipt is already published; {exc}"
                ) from exc
            raise


def _publish_submission_receipt(path: Path, value: object) -> None:
    _publish_receipt(path, value, receipt_kind="submission")


def _publish_completion_receipt(path: Path, value: object) -> None:
    _publish_receipt(path, value, receipt_kind="completion")


def _exclusive_write_text(path: Path, value: str) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags, 0o600)
    except OSError as exc:
        raise PaperStoryError(f"create-only write refused: {path}: {exc}") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            fd = -1
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        if fd >= 0:
            os.close(fd)


def _json_safe(value: Any) -> Any:
    if type(value) is int:
        try:
            float(value)
        except OverflowError:
            return {
                "integer_out_of_finite_range": {
                    "sign": -1 if value < 0 else 1,
                    "bit_length": value.bit_length(),
                }
            }
    if isinstance(value, float) and not math.isfinite(value):
        if math.isnan(value):
            label = "nan"
        elif value > 0:
            label = "+inf"
        else:
            label = "-inf"
        return {"nonfinite_number": label}
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _policy_schema(policy: Mapping[str, object]) -> str:
    schema = policy.get("schema_version")
    if schema not in {POLICY_SCHEMA_V2, POLICY_SCHEMA_V3}:
        raise PaperStoryError("policy schema version is unknown")
    return str(schema)


def _policy_identity(study_id: str) -> tuple[Path, str, str | None]:
    if study_id == STUDY_ID:
        return POLICY_PATH, POLICY_RELATIVE_PATH, POLICY_SHA256
    if study_id == V3_PILOT_STUDY_ID:
        return (
            V3_PILOT_POLICY_PATH,
            V3_PILOT_POLICY_RELATIVE_PATH,
            V3_PILOT_POLICY_SHA256,
        )
    if study_id == V3_SIZED_STUDY_ID:
        return (
            V3_SIZED_POLICY_PATH,
            V3_SIZED_POLICY_RELATIVE_PATH,
            V3_SIZED_POLICY_SHA256,
        )
    raise PaperStoryError("study ID is not registered")


def _policy_study_id(policy: Mapping[str, object]) -> str:
    study_id = policy.get("study_id")
    if type(study_id) is not str:
        raise PaperStoryError("policy study ID is missing")
    _policy_identity(study_id)
    return study_id


def _policy_path(policy: Mapping[str, object]) -> Path:
    return _policy_identity(_policy_study_id(policy))[0]


def _policy_relative_path(policy: Mapping[str, object]) -> str:
    return _policy_identity(_policy_study_id(policy))[1]


def _pairing_design(policy: Mapping[str, object]) -> str:
    pairing = policy.get("pairing")
    design = pairing.get("design") if type(pairing) is dict else None
    if type(design) is not str:
        raise PaperStoryError("policy pairing design is missing")
    return design


def _campaign_schema(policy: Mapping[str, object]) -> str:
    return (
        "paper-story-a1-paired-campaign/v1"
        if _policy_schema(policy) == POLICY_SCHEMA_V2
        else "paper-story-a1-paired-campaign/v2"
    )


def _campaign_ccbench_commit(policy: Mapping[str, object]) -> str:
    """Keep legacy identity short while binding v3 to its canonical full OID."""
    if _policy_schema(policy) == POLICY_SCHEMA_V2:
        return pin.CURRENT_PIN
    acceptance = policy.get("ccbench_acceptance")
    canonical_pin = (
        acceptance.get("canonical_pin")
        if type(acceptance) is dict else None
    )
    if (
        type(canonical_pin) is not str
        or re.fullmatch(r"[0-9a-f]{40}", canonical_pin) is None
    ):
        raise PaperStoryError("v3 canonical CCBench pin differs")
    return canonical_pin


def _workload_plan(
    policy: Mapping[str, object], workload_name: str,
) -> Mapping[str, object]:
    workloads = policy.get("workloads")
    if type(workloads) is not list:
        raise PaperStoryError("policy workloads must be a list")
    matches = [
        item for item in workloads
        if type(item) is dict and item.get("name") == workload_name
    ]
    if len(matches) != 1:
        raise PaperStoryError(
            f"policy must contain exactly one workload plan: {workload_name}"
        )
    return matches[0]


def _workload_arms(
    policy: Mapping[str, object], workload_name: str,
) -> list[Mapping[str, object]]:
    if _policy_schema(policy) == POLICY_SCHEMA_V2:
        arms = policy.get("arms")
    else:
        arms = _workload_plan(policy, workload_name).get("arms")
    if type(arms) is not list or any(type(arm) is not dict for arm in arms):
        raise PaperStoryError(f"policy arms are invalid: {workload_name}")
    return arms


def _workload_arm_order(
    policy: Mapping[str, object], workload_name: str,
) -> tuple[str, str]:
    arms = _workload_arms(policy, workload_name)
    names = tuple(arm.get("name") for arm in arms)
    if len(names) != 2 or any(type(name) is not str for name in names):
        raise PaperStoryError(f"policy arm names are invalid: {workload_name}")
    return names


def _workload_arm_by_role(
    policy: Mapping[str, object], workload_name: str, role: str,
) -> Mapping[str, object]:
    if _policy_schema(policy) == POLICY_SCHEMA_V2:
        legacy_name = {"baseline": "adaptive", "variant": "static10"}.get(role)
        matches = [
            arm for arm in _workload_arms(policy, workload_name)
            if arm.get("name") == legacy_name
        ]
    else:
        matches = [
            arm for arm in _workload_arms(policy, workload_name)
            if arm.get("role") == role
        ]
    if len(matches) != 1:
        raise PaperStoryError(
            f"policy must contain exactly one {role} arm: {workload_name}"
        )
    return matches[0]


def _expected_reps(policy: Mapping[str, object], workload_name: str) -> int:
    reps = _workload_plan(policy, workload_name).get("reps")
    if type(reps) is not int or reps < 2:
        raise PaperStoryError(f"workload reps is invalid: {workload_name}")
    return reps


def _pair_indices(policy: Mapping[str, object], workload_name: str) -> range:
    workload = _workload_plan(policy, workload_name)
    rule = workload.get("pair_indices")
    if type(rule) is not dict or set(rule) != {
        "start_inclusive", "stop_exclusive",
    }:
        raise PaperStoryError(f"pair index rule is invalid: {workload_name}")
    start = rule.get("start_inclusive")
    stop = rule.get("stop_exclusive")
    reps = _expected_reps(policy, workload_name)
    if type(start) is not int or start != 0 or type(stop) is not int or stop != reps:
        raise PaperStoryError(f"pair index rule differs from reps: {workload_name}")
    return range(start, stop)


def _campaign_scale(
    policy: Mapping[str, object], workload_name: str,
) -> dict[str, object]:
    scale = policy.get("scale")
    if type(scale) is not dict:
        raise PaperStoryError("policy scale must be an object")
    return {**scale, "reps": _expected_reps(policy, workload_name)}


def _validate_policy_v2_semantics(policy: object) -> dict:
    if type(policy) is not dict:
        raise PaperStoryError("policy must be an exact JSON object")
    if policy.get("schema_version") != POLICY_SCHEMA_V2:
        raise PaperStoryError("policy schema version differs")
    if policy.get("study_id") != STUDY_ID:
        raise PaperStoryError("policy study ID differs")
    if policy.get("arm_order") != list(ARM_ORDER):
        raise PaperStoryError("policy arm order differs")
    workloads = policy.get("workloads")
    if (
        type(workloads) is not list
        or [item.get("name") for item in workloads if type(item) is dict]
        != list(WORKLOAD_ORDER)
    ):
        raise PaperStoryError("policy workload order or existence differs")
    for workload_name, expected in WORKLOAD_DESIGNS.items():
        workload = _workload_plan(policy, workload_name)
        reps = workload.get("reps")
        df = workload.get("df")
        k = workload.get("k")
        sigma = workload.get("planned_sigma_tps")
        if type(reps) is not int or reps < 2:
            raise PaperStoryError(f"workload reps is invalid: {workload_name}")
        if type(df) is not int or df != reps - 1:
            raise PaperStoryError(f"workload df differs from reps: {workload_name}")
        if (
            not _finite_number(k)
            or not _finite_number(sigma)
            or float(k) <= 0
            or float(sigma) <= 0
        ):
            raise PaperStoryError(f"workload statistical plan is invalid: {workload_name}")
        if any(workload.get(key) != value for key, value in expected.items()):
            raise PaperStoryError(
                f"workload reps, k, or sigma differs from frozen design: {workload_name}"
            )
        _pair_indices(policy, workload_name)
    statistics_policy = policy.get("statistics")
    if type(statistics_policy) is not dict:
        raise PaperStoryError("policy statistics must be an object")
    floor = statistics_policy.get("floor")
    if (
        type(floor) is not dict
        or floor.get("floor_fraction") != 0.030
        or floor.get("boundary")
        != "B = floor_fraction * current_run_adaptive_mean_tps"
        or floor.get("past_run_absolute_tps_prohibited") is not True
    ):
        raise PaperStoryError("policy adaptive-relative floor differs")
    if statistics_policy.get("classification_rules") != CLASSIFICATION_RULES:
        raise PaperStoryError("policy classification priority differs")
    variance = statistics_policy.get("variance_plan_breach")
    if (
        type(variance) is not dict
        or variance.get("predicate")
        != "sample_sd > workload.planned_sigma_tps"
        or variance.get("overrides_classification") is not False
    ):
        raise PaperStoryError("policy variance-plan breach rule differs")
    rerun = policy.get("rerun")
    if (
        type(rerun) is not dict
        or rerun.get("closed_enumeration") is not True
        or rerun.get("allowed_reasons") != RERUN_REASONS
    ):
        raise PaperStoryError("policy rerun reason enumeration differs")
    execution = policy.get("execution")
    if (
        type(execution) is not dict
        or execution.get("bench_max_rounds") != 3
        or execution.get("materialization_relative_path")
        != MATERIALIZATION_RELATIVE_PATH.as_posix()
    ):
        raise PaperStoryError("policy materialization destination differs")
    preregistration = policy.get("preregistration")
    if preregistration != {
        "path": PREREGISTRATION_RELATIVE_PATH,
        "sha256": PREREGISTRATION_SHA256,
    }:
        raise PaperStoryError("policy preregistration binding differs")
    return policy


def _validate_v3_fraction(
    value: object, *, numerator: int, denominator: int, label: str,
) -> None:
    if value != {"denominator": denominator, "numerator": numerator}:
        raise PaperStoryError(f"v3 policy {label} differs")


def _positive_decimal(value: object, label: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise PaperStoryError(f"{label} is not a positive decimal")
    try:
        decimal = Decimal(str(value))
    except InvalidOperation as exc:
        raise PaperStoryError(f"{label} is not a positive decimal") from exc
    if not decimal.is_finite() or decimal <= 0:
        raise PaperStoryError(f"{label} is not a positive decimal")
    return decimal


def _read_sized_input_binding(
    label: str, binding: Mapping[str, object],
) -> tuple[Path, bytes]:
    relative = binding.get("path")
    expected_sha = binding.get("sha256")
    if (
        type(relative) is not str
        or not relative
        or Path(relative).is_absolute()
        or Path(relative).as_posix() != relative
        or any(part in {"", ".", ".."} for part in Path(relative).parts)
        or type(expected_sha) is not str
        or _FULL_SHA256.fullmatch(expected_sha) is None
    ):
        raise PaperStoryError(f"v3 sized {label} binding differs")
    try:
        repo_root = _repo_root().resolve(strict=True)
        path = (repo_root / relative).resolve(strict=True)
    except OSError as exc:
        raise PaperStoryError(f"v3 sized {label} input is unavailable") from exc
    if not _is_within(path, repo_root):
        raise PaperStoryError(f"v3 sized {label} path escaped repository")
    raw = _read_bytes_once(path)
    if raw is None or not hmac.compare_digest(_sha256_bytes(raw), expected_sha):
        raise PaperStoryError(f"v3 sized {label} hash differs")
    return path, raw


def _validate_v3_sized_certificate(
    policy: Mapping[str, object], bindings: Mapping[str, object],
) -> None:
    _pilot_path, pilot_raw = _read_sized_input_binding(
        "pilot_result", bindings["pilot_result"],
    )
    _certificate_path, certificate_raw = _read_sized_input_binding(
        "sizing_certificate", bindings["sizing_certificate"],
    )
    pilot = _decode_json_bytes(pilot_raw, "v3 sized pilot result")
    certificate = _decode_json_bytes(
        certificate_raw, "v3 sized sizing certificate",
    )
    try:
        canonical_certificate = (
            json.dumps(
                certificate,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise PaperStoryError("v3 sized sizing certificate is not canonical") from exc
    if certificate_raw != canonical_certificate:
        raise PaperStoryError("v3 sized sizing certificate is not canonical")
    certificate_pilot = certificate.get("inputs")
    certificate_pilot = (
        certificate_pilot.get("pilot")
        if type(certificate_pilot) is dict else None
    )
    if (
        pilot.get("schema_version") != BALANCED_SIZING_PILOT_SCHEMA
        or pilot.get("study_id") != V3_PILOT_STUDY_ID
        or pilot.get("final_estimate_eligible") is not False
        or certificate.get("schema_version")
        != BALANCED_SIZING_CERTIFICATE_SCHEMA
        or certificate.get("status") != "selected"
        or type(certificate_pilot) is not dict
        or certificate_pilot.get("path")
        != bindings["pilot_result"].get("path")
        or certificate_pilot.get("sha256")
        != bindings["pilot_result"].get("sha256")
    ):
        raise PaperStoryError("v3 sized certificate input binding differs")
    certificate_workloads = certificate.get("workloads")
    if (
        type(certificate_workloads) is not list
        or [
            item.get("workload") for item in certificate_workloads
            if type(item) is dict
        ] != list(WORKLOAD_ORDER)
    ):
        raise PaperStoryError("v3 sized certificate workload set differs")
    for name, certificate_workload in zip(
        WORKLOAD_ORDER, certificate_workloads,
    ):
        if type(certificate_workload) is not dict:
            raise PaperStoryError(
                f"v3 sized certificate workload differs: {name}"
            )
        selected = certificate_workload.get("selected")
        policy_workload = _workload_plan(policy, name)
        if (
            certificate_workload.get("status") != "selected"
            or type(selected) is not dict
            or type(selected.get("n")) is not int
            or isinstance(selected.get("n"), bool)
            or type(selected.get("df")) is not int
            or isinstance(selected.get("df"), bool)
            or policy_workload.get("reps") != selected.get("n")
            or policy_workload.get("df") != selected.get("df")
        ):
            raise PaperStoryError(
                f"v3 sized n or df differs from certificate: {name}"
            )
        if _positive_decimal(
            policy_workload.get("k"), f"v3 sized policy k: {name}",
        ) != _positive_decimal(
            selected.get("t_critical"),
            f"v3 sized certificate t critical: {name}",
        ):
            raise PaperStoryError(
                f"v3 sized k differs from certificate: {name}"
            )
        if _positive_decimal(
            policy_workload.get("planned_sigma_tps"),
            f"v3 sized policy planned sigma: {name}",
        ) != _positive_decimal(
            certificate_workload.get("planned_sigma_tps"),
            f"v3 sized certificate planned sigma: {name}",
        ):
            raise PaperStoryError(
                f"v3 sized planned sigma differs from certificate: {name}"
            )

    certificate_policy = certificate.get("policy")
    if type(certificate_policy) is not dict:
        raise PaperStoryError("v3 sized certificate registered policy differs")
    for section_name, field, expected in V3_SIZED_CERTIFICATE_REGISTERED_PARAMETERS:
        section = certificate_policy.get(section_name)
        if type(section) is not dict:
            raise PaperStoryError(
                f"v3 sized certificate registered policy differs: {section_name}"
            )
        observed = section.get(field)
        if type(observed) is not type(expected) or observed != expected:
            raise PaperStoryError(
                "v3 sized certificate registered policy differs: "
                f"{section_name}.{field}"
            )


def _validate_policy_v3_semantics(policy: object) -> dict:
    if type(policy) is not dict:
        raise PaperStoryError("policy must be an exact JSON object")
    if policy.get("schema_version") != POLICY_SCHEMA_V3:
        raise PaperStoryError("policy schema version differs")
    if "arms" in policy or "arm_order" in policy:
        raise PaperStoryError("v3 policy prohibits top-level arms and arm_order")
    study_id = policy.get("study_id")
    if study_id not in {V3_PILOT_STUDY_ID, V3_SIZED_STUDY_ID}:
        raise PaperStoryError("v3 policy study ID differs")
    is_pilot = study_id == V3_PILOT_STUDY_ID
    if policy.get("campaign_schema") != "paper-story-a1-paired-campaign/v2":
        raise PaperStoryError("v3 campaign schema differs")
    if policy.get("final_estimate_eligible") is (not is_pilot):
        pass
    else:
        raise PaperStoryError("v3 final estimate eligibility differs")

    workloads = policy.get("workloads")
    if (
        type(workloads) is not list
        or [item.get("name") for item in workloads if type(item) is dict]
        != list(WORKLOAD_ORDER)
    ):
        raise PaperStoryError("v3 workload order or existence differs")
    expected_variants = {
        "write-heavy": ("fixed10", 10, "5"),
        "balanced": ("fixed5", 5, "50"),
        "read-heavy": ("fixed2", 2, "95"),
    }
    common_variant_flags = {
        "BACK_OFF": 1,
        "NO_WAIT_LOCKING_IN_VALIDATION": 1,
        "NO_WAIT_OF_TICTOC": 0,
        "WAL": 0,
    }
    baseline_flags = {
        "BACKOFF_FIXED": -1,
        "BACK_OFF": 0,
        "NO_WAIT_LOCKING_IN_VALIDATION": 1,
        "NO_WAIT_OF_TICTOC": 0,
        "WAL": 0,
    }
    for workload_name in WORKLOAD_ORDER:
        workload = _workload_plan(policy, workload_name)
        variant_name, fixed, rratio = expected_variants[workload_name]
        arms = workload.get("arms")
        if type(arms) is not list or len(arms) != 2:
            raise PaperStoryError(
                f"v3 workload must contain exactly two arms: {workload_name}"
            )
        expected_arms = [
            {
                "contrast": "minuend",
                "flags": {"BACKOFF_FIXED": fixed, **common_variant_flags},
                "name": variant_name,
                "protocol": "silo",
                "role": "variant",
            },
            {
                "contrast": "subtrahend",
                "flags": baseline_flags,
                "name": "no-backoff",
                "protocol": "silo",
                "role": "baseline",
            },
        ]
        if arms != expected_arms:
            raise PaperStoryError(f"v3 workload arms differ: {workload_name}")
        reps = workload.get("reps")
        df = workload.get("df")
        if (
            type(reps) is not int
            or type(df) is not int
            or df != reps - 1
            or workload.get("ycsb_rratio") != rratio
            or type(workload.get("schedule_root_seed")) is not str
            or _FULL_SHA256.fullmatch(workload["schedule_root_seed"]) is None
        ):
            raise PaperStoryError(f"v3 workload plan differs: {workload_name}")
        if is_pilot:
            if reps != 60 or set(workload) != {
                "arms", "df", "name", "pair_indices", "reps",
                "schedule_root_seed", "ycsb_rratio",
            }:
                raise PaperStoryError(f"v3 pilot workload shape differs: {workload_name}")
        else:
            if reps < 30 or reps % 10 != 0:
                raise PaperStoryError(
                    f"v3 sized workload plan differs: {workload_name}"
                )
            for field in ("k", "planned_sigma_tps"):
                value = workload.get(field)
                label = f"v3 sized workload {field}: {workload_name}"
                _positive_decimal(value, label)
                try:
                    converted = float(value)
                except (TypeError, ValueError, OverflowError) as exc:
                    raise PaperStoryError(
                        f"{label} is not a positive finite float"
                    ) from exc
                if not math.isfinite(converted) or converted <= 0:
                    raise PaperStoryError(
                        f"{label} is not a positive finite float"
                    )
        _pair_indices(policy, workload_name)

    pairing = policy.get("pairing")
    if type(pairing) is not dict or set(pairing) != {
        "arm_block_reps", "contrast", "design", "estimand", "group_pairs",
        "physical_orders", "schedule_receipt_schema", "seed",
    }:
        raise PaperStoryError("v3 pairing shape differs")
    if any((
        pairing.get("arm_block_reps") != 5,
        pairing.get("contrast") != "variant-minus-baseline",
        pairing.get("design") != V3_PAIRING_DESIGN,
        pairing.get("estimand")
        != "arithmetic mean of paired differences under the balanced five-rep schedule",
        pairing.get("group_pairs") != 10,
        pairing.get("physical_orders") != {
            "bit_0": "A^5 B^5 B^5 A^5",
            "bit_1": "B^5 A^5 A^5 B^5",
        },
        pairing.get("schedule_receipt_schema")
        != "paper-story-a1-balanced-schedule-receipt/v1",
    )):
        raise PaperStoryError("v3 pairing design differs")
    seed = pairing.get("seed")
    redraw = seed.get("all_identical_redraw") if type(seed) is dict else None
    if (
        type(seed) is not dict
        or seed.get("group_preimage")
        != "a1-balanced5/v1|workload=<name>|group=<zero-based decimal>"
        or seed.get("group_preimage_prohibits") != ["study ID", "date"]
        or seed.get("digest") != "SHA-256"
        or seed.get("order_bit")
        != "least-significant bit of the SHA-256 digest"
        or seed.get("concatenation")
        != "root seed ASCII bytes followed immediately by group preimage UTF-8 bytes"
        or seed.get("root_seed_encoding")
        != "64 lowercase hexadecimal ASCII characters"
        or type(redraw) is not dict
        or redraw.get("counter_initial") != 0
        or redraw.get("counter_limit_exclusive") != 16
        or redraw.get("effective_root_seed_preimage")
        != "<64-lowercase-hex>|counter=<zero-based decimal>"
        or redraw.get("predicate")
        != "all workload group order bits are 0 or all workload group order bits are 1"
        or redraw.get("rule")
        != "increment the fixed counter and redraw the entire workload bit sequence before observing or selecting any realized schedule"
        or redraw.get("failure")
        != "fail-closed when counter reaches 16 without a non-identical bit sequence"
    ):
        raise PaperStoryError("v3 seed or all-identical redraw rule differs")

    execution = policy.get("execution")
    if (
        type(execution) is not dict
        or execution.get("bench_max_rounds") != 1
        or execution.get("schedule_round_definition")
        != "one complete workload schedule"
        or execution.get("bench_lock_acquisitions_per_workload") != 1
        or execution.get("settle") != "once-at-workload-schedule-start"
        or execution.get("competing_tenant_probe")
        != "before-each-five-rep-arm-block-fail-closed-workload-abort"
    ):
        raise PaperStoryError("v3 execution schedule differs")
    quality = policy.get("quality")
    if (
        type(quality) is not dict
        or quality.get("aggregate_cv")
        != "sample standard deviation of all arm rep TPS divided by arithmetic mean of all arm rep TPS"
        or quality.get("block_cv")
        != "diagnostic-only and never substituted or averaged for aggregate CV"
        or quality.get("unstable") != "aggregate_cv > 0.05"
        or quality.get("throughput_absent")
        != "bench-no-throughput and abort whole workload"
        or quality.get("undefined_cv")
        != "bench-cv-undefined and abort whole workload"
        or quality.get("unsettled") != "bench-unsettled and abort whole workload"
    ):
        raise PaperStoryError("v3 quality gate differs")
    if policy.get("invalid_rules") != V3_INVALID_RULES:
        raise PaperStoryError("v3 invalid rules differ")
    if policy.get("rerun") != {
        "allowed_reasons": RERUN_REASONS,
        "closed_enumeration": True,
        "performance_output_may_not_authorize_rerun": True,
    }:
        raise PaperStoryError("v3 rerun rules differ")

    sizing = policy.get("sizing")
    if type(sizing) is not dict:
        raise PaperStoryError("v3 sizing policy is missing")
    _validate_v3_fraction(
        sizing.get("alpha_c"), numerator=1, denominator=20, label="alpha_c",
    )
    _validate_v3_fraction(
        sizing.get("family_alpha"), numerator=1, denominator=20,
        label="family alpha",
    )
    _validate_v3_fraction(
        sizing.get("arm_failure_probability"), numerator=1, denominator=120,
        label="arm failure probability",
    )
    _validate_v3_fraction(
        sizing.get("floor_fraction"), numerator=3, denominator=100,
        label="floor fraction",
    )
    _validate_v3_fraction(
        sizing.get("required_success_probability"), numerator=4,
        denominator=5, label="required success probability",
    )
    if any((
        sizing.get("sigma_pair")
        != "c(one-sided, alpha_c, df = 59) * sd(60 paired differences)",
        sizing.get("sigma_block")
        != "sqrt(5) * c(one-sided, alpha_c, df = 11) * sd(12 five-pair block means)",
        sizing.get("planned_sigma") != "max(sigma_pair, sigma_block)",
        sizing.get("sqrt_block_size") != "sqrt(5)",
        sizing.get("upper_factor")
        != "c(one-sided, alpha_c, df) = sqrt(df / chi-square-quantile(alpha_c, df))",
        sizing.get("block_mean_count") != 12,
        sizing.get("pilot_pairs_per_workload") != 60,
        sizing.get("pilot_pair_blocks") != {
            "baseline_first": 6,
            "pairs_per_block": 5,
            "total": 12,
            "variant_first": 6,
        },
        sizing.get("n_grid") != {
            "effective_minimum": 30,
            "maximum": 4096,
            "maximum_candidate": 4090,
            "nominal_minimum": 28,
            "rule": "evaluate operating characteristics only at the actual candidate n",
            "step": 10,
        },
        sizing.get("conditions") != [
            {"delta_from_baseline_mean": {"denominator": 1, "numerator": 0}, "name": "zero"},
            {"delta_from_baseline_mean": {"denominator": 50, "numerator": 3}, "name": "positive-six-percent"},
            {"delta_from_baseline_mean": {"denominator": 50, "numerator": -3}, "name": "negative-six-percent"},
        ],
    )):
        raise PaperStoryError("v3 sizing formula or search grid differs")

    ccbench = policy.get("ccbench_acceptance")
    if ccbench != {
        "boundaries": V3_CCBENCH_BOUNDARIES,
        "build_preflight_required": True,
        "canonical_pin": CANONICAL_CCBENCH_OID,
        "parent_submodule_ignore_independent": True,
        "tracked_clean_required": True,
        "untracked_files_ignored": True,
    }:
        raise PaperStoryError("v3 CCBench acceptance contract differs")
    preregistration = policy.get("preregistration")
    if type(preregistration) is not dict or set(preregistration) != {"path", "sha256"}:
        raise PaperStoryError("v3 preregistration binding shape differs")
    expected_preregistration = (
        {
            "path": V3_PILOT_PREREGISTRATION_RELATIVE_PATH,
            "sha256": V3_PILOT_PREREGISTRATION_SHA256,
        }
        if is_pilot else
        {
            "path": V3_SIZED_PREREGISTRATION_RELATIVE_PATH,
            "sha256": V3_SIZED_PREREGISTRATION_SHA256,
        }
    )
    if preregistration != expected_preregistration:
        raise PaperStoryError("v3 preregistration binding differs from module pins")
    prereg_path = preregistration.get("path")
    prereg_sha = preregistration.get("sha256")
    if (prereg_path is None) != (prereg_sha is None):
        raise PaperStoryError("v3 preregistration binding is only partially frozen")
    if prereg_path is not None and (
        type(prereg_path) is not str
        or not prereg_path
        or type(prereg_sha) is not str
        or _FULL_SHA256.fullmatch(prereg_sha) is None
    ):
        raise PaperStoryError("v3 preregistration binding differs")
    if not is_pilot:
        bindings = policy.get("sizing_inputs")
        if type(bindings) is not dict or set(bindings) != {
            "pilot_result", "sizing_certificate",
        }:
            raise PaperStoryError("v3 sized policy input bindings differ")
        for label, binding in bindings.items():
            if (
                type(binding) is not dict
                or set(binding) != {"path", "sha256"}
                or type(binding.get("path")) is not str
                or type(binding.get("sha256")) is not str
                or _FULL_SHA256.fullmatch(binding["sha256"]) is None
            ):
                raise PaperStoryError(f"v3 sized {label} binding differs")
        _validate_v3_sized_certificate(policy, bindings)
    return policy


def _validate_policy_semantics(policy: object) -> dict:
    if type(policy) is not dict:
        raise PaperStoryError("policy must be an exact JSON object")
    schema = policy.get("schema_version")
    if schema == POLICY_SCHEMA_V2:
        return _validate_policy_v2_semantics(policy)
    if schema == POLICY_SCHEMA_V3:
        return _validate_policy_v3_semantics(policy)
    raise PaperStoryError("policy schema version is unknown")


def validate_policy(policy: object) -> dict:
    policy = _validate_policy_semantics(policy)
    policy_path = _policy_path(policy)
    canonical = _read_json(policy_path)
    if set(policy) != set(canonical):
        raise PaperStoryError("policy top-level key set differs")
    for key, expected in canonical.items():
        if policy.get(key) != expected:
            raise PaperStoryError(f"policy field differs: {key}")
    expected_policy_sha = _policy_identity(_policy_study_id(policy))[2]
    if (
        expected_policy_sha is not None
        and _sha256_file(policy_path) != expected_policy_sha
    ):
        raise PaperStoryError("tracked policy bytes differ from the registered hash")
    preregistration = policy.get("preregistration")
    prereg_path = preregistration.get("path")
    prereg_sha = preregistration.get("sha256")
    if prereg_path is not None and _sha256_file(
        _repo_root() / prereg_path
    ) != prereg_sha:
        raise PaperStoryError("human-readable preregistration bytes differ")
    return policy


def load_policy(study_id: str = STUDY_ID) -> tuple[dict, str]:
    policy_path, _relative, expected_sha = _policy_identity(study_id)
    if not policy_path.is_file():
        raise PaperStoryError(f"registered policy file is missing: {policy_path.name}")
    policy = validate_policy(_read_json(policy_path))
    observed_sha = _sha256_file(policy_path)
    if expected_sha is not None and observed_sha != expected_sha:
        raise PaperStoryError("tracked policy bytes differ from the registered hash")
    return policy, observed_sha


def _load_policy_for_study(study_id: str) -> tuple[dict, str]:
    """Keep the legacy no-argument loader seam while dispatching new studies."""
    return load_policy() if study_id == STUDY_ID else load_policy(study_id)


def _require_policy_ready_for_execution(policy: Mapping[str, object]) -> None:
    if _policy_schema(policy) != POLICY_SCHEMA_V3:
        return
    preregistration = policy.get("preregistration")
    if (
        type(preregistration) is not dict
        or preregistration.get("path") is None
        or preregistration.get("sha256") is None
    ):
        raise PaperStoryError(
            "v3 policy preregistration binding is not frozen by the parent"
        )


def _schedule_group_bits(
    policy: Mapping[str, object], workload_name: str,
) -> dict[str, object]:
    if _policy_schema(policy) != POLICY_SCHEMA_V3:
        raise PaperStoryError("balanced schedule is only defined for policy v3")
    workload = _workload_plan(policy, workload_name)
    reps = _expected_reps(policy, workload_name)
    if reps % 10 != 0:
        raise PaperStoryError("balanced schedule reps must be a multiple of ten")
    root_seed = workload.get("schedule_root_seed")
    if type(root_seed) is not str or _FULL_SHA256.fullmatch(root_seed) is None:
        raise PaperStoryError("balanced schedule root seed differs")
    group_count = reps // 10
    for counter in range(16):
        effective_seed = root_seed
        if counter:
            redraw_preimage = f"{root_seed}|counter={counter}"
            effective_seed = hashlib.sha256(
                redraw_preimage.encode("utf-8")
            ).hexdigest()
        preimages = [
            f"a1-balanced5/v1|workload={workload_name}|group={group}"
            for group in range(group_count)
        ]
        bits = [
            hashlib.sha256((effective_seed + preimage).encode("utf-8")).digest()[-1]
            & 1
            for preimage in preimages
        ]
        if len(set(bits)) > 1:
            return {
                "counter": counter,
                "effective_root_seed": effective_seed,
                "group_preimages": preimages,
                "order_bits": bits,
            }
    raise PaperStoryError(
        "balanced schedule redraw reached counter 16 with all-identical bits"
    )


def _balanced_schedule_plan(
    policy: Mapping[str, object], workload_name: str,
) -> dict[str, object]:
    derivation = _schedule_group_bits(policy, workload_name)
    variant = _workload_arm_by_role(policy, workload_name, "variant")["name"]
    baseline = _workload_arm_by_role(policy, workload_name, "baseline")["name"]
    blocks: list[dict[str, object]] = []
    for group, bit in enumerate(derivation["order_bits"]):
        pair_orders = (
            ((variant, baseline), (baseline, variant))
            if bit == 0 else
            ((baseline, variant), (variant, baseline))
        )
        for within_group, pair_order in enumerate(pair_orders):
            pair_block = group * 2 + within_group
            pair_start = pair_block * 5
            pair_indices = list(range(pair_start, pair_start + 5))
            for within_pair_block, arm_name in enumerate(pair_order):
                role = (
                    "variant" if arm_name == variant else "baseline"
                )
                blocks.append({
                    "arm": arm_name,
                    "block_number": len(blocks),
                    "group": group,
                    "pair_block_number": pair_block,
                    "pair_indices": pair_indices,
                    "position_in_pair_block": within_pair_block,
                    "reps": 5,
                    "role": role,
                })
    return {
        "blocks": blocks,
        "competing_tenant_probe": "before-each-block-fail-closed",
        "derivation": derivation,
        "physical_orders": policy["pairing"]["physical_orders"],
        "schedule_receipt_schema": policy["pairing"]["schedule_receipt_schema"],
        "settle": "once-before-block-zero",
    }


_BALANCED_RECEIPT_KEYS = frozenset({
    "schema_version", "pairing_design", "workload", "root_seed",
    "effective_root_seed", "seed_counter", "group_bits",
    "bench_max_rounds", "rounds", "settled", "schedule_wall_s", "arms",
    "blocks", "reps",
})
_BALANCED_RECEIPT_ARM_KEYS = frozenset({
    "variant", "rounds", "tps", "median_tps", "cv", "unstable",
    "block_cvs",
})
_BALANCED_RECEIPT_BLOCK_KEYS = frozenset({
    "arm", "group", "block", "block_in_group", "cv", "tps",
})
_BALANCED_RECEIPT_REP_KEYS = frozenset({
    "tps", "arm", "pair_index", "group", "block", "block_position",
    "started_at_ns", "ended_at_ns",
})


def _exact_receipt_int(value: object, expected: int) -> bool:
    return type(value) is int and value == expected


def _balanced_schedule_receipt_errors(
    policy: Mapping[str, object], workload_name: str, receipt: object,
    arm_results: Mapping[str, Mapping[str, object]] | None = None,
) -> list[str]:
    if type(receipt) is not dict:
        return ["schedule-receipt-missing"]
    errors: list[str] = []
    if set(receipt) != _BALANCED_RECEIPT_KEYS:
        errors.append("schedule-receipt-shape-mismatch")
    plan = _balanced_schedule_plan(policy, workload_name)
    derivation = plan["derivation"]
    workload = _workload_plan(policy, workload_name)
    if any((
        receipt.get("schema_version")
        != policy["pairing"]["schedule_receipt_schema"],
        receipt.get("pairing_design") != _pairing_design(policy),
        receipt.get("workload") != workload_name,
        receipt.get("root_seed") != workload.get("schedule_root_seed"),
        receipt.get("effective_root_seed")
        != derivation["effective_root_seed"],
        not _exact_receipt_int(
            receipt.get("seed_counter"), derivation["counter"],
        ),
        (
            type(receipt.get("group_bits")) is not list
            or any(type(bit) is not int for bit in receipt["group_bits"])
            or receipt["group_bits"] != derivation["order_bits"]
        ),
        not _exact_receipt_int(receipt.get("bench_max_rounds"), 1),
        not _exact_receipt_int(receipt.get("rounds"), 1),
        type(receipt.get("settled")) is not dict,
        (
            receipt.get("settled", {}).get("settled") is not True
            if type(receipt.get("settled")) is dict else True
        ),
        not _finite_number(receipt.get("schedule_wall_s")),
        (
            float(receipt["schedule_wall_s"]) < 0
            if _finite_number(receipt.get("schedule_wall_s")) else False
        ),
    )):
        errors.append("schedule-receipt-header-mismatch")

    blocks = receipt.get("blocks")
    reps = receipt.get("reps")
    arms = receipt.get("arms")
    arm_names = _workload_arm_order(policy, workload_name)
    if (
        type(blocks) is not list
        or len(blocks) != len(plan["blocks"])
        or type(reps) is not list
        or len(reps) != _expected_reps(policy, workload_name) * 2
        or type(arms) is not dict
        or set(arms) != set(arm_names)
    ):
        errors.append("schedule-receipt-shape-mismatch")
        return sorted(set(errors))

    role_to_name = {
        role: _workload_arm_by_role(policy, workload_name, role)["name"]
        for role in ("variant", "baseline")
    }
    physical_tps: dict[str, list[float]] = {
        name: [] for name in arm_names
    }
    block_cvs: dict[str, list[float]] = {
        name: [] for name in arm_names
    }
    previous_finished: int | None = None
    for block_number, planned_block in enumerate(plan["blocks"]):
        arm_name = planned_block["arm"]
        observed_block = blocks[block_number]
        observed_rows = reps[block_number * 5:block_number * 5 + 5]
        if (
            type(observed_block) is not dict
            or set(observed_block) != _BALANCED_RECEIPT_BLOCK_KEYS
            or any(type(row) is not dict for row in observed_rows)
            or any(set(row) != _BALANCED_RECEIPT_REP_KEYS for row in observed_rows)
        ):
            errors.append("schedule-receipt-shape-mismatch")
            continue
        expected_group = planned_block["group"]
        expected_block_in_group = block_number % 4
        if any((
            observed_block.get("arm") != arm_name,
            not _exact_receipt_int(
                observed_block.get("group"), expected_group,
            ),
            not _exact_receipt_int(
                observed_block.get("block"), block_number,
            ),
            not _exact_receipt_int(
                observed_block.get("block_in_group"), expected_block_in_group,
            ),
        )):
            errors.append("schedule-receipt-placement-mismatch")
        values: list[float] = []
        for position, (row, pair_index) in enumerate(zip(
            observed_rows, planned_block["pair_indices"],
        )):
            started = row.get("started_at_ns")
            finished = row.get("ended_at_ns")
            if any((
                row.get("arm") != arm_name,
                not _exact_receipt_int(row.get("pair_index"), pair_index),
                not _exact_receipt_int(row.get("group"), expected_group),
                not _exact_receipt_int(
                    row.get("block"), planned_block["pair_block_number"],
                ),
                not _exact_receipt_int(row.get("block_position"), position),
                type(started) is not int,
                isinstance(started, bool),
                type(finished) is not int,
                isinstance(finished, bool),
                (
                    finished < started
                    if type(started) is int and not isinstance(started, bool)
                    and type(finished) is int and not isinstance(finished, bool)
                    else False
                ),
                (
                    started < previous_finished
                    if previous_finished is not None
                    and type(started) is int and not isinstance(started, bool)
                    else False
                ),
                not _finite_number(row.get("tps")),
                (
                    float(row["tps"]) <= 0
                    if _finite_number(row.get("tps")) else False
                ),
            )):
                errors.append("schedule-receipt-placement-mismatch")
            if (
                type(finished) is int and not isinstance(finished, bool)
                and type(started) is int and not isinstance(started, bool)
                and finished >= started
            ):
                previous_finished = finished
            if _finite_number(row.get("tps")) and float(row["tps"]) > 0:
                values.append(float(row["tps"]))
        if len(values) != 5:
            continue
        cv = statistics.stdev(values) / statistics.fmean(values)
        if (
            observed_block.get("tps") != [row["tps"] for row in observed_rows]
            or not _numbers_equal(observed_block.get("cv"), cv)
        ):
            errors.append("schedule-receipt-block-projection-mismatch")
        physical_tps[arm_name].extend(values)
        block_cvs[arm_name].append(cv)

    for _role, arm_name in role_to_name.items():
        arm_record = arms.get(arm_name)
        values = physical_tps[arm_name]
        if (
            type(arm_record) is not dict
            or set(arm_record) != _BALANCED_RECEIPT_ARM_KEYS
            or len(values) != _expected_reps(policy, workload_name)
        ):
            errors.append("schedule-receipt-arm-projection-mismatch")
            continue
        mean = statistics.fmean(values)
        cv = statistics.stdev(values) / mean
        expected_arm = (
            arm_results.get(arm_name)
            if arm_results is not None else None
        )
        if any((
            not _exact_receipt_int(arm_record.get("rounds"), 1),
            arm_record.get("tps") != values,
            not _numbers_equal(arm_record.get("median_tps"), statistics.median(values)),
            not _numbers_equal(arm_record.get("cv"), cv),
            arm_record.get("unstable") is not (cv > 0.05),
            (
                type(arm_record.get("block_cvs")) is not list
                or len(arm_record["block_cvs"]) != len(block_cvs[arm_name])
                or any(
                    not _numbers_equal(observed, expected)
                    for observed, expected in zip(
                        arm_record["block_cvs"], block_cvs[arm_name],
                    )
                )
            ),
            (
                type(arm_record.get("variant")) is not str
                or not arm_record["variant"]
            ),
            (
                expected_arm is not None
                and arm_record.get("variant") != expected_arm.get("variant")
            ),
            (
                expected_arm is not None
                and arm_record.get("tps") != expected_arm.get("raw_tps")
            ),
        )):
            errors.append("schedule-receipt-arm-projection-mismatch")
    return sorted(set(errors))


def _snapshot_balanced_schedule_receipt(
    policy: Mapping[str, object], workload_name: str, layout: CampaignLayout,
    expected_receipt: object = None,
) -> tuple[dict[str, object] | None, list[str]]:
    if _policy_schema(policy) != POLICY_SCHEMA_V3:
        return None, []
    path = Path(layout.root) / BALANCED_SCHEDULE_RECEIPT_NAME
    errors: list[str] = []
    try:
        raw = _read_bytes_once(path, missing_ok=True)
    except PaperStoryError as exc:
        raw = None
        errors.append(f"schedule-receipt-open-error:{exc}")
    evidence: dict[str, object] = {
        "path": os.fspath(path.resolve(strict=False)),
        "size": len(raw) if raw is not None else 0,
        "sha256": _sha256_bytes(raw) if raw is not None else None,
        "document": None,
    }
    if raw is None:
        errors.append("schedule-receipt-missing")
        return evidence, errors
    try:
        document = _decode_json_bytes(raw, "balanced schedule receipt")
    except PaperStoryError as exc:
        errors.append(f"schedule-receipt-decode-error:{exc}")
        return evidence, errors
    evidence["document"] = document
    if expected_receipt is not None and document != expected_receipt:
        errors.append("schedule-receipt-summary-mismatch")
    return evidence, errors


def _balanced_sizing_pilot_document(
    policy: Mapping[str, object], result: Mapping[str, object],
) -> dict[str, object]:
    if (
        _policy_schema(policy) != POLICY_SCHEMA_V3
        or _policy_study_id(policy) != V3_PILOT_STUDY_ID
        or policy.get("final_estimate_eligible") is not False
        or result.get("complete") is not True
    ):
        raise PaperStoryError(
            "balanced sizing pilot requires one complete registered pilot"
        )
    workloads = result.get("workloads")
    if (
        type(workloads) is not list
        or [item.get("workload") for item in workloads if type(item) is dict]
        != list(WORKLOAD_ORDER)
    ):
        raise PaperStoryError("balanced sizing pilot workload set differs")
    converted = []
    for item in workloads:
        name = item["workload"]
        evidence = item.get("schedule_receipt")
        document = evidence.get("document") if type(evidence) is dict else None
        receipt_errors = _balanced_schedule_receipt_errors(
            policy,
            name,
            document,
            item.get("arms") if type(item.get("arms")) is dict else None,
        )
        if receipt_errors:
            raise PaperStoryError(
                f"balanced sizing pilot receipt differs: {name}: "
                + ",".join(receipt_errors)
            )
        converted.append({
            "observations": document["reps"],
            "workload": name,
        })
    return {
        "final_estimate_eligible": False,
        "schema_version": BALANCED_SIZING_PILOT_SCHEMA,
        "study_id": V3_PILOT_STUDY_ID,
        "workloads": converted,
    }


def _campaign_execution_options(
    policy: Mapping[str, object], workload_name: str,
) -> dict[str, object]:
    """Return the only registered execution route for this policy schema."""
    if _policy_schema(policy) == POLICY_SCHEMA_V2:
        return {}
    workload = _workload_plan(policy, workload_name)
    options: dict[str, object] = {
        "bench_max_rounds": policy["execution"]["bench_max_rounds"],
        "balanced_schedule": BalancedScheduleConfig(
            workload=workload_name,
            root_seed=workload["schedule_root_seed"],
            arm_names=_workload_arm_order(policy, workload_name),
            receipt_name=BALANCED_SCHEDULE_RECEIPT_NAME,
        ),
    }
    return options


def _require_registered_execution_options(
    policy: Mapping[str, object], workload_name: str,
    options: Mapping[str, object],
) -> dict[str, object]:
    """Fail closed if a v3 caller could fall through to loop.py defaults."""
    if _policy_schema(policy) == POLICY_SCHEMA_V2:
        if dict(options):
            raise PaperStoryError("v2 execution options differ from legacy route")
        return {}
    workload = _workload_plan(policy, workload_name)
    schedule = options.get("balanced_schedule")
    if (
        set(options) != {"bench_max_rounds", "balanced_schedule"}
        or options.get("bench_max_rounds") != 1
        or type(schedule) is not BalancedScheduleConfig
        or schedule.workload != workload_name
        or schedule.root_seed != workload.get("schedule_root_seed")
        or schedule.arm_names != _workload_arm_order(policy, workload_name)
        or schedule.receipt_name != BALANCED_SCHEDULE_RECEIPT_NAME
    ):
        raise PaperStoryError(
            "v3 execution must use the registered balanced schedule"
        )
    return dict(options)


def _source_relative_paths(
    policy: Mapping[str, object], *, non_certifying: bool,
) -> tuple[str, ...]:
    is_v3 = _policy_schema(policy) == POLICY_SCHEMA_V3
    paths = (
        V3_NON_CERTIFYING_SOURCE_RELATIVE_PATHS
        if is_v3 and non_certifying else
        NON_CERTIFYING_SOURCE_RELATIVE_PATHS
        if non_certifying else
        V3_SOURCE_RELATIVE_PATHS
        if is_v3 else
        SOURCE_RELATIVE_PATHS
    )
    if _policy_study_id(policy) in a1_source.CONTRACTS:
        paths = (*paths, *a1_source.CONTRACTS[_policy_study_id(policy)][2])
    policy_relative = _policy_relative_path(policy)
    return tuple(
        policy_relative if item == POLICY_RELATIVE_PATH else item
        for item in paths
    )


def genomes(
    policy: Mapping[str, object], workload_name: str | None = None,
) -> list[Genome]:
    validate_policy(policy)
    if workload_name is None:
        if _policy_schema(policy) == POLICY_SCHEMA_V3:
            raise PaperStoryError("v3 genomes require an explicit workload")
        workload_name = WORKLOAD_ORDER[0]
    return [
        Genome(arm["protocol"], dict(arm["flags"]))
        for arm in _workload_arms(policy, workload_name)
    ]


def workload_flags(policy: Mapping[str, object], workload_name: str) -> dict[str, str]:
    validate_policy(policy)
    workload = next(
        (item for item in policy["workloads"] if item["name"] == workload_name),
        None,
    )
    if workload is None:
        raise PaperStoryError(f"unknown workload: {workload_name}")
    scale = policy["scale"]
    return {
        "ycsb_zipf_skew": scale["ycsb_zipf_skew"],
        "ycsb_rratio": workload["ycsb_rratio"],
        "ycsb_rmw": scale["ycsb_rmw"],
        "ycsb_max_ope": scale["ycsb_max_ope"],
    }


def _a1_noncertifying_marker_fields() -> dict[str, object]:
    return {
        "formal": False,
        "promotion_prohibited": True,
        "non_certifying_mode": (
            trial_registry.REGISTERED_FORMAL_NON_CERTIFYING_MODE
        ),
    }


def campaign_config(
    policy: Mapping[str, object], workload_name: str, *, contract=None,
    non_certifying: bool = False,
) -> CampaignConfig:
    validate_policy(policy)
    contract = contract or p2_2._legacy_linux_contract()
    flags = workload_flags(policy, workload_name)
    arm_plans = _workload_arms(policy, workload_name)
    study_id = _policy_study_id(policy)
    pairing_design = _pairing_design(policy)
    search_config = {
        "schema": _campaign_schema(policy),
        "study_id": study_id,
        "arm_order": [arm["name"] for arm in arm_plans],
        "arms": [
            {
                "name": arm["name"],
                "genome": Genome(arm["protocol"], dict(arm["flags"])).canonical(),
            }
            for arm in arm_plans
        ],
        "workload": {"name": workload_name, **flags},
        "scale": _campaign_scale(policy, workload_name),
        "pairing_design": pairing_design,
    }
    if _policy_schema(policy) == POLICY_SCHEMA_V3:
        search_config["schedule"] = {
            "arm_roles": {
                arm["name"]: {
                    "role": arm["role"],
                    "contrast": arm["contrast"],
                }
                for arm in arm_plans
            },
            **_balanced_schedule_plan(policy, workload_name),
        }
    if type(non_certifying) is not bool:
        raise PaperStoryError("non_certifying selector must be an exact bool")
    if non_certifying:
        search_config.update(_a1_noncertifying_marker_fields())
    else:
        search_config.update({
            "formal": False,
            "promotion_prohibited": True,
        })
    cfg = CampaignConfig(
        spec_slug=f"paper-story-a1-{workload_name}",
        search_tag="paired",
        spec_content=(
            (
                "D95 exploratory A-1 static10 minus adaptive, arm-grouped "
                "positional comparison"
            )
            if _policy_schema(policy) == POLICY_SCHEMA_V2
            else (
                "A-1 variant minus baseline under balanced five-rep blocks"
            )
        ) + f", workload={workload_name}",
        ccbench_commit=_campaign_ccbench_commit(policy),
        search_config=search_config,
        trial=study_id,
    )
    return ident.bind_environment_contract(cfg, contract)


def default_campaign_configs() -> tuple[CampaignConfig, ...]:
    """Return the legacy identity configs in the preregistered workload order."""
    policy, _policy_sha = load_policy()
    return tuple(
        campaign_config(policy, workload_name)
        for workload_name in WORKLOAD_ORDER
    )


def _run_git(repo_root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", os.fspath(repo_root), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise PaperStoryError(
            f"git {' '.join(args)} failed rc={proc.returncode}: {proc.stderr.strip()}"
        )
    return proc.stdout.strip()


def _assert_ccbench_acceptance(
    repo_root: Path,
    policy: Mapping[str, object],
    *,
    boundary: str,
) -> None:
    """Enforce one named v3 CCBench boundary against the submodule itself."""
    if _policy_schema(policy) == POLICY_SCHEMA_V2:
        return
    if boundary not in {
        "login-submit",
        "driver-measurement",
        "artifact-consumer",
    }:
        raise PaperStoryError("CCBench acceptance boundary is unknown")
    acceptance = policy.get("ccbench_acceptance")
    expected = (
        acceptance.get("canonical_pin") if type(acceptance) is dict else None
    )
    if expected != CANONICAL_CCBENCH_OID:
        raise PaperStoryError(f"CCBench {boundary}: policy canonical pin differs")
    ccbench_root = repo_root / "external" / "ccbench"
    try:
        observed = _run_git(ccbench_root, "rev-parse", "HEAD")
    except PaperStoryError as exc:
        raise PaperStoryError(
            f"CCBench {boundary}: cannot resolve submodule HEAD"
        ) from exc
    if observed != expected:
        raise PaperStoryError(f"CCBench {boundary}: canonical HEAD mismatch")
    try:
        tracked_status = _run_git(
            ccbench_root, "status", "--porcelain", "--untracked-files=no"
        )
    except PaperStoryError as exc:
        raise PaperStoryError(
            f"CCBench {boundary}: cannot inspect tracked status"
        ) from exc
    if tracked_status:
        raise PaperStoryError(f"CCBench {boundary}: tracked files are dirty")


def _parent_porcelain(
    repo_root: Path, policy: Mapping[str, object],
) -> str:
    args = ["status"]
    if _policy_schema(policy) == POLICY_SCHEMA_V3:
        args.append("--ignore-submodules=all")
    args.extend(("--porcelain", "--untracked-files=all"))
    return _run_git(repo_root, *args)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _paths_overlap(left: Path, right: Path) -> bool:
    return _is_within(left, right) or _is_within(right, left)


def _under_scr(path: Path) -> bool:
    scr = Path("/scr")
    return path == scr or _is_within(path, scr)


def _durable_measurement_base(policy: Mapping[str, object]) -> Path:
    execution = policy.get("execution")
    raw = (
        execution.get("durable_measurement_base")
        if type(execution) is dict else None
    )
    if type(raw) is not str:
        raise PaperStoryError("durable measurement base is missing from policy")
    base = Path(raw)
    if not base.is_absolute() or base.resolve(strict=False) != base:
        raise PaperStoryError("durable measurement base must be canonical absolute")
    return base


def _validate_attempt_root(attempt: Path, base: Path) -> Path:
    if not attempt.is_absolute() or attempt.resolve(strict=False) != attempt:
        raise PaperStoryError("acquisition attempt root must be canonical absolute")
    if attempt.parent != base or attempt == base:
        raise PaperStoryError(
            "acquisition attempt root must be one direct durable-base child"
        )
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", attempt.name) is None:
        raise PaperStoryError("acquisition attempt child name is unsafe")
    if os.path.lexists(attempt):
        try:
            info = attempt.lstat()
        except OSError as exc:
            raise PaperStoryError(f"acquisition attempt root stat failed: {exc}") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise PaperStoryError("acquisition attempt root must be a real directory")
        if attempt.resolve(strict=True) != attempt:
            raise PaperStoryError("acquisition attempt root must not traverse a symlink")
    return attempt


def _attempt_root_identity(attempt: Path) -> dict[str, int]:
    try:
        info = attempt.lstat()
    except OSError as exc:
        raise PaperStoryError(f"attempt root identity stat failed: {exc}") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise PaperStoryError("attempt root identity requires a real directory")
    if attempt.resolve(strict=True) != attempt:
        raise PaperStoryError("attempt root identity traverses a symlink")
    return {"st_dev": info.st_dev, "st_ino": info.st_ino}


def _revalidate_attempt_root(roots: Mapping[str, object]) -> None:
    attempt_raw = roots.get("attempt_root")
    expected = roots.get("attempt_identity")
    if (
        type(attempt_raw) is not str
        or type(expected) is not dict
        or set(expected) != {"st_dev", "st_ino"}
        or type(expected.get("st_dev")) is not int
        or type(expected.get("st_ino")) is not int
    ):
        raise PaperStoryError("attempt root inode binding is missing")
    if _attempt_root_identity(Path(attempt_raw)) != expected:
        raise PaperStoryError("attempt root inode binding differs")


def _attempt_evidence_paths(attempt: Path) -> dict[str, str]:
    base = attempt.parent
    stem = attempt.name
    return {
        "submission_receipt": os.fspath(base / f"{stem}.submission.json"),
        "completion_receipt": os.fspath(base / f"{stem}.completion.json"),
        "stdout_path": os.fspath(base / f"{stem}.stdout"),
        "stderr_path": os.fspath(base / f"{stem}.stderr"),
    }


def _v3_attempt_evidence_paths(attempt: Path) -> dict[str, str]:
    return {
        "submission_receipt": os.fspath(attempt / "receipts" / "submission.json"),
        "submission_failure": os.fspath(
            attempt / "receipts" / "submission-failure.json"
        ),
        "completion_receipt": os.fspath(attempt / "receipts" / "completion.json"),
        "group_terminal": os.fspath(attempt / "raw" / "job-terminal.json"),
        "result_root": os.fspath(attempt / "raw" / "results"),
    }


def _v3_job_roots(attempt: Path, workload: str) -> dict[str, str]:
    if workload not in WORKLOAD_ORDER:
        raise PaperStoryError("workload selector differs")
    job_root = attempt / "jobs" / workload
    scheduler_root = job_root / "scheduler"
    raw_root = job_root / "raw"
    return {
        "attempt_root": os.fspath(attempt),
        "attempt_identity": (
            _attempt_root_identity(attempt) if attempt.is_dir() else None
        ),
        "job_root": os.fspath(job_root),
        "scheduler_root": os.fspath(scheduler_root),
        "raw_root": os.fspath(raw_root),
        "output_root": os.fspath(raw_root / "campaign-output"),
        "cache_root": os.fspath(job_root / "cache"),
        "result_root": os.fspath(raw_root / "results"),
        "tmp_root": os.fspath(raw_root / "tmp"),
        "stdout_path": os.fspath(scheduler_root / "job.stdout"),
        "stderr_path": os.fspath(scheduler_root / "job.stderr"),
        "qsub_stdout_path": os.fspath(scheduler_root / "qsub.stdout"),
        "qsub_stderr_path": os.fspath(scheduler_root / "qsub.stderr"),
        "request_id_path": os.fspath(scheduler_root / "request-id"),
        "qstat_visibility_path": os.fspath(
            scheduler_root / "qstat-visibility.json"
        ),
        "submission_receipt": os.fspath(
            attempt / "receipts" / "submission.json"
        ),
        "completion_receipt": os.fspath(
            attempt / "receipts" / "completion.json"
        ),
        "job_terminal": os.fspath(job_root / "job-terminal.json"),
        "ready": os.fspath(attempt / "barrier" / "ready" / f"{workload}.json"),
        "bench_go": os.fspath(attempt / "barrier" / "bench-go.json"),
        "bench_start": os.fspath(
            attempt / "barrier" / "bench-start" / f"{workload}.json"
        ),
    }


def _canonical_v3_qsub_contract(
    *,
    repo_root: Path,
    study_id: str,
    source_commit: str,
    attempt: Path,
    workload: str,
    third_party_source_root: str | None = None,
) -> tuple[list[str], dict[str, object]]:
    roots = _v3_job_roots(attempt, workload)
    variables = {
        "IZANAGI_EXPECTED_HEAD": source_commit,
        "IZANAGI_A1_STUDY_ID": study_id,
        "IZANAGI_A1_ATTEMPT_ROOT": os.fspath(attempt),
        "IZANAGI_A1_WORKLOAD": workload,
        "IZANAGI_A1_ACQUISITION_RECEIPT": roots["submission_receipt"],
        "IZANAGI_A1_COMPLETION_RECEIPT": roots["completion_receipt"],
        "IZANAGI_SUBMISSION_NONCE": f"{attempt.name}.{workload}",
    }
    if third_party_source_root is not None:
        variables["IZANAGI_A1_THIRD_PARTY_SOURCE_ROOT"] = third_party_source_root
    variable_text = ",".join(f"{key}={value}" for key, value in variables.items())
    options = {
        "v": variable_text,
        "variables": variables,
        "o": roots["stdout_path"],
        "e": roots["stderr_path"],
    }
    argv = [
        "qsub", "-v", variable_text,
        "-o", roots["stdout_path"],
        "-e", roots["stderr_path"],
        os.fspath((repo_root / JOB_RELATIVE_PATH).resolve(strict=True)),
    ]
    return argv, options


def _v3_group_intent(
    *,
    repo_root: Path,
    policy: Mapping[str, object],
    source_commit: str,
    attempt: Path,
    third_party_source_root: str | None = None,
) -> dict[str, object]:
    if third_party_source_root is None and _attempt_intent_path(attempt).is_file():
        recorded = _read_json(_attempt_intent_path(attempt))
        try:
            third_party_source_root = recorded["jobs"][0]["qsub_options"]["variables"].get(
                "IZANAGI_A1_THIRD_PARTY_SOURCE_ROOT")
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            raise PaperStoryError("group submission intent supply shape differs") from exc
    if third_party_source_root is not None:
        if (not _canonical_absolute_token(third_party_source_root)
                or any(c in third_party_source_root for c in ",\n\r")):
            raise PaperStoryError("third-party source root must be canonical absolute qsub data")
    if (_policy_study_id(policy) in a1_source.CONTRACTS
            and (_policy_study_id(policy) == a1_source.SIZED_STUDY_ID
                 or attempt.name == "attempt-0004")):
        a1_source.load_contract(repo_root, _policy_study_id(policy))
        if third_party_source_root is None:
            raise PaperStoryError("attempt-0004 requires hydrated third-party source root")
    jobs = []
    for ordinal, workload in enumerate(WORKLOAD_ORDER):
        argv, options = _canonical_v3_qsub_contract(
            repo_root=repo_root,
            study_id=_policy_study_id(policy),
            source_commit=source_commit,
            attempt=attempt,
            workload=workload,
            third_party_source_root=third_party_source_root,
        )
        jobs.append({
            "workload": workload,
            "ordinal": ordinal,
            "qsub_argv": argv,
            "qsub_options": options,
        })
    value = {
        "schema_version": V3_GROUP_INTENT_SCHEMA,
        "study_id": _policy_study_id(policy),
        "source_commit": source_commit,
        "attempt_root": os.fspath(attempt),
        "jobs": jobs,
        "source_binding": _non_certifying_source_binding(
            repo_root, source_commit, policy,
        ),
    }
    value["intent_sha256"] = _submission_intent_digest(value)
    return value


def _assert_no_prior_v3_bench_start(
    base: Path, *, study_id: str, current_attempt: Path,
) -> None:
    """MF2 rear gate: fail closed once a prior attempt could reach bench."""
    try:
        entries = tuple(base.iterdir())
    except FileNotFoundError:
        return
    except OSError as exc:
        raise PaperStoryError(f"cannot inspect prior attempts: {exc}") from exc

    intent_studies: dict[Path, str] = {}
    suffix = ".intent.json"
    for intent_path in entries:
        if not intent_path.name.endswith(suffix):
            continue
        if intent_path.is_symlink() or not intent_path.is_file():
            raise PaperStoryError("prior group intent evidence is unsafe")
        intent = _read_json(intent_path)
        attempt_name = intent_path.name[:-len(suffix)]
        prior = base / attempt_name
        if (
            not attempt_name
            or type(intent) is not dict
            or set(intent) != {
                "schema_version", "study_id", "source_commit", "attempt_root",
                "jobs", "source_binding", "intent_sha256",
            }
            or intent.get("schema_version") != V3_GROUP_INTENT_SCHEMA
            or type(intent.get("study_id")) is not str
            or type(intent.get("source_commit")) is not str
            or _FULL_OID.fullmatch(intent["source_commit"]) is None
            or intent.get("attempt_root") != os.fspath(prior)
            or type(intent.get("jobs")) is not list
            or len(intent["jobs"]) != len(WORKLOAD_ORDER)
            or any(type(job) is not dict for job in intent["jobs"])
            or type(intent.get("source_binding")) is not dict
            or intent.get("intent_sha256") != _submission_intent_digest(intent)
        ):
            raise PaperStoryError("prior group intent evidence is corrupt")
        if [job.get("workload") for job in intent["jobs"]] != list(
            WORKLOAD_ORDER
        ) or [job.get("ordinal") for job in intent["jobs"]] != list(
            range(len(WORKLOAD_ORDER))
        ):
            raise PaperStoryError("prior group intent job identity is corrupt")
        intent_studies[prior] = intent["study_id"]

    candidates = {
        entry for entry in entries
        if entry != current_attempt
        and not entry.name.endswith(suffix)
        and (entry / "barrier").exists()
    } | {
        prior for prior in intent_studies
        if prior != current_attempt and os.path.lexists(prior)
    }
    for prior in sorted(candidates):
        if prior.is_symlink() or not prior.is_dir():
            raise PaperStoryError("prior attempt evidence root is unsafe")
        same_study_intent = intent_studies.get(prior) == study_id
        barrier = prior / "barrier"
        if barrier.is_symlink() or not barrier.is_dir():
            raise PaperStoryError("prior barrier evidence root is unsafe")

        ready_root = barrier / "ready"
        ready_workloads: set[str] = set()
        if os.path.lexists(ready_root):
            if ready_root.is_symlink() or not ready_root.is_dir():
                raise PaperStoryError("prior ready evidence root is unsafe")
            try:
                ready_entries = tuple(ready_root.iterdir())
            except OSError as exc:
                raise PaperStoryError(
                    f"cannot inspect prior ready evidence: {exc}"
                ) from exc
            for ready_path in ready_entries:
                if (
                    ready_path.is_symlink()
                    or not ready_path.is_file()
                    or ready_path.name not in {
                        f"{workload}.json" for workload in WORKLOAD_ORDER
                    }
                ):
                    raise PaperStoryError("prior ready evidence is unsafe")
                ready = _read_json(ready_path)
                ready_workload = ready_path.stem
                if (
                    type(ready) is not dict
                    or set(ready) != {
                        "schema_version", "study_id", "source_commit",
                        "attempt_root", "workload", "ordinal", "request_id",
                        "reservation_nonce", "campaign_id", "prepared_arms",
                        "recorded_epoch",
                    }
                    or ready.get("schema_version") != V3_READY_SCHEMA
                    or ready.get("attempt_root") != os.fspath(prior)
                    or ready.get("workload") != ready_workload
                    or ready.get("ordinal") != WORKLOAD_ORDER.index(ready_workload)
                    or type(ready.get("study_id")) is not str
                    or type(ready.get("source_commit")) is not str
                    or _FULL_OID.fullmatch(ready["source_commit"]) is None
                    or type(ready.get("request_id")) is not str
                    or type(ready.get("reservation_nonce")) is not str
                    or type(ready.get("campaign_id")) is not str
                    or not ready["campaign_id"]
                    or type(ready.get("prepared_arms")) is not list
                    or len(ready["prepared_arms"]) != len(ARM_ORDER)
                    or type(ready.get("recorded_epoch")) is not int
                    or ready["recorded_epoch"] <= 0
                ):
                    raise PaperStoryError("prior ready evidence is corrupt")
                for arm in ready["prepared_arms"]:
                    if (
                        type(arm) is not dict
                        or set(arm) != {
                            "variant", "build_attempt_id",
                            "build_admission_receipt_sha256", "verify_tags",
                        }
                        or type(arm.get("variant")) is not str
                        or not arm["variant"]
                        or type(arm.get("build_attempt_id")) is not str
                        or not arm["build_attempt_id"]
                        or type(arm.get(
                            "build_admission_receipt_sha256"
                        )) is not str
                        or _FULL_SHA256.fullmatch(
                            arm["build_admission_receipt_sha256"]
                        ) is None
                        or arm.get("verify_tags") != list(EXPECTED_VERIFY_CONFIGS)
                    ):
                        raise PaperStoryError("prior ready arm evidence is corrupt")
                if same_study_intent and ready.get("study_id") != study_id:
                    raise PaperStoryError("prior ready evidence study differs")
                if ready.get("study_id") == study_id:
                    ready_workloads.add(ready_workload)

        bench_go_path = barrier / "bench-go.json"
        bench_go_study = None
        if os.path.lexists(bench_go_path):
            if bench_go_path.is_symlink() or not bench_go_path.is_file():
                raise PaperStoryError("prior bench-go evidence is unsafe")
            bench_go = _read_json(bench_go_path)
            if (
                type(bench_go) is not dict
                or set(bench_go) != {
                    "schema_version", "study_id", "source_commit",
                    "attempt_root", "ready",
                }
                or bench_go.get("schema_version") != V3_BENCH_GO_SCHEMA
                or bench_go.get("attempt_root") != os.fspath(prior)
                or type(bench_go.get("study_id")) is not str
                or type(bench_go.get("ready")) is not list
                or len(bench_go["ready"]) != len(WORKLOAD_ORDER)
            ):
                raise PaperStoryError("prior bench-go evidence is corrupt")
            for ordinal, (binding, workload) in enumerate(zip(
                bench_go["ready"], WORKLOAD_ORDER,
            )):
                if (
                    type(binding) is not dict
                    or set(binding) != {
                        "workload", "ordinal", "campaign_id", "path", "sha256",
                    }
                    or binding.get("workload") != workload
                    or binding.get("ordinal") != ordinal
                    or type(binding.get("campaign_id")) is not str
                    or not binding["campaign_id"]
                    or binding.get("path")
                    != os.fspath(ready_root / f"{workload}.json")
                    or type(binding.get("sha256")) is not str
                    or _FULL_SHA256.fullmatch(binding["sha256"]) is None
                ):
                    raise PaperStoryError("prior bench-go ready binding is corrupt")
            bench_go_study = bench_go["study_id"]
            if same_study_intent and bench_go_study != study_id:
                raise PaperStoryError("prior bench-go evidence study differs")

        bench_root = barrier / "bench-start"
        bench_start_studies: set[str] = set()
        if not os.path.lexists(bench_root):
            bench_entries = ()
        elif bench_root.is_symlink() or not bench_root.is_dir():
            raise PaperStoryError("prior bench-start evidence root is unsafe")
        else:
            try:
                bench_entries = tuple(bench_root.iterdir())
            except OSError as exc:
                raise PaperStoryError(
                    f"cannot inspect prior bench-start evidence: {exc}"
                ) from exc
        for evidence_path in bench_entries:
            if (
                evidence_path.is_symlink()
                or not evidence_path.is_file()
                or evidence_path.name not in {
                    f"{workload}.json" for workload in WORKLOAD_ORDER
                }
            ):
                raise PaperStoryError("prior bench-start evidence is unsafe")
            evidence = _read_json(evidence_path)
            if (
                type(evidence) is not dict
                or evidence.get("schema_version") != V3_BENCH_START_SCHEMA
                or set(evidence) != {
                    "schema_version", "study_id", "source_commit",
                    "attempt_root", "workload", "ordinal", "request_id",
                    "bench_go_sha256", "ready_sha256", "recorded_epoch",
                }
                or evidence.get("attempt_root") != os.fspath(prior)
                or evidence.get("workload") != evidence_path.stem
                or evidence.get("ordinal")
                != WORKLOAD_ORDER.index(evidence_path.stem)
                or type(evidence.get("study_id")) is not str
                or type(evidence.get("source_commit")) is not str
                or _FULL_OID.fullmatch(evidence["source_commit"]) is None
                or type(evidence.get("request_id")) is not str
                or type(evidence.get("bench_go_sha256")) is not str
                or _FULL_SHA256.fullmatch(evidence["bench_go_sha256"]) is None
                or type(evidence.get("ready_sha256")) is not str
                or _FULL_SHA256.fullmatch(evidence["ready_sha256"]) is None
                or type(evidence.get("recorded_epoch")) is not int
                or evidence["recorded_epoch"] <= 0
            ):
                raise PaperStoryError("prior bench-start evidence is corrupt")
            if same_study_intent and evidence.get("study_id") != study_id:
                raise PaperStoryError("prior bench-start evidence study differs")
            bench_start_studies.add(evidence["study_id"])

        if (
            bench_go_study == study_id
            or ready_workloads == set(WORKLOAD_ORDER)
            or study_id in bench_start_studies
        ):
            raise PaperStoryError(
                "prior attempt reached the bench barrier; group rerun is prohibited"
            )
        if same_study_intent and (
            os.path.lexists(bench_go_path)
            or all(os.path.lexists(
                ready_root / f"{workload}.json"
            ) for workload in WORKLOAD_ORDER)
        ):
            # The intent supplies study identity even if a later namespace was
            # emptied between publication and this inspection.
            raise PaperStoryError(
                "prior attempt reached the bench barrier; group rerun is prohibited"
            )


def _attempt_intent_path(attempt: Path) -> Path:
    return attempt.parent / f"{attempt.name}.intent.json"


def _submission_intent_digest(value: Mapping[str, object]) -> str:
    payload = dict(value)
    supplied = payload.pop("intent_sha256", None)
    if supplied is not None and (
        type(supplied) is not str or _FULL_SHA256.fullmatch(supplied) is None
    ):
        raise PaperStoryError("submission intent digest shape differs")
    return _sha256_bytes(_canonical_json_bytes(payload))


def _validate_submission_intent(
    value: object,
    *,
    repo_root: Path,
    source_commit: str,
    attempt: Path,
    policy: Mapping[str, object] | None = None,
) -> dict[str, object]:
    policy = policy if policy is not None else load_policy()[0]
    study_id = _policy_study_id(policy)
    if _policy_schema(policy) == POLICY_SCHEMA_V3:
        expected = _v3_group_intent(
            repo_root=repo_root,
            policy=policy,
            source_commit=source_commit,
            attempt=attempt,
        )
        if type(value) is not dict or value != expected:
            raise PaperStoryError("group submission intent identity differs")
        _verify_current_source_paths(
            repo_root,
            source_commit,
            value["source_binding"],
            relative_paths=_source_relative_paths(policy, non_certifying=True),
            label="group submission intent",
        )
        return dict(value)
    if type(value) is not dict or set(value) != {
        "schema_version", "study_id", "source_commit", "attempt_root",
        "qsub_argv", "qsub_options", "source_binding", "intent_sha256",
    }:
        raise PaperStoryError("submission intent shape differs")
    expected_argv, expected_options = _canonical_qsub_contract(
        repo_root=repo_root,
        study_id=study_id,
        source_commit=source_commit,
        attempt=attempt,
    )
    if (
        value.get("schema_version") != SUBMISSION_INTENT_SCHEMA
        or value.get("study_id") != study_id
        or value.get("source_commit") != source_commit
        or value.get("attempt_root") != os.fspath(attempt)
        or value.get("qsub_argv") != expected_argv
        or value.get("qsub_options") != expected_options
        or not _validate_non_certifying_source_binding(
            value.get("source_binding"), policy,
        )
        or value.get("intent_sha256") != _submission_intent_digest(value)
    ):
        raise PaperStoryError("submission intent identity differs")
    _verify_current_source_paths(
        repo_root,
        source_commit,
        value["source_binding"],
        relative_paths=_source_relative_paths(policy, non_certifying=True),
        label="submission intent",
    )
    return dict(value)


def _run_qsub(
    argv: Sequence[str], *, cwd: Path,
) -> subprocess.CompletedProcess[str]:
    """Production direct qsub call site; tests monkeypatch this private seam."""
    return subprocess.run(
        list(argv), text=True, capture_output=True, check=False, cwd=cwd,
    )


def _assert_submit_a1_noncertifying_markers(
    policy: Mapping[str, object] | None = None,
) -> None:
    """Refuse before intent/qsub if the tracked A-1 producer markers drift."""
    policy = policy if policy is not None else load_policy()[0]
    study_id = _policy_study_id(policy)
    cfg = CampaignConfig(
        spec_slug="paper-story-a1-submit-marker",
        spec_content="paper-story A-1 submit marker",
        ccbench_commit=_campaign_ccbench_commit(policy),
        search_tag="paired",
        search_config={
            "schema": _campaign_schema(policy),
            "study_id": study_id,
            "pairing_design": _pairing_design(policy),
            **_a1_noncertifying_marker_fields(),
        },
        trial=study_id,
    )
    if (
        tuple(WORKLOAD_ORDER) != trial_registry.A1_NON_CERTIFYING_WORKLOADS
        or not ident.is_a1_non_certifying_config(cfg)
    ):
        raise PaperStoryError(
            "A-1 formal/promotion_prohibited marker differs before submit"
        )


def _observe_qstat_visibility(request_id: str) -> dict[str, object]:
    """Observe the submitted NQSV request once through direct qstat."""
    completed = subprocess.run(
        ["qstat", "-f", _validated_request_id(request_id, "qstat request ID")],
        text=True,
        capture_output=True,
        check=False,
    )
    stdout = completed.stdout
    state = target_bound_qstat_state_result(stdout, request_id).state
    request_matches = list(_QSTAT_REQUEST_ID_RE.finditer(stdout))
    queue_candidates = list(_NQSV_EXECUTION_QUEUE_CANDIDATE_RE.finditer(stdout))
    queue_match = (
        _NQSV_EXECUTION_QUEUE_RE.fullmatch(queue_candidates[0].group(0))
        if len(queue_candidates) == 1
        else None
    )
    queue = queue_match.group(1) if queue_match is not None else None
    visible = (
        completed.returncode == 0
        and completed.stderr == ""
        and state in _NQSV_SUBMISSION_VISIBLE_STATES
        and len(request_matches) == 1
        and len(queue_candidates) == 1
        and queue_candidates[0].start() > request_matches[0].end()
        and queue_match is not None
        and queue == _PBS_QUEUE
    )
    if not visible:
        raise PaperStoryError("qstat did not visibly bind the submitted request")
    return {
        "request_id": request_id,
        "visible": True,
        "state": state,
        "queue": queue,
        "observed_epoch": int(time.time()),
    }


def _validate_v3_group_submission(
    value: object,
    *,
    repo_root: Path,
    policy: Mapping[str, object],
    source_commit: str,
    attempt: Path,
) -> dict[str, object]:
    """Validate the exact ordered group receipt and normalized job identities."""
    expected_intent = _v3_group_intent(
        repo_root=repo_root,
        policy=policy,
        source_commit=source_commit,
        attempt=attempt,
    )
    evidence = _v3_attempt_evidence_paths(attempt)
    if type(value) is not dict or set(value) != {
        "schema_version", "route", "study_id", "source_commit",
        "attempt_root", "submission_receipt_path", "completion_receipt_path",
        "intent_sha256", "jobs",
    }:
        raise PaperStoryError("group submission receipt shape differs")
    if (
        value.get("schema_version") != V3_GROUP_SUBMISSION_SCHEMA
        or value.get("route") != "direct-qsub-workload-fanout"
        or value.get("study_id") != _policy_study_id(policy)
        or value.get("source_commit") != source_commit
        or value.get("attempt_root") != os.fspath(attempt)
        or value.get("submission_receipt_path") != evidence["submission_receipt"]
        or value.get("completion_receipt_path") != evidence["completion_receipt"]
        or value.get("intent_sha256") != expected_intent["intent_sha256"]
    ):
        raise PaperStoryError("group submission receipt identity differs")
    jobs = value.get("jobs")
    if type(jobs) is not list or len(jobs) != len(WORKLOAD_ORDER):
        raise PaperStoryError("group submission is not the exact workload triple")
    normalized: list[str] = []
    validated_jobs = []
    for ordinal, (job, expected_job, workload) in enumerate(zip(
        jobs, expected_intent["jobs"], WORKLOAD_ORDER,
    )):
        if type(job) is not dict or set(job) != {
            "workload", "ordinal", "request_id", "qsub_argv",
            "qsub_options", "submit_observation",
        }:
            raise PaperStoryError("group submission job shape differs")
        if (
            job.get("workload") != workload
            or job.get("ordinal") != ordinal
            or job.get("qsub_argv") != expected_job["qsub_argv"]
            or job.get("qsub_options") != expected_job["qsub_options"]
        ):
            raise PaperStoryError("group submission job contract differs")
        request_id = _validated_request_id(
            job.get("request_id"), f"{workload} submission request ID",
        )
        observation = job.get("submit_observation")
        if type(observation) is not dict or set(observation) != {
            "submit_host", "qsub_stdout", "qsub_stdout_sha256",
            "qsub_stderr", "qsub_stderr_sha256", "qstat_visibility",
        }:
            raise PaperStoryError("group submission observation shape differs")
        stdout = observation.get("qsub_stdout")
        stderr = observation.get("qsub_stderr")
        visibility = observation.get("qstat_visibility")
        if (
            type(observation.get("submit_host")) is not str
            or not observation["submit_host"]
            or type(stdout) is not str
            or stderr != ""
            or observation.get("qsub_stdout_sha256")
            != _sha256_bytes(stdout.encode("utf-8"))
            or observation.get("qsub_stderr_sha256")
            != _sha256_bytes(stderr.encode("utf-8"))
            or _validated_request_id(
                _parse_request_id(stdout), f"{workload} parsed request ID",
            ) != request_id
            or type(visibility) is not dict
            or set(visibility) != {
                "request_id", "visible", "state", "queue", "observed_epoch",
            }
            or visibility.get("visible") is not True
            or visibility.get("state") not in NQSV_QSTAT_STATES
            or visibility.get("queue") != _PBS_QUEUE
            or type(visibility.get("observed_epoch")) is not int
            or visibility["observed_epoch"] <= 0
            or _validated_request_id(
                visibility.get("request_id"), f"{workload} qstat request ID",
            ) != request_id
        ):
            raise PaperStoryError("group submission observation differs")
        normalized.append(request_id)
        validated_jobs.append(dict(job))
    # MF1: raw aliases such as 123.server and 0:123.server are one request.
    if len(set(normalized)) != len(WORKLOAD_ORDER):
        raise PaperStoryError("normalized request IDs are not a unique triple")
    return {**value, "jobs": validated_jobs}


def _write_v3_submission_failure(
    path: Path,
    *,
    study_id: str,
    source_commit: str,
    attempt: Path,
    intent_sha256: str,
    jobs: Sequence[Mapping[str, object]],
) -> None:
    statuses = [dict(item) for item in jobs]
    while len(statuses) < len(WORKLOAD_ORDER):
        ordinal = len(statuses)
        statuses.append({
            "workload": WORKLOAD_ORDER[ordinal],
            "ordinal": ordinal,
            "status": "not-attempted",
            "request_id": None,
            "returncode": None,
        })
    _exclusive_write(path, {
        "schema_version": V3_GROUP_SUBMISSION_FAILURE_SCHEMA,
        "status": "not-successful",
        "reason": "scheduler-or-infrastructure-failure-before-bench",
        "study_id": study_id,
        "source_commit": source_commit,
        "attempt_root": os.fspath(attempt),
        "intent_sha256": intent_sha256,
        "jobs": statuses,
        "recorded_epoch": int(time.time()),
    })
    _fsync_directory(path.parent)


def _run_submit_v3(
    *,
    repo_root: Path,
    policy: Mapping[str, object],
    expected_head: str,
    attempt: Path,
    third_party_source_root: str | None = None,
) -> int:
    study_id = _policy_study_id(policy)
    evidence = _v3_attempt_evidence_paths(attempt)
    intent_path = _attempt_intent_path(attempt)
    submission_path = Path(evidence["submission_receipt"])
    failure_path = Path(evidence["submission_failure"])
    staging_path = _receipt_staging_path(
        submission_path, receipt_kind="submission",
    )
    guarded = [
        submission_path, failure_path, Path(evidence["completion_receipt"]),
        Path(evidence["group_terminal"]), staging_path,
    ]
    if os.path.lexists(intent_path):
        raise PaperStoryError(
            "submission indeterminate: intent exists without group receipt; "
            "qsub will not be repeated"
        )
    if os.path.lexists(attempt):
        raise PaperStoryError("submit attempt root must not already exist")
    if any(os.path.lexists(path) for path in guarded):
        raise PaperStoryError("v3 group evidence namespace is not fresh")
    _assert_no_prior_v3_bench_start(
        attempt.parent, study_id=study_id, current_attempt=attempt,
    )
    intent = _v3_group_intent(
        repo_root=repo_root,
        policy=policy,
        source_commit=expected_head,
        attempt=attempt,
        third_party_source_root=third_party_source_root,
    )
    _exclusive_write(intent_path, intent)
    _fsync_directory(intent_path.parent)
    try:
        attempt.mkdir(mode=0o700)
        (attempt / "receipts").mkdir(mode=0o700)
        (attempt / "raw").mkdir(mode=0o700)
        (attempt / "barrier").mkdir(mode=0o700)
        (attempt / "barrier" / "ready").mkdir(mode=0o700)
        (attempt / "barrier" / "bench-start").mkdir(mode=0o700)
        (attempt / "jobs").mkdir(mode=0o700)
        for workload in WORKLOAD_ORDER:
            job_root = attempt / "jobs" / workload
            job_root.mkdir(mode=0o700)
            (job_root / "scheduler").mkdir(mode=0o700)
            _fsync_directory(job_root / "scheduler")
            _fsync_directory(job_root)
        for directory in (
            attempt / "receipts", attempt / "raw",
            attempt / "barrier" / "ready",
            attempt / "barrier" / "bench-start",
            attempt / "barrier", attempt / "jobs",
        ):
            _fsync_directory(directory)
        _fsync_directory(attempt)
    except OSError as exc:
        raise PaperStoryError(f"v3 attempt topology creation failed: {exc}") from exc

    receipt_jobs: list[dict[str, object]] = []
    failure_jobs: list[dict[str, object]] = []
    for ordinal, expected_job in enumerate(intent["jobs"]):
        workload = WORKLOAD_ORDER[ordinal]
        roots = _v3_job_roots(attempt, workload)
        try:
            completed = _run_qsub(expected_job["qsub_argv"], cwd=repo_root)
        except OSError as exc:
            _exclusive_write_text(Path(roots["qsub_stdout_path"]), "")
            _exclusive_write_text(Path(roots["qsub_stderr_path"]), str(exc) + "\n")
            _fsync_directory(Path(roots["scheduler_root"]))
            failure_jobs.append({
                "workload": workload, "ordinal": ordinal,
                "status": "indeterminate", "request_id": None,
                "returncode": None,
            })
            _write_v3_submission_failure(
                failure_path, study_id=study_id, source_commit=expected_head,
                attempt=attempt, intent_sha256=intent["intent_sha256"],
                jobs=failure_jobs,
            )
            raise PaperStoryError("qsub invocation is indeterminate") from exc
        _exclusive_write_text(Path(roots["qsub_stdout_path"]), completed.stdout)
        _exclusive_write_text(Path(roots["qsub_stderr_path"]), completed.stderr)
        _fsync_directory(Path(roots["scheduler_root"]))
        if completed.returncode != 0 or completed.stderr != "":
            failure_jobs.append({
                "workload": workload, "ordinal": ordinal,
                "status": "failed", "request_id": None,
                "returncode": completed.returncode,
            })
            _write_v3_submission_failure(
                failure_path, study_id=study_id, source_commit=expected_head,
                attempt=attempt, intent_sha256=intent["intent_sha256"],
                jobs=failure_jobs,
            )
            raise PaperStoryError(
                "qsub failed after durable group intent; group submission failed"
            )
        try:
            request_id = _parse_request_id(completed.stdout)
            _exclusive_write_text(Path(roots["request_id_path"]), request_id + "\n")
            _fsync_directory(Path(roots["scheduler_root"]))
            visibility = _observe_qstat_visibility(request_id)
        except (PaperStoryError, OSError) as exc:
            failure_jobs.append({
                "workload": workload, "ordinal": ordinal,
                "status": "indeterminate", "request_id": None,
                "returncode": completed.returncode,
            })
            _write_v3_submission_failure(
                failure_path, study_id=study_id, source_commit=expected_head,
                attempt=attempt, intent_sha256=intent["intent_sha256"],
                jobs=failure_jobs,
            )
            raise PaperStoryError(
                "qsub request identity/visibility is indeterminate"
            ) from exc
        _exclusive_write(Path(roots["qstat_visibility_path"]), visibility)
        _fsync_directory(Path(roots["scheduler_root"]))
        normalized = _validated_request_id(request_id, "submitted request ID")
        prior = [
            _validated_request_id(item["request_id"], "prior request ID")
            for item in receipt_jobs
        ]
        if normalized in prior:
            failure_jobs.append({
                "workload": workload, "ordinal": ordinal,
                "status": "indeterminate", "request_id": request_id,
                "returncode": completed.returncode,
            })
            _write_v3_submission_failure(
                failure_path, study_id=study_id, source_commit=expected_head,
                attempt=attempt, intent_sha256=intent["intent_sha256"],
                jobs=failure_jobs,
            )
            raise PaperStoryError("normalized request IDs are not a unique triple")
        observation = {
            "submit_host": socket.gethostname(),
            "qsub_stdout": completed.stdout,
            "qsub_stdout_sha256": _sha256_bytes(completed.stdout.encode("utf-8")),
            "qsub_stderr": completed.stderr,
            "qsub_stderr_sha256": _sha256_bytes(completed.stderr.encode("utf-8")),
            "qstat_visibility": visibility,
        }
        receipt_jobs.append({
            "workload": workload, "ordinal": ordinal, "request_id": request_id,
            "qsub_argv": expected_job["qsub_argv"],
            "qsub_options": expected_job["qsub_options"],
            "submit_observation": observation,
        })
        failure_jobs.append({
            "workload": workload, "ordinal": ordinal,
            "status": "accepted", "request_id": request_id,
            "returncode": completed.returncode,
        })
    receipt = {
        "schema_version": V3_GROUP_SUBMISSION_SCHEMA,
        "route": "direct-qsub-workload-fanout",
        "study_id": study_id,
        "source_commit": expected_head,
        "attempt_root": os.fspath(attempt),
        "submission_receipt_path": evidence["submission_receipt"],
        "completion_receipt_path": evidence["completion_receipt"],
        "intent_sha256": intent["intent_sha256"],
        "jobs": receipt_jobs,
    }
    _validate_v3_group_submission(
        receipt, repo_root=repo_root, policy=policy,
        source_commit=expected_head, attempt=attempt,
    )
    try:
        _publish_submission_receipt(submission_path, receipt)
    except _PublishedReceiptCleanupError:
        raise
    except PaperStoryError:
        _write_v3_submission_failure(
            failure_path, study_id=study_id, source_commit=expected_head,
            attempt=attempt, intent_sha256=intent["intent_sha256"],
            jobs=failure_jobs,
        )
        raise
    return 0


def run_submit(args) -> int:
    """Create an intent before direct qsub, then publish one submission receipt."""
    repo_root = _repo_root().resolve(strict=True)
    study_id = args.study_id
    policy, _policy_sha = _load_policy_for_study(study_id)
    _require_policy_ready_for_execution(policy)
    _assert_submit_a1_noncertifying_markers(policy)
    if args.expected_head != _run_git(repo_root, "rev-parse", "HEAD"):
        raise PaperStoryError("current HEAD differs from expected HEAD")
    if _parent_porcelain(repo_root, policy):
        raise PaperStoryError("working tree is dirty")
    _assert_ccbench_acceptance(repo_root, policy, boundary="login-submit")
    base = _durable_measurement_base(policy)
    attempt = _validate_attempt_root(Path(args.attempt_root), base)
    base.mkdir(parents=True, exist_ok=True)
    if _policy_study_id(policy) in a1_source.CONTRACTS:
        source_contract = a1_source.load_contract(repo_root, _policy_study_id(policy))
        if _policy_study_id(policy) == V3_PILOT_STUDY_ID and attempt.name != source_contract["attempt"]:
            raise PaperStoryError("new pilot submission requires source amendment attempt-0004")
        supplied = getattr(args, "third_party_source_root", None)
        if supplied is None or not Path(supplied).is_dir():
            raise PaperStoryError("hydrated third-party source root is unavailable")
    if _policy_schema(policy) == POLICY_SCHEMA_V3:
        return _run_submit_v3(
            repo_root=repo_root, policy=policy,
            expected_head=args.expected_head, attempt=attempt,
            third_party_source_root=getattr(args, "third_party_source_root", None),
        )
    evidence = _attempt_evidence_paths(attempt)
    intent_path = _attempt_intent_path(attempt)
    submission_path = Path(evidence["submission_receipt"])
    submission_staging_path = _receipt_staging_path(
        submission_path, receipt_kind="submission",
    )
    if os.path.lexists(submission_path):
        raise PaperStoryError("submission receipt already exists")
    if os.path.lexists(intent_path):
        raise PaperStoryError(
            "submission indeterminate: intent exists without submission receipt; "
            "qsub will not be repeated"
        )
    if os.path.lexists(attempt):
        raise PaperStoryError("submit attempt root must not already exist")
    if os.path.lexists(Path(evidence["completion_receipt"])):
        raise PaperStoryError("completion receipt already exists")
    if os.path.lexists(Path(evidence["stdout_path"])):
        raise PaperStoryError("stdout already exists")
    if os.path.lexists(Path(evidence["stderr_path"])):
        raise PaperStoryError("stderr already exists")
    if os.path.lexists(submission_staging_path):
        raise PaperStoryError("submission receipt staging already exists")
    argv, options = _canonical_qsub_contract(
        repo_root=repo_root,
        study_id=study_id,
        source_commit=args.expected_head,
        attempt=attempt,
    )
    intent = {
        "schema_version": SUBMISSION_INTENT_SCHEMA,
        "study_id": study_id,
        "source_commit": args.expected_head,
        "attempt_root": os.fspath(attempt),
        "qsub_argv": argv,
        "qsub_options": options,
        "source_binding": _non_certifying_source_binding(
            repo_root, args.expected_head, policy,
        ),
    }
    intent["intent_sha256"] = _submission_intent_digest(intent)
    _exclusive_write(intent_path, intent)
    _fsync_directory(intent_path.parent)
    completed = _run_qsub(argv, cwd=repo_root)
    if completed.returncode != 0 or completed.stderr != "":
        raise PaperStoryError(
            "qsub failed after durable intent; submission is indeterminate"
        )
    request_id = _parse_request_id(completed.stdout)
    visibility = _observe_qstat_visibility(request_id)
    receipt = {
        "schema_version": SUBMISSION_SCHEMA,
        "route": "direct-qsub",
        "study_id": study_id,
        "source_commit": args.expected_head,
        "attempt_root": os.fspath(attempt),
        "request_id": request_id,
        "submission_receipt_path": evidence["submission_receipt"],
        "completion_receipt_path": evidence["completion_receipt"],
        "qsub_argv": argv,
        "qsub_options": options,
        "submit_observation": {
            "submit_host": socket.gethostname(),
            "qsub_stdout": completed.stdout,
            "qsub_stdout_sha256": _sha256_bytes(completed.stdout.encode("utf-8")),
            "qsub_stderr": completed.stderr,
            "qsub_stderr_sha256": _sha256_bytes(completed.stderr.encode("utf-8")),
            "qstat_visibility": visibility,
        },
    }
    _publish_submission_receipt(submission_path, receipt)
    return 0


def _canonical_qsub_contract(
    *,
    repo_root: Path,
    study_id: str,
    source_commit: str,
    attempt: Path,
) -> tuple[list[str], dict[str, object]]:
    evidence = _attempt_evidence_paths(attempt)
    variables = {
        "IZANAGI_EXPECTED_HEAD": source_commit,
        "IZANAGI_A1_STUDY_ID": study_id,
        "IZANAGI_A1_ATTEMPT_ROOT": os.fspath(attempt),
        "IZANAGI_A1_ACQUISITION_RECEIPT": evidence["submission_receipt"],
        "IZANAGI_A1_COMPLETION_RECEIPT": evidence["completion_receipt"],
        "IZANAGI_SUBMISSION_NONCE": attempt.name,
    }
    variable_text = ",".join(f"{key}={value}" for key, value in variables.items())
    options = {
        "v": variable_text,
        "variables": variables,
        "o": evidence["stdout_path"],
        "e": evidence["stderr_path"],
    }
    argv = [
        "qsub",
        "-v",
        variable_text,
        "-o",
        evidence["stdout_path"],
        "-e",
        evidence["stderr_path"],
        os.fspath((repo_root / JOB_RELATIVE_PATH).resolve(strict=True)),
    ]
    return argv, options


def _pbs_environment_observation() -> dict[str, str]:
    observation = {
        "pbs_jobid": os.environ.get("PBS_JOBID"),
        "pbs_o_host": os.environ.get("PBS_O_HOST"),
        "pbs_o_workdir": os.environ.get("PBS_O_WORKDIR"),
    }
    if any(type(value) is not str or not value for value in observation.values()):
        raise PaperStoryError("PBS environment observation is incomplete")
    return observation


def _validate_pbs_observation(
    observation: object,
    *,
    receipt: Mapping[str, object],
    repo_root: Path,
    request_id: str,
) -> dict[str, str]:
    if type(observation) is not dict or set(observation) != _PBS_OBSERVATION_KEYS:
        raise PaperStoryError("PBS environment observation shape differs")
    if any(type(observation.get(key)) is not str for key in _PBS_OBSERVATION_KEYS):
        raise PaperStoryError("PBS environment observation values differ")
    submit = receipt.get("submit_observation")
    if (
        _validated_request_id(observation["pbs_jobid"], "PBS_JOBID")
        != _validated_request_id(request_id, "submission request ID")
        or observation.get("pbs_o_host")
        != (submit.get("submit_host") if type(submit) is dict else None)
        or observation.get("pbs_o_workdir") != os.fspath(repo_root)
    ):
        raise PaperStoryError("PBS environment observation does not cross-bind receipt")
    return dict(observation)


def _validate_v3_acquisition_receipt(
    receipt: object,
    *,
    repo_root: Path,
    policy: Mapping[str, object],
    source_commit: str,
    request_id: str,
    pbs_observation: Mapping[str, object],
    workload: str,
) -> dict[str, object]:
    if workload not in WORKLOAD_ORDER:
        raise PaperStoryError("v3 acquisition workload selector differs")
    base = _durable_measurement_base(policy)
    raw_attempt = receipt.get("attempt_root") if type(receipt) is dict else None
    if type(raw_attempt) is not str:
        raise PaperStoryError("group acquisition attempt root differs")
    attempt = _validate_attempt_root(Path(raw_attempt), base)
    validated = _validate_v3_group_submission(
        receipt,
        repo_root=repo_root.resolve(strict=True),
        policy=policy,
        source_commit=source_commit,
        attempt=attempt,
    )
    ordinal = WORKLOAD_ORDER.index(workload)
    job = validated["jobs"][ordinal]
    if _validated_request_id(
        job["request_id"], f"{workload} group request ID",
    ) != _validated_request_id(request_id, "PBS_JOBID"):
        raise PaperStoryError("group acquisition request ID differs from PBS_JOBID")
    synthetic = {
        "submit_observation": job["submit_observation"],
    }
    _validate_pbs_observation(
        pbs_observation,
        receipt=synthetic,
        repo_root=repo_root.resolve(strict=True),
        request_id=job["request_id"],
    )
    roots = _v3_job_roots(attempt, workload)
    if _is_within(attempt, repo_root.resolve(strict=True)) or _under_scr(attempt):
        raise PaperStoryError("group acquisition attempt root is not durable")
    return {
        **roots,
        "workload": workload,
        "ordinal": ordinal,
        "group_result_root": _v3_attempt_evidence_paths(attempt)["result_root"],
        "group_terminal": _v3_attempt_evidence_paths(attempt)["group_terminal"],
    }


def validate_acquisition_receipt(
    receipt: object,
    *,
    repo_root: Path,
    study_id: str,
    source_commit: str,
    request_id: str,
    pbs_observation: Mapping[str, object],
    policy: Mapping[str, object] | None = None,
    workload: str | None = None,
) -> dict[str, object]:
    policy = policy if policy is not None else load_policy()[0]
    if study_id != _policy_study_id(policy):
        raise PaperStoryError("acquisition study ID differs from policy")
    if _policy_schema(policy) == POLICY_SCHEMA_V3:
        if type(workload) is not str:
            raise PaperStoryError("v3 acquisition workload selector is required")
        return _validate_v3_acquisition_receipt(
            receipt,
            repo_root=repo_root,
            policy=policy,
            source_commit=source_commit,
            request_id=request_id,
            pbs_observation=pbs_observation,
            workload=workload,
        )
    if type(receipt) is not dict or set(receipt) != _SUBMISSION_RECEIPT_KEYS:
        raise PaperStoryError("submission receipt shape differs")
    if receipt.get("schema_version") != SUBMISSION_SCHEMA:
        raise PaperStoryError("submission receipt schema differs")
    if receipt.get("route") != "direct-qsub":
        raise PaperStoryError("acquisition route is not direct-qsub")
    if receipt.get("study_id") != study_id:
        raise PaperStoryError("acquisition study ID differs")
    if receipt.get("source_commit") != source_commit:
        raise PaperStoryError("acquisition source commit differs")
    receipt_request_id = receipt.get("request_id")
    if (
        _validated_request_id(receipt_request_id, "submission request ID")
        != _validated_request_id(request_id, "PBS_JOBID")
    ):
        raise PaperStoryError("acquisition request ID differs from PBS_JOBID")
    raw_attempt = receipt.get("attempt_root")
    if type(raw_attempt) is not str or not Path(raw_attempt).is_absolute():
        raise PaperStoryError("acquisition attempt root must be absolute")
    base = _durable_measurement_base(policy)
    attempt = _validate_attempt_root(Path(raw_attempt), base)
    repo = repo_root.resolve(strict=True)
    if _is_within(attempt, repo):
        raise PaperStoryError("acquisition attempt root must be outside the repository")
    if _under_scr(attempt):
        raise PaperStoryError("acquisition attempt root must not be under /scr")
    evidence = _attempt_evidence_paths(attempt)
    expected_argv, expected_options = _canonical_qsub_contract(
        repo_root=repo,
        study_id=study_id,
        source_commit=source_commit,
        attempt=attempt,
    )
    if receipt.get("submission_receipt_path") != evidence["submission_receipt"]:
        raise PaperStoryError("submission receipt durable path differs")
    if receipt.get("completion_receipt_path") != evidence["completion_receipt"]:
        raise PaperStoryError("completion receipt durable path differs")
    if receipt.get("qsub_argv") != expected_argv:
        raise PaperStoryError("canonical qsub argv differs")
    if receipt.get("qsub_options") != expected_options:
        raise PaperStoryError("canonical qsub -v/-o/-e options differ")
    observation = receipt.get("submit_observation")
    if type(observation) is not dict or set(observation) != {
        "submit_host",
        "qsub_stdout",
        "qsub_stdout_sha256",
        "qsub_stderr",
        "qsub_stderr_sha256",
        "qstat_visibility",
    }:
        raise PaperStoryError("submission observation shape differs")
    submit_host = observation.get("submit_host")
    if (
        type(submit_host) is not str
        or not submit_host
        or any(ord(character) < 0x20 for character in submit_host)
    ):
        raise PaperStoryError("submission host observation is invalid")
    qsub_stdout = observation.get("qsub_stdout")
    qsub_stderr = observation.get("qsub_stderr")
    if qsub_stderr != "":
        raise PaperStoryError("qsub stdout/stderr observation differs")
    parsed_request_id = _parse_request_id(qsub_stdout)
    if (
        _validated_request_id(parsed_request_id, "parsed qsub request ID")
        != _validated_request_id(receipt_request_id, "submission request ID")
    ):
        raise PaperStoryError("qsub stdout request ID differs")
    if (
        observation.get("qsub_stdout_sha256")
        != _sha256_bytes(qsub_stdout.encode("utf-8"))
        or observation.get("qsub_stderr_sha256")
        != _sha256_bytes(qsub_stderr.encode("utf-8"))
    ):
        raise PaperStoryError("qsub stdout/stderr observation hash differs")
    visibility = observation.get("qstat_visibility")
    if type(visibility) is not dict or set(visibility) != {
        "request_id", "visible", "state", "queue", "observed_epoch",
    }:
        raise PaperStoryError("qstat visibility observation shape differs")
    if (
        visibility.get("visible") is not True
        or type(visibility.get("state")) is not str
        or visibility["state"] not in NQSV_QSTAT_STATES
        or visibility.get("queue") != _PBS_QUEUE
        or type(visibility.get("observed_epoch")) is not int
        or visibility["observed_epoch"] <= 0
    ):
        raise PaperStoryError("qstat did not visibly bind the submitted request")
    if (
        _validated_request_id(
            visibility.get("request_id"), "qstat visibility request ID"
        )
        != _validated_request_id(receipt_request_id, "submission request ID")
    ):
        raise PaperStoryError("qstat did not visibly bind the submitted request")
    _validate_pbs_observation(
        pbs_observation,
        receipt=receipt,
        repo_root=repo,
        request_id=request_id,
    )
    return {
        "attempt_root": os.fspath(attempt),
        "attempt_identity": _attempt_root_identity(attempt),
        "raw_root": os.fspath(attempt / "raw"),
        "output_root": os.fspath(attempt / "raw" / "campaign-output"),
        "cache_root": os.fspath(attempt / "cache"),
        "result_root": os.fspath(attempt / "raw" / "results"),
        "tmp_root": os.fspath(attempt / "raw" / "tmp"),
        **evidence,
    }


def _validate_prior_qstat_visibility(
    submission_receipt: object,
    *,
    request_id: str,
    terminal_observed_epoch: int,
) -> None:
    if type(submission_receipt) is not dict:
        raise PaperStoryError(
            "scheduler disappearance lacks prior submission visibility"
        )
    submit = submission_receipt.get("submit_observation")
    visibility = submit.get("qstat_visibility") if type(submit) is dict else None
    if (
        type(visibility) is not dict
        or set(visibility) != {
            "request_id", "visible", "state", "queue", "observed_epoch",
        }
        or visibility.get("visible") is not True
        or type(visibility.get("state")) is not str
        or visibility["state"] not in NQSV_QSTAT_STATES
        or visibility.get("queue") != _PBS_QUEUE
        or type(visibility.get("observed_epoch")) is not int
        or visibility["observed_epoch"] <= 0
        or visibility["observed_epoch"] >= terminal_observed_epoch
    ):
        raise PaperStoryError(
            "scheduler disappearance lacks prior submission visibility"
        )
    expected = _validated_request_id(request_id, "completion request ID")
    if (
        _validated_request_id(
            submission_receipt.get("request_id"), "submission request ID"
        ) != expected
        or _validated_request_id(
            visibility.get("request_id"), "qstat visibility request ID"
        ) != expected
    ):
        raise PaperStoryError(
            "scheduler disappearance lacks prior submission visibility"
        )


def validate_completion_receipt(
    receipt: object,
    *,
    trusted_roots: Mapping[str, str],
    source_commit: str,
    request_id: str,
    submission_receipt: Mapping[str, object],
    submission_receipt_sha256: str,
    job_terminal_sha256: str,
    study_id: str = STUDY_ID,
) -> dict:
    if type(receipt) is not dict or set(receipt) != {
        "schema_version",
        "study_id",
        "source_commit",
        "attempt_root",
        "request_id",
        "submission_receipt",
        "scheduler_terminal",
        "stdout",
        "stderr",
        "job_terminal",
    }:
        raise PaperStoryError("scheduler completion receipt shape differs")
    if (
        receipt.get("schema_version") != COMPLETION_SCHEMA
        or receipt.get("study_id") != study_id
        or receipt.get("source_commit") != source_commit
        or receipt.get("attempt_root") != trusted_roots.get("attempt_root")
    ):
        raise PaperStoryError("scheduler completion receipt identity differs")
    if (
        _validated_request_id(
            receipt.get("request_id"), "completion request ID"
        )
        != _validated_request_id(request_id, "job receipt PBS_JOBID")
    ):
        raise PaperStoryError("scheduler completion receipt identity differs")
    expected_bindings = {
        "submission_receipt": (
            trusted_roots.get("submission_receipt"), submission_receipt_sha256
        ),
        "stdout": (trusted_roots.get("stdout_path"), None),
        "stderr": (trusted_roots.get("stderr_path"), None),
        "job_terminal": (
            os.fspath(Path(trusted_roots["raw_root"]) / "job-terminal.json"),
            job_terminal_sha256,
        ),
    }
    for label, (expected_path, expected_sha) in expected_bindings.items():
        binding = receipt.get(label)
        if type(binding) is not dict or set(binding) != {"path", "sha256"}:
            raise PaperStoryError(f"scheduler completion {label} binding differs")
        path = binding.get("path")
        digest = binding.get("sha256")
        if path != expected_path or type(digest) is not str:
            raise PaperStoryError(f"scheduler completion {label} identity differs")
        try:
            observed_sha = _sha256_file(Path(path))
        except OSError as exc:
            raise PaperStoryError(
                f"scheduler completion {label} bytes are unreadable: {exc}"
            ) from exc
        if digest != observed_sha or (expected_sha is not None and digest != expected_sha):
            raise PaperStoryError(f"scheduler completion {label} hash differs")
    terminal = receipt.get("scheduler_terminal")
    if type(terminal) is not dict or set(terminal) != {
        "terminal_reason",
        "qstat_visible",
        "qstat_rc",
        "state",
        "exit_status",
        "observed_epoch",
        "qstat_stdout",
        "qstat_stdout_sha256",
    }:
        raise PaperStoryError("scheduler terminal observation shape differs")
    qstat_stdout = terminal.get("qstat_stdout")
    if (
        type(terminal.get("qstat_rc")) is not int
        or terminal.get("qstat_rc") != 0
        or type(terminal.get("observed_epoch")) is not int
        or terminal["observed_epoch"] <= 0
        or type(qstat_stdout) is not str
        or not qstat_stdout
        or terminal.get("qstat_stdout_sha256")
        != _sha256_bytes(qstat_stdout.encode("utf-8"))
    ):
        raise PaperStoryError("scheduler terminal observation is incomplete")
    terminal_reason = terminal.get("terminal_reason")
    state = terminal.get("state")
    exit_status = terminal.get("exit_status")
    if terminal_reason == "scheduler-end-state":
        parsed_request_id, parsed_state, parsed_exit_status = (
            _parse_qstat_terminal(qstat_stdout)
        )
        if (
            terminal.get("qstat_visible") is not True
            or type(state) is not dict
            or set(state) != {"observed", "value"}
            or state.get("observed") is not True
            or state.get("value") not in NQSV_QSTAT_TERMINAL_STATES
            or type(exit_status) is not dict
            or set(exit_status) != {"observed", "value"}
            or exit_status.get("observed") is not True
            or type(exit_status.get("value")) is not int
            or exit_status.get("value") != 0
            or parsed_request_id
            != _validated_request_id(
                receipt.get("request_id"), "completion request ID"
            )
            or parsed_state != state.get("value")
            or parsed_exit_status != exit_status.get("value")
        ):
            raise PaperStoryError("visible scheduler terminal observation differs")
    elif terminal_reason == "request-disappeared-after-visibility":
        if (
            terminal.get("qstat_visible") is not False
            or state != {"observed": False}
            or exit_status != {"observed": False}
            or not _is_target_nqsv_disappearance(qstat_stdout, request_id)
        ):
            raise PaperStoryError("disappeared scheduler terminal observation differs")
        _validate_prior_qstat_visibility(
            submission_receipt,
            request_id=request_id,
            terminal_observed_epoch=terminal["observed_epoch"],
        )
    else:
        raise PaperStoryError("scheduler terminal reason differs")
    return receipt


def _observe_scheduler_terminal(
    request_id: str, submission_receipt: Mapping[str, object],
) -> dict[str, object]:
    """Observe one scheduler terminal form through direct qstat."""
    completed = subprocess.run(
        ["qstat", "-f", _validated_request_id(request_id, "completion request ID")],
        text=True,
        capture_output=True,
        check=False,
    )
    stdout = completed.stdout
    if (
        completed.returncode != 0
        or completed.stderr != ""
        or not stdout
    ):
        raise PaperStoryError("scheduler terminal qstat observation failed")
    observed_epoch = int(time.time())
    if not _qstat_mentions_request(stdout, request_id):
        if not _is_target_nqsv_disappearance(stdout, request_id):
            raise PaperStoryError("scheduler terminal qstat observation failed")
        _validate_prior_qstat_visibility(
            submission_receipt,
            request_id=request_id,
            terminal_observed_epoch=observed_epoch,
        )
        return {
            "terminal_reason": "request-disappeared-after-visibility",
            "qstat_visible": False,
            "qstat_rc": completed.returncode,
            "state": {"observed": False},
            "exit_status": {"observed": False},
            "observed_epoch": observed_epoch,
            "qstat_stdout": stdout,
            "qstat_stdout_sha256": _sha256_bytes(stdout.encode("utf-8")),
        }
    parsed_request_id, state, exit_status = _parse_qstat_terminal(stdout)
    if (
        parsed_request_id
        != _validated_request_id(request_id, "completion request ID")
        or state not in NQSV_QSTAT_TERMINAL_STATES
    ):
        raise PaperStoryError("visible scheduler request is not terminal")
    return {
        "terminal_reason": "scheduler-end-state",
        "qstat_visible": True,
        "qstat_rc": completed.returncode,
        "state": {"observed": True, "value": state},
        "exit_status": {"observed": True, "value": exit_status},
        "observed_epoch": observed_epoch,
        "qstat_stdout": stdout,
        "qstat_stdout_sha256": _sha256_bytes(stdout.encode("utf-8")),
    }


def _validate_v3_workload_shard(
    shard: object,
    receipt: object,
    terminal: object,
    *,
    policy: Mapping[str, object],
    policy_sha: str,
    source_commit: str,
    attempt: Path,
    workload: str,
    ordinal: int,
    submission: Mapping[str, object],
    result_path: Path,
    receipt_path: Path,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    if type(shard) is not dict or set(shard) != {
        "schema_version", "study_id", "workload", "ordinal", "campaign_id",
        "campaign_ids", "common_record", "source_binding",
        "non_certifying_source_binding", "reservation_binding",
        "workload_result",
    }:
        raise PaperStoryError("workload shard shape differs")
    if type(receipt) is not dict or set(receipt) != {
        "schema_version", "study_id", "workload", "ordinal", "pbs_jobid",
        "host", "recorded_epoch", "policy", "source_binding",
        "submission_receipt", "roots", "result", "calibration_sha256",
    }:
        raise PaperStoryError("workload receipt shape differs")
    terminal_keys = {
        "schema_version", "study_id", "workload", "ordinal", "pbs_jobid",
        "expected_head", "observed_head", "porcelain", "driver_rc",
        "shell_rc", "status", "result_sha256", "receipt_sha256",
        "submission_receipt_sha256", "completion_receipt_path",
        "pbs_observation", "reservation_binding", "accounting",
        "attempt_identity", "terminal_source_binding", "recorded_epoch",
    }
    if type(terminal) is not dict or set(terminal) != terminal_keys:
        raise PaperStoryError("workload job terminal shape differs")
    study_id = _policy_study_id(policy)
    if any(document.get("study_id") != study_id for document in (
        shard, receipt, terminal,
    )):
        raise PaperStoryError("workload shard study ID differs")
    if any(document.get("workload") != workload for document in (
        shard, receipt, terminal,
    )) or any(document.get("ordinal") != ordinal for document in (
        shard, receipt, terminal,
    )):
        raise PaperStoryError("workload shard ordinal differs")
    jobs = submission.get("jobs")
    job = jobs[ordinal] if type(jobs) is list and len(jobs) == 3 else None
    if type(job) is not dict:
        raise PaperStoryError("workload submission entry is missing")
    request_id = _validated_request_id(
        job.get("request_id"), f"{workload} submission request ID",
    )
    for candidate, label in (
        (receipt.get("pbs_jobid"), "receipt"),
        (terminal.get("pbs_jobid"), "terminal"),
    ):
        if _validated_request_id(candidate, f"{workload} {label} request ID") != request_id:
            raise PaperStoryError("workload request ID cross-binding differs")
    reservation = _validate_reservation_binding_document(
        terminal.get("reservation_binding")
    )
    if (
        shard.get("reservation_binding") != reservation
        or _validated_request_id(
            reservation["job_id"], f"{workload} reservation request ID",
        ) != request_id
        or reservation["nonce"] != f"{attempt.name}.{workload}"
    ):
        raise PaperStoryError("workload reservation binding differs")
    accounting = _validate_v3_accounting(terminal.get("accounting"))
    roots = _v3_job_roots(attempt, workload)
    if receipt.get("roots") != {
        **roots,
        "workload": workload,
        "ordinal": ordinal,
        "group_result_root": _v3_attempt_evidence_paths(attempt)["result_root"],
        "group_terminal": _v3_attempt_evidence_paths(attempt)["group_terminal"],
    }:
        raise PaperStoryError("workload receipt roots differ")
    submission_raw = _read_bytes_once(Path(roots["submission_receipt"]))
    if (
        receipt.get("submission_receipt") != {
            "path": roots["submission_receipt"],
            "sha256": _sha256_bytes(submission_raw),
        }
        or terminal.get("submission_receipt_sha256")
        != _sha256_bytes(submission_raw)
    ):
        raise PaperStoryError("workload group receipt binding differs")
    if (
        receipt.get("policy") != {
            "path": _policy_relative_path(policy), "sha256": policy_sha,
        }
        or receipt.get("source_binding") != shard.get("source_binding")
        or not _validate_source_binding(shard.get("source_binding"), policy)
        or not _validate_non_certifying_source_binding(
            shard.get("non_certifying_source_binding"), policy,
        )
        or terminal.get("terminal_source_binding") != shard.get("source_binding")
    ):
        raise PaperStoryError("workload source/policy binding differs")
    if (
        terminal.get("expected_head") != source_commit
        or terminal.get("observed_head") != source_commit
        or terminal.get("porcelain") != ""
        or terminal.get("driver_rc") != 0
        or terminal.get("shell_rc") != 0
        or terminal.get("status") != "finished"
        or terminal.get("attempt_identity") != _attempt_root_identity(attempt)
        or terminal.get("completion_receipt_path")
        != _v3_attempt_evidence_paths(attempt)["completion_receipt"]
    ):
        raise PaperStoryError("workload job did not finish cleanly")
    if (
        terminal.get("result_sha256") != _sha256_file(result_path)
        or terminal.get("receipt_sha256") != _sha256_file(receipt_path)
        or receipt.get("result") != {
            "path": os.fspath(result_path),
            "sha256": _sha256_file(result_path),
        }
    ):
        raise PaperStoryError("workload shard byte binding differs")
    pbs = terminal.get("pbs_observation")
    if (
        type(pbs) is not dict
        or set(pbs) != _PBS_OBSERVATION_KEYS
        or _validated_request_id(
            pbs.get("pbs_jobid"), f"{workload} PBS observation request ID",
        ) != request_id
        or pbs.get("pbs_o_workdir") != os.fspath(_repo_root().resolve(strict=True))
        or pbs.get("pbs_o_host")
        != job.get("submit_observation", {}).get("submit_host")
    ):
        raise PaperStoryError("workload PBS observation differs")
    common = shard.get("common_record")
    if (
        type(common) is not dict
        or shard.get("campaign_ids") != common.get("campaign_ids")
    ):
        raise PaperStoryError("workload campaign triple differs")
    workload_result = shard.get("workload_result")
    if (
        type(shard.get("campaign_ids")) is not list
        or len(shard["campaign_ids"]) != 3
        or len(set(shard["campaign_ids"])) != 3
        or shard.get("campaign_id") != shard["campaign_ids"][ordinal]
        or type(workload_result) is not dict
        or workload_result.get("workload") != workload
        or workload_result.get("campaign_id")
        != shard.get("campaign_id")
        or not _workload_has_terminal_result(workload_result)
    ):
        raise PaperStoryError("workload shard campaign binding differs")
    return dict(shard), dict(receipt), {
        **terminal, "reservation_binding": reservation, "accounting": accounting,
    }


def _validate_v3_barrier_for_completion(
    *,
    attempt: Path,
    policy: Mapping[str, object],
    source_commit: str,
    submission: Mapping[str, object],
    campaign_ids: Sequence[str],
) -> None:
    ready_bindings = []
    for ordinal, workload in enumerate(WORKLOAD_ORDER):
        roots = _v3_job_roots(attempt, workload)
        ready_path = Path(roots["ready"])
        ready_raw = _read_bytes_once(ready_path)
        ready = _validate_v3_ready_document(
            _decode_json_bytes(ready_raw, f"{workload} ready evidence"),
            workload=workload, ordinal=ordinal,
            study_id=_policy_study_id(policy), source_commit=source_commit,
            attempt=attempt, submission=submission,
        )
        if ready.get("campaign_id") != campaign_ids[ordinal]:
            raise PaperStoryError("ready campaign ordinal differs")
        ready_bindings.append({
            "workload": workload, "ordinal": ordinal,
            "campaign_id": campaign_ids[ordinal], "path": os.fspath(ready_path),
            "sha256": _sha256_bytes(ready_raw),
        })
    bench_go_path = Path(_v3_job_roots(attempt, WORKLOAD_ORDER[0])["bench_go"])
    bench_go_raw = _read_bytes_once(bench_go_path)
    bench_go = _decode_json_bytes(bench_go_raw, "bench-go evidence")
    if bench_go != {
        "schema_version": V3_BENCH_GO_SCHEMA,
        "study_id": _policy_study_id(policy),
        "source_commit": source_commit,
        "attempt_root": os.fspath(attempt),
        "ready": ready_bindings,
    }:
        raise PaperStoryError("bench-go does not bind the exact ready triple")
    for ordinal, workload in enumerate(WORKLOAD_ORDER):
        start_path = Path(_v3_job_roots(attempt, workload)["bench_start"])
        start = _read_json(start_path)
        job = submission["jobs"][ordinal]
        if (
            set(start) != {
                "schema_version", "study_id", "source_commit", "attempt_root",
                "workload", "ordinal", "request_id", "bench_go_sha256",
                "ready_sha256", "recorded_epoch",
            }
            or start.get("schema_version") != V3_BENCH_START_SCHEMA
            or start.get("study_id") != _policy_study_id(policy)
            or start.get("source_commit") != source_commit
            or start.get("attempt_root") != os.fspath(attempt)
            or start.get("workload") != workload
            or start.get("ordinal") != ordinal
            or _validated_request_id(
                start.get("request_id"), f"{workload} bench-start request ID",
            ) != _validated_request_id(
                job.get("request_id"), f"{workload} submission request ID",
            )
            or start.get("bench_go_sha256") != _sha256_bytes(bench_go_raw)
            or start.get("ready_sha256") != ready_bindings[ordinal]["sha256"]
        ):
            raise PaperStoryError("bench-start evidence differs")


def _run_complete_v3(
    args,
    *,
    repo_root: Path,
    policy: Mapping[str, object],
    policy_sha: str,
    attempt: Path,
) -> int:
    study_id = _policy_study_id(policy)
    evidence = _v3_attempt_evidence_paths(attempt)
    submission_path = Path(evidence["submission_receipt"])
    submission_raw = _read_bytes_once(submission_path)
    submission = _validate_v3_group_submission(
        _decode_json_bytes(submission_raw, "group submission receipt"),
        repo_root=repo_root, policy=policy, source_commit=args.expected_head,
        attempt=attempt,
    )
    intent_raw = _read_bytes_once(_attempt_intent_path(attempt))
    intent = _validate_submission_intent(
        _decode_json_bytes(intent_raw, "group submission intent"),
        repo_root=repo_root, source_commit=args.expected_head,
        attempt=attempt, policy=policy,
    )
    if submission.get("intent_sha256") != intent.get("intent_sha256"):
        raise PaperStoryError("group submission differs from create-only intent")
    shards = []
    terminals = []
    completion_jobs = []
    executions = []
    common_record = None
    campaign_ids = None
    for ordinal, workload in enumerate(WORKLOAD_ORDER):
        roots = _v3_job_roots(attempt, workload)
        result_path = Path(roots["result_root"]) / "result.json"
        receipt_path = Path(roots["result_root"]) / "receipt.json"
        terminal_path = Path(roots["job_terminal"])
        result_raw = _read_bytes_once(result_path)
        receipt_raw = _read_bytes_once(receipt_path)
        terminal_raw = _read_bytes_once(terminal_path)
        shard, _shard_receipt, terminal = _validate_v3_workload_shard(
            _decode_json_bytes(result_raw, f"{workload} shard result"),
            _decode_json_bytes(receipt_raw, f"{workload} shard receipt"),
            _decode_json_bytes(terminal_raw, f"{workload} job terminal"),
            policy=policy, policy_sha=policy_sha,
            source_commit=args.expected_head, attempt=attempt,
            workload=workload, ordinal=ordinal, submission=submission,
            result_path=result_path, receipt_path=receipt_path,
        )
        if common_record is None:
            common_record = shard["common_record"]
            campaign_ids = shard["campaign_ids"]
        elif (
            shard["common_record"] != common_record
            or shard["campaign_ids"] != campaign_ids
            or shard["source_binding"] != shards[0]["source_binding"]
            or shard["non_certifying_source_binding"]
            != shards[0]["non_certifying_source_binding"]
        ):
            raise PaperStoryError("workload shard common projection differs")
        scheduler_terminal = _observe_scheduler_terminal(
            submission["jobs"][ordinal]["request_id"], submission["jobs"][ordinal],
        )
        if scheduler_terminal.get("terminal_reason") == "scheduler-end-state":
            if scheduler_terminal.get("exit_status") != {"observed": True, "value": 0}:
                raise PaperStoryError("workload scheduler exit status differs")
        bindings = {}
        for label, path in (
            ("stdout", Path(roots["stdout_path"])),
            ("stderr", Path(roots["stderr_path"])),
            ("job_terminal", terminal_path),
        ):
            raw = _read_bytes_once(path)
            bindings[label] = {"path": os.fspath(path), "sha256": _sha256_bytes(raw)}
        completion_jobs.append({
            "workload": workload, "ordinal": ordinal,
            "request_id": submission["jobs"][ordinal]["request_id"],
            "scheduler_terminal": scheduler_terminal,
            **bindings,
        })
        executions.append({
            "workload": workload, "ordinal": ordinal,
            "request_id": submission["jobs"][ordinal]["request_id"],
            "reservation_binding": terminal["reservation_binding"],
            "accounting": terminal["accounting"],
        })
        shards.append(shard)
        terminals.append(terminal)
    _validate_v3_barrier_for_completion(
        attempt=attempt, policy=policy, source_commit=args.expected_head,
        submission=submission, campaign_ids=campaign_ids,
    )
    workloads = [shard["workload_result"] for shard in shards]
    result = assemble_result(
        policy, policy_sha256=policy_sha,
        source_binding=shards[0]["source_binding"],
        job_executions=executions, workloads=workloads,
    )
    group_roots = {
        "attempt_root": os.fspath(attempt),
        "attempt_identity": _attempt_root_identity(attempt),
        "raw_root": os.fspath(attempt / "raw"),
        "result_root": evidence["result_root"],
        "submission_receipt": evidence["submission_receipt"],
        "completion_receipt": evidence["completion_receipt"],
        "group_terminal": evidence["group_terminal"],
        "job_roots": [
            _v3_job_roots(attempt, workload) for workload in WORKLOAD_ORDER
        ],
    }
    result_root = Path(evidence["result_root"])
    result_root.mkdir(mode=0o700)
    _fsync_directory(result_root.parent)
    result_path = result_root / "result.json"
    _exclusive_write(result_path, result)
    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "study_id": study_id,
        "formal": False,
        "promotion_prohibited": True,
        "route": "direct-qsub-workload-fanout",
        "recorded_epoch": int(time.time()),
        "policy": {"path": _policy_relative_path(policy), "sha256": policy_sha},
        "source_binding": shards[0]["source_binding"],
        "submission_receipt": {
            "path": evidence["submission_receipt"],
            "sha256": _sha256_bytes(submission_raw),
        },
        "scheduler_completion_receipt": {
            "path": evidence["completion_receipt"],
        },
        "roots": group_roots,
        "result": {
            "path": os.fspath(result_path), "sha256": _sha256_file(result_path),
            "complete": result["complete"],
            "all_workloads_terminal": result["all_workloads_terminal"],
        },
        "job_executions": executions,
    }
    receipt_path = result_root / "receipt.json"
    _exclusive_write(receipt_path, receipt)
    sidecar_path = _issue_non_certifying_observation(
        common_record=common_record,
        source_binding=shards[0]["non_certifying_source_binding"],
        workloads=workloads,
        result_path=result_path,
        receipt_path=receipt_path,
    )
    _validate_non_certifying_observation_contents(sidecar_path)
    group_terminal = {
        "schema_version": V3_GROUP_TERMINAL_SCHEMA,
        "study_id": study_id,
        "source_commit": args.expected_head,
        "attempt_root": os.fspath(attempt),
        "jobs": [
            {
                "workload": workload, "ordinal": ordinal,
                "request_id": executions[ordinal]["request_id"],
                "path": _v3_job_roots(attempt, workload)["job_terminal"],
                "sha256": _sha256_file(Path(
                    _v3_job_roots(attempt, workload)["job_terminal"]
                )),
                "result": {
                    "path": os.fspath(Path(
                        _v3_job_roots(attempt, workload)["result_root"]
                    ) / "result.json"),
                    "sha256": terminals[ordinal]["result_sha256"],
                },
                "receipt": {
                    "path": os.fspath(Path(
                        _v3_job_roots(attempt, workload)["result_root"]
                    ) / "receipt.json"),
                    "sha256": terminals[ordinal]["receipt_sha256"],
                },
            }
            for ordinal, workload in enumerate(WORKLOAD_ORDER)
        ],
    }
    group_terminal_path = Path(evidence["group_terminal"])
    _exclusive_write(group_terminal_path, group_terminal)
    _fsync_directory(group_terminal_path.parent)
    completion = {
        "schema_version": V3_GROUP_COMPLETION_SCHEMA,
        "study_id": study_id,
        "source_commit": args.expected_head,
        "attempt_root": os.fspath(attempt),
        "submission_receipt": {
            "path": evidence["submission_receipt"],
            "sha256": _sha256_bytes(submission_raw),
        },
        "group_terminal": {
            "path": evidence["group_terminal"],
            "sha256": _sha256_file(group_terminal_path),
        },
        "jobs": completion_jobs,
    }
    completion_path = Path(evidence["completion_receipt"])
    _publish_completion_receipt(completion_path, completion)
    return 0


def run_complete(args) -> int:
    """Publish only the one-shot scheduler completion receipt."""
    repo_root = _repo_root().resolve(strict=True)
    study_id = getattr(args, "study_id", STUDY_ID)
    policy, _policy_sha = _load_policy_for_study(study_id)
    _require_policy_ready_for_execution(policy)
    attempt = _validate_attempt_root(
        Path(args.attempt_root), _durable_measurement_base(policy),
    )
    if _policy_schema(policy) == POLICY_SCHEMA_V3:
        return _run_complete_v3(
            args, repo_root=repo_root, policy=policy, policy_sha=_policy_sha,
            attempt=attempt,
        )
    evidence = _attempt_evidence_paths(attempt)
    submission_path = Path(evidence["submission_receipt"])
    submission_raw = _read_bytes_once(submission_path)
    if submission_raw is None:  # pragma: no cover
        raise PaperStoryError("submission receipt is missing")
    submission = _decode_json_bytes(submission_raw, "submission receipt")
    intent_raw = _read_bytes_once(_attempt_intent_path(attempt))
    if intent_raw is None:  # pragma: no cover
        raise PaperStoryError("submission intent is missing")
    intent = _validate_submission_intent(
        _decode_json_bytes(intent_raw, "submission intent"),
        repo_root=repo_root,
        source_commit=args.expected_head,
        attempt=attempt,
        policy=policy,
    )
    if (
        type(submission) is not dict
        or set(submission) != _SUBMISSION_RECEIPT_KEYS
        or submission.get("schema_version") != SUBMISSION_SCHEMA
        or submission.get("route") != "direct-qsub"
        or submission.get("study_id") != study_id
        or submission.get("source_commit") != args.expected_head
        or submission.get("attempt_root") != os.fspath(attempt)
        or submission.get("submission_receipt_path")
        != evidence["submission_receipt"]
        or submission.get("completion_receipt_path")
        != evidence["completion_receipt"]
        or submission.get("qsub_argv") != intent["qsub_argv"]
        or submission.get("qsub_options") != intent["qsub_options"]
    ):
        raise PaperStoryError("submission receipt differs from its intent")
    request_id = submission.get("request_id")
    _validate_raw_non_certifying_observation_for_completion(
        attempt / "raw" / "results" / NON_CERTIFYING_OBSERVATION_FILENAME,
        expected_head=args.expected_head,
        attempt=attempt,
        request_id=request_id,
    )
    scheduler_terminal = _observe_scheduler_terminal(request_id, submission)
    terminal_path = attempt / "raw" / "job-terminal.json"
    required = {
        "stdout": Path(evidence["stdout_path"]),
        "stderr": Path(evidence["stderr_path"]),
        "job_terminal": terminal_path,
    }
    bindings = {}
    for label, path in required.items():
        raw = _read_bytes_once(path)
        if raw is None:  # pragma: no cover
            raise PaperStoryError(f"completion input is missing: {label}")
        bindings[label] = {
            "path": os.fspath(path),
            "sha256": _sha256_bytes(raw),
        }
    completion = {
        "schema_version": COMPLETION_SCHEMA,
        "study_id": study_id,
        "source_commit": args.expected_head,
        "attempt_root": os.fspath(attempt),
        "request_id": request_id,
        "submission_receipt": {
            "path": os.fspath(submission_path),
            "sha256": _sha256_bytes(submission_raw),
        },
        "scheduler_terminal": scheduler_terminal,
        "stdout": bindings["stdout"],
        "stderr": bindings["stderr"],
        "job_terminal": bindings["job_terminal"],
    }
    completion_path = Path(evidence["completion_receipt"])
    _publish_completion_receipt(completion_path, completion)
    return 0


def validate_measure_environment(
    *,
    repo_root: Path,
    expected_head: str,
    output_root: Path,
    cache_root: Path,
    result_root: Path,
    pbs_jobid: str,
    site: str,
    observed_head: str,
    porcelain: str,
    attempt_root: Path | None = None,
    workload: str | None = None,
) -> dict[str, str]:
    """Pure fail-closed gate shared by the CLI and negative contract tests."""
    if site != site_policy.PEGASUS_COMPUTE:
        raise PaperStoryError("measure mode requires Pegasus compute")
    if not _FULL_OID.fullmatch(expected_head):
        raise PaperStoryError("expected HEAD must be one full lowercase OID")
    if observed_head != expected_head:
        raise PaperStoryError("current HEAD differs from expected HEAD")
    if porcelain:
        raise PaperStoryError("working tree is dirty")
    if not _PBS_JOBID.fullmatch(pbs_jobid):
        raise PaperStoryError("PBS_JOBID is missing or unsafe")
    resolved_repo = repo_root.resolve(strict=True)
    roots: dict[str, str] = {}
    for label, raw in (
        ("output_root", output_root),
        ("cache_root", cache_root),
        ("result_root", result_root),
    ):
        if not raw.is_absolute():
            raise PaperStoryError(f"{label} must be absolute")
        resolved = raw.resolve(strict=False)
        if _is_within(resolved, resolved_repo):
            raise PaperStoryError(f"{label} must be outside the repository")
        if os.path.lexists(raw) or os.path.lexists(resolved):
            raise PaperStoryError(f"{label} must not already exist")
        roots[label] = os.fspath(resolved)
    resolved_roots = [Path(value) for value in roots.values()]
    if len(set(roots.values())) != 3:
        raise PaperStoryError("output/cache/result roots must be distinct")
    for index, left in enumerate(resolved_roots):
        for right in resolved_roots[index + 1:]:
            if _paths_overlap(left, right):
                raise PaperStoryError("output/cache/result roots must not overlap")
    if any(_under_scr(item) for item in resolved_roots):
        raise PaperStoryError("measurement roots must not be under /scr")
    if attempt_root is not None:
        attempt = attempt_root.resolve(strict=False)
        if workload is None:
            expected = {
                "output_root": attempt / "raw" / "campaign-output",
                "cache_root": attempt / "cache",
                "result_root": attempt / "raw" / "results",
            }
        else:
            if workload not in WORKLOAD_ORDER:
                raise PaperStoryError("measurement workload selector differs")
            job_root = attempt / "jobs" / workload
            expected = {
                "output_root": job_root / "raw" / "campaign-output",
                "cache_root": job_root / "cache",
                "result_root": job_root / "raw" / "results",
            }
        if any(Path(roots[key]) != value for key, value in expected.items()):
            raise PaperStoryError("measurement roots differ from fixed attempt topology")
    return roots


def _source_binding_for_paths(
    repo_root: Path,
    expected_head: str,
    relative_paths: Sequence[str],
) -> dict:
    if _run_git(repo_root, "rev-parse", "HEAD") != expected_head:
        raise PaperStoryError("source HEAD moved before source binding")
    files = {}
    for relative in relative_paths:
        oid = _run_git(repo_root, "rev-parse", f"{expected_head}:{relative}")
        if not _FULL_OID.fullmatch(oid):
            raise PaperStoryError(f"source git blob OID is invalid: {relative}")
        working_sha = _sha256_file(repo_root / relative)
        if not _FULL_SHA256.fullmatch(working_sha):
            raise PaperStoryError(f"working source SHA-256 is invalid: {relative}")
        files[relative] = {
            "git_blob_oid": oid,
            "working_sha256": working_sha,
        }
    binding = {
        "measurement_source_commit": expected_head,
        "files": files,
        "evidence_level": "source-routed-trace0",
        "artifact_standalone_proof": False,
    }
    return binding


def _source_binding(
    repo_root: Path, expected_head: str,
    policy: Mapping[str, object] | None = None,
) -> dict:
    relative_paths = (
        SOURCE_RELATIVE_PATHS
        if policy is None else _source_relative_paths(policy, non_certifying=False)
    )
    return _source_binding_for_paths(
        repo_root, expected_head, relative_paths,
    )


def _non_certifying_source_binding(
    repo_root: Path, expected_head: str,
    policy: Mapping[str, object] | None = None,
) -> dict:
    relative_paths = (
        NON_CERTIFYING_SOURCE_RELATIVE_PATHS
        if policy is None else _source_relative_paths(policy, non_certifying=True)
    )
    return _source_binding_for_paths(
        repo_root, expected_head, relative_paths,
    )


def _classify_difference(mean: float, half_width: float, boundary: float) -> str:
    if not all(_finite_number(value) for value in (mean, half_width, boundary)):
        raise PaperStoryError("classification input is not finite")
    if half_width < 0 or boundary < 0:
        raise PaperStoryError("classification width or boundary is negative")
    if abs(mean) - half_width > boundary:
        return "resolved-above-floor"
    if abs(mean) + half_width <= boundary:
        return "bounded-below-floor"
    return "unresolved"


def positional_statistics(
    policy: Mapping[str, object],
    workload_name: str,
    baseline: Sequence[object],
    variant: Sequence[object],
) -> dict:
    """Producer-side signed contrast; the artifact consumer does not call it."""
    expected_reps = _expected_reps(policy, workload_name)
    baseline_arm = _workload_arm_by_role(policy, workload_name, "baseline")
    variant_arm = _workload_arm_by_role(policy, workload_name, "variant")
    for label, values in (
        (baseline_arm["name"], baseline), (variant_arm["name"], variant),
    ):
        if type(values) is not list or len(values) != expected_reps:
            raise PaperStoryError(f"{label} length differs from workload policy reps")
        if any(not _finite_number(value) or value <= 0 for value in values):
            raise PaperStoryError(f"{label} contains a non-positive finite-number violation")
    pair_indices = _pair_indices(policy, workload_name)
    differences = [
        float(variant[index]) - float(baseline[index])
        for index in pair_indices
    ]
    return _statistics_from_signed_differences(
        policy,
        workload_name,
        baseline,
        variant,
        differences,
    )


def _consumer_positional_statistics(
    policy: Mapping[str, object],
    workload_name: str,
    arm_tps: Mapping[str, Sequence[object]],
) -> dict:
    """Independently recompute variant-minus-baseline from artifact arm roles."""
    expected_reps = _expected_reps(policy, workload_name)
    baseline_arm = _workload_arm_by_role(policy, workload_name, "baseline")
    variant_arm = _workload_arm_by_role(policy, workload_name, "variant")
    baseline = arm_tps.get(str(baseline_arm["name"]))
    variant = arm_tps.get(str(variant_arm["name"]))
    for label, values in (
        (baseline_arm["name"], baseline), (variant_arm["name"], variant),
    ):
        if type(values) is not list or len(values) != expected_reps:
            raise PaperStoryError(
                f"artifact consumer {label} length differs from policy reps"
            )
        if any(not _finite_number(value) or value <= 0 for value in values):
            raise PaperStoryError(
                f"artifact consumer {label} contains invalid throughput"
            )
    pair_indices = _pair_indices(policy, workload_name)
    differences = [
        float(variant[index]) - float(baseline[index])
        for index in pair_indices
    ]
    return _statistics_from_signed_differences(
        policy,
        workload_name,
        baseline,
        variant,
        differences,
    )


def _statistics_from_signed_differences(
    policy: Mapping[str, object],
    workload_name: str,
    baseline: Sequence[object],
    variant: Sequence[object],
    differences: Sequence[float],
) -> dict:
    expected_reps = _expected_reps(policy, workload_name)
    pair_indices = _pair_indices(policy, workload_name)
    baseline_arm = _workload_arm_by_role(policy, workload_name, "baseline")
    variant_arm = _workload_arm_by_role(policy, workload_name, "variant")
    mean = statistics.fmean(differences)
    variance = (
        sum((value - mean) ** 2 for value in differences)
        / (expected_reps - 1)
    )
    sample_sd = math.sqrt(variance)
    baseline_mean = statistics.fmean(float(value) for value in baseline)
    workload = _workload_plan(policy, workload_name)
    is_v2 = _policy_schema(policy) == POLICY_SCHEMA_V2
    floor_fraction = (
        policy["statistics"]["floor"]["floor_fraction"]
        if is_v2 else 0.03
    )
    boundary = float(floor_fraction) * baseline_mean
    result = {
        "pairing_design": _pairing_design(policy),
        "contrast": (
            "static10-minus-adaptive" if is_v2 else "variant-minus-baseline"
        ),
        "n": expected_reps,
        "df": expected_reps - 1,
        "pairs": [
            {
                "pair_index": index,
                f"{baseline_arm['name']}_tps": float(baseline[index]),
                f"{variant_arm['name']}_tps": float(variant[index]),
                "signed_difference_tps": differences[index],
            }
            for index in pair_indices
        ],
        "mean_signed_positional_difference_tps": mean,
        "sample_sd_positional_difference_tps": sample_sd,
        "sample_variance_positional_difference_tps2": variance,
        (
            "adaptive_mean_tps" if is_v2 else "baseline_mean_tps"
        ): baseline_mean,
        "floor_fraction": float(floor_fraction),
        "floor_boundary_tps": boundary,
    }
    if not is_v2 and policy.get("final_estimate_eligible") is False:
        result.update({
            "classification": "pilot-sizing-input-only",
            "final_estimate_eligible": False,
        })
        return result
    k = float(workload["k"])
    half_width = k * sample_sd / math.sqrt(expected_reps)
    result.update({
        "k": k,
        "descriptive_half_width_tps": half_width,
        "descriptive_interval_tps": [mean - half_width, mean + half_width],
        "classification": _classify_difference(mean, half_width, boundary),
        "planned_sigma_tps": float(workload["planned_sigma_tps"]),
        "variance_plan_breach": sample_sd > float(workload["planned_sigma_tps"]),
    })
    return result


def _finite_number(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, ValueError):
        return False


def _numbers_equal(left: object, right: object) -> bool:
    return (
        _finite_number(left)
        and _finite_number(right)
        and float(left) == float(right)
    )


def _command_argv(value: object) -> list[str] | None:
    if isinstance(value, str):
        try:
            argv = shlex.split(value)
        except ValueError:
            return None
    elif (
        isinstance(value, list)
        and all(type(item) is str for item in value)
    ):
        argv = list(value)
    else:
        return None
    return argv if argv else None


def _frame_payload(frame: Mapping[str, object]) -> dict:
    payload = frame.get("payload")
    return payload if type(payload) is dict else {}


def _frame_ref(frame: Mapping[str, object]) -> dict:
    return {
        "line_number": _json_safe(frame.get("line_number")),
        "byte_start": _json_safe(frame.get("byte_start")),
        "byte_end": _json_safe(frame.get("byte_end")),
        "raw_sha256": _json_safe(frame.get("raw_sha256")),
        "stage": _json_safe(frame.get("stage")),
    }


def _valid_physical_frame(frame: Mapping[str, object]) -> bool:
    return (
        type(frame.get("line_number")) is int
        and frame["line_number"] > 0
        and type(frame.get("byte_start")) is int
        and frame["byte_start"] >= 0
        and type(frame.get("byte_end")) is int
        and frame["byte_end"] > frame["byte_start"]
        and type(frame.get("raw_sha256")) is str
        and _FULL_SHA256.fullmatch(frame["raw_sha256"]) is not None
    )


def _validate_source_binding_for_paths(
    binding: object, relative_paths: Sequence[str],
) -> bool:
    if type(binding) is not dict or set(binding) != {
        "measurement_source_commit",
        "files",
        "evidence_level",
        "artifact_standalone_proof",
    }:
        return False
    files = binding.get("files")
    if type(files) is not dict or set(files) != set(relative_paths):
        return False
    for relative in relative_paths:
        item = files.get(relative)
        if (
            type(item) is not dict
            or set(item) != {"git_blob_oid", "working_sha256"}
            or type(item.get("git_blob_oid")) is not str
            or _FULL_OID.fullmatch(item["git_blob_oid"]) is None
            or type(item.get("working_sha256")) is not str
            or _FULL_SHA256.fullmatch(item["working_sha256"]) is None
        ):
            return False
    for study_id, (contract_path, _, _) in a1_source.CONTRACTS.items():
        if contract_path in relative_paths and not a1_source.binding_matches(files, study_id=study_id):
            return False
    return (
        type(binding.get("measurement_source_commit")) is str
        and _FULL_OID.fullmatch(binding["measurement_source_commit"]) is not None
        and binding.get("evidence_level") == "source-routed-trace0"
        and binding.get("artifact_standalone_proof") is False
    )


def _validate_source_binding(
    binding: object, policy: Mapping[str, object] | None = None,
) -> bool:
    relative_paths = (
        SOURCE_RELATIVE_PATHS
        if policy is None else _source_relative_paths(policy, non_certifying=False)
    )
    return _validate_source_binding_for_paths(binding, relative_paths)


def _validate_non_certifying_source_binding(
    binding: object, policy: Mapping[str, object] | None = None,
) -> bool:
    relative_paths = (
        NON_CERTIFYING_SOURCE_RELATIVE_PATHS
        if policy is None else _source_relative_paths(policy, non_certifying=True)
    )
    return _validate_source_binding_for_paths(
        binding, relative_paths,
    )


def _cmake_defines(argv: Sequence[str] | None) -> dict[str, str] | None:
    if argv is None:
        return None
    values: dict[str, str] = {}
    for token in argv:
        match = re.fullmatch(r"-DCCBENCH_([A-Z0-9_]+)=(.*)", token)
        if match is None:
            continue
        key, value = match.groups()
        if key in values:
            return None
        values[key] = value
    return values


def _option_values(argv: Sequence[str] | None) -> dict[str, list[str]] | None:
    if argv is None:
        return None
    values: dict[str, list[str]] = {}
    index = 1
    while index < len(argv):
        token = argv[index]
        match = re.fullmatch(r"--?([A-Za-z0-9_]+)=(.*)", token)
        if match is not None:
            key, value = match.groups()
            values.setdefault(key, []).append(value)
        elif re.fullmatch(r"--?[A-Za-z0-9_]+", token) and index + 1 < len(argv):
            key = token.lstrip("-")
            if not argv[index + 1].startswith("-"):
                values.setdefault(key, []).append(argv[index + 1])
                index += 1
        index += 1
    return values


def _one_option(
    options: Mapping[str, Sequence[str]], aliases: Sequence[str], expected: object
) -> bool:
    observed = [value for alias in aliases for value in options.get(alias, ())]
    return observed == [str(expected)]


def _canonical_absolute_token(value: str) -> bool:
    path = Path(value)
    return path.is_absolute() and path.resolve(strict=False) == path


def _dependency_prefix_components(value: object) -> tuple[Path, Path] | None:
    if type(value) is not str:
        return None
    components = value.split(";")
    if len(components) != 2 or any(not item for item in components):
        return None
    paths = tuple(Path(item) for item in components)
    if (
        any(not _canonical_absolute_token(item) for item in components)
        or paths[0].name != "gflags-install"
        or paths[1].name != "glog-install"
        or paths[0].parent != paths[1].parent
        or paths[0] == paths[1]
    ):
        return None
    return paths


def _validated_dependency_prefix(value: object, *, require_scr: bool) -> str:
    components = _dependency_prefix_components(value)
    if components is None:
        raise PaperStoryError(
            "dependency prefix must be exact gflags/glog install siblings"
        )
    if require_scr and any(not _under_scr(path) for path in components):
        raise PaperStoryError("dependency install prefixes must be under /scr")
    return str(value)


def _compiler_define_path(token: str, prefix: str) -> str | None:
    if not token.startswith(prefix):
        return None
    value = token[len(prefix):]
    return value if _canonical_absolute_token(value) else None


def _trace0_commands_match(
    arm_policy: Mapping[str, object],
    policy: Mapping[str, object],
    workload_name: str,
    configure_argv: Sequence[str] | None,
    build_argv: Sequence[str] | None,
    run_argv: Sequence[str] | None,
    use_perf: object,
    perf_bin_sha256: str,
    *, amended_source_root: str | None = None,
) -> bool:
    expected_defines = {
        **{key: str(value) for key, value in arm_policy["flags"].items()},
        "TRACE": "0",
    }
    if (
        set(expected_defines) != CONTROLLED_CCBENCH_DEFINES
        or configure_argv is None
        or build_argv is None
        or run_argv is None
        or type(use_perf) is not bool
    ):
        return False

    define_tokens = [
        f"-DCCBENCH_{key}={expected_defines[key]}"
        for key in sorted(arm_policy["flags"])
    ] + ["-DCCBENCH_TRACE=0"]
    if len(configure_argv) != 10 + len(define_tokens) + (4 if amended_source_root is not None else 0):
        return False
    cmake_executable = configure_argv[0]
    source_token = configure_argv[2]
    build_token = configure_argv[4]
    c_compiler = _compiler_define_path(
        configure_argv[7], "-DCMAKE_C_COMPILER="
    )
    cxx_compiler = _compiler_define_path(
        configure_argv[8], "-DCMAKE_CXX_COMPILER="
    )
    dependency_prefix_token = configure_argv[9]
    dependency_prefix_marker = "-DCMAKE_PREFIX_PATH="
    dependency_prefix = (
        dependency_prefix_token[len(dependency_prefix_marker):]
        if dependency_prefix_token.startswith(dependency_prefix_marker)
        else None
    )
    fetchcontent_tokens = []
    if amended_source_root is not None:
        if source_token != amended_source_root:
            return False
        fetchcontent_tokens = list(configure_argv[10:14])
        marker = "-DFETCHCONTENT_BASE_DIR="
        if not fetchcontent_tokens[0].startswith(marker):
            return False
        base = fetchcontent_tokens[0][len(marker):]
        if not _canonical_absolute_token(base):
            return False
        options = {"fetchcontent_base_dir": base, **{
            f"{name}_source_dir": os.fspath(Path(base) / f"{name}-src")
            for name in ("masstree", "mimalloc", "googletest")
        }}
        if fetchcontent_tokens != list(a1_source.configure_dependencies(options)):
            return False
    expected_configure = [
        cmake_executable,
        "-S",
        source_token,
        "-B",
        build_token,
        "-DCMAKE_BUILD_TYPE=Release",
        "-DENABLE_SANITIZER=OFF",
        f"-DCMAKE_C_COMPILER={c_compiler}",
        f"-DCMAKE_CXX_COMPILER={cxx_compiler}",
        dependency_prefix_token,
        *fetchcontent_tokens,
        *define_tokens,
    ]
    if any((
        not _canonical_absolute_token(cmake_executable),
        Path(cmake_executable).name != "cmake",
        not _canonical_absolute_token(source_token),
        not _canonical_absolute_token(build_token),
        c_compiler is None,
        cxx_compiler is None,
        _dependency_prefix_components(dependency_prefix) is None,
        list(configure_argv) != expected_configure,
    )):
        return False

    if len(build_argv) != 7:
        return False
    jobs = build_argv[6]
    expected_build = [
        cmake_executable,
        "--build",
        build_token,
        "--target",
        "ycsb_silo.exe",
        "-j",
        jobs,
    ]
    if (
        list(build_argv) != expected_build
        or not jobs.isdecimal()
        or int(jobs) <= 0
        or str(int(jobs)) != jobs
    ):
        return False

    configure_dir = Path(build_token)
    build_dir = Path(build_argv[2])
    if (
        configure_dir != build_dir
    ):
        return False
    executable = build_dir / "cc" / "silo" / "ycsb_silo.exe"
    try:
        executable_raw = _read_bytes_once(executable)
    except PaperStoryError:
        return False
    if executable_raw is None or _sha256_bytes(executable_raw) != perf_bin_sha256:
        return False
    workload = next(
        item for item in policy["workloads"] if item["name"] == workload_name
    )
    scale = policy["scale"]
    pegasus_contract = p2_2.env_contract.lookup("pegasus")
    executable_run = [
        os.fspath(executable),
        f"-thread_num={scale['threads']}",
        f"-ycsb_tuple_num={scale['records']}",
        f"-extime={scale['extime_s']}",
        f"-clocks_per_us={pegasus_contract.clocks_per_us}",
        f"-ycsb_zipf_skew={scale['ycsb_zipf_skew']}",
        f"-ycsb_rratio={workload['ycsb_rratio']}",
        f"-ycsb_rmw={scale['ycsb_rmw']}",
        f"-ycsb_max_ope={scale['ycsb_max_ope']}",
    ]
    perf_prefix = [
        "perf",
        "stat",
        "-e",
        ",".join(calibrator_runner.PERF_EVENTS),
        "--",
    ]
    expected_run = (
        list(pegasus_contract.numactl)
        + (perf_prefix if use_perf else [])
        + executable_run
    )
    return list(run_argv) == expected_run


def _validate_arm(
    arm_policy: Mapping[str, object],
    evidence: Mapping[str, object],
    *,
    policy: Mapping[str, object],
    workload_name: str,
    env_tag: str,
    source_binding: Mapping[str, object],
    require_anomalies_zero: bool = False,
) -> dict:
    name = arm_policy["name"]
    errors: list[str] = []
    attempts = evidence.get("attempts")
    if type(evidence.get("attempt_count")) is not int or evidence.get("attempt_count") != 1:
        errors.append("attempt-count-not-one")
    if type(attempts) is not list or not attempts:
        attempts = []
    attempt = attempts[0] if attempts else {}
    attempt_id = attempt.get("build_attempt_id")
    frames = attempt.get("frames")
    if type(attempt_id) is not str or not attempt_id:
        errors.append("attempt-id-invalid")
    if type(frames) is not list:
        frames = []
    expected_stages = [
        STAGE_BUILD_START,
        STAGE_BUILD_DONE,
        *([STAGE_VERIFY_DONE] * len(EXPECTED_VERIFY_CONFIGS)),
        STAGE_BENCH_DONE,
        STAGE_COMMIT,
    ]
    stages = [frame.get("stage") for frame in frames if type(frame) is dict]
    if stages != expected_stages:
        errors.append("stage-sequence-mismatch")
    if evidence.get("last_terminal_stage") != STAGE_COMMIT:
        errors.append("final-terminal-not-commit")
    if evidence.get("last_stage") != STAGE_COMMIT:
        errors.append("commit-not-final-frame")
    variant = evidence.get("variant")
    for frame in frames:
        if type(frame) is not dict:
            errors.append("frame-not-object")
            continue
        payload = _frame_payload(frame)
        if (
            frame.get("variant") != variant
            or frame.get("env_tag") != env_tag
            or (
                payload.get("build_attempt_id") is not None
                and payload.get("build_attempt_id") != attempt_id
            )
        ):
            errors.append("frame-attempt-variant-env-mismatch")
            break

    by_stage: dict[str, list[dict]] = {}
    for frame in frames:
        if type(frame) is dict:
            by_stage.setdefault(str(frame.get("stage")), []).append(frame)
    start = _frame_payload(by_stage.get(STAGE_BUILD_START, [{}])[0])
    build = _frame_payload(by_stage.get(STAGE_BUILD_DONE, [{}])[0])
    bench = _frame_payload(by_stage.get(STAGE_BENCH_DONE, [{}])[0])
    commit = _frame_payload(by_stage.get(STAGE_COMMIT, [{}])[0])
    verify_frames = by_stage.get(STAGE_VERIFY_DONE, [])
    build_frame = by_stage.get(STAGE_BUILD_DONE, [{}])[0]
    bench_frame = by_stage.get(STAGE_BENCH_DONE, [{}])[0]
    physical_frames = evidence.get("all_evaluation_frames")
    if evidence.get("attempt_count") == 1 and physical_frames is not None and (
        type(physical_frames) is not list or physical_frames != frames
    ):
        errors.append("physical-evaluation-stage-binding-mismatch")

    expected_genome = Genome(
        arm_policy["protocol"], dict(arm_policy["flags"])
    ).canonical()
    if (
        start.get("genome") != expected_genome
        or type(start.get("src_token")) is not str
        or not start["src_token"]
    ):
        errors.append("source-genome-binding-mismatch")
    receipt_sha = start.get("build_admission_receipt_sha256")
    if (
        type(receipt_sha) is not str
        or _FULL_SHA256.fullmatch(receipt_sha) is None
        or build.get("build_admission_receipt_sha256") != receipt_sha
        or commit.get("build_admission_receipt_sha256") != receipt_sha
    ):
        errors.append("build-admission-binding-mismatch")

    amended_source_root = None
    if any(path in source_binding.get("files", {}) for path, _, _ in a1_source.CONTRACTS.values()):
        admission = start.get("build_admission", {})
        source = admission.get("source", {})
        amended_source_root = source.get("source_root")
        if (type(amended_source_root) is not str
                or not _canonical_absolute_token(amended_source_root)
                or source.get("ccbench_commit") != CANONICAL_CCBENCH_OID
                or source.get("tracked_clean") is not False
                or source.get("src_token") != start.get("src_token")
                or source.get("genome_sha256") != _sha256_bytes(expected_genome.encode("utf-8"))):
            errors.append("amended-source-admission-mismatch")
            amended_source_root = "invalid"

    verify_tags = []
    for frame in verify_frames:
        payload = _frame_payload(frame)
        workload = payload.get("workload")
        verify_tags.append(workload.get("tag") if type(workload) is dict else None)
        if payload.get("certified") is not True:
            errors.append("verify-not-certified")
        if require_anomalies_zero and (
            type(payload.get("anomalies")) is not int
            or payload["anomalies"] != 0
        ):
            errors.append("verify-anomalies-not-zero")
    if verify_tags != list(EXPECTED_VERIFY_CONFIGS):
        errors.append("verify-config-sequence-mismatch")
    if commit.get("verify_configs") != list(EXPECTED_VERIFY_CONFIGS):
        errors.append("commit-verify-projection-mismatch")

    raw_tps = bench.get("tps")
    expected_reps = _expected_reps(policy, workload_name)
    is_v3 = _policy_schema(policy) == POLICY_SCHEMA_V3
    if is_v3 and (type(raw_tps) is not list or not raw_tps):
        errors.append("bench-no-throughput")
    tps_valid = (
        type(raw_tps) is list
        and len(raw_tps) == expected_reps
        and all(_finite_number(value) and value > 0 for value in raw_tps)
    )
    if not tps_valid:
        errors.append("tps-length-or-value-disagrees-with-workload-policy")
    if bench.get("rep_notes") != []:
        errors.append("rep-notes-not-empty")
    rounds = bench.get("rounds")
    if type(rounds) is not int or rounds != 1:
        errors.append("rounds-not-one")
    if bench.get("unstable") is not False:
        errors.append("unstable-not-false")
    if is_v3:
        if not _finite_number(bench.get("cv")):
            errors.append("bench-cv-undefined")
        if bench.get("settled") is not True:
            errors.append("bench-unsettled")

    if tps_valid:
        median = statistics.median(float(value) for value in raw_tps)
        mean = statistics.fmean(float(value) for value in raw_tps)
        cv = statistics.stdev(float(value) for value in raw_tps) / mean
        if not _numbers_equal(bench.get("median_tps"), median):
            errors.append("bench-median-does-not-match-tps")
        if not _numbers_equal(bench.get("cv"), cv):
            errors.append("bench-cv-does-not-match-tps")
        if is_v3 and bench.get("unstable") is not (cv > 0.05):
            errors.append("bench-unstable-does-not-match-aggregate-cv")
    if (
        not _numbers_equal(commit.get("fitness_tps"), bench.get("median_tps"))
        or not _numbers_equal(commit.get("cv"), bench.get("cv"))
        or commit.get("unstable") is not bench.get("unstable")
        or commit.get("high_variance") is not bench.get("high_variance")
    ):
        errors.append("bench-commit-numeric-projection-mismatch")

    perf_sha = build.get("perf_bin_sha256")
    configure_cmd = build.get("perf_configure_cmd")
    build_cmd = build.get("perf_build_cmd")
    configure_argv = _command_argv(configure_cmd)
    build_argv = _command_argv(build_cmd)
    run_argv = _command_argv(bench.get("run_cmd"))
    perf_observation = bench.get("perf_observation")
    use_perf = (
        perf_observation.get("use_perf")
        if type(perf_observation) is dict else None
    )
    if (
        type(perf_sha) is not str
        or _FULL_SHA256.fullmatch(perf_sha) is None
        or not _trace0_commands_match(
            arm_policy,
            policy,
            workload_name,
            configure_argv,
            build_argv,
            run_argv,
            use_perf,
            perf_sha,
            amended_source_root=amended_source_root,
        )
        or not _valid_physical_frame(build_frame)
        or not _valid_physical_frame(bench_frame)
        or not _validate_source_binding(source_binding, policy)
    ):
        errors.append("trace0-source-route-incomplete")

    result = {
        "name": name,
        "variant": _json_safe(variant),
        "genome": expected_genome,
        "valid": not errors,
        "errors": sorted(set(errors)),
        "raw_tps": _json_safe(raw_tps),
        "expected_reps": expected_reps,
        "observed_reps": len(raw_tps) if type(raw_tps) is list else None,
        "actual_rounds": _json_safe(rounds),
        "unstable": _json_safe(bench.get("unstable")),
        "rep_notes": _json_safe(bench.get("rep_notes")),
        "attempt_count": _json_safe(evidence.get("attempt_count")),
        "correctness_evidence": {
            "verify_configs": _json_safe(verify_tags),
            "certified": [
                _json_safe(_frame_payload(frame).get("certified"))
                for frame in verify_frames
            ],
            "verify_done_frames": [_frame_ref(frame) for frame in verify_frames],
        },
        "performance_trace0_evidence": {
            **dict(source_binding),
            "perf_bin_sha256": _json_safe(perf_sha),
            "perf_configure_cmd": _json_safe(configure_cmd),
            "perf_build_cmd": _json_safe(build_cmd),
            "bench_run_cmd": _json_safe(bench.get("run_cmd")),
            "build_done_frame": _frame_ref(build_frame),
            "bench_done_frame": _frame_ref(bench_frame),
        },
        "ordered_attempt_frames": [_frame_ref(frame) for frame in frames],
    }
    return result


def validate_workload_evidence(
    policy: Mapping[str, object],
    *,
    workload_name: str,
    campaign_id: str,
    env_tag: str,
    arms: Sequence[Mapping[str, object]],
    wal_evidence: Mapping[str, object],
    source_binding: Mapping[str, object],
    preexisting_errors: Sequence[str] = (),
    campaign_binding: Mapping[str, object] | None = None,
    non_certifying_lock: bool = False,
    schedule_receipt_evidence: Mapping[str, object] | None = None,
) -> dict:
    validate_policy(policy)
    _assert_ccbench_acceptance(
        _repo_root(), policy, boundary="artifact-consumer",
    )
    errors = list(preexisting_errors)
    if workload_name not in WORKLOAD_ORDER:
        errors.append("unexpected-workload")
    if type(campaign_id) is not str or not campaign_id:
        errors.append("campaign-id-invalid")
    if len(arms) != 2:
        errors.append("variant-set-cardinality-not-two")
    names = [arm.get("name") for arm in arms]
    expected_arm_order = _workload_arm_order(policy, workload_name)
    if names != list(expected_arm_order):
        errors.append("arm-order-or-set-mismatch")
    arm_results = {}
    for arm_policy in _workload_arms(policy, workload_name):
        matches = [arm for arm in arms if arm.get("name") == arm_policy["name"]]
        if len(matches) != 1:
            errors.append(f"{arm_policy['name']}:arm-missing-or-duplicate")
            arm_results[arm_policy["name"]] = {
                "name": arm_policy["name"],
                "valid": False,
                "errors": ["arm-missing-or-duplicate"],
                "raw_tps": None,
            }
            continue
        arm_result = _validate_arm(
            arm_policy,
            matches[0],
            policy=policy,
            workload_name=workload_name,
            env_tag=env_tag,
            source_binding=source_binding,
            require_anomalies_zero=non_certifying_lock,
        )
        arm_results[arm_policy["name"]] = arm_result
        errors.extend(f"{arm_policy['name']}:{item}" for item in arm_result["errors"])

    is_v3 = _policy_schema(policy) == POLICY_SCHEMA_V3
    if is_v3:
        schedule_document = (
            schedule_receipt_evidence.get("document")
            if type(schedule_receipt_evidence) is dict else None
        )
        errors.extend(_balanced_schedule_receipt_errors(
            policy, workload_name, schedule_document, arm_results,
        ))

    valid = not errors and all(item.get("valid") for item in arm_results.values())
    stats = None
    if valid:
        try:
            stats = positional_statistics(
                policy,
                workload_name,
                arm_results[_workload_arm_by_role(
                    policy, workload_name, "baseline",
                )["name"]]["raw_tps"],
                arm_results[_workload_arm_by_role(
                    policy, workload_name, "variant",
                )["name"]]["raw_tps"],
            )
        except PaperStoryError as exc:
            errors.append(f"statistics-invalid:{exc}")
            valid = False
    terminal_result = (
        {
            "status": "valid",
            "classification": stats["classification"],
        }
        if valid else {
            "status": "invalid",
            "reasons": sorted(set(errors)),
        }
    )
    result = {
        "workload": workload_name,
        "campaign_id": campaign_id,
        "valid": valid,
        "errors": sorted(set(errors)),
        "terminal_result": terminal_result,
        "arms": arm_results,
        "statistics": stats if valid else None,
        "wal_evidence": _json_safe(dict(wal_evidence)),
        "campaign_binding": _json_safe(dict(campaign_binding or {})),
    }
    if is_v3:
        result["schedule_receipt"] = _json_safe(
            dict(schedule_receipt_evidence or {})
        )
    return result


def _infer_arm_name(
    frames: Sequence[Mapping[str, object]],
    policy: Mapping[str, object],
    workload_name: str,
):
    starts = [frame for frame in frames if frame.get("stage") == STAGE_BUILD_START]
    if not starts:
        return None
    genome = _frame_payload(starts[0]).get("genome")
    matches = [
        arm["name"]
        for arm in _workload_arms(policy, workload_name)
        if Genome(arm["protocol"], dict(arm["flags"])).canonical() == genome
    ]
    return matches[0] if len(matches) == 1 else None


def _campaign_id_from_preimage(workload_name: str, preimage: str) -> str:
    return (
        f"paper-story-a1-{workload_name}-paired-"
        f"{_sha256_bytes(preimage.encode('utf-8'))[:8]}"
    )


def _campaign_identity_preimage(canonical_lock: object) -> str | None:
    if type(canonical_lock) is not str:
        return None
    try:
        return campaign_lock_codec.decode_non_certifying_campaign_lock(
            canonical_lock
        ).identity_preimage
    except campaign_lock_codec.CampaignLockCodecError:
        pass
    try:
        decoded = campaign_lock_codec.decode_campaign_lock(canonical_lock)
    except campaign_lock_codec.CampaignLockCodecError:
        return None
    return decoded.identity_preimage if decoded.is_v2 else None


def _validate_campaign_preimage(
    policy: Mapping[str, object],
    workload_name: str,
    preimage: object,
    admission_policy,
) -> bool:
    identity_preimage = _campaign_identity_preimage(preimage)
    if identity_preimage is None:
        return False
    try:
        value = json.loads(
            identity_preimage,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, PaperStoryError):
        return False
    if (
        type(value) is not dict
        or set(value) != {
            "ccbench_commit", "search_config", "search_tag", "spec_content",
            "trial",
        }
        or type(value.get("search_config")) is not dict
    ):
        return False
    search = value["search_config"]
    expected_search_keys = {
        "arm_order", "arms", "build_admission", "formal", "measurement_env",
        "pairing_design", "promotion_prohibited", "scale", "schema",
        "study_id", "workload",
    }
    if _policy_schema(policy) == POLICY_SCHEMA_V3:
        expected_search_keys.add("schedule")
    if set(search) not in (
        expected_search_keys,
        expected_search_keys | {"non_certifying_mode"},
    ):
        return False
    if (
        "non_certifying_mode" in search
        and search["non_certifying_mode"]
        != trial_registry.REGISTERED_FORMAL_NON_CERTIFYING_MODE
    ):
        return False
    expected_arms = [
        {
            "name": arm["name"],
            "genome": Genome(arm["protocol"], dict(arm["flags"])).canonical(),
        }
        for arm in _workload_arms(policy, workload_name)
    ]
    expected_workload = {"name": workload_name, **workload_flags(policy, workload_name)}
    study_id = _policy_study_id(policy)
    arm_order = _workload_arm_order(policy, workload_name)
    is_v2 = _policy_schema(policy) == POLICY_SCHEMA_V2
    expected_spec = (
        "D95 exploratory A-1 static10 minus adaptive, arm-grouped "
        f"positional comparison, workload={workload_name}"
        if is_v2 else
        "A-1 variant minus baseline under balanced five-rep blocks, "
        f"workload={workload_name}"
    )
    if any((
        value.get("ccbench_commit") != _campaign_ccbench_commit(policy),
        value.get("trial") != study_id,
        value.get("search_tag") != "paired",
        value.get("spec_content") != expected_spec,
        search.get("schema") != _campaign_schema(policy),
        search.get("study_id") != study_id,
        search.get("arm_order") != list(arm_order),
        search.get("arms") != expected_arms,
        search.get("workload") != expected_workload,
        search.get("scale") != _campaign_scale(policy, workload_name),
        search.get("measurement_env") != "pegasus",
        search.get("pairing_design") != _pairing_design(policy),
        search.get("formal") is not False,
        search.get("promotion_prohibited") is not True,
    )):
        return False
    if not is_v2 and search.get("schedule") != campaign_config(
        policy, workload_name,
    ).search_config["schedule"]:
        return False
    if admission_policy is not None:
        try:
            expected_admission = json.loads(admission_policy._preimage_json)
        except (AttributeError, json.JSONDecodeError):
            return False
        if search.get("build_admission") != expected_admission:
            return False
    return True


def _snapshot_frames(raw: bytes, records, issues) -> list[dict]:
    issue_lines = {
        issue[0]
        for issue in issues
        if type(issue) is tuple and len(issue) >= 1 and type(issue[0]) is int
    }
    candidates = []
    offset = 0
    for line_number, line in enumerate(raw.splitlines(keepends=True), 1):
        end = offset + len(line)
        if line_number not in issue_lines and line.endswith(b"\n"):
            candidates.append((line_number, offset, end, line))
        offset = end
    if len(candidates) != len(records):
        raise PaperStoryError("WAL snapshot record/line projection differs")
    return [
        {
            "line_number": line_number,
            "byte_start": start,
            "byte_end": end,
            "raw_sha256": _sha256_bytes(line),
            "variant": record.variant,
            "stage": record.stage,
            "env_tag": record.env_tag,
            "payload": _json_safe(record.payload),
        }
        for record, (line_number, start, end, line) in zip(records, candidates)
    ]


def _arm_evidence_from_snapshot(
    physical_frames: Sequence[Mapping[str, object]], policy: Mapping[str, object],
    workload_name: str,
) -> list[dict]:
    evaluation_stages = {
        STAGE_BUILD_START,
        STAGE_BUILD_DONE,
        STAGE_VERIFY_DONE,
        STAGE_BENCH_DONE,
        STAGE_COMMIT,
        STAGE_ABORT,
    }
    variants = []
    for frame in physical_frames:
        if frame.get("stage") in evaluation_stages and frame.get("variant") not in variants:
            variants.append(frame.get("variant"))
    arms = []
    for variant in variants:
        frames = [
            dict(frame)
            for frame in physical_frames
            if frame.get("variant") == variant and frame.get("stage") in evaluation_stages
        ]
        attempt_ids = []
        for frame in frames:
            if frame.get("stage") != STAGE_BUILD_START:
                continue
            attempt_id = _frame_payload(frame).get("build_attempt_id")
            if type(attempt_id) is str and attempt_id not in attempt_ids:
                attempt_ids.append(attempt_id)
        attempts = []
        for attempt_id in attempt_ids:
            selected = [
                frame
                for frame in frames
                if len(attempt_ids) == 1
                or _frame_payload(frame).get("build_attempt_id") == attempt_id
            ]
            attempts.append({"build_attempt_id": attempt_id, "frames": selected})
        terminals = [
            frame.get("stage")
            for frame in frames
            if frame.get("stage") in {STAGE_COMMIT, STAGE_ABORT}
        ]
        arms.append({
            "name": _infer_arm_name(frames, policy, workload_name),
            "variant": variant,
            "attempt_count": len(attempt_ids),
            "attempts": attempts,
            "all_evaluation_frames": frames,
            "last_terminal_stage": terminals[-1] if terminals else None,
            "last_stage": frames[-1].get("stage") if frames else None,
        })
    arm_order = _workload_arm_order(policy, workload_name)
    arms.sort(key=lambda item: (
        list(arm_order).index(item["name"])
        if item["name"] in arm_order else len(arm_order),
        str(item["variant"]),
    ))
    return arms


def collect_workload(
    policy: Mapping[str, object],
    *,
    workload_name: str,
    campaign_id: str,
    layout: CampaignLayout,
    admission_policy,
    env_tag: str,
    source_binding: Mapping[str, object],
    summary=None,
    campaign_error: str | None = None,
    expected_campaign_preimage: str | None = None,
    expected_layout_root: str | None = None,
    expected_schedule_receipt: object = None,
) -> dict:
    wal_path = Path(layout.wal_file)
    preexisting_errors: list[str] = []
    if campaign_error is not None:
        preexisting_errors.append(f"campaign-error:{campaign_error}")
    if summary is not None and (
        summary.total != 2
        or summary.evaluated != 2
        or summary.skipped != 0
        or summary.identity_skipped != 0
    ):
        preexisting_errors.append("campaign-summary-not-fresh-exact-two")

    try:
        wal_raw = _read_bytes_once(wal_path, missing_ok=True)
    except PaperStoryError as exc:
        wal_raw = None
        preexisting_errors.append(f"wal-snapshot-open-error:{exc}")
    lock_path = Path(layout.lock_file)
    try:
        lock_raw = _read_bytes_once(lock_path, missing_ok=True)
    except PaperStoryError as exc:
        lock_raw = None
        preexisting_errors.append(f"campaign-lock-open-error:{exc}")
    wal_evidence = {
        "path": os.fspath(wal_path),
        "expected_env_tag": env_tag,
        "size": len(wal_raw) if wal_raw is not None else 0,
        "sha256": _sha256_bytes(wal_raw) if wal_raw is not None else None,
        "records": [],
        "line_issues": [],
        "truncated_tail": False,
    }
    if wal_raw is None:
        preexisting_errors.append("wal-snapshot-missing")
    if lock_raw is None:
        preexisting_errors.append("campaign-lock-snapshot-missing")
    lock_preimage = None
    decoded_snapshot_lock = None
    physical_frames: list[dict] = []
    if wal_raw is not None and lock_raw is not None:
        try:
            with tempfile.TemporaryDirectory(prefix="paper-story-a1-snapshot-") as raw_tmp:
                snapshot = CampaignLayout(raw_tmp)
                Path(snapshot.runs_dir).mkdir(mode=0o700)
                _exclusive_write_bytes(Path(snapshot.lock_file), lock_raw)
                _exclusive_write_bytes(Path(snapshot.wal_file), wal_raw)
                lock_preimage = wal.read_lock(snapshot)
                records, issues, truncated_tail = wal.read_records_collected(snapshot)
                wal_evidence["line_issues"] = [list(issue) for issue in issues]
                wal_evidence["truncated_tail"] = truncated_tail
                wal_evidence["records"] = [
                    {
                        "variant": record.variant,
                        "stage": record.stage,
                        "env_tag": record.env_tag,
                        "payload": _json_safe(record.payload),
                    }
                    for record in records
                ]
                physical_frames = _snapshot_frames(wal_raw, records, issues)
                if issues:
                    preexisting_errors.append("wal-line-issues-present")
                if truncated_tail:
                    preexisting_errors.append("wal-truncated-tail")
                try:
                    try:
                        decoded_snapshot_lock = (
                            campaign_lock_codec.decode_non_certifying_campaign_lock(
                                lock_preimage
                            )
                        )
                    except campaign_lock_codec.CampaignLockCodecError:
                        decoded_snapshot_lock = None
                    replay_fn = (
                        wal.replay_a1_non_certifying
                        if decoded_snapshot_lock is not None else wal.replay
                    )
                    replayed = replay_fn(
                        snapshot, admission_policy=admission_policy,
                    )
                    replay_variants = set(replayed)
                    physical_variants = {
                        frame["variant"] for frame in physical_frames
                        if frame["stage"] in {
                            STAGE_BUILD_START, STAGE_BUILD_DONE, STAGE_VERIFY_DONE,
                            STAGE_BENCH_DONE, STAGE_COMMIT, STAGE_ABORT,
                        }
                    }
                    if replay_variants != physical_variants:
                        preexisting_errors.append("wal-replay-physical-variant-mismatch")
                except Exception as exc:  # noqa: BLE001
                    preexisting_errors.append(f"wal-replay-error:{type(exc).__name__}")
        except Exception as exc:  # noqa: BLE001 - retain a bounded forensic result
            preexisting_errors.append(f"wal-snapshot-read-error:{type(exc).__name__}")

    if expected_campaign_preimage is None and admission_policy is not None:
        cfg = ident.bind_admission_policy(
            campaign_config(policy, workload_name), admission_policy
        )
        expected_campaign_preimage = ident.canonical_preimage(cfg)
    expected_id = (
        _campaign_id_from_preimage(workload_name, expected_campaign_preimage)
        if type(expected_campaign_preimage) is str else None
    )
    layout_root = Path(layout.root).resolve(strict=False)
    lock_identity_preimage = _campaign_identity_preimage(lock_preimage)
    if (
        lock_identity_preimage != expected_campaign_preimage
        or not _validate_campaign_preimage(
            policy, workload_name, lock_preimage, admission_policy
        )
    ):
        preexisting_errors.append("campaign-lock-preimage-mismatch")
    if expected_id != campaign_id:
        preexisting_errors.append("campaign-id-recomputed-mismatch")
    if layout_root.name != campaign_id:
        preexisting_errors.append("campaign-layout-id-mismatch")
    if expected_layout_root is not None and layout_root != Path(
        expected_layout_root
    ).resolve(strict=False):
        preexisting_errors.append("campaign-layout-root-mismatch")
    if wal_path.resolve(strict=False) != layout_root / "runs" / "wal.jsonl":
        preexisting_errors.append("campaign-wal-path-mismatch")
    campaign_binding = {
        "layout_root": os.fspath(layout_root),
        "wal_path": os.fspath(wal_path.resolve(strict=False)),
        "campaign_lock_path": os.fspath(lock_path.resolve(strict=False)),
        "campaign_lock_size": len(lock_raw) if lock_raw is not None else 0,
        "campaign_lock_sha256": (
            _sha256_bytes(lock_raw) if lock_raw is not None else None
        ),
        "canonical_preimage": lock_preimage,
        "recomputed_campaign_id": expected_id,
    }
    arm_evidence = _arm_evidence_from_snapshot(
        physical_frames, policy, workload_name,
    )
    schedule_receipt_evidence, schedule_receipt_errors = (
        _snapshot_balanced_schedule_receipt(
            policy,
            workload_name,
            layout,
            expected_receipt=expected_schedule_receipt,
        )
    )
    preexisting_errors.extend(schedule_receipt_errors)
    return validate_workload_evidence(
        policy,
        workload_name=workload_name,
        campaign_id=campaign_id,
        env_tag=env_tag,
        arms=arm_evidence,
        wal_evidence=wal_evidence,
        source_binding=source_binding,
        preexisting_errors=preexisting_errors,
        campaign_binding=campaign_binding,
        non_certifying_lock=(
            type(decoded_snapshot_lock)
            is campaign_lock_codec.DecodedNonCertifyingCampaignLock
        ),
        schedule_receipt_evidence=schedule_receipt_evidence,
    )


def _workload_has_terminal_result(item: object) -> bool:
    if type(item) is not dict:
        return False
    terminal = item.get("terminal_result")
    if type(terminal) is not dict:
        return False
    if item.get("valid") is True:
        statistics_result = item.get("statistics")
        return (
            set(terminal) == {"status", "classification"}
            and terminal.get("status") == "valid"
            and type(statistics_result) is dict
            and terminal.get("classification")
            == statistics_result.get("classification")
            and terminal.get("classification") in {
                "resolved-above-floor",
                "bounded-below-floor",
                "unresolved",
                "pilot-sizing-input-only",
            }
            and item.get("errors") == []
        )
    errors = item.get("errors")
    return (
        item.get("valid") is False
        and type(errors) is list
        and bool(errors)
        and all(type(error) is str and error for error in errors)
        and item.get("statistics") is None
        and terminal == {"status": "invalid", "reasons": errors}
    )


def assemble_result(
    policy: Mapping[str, object],
    *,
    policy_sha256: str,
    source_binding: Mapping[str, object],
    reservation_binding: Mapping[str, object] | None = None,
    job_executions: Sequence[Mapping[str, object]] | None = None,
    workloads: Sequence[Mapping[str, object]],
    measurement_error: str | None = None,
) -> dict:
    validate_policy(policy)
    v3 = _policy_schema(policy) == POLICY_SCHEMA_V3
    if v3:
        if reservation_binding is not None:
            raise PaperStoryError("v3 result must not claim one group reservation")
        executions = _validate_v3_job_executions(job_executions)
    else:
        if job_executions is not None:
            raise PaperStoryError("legacy result must not claim job executions")
        reservation = _validate_reservation_binding_document(reservation_binding)
    workload_names = [item.get("workload") for item in workloads]
    campaign_ids = [item.get("campaign_id") for item in workloads]
    wal_paths = [
        item.get("campaign_binding", {}).get("wal_path")
        if type(item.get("campaign_binding")) is dict else None
        for item in workloads
    ]
    all_workloads_terminal = (
        measurement_error is None
        and workload_names == list(WORKLOAD_ORDER)
        and len(set(campaign_ids)) == 3
        and len(wal_paths) == 3
        and None not in wal_paths
        and len(set(wal_paths)) == 3
        and all(_workload_has_terminal_result(item) for item in workloads)
    )
    complete = all_workloads_terminal and all(
        item.get("valid") is True for item in workloads
    )
    result = {
        "schema_version": RESULT_SCHEMA,
        "study_id": _policy_study_id(policy),
        "formal": False,
        "promotion_prohibited": True,
        "authority": "exploratory",
        "pairing_design": _pairing_design(policy),
        "policy_sha256": policy_sha256,
        "source_binding": dict(source_binding),
        "pbs_evidence_scope": _json_safe(PBS_EVIDENCE_SCOPE),
        "workload_reps": {
            name: _expected_reps(policy, name) for name in WORKLOAD_ORDER
        },
        "all_workloads_terminal": all_workloads_terminal,
        "complete": complete,
        "measurement_error": measurement_error,
        "workloads": [_json_safe(dict(item)) for item in workloads],
        "limitations": (
            [
                "Arm-grouped ordinal positions are not shared time blocks.",
                "The preregistered intervals are descriptive, not official confidence intervals.",
                "No causal effect, population mean, repeatability, or official significance is claimed.",
                "Source-routed trace0 evidence is not an artifact-standalone proof.",
                "No cross-workload conclusion is produced.",
            ]
            if _policy_schema(policy) == POLICY_SCHEMA_V2
            else [
                "The estimand is the difference under the balanced five-rep schedule, not a carryover-free steady-state direct effect.",
                "Pilot observations are sizing inputs and are ineligible for the final estimate.",
                "Source-routed trace0 evidence is not an artifact-standalone proof.",
                "No cross-workload conclusion is produced.",
            ]
        ),
    }
    if v3:
        result["job_executions"] = executions
    else:
        result["reservation_binding"] = reservation
    return result


def _prepare_runtime_roots(roots: Mapping[str, str], env_tag: str) -> None:
    result_root = Path(roots["result_root"])
    output_root = Path(roots["output_root"])
    cache_root = Path(roots["cache_root"])
    try:
        result_root.mkdir(mode=0o700)
        output_root.mkdir(mode=0o700)
        cache_root.mkdir(mode=0o700)
        (output_root / "env" / env_tag / "claims").mkdir(parents=True, mode=0o700)
    except OSError as exc:
        raise PaperStoryError(f"fresh runtime root creation failed: {exc}") from exc


def _measurement_intent(
    *, acquisition: Mapping[str, object], repo_root: Path, attempt: Path,
    source_commit: str, policy: Mapping[str, object] | None = None,
    workload: str | None = None,
) -> dict[str, object]:
    raw = _read_bytes_once(_attempt_intent_path(attempt))
    if raw is None:  # pragma: no cover
        raise PaperStoryError("submission intent is missing")
    intent = _validate_submission_intent(
        _decode_json_bytes(raw, "submission intent"),
        repo_root=repo_root,
        source_commit=source_commit,
        attempt=attempt,
        policy=policy,
    )
    if _policy_schema(policy if policy is not None else load_policy()[0]) == POLICY_SCHEMA_V3:
        if workload not in WORKLOAD_ORDER:
            raise PaperStoryError("group intent workload selector differs")
        ordinal = WORKLOAD_ORDER.index(workload)
        acquisition_jobs = acquisition.get("jobs")
        if (
            type(acquisition_jobs) is not list
            or len(acquisition_jobs) != len(WORKLOAD_ORDER)
            or acquisition.get("attempt_root") != intent["attempt_root"]
            or acquisition.get("source_commit") != intent["source_commit"]
            or acquisition.get("intent_sha256") != intent["intent_sha256"]
            or acquisition_jobs[ordinal].get("qsub_argv")
            != intent["jobs"][ordinal]["qsub_argv"]
            or acquisition_jobs[ordinal].get("qsub_options")
            != intent["jobs"][ordinal]["qsub_options"]
        ):
            raise PaperStoryError("group receipt differs from its create-only intent")
    elif (
        acquisition.get("qsub_argv") != intent["qsub_argv"]
        or acquisition.get("qsub_options") != intent["qsub_options"]
        or acquisition.get("attempt_root") != intent["attempt_root"]
        or acquisition.get("source_commit") != intent["source_commit"]
    ):
        raise PaperStoryError("submission receipt differs from its create-only intent")
    return intent


def _a1_common_record(
    projection: trial_registry.A1RegisteredNonCertifyingProjection,
    *,
    source_binding: Mapping[str, object],
    environment_contract_sha256: str,
    intent_sha256: str,
) -> dict[str, object]:
    record = trial_registry.a1_registered_noncertifying_record(projection)
    return {
        **record,
        "source_binding_sha256": _sha256_bytes(
            campaign_lock_codec.canonical_json(dict(source_binding)).encode("utf-8")
        ),
        "environment_contract_sha256": environment_contract_sha256,
        "intent_sha256": intent_sha256,
    }


def _preseed_a1_non_certifying_locks(
    *,
    configs: Sequence[CampaignConfig],
    layouts: Sequence[CampaignLayout],
    workloads: Sequence[str],
    common_record: Mapping[str, object],
) -> None:
    if not (
        len(configs) == len(layouts) == len(workloads) == 3
        and list(workloads) == list(WORKLOAD_ORDER)
    ):
        raise PaperStoryError("A-1 lock preseed requires the exact workload triple")
    if any(not ident.is_a1_non_certifying_config(cfg) for cfg in configs):
        raise PaperStoryError(
            "A-1 formal/promotion_prohibited marker differs before lock preseed"
        )
    for ordinal, (cfg, layout, workload) in enumerate(
        zip(configs, layouts, workloads)
    ):
        layout.ensure()
        identity_preimage = ident.canonical_preimage(cfg)
        campaign_id = str(ident.campaign_id(cfg))
        lock_text = campaign_lock_codec.encode_non_certifying_campaign_lock(
            identity_preimage,
            common_record=common_record,
            workload_binding={
                "workload": workload,
                "campaign_id": campaign_id,
                "ordinal": ordinal,
            },
        )
        if wal.acquire_lock_atomic(layout, lock_text):
            continue
        stored = wal.read_lock(layout)
        if stored != lock_text:
            raise PaperStoryError("existing A-1 non-certifying lock differs")


def _preseed_v3_workload_lock(
    *,
    configs: Sequence[CampaignConfig],
    campaign_ids: Sequence[str],
    workload: str,
    output_root: str,
    common_record: Mapping[str, object],
) -> CampaignLayout:
    if (
        workload not in WORKLOAD_ORDER
        or len(configs) != len(WORKLOAD_ORDER)
        or len(campaign_ids) != len(WORKLOAD_ORDER)
    ):
        raise PaperStoryError("v3 lock preseed requires the exact campaign triple")
    ordinal = WORKLOAD_ORDER.index(workload)
    cfg = configs[ordinal]
    if not ident.is_a1_non_certifying_config(cfg):
        raise PaperStoryError("A-1 marker differs before workload lock preseed")
    layout = exploration_campaign_layout(campaign_ids[ordinal], output_root)
    layout.ensure()
    lock_text = campaign_lock_codec.encode_non_certifying_campaign_lock(
        ident.canonical_preimage(cfg),
        common_record=common_record,
        workload_binding={
            "workload": workload,
            "campaign_id": campaign_ids[ordinal],
            "ordinal": ordinal,
        },
    )
    if not wal.acquire_lock_atomic(layout, lock_text):
        if wal.read_lock(layout) != lock_text:
            raise PaperStoryError("existing A-1 workload lock differs")
    return layout


def _validate_v3_ready_document(
    value: object,
    *,
    workload: str,
    ordinal: int,
    study_id: str,
    source_commit: str,
    attempt: Path,
    submission: Mapping[str, object],
) -> dict[str, object]:
    if type(value) is not dict or set(value) != {
        "schema_version", "study_id", "source_commit", "attempt_root",
        "workload", "ordinal", "request_id", "reservation_nonce",
        "campaign_id", "prepared_arms", "recorded_epoch",
    }:
        raise PaperStoryError("workload ready evidence shape differs")
    jobs = submission.get("jobs")
    job = jobs[ordinal] if type(jobs) is list and len(jobs) == 3 else None
    prepared = value.get("prepared_arms")
    if (
        value.get("schema_version") != V3_READY_SCHEMA
        or value.get("study_id") != study_id
        or value.get("source_commit") != source_commit
        or value.get("attempt_root") != os.fspath(attempt)
        or value.get("workload") != workload
        or value.get("ordinal") != ordinal
        or type(job) is not dict
        or _validated_request_id(
            value.get("request_id"), f"{workload} ready request ID",
        ) != _validated_request_id(
            job.get("request_id"), f"{workload} submission request ID",
        )
        or value.get("reservation_nonce") != f"{attempt.name}.{workload}"
        or type(value.get("campaign_id")) is not str
        or type(value.get("recorded_epoch")) is not int
        or value["recorded_epoch"] <= 0
        or type(prepared) is not list
        or len(prepared) != len(ARM_ORDER)
    ):
        raise PaperStoryError("workload ready evidence differs")
    for arm in prepared:
        if type(arm) is not dict or set(arm) != {
            "variant", "build_attempt_id", "build_admission_receipt_sha256",
            "verify_tags",
        }:
            raise PaperStoryError("workload ready arm evidence shape differs")
        if (
            type(arm.get("variant")) is not str
            or not arm["variant"]
            or type(arm.get("build_attempt_id")) is not str
            or not arm["build_attempt_id"]
            or type(arm.get("build_admission_receipt_sha256")) is not str
            or _FULL_SHA256.fullmatch(arm["build_admission_receipt_sha256"])
            is None
            or arm.get("verify_tags") != list(EXPECTED_VERIFY_CONFIGS)
        ):
            raise PaperStoryError("workload ready arm evidence differs")
    return dict(value)


def _v3_barrier_before_bench(
    *,
    prepared_arms: Sequence[object],
    workload: str,
    campaign_id: str,
    policy: Mapping[str, object],
    source_commit: str,
    attempt: Path,
    submission: Mapping[str, object],
    reservation: Mapping[str, object],
    timeout_s: float = 600.0,
) -> None:
    """MF2 front gate: exact three ready files precede bench-go/start."""
    ordinal = WORKLOAD_ORDER.index(workload)
    roots = _v3_job_roots(attempt, workload)
    ready = {
        "schema_version": V3_READY_SCHEMA,
        "study_id": _policy_study_id(policy),
        "source_commit": source_commit,
        "attempt_root": os.fspath(attempt),
        "workload": workload,
        "ordinal": ordinal,
        "request_id": reservation["job_id"],
        "reservation_nonce": reservation["nonce"],
        "campaign_id": campaign_id,
        "prepared_arms": [
            {
                "variant": prepared.result.variant,
                "build_attempt_id": prepared.build_attempt_id,
                "build_admission_receipt_sha256": (
                    prepared.build_admission_receipt_sha256
                ),
                "verify_tags": list(prepared.verify_tags),
            }
            for prepared in prepared_arms
        ],
        "recorded_epoch": int(time.time()),
    }
    _validate_v3_ready_document(
        ready, workload=workload, ordinal=ordinal,
        study_id=_policy_study_id(policy), source_commit=source_commit,
        attempt=attempt, submission=submission,
    )
    ready_path = Path(roots["ready"])
    _exclusive_write(ready_path, ready)
    _fsync_directory(ready_path.parent)

    deadline = time.monotonic() + timeout_s
    ready_bindings = None
    while time.monotonic() <= deadline:
        bindings = []
        try:
            for ready_ordinal, ready_workload in enumerate(WORKLOAD_ORDER):
                path = Path(_v3_job_roots(attempt, ready_workload)["ready"])
                raw = _read_bytes_once(path, missing_ok=True)
                if raw is None:
                    raise FileNotFoundError
                document = _validate_v3_ready_document(
                    _decode_json_bytes(raw, f"{ready_workload} ready evidence"),
                    workload=ready_workload, ordinal=ready_ordinal,
                    study_id=_policy_study_id(policy),
                    source_commit=source_commit, attempt=attempt,
                    submission=submission,
                )
                bindings.append({
                    "workload": ready_workload,
                    "ordinal": ready_ordinal,
                    "campaign_id": document["campaign_id"],
                    "path": os.fspath(path),
                    "sha256": _sha256_bytes(raw),
                })
        except FileNotFoundError:
            time.sleep(0.1)
            continue
        ready_bindings = bindings
        break
    if ready_bindings is None:
        raise PaperStoryError("exact workload ready triple did not appear before bench")
    bench_go = {
        "schema_version": V3_BENCH_GO_SCHEMA,
        "study_id": _policy_study_id(policy),
        "source_commit": source_commit,
        "attempt_root": os.fspath(attempt),
        "ready": ready_bindings,
    }
    bench_go_path = Path(roots["bench_go"])
    if not os.path.lexists(bench_go_path):
        try:
            _exclusive_write(bench_go_path, bench_go)
            _fsync_directory(bench_go_path.parent)
        except PaperStoryError:
            if not os.path.lexists(bench_go_path):
                raise
    bench_go_raw = _read_bytes_once(bench_go_path)
    if (
        bench_go_raw is None
        or _decode_json_bytes(bench_go_raw, "bench-go evidence") != bench_go
    ):
        raise PaperStoryError("bench-go evidence differs from exact ready triple")
    own_ready_raw = _read_bytes_once(ready_path)
    bench_start = {
        "schema_version": V3_BENCH_START_SCHEMA,
        "study_id": _policy_study_id(policy),
        "source_commit": source_commit,
        "attempt_root": os.fspath(attempt),
        "workload": workload,
        "ordinal": ordinal,
        "request_id": reservation["job_id"],
        "bench_go_sha256": _sha256_bytes(bench_go_raw),
        "ready_sha256": _sha256_bytes(own_ready_raw),
        "recorded_epoch": int(time.time()),
    }
    bench_start_path = Path(roots["bench_start"])
    _exclusive_write(bench_start_path, bench_start)
    _fsync_directory(bench_start_path.parent)


def _observation_identity_tag(value: Mapping[str, object]) -> str:
    common = value.get("common_record")
    if type(common) is not dict:
        raise PaperStoryError("observation common record is missing")
    payload = dict(value)
    payload.pop("observation_tag", None)
    try:
        key = campaign_lock_codec.disclosed_identity_key(
            common.get("intent_sha256")
        )
    except campaign_lock_codec.CampaignLockCodecError as exc:
        raise PaperStoryError("observation intent digest is invalid") from exc
    return hmac.new(
        key,
        _OBSERVATION_TAG_DOMAIN + _canonical_json_bytes(payload),
        hashlib.sha256,
    ).hexdigest()


def _validate_observation_intent_binding(
    *,
    common_record: Mapping[str, object],
    receipt: Mapping[str, object],
    source_binding: Mapping[str, object],
    policy: Mapping[str, object] | None = None,
) -> None:
    policy = policy if policy is not None else load_policy()[0]
    study_id = _policy_study_id(policy)
    roots = receipt.get("roots")
    attempt_root = roots.get("attempt_root") if type(roots) is dict else None
    if type(attempt_root) is not str or not Path(attempt_root).is_absolute():
        raise PaperStoryError("non-certifying receipt attempt binding differs")
    attempt = Path(attempt_root)
    raw = _read_bytes_once(_attempt_intent_path(attempt))
    if raw is None:  # pragma: no cover - missing_ok is false
        raise PaperStoryError("non-certifying submission intent is missing")
    intent = _decode_json_bytes(raw, "non-certifying submission intent")
    if _policy_schema(policy) == POLICY_SCHEMA_V3:
        if (
            type(intent) is not dict
            or set(intent) != {
                "schema_version", "study_id", "source_commit", "attempt_root",
                "jobs", "source_binding", "intent_sha256",
            }
            or intent.get("schema_version") != V3_GROUP_INTENT_SCHEMA
            or type(intent.get("jobs")) is not list
            or len(intent["jobs"]) != 3
        ):
            raise PaperStoryError("non-certifying group intent shape differs")
    elif type(intent) is not dict or set(intent) != {
        "schema_version", "study_id", "source_commit", "attempt_root",
        "qsub_argv", "qsub_options", "source_binding", "intent_sha256",
    } or intent.get("schema_version") != SUBMISSION_INTENT_SCHEMA:
        raise PaperStoryError("non-certifying submission intent shape differs")
    if (
        intent.get("study_id") != study_id
        or intent.get("source_commit") != common_record.get("source_commit")
        or intent.get("attempt_root") != attempt_root
        or not _validate_non_certifying_source_binding(
            intent.get("source_binding"), policy,
        )
        or intent.get("source_binding") != source_binding
        or intent.get("intent_sha256") != _submission_intent_digest(intent)
        or intent.get("intent_sha256") != common_record.get("intent_sha256")
    ):
        raise PaperStoryError("non-certifying submission intent binding differs")


def _assert_observation_anomalies_zero(result: Mapping[str, object]) -> None:
    workloads = result.get("workloads")
    if type(workloads) is not list or len(workloads) != len(WORKLOAD_ORDER):
        raise PaperStoryError("non-certifying anomaly evidence set differs")
    verify_count = 0
    for workload in workloads:
        wal_evidence = (
            workload.get("wal_evidence") if type(workload) is dict else None
        )
        records = wal_evidence.get("records") if type(wal_evidence) is dict else None
        if type(records) is not list:
            raise PaperStoryError("non-certifying anomaly evidence is missing")
        for record in records:
            if type(record) is not dict or record.get("stage") != STAGE_VERIFY_DONE:
                continue
            payload = record.get("payload")
            anomalies = payload.get("anomalies") if type(payload) is dict else None
            if type(anomalies) is not int or anomalies != 0:
                raise PaperStoryError("non-certifying observation anomalies are nonzero")
            verify_count += 1
    expected = len(WORKLOAD_ORDER) * len(ARM_ORDER) * len(EXPECTED_VERIFY_CONFIGS)
    if verify_count != expected:
        raise PaperStoryError("non-certifying anomaly evidence cardinality differs")


def _read_observation_binding(binding: object, *, label: str) -> bytes:
    if type(binding) is not dict or set(binding) != {"path", "sha256"}:
        raise PaperStoryError(f"non-certifying {label} binding differs")
    raw_path = binding.get("path")
    digest = binding.get("sha256")
    if (
        type(raw_path) is not str
        or not Path(raw_path).is_absolute()
        or type(digest) is not str
        or _FULL_SHA256.fullmatch(digest) is None
    ):
        raise PaperStoryError(f"non-certifying {label} binding differs")
    raw = _read_bytes_once(Path(raw_path))
    if raw is None or _sha256_bytes(raw) != digest:
        raise PaperStoryError(f"non-certifying {label} digest differs")
    return raw


def _issue_non_certifying_observation(
    *,
    common_record: Mapping[str, object],
    source_binding: Mapping[str, object],
    workloads: Sequence[Mapping[str, object]],
    result_path: Path,
    receipt_path: Path,
) -> Path:
    campaigns = []
    for workload in workloads:
        binding = workload.get("campaign_binding")
        wal_evidence = workload.get("wal_evidence")
        if type(binding) is not dict or type(wal_evidence) is not dict:
            raise PaperStoryError("observation workload binding is missing")
        campaigns.append({
            "workload": workload.get("workload"),
            "campaign_id": workload.get("campaign_id"),
            "campaign_lock": {
                "path": binding.get("campaign_lock_path"),
                "sha256": binding.get("campaign_lock_sha256"),
            },
            "wal": {
                "path": wal_evidence.get("path"),
                "sha256": wal_evidence.get("sha256"),
            },
        })
    sidecar = {
        "schema_version": NON_CERTIFYING_OBSERVATION_SCHEMA,
        "common_record": dict(common_record),
        "source_binding": dict(source_binding),
        "campaigns": campaigns,
        "result": {
            "path": os.fspath(result_path),
            "sha256": _sha256_file(result_path),
        },
        "receipt": {
            "path": os.fspath(receipt_path),
            "sha256": _sha256_file(receipt_path),
        },
    }
    sidecar["observation_tag"] = _observation_identity_tag(sidecar)
    sidecar_path = result_path.parent / NON_CERTIFYING_OBSERVATION_FILENAME
    _exclusive_write(sidecar_path, sidecar)
    _fsync_directory(sidecar_path.parent)
    return sidecar_path


def _validate_non_certifying_observation_contents(
    sidecar_path: Path,
) -> dict[str, object]:
    """Completion receipt に依存しない sidecar と測定 bytes を再検証する。"""
    path = Path(sidecar_path).resolve(strict=True)
    value = _read_json(path)
    if type(value) is not dict or set(value) != {
        "schema_version", "common_record", "source_binding", "campaigns",
        "result", "receipt", "observation_tag",
    }:
        raise PaperStoryError("non-certifying observation shape differs")
    if value.get("schema_version") != NON_CERTIFYING_OBSERVATION_SCHEMA:
        raise PaperStoryError("non-certifying observation schema differs")
    expected_tag = _observation_identity_tag(value)
    if (
        type(value.get("observation_tag")) is not str
        or not hmac.compare_digest(value["observation_tag"], expected_tag)
    ):
        raise PaperStoryError("non-certifying observation tag mismatch")
    common = value.get("common_record")
    campaigns = value.get("campaigns")
    if (
        type(common) is not dict
        or type(campaigns) is not list
        or len(campaigns) != 3
        or [item.get("workload") for item in campaigns if type(item) is dict]
        != list(WORKLOAD_ORDER)
    ):
        raise PaperStoryError("non-certifying observation campaign set differs")
    for ordinal, item in enumerate(campaigns):
        if type(item) is not dict or set(item) != {
            "workload", "campaign_id", "campaign_lock", "wal",
        }:
            raise PaperStoryError("non-certifying campaign binding shape differs")
        lock_raw = _read_observation_binding(
            item["campaign_lock"], label="campaign_lock",
        )
        try:
            lock_text = lock_raw.decode("utf-8")
            decoded = campaign_lock_codec.decode_non_certifying_campaign_lock(
                lock_text
            )
        except (UnicodeError, campaign_lock_codec.CampaignLockCodecError) as exc:
            raise PaperStoryError("non-certifying campaign lock is invalid") from exc
        if (
            decoded.common_record != common
            or decoded.workload_binding != {
                "workload": item["workload"],
                "campaign_id": item["campaign_id"],
                "ordinal": ordinal,
            }
        ):
            raise PaperStoryError("non-certifying lock/workload binding differs")
        _read_observation_binding(item["wal"], label="wal")
    references = {}
    for label in ("result", "receipt"):
        raw = _read_observation_binding(value[label], label=label)
        references[label] = _decode_json_bytes(raw, label)
    result = references["result"]
    receipt = references["receipt"]
    result_study_id = result.get("study_id") if type(result) is dict else None
    policy, policy_sha = _load_policy_for_study(result_study_id)
    study_id = _policy_study_id(policy)
    policy_relative = _policy_relative_path(policy)
    preregistration_sha = policy["preregistration"]["sha256"]
    result_keys = (
        _V3_NON_CERTIFYING_RESULT_KEYS
        if _policy_schema(policy) == POLICY_SCHEMA_V3
        else _NON_CERTIFYING_RESULT_KEYS
    )
    receipt_keys = (
        _V3_NON_CERTIFYING_RECEIPT_KEYS
        if _policy_schema(policy) == POLICY_SCHEMA_V3
        else _NON_CERTIFYING_RECEIPT_KEYS
    )
    expected_route = (
        "direct-qsub-workload-fanout"
        if _policy_schema(policy) == POLICY_SCHEMA_V3
        else "direct-qsub"
    )
    if (
        set(result) != result_keys
        or set(receipt) != receipt_keys
        or result.get("schema_version") != RESULT_SCHEMA
        or receipt.get("schema_version") != RECEIPT_SCHEMA
        or result.get("study_id") != study_id
        or receipt.get("study_id") != study_id
        or result.get("formal") is not False
        or result.get("promotion_prohibited") is not True
        or result.get("authority") != "exploratory"
        or result.get("pairing_design") != _pairing_design(policy)
        or receipt.get("formal") is not False
        or receipt.get("promotion_prohibited") is not True
        or receipt.get("route") != expected_route
        or receipt.get("policy") != {
            "path": policy_relative,
            "sha256": policy_sha,
        }
        or receipt.get("result") != {
            "path": value["result"]["path"],
            "sha256": value["result"]["sha256"],
            "complete": result.get("complete"),
            "all_workloads_terminal": result.get("all_workloads_terminal"),
        }
    ):
        raise PaperStoryError("non-certifying result/receipt authority differs")
    source_binding = value.get("source_binding")
    result_source_binding = result.get("source_binding")
    if (
        not _validate_non_certifying_source_binding(source_binding, policy)
        or common.get("source_binding_sha256")
        != _sha256_bytes(
            campaign_lock_codec.canonical_json(source_binding).encode("utf-8")
        )
        or not _validate_source_binding(result_source_binding, policy)
        or receipt.get("source_binding") != result_source_binding
        or common.get("mode")
        != trial_registry.REGISTERED_FORMAL_NON_CERTIFYING_MODE
        or common.get("certifying") is not False
        or common.get("policy_sha256") != policy_sha
        or common.get("policy_sha256") != result.get("policy_sha256")
        or common.get("preregistration_sha256") != preregistration_sha
        or common.get("study_id") != study_id
        or common.get("study_id") != result.get("study_id")
        or common.get("source_commit")
        != source_binding.get("measurement_source_commit")
        or common.get("source_commit")
        != result_source_binding.get("measurement_source_commit")
    ):
        raise PaperStoryError("non-certifying common/source binding differs")
    _validate_observation_intent_binding(
        common_record=common,
        receipt=receipt,
        source_binding=source_binding,
        policy=policy,
    )
    result_workloads = result.get("workloads")
    if type(result_workloads) is not list or len(result_workloads) != 3:
        raise PaperStoryError("non-certifying result workload set differs")
    expected_campaigns = []
    for item in result_workloads:
        campaign_binding = item.get("campaign_binding") if type(item) is dict else None
        wal_evidence = item.get("wal_evidence") if type(item) is dict else None
        if type(campaign_binding) is not dict or type(wal_evidence) is not dict:
            raise PaperStoryError("non-certifying result campaign binding is missing")
        expected_campaigns.append({
            "workload": item.get("workload"),
            "campaign_id": item.get("campaign_id"),
            "campaign_lock": {
                "path": campaign_binding.get("campaign_lock_path"),
                "sha256": campaign_binding.get("campaign_lock_sha256"),
            },
            "wal": {
                "path": wal_evidence.get("path"),
                "sha256": wal_evidence.get("sha256"),
            },
        })
    if campaigns != expected_campaigns:
        raise PaperStoryError("non-certifying sidecar/result campaign binding differs")
    if common.get("campaign_ids") != [
        item["campaign_id"] for item in expected_campaigns
    ]:
        raise PaperStoryError("non-certifying common campaign IDs differ")
    _revalidate_raw_wals(result, receipt, policy)
    _assert_observation_anomalies_zero(result)
    if (
        result.get("complete") is not True
        or result.get("all_workloads_terminal") is not True
        or any(item.get("valid") is not True for item in result_workloads)
    ):
        raise PaperStoryError("non-certifying observation is not complete and valid")
    return {
        "sidecar_path": path,
        "result_path": Path(value["result"]["path"]),
        "receipt_path": Path(value["receipt"]["path"]),
        "common_record": common,
        "source_binding": source_binding,
        "campaigns": campaigns,
        "result": result,
        "receipt": receipt,
    }


def _validate_raw_non_certifying_observation_for_completion(
    sidecar_path: Path,
    *,
    expected_head: str,
    attempt: Path,
    request_id: str,
) -> None:
    """``run_complete`` 専用の、completion 非依存 sidecar gate。"""
    validated = _validate_non_certifying_observation_contents(sidecar_path)
    common = validated["common_record"]
    receipt = validated["receipt"]
    policy = _load_policy_for_study(common.get("study_id"))[0]
    roots = receipt.get("roots") if type(receipt) is dict else None
    if (
        type(common) is not dict
        or common.get("source_commit") != expected_head
        or type(receipt) is not dict
        or _validated_request_id(receipt.get("pbs_jobid"), "raw receipt PBS_JOBID")
        != _validated_request_id(request_id, "completion request ID")
        or type(roots) is not dict
        or roots.get("attempt_root") != os.fspath(attempt)
        or Path(validated["sidecar_path"])
        != Path(roots.get("result_root", "")) / NON_CERTIFYING_OBSERVATION_FILENAME
    ):
        raise PaperStoryError("raw non-certifying observation completion binding differs")
    _verify_current_source_paths(
        _repo_root().resolve(strict=True),
        expected_head,
        validated["source_binding"],
        relative_paths=_source_relative_paths(policy, non_certifying=True),
        label="non-certifying observation",
    )


def _validate_completed_non_certifying_observation(
    validated: Mapping[str, object],
) -> None:
    """Final view 発行前に scheduler と job の実 bytes を再検証する。"""
    repo_root = _repo_root().resolve(strict=True)
    common = validated["common_record"]
    result = validated["result"]
    receipt = validated["receipt"]
    if not all(type(value) is dict for value in (common, result, receipt)):
        raise PaperStoryError("non-certifying final observation shape differs")
    expected_head = common.get("source_commit")
    if type(expected_head) is not str:
        raise PaperStoryError("non-certifying final source commit is missing")
    policy, policy_sha = _load_policy_for_study(common.get("study_id"))
    study_id = _policy_study_id(policy)
    _verify_current_source_paths(
        repo_root,
        expected_head,
        validated["source_binding"],
        relative_paths=_source_relative_paths(policy, non_certifying=True),
        label="non-certifying observation",
    )
    roots = receipt.get("roots")
    if type(roots) is not dict:
        raise PaperStoryError("non-certifying final roots are missing")
    if _policy_schema(policy) == POLICY_SCHEMA_V3:
        terminal_path = Path(roots.get("group_terminal", ""))
        terminal_raw = _read_bytes_once(terminal_path, missing_ok=True)
        if terminal_raw is None:
            raise PaperStoryError("non-certifying group terminal is missing")
        terminal = _decode_json_bytes(
            terminal_raw, "non-certifying group terminal",
        )
        validate_raw_documents(result, receipt, terminal, policy)
        acquisition_raw = _read_observation_binding(
            receipt.get("submission_receipt"), label="submission receipt",
        )
        acquisition = _validate_v3_group_submission(
            _decode_json_bytes(acquisition_raw, "group submission receipt"),
            repo_root=repo_root, policy=policy, source_commit=expected_head,
            attempt=Path(roots["attempt_root"]),
        )
        completion_path = Path(roots["completion_receipt"])
        completion_raw = _read_bytes_once(completion_path, missing_ok=True)
        if completion_raw is None:
            raise PaperStoryError("non-certifying group completion is missing")
        _validate_v3_group_completion(
            _decode_json_bytes(completion_raw, "group completion receipt"),
            policy=policy, source_commit=expected_head,
            attempt=Path(roots["attempt_root"]), submission=acquisition,
            submission_sha256=_sha256_bytes(acquisition_raw),
            group_terminal_sha256=_sha256_bytes(terminal_raw),
        )
        if result.get("policy_sha256") != policy_sha:
            raise PaperStoryError("non-certifying final policy hash differs")
        return
    terminal_path = Path(roots.get("raw_root", "")) / "job-terminal.json"
    terminal_raw = _read_bytes_once(terminal_path, missing_ok=True)
    if terminal_raw is None:
        raise PaperStoryError("non-certifying job terminal is missing")
    terminal = _decode_json_bytes(terminal_raw, "non-certifying job terminal")
    validate_raw_documents(result, receipt, terminal, policy)

    acquisition_binding = receipt.get("submission_receipt")
    acquisition_raw = _read_observation_binding(
        acquisition_binding, label="submission receipt",
    )
    acquisition = _decode_json_bytes(
        acquisition_raw, "non-certifying submission receipt",
    )
    trusted_roots = validate_acquisition_receipt(
        acquisition,
        repo_root=repo_root,
        study_id=study_id,
        source_commit=expected_head,
        request_id=receipt.get("pbs_jobid"),
        pbs_observation=terminal.get("pbs_observation"),
        policy=policy,
    )
    _revalidate_attempt_root(roots)
    if roots != trusted_roots:
        raise PaperStoryError("non-certifying final roots differ from submission")
    if Path(validated["sidecar_path"]) != (
        Path(trusted_roots["result_root"]) / NON_CERTIFYING_OBSERVATION_FILENAME
    ):
        raise PaperStoryError("non-certifying sidecar path differs from submission")
    if (
        Path(validated["result_path"])
        != Path(trusted_roots["result_root"]) / "result.json"
        or Path(validated["receipt_path"])
        != Path(trusted_roots["result_root"]) / "receipt.json"
    ):
        raise PaperStoryError("non-certifying raw document path differs from submission")

    completion_binding = receipt.get("scheduler_completion_receipt")
    if completion_binding != {"path": trusted_roots["completion_receipt"]}:
        raise PaperStoryError("non-certifying completion receipt binding differs")
    completion_path = Path(trusted_roots["completion_receipt"])
    completion_raw = _read_bytes_once(completion_path, missing_ok=True)
    if completion_raw is None:
        raise PaperStoryError("non-certifying completion receipt is missing")
    completion = _decode_json_bytes(
        completion_raw, "non-certifying completion receipt",
    )
    validate_completion_receipt(
        completion,
        trusted_roots=trusted_roots,
        source_commit=expected_head,
        request_id=receipt.get("pbs_jobid"),
        submission_receipt=acquisition,
        submission_receipt_sha256=acquisition_binding["sha256"],
        job_terminal_sha256=_sha256_bytes(terminal_raw),
        study_id=study_id,
    )
    if result.get("policy_sha256") != policy_sha:
        raise PaperStoryError("non-certifying final policy hash differs")
    if terminal.get("result_sha256") != _sha256_file(Path(validated["result_path"])):
        raise PaperStoryError("non-certifying terminal result hash differs")
    if terminal.get("receipt_sha256") != _sha256_file(
        Path(validated["receipt_path"])
    ):
        raise PaperStoryError("non-certifying terminal receipt hash differs")


def consume_non_certifying_observation(
    sidecar_path: Path,
) -> NonCertifyingObservationView:
    """全測定・scheduler bytes の再検証後にだけ A-1 局所 view を発行する。"""
    validated = _validate_non_certifying_observation_contents(sidecar_path)
    _validate_completed_non_certifying_observation(validated)
    return NonCertifyingObservationView(
        sidecar_path=validated["sidecar_path"],
        common_record=_freeze_json(dict(validated["common_record"])),
        campaigns=tuple(
            _freeze_json(dict(item)) for item in validated["campaigns"]
        ),
        result=_freeze_json(dict(validated["result"])),
        receipt=_freeze_json(dict(validated["receipt"])),
        _token=_NON_CERTIFYING_VIEW_TOKEN,
    )


def _persist_v3_condition_gate_record(
    output_path: Path, canonical_bytes: bytes,
) -> None:
    """Publish one complete record using the D1912 durability sequence."""
    temporary_path: Path | None = None
    try:
        temporary_path = output_path.parent / (
            f".{output_path.name}.tmp-{os.getpid()}-{secrets.token_hex(16)}"
        )
        with temporary_path.open("xb") as output:
            output.write(canonical_bytes)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary_path, output_path)
        descriptor = os.open(
            output_path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
        )
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except Exception:
                pass


def _require_v3_backoff_fixed_condition_gate(
    *,
    repo_root: Path,
    policy: Mapping[str, object],
    workload: str,
    cxx: str,
    cc: str | None = None,
    evidence_root: Path | None = None,
    source_root: Path | None = None,
    stock_root: Path | None = None,
    dependency_prefix: str = "",
    dependency_options: dict | None = None,
) -> None:
    """Require live supply and meaning records for every v3 fixed-backoff arm."""
    values = tuple(dict.fromkeys(
        genome.flags["BACKOFF_FIXED"]
        for genome in genomes(policy, workload)
    ))
    try:
        source_root = source_root or (repo_root / "external" / "ccbench").resolve(strict=True)
        stock_context = (nullcontext(stock_root) if stock_root is not None else
                         patchharness.checkout(CANONICAL_CCBENCH_OID, base_dir=os.fspath(source_root)))
        with stock_context as stock_root:
            supply_records = []
            meaning_records = []
            for value in values:
                genome = next(g for g in genomes(policy, workload) if g.flags["BACKOFF_FIXED"] == value)
                configure_args = (
                    "-DCMAKE_BUILD_TYPE=Release", "-DENABLE_SANITIZER=OFF",
                    *([f"-DCMAKE_C_COMPILER={cc}"] if cc else []),
                    *([f"-DCMAKE_PREFIX_PATH={dependency_prefix}"] if dependency_prefix else []),
                    *(a1_source.configure_dependencies(dependency_options) if dependency_options else ()),
                    *(f"-DCCBENCH_{key}={genome.flags[key]}" for key in sorted(genome.flags)
                      if key != "BACKOFF_FIXED"), "-DCCBENCH_TRACE=0",
                )
                captured = condition_meaning_gate.capture_define_inputs(
                    source_root, stock_root=stock_root, configure_args=configure_args,
                )
                request = condition_meaning_gate.make_define_request(
                    driver_id=(
                        "orchestrator.campaign.paper_story_a1_paired:"
                        f"v3-{workload}"
                    ),
                    macro="BACKOFF_FIXED",
                    requested_value=value,
                    default_value=-1,
                    stock_comparison=value == -1,
                )
                if value == -1:
                    meaning_case = condition_meaning_gate.MeaningCase(
                        -1,
                        None,
                        expected_selected_branch=(
                            condition_meaning_gate.STOCK_ADAPTIVE_BRANCH
                        ),
                    )
                else:
                    bits = struct.pack(">d", float(value)).hex()
                    meaning_case = condition_meaning_gate.MeaningCase(
                        value, (bits, bits),
                    )
                declaration = condition_meaning_gate.MeaningWitnessDeclaration(
                    "BACKOFF_FIXED", (meaning_case,),
                )
                supply_records.append(
                    condition_meaning_gate.evaluate_define_supply_effectuation(
                        captured, request=request, cxx=cxx, cmake="cmake",
                    )
                )
                meaning_records.append(
                    condition_meaning_gate.evaluate_define_runtime_meaning(
                        captured,
                        request=request,
                        declaration=declaration,
                        cxx=cxx,
                    )
                )
            admission = condition_meaning_gate.require_condition_gate_family(
                supply_records, meaning_records, use_class="paper",
            )
    except (OSError, RuntimeError) as exc:
        raise PaperStoryError(
            f"v3 BACKOFF_FIXED condition gate could not run: {exc}"
        ) from exc
    if not admission.admitted:
        rejected = ",".join(
            f"{record.arm}:{record.reason_code}"
            for record in (*supply_records, *meaning_records)
            if record.terminal_status != "green"
        )
        rejection = (
            "v3 BACKOFF_FIXED condition gate rejected measurement: "
            f"{rejected or 'admission-not-granted'}"
        )
        if evidence_root is not None:
            failures = []
            for label, records in (
                ("supply", supply_records), ("meaning", meaning_records),
            ):
                for index, record in enumerate(records):
                    try:
                        output_path = evidence_root / (
                            f"condition-gate-{record.arm}-{record.record_digest}.json"
                        )
                        _persist_v3_condition_gate_record(
                            output_path, record.canonical_json().encode("ascii"),
                        )
                    except Exception as exc:
                        failures.append(f"{label}[{index}]:{type(exc).__name__}")
            try:
                output_path = evidence_root / (
                    f"condition-gate-admission-{admission.admission_digest}.json"
                )
                _persist_v3_condition_gate_record(
                    output_path, admission.canonical_json().encode("ascii"),
                )
            except Exception as exc:
                failures.append(f"admission:{type(exc).__name__}")
            if failures:
                rejection += "; evidence_write_failures=" + ",".join(failures)
        raise PaperStoryError(rejection)


def _run_measurement_v3(
    args,
    *,
    repo_root: Path,
    policy: Mapping[str, object],
    policy_sha: str,
) -> int:
    workload = getattr(args, "workload", None)
    if workload not in WORKLOAD_ORDER:
        raise PaperStoryError("v3 measure requires one exact workload selector")
    study_id = _policy_study_id(policy)
    acquisition_path = Path(args.acquisition_receipt)
    if not acquisition_path.is_absolute() or acquisition_path.resolve(
        strict=True
    ) != acquisition_path:
        raise PaperStoryError("acquisition receipt path must be canonical absolute")
    acquisition_raw = _read_bytes_once(acquisition_path)
    acquisition_sha = _sha256_bytes(acquisition_raw)
    if acquisition_sha != args.acquisition_receipt_sha256:
        raise PaperStoryError("acquisition receipt bytes differ from job binding")
    acquisition = _decode_json_bytes(acquisition_raw, "group acquisition receipt")
    trusted_roots = validate_acquisition_receipt(
        acquisition,
        repo_root=repo_root,
        study_id=study_id,
        source_commit=args.expected_head,
        request_id=args.pbs_jobid,
        pbs_observation=_pbs_environment_observation(),
        policy=policy,
        workload=workload,
    )
    attempt = Path(trusted_roots["attempt_root"])
    submission_intent = _measurement_intent(
        acquisition=acquisition,
        repo_root=repo_root,
        attempt=attempt,
        source_commit=args.expected_head,
        policy=policy,
        workload=workload,
    )
    if os.fspath(acquisition_path) != trusted_roots["submission_receipt"]:
        raise PaperStoryError("group receipt path differs from durable topology")
    roots = validate_measure_environment(
        repo_root=repo_root,
        expected_head=args.expected_head,
        output_root=Path(args.output_root),
        cache_root=Path(args.cache_root),
        result_root=Path(args.result_root),
        pbs_jobid=args.pbs_jobid,
        site=site_policy.current_site(),
        observed_head=_run_git(repo_root, "rev-parse", "HEAD"),
        porcelain=_parent_porcelain(repo_root, policy),
        attempt_root=attempt,
        workload=workload,
    )
    if any(roots[key] != trusted_roots[key] for key in roots):
        raise PaperStoryError("CLI roots differ from workload acquisition topology")
    roots = dict(trusted_roots)
    dependency_prefix = _validated_dependency_prefix(
        args.dependency_prefix, require_scr=True,
    )
    reservation = _reservation_binding_from_environment(os.environ)
    ordinal = WORKLOAD_ORDER.index(workload)
    if reservation["nonce"] != f"{attempt.name}.{workload}":
        raise PaperStoryError("workload reservation nonce differs")
    submission_job = acquisition["jobs"][ordinal]
    if _validated_request_id(
        reservation["job_id"], "reservation job ID",
    ) != _validated_request_id(
        submission_job["request_id"], "submission request ID",
    ):
        raise PaperStoryError("workload reservation request ID differs")

    site, contract, authorization = p2_2.resolve_site_runtime()
    if site != site_policy.PEGASUS_COMPUTE:
        raise PaperStoryError("resolved runtime is not Pegasus compute")
    loaded_calibration = p2_2._assert_matches_calibration(contract)
    _prepare_runtime_roots(roots, contract.env_tag)
    source_binding = _source_binding(repo_root, args.expected_head, policy)
    non_certifying_source_binding = _non_certifying_source_binding(
        repo_root, args.expected_head, policy,
    )
    build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    resolved_cc, resolved_cxx = buildcache.compilers_for_current_site()
    toolchain_manifest = buildcache.observed_toolchain_manifest(
        resolved_cc, resolved_cxx,
    )
    durable_policy = DurableRootPolicy(
        approved_roots=(Path(roots["output_root"]).resolve(),),
        forbidden_roots=(),
    )
    campaign_configs = tuple(
        ident.bind_admission_policy(
            p2_2._campaign_cfg_for_site(
                campaign_config(
                    policy, name, contract=contract, non_certifying=True,
                ),
                site,
                contract,
            ),
            build_context.policy,
        )
        for name in WORKLOAD_ORDER
    )
    campaign_ids = tuple(str(ident.campaign_id(cfg)) for cfg in campaign_configs)
    projection = trial_registry.issue_a1_registered_noncertifying_projection(
        study_id=study_id,
        policy_sha256=policy_sha,
        preregistration_sha256=policy["preregistration"]["sha256"],
        source_commit=args.expected_head,
        workloads=WORKLOAD_ORDER,
        campaign_ids=campaign_ids,
    )
    common_record = _a1_common_record(
        projection,
        source_binding=non_certifying_source_binding,
        environment_contract_sha256=contract.contract_sha256,
        intent_sha256=submission_intent["intent_sha256"],
    )
    layout = _preseed_v3_workload_lock(
        configs=campaign_configs,
        campaign_ids=campaign_ids,
        workload=workload,
        output_root=roots["output_root"],
        common_record=common_record,
    )
    cfg = campaign_configs[ordinal]
    campaign_preimage = ident.canonical_preimage(cfg)
    perf = PerfConfig(
        records=policy["scale"]["records"],
        threads=policy["scale"]["threads"],
        workload=workload_flags(policy, workload),
        extime=policy["scale"]["extime_s"],
        reps=_expected_reps(policy, workload),
    )

    def capability_resolver(evidence):
        generator_input = (
            f"paper-story-a1-paired/v1|{study_id}|{workload}|"
            f"{evidence.genome_sha256}"
        ).encode("utf-8")
        return attest_generator_output(
            build_context,
            evidence,
            generator_input_sha256=_sha256_bytes(generator_input),
        )

    execution_options = _require_registered_execution_options(
        policy, workload, _campaign_execution_options(policy, workload),
    )
    contract_source = a1_source.load_contract(repo_root, study_id)
    if study_id != contract_source["study_id"]:
        raise PaperStoryError("A1 source amendment study differs")
    if study_id == V3_PILOT_STUDY_ID and attempt.name != contract_source["attempt"]:
        raise PaperStoryError("A1 source amendment requires pilot attempt-0004")
    expected_hydrate = submission_intent["jobs"][ordinal]["qsub_options"]["variables"].get(
        "IZANAGI_A1_THIRD_PARTY_SOURCE_ROOT")
    if not expected_hydrate or os.environ.get("IZANAGI_A1_THIRD_PARTY_SOURCE_ROOT") != expected_hydrate:
        raise PaperStoryError("third-party source origin differs from intent")
    staged_root = Path(args.third_party_source_root).resolve(strict=True)
    prefix_parent = _dependency_prefix_components(dependency_prefix)[0].parent
    if staged_root != prefix_parent / "fetchcontent":
        raise PaperStoryError("third-party staged root differs from dependency scratch")
    with a1_source.materialized(repo_root, study_id=study_id) as (source_context, stock_root):
        dependency_options = a1_source.prepare_dependencies(
            root=staged_root, source=source_context.root,
            repo_root=repo_root, dependency_prefix=dependency_prefix,
            toolchain=toolchain_manifest,
        )
        _require_v3_backoff_fixed_condition_gate(
            repo_root=repo_root,
            policy=policy,
            workload=workload,
            cxx=resolved_cxx, cc=resolved_cc,
            evidence_root=Path(roots["raw_root"]),
            source_root=source_context.root, stock_root=stock_root,
            dependency_prefix=dependency_prefix, dependency_options=dependency_options,
        )
        original_balanced_executor = campaign_loop._run_balanced_schedule

        def gated_balanced_executor(prepared_arms, schedule):
            _v3_barrier_before_bench(
                prepared_arms=prepared_arms,
                workload=workload,
                campaign_id=campaign_ids[ordinal],
                policy=policy,
                source_commit=args.expected_head,
                attempt=attempt,
                submission=acquisition,
                reservation=reservation,
                timeout_s=max(
                    0.0, float(reservation["deadline_epoch"]) - time.time() - 60.0,
                ),
            )
            return original_balanced_executor(prepared_arms, schedule)

        campaign_loop._run_balanced_schedule = gated_balanced_executor
        try:
            _assert_single_tenant()
            summary = run_campaign(
                cfg,
                genomes(policy, workload),
                perf,
                contract.env_tag,
                contract.clocks_per_us,
                numactl=list(contract.numactl),
                output_root=roots["output_root"],
                cache_root=roots["cache_root"],
                dependency_prefix=dependency_prefix,
                ccbench_dir=os.fspath(source_context.root),
                a1_source_context=source_context,
                **dependency_options,
                authorization_contract=authorization,
                env_contract=contract,
                expected_toolchain_manifest=toolchain_manifest,
                build_context=build_context,
                declared_use_class=DECLARED_USE_CLASS,
                capability_resolver=capability_resolver,
                durable_root_policy=durable_policy,
                **execution_options,
            )
        finally:
            campaign_loop._run_balanced_schedule = original_balanced_executor
        collected = collect_workload(
            policy,
            workload_name=workload,
            campaign_id=summary.campaign_id,
            layout=CampaignLayout(summary.layout_root),
            admission_policy=build_context.policy,
            env_tag=contract.env_tag,
            source_binding=source_binding,
            summary=summary,
            expected_campaign_preimage=campaign_preimage,
            expected_layout_root=layout.root,
            expected_schedule_receipt=summary.balanced_schedule_receipt,
        )
    if not _workload_has_terminal_result(collected):
        raise PaperStoryError("workload did not produce one terminal shard")
    shard = {
        "schema_version": V3_WORKLOAD_SHARD_SCHEMA,
        "study_id": study_id,
        "workload": workload,
        "ordinal": ordinal,
        "campaign_id": campaign_ids[ordinal],
        "campaign_ids": list(campaign_ids),
        "common_record": common_record,
        "source_binding": source_binding,
        "non_certifying_source_binding": non_certifying_source_binding,
        "reservation_binding": reservation,
        "workload_result": collected,
    }
    _revalidate_attempt_root(roots)
    result_path = Path(roots["result_root"]) / "result.json"
    _exclusive_write(result_path, shard)
    receipt = {
        "schema_version": V3_WORKLOAD_RECEIPT_SCHEMA,
        "study_id": study_id,
        "workload": workload,
        "ordinal": ordinal,
        "pbs_jobid": args.pbs_jobid,
        "host": socket.gethostname(),
        "recorded_epoch": int(time.time()),
        "policy": {
            "path": _policy_relative_path(policy),
            "sha256": policy_sha,
        },
        "source_binding": source_binding,
        "submission_receipt": {
            "path": os.fspath(acquisition_path),
            "sha256": acquisition_sha,
        },
        "roots": roots,
        "result": {
            "path": os.fspath(result_path),
            "sha256": _sha256_file(result_path),
        },
        "calibration_sha256": getattr(loaded_calibration, "sha256", None),
    }
    _exclusive_write(Path(roots["result_root"]) / "receipt.json", receipt)
    return 0


def run_measurement(args) -> int:
    repo_root = _repo_root()
    policy, policy_sha = _load_policy_for_study(args.study_id)
    study_id = _policy_study_id(policy)
    if args.study_id != study_id:
        raise PaperStoryError("study ID differs from the preregistered ID")
    _require_policy_ready_for_execution(policy)
    _assert_ccbench_acceptance(
        repo_root, policy, boundary="driver-measurement",
    )
    if _policy_schema(policy) == POLICY_SCHEMA_V3:
        return _run_measurement_v3(
            args, repo_root=repo_root, policy=policy, policy_sha=policy_sha,
        )
    if getattr(args, "workload", None) is not None:
        raise PaperStoryError("v2 measure does not accept --workload")
    acquisition_path = Path(args.acquisition_receipt)
    if not acquisition_path.is_absolute() or acquisition_path.resolve(
        strict=True
    ) != acquisition_path:
        raise PaperStoryError("acquisition receipt path must be canonical absolute")
    acquisition_raw = _read_bytes_once(acquisition_path)
    if acquisition_raw is None:  # pragma: no cover - missing_ok is false
        raise PaperStoryError("acquisition receipt is missing")
    acquisition_sha = _sha256_bytes(acquisition_raw)
    if acquisition_sha != args.acquisition_receipt_sha256:
        raise PaperStoryError("acquisition receipt bytes differ from job binding")
    acquisition = _decode_json_bytes(acquisition_raw, "acquisition receipt")
    trusted_roots = validate_acquisition_receipt(
        acquisition,
        repo_root=repo_root,
        study_id=args.study_id,
        source_commit=args.expected_head,
        request_id=args.pbs_jobid,
        pbs_observation=_pbs_environment_observation(),
        policy=policy,
    )
    submission_intent = _measurement_intent(
        acquisition=acquisition,
        repo_root=repo_root,
        attempt=Path(trusted_roots["attempt_root"]),
        source_commit=args.expected_head,
        policy=policy,
    )
    if os.fspath(acquisition_path) != trusted_roots["submission_receipt"]:
        raise PaperStoryError("submission receipt path differs from durable topology")
    observed_head = _run_git(repo_root, "rev-parse", "HEAD")
    porcelain = _parent_porcelain(repo_root, policy)
    current_site = site_policy.current_site()
    roots = validate_measure_environment(
        repo_root=repo_root,
        expected_head=args.expected_head,
        output_root=Path(args.output_root),
        cache_root=Path(args.cache_root),
        result_root=Path(args.result_root),
        pbs_jobid=args.pbs_jobid,
        site=current_site,
        observed_head=observed_head,
        porcelain=porcelain,
        attempt_root=Path(trusted_roots["attempt_root"]),
    )
    if any(roots[key] != trusted_roots[key] for key in roots):
        raise PaperStoryError("CLI roots differ from acquisition receipt topology")
    roots = dict(trusted_roots)
    dependency_prefix = _validated_dependency_prefix(
        args.dependency_prefix, require_scr=True
    )
    reservation_binding = _reservation_binding_from_environment(os.environ)
    site, contract, authorization = p2_2.resolve_site_runtime()
    if site != site_policy.PEGASUS_COMPUTE:
        raise PaperStoryError("resolved runtime is not Pegasus compute")
    loaded_calibration = p2_2._assert_matches_calibration(contract)
    _prepare_runtime_roots(roots, contract.env_tag)
    source_binding = _source_binding(repo_root, args.expected_head, policy)
    non_certifying_source_binding = _non_certifying_source_binding(
        repo_root, args.expected_head, policy,
    )
    build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    resolved_cc, resolved_cxx = buildcache.compilers_for_current_site()
    toolchain_manifest = buildcache.observed_toolchain_manifest(
        resolved_cc, resolved_cxx
    )
    durable_policy = DurableRootPolicy(
        approved_roots=(Path(roots["output_root"]).resolve(),),
        forbidden_roots=(),
    )

    # All three identities are fixed before the first lock is issued.
    campaign_configs = tuple(
        ident.bind_admission_policy(
            p2_2._campaign_cfg_for_site(
                campaign_config(
                    policy,
                    workload_name,
                    contract=contract,
                    non_certifying=True,
                ),
                site,
                contract,
            ),
            build_context.policy,
        )
        for workload_name in WORKLOAD_ORDER
    )
    campaign_ids = tuple(
        str(ident.campaign_id(cfg)) for cfg in campaign_configs
    )
    projection = trial_registry.issue_a1_registered_noncertifying_projection(
        study_id=study_id,
        policy_sha256=policy_sha,
        preregistration_sha256=policy["preregistration"]["sha256"],
        source_commit=args.expected_head,
        workloads=WORKLOAD_ORDER,
        campaign_ids=campaign_ids,
    )
    common_record = _a1_common_record(
        projection,
        source_binding=non_certifying_source_binding,
        environment_contract_sha256=contract.contract_sha256,
        intent_sha256=submission_intent["intent_sha256"],
    )
    campaign_layouts = tuple(
        exploration_campaign_layout(campaign_id, roots["output_root"])
        for campaign_id in campaign_ids
    )
    _preseed_a1_non_certifying_locks(
        configs=campaign_configs,
        layouts=campaign_layouts,
        workloads=WORKLOAD_ORDER,
        common_record=common_record,
    )

    workload_results = []
    measurement_error = None
    for workload_name, cfg, campaign_id, layout in zip(
            WORKLOAD_ORDER, campaign_configs, campaign_ids, campaign_layouts):
        campaign_preimage = ident.canonical_preimage(cfg)
        expected_layout_root = layout.root
        summary = None
        campaign_error = None
        try:
            _assert_single_tenant()
            perf = PerfConfig(
                records=policy["scale"]["records"],
                threads=policy["scale"]["threads"],
                workload=workload_flags(policy, workload_name),
                extime=policy["scale"]["extime_s"],
                reps=_expected_reps(policy, workload_name),
            )

            def capability_resolver(evidence, *, workload_name=workload_name):
                generator_input = (
                    f"paper-story-a1-paired/v1|{study_id}|{workload_name}|"
                    f"{evidence.genome_sha256}"
                ).encode("utf-8")
                return attest_generator_output(
                    build_context,
                    evidence,
                    generator_input_sha256=_sha256_bytes(generator_input),
                )

            execution_options = _campaign_execution_options(
                policy, workload_name,
            )
            execution_options = _require_registered_execution_options(
                policy, workload_name, execution_options,
            )
            summary = run_campaign(
                cfg,
                genomes(policy, workload_name),
                perf,
                contract.env_tag,
                contract.clocks_per_us,
                numactl=list(contract.numactl),
                output_root=roots["output_root"],
                cache_root=roots["cache_root"],
                dependency_prefix=dependency_prefix,
                authorization_contract=authorization,
                env_contract=contract,
                expected_toolchain_manifest=toolchain_manifest,
                build_context=build_context,
                declared_use_class=DECLARED_USE_CLASS,
                capability_resolver=capability_resolver,
                durable_root_policy=durable_policy,
                **execution_options,
            )
            campaign_id = summary.campaign_id
            layout = CampaignLayout(summary.layout_root)
        except Exception as exc:  # noqa: BLE001 - invalid campaigns are landed raw
            campaign_error = f"{type(exc).__name__}: {exc}"
        collected = collect_workload(
            policy,
            workload_name=workload_name,
            campaign_id=campaign_id,
            layout=layout,
            admission_policy=build_context.policy,
            env_tag=contract.env_tag,
            source_binding=source_binding,
            summary=summary,
            campaign_error=campaign_error,
            expected_campaign_preimage=campaign_preimage,
            expected_layout_root=expected_layout_root,
            expected_schedule_receipt=(
                summary.balanced_schedule_receipt
                if summary is not None else None
            ),
        )
        workload_results.append(collected)

    result = assemble_result(
        policy,
        policy_sha256=policy_sha,
        source_binding=source_binding,
        reservation_binding=reservation_binding,
        workloads=workload_results,
        measurement_error=measurement_error,
    )
    _revalidate_attempt_root(roots)
    result_path = Path(roots["result_root"]) / "result.json"
    _exclusive_write(result_path, result)
    result_sha = _sha256_file(result_path)
    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "study_id": study_id,
        "formal": False,
        "promotion_prohibited": True,
        "route": "direct-qsub",
        "pbs_jobid": args.pbs_jobid,
        "host": socket.gethostname(),
        "recorded_epoch": int(time.time()),
        "policy": {
            "path": _policy_relative_path(policy),
            "sha256": policy_sha,
        },
        "source_binding": source_binding,
        "submission_receipt": {
            "path": os.fspath(acquisition_path),
            "sha256": acquisition_sha,
        },
        "scheduler_completion_receipt": {
            "path": trusted_roots["completion_receipt"],
        },
        "roots": roots,
        "result": {
            "path": os.fspath(result_path),
            "sha256": result_sha,
            "complete": result["complete"],
            "all_workloads_terminal": result["all_workloads_terminal"],
        },
        "calibration_sha256": getattr(loaded_calibration, "sha256", None),
    }
    receipt_path = Path(roots["result_root"]) / "receipt.json"
    _exclusive_write(receipt_path, receipt)
    _issue_non_certifying_observation(
        common_record=common_record,
        source_binding=non_certifying_source_binding,
        workloads=workload_results,
        result_path=result_path,
        receipt_path=receipt_path,
    )
    return 0


def _verify_current_source_paths(
    repo_root: Path,
    expected_head: str,
    binding: Mapping[str, object],
    *,
    relative_paths: Sequence[str],
    label: str,
) -> None:
    if _run_git(repo_root, "rev-parse", "HEAD") != expected_head:
        raise PaperStoryError(f"HEAD differs from {label} source binding")
    if binding.get("measurement_source_commit") != expected_head:
        raise PaperStoryError(f"{label} source commit differs from expected HEAD")
    if not _validate_source_binding_for_paths(binding, relative_paths):
        raise PaperStoryError(f"{label} source binding shape differs")
    for relative in relative_paths:
        expected = binding["files"][relative]
        oid = _run_git(repo_root, "rev-parse", f"{expected_head}:{relative}")
        if oid != expected.get("git_blob_oid"):
            raise PaperStoryError(
                f"git blob differs from {label} source binding: {relative}"
            )
        if _sha256_file(repo_root / relative) != expected.get("working_sha256"):
            raise PaperStoryError(
                f"working bytes differ from {label} source binding: {relative}"
            )


def _verify_current_source(
    repo_root: Path, expected_head: str, binding: Mapping[str, object],
    policy: Mapping[str, object] | None = None,
) -> None:
    active_policy = policy if policy is not None else load_policy()[0]
    if _parent_porcelain(repo_root, active_policy):
        raise PaperStoryError("working tree is dirty before materialization")
    _verify_current_source_paths(
        repo_root,
        expected_head,
        binding,
        relative_paths=(
            SOURCE_RELATIVE_PATHS
            if policy is None
            else _source_relative_paths(policy, non_certifying=False)
        ),
        label="raw",
    )


def _canonical_workload_wal_layout(
    *,
    resolved_wal_path: Path,
    output_root: Path,
    campaign_id: object,
) -> CampaignLayout:
    if type(campaign_id) is not str:
        raise PaperStoryError("workload campaign ID is missing")
    try:
        expected = exploration_campaign_layout(campaign_id, os.fspath(output_root))
    except ValueError as exc:
        raise PaperStoryError(f"workload campaign ID is invalid: {exc}") from exc
    observed_relative = resolved_wal_path.relative_to(output_root)
    expected_relative = Path(expected.wal_file).resolve(strict=False).relative_to(
        output_root
    )
    observed_parts = observed_relative.parts
    expected_parts = expected_relative.parts
    campaign_id_index = 2
    if (
        len(observed_parts) != len(expected_parts)
        or observed_parts[:campaign_id_index] != expected_parts[:campaign_id_index]
        or observed_parts[campaign_id_index + 1:]
        != expected_parts[campaign_id_index + 1:]
    ):
        raise PaperStoryError("WAL evidence is not in the canonical campaign layout")
    if observed_parts[campaign_id_index] != campaign_id:
        raise PaperStoryError("WAL evidence campaign ID differs from workload")
    return CampaignLayout(expected.root)


def _revalidate_raw_wals(
    result: Mapping[str, object], receipt: Mapping[str, object],
    policy: Mapping[str, object] | None = None,
) -> None:
    policy = policy if policy is not None else load_policy()[0]
    roots = receipt.get("roots")
    if type(roots) is not dict:
        raise PaperStoryError("receipt output root binding is missing")
    v3_job_roots = roots.get("job_roots")
    if _policy_schema(policy) == POLICY_SCHEMA_V3:
        if type(v3_job_roots) is not list or len(v3_job_roots) != 3:
            raise PaperStoryError("receipt workload output roots are missing")
        output_roots = []
        for ordinal, workload in enumerate(WORKLOAD_ORDER):
            item = v3_job_roots[ordinal]
            if (
                type(item) is not dict
                or item != _v3_job_roots(Path(roots["attempt_root"]), workload)
                or type(item.get("output_root")) is not str
            ):
                raise PaperStoryError("receipt workload output root differs")
            output_roots.append(Path(item["output_root"]).resolve(strict=True))
    else:
        if type(roots.get("output_root")) is not str:
            raise PaperStoryError("receipt output root binding is missing")
        output_roots = [Path(roots["output_root"]).resolve(strict=True)] * 3
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    for ordinal, workload in enumerate(result["workloads"]):
        output_root = output_roots[ordinal]
        wal_evidence = workload.get("wal_evidence")
        if type(wal_evidence) is not dict or type(wal_evidence.get("path")) is not str:
            raise PaperStoryError("workload WAL evidence is missing")
        wal_path = Path(wal_evidence["path"])
        if not wal_path.is_absolute():
            raise PaperStoryError("WAL evidence path is not absolute")
        resolved = wal_path.resolve(strict=False)
        if not _is_within(resolved, output_root):
            raise PaperStoryError("WAL evidence path escaped the measured output root")
        layout = _canonical_workload_wal_layout(
            resolved_wal_path=resolved,
            output_root=output_root,
            campaign_id=workload.get("campaign_id"),
        )
        records = wal_evidence.get("records")
        env_tags = {
            record.get("env_tag")
            for record in records
            if type(record) is dict and type(record.get("env_tag")) is str
        } if type(records) is list else set()
        if not env_tags and type(wal_evidence.get("expected_env_tag")) is str:
            env_tags = {wal_evidence["expected_env_tag"]}
        if len(env_tags) != 1:
            raise PaperStoryError("workload does not bind one WAL env tag")
        campaign_binding = workload.get("campaign_binding")
        if type(campaign_binding) is not dict:
            raise PaperStoryError("workload campaign binding is missing")
        recollected = collect_workload(
            policy,
            workload_name=workload["workload"],
            campaign_id=workload["campaign_id"],
            layout=layout,
            admission_policy=context.policy,
            env_tag=next(iter(env_tags)),
            source_binding=result["source_binding"],
            expected_campaign_preimage=_campaign_identity_preimage(
                campaign_binding.get("canonical_preimage")
            ),
            expected_layout_root=campaign_binding.get("layout_root"),
        )
        if recollected != workload:
            raise PaperStoryError("workload does not revalidate from raw WAL snapshot")


def _validate_v3_raw_documents(
    result: object, receipt: object, terminal: object, policy: Mapping[str, object],
):
    study_id = _policy_study_id(policy)
    policy_sha = _sha256_file(_policy_path(policy))
    if type(result) is not dict or set(result) != _V3_NON_CERTIFYING_RESULT_KEYS:
        raise PaperStoryError("v3 raw result shape differs")
    if type(receipt) is not dict or set(receipt) != _V3_NON_CERTIFYING_RECEIPT_KEYS:
        raise PaperStoryError("v3 raw receipt shape differs")
    if type(terminal) is not dict or set(terminal) != {
        "schema_version", "study_id", "source_commit", "attempt_root", "jobs",
    }:
        raise PaperStoryError("v3 group terminal shape differs")
    if (
        result.get("schema_version") != RESULT_SCHEMA
        or receipt.get("schema_version") != RECEIPT_SCHEMA
        or terminal.get("schema_version") != V3_GROUP_TERMINAL_SCHEMA
        or any(item.get("study_id") != study_id for item in (
            result, receipt, terminal,
        ))
        or result.get("formal") is not False
        or result.get("promotion_prohibited") is not True
        or receipt.get("formal") is not False
        or receipt.get("promotion_prohibited") is not True
        or receipt.get("route") != "direct-qsub-workload-fanout"
        or result.get("pairing_design") != _pairing_design(policy)
        or result.get("pbs_evidence_scope") != _json_safe(PBS_EVIDENCE_SCOPE)
        or result.get("policy_sha256") != policy_sha
        or receipt.get("policy") != {
            "path": _policy_relative_path(policy), "sha256": policy_sha,
        }
    ):
        raise PaperStoryError("v3 raw authority/policy binding differs")
    source_binding = result.get("source_binding")
    if (
        not _validate_source_binding(source_binding, policy)
        or receipt.get("source_binding") != source_binding
        or terminal.get("source_commit")
        != source_binding.get("measurement_source_commit")
    ):
        raise PaperStoryError("v3 raw source binding differs")
    roots = receipt.get("roots")
    if type(roots) is not dict or set(roots) != {
        "attempt_root", "attempt_identity", "raw_root", "result_root",
        "submission_receipt", "completion_receipt", "group_terminal",
        "job_roots",
    }:
        raise PaperStoryError("v3 raw roots shape differs")
    attempt_raw = roots.get("attempt_root")
    if type(attempt_raw) is not str or not Path(attempt_raw).is_absolute():
        raise PaperStoryError("v3 raw attempt root differs")
    attempt = Path(attempt_raw)
    evidence = _v3_attempt_evidence_paths(attempt)
    if (
        roots.get("attempt_identity") != _attempt_root_identity(attempt)
        or roots.get("raw_root") != os.fspath(attempt / "raw")
        or roots.get("result_root") != evidence["result_root"]
        or roots.get("submission_receipt") != evidence["submission_receipt"]
        or roots.get("completion_receipt") != evidence["completion_receipt"]
        or roots.get("group_terminal") != evidence["group_terminal"]
        or terminal.get("attempt_root") != os.fspath(attempt)
    ):
        raise PaperStoryError("v3 raw roots identity differs")
    executions = _validate_v3_job_executions(
        result.get("job_executions"), attempt=attempt,
    )
    if receipt.get("job_executions") != executions:
        raise PaperStoryError("v3 receipt job executions differ")
    workloads = result.get("workloads")
    if type(workloads) is not list:
        raise PaperStoryError("v3 result workloads is not a list")
    names = [item.get("workload") if type(item) is dict else None for item in workloads]
    ids = [item.get("campaign_id") if type(item) is dict else None for item in workloads]
    wal_paths = [
        item.get("campaign_binding", {}).get("wal_path")
        if type(item) is dict and type(item.get("campaign_binding")) is dict
        else None
        for item in workloads
    ]
    all_terminal = (
        result.get("measurement_error") is None
        and names == list(WORKLOAD_ORDER)
        and len(ids) == len(set(ids)) == 3
        and len(wal_paths) == len(set(wal_paths)) == 3
        and None not in wal_paths
        and all(_workload_has_terminal_result(item) for item in workloads)
    )
    complete = all_terminal and all(item.get("valid") is True for item in workloads)
    if (
        result.get("workload_reps") != {
            name: _expected_reps(policy, name) for name in WORKLOAD_ORDER
        }
        or result.get("all_workloads_terminal") is not all_terminal
        or result.get("complete") is not complete
        or "cross_workload_conclusion" in result
    ):
        raise PaperStoryError("v3 raw workload aggregate differs")
    for item in workloads:
        schedule = item.get("schedule_receipt") if type(item) is dict else None
        arms = item.get("arms") if type(item) is dict else None
        errors = _balanced_schedule_receipt_errors(
            policy, item.get("workload"),
            schedule.get("document") if type(schedule) is dict else None,
            arms if type(arms) is dict else None,
        )
        if (
            type(item.get("errors")) is not list
            or any(error not in item["errors"] for error in errors)
            or (item.get("valid") is True and errors)
        ):
            raise PaperStoryError("v3 balanced schedule evidence differs")
        if item.get("valid") is True:
            expected_names = _workload_arm_order(policy, item["workload"])
            if type(arms) is not dict or set(arms) != set(expected_names):
                raise PaperStoryError("v3 valid workload arm set differs")
            statistics_result = _consumer_positional_statistics(
                policy, item["workload"],
                {name: arms[name].get("raw_tps") for name in expected_names},
            )
            if item.get("statistics") != statistics_result:
                raise PaperStoryError("v3 workload statistics differ")
    terminal_jobs = terminal.get("jobs")
    job_roots = roots.get("job_roots")
    if (
        type(terminal_jobs) is not list or len(terminal_jobs) != 3
        or type(job_roots) is not list or len(job_roots) != 3
    ):
        raise PaperStoryError("v3 group terminal is not the exact job triple")
    for ordinal, workload in enumerate(WORKLOAD_ORDER):
        expected_roots = _v3_job_roots(attempt, workload)
        entry = terminal_jobs[ordinal]
        execution = executions[ordinal]
        terminal_path = Path(expected_roots["job_terminal"])
        result_path = Path(expected_roots["result_root"]) / "result.json"
        receipt_path = Path(expected_roots["result_root"]) / "receipt.json"
        if (
            job_roots[ordinal] != expected_roots
            or type(entry) is not dict
            or set(entry) != {
                "workload", "ordinal", "request_id", "path", "sha256",
                "result", "receipt",
            }
            or entry.get("workload") != workload
            or entry.get("ordinal") != ordinal
            or _validated_request_id(
                entry.get("request_id"), f"{workload} group terminal request ID",
            ) != _validated_request_id(
                execution["request_id"], f"{workload} execution request ID",
            )
            or entry.get("path") != os.fspath(terminal_path)
            or entry.get("sha256") != _sha256_file(terminal_path)
            or entry.get("result") != {
                "path": os.fspath(result_path), "sha256": _sha256_file(result_path),
            }
            or entry.get("receipt") != {
                "path": os.fspath(receipt_path), "sha256": _sha256_file(receipt_path),
            }
            or execution["reservation_binding"]["script_sha256"]
            != source_binding["files"][JOB_RELATIVE_PATH]["working_sha256"]
        ):
            raise PaperStoryError("v3 group terminal job binding differs")
    result_path = Path(evidence["result_root"]) / "result.json"
    if receipt.get("result") != {
        "path": os.fspath(result_path),
        "sha256": _sha256_file(result_path),
        "complete": result["complete"],
        "all_workloads_terminal": result["all_workloads_terminal"],
    }:
        raise PaperStoryError("v3 raw result byte binding differs")
    submission = receipt.get("submission_receipt")
    if (
        type(submission) is not dict
        or set(submission) != {"path", "sha256"}
        or submission.get("path") != evidence["submission_receipt"]
        or submission.get("sha256") != _sha256_file(Path(evidence["submission_receipt"]))
        or receipt.get("scheduler_completion_receipt")
        != {"path": evidence["completion_receipt"]}
    ):
        raise PaperStoryError("v3 raw scheduler binding differs")
    return result, receipt, terminal


def validate_raw_documents(result: object, receipt: object, terminal: object, policy: object):
    validate_policy(policy)
    if _policy_schema(policy) == POLICY_SCHEMA_V3:
        return _validate_v3_raw_documents(result, receipt, terminal, policy)
    study_id = _policy_study_id(policy)
    pairing_design = _pairing_design(policy)
    policy_path = _policy_relative_path(policy)
    policy_sha = _sha256_file(_policy_path(policy))
    if type(result) is not dict or result.get("schema_version") != RESULT_SCHEMA:
        raise PaperStoryError("raw result schema differs")
    if type(receipt) is not dict or receipt.get("schema_version") != RECEIPT_SCHEMA:
        raise PaperStoryError("raw receipt schema differs")
    if type(terminal) is not dict or terminal.get("schema_version") != JOB_TERMINAL_SCHEMA:
        raise PaperStoryError("job terminal schema differs")
    for document in (result, receipt, terminal):
        if document.get("study_id") != study_id:
            raise PaperStoryError("raw document study ID differs")
    if (
        result.get("formal") is not False
        or result.get("promotion_prohibited") is not True
        or receipt.get("formal") is not False
        or receipt.get("promotion_prohibited") is not True
    ):
        raise PaperStoryError("exploratory authority flags differ")
    if result.get("pairing_design") != pairing_design:
        raise PaperStoryError("pairing design differs")
    if result.get("pbs_evidence_scope") != _json_safe(PBS_EVIDENCE_SCOPE):
        raise PaperStoryError("PBS evidence scope disclosure differs")
    if result.get("policy_sha256") != policy_sha:
        raise PaperStoryError("raw result policy hash differs from tracked policy")
    if receipt.get("policy") != {
        "path": policy_path,
        "sha256": policy_sha,
    }:
        raise PaperStoryError("raw receipt policy binding differs")
    expected_workload_reps = {
        name: _expected_reps(policy, name) for name in WORKLOAD_ORDER
    }
    if result.get("workload_reps") != expected_workload_reps:
        raise PaperStoryError("result workload reps differ from policy")
    workloads = result.get("workloads")
    if type(workloads) is not list:
        raise PaperStoryError("result workloads is not a list")
    names = [item.get("workload") for item in workloads if type(item) is dict]
    ids = [item.get("campaign_id") for item in workloads if type(item) is dict]
    wal_paths = [
        item.get("campaign_binding", {}).get("wal_path")
        if type(item.get("campaign_binding")) is dict else None
        for item in workloads if type(item) is dict
    ]
    recomputed_all_terminal = (
        result.get("measurement_error") is None
        and names == list(WORKLOAD_ORDER)
        and len(ids) == 3
        and len(set(ids)) == 3
        and len(wal_paths) == 3
        and None not in wal_paths
        and len(set(wal_paths)) == 3
        and all(_workload_has_terminal_result(item) for item in workloads)
    )
    if result.get("all_workloads_terminal") is not recomputed_all_terminal:
        raise PaperStoryError(
            "top-level terminal status does not match workload outcomes"
        )
    recomputed_complete = recomputed_all_terminal and all(
        item.get("valid") is True for item in workloads
    )
    if result.get("complete") is not recomputed_complete:
        raise PaperStoryError("top-level complete does not match workload validity")
    if "cross_workload_conclusion" in result:
        raise PaperStoryError("cross-workload conclusion is prohibited")
    for item in workloads:
        if type(item) is not dict:
            raise PaperStoryError("result workload is not an object")
        if _policy_schema(policy) == POLICY_SCHEMA_V3:
            schedule_evidence = item.get("schedule_receipt")
            schedule_document = (
                schedule_evidence.get("document")
                if type(schedule_evidence) is dict else None
            )
            arms = item.get("arms")
            schedule_errors = _balanced_schedule_receipt_errors(
                policy,
                item.get("workload"),
                schedule_document,
                arms if type(arms) is dict else None,
            )
            recorded_errors = item.get("errors")
            if (
                type(recorded_errors) is not list
                or any(error not in recorded_errors for error in schedule_errors)
                or (item.get("valid") is True and schedule_errors)
            ):
                raise PaperStoryError(
                    "balanced schedule receipt does not match workload validity"
                )
        if item.get("valid") is True:
            arms = item.get("arms")
            expected_names = _workload_arm_order(
                policy, item.get("workload"),
            )
            if type(arms) is not dict or set(arms) != set(expected_names):
                raise PaperStoryError("materialized valid workload arm set differs")
            stats = _consumer_positional_statistics(
                policy,
                item.get("workload"),
                {
                    name: arms[name].get("raw_tps")
                    for name in expected_names
                },
            )
            if item.get("statistics") != stats:
                raise PaperStoryError(
                    "stored statistics fail result self-consistency check"
                )
    if (
        type(terminal.get("driver_rc")) is not int
        or terminal.get("driver_rc") != 0
        or type(terminal.get("shell_rc")) is not int
        or terminal.get("shell_rc") != 0
        or terminal.get("status") != "finished"
    ):
        raise PaperStoryError("job did not terminate with a finished raw bundle")
    if (
        _validated_request_id(terminal.get("pbs_jobid"), "terminal PBS_JOBID")
        != _validated_request_id(receipt.get("pbs_jobid"), "receipt PBS_JOBID")
    ):
        raise PaperStoryError("job terminal PBS identity differs from receipt")
    pbs_observation = terminal.get("pbs_observation")
    if (
        type(pbs_observation) is not dict
        or set(pbs_observation) != _PBS_OBSERVATION_KEYS
        or pbs_observation.get("pbs_jobid") != terminal.get("pbs_jobid")
    ):
        raise PaperStoryError("job terminal PBS environment observation differs")
    reservation_binding = _validate_reservation_binding_document(
        result.get("reservation_binding")
    )
    if terminal.get("reservation_binding") != reservation_binding:
        raise PaperStoryError("job terminal reservation binding differs from result")
    if (
        reservation_binding["job_id"] != terminal.get("pbs_jobid")
        or reservation_binding["job_id"] != receipt.get("pbs_jobid")
    ):
        raise PaperStoryError("reservation job ID differs from raw PBS identity")
    binding = result.get("source_binding")
    if type(binding) is not dict:
        raise PaperStoryError("result source binding is missing")
    if not _validate_source_binding(binding, policy):
        raise PaperStoryError("source binding is incomplete")
    if terminal.get("expected_head") != binding.get("measurement_source_commit"):
        raise PaperStoryError("job terminal expected HEAD differs from source binding")
    if (
        terminal.get("observed_head") != terminal.get("expected_head")
        or terminal.get("porcelain") != ""
    ):
        raise PaperStoryError("job terminal did not observe H0 clean")
    if receipt.get("source_binding") != result.get("source_binding"):
        raise PaperStoryError("result and receipt source bindings differ")
    if terminal.get("terminal_source_binding") != result.get("source_binding"):
        raise PaperStoryError("terminal source bytes differ from result source binding")
    roots = receipt.get("roots")
    if (
        type(roots) is not dict
        or terminal.get("completion_receipt_path") != roots.get("completion_receipt")
    ):
        raise PaperStoryError("terminal completion receipt path differs")
    if terminal.get("attempt_identity") != roots.get("attempt_identity"):
        raise PaperStoryError("terminal attempt root inode binding differs")
    attempt_root = roots.get("attempt_root")
    if (
        type(attempt_root) is not str
        or Path(attempt_root).name != reservation_binding["nonce"]
    ):
        raise PaperStoryError("reservation nonce differs from attempt identity")
    if (
        reservation_binding["script_sha256"]
        != binding["files"][JOB_RELATIVE_PATH]["working_sha256"]
    ):
        raise PaperStoryError("reservation script SHA differs from source binding")
    submission = receipt.get("submission_receipt")
    if (
        type(submission) is not dict
        or terminal.get("submission_receipt_sha256") != submission.get("sha256")
    ):
        raise PaperStoryError("terminal submission receipt hash differs")
    return result, receipt, terminal


def _readme(result: Mapping[str, object]) -> str:
    complete = result["complete"] is True
    all_terminal = result.get("all_workloads_terminal") is True
    balanced_v3 = result.get("pairing_design") == V3_PAIRING_DESIGN
    workload_rows = []
    workloads = result.get("workloads")
    for item in workloads if type(workloads) is list else []:
        if type(item) is not dict:
            continue
        name = item.get("workload")
        statistics_result = item.get("statistics")
        if item.get("valid") is True and type(statistics_result) is dict:
            interval = statistics_result.get("descriptive_interval_tps")
            interval_text = (
                f"[{float(interval[0]):.6f}, {float(interval[1]):.6f}]"
                if type(interval) is list and len(interval) == 2
                else "not-applicable" if balanced_v3 else "invalid"
            )
            workload_rows.append(
                f"| {name} | valid | {statistics_result.get('n')} | "
                f"{float(statistics_result.get('mean_signed_positional_difference_tps')):.6f} | "
                f"{interval_text} | {float(statistics_result.get('floor_boundary_tps')):.6f} | "
                f"{statistics_result.get('classification')} | "
                f"{str(statistics_result.get('variance_plan_breach')).lower()} |"
            )
        else:
            expected = result.get("workload_reps", {}).get(name)
            reasons = "; ".join(item.get("errors", []))
            workload_rows.append(
                f"| {name} | invalid | {expected} | n/a | n/a | n/a | "
                f"invalid: {reasons} | n/a |"
            )
    workload_table = "\n".join(workload_rows)
    accounting_rows = []
    executions = result.get("job_executions")
    if type(executions) is list:
        for execution in executions:
            if type(execution) is not dict:
                continue
            reservation = execution.get("reservation_binding")
            accounting = execution.get("accounting")
            if type(reservation) is dict and type(accounting) is dict:
                accounting_rows.append(
                    f"| {execution.get('workload')} | {execution.get('request_id')} | "
                    f"{reservation.get('host')} | "
                    f"{float(accounting.get('cpu_total_s')):.6f} | "
                    f"{float(accounting.get('elapsed_s')):.6f} |"
                )
    accounting_section = ""
    if accounting_rows:
        accounting_section = (
            "\n## Job accounting\n\n"
            "CPU is the baseline-subtracted Bash shell plus reaped-descendant "
            "CPU window recorded by each workload job.\n\n"
            "| workload | request ID | host | CPU total s | elapsed s |\n"
            "|---|---|---|---:|---:|\n"
            + "\n".join(accounting_rows)
            + "\n"
        )
    materialization_evidence = result.get("materialization_evidence")
    publish_evidence = (
        materialization_evidence.get("publish")
        if type(materialization_evidence) is dict else None
    )
    if (
        type(publish_evidence) is dict
        and publish_evidence.get("selected_mechanism") == PUBLISH_EINVAL_FALLBACK
    ):
        publish_text = (
            "Materialization publish: RENAME_NOREPLACE was attempted on this "
            "filesystem and returned EINVAL. The fallback held an A-1-specific "
            "exclusive sibling claim, refused a destination present at its "
            "existence check, and then exposed the complete staging directory with "
            "one flags-zero renameat2 call. This is not atomic no-replace against a "
            "non-cooperating writer: an empty type-compatible destination created "
            "after the check and before that rename may be replaced. No file is "
            "written below the destination after the directory publish.\n"
        )
    elif (
        type(publish_evidence) is dict
        and publish_evidence.get("selected_mechanism") == PUBLISH_RENAME_NOREPLACE
    ):
        publish_text = (
            "Materialization publish: the complete staging directory was exposed "
            "with renameat2 RENAME_NOREPLACE, providing atomic no-replace publish "
            "on this filesystem. No file is written below the destination after "
            "the directory publish.\n"
        )
    else:
        publish_text = ""
    publish_section = f"\n{publish_text}" if publish_text else ""
    title = (
        "# Paper-story A-1 balanced five-rep comparison"
        if balanced_v3 else
        "# Paper-story A-1 exploratory positional comparison"
    )
    mean_label = (
        "mean variant-baseline tps" if balanced_v3
        else "mean static10-adaptive tps"
    )
    design_text = (
        "The registered estimand is the arithmetic mean of paired variant-minus-"
        "baseline TPS differences under the balanced five-rep schedule. Pilot "
        "observations are sizing-only and cannot enter the final estimate."
        if balanced_v3 else
        "The registered positions are arm-grouped ordinal matches, not shared time "
        "blocks. The interval and classification are descriptive outputs of the "
        "registered rule."
    )
    limitations = (
        "\n".join(f"- {item}" for item in result.get("limitations", []))
        if balanced_v3 else PREREGISTERED_LIMITATIONS
    )
    return (
        f"{title}\n\n"
        f"Study: `{result.get('study_id')}`\n\n"
        f"All workloads terminal: `{'true' if all_terminal else 'false'}`\n\n"
        f"All workloads valid: `{'true' if complete else 'false'}`\n\n"
        "No cross-workload conclusion is produced. Each row is a terminal "
        "workload result.\n\n"
        f"| workload | status | reps | {mean_label} | descriptive interval tps | B tps | classification | variance_plan_breach |\n"
        "|---|---:|---:|---:|---:|---:|---|---:|\n"
        f"{workload_table}\n\n"
        f"{accounting_section}"
        "This result is exploratory, formal=false, and promotion is prohibited. "
        f"{design_text} Trace0 evidence is source-routed and is not an "
        "artifact-standalone proof.\n\n"
        "## この設計が言えないこと\n\n"
        f"{limitations}\n"
        "PBS evidence scope: the job observes PBS_JOBID, PBS_O_HOST, and "
        "PBS_O_WORKDIR. PBS_O_QUEUE is not exported by this NQSV site and is not "
        "claimed as a job observation. NQSV stdout/stderr FD targets are not the "
        "qsub -o/-e delivery files; their delivered bytes are bound only by the "
        "scheduler completion receipt SHA-256 values and the job-terminal SHA-256. "
        "Scheduler terminal evidence accepts exactly two forms: a request still "
        "visible in a terminal state, or a request proven visible at submission and "
        "later absent from qstat. In the absent form, scheduler state and exit status "
        "are explicitly recorded as unobserved, not as empty values or zero. Job "
        "success remains established independently by driver_rc=0, shell_rc=0, and "
        "job terminal status=finished.\n"
        f"{publish_section}"
    )


def _materialized_result(
    result: Mapping[str, object],
    completion: Mapping[str, object],
    terminal: Mapping[str, object],
) -> dict[str, object]:
    if completion.get("schema_version") == V3_GROUP_COMPLETION_SCHEMA:
        jobs = completion.get("jobs")
        return {
            **result,
            "materialization_evidence": {
                "schema_version": MATERIALIZATION_EVIDENCE_SCHEMA,
                "derivation": {
                    "authoritative_input": "three workload-local raw WAL byte sequences",
                    "workload_rederivation": "recollected from its ordinal job root before publish",
                    "result_receipt_comparison": "self-consistency check only",
                    "independent_evidence_claimed": False,
                },
                "scheduler_terminals": [
                    {
                        "workload": item["workload"],
                        "request_id": item["request_id"],
                        "scheduler_terminal": dict(item["scheduler_terminal"]),
                    }
                    for item in jobs
                ],
                "job_terminal_outcomes": [
                    {
                        "workload": execution["workload"],
                        "request_id": execution["request_id"],
                        "accounting": dict(execution["accounting"]),
                    }
                    for execution in result["job_executions"]
                ],
                "interpretation": _json_safe(SCHEDULER_COMPLETION_INTERPRETATION),
            },
        }
    return {
        **result,
        "materialization_evidence": {
            "schema_version": MATERIALIZATION_EVIDENCE_SCHEMA,
            "derivation": {
                "authoritative_input": "raw WAL byte sequence",
                "workload_rederivation": "recollected from raw WAL before publish",
                "result_receipt_comparison": "self-consistency check only",
                "independent_evidence_claimed": False,
            },
            "scheduler_terminal": dict(completion["scheduler_terminal"]),
            "job_terminal_outcome": {
                "driver_rc": terminal["driver_rc"],
                "shell_rc": terminal["shell_rc"],
                "status": terminal["status"],
            },
            "interpretation": _json_safe(SCHEDULER_COMPLETION_INTERPRETATION),
        },
    }


def create_materialization_destination(raw: Path) -> Path:
    destination = raw
    if not destination.is_absolute():
        destination = (Path.cwd() / destination).resolve(strict=False)
    else:
        destination = destination.resolve(strict=False)
    if os.path.lexists(destination):
        raise PaperStoryError("materialize destination already exists")
    if not destination.parent.is_dir():
        raise PaperStoryError("materialize destination parent does not exist")
    try:
        destination.mkdir(mode=0o700)
    except OSError as exc:
        raise PaperStoryError(f"exclusive destination creation failed: {exc}") from exc
    return destination


def _exact_materialization_destination(
    repo_root: Path, raw: Path,
    policy: Mapping[str, object] | None = None,
) -> Path:
    destination = raw if raw.is_absolute() else Path.cwd() / raw
    destination = destination.resolve(strict=False)
    relative = MATERIALIZATION_RELATIVE_PATH
    if policy is not None:
        execution = policy.get("execution")
        value = (
            execution.get("materialization_relative_path")
            if type(execution) is dict else None
        )
        if type(value) is not str:
            raise PaperStoryError("policy materialization destination is missing")
        relative = Path(value)
    expected = (repo_root / relative).resolve(strict=False)
    if destination != expected:
        raise PaperStoryError("materialize destination is not the exact A-1 insight leaf")
    if os.path.lexists(destination):
        raise PaperStoryError("materialize destination already exists")
    if not destination.parent.is_dir():
        raise PaperStoryError("materialize destination parent does not exist")
    return destination


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    fd = os.open(path, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _renameat2_directory(staging: Path, destination: Path, flags: int) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise PaperStoryError("renameat2 no-replace is unavailable")
    renameat2.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    renameat2.restype = ctypes.c_int
    rc = renameat2(
        _AT_FDCWD,
        os.fsencode(staging),
        _AT_FDCWD,
        os.fsencode(destination),
        flags,
    )
    if rc != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), os.fspath(destination))


def _publish_staging_noreplace(staging: Path, destination: Path) -> None:
    try:
        _renameat2_directory(staging, destination, _RENAME_NOREPLACE)
    except OSError as exc:
        raise PaperStoryError(
            f"no-replace materialization publish failed: {exc.strerror}"
        ) from exc
    _fsync_directory(destination.parent)


def _materialization_publish_evidence(mechanism: str) -> dict[str, object]:
    if mechanism == PUBLISH_RENAME_NOREPLACE:
        return {
            "schema_version": MATERIALIZATION_PUBLISH_SCHEMA,
            "selected_mechanism": mechanism,
            "selection_observation": {
                "rename_noreplace_attempted": True,
                "errno": None,
            },
            "guarantees": [
                "Destination publication is atomic and no-replace on the observed filesystem.",
                "Every materialized file and the completion marker exist in staging before publish.",
                "No file is written below destination after directory publish.",
            ],
            "limitations": [],
        }
    if mechanism == PUBLISH_EINVAL_FALLBACK:
        return {
            "schema_version": MATERIALIZATION_PUBLISH_SCHEMA,
            "selected_mechanism": mechanism,
            "selection_observation": {
                "rename_noreplace_attempted": True,
                "errno": "EINVAL",
            },
            "guarantees": [
                "A destination present at the fallback existence check is refused without publication.",
                "Cooperating A-1 publishers cannot hold the same exclusive sibling claim.",
                "Every materialized file and the completion marker exist in staging before publish.",
                "No file is written below destination after directory publish.",
            ],
            "limitations": [
                "Fallback publication is not atomic no-replace against a non-cooperating writer.",
                "An empty type-compatible destination created after the existence check and before the flags-zero renameat2 call may be replaced.",
            ],
        }
    raise PaperStoryError("materialization publish mechanism differs")


def _observe_materialization_publish(destination: Path) -> dict[str, object]:
    """Select the A-1 publish path only by an actual same-filesystem attempt."""
    try:
        probe_root = Path(tempfile.mkdtemp(
            prefix=f".{destination.name}.publish-probe-",
            dir=destination.parent,
        ))
        probe_source = probe_root / "source"
        probe_destination = probe_root / "destination"
        probe_source.mkdir(mode=0o700)
    except OSError as exc:
        raise PaperStoryError(
            f"materialization publish probe creation failed: {exc}"
        ) from exc
    try:
        try:
            _renameat2_directory(
                probe_source, probe_destination, _RENAME_NOREPLACE
            )
        except OSError as exc:
            if exc.errno != errno.EINVAL:
                raise PaperStoryError(
                    "no-replace materialization publish probe failed: "
                    f"{exc.strerror}"
                ) from exc
            return _materialization_publish_evidence(PUBLISH_EINVAL_FALLBACK)
        return _materialization_publish_evidence(PUBLISH_RENAME_NOREPLACE)
    finally:
        try:
            if probe_source.exists():
                probe_source.rmdir()
            if probe_destination.exists():
                probe_destination.rmdir()
            probe_root.rmdir()
        except OSError as exc:
            raise PaperStoryError(
                f"materialization publish probe cleanup failed: {exc}"
            ) from exc


def _release_materialization_publish_claim(
    claim: Path, identity: tuple[int, int]
) -> None:
    try:
        info = claim.lstat()
    except OSError as exc:
        raise PaperStoryError(
            f"fallback materialization publish claim stat failed: {exc}"
        ) from exc
    if (
        not stat.S_ISREG(info.st_mode)
        or (info.st_dev, info.st_ino) != identity
    ):
        raise PaperStoryError("fallback materialization publish claim identity differs")
    try:
        claim.unlink()
        _fsync_directory(claim.parent)
    except OSError as exc:
        raise PaperStoryError(
            f"fallback materialization publish claim cleanup failed: {exc}"
        ) from exc


def _publish_staging_after_einval(staging: Path, destination: Path) -> None:
    claim = destination.parent / f".{destination.name}.publish-claim"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        claim_fd = os.open(claim, flags, 0o600)
    except OSError as exc:
        raise PaperStoryError(
            f"exclusive fallback materialization publish claim failed: {exc}"
        ) from exc
    claim_identity = os.fstat(claim_fd)
    try:
        os.fsync(claim_fd)
        _fsync_directory(destination.parent)
        if os.path.lexists(destination):
            raise PaperStoryError(
                "fallback materialization publish refused: destination already exists"
            )
        try:
            _renameat2_directory(staging, destination, _RENAME_DEFAULT)
        except OSError as exc:
            raise PaperStoryError(
                f"fallback materialization publish failed: {exc.strerror}"
            ) from exc
        _fsync_directory(destination.parent)
    finally:
        os.close(claim_fd)
        _release_materialization_publish_claim(
            claim, (claim_identity.st_dev, claim_identity.st_ino)
        )


def _publish_complete_staging(
    staging: Path,
    destination: Path,
    completion: Mapping[str, object],
    publish_evidence: Mapping[str, object] | None = None,
) -> None:
    selected = (
        dict(publish_evidence)
        if publish_evidence is not None
        else _observe_materialization_publish(destination)
    )
    _exclusive_write(staging / COMPLETION_MARKER, completion)
    _fsync_directory(staging)
    mechanism = selected.get("selected_mechanism")
    if mechanism == PUBLISH_RENAME_NOREPLACE:
        _publish_staging_noreplace(staging, destination)
    elif mechanism == PUBLISH_EINVAL_FALLBACK:
        _publish_staging_after_einval(staging, destination)
    else:
        raise PaperStoryError("materialization publish mechanism differs")


def _remove_unpublished_staging(
    staging: Path, identity: tuple[int, int]
) -> None:
    try:
        info = staging.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise PaperStoryError(f"staging cleanup stat failed: {exc}") from exc
    if (
        stat.S_ISLNK(info.st_mode)
        or not stat.S_ISDIR(info.st_mode)
        or (info.st_dev, info.st_ino) != identity
    ):
        raise PaperStoryError("staging cleanup identity differs")
    try:
        shutil.rmtree(staging)
    except OSError as exc:
        raise PaperStoryError(f"staging cleanup failed: {exc}") from exc


def _attach_materialization_publish_evidence(
    result: Mapping[str, object], publish_evidence: Mapping[str, object]
) -> dict[str, object]:
    materialization = result.get("materialization_evidence")
    if type(materialization) is not dict:
        materialization = {}
    published = {
        **result,
        "materialization_evidence": {
            **materialization,
            "publish": dict(publish_evidence),
        },
    }
    if publish_evidence.get("selected_mechanism") == PUBLISH_EINVAL_FALLBACK:
        limitations = result.get("limitations")
        published["limitations"] = [
            *(limitations if type(limitations) is list else []),
            (
                "EINVAL publish fallback is not atomic no-replace against a "
                "non-cooperating destination writer."
            ),
        ]
    return published


def _publish_materialization_bundle(
    destination: Path,
    materialized_receipt: Mapping[str, object],
    result: Mapping[str, object],
    policy: Mapping[str, object] | None = None,
) -> None:
    if result.get("all_workloads_terminal") is not True:
        raise PaperStoryError(
            "materialization requires terminal outcomes for every workload"
        )
    staging = destination.parent / f".{destination.name}.staging-{os.getpid()}"
    try:
        staging.mkdir(mode=0o700)
        staging_info = staging.lstat()
    except OSError as exc:
        raise PaperStoryError(f"exclusive staging creation failed: {exc}") from exc
    staging_identity = (staging_info.st_dev, staging_info.st_ino)
    published = False
    try:
        publish_evidence = _observe_materialization_publish(destination)
        published_result = _attach_materialization_publish_evidence(
            result, publish_evidence
        )
        _exclusive_write(staging / "receipt.json", materialized_receipt)
        _exclusive_write(staging / "result.json", published_result)
        _exclusive_write_text(staging / "README.md", _readme(published_result))
        materialized_names = ["README.md", "receipt.json", "result.json"]
        if (
            policy is not None
            and _policy_schema(policy) == POLICY_SCHEMA_V3
            and _policy_study_id(policy) == V3_PILOT_STUDY_ID
            and result.get("complete") is True
        ):
            _exclusive_write(
                staging / BALANCED_SIZING_PILOT_FILENAME,
                _balanced_sizing_pilot_document(policy, result),
            )
            materialized_names.append(BALANCED_SIZING_PILOT_FILENAME)
        completion = {
            "schema_version": "paper-story-a1-paired-materialization-complete/v1",
            "destination": os.fspath(destination),
            "publish": publish_evidence,
            "files": {
                name: _sha256_file(staging / name)
                for name in materialized_names
            },
        }
        _publish_complete_staging(
            staging, destination, completion, publish_evidence
        )
        published = True
    finally:
        if not published:
            _remove_unpublished_staging(staging, staging_identity)


def _validate_v3_group_completion(
    completion: object,
    *,
    policy: Mapping[str, object],
    source_commit: str,
    attempt: Path,
    submission: Mapping[str, object],
    submission_sha256: str,
    group_terminal_sha256: str,
) -> dict[str, object]:
    if type(completion) is not dict or set(completion) != {
        "schema_version", "study_id", "source_commit", "attempt_root",
        "submission_receipt", "group_terminal", "jobs",
    }:
        raise PaperStoryError("group completion shape differs")
    evidence = _v3_attempt_evidence_paths(attempt)
    if (
        completion.get("schema_version") != V3_GROUP_COMPLETION_SCHEMA
        or completion.get("study_id") != _policy_study_id(policy)
        or completion.get("source_commit") != source_commit
        or completion.get("attempt_root") != os.fspath(attempt)
        or completion.get("submission_receipt") != {
            "path": evidence["submission_receipt"],
            "sha256": submission_sha256,
        }
        or completion.get("group_terminal") != {
            "path": evidence["group_terminal"],
            "sha256": group_terminal_sha256,
        }
    ):
        raise PaperStoryError("group completion identity differs")
    jobs = completion.get("jobs")
    if type(jobs) is not list or len(jobs) != 3:
        raise PaperStoryError("group completion is not the exact job triple")
    for ordinal, workload in enumerate(WORKLOAD_ORDER):
        roots = _v3_job_roots(attempt, workload)
        entry = jobs[ordinal]
        submission_job = submission["jobs"][ordinal]
        if type(entry) is not dict or set(entry) != {
            "workload", "ordinal", "request_id", "scheduler_terminal",
            "stdout", "stderr", "job_terminal",
        }:
            raise PaperStoryError("group completion job shape differs")
        if (
            entry.get("workload") != workload
            or entry.get("ordinal") != ordinal
            or _validated_request_id(
                entry.get("request_id"), f"{workload} completion request ID",
            ) != _validated_request_id(
                submission_job.get("request_id"),
                f"{workload} submission request ID",
            )
        ):
            raise PaperStoryError("group completion job identity differs")
        fake_roots = {
            "attempt_root": os.fspath(attempt),
            "submission_receipt": evidence["submission_receipt"],
            "stdout_path": roots["stdout_path"],
            "stderr_path": roots["stderr_path"],
            "raw_root": roots["job_root"],
        }
        fake_completion = {
            "schema_version": COMPLETION_SCHEMA,
            "study_id": _policy_study_id(policy),
            "source_commit": source_commit,
            "attempt_root": os.fspath(attempt),
            "request_id": entry["request_id"],
            "submission_receipt": completion["submission_receipt"],
            "scheduler_terminal": entry["scheduler_terminal"],
            "stdout": entry["stdout"],
            "stderr": entry["stderr"],
            "job_terminal": entry["job_terminal"],
        }
        validate_completion_receipt(
            fake_completion,
            trusted_roots=fake_roots,
            source_commit=source_commit,
            request_id=entry["request_id"],
            submission_receipt=submission_job,
            submission_receipt_sha256=submission_sha256,
            job_terminal_sha256=_sha256_file(Path(roots["job_terminal"])),
            study_id=_policy_study_id(policy),
        )
    return dict(completion)


def _run_materialize_v3(
    args,
    *,
    repo_root: Path,
    result: Mapping[str, object],
    receipt: Mapping[str, object],
    terminal: Mapping[str, object],
    policy: Mapping[str, object],
    policy_sha: str,
    raw_result_path: Path,
    raw_receipt_path: Path,
    group_terminal_path: Path,
    completion_path: Path,
) -> int:
    validate_raw_documents(result, receipt, terminal, policy)
    roots = receipt["roots"]
    attempt = Path(roots["attempt_root"])
    evidence = _v3_attempt_evidence_paths(attempt)
    if (
        raw_result_path != Path(evidence["result_root"]) / "result.json"
        or raw_receipt_path != Path(evidence["result_root"]) / "receipt.json"
        or group_terminal_path != Path(evidence["group_terminal"])
        or completion_path != Path(evidence["completion_receipt"])
    ):
        raise PaperStoryError("v3 raw document paths differ from group topology")
    acquisition_binding = receipt["submission_receipt"]
    acquisition_raw = _read_bytes_once(Path(acquisition_binding["path"]))
    if _sha256_bytes(acquisition_raw) != acquisition_binding["sha256"]:
        raise PaperStoryError("v3 group submission bytes differ")
    acquisition = _validate_v3_group_submission(
        _decode_json_bytes(acquisition_raw, "materialized group submission"),
        repo_root=repo_root, policy=policy, source_commit=args.expected_head,
        attempt=attempt,
    )
    _revalidate_attempt_root(roots)
    completion_raw = _read_bytes_once(completion_path)
    completion = _validate_v3_group_completion(
        _decode_json_bytes(completion_raw, "group completion receipt"),
        policy=policy, source_commit=args.expected_head, attempt=attempt,
        submission=acquisition,
        submission_sha256=acquisition_binding["sha256"],
        group_terminal_sha256=_sha256_file(group_terminal_path),
    )
    consume_non_certifying_observation(
        Path(evidence["result_root"]) / NON_CERTIFYING_OBSERVATION_FILENAME
    )
    if result.get("policy_sha256") != policy_sha:
        raise PaperStoryError("v3 raw result policy hash differs")
    _verify_current_source(
        repo_root, args.expected_head, result["source_binding"], policy,
    )
    _revalidate_raw_wals(result, receipt, policy)
    destination = _exact_materialization_destination(
        repo_root, Path(args.destination), policy,
    )
    materialized_receipt = {
        **receipt,
        "materialization": {
            "destination": os.fspath(destination),
            "raw_result": {
                "path": os.fspath(raw_result_path),
                "sha256": _sha256_file(raw_result_path),
            },
            "raw_receipt": {
                "path": os.fspath(raw_receipt_path),
                "sha256": _sha256_file(raw_receipt_path),
            },
            "job_terminal": {
                "path": os.fspath(group_terminal_path),
                "sha256": _sha256_file(group_terminal_path),
            },
            "scheduler_completion_receipt": {
                "path": os.fspath(completion_path),
                "sha256": _sha256_bytes(completion_raw),
            },
        },
    }
    _publish_materialization_bundle(
        destination,
        materialized_receipt,
        _materialized_result(result, completion, terminal),
        policy,
    )
    return 0


def run_materialize(args) -> int:
    repo_root = _repo_root()
    raw_result_path = Path(args.raw_result).resolve(strict=True)
    raw_receipt_path = Path(args.raw_receipt).resolve(strict=True)
    job_terminal_path = Path(args.job_terminal).resolve(strict=True)
    completion_receipt_path = Path(args.completion_receipt).resolve(strict=True)
    result = _read_json(raw_result_path)
    receipt = _read_json(raw_receipt_path)
    terminal = _read_json(job_terminal_path)
    policy, policy_sha = _load_policy_for_study(result.get("study_id"))
    study_id = _policy_study_id(policy)
    _require_policy_ready_for_execution(policy)
    if _policy_schema(policy) == POLICY_SCHEMA_V3:
        return _run_materialize_v3(
            args, repo_root=repo_root, result=result, receipt=receipt,
            terminal=terminal, policy=policy, policy_sha=policy_sha,
            raw_result_path=raw_result_path, raw_receipt_path=raw_receipt_path,
            group_terminal_path=job_terminal_path,
            completion_path=completion_receipt_path,
        )
    validate_raw_documents(result, receipt, terminal, policy)
    acquisition_binding = receipt.get("submission_receipt")
    if (
        type(acquisition_binding) is not dict
        or set(acquisition_binding) != {"path", "sha256"}
        or type(acquisition_binding.get("path")) is not str
        or type(acquisition_binding.get("sha256")) is not str
    ):
        raise PaperStoryError("raw receipt acquisition binding differs")
    acquisition_path = Path(acquisition_binding["path"])
    if not acquisition_path.is_absolute() or acquisition_path.resolve(
        strict=True
    ) != acquisition_path:
        raise PaperStoryError("materialized acquisition path is not canonical absolute")
    acquisition_raw = _read_bytes_once(acquisition_path)
    if (
        acquisition_raw is None
        or _sha256_bytes(acquisition_raw) != acquisition_binding["sha256"]
        or terminal.get("submission_receipt_sha256") != acquisition_binding["sha256"]
    ):
        raise PaperStoryError("acquisition receipt bytes do not cross-bind")
    acquisition = _decode_json_bytes(acquisition_raw, "materialized acquisition receipt")
    trusted_roots = validate_acquisition_receipt(
        acquisition,
        repo_root=repo_root,
        study_id=study_id,
        source_commit=args.expected_head,
        request_id=receipt.get("pbs_jobid"),
        pbs_observation=terminal.get("pbs_observation"),
        policy=policy,
    )
    submission_variables = acquisition.get("qsub_options", {}).get("variables")
    if (
        type(submission_variables) is not dict
        or submission_variables.get("IZANAGI_SUBMISSION_NONCE")
        != result["reservation_binding"]["nonce"]
    ):
        raise PaperStoryError("reservation nonce differs from submission binding")
    _revalidate_attempt_root(receipt.get("roots", {}))
    if receipt.get("roots") != trusted_roots:
        raise PaperStoryError("raw receipt roots differ from fixed acquisition topology")
    if receipt.get("scheduler_completion_receipt") != {
        "path": trusted_roots["completion_receipt"]
    }:
        raise PaperStoryError("raw receipt scheduler completion binding differs")
    if (
        raw_result_path != Path(trusted_roots["result_root"]) / "result.json"
        or raw_receipt_path != Path(trusted_roots["result_root"]) / "receipt.json"
        or job_terminal_path != Path(trusted_roots["raw_root"]) / "job-terminal.json"
        or completion_receipt_path != Path(trusted_roots["completion_receipt"])
    ):
        raise PaperStoryError("raw document paths differ from fixed attempt topology")
    completion_raw = _read_bytes_once(completion_receipt_path)
    if completion_raw is None:  # pragma: no cover - missing_ok is false
        raise PaperStoryError("scheduler completion receipt is missing")
    completion = _decode_json_bytes(completion_raw, "scheduler completion receipt")
    validate_completion_receipt(
        completion,
        trusted_roots=trusted_roots,
        source_commit=args.expected_head,
        request_id=receipt.get("pbs_jobid"),
        submission_receipt=acquisition,
        submission_receipt_sha256=acquisition_binding["sha256"],
        job_terminal_sha256=_sha256_file(job_terminal_path),
        study_id=study_id,
    )
    if result.get("policy_sha256") != policy_sha:
        raise PaperStoryError("raw result policy hash differs from tracked policy")
    if receipt.get("policy") != {
        "path": _policy_relative_path(policy),
        "sha256": policy_sha,
    }:
        raise PaperStoryError("raw receipt policy binding differs")
    if receipt.get("result") != {
        "path": os.fspath(raw_result_path),
        "sha256": _sha256_file(raw_result_path),
        "complete": result["complete"],
        "all_workloads_terminal": result["all_workloads_terminal"],
    }:
        raise PaperStoryError("raw receipt result binding differs")
    if terminal.get("result_sha256") != _sha256_file(raw_result_path):
        raise PaperStoryError("job terminal result hash differs")
    if terminal.get("receipt_sha256") != _sha256_file(raw_receipt_path):
        raise PaperStoryError("job terminal receipt hash differs")
    _verify_current_source(
        repo_root, args.expected_head, result["source_binding"], policy,
    )
    _revalidate_raw_wals(result, receipt, policy)

    destination = _exact_materialization_destination(
        repo_root, Path(args.destination), policy,
    )
    materialized_receipt = {
        **receipt,
        "materialization": {
            "destination": os.fspath(destination),
            "raw_result": {
                "path": os.fspath(raw_result_path),
                "sha256": _sha256_file(raw_result_path),
            },
            "raw_receipt": {
                "path": os.fspath(raw_receipt_path),
                "sha256": _sha256_file(raw_receipt_path),
            },
            "job_terminal": {
                "path": os.fspath(job_terminal_path),
                "sha256": _sha256_file(job_terminal_path),
            },
            "scheduler_completion_receipt": {
                "path": os.fspath(completion_receipt_path),
                "sha256": _sha256_bytes(completion_raw),
            },
        },
    }
    _publish_materialization_bundle(
        destination,
        materialized_receipt,
        _materialized_result(result, completion, terminal),
        policy,
    )
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    submit = sub.add_parser("submit")
    submit.add_argument("--study-id", required=True)
    submit.add_argument("--expected-head", required=True)
    submit.add_argument("--attempt-root", required=True)
    submit.add_argument("--third-party-source-root")
    measure = sub.add_parser("measure")
    measure.add_argument("--study-id", required=True)
    measure.add_argument("--expected-head", required=True)
    measure.add_argument("--pbs-jobid", required=True)
    measure.add_argument("--acquisition-receipt", required=True)
    measure.add_argument("--acquisition-receipt-sha256", required=True)
    measure.add_argument("--output-root", required=True)
    measure.add_argument("--cache-root", required=True)
    measure.add_argument("--result-root", required=True)
    measure.add_argument("--dependency-prefix", required=True)
    measure.add_argument("--third-party-source-root")
    measure.add_argument("--workload", choices=WORKLOAD_ORDER)
    materialize = sub.add_parser("materialize")
    materialize.add_argument("--expected-head", required=True)
    materialize.add_argument("--raw-result", required=True)
    materialize.add_argument("--raw-receipt", required=True)
    materialize.add_argument("--job-terminal", required=True)
    materialize.add_argument("--completion-receipt", required=True)
    materialize.add_argument("--destination", required=True)
    complete = sub.add_parser("complete")
    complete.add_argument("--study-id", default=STUDY_ID)
    complete.add_argument("--expected-head", required=True)
    complete.add_argument("--attempt-root", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.mode == "submit":
            return run_submit(args)
        if args.mode == "measure":
            return run_measurement(args)
        if args.mode == "complete":
            return run_complete(args)
        return run_materialize(args)
    except PaperStoryError as exc:
        print(f"paper-story A-1 refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
