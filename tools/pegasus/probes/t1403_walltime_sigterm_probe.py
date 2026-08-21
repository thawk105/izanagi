#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-
"""NQSV walltime warning-signal probe for T-1403.

The scheduler's output is external evidence.  This module only extracts the
small set of fields needed by the probe and never treats text from NQSV as an
instruction.  The verdict core is deliberately independent of subprocess and
signal execution so that it can be tested with synthetic observations.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import os
from pathlib import Path
import re
import signal
import sys
import time
from typing import Any, Mapping, NamedTuple, Optional, Sequence


SCHEMA_VERSION = "t1403-walltime-sigterm-probe/v1"
DEFAULT_MAX_WALLTIME = "00:03:00"
DEFAULT_WARN_WALLTIME = "00:02:00"
DEFAULT_MAX_SECONDS = 180.0
DEFAULT_WARN_SECONDS = 120.0

# These values are fixed before the mitigation leg is submitted.  In
# particular, absence of a TERM checkpoint is not itself evidence of SIGKILL;
# the NO_SIGNAL value describes the observation and requires an independently
# confirmed death (for example, scheduler accounting) in the input.
SIGTERM_CAUGHT_CLEAN_EXIT = "SIGTERM_CAUGHT_CLEAN_EXIT"
SIGTERM_CAUGHT_THEN_KILLED = "SIGTERM_CAUGHT_THEN_KILLED"
NO_SIGNAL_OBSERVED_SIGKILLED = "NO_SIGNAL_OBSERVED_SIGKILLED"
UNKNOWN = "UNKNOWN"
CLASSIFICATIONS = frozenset(
    {
        SIGTERM_CAUGHT_CLEAN_EXIT,
        SIGTERM_CAUGHT_THEN_KILLED,
        NO_SIGNAL_OBSERVED_SIGKILLED,
        UNKNOWN,
    }
)

_PBS_JOBID_RE = re.compile(r"^(?:[0-9]+:)?[A-Za-z0-9._-]+$")
_WALLTIME_RE = re.compile(r"^(?P<hours>[0-9]{2}):(?P<minutes>[0-9]{2}):(?P<seconds>[0-9]{2})$")
_NQSV_SIGNAL_RE = re.compile(
    r"^\s*%NQSV\(INFO\):\s*Batch job received signal\s+"
    r"(?P<signal>[A-Za-z][A-Za-z0-9_]*)\.\s*(?:.*)?$"
)
_NQSV_ACCOUNTING_RE = re.compile(
    r"^\s*(?P<field>Elapse|Remaining Elapse):\s*"
    r"(?P<value>[0-9]+(?:\.[0-9]+)?)\s*(?P<unit>[SMHD])\s*$",
    re.IGNORECASE,
)


class VerdictResult(NamedTuple):
    """The fixed classification and the observed post-TERM interval."""

    classification: str
    grace_seconds: Optional[float]

    @property
    def verdict(self) -> str:
        """Convenient name for callers that refer to the classification as verdict."""

        return self.classification

    def as_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification,
            "grace_seconds": self.grace_seconds,
        }


@dataclasses.dataclass(frozen=True)
class VerdictObservation:
    """Synthetic or observed timestamps used by :func:`compute_verdict`.

    Boundaries are absolute epoch timestamps.  ``death_confirmed_at`` is an
    externally confirmed process death; it does not assert which signal caused
    it.  A clean exit is represented separately because a normal exit is not a
    death observation.
    """

    job_started_at: float
    warn_boundary: float
    max_boundary: float
    sigterm_received_at: Optional[float] = None
    clean_exit_at: Optional[float] = None
    death_confirmed_at: Optional[float] = None
    cleanup_started_at: Optional[float] = None

    @property
    def job_start_epoch(self) -> float:
        return self.job_started_at

    @property
    def warn_at(self) -> float:
        return self.warn_boundary

    @property
    def max_at(self) -> float:
        return self.max_boundary


# A descriptive alias keeps the observation type easy to find for callers
# that use the shorter term from the wave brief.
WalltimeObservation = VerdictObservation


def _finite(value: float) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _valid_observation(observation: VerdictObservation) -> bool:
    if not all(
        _finite(value)
        for value in (
            observation.job_started_at,
            observation.warn_boundary,
            observation.max_boundary,
        )
    ):
        return False
    if not (
        observation.job_started_at < observation.warn_boundary <= observation.max_boundary
    ):
        return False
    for value in (
        observation.sigterm_received_at,
        observation.clean_exit_at,
        observation.death_confirmed_at,
        observation.cleanup_started_at,
    ):
        if value is not None and not _finite(value):
            return False
    return True


def compute_verdict(observation: VerdictObservation) -> VerdictResult:
    """Classify a walltime observation without consulting a process or scheduler.

    A TERM is considered useful only when it was received before the max
    boundary.  A clean exit must be confirmed before that boundary.  A death
    without a TERM checkpoint is reported with the fixed no-signal value, but
    the function does not infer a signal name from timing; the receipt keeps
    NQSV's explicit signal extraction separately.
    """

    if not isinstance(observation, VerdictObservation) or not _valid_observation(observation):
        return VerdictResult(UNKNOWN, None)

    term_at = observation.sigterm_received_at
    clean_at = observation.clean_exit_at
    death_at = observation.death_confirmed_at

    if term_at is not None and not (
        observation.job_started_at <= term_at < observation.max_boundary
    ):
        return VerdictResult(UNKNOWN, None)

    if term_at is not None:
        if clean_at is not None and death_at is None:
            if term_at <= clean_at < observation.max_boundary:
                return VerdictResult(
                    SIGTERM_CAUGHT_CLEAN_EXIT,
                    float(clean_at - term_at),
                )
            return VerdictResult(UNKNOWN, None)
        if death_at is not None and clean_at is None:
            if death_at >= observation.max_boundary and death_at >= term_at:
                return VerdictResult(
                    SIGTERM_CAUGHT_THEN_KILLED,
                    float(death_at - term_at),
                )
            return VerdictResult(UNKNOWN, None)
        return VerdictResult(UNKNOWN, None)

    if death_at is not None and death_at >= observation.max_boundary:
        # The name records "no TERM observed + independently confirmed death";
        # it is not a claim that timing alone identified SIGKILL.
        return VerdictResult(NO_SIGNAL_OBSERVED_SIGKILLED, None)

    return VerdictResult(UNKNOWN, None)


def calculate_verdict(observation: VerdictObservation) -> VerdictResult:
    """Compatibility spelling for the pure verdict function."""

    return compute_verdict(observation)


def walltime_seconds(value: str) -> float:
    """Convert an ``HH:MM:SS`` PBS walltime into seconds."""

    match = _WALLTIME_RE.fullmatch(value)
    if match is None:
        raise ValueError(f"invalid PBS walltime: {value!r}")
    hours = int(match.group("hours"))
    minutes = int(match.group("minutes"))
    seconds = int(match.group("seconds"))
    if minutes >= 60 or seconds >= 60:
        raise ValueError(f"invalid PBS walltime: {value!r}")
    return float(hours * 3600 + minutes * 60 + seconds)


def render_pbs_directives(
    max_walltime: str = DEFAULT_MAX_WALLTIME,
    warn_walltime: str = DEFAULT_WARN_WALLTIME,
) -> tuple[str, ...]:
    """Render the exact mitigation directives used by the PBS wrapper."""

    if walltime_seconds(warn_walltime) >= walltime_seconds(max_walltime):
        raise ValueError("warn walltime must be shorter than max walltime")
    return (
        "#PBS -A SFC",
        "#PBS -q gen_S",
        "#PBS -b 1",
        f'#PBS -l elapstim_req="{max_walltime},{warn_walltime}"',
        "#PBS --warning-signal=elapstim:SIGTERM",
        "#PBS --accept-sigterm=yes",
    )


def render_pbs_directive_text(
    max_walltime: str = DEFAULT_MAX_WALLTIME,
    warn_walltime: str = DEFAULT_WARN_WALLTIME,
) -> str:
    return "\n".join(render_pbs_directives(max_walltime, warn_walltime))


def _resolved_absolute(path: os.PathLike[str] | str, *, label: str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        raise ValueError(f"{label} must be an absolute path")
    try:
        return candidate.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"cannot resolve {label}: {candidate}") from exc


def ensure_off_repo_path(
    path: os.PathLike[str] | str,
    repository_root: os.PathLike[str] | str,
    *,
    git_common_root: os.PathLike[str] | str | None = None,
) -> Path:
    """Return an absolute path only when it is outside the repository roots.

    This is the Python counterpart of the floor campaign's evidence-root
    rejection.  It resolves existing symlinks before checking containment, so
    a path that appears external but resolves into a repository is rejected.
    """

    resolved_path = _resolved_absolute(path, label="evidence path")
    roots = [_resolved_absolute(repository_root, label="repository root")]
    if git_common_root is not None:
        roots.append(_resolved_absolute(git_common_root, label="Git common root"))
    for root in roots:
        if resolved_path == root or root in resolved_path.parents:
            raise ValueError(f"diagnostic path resolves inside repository: {resolved_path}")
    return resolved_path


def build_evidence_path(
    evidence_root: os.PathLike[str] | str,
    repository_root: os.PathLike[str] | str,
    job_id: str,
    filename: str,
    *,
    git_common_root: os.PathLike[str] | str | None = None,
) -> Path:
    """Build and guard one job artifact path below an external evidence root."""

    if _PBS_JOBID_RE.fullmatch(job_id) is None:
        raise ValueError(f"unsafe PBS_JOBID: {job_id!r}")
    if not filename or Path(filename).name != filename or filename in {".", ".."}:
        raise ValueError("evidence filename must be one direct path component")
    root = ensure_off_repo_path(
        evidence_root,
        repository_root,
        git_common_root=git_common_root,
    )
    return ensure_off_repo_path(
        root / "pegasus" / job_id / "t1403-walltime-sigterm" / filename,
        repository_root,
        git_common_root=git_common_root,
    )


def append_checkpoint_line(path: os.PathLike[str] | str, record: Mapping[str, Any]) -> None:
    """Append exactly one JSONL checkpoint record.

    The handler calls this before doing any post-TERM work.  A completed
    ``write`` is enough for process-kill durability; no cleanup is placed ahead
    of the checkpoint.
    """

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    payload = (json.dumps(dict(record), sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(destination, flags, 0o600)
    try:
        offset = 0
        while offset < len(payload):
            offset += os.write(descriptor, payload[offset:])
    finally:
        os.close(descriptor)


def read_checkpoint_record(path: os.PathLike[str] | str) -> dict[str, Any] | None:
    """Read the single post-TERM checkpoint, or ``None`` when it is absent."""

    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    lines = text.splitlines()
    if not lines:
        return None
    if len(lines) != 1:
        raise ValueError("checkpoint JSONL must contain at most one line")
    try:
        record = json.loads(lines[0])
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("checkpoint JSONL contains invalid JSON") from exc
    if not isinstance(record, dict):
        raise ValueError("checkpoint JSONL record must be an object")
    return record


def parse_nqsv_output(text: str) -> dict[str, Any]:
    """Extract explicit signal and accounting fields from NQSV text.

    Only anchored, known output shapes are parsed.  The remainder of each
    signal line is intentionally ignored rather than interpreted.
    """

    if not isinstance(text, str):
        raise TypeError("NQSV output must be text")

    signals: list[str] = []
    elapsed_seconds: float | None = None
    remaining_elapsed_seconds: float | None = None
    for line in text.splitlines():
        signal_match = _NQSV_SIGNAL_RE.match(line)
        if signal_match is not None:
            signals.append(signal_match.group("signal"))
            continue
        accounting_match = _NQSV_ACCOUNTING_RE.match(line)
        if accounting_match is None:
            continue
        value = float(accounting_match.group("value"))
        unit = accounting_match.group("unit").upper()
        multiplier = {"S": 1.0, "M": 60.0, "H": 3600.0, "D": 86400.0}[unit]
        seconds = value * multiplier
        if accounting_match.group("field").lower() == "elapse":
            elapsed_seconds = seconds
        else:
            remaining_elapsed_seconds = seconds
    return {
        "signals": signals,
        "elapsed_seconds": elapsed_seconds,
        "remaining_elapsed_seconds": remaining_elapsed_seconds,
    }


def analyze_nqsv_output(text: str) -> dict[str, Any]:
    """Alias emphasizing that this is postmortem structured extraction."""

    return parse_nqsv_output(text)


def reconcile_observation(
    *,
    checkpoint_record: Mapping[str, Any] | None,
    nqsv_analysis: Mapping[str, Any],
    warn_seconds: float,
    max_seconds: float,
    final_stdout_observed: bool,
) -> VerdictObservation:
    """Reconstruct a verdict observation from postmortem evidence.

    A checkpoint preserves the epoch-time axis used by ``run_workload``.  If
    no checkpoint exists, the observation uses a zero-based relative axis
    because the job start epoch is not known.  Missing or contradictory
    evidence remains an observation that ``compute_verdict`` classifies as
    ``UNKNOWN`` rather than inventing a signal event.
    """

    if not isinstance(nqsv_analysis, Mapping):
        raise TypeError("nqsv_analysis must be a mapping")
    if type(final_stdout_observed) is not bool:
        raise TypeError("final_stdout_observed must be a bool")
    if not (
        _finite(warn_seconds)
        and _finite(max_seconds)
        and 0 < warn_seconds < max_seconds
    ):
        raise ValueError("warn_seconds must be positive and shorter than max_seconds")

    elapsed_value = nqsv_analysis.get("elapsed_seconds")
    elapsed_seconds: float | None = None
    if elapsed_value is not None:
        if not _finite(elapsed_value) or float(elapsed_value) < 0:
            raise ValueError("nqsv elapsed_seconds must be a non-negative finite number")
        elapsed_seconds = float(elapsed_value)

    if checkpoint_record is None:
        # No checkpoint means no SIGTERM was observed by the job process.
        if final_stdout_observed:
            return VerdictObservation(
                job_started_at=0.0,
                warn_boundary=float(warn_seconds),
                max_boundary=float(max_seconds),
            )
        return VerdictObservation(
            job_started_at=0.0,
            warn_boundary=float(warn_seconds),
            max_boundary=float(max_seconds),
            death_confirmed_at=elapsed_seconds,
        )

    if not isinstance(checkpoint_record, Mapping):
        raise TypeError("checkpoint_record must be a mapping or None")

    try:
        job_started_epoch = checkpoint_record["job_started_epoch"]
        received_epoch = checkpoint_record["received_epoch"]
    except KeyError as exc:
        raise ValueError(f"checkpoint record is missing {exc.args[0]!r}") from exc
    if not _finite(job_started_epoch) or not _finite(received_epoch):
        raise ValueError("checkpoint timestamps must be finite numbers")
    job_started_at = float(job_started_epoch)
    sigterm_received_at = float(received_epoch)
    if sigterm_received_at < job_started_at:
        raise ValueError("checkpoint SIGTERM timestamp precedes job start")

    common = {
        "job_started_at": job_started_at,
        "warn_boundary": job_started_at + float(warn_seconds),
        "max_boundary": job_started_at + float(max_seconds),
        "sigterm_received_at": sigterm_received_at,
    }
    if final_stdout_observed:
        # NQSV elapsed time is the clean-exit proxy; without it, receive time is conservative.
        common["clean_exit_at"] = (
            job_started_at + elapsed_seconds
            if elapsed_seconds is not None
            else sigterm_received_at
        )
        return VerdictObservation(**common)
    if elapsed_seconds is not None:
        common["death_confirmed_at"] = job_started_at + elapsed_seconds
    return VerdictObservation(**common)


def compose_receipt(
    verdict: VerdictResult,
    nqsv_analysis: Mapping[str, Any],
    *,
    observation: VerdictObservation | None = None,
    job_id: str | None = None,
) -> dict[str, Any]:
    """Compose the JSON-compatible final receipt from the two pure results."""

    if verdict.classification not in CLASSIFICATIONS:
        raise ValueError(f"unknown classification: {verdict.classification!r}")
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "verdict": verdict.as_dict(),
        "nqsv": dict(nqsv_analysis),
    }
    if job_id is not None:
        if _PBS_JOBID_RE.fullmatch(job_id) is None:
            raise ValueError(f"unsafe PBS_JOBID: {job_id!r}")
        receipt["PBS_JOBID"] = job_id
    if observation is not None:
        receipt["observation"] = dataclasses.asdict(observation)
    return receipt


def write_final_receipt(
    path: os.PathLike[str] | str,
    verdict: VerdictResult,
    nqsv_analysis: Mapping[str, Any],
    *,
    repository_root: os.PathLike[str] | str,
    observation: VerdictObservation | None = None,
    job_id: str | None = None,
) -> Path:
    """Write a guarded final receipt outside the repository."""

    destination = ensure_off_repo_path(path, repository_root)
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    destination = ensure_off_repo_path(destination, repository_root)
    payload = (
        json.dumps(
            compose_receipt(
                verdict,
                nqsv_analysis,
                observation=observation,
                job_id=job_id,
            ),
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )
    temporary = destination.with_name(f".{destination.name}.tmp.{os.getpid()}")
    try:
        with temporary.open("x", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise
    return destination


def write_receipt(
    path: os.PathLike[str] | str,
    verdict: VerdictResult,
    nqsv_analysis: Mapping[str, Any],
    *,
    repository_root: os.PathLike[str] | str,
    observation: VerdictObservation | None = None,
    job_id: str | None = None,
) -> Path:
    """Short alias for :func:`write_final_receipt`."""

    return write_final_receipt(
        path,
        verdict,
        nqsv_analysis,
        repository_root=repository_root,
        observation=observation,
        job_id=job_id,
    )


class _SigtermCaught(Exception):
    pass


def run_workload(
    repo_root: os.PathLike[str] | str,
    evidence_root: os.PathLike[str] | str,
    *,
    job_id: str,
    warn_seconds: float = DEFAULT_WARN_SECONDS,
    max_seconds: float = DEFAULT_MAX_SECONDS,
) -> tuple[VerdictObservation, Path]:
    """Run the over-walltime workload and return the local observation.

    The scheduler is expected to terminate the process at the requested max
    boundary when no warning signal is delivered.  When TERM is delivered, the
    handler writes the checkpoint before raising the clean-exit exception.
    """

    if not _PBS_JOBID_RE.fullmatch(job_id):
        raise ValueError(f"unsafe PBS_JOBID: {job_id!r}")
    if not (
        _finite(warn_seconds)
        and _finite(max_seconds)
        and 0 < warn_seconds < max_seconds
    ):
        raise ValueError("warn_seconds must be positive and shorter than max_seconds")
    repository = _resolved_absolute(repo_root, label="repository root")
    checkpoint = build_evidence_path(
        evidence_root,
        repository,
        job_id,
        "checkpoint.jsonl",
    )
    checkpoint.parent.mkdir(parents=True, exist_ok=True, mode=0o700)

    started_epoch = time.time()
    started_monotonic = time.monotonic()
    signal_state: dict[str, float] = {}

    def handle_sigterm(_signum: int, _frame: Any) -> None:
        if "received_epoch" in signal_state:
            return
        received_epoch = time.time()
        received_elapsed = time.monotonic() - started_monotonic
        # This is intentionally the first operation in the handler.
        append_checkpoint_line(
            checkpoint,
            {
                "event": "SIGTERM_RECEIVED",
                "signal": "SIGTERM",
                "PBS_JOBID": job_id,
                "job_started_epoch": started_epoch,
                "received_epoch": received_epoch,
                "elapsed_seconds": received_elapsed,
            },
        )
        signal_state["received_epoch"] = received_epoch
        signal_state["received_elapsed"] = received_elapsed
        # The checkpoint is complete before this post-TERM exit path begins.
        signal_state["cleanup_started_epoch"] = time.time()
        raise _SigtermCaught()

    previous_handler = signal.signal(signal.SIGTERM, handle_sigterm)
    try:
        try:
            time.sleep(max_seconds * 2.0)
        except _SigtermCaught:
            clean_exit_at = time.time()
            return (
                VerdictObservation(
                    job_started_at=started_epoch,
                    warn_boundary=started_epoch + warn_seconds,
                    max_boundary=started_epoch + max_seconds,
                    sigterm_received_at=signal_state["received_epoch"],
                    clean_exit_at=clean_exit_at,
                    cleanup_started_at=signal_state["cleanup_started_epoch"],
                ),
                checkpoint,
            )
        return (
            VerdictObservation(
                job_started_at=started_epoch,
                warn_boundary=started_epoch + warn_seconds,
                max_boundary=started_epoch + max_seconds,
            ),
            checkpoint,
        )
    finally:
        signal.signal(signal.SIGTERM, previous_handler)


def _default_evidence_root(
    repository_root: os.PathLike[str] | str | None = None,
) -> Path:
    """Return the shared evidence root derived from the Git common directory."""

    if repository_root is None:
        repository = _resolved_absolute(
            Path(__file__).resolve().parents[3],
            label="repository root",
        )
    else:
        repository = _resolved_absolute(repository_root, label="repository root")

    git_entry = repository / ".git"
    common_dir = git_entry
    if git_entry.is_file() and not git_entry.is_symlink():
        try:
            gitdir_line = git_entry.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeError):
            gitdir_line = ""
        prefix = "gitdir: "
        if gitdir_line.startswith(prefix):
            admin = Path(gitdir_line[len(prefix) :])
            if not admin.is_absolute():
                admin = repository / admin
            if len(admin.parents) >= 2 and admin.parent.name == "worktrees":
                common_dir = admin.parent.parent
    return common_dir.parent.parent / "izanagi-job-evidence"


def _pbs_context() -> tuple[str, Path]:
    job_id = os.environ.get("PBS_JOBID", "")
    workdir = os.environ.get("PBS_O_WORKDIR", "")
    if _PBS_JOBID_RE.fullmatch(job_id) is None:
        raise ValueError("PBS_JOBID is missing or malformed")
    if not workdir or not Path(workdir).is_absolute() or not Path(workdir).is_dir():
        raise ValueError("PBS_O_WORKDIR must be an existing absolute directory")
    return job_id, _resolved_absolute(workdir, label="PBS_O_WORKDIR")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--evidence-root", type=Path, default=None)
    parser.add_argument("--warn-seconds", type=float, default=DEFAULT_WARN_SECONDS)
    parser.add_argument("--max-seconds", type=float, default=DEFAULT_MAX_SECONDS)
    args = parser.parse_args(argv)
    try:
        job_id, _workdir = _pbs_context()
        repository = _resolved_absolute(args.repo_root, label="repository root")
        evidence_root = args.evidence_root or _default_evidence_root(repository)
        observation, checkpoint = run_workload(
            repository,
            evidence_root,
            job_id=job_id,
            warn_seconds=args.warn_seconds,
            max_seconds=args.max_seconds,
        )
    except (OSError, ValueError) as exc:
        print(f"t1403 probe failed closed: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "checkpoint": str(checkpoint),
                "observation": dataclasses.asdict(observation),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
