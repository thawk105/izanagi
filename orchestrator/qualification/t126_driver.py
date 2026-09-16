#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-126 qualification-only controller.

Public modes are ``run`` and read-only ``verify``.  There is deliberately no
promote, official, headline, or resume mode.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.qualification"

from orchestrator.campaign import (  # noqa: E402
    env_attestation,
    env_contract,
    pipeline,
    reservation,
    source_digest,
)
from orchestrator.campaign.build_admission import (  # noqa: E402
    GeneratorId,
    build_run_context,
)
from orchestrator.campaign.model import Genome  # noqa: E402
from orchestrator.calibrator import perf_preflight as _perf_preflight  # noqa: E402

from .artifacts import (  # noqa: E402
    QualificationArtifactError,
    QualificationEventSink,
    QualificationRoot,
    ReceiptVerification,
    create_attempt,
    create_json,
    file_record,
    load_json_strict,
    load_jsonl_strict,
    load_source_json,
    safe_relative_path,
    select_source_pair,
    sha256_file,
    snapshot_source,
    validate_member_evidence,
    validate_json_schema,
    verify_manifest_entries,
)
from .attempt_ledger import SeriesAttemptLedger  # noqa: E402
from .contract import (  # noqa: E402
    ProtocolError,
    REQUIRED_CODE_IDENTITY_PATHS,
    REQUIRED_SCRIPT_IDENTITY_PATHS,
    RESERVATION_POLICY_RELATIVE_PATH,
    attempt_identity,
    canonical_json_bytes,
    load_protocol,
    protocol_sha256,
    series_identity,
    sprt_decide,
)
from .series import SeriesFSM, replay_ledger  # noqa: E402
from .identity import (  # noqa: E402
    verify_recorded_series_identity,
    verify_submission_script_chain,
)
from .qsub_binding import validate_qsub_binding  # noqa: E402
from .retry_index import (  # noqa: E402
    RetryIndexError,
    validate_retry_index,
)


_HEX40 = re.compile(r"[0-9a-f]{40}")
_HEX64 = re.compile(r"[0-9a-f]{64}")
_CANONICAL_GENOME = re.compile(r"([a-zA-Z0-9_.-]+)\|(.+)")

RC_SUCCESS = 0
RC_CLEAN_UPPER = 20
RC_INDETERMINATE = 21
RC_MEMBER_REJECTED = 30
RC_ATTESTATION = 31
RC_RESERVATION = 32
RC_MEMBER_TIMEOUT = 33
RC_INFRASTRUCTURE = 34


class QualificationDriverError(RuntimeError):
    """The controller cannot produce a valid series result."""

    rc = RC_INFRASTRUCTURE


def _exact_retry_index(value: object, label: str) -> int:
    try:
        return validate_retry_index(value)
    except RetryIndexError as exc:
        raise QualificationDriverError(
            f"{label} retry index is not exact") from exc


class MemberRunError(QualificationDriverError):
    def __init__(self, reason: str, evidence: Mapping[str, Any]):
        super().__init__(reason)
        self.reason = reason
        self.evidence = dict(evidence)
        self.rc = (
            RC_MEMBER_TIMEOUT
            if reason in {"member-timeout", "member-descendant-survived"}
            else RC_MEMBER_REJECTED
            if reason == "member-evaluation-rejected"
            else RC_INFRASTRUCTURE
        )


class AttestationError(QualificationDriverError):
    rc = RC_ATTESTATION


class ReservationError(QualificationDriverError):
    rc = RC_RESERVATION


class ControllerSignal(QualificationDriverError):
    """A scheduler/controller signal interrupted the series."""

    rc = RC_INFRASTRUCTURE


@dataclasses.dataclass(frozen=True)
class MonotonicEnvelope:
    started_ns: int
    deadline_ns: int
    wmax_s: int
    monotonic_ns: Callable[[], int] = time.monotonic_ns

    @classmethod
    def from_environ(
            cls, environ: Mapping[str, str], wmax_s: int) -> "MonotonicEnvelope":
        raw_started = environ.get("IZANAGI_T126_JOB_STARTED_MONOTONIC_NS")
        raw_deadline = environ.get("IZANAGI_T126_JOB_DEADLINE_MONOTONIC_NS")
        if raw_started is None or raw_deadline is None:
            raise QualificationDriverError(
                "live run requires the external job monotonic envelope")
        try:
            started = int(raw_started or "")
            deadline = int(raw_deadline or "")
        except ValueError as exc:
            raise QualificationDriverError(
                "job monotonic envelope is not exact integers") from exc
        if (started < 0 or deadline <= started
                or deadline - started != wmax_s * 1_000_000_000):
            raise QualificationDriverError("job monotonic envelope mismatch")
        return cls(started, deadline, wmax_s)

    def remaining_s(self, *, reserve_s: float = 0.0) -> float:
        remaining = (
            self.deadline_ns - self.monotonic_ns()) / 1_000_000_000 - reserve_s
        if remaining <= 0:
            raise QualificationDriverError("qualification Wmax deadline exhausted")
        return remaining

    def receipt(self) -> dict[str, int]:
        completed = self.monotonic_ns()
        elapsed = completed - self.started_ns
        if elapsed < 0 or completed > self.deadline_ns:
            raise QualificationDriverError("qualification exceeded monotonic Wmax")
        return {
            "job_started_monotonic_ns": self.started_ns,
            "completed_monotonic_ns": completed,
            "elapsed_ns": elapsed,
            "wmax_s": self.wmax_s,
        }


class ActiveProcessGroups:
    """Track all owned PGIDs and synchronously extinguish them on every exit."""

    def __init__(self, grace_s: float):
        self.grace_s = grace_s
        self._active: set[int] = set()
        self._old_handlers: dict[int, Any] = {}

    def add(self, pgid: int) -> None:
        if type(pgid) is not int or pgid <= 0:
            raise QualificationDriverError("active PGID is invalid")
        self._active.add(pgid)

    def discard(self, pgid: int) -> None:
        self._active.discard(pgid)

    def terminate_all(self) -> None:
        survivors = []
        for pgid in tuple(self._active):
            if _terminate_process_group(pgid, self.grace_s):
                self._active.discard(pgid)
            else:
                survivors.append(pgid)
        if survivors:
            raise QualificationDriverError(
                f"controller descendants survived: {survivors}")

    def _handle(self, signum, _frame):
        try:
            self.terminate_all()
        finally:
            raise ControllerSignal(f"controller received signal {signum}")

    def __enter__(self):
        for signum in (signal.SIGTERM, signal.SIGHUP):
            self._old_handlers[signum] = signal.getsignal(signum)
            signal.signal(signum, self._handle)
        return self

    def __exit__(self, _exc_type, _exc, _tb):
        cleanup_error = None
        try:
            self.terminate_all()
        except Exception as exc:  # preserve cleanup failure after body exception
            cleanup_error = exc
        finally:
            for signum, handler in self._old_handlers.items():
                signal.signal(signum, handler)
        if cleanup_error is not None:
            raise cleanup_error


def _fork_owned_process_group(
        process_groups: ActiveProcessGroups) -> tuple[int, bool]:
    """Fork with TERM/HUP blocked until the child group is registered."""
    blocked = {signal.SIGTERM, signal.SIGHUP}
    old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, blocked)
    ready_read, ready_write = os.pipe()
    try:
        pid = os.fork()
    except BaseException:
        os.close(ready_read)
        os.close(ready_write)
        signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
        raise
    if pid == 0:
        os.close(ready_read)
        try:
            os.setsid()
            os.write(ready_write, b"R")
        except BaseException:
            os.close(ready_write)
            signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
            os._exit(RC_INFRASTRUCTURE)
        os.close(ready_write)
        signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
        return 0, True
    os.close(ready_write)
    try:
        ready = os.read(ready_read, 1)
        if ready != b"R":
            try:
                os.waitpid(pid, 0)
            except ChildProcessError:
                pass
            raise QualificationDriverError(
                "child process group did not become ready")
        process_groups.add(pid)
    finally:
        os.close(ready_read)
        signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
    return pid, False


def _terminate_process_group(pgid: int, grace_s: float) -> bool:
    """Terminate only a controller-owned process group and confirm extinction."""
    def reap_direct_child() -> None:
        try:
            os.waitpid(pgid, os.WNOHANG)
        except (ChildProcessError, ProcessLookupError):
            pass

    started = time.monotonic()
    hard_deadline = started + max(0.0, grace_s)
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        return True
    deadline = started + max(0.0, grace_s) / 2.0
    while time.monotonic() < deadline:
        reap_direct_child()
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.05)
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        return True
    while time.monotonic() < hard_deadline:
        reap_direct_child()
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.05)
    reap_direct_child()
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return True
    return False


def _run_git(repo_root: Path, *args: str) -> str:
    try:
        value = subprocess.check_output(
            ["git", "-C", str(repo_root), *args],
            text=True, stderr=subprocess.DEVNULL, timeout=10,
        ).strip()
    except (OSError, subprocess.SubprocessError) as exc:
        raise QualificationDriverError(f"git identity command failed: {args}: {exc}") from exc
    return value


def _parse_genome(canonical: str) -> Genome:
    if type(canonical) is not str:
        raise QualificationDriverError("genome must be a canonical string")
    match = _CANONICAL_GENOME.fullmatch(canonical)
    if match is None:
        raise QualificationDriverError(f"invalid canonical genome: {canonical!r}")
    flags = {}
    for assignment in match.group(2).split(","):
        if assignment.count("=") != 1:
            raise QualificationDriverError("invalid genome flag assignment")
        key, raw = assignment.split("=", 1)
        if not key or key in flags:
            raise QualificationDriverError("duplicate/empty genome flag")
        try:
            flags[key] = int(raw, 10)
        except ValueError as exc:
            raise QualificationDriverError("genome flag must be an integer") from exc
    genome = Genome(match.group(1), flags)
    if genome.canonical() != canonical:
        raise QualificationDriverError("genome is not canonical")
    return genome


def _identity_files(
        source_root: Path, git_repo_root: Path,
        commit: str) -> tuple[dict[str, str], dict[str, str]]:
    code_paths = tuple(sorted(REQUIRED_CODE_IDENTITY_PATHS))
    script_paths = tuple(sorted(REQUIRED_SCRIPT_IDENTITY_PATHS))
    code = {}
    scripts = {}
    for relative in code_paths:
        path = source_root / relative
        if path.is_symlink() or not path.is_file():
            raise QualificationDriverError(f"identity code file missing: {relative}")
        current = sha256_file(path)
        if current != _git_blob_sha256(git_repo_root, commit, relative):
            raise QualificationDriverError(
                f"identity code file differs from HEAD: {relative}")
        code[relative] = current
    for relative in script_paths:
        path = source_root / relative
        if path.is_symlink() or not path.is_file():
            raise QualificationDriverError(f"identity script file missing: {relative}")
        current = sha256_file(path)
        if current != _git_blob_sha256(git_repo_root, commit, relative):
            raise QualificationDriverError(
                f"identity script file differs from HEAD: {relative}")
        scripts[relative] = current
    return code, scripts


def _git_blob_sha256(repo_root: Path, commit: str, relative: str) -> str:
    try:
        blob = subprocess.check_output(
            ["git", "-C", str(repo_root), "show", f"{commit}:{relative}"],
            stderr=subprocess.DEVNULL, timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise QualificationDriverError(
            f"cannot bind HEAD blob identity: {relative}: {exc}") from exc
    return hashlib.sha256(blob).hexdigest()


def build_series_preimage(
        repo_root: Path, protocol: Mapping[str, Any],
        toolchain_manifest: Mapping[str, Any], *,
        source_root: Path | None = None) -> dict[str, Any]:
    """Bind source, code, scripts, protocol, and toolchain into one series ID."""
    commit = _run_git(repo_root, "rev-parse", "--verify", "HEAD")
    tree = _run_git(repo_root, "rev-parse", "--verify", "HEAD^{tree}")
    gitlink = _run_git(repo_root, "rev-parse", "--verify", "HEAD:external/ccbench")
    if (_HEX40.fullmatch(commit) is None or _HEX40.fullmatch(tree) is None
            or _HEX40.fullmatch(gitlink) is None):
        raise QualificationDriverError("git source identity is not full lowercase hex")
    code, scripts = _identity_files(source_root or repo_root, repo_root, commit)
    source = protocol["source"]
    return {
        "schema_version": "t126-qualification-series-identity/v1",
        "protocol_sha256": protocol_sha256(protocol),
        "superproject_commit": commit,
        "superproject_tree": tree,
        "ccbench_gitlink": gitlink,
        "source_snapshots": {
            "campaign_lock": {
                "path": source["campaign_lock_path"],
                "sha256": source["campaign_lock_sha256"],
            },
            "wal": {
                "path": source["wal_path"],
                "sha256": source["wal_sha256"],
            },
        },
        "pair_roles": source["members"],
        "workload": protocol["workload"],
        "verification": protocol["verification"],
        "threshold": protocol["threshold"],
        "sprt": protocol["sprt"],
        "timing": protocol["timing"],
        "order_seed": protocol["order"]["seed"],
        "code_identity": code,
        "script_identity": scripts,
        "toolchain_manifest": dict(toolchain_manifest),
    }


def _boot_id() -> str:
    try:
        value = Path("/proc/sys/kernel/random/boot_id").read_text(
            encoding="ascii").strip()
    except OSError as exc:
        raise QualificationDriverError(f"cannot read boot id: {exc}") from exc
    if not value:
        raise QualificationDriverError("boot id is empty")
    return value


def _attest(repo_root: Path, contract) -> dict[str, Any]:
    try:
        verified = env_attestation.load_verified_calibration(contract, repo_root)
        observed = env_attestation.probe()
        parsed = env_attestation.parse_probe_output(json.dumps({
            "schema_version": env_attestation.PEGASUS_PROBE_OUTPUT_V2,
            "ok": True,
            "observed_epoch": int(time.time()),
            "profile": env_attestation.observed_profile_to_dict(observed),
        }))
        comparisons = env_attestation.compare_profiles(
            verified.calibration.attestation_profile, parsed.profile, now_fn=time.time,
        )
        observed_sha256 = env_attestation.observed_profile_sha256(parsed)
    except Exception as exc:
        raise QualificationDriverError(f"attestation failed: {type(exc).__name__}: {exc}") from exc
    if not comparisons or any(row.get("verdict") != "pass" for row in comparisons):
        raise QualificationDriverError("attestation comparison contains a mismatch")
    return {
        "schema_version": "t126-qualification-attestation/v2",
        "status": "accepted",
        "expected_profile_sha256": verified.attestation_profile_sha256,
        "observed_profile_sha256": observed_sha256,
        "observed_profile_projection_schema": parsed.schema_version,
        "comparisons": comparisons,
    }


def _member_identity(
        *, ccbench_gitlink: str, source_token: str, genome: Genome,
        role: str) -> str:
    return hashlib.sha256(canonical_json_bytes({
        "schema_version": "t126-live-member-identity/v1",
        "ccbench_gitlink": ccbench_gitlink,
        "full_source_digest": source_token,
        "genome": genome.canonical(),
        "role": role,
    })).hexdigest()


class ForkedMemberRunner:
    """Run one pipeline evaluation in a bounded process group."""

    def __init__(
            self, *, repo_root: Path, capability, layout, protocol,
            ccbench_dir: Path, cache_root: Path, ccbench_gitlink: str,
            process_groups: ActiveProcessGroups,
            envelope: MonotonicEnvelope,
            perf_observation: Mapping[str, Any] | None):
        self.repo_root = repo_root
        self.capability = capability
        self.layout = layout
        self.protocol = protocol
        self.ccbench_dir = ccbench_dir
        self.cache_root = cache_root
        self.ccbench_gitlink = ccbench_gitlink
        self.process_groups = process_groups
        self.envelope = envelope
        self.perf_observation = perf_observation

    def __call__(self, round_index: int, role: str) -> dict[str, Any]:
        source_member = self.protocol["source"]["members"][role]
        genome = _parse_genome(source_member["genome"])
        sink = QualificationEventSink(
            self.capability, self.layout, round_index=round_index, role=role,
            source_lock_identity_sha256=(
                self.protocol["source"]["campaign_lock_sha256"]
            ),
        )
        policy = pipeline.QualificationPipelinePolicy.t126_pegasus(sink)
        contract = env_contract.lookup(self.protocol["environment"]["env_tag"])
        perf_cfg = pipeline.PerfConfig(
            records=self.protocol["workload"]["records"],
            threads=self.protocol["workload"]["threads"],
            workload={
                "ycsb_zipf_skew": self.protocol["workload"]["ycsb_zipf_skew"],
                "ycsb_rratio": self.protocol["workload"]["ycsb_rratio"],
                "ycsb_rmw": self.protocol["workload"]["ycsb_rmw"],
                "ycsb_max_ope": self.protocol["workload"]["ycsb_max_ope"],
            },
            extime=self.protocol["workload"]["extime"],
            reps=self.protocol["workload"]["reps"],
        )
        pid, is_child = _fork_owned_process_group(self.process_groups)
        if is_child:
            try:
                authorization = env_contract.authorize(
                    self.protocol["environment"]["env_tag"]
                )
                contract = authorization.contract
                full_source_digest = source_digest.compute(
                    genome, ccbench_dir=str(self.ccbench_dir),
                )
                build_context = build_run_context(
                    generator_id=GeneratorId.BACKOFF_SWEEP,
                )
                live_member_id = _member_identity(
                    ccbench_gitlink=self.ccbench_gitlink,
                    source_token=full_source_digest,
                    genome=genome,
                    role=role,
                )
                result = pipeline.evaluate(
                    genome,
                    self.layout,
                    contract.env_tag,
                    self.ccbench_gitlink,
                    perf_cfg,
                    contract.clocks_per_us,
                    numactl=contract.numactl,
                    extra_correctness=[
                        (pipeline.S2_TAG, pipeline.s2_correctness_workload())
                    ],
                    do_bench=True,
                    do_settle=True,
                    ccbench_dir=str(self.ccbench_dir),
                    cache_root=str(self.cache_root),
                    bench_max_rounds=self.protocol["workload"]["bench_max_rounds"],
                    env_contract=contract,
                    authorization_contract=authorization,
                    record_rep_returncodes=True,
                    qualification_policy=policy,
                    build_context=build_context,
                    log=lambda *args, **kwargs: None,
                    **_member_pipeline_perf_kwargs(self.perf_observation),
                )
                if not result.certified or result.aborted:
                    os._exit(RC_MEMBER_REJECTED)
                create_json(
                    self.capability,
                    (
                        f"attempts/{self.layout.attempt_id}/rounds/"
                        f"{round_index:04d}/{role}/member-runtime.json"
                    ),
                    {
                        "schema_version": "t126-qualification-member-runtime/v1",
                        "round_index": round_index,
                        "member_role": role,
                        "source_wal_variant": source_member["source_wal_variant"],
                        "genome": genome.canonical(),
                        "full_source_digest": full_source_digest,
                        "live_member_id": live_member_id,
                    },
                )
                os._exit(0)
            except BaseException:
                os._exit(RC_INFRASTRUCTURE)

        cap_s = min(
            float(self.protocol["timing"]["member_cap_s"]),
            self.envelope.remaining_s(
                reserve_s=self.protocol["timing"]["finalize_reserve_s"]),
        )
        grace_s = self.protocol["timing"]["member_term_grace_s"]
        hard_deadline = time.monotonic() + cap_s
        deadline = hard_deadline - grace_s
        status = None
        timed_out = False
        while time.monotonic() < deadline:
            waited, status = os.waitpid(pid, os.WNOHANG)
            if waited == pid:
                break
            time.sleep(0.1)
        else:
            timed_out = True
            try:
                os.killpg(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            while time.monotonic() < hard_deadline:
                waited, status = os.waitpid(pid, os.WNOHANG)
                if waited == pid:
                    break
                time.sleep(0.1)
            else:
                try:
                    os.killpg(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                _, status = os.waitpid(pid, 0)
        if status is None:
            _, status = os.waitpid(pid, 0)
        try:
            os.killpg(pid, 0)
        except ProcessLookupError:
            descendants_gone = True
        else:
            descendants_gone = _terminate_process_group(
                pid, max(0.0, hard_deadline - time.monotonic()))
        if descendants_gone:
            self.process_groups.discard(pid)
        if timed_out or not descendants_gone:
            raise MemberRunError(
                "member-timeout" if timed_out else "member-descendant-survived",
                {"member_cap_s": cap_s, "descendants_gone": descendants_gone},
            )
        rc = os.waitstatus_to_exitcode(status)
        relative = self.layout.member_events_relpath(round_index, role)
        event_path = self.capability.root / relative
        if rc != 0:
            evidence = {"rc": rc}
            if event_path.is_file() and not event_path.is_symlink():
                evidence["event_file"] = file_record(
                    event_path, relative_to=self.layout.attempt_dir,
                )
            reason = (
                "member-evaluation-rejected"
                if rc == RC_MEMBER_REJECTED else "member-infrastructure"
            )
            raise MemberRunError(reason, evidence)
        records = load_jsonl_strict(event_path)
        admitted = validate_member_evidence(
            records, expected_role=role, expected_round=round_index,
            expected_reps=self.protocol["workload"]["reps"],
            expected_perf_observation=self.perf_observation,
            expected_lock_identity_sha256=(
                self.protocol["source"]["campaign_lock_sha256"]
            ),
        )
        runtime_path = event_path.with_name("member-runtime.json")
        runtime = load_json_strict(runtime_path)
        if (set(runtime) != {
                "schema_version", "round_index", "member_role",
                "source_wal_variant", "genome", "full_source_digest",
                "live_member_id"}
                or runtime["schema_version"]
                != "t126-qualification-member-runtime/v1"
                or runtime["round_index"] != round_index
                or runtime["member_role"] != role
                or runtime["source_wal_variant"]
                != source_member["source_wal_variant"]
                or runtime["genome"] != genome.canonical()
                or _HEX64.fullmatch(runtime["full_source_digest"]) is None
                or _HEX64.fullmatch(runtime["live_member_id"]) is None
                or runtime["live_member_id"] != _member_identity(
                    ccbench_gitlink=self.ccbench_gitlink,
                    source_token=runtime["full_source_digest"],
                    genome=genome,
                    role=role,
                )):
            raise MemberRunError(
                "member-runtime-identity",
                {"path": runtime_path.relative_to(self.layout.attempt_dir).as_posix()},
            )
        admitted.update({
            "live_member_id": runtime["live_member_id"],
            "full_source_digest": runtime["full_source_digest"],
            "source_wal_variant": source_member["source_wal_variant"],
            "evidence_ref": file_record(
                event_path, relative_to=self.layout.attempt_dir,
            ),
            "terminal_monotonic": time.monotonic(),
        })
        return admitted


def _member_pipeline_perf_kwargs(
        perf_observation: Mapping[str, Any] | None) -> dict[str, Any]:
    """Keep the legacy evaluate call exact unless prologue proved degraded."""
    if perf_observation is None:
        return {}
    if perf_observation.get("use_perf") is not False:
        raise QualificationDriverError(
            "member perf observation is not canonical degraded evidence")
    return {
        "use_perf": False,
        "perf_preflight_receipt": perf_observation["preflight"],
    }


def _series_result_perf_fields(
        perf_observation: Mapping[str, Any] | None) -> dict[str, Any]:
    """Keep the legacy series-result key set exact for perf-present runs."""
    if perf_observation is None:
        return {}
    return {"perf_observation": perf_observation}


def run_series(
        *, fsm: SeriesFSM, protocol: Mapping[str, Any],
        member_runner: Callable[[int, str], Mapping[str, Any]],
        attestation_fn: Callable[[str, Optional[int]], Mapping[str, Any]],
        reservation_recheck: Callable[[int], None],
        sleep_fn: Callable[[float], None] = time.sleep,
        monotonic_fn: Callable[[], float] = time.monotonic,
        envelope: MonotonicEnvelope | None = None,
) -> dict[str, Any]:
    """Execute at most one pre-registered series without resume or relabeling."""
    fsm.open()
    rounds = []
    rmax = protocol["sprt"]["rmax"]
    for round_index in range(1, rmax + 1):
        if envelope is not None:
            envelope.remaining_s(
                reserve_s=protocol["timing"]["finalize_reserve_s"])
        remaining_members = 2 * (rmax - round_index + 1)
        remaining_gaps = rmax - round_index
        remaining_required = (
            remaining_members * protocol["timing"]["member_cap_s"]
            + remaining_gaps * protocol["timing"]["round_gap_s"]
            + protocol["timing"]["attestation_cap_s"]
            + protocol["timing"]["finalize_reserve_s"]
        )
        try:
            reservation_recheck(remaining_required)
        except Exception as exc:
            fsm.reject(
                "reservation-recheck",
                {"type": type(exc).__name__, "message": str(exc)},
                round_index=(round_index - 1 or None),
            )
            raise
        try:
            attestation_fn("pre-round", round_index)
        except Exception as exc:
            fsm.reject(
                "attestation",
                {"stage": "pre-round", "type": type(exc).__name__,
                 "message": str(exc)},
                round_index=(round_index - 1 or None),
            )
            raise
        order = fsm.open_round(round_index)
        member_results = {}
        last_terminal = None
        for role in order:
            try:
                result = dict(member_runner(round_index, role))
            except MemberRunError as exc:
                fsm.reject(
                    exc.reason, exc.evidence, round_index=round_index,
                )
                raise
            required = {"median_tps", "evidence_ref", "terminal_monotonic"}
            if not required.issubset(result):
                fsm.reject(
                    "member-evidence-incomplete",
                    {"role": role, "keys": sorted(result)},
                    round_index=round_index,
                )
                raise MemberRunError(
                    "member-evidence-incomplete", {"role": role})
            fsm.member_terminal(
                round_index, role, result["median_tps"], result["evidence_ref"],
            )
            member_results[role] = result
            last_terminal = float(result["terminal_monotonic"])
        decision = fsm.round_terminal(
            round_index,
            subject_median_tps=member_results["subject"]["median_tps"],
            reference_median_tps=member_results["reference"]["median_tps"],
        )
        round_event = fsm.events[-1]["payload"]
        rounds.append({
            "round_index": round_index,
            "member_order": list(order),
            "subject": member_results["subject"],
            "reference": member_results["reference"],
            "relative": round_event["relative"],
            "direction": round_event["direction"],
            "bit": round_event["bit"],
            "llr_hex": round_event["llr_hex"],
            "sprt_terminal": decision,
        })
        if decision != "continuing":
            try:
                attestation_fn("post-series", None)
            except Exception as exc:
                fsm.reject(
                    "attestation",
                    {"stage": "post-series", "type": type(exc).__name__,
                     "message": str(exc)},
                    round_index=round_index,
                )
                raise
            fsm.terminal(round_index)
            break
        gap = protocol["timing"]["round_gap_s"]
        now = monotonic_fn()
        elapsed = max(0.0, now - last_terminal)
        if elapsed < gap:
            wait_s = gap - elapsed
            if envelope is not None:
                remaining = envelope.remaining_s(
                    reserve_s=protocol["timing"]["finalize_reserve_s"])
                if wait_s > remaining:
                    raise QualificationDriverError(
                        "round gap cannot fit within monotonic deadline")
            sleep_fn(wait_s)
        elapsed = monotonic_fn() - last_terminal
        fsm.wait_satisfied(round_index, elapsed)
    replay = fsm.replay
    if replay.state != "terminal" or replay.terminal not in {
            "lower_boundary", "upper_boundary", "indeterminate"}:
        raise QualificationDriverError("series did not reach a clean terminal")
    decision = sprt_decide(replay.bits, protocol["sprt"])
    return {
        "terminal": decision.terminal,
        "bits": list(replay.bits),
        "rounds": rounds,
        "llr_hex": decision.llr_hex,
    }


def _toolchain_manifest(path: Path) -> dict[str, Any]:
    value = load_json_strict(path)
    if not value:
        raise QualificationDriverError("toolchain manifest is empty")
    return value


def _verify_prologue_evidence(
        path: Path, *, series_preimage: Mapping[str, Any],
        toolchain_manifest_path: Path,
) -> dict[str, Any] | None:
    value = load_json_strict(path)
    required = {
        "schema_version", "source_commit", "source_tree", "ccbench_gitlink",
        "tracked_only", "immutable_mode", "protocol_sha256", "policy_sha256",
        "reservation_policy_sha256", "driver_sha256", "job_script_sha256",
        "toolchain_manifest_sha256", "perf_smoke_returncode",
        "perf_smoke_stdout", "perf_smoke_stderr",
    }
    smoke_fields = {
        "perf_smoke_returncode", "perf_smoke_stdout", "perf_smoke_stderr",
    }
    common_required = required - smoke_fields
    key_set = set(value)
    if key_set not in (
            required, common_required | {"perf_observation"}):
        raise QualificationDriverError(
            "prologue source-stage/perf evidence is not consumer-verifiable")
    identities = {
        **series_preimage["code_identity"],
        **series_preimage["script_identity"],
    }
    if (value.get("schema_version") != "t126-source-stage-evidence/v1"
            or value["source_commit"] != series_preimage["superproject_commit"]
            or value["source_tree"] != series_preimage["superproject_tree"]
            or value["ccbench_gitlink"] != series_preimage["ccbench_gitlink"]
            or value["tracked_only"] is not True
            or value["immutable_mode"] is not True
            or value["protocol_sha256"] != identities[
                "orchestrator/qualification/t126_control_v1.json"]
            or value["policy_sha256"] != identities["tools/pegasus/policy.json"]
            or value["reservation_policy_sha256"] != identities[
                RESERVATION_POLICY_RELATIVE_PATH]
            or value["driver_sha256"] != identities[
                "orchestrator/qualification/t126_driver.py"]
            or value["job_script_sha256"] != identities[
                "tools/pegasus/t126_qualification.sh"]
            or value["toolchain_manifest_sha256"]
            != sha256_file(toolchain_manifest_path)):
        raise QualificationDriverError(
            "prologue source-stage/perf evidence is not consumer-verifiable")
    if key_set == required:
        perf_text = (
            str(value.get("perf_smoke_stdout", ""))
            + "\n" + str(value.get("perf_smoke_stderr", ""))).lower()
        if (value["perf_smoke_returncode"] != 0
                or "<not supported>" in perf_text
                or "<not counted>" in perf_text
                or not all(name in perf_text for name in (
                    "llc-load-misses", "llc-loads", "instructions", "cycles"))):
            raise QualificationDriverError(
                "prologue source-stage/perf evidence is not consumer-verifiable")
        return None
    try:
        observation = _perf_preflight.validate_perf_observation(
            value["perf_observation"], run_cmd=["true"],
            leading_indicators={"ipc": None, "llc_miss_rate": None},
        )
    except _perf_preflight.PerfPreflightError as exc:
        raise QualificationDriverError(
            "prologue source-stage/perf evidence is not consumer-verifiable"
        ) from exc
    if observation["use_perf"] is not False:
        raise QualificationDriverError(
            "prologue source-stage/perf evidence is not consumer-verifiable")
    return observation


def run(
        *, repo_root: Path, toolchain_manifest_path: Path,
        ccbench_dir: Path, cache_root: Path, environ: Mapping[str, str] = os.environ,
        artifact_repo_root: Path | None = None,
        git_repo_root: Path | None = None,
        prologue_evidence_path: Path | None = None,
) -> tuple[int, Path]:
    source_root = repo_root
    artifact_repo_root = artifact_repo_root or source_root
    git_repo_root = git_repo_root or source_root
    protocol = load_protocol(repo_root / "orchestrator/qualification/t126_control_v1.json")
    envelope = MonotonicEnvelope.from_environ(
        environ, protocol["timing"]["wmax_s"])
    envelope.remaining_s(
        reserve_s=protocol["timing"]["finalize_reserve_s"])
    select_source_pair(repo_root, protocol)
    contract = env_contract.lookup(protocol["environment"]["env_tag"])
    if (contract.clocks_per_us != protocol["environment"]["clocks_per_us"]
            or list(contract.numactl) != protocol["environment"]["numactl"]
            or contract.attestation_mode != protocol["environment"]["attestation_mode"]
            or contract.isolation_policy.single_process is not True
            or contract.isolation_policy.allow_resume is not False):
        raise QualificationDriverError("registered environment contract mismatch")
    toolchain = _toolchain_manifest(toolchain_manifest_path)
    series_preimage = build_series_preimage(
        git_repo_root, protocol, toolchain, source_root=source_root)
    series_id = series_identity(series_preimage)
    if prologue_evidence_path is None:
        raise QualificationDriverError(
            "live run requires immutable prologue evidence")
    perf_observation = _verify_prologue_evidence(
        prologue_evidence_path, series_preimage=series_preimage,
        toolchain_manifest_path=toolchain_manifest_path)
    try:
        binding = reservation.read_binding(environ)
        check = reservation.check_reservation(
            binding,
            required_s=protocol["timing"]["wmax_s"] - protocol["timing"]["prologue_cap_s"],
            safety_margin_s=0,
            environ=environ,
        )
    except Exception as exc:
        raise ReservationError(f"reservation check failed: {exc}") from exc
    nonce = environ.get("IZANAGI_SUBMISSION_NONCE", "")
    if re.fullmatch(r"[0-9a-f]{32}", nonce) is None:
        raise QualificationDriverError("submission nonce is not exact 32 lowercase hex")
    root = QualificationRoot(artifact_repo_root)
    capability = root.issue()
    submission_path = (
        root.path / "submissions" / nonce / "submit-receipt.json")
    submission = load_json_strict(submission_path)
    submitted_series_preimage = load_json_strict(
        submission_path.with_name("series-identity.json"))
    if (submitted_series_preimage != series_preimage
            or series_identity(submitted_series_preimage) != series_id):
        raise QualificationDriverError(
            "submission series identity differs from node identity")
    normalized_submit_job = str(submission.get("job_id", ""))
    normalized_binding_job = binding.job_id
    if normalized_submit_job.startswith("0:"):
        normalized_submit_job = normalized_submit_job[2:]
    if normalized_binding_job.startswith("0:"):
        normalized_binding_job = normalized_binding_job[2:]
    submission_retry_index = _exact_retry_index(
        submission.get("retry_index"), "submission receipt")
    if (submission.get("schema_version")
            != "t126-qualification-submit-receipt/v1"
            or submission.get("qualification_lineage") != "t126-only"
            or submission.get("authority") != "evidence-only/no-promotion"
            or submission.get("hold_enforced") is not False
            or submission.get("nonce") != nonce
            or normalized_submit_job != normalized_binding_job
            or submission.get("source_commit") != series_preimage["superproject_commit"]
            or submission.get("source_tree") != series_preimage["superproject_tree"]
            or submission.get("ccbench_gitlink") != series_preimage["ccbench_gitlink"]
            or submission.get("job_script_sha256")
            != series_preimage["script_identity"][
                "tools/pegasus/t126_qualification.sh"]
            or submission.get("collector_sha256")
            != series_preimage["script_identity"][
                "tools/pegasus/collect_t126_qualification.py"]
            or submission.get("protocol_sha256")
            != sha256_file(
                repo_root / "orchestrator/qualification/t126_control_v1.json")
            or _HEX64.fullmatch(
                submission.get("submission_intent_sha256", "")) is None
            or (
                submission_retry_index == 0
                and any(submission.get(key) is not None for key in (
                    "retry_from_attempt_id", "retry_from_series_id",
                    "retry_receipt_sha256"))
            )
            or (
                submission_retry_index == 1
                and (
                    submission.get("retry_from_series_id") != series_id
                    or _HEX64.fullmatch(
                        submission.get("retry_from_attempt_id", "")) is None
                    or _HEX64.fullmatch(
                        submission.get("retry_receipt_sha256", "")) is None
                )
            )):
        raise QualificationDriverError("submission receipt identity mismatch")
    binding_path = submission_path.with_name("qsub-binding.json")
    invocation_path = submission_path.with_name("qsub-invocation.json")
    invocation = load_json_strict(invocation_path)
    invocation_retry_index = _exact_retry_index(
        invocation.get("retry_index"), "qsub invocation")
    invocation_sha256 = sha256_file(invocation_path)
    binding_record = load_json_strict(binding_path)
    validate_qsub_binding(
        binding_record, expected_nonce=nonce,
        expected_intent_sha256=submission["submission_intent_sha256"],
        expected_invocation_sha256=invocation_sha256,
        expected_retry_index=submission_retry_index,
        expected_job_id=submission["job_id"])
    if (set(invocation) != {
            "nonce", "retry_index", "submission_intent_sha256"}
            or invocation.get("nonce") != nonce
            or invocation_retry_index != submission_retry_index
            or invocation.get("submission_intent_sha256")
            != submission["submission_intent_sha256"]
            or submission.get("qsub_invocation_sha256")
            != invocation_sha256):
        raise QualificationDriverError(
            "submission qsub invocation proof is not durable and exact")
    verify_submission_script_chain(
        submission=submission, preimage=series_preimage)
    if submission.get("qsub_binding_sha256") != sha256_file(binding_path):
        raise QualificationDriverError(
            "submission qsub binding is not durable and exact")
    submission_sha256 = sha256_file(submission_path)
    attempt_preimage = {
        "schema_version": "t126-qualification-attempt-identity/v1",
        "qualification_series_id": series_id,
        "pbs_job_id": normalized_submit_job,
        "nonce": nonce,
        "retry_index": submission_retry_index,
        "submission_intent_sha256": submission["submission_intent_sha256"],
    }
    attempt_id = attempt_identity(attempt_preimage)
    attempt_ledger = SeriesAttemptLedger(
        capability, series_id, protocol["retry"]["eligible_reasons"])
    attempt_state = attempt_ledger.replay
    if (attempt_state.state not in {"initial_submitted", "retry_submitted"}
            or attempt_state.last_attempt_id != attempt_id
            or attempt_state.last_retry_index != submission_retry_index
            or attempt_state.last_job_id != normalized_submit_job
            or attempt_state.last_nonce != nonce
            or attempt_state.last_submission_intent_sha256
            != submission["submission_intent_sha256"]
            or attempt_state.last_qsub_invocation_sha256
            != invocation_sha256
            or attempt_state.last_submission_evidence_sha256
            != sha256_file(binding_path)):
        raise QualificationDriverError(
            "measurement cannot start before durable series-ledger binding")
    layout = create_attempt(
        root, capability, series_id=series_id, attempt_id=attempt_id,
    )
    job_staging_name = f"{normalized_submit_job}.{nonce}"
    if re.fullmatch(r"[A-Za-z0-9._-]+", job_staging_name) is None:
        raise QualificationDriverError("job id cannot form a safe staging name")
    create_json(
        capability,
        f"job-staging/{job_staging_name}/attempt-pointer.json",
        {
            "schema_version": "t126-qualification-attempt-pointer/v1",
            "qualification_series_id": series_id,
            "qualification_attempt_id": attempt_id,
            "pbs_job_id": normalized_submit_job,
            "nonce": nonce,
        },
    )
    prefix = f"attempts/{attempt_id}"
    create_json(capability, f"{prefix}/protocol.json", protocol)
    create_json(capability, f"{prefix}/series-identity.json", series_preimage)
    create_json(capability, f"{prefix}/attempt-identity.json", attempt_preimage)
    create_json(capability, f"{prefix}/reservation.json", dataclasses.asdict(binding))
    snapshot_source(
        capability, toolchain_manifest_path,
        f"{prefix}/prologue/toolchain-manifest.json",
        expected_sha256=sha256_file(toolchain_manifest_path),
    )
    if prologue_evidence_path is not None:
        snapshot_source(
            capability, prologue_evidence_path,
            f"{prefix}/prologue/source-stage-evidence.json",
            expected_sha256=sha256_file(prologue_evidence_path),
        )
    lock_snapshot = snapshot_source(
        capability, source_root / protocol["source"]["campaign_lock_path"],
        f"{prefix}/source/campaign.lock.snapshot",
        expected_sha256=protocol["source"]["campaign_lock_sha256"],
    )
    wal_snapshot = snapshot_source(
        capability, source_root / protocol["source"]["wal_path"],
        f"{prefix}/source/source-wal.snapshot.jsonl",
        expected_sha256=protocol["source"]["wal_sha256"],
    )
    submission_snapshot = snapshot_source(
        capability, submission_path,
        f"{prefix}/source/submission-receipt.snapshot.json",
        expected_sha256=submission_sha256,
    )
    binding_snapshot = snapshot_source(
        capability, binding_path,
        f"{prefix}/source/qsub-binding.snapshot.json",
        expected_sha256=sha256_file(binding_path),
    )
    invocation_snapshot = snapshot_source(
        capability, invocation_path,
        f"{prefix}/source/qsub-invocation.snapshot.json",
        expected_sha256=invocation_sha256,
    )
    for snapshot in (
            lock_snapshot, wal_snapshot, submission_snapshot, binding_snapshot,
            invocation_snapshot):
        snapshot["path"] = str(
            Path(snapshot["path"]).relative_to(Path(prefix)))
    create_json(capability, f"{prefix}/source/source-snapshots.json", {
        "schema_version": "t126-qualification-source-snapshots/v1",
        "campaign_lock": {
            "original_path": protocol["source"]["campaign_lock_path"],
            **lock_snapshot,
        },
        "wal": {
            "original_path": protocol["source"]["wal_path"],
            **wal_snapshot,
        },
        "submission_receipt": {
            "original_path": submission_path.relative_to(
                artifact_repo_root).as_posix(),
            **submission_snapshot,
        },
        "qsub_binding": {
            "original_path": binding_path.relative_to(
                artifact_repo_root).as_posix(),
            **binding_snapshot,
        },
        "qsub_invocation": {
            "original_path": invocation_path.relative_to(
                artifact_repo_root).as_posix(),
            **invocation_snapshot,
        },
    })
    identity = {
        "qualification_series_id": series_id,
        "qualification_attempt_id": attempt_id,
        "pbs_job_id": binding.job_id,
        "host": binding.host,
        "boot_id": binding.boot_id,
        "controller_pid": os.getpid(),
    }
    fsm = SeriesFSM(capability, layout.ledger_relpath, identity, protocol)
    process_groups = ActiveProcessGroups(
        protocol["timing"]["member_term_grace_s"])
    attestation_records = []
    attestation_elapsed_s = 0.0

    def attest(stage: str, round_index: Optional[int]) -> Mapping[str, Any]:
        nonlocal attestation_elapsed_s
        cap_s = protocol["timing"]["attestation_cap_s"]
        remaining_s = cap_s - attestation_elapsed_s
        if remaining_s <= 0:
            raise AttestationError(
                "aggregate attestation cap exhausted")
        relative = (
            f"{prefix}/attestation/{stage}-"
            f"{round_index if round_index is not None else 'final'}.json"
        )
        started = time.monotonic()
        pid, is_child = _fork_owned_process_group(process_groups)
        if is_child:
            try:
                payload = _attest(source_root, contract)
                payload.update({"stage": stage, "round_index": round_index})
                create_json(capability, relative, payload)
                os._exit(0)
            except BaseException:
                os._exit(RC_ATTESTATION)
        try:
            hard_deadline = started + remaining_s
            deadline = hard_deadline - min(
                protocol["timing"]["member_term_grace_s"], remaining_s)
            status = None
            while time.monotonic() < deadline:
                waited, status = os.waitpid(pid, os.WNOHANG)
                if waited == pid:
                    break
                time.sleep(0.1)
            else:
                try:
                    os.killpg(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                while time.monotonic() < hard_deadline:
                    waited, status = os.waitpid(pid, os.WNOHANG)
                    if waited == pid:
                        break
                    time.sleep(0.1)
                else:
                    try:
                        os.killpg(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    _, status = os.waitpid(pid, 0)
                raise AttestationError(
                    "aggregate attestation cap exceeded")
            if status is None:
                _, status = os.waitpid(pid, 0)
            if os.waitstatus_to_exitcode(status) != 0:
                raise AttestationError("attestation child rejected")
            try:
                os.killpg(pid, 0)
            except ProcessLookupError:
                pass
            else:
                if not _terminate_process_group(
                        pid, max(0.0, hard_deadline - time.monotonic())):
                    raise AttestationError(
                        "attestation descendant survived termination")
                raise AttestationError(
                    "attestation descendant survived child exit")
            process_groups.discard(pid)
        finally:
            attestation_elapsed_s += max(0.0, time.monotonic() - started)
        payload = load_json_strict(capability.root / relative)
        path = capability.root / relative
        attestation_records.append(file_record(path, relative_to=layout.attempt_dir))
        return payload

    def recheck(required_s: int) -> None:
        nonlocal check
        try:
            check = check.ensure_remaining(
                required_s=required_s, safety_margin_s=0)
        except Exception as exc:
            raise ReservationError(
                f"reservation remaining check failed: {exc}") from exc

    with process_groups:
        member_runner = ForkedMemberRunner(
            repo_root=repo_root, capability=capability, layout=layout,
            protocol=protocol, ccbench_dir=ccbench_dir, cache_root=cache_root,
            ccbench_gitlink=series_preimage["ccbench_gitlink"],
            process_groups=process_groups, envelope=envelope,
            perf_observation=perf_observation,
        )
        try:
            outcome = run_series(
                fsm=fsm, protocol=protocol, member_runner=member_runner,
                attestation_fn=attest, reservation_recheck=recheck,
                envelope=envelope,
            )
        except MemberRunError:
            raise
    evidence_manifest = []
    for path in sorted(layout.attempt_dir.rglob("*")):
        if path.is_file() and not path.is_symlink():
            evidence_manifest.append(file_record(path, relative_to=layout.attempt_dir))
    result = {
        "schema_version": "t126-qualification-series-result/v1",
        "qualification_lineage": "t126-only",
        "authority": "evidence-only/no-promotion",
        "hold_enforced": False,
        "statistical_claim": "none",
        "qualification_series_id": series_id,
        "qualification_attempt_id": attempt_id,
        "terminal": outcome["terminal"],
        "execution_integrity": "valid",
        "expectation_match": "not-applicable-observational-smoke",
        "bits": outcome["bits"],
        "rounds": outcome["rounds"],
        "ledger": file_record(
            layout.attempt_dir / "series-ledger.jsonl",
            relative_to=layout.attempt_dir,
        ),
        "evidence_manifest": evidence_manifest,
        "timing_envelope": envelope.receipt(),
    }
    result.update(_series_result_perf_fields(perf_observation))
    validate_json_schema("t126_series_result_schema.json", result)
    result_path = create_json(capability, f"{prefix}/series-result.json", result)
    rc = {
        "lower_boundary": RC_SUCCESS,
        "upper_boundary": RC_CLEAN_UPPER,
        "indeterminate": RC_INDETERMINATE,
    }[outcome["terminal"]]
    return rc, result_path


def verify(attempt_dir: Path) -> ReceiptVerification:
    errors = []
    try:
        attempt_dir = attempt_dir.resolve(strict=True)
        expected_suffix = Path(
            "output/env/pegasus/qualification/t126/attempts") / attempt_dir.name
        if Path(*attempt_dir.parts[-7:]) != expected_suffix:
            raise QualificationDriverError(
                "attempt is outside the exact qualification namespace")
        repo_root = attempt_dir.parents[6]
        marker = load_json_strict(attempt_dir / "qualification-marker.json")
        result = load_json_strict(attempt_dir / "series-result.json")
        protocol = load_protocol(attempt_dir / "protocol.json")
        series_preimage = load_json_strict(attempt_dir / "series-identity.json")
        attempt_preimage = load_json_strict(attempt_dir / "attempt-identity.json")
        reservation_record = load_json_strict(attempt_dir / "reservation.json")
        source_snapshots = load_json_strict(
            attempt_dir / "source/source-snapshots.json")
        ledger = load_jsonl_strict(attempt_dir / "series-ledger.jsonl")
        validate_json_schema("t126_series_result_schema.json", result)
        prologue_manifest = attempt_dir / "prologue/toolchain-manifest.json"
        perf_observation = _verify_prologue_evidence(
            attempt_dir / "prologue/source-stage-evidence.json",
            series_preimage=series_preimage,
            toolchain_manifest_path=prologue_manifest)
        for event in ledger:
            validate_json_schema("t126_event_schema.json", event)
        replay = replay_ledger(ledger, protocol)
        expected_result_keys = {
            "schema_version", "qualification_lineage", "authority",
            "hold_enforced", "statistical_claim", "qualification_series_id",
            "qualification_attempt_id", "terminal", "execution_integrity",
            "expectation_match", "bits", "rounds", "ledger",
            "evidence_manifest", "timing_envelope",
        }
        expected_result_keys.update(
            _series_result_perf_fields(perf_observation))
        if set(result) != expected_result_keys:
            raise QualificationDriverError("series result key set mismatch")
        if result.get("perf_observation") != perf_observation:
            raise QualificationDriverError(
                "series result/prologue perf observation mismatch")
        computed_series_id = series_identity(series_preimage)
        computed_attempt_id = attempt_identity(attempt_preimage)
        if (marker.get("qualification_series_id") != computed_series_id
                or result.get("qualification_series_id") != computed_series_id
                or marker.get("qualification_attempt_id") != computed_attempt_id
                or result.get("qualification_attempt_id") != computed_attempt_id
                or attempt_dir.name != computed_attempt_id):
            raise QualificationDriverError("marker/result identity mismatch")
        policy = load_source_json(repo_root / "tools/pegasus/policy.json")
        reservation_policy = load_source_json(
            repo_root / RESERVATION_POLICY_RELATIVE_PATH)
        verify_recorded_series_identity(
            git_repo_root=repo_root, attempt_dir=attempt_dir,
            preimage=series_preimage, protocol=protocol, policy=policy,
            reservation_policy=reservation_policy,
        )
        source_rows = source_snapshots
        if (set(source_rows) != {
                "schema_version", "campaign_lock", "wal", "submission_receipt",
                "qsub_binding", "qsub_invocation"}
                or source_rows["schema_version"]
                != "t126-qualification-source-snapshots/v1"):
            raise QualificationDriverError("source snapshot manifest mismatch")
        expected_sources = {
            "campaign_lock": (
                protocol["source"]["campaign_lock_path"],
                protocol["source"]["campaign_lock_sha256"],
            ),
            "wal": (
                protocol["source"]["wal_path"],
                protocol["source"]["wal_sha256"],
            ),
        }
        for name, (original_path, expected_hash) in expected_sources.items():
            row = source_rows[name]
            if (row.get("original_path") != original_path
                    or row.get("sha256") != expected_hash):
                raise QualificationDriverError(
                    f"{name} snapshot provenance mismatch")
            snapshot_path = attempt_dir / row["path"]
            if (snapshot_path.stat().st_size != row["size"]
                    or sha256_file(snapshot_path) != row["sha256"]):
                raise QualificationDriverError(f"{name} snapshot bytes mismatch")
        submission_row = source_rows["submission_receipt"]
        submission_snapshot = safe_relative_path(
            attempt_dir, submission_row["path"], "submission snapshot")
        if (submission_snapshot.stat().st_size != submission_row["size"]
                or sha256_file(submission_snapshot) != submission_row["sha256"]):
            raise QualificationDriverError("submission snapshot bytes mismatch")
        binding_row = source_rows["qsub_binding"]
        binding_snapshot = safe_relative_path(
            attempt_dir, binding_row["path"], "qsub binding snapshot")
        if (binding_snapshot.stat().st_size != binding_row["size"]
                or sha256_file(binding_snapshot) != binding_row["sha256"]):
            raise QualificationDriverError("qsub binding snapshot bytes mismatch")
        invocation_row = source_rows["qsub_invocation"]
        invocation_snapshot = safe_relative_path(
            attempt_dir, invocation_row["path"], "qsub invocation snapshot")
        if (invocation_snapshot.stat().st_size != invocation_row["size"]
                or sha256_file(invocation_snapshot)
                != invocation_row["sha256"]):
            raise QualificationDriverError(
                "qsub invocation snapshot bytes mismatch")
        submission_value = load_json_strict(submission_snapshot)
        submission_retry_index = _exact_retry_index(
            submission_value.get("retry_index"), "submission snapshot")
        binding_value = load_json_strict(binding_snapshot)
        invocation_value = load_json_strict(invocation_snapshot)
        invocation_retry_index = _exact_retry_index(
            invocation_value.get("retry_index"), "qsub invocation snapshot")
        validate_qsub_binding(
            binding_value,
            expected_nonce=submission_value.get("nonce"),
            expected_intent_sha256=submission_value.get(
                "submission_intent_sha256"),
            expected_invocation_sha256=invocation_row["sha256"],
            expected_retry_index=submission_retry_index,
            expected_job_id=submission_value.get("job_id"))
        if (set(invocation_value) != {
                "nonce", "retry_index", "submission_intent_sha256"}
                or invocation_value.get("nonce")
                != submission_value.get("nonce")
                or invocation_retry_index != submission_retry_index
                or invocation_value.get("submission_intent_sha256")
                != submission_value.get("submission_intent_sha256")
                or submission_value.get("qsub_invocation_sha256")
                != invocation_row["sha256"]):
            raise QualificationDriverError(
                "submission/qsub invocation snapshot mismatch")
        verify_submission_script_chain(
            submission=submission_value, preimage=series_preimage)
        if submission_value.get("qsub_binding_sha256") != binding_row["sha256"]:
            raise QualificationDriverError(
                "submission/qsub binding snapshot mismatch")
        event_identity = ledger[0]["identity"]
        if (event_identity["qualification_series_id"] != computed_series_id
                or event_identity["qualification_attempt_id"] != computed_attempt_id
                or event_identity["pbs_job_id"] != attempt_preimage["pbs_job_id"]
                or event_identity["host"] != reservation_record["host"]
                or event_identity["boot_id"] != reservation_record["boot_id"]
                or event_identity["controller_pid"] <= 0):
            raise QualificationDriverError("ledger/attempt identity mismatch")
        if (result.get("schema_version")
                != "t126-qualification-series-result/v1"
                or result.get("qualification_lineage") != "t126-only"
                or result.get("authority") != "evidence-only/no-promotion"
                or result.get("hold_enforced") is not False
                or result.get("statistical_claim") != "none"
                or result.get("terminal") != replay.terminal
                or result.get("bits") != list(replay.bits)
                or result.get("execution_integrity") != "valid"
                or result.get("expectation_match")
                != "not-applicable-observational-smoke"):
            raise QualificationDriverError("series result semantic mismatch")
        timing = result.get("timing_envelope")
        if (type(timing) is not dict or set(timing) != {
                "job_started_monotonic_ns", "completed_monotonic_ns",
                "elapsed_ns", "wmax_s"}
                or timing["wmax_s"] != protocol["timing"]["wmax_s"]
                or type(timing["job_started_monotonic_ns"]) is not int
                or type(timing["completed_monotonic_ns"]) is not int
                or type(timing["elapsed_ns"]) is not int
                or timing["elapsed_ns"] < 0
                or timing["elapsed_ns"] != (
                    timing["completed_monotonic_ns"]
                    - timing["job_started_monotonic_ns"])
                or timing["elapsed_ns"] > timing["wmax_s"] * 1_000_000_000):
            raise QualificationDriverError(
                "series result monotonic envelope mismatch")
        if len(result["rounds"]) != len(replay.bits):
            raise QualificationDriverError("round/result count mismatch")
        round_events = [
            event for event in ledger
            if event["event_type"] == "round_terminal"
        ]
        round_open_events = [
            event for event in ledger if event["event_type"] == "round_open"
        ]
        for expected_round, role_round in enumerate(result["rounds"], 1):
            round_index = role_round["round_index"]
            if round_index != expected_round:
                raise QualificationDriverError("round indexes are not contiguous")
            terminal_payload = round_events[expected_round - 1]["payload"]
            if (role_round.get("member_order")
                    != round_open_events[expected_round - 1][
                        "payload"]["member_order"]
                    or role_round.get("relative")
                    != terminal_payload["relative"]
                    or role_round.get("direction")
                    != terminal_payload["direction"]
                    or role_round.get("bit") != terminal_payload["bit"]
                    or role_round.get("llr_hex") != terminal_payload["llr_hex"]
                    or role_round.get("sprt_terminal")
                    != terminal_payload["sprt_terminal"]):
                raise QualificationDriverError(
                    f"round {round_index} decision summary mismatch")
            for role in ("subject", "reference"):
                path = (
                    attempt_dir / f"rounds/{round_index:04d}/{role}/"
                    "evaluation-events.jsonl"
                )
                admitted = validate_member_evidence(
                    load_jsonl_strict(path), expected_role=role,
                    expected_round=round_index,
                    expected_perf_observation=perf_observation,
                    expected_lock_identity_sha256=(
                        protocol["source"]["campaign_lock_sha256"]
                    ),
                )
                if (role_round[role]["median_tps"] != admitted["median_tps"]
                        or role_round[role]["evidence_ref"]
                        != file_record(path, relative_to=attempt_dir)):
                    raise QualificationDriverError(
                        f"round {round_index} {role} summary mismatch")
                runtime = load_json_strict(path.with_name("member-runtime.json"))
                expected_member = protocol["source"]["members"][role]
                if (role_round[role].get("live_member_id")
                        != runtime.get("live_member_id")
                        or role_round[role].get("full_source_digest")
                        != runtime.get("full_source_digest")
                        or role_round[role].get("source_wal_variant")
                        != expected_member["source_wal_variant"]):
                    raise QualificationDriverError(
                        f"round {round_index} {role} runtime identity mismatch")
        if result["ledger"] != file_record(
                attempt_dir / "series-ledger.jsonl", relative_to=attempt_dir):
            raise QualificationDriverError("series ledger reference mismatch")
        verify_manifest_entries(attempt_dir, result["evidence_manifest"])
        manifested = {row["path"] for row in result["evidence_manifest"]}
        actual = {
            path.relative_to(attempt_dir).as_posix()
            for path in attempt_dir.rglob("*")
            if path.is_file() and not path.is_symlink()
        }
        allowed_later = {
            "series-result.json", "job-result.json",
            "final-qualification-receipt.json",
            "attempt-failure-receipt.json",
        }
        unexpected = sorted(
            path for path in actual - manifested
            if path not in allowed_later
            and not path.startswith(("post-job/", "rejected-evidence/")))
        if unexpected:
            raise QualificationDriverError(
                f"unreferenced in-job evidence: {unexpected}")
        return ReceiptVerification("valid", "valid", replay.terminal, ())
    except Exception as exc:
        errors.append(f"{type(exc).__name__}: {exc}")
        return ReceiptVerification("invalid", "invalid", None, tuple(errors))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    run_p = sub.add_parser("run")
    run_p.add_argument("--repo-root", type=Path, required=True)
    run_p.add_argument("--toolchain-manifest", type=Path, required=True)
    run_p.add_argument("--ccbench-dir", type=Path, required=True)
    run_p.add_argument("--cache-root", type=Path, required=True)
    run_p.add_argument("--artifact-repo-root", type=Path)
    run_p.add_argument("--git-repo-root", type=Path)
    run_p.add_argument("--prologue-evidence", type=Path)
    verify_p = sub.add_parser("verify")
    verify_p.add_argument("--attempt-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.mode == "run":
            rc, path = run(
                repo_root=args.repo_root,
                toolchain_manifest_path=args.toolchain_manifest,
                ccbench_dir=args.ccbench_dir,
                cache_root=args.cache_root,
                artifact_repo_root=args.artifact_repo_root,
                git_repo_root=args.git_repo_root,
                prologue_evidence_path=args.prologue_evidence,
            )
            print(path)
            return rc
        result = verify(args.attempt_dir)
        json.dump(dataclasses.asdict(result), sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
        return 0 if result.integrity_status == "valid" else 2
    except (ProtocolError, QualificationArtifactError, QualificationDriverError) as exc:
        print(f"t126 qualification: {type(exc).__name__}: {exc}", file=sys.stderr)
        return getattr(exc, "rc", RC_INFRASTRUCTURE)


if __name__ == "__main__":
    raise SystemExit(main())
