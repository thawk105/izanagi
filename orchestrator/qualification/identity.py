# -*- coding: utf-8 -*-
"""External verification of recorded Git, source, dependency, and tool bytes."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from orchestrator.campaign.silo_ladder_rung1 import (
    THIRD_PARTY_SOURCE_ROOT_ENV,
    THIRD_PARTY_STAGING_RELATIVE,
)

from . import artifacts as qualification_artifacts
from .artifacts import (
    QualificationArtifactError,
    load_json_strict,
    read_regular_file,
)
from .contract import (
    REGISTERED_DEPENDENCY_BUILD_ARGV,
    REQUIRED_CODE_IDENTITY_PATHS,
    REQUIRED_SCRIPT_IDENTITY_PATHS,
    RESERVATION_POLICY_RELATIVE_PATH,
    protocol_sha256,
    series_identity,
)


_HEX40 = re.compile(r"[0-9a-f]{40}")


class IdentityVerificationError(QualificationArtifactError):
    """Recorded identity does not derive from immutable external anchors."""


def verify_submission_script_chain(
        *, submission: Mapping[str, Any],
        preimage: Mapping[str, Any],
        job_result: Mapping[str, Any] | None = None) -> str:
    """Re-derive submission/runtime result script identity from the Git preimage."""
    committed = preimage.get("script_identity", {}).get(
        "tools/pegasus/t126_qualification.sh")
    submitted = submission.get("job_script_sha256")
    if (type(committed) is not str or type(submitted) is not str
            or submitted != committed):
        raise IdentityVerificationError(
            "submission job script hash differs from committed series blob")
    if (job_result is not None
            and job_result.get("job_script_sha256") != submitted):
        raise IdentityVerificationError(
            "job-result script hash differs from submission identity")
    return committed


def _safe_relative(value: object, label: str) -> str:
    if type(value) is not str or not value:
        raise IdentityVerificationError(f"{label} path is empty")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise IdentityVerificationError(f"{label} path is unsafe")
    return path.as_posix()


def _git_bytes(repo: Path, *args: str) -> bytes:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), *args],
            stderr=subprocess.DEVNULL, timeout=20,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise IdentityVerificationError(
            f"Git object verification failed for {args}: {exc}") from exc


def _git_text(repo: Path, *args: str) -> str:
    try:
        return _git_bytes(repo, *args).decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise IdentityVerificationError("Git identity is not ASCII") from exc


def _fd_sha256(path: Path) -> str:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise IdentityVerificationError(
            f"cannot open immutable executable {path}: {exc}") from exc
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise IdentityVerificationError(
                f"toolchain path is not a regular file: {path}")
        digest = hashlib.sha256()
        while True:
            block = os.read(fd, 1024 * 1024)
            if not block:
                break
            digest.update(block)
        after = os.fstat(fd)
        if ((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
                != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)):
            raise IdentityVerificationError(
                f"toolchain executable changed while hashing: {path}")
        return digest.hexdigest()
    finally:
        os.close(fd)


def verify_recorded_series_identity(
        *, git_repo_root: Path, attempt_dir: Path,
        preimage: Mapping[str, Any], protocol: Mapping[str, Any],
        policy: Mapping[str, Any], reservation_policy: Mapping[str, Any],
) -> str:
    """Re-derive every load-bearing identity from Git objects or immutable bytes."""
    computed = series_identity(preimage)
    commit = preimage["superproject_commit"]
    if _HEX40.fullmatch(commit) is None:
        raise IdentityVerificationError("recorded commit is invalid")
    actual_tree = _git_text(git_repo_root, "rev-parse", f"{commit}^{{tree}}")
    actual_gitlink = _git_text(
        git_repo_root, "rev-parse", f"{commit}:external/ccbench")
    if (actual_tree != preimage["superproject_tree"]
            or actual_gitlink != preimage["ccbench_gitlink"]):
        raise IdentityVerificationError(
            "recorded commit/tree/gitlink chain does not derive from Git")

    identities = {
        **preimage["code_identity"],
        **preimage["script_identity"],
    }
    required = REQUIRED_CODE_IDENTITY_PATHS | REQUIRED_SCRIPT_IDENTITY_PATHS
    if set(identities) != required:
        raise IdentityVerificationError("recorded code/script set is incomplete")
    for relative, expected in identities.items():
        safe = _safe_relative(relative, "Git blob")
        actual = hashlib.sha256(
            _git_bytes(git_repo_root, "cat-file", "blob", f"{commit}:{safe}")
        ).hexdigest()
        if actual != expected:
            raise IdentityVerificationError(
                f"recorded Git blob hash mismatch: {safe}")

    for relative in sorted(
            qualification_artifacts.QUALIFICATION_SCHEMA_RELATIVE_PATHS):
        expected = identities[relative]
        live = qualification_artifacts.qualification_schema_bytes(
            PurePosixPath(relative).name)
        if hashlib.sha256(live).hexdigest() != expected:
            raise IdentityVerificationError(
                "live qualification schema differs from recorded Git blob: "
                f"{relative}")

    committed_protocol = _git_bytes(
        git_repo_root, "cat-file", "blob",
        f"{commit}:orchestrator/qualification/t126_control_v1.json",
    )
    if hashlib.sha256(committed_protocol).hexdigest() != identities[
            "orchestrator/qualification/t126_control_v1.json"]:
        raise IdentityVerificationError("approved protocol blob pin mismatch")
    if preimage["protocol_sha256"] != protocol_sha256(protocol):
        raise IdentityVerificationError("protocol semantic hash mismatch")
    committed_policy = json.loads(_git_bytes(
        git_repo_root, "cat-file", "blob",
        f"{commit}:tools/pegasus/policy.json"))
    if dict(policy) != committed_policy:
        raise IdentityVerificationError(
            "live policy differs from the committed approved policy")
    committed_reservation_policy = json.loads(_git_bytes(
        git_repo_root, "cat-file", "blob",
        f"{commit}:{RESERVATION_POLICY_RELATIVE_PATH}"))
    if dict(reservation_policy) != committed_reservation_policy:
        raise IdentityVerificationError(
            "live reservation policy differs from the committed approved"
            " reservation policy")
    if (preimage["pair_roles"] != protocol["source"]["members"]
            or preimage["workload"] != protocol["workload"]
            or preimage["verification"] != protocol["verification"]
            or preimage["threshold"] != protocol["threshold"]
            or preimage["sprt"] != protocol["sprt"]
            or preimage["timing"] != protocol["timing"]
            or preimage["order_seed"] != protocol["order"]["seed"]
            or preimage["source_snapshots"] != {
                "campaign_lock": {
                    "path": protocol["source"]["campaign_lock_path"],
                    "sha256": protocol["source"]["campaign_lock_sha256"],
                },
                "wal": {
                    "path": protocol["source"]["wal_path"],
                    "sha256": protocol["source"]["wal_sha256"],
                },
            }):
        raise IdentityVerificationError("approved source pair/snapshot pin mismatch")

    source_manifest = load_json_strict(
        attempt_dir / "source/source-snapshots.json")
    for name in ("campaign_lock", "wal"):
        expected = preimage["source_snapshots"][name]
        relative = _safe_relative(expected["path"], f"{name} original")
        committed = _git_bytes(
            git_repo_root, "cat-file", "blob", f"{commit}:{relative}")
        if hashlib.sha256(committed).hexdigest() != expected["sha256"]:
            raise IdentityVerificationError(
                f"{name} is not the recorded committed blob")
        row = source_manifest[name]
        snapshot_relative = _safe_relative(row.get("path"), f"{name} snapshot")
        snapshot = attempt_dir.joinpath(*PurePosixPath(snapshot_relative).parts)
        if snapshot.is_symlink() or not snapshot.is_file():
            raise IdentityVerificationError(f"{name} snapshot is missing")
        if read_regular_file(snapshot) != committed:
            raise IdentityVerificationError(
                f"{name} snapshot differs from committed bytes")

    toolchain = preimage["toolchain_manifest"]
    for name, row in toolchain["executables"].items():
        path = Path(row["path"])
        if _fd_sha256(path) != row["sha256"]:
            raise IdentityVerificationError(
                f"toolchain executable hash mismatch: {name}")
    source_root = Path(os.environ.get(THIRD_PARTY_SOURCE_ROOT_ENV)
                       or git_repo_root / THIRD_PARTY_STAGING_RELATIVE)
    dependency_paths = {
        "gflags": source_root / "gflags",
        "glog": source_root / "glog",
    }
    for name, row in toolchain["dependencies"].items():
        source = Path(dependency_paths.get(name, ""))
        if (not source.is_absolute() or source.is_symlink()
                or not source.is_dir()):
            raise IdentityVerificationError(
                f"dependency source root is invalid: {name}")
        expected_head = policy.get(f"{name}_expected_head")
        if row["commit"] != expected_head:
            raise IdentityVerificationError(
                f"dependency commit is not the policy expected head: {name}")
        commit_actual = _git_text(
            source, "rev-parse", f"{row['commit']}^{{commit}}")
        tree_actual = _git_text(
            source, "rev-parse", f"{row['commit']}^{{tree}}")
        if commit_actual != row["commit"] or tree_actual != row["tree"]:
            raise IdentityVerificationError(
                f"dependency Git object mismatch: {name}")
    if toolchain["build_argv"] != REGISTERED_DEPENDENCY_BUILD_ARGV:
        raise IdentityVerificationError(
            "dependency build argv differs from the registered argv")
    return computed
