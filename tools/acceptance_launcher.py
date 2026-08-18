#!/usr/bin/env python3
"""Run the acceptance runner from a tested Git blob and author its receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable, Mapping, Sequence


_RUNNER_PATH = "tools/run_tests.py"
_EXACT_RUNNER_ARGV = ("python3", _RUNNER_PATH)
_SCHEMA_VERSION = "dev-wave-acceptance-receipt/v5"
_SOURCE_REVISIONS = frozenset({"tested-main", "tested-tip-bootstrap"})
_AUTHORITY_KINDS = {
    "tested-main": "dev-wave-acceptance-launcher",
    "tested-tip-bootstrap": "dev-wave-acceptance-launcher-bootstrap-tip",
}
_EFFECTIVE_SCHEDULERS = frozenset({"loadgroup", "serial", "unknown"})
_SHA1_RE = re.compile(r"[0-9a-f]{40}\Z")
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_HOLDER_RE = re.compile(r"[0-9a-f]{12}\Z")
_MAX_COMPLETION_BYTES = 1024 * 1024
_FINGERPRINT_FIELDS = frozenset(
    {"digest", "head_sha", "status_bytes", "diff_bytes", "submodule_status_bytes"}
)
_ENV_PROJECTION_FIELDS = frozenset(
    {
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
        "IZANAGI_TASK_RUN_ID",
        "IZANAGI_TASK_RUNS_ROOT",
    }
)
_GIT_ENV_OVERRIDES = {
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_ATTR_NOSYSTEM": "1",
    "GIT_NO_REPLACE_OBJECTS": "1",
}

_RUNNER_BOOTSTRAP = (
    "import os,sys\n"
    "if os.environ.get('PYTHONDONTWRITEBYTECODE'):\n"
    "    sys.dont_write_bytecode = True\n"
    "source = sys.stdin.buffer.read()\n"
    "namespace = {\n"
    "    '__name__': '_izanagi_acceptance_runner',\n"
    "    '__file__': sys.argv[1],\n"
    "}\n"
    "exec(compile(source, namespace['__file__'], 'exec'), namespace)\n"
    "raise SystemExit(namespace['main'](sys.argv[2:]))\n"
)


class LauncherFailure(Exception):
    """A fail-closed launcher error."""


@dataclass(frozen=True)
class _Config:
    repo_root: Path
    wave: str
    lease_holder: str
    tested_main: str
    tested_tip: str
    launcher_source_revision: str
    launcher_blob_sha: str
    launcher_executed_sha256: str
    waiter_executed_sha256: str
    waiter_blob_sha: str
    receipt_file: Path
    log_file: Path
    outcome_fd: int
    completion_fd: int
    pre_fingerprint: Mapping[str, object]
    env_projection: Mapping[str, object]


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return (
            json.dumps(
                value,
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("ascii")
    except (TypeError, UnicodeError, ValueError, RecursionError) as exc:
        raise LauncherFailure("JSON value is not canonicalizable") from exc


def _normalize_child_rc(returncode: int) -> int:
    if returncode >= 0:
        return returncode
    return 128 + (-returncode)


def _validate_fingerprint(value: Mapping[str, object], label: str) -> None:
    if set(value) != _FINGERPRINT_FIELDS:
        raise LauncherFailure(f"{label} fingerprint has unexpected fields")
    if (
        not isinstance(value["digest"], str)
        or _SHA256_RE.fullmatch(value["digest"]) is None
        or not isinstance(value["head_sha"], str)
        or _SHA1_RE.fullmatch(value["head_sha"]) is None
    ):
        raise LauncherFailure(f"invalid {label} fingerprint digest")
    for field in ("status_bytes", "diff_bytes", "submodule_status_bytes"):
        number = value[field]
        if not isinstance(number, int) or isinstance(number, bool) or number < 0:
            raise LauncherFailure(f"invalid {label} fingerprint byte count")


def _validate_config(config: _Config, runner_argv: Sequence[str]) -> None:
    repo_text = str(config.repo_root)
    if (
        not config.repo_root.is_absolute()
        or str(config.repo_root.resolve()) != repo_text
    ):
        raise LauncherFailure("repo root must be a canonical absolute path")
    if tuple(runner_argv) != _EXACT_RUNNER_ARGV:
        raise LauncherFailure("runner argv is not exact")
    if config.launcher_source_revision not in _SOURCE_REVISIONS:
        raise LauncherFailure("invalid launcher source revision")
    if not config.wave or _HOLDER_RE.fullmatch(config.lease_holder) is None:
        raise LauncherFailure("invalid wave or lease holder")
    for name, value in (
        ("tested_main", config.tested_main),
        ("tested_tip", config.tested_tip),
        ("launcher_blob_sha", config.launcher_blob_sha),
        ("waiter_blob_sha", config.waiter_blob_sha),
    ):
        if _SHA1_RE.fullmatch(value) is None:
            raise LauncherFailure(f"invalid {name}")
    for name, value in (
        ("launcher_executed_sha256", config.launcher_executed_sha256),
        ("waiter_executed_sha256", config.waiter_executed_sha256),
    ):
        if _SHA256_RE.fullmatch(value) is None:
            raise LauncherFailure(f"invalid {name}")
    if not isinstance(config.pre_fingerprint, Mapping):
        raise LauncherFailure("pre fingerprint must be an object")
    if not isinstance(config.env_projection, Mapping):
        raise LauncherFailure("environment projection must be an object")
    _validate_fingerprint(config.pre_fingerprint, "pre")
    if set(config.env_projection) != _ENV_PROJECTION_FIELDS or any(
        value is not None and not isinstance(value, str)
        for value in config.env_projection.values()
    ):
        raise LauncherFailure("invalid environment projection")
    if not config.receipt_file.is_absolute() or not config.log_file.is_absolute():
        raise LauncherFailure("output paths must be absolute")
    if config.outcome_fd < 0 or config.completion_fd < 0:
        raise LauncherFailure("invalid protocol fd")


def _read_runner_blob(repo: Path, tested_tip: str) -> bytes:
    environment = dict(os.environ)
    environment.update(_GIT_ENV_OVERRIDES)
    result = subprocess.run(
        (
            "git",
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "credential.helper=",
            "-C",
            str(repo),
            "cat-file",
            "blob",
            f"{tested_tip}:{_RUNNER_PATH}",
        ),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
    )
    if result.returncode != 0:
        raise LauncherFailure("cannot read tested-tip runner blob")
    return result.stdout


def _run_blob(
    source: bytes,
    canonical_runner_path: Path,
    log_file: Path,
) -> int:
    try:
        with log_file.open("xb") as stream:
            result = subprocess.run(
                (
                    "python3",
                    "-I",
                    "-c",
                    _RUNNER_BOOTSTRAP,
                    str(canonical_runner_path),
                ),
                check=False,
                stdout=stream,
                stderr=subprocess.STDOUT,
                input=source,
                cwd=canonical_runner_path.parent.parent,
            )
    except OSError as exc:
        raise LauncherFailure("cannot execute runner blob") from exc
    return _normalize_child_rc(result.returncode)


def _write_fd(fd: int, payload: bytes) -> None:
    view = memoryview(payload)
    while view:
        try:
            written = os.write(fd, view)
        except OSError as exc:
            raise LauncherFailure("cannot write outcome protocol") from exc
        if written <= 0:
            raise LauncherFailure("short outcome protocol write")
        view = view[written:]


def _read_completion_fd(fd: int) -> Mapping[str, object]:
    chunks: list[bytes] = []
    size = 0
    while True:
        try:
            chunk = os.read(fd, min(65536, _MAX_COMPLETION_BYTES + 1 - size))
        except OSError as exc:
            raise LauncherFailure("cannot read completion protocol") from exc
        if not chunk:
            break
        chunks.append(chunk)
        size += len(chunk)
        if size > _MAX_COMPLETION_BYTES:
            raise LauncherFailure("completion protocol is too large")
    raw = b"".join(chunks)
    try:
        value = json.loads(raw.decode("ascii"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise LauncherFailure("invalid completion protocol JSON") from exc
    if not isinstance(value, dict) or _canonical_json_bytes(value) != raw:
        raise LauncherFailure("completion protocol JSON is not canonical")
    return value


def _validated_completion(
    completion: Mapping[str, object], child_rc: int
) -> tuple[Mapping[str, object], str, Mapping[str, object] | None, str]:
    if set(completion) != {
        "effective_scheduler",
        "post_fingerprint",
        "red_check",
    }:
        raise LauncherFailure("completion protocol has unexpected fields")
    post_fingerprint = completion["post_fingerprint"]
    scheduler = completion["effective_scheduler"]
    red_check = completion["red_check"]
    if not isinstance(post_fingerprint, dict):
        raise LauncherFailure("post fingerprint must be an object")
    _validate_fingerprint(post_fingerprint, "post")
    if not isinstance(scheduler, str) or scheduler not in _EFFECTIVE_SCHEDULERS:
        raise LauncherFailure("invalid effective scheduler")
    if child_rc == 0:
        if red_check is not None:
            raise LauncherFailure("child-green cannot contain red-check data")
        return post_fingerprint, scheduler, None, "child-green"
    if child_rc != 1 or not isinstance(red_check, dict):
        raise LauncherFailure("runner result is not receiptable")
    required = {
        "checker_blob_sha",
        "checker_rc",
        "checker_receipt_sha256",
        "checker_status",
        "flake_nodeids",
        "red_nodeids",
    }
    if set(red_check) != required:
        raise LauncherFailure("red-check data has unexpected fields")
    if (
        not isinstance(red_check["checker_rc"], int)
        or isinstance(red_check["checker_rc"], bool)
        or not isinstance(red_check["checker_status"], str)
        or not isinstance(red_check["checker_blob_sha"], str)
        or _SHA1_RE.fullmatch(red_check["checker_blob_sha"]) is None
        or not isinstance(red_check["checker_receipt_sha256"], str)
        or _SHA256_RE.fullmatch(red_check["checker_receipt_sha256"]) is None
    ):
        raise LauncherFailure("invalid red-check scalar")
    red_nodeids = red_check["red_nodeids"]
    flake_nodeids = red_check["flake_nodeids"]
    if not isinstance(red_nodeids, list) or not isinstance(flake_nodeids, list):
        raise LauncherFailure("red-check nodeids must be arrays")
    if any(
        not isinstance(item, str) or not item
        for item in red_nodeids + flake_nodeids
    ):
        raise LauncherFailure("invalid red-check nodeid")
    if (
        red_nodeids != sorted(set(red_nodeids))
        or flake_nodeids != sorted(set(flake_nodeids))
        or not set(red_nodeids).isdisjoint(flake_nodeids)
        or not (red_nodeids or flake_nodeids)
    ):
        raise LauncherFailure("invalid red-check nodeid sets")
    return post_fingerprint, scheduler, red_check, "non-attributable-only"


def _receipt_bytes(
    config: _Config,
    runner_argv: Sequence[str],
    child_rc: int,
    runner_executed_sha256: str,
    log_sha256: str,
    completion: Mapping[str, object],
) -> bytes:
    post_fingerprint, scheduler, red_check, verdict = _validated_completion(
        completion, child_rc
    )
    receipt = {
        "schema_version": _SCHEMA_VERSION,
        "authority_kind": _AUTHORITY_KINDS[config.launcher_source_revision],
        "acceptance_wave": config.wave,
        "lease_holder": config.lease_holder,
        "tested_main": config.tested_main,
        "tested_tip": config.tested_tip,
        "argv": list(runner_argv),
        "resolved_runner_path": str(config.repo_root / _RUNNER_PATH),
        "child_rc": child_rc,
        "pre_fingerprint": dict(config.pre_fingerprint),
        "post_fingerprint": dict(post_fingerprint),
        "waiter_blob_sha": config.waiter_blob_sha,
        "env_projection": dict(config.env_projection),
        "verdict": verdict,
        "log_sha256": log_sha256,
        "effective_scheduler": scheduler,
        "checker_rc": None if red_check is None else red_check["checker_rc"],
        "checker_status": None if red_check is None else red_check["checker_status"],
        "checker_blob_sha": (
            None if red_check is None else red_check["checker_blob_sha"]
        ),
        "checker_receipt_sha256": (
            None if red_check is None else red_check["checker_receipt_sha256"]
        ),
        "red_nodeids": [] if red_check is None else red_check["red_nodeids"],
        "flake_nodeids": [] if red_check is None else red_check["flake_nodeids"],
        "launcher_source_revision": config.launcher_source_revision,
        "launcher_blob_sha": config.launcher_blob_sha,
        "launcher_executed_sha256": config.launcher_executed_sha256,
        "waiter_executed_sha256": config.waiter_executed_sha256,
        "runner_executed_sha256": runner_executed_sha256,
    }
    return _canonical_json_bytes(receipt)


def _write_receipt(path: Path, payload: bytes) -> None:
    flags = os.O_WRONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise LauncherFailure("cannot open precreated receipt file") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size != 0 or info.st_nlink != 1:
            raise LauncherFailure("receipt file is not a fresh regular file")
        with os.fdopen(fd, "wb", closefd=False) as stream:
            written = stream.write(payload)
            if written != len(payload):
                raise LauncherFailure("short receipt write")
            stream.flush()
            os.fsync(fd)
    except OSError as exc:
        raise LauncherFailure("cannot persist receipt") from exc
    finally:
        os.close(fd)


def _launch(
    config: _Config,
    runner_argv: Sequence[str],
    *,
    blob_reader: Callable[[Path, str], bytes] = _read_runner_blob,
    blob_runner: Callable[[bytes, Path, Path], int] = _run_blob,
    outcome_writer: Callable[[bytes], None] | None = None,
    completion_reader: Callable[[], Mapping[str, object]] | None = None,
) -> None:
    _validate_config(config, runner_argv)
    canonical_runner_path = config.repo_root / _RUNNER_PATH
    source = blob_reader(config.repo_root, config.tested_tip)
    runner_executed_sha256 = hashlib.sha256(source).hexdigest()
    child_rc = blob_runner(source, canonical_runner_path, config.log_file)

    # Fetch the immutable tested-tip blob independently after execution. This is
    # intentionally not derived from the executed buffer: M3 must fail closed if
    # the observed tip content and the bytes handed to compile/exec ever differ.
    tip_source = blob_reader(config.repo_root, config.tested_tip)
    tip_content_sha256 = hashlib.sha256(tip_source).hexdigest()
    if runner_executed_sha256 != tip_content_sha256:
        raise LauncherFailure("executed runner does not match tested-tip blob")
    try:
        log_sha256 = hashlib.sha256(config.log_file.read_bytes()).hexdigest()
    except OSError as exc:
        raise LauncherFailure("cannot hash runner log") from exc
    outcome = _canonical_json_bytes(
        {
            "child_rc": child_rc,
            "log_sha256": log_sha256,
            "runner_executed_sha256": runner_executed_sha256,
        }
    )
    (outcome_writer or (lambda value: _write_fd(config.outcome_fd, value)))(outcome)
    if child_rc not in {0, 1}:
        raise LauncherFailure("runner result is not receiptable")
    completion = (
        completion_reader or (lambda: _read_completion_fd(config.completion_fd))
    )()
    receipt = _receipt_bytes(
        config,
        runner_argv,
        child_rc,
        runner_executed_sha256,
        log_sha256,
        completion,
    )
    _write_receipt(config.receipt_file, receipt)


def _json_object(raw: str, label: str) -> Mapping[str, object]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"{label} must be JSON") from exc
    if not isinstance(value, dict):
        raise argparse.ArgumentTypeError(f"{label} must be a JSON object")
    return value


def _parse_args(argv: Sequence[str]) -> tuple[_Config, tuple[str, ...]]:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--wave", required=True)
    parser.add_argument("--lease-holder", required=True)
    parser.add_argument("--tested-main", required=True)
    parser.add_argument("--tested-tip", required=True)
    parser.add_argument("--launcher-source-revision", required=True)
    parser.add_argument("--launcher-blob-sha", required=True)
    parser.add_argument("--launcher-executed-sha256", required=True)
    parser.add_argument("--waiter-executed-sha256", required=True)
    parser.add_argument("--waiter-blob-sha", required=True)
    parser.add_argument("--receipt-file", required=True, type=Path)
    parser.add_argument("--log-file", required=True, type=Path)
    parser.add_argument("--outcome-fd", required=True, type=int)
    parser.add_argument("--completion-fd", required=True, type=int)
    parser.add_argument(
        "--pre-fingerprint-json",
        required=True,
        type=lambda raw: _json_object(raw, "pre fingerprint"),
    )
    parser.add_argument(
        "--env-projection-json",
        required=True,
        type=lambda raw: _json_object(raw, "environment projection"),
    )
    parser.add_argument("runner_argv", nargs=argparse.REMAINDER)
    args = parser.parse_args(list(argv))
    runner_argv = tuple(args.runner_argv)
    if runner_argv[:1] == ("--",):
        runner_argv = runner_argv[1:]
    config = _Config(
        repo_root=args.repo_root,
        wave=args.wave,
        lease_holder=args.lease_holder,
        tested_main=args.tested_main,
        tested_tip=args.tested_tip,
        launcher_source_revision=args.launcher_source_revision,
        launcher_blob_sha=args.launcher_blob_sha,
        launcher_executed_sha256=args.launcher_executed_sha256,
        waiter_executed_sha256=args.waiter_executed_sha256,
        waiter_blob_sha=args.waiter_blob_sha,
        receipt_file=args.receipt_file,
        log_file=args.log_file,
        outcome_fd=args.outcome_fd,
        completion_fd=args.completion_fd,
        pre_fingerprint=args.pre_fingerprint_json,
        env_projection=args.env_projection_json,
    )
    return config, runner_argv


def main(argv: Sequence[str] | None = None) -> int:
    try:
        config, runner_argv = _parse_args(sys.argv[1:] if argv is None else argv)
        _launch(config, runner_argv)
    except LauncherFailure as exc:
        print(f"acceptance launcher: {exc}", file=sys.stderr, flush=True)
        return 70
    return 0


if __name__ == "__main__":
    sys.exit(main())
