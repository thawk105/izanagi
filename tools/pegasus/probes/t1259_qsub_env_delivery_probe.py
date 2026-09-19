#!/usr/bin/env python3
"""Observe the exact T-1259 qsub environment delivered to one PBS job."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "izanagi-t1259-qsub-env-delivery-result/v1"
SUBMISSION_MANIFEST_SCHEMA = "izanagi-t1259-qsub-submission-manifest/v1"
RESULT_PREFIX = "T1259_QSUB_ENV_DELIVERY_RESULT "
AUTHORITY = "diagnostic-only"
PROBE_RELATIVE_PATH = "tools/pegasus/probes/t1259_qsub_env_delivery_probe.py"
PBS_RELATIVE_PATH = "tools/pegasus/probes/t1259_qsub_env_delivery_probe.pbs"
CAMPAIGN_RELATIVE_PATH = "orchestrator/campaign/s8b_floor_campaign.py"
SUBMISSION_MANIFEST_NAME = "submission-manifest.json"
RESULT_NAME = "result.json"
DRIVER_TIMEOUT_SECONDS = 60.0
AMBIENT_APPROVAL_LITERAL = "t1259-ambient-approval-must-not-match"

SUBMISSION_NONCE = "IZANAGI_SUBMISSION_NONCE"
APPROVAL = "IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN"
EVIDENCE_ROOT = "IZANAGI_FLOOR_JOB_EVIDENCE_ROOT"
SECOND_HEX = "T1259_QSUB_SECOND_HEX"
AMBIENT_SENTINEL = "T1259_NQSV_AMBIENT_SENTINEL"
TARGET_ENV_NAMES = (
    SUBMISSION_NONCE,
    APPROVAL,
    EVIDENCE_ROOT,
    SECOND_HEX,
    AMBIENT_SENTINEL,
)
REQUEST_ENV_NAMES = {
    "R1": (SUBMISSION_NONCE, APPROVAL, EVIDENCE_ROOT),
    "R2": (SUBMISSION_NONCE, SECOND_HEX, EVIDENCE_ROOT),
    "R3": (SUBMISSION_NONCE, EVIDENCE_ROOT),
}
REQUEST_LABELS = {
    "R1": "with-explicit-approval",
    "R2": "without-approval-with-duplicate-second-name",
    "R3": "ambient-approval-name-only",
}
HEX32_RE = re.compile(r"[0-9a-f]{32}")
HEX40_RE = re.compile(r"[0-9a-f]{40}")
HEX64_RE = re.compile(r"[0-9a-f]{64}")
PBS_JOB_ID_RE = re.compile(r"([0-9]+:)?[A-Za-z0-9._-]+")
_MANIFEST_KEYS = {
    "schema_version",
    "authority",
    "request_id",
    "request_label",
    "repo_head",
    "probe_script_path",
    "probe_script_sha256",
    "pbs_script_path",
    "pbs_script_sha256",
    "campaign_script_path",
    "campaign_script_sha256",
    "ordered_explicit_env",
    "qsub_v_exact",
    "qsub_v_byte_length",
    "qsub_caller_environment",
    "qsub_caller_pid",
    "qsub_caller_observed_utc",
    "qsub_hostname",
}


class ProbeError(RuntimeError):
    """The observation cannot be bound to its submission evidence."""


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _byte_length(value: str) -> int:
    return len(value.encode("utf-8"))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _environment_state(environ: Mapping[str, str], name: str) -> dict[str, Any]:
    present = name in environ
    value = environ.get(name) if present else None
    return {
        "present": present,
        "value": value,
        "value_byte_length": _byte_length(value) if value is not None else None,
    }


def _strict_object(raw: bytes, *, source: Path) -> dict[str, Any]:
    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in rows:
            if key in result:
                raise ProbeError(f"duplicate JSON key in {source}: {key}")
            result[key] = value
        return result

    try:
        document = json.loads(
            raw.decode("utf-8", "strict"),
            object_pairs_hook=pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ProbeError(f"non-finite JSON token in {source}: {token}")
            ),
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ProbeError(f"cannot strictly parse JSON from {source}: {exc}") from exc
    if type(document) is not dict:
        raise ProbeError(f"JSON top level is not an object: {source}")
    return document


def _run_git(
    repo_root: Path, *args: str, git_timeout_seconds: float = 30.0
) -> str:
    environment = dict(os.environ)
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    completed = subprocess.run(
        ["git", "-C", os.fspath(repo_root), *args],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
        timeout=git_timeout_seconds,
    )
    return completed.stdout


def _repo_is_detached(
    repo_root: Path, *, git_timeout_seconds: float = 30.0
) -> bool:
    environment = dict(os.environ)
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    completed = subprocess.run(
        ["git", "-C", os.fspath(repo_root), "symbolic-ref", "-q", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
        timeout=git_timeout_seconds,
    )
    if completed.returncode not in (0, 1):
        raise ProbeError("cannot determine whether repository HEAD is detached")
    return completed.returncode == 1


def _repo_snapshot(
    repo_root: Path, *, git_timeout_seconds: float = 30.0
) -> dict[str, Any]:
    head = _run_git(
        repo_root, "rev-parse", "--verify", "HEAD",
        git_timeout_seconds=git_timeout_seconds,
    ).strip()
    if HEX40_RE.fullmatch(head) is None:
        raise ProbeError("repository HEAD is not an exact lowercase 40-hex commit")
    tracked = _run_git(
        repo_root,
        "status",
        "--porcelain=v1",
        "--untracked-files=no",
        "--ignore-submodules=none",
        git_timeout_seconds=git_timeout_seconds,
    )
    untracked_raw = _run_git(
        repo_root,
        "ls-files",
        "--others",
        "--exclude-standard",
        "-z",
        git_timeout_seconds=git_timeout_seconds,
    )
    return {
        "head": head,
        "detached": _repo_is_detached(
            repo_root, git_timeout_seconds=git_timeout_seconds
        ),
        "tracked_status": tracked,
        "untracked_paths": sorted(path for path in untracked_raw.split("\0") if path),
        "source_sha256": {
            relative: _sha256_file(repo_root / relative)
            for relative in (
                PROBE_RELATIVE_PATH,
                PBS_RELATIVE_PATH,
                CAMPAIGN_RELATIVE_PATH,
            )
        },
    }


def _canonical_directory(path: Path, *, label: str) -> Path:
    if not path.is_absolute():
        raise ProbeError(f"{label} must be absolute")
    canonical = path.resolve(strict=True)
    if canonical != path or path.is_symlink() or not canonical.is_dir():
        raise ProbeError(f"{label} must be an existing canonical non-symlink directory")
    return canonical


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _validate_state(value: object, *, field: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != {
        "present", "value", "value_byte_length"
    }:
        raise ProbeError(f"{field} has an invalid exact key set")
    present = value["present"]
    raw_value = value["value"]
    raw_length = value["value_byte_length"]
    if type(present) is not bool:
        raise ProbeError(f"{field}.present is not an exact bool")
    if present:
        if type(raw_value) is not str or raw_length != _byte_length(raw_value):
            raise ProbeError(f"{field} value/byte length is invalid")
    elif raw_value is not None or raw_length is not None:
        raise ProbeError(f"{field} absent state carries a value")
    return dict(value)


def _validate_submission_manifest(
    path: Path,
    *,
    evidence_dir: Path,
    repo_snapshot: Mapping[str, Any],
    executing_pbs_sha256: str,
) -> tuple[dict[str, Any], str]:
    if path.is_symlink() or not path.is_file():
        raise ProbeError("submission manifest is not a regular non-symlink file")
    raw = path.read_bytes()
    if len(raw) > 128 * 1024:
        raise ProbeError("submission manifest exceeds 128 KiB")
    document = _strict_object(raw, source=path)
    if set(document) != _MANIFEST_KEYS:
        raise ProbeError("submission manifest exact key set is invalid")
    if document["schema_version"] != SUBMISSION_MANIFEST_SCHEMA:
        raise ProbeError("submission manifest schema version is invalid")
    if document["authority"] != AUTHORITY:
        raise ProbeError("submission manifest authority is invalid")

    request_id = document["request_id"]
    if request_id not in REQUEST_ENV_NAMES:
        raise ProbeError("submission manifest request_id is invalid")
    if document["request_label"] != REQUEST_LABELS[request_id]:
        raise ProbeError("submission manifest request label is invalid")
    if HEX40_RE.fullmatch(document.get("repo_head", "")) is None:
        raise ProbeError("submission manifest repo_head is invalid")
    if document["repo_head"] != repo_snapshot["head"]:
        raise ProbeError("submission manifest repo_head does not match the job repository")
    if repo_snapshot["detached"] is not True:
        raise ProbeError("job repository HEAD is not detached")
    if repo_snapshot["tracked_status"] != "":
        raise ProbeError("job repository is not tracked-clean at observer start")
    if repo_snapshot["untracked_paths"] != []:
        raise ProbeError("job repository has untracked paths at observer start")

    source_fields = (
        ("probe_script", PROBE_RELATIVE_PATH),
        ("pbs_script", PBS_RELATIVE_PATH),
        ("campaign_script", CAMPAIGN_RELATIVE_PATH),
    )
    for field_prefix, expected_path in source_fields:
        if document[f"{field_prefix}_path"] != expected_path:
            raise ProbeError(f"submission manifest {field_prefix} path is invalid")
        expected_sha256 = document[f"{field_prefix}_sha256"]
        if HEX64_RE.fullmatch(expected_sha256) is None:
            raise ProbeError(f"submission manifest {field_prefix} sha256 is invalid")
        if expected_sha256 != repo_snapshot["source_sha256"][expected_path]:
            raise ProbeError(
                f"submission manifest {field_prefix} sha256 does not match job source"
            )
    if HEX64_RE.fullmatch(executing_pbs_sha256) is None:
        raise ProbeError("executing PBS sha256 is invalid")
    if executing_pbs_sha256 != document["pbs_script_sha256"]:
        raise ProbeError("executing PBS bytes do not match the submission manifest")

    rows = document["ordered_explicit_env"]
    expected_names = REQUEST_ENV_NAMES[request_id]
    if type(rows) is not list or len(rows) != len(expected_names):
        raise ProbeError("submission manifest ordered env row count is invalid")
    ordered: list[tuple[str, str]] = []
    for index, (row, expected_name) in enumerate(zip(rows, expected_names)):
        if type(row) is not dict or set(row) != {
            "name", "value", "value_byte_length"
        }:
            raise ProbeError(f"submission manifest env row {index} is invalid")
        name = row["name"]
        value = row["value"]
        if name != expected_name or type(value) is not str or not value:
            raise ProbeError(f"submission manifest env row {index} identity is invalid")
        if row["value_byte_length"] != _byte_length(value):
            raise ProbeError(f"submission manifest env row {index} byte length is invalid")
        if "," in value or "\n" in value or "\r" in value:
            raise ProbeError(f"submission manifest env row {index} is not qsub -v safe")
        ordered.append((name, value))
    export_spec = ",".join(f"{name}={value}" for name, value in ordered)
    if document["qsub_v_exact"] != export_spec:
        raise ProbeError("submission manifest qsub_v_exact is not reconstructed from rows")
    if document["qsub_v_byte_length"] != _byte_length(export_spec):
        raise ProbeError("submission manifest qsub_v byte length is invalid")

    ordered_values = dict(ordered)
    if HEX32_RE.fullmatch(ordered_values[SUBMISSION_NONCE]) is None:
        raise ProbeError("submission nonce is not exact lowercase 32-hex")
    if ordered_values[EVIDENCE_ROOT] != os.fspath(evidence_dir):
        raise ProbeError("submission evidence root does not match manifest directory")
    if request_id == "R1":
        if ordered_values[APPROVAL] != ordered_values[SUBMISSION_NONCE]:
            raise ProbeError("R1 approval is not exactly bound to its nonce")
    elif request_id == "R2":
        if HEX32_RE.fullmatch(ordered_values[SECOND_HEX]) is None:
            raise ProbeError("R2 explicit second value is not exact lowercase 32-hex")

    caller_environment = document["qsub_caller_environment"]
    if type(caller_environment) is not dict or set(caller_environment) != set(
        TARGET_ENV_NAMES
    ):
        raise ProbeError("submission manifest caller environment key set is invalid")
    caller_states = {
        name: _validate_state(caller_environment[name], field=f"caller.{name}")
        for name in TARGET_ENV_NAMES
    }
    sentinel = caller_states[AMBIENT_SENTINEL]
    if not sentinel["present"] or HEX32_RE.fullmatch(sentinel["value"]) is None:
        raise ProbeError("qsub caller did not carry the attempt-random ambient sentinel")
    for name in (SUBMISSION_NONCE, EVIDENCE_ROOT):
        if caller_states[name]["present"]:
            raise ProbeError(f"qsub caller unexpectedly carried ambient {name}")
    if request_id == "R1":
        for name in (APPROVAL, SECOND_HEX):
            if caller_states[name]["present"]:
                raise ProbeError(f"R1 qsub caller unexpectedly carried ambient {name}")
    elif request_id == "R2":
        if caller_states[APPROVAL]["present"]:
            raise ProbeError("R2 qsub caller unexpectedly carried ambient approval")
        ambient_second = caller_states[SECOND_HEX]
        if (not ambient_second["present"]
                or HEX32_RE.fullmatch(ambient_second["value"]) is None
                or ambient_second["value"] == ordered_values[SECOND_HEX]):
            raise ProbeError("R2 ambient duplicate value is absent, invalid, or not distinct")
    else:
        if caller_states[SECOND_HEX]["present"]:
            raise ProbeError("R3 qsub caller unexpectedly carried ambient second value")
        ambient_approval = caller_states[APPROVAL]
        if (not ambient_approval["present"]
                or ambient_approval["value"] != AMBIENT_APPROVAL_LITERAL):
            raise ProbeError("R3 qsub caller did not carry the fixed mismatching approval literal")

    caller_pid = document["qsub_caller_pid"]
    if type(caller_pid) is not int or caller_pid <= 0:
        raise ProbeError("submission manifest qsub caller pid is invalid")
    observed_utc = document["qsub_caller_observed_utc"]
    if type(observed_utc) is not str:
        raise ProbeError("submission manifest caller UTC is invalid")
    try:
        parsed_utc = dt.datetime.fromisoformat(observed_utc.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProbeError("submission manifest caller UTC is invalid") from exc
    if parsed_utc.tzinfo is None or parsed_utc.utcoffset() != dt.timedelta(0):
        raise ProbeError("submission manifest caller time is not UTC")
    if type(document["qsub_hostname"]) is not str or not document["qsub_hostname"]:
        raise ProbeError("submission manifest qsub hostname is invalid")
    return document, hashlib.sha256(raw).hexdigest()


def _explicit_comparisons(
    manifest: Mapping[str, Any], environ: Mapping[str, str]
) -> list[dict[str, Any]]:
    comparisons = []
    for row in manifest["ordered_explicit_env"]:
        name = row["name"]
        expected = row["value"]
        present = name in environ
        observed = environ.get(name) if present else None
        comparisons.append({
            "name": name,
            "expected_value": expected,
            "expected_value_byte_length": row["value_byte_length"],
            "observed_present": present,
            "observed_value": observed,
            "observed_value_byte_length": (
                _byte_length(observed) if observed is not None else None
            ),
            "exact_match": present and observed == expected,
        })
    return comparisons


def _source_projection(
    request_id: str, environ: Mapping[str, str]
) -> dict[str, Any]:
    """Project only the three actually submitted conditions onto current source."""
    nonce = environ.get(SUBMISSION_NONCE)
    approval_present = APPROVAL in environ
    approval = environ.get(APPROVAL) if approval_present else None
    base = {
        "kind": "source-projection-from-measured-environment",
        "floor_campaign_shell_section8_executed": False,
        "driver_argv_executed_by_floor_campaign_shell": False,
        "approval_present": approval_present,
        "approval_value": approval,
        "submission_nonce_value": nonce,
    }
    approval_bound = approval_present and nonce is not None and approval == nonce
    if approval_bound:
        base.update({
            "projected_outcome": "approval-bound",
            "official_approval_bound": True,
            "confirm_flag_would_be_appended": True,
        })
    elif not approval_present and request_id == "R3":
        base.update({
            "projected_outcome": "ambient-approval-not-delivered-unbound",
            "official_approval_bound": False,
            "confirm_flag_would_be_appended": False,
        })
    elif not approval_present:
        base.update({
            "projected_outcome": "approval-unset-unbound",
            "official_approval_bound": False,
            "confirm_flag_would_be_appended": False,
        })
    elif request_id == "R3":
        base.update({
            "projected_outcome": "ambient-approval-delivered-submit-binding-rejects-mismatch",
            "official_approval_bound": False,
            "confirm_flag_would_be_appended": False,
        })
    else:
        base.update({
            "projected_outcome": "approval-present-submit-binding-rejects-mismatch",
            "official_approval_bound": False,
            "confirm_flag_would_be_appended": False,
        })
    categorical_bound = base["projected_outcome"] == "approval-bound"
    if (categorical_bound is not base["official_approval_bound"]
            or base["confirm_flag_would_be_appended"]
            is not base["official_approval_bound"]):
        raise ProbeError("source projection categorical and boolean values disagree")
    return base


def _scratch_entries(path: Path) -> list[str]:
    return sorted(entry.name for entry in path.iterdir())


def _validated_unapproved_driver_environment(
    argv: Sequence[str], expected_argv: tuple[str, ...]
) -> dict[str, str]:
    """Reject any R2 argv outside the exact unapproved driver contract."""
    if tuple(argv) != expected_argv:
        raise ProbeError("R2 unapproved driver argv differs from the fixed contract")
    if "--confirm-official-floor-run" in argv:
        raise ProbeError("R2 unapproved driver argv unexpectedly carries approval")
    environment = dict(os.environ)
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def _unapproved_driver_observation(
    *,
    repo_root: Path,
    scratch_dir: Path,
    python_executable: str,
    expected_campaign_sha256: str,
) -> dict[str, Any]:
    protocol = scratch_dir / "protocol-loader-must-not-run.json"
    if os.path.lexists(protocol):
        raise ProbeError("R2 nonexistent protocol control already exists")
    before_entries = _scratch_entries(scratch_dir)
    campaign_path = repo_root / CAMPAIGN_RELATIVE_PATH
    campaign_sha256_before = _sha256_file(campaign_path)
    if campaign_sha256_before != expected_campaign_sha256:
        raise ProbeError("R2 campaign source bytes differ before driver execution")
    argv = [
        python_executable,
        "-I",
        "-B",
        os.fspath(campaign_path),
        "--mode",
        "official",
        "--protocol",
        os.fspath(protocol),
    ]
    expected_argv = (
        python_executable,
        "-I",
        "-B",
        os.fspath(campaign_path),
        "--mode",
        "official",
        "--protocol",
        os.fspath(protocol),
    )
    environment = _validated_unapproved_driver_environment(argv, expected_argv)
    try:
        completed = subprocess.run(
            argv,
            cwd=scratch_dir,
            env=environment,
            capture_output=True,
            text=True,
            timeout=DRIVER_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "executed": True,
            "argv": argv,
            "argv_exact_match": tuple(argv) == expected_argv,
            "campaign_source_sha256_expected": expected_campaign_sha256,
            "campaign_source_sha256_before": campaign_sha256_before,
            "campaign_source_sha256_after": _sha256_file(campaign_path),
            "approval_flag_absent": True,
            "timeout_seconds": DRIVER_TIMEOUT_SECONDS,
            "timed_out": True,
            "returncode": None,
            "stdout": exc.stdout,
            "stderr": exc.stderr,
            "protocol_existed_before": False,
            "protocol_exists_after": os.path.lexists(protocol),
            "scratch_entries_before": before_entries,
            "scratch_entries_after": _scratch_entries(scratch_dir),
            "accepted_as_expected_refusal": False,
        }
    except OSError as exc:
        return {
            "executed": True,
            "argv": argv,
            "argv_exact_match": tuple(argv) == expected_argv,
            "campaign_source_sha256_expected": expected_campaign_sha256,
            "campaign_source_sha256_before": campaign_sha256_before,
            "campaign_source_sha256_after": _sha256_file(campaign_path),
            "approval_flag_absent": True,
            "timeout_seconds": DRIVER_TIMEOUT_SECONDS,
            "timed_out": False,
            "returncode": None,
            "launch_error": f"{type(exc).__name__}: {exc}",
            "protocol_existed_before": False,
            "protocol_exists_after": os.path.lexists(protocol),
            "scratch_entries_before": before_entries,
            "scratch_entries_after": _scratch_entries(scratch_dir),
            "accepted_as_expected_refusal": False,
        }
    after_entries = _scratch_entries(scratch_dir)
    campaign_sha256_after = _sha256_file(campaign_path)
    lines = completed.stdout.splitlines()
    parsed: object = None
    parse_error: str | None = None
    if len(lines) == 1:
        try:
            parsed = _strict_object(lines[0].encode("utf-8"), source=Path("<driver-stdout>"))
        except ProbeError as exc:
            parse_error = str(exc)
    else:
        parse_error = f"expected exactly one stdout line, got {len(lines)}"
    expected_payload = (
        type(parsed) is dict
        and set(parsed) == {"status", "reason"}
        and parsed.get("status") == "refused"
        and type(parsed.get("reason")) is str
        and "--confirm-official-floor-run" in parsed["reason"]
    )
    accepted = (
        tuple(argv) == expected_argv
        and campaign_sha256_before == expected_campaign_sha256
        and campaign_sha256_after == expected_campaign_sha256
        and completed.returncode == 2
        and completed.stderr == ""
        and parse_error is None
        and expected_payload
        and not os.path.lexists(protocol)
        and after_entries == before_entries
    )
    return {
        "executed": True,
        "argv": argv,
        "argv_exact_match": tuple(argv) == expected_argv,
        "campaign_source_sha256_expected": expected_campaign_sha256,
        "campaign_source_sha256_before": campaign_sha256_before,
        "campaign_source_sha256_after": campaign_sha256_after,
        "approval_flag_absent": "--confirm-official-floor-run" not in argv,
        "timeout_seconds": DRIVER_TIMEOUT_SECONDS,
        "timed_out": False,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "parsed_stdout": parsed,
        "stdout_parse_error": parse_error,
        "protocol_existed_before": False,
        "protocol_exists_after": os.path.lexists(protocol),
        "scratch_entries_before": before_entries,
        "scratch_entries_after": after_entries,
        "accepted_as_expected_refusal": accepted,
    }


def _write_atomic_create_only(path: Path, payload: Mapping[str, Any]) -> None:
    if not path.is_absolute() or not path.parent.is_dir():
        raise ProbeError("result path must have an existing absolute parent")
    encoded = (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
        directory_fd = os.open(
            path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        )
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def observe(
    *,
    repo_root: Path,
    scratch_dir: Path,
    pbs_job_id: str,
    executing_pbs_sha256: str,
    environ: Mapping[str, str] | None = None,
    python_executable: str | None = None,
) -> tuple[dict[str, Any], Path | None]:
    environment = dict(os.environ if environ is None else environ)
    repository = _canonical_directory(Path(repo_root), label="repository root")
    scratch = _canonical_directory(Path(scratch_dir), label="scratch directory")
    if _is_within(scratch, repository):
        raise ProbeError("scratch directory must be outside the repository")
    if PBS_JOB_ID_RE.fullmatch(pbs_job_id) is None:
        raise ProbeError("PBS job ID has an unsafe shape")
    probe_path = repository / PROBE_RELATIVE_PATH
    pbs_path = repository / PBS_RELATIVE_PATH
    campaign_path = repository / CAMPAIGN_RELATIVE_PATH
    for required in (probe_path, pbs_path, campaign_path):
        if required.is_symlink() or not required.is_file():
            raise ProbeError(f"required source is unavailable: {required}")

    errors: list[str] = []
    before = _repo_snapshot(repository)
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "authority": AUTHORITY,
        "official_campaign_executed": False,
        "ok": False,
        "request_id": None,
        "hostname": socket.gethostname(),
        "pbs_job_id": pbs_job_id,
        "observed_utc": _utc_now(),
        "probe_script": {
            "path": PROBE_RELATIVE_PATH,
            "sha256": _sha256_file(probe_path),
        },
        "pbs_script": {
            "path": PBS_RELATIVE_PATH,
            "repo_file_sha256": _sha256_file(pbs_path),
            "executing_sha256": executing_pbs_sha256,
        },
        "ordering_semantics": (
            "ordered_explicit_env is the order written into the submission qsub -v argv; "
            "arrival order cannot be reconstructed from os.environ"
        ),
        "repo_write_invariant": (
            "the probe must not create or change files in the repository working tree; "
            "scheduler-owned spool is outside this closure"
        ),
        "environment_observation": {
            name: _environment_state(environment, name) for name in TARGET_ENV_NAMES
        },
        "repo_state_before": before,
    }
    evidence_dir: Path | None = None
    manifest: dict[str, Any] | None = None
    manifest_sha256: str | None = None
    evidence_raw = environment.get(EVIDENCE_ROOT)
    try:
        if evidence_raw is None:
            raise ProbeError(f"{EVIDENCE_ROOT} was not delivered")
        evidence_dir = _canonical_directory(Path(evidence_raw), label="evidence directory")
        if _is_within(evidence_dir, repository):
            raise ProbeError("evidence directory must be outside the repository")
        manifest_path = evidence_dir / SUBMISSION_MANIFEST_NAME
        manifest, manifest_sha256 = _validate_submission_manifest(
            manifest_path,
            evidence_dir=evidence_dir,
            repo_snapshot=before,
            executing_pbs_sha256=executing_pbs_sha256,
        )
    except (OSError, ProbeError, subprocess.SubprocessError) as exc:
        errors.append(f"submission-manifest: {type(exc).__name__}: {exc}")

    if manifest is not None:
        request_id = manifest["request_id"]
        result["request_id"] = request_id
        result["request_label"] = manifest["request_label"]
        result["submission_manifest"] = {
            "path": os.fspath(evidence_dir / SUBMISSION_MANIFEST_NAME),
            "sha256": manifest_sha256,
            "ordered_explicit_env": manifest["ordered_explicit_env"],
            "qsub_v_exact": manifest["qsub_v_exact"],
            "qsub_v_byte_length": manifest["qsub_v_byte_length"],
            "qsub_caller_environment": manifest["qsub_caller_environment"],
            "qsub_caller_pid": manifest["qsub_caller_pid"],
            "qsub_caller_observed_utc": manifest["qsub_caller_observed_utc"],
            "qsub_hostname": manifest["qsub_hostname"],
            "source_identity": {
                "repo_head": manifest["repo_head"],
                "probe_script_path": manifest["probe_script_path"],
                "probe_script_sha256": manifest["probe_script_sha256"],
                "pbs_script_path": manifest["pbs_script_path"],
                "pbs_script_sha256": manifest["pbs_script_sha256"],
                "executing_pbs_sha256": executing_pbs_sha256,
                "campaign_script_path": manifest["campaign_script_path"],
                "campaign_script_sha256": manifest["campaign_script_sha256"],
            },
        }
        comparisons = _explicit_comparisons(manifest, environment)
        result["explicit_env_comparisons"] = comparisons
        if not all(row["exact_match"] is True for row in comparisons):
            errors.append("one or more explicitly submitted environment values differ exactly")

        caller_sentinel = manifest["qsub_caller_environment"][AMBIENT_SENTINEL]
        observed_sentinel = result["environment_observation"][AMBIENT_SENTINEL]
        result["ambient_sentinel_delivery"] = {
            "submitted_process_present": caller_sentinel["present"],
            "submitted_process_value": caller_sentinel["value"],
            "job_present": observed_sentinel["present"],
            "job_value": observed_sentinel["value"],
            "job_value_matches_if_present": (
                not observed_sentinel["present"]
                or observed_sentinel["value"] == caller_sentinel["value"]
            ),
        }
        if (observed_sentinel["present"]
                and observed_sentinel["value"] != caller_sentinel["value"]):
            errors.append("ambient sentinel arrived with a value different from the qsub caller")

        if request_id == "R1" and SECOND_HEX in environment:
            errors.append("R1 unexpectedly received the probe-only second environment name")
        if request_id == "R2":
            if APPROVAL in environment:
                errors.append("R2 unexpectedly received the approval environment name")
            explicit_second = next(
                row["value"] for row in manifest["ordered_explicit_env"]
                if row["name"] == SECOND_HEX
            )
            ambient_second = manifest["qsub_caller_environment"][SECOND_HEX]["value"]
            observed_second = environment.get(SECOND_HEX)
            result["duplicate_name_precedence"] = {
                "explicit_value": explicit_second,
                "ambient_value": ambient_second,
                "job_value": observed_second,
                "explicit_value_won": observed_second == explicit_second,
                "ambient_value_won": observed_second == ambient_second,
            }
        if request_id == "R3":
            if SECOND_HEX in environment:
                errors.append("R3 unexpectedly received the probe-only second environment name")
            caller_approval = manifest["qsub_caller_environment"][APPROVAL]
            observed_approval = result["environment_observation"][APPROVAL]
            result["ambient_approval_name_delivery"] = {
                "submitted_process_present": caller_approval["present"],
                "submitted_process_value": caller_approval["value"],
                "job_present": observed_approval["present"],
                "job_value": observed_approval["value"],
                "job_value_matches_if_present": (
                    not observed_approval["present"]
                    or observed_approval["value"] == AMBIENT_APPROVAL_LITERAL
                ),
            }
            if (observed_approval["present"]
                    and observed_approval["value"] != AMBIENT_APPROVAL_LITERAL):
                errors.append("ambient approval name arrived with an unexpected value")

        result["floor_section8_source_projection"] = _source_projection(
            request_id, environment
        )
        if request_id == "R2":
            driver_observation = _unapproved_driver_observation(
                repo_root=repository,
                scratch_dir=scratch,
                python_executable=python_executable or sys.executable,
                expected_campaign_sha256=manifest["campaign_script_sha256"],
            )
            if driver_observation["accepted_as_expected_refusal"] is not True:
                errors.append("R2 unapproved real driver did not produce the exact early refusal")
        else:
            driver_observation = {
                "executed": False,
                "reason": (
                    "R1 does not execute the approved real driver because official campaign "
                    "execution is outside probe scope"
                    if request_id == "R1"
                    else "R3 does not execute the real driver; it observes ambient approval-name delivery only"
                ),
                "timed_out": False,
                "accepted_as_expected_refusal": None,
            }
        result["unapproved_driver_cli"] = driver_observation
    else:
        result["unapproved_driver_cli"] = {
            "executed": False,
            "reason": "submission manifest was unavailable or invalid",
            "timed_out": False,
            "accepted_as_expected_refusal": None,
        }

    after = _repo_snapshot(repository)
    result["repo_state_after"] = after
    result["repo_working_tree_unchanged"] = before == after
    if before != after:
        errors.append(
            "repository HEAD/detached/clean state, untracked paths, or target source "
            "digests changed during observation"
        )
    result["errors"] = errors
    result["ok"] = not errors
    return result, evidence_dir if manifest is not None else None


def _minimal_failure(
    *, repo_root: Path, pbs_job_id: str, exc: BaseException
) -> dict[str, Any]:
    probe_path = Path(repo_root) / PROBE_RELATIVE_PATH
    probe_sha256 = None
    try:
        if probe_path.is_file() and not probe_path.is_symlink():
            probe_sha256 = _sha256_file(probe_path)
    except OSError:
        pass
    return {
        "schema_version": SCHEMA_VERSION,
        "authority": AUTHORITY,
        "official_campaign_executed": False,
        "ok": False,
        "request_id": None,
        "hostname": socket.gethostname(),
        "pbs_job_id": pbs_job_id,
        "observed_utc": _utc_now(),
        "probe_script": {
            "path": PROBE_RELATIVE_PATH,
            "sha256": probe_sha256,
        },
        "errors": [f"observer: {type(exc).__name__}: {exc}"],
    }


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--scratch-dir", type=Path, required=True)
    parser.add_argument("--pbs-job-id", required=True)
    parser.add_argument("--executing-pbs-sha256", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _argument_parser().parse_args(argv)
    evidence_dir: Path | None = None
    try:
        result, evidence_dir = observe(
            repo_root=args.repo_root,
            scratch_dir=args.scratch_dir,
            pbs_job_id=args.pbs_job_id,
            executing_pbs_sha256=args.executing_pbs_sha256,
        )
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        result = _minimal_failure(
            repo_root=args.repo_root,
            pbs_job_id=args.pbs_job_id,
            exc=exc,
        )
    if evidence_dir is not None:
        destination = evidence_dir / RESULT_NAME
        result["auxiliary_result_json"] = {
            "path": os.fspath(destination),
            "create_only": True,
            "primary_evidence_channel": False,
        }
        try:
            _write_atomic_create_only(destination, result)
        except Exception as exc:
            result["ok"] = False
            result.setdefault("errors", []).append(
                f"auxiliary-result-publish: {type(exc).__name__}: {exc}"
            )
    print(
        RESULT_PREFIX + json.dumps(
            result,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ),
        flush=True,
    )
    return 0 if result.get("ok") is True else 1


if __name__ == "__main__":
    raise SystemExit(main())
