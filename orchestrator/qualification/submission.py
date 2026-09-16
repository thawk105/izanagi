#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prepare immutable series/toolchain identity before T-126 qsub."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.qualification"

from orchestrator.campaign.silo_ladder_rung1 import (
    THIRD_PARTY_SOURCE_ROOT_ENV,
    THIRD_PARTY_STAGING_RELATIVE,
)

from .contract import (  # noqa: E402
    REGISTERED_DEPENDENCY_BUILD_ARGV,
    canonical_json_bytes,
    load_protocol,
    series_identity,
)
from .t126_driver import build_series_preimage  # noqa: E402
from orchestrator.calibrator import perf_preflight as _perf_preflight  # noqa: E402


class SubmissionPreparationError(RuntimeError):
    """Pre-qsub identity cannot be established."""


def _run_text(argv: Sequence[str]) -> str:
    try:
        completed = subprocess.run(
            list(argv), check=True, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError) as exc:
        raise SubmissionPreparationError(
            f"identity command failed: {argv}: {exc}") from exc
    output = (completed.stdout or completed.stderr).splitlines()
    if not output or not output[0]:
        raise SubmissionPreparationError(f"identity command returned empty: {argv}")
    return output[0]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise SubmissionPreparationError(
                f"executable is not a regular file: {path}")
        while True:
            data = os.read(fd, 1024 * 1024)
            if not data:
                break
            digest.update(data)
        after = os.fstat(fd)
        if ((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
                != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)):
            raise SubmissionPreparationError(
                f"executable changed while hashing: {path}")
    finally:
        os.close(fd)
    return digest.hexdigest()


def _executable(name: str, candidates: Sequence[str]) -> dict[str, str]:
    selected = None
    for candidate in candidates:
        found = candidate if Path(candidate).is_absolute() else shutil.which(candidate)
        if found and Path(found).is_file() and not Path(found).is_symlink():
            selected = Path(found).resolve(strict=True)
            break
    if selected is None:
        raise SubmissionPreparationError(f"required executable unavailable: {name}")
    version_argv = (
        [str(selected), "--version"]
        if name != "python" else [str(selected), "--version"])
    return {
        "path": str(selected),
        "sha256": _sha256(selected),
        "version": _run_text(version_argv),
    }


def _dependency(path: Path, expected_commit: str) -> dict[str, str]:
    if path.is_symlink() or not path.is_dir():
        raise SubmissionPreparationError(f"dependency source is unsafe: {path}")
    commit = _run_text(
        ["git", "-C", str(path), "rev-parse", f"{expected_commit}^{{commit}}"])
    tree = _run_text(
        ["git", "-C", str(path), "rev-parse", f"{expected_commit}^{{tree}}"])
    if commit != expected_commit:
        raise SubmissionPreparationError(
            f"dependency expected commit mismatch: {path}")
    return {"commit": commit, "tree": tree}


def prepare_toolchain(policy: Mapping[str, Any]) -> dict[str, Any]:
    executables = {
        "python": _executable("python", ["python3", "python3.10", "python3.11"]),
        "cc": _executable("cc", ["gcc-13"]),
        "cxx": _executable("cxx", ["g++-13"]),
        "cmake": _executable("cmake", ["cmake"]),
    }
    perf_row = None
    perf_error: SubmissionPreparationError | None = None
    try:
        perf_row = _executable("perf", policy["perf_candidates"])
        perf = perf_row["path"]
        try:
            smoke = subprocess.run(
                [perf, "stat", "-x,", "-e",
                 "LLC-load-misses,LLC-loads,instructions,cycles", "--", "true"],
                capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.SubprocessError) as exc:
            raise SubmissionPreparationError(f"perf smoke failed: {exc}") from exc
        perf_text = (smoke.stdout + "\n" + smoke.stderr).lower()
        if (smoke.returncode != 0 or "<not supported>" in perf_text
                or "<not counted>" in perf_text):
            raise SubmissionPreparationError("perf candidate is not functional")
    except SubmissionPreparationError as exc:
        perf_error = exc

    original_path = os.environ.get("PATH")
    try:
        with tempfile.TemporaryDirectory(prefix="t126-submit-perf-") as tmp:
            if perf_row is not None and perf_error is None:
                os.symlink(perf_row["path"], Path(tmp) / "perf")
                os.environ["PATH"] = tmp + os.pathsep + (original_path or "")
            receipt = _perf_preflight.probe_perf_availability(
                perf_candidates=policy["perf_candidates"])
    except (OSError, _perf_preflight.PerfPreflightError) as exc:
        raise SubmissionPreparationError(f"perf preflight failed: {exc}") from exc
    finally:
        if original_path is None:
            os.environ.pop("PATH", None)
        else:
            os.environ["PATH"] = original_path
    try:
        use_perf = _perf_preflight.use_perf_from_receipt(receipt)
    except _perf_preflight.PerfPreflightError as exc:
        raise SubmissionPreparationError(f"perf preflight failed: {exc}") from exc
    if use_perf:
        if perf_error is not None:
            raise perf_error
        if perf_row is None:  # pragma: no cover - guarded by the branch above
            raise SubmissionPreparationError("required executable unavailable: perf")
        executables["perf"] = perf_row
    source_root = Path(os.environ.get(THIRD_PARTY_SOURCE_ROOT_ENV)
                       or Path(__file__).resolve().parents[2] / THIRD_PARTY_STAGING_RELATIVE)
    dependencies = {
        "gflags": _dependency(
            source_root / "gflags", policy["gflags_expected_head"]),
        "glog": _dependency(
            source_root / "glog", policy["glog_expected_head"]),
    }
    build_argv = {
        name: list(argv)
        for name, argv in REGISTERED_DEPENDENCY_BUILD_ARGV.items()
    }
    manifest = {
        "schema_version": "t126-toolchain-manifest/v1",
        "executables": executables,
        "dependencies": dependencies,
        "build_argv": build_argv,
    }
    if not use_perf:
        manifest["perf_preflight"] = receipt
    return manifest


def _durable_json(path: Path, value: Mapping[str, Any]) -> None:
    data = canonical_json_bytes(dict(value)) + b"\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        offset = 0
        while offset < len(data):
            written = os.write(fd, data[offset:])
            if written <= 0:
                raise SubmissionPreparationError(
                    "submission write made no progress")
            offset += written
        os.fsync(fd)
    finally:
        os.close(fd)
    directory = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def prepare(repo_root: Path, output_dir: Path) -> tuple[str, Path, Path]:
    policy = json.loads(
        (repo_root / "tools/pegasus/policy.json").read_text(encoding="utf-8"))
    protocol = load_protocol(
        repo_root / "orchestrator/qualification/t126_control_v1.json")
    toolchain = prepare_toolchain(policy)
    preimage = build_series_preimage(repo_root, protocol, toolchain)
    series_id = series_identity(preimage)
    toolchain_path = output_dir / "toolchain-manifest.json"
    identity_path = output_dir / "series-identity.json"
    _durable_json(toolchain_path, toolchain)
    _durable_json(identity_path, preimage)
    return series_id, toolchain_path, identity_path


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        series_id, toolchain, identity = prepare(
            args.repo_root, args.output_dir)
    except Exception as exc:
        print(f"t126 submission: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(series_id)
    print(toolchain)
    print(identity)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
